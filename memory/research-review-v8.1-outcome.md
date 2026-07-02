---
name: research-review-v8-1-outcome
description: External Codex review of v8.1 (3 rounds) — same-object fix rescued design to 7/10; R2+ is the real novelty threat
metadata: 
  node_type: memory
  type: project
  originSessionId: 344d8c16-083b-410f-ad0c-b2a6a5c479f2
---

On 2026-06-29 ran `/research-review` (Codex gpt-5.5, xhigh, 3 rounds, threadId `019f1188-f6ca-7322-bcbd-b9bd49bfbe4c`) on the v8.1 complete experiment idea. Artifacts on dev worktree: `RESEARCH_REVIEW.md` (standalone), `RESEARCH_REVIEW_REQUEST/ROUND_2/ROUND_3.md`, `.aris/traces/research-review/2026-06-29_run01/`.

**Verdict:** original design **5/10** (borderline) with a decisive baseline-alignment flaw; revised design reaches **7/10** with no remaining fatal structural flaw — only empirical risk.

**The flaw that almost sank it (Round 1):** R₂ = FactReview on the *released repo* while R₃ = component audit of the *agent's reconstruction* = **two different objects**. "R₂=Supported, R₃=M₁" then only proves the released repo supports the claim while the agent reconstructed it wrongly, NOT that FactReview failed.

**The fix (Round 2, accepted):** R₁/R₂/R₂₊/R₃ all score the **same agent reproduction trace**. R₂ = FactReview-style claim verdict on the agent's trace (no component provenance). **R₂₊ = R₂ + provenance check + hard-code scanner** (the "FactReview extended" baseline reviewers demand). R₃ = component audit of same trace. Original FactReview-on-released-repo → separate **prior-art calibration cell** (35-paper), NOT head-to-head.

**R₂₊ is the real novelty threat.** Pre-register FRR(R₂) > FRR(R₂₊) > FRR(R₃). If FRR(R₂₊) ≈ FRR(R₃), D1 detection claim collapses → fallback: D1 = **continuous per-component fidelity score** enabling Study 2 Component×IO + Study 4 correlation (R₂₊ gives binary flags, not continuous scores). Carried by Study 2 + reliability + localization, NOT Study 4.

**Killer-case operationalization (Round 3):** panel = "process-invalid supported cases", split **S-exact** (numeric match + invalid; M₂ populates, M₁ rare ~1–5%) and **S-directional** (directional match + invalid; M₁ ~10–25%). Fair-baseline rule: R₂ may call "Supported" only at the extracted claim's evidence-target granularity; pre-register before scoring; report Supported-exact vs Supported-directional separately. Metric: P(R₂/R₂₊=Supported | R₃=invalid), bootstrap CI, full denominator, blinded.

**Other downgrades:** Study 2 → "controlled input-sensitivity intervention" (not population-causal). Study 4 → exploratory (appendix for NeurIPS/ICML). Reliability gates (R121 gold chains, per-component α/ICC, repeat seed 36 runs) are load-bearing — without them the continuous-measurement fallback collapses.

**17-item prioritized TODO** with stop-the-presses gates in `RESEARCH_REVIEW.md`. Next concrete steps: (1) rewrite Block 3a to same-trace R₂/R₂₊ + calibration cell; (2) fill pool slot #20 + freeze R120; (3) freeze R121 gold chains; (4) lock scorers/schema before runs.

Related: [[factreview-closest-prior-art]], [[evidence-chain-theory-v7.2]], [[parallel-worktree-setup]]
