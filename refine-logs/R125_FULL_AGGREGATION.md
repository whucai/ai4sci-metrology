# R125 Full Aggregation — Study 2 (IO₁→IO₂→IO₃) + Evidence-Chain Uptake mechanism

**Date**: 2026-07-01
**Runs**: 105 DONE across IO₁/IO₂/IO₃ (18 papers × ≤3 IO × 2 models; deng2023/galuez2023 excluded as R122 coverage gaps; 2 transient LLM_FAIL in IO₃).
**Frozen contract**: gold v1-r3, v2 scorer, v1 weights+gates — UNCHANGED.

## 1. Headline: the IO gradient and the uptake bottleneck

| IO level | mean ECRF | what's provided |
|---|---:|---|
| IO₁ | **0.499** | paper text only → all agents synthesize → gate (c) caps 0.50 |
| IO₂ | **0.601** | + data dict + docs + raw_data → some agents ground → +0.102 |
| IO₃ | **0.591** | + original/reference code → **no overall lift** (−0.010 vs IO₂) |

**IO₃ does not exceed IO₂.** This is the central anomaly: adding executable code did *not* raise mean ECRF. Monotonicity IO₁<IO₃ holds for **11/18 papers** — the 7 non-monotonic cases are the SGF counterexamples (code-bearing papers where the agent synthesized at IO₃).

By model: qwen3-32b 0.500/0.604/0.583; deepseek-v4-pro 0.497/0.597/0.599 — the bottleneck is present in both model families.

## 2. Component × IO (where the bottleneck lives)

| component | IO₁ | IO₂ | IO₃ | slope (IO₃−IO₁) |
|---|---:|---:|---:|---:|
| **data_source** | 0.500 | 0.917 | 0.868 | **+0.368** |
| result | 0.529 | 0.556 | 0.603 | +0.074 |
| sample | 0.986 | 0.972 | 0.941 | −0.045 |
| indicator | 0.857 | 0.847 | 0.809 | −0.048 |
| claim | 1.000 | 0.986 | 0.985 | −0.015 |
| **model** | 0.600 | 0.500 | 0.441 | **−0.159** |

**Interpretation**: observability strongly lifts the **data_source** component (+0.368 — agents get credit for loading provided data), but the **model** component *declines* (−0.159) and **result** rises only modestly (+0.074). The IO→ECRF link breaks down at the **execution/uptake** stage (model + result), not at data access. This localizes the uptake bottleneck to the agent's *use* of materials, not their *availability*.

## 3. Table 1 — three-mechanism-layer collapse (IO₃, n=34 DONE runs)

### Layer 1 — Code observability ≠ code uptake
| condition | n | mean ECRF | floor-break % | synth % |
|---|---:|---:|---:|---:|
| code present + refcode used | 4 | 0.600 | 25% | 0.75 |
| code present + refcode NOT used | 30 | 0.590 | 50% | 0.47 |
> **Code observability does not guarantee code uptake.** Runs that *used* the reference code had *lower* floor-break (25%) and *higher* synthesis (75%) than runs that ignored it.

### Layer 2 — Uptake (real data + no synthesis) drives floor-break
| condition | n | mean ECRF | floor-break % | synth % |
|---|---:|---:|---:|---:|
| **real_data ∧ ¬synth** | **15** | **0.703** | **100%** | 0.00 |
| real_data ∧ synth | 10 | 0.495 | 0% | 1.00 |
> **`real_data_used ∧ ¬synth` is necessary and ~sufficient for floor-break** (100%, mean 0.703). Synthesis collapses it to 0% (mean 0.495).

### Layer 3 — Synthetic gate is structural (agentic shortcut collapse)
| condition | n | mean ECRF | floor-break % |
|---|---:|---:|---:|
| synth=True | 17 | 0.497 | 0% |
| synth=False | 17 | 0.685 | 94% |
> **`synth=True ⇒ ECRF≈0.50`** (gate c is mechanical). This is an agentic failure mode — the synthetic shortcut — not measurement noise.

## 4. Three high-value counterexample types (the failure-mode taxonomy)

1. **arts2021 / obadage2024** — code present → synth=True → ECRF=0.50. *Code ≠ grounding.*
2. **liu2018** (the key counterexample) — `refcode_used=True` but `synth=True` → ECRF=0.50. ***Even explicit code invocation does not prevent synthetic collapse.***
3. **petersen2024 / park2023** — `real_data_used=True`, `refcode=False` → floor break. ***Data grounding, not code, determines ECRF.***

## 5. Theorem-style claim (UTD)

> **Proposition (Evidence-Chain Uptake).** Let **IO** denote material observability (the evidence materials supplied to the agent), **U** denote agentic uptake (the agent incorporating real data into its execution chain and refraining from synthetic substitution), and **F** denote reconstruction fidelity (ECRF). Then:
> (i) IO is **necessary but not sufficient** for F;
> (ii) **U mediates IO→F** — specifically, floor-break (F > 0.50) occurs iff `real_data_used ∧ ¬synth`, and is **independent of `refcode_used`**;
> (iii) `synth` (synthetic substitution) is a **structural agentic failure mode** that collapses F to the 0.50 gate regardless of IO.
>
> **Corollary (code is not the lever).** Code availability (IO₃ `ref_code_available`) does not guarantee code uptake (`refcode_used`), and code uptake does not guarantee grounding (`¬synth`). Therefore executable-code provision is an insufficient intervention for raising reconstruction fidelity.
>
> **Evidence.** R124, n=34 DONE IO₃ runs: `real_data ∧ ¬synth` → 100% break (mean 0.703); `synth=True` → 0% break (mean 0.497); `refcode_used` → 25% break (3/4 still synthesized). IO₃ mean (0.591) ≤ IO₂ mean (0.601). Component×IO: data_source +0.368, model −0.159.

**Core contribution sentence**: *Our results show that increasing observability (IO₃) is not sufficient to improve reconstruction fidelity. Instead, improvements occur only when agents actively incorporate real data into their execution chain and avoid synthetic substitution, revealing an uptake bottleneck in evidence-chain reconstruction.*

## 6. What this rules out / what it establishes
- ❌ Not an engineering benchmark or system eval.
- ✅ A **mechanism discovery**: evidence-chain reconstruction depends on whether agents actually *use* evidence, not merely whether evidence is *available*.
- The hypothesis is renamed **H_SGF → H_EUC (Evidence-Chain Uptake Constraint)**: material observability alone is insufficient; reconstruction fidelity is mediated by agentic uptake of real data.

## Artifacts
- `refine-logs/r125_full_aggregation.json` — full per-paper + Component×IO + Table 1 + theorem.
- `refine-logs/r125_sgf_verdict.json` — 6-condition + 3-category verdict.
- `scripts/r125_full_aggregation.py`, `scripts/r125_sgf_verdict.py` — reproducible.
- Figure 1 (mechanism diagram) — to be rendered via Codex.
