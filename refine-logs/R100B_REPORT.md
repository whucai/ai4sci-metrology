# R100b Report — ECRF v1 Re-scoring + B₁ Adjudication (2026-06-24)

**No new runs.** Re-scored the existing 10 R100 outputs with ECRF v1 (weights + execution-evidence gates) and ran R132-lite B₁ adjudication. R101/R102 remain blocked.

---

## R100 status

10/10 runs DONE (exit 0, network-blocked, no leakage). Unchanged from R100.

## The ECRF v0 problem

v0 overall mean = **0.792** at IO₁ — ceiling-inflated and **not low**. Cause: keyword matching credits Data_Source/Indicator/Claim = 1.0 for "agent mentioned the concept in code," even when nothing executed against real data. This made R103 Gate-1 (IO₁ < IO₃ monotonicity) untestable, because IO₁ looked strong.

## ECRF v1 results

**Weights**: Data Source 0.10 · Sample 0.15 · Indicator 0.15 · Model 0.10 · Result 0.35 · Claim 0.15.
**Gates** (caps, take the minimum): (a) no executable result evidence → 0.60; (b) Result=0 → 0.55; (c) synthetic/placeholder data as substitute → 0.50; (d) Claim>0 & Result=0 → 0.60; (e) paper numbers hard-coded as computed results → 0.50.

### v0 vs v1 per run

| Paper | Model | v0 | v1 | Caps applied |
|-------|-------|-----|-----|--------------|
| petersen2024 | qwen3-32b | 0.667 | 0.50 | b result=0, c synthetic, d claim>0&result=0 |
| petersen2024 | deepseek | 0.667 | 0.50 | a no-exec-result, b, c |
| arts2021 | qwen3-32b | 0.583 | 0.45 | a, b, c |
| arts2021 | deepseek | 0.583 | 0.45 | a, b, c |
| funk2017 | qwen3-32b | 0.917 | 0.50 | c synthetic |
| funk2017 | deepseek | 0.917 | 0.50 | c synthetic |
| maddi2024 | qwen3-32b | 0.917 | 0.50 | a, c |
| maddi2024 | deepseek | 1.000 | 0.50 | a, c |
| bikard2013 | qwen3-32b | 0.833 | 0.50 | b, c, d |
| bikard2013 | deepseek | 0.833 | 0.50 | a, b, c |

### Component means (v1, unchanged from v0 — gates act on the overall)

| Component | Mean |
|-----------|------|
| Data Source | 1.00 |
| Indicator | 1.00 |
| Claim | 0.95 |
| Model | 0.85 |
| Sample | 0.60 |
| Result | 0.35 |

### Overall means

- **v0 = 0.792 → v1 = 0.490**
- **IO₁ low after v1 gating? ✅ YES (v1 < 0.60).**

The synthetic-substitute gate (c) fires on all 10 — expected, because IO₁ provides no data so every agent must synthesize. This is exactly the IO₁ low-fidelity baseline the theory predicts: structurally-informed (components understood) but execution-incomplete (Result low, synthetic data). At IO₃ (real data + code), gate (c) will not fire and Result should rise → the gradient becomes testable.

### Refined B₂ detection

B₂ is now flagged only when paper-reported numbers appear in a `RESULT` line **without** a distinguishing label (PAPER_REPORTED / reported / gold / compare). Legitimate comparison lines (e.g. `PAPER_REPORTED marginal_effect ≈ -0.017`) are **not** flagged. Under this rule, gate (e) fired on 0/10 runs at IO₁ — agents consistently labeled paper numbers as comparison, not as computed results. B₂ circularity is not the dominant risk at IO₁; B₁ (substitution) is.

## B₁ adjudication (R132-lite, 3 qwen candidates)

| Run | (a) synthetic data used? | (b) synthetic result presented as reproduction? | (c) claim depends on synthetic result? | Verdict |
|-----|--------------------------|-------------------------------------------------|------------------------------------------|---------|
| petersen2024 × qwen3-32b | ✅ True | ✅ True | ✅ True | **CONFIRM B₁** |
| bikard2013 × qwen3-32b | ✅ True | ✅ True | ✅ True | **CONFIRM B₁** |
| funk2017 × qwen3-32b | ✅ True | ✅ True | ✅ True | **CONFIRM B₁** |

All three confirmed: the agent synthesized placeholder data, ran the analysis on it, printed the synthetic-derived numbers as `RESULT` (the reproduction output), and rested the final claim on those numbers. This is the canonical B₁ (Substitution) mechanism — "wrong data produces coincidentally direction-correct results." Example (petersen × qwen): synthetic data → `coef_ln_rp = -0.02448` (paper: -0.002322; wrong magnitude, **direction NEGATIVE ✓**) → claim "citation inflation biases CD downward." A result-level evaluator would accept the direction match; the component audit flags the substitution.

## Recommendation — can R101 start?

**Almost.** ECRF v1 fixes the ceiling problem (IO₁ now correctly low at 0.49, B₁ confirmed). Two remaining items before R101:

1. **Score compression at IO₁** — v1 caps cluster everyone at 0.45–0.50 because all IO₁ runs use synthetic data. This is *correct* for the baseline, but means per-paper/per-model variation is invisible at IO₁. R101 (IO₂) and R102 (IO₃) are where variation should appear (real data at IO₃ → gate c lifts). Acceptable — proceed.
2. **B₂/B₁ boundary at IO₂/IO₃** — when real (but substitute) data appears at IO₂, the synthetic gate (c) must be refined to distinguish "substitute real data" (DATA-SUB, legitimate) from "synthetic toy data" (B₁). Current gate (c) keywords (synthetic/placeholder/toy) already do this, but verify on the first IO₂ runs.

**Verdict: R101 may start** once you greenlight. The scorer is now theoretically sound for the IO₁ < IO₂ < IO₃ monotonicity test (Gate 1). Recommend running R101 (IO₂) next, then R102 (IO₃), then R103 gate judgment.

## Artifacts

- `scripts/ecrf_v1_scorer.py` — v1 scorer + B₁ adjudicator
- `refine-logs/r100/r100b_v1_rescore.json` — v0/v1 per-run scores + caps
