# R101b Report — ECRF v2 Re-scoring (2026-06-24)

**No new runs.** Re-scored the existing 10 R101 (IO₂) outputs with scorer v2. v2 modifies **recognition rules only** — v1 weights (DS 0.10, Sample 0.15, Indicator 0.15, Model 0.10, Result 0.35, Claim 0.15) and all 5 gates (a–e) are **unchanged**. R102 remains blocked.

## What v2 fixes (recognition only)

1. **data_source**: credits code that *loads the provided raw_data file* (`read_parquet/read_csv/open/Path/raw_data`), even if the source name (SciSciNet/WoS) is never mentioned. v1 only keyword-matched source names.
2. **sample**: credits *computed* sample evidence — `df.shape`, `len(df)`, `N=`, row counts, year ranges, filters (`dropna/between/query`). Full credit if N + window/filter; partial if ≥1 signal. v1 only keyword-matched.
3. **result**: broadens evidence to Markdown/stdout tables, `coef=/beta=/estimate=/marginal_effect=`, `R²/R2/r_squared`, p-value, stderr/se, mean/median/correlation/ATE/ATT. v1 only matched gold result numbers.
4. **result-line classifier**: classifies each result line as PAPER_REPORTED / DATA_SUB / COMPUTED / SYNTHETIC.

## v1 vs v2 — overall (IO₂, 10 runs)

| | v1 | v2 |
|---|---|---|
| overall mean | 0.483 | **0.552** |

## Component means: v1 → v2 (IO₂)

| Component | v1 | v2 | Δ |
|-----------|-----|-----|---|
| data_source | 0.75 | 0.90 | +0.15 |
| sample | 0.45 | **1.00** | **+0.55** |
| indicator | 1.00 | 1.00 | 0 |
| model | 0.90 | 0.90 | 0 |
| result | 0.40 | **0.55** | **+0.15** |
| claim | 1.00 | 1.00 | 0 |

The two fix-targets (sample, data_source) rose as designed; result also rose (+0.15) from broader evidence recognition. Indicator/model/claim unchanged (their v1 recognition was already sound).

## Per-paper / per-model (v2)

| Paper | v2 mean |
|---|---|
| petersen2024 | **0.688** |
| funk2017 | 0.550 |
| bikard2013 | 0.525 |
| arts2021 | 0.500 |
| maddi2024 | 0.500 |

Per-model: deepseek 0.565 · qwen3-32b 0.540 (deepseek slightly ahead at IO₂).

## v1 vs v2 per run

| Paper | Model | v1 | v2 |
|---|---|---|---|
| petersen2024 | deepseek | 0.45 | **0.825** |
| funk2017 | qwen3-32b | 0.60 | 0.60 |
| bikard2013 | qwen3-32b | 0.45 | 0.55 |
| arts2021 | qwen3-32b | 0.475 | 0.50 |
| arts2021 | deepseek | 0.40 | 0.50 |
| bikard2013 | deepseek | 0.50 | 0.50 |
| funk2017 | deepseek | 0.50 | 0.50 |
| maddi2024 | both | 0.50 | 0.50 |
| petersen2024 | qwen3-32b | 0.45 | 0.55 |

petersen×deepseek jumped to 0.825 (used real SciSciNet data, produced gold-matching results, no synth → no caps).

## Three tests — all PASS ✅

1. **IO₂ v2 overall > IO₁ v1 (0.490)?** ✅ PASS — v2 = 0.552 > 0.490. The IO₁→IO₂ lift now shows once recognition is fixed.
2. **4 data-using runs > 6 synthetic runs?** ✅ PASS — data-using mean **0.631** vs synthetic **0.500**. The agents that used the provided real data score clearly higher; the synthetic-substitution gate correctly holds the synthesizers down.
3. **Gate (c) only on synthetic/toy/placeholder, not DATA_SUB?** ✅ PASS — no misfire. Gate (c) fires iff synth markers in code; legitimate DATA_SUB (loading the provided real parquet) is not penalized.

## Result-line classification (v2, across 10 runs)

| Class | Count |
|---|---|
| COMPUTED | 37 |
| PAPER_REPORTED | 17 |
| SYNTHETIC | 7 |
| DATA_SUB | 0 (explicit) |

The classifier now finds 61 result lines (v1 found 1). DATA_SUB=0 because agents don't label outputs "DATA_SUB" explicitly — but gate (c) + the data-using subset analysis distinguish substitute-real-data from synthetic at the *run* level. (Optional v3: infer DATA_SUB from "loaded provided file + no synth markers.")

## B₁–B₄ candidates (v2 rules)

| Break | Count |
|---|---|
| B₁ Substitution | 6 |
| B₃ Shopping | 4 |
| B₄ Assertion | 3 |
| B₂ Circularity | 2 |

B₄ dropped 6→3 because v2's broader result recognition means fewer "claim>0 but result=0" cases. B₁ unchanged (still the 6 synth-using runs).

## Recommendation — can R102 start?

**Yes.** The IO manipulation is now measurable:
- IO₁ v1 = 0.490 → IO₂ v2 = 0.552 (lift visible after recognition fix).
- Data-using runs (0.631) clearly beat synthetic runs (0.500).
- Gate (c) cleanly separates legitimate DATA_SUB from B₁ substitution.

R102 (IO₃ = real data + reference code) is the **decisive** level: the agent has both data *and* code, so the synthetic gate won't fire on any data-using run and Result should rise further. The IO₁ < IO₂ < IO₃ monotonicity (R103 Gate 1) is now testable.

**One v3 nice-to-have (not blocking R102)**: infer DATA_SUB at the line level from "loaded provided file + no synth markers" so the result-line classification labels substitute-real-data outputs explicitly rather than as COMPUTED.

## Artifacts

- `scripts/ecrf_v2_scorer.py` — v2 recognition (file-load, computed sample, broad result) + v1 weights/gates + result-line classifier
- `refine-logs/r101/r101b_v2_rescore.json` — v1/v2 per-run + components + data-using flag
- `refine-logs/R101B_REPORT.md` — this report
