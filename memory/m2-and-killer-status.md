---
name: m2-and-killer-status
description: M2 qwen3 full done (50/51 runs); v2 rescore IO1=0.50 IO2=0.49 IO3=0.60; 6 Study-3 killer cases found
metadata: 
  node_type: memory
  type: project
  originSessionId: 344d8c16-083b-410f-ad0c-b2a6a5c479f2
---

**M2 Study 2 qwen3 single-model run — COMPLETE (2026-07-01/02):**
- 20 papers × IO levels, 50/51 DONE (1 NO_CODE). wave2 on .41 (28/30) + wave3b on .42 (23/24, after .41 vLLM hung).
- v2 rescore (r122_freeze/ecrf_v2_scorer.py, final_ecrf with v1 weights+caps): **IO1 mean=0.496, IO2=0.490, IO3=0.595 (n=11 clean-IO₃ anchors)**.
- v2 fixes v0 ceiling-inflation: IO1/IO2 capped ~0.5 (synthetic-substitute / no-exec-result / result=0 caps); IO3 rises with real data+code. IO1≈IO2 reflects B₁ non-compliance (agents synthesize despite being given real data at IO2 → cap 0.5).
- Tables: `refine-logs/r122/R122_V2_RESCORE.md`.

**Study 3 killer panel — 6 B₁ cases found (2026-07-02):** see `refine-logs/r122/R122_B1_KILLER_CASES.md`.
- Scan of 20 IO₂ runs: 6 cases where agent was given real data, synthesized/substituted, yet produced direction/number matches → R₂ would label "Supported" but R₃ flags M₁ (+M₂ paper-numbers-as-computed). Exceeds ≥3-cases-≥2-modes gate.
- Strongest: **park2023 io2** — given sciscinet parquet, read_parquet failed ("Missing required columns"), fell back to np.random citation network, computed "declining" trend (slope -0.000419) on RANDOM data, printed `PAPER_REPORTED_TREND_DIRECTION=declining` matching paper. R₂=Supported, R₃=M₁. S-directional killer (exactly as external review predicted).
- donner2024: given real donner_data.csv + parquet, still synthesized (USE_SYNTHETIC=True).
- 6/20 IO₂ runs (30%) show trust-inflation → headline C1 evidence.

**Next (Study 3 closure):** (1) implement same-trace R₂ (FactReview-style claim audit) on these 6 traces, confirm R₂ labels them "Supported" (pre-registered killer condition); (2) blinded human adjudication of the 6; (3) full FRR ladder FRR(R₁)>FRR(R₂)>FRR(R₂₊)>FRR(R₃) + McNemar. R₂₊ = R₂ + provenance + hard-code scanner.

**All 20 IO packages built** (dev worktree): 8 with IO₃ (petersen, wu2019, park2023, bentley2023, funk2017, obadage2024, liu2018, arts2021_patent_nlp) + 12 boundary (IO₁/IO₂ only). Runner `scripts/run_m2_study2_batch.py` (--papers, --skip-existing, per-model vLLM routing). PAPER_GOLD for all 20.

Related: [[research-review-v8.1-outcome]], [[factreview-closest-prior-art]], [[parallel-worktree-setup]], [[session-start-v8-dev]]
