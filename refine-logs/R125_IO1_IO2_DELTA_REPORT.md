# R125 (interim) — IO₁ → IO₂ Delta Analysis & Three-Layer Structure

**Date**: 2026-07-01
**Runs**: R122 IO₁ (36 DONE) × R123 IO₂ (36 DONE), 18 papers × 2 models, frozen v2 scorer + v1 weights/gates.
**Core metric**: **ΔECRF = ECRF(IO₂) − ECRF(IO₁)**.
**Figure**: `refine-logs/figures/fig_io1_io2_3layer.png` (paper Figure 2/3 candidate).

## Headline

| metric | value |
|---|---|
| mean ECRF(IO₁) | 0.499 |
| mean ECRF(IO₂) | 0.604 |
| **mean ΔECRF** | **+0.105** |

The IO₁→IO₂ observability gradient is real and positive: providing structured data + docs (no code) lifts mean ECRF by +0.105. The effect is **heterogeneous** — it partitions cleanly into three layers.

## Three-layer structure (the paper figure)

| layer | n papers | mean IO₁ | mean IO₂ | mean Δ | interpretation |
|---|---|---|---|---|---|
| **partial grounding uplift** | 9 | 0.500 | 0.693 | **+0.196** | agent loaded the provided real data (synth=False) → broke the 0.50 synth floor |
| **synthetic floor** | 5 | 0.500 | 0.500 | 0.000 | data was provided but agent synthesized anyway (synth=True) → gate (c) capped at 0.50 |
| **boundary invariance** | 4 | 0.500 | 0.519 | +0.019 | no data provided (data_provided=False) → IO₂ cannot help; flat at floor |

## Per-paper ΔECRF (sorted within layer)

### Partial grounding uplift (9 papers — the IO manipulation works here)
| paper | IO₁ | IO₂ | Δ | note |
|---|---|---|---|---|
| ke2015_sleeping_beauties | 0.500 | 0.900 | **+0.400** | largest uplift — SciSciNet substitute grounded the B-criterion |
| park2023_disruptive | 0.500 | 0.875 | +0.375 | STRICT CD5 trend recovered |
| obadage2024_citations_repro | 0.500 | 0.750 | +0.250 | labeled CSVs grounded the sentiment pipeline |
| bentley2023_disruption | 0.475 | 0.675 | +0.200 | weighted CD5 |
| wu2019_teams | 0.500 | 0.700 | +0.200 | team-size D-index |
| arts2021 | 0.500 | 0.663 | +0.163 | NLP indicators on USPTO |
| funk2017 | 0.500 | 0.600 | +0.100 | CDt/mCDt |
| gebhart2023_math_framework | 0.500 | 0.550 | +0.050 | OpenAlex substitute |
| sun2023_ranking_mobility | 0.500 | 0.525 | +0.025 | marginal |

### Synthetic floor (5 papers — **the theoretically critical layer**)
| paper | IO₁ | IO₂ | Δ | note |
|---|---|---|---|---|
| petersen2024 | 0.500 | 0.500 | 0.000 | **calibration anchor** — agent synthesized despite SciSciNet data provided |
| liu2018_hotstreaks | 0.500 | 0.500 | 0.000 | synthesized despite 108MB career data provided |
| arts2021_patent_nlp | 0.500 | 0.500 | 0.000 | synthesized despite 50K patent measures provided |
| donner2024_data_inaccuracy | 0.500 | 0.500 | 0.000 | synthesized despite Zenodo CSV provided |
| schaper2025_frontier | 0.500 | 0.500 | 0.000 | boundary-ish (linkage private) |

**This layer is the key finding**: observability (providing real data) did NOT translate to grounding (agent using it). The agent synthesized placeholder data despite real materials being available at IO₂ → gate (c) capped at 0.50. These are **B₃ (synthetic-despite-materials) break candidates** — the strongest single diagnostic for the trust-inflation mechanism (P3). It shows the IO→ECRF link is **not automatic**: the agent's choice to ground vs synthesize mediates it. This is itself a contribution about agent behavior under observability.

### Boundary invariance (4 papers — pre-registered R153 boundary)
| paper | IO₁ | IO₂ | Δ | note |
|---|---|---|---|---|
| zheng2025_male_female_retractions | 0.500 | 0.575 | +0.075 | one model broke floor (deepseek used the RW docs) |
| bikard2013 | 0.500 | 0.500 | 0.000 | MIT faculty private |
| maddi2024 | 0.500 | 0.500 | 0.000 | Publons private |
| vasarhelyi2023_who_benefits | 0.500 | 0.500 | 0.000 | Altmetric API-gated |

Confirms the pre-registered boundary: when data is genuinely unavailable (private/API-gated), IO₂ cannot lift ECRF — the manipulation has no leverage. This is the R153 negative-result boundary condition, behaving as designed.

## What this means for the paper (Figure 2/3)

The three-layer structure is the visual spine of the IO→ECRF mechanism story:
1. **Synthetic floor** (orange): ECRF flat at 0.50 across IO₁→IO₂ — either no data (boundary) or agent synthesized despite data. This is the *failure* mode: observability didn't help.
2. **Partial grounding uplift** (green): ECRF rises IO₁→IO₂ when the agent grounds on real data. This is the *causal* IO effect (P1/P2).
3. **Boundary invariance** (purple): flat at floor because the data is genuinely unavailable — the honest IO bound.

The **synthetic-floor-despite-data** sub-layer (5 papers) is the surprise: it splits "no data" (boundary) from "data provided but agent didn't use it" (synthetic floor) — a behavior-mediated gap that R124 (IO₃, + original code) should test whether executable code closes.

## Process evidence (IO₂)
- real_data_used: 27/36 runs (75%) — agents loaded provided data in most cases.
- synthetic_generated: 14/36 (39%) — down from 100% at IO₁; the agents that synthesized despite data are the synthetic-floor layer.
- execution_succeeded: 36/36.

## Next (NOT launched yet — per instruction)
- R124 (IO₃) is **not launched**. The IO₁→IO₂ delta + 3-layer figure is the immediate deliverable.
- R124 will test whether adding original/reference code (IO₃) closes the synthetic-floor gap (does executable code push the 5 synthetic-floor papers off the 0.50 cap?) and lifts the partial-uplift layer further.
- R125 full aggregation (IO₁→IO₂→IO₃ monotonicity, Component×IO mixed-effects) after R124.

## Artifacts
- `refine-logs/r125_io1_io2_delta.json` — full per-run + per-paper deltas + layer classification.
- `refine-logs/figures/fig_io1_io2_3layer.png` — Figure 2/3 candidate (Panel A: per-paper slope chart; Panel B: three-layer bars).
- `scripts/r125_io1_io2_delta.py` — reproducible analysis.
