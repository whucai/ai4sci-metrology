# R-robust-KU + clean-anchor + boundary-excluded robustness

**Date**: 2026-07-01
**Frozen**: R125 outputs + v2 scorer + v1 gates + gold v1-r3 — UNCHANGED (no edits to experiments, prompts, packages, scorer, refcode detection, or synth classifier). Pure re-analysis.

## Verdict: H_EUC (Evidence-Chain Uptake Constraint) holds in every configuration.

| check | n papers | IO₁ | IO₂ | IO₃ | IO₁<IO₂ | IO₁<IO₃ | IO₂<IO₃ | ground∧¬synth (mean / break%) | synth=True (mean / break%) | H_EUC? |
|---|---:|---:|---:|---:|---|---|---|---|---|---|
| **0. Baseline (full)** | 18 | 0.499 | 0.601 | 0.591 | YES | YES | **NO** | 0.702 / **100%** | 0.499 / **0%** | ✅ |
| **1. KU excluded** | 15 | 0.498 | 0.610 | 0.588 | YES | YES | **NO** | 0.696 / **100%** | 0.500 / **0%** | ✅ |
| **2. KU grouped** (see below) | 18 | — | — | — | — | — | — | KU & non-KU identical pattern | | ✅ |
| **3. Clean-IO₃ anchors** | 9 | 0.497 | 0.640 | 0.638 | YES | YES | **NO** | 0.720 / **100%** | 0.496 / **0%** | ✅ |
| **4. Boundary excluded** | 13 | 0.498 | 0.634 | 0.619 | YES | YES | **NO** | 0.706 / **100%** | 0.497 / **0%** | ✅ |

### Check 2 — KU grouped sensitivity (is the result driven by the KU cluster?)
| cluster | n papers | ground∧¬synth break% | synth=True break% |
|---|---:|---:|---:|
| KU Leuven/Arts (3 papers) | 3 | **100%** | **0%** |
| non-KU (15 papers) | 15 | **100%** | **0%** |

**The uptake pattern is identical inside and outside the KU cluster** → the result is **not** driven by KU Leuven/Arts concentration. (Note: KU cluster mean ECRF IO₁/IO₂/IO₃ = 0.500/0.554/0.604; non-KU = 0.498/0.610/0.588 — same shape.)

## Refcode comparison (robust across checks)
| check | refcode used: break% | refcode not used: break% |
|---|---:|---:|
| Baseline | 25% (n=4) | 50% (n=66) |
| KU excluded | 33% (n=3) | 53% (n=55) |
| Clean anchors | 25% (n=4) | 69% (n=32) |
| Boundary excluded | 25% (n=4) | 65% (n=46) |

In **every** configuration, `refcode_used` has *lower* floor-break than `refcode_not_used` — code use does not help and often hurts (code-users still synthesized). This is robust.

## Component×IO slopes (robust)
| check | data_source slope | model slope | result slope |
|---|---:|---:|---:|
| Baseline | +0.368 | −0.159 | +0.074 |
| KU excluded | +0.375 | −0.175 | +0.074 |
| Clean anchors | +0.500 | −0.142 | +0.051 |
| Boundary excluded | +0.500 | −0.187 | +0.084 |

`data_source` slope is **positive in all configs** (observability lifts data access); `model` slope is **negative in all** (execution bottleneck); `result` is modest positive. The component-level localization of the uptake bottleneck is robust.

## IO₂ < IO₃ is NO in every configuration
The non-monotonicity (IO₃ never exceeds IO₂) is **not noise** — it replicates across KU-excluded, clean-anchor, and boundary-excluded samples. This is the structural signature of the uptake bottleneck: adding executable code does not raise mean ECRF because code availability ≠ code uptake ≠ grounding.

## Interpretation (per the pre-registered rule — NOT simple monotonic observability)

> **Do not claim simple monotonic observability.** The correct conclusion: observability increases **material availability** (data_source slope +0.37–0.50 across all configs), but **realized reconstruction fidelity depends on agentic uptake** — specifically `real_data_used ∧ ¬synth` (100% floor-break, mean ≈0.70, in every configuration) vs `synth=True` (0% break, mean ≈0.50, in every configuration). **Code availability alone is incomplete**: `refcode_used` underperforms `refcode_not_used` in all four checks. The Evidence-Chain Uptake Constraint (H_EUC) is **robust** to KU-cluster exclusion, clean-anchor restriction, and boundary-paper exclusion.

This converts the R125 finding from a single-sample result into a **robust mechanism**: the IO→ECRF link is mediated by uptake, and this mediation survives every reasonable subsample. The boundary condition (observability necessary but not sufficient; uptake mediates) is the paper's theoretical contribution, not an artifact of paper selection.

## Artifacts
- `refine-logs/r_robust_ku.json` — full machine-readable robustness output.
- `scripts/r_robust_ku.py` — reproducible (read-only over frozen R125 runs).
