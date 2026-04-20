"""
Diagnostic script: check data/raw/ county coverage and extraction quality.
"""
import os
import json
import glob
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.config import MATERNAL_HEALTH_URLS

RAW_DIR = os.path.join("data", "raw")


def county_to_slug(name: str) -> str:
    return name.lower().replace(" ", "-")


def check_raw_data():
    expected = {name: county_to_slug(name) for name in MATERNAL_HEALTH_URLS}
    raw_dirs = {d for d in os.listdir(RAW_DIR) if os.path.isdir(os.path.join(RAW_DIR, d))}

    missing, empty, thin, good = [], [], [], []

    for county_name, slug in sorted(expected.items()):
        county_dir = os.path.join(RAW_DIR, slug)

        if slug not in raw_dirs:
            missing.append(county_name)
            continue

        json_files = glob.glob(os.path.join(county_dir, "*.json"))
        if not json_files:
            empty.append(county_name)
            continue

        # Check text quality: count files with non-trivial text
        total_chars = 0
        bad_files = 0
        for f in json_files:
            try:
                with open(f) as fh:
                    data = json.load(fh)
                text = data.get("text", "")
                total_chars += len(text)
                if len(text) < 100:
                    bad_files += 1
            except (json.JSONDecodeError, OSError):
                bad_files += 1

        avg_chars = total_chars // len(json_files)
        if len(json_files) == 1 and bad_files == 1:
            thin.append((county_name, len(json_files), avg_chars, "only 1 file, near-empty text"))
        elif bad_files == len(json_files):
            thin.append((county_name, len(json_files), avg_chars, "all files have <100 chars text"))
        elif avg_chars < 200:
            thin.append((county_name, len(json_files), avg_chars, f"{bad_files}/{len(json_files)} files near-empty"))
        else:
            good.append((county_name, len(json_files), avg_chars))

    # ── Unexpected dirs (scraped but not in config) ──────────────────────────
    expected_slugs = set(expected.values())
    extra_dirs = sorted(raw_dirs - expected_slugs)

    # ── Summary ──────────────────────────────────────────────────────────────
    total_expected = len(expected)
    total_good = len(good)

    print("=" * 62)
    print("  data/raw  Coverage Report")
    print("=" * 62)
    print(f"  Expected counties (from config) : {total_expected}")
    print(f"  ✓  Good extraction              : {total_good}")
    print(f"  ⚠  Thin / low-quality           : {len(thin)}")
    print(f"  ✗  Empty directory              : {len(empty)}")
    print(f"  ✗  Missing directory            : {len(missing)}")
    if extra_dirs:
        print(f"  ?  Extra dirs (not in config)   : {len(extra_dirs)}")
    print()

    if missing:
        print("── MISSING (no directory in data/raw/) ──────────────────────")
        for c in missing:
            print(f"  {c}")
        print()

    if empty:
        print("── EMPTY (directory exists but 0 JSON files) ────────────────")
        for c in empty:
            print(f"  {c}")
        print()

    if thin:
        print("── THIN / LOW-QUALITY EXTRACTION ────────────────────────────")
        print(f"  {'County':<22} {'Files':>6}  {'Avg chars':>10}  Note")
        print(f"  {'-'*22}  {'-'*6}  {'-'*10}  {'-'*28}")
        for county_name, nfiles, avg, note in thin:
            print(f"  {county_name:<22} {nfiles:>6}  {avg:>10,}  {note}")
        print()

    print("── GOOD EXTRACTION ──────────────────────────────────────────")
    print(f"  {'County':<22} {'Files':>6}  {'Avg chars':>10}")
    print(f"  {'-'*22}  {'-'*6}  {'-'*10}")
    for county_name, nfiles, avg in good:
        print(f"  {county_name:<22} {nfiles:>6}  {avg:>10,}")
    print()

    if extra_dirs:
        print("── EXTRA DIRS (not in MATERNAL_HEALTH_URLS) ─────────────────")
        for d in extra_dirs:
            print(f"  {d}")
        print()

    total_json = sum(
        len(glob.glob(os.path.join(RAW_DIR, slug, "*.json")))
        for slug in raw_dirs
    )
    print(f"  Total JSON files across all counties: {total_json:,}")
    print("=" * 62)

    needs_rerun = missing + empty + [c for c, *_ in thin]
    if needs_rerun:
        print("\nCounties to re-run Phase 1 scraping:")
        print("  " + ", ".join(f'"{c}"' for c in needs_rerun))


if __name__ == "__main__":
    check_raw_data()
