# Method — Three Observability Regimes & Synthetic Grounding Failure (SGF)

**Frame**: v7.2 (IO → ECRF → TCE). This section formalizes the three regimes that partition the IO₁→IO₂ trajectory (observed empirically in R122/R123, 18 papers × 2 models) and defines the **Synthetic Grounding Failure (SGF)** construct, then states the R124 hypothesis test.

## 1. The ECRF observability ceiling and the synthetic gate

Each run produces a 6-component ECRF score in [0,1] under the frozen v2 scorer with v1 weights and gates. Gate (c) caps the final ECRF at **0.50** whenever the agent generates synthetic/placeholder data (`uses_synthetic_data(code)=True`), regardless of whether real data was provided. This cap is the **synthetic floor** — it is the empirically observed IO₁ baseline (mean 0.499): with paper text only, every agent synthesizes, so every run saturates at 0.50.

## 2. Three regimes (paper-level, defined on the IO₁→IO₂ trajectory)

Let `data_provided(IOₖ)` be the frozen IO-package flag (whether real data is supplied at level k), `real_data_used` the process-evidence flag (agent loaded a raw_data file), `synth` the synthetic-generation flag, and `Δ = ECRF(IO₂) − ECRF(IO₁)`.

**Regime R_U — Partial Grounding Uplift.**
> `data_provided(IO₂)=True ∧ real_data_used=True ∧ synth=False ∧ Δ > 0`.

The agent grounded on the provided real data; the synthetic cap released and ECRF rose above 0.50. This is the **causal IO effect** (propositions P1/P2): increasing observability lifted fidelity. Empirically 9/18 papers, mean Δ = +0.196.

**Regime R_SGF — Synthetic Grounding Failure.**
> `data_provided(IO₂)=True ∧ synth=True` (agent synthesized *despite* real materials being available).

Real data was supplied but the agent did not load it; gate (c) kept ECRF at 0.50; Δ ≈ 0. This is the **behavior-mediated failure**: observability was increased but did not translate to grounding. Empirically 5/18 papers, mean Δ = 0.000. (Formal SGF definition in §3.)

**Regime R_B — Boundary Invariance.**
> `data_provided(IO₂)=False` (data is private/API-gated/licensed with no public substitute).

No real data can be supplied at any IO level; the agent must synthesize; ECRF stays at 0.50; Δ ≈ 0. This is the **honest IO bound** — the pre-registered R153 boundary condition. Empirically 4/18 papers, mean Δ = +0.019.

### Why the three regimes matter
R_U vs R_SGF **splits** the naive "data helps" effect: R_SGF shows that *providing* data is necessary but not sufficient — the agent's choice to ground mediates the IO→ECRF link. R_B separates "no data" (boundary) from "data not used" (SGF), preventing the conflation of structural unavailability with behavioral non-grounding. The three regimes are **disjoint and exhaustive** over the IO₁→IO₂ trajectory.

## 3. Synthetic Grounding Failure (SGF) — formal definition

**Definition (SGF).** For a run at IO level k ≥ 2:
> SGF(paper, model, IOₖ) = 1 ⟺ `data_provided(IOₖ)=True ∧ real_data_used=False ∧ synthetic_generated=True`.

A paper is in regime R_SGF if SGF holds for at least one of its IO₂ runs (the agent had real data available but generated synthetic data instead, triggering gate (c)).

**Mechanism.** SGF is the strongest single diagnostic for the **trust-inflation mechanism (P3)**: the agent produces a runnable script with synthetic data whose numbers are *indistinguishable from a grounded reproduction at the result level* — exactly the failure mode result-level evaluation (R₁) cannot detect and component-level audit (R₃) is designed to catch (gate (c) caps the ECRF, and the `synthetic_generated` process-evidence flag localizes the break to the Data component).

**Operational test (R124).** SGF is *prima facie* a code-observability problem: at IO₂ the agent has data but no executable reference, so it may synthesize rather than reverse-engineer the loading path. IO₃ supplies the **original/reference executable code**. If SGF is code-mediated, adding code should break the floor.

## 4. R124 hypothesis test — "Does execution-level IO break the synthetic floor?"

**Pre-registered hypothesis (H_SGF):**
> Adding original/reference executable code (IO₃) breaks the synthetic floor for R_SGF papers that *have* public code, lifting their ECRF above the 0.50 gate-(c) cap (Δ_SGF = ECRF(IO₃) − ECRF(IO₂) > 0); SGF persists for R_SGF papers *without* public code (IO₃ collapses to IO₂).

**Design (natural experiment with internal control):** the 5 R_SGF papers split by code availability:

| R_SGF paper | public code? | IO₃ condition | prediction |
|---|---|---|---|
| petersen2024 | ✓ (R002 reproduce_final.py) | clean IO₃ | ECRF rises above 0.50 |
| liu2018_hotstreaks | ✓ (code_bursts.py) | clean IO₃ | ECRF rises above 0.50 |
| arts2021_patent_nlp | ✓ (sam-arts/respol_patents_code) | clean IO₃ | ECRF rises above 0.50 |
| donner2024_data_inaccuracy | ✗ | IO₃ collapses to IO₂ | SGF persists (control) |
| schaper2025_frontier | ✗ (linkage private) | IO₃ collapses to IO₂ | SGF persists (control) |

The 3 code-bearing papers are the **treatment**; the 2 code-less papers are the **internal control** — they receive the IO₃ "prompt" (reference-code slot) but no actual code, so if SGF persists there while breaking for the treatment papers, the effect is attributable to *executable code* specifically, not to the IO₃ prompt or more materials per se.

**Secondary**: R124 also tests whether IO₃ lifts the R_U (partial-uplift) papers further (does code push them toward their gold ceiling?) and leaves R_B (boundary) papers flat (no data → no code → no change).

**Decision rule.** H_SGF is supported if:
- ≥2/3 treatment papers show ECRF(IO₃) > 0.50 with `ref_code_used=True ∧ synth=False` (code grounded, floor broken), AND
- ≥1/2 control papers remain at ECRF(IO₃) ≤ 0.50 with `synth=True` (SGF persists without code).

If the treatment papers do NOT break the floor (SGF persists despite code), SGF is **not** code-mediated — it is a deeper agent-behavior issue (e.g., the agent ignores provided code), which is itself a finding about the limits of observability.

## 5. Measurement (frozen contract)
- ECRF: frozen v2 scorer, v1 weights + gates (refine-logs/r122_freeze/).
- `synthetic_generated`, `real_data_used`, `ref_code_used`, `execution_succeeded`: process-evidence flags embedded per-run.
- Regime classification is post-hoc descriptive (not used by the scorer); the scorer applies gate (c) mechanistically.
- Gold ceiling (r121_gold_v1_frozen v1-r3) is unchanged; R124 does not modify gold, scorer, gates, or IO definitions (corrections via patch record only).
