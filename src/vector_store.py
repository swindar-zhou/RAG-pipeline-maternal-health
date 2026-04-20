"""
Per-county ChromaDB vector stores for the ZIP → programs RAG pipeline.

Reads Phase 2 raw JSON files (data/raw/{county}/*.json), chunks the page
text, embeds with text-embedding-3-small, and persists one ChromaDB
collection per county to data/vectorstore/{county}/.

USAGE
  # Build all counties that have raw data:
  python -m src.vector_store

  # Build specific counties:
  python -m src.vector_store --counties "San Francisco,Sacramento,Los Angeles"

  # Force rebuild even if collection exists:
  python -m src.vector_store --counties "San Francisco" --force

REQUIRES
  pip install -r requirements-langchain.txt
  OPENAI_API_KEY must be set in .env or environment
"""

from __future__ import annotations

import glob
import json
import os
from typing import Dict, List, Optional

from src.config import CALIFORNIA_COUNTIES

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

EMBED_MODEL     = "text-embedding-3-small"
VECTORSTORE_DIR = os.path.join("data", "vectorstore")
RAW_DIR         = os.path.join("data", "raw")

CHUNK_SIZE      = 800
CHUNK_OVERLAP   = 100

# Minimum text length to bother embedding a chunk
MIN_CHUNK_CHARS = 80


# ─────────────────────────────────────────────────────────────────────────────
# Naming helpers
# ─────────────────────────────────────────────────────────────────────────────

def county_to_collection_name(county: str) -> str:
    """'San Francisco' → 'county_san_francisco'"""
    return "county_" + county.lower().replace(" ", "_").replace("-", "_")


def vectorstore_path(county: str) -> str:
    return os.path.join(VECTORSTORE_DIR, county.lower().replace(" ", "_"))


def vectorstore_exists(county: str) -> bool:
    """True if a persisted ChromaDB collection already exists for this county."""
    path = vectorstore_path(county)
    # ChromaDB creates a chroma.sqlite3 file when a collection is persisted
    return os.path.isfile(os.path.join(path, "chroma.sqlite3"))


# ─────────────────────────────────────────────────────────────────────────────
# Raw JSON → LangChain Documents
# ─────────────────────────────────────────────────────────────────────────────

def _slugify_for_path(text: str) -> str:
    import re
    s = re.sub(r'[^a-zA-Z0-9]+', '-', (text or "").strip().lower())
    return s.strip('-')[:60] or "item"


def _load_raw_records(county: str, raw_dir: str = RAW_DIR) -> List[Dict]:
    """Load all Phase 2 raw JSON files for a county."""
    county_dir = os.path.join(raw_dir, _slugify_for_path(county))
    if not os.path.isdir(county_dir):
        return []
    records = []
    for path in glob.glob(os.path.join(county_dir, "*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                records.append(json.load(f))
        except Exception:
            pass
    return records


def _records_to_documents(county: str, records: List[Dict]):
    """
    Convert raw Phase 2 records to LangChain Document objects.
    Each record becomes one Document; chunking happens downstream.
    """
    from langchain_core.documents import Document

    docs = []
    for rec in records:
        text = (rec.get("text") or "").strip()
        if len(text) < MIN_CHUNK_CHARS:
            continue

        # Flatten contacts for metadata (must be scalar values for ChromaDB)
        contacts = rec.get("contacts") or {}
        phones = "; ".join(contacts.get("phones") or [])
        emails = "; ".join(contacts.get("emails") or [])

        metadata = {
            "county":           county,
            "page_url":         rec.get("page_url", ""),
            "link_text":        (rec.get("link_text") or "")[:200],
            "scraped_at":       rec.get("scraped_at", ""),
            "registry_signals": "; ".join(rec.get("registry_signals") or []),
            "phones":           phones,
            "emails":           emails,
            "source_depth":     rec.get("source_depth", 0),
        }
        docs.append(Document(page_content=text, metadata=metadata))
    return docs


# ─────────────────────────────────────────────────────────────────────────────
# Build / load a single county's vector store
# ─────────────────────────────────────────────────────────────────────────────

def build_county_vectorstore(
    county: str,
    raw_dir: str = RAW_DIR,
    force_rebuild: bool = False,
):
    """
    Build (or load) the ChromaDB collection for a single county.

    Returns a Chroma vectorstore instance, or None if there is no raw data.
    Skips rebuild if the collection already exists unless force_rebuild=True.
    """
    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    persist_dir     = vectorstore_path(county)
    collection_name = county_to_collection_name(county)

    # Return existing collection if already built
    if vectorstore_exists(county) and not force_rebuild:
        print(f"  [load]   {county} — existing collection at {persist_dir}")
        return Chroma(
            collection_name=collection_name,
            embedding_function=OpenAIEmbeddings(model=EMBED_MODEL),
            persist_directory=persist_dir,
        )

    # Load raw records
    records = _load_raw_records(county, raw_dir)
    if not records:
        print(f"  [skip]   {county} — no raw data in {os.path.join(raw_dir, _slugify_for_path(county))}")
        return None

    docs = _records_to_documents(county, records)
    if not docs:
        print(f"  [skip]   {county} — raw files exist but all too short to embed")
        return None

    # Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)

    # Filter out chunks that are too short after splitting
    chunks = [c for c in chunks if len(c.page_content.strip()) >= MIN_CHUNK_CHARS]

    if not chunks:
        print(f"  [skip]   {county} — no usable chunks after splitting")
        return None

    os.makedirs(persist_dir, exist_ok=True)

    embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
    store = Chroma.from_documents(
        chunks,
        embeddings,
        collection_name=collection_name,
        persist_directory=persist_dir,
    )

    print(f"  [built]  {county} — {len(records)} pages → {len(chunks)} chunks → {persist_dir}")
    return store


# ─────────────────────────────────────────────────────────────────────────────
# Batch builder
# ─────────────────────────────────────────────────────────────────────────────

def build_all_vectorstores(
    counties: Optional[List[str]] = None,
    raw_dir: str = RAW_DIR,
    force_rebuild: bool = False,
) -> Dict[str, object]:
    """
    Build vectorstores for all counties that have raw Phase 2 data.

    Args:
        counties     : list of county names; defaults to all 58 CA counties
        raw_dir      : path to data/raw
        force_rebuild: if True, rebuild even if collection already exists

    Returns:
        dict mapping county name → Chroma instance (or None if skipped)
    """
    if counties is None:
        counties = list(CALIFORNIA_COUNTIES.keys())

    os.makedirs(VECTORSTORE_DIR, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Building vectorstores  ({len(counties)} counties)")
    print(f"  embed model : {EMBED_MODEL}")
    print(f"  chunk size  : {CHUNK_SIZE}  overlap: {CHUNK_OVERLAP}")
    print(f"  persist dir : {VECTORSTORE_DIR}")
    print(f"{'='*60}\n")

    results: Dict[str, object] = {}
    built = skipped = loaded = 0

    for county in counties:
        store = build_county_vectorstore(county, raw_dir, force_rebuild)
        results[county] = store
        if store is None:
            skipped += 1
        elif vectorstore_exists(county) and not force_rebuild:
            loaded += 1
        else:
            built += 1

    print(f"\n{'─'*60}")
    print(f"  Built:   {built}")
    print(f"  Loaded:  {loaded}  (already existed)")
    print(f"  Skipped: {skipped}  (no raw data)")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Retriever factory — used by knowledge_graph.py
# ─────────────────────────────────────────────────────────────────────────────

def get_county_vectorstore(county: str):
    """
    Load an existing county vectorstore.
    Returns None (with a warning) if the collection hasn't been built yet.
    """
    if not vectorstore_exists(county):
        print(f"  [warn] No vectorstore for '{county}'. Run build_all_vectorstores() first.")
        return None

    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma

    return Chroma(
        collection_name=county_to_collection_name(county),
        embedding_function=OpenAIEmbeddings(model=EMBED_MODEL),
        persist_directory=vectorstore_path(county),
    )


def get_county_retriever(county: str, k: int = 8):
    """
    Return a LangChain retriever for a county's vectorstore.

    Args:
        county : county name (e.g. 'San Francisco')
        k      : number of chunks to retrieve per query

    Returns:
        A LangChain BaseRetriever, or None if no store exists.
    """
    store = get_county_vectorstore(county)
    if store is None:
        return None
    return store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: list counties that have a built vectorstore
# ─────────────────────────────────────────────────────────────────────────────

def list_built_counties() -> List[str]:
    """Return county names for which a persisted vectorstore exists."""
    if not os.path.isdir(VECTORSTORE_DIR):
        return []
    return [
        d.replace("_", " ").title()
        for d in os.listdir(VECTORSTORE_DIR)
        if os.path.isfile(os.path.join(VECTORSTORE_DIR, d, "chroma.sqlite3"))
    ]


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _parse_args():
    import argparse
    p = argparse.ArgumentParser(description="Build per-county ChromaDB vectorstores")
    p.add_argument(
        "--counties",
        type=str,
        default=None,
        help="Comma-separated county names (default: all counties with raw data)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Rebuild even if vectorstore already exists",
    )
    p.add_argument(
        "--list",
        action="store_true",
        help="List counties that already have a built vectorstore and exit",
    )
    return p.parse_args()


def main():
    args = _parse_args()

    if args.list:
        built = list_built_counties()
        if built:
            print(f"Built vectorstores ({len(built)}):")
            for c in sorted(built):
                print(f"  {c}")
        else:
            print("No vectorstores built yet.")
        return

    counties = None
    if args.counties:
        counties = [c.strip() for c in args.counties.split(",") if c.strip()]

    build_all_vectorstores(counties=counties, force_rebuild=args.force)


if __name__ == "__main__":
    main()
