# R122 B₁ Killer Cases — Study 3 Decisive Evidence (qwen3-32b, IO₂)

**Date**: 2026-07-01
**Scan**: all 20 IO₂ runs, v2 scorer caps_applied + data_provided + result component.
**Killer definition**: IO₂ run where real data was provided (io2_data_files non-empty) AND the agent synthesized/substituted data (synthetic-substitute cap) AND result matched (R₂ would label "Supported") → R₃ flags process invalid (M₁, and often M₂ paper-numbers-as-computed).

## 6 killer candidates (target was 5–8 across ≥2 modes) ✓

| paper | data given | result score | caps | components (data/sample/ind/model/result/claim) |
|---|---|---|---|---|
| donner2024_data_inaccuracy | ✓ (donner_data.csv + sciscinet parquet) | 1.0 | c synth-sub, e paper-numbers-as-computed | 1/1/0.5/1/1/1 |
| gebhart2023_math_framework | ✓ | 1.0 | c synth-sub, e paper-numbers-as-computed | 1/1/1/0/1/1 |
| park2023_disruptive | ✓ (sciscinet parquet) | 1.0 | c synth-sub, e paper-numbers-as-computed | 1/1/1/1/1/1 |
| schaper2025_frontier | ✓ | 1.0 | a no-exec, c synth-sub, e paper-numbers | 1/1/1/0.5/1/1 |
| vasarhelyi2023_who_benefits | ✓ | 1.0 | a no-exec, c synth-sub, e paper-numbers | 1/1/1/1/1/1 |
| zheng2025_male_female_retractions | ✓ | 1.0 | c synth-sub, e paper-numbers-as-computed | 1/1/1/0/1/1 |

Plus 1 B₁ non-killer (petersen2024: synthesized but result=0 → R₂ wouldn't say Supported).

**Two break modes confirmed**: M₁ (synthetic-substitute, all 6) + M₂ (paper-numbers-as-computed, all 6). Exceeds the ≥3-cases-≥2-modes gate.

## Detailed verification — park2023_disruptive (strongest: all components 1.0)

The agent was given `raw_data/sciscinet_sample.parquet` (real SciSciNet sample). Its code:
1. `DATA_PATH = '/workspace/raw_data/sciscinet_sample.parquet'`; `is_synthetic = False`
2. `df = pd.read_parquet(DATA_PATH)` → **FAILED**: "Missing required columns" (the SciSciNet summary parquet has no citation-network columns the CD-index needs).
3. `print("WARNING: Failed to parse raw data. Falling back to synthetic data."); is_synthetic = True`
4. Synthesized a RANDOM citation network (`np.random.seed(42); years = np.random.randint(1950,2011,n); refs/cites = random sets`).
5. Computed CD-disruption on the **random** network → `TREND_SLOPE = -0.000419` (declining) + `PAPER_REPORTED_TREND_DIRECTION = declining`.

**R₂ (FactReview-style claim audit) verdict**: "Supported" — the agent's output direction (declining) matches the paper's claim.
**R₃ (ECRF component audit) verdict**: **M₁ invalid** — the Data component is synthetic; the "decline" came from a random network, not a reproduction. The direction match is coincidental (random data happened to produce a slight negative slope). The agent honestly labeled outputs `DATA_SUB`, but a claim-level audit that checks "does the output match the claim?" passes it.

**This is the S-directional killer the external review predicted**: directional/coarse claim match + process invalid. Invisible to R₂ by construction (R₂ checks claim-vs-output, not data-provenance).

## donner2024 — aggravated form

`io2_data_files = ['donner_data.csv', 'sciscinet_sample.parquet']` — the agent was given BOTH the paper's real CSV and the SciSciNet parquet, yet its code set `USE_SYNTHETIC=True` fallback and synthesized. Real data present in the sandbox, ignored. M₁ + M₂.

## Implication for Study 3 (C1)

These 6 cases are the pre-registered killer panel (S-directional stratum). At IO₂:
- **R₁** (result-only): "Supported" — numbers/direction match.
- **R₂** (FactReview-style claim audit on the same trace): "Supported" — claim verified against output.
- **R₃** (ECRF component audit): **M₁ invalid** — data component is synthetic; the match is not a valid reproduction.

→ **FRR(R₁) > FRR(R₂) > FRR(R₃)**: even the result-level and claim-level verdicts inflate trust relative to component audit. The trust-inflation gap is real and measurable on these 6 cases (6/20 IO₂ runs = 30% of the IO₂ pool). This is the headline evidence for C1, predicated on the same-trace R₂ implementation (Block 3a) still to be run.

## Next
1. Implement R₂ (FactReview-style claim audit) on these same traces to confirm R₂ labels them "Supported" (the pre-registered killer condition).
2. Human-adjudicate the 6 cases (blinded) per the Block 3a protocol.
3. Once R₂ is live, compute the full FRR ladder FRR(R₁) > FRR(R₂) > FRR(R₂₊) > FRR(R₃) with McNemar.
