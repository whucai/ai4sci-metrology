# Experimental Synthesis: Multi-Dimensional Reproduction Quality Framework

**Date**: 2026-06-16
**Status**: R001-R007 complete (M0 milestone, 7 experiments across 4 task types)

---

## 1. Unified Results Table

| Run | Paper | Task Type | Agent | N | Main Result | Diagnostic Value | D1 | D2 | D3 | D4 | D5 | Overall |
|-----|-------|-----------|-------|---|-------------|------------------|----|----|----|----|----|---------|
| R001 | Wu2019 "Large teams develop, small teams disrupt" | DATA-SUB | DeepSeek-V4-Pro (hybrid: LLM+manual fix) | 1 | Direction negative ✓, coef=-0.0093 vs paper -0.03. D_mean=0.0049 | Validates local reproducible computation on substitute data; proves agent can execute evidence chain end-to-end | — | — | Reference-only | — | — | L3(ds) |
| R001b | Wu2019 (same) | DATA-SUB | DeepSeek-V4-Pro + Codex pre-validation | 1 | Same direction, no self-correction needed. Coef=-0.00929. All 8 evidence-chain modules preserved. | Validates constrained prompting eliminates corrective simplification; proves method-chain fidelity with audit trail | — | — | Reference-only | — | — | L3(ds) |
| R002 | Petersen2024 "Disruption index suffers from citation inflation" | STRICT L3 | DeepSeek-V4-Pro | 1 | D3=8/8 (100%): all 3 coefficients to 6+ decimal places, N=102,550 exact, R²=0.120403 exact | Validates coefficient-level exact reproduction when methodology is formalizable as explicit protocol | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | L3 |
| R003 | Arts2021 "NLP to identify creation and impact of new technologies" | COMPONENT DIAGNOSIS | DeepSeek-V4-Pro | 1 | 10/10 preprocessing steps + 10/10 indicators identified. Reuse I6-I9 have formula aggregation bug (|set|*(1+Σui) vs |set|+Σui) | Validates error source localization — bug traced to lines 233-236 (formula sub-component), not data or preprocessing | 1.00 | 1.00 | 0.80 | 0.85 | 0.85 | 0.90 |
| R004 | Park2023 "Papers and patents are becoming less disruptive over time" | STRICT L3 | DeepSeek-V4-Pro | 1 | D3=6/6 (100%): sample N=469,855 exact, 66 years, CD 1945=0.035979, CD 2010=0.001191, decline=96.7%, overall mean=0.005724 — all exact to O(6) decimals | Validates STRICT pathway generalizes beyond regression to time-trend analysis; the "same data, same result" guarantee holds across different analytical patterns | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | L3 |
| R005 | Zhao2025 "A Review on the Novelty Measurements of Academic Papers" | METHOD | DeepSeek-V4-Pro | 1 | D1=1.00 (6/6 sections), D2=0.95 (coverage): 3 conceptual distinctions, 5+ novelty types, 4 measurement categories, 7 validation approaches, 8 open challenges | Validates METHOD task type — agent reproduces conceptual taxonomy structure without any data access or numerical targets. Proves framework handles survey/theory papers. | 1.00 | 0.95 | N/A | 1.00 | 1.00 | 0.98 |
| R007 | Bentley2023 "Is disruption decreasing, or is it accelerating?" | STRICT L3 | DeepSeek-V4-Pro | 1 | D3=9/9 (100%): all 9 metrics exact, including citation-weighted CD per year. UW and W CD1945/2010, decline rates, overall W, post1970 W — all exact to O(4)-O(6) decimals | Third STRICT paper with D3=1.00. Weighted index on same SciSciNet data as R004 — proves consistency across related methods. Finding: weighted CD NOT close to zero post-1970 (0.0104), contradicting paper claim. | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | L3 |

**Task Type Legend**:
- **STRICT L3** (Strict Reproduction): Same data, same sample, same model; D3 is pass/fail. Target is numerical identity. **3/3 papers D3=1.00.**
- **DATA-SUB** (Data-substituted Reproduction): Different data source from original; D3 is reference-only. Decisive metrics are direction consistency and method-chain fidelity.
- **COMPONENT DIAGNOSIS**: Multi-indicator decomposition; evaluates component identification completeness and error source localization. D3 measures per-component formula correctness, not aggregate numerical accuracy.
- **METHOD**: No numerical targets exist; structural correctness (D1, D2) and auditability (D5) are decisive. **1 paper, Overall=0.98.**

---

## 2. Error Type Taxonomy

Each detected error is classified along two axes: **source component** (WHERE in the reproduction chain) and **error nature** (WHAT kind of error).

### 2.1 Error Source × Nature Matrix

| Error Source | Nature | Example | Detected In | Dimension Flagged | Severity |
|-------------|--------|---------|-------------|-------------------|----------|
| Data Source | Missing/wrong dataset | Agent uses SciSciNet instead of WoS (unavoidable — WoS unavailable) | R001, R001b | D1 (fidelity) | Expected — flagged as data-substituted |
| Data Source | Missing field | Title column absent from patent data; agent correctly uses abstract+claims | R003 eval | D1 (fidelity) | Minor — agent adapts correctly |
| Sample Construction | Wrong filtering window | — (not yet observed) | — | D1, D3 (N error) | — |
| Sample Construction | Wrong temporal ordering | Agent uses same-date patents (no ordering) instead of multi-week spread | R003 | D2 (executability semantics) | Moderate — affects first-occurrence semantics |
| Variable Construction | Wrong variable mapping | — (not yet observed in isolation) | — | D3 | — |
| Indicator Construction | Wrong formula sub-component | Reuse indicators: |set|*(1+Σui) instead of |set|+Σui | R003 (I6-I9) | D3 (formula accuracy) | High — inflates reuse values by factor of |set| |
| Indicator Construction | Missing normalization | — (not yet observed) | — | D3 | — |
| Model Specification | Wrong controls / FE | — (not yet observed — R002 was exact) | — | D3, D4 | — |
| Result Table | Cell-level numerical deviation | — (R002 was exact at 6 decimals) | — | D3 | — |
| Claim | Direction/sign error | — (all runs preserved direction) | — | D4 | — |
| Execution | Code syntax error | Escaped newlines in LLM response (DeepSeek API artifact) | R003 (first attempt) | D2 | Minor — fixable, not logic error |
| Execution | Self-correction degradation | Agent self-corrected but simplified evidence chain, losing completeness | R001 | D2, D5 | Moderate — constrained prompts mitigate (R001b) |
| Execution | API response format mismatch | DeepSeek returns structured [{thinking},{text}] list instead of string; parse_agent_response extracts code from .content but not from list-of-dicts | R004 (first parse) | D2 | Minor — fixable with isinstance(response, list) check; code logic correct, only extraction failed |

### 2.2 Error Categories for Paper

For the paper's error taxonomy figure, collapse into 5 high-level categories:

| Error Category | Definition | Example from Experiments |
|----------------|-----------|--------------------------|
| **Data Source Error** | Wrong dataset, missing fields, version mismatch | SciSciNet vs WoS substitution (R001); missing title column (R003) |
| **Sample Construction Error** | Wrong filters, time window, inclusion criteria | Same-date vs multi-week ordering (R003 gold mismatch) |
| **Variable/Indicator Construction Error** | Wrong formula, missing normalization, incorrect feature engineering | Reuse formula aggregation bug (R003 I6-I9) |
| **Model Specification Error** | Wrong regression controls, FE, SE type | — (not yet observed; R002 was exact) |
| **Claim/Conclusion Error** | Direction error, significance mismatch, overclaiming | — (not yet observed) |
| **API/Infrastructure Error** | Response format mismatch, parsing failure, API artifact (not scientific error, but blocks execution) | Structured [{thinking},{text}] response not parsed (R004); escaped newlines in code (R003) |

---

## 3. Refined Paper Contributions

### Three-Point Contribution Structure

**C1. Task Type Taxonomy for LLM-Driven Scientific Reproduction**

We propose a four-category classification of reproduction tasks that determines which evaluation dimensions are decisive:

- **STRICT**: Same data, same sample, same model → D3 (numerical accuracy) is pass/fail
- **DATA-SUB**: Different data source → D3 is reference-only; direction consistency (D4) and method-chain fidelity (D1) are decisive
- **COMPONENT DIAGNOSIS**: Multi-indicator decomposition → evaluates whether agent can identify and correctly implement sub-components; error localization capability is the primary metric
- **METHOD**: No numerical targets exist → structural correctness (D1, D2) and auditability (D5) are decisive

This taxonomy prevents the common benchmark mistake of scoring all tasks on numerical accuracy, which would penalize agents for correctly using available data.

**C2. Component-Level Reproducibility Metrology**

Rather than a binary pass/fail judgment, our framework measures reproducibility fidelity at the level of individual evidence-chain components (Data Source → Sample → Indicator → Model → Result Table → Claim), each evaluated across five dimensions (Fidelity, Executability, Numerical Accuracy, Claim Consistency, Auditability).

The 6×5 matrix produces a diagnostic profile that answers not just "was it reproduced?" but "which link in the evidence chain broke, and how?"

**C3. Empirical Evidence from Scientometric Studies**

We validate the framework on seven experiments across four task types:

- **STRICT (R002, R004, R007)**: 3/3 papers achieve D3=1.00 — Petersen2024 regression (8/8), Park2023 time-trend (6/6), Bentley2023 weighted index (9/9). All use same SciSciNet data (N=469,855). Proves agent capability for exact reproduction across regression, descriptive, and weighted-index methods.
- **COMPONENT (R003)**: Arts2021 NLP indicators — agent correctly decomposes 10 preprocessing + 10 indicators but makes systematic formula error (|set|*(1+Σui) vs |set|+Σui). Framework localizes error to lines 233-236 (formula sub-component).
- **DATA-SUB (R001/R001b)**: Wu2019 team-size — agent preserves method-chain fidelity and direction consistency on substitute data.
- **METHOD (R005)**: Zhao2025 survey — agent reproduces novelty measurement taxonomy with D1=1.00, D2=0.95, no data or code execution needed.

Key findings: (1) STRICT pathway is robust — 3/3 papers with D3=1.00 across different analytical patterns. (2) COMPONENT diagnosis works — framework localizes errors to specific sub-components. (3) METHOD is viable — survey/theory papers evaluated on structural fidelity.

---

## 4. Framework Architecture Diagram (Text)

```
Paper → [Agent reads] → Reproduction Script
                              ↓
          ┌────────────────────────────────────┐
          │  Component-Level Evaluation         │
          │                                      │
          │  C1: Data Source ─── D1,D2          │
          │  C2: Sample ──────── D1,D2,D3       │
          │  C3: Indicator ───── D1,D2,D3       │
          │  C4: Model ───────── D1,D2,D3       │
          │  C5: Result Table ── D1,D2,D3,D4    │
          │  C6: Claim ───────── D1,D4,D5       │
          │                                      │
          │  Each cell scored 0-1                │
          └────────────────────────────────────┘
                              ↓
          ┌────────────────────────────────────┐
          │  Task-Type Routing                  │
          │                                      │
          │  STRICT?    → D3 is pass/fail       │
          │  DATA-SUB?  → D3 is reference-only  │
          │  COMPONENT? → Error localization    │
          │  METHOD?    → Structural fidelity   │
          └────────────────────────────────────┘
                              ↓
          ┌────────────────────────────────────┐
          │  Error Taxonomy                     │
          │                                      │
          │  Data Source Error                  │
          │  Sample Construction Error          │
          │  Variable/Indicator Error           │
          │  Model Specification Error          │
          │  Claim/Conclusion Error             │
          └────────────────────────────────────┘
```

---

## 5. Next Steps (Priority Order)

1. **Funk2017 (STRICT)**: Patent network measure on PatentsView — CPC data limited (145K patents, all 2016), need citation graph for full network construction
2. **Deng2023 (COMPONENT)**: Edge-removal robustness — paper_citations.parquet (78M edges) available, feasible with network computation
3. **Ke2023 (DATA-SUB)**: Network propagation impact — requires 78M-edge citation graph computation, computationally intensive
4. **Remaining benchmark**: Abramo2017, Donner2024 — need author career data or Bayesian regression, more complex
2. **M1 (R007-R011)**: B1 baseline — 10 papers across all 4 task types with Qwen3-32B
3. **M2 (R012-R014)**: B2 component eval (60 component tasks) + B3 spurious detection
4. **M5 (R019-R022)**: Multi-model comparison (Qwen3-32B, DeepSeek-V3, GPT-4o, Claude Opus 4)

**Immediate bottleneck**: Need to define the 10-paper benchmark set (R007-R010). Current bench-mark/ directory has papers from Nature, Science, PNAS, PLoS ONE, etc. — but which 10 to use?
