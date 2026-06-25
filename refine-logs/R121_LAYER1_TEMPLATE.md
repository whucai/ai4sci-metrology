# R121 — Layer 1 Gold Evidence-Chain Annotation Template

**Date**: 2026-06-25
**Frame**: v7.2 (IO → ECRF → TCE). Layer 1 = human gold evidence chain per paper, the trusted reference against which agent ECRF scores are compared in Study 2/3.
**Scope**: 20 papers (R120 pool) × 2 annotators × 6 components = 240 component-level gold labels.
**Reliability target**: component-stratified Krippendorff/Cohen α ≥ 0.70 (reported in R161).

---

## 1. Annotation object — the 6-component evidence chain

For each paper, the annotator records the **gold evidence chain**: the set of factual, paper-supported claims that a faithful reproduction must recover, broken into the six v7.2 components. Each component has a structured sub-record (below) and a final 3-level fidelity score.

### Component schema

| # | Component | Question the gold answers | Sub-fields (annotator fills) |
|---|---|---|---|
| C1 | **Data** | What data source(s) does the paper use? | `data_source`, `data_description`, `access`, `provenance` |
| C2 | **Sample** | What is the analytical sample? | `N`, `time_window`, `unit_of_analysis`, `filter_rules` |
| C3 | **Indicator** | What derived measures/indicators are computed? | `formula`, `parameters`, `computation_steps` |
| C4 | **Model** | What statistical/analytical model is estimated? | `spec_elements`, `estimator`, `coefficients`, `fixed_effects` |
| C5 | **Result** | What numerical/tabular results are reported? | `target_tables`, `target_values`, `expected_direction` |
| C6 | **Claim** | What conclusions does the paper assert? | `conclusion_claims`, `claim_scope`, `uncertainty` |

### Fidelity scoring (per component, 3-level — the gold target for agent ECRF)

| Score | Label | Meaning |
|---|---|---|
| 1.0 | FULL | Component fully specified & recoverable from the paper + executable materials |
| 0.5 | PARTIAL | Component partly specified; missing parameter / ambiguous scope / requires assumption |
| 0.0 | NONE | Component not specified or not recoverable even with IO₃ materials |

> The gold score is the **ceiling** an agent could reach given the paper's actual observability, NOT the agent's achieved score. This is what makes IO-bound analysis possible: an agent scoring below gold at IO₁ but at gold at IO₃ demonstrates the IO effect.

---

## 2. Per-component annotation fields (structured)

### C1 — Data
```yaml
data_source:           # e.g., "Web of Science", "USPTO PatentsView", "SciSciNet"
data_description:      # 1-2 sentences on what the dataset contains
access:                # public | partial | private | api-dependent
provenance:            # URL / repository / institution
gold_fidelity:         # 1.0 | 0.5 | 0.0
fidelity_rationale:    # why this score (1 sentence)
```

### C2 — Sample
```yaml
N:                     # sample size (number; "unknown" if not stated)
time_window:           # e.g., "1975-2020" or "2008-2018"
unit_of_analysis:      # paper | patent | author | team | firm | faculty
filter_rules:          # list of inclusion/exclusion rules
gold_fidelity:         # 1.0 | 0.5 | 0.0
fidelity_rationale:
```

### C3 — Indicator
```yaml
formula:               # the indicator's mathematical formula (LaTeX or plain)
parameters:            # thresholds/weights/parameter choices (e.g., "c=5 citation window")
computation_steps:     # ordered list of steps to compute (P1, P2, ...)
gold_fidelity:         # 1.0 | 0.5 | 0.0
fidelity_rationale:
```

### C4 — Model
```yaml
spec_elements:         # list, e.g., ["OLS", "year FE", "team_size_deciles", "clustered SE"]
estimator:             # OLS | logit | negative-binomial | NLP | simulation | none
coefficients:          # dict of key coefs with paper-reported values & signs
fixed_effects:         # list
gold_fidelity:         # 1.0 | 0.5 | 0.0
fidelity_rationale:
```

### C5 — Result
```yaml
target_tables:         # list, e.g., ["Table 1: Mean D by team-size decile"]
target_values:         # list of {label, value, tolerance} — the numerical targets
expected_direction:    # positive | negative | mixed | none
gold_fidelity:         # 1.0 | 0.5 | 0.0
fidelity_rationale:
```

### C6 — Claim
```yaml
conclusion_claims:     # list of the paper's asserted conclusions (verbatim or paraphrase)
claim_scope:           # sample-specific | general | causal | descriptive
uncertainty:           # stated-qualifiers | none
gold_fidelity:         # 1.0 | 0.5 | 0.0
fidelity_rationale:
```

---

## 3. Evidence-break pre-registration (per paper)

For each paper, the annotator also pre-registers the **expected evidence-break** the agent is most likely to commit, so Study 3 (B₁–B₄ adjudication) has a trusted target. This is the gold-side expectation; R131 screens agent outputs against it.

| Break | Name | Definition | Gold-side record |
|---|---|---|---|
| B₁ | Substitution | Agent substitutes a different data source/sample than the paper's | `expected_B1`: yes/no + which component |
| B₂ | Circularity | Agent hard-codes paper-reported values instead of computing | `expected_B2`: yes/no + which value |
| B₃ | Synthetic | Agent synthesizes data when real data is available | `expected_B3`: yes/no + which component |
| B₄ | Assertion | Agent asserts a conclusion not supported by its own reproduction | `expected_B4`: yes/no + which claim |

```yaml
expected_breaks:
  B1: {likely: bool, component: ..., note: ...}
  B2: {likely: bool, component: ..., note: ...}
  B3: {likely: bool, component: ..., note: ...}
  B4: {likely: bool, component: ..., note: ...}
break_confidence:      # high | medium | low
```

---

## 4. IO-feasibility annotation (per paper, per IO level)

The annotator confirms the R120 pre-annotation by recording, for each IO level, whether a faithful reproduction is *possible* at that observability — this is the gold-side IO ceiling.

```yaml
io_feasibility:
  IO1: {feasible: yes|partial|no, ceiling_components: [list], rationale: ...}
  IO2: {feasible: yes|partial|no, ceiling_components: [list], rationale: ...}
  IO3: {feasible: yes|partial|no, ceiling_components: [list], rationale: ...}
io_collapse:           # none | IO2_IO3 | IO1_IO2  — where the IO manipulation can't separate levels
```

> `io_collapse` flags boundary papers (e.g., bikard2013 IO₂/IO₃ collapse) — the pre-registered R153 boundary-condition candidates.

---

## 5. Full paper-level record (one per paper)

```yaml
paper_id:              # slug, e.g., "petersen2023_disruption_index"
title:
domain:                # SoS | IS_Innovation | Management_Strategy
venue:
year:
task_type:             # STRICT | METHOD | DATA-SUB | CLAIM-ROBUST
observability_stratum: # Low | Medium | High  (annotator confirms/overrides R120)
annotator_id:          # A | B
date:

data:        { ...C1 fields... }
sample:      { ...C2 fields... }
indicator:   { ...C3 fields... }
model:       { ...C4 fields... }
result:      { ...C5 fields... }
claim:       { ...C6 fields... }

expected_breaks: { ...§3... }
io_feasibility:  { ...§4... }

overall_gold_ecrf:     # mean of the 6 component gold_fidelity values
notes:
```

---

## 6. Inter-annotator reliability protocol

1. **Independent annotation**: Annotators A and B each complete all 20 papers without consulting each other.
2. **Component-stratified α**: compute Krippendorff's α per component (Data, Sample, Indicator, Model, Result, Claim) on the 3-level fidelity score. Target ≥ 0.70 per component.
3. **Adjudication**:
   - Disagreements of ≤1 level (0 vs 0.5, or 0.5 vs 1.0): **average** the two scores.
   - Disagreements of >1 level (0 vs 1.0): **third-pass adjudication** by a senior annotator; the adjudicated value is final.
   - Record adjudication flips in `adjudication_log` for R161 transparency.
4. **Disagreement analysis**: report which components have lowest α (expected: Sample and Claim — most interpretive) — this itself informs the v7.2 construct (which components are reliably auditable vs not).
5. **Lock the gold**: once adjudicated, the 20-paper gold chain is frozen and versioned (`r121_gold_v1.json`); R122–R125 score against this frozen reference. Changes require re-versioning.

---

## 7. Coverage check (before R122 launch — gate)

Before R122–R125 may launch, confirm:
- [ ] 20/20 papers annotated by both annotators
- [ ] Component-stratified α ≥ 0.70 on ≥4 of 6 components (Sample/Claim ≥0.60 acceptable)
- [ ] All `expected_breaks` records filled
- [ ] All `io_feasibility` records filled; `io_collapse` papers explicitly flagged
- [ ] `r121_gold_v1.json` frozen and committed
- [ ] R120 stratum assignments confirmed or overridden per paper

> If α < threshold on ≥3 components: **do not launch R122** — refine the codebook (especially for the failing component) and re-annotate. This is the human-annotation critical path; it cannot be bypassed by compute.
