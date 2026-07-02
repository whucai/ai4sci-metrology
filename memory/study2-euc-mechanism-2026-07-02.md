---
name: study2-euc-mechanism-2026-07-02
description: Study 2 (R122-R125) done — Evidence-Chain Uptake (H_EUC) mechanism finding; observability necessary not sufficient, uptake mediates
metadata:
  node_type: memory
  type: project
  originSessionId: current
---

**Study 2 complete (R122-R125, 105 runs, 18 papers × ≤3 IO × 2 models: qwen3-32b + deepseek-v4-pro).** The headline result is a **mechanism discovery**, not a benchmark.

**IO gradient (mean ECRF): IO₁ 0.499 → IO₂ 0.601 → IO₃ 0.591.** IO₃ does NOT exceed IO₂ — the "uptake bottleneck". Monotonicity IO₁<IO₃ holds for 11/18 papers; the 7 failures are SGF counterexamples.

**Core finding = Evidence-Chain Uptake Constraint (H_EUC), supersedes H_SGF (code-availability):**
- `real_data_used ∧ ¬synth` → **100% floor-break, mean 0.703** (n=15) — necessary + ~sufficient.
- `synth=True` → **0% break, mean 0.497** (gate c mechanical, structural agentic failure mode).
- `refcode_used` → 25% break (3/4 code-using runs still synthesized) — **neither necessary nor sufficient**.
- Counterexamples (code present/used but synth=True → 0.50): arts2021, liu2018 (refcode=True but synth!), obadage2024. Data>code break: petersen2024, park2023.
- Component×IO: data_source slope +0.368 (observability lifts data access), model slope −0.159, result +0.074 (execution bottleneck).

**R-robust-KU (4 checks, frozen R125): H_EUC holds in every config** — KU-excluded, KU-grouped (KU & non-KU identical pattern → not cluster-driven), clean-IO₃-anchors, boundary-excluded. IO₂<IO₃=NO in all (bottleneck structural).

**Theorem (UTD-style):** IO → material availability; U (uptake) → evidence use; ECRF → reconstruction fidelity. Observability necessary but not sufficient; agentic uptake mediates. Core sentence: "increasing observability (IO₃) is not sufficient to improve reconstruction fidelity; improvements occur only when agents actively incorporate real data and avoid synthetic substitution."

**R121 = independent model-family dual annotation with adjudication** (A=glm-5.2, B=codex-gpt-5.2 via Codex MCP), NOT human annotation. 3-round → α=0.945 overall, 6/6 components ≥0.70. Targeted human audit of borderline components scheduled later (off critical path).

**Frozen artifacts (refine-logs/r122_freeze/, immutable for R122-R124):** gold_v1_r3.json (sha 78efaa05), ecrf_v2_scorer.py + ecrf_v1_scorer.py (v1 weights: ds.10/sa.15/ind.15/mo.10/res.35/cl.15; gates a-e), io_manifests.json (60 pkgs), paper_gold.json (20-paper signals). Corrections via patch records only (patch_001 zheng2025_male RW registration-gated; patch_002 bikard2013 legacy parquet removed).

**Coverage gaps (legal OA recovery failed):** deng2023 (Scientometrics paywalled), galuez2023 (RISTI no DOI unindexed) — 2 papers excluded from IO₁. All others recovered (sun2023 PNAS, zheng2025_male arXiv, liu2018/obadage/arts_patent_nlp code repos, etc.).

**Reports:** R125_FULL_AGGREGATION.md, R125_SGF_VERDICT.md, R125_METHOD_3REGIMES_SGF.md, R_ROBUST_KU.md. Figures: figures/ai_generated/figure_final.png (native gpt-image-2, see [[codex-image2-mcp-wiring]]) + refine-logs/figures/fig1_sketch.png + fig_io1_io2_3layer.png.

Related: [[evidence-chain-theory-v7.2]], [[git-sync-policy]], [[codex-image2-mcp-wiring]]
