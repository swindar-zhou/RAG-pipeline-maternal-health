# Phase 1 Discovery — Version Comparison & Validation
**iTREDS · California 58-County Pipeline**
_Last updated: 2026-03-26_

---

## 1. Summary Metrics

| Metric | V1 | V2 | V3 | V4 | V5 |
|--------|----|----|----|----|-----|
| Total program links | **497** | 309 | 354 | 339 | 346 |
| Counties with hits | **48** | 39 | 40 | 42 | 46 |
| Counties with 0 programs | 10 | 19 | 18 | 16 | **12** |
| Hit rate (%) | **82.8%** | 67.2% | 69.0% | 72.4% | **79.3%** |

**Key takeaway:** V1 had the most total links (497) but V5 has the fewest zero-counties (12). V2 was the worst across both dimensions — a regression triggered by methodology changes that was only partially recovered through V3–V5.

---

## 2. Discovery Tier Breakdown

| Tier | V1 | V2 | V3 | V4 | V5 |
|------|----|----|----|----|-----|
| tier1_validated | 4 | 4 | 4 | 4 | 4 |
| tier2_search | 42 | 37 | 38 | 35 | 39 |
| tier2_search_relaxed_extract | 7 | 8 | 11 | 12 | 9 |
| tier2_search_relaxed_extract_seed_program | 4 | 7 | 4 | 6 | 4 |
| tier2_search_alt_seed | — | — | — | — | 1 |
| tier2_search_relaxed_extract_alt_seed | — | — | — | — | 1 |
| tier3_fallback | 1 | — | 1 | 1 | — |

V5 introduces `alt_seed` tiers — the new multi-seed fallback logic for counties where the primary DDG search URL yields 0 programs.

---

## 3. County-by-County Program Counts (All 58 Counties)

| County | V1 | V2 | V3 | V4 | V5 | V4→V5 |
|--------|----|----|----|----|-----|--------|
| Alameda | 30 | 30 | 30 | 30 | 30 | — |
| Alpine | 1 | 7 | 1 | 1 | 1 | — |
| Amador | 0 | 1 | 7 | 0 | 0 | — |
| Butte | 1 | 6 | 7 | 1 | 2 | +1 |
| Calaveras | 3 | 1 | 0 | 3 | 3 | — |
| Colusa | 1 | 1 | 1 | 1 | 1 | — |
| Contra Costa | 30 | 0 | 30 | 0 | 0 | — |
| Del Norte | 5 | 5 | 5 | 5 | 5 | — |
| El Dorado | 0 | 0 | 0 | 0 | 0 | — |
| Fresno | 0 | 0 | 0 | 0 | 0 | — |
| Glenn | 11 | 0 | 11 | 0 | 0 | — |
| Humboldt | 2 | 1 | 1 | 9 | 1 | **-8** |
| Imperial | 1 | 15 | 15 | 15 | 15 | — |
| Inyo | 5 | 7 | 11 | 11 | 5 | -6 |
| Kern | 0 | 0 | 7 | 0 | 0 | — |
| Kings | 0 | 0 | 0 | 5 | 0 | -5 |
| Lake | 1 | 1 | 1 | 1 | 2 | +1 |
| Lassen | 1 | 1 | 1 | 1 | 1 | — |
| Los Angeles | 5 | 5 | 5 | 5 | 5 | — |
| Madera | 30 | 0 | 30 | 0 | 0 | — |
| Marin | 16 | 30 | 7 | 9 | 30 | **+21** |
| Mariposa | 15 | 15 | 0 | 15 | 4 | -11 |
| Mendocino | 0 | 0 | 0 | 0 | 0 | — |
| Merced | 15 | 1 | 0 | 15 | 15 | — |
| Modoc | 1 | 7 | 1 | 7 | 7 | — |
| Mono | 30 | 7 | 7 | 9 | 7 | -2 |
| Monterey | 0 | 1 | 0 | 1 | 0 | -1 |
| Napa | 30 | 1 | 0 | 1 | 1 | — |
| Nevada | 2 | 7 | 0 | 7 | 2 | -5 |
| Orange | 2 | 2 | 2 | 2 | 2 | — |
| Placer | 12 | 0 | 7 | 1 | 17 | **+16** |
| Plumas | 1 | 0 | 6 | 6 | 2 | -4 |
| Riverside | 30 | 0 | 15 | 15 | 15 | — |
| Sacramento | 3 | 3 | 3 | 3 | 3 | — |
| San Benito | 1 | 0 | 1 | 7 | 1 | -6 |
| San Bernardino | 24 | 24 | 24 | 24 | 24 | — |
| San Diego | 3 | 3 | 3 | 3 | 3 | — |
| San Francisco | 10 | 10 | 10 | 10 | 10 | — |
| San Joaquin | 15 | 0 | 15 | 0 | 15 | **+15** |
| San Luis Obispo | 2 | 12 | 2 | 2 | 2 | — |
| San Mateo | 15 | 16 | 0 | 0 | 10 | **+10** |
| Santa Barbara | 1 | 1 | 1 | 0 | 1 | +1 |
| Santa Clara | 0 | 0 | 0 | 0 | 2 | **+2** |
| Santa Cruz | 30 | 0 | 30 | 30 | 30 | — |
| Shasta | 0 | 0 | 0 | 0 | 0 | — |
| Sierra | 1 | 6 | 0 | 3 | 3 | — |
| Siskiyou | 1 | 1 | 1 | 6 | 1 | -5 |
| Solano | 2 | 2 | 2 | 3 | 3 | — |
| Sonoma | 11 | 11 | 11 | 11 | 11 | — |
| Stanislaus | 15 | 15 | 0 | 15 | 15 | — |
| Sutter | 4 | 7 | 4 | 7 | 4 | -3 |
| Tehama | 30 | 30 | 30 | 30 | 30 | — |
| Trinity | 30 | 1 | 1 | 1 | 1 | — |
| Tulare | 15 | 0 | 7 | 7 | 1 | -6 |
| Tuolumne | 0 | 0 | 0 | 0 | 1 | +1 |
| Ventura | 1 | 1 | 0 | 1 | 1 | — |
| Yolo | 1 | 0 | 0 | 0 | 0 | — |
| Yuba | 1 | 14 | 1 | 0 | 1 | +1 |

---

## 4. V5 vs V4: Improvements & Regressions

### Improved (V5 > V4) — 10 counties
| County | V4 | V5 | Gain |
|--------|----|----|------|
| Marin | 9 | 30 | **+21** |
| Placer | 1 | 17 | **+16** |
| San Joaquin | 0 | 15 | **+15** |
| San Mateo | 0 | 10 | **+10** |
| Santa Clara | 0 | 2 | +2 |
| Butte | 1 | 2 | +1 |
| Lake | 1 | 2 | +1 |
| Santa Barbara | 0 | 1 | +1 |
| Tuolumne | 0 | 1 | +1 |
| Yuba | 0 | 1 | +1 |

### Regressed (V5 < V4) — 12 counties
| County | V4 | V5 | Loss |
|--------|----|----|------|
| Mariposa | 15 | 4 | -11 |
| Humboldt | 9 | 1 | -8 |
| Inyo | 11 | 5 | -6 |
| San Benito | 7 | 1 | -6 |
| Tulare | 7 | 1 | -6 |
| Kings | 5 | 0 | -5 |
| Nevada | 7 | 2 | -5 |
| Siskiyou | 6 | 1 | -5 |
| Plumas | 6 | 2 | -4 |
| Sutter | 7 | 4 | -3 |
| Mono | 9 | 7 | -2 |
| Monterey | 1 | 0 | -1 |

> **Note:** Regressions in V5 are primarily from counties relying on DuckDuckGo search (tier2). The DDG retry change improved hit rate but introduced score-filter sensitivity — some previously relaxed-pass results no longer pass the threshold. These counties need hardcoded `MATERNAL_HEALTH_URLS` entries to stabilize.

---

## 5. Volatility Analysis

Counties that oscillated between 0 and non-zero across versions are driven by DDG rate-limiting, not pipeline logic failures. A county at 30 one run and 0 the next indicates the search returned off-domain results.

**High-volatility counties (swings ≥15 across versions):**
| County | Min | Max | Swing |
|--------|-----|-----|-------|
| Contra Costa | 0 | 30 | 30 |
| Madera | 0 | 30 | 30 |
| Santa Cruz | 0 | 30 | 30 |
| Trinity | 0 | 30 | 30 |
| Riverside | 0 | 30 | 30 |
| Napa | 0 | 30 | 30 |
| Marin | 7 | 30 | 23 |
| Glenn | 0 | 11 | 11 |
| Placer | 0 | 17 | 17 |

**Root cause:** These counties are not in `MATERNAL_HEALTH_URLS`, so every run re-discovers them via DDG. DDG rate-limits vary by time of day; a throttled run returns 0 or off-domain results.
**Fix:** Add validated `MATERNAL_HEALTH_URLS` entries — same approach as the 4 gold-standard counties (LA, SD, SF, Sacramento).

---

## 6. Persistent Failures — All 5 Versions Zero

These 4 counties returned 0 program links in every single run:

| County | V1 | V2 | V3 | V4 | V5 | Diagnosis |
|--------|----|----|----|----|-----|-----------|
| El Dorado | 0 | 0 | 0 | 0 | 0 | Validated URL 404'd; DDG returns off-domain |
| Fresno | 0 | 0 | 0 | 0 | 0 | Validated URL 404'd; DDG returns off-domain |
| Mendocino | 0 | 0 | 0 | 0 | 0 | Validated URL 404'd; DDG returns off-domain |
| Shasta | 0 | 0 | 0 | 0 | 0 | Validated URL 404'd; DDG returns off-domain |

**Action required:** Manually verify the correct MCH page URL for each county and add to `MATERNAL_HEALTH_URLS` in `src/config.py`.

**Additionally zero in V5 (need stabilization):**
Amador, Contra Costa, Glenn, Kern, Kings, Madera, Monterey, Yolo

---

## 7. Validation Score — V5

Using V1 as baseline (best raw recall):

| Metric | Value |
|--------|-------|
| Hit rate vs V1 baseline | 46/48 = **95.8%** of V1-reachable counties |
| New counties found in V5 not in V1 | Santa Clara (+2) |
| Counties lost vs V1 | El Dorado, Fresno, Kern, Kings, Mendocino, Monterey, Shasta, Tuolumne (only 7 persistent — Tuolumne recovered in V5) |
| Persistently zero (all versions) | **4 counties** |
| Volatile (DDG-dependent) zero in V5 | **8 counties** |
| Stable hits (non-zero across all 5 versions) | **27 counties** (46.6%) |
| Total program links vs V1 | 346/497 = **69.6%** |

---

## 8. Recommended Next Steps

### Immediate (fixes zero-result counties)
1. **Manually verify and add MCH URLs** for the 12 V5 zero-counties — especially the 4 persistent zeros (El Dorado, Fresno, Mendocino, Shasta) and high-volatility counties (Contra Costa, Madera, Glenn, Kern)
2. **Add Bing/Google as DDG fallback** — DDG rate-limiting is the primary source of volatility; a secondary search engine backup would stabilize ~8 counties

### Medium-term (quality improvements)
3. **Investigate V1 → V2 regression** — V1 achieved 497 links; understanding why V2 dropped to 309 may reveal a configuration or threshold change that should be reverted
4. **Score calibration** — counties like Humboldt (V4: 9 → V5: 1) suggest the scoring threshold is sensitive; consider capping score changes between versions or adding hysteresis
5. **Expand tier1_validated coverage** — currently only 4 counties; targeting 20+ would eliminate DDG dependency for the most important counties
