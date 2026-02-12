# Structured Output Comparison: v1 vs v2

This document compares:

- `data/structured/v1/California_County_Healthcare_Data_v1.csv`
- `data/structured/v2/California_County_Healthcare_Data_v2.csv`

`v1` uses the previous taxonomy flow, while `v2` uses the LLM-based classifier plus expanded maternal-health keyword library.

## Evaluation setup

- **Gold reference**: `eval/gold_maternal.jsonl`
- **Matching unit**: county + normalized program name
- **Dedup logic**: deduplicate by `(county, normalized program name)` before precision/recall scoring
- **Gold matching heuristic**: token-overlap and normalized-name containment between extracted and gold program names
- **Scope**: 4 counties (Los Angeles, Sacramento, San Diego, San Francisco)

## Headline result

`v2` improves overall maternal program detection quality and category alignment:

- Higher macro recall, precision, and F1 against the gold dataset
- Lower duplicate rate
- Better taxonomy-conformant categories

## Aggregate metrics (v1 -> v2)

| Metric | v1 | v2 | Delta (v2 - v1) |
|---|---:|---:|---:|
| Rows produced | 43 | 40 | -3 |
| Unique program rows (deduped) | 26 | 27 | +1 |
| Duplicate rate | 0.3953 | 0.3250 | -0.0703 |
| Distinct categories | 11 | 10 | -1 |
| `Other` category rate | 0.0233 | 0.0000 | -0.0233 |
| In-taxonomy category rate | 0.9070 | 1.0000 | +0.0930 |
| Eligibility field fill rate | 0.2558 | 0.3250 | +0.0692 |
| Application field fill rate | 0.2326 | 0.2250 | -0.0076 |
| Required documentation fill rate | 0.0000 | 0.0000 | +0.0000 |
| Program URL fill rate | 0.9070 | 0.8500 | -0.0570 |
| Department phone fill rate | 0.4419 | 0.6500 | +0.2081 |
| Target population fill rate | 1.0000 | 1.0000 | +0.0000 |
| Program description fill rate | 1.0000 | 1.0000 | +0.0000 |
| Macro gold recall | 0.6250 | 0.7083 | +0.0833 |
| Macro gold precision | 0.3036 | 0.3333 | +0.0298 |
| Macro gold F1 | 0.3963 | 0.4381 | +0.0418 |

## Per-county gold performance

| County | v1 Recall | v2 Recall | Delta | v1 Precision | v2 Precision | Delta |
|---|---:|---:|---:|---:|---:|---:|
| Los Angeles | 0.6667 | 1.0000 | +0.3333 | 0.4286 | 0.5000 | +0.0714 |
| Sacramento | 0.5000 | 0.5000 | +0.0000 | 0.2500 | 0.3333 | +0.0833 |
| San Diego | 0.3333 | 0.3333 | +0.0000 | 0.2500 | 0.2500 | +0.0000 |
| San Francisco | 1.0000 | 1.0000 | +0.0000 | 0.2857 | 0.2500 | -0.0357 |

## Programs extracted per county

| County | v1 | v2 | Delta |
|---|---:|---:|---:|
| Los Angeles | 19 | 17 | -2 |
| Sacramento | 4 | 3 | -1 |
| San Diego | 9 | 9 | 0 |
| San Francisco | 11 | 11 | 0 |

## Interpretation

- **v2 improved retrieval quality**: macro recall/precision/F1 all increased.
- **v2 improved category consistency**: no `Other` labels and 100% taxonomy category alignment.
- **v2 reduced redundancy**: fewer total rows but more unique programs and lower duplicate rate.
- **v2 still has data quality gaps**: required documentation extraction remains 0% and URL fill rate dropped.
- **San Diego remains bottlenecked**: recall did not improve (0.3333 in both versions), indicating discovery/extraction constraints upstream.

## Known artifact to fix next

Both versions contain a noisy notes artifact:

- `Notes` includes the phrase `"Not a maternal health program"` in nearly all rows.

This likely reflects prompt/post-processing behavior and should be cleaned to improve readability and downstream analysis.

