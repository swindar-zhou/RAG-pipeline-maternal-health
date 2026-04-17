"""
LangGraph conversational agent: ZIP code → county confirmation → maternal health programs.

Flow
  1. User enters a 5-digit ZIP code
  2. Bot resolves ZIP → California county (via pgeocode, offline USPS data)
  3. Bot asks user to confirm the county
  4. User confirms → programs retrieved and displayed
  5. User denies → ask for ZIP again

Program retrieval strategy (in priority order)
  A. Phase 3 structured CSV (data/structured/v{N}/California_{County}_Healthcare_Data.csv)
     — pre-computed, no LLM call required, fastest path
  B. RAG + LLM (ChromaDB vectorstore → gpt-4o-mini)
     — used when no CSV exists for a county (e.g. newly scraped but not yet structured)

State is a plain dict — fully JSON-serializable for FastAPI / Streamlit integration.

USAGE
  # Interactive CLI:
  python -m src.knowledge_graph

  # Programmatic (e.g. FastAPI handler):
  from src.knowledge_graph import chat, initial_state
  state = initial_state()
  response, state = chat("94103", state)   # → "Found ZIP 94103 in San Francisco County..."
  response, state = chat("yes", state)     # → list of programs

REQUIRES
  pip install -r requirements-langchain.txt
  OPENAI_API_KEY set in .env or environment (only needed for RAG fallback path)
"""

from __future__ import annotations

import csv
import glob
import os
import re
from typing import Any, Dict, List, Optional, TypedDict

# ─────────────────────────────────────────────────────────────────────────────
# State schema
# ─────────────────────────────────────────────────────────────────────────────

class ConversationState(TypedDict):
    user_input:        str
    zip_code:          Optional[str]
    county:            Optional[str]
    county_confirmed:  bool
    programs:          Optional[List[Dict[str, str]]]
    response:          str
    # step drives the graph routing:
    # "ask_zip" | "confirm_county" | "show_programs" | "done" | "error"
    step:              str


def initial_state() -> ConversationState:
    return ConversationState(
        user_input="",
        zip_code=None,
        county=None,
        county_confirmed=False,
        programs=None,
        response="Please enter your 5-digit California ZIP code to find maternal health programs near you.",
        step="ask_zip",
    )


# ─────────────────────────────────────────────────────────────────────────────
# ZIP → county (pgeocode, offline)
# ─────────────────────────────────────────────────────────────────────────────

def zip_to_county(zip_code: str) -> Optional[str]:
    """
    Resolve a US ZIP code to a California county name.
    Returns the county name (without ' County' suffix) or None if not found / not in CA.
    """
    try:
        import pgeocode
        nomi = pgeocode.Nominatim("us")
        result = nomi.query_postal_code(zip_code)
        # pgeocode returns a pandas Series; check for NaN
        import math
        if result is None:
            return None
        county_raw = result.get("county_name", "") if hasattr(result, "get") else getattr(result, "county_name", "")
        state_code = result.get("state_code", "") if hasattr(result, "get") else getattr(result, "state_code", "")
        if not county_raw or (hasattr(county_raw, "__class__") and county_raw.__class__.__name__ == "float"):
            return None
        county_raw = str(county_raw)
        if str(state_code) != "CA":
            return None
        # Strip " County" suffix
        return re.sub(r'\s+county$', '', county_raw, flags=re.IGNORECASE).strip()
    except ImportError:
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Program retrieval — Path A: Phase 3 structured CSV
# ─────────────────────────────────────────────────────────────────────────────

_STRUCTURED_DIR = os.path.join("data", "structured")


def _latest_structured_version() -> Optional[str]:
    """Return the path to the highest-numbered version directory."""
    dirs = glob.glob(os.path.join(_STRUCTURED_DIR, "v*"))
    versioned = []
    for d in dirs:
        name = os.path.basename(d)
        m = re.match(r'^v(\d+)$', name)
        if m:
            versioned.append((int(m.group(1)), d))
    if not versioned:
        return None
    return max(versioned, key=lambda x: x[0])[1]


def _county_csv_path(county: str) -> Optional[str]:
    """Locate the Phase 3 CSV for a county in the latest version dir."""
    version_dir = _latest_structured_version()
    if not version_dir:
        return None
    # File naming convention: California_{County}_Healthcare_Data.csv
    # spaces replaced with underscores, e.g. "San Francisco" → "San_Francisco"
    county_snake = county.replace(" ", "_")
    pattern = os.path.join(version_dir, f"California_{county_snake}_Healthcare_Data.csv")
    if os.path.isfile(pattern):
        return pattern
    # Also try case-insensitive glob fallback
    matches = glob.glob(os.path.join(version_dir, f"*{county_snake}*"))
    return matches[0] if matches else None


def _load_programs_from_csv(county: str) -> List[Dict[str, str]]:
    """Load pre-structured programs for a county from the latest Phase 3 CSV."""
    csv_path = _county_csv_path(county)
    if not csv_path:
        return []
    programs: List[Dict[str, str]] = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = row.get("Program_Name", "").strip()
                if not name or name.lower() in ("not found", "n/a", ""):
                    continue
                programs.append({
                    "program_name":        name,
                    "program_category":    row.get("Program_Category", "").strip(),
                    "program_description": row.get("Program_Description", "").strip(),
                    "target_population":   row.get("Target_Population", "").strip(),
                    "eligibility":         row.get("Eligibility_Requirements", "").strip(),
                    "how_to_apply":        row.get("Application_Process", "").strip(),
                    "financial_help":      row.get("Financial_Assistance_Available", "").strip(),
                    "website":             row.get("Program_Website_URL", "").strip(),
                })
    except Exception:
        pass
    return programs


# ─────────────────────────────────────────────────────────────────────────────
# Program retrieval — Path B: RAG + LLM via vectorstore
# ─────────────────────────────────────────────────────────────────────────────

_RAG_PROMPT = """\
You are a maternal health program specialist for California.
Using ONLY the context below, list all maternal health programs available in {county} County.

For each program provide:
- Program name
- One-sentence description
- Who is eligible
- How to apply (if mentioned)
- Website URL (if mentioned)

If a field is not mentioned in the context, write "Not specified".
List programs as a numbered markdown list. Do not invent information.

Context:
{context}
"""


def _load_programs_from_rag(county: str) -> List[Dict[str, str]]:
    """RAG fallback: retrieve chunks from vectorstore, extract programs with LLM."""
    from src.vector_store import get_county_retriever
    from langchain_openai import ChatOpenAI
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate

    retriever = get_county_retriever(county, k=10)
    if retriever is None:
        return []

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = PromptTemplate(
        input_variables=["context", "county"],
        template=_RAG_PROMPT,
    )

    # Partial the county into the prompt so RetrievalQA only passes 'context'
    county_prompt = prompt.partial(county=county)

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": county_prompt},
        return_source_documents=False,
    )

    try:
        result = chain.invoke({"query": f"List all maternal health programs in {county} County California"})
        raw_text = result.get("result", "") if isinstance(result, dict) else str(result)
    except Exception as e:
        return [{"program_name": f"[RAG error: {e}]", "program_description": "",
                 "target_population": "", "eligibility": "", "how_to_apply": "",
                 "financial_help": "", "website": "", "program_category": ""}]

    # Return as a single "raw" entry — the caller formats it
    return [{"program_name": "__rag_raw__", "raw_text": raw_text,
             "program_description": "", "target_population": "",
             "eligibility": "", "how_to_apply": "", "financial_help": "",
             "website": "", "program_category": ""}]


def retrieve_programs(county: str) -> List[Dict[str, str]]:
    """Priority: CSV → RAG → empty."""
    programs = _load_programs_from_csv(county)
    if programs:
        return programs
    return _load_programs_from_rag(county)


# ─────────────────────────────────────────────────────────────────────────────
# Response formatter
# ─────────────────────────────────────────────────────────────────────────────

def _format_programs(county: str, programs: List[Dict[str, str]]) -> str:
    if not programs:
        return (
            f"I wasn't able to find specific maternal health programs for "
            f"**{county} County** in my database yet.\n\n"
            f"You can contact the county health department directly or visit "
            f"the California Department of Public Health at:\n"
            f"https://www.cdph.ca.gov/Programs/CFH/DMCAH"
        )

    # RAG raw text path
    if len(programs) == 1 and programs[0].get("program_name") == "__rag_raw__":
        header = f"**Maternal health programs in {county} County** (retrieved via search):\n\n"
        return header + programs[0].get("raw_text", "No programs found.")

    lines = [f"**Maternal health programs in {county} County** ({len(programs)} found):\n"]
    for i, p in enumerate(programs, 1):
        name = p.get("program_name", "Unnamed program")
        desc = p.get("program_description", "")
        elig = p.get("eligibility", "")
        apply_ = p.get("how_to_apply", "")
        url = p.get("website", "")

        block = [f"{i}. **{name}**"]
        if desc and desc.lower() not in ("not specified", "not found", ""):
            block.append(f"   {desc[:160]}{'...' if len(desc) > 160 else ''}")
        if elig and elig.lower() not in ("not specified", "not found", ""):
            block.append(f"   *Eligibility:* {elig[:120]}")
        if apply_ and apply_.lower() not in ("not specified", "not found", ""):
            block.append(f"   *How to apply:* {apply_[:120]}")
        if url and url.lower() not in ("not specified", "not found", ""):
            block.append(f"   *Website:* {url}")
        lines.append("\n".join(block))

    lines.append(
        f"\nFor more information, visit your county health department or "
        f"call 2-1-1 (California social services hotline)."
    )
    return "\n\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LangGraph nodes
# ─────────────────────────────────────────────────────────────────────────────

def node_parse_input(state: ConversationState) -> ConversationState:
    """
    Parse user input and route to the next step.
    Handles: ZIP entry, yes/no county confirmation, free-form county name.
    """
    text = state["user_input"].strip()
    text_lower = text.lower()

    # ── ZIP code entered ──────────────────────────────────────────────────────
    if re.match(r'^\d{5}$', text):
        county = zip_to_county(text)
        if not county:
            return {
                **state,
                "step": "ask_zip",
                "response": (
                    f"I couldn't find a California county for ZIP code **{text}**. "
                    f"Please double-check and try again."
                ),
            }
        return {
            **state,
            "zip_code": text,
            "county": county,
            "county_confirmed": False,
            "step": "confirm_county",
            "response": (
                f"ZIP code **{text}** is in **{county} County**, California. "
                f"Is that correct? *(yes / no)*"
            ),
        }

    # ── County confirmation ───────────────────────────────────────────────────
    if text_lower in ("yes", "y", "yeah", "yep", "correct", "that's right", "right"):
        if state.get("county"):
            return {
                **state,
                "county_confirmed": True,
                "step": "show_programs",
                "response": f"Looking up programs for **{state['county']} County**...",
            }

    if text_lower in ("no", "n", "nope", "wrong", "incorrect"):
        return {
            **state,
            "zip_code": None,
            "county": None,
            "county_confirmed": False,
            "step": "ask_zip",
            "response": "No problem! Please enter your 5-digit California ZIP code again.",
        }

    # ── Free-form county name input ───────────────────────────────────────────
    from src.config import CALIFORNIA_COUNTIES
    for known_county in CALIFORNIA_COUNTIES:
        if known_county.lower() in text_lower:
            return {
                **state,
                "county": known_county,
                "county_confirmed": False,
                "step": "confirm_county",
                "response": (
                    f"Got it — looking at **{known_county} County**. "
                    f"Is that correct? *(yes / no)*"
                ),
            }

    # ── Unrecognised input ────────────────────────────────────────────────────
    if state.get("step") == "confirm_county" and state.get("county"):
        return {
            **state,
            "step": "confirm_county",
            "response": (
                f"I didn't catch that. Is **{state['county']} County** correct? "
                f"Please reply *yes* or *no*."
            ),
        }

    return {
        **state,
        "step": "ask_zip",
        "response": (
            "Please enter your 5-digit California ZIP code "
            "(e.g. **94103** for San Francisco)."
        ),
    }


def node_show_programs(state: ConversationState) -> ConversationState:
    """Retrieve programs for the confirmed county and format the response."""
    county = state.get("county", "")
    programs = retrieve_programs(county)
    return {
        **state,
        "programs": programs,
        "step": "done",
        "response": _format_programs(county, programs),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Graph assembly
# ─────────────────────────────────────────────────────────────────────────────

def _build_graph():
    from langgraph.graph import StateGraph, END

    graph = StateGraph(ConversationState)
    graph.add_node("parse_input", node_parse_input)
    graph.add_node("show_programs", node_show_programs)

    graph.set_entry_point("parse_input")

    graph.add_conditional_edges(
        "parse_input",
        lambda s: s["step"],
        {
            "ask_zip":       END,        # wait for user to re-enter ZIP
            "confirm_county": END,       # wait for yes/no
            "show_programs": "show_programs",
            "done":          END,
            "error":         END,
        },
    )
    graph.add_edge("show_programs", END)

    return graph.compile()


# Lazy-initialised singleton — only built when first needed
_app = None

def _get_app():
    global _app
    if _app is None:
        _app = _build_graph()
    return _app


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def chat(
    user_input: str,
    state: Optional[ConversationState] = None,
) -> tuple[str, ConversationState]:
    """
    Single-turn entry point.

    Args:
        user_input : the user's latest message
        state      : current conversation state (pass None to start fresh)

    Returns:
        (response_text, updated_state)

    The returned state is JSON-serializable and can be stored between turns
    in a session cookie, Redis, or any key-value store.
    """
    if state is None:
        state = initial_state()

    state = {**state, "user_input": user_input}
    new_state: ConversationState = _get_app().invoke(state)
    return new_state["response"], new_state


# ─────────────────────────────────────────────────────────────────────────────
# CLI — interactive REPL for manual testing
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    print("\n" + "="*60)
    print("iTREDS Maternal Health Program Finder")
    print("Type your ZIP code to get started. Ctrl+C to quit.")
    print("="*60 + "\n")

    state = initial_state()
    print(f"Bot: {state['response']}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        response, state = chat(user_input, state)
        print(f"\nBot: {response}\n")

        if state["step"] == "done":
            print("-"*60)
            restart = input("Search again? (yes / no): ").strip().lower()
            if restart in ("yes", "y"):
                state = initial_state()
                print(f"\nBot: {state['response']}\n")
            else:
                print("Goodbye.")
                break


if __name__ == "__main__":
    _cli()
