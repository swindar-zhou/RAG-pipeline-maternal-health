"""
Gap Detector for Federal Program Registry
==========================================
iTREDS Project - Identifies programs that appear on county websites
but are not yet captured in federal_program_registry.py.

THREE SIGNAL TYPES:
  Signal 1 - Unmatched extractions: LLM found a program the registry doesn't know about
  Signal 2 - Alias misses:          Registry knows the program but alias set missed it
  Signal 3 - LLM/alias disagreement: LLM found something alias matcher didn't flag

USAGE:
  detector = GapDetector(state_code="CA")

  # After running Phase 1 (discovery):
  detector.record_page_text(county="San Diego", url="...", text="...")

  # After running Phase 3 (structuring):
  detector.record_extraction(county="San Diego", url="...", extracted_name="Centering Pregnancy",
                             extracted_services=["group prenatal care", "prenatal education"],
                             alias_matched_id=None)

  # Generate gap report:
  report = detector.build_gap_report()
  report.print_summary()
  report.export_candidates("data/gap_candidates.jsonl")

  # Or run against existing pipeline output without re-scraping:
  from eval.gap_detector import run_gap_analysis_from_pipeline_output
  run_gap_analysis_from_pipeline_output(
      structured_csv_dir="data/structured",
      raw_json_dir="data/raw",
      state_code="CA",
  )
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.federal_program_registry import (
    FEDERAL_PROGRAM_REGISTRY,
    FederalProgram,
    get_aliases_flat,
    get_applicable_programs,
)


# =============================================================================
# Data structures
# =============================================================================

@dataclass
class GapCandidate:
    """A program extracted from county pages that has no registry match."""
    extracted_name: str           # What the LLM or scraper called it
    signal_type: str              # "unmatched_extraction" | "alias_miss" | "llm_alias_disagreement"
    counties: List[str]           # Which counties surfaced this
    source_urls: List[str]        # Where it was found
    sample_text: str              # Representative text from page (<=300 chars)
    extracted_services: List[str] # Services the LLM extracted
    semantic_match: Optional[str] # Closest registry program_id by semantic similarity
    semantic_score: float         # 0.0-1.0; >0.6 = likely alias miss, <0.4 = likely novel
    frequency: int                # How many county pages mention this
    gap_score: float              # Composite signal score (0-1); higher = more worth adding

    @property
    def signal_label(self) -> str:
        if self.semantic_score >= 0.65:
            return "ALIAS MISS - add alias to existing program"
        elif self.semantic_score >= 0.40:
            return "VARIANT - may need new Tier 3 entry or alias expansion"
        else:
            return "NOVEL - likely new registry entry needed"

    def to_dict(self) -> dict:
        return {
            "extracted_name": self.extracted_name,
            "signal_type": self.signal_type,
            "signal_label": self.signal_label,
            "gap_score": round(self.gap_score, 3),
            "frequency": self.frequency,
            "counties": self.counties,
            "semantic_match": self.semantic_match,
            "semantic_score": round(self.semantic_score, 3),
            "sample_text": self.sample_text,
            "extracted_services": self.extracted_services,
            "source_urls": self.source_urls,
        }


@dataclass
class AbsenceRecord:
    """
    Tracks cases where the alias matcher said 'absent' but page text
    contains semantically relevant content - indicating an alias miss.
    """
    program_id: str          # Registry program that was supposedly absent
    county: str
    url: str
    matching_text: str       # Text segment that semantically resembles the program
    semantic_score: float


@dataclass
class GapReport:
    state_code: str
    counties_scanned: int
    total_extractions: int
    matched_extractions: int
    candidates: List[GapCandidate]
    absence_signals: List[AbsenceRecord]

    @property
    def unmatched_rate(self) -> float:
        if self.total_extractions == 0:
            return 0.0
        return (self.total_extractions - self.matched_extractions) / self.total_extractions

    def print_summary(self):
        print(f"\n{'='*64}")
        print(f"GAP DETECTION REPORT - {self.state_code}")
        print(f"{'='*64}")
        print(f"  Counties scanned:      {self.counties_scanned}")
        print(f"  Total extractions:     {self.total_extractions}")
        print(f"  Matched to registry:   {self.matched_extractions}")
        print(f"  Unmatched rate:        {self.unmatched_rate:.1%}")
        print(f"  Gap candidates:        {len(self.candidates)}")
        print(f"  Alias miss signals:    {len(self.absence_signals)}")

        if self.candidates:
            print(f"\n  TOP GAP CANDIDATES (by gap_score):")
            for c in sorted(self.candidates, key=lambda x: x.gap_score, reverse=True)[:10]:
                print(f"\n    [{c.gap_score:.2f}] {c.extracted_name}")
                print(f"           Signal:  {c.signal_label}")
                print(f"           Found in {c.frequency} pages across: {', '.join(c.counties[:4])}")
                if c.semantic_match:
                    print(f"           Closest registry match: {c.semantic_match} "
                          f"(similarity: {c.semantic_score:.2f})")
                print(f"           Sample: \"{c.sample_text[:120]}...\"")

        if self.absence_signals:
            print(f"\n  TOP ALIAS MISS SIGNALS:")
            by_prog: Dict[str, List[AbsenceRecord]] = defaultdict(list)
            for rec in self.absence_signals:
                by_prog[rec.program_id].append(rec)
            for prog_id, recs in sorted(by_prog.items(), key=lambda x: -len(x[1]))[:5]:
                print(f"\n    {prog_id} - alias matcher said absent in {len(recs)} counties "
                      f"but page text suggests presence")
                print(f"      Sample text: \"{recs[0].matching_text[:120]}\"")

    def export_candidates(self, path: str):
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            for c in self.candidates:
                f.write(json.dumps(c.to_dict()) + "\n")
        print(f"  Exported {len(self.candidates)} gap candidates -> {out}")

    def export_alias_suggestions(self, path: str):
        """
        Exports a ready-to-paste alias expansion dict.
        For each alias-miss candidate, suggests which program_id to add the alias to.
        """
        suggestions: Dict[str, List[str]] = defaultdict(list)
        for c in self.candidates:
            if c.semantic_match and c.semantic_score >= 0.65:
                suggestions[c.semantic_match].append(c.extracted_name)
        for rec in self.absence_signals:
            if rec.semantic_score >= 0.65:
                suggestions[rec.program_id].append(rec.matching_text[:60].strip())

        out = Path(path)
        with open(out, "w") as f:
            json.dump(
                {k: list(set(v)) for k, v in suggestions.items()},
                f, indent=2
            )
        print(f"  Exported alias suggestions -> {out}")


# =============================================================================
# Lightweight semantic similarity (no GPU, no OpenAI call)
# Uses TF-IDF cosine similarity over program descriptions
# =============================================================================

def _build_program_corpus(programs: List[FederalProgram]) -> Tuple[List[str], List[str]]:
    """Build (program_ids, text_documents) for TF-IDF fitting."""
    ids, docs = [], []
    for p in programs:
        ids.append(p.program_id)
        doc = " ".join([
            p.canonical_name,
            p.acronym,
            p.target_population,
            " ".join(p.core_services),
            " ".join(p.county_aliases),
        ]).lower()
        docs.append(doc)
    return ids, docs


def _cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    """Cosine similarity between two TF-IDF sparse dicts."""
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] for k in common)
    norm_a = sum(v ** 2 for v in vec_a.values()) ** 0.5
    norm_b = sum(v ** 2 for v in vec_b.values()) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _tfidf_vectorize(text: str, idf: dict) -> dict:
    """Produce a TF-IDF vector for a single text string."""
    tokens = re.findall(r"[a-z]{3,}", text.lower())
    if not tokens:
        return {}
    tf: Dict[str, float] = defaultdict(float)
    for t in tokens:
        tf[t] += 1
    n = len(tokens)
    return {t: (count / n) * idf.get(t, 0.0) for t, count in tf.items()}


def _build_idf(docs: List[str]) -> dict:
    import math
    n = len(docs)
    df: Dict[str, int] = defaultdict(int)
    for doc in docs:
        for token in set(re.findall(r"[a-z]{3,}", doc)):
            df[token] += 1
    return {t: math.log((n + 1) / (count + 1)) + 1 for t, count in df.items()}


class SemanticMatcher:
    """Matches arbitrary text to registry programs using TF-IDF cosine similarity."""

    def __init__(self, programs: List[FederalProgram]):
        self.programs = programs
        self.prog_ids, docs = _build_program_corpus(programs)
        self.idf = _build_idf(docs)
        self.prog_vectors = [_tfidf_vectorize(doc, self.idf) for doc in docs]

    def best_match(self, text: str, threshold: float = 0.20) -> Tuple[Optional[str], float]:
        """
        Returns (program_id, score) for the best matching registry program.
        Returns (None, 0.0) if no match exceeds threshold.
        """
        query_vec = _tfidf_vectorize(text, self.idf)
        if not query_vec:
            return None, 0.0
        scores = [
            _cosine_similarity(query_vec, pv) for pv in self.prog_vectors
        ]
        best_idx = max(range(len(scores)), key=lambda i: scores[i])
        best_score = scores[best_idx]
        if best_score < threshold:
            return None, best_score
        return self.prog_ids[best_idx], best_score

    def scan_for_program(
        self, page_text: str, program_id: str, threshold: float = 0.35
    ) -> Tuple[str, float]:
        """
        Scan page_text in sliding windows to find the segment most similar
        to a specific program. Used for alias-miss detection.
        Returns (best_matching_segment, score).
        """
        prog_idx = next(
            (i for i, pid in enumerate(self.prog_ids) if pid == program_id), None
        )
        if prog_idx is None:
            return "", 0.0

        prog_vec = self.prog_vectors[prog_idx]
        words = page_text.lower().split()
        window = 60  # words per window
        best_text, best_score = "", 0.0

        for i in range(0, max(1, len(words) - window), window // 2):
            chunk = " ".join(words[i: i + window])
            chunk_vec = _tfidf_vectorize(chunk, self.idf)
            score = _cosine_similarity(chunk_vec, prog_vec)
            if score > best_score:
                best_score = score
                best_text = chunk

        if best_score < threshold:
            return "", 0.0
        return best_text[:300], best_score


# =============================================================================
# Main detector class
# =============================================================================

class GapDetector:
    """
    Collects extraction events from the pipeline and identifies
    programs not yet captured in the registry.

    Intended integration points:
      - After Phase 1 (discovery): call record_page_text() for each fetched page
      - After Phase 3 (structuring): call record_extraction() for each LLM output
      - At analysis time: call build_gap_report()
    """

    def __init__(self, state_code: str):
        self.state_code = state_code
        self.applicable_programs = get_applicable_programs(state_code)
        self.alias_map = get_aliases_flat(state_code)
        self.matcher = SemanticMatcher(self.applicable_programs)

        # Internal accumulators
        self._page_texts: List[Tuple[str, str, str]] = []  # (county, url, text)
        self._extractions: List[dict] = []                 # raw extraction events
        self._absence_signals: List[AbsenceRecord] = []

    # -- Phase 1 integration ---------------------------------------------------

    def record_page_text(self, county: str, url: str, text: str):
        """
        Call this after Phase 1 fetches a page.
        Stores text for later alias-miss scanning.
        """
        self._page_texts.append((county, url, text))

    # -- Phase 3 integration ---------------------------------------------------

    def record_extraction(
        self,
        county: str,
        url: str,
        extracted_name: str,
        extracted_services: List[str],
        alias_matched_id: Optional[str] = None,
        sample_text: str = "",
    ):
        """
        Call this after Phase 3 extracts a program from a county page.

        If alias_matched_id is None, the extraction is a gap candidate.
        If alias_matched_id is set but doesn't match what the LLM found, that's
        a signal 3 (LLM/alias disagreement).
        """
        combined_text = extracted_name + " " + " ".join(extracted_services)
        sem_match, sem_score = self.matcher.best_match(combined_text)

        if alias_matched_id is None:
            signal_type = "unmatched_extraction"
        elif sem_match and sem_match != alias_matched_id:
            signal_type = "llm_alias_disagreement"
        else:
            signal_type = "matched"

        self._extractions.append({
            "county": county,
            "url": url,
            "extracted_name": extracted_name,
            "extracted_services": extracted_services,
            "alias_matched_id": alias_matched_id,
            "semantic_match": sem_match,
            "semantic_score": sem_score,
            "signal_type": signal_type,
            "sample_text": sample_text[:300],
        })

    # -- Alias-miss scanning ---------------------------------------------------

    def scan_for_alias_misses(
        self,
        absent_program_ids: List[str],
        semantic_threshold: float = 0.38,
    ):
        """
        For programs the alias matcher marked 'absent' in a county,
        scan the page text semantically to check if the content is actually there.
        """
        for county, url, text in self._page_texts:
            for prog_id in absent_program_ids:
                segment, score = self.matcher.scan_for_program(
                    text, prog_id, threshold=semantic_threshold
                )
                if segment:
                    self._absence_signals.append(AbsenceRecord(
                        program_id=prog_id,
                        county=county,
                        url=url,
                        matching_text=segment,
                        semantic_score=score,
                    ))

    # -- Report generation -----------------------------------------------------

    def build_gap_report(self) -> GapReport:
        """Aggregate all signals into a ranked GapReport."""
        gap_events = [e for e in self._extractions if e["signal_type"] != "matched"]
        matched_count = len(self._extractions) - len(gap_events)

        grouped: Dict[str, List[dict]] = defaultdict(list)
        for e in gap_events:
            key = _normalize_name(e["extracted_name"])
            grouped[key].append(e)

        candidates: List[GapCandidate] = []
        all_counties = set(e["county"] for e in self._extractions)

        for norm_name, events in grouped.items():
            counties = list({e["county"] for e in events})
            urls = list({e["url"] for e in events})
            frequency = len(events)

            best_sem_match = max(events, key=lambda e: e["semantic_score"])
            sem_match = best_sem_match["semantic_match"]
            sem_score = best_sem_match["semantic_score"]

            sample = next((e["sample_text"] for e in events if e["sample_text"]), "")

            import math
            spread = min(len(counties) / max(len(all_counties), 1), 1.0) * 0.4
            freq_score = min(math.log1p(frequency) / math.log1p(20), 1.0) * 0.3
            novelty = (1.0 - min(sem_score, 1.0)) * 0.3
            gap_score = spread + freq_score + novelty

            sig_counts: Dict[str, int] = defaultdict(int)
            for e in events:
                sig_counts[e["signal_type"]] += 1
            dominant_signal = max(sig_counts, key=sig_counts.get)

            all_services: List[str] = []
            for e in events:
                all_services.extend(e.get("extracted_services", []))
            unique_services = list(dict.fromkeys(all_services))[:6]

            candidates.append(GapCandidate(
                extracted_name=events[0]["extracted_name"],
                signal_type=dominant_signal,
                counties=counties,
                source_urls=urls[:5],
                sample_text=sample,
                extracted_services=unique_services,
                semantic_match=sem_match,
                semantic_score=sem_score,
                frequency=frequency,
                gap_score=gap_score,
            ))

        return GapReport(
            state_code=self.state_code,
            counties_scanned=len(set(e["county"] for e in self._extractions)),
            total_extractions=len(self._extractions),
            matched_extractions=matched_count,
            candidates=sorted(candidates, key=lambda c: c.gap_score, reverse=True),
            absence_signals=self._absence_signals,
        )


# =============================================================================
# Utilities
# =============================================================================

def _normalize_name(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace for grouping."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name


def run_gap_analysis_from_pipeline_output(
    structured_csv_dir: str = "data/structured",
    raw_json_dir: str = "data/raw",
    state_code: str = "CA",
    output_dir: str = "data/gap_analysis",
) -> GapReport:
    """
    Convenience function: runs gap detection over existing pipeline output
    without re-scraping. Reads Phase 2 raw JSON files and Phase 3 structured CSVs.

    Produces:
      data/gap_analysis/gap_candidates.jsonl
      data/gap_analysis/alias_suggestions.json
      data/gap_analysis/gap_report.txt
    """
    import csv
    import glob

    detector = GapDetector(state_code=state_code)
    alias_map = get_aliases_flat(state_code)

    # -- Load Phase 2 raw page texts ------------------------------------------
    raw_files = glob.glob(f"{raw_json_dir}/**/*.json", recursive=True)
    for fpath in raw_files:
        with open(fpath) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                continue
        county = data.get("county", Path(fpath).parent.name)
        url = data.get("url", "") or data.get("page_url", "")
        text = data.get("text", "") or data.get("content", "")
        if text:
            detector.record_page_text(county=county, url=url, text=text)

    # -- Load Phase 3 structured extractions ----------------------------------
    csv_files = glob.glob(f"{structured_csv_dir}/**/*.csv", recursive=True)
    for fpath in csv_files:
        county = Path(fpath).stem
        # Strip common filename prefixes to get the county name
        for prefix in ["California_", "_Healthcare_Data"]:
            county = county.replace(prefix, "")
        county = county.replace("_", " ").strip()

        with open(fpath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                prog_name = row.get("Program_Name", "") or row.get("program_name", "")
                services_raw = row.get("Services", "") or row.get("services_provided", "")
                url = row.get("Program_Website_URL", "") or row.get("program_website_url", "")
                sample = row.get("Program_Description", "") or row.get("program_description", "")

                if not prog_name:
                    continue

                services = [s.strip() for s in services_raw.split(";") if s.strip()]

                # Check alias match
                norm = _normalize_name(prog_name)
                alias_match = alias_map.get(norm)
                if alias_match is None:
                    alias_match = next(
                        (pid for alias, pid in alias_map.items() if alias in norm or norm in alias),
                        None
                    )

                detector.record_extraction(
                    county=county,
                    url=url,
                    extracted_name=prog_name,
                    extracted_services=services,
                    alias_matched_id=alias_match,
                    sample_text=sample,
                )

    # -- Scan for alias misses on absent programs -----------------------------
    applicable_ids = [p.program_id for p in get_applicable_programs(state_code)]
    matched_ids = {
        e["alias_matched_id"]
        for e in detector._extractions
        if e["alias_matched_id"] is not None
    }
    absent_ids = [pid for pid in applicable_ids if pid not in matched_ids]
    detector.scan_for_alias_misses(absent_program_ids=absent_ids)

    # -- Build and export report ----------------------------------------------
    report = detector.build_gap_report()
    report.print_summary()

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    report.export_candidates(str(out / "gap_candidates.jsonl"))
    report.export_alias_suggestions(str(out / "alias_suggestions.json"))

    with open(out / "gap_report.txt", "w") as f:
        import sys
        old_stdout = sys.stdout
        sys.stdout = f
        report.print_summary()
        sys.stdout = old_stdout

    print(f"  Gap report saved -> {out / 'gap_report.txt'}")
    return report


# =============================================================================
# CLI entry point
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Detect registry gaps from pipeline output")
    parser.add_argument("--state", default="CA", choices=["CA", "IN", "TX"],
                        help="State code to run gap analysis for")
    parser.add_argument("--structured-dir", default="data/structured",
                        help="Path to Phase 3 CSV output directory")
    parser.add_argument("--raw-dir", default="data/raw",
                        help="Path to Phase 2 raw JSON directory")
    parser.add_argument("--output-dir", default="data/gap_analysis",
                        help="Where to write gap analysis outputs")
    args = parser.parse_args()

    run_gap_analysis_from_pipeline_output(
        structured_csv_dir=args.structured_dir,
        raw_json_dir=args.raw_dir,
        state_code=args.state,
        output_dir=args.output_dir,
    )
