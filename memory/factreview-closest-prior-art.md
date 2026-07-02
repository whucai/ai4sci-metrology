---
name: factreview-closest-prior-art
description: "FactReview (Yue 2026) is the closest prior work to ECRF; novelty re-grounded on D1-D4, v8.1 on dev"
metadata: 
  node_type: memory
  type: project
  originSessionId: 344d8c16-083b-410f-ad0c-b2a6a5c479f2
---

On 2026-06-25 two 2026 papers were ingested into research-wiki and forced a novelty re-run for the evidence-chain idea: **FactReview** (Yue et al., arXiv:2604.04074, 2026-05-27) and **RPC-Bench** (Chen et al., arXiv:2601.14289, 2026-04-30). Both were missed by the 2026-06-24 v8 novelty check (59 papers; both are 2026).

**FactReview is now the closest prior work** — it executes released code (K=3 wrapper-only repair) to assign 4-status claim verdicts (Supported/Partial/In-conflict/Inconclusive); manuscript+lit+execution evidence; 35 ML papers/463 claims; **removing execution evidence changes 17% of verdicts**. This partially breaches the v8 claim "no prior work combines agent-reproduces-paper + component-fidelity + reproduction-as-measurement-instrument" — FactReview does (a)+partial-(b) at the *claim* level.

**Novelty re-grounded on 4 structural differentiators (D1–D4), not "no prior execution audit":**
- D1 unit = evidence-chain component (Data→Sample→Indicator→Model→Result→Claim), not the claim
- D2 IO = 3-level causal treatment (IO₁ narrative / IO₂ structured-docs-no-code / IO₃ executable), not FactReview's binary code-on/off + observational ablation
- D3 trust inflation (result-vs-component gap, RIB/FRR) = primary DV — FactReview has no concept
- D4 scientometric linkage (Study 4) — FactReview has none
- Plus B₁–B₄ structural breaks vs FactReview's pipeline failures; FactReview is **B₁-invisible by construction** (agent runs the *released* repo, never chooses data/sample).

**Strongest move:** reposition FactReview as the **R₂ baseline in Study 3** (claim-level execution audit, not a strawman). H4 = TIR/FRR(R₂) > FRR(R₃) — even FactReview-style claim audit inflates trust vs component audit. Killer result: cases where FactReview labels "Supported" (numbers reproduce) but ECRF reveals M₁ (data-path substitution → coincidentally similar numbers) or M₂ (paper values hard-coded) — invisible to FactReview by construction. N=3–5 human-adjudicated cases = decisive.

**RPC-Bench = low threat / motivation only.** 15K QA from review-rebuttal, 9-cat comprehension taxonomy, GPT-5 only 37.46% Informativeness. No execution, no IO, no components, no fidelity metric. Use as the comprehension-ceiling motivation.

**Venue opened (v8.1):** not locked to Scientometrics. Candidates under external review: NHB/SciAdv/PNAS; MISQ/MgmtSci/ISR (v7 governance lineage); NeurIPS D&B/ICML (benchmark+contrast headline). Scientometrics stays safe default (FactReview is a CS/ML tool, not direct competition there). Core theory D1–D4 venue-agnostic.

**Deliverables on dev (committed):** `refine-logs/NOVELTY_ASSERTION_V8.md` (formal re-run), `refine-logs/ADJUSTMENT_RPC_FACTREVIEW.md` (memo), updated `idea-stage/IDEA_REPORT.md` §5 + title, `refine-logs/FINAL_PROPOSAL.md`, `refine-logs/EXPERIMENT_PLAN.md` (C1/M3/Block 3 + R₂=FactReview-style). research-wiki now 60 papers / 17 edges.

Related: [[evidence-chain-theory-v7.2]], [[scientometrics-pivot-v8]], [[git-sync-policy]]
