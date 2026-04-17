"""
iTREDS Maternal Health — Comprehensive Benchmark Suite
=======================================================

Evaluates every component built so far against the gold standard and
compares scraper versions (v1–v4) on defined metrics.

Metric methodology — borrowed from:

  1. SQuAD (Rajpurkar et al., 2016) — token-F1 and Exact Match for
     extraction quality. Token-F1 is the harmonic mean of token-level
     precision and recall between the extracted text and the gold answer,
     after lowercasing and stripping punctuation.

  2. BEIR (Thakur et al., 2021) — Recall@K and NDCG@K for retrieval.
     We apply Recall@K to program discovery: of the K programs returned
     by the pipeline, what fraction of gold-standard programs are covered?

  3. RAGAS (Es et al., 2023) — Context Recall (CR) and Answer Recall (AR)
     for RAG pipelines. We adapt:
       Context Recall  = |gold program terms in retrieved chunks| / |gold program terms|
       Answer Recall   = |gold program names in chatbot response| / |gold program names|
     Both use token-F1 ≥ 0.5 as the match threshold.

  4. KILT (Petroni et al., 2021) — end-to-end recall for knowledge-
     intensive tasks. Here: does the knowledge graph return the right
     programs when given a county name directly?

WHAT IS TESTED (no API calls required for benchmarks 1–4)
  B1. Version regression  — program count per gold county v1→v4
  B2. Program Recall@K    — BEIR-style, K ∈ {5, 10, 20} vs gold programs
  B3. Extraction F1       — SQuAD token-F1 for program name extraction
  B4. Field completeness  — % of critical fields populated across versions
  B5. Knowledge graph     — RAGAS-style Answer Recall on CSV fast path
  B6. ZIP→county accuracy — spot-check known ZIPs (requires pgeocode)

USAGE
  python -m eval.benchmark               # run all benchmarks
  python -m eval.benchmark --bench 1,3   # run specific benchmarks
"""

from __future__ import annotations

import csv
import glob
import json
import os
import re
import string
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

GOLD_PATH      = os.path.join("eval", "gold_maternal.jsonl")
STRUCTURED_DIR = os.path.join("data", "structured")
RAW_DIR        = os.path.join("data", "raw")
RESULTS_DIR    = os.path.join("eval", "results")
VERSIONS       = ["v1", "v2", "v3", "v4"]


# ─────────────────────────────────────────────────────────────────────────────
# SQuAD-style token F1  (Rajpurkar et al., 2016)
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return " ".join(text.split())


def token_f1(pred: str, gold: str) -> float:
    """
    Token-level F1 between pred and gold strings.
    Exact Match (EM) = 1 iff token_f1 == 1.0.
    Ref: SQuAD evaluation script (Rajpurkar et al., 2016).
    """
    pred_tokens = set(_normalize(pred).split())
    gold_tokens = set(_normalize(gold).split())
    if not pred_tokens or not gold_tokens:
        return float(pred_tokens == gold_tokens)
    common = pred_tokens & gold_tokens
    if not common:
        return 0.0
    precision = len(common) / len(pred_tokens)
    recall    = len(common) / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def best_match_f1(candidate: str, gold_list: List[str]) -> Tuple[float, str]:
    """Return (max_f1, best_gold_match) over all gold strings."""
    if not gold_list:
        return 0.0, ""
    scored = [(token_f1(candidate, g), g) for g in gold_list]
    return max(scored, key=lambda x: x[0])


# ─────────────────────────────────────────────────────────────────────────────
# NDCG@K  (BEIR — Thakur et al., 2021)
# ─────────────────────────────────────────────────────────────────────────────

import math

def ndcg_at_k(ranked_relevances: List[int], k: int) -> float:
    """
    Normalised Discounted Cumulative Gain at K.
    ranked_relevances: binary relevance list in rank order (1=relevant, 0=not).
    Ref: BEIR benchmark (Thakur et al., 2021).
    """
    k = min(k, len(ranked_relevances))
    dcg  = sum(r / math.log2(i + 2) for i, r in enumerate(ranked_relevances[:k]))
    # Ideal DCG: all relevant docs first
    ideal = sorted(ranked_relevances, reverse=True)[:k]
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def recall_at_k(retrieved: List[str], gold: List[str], k: int,
                threshold: float = 0.5) -> float:
    """
    Recall@K: fraction of gold items matched in top-K retrieved items
    using token-F1 ≥ threshold as the match criterion.
    Adapted from BEIR Recall@K (Thakur et al., 2021).
    """
    if not gold:
        return 0.0
    top_k = retrieved[:k]
    matched = sum(
        1 for g in gold
        if any(token_f1(r, g) >= threshold for r in top_k)
    )
    return matched / len(gold)


# ─────────────────────────────────────────────────────────────────────────────
# Data loaders
# ─────────────────────────────────────────────────────────────────────────────

def load_gold() -> Dict[str, dict]:
    """Load gold_maternal.jsonl → {county_name: gold_record}."""
    gold = {}
    if not os.path.isfile(GOLD_PATH):
        return gold
    with open(GOLD_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                gold[rec["county_name"]] = rec
    return gold


def load_version_programs(version: str) -> Dict[str, List[Dict]]:
    """Load all county CSVs for a version → {county_name: [program_rows]}."""
    result: Dict[str, List[Dict]] = {}
    pattern = os.path.join(STRUCTURED_DIR, version, "California_*_Healthcare_Data.csv")
    for csv_path in glob.glob(pattern):
        # Skip combined files
        base = os.path.basename(csv_path)
        if "County_Healthcare" in base:
            continue
        rows = []
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("Program_Name", "").strip():
                        rows.append(row)
        except Exception:
            continue
        if rows:
            county = rows[0].get("County_Name", "").strip()
            if county:
                result[county] = rows
    return result


def load_raw_texts(county: str) -> List[str]:
    """Load all Phase 2 raw page texts for a county."""
    slug = re.sub(r'[^a-z0-9]+', '-', county.lower()).strip('-')
    county_dir = os.path.join(RAW_DIR, slug)
    texts = []
    if not os.path.isdir(county_dir):
        return texts
    for p in glob.glob(os.path.join(county_dir, "*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
                t = d.get("text", "")
                if t:
                    texts.append(t)
        except Exception:
            pass
    return texts


# ─────────────────────────────────────────────────────────────────────────────
# B1 — Version regression table
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class B1Result:
    county: str
    counts: Dict[str, int]      # version → program count
    gold_count: int

    def delta(self, v_from: str, v_to: str) -> int:
        return self.counts.get(v_to, 0) - self.counts.get(v_from, 0)


def benchmark_1_version_regression(gold: Dict[str, dict]) -> List[B1Result]:
    """
    B1: Program count per gold county across versions.
    Surfaces regressions (count drops between versions).
    """
    results = []
    for county, gold_rec in gold.items():
        counts = {}
        for v in VERSIONS:
            county_data = load_version_programs(v)
            counts[v] = len(county_data.get(county, []))
        results.append(B1Result(
            county=county,
            counts=counts,
            gold_count=len(gold_rec.get("programs", [])),
        ))
    return results


def print_b1(results: List[B1Result]) -> None:
    print("\n── B1: Version Regression Table ───────────────────────────────────────")
    print(f"  {'County':<20}", end="")
    for v in VERSIONS:
        print(f"  {v:>4}", end="")
    print(f"  {'Gold':>4}  {'v1→v4':>6}  {'Regress?':>8}")
    print("  " + "─" * 64)
    for r in results:
        delta = r.delta("v1", "v4")
        flag = "  ⚠" if any(r.delta(VERSIONS[i], VERSIONS[i+1]) < 0 for i in range(len(VERSIONS)-1)) else ""
        print(f"  {r.county:<20}", end="")
        for v in VERSIONS:
            print(f"  {r.counts[v]:>4}", end="")
        sign = "+" if delta >= 0 else ""
        print(f"  {r.gold_count:>4}  {sign}{delta:>5}  {flag}")
    # Summary
    any_regress = sum(
        1 for r in results
        if any(r.delta(VERSIONS[i], VERSIONS[i+1]) < 0 for i in range(len(VERSIONS)-1))
    )
    print(f"\n  Counties with at least one version regression: {any_regress}/{len(results)}")


# ─────────────────────────────────────────────────────────────────────────────
# B2 — Program Recall@K (BEIR-style)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class B2Result:
    county: str
    version: str
    recall_at_5:  float
    recall_at_10: float
    recall_at_20: float
    ndcg_at_10:   float
    n_extracted:  int
    n_gold:       int


def benchmark_2_recall_at_k(gold: Dict[str, dict]) -> List[B2Result]:
    """
    B2: Recall@K and NDCG@10 for each version vs gold program names.
    Match criterion: token-F1 ≥ 0.5 (SQuAD threshold).
    Methodology: BEIR (Thakur et al., 2021).
    """
    results = []
    for county, gold_rec in gold.items():
        gold_names = [p["program_name"] for p in gold_rec.get("programs", [])]
        if not gold_names:
            continue
        for v in VERSIONS:
            county_data = load_version_programs(v)
            extracted_names = [r.get("Program_Name", "") for r in county_data.get(county, [])]

            # Recall@K
            r5  = recall_at_k(extracted_names, gold_names, k=5)
            r10 = recall_at_k(extracted_names, gold_names, k=10)
            r20 = recall_at_k(extracted_names, gold_names, k=20)

            # NDCG@10 — binary relevance: 1 if extracted name matches any gold at F1≥0.5
            relevances = [
                int(best_match_f1(name, gold_names)[0] >= 0.5)
                for name in extracted_names
            ]
            ndcg10 = ndcg_at_k(relevances, k=10)

            results.append(B2Result(
                county=county,
                version=v,
                recall_at_5=r5,
                recall_at_10=r10,
                recall_at_20=r20,
                ndcg_at_10=ndcg10,
                n_extracted=len(extracted_names),
                n_gold=len(gold_names),
            ))
    return results


def print_b2(results: List[B2Result]) -> None:
    print("\n── B2: Program Recall@K & NDCG@10 (BEIR methodology) ──────────────────")
    print(f"  {'County':<20}  {'Ver':>3}  {'R@5':>5}  {'R@10':>5}  {'R@20':>5}  {'NDCG@10':>7}  {'n_ext':>5}  {'n_gold':>6}")
    print("  " + "─" * 70)
    for r in results:
        print(f"  {r.county:<20}  {r.version:>3}  "
              f"{r.recall_at_5:>5.2f}  {r.recall_at_10:>5.2f}  {r.recall_at_20:>5.2f}  "
              f"{r.ndcg_at_10:>7.3f}  {r.n_extracted:>5}  {r.n_gold:>6}")

    # Macro averages per version
    print()
    for v in VERSIONS:
        vr = [r for r in results if r.version == v]
        if not vr:
            continue
        avg_r20   = sum(r.recall_at_20 for r in vr) / len(vr)
        avg_ndcg  = sum(r.ndcg_at_10   for r in vr) / len(vr)
        print(f"  {v} avg across {len(vr)} counties: Recall@20={avg_r20:.2f}  NDCG@10={avg_ndcg:.3f}")


# ─────────────────────────────────────────────────────────────────────────────
# B3 — Extraction F1  (SQuAD token-F1)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class B3Result:
    county: str
    version: str
    program_name_f1:   float   # avg token-F1 for matched program names
    exact_match_rate:  float   # fraction with token-F1 == 1.0
    n_matched: int
    n_gold: int


def benchmark_3_extraction_f1(gold: Dict[str, dict]) -> List[B3Result]:
    """
    B3: SQuAD-style token-F1 for program name extraction.
    Each gold program is matched to the single best-F1 extracted program.
    Ref: SQuAD evaluation (Rajpurkar et al., 2016).
    """
    results = []
    for county, gold_rec in gold.items():
        gold_programs = gold_rec.get("programs", [])
        gold_names = [p["program_name"] for p in gold_programs]
        if not gold_names:
            continue
        for v in VERSIONS:
            county_data = load_version_programs(v)
            extracted_names = [r.get("Program_Name", "") for r in county_data.get(county, [])]
            if not extracted_names:
                results.append(B3Result(county=county, version=v,
                                        program_name_f1=0.0, exact_match_rate=0.0,
                                        n_matched=0, n_gold=len(gold_names)))
                continue

            f1_scores = []
            em_scores = []
            for gold_name in gold_names:
                best_f1, _ = best_match_f1(gold_name, extracted_names)
                f1_scores.append(best_f1)
                em_scores.append(1 if best_f1 == 1.0 else 0)

            results.append(B3Result(
                county=county,
                version=v,
                program_name_f1=sum(f1_scores) / len(f1_scores),
                exact_match_rate=sum(em_scores) / len(em_scores),
                n_matched=sum(1 for s in f1_scores if s >= 0.5),
                n_gold=len(gold_names),
            ))
    return results


def print_b3(results: List[B3Result]) -> None:
    print("\n── B3: Program Name Extraction F1 (SQuAD token-F1 methodology) ─────────")
    print(f"  {'County':<20}  {'Ver':>3}  {'Name F1':>7}  {'EM rate':>7}  {'Matched':>7}  {'Gold':>4}")
    print("  " + "─" * 60)
    for r in results:
        print(f"  {r.county:<20}  {r.version:>3}  "
              f"{r.program_name_f1:>7.3f}  {r.exact_match_rate:>7.2%}  "
              f"{r.n_matched:>7}  {r.n_gold:>4}")

    # Best version per county
    print()
    counties = list({r.county for r in results})
    for county in sorted(counties):
        county_results = [r for r in results if r.county == county]
        best = max(county_results, key=lambda r: r.program_name_f1)
        print(f"  Best for {county}: {best.version}  (F1={best.program_name_f1:.3f})")


# ─────────────────────────────────────────────────────────────────────────────
# B4 — Field completeness
# ─────────────────────────────────────────────────────────────────────────────

CRITICAL_FIELDS = [
    "Eligibility_Requirements",
    "Application_Process",
    "Program_Description",
    "Program_Website_URL",
    "Target_Population",
]
NOT_FOUND_VALUES = {"not specified", "not found", "n/a", "", "none"}


def _is_populated(value: str) -> bool:
    return value.strip().lower() not in NOT_FOUND_VALUES


@dataclass
class B4Result:
    version: str
    n_programs: int
    field_fill_rates: Dict[str, float]   # field → fill rate across all programs
    critical_complete_rate: float        # % programs with ALL critical fields filled


def benchmark_4_field_completeness() -> List[B4Result]:
    """
    B4: Field completeness across versions — % of programs with each
    critical field populated (not 'Not specified'/'Not found'/empty).
    Measures information extraction completeness.
    """
    results = []
    for v in VERSIONS:
        all_rows = []
        for csv_path in glob.glob(os.path.join(STRUCTURED_DIR, v, "California_*_Healthcare_Data.csv")):
            if "County_Healthcare" in os.path.basename(csv_path):
                continue
            try:
                with open(csv_path, newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        if row.get("Program_Name", "").strip():
                            all_rows.append(row)
            except Exception:
                pass

        if not all_rows:
            continue

        fill_rates = {}
        for field in CRITICAL_FIELDS:
            filled = sum(1 for row in all_rows if _is_populated(row.get(field, "")))
            fill_rates[field] = filled / len(all_rows)

        # All critical fields filled
        all_filled = sum(
            1 for row in all_rows
            if all(_is_populated(row.get(f, "")) for f in CRITICAL_FIELDS)
        )

        results.append(B4Result(
            version=v,
            n_programs=len(all_rows),
            field_fill_rates=fill_rates,
            critical_complete_rate=all_filled / len(all_rows),
        ))
    return results


def print_b4(results: List[B4Result]) -> None:
    short = {
        "Eligibility_Requirements": "Eligibility",
        "Application_Process":      "How_to_Apply",
        "Program_Description":      "Description",
        "Program_Website_URL":      "Website_URL",
        "Target_Population":        "Target_Pop",
    }
    print("\n── B4: Field Completeness Across Versions ──────────────────────────────")
    # Header
    print(f"  {'Ver':>3}  {'N':>5}  ", end="")
    for f in CRITICAL_FIELDS:
        print(f"  {short[f]:>11}", end="")
    print(f"  {'All_Filled':>10}")
    print("  " + "─" * 80)
    for r in results:
        print(f"  {r.version:>3}  {r.n_programs:>5}  ", end="")
        for f in CRITICAL_FIELDS:
            rate = r.field_fill_rates.get(f, 0.0)
            print(f"  {rate:>10.1%}", end="")
        print(f"  {r.critical_complete_rate:>10.1%}")

    # Trend arrow
    if len(results) >= 2:
        first = results[0].critical_complete_rate
        last  = results[-1].critical_complete_rate
        trend = "▲" if last > first else ("▼" if last < first else "─")
        print(f"\n  All-fields complete: {first:.1%} ({results[0].version}) → "
              f"{last:.1%} ({results[-1].version})  {trend}")


# ─────────────────────────────────────────────────────────────────────────────
# B5 — Knowledge graph Answer Recall (RAGAS-style)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class B5Result:
    county: str
    n_gold: int
    n_returned: int
    answer_recall: float        # RAGAS: fraction of gold programs mentioned in response
    answer_precision: float     # fraction of returned programs matching a gold program


def benchmark_5_knowledge_graph(gold: Dict[str, dict]) -> List[B5Result]:
    """
    B5: RAGAS-style Answer Recall for the knowledge graph CSV fast path.
    Answer Recall = |gold programs recalled in response| / |gold programs|
    Answer Precision = |returned programs matching gold| / |returned programs|
    Ref: RAGAS (Es et al., 2023) — Answer Recall metric.
    No LLM calls; uses Phase 3 CSV data via _load_programs_from_csv().
    """
    # Lazy import to avoid dependency on LangChain at module level
    from src.knowledge_graph import (
        _load_programs_from_csv,
        node_parse_input,
        node_show_programs,
        initial_state,
    )

    results = []
    for county, gold_rec in gold.items():
        gold_names = [p["program_name"] for p in gold_rec.get("programs", [])]
        if not gold_names:
            continue

        # Simulate conversation: type county name → confirm → get programs
        state = initial_state()
        state["user_input"] = county
        state = node_parse_input(state)
        state["user_input"] = "yes"
        state = node_parse_input(state)
        if state["step"] == "show_programs":
            state = node_show_programs(state)

        returned_programs = state.get("programs") or []
        returned_names = [p.get("program_name", "") for p in returned_programs
                          if p.get("program_name") != "__rag_raw__"]

        # Answer Recall (RAGAS): gold program recalled if response contains it at F1≥0.5
        recall_hits = sum(
            1 for gn in gold_names
            if any(token_f1(rn, gn) >= 0.5 for rn in returned_names)
        )
        answer_recall = recall_hits / len(gold_names)

        # Answer Precision: returned programs that match any gold
        precision_hits = sum(
            1 for rn in returned_names
            if best_match_f1(rn, gold_names)[0] >= 0.5
        )
        answer_precision = precision_hits / len(returned_names) if returned_names else 0.0

        results.append(B5Result(
            county=county,
            n_gold=len(gold_names),
            n_returned=len(returned_names),
            answer_recall=answer_recall,
            answer_precision=answer_precision,
        ))

    return results


def print_b5(results: List[B5Result]) -> None:
    print("\n── B5: Knowledge Graph Answer Recall (RAGAS methodology) ──────────────")
    print(f"  {'County':<20}  {'Gold':>4}  {'Returned':>8}  {'Recall':>6}  {'Precis':>6}  {'F1':>6}")
    print("  " + "─" * 60)
    for r in results:
        f1 = (2 * r.answer_recall * r.answer_precision / (r.answer_recall + r.answer_precision)
              if r.answer_recall + r.answer_precision > 0 else 0.0)
        print(f"  {r.county:<20}  {r.n_gold:>4}  {r.n_returned:>8}  "
              f"{r.answer_recall:>6.2%}  {r.answer_precision:>6.2%}  {f1:>6.2%}")

    if results:
        avg_recall = sum(r.answer_recall for r in results) / len(results)
        avg_prec   = sum(r.answer_precision for r in results) / len(results)
        avg_f1_val = (2 * avg_recall * avg_prec / (avg_recall + avg_prec)
                      if avg_recall + avg_prec > 0 else 0.0)
        print(f"\n  Macro avg  Recall={avg_recall:.2%}  Precision={avg_prec:.2%}  F1={avg_f1_val:.2%}")
        print(f"\n  Note: B5 uses only Phase 3 CSV data (no LLM calls).")
        print(f"  Low recall here = programs in gold not yet extracted by Phase 3.")
        print(f"  After Phase 2 enhanced + re-run of Phase 3, expect recall to rise.")


# ─────────────────────────────────────────────────────────────────────────────
# B6 — ZIP→county accuracy (requires pgeocode)
# ─────────────────────────────────────────────────────────────────────────────

# Known-correct ZIP→county pairs for California (gold spot-check)
ZIP_GOLD = {
    "94103": "San Francisco",
    "90012": "Los Angeles",
    "95814": "Sacramento",
    "92101": "San Diego",
    "94577": "Alameda",
    "93301": "Kern",
    "93726": "Fresno",
    "95301": "Merced",
    "95482": "Mendocino",
    "96001": "Shasta",
    "95901": "Yuba",
    "96130": "Lassen",
    "93940": "Monterey",
    "93030": "Ventura",
    "95695": "Yolo",
}


def benchmark_6_zip_accuracy() -> Optional[dict]:
    """
    B6: ZIP→county accuracy on 15 known-correct CA ZIP codes.
    Requires pgeocode (offline USPS data).
    Ref: KILT (Petroni et al., 2021) — entity linking accuracy.
    """
    from src.knowledge_graph import zip_to_county
    try:
        import pgeocode  # noqa: F401
    except ImportError:
        return None

    correct = 0
    details = []
    for zip_code, expected in ZIP_GOLD.items():
        got = zip_to_county(zip_code)
        ok = (got or "").lower() == expected.lower()
        correct += int(ok)
        details.append({"zip": zip_code, "expected": expected, "got": got, "ok": ok})

    return {
        "accuracy": correct / len(ZIP_GOLD),
        "n_correct": correct,
        "n_total": len(ZIP_GOLD),
        "details": details,
    }


def print_b6(result: Optional[dict]) -> None:
    print("\n── B6: ZIP→County Accuracy (KILT entity-linking methodology) ──────────")
    if result is None:
        print("  Skipped — pgeocode not installed.")
        print("  Install with: pip install pgeocode")
        return
    print(f"  Accuracy: {result['accuracy']:.1%}  ({result['n_correct']}/{result['n_total']})")
    failures = [d for d in result["details"] if not d["ok"]]
    if failures:
        print(f"\n  Failures ({len(failures)}):")
        for d in failures:
            print(f"    ZIP {d['zip']}  expected={d['expected']}  got={d['got']}")
    else:
        print("  All ZIPs resolved correctly.")


# ─────────────────────────────────────────────────────────────────────────────
# Run ID
# ─────────────────────────────────────────────────────────────────────────────

def _run_id() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        sha = "unknown"
    return f"{ts}_{sha}"


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────

def run_all(bench_filter: Optional[List[int]] = None) -> dict:
    gold = load_gold()
    if not gold:
        print(f"ERROR: gold standard not found at {GOLD_PATH}")
        return {}

    run_id = _run_id()
    print(f"\n{'='*70}")
    print(f"iTREDS Maternal Health Benchmark Suite  |  run_id={run_id}")
    print(f"Gold counties: {list(gold.keys())}")
    print(f"{'='*70}")

    summary = {"run_id": run_id, "timestamp": datetime.now().isoformat()}

    def should_run(n: int) -> bool:
        return bench_filter is None or n in bench_filter

    if should_run(1):
        b1 = benchmark_1_version_regression(gold)
        print_b1(b1)
        summary["B1_version_regression"] = [asdict(r) for r in b1]

    if should_run(2):
        b2 = benchmark_2_recall_at_k(gold)
        print_b2(b2)
        summary["B2_recall_at_k"] = [asdict(r) for r in b2]

    if should_run(3):
        b3 = benchmark_3_extraction_f1(gold)
        print_b3(b3)
        summary["B3_extraction_f1"] = [asdict(r) for r in b3]

    if should_run(4):
        b4 = benchmark_4_field_completeness()
        print_b4(b4)
        summary["B4_field_completeness"] = [asdict(r) for r in b4]

    if should_run(5):
        b5 = benchmark_5_knowledge_graph(gold)
        print_b5(b5)
        summary["B5_knowledge_graph"] = [asdict(r) for r in b5]

    if should_run(6):
        b6 = benchmark_6_zip_accuracy()
        print_b6(b6)
        summary["B6_zip_accuracy"] = b6

    # Save results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, f"benchmark_{run_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n{'='*70}")
    print(f"Results saved → {out_path}")
    print(f"{'='*70}\n")

    return summary


def _parse_args():
    import argparse
    p = argparse.ArgumentParser(description="iTREDS benchmark suite")
    p.add_argument(
        "--bench", type=str, default=None,
        help="Comma-separated benchmark numbers to run, e.g. '1,3,5' (default: all)"
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    bench_filter = None
    if args.bench:
        bench_filter = [int(x.strip()) for x in args.bench.split(",") if x.strip().isdigit()]
    run_all(bench_filter)
