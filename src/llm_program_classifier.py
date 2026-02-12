"""
LLM-based maternal program classifier.

This classifier learns category assignments from program descriptions using
in-context examples derived from the maternal taxonomy.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from .config import OPENAI_MODEL, TEMPERATURE
from .maternal_taxonomy import MATERNAL_PROGRAM_TYPES, ProgramType, classify_program


@dataclass
class ProgramClassification:
    """Structured output from LLM category classification."""

    program_name: str
    program_category: str
    program_type: str
    sdoh_domain: str
    blueprint_goal: str
    confidence: float
    rationale: str


class LLMProgramClassifier:
    """
    LLM-backed classifier that predicts maternal program categories from text.

    Fallback behavior:
    - If no API key or model failure, falls back to keyword taxonomy classification.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = TEMPERATURE,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or OPENAI_MODEL
        self.temperature = temperature
        self._program_types = MATERNAL_PROGRAM_TYPES

    def _category_profiles(self) -> str:
        """Create compact category descriptions for prompt grounding."""
        by_category: Dict[str, List[ProgramType]] = {}
        for pt in self._program_types:
            by_category.setdefault(pt.category, []).append(pt)

        lines: List[str] = []
        for category in sorted(by_category):
            pts = by_category[category]
            type_names = ", ".join(sorted({p.name for p in pts})[:4])
            sdoh = sorted({p.sdoh_domain.value for p in pts})[0]
            goal = sorted({p.blueprint_goal.value for p in pts})[0]
            lines.append(
                f"- {category}: {type_names}. "
                f"SDOH={sdoh}. Blueprint={goal}."
            )
        return "\n".join(lines)

    def _few_shot_examples(self) -> str:
        """Build lightweight training examples from taxonomy descriptions."""
        examples: List[str] = []
        used_categories = set()

        for pt in self._program_types:
            if pt.category in used_categories:
                continue
            used_categories.add(pt.category)
            program_title = pt.examples[0] if pt.examples else pt.name
            examples.append(
                (
                    f'Input: name="{program_title}", description="{pt.description}"\n'
                    f'Output: {{"program_category":"{pt.category}","program_type":"{pt.name}",'
                    f'"sdoh_domain":"{pt.sdoh_domain.value}",'
                    f'"blueprint_goal":"{pt.blueprint_goal.value}","confidence":0.90}}'
                )
            )
        return "\n\n".join(examples)

    def _build_prompt(self, programs: List[Dict]) -> str:
        categories = sorted({pt.category for pt in self._program_types})
        taxonomy_names = sorted({pt.name for pt in self._program_types})
        category_profiles = self._category_profiles()
        few_shot = self._few_shot_examples()
        return f"""You are a maternal health program classifier.

Task:
Classify each program based primarily on its description and services.
Use category meaning and context, not only keyword overlap.

Allowed program_category values:
{", ".join(categories)}

Allowed program_type values:
{", ".join(taxonomy_names)}

Category profiles:
{category_profiles}

Training examples:
{few_shot}

Programs to classify:
{json.dumps(programs, ensure_ascii=False)}

Return ONLY valid JSON with this schema:
{{
  "classifications": [
    {{
      "program_name": "string",
      "program_category": "one of allowed categories",
      "program_type": "one of allowed program_type values",
      "sdoh_domain": "string",
      "blueprint_goal": "string",
      "confidence": 0.0,
      "rationale": "short explanation"
    }}
  ]
}}
"""

    @staticmethod
    def _safe_parse_json(content: str) -> Optional[Dict]:
        """Parse assistant content that may include fenced code."""
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

    def _fallback_classify(self, programs: List[Dict]) -> List[ProgramClassification]:
        """Keyword-based fallback when LLM cannot run."""
        out: List[ProgramClassification] = []
        for program in programs:
            name = str(program.get("program_name", "")).strip()
            desc = str(program.get("program_description", "")).strip()
            services = program.get("services_provided", [])
            service_text = " ".join(services) if isinstance(services, list) else str(services)
            combined = f"{name}. {desc}. {service_text}"

            # Prefer strong name/example matches before broader keyword scoring.
            combined_lower = combined.lower()
            best_pt: Optional[ProgramType] = None
            best_score = 0
            for candidate in self._program_types:
                score = 0
                name_tokens = candidate.name.lower()
                if name_tokens in combined_lower:
                    score += 8
                for ex in candidate.examples:
                    if ex.lower() in combined_lower:
                        score += 7
                for kw in candidate.keywords:
                    if kw in combined_lower:
                        score += max(1, len(kw.split()))
                if score > best_score:
                    best_score = score
                    best_pt = candidate

            pt = best_pt if best_pt and best_score > 0 else classify_program(combined)
            if pt:
                out.append(
                    ProgramClassification(
                        program_name=name,
                        program_category=pt.category,
                        program_type=pt.name,
                        sdoh_domain=pt.sdoh_domain.value,
                        blueprint_goal=pt.blueprint_goal.value,
                        confidence=0.65,
                        rationale="Keyword fallback classification.",
                    )
                )
            else:
                out.append(
                    ProgramClassification(
                        program_name=name,
                        program_category="Other",
                        program_type="Unknown",
                        sdoh_domain="Unknown",
                        blueprint_goal="Unknown",
                        confidence=0.30,
                        rationale="Insufficient signals for taxonomy match.",
                    )
                )
        return out

    def classify_programs(self, programs: List[Dict]) -> List[ProgramClassification]:
        """Classify program records based on descriptions."""
        if not programs:
            return []
        if not self.api_key:
            return self._fallback_classify(programs)

        prompt = self._build_prompt(programs)

        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a careful classifier. Use the provided taxonomy. "
                            "Return JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1200,
            )
            content = (response.choices[0].message.content or "").strip()
            payload = self._safe_parse_json(content)
            if not payload or "classifications" not in payload:
                return self._fallback_classify(programs)

            allowed_categories = {pt.category for pt in self._program_types}
            name_to_pt = {pt.name: pt for pt in self._program_types}
            out: List[ProgramClassification] = []

            for row in payload.get("classifications", []):
                program_name = str(row.get("program_name", "")).strip()
                category = str(row.get("program_category", "Other")).strip()
                program_type = str(row.get("program_type", "Unknown")).strip()
                confidence_raw = row.get("confidence", 0.0)
                rationale = str(row.get("rationale", "")).strip()

                try:
                    confidence = float(confidence_raw)
                except (TypeError, ValueError):
                    confidence = 0.0
                confidence = max(0.0, min(1.0, confidence))

                if category not in allowed_categories:
                    category = "Other"
                if program_type not in name_to_pt:
                    program_type = "Unknown"

                if program_type in name_to_pt:
                    pt = name_to_pt[program_type]
                    sdoh_domain = pt.sdoh_domain.value
                    blueprint_goal = pt.blueprint_goal.value
                    if category == "Other":
                        category = pt.category
                else:
                    sdoh_domain = str(row.get("sdoh_domain", "Unknown")).strip() or "Unknown"
                    blueprint_goal = (
                        str(row.get("blueprint_goal", "Unknown")).strip() or "Unknown"
                    )

                out.append(
                    ProgramClassification(
                        program_name=program_name,
                        program_category=category,
                        program_type=program_type,
                        sdoh_domain=sdoh_domain,
                        blueprint_goal=blueprint_goal,
                        confidence=confidence,
                        rationale=rationale,
                    )
                )

            if not out:
                return self._fallback_classify(programs)
            return out
        except Exception:
            return self._fallback_classify(programs)
