# 10-Paper Benchmark Proposal for M1 Baseline

**Date**: 2026-06-16
**Purpose**: Define the 10-paper set for M1 B1 baseline (R007-R016), validating the Multi-Dimensional Reproduction Quality Framework across task types and methodologies.

---

## Selection Principles

1. **Task type coverage**: 3 STRICT + 3 DATA-SUB + 2 COMPONENT + 2 METHOD = 10
2. **Venue diversity**: Nature, Science, PNAS, Management Science, Research Policy, Scientometrics, PLoS ONE, arXiv
3. **Method diversity**: OLS regression, NLP preprocessing, network analysis, bibliometric indicators, time-trend analysis, patent analysis
4. **Data accessibility**: All papers use SciSciNet papers/patents or PatentsView data (locally available)
5. **Gold feasibility**: All papers have pre-extracted methods in `bench-mark/`; gold values can be pre-computed

---

## The 10 Papers

### STRICT (3 papers — same data, D3=pass/fail)

| # | Paper | Venue | Year | Method | Data | Gold Status |
|---|-------|-------|------|--------|------|-------------|
| 1 | **Petersen2024** "The disruption index suffers from citation inflation" | arXiv (Nature CS) | 2024 | OLS regression: CD = f(ln_kp, ln_rp, ln_cp5, year_FE) | SciSciNet papers | **DONE** (R002, D3=8/8) |
| 2 | **Park2023** "Papers and patents are becoming less disruptive over time" | Nature | 2023 | CD time-trend analysis (1950–2010), field-level aggregation | SciSciNet papers | Pre-extracted |
| 3 | **Funk2017** "A Dynamic Network Measure of Technological Change" | Management Science | 2017 | Patent network: new subclass pairs, difficulty-score, network convergence | PatentsView | Pre-extracted |

**Why these three**: Petersen2024 tests regression exactness, Park2023 tests time-trend computation, Funk2017 tests network-based indicator construction. Each has a different "what must match" at D3.

### DATA-SUB (3 papers — substitute data, D3=reference-only)

| # | Paper | Venue | Year | Method | Original Data | Substitute Data | Gold Status |
|---|-------|-------|------|--------|---------------|-----------------|-------------|
| 4 | **Wu2019** "Large teams develop and small teams disrupt" | Nature | 2019 | OLS: disruption = f(team_size, controls, year_FE) | WoS (~42M) | SciSciNet (~111K) | **DONE** (R001/R001b) |
| 5 | **Ke2023** "A network-based normalized impact measure" | PNAS | 2023 | Normalized citation impact via network propagation | WoS/MAG | SciSciNet | Pre-extracted |
| 6 | **Abramo2017** "How long do top scientists maintain their stardom?" | Scientometrics | 2017 | Career productivity/impact decay analysis | WoS Italy | SciSciNet | Pre-extracted |

**Why these three**: Wu2019 tests direction preservation on substitute data, Ke2023 tests network algorithm fidelity, Abramo2017 tests career-level metric consistency. Each shows a different facet of "what survives data substitution."

### COMPONENT DIAGNOSIS (2 papers — multi-indicator decomposition)

| # | Paper | Venue | Year | Method | Indicators | Gold Status |
|---|-------|-------|------|--------|------------|-------------|
| 7 | **Arts2021** "NLP to identify creation and impact of new technologies" | Research Policy | 2021 | 10 NLP indicators (5 novelty + 5 reuse) | PatentsView | **DONE** (R003, D=0.90) |
| 8 | **Deng2023** "Enhancing the robustness of the disruption metric" | Scientometrics | 2023 | CD₅ variant comparison, noise injection, robustness tests | SciSciNet | Pre-extracted |

**Why these two**: Arts2021 tests NLP preprocessing + multi-indicator construction, Deng2023 tests indicator variant comparison and noise sensitivity. Both require the agent to decompose a complex method into sub-components.

### METHOD (2 papers — structural correctness, no numerical targets)

| # | Paper | Venue | Year | Method | Evaluation | Gold Status |
|---|-------|-------|------|--------|------------|-------------|
| 9 | **Zhao2025** "A Review on the Novelty Measurements of Academic Papers" | Scientometrics | 2025 | Survey/taxonomy of novelty measures | Structural fidelity, taxonomy completeness | Pre-extracted |
| 10 | **Donner2024** "Data inaccuracy quantification and uncertainty propagation for bibliometric indicators" | arXiv | 2024 | Error propagation model for bibliometric indicators | Formula correctness, uncertainty methodology | Pre-extracted |

**Why these two**: Zhao2025 tests whether the agent can correctly categorize and describe a methodological taxonomy. Donner2024 tests whether the agent can implement a mathematical error propagation model without target values. Both have no "gold numbers" — the evaluation is structural.

---

## Coverage Matrix

| Paper | Data Source | Sample | Indicator | Model | Result Table | Claim |
|-------|-------------|--------|-----------|-------|--------------|-------|
| Petersen2024 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Park2023 | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| Funk2017 | ✓ | ✓ | ✓ | — | — | ✓ |
| Wu2019 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ke2023 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Abramo2017 | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| Arts2021 | ✓ | ✓ | ✓ | — | — | ✓ |
| Deng2023 | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| Zhao2025 | — | — | ✓ | — | — | ✓ |
| Donner2024 | — | — | ✓ | ✓ | — | ✓ |

✓ = component evaluable; — = component not applicable

---

## Methodological Diversity

| Category | Papers | Methods Represented |
|----------|--------|---------------------|
| Regression-based | 3 | Petersen2024, Wu2019, Abramo2017 |
| NLP/Text-based | 2 | Arts2021, Zhao2025 |
| Network-based | 2 | Funk2017, Ke2023 |
| Time-trend/Descriptive | 1 | Park2023 |
| Robustness/Uncertainty | 2 | Deng2023, Donner2024 |

---

## Resource Estimate

| Activity | Per Paper | Total (10 papers) |
|----------|-----------|--------------------|
| Gold pre-computation | 20–60 min | ~6 hours |
| LLM generation (C1) | 2–5 min | ~30 min |
| Execution + evaluation | 5–10 min | ~1 hour |
| Per-model run (×4 models) | ~30 min | ~2 hours |
| **Total M1–M5** | — | **~50 compute-hours** |

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| SciSciNet doesn't have needed fields for Ke2023/Abramo2017 | Medium | Substitute with simplified version; flag as DATA-SUB-METHOD hybrid |
| Park2023 requires CD₅ computation on all of SciSciNet | Low | CD already available in SciSciNet schema |
| Funk2017 patent network needs CPC data | Low | cpc_ids available in PatentsView data |
| Donner2024 error propagation too complex for LLM | Medium | Accept partial implementation; document as METHOD complexity ceiling |
| Zhao2025 survey paper has no executable code | Low | This is the point — tests structural understanding without code |

---

## Decision Required

1. Confirm the 10-paper set or suggest substitutions
2. Priority: start with Park2023 (R004 gold) and Funk2017 (R005 gold) as next M0 runs
3. Defer Ke2023 and Abramo2017 if SciSciNet field compatibility issues arise
