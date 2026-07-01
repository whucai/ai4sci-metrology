# R125 SGF Verdict — Does IO₃ (execution-level observability) break the synthetic floor?

**Date**: 2026-07-01
**Runs**: R124 IO₃, 34/36 DONE (18 papers × 2 models; 2 transient LLM_FAIL: donner2024 qwen3, gebhart2023 qwen3 — non-critical, included as gaps).
**Frozen contract**: gold v1-r3, v2 scorer, v1 weights+gates, IO package definitions — UNCHANGED throughout (no prompt/scorer/gate/refcode-detection/synth-classifier/package edits during R124).

## 1. Six-condition table (the core result)

| condition | n | mean ECRF | floor-break % | real-data % | synth % |
|---|---:|---:|---:|---:|---:|
| 1. has code + refcode used | 4 | 0.600 | **25%** | 1.00 | 0.75 |
| 2. has code + refcode NOT used | 14 | 0.648 | 71% | 1.00 | 0.29 |
| 3. no code + real data used | 7 | 0.575 | 57% | 1.00 | 0.43 |
| **4. real data used + synth false** | **15** | **0.703** | **100%** | 1.00 | 0.00 |
| 5. real data used + synth true | 10 | 0.495 | 0% | 1.00 | 1.00 |
| 6. synth true overall | 17 | 0.497 | 0% | 0.59 | 1.00 |

**The discriminator is row 4 vs row 5**: when the agent grounds on real data *and does not synthesize* (row 4), the floor breaks **100%** of the time (mean 0.703); when it has real data but synthesizes anyway (row 5), the floor breaks **0%** (mean 0.495). Synthesis (row 6) always caps at 0.50 — gate (c) is mechanical.

## 2. ITT vs per-protocol (the code-availability question)

| analysis | treatment | n | floor-break rate |
|---|---|---:|---:|
| **ITT** (has reference code in IO₃ package) | treatment vs control | 18 / 16 | **0.611 vs 0.312** |
| **Per-protocol** (refcode_used=True) | used vs not-used | 4 / 30 | **0.25 vs 0.50** |

ITT says having code helps (61% vs 31% break). **But per-protocol inverts it**: runs that *actually used* the reference code broke the floor only **25%** of the time — worse than runs that ignored the code (50%). The 4 code-using runs mostly still synthesized (75% synth). This is the key counterexample to the simple code-availability story.

## 3. Three-category verdict (per run)

| category | n runs | meaning |
|---|---:|---|
| clean SGF break (refcode used, synth=False, ECRF>0.50) | 1 | code-driven break — rare |
| ambiguous SGF break (ECRF>0.50, refcode NOT used) | 15 | floor broke via **data grounding**, not code |
| SGF persistence / counterexample (code available/used, synth=True, ECRF=0.50) | 7 | code present (even used) but agent took synthetic shortcut |
| SGF persistence (no break, not a code case) | 11 | boundary/no-data, flat at 0.50 |

### Per-paper verdict
- **Counterexamples (treatment, code available, synth=True → 0.50)**: `arts2021`, `liu2018_hotstreaks`, `obadage2024_citations_repro` — these had public reference code, two even imported it, yet the agent still synthesized placeholder data → stayed at the floor. **Most theoretically valuable failure mode.**
- **Ambiguous breaks (floor broke, refcode NOT used — data grounding)**: `petersen2024` (0.60/0.55), `park2023` (0.60/0.875), `arts2021_patent_nlp` (0.90/0.775), `bentley2023` (0.675), `funk2017`, `wu2019` (treatment) + `bikard2013`, `donner2024`, `gebhart2023`, `sun2023`, `zheng2025_male` (control).
- **Boundary persistence (no data → no break)**: `maddi2024`, `schaper2025`, `vasarhelyi2023`, `ke2015`.

## 4. Locked theoretical statement

> The IO₃ rerun does **not** provide clean support for the simple code-availability hypothesis. Instead, the emerging evidence suggests a stronger **uptake mechanism**: executable evidence improves reconstruction only when the agent grounds its workflow in real data and avoids synthetic substitution. **Code availability alone is insufficient.**
>
> Mechanism: **IO → material availability; agent uptake → evidence use; ECRF → reconstruction fidelity.** Observability is necessary but not sufficient; agentic uptake mediates the conversion from observable materials to reconstruction fidelity.

This upgrades the theory from "observability → ECRF" to "observability → **uptake** → ECRF", with the boundary condition that uptake (real-data grounding + non-synthetic execution) is the mediating mechanism. The SGF counterexamples (arts2021, liu2018, obadage2024 — code present/used but synthetic shortcut taken) are the strongest evidence that **material availability ≠ evidence uptake**.

## 5. Why this is a stronger finding than "H_SGF passes/fails"

A binary "code helps / doesn't help" result would be thin. Instead, R124 produced a **mechanism split**:
- the *necessary* condition for breaking the synthetic floor is `synth=False` (gate c is mechanical — no run with synth=True ever exceeded 0.50);
- the *sufficient* observed condition is `real_data_used=True ∧ synth=False` (100% break);
- `refcode_used` is neither necessary (most breaks had refcode=False) nor sufficient (3/4 code-using runs still synthesized).

This is a UTD-paper-grade mechanism finding: it identifies the **agent's uptake decision** (ground vs synthesize) as the mediator that converts observable materials into reconstruction fidelity — a boundary condition on the IO→ECRF causal claim, and a direct handle for the trust-inflation mechanism (P3): a result-level audit cannot see whether the agent grounded or synthesized, but the `synth` process-evidence flag localizes it.

## Artifacts
- `refine-logs/r125_sgf_verdict.json` — full machine-readable verdict (conditions, per-paper, locked statement).
- `scripts/r125_sgf_verdict.py` — reproducible analysis (read-only over R124 runs).
- `refine-logs/figures/fig_method_framework.png` — Figure 1 (Panel C to be updated with the empirical IO₃ results in a follow-up render).
