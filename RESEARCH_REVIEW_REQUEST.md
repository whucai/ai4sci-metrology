# Research Review Request — v8.1 AI-Agent Metrology of Computational Reproducibility

**Requester**: Claude (for the author)
**Date**: 2026-06-29
**Artifact path**: `refine-logs/COMPLETE_EXPERIMENT_IDEA_V8.1.md` (also inlined below)
**Reviewer role**: Senior ML / Science-of-Science reviewer (NeurIPS D&B / ICML / MISQ level). Be brutally honest.

---

## What to review

A complete research plan (theory + 4 studies + paper pool + run order + falsification). The contribution is a **measurement instrument**, not a benchmark: an AI agent reproduces a computational paper and is scored, per evidence-chain component, on reconstruction fidelity (ECRF). The headline claim is **trust inflation** — the gap between result-level reproduction verdicts and component-level validity — and that even the closest prior art (FactReview) suffers it.

## Background the reviewer needs

**Closest prior art — FactReview (Yue et al., 2026, arXiv:2604.04074):** a reviewing system that extracts claims from a manuscript, grounds them in related work, and executes released code under a fixed repair budget (K=3, wrapper-only fixes) to assign 4-status claim verdicts (Supported / Partially-supported / In-conflict / Inconclusive). 35 ML papers, 463 claims, 84% coverage; removing execution evidence changes 17% of verdicts (largest single source); reviews score 4.86/5. Explicitly: "LLM reviewers should audit empirical claims, not make accept-reject decisions."

**Other prior art:** RPC-Bench (Chen et al. 2026, 15K QA, comprehension-only, GPT-5 37.46% Informativeness — motivation, not competition); Theiler 2026 (paper→benchmark agent, PHM-domain-locked); SRI/Hossain 2025 (per-cell notebook reproducibility, no agent); Kapoor & Narayanan 2022 (human leakage audit). Existing agent benchmarks (PaperBench, ScienceAgentBench, MLE-bench, MLAgentBench) are leaderboards measuring task success, not component-resolved fidelity.

**Pilot status (real, already run):** M0 (6 papers, 3 STRICT at D3=100%); M1 (10-paper framework validation, all 4 tests PASS); R100–R103 mini-Study-2 pilot (5 papers × 3 IO × 2 models = 30 runs) — **all 4 green-light gates passed**: G1 ECRF IO₁<IO₃ in 4/5 papers (0.497<0.713); G2 3 IO-sensitive components; G3 7 result-vs-component disagreements; G4 42 B-candidates (B₁=19 confirmed). SciSciBench 115-paper baseline (L2=0.907). R003 localized Arts2021 bug to formula lines 233–236 (proves component-level diagnosis works).

## The complete experiment idea (v8.1, inlined)

### One-line
Treat an AI agent that reproduces a computational paper as a **measurement instrument**, define a component-resolved reproduction-fidelity metric (ECRF), and show that the field's accessible reproducibility signal (result-matching, and even FactReview-style claim-level execution audit) carries systematic **trust inflation** that component-level audit corrects — then link that fidelity to scientometric impact.

### Theory chain: IO → ECRF → RIB
- **IO (Information Observability)**, 3-level manipulated treatment: IO₁ narrative (paper text only) / IO₂ structured docs + raw data, no code / IO₃ full executable (data + reference code).
- **ECRF (Evidence-Chain Reconstruction Fidelity)**: per-component score on Data → Sample → Indicator → Model → Result → Claim.
- **RIB (Result-Indicator Bias)** = FRR (False Reproduction Rate) = P(verdict=valid | components invalid).
- 4 structural failure modes: M₁ Substitution (right number, wrong data path) / M₂ Circularity (paper values hard-coded as outputs) / M₃ Shopping (undisclosed spec search) / M₄ Assertion (claims unsupported by outputs).

### Novelty vs. FactReview (4 structural differentiators)
| Axis | FactReview (closest) | This work |
|---|---|---|
| D1 Unit of analysis | the claim (4 statuses) | the evidence-chain component (6, per-component fidelity) |
| D2 Observability | binary code-on/off + post-hoc ablation | 3-level causal treatment (IO₁/IO₂/IO₃) |
| D3 Trust inflation | no concept | FRR(result) vs FRR(component) = primary DV |
| D4 Scientometric link | none | ECRF ↔ citations / CD-index / altmetrics / team size |

**Structural wedge:** R₂ (FactReview-style) executes the *released* repo; its agent never chooses data/sample → it is **M₁-invisible by construction**. ECRF's setting (agent reconstructs *from the paper* at IO₁/IO₂) is where M₁ lives.

### Four studies
- **Study 1 (construct validation):** ECRF is multi-dimensional. Re-analyze M0/M1. *Largely done.*
- **Study 2 (input sensitivity, C2):** 20 papers × 3 IO × 2 models = 120 runs. H1 monotonic ECRF IO₁→IO₃; H2 significant Component×IO interaction. Isolated Docker `--network none`, randomized order, pre-registered. *Pilot already 4-gate green.*
- **Study 3 (MAIN, C1):** three regimes on the same runs. R₁ result-level / **R₂ FactReview-style claim-level execution audit (faithfully replicated + calibrated on FactReview's 35-paper set)** / R₃ ECRF component-level (task-contingent). **Headline: FRR(R₁)>FRR(R₂)>FRR(R₃), McNemar p<0.05.** **Killer:** ≥3 human-adjudicated cases where R₂="Supported" but R₃ reveals M₁/M₂ — invisible to R₂ by construction. Generalization asymmetry: R₂ Inconclusive at IO₁/IO₂; R₃ still scores.
- **Study 4 (scientometric capstone, C3):** regress ECRF on citations/CD-index/altmetrics/team size over 20-paper deep set + 115-paper SciSciBench substrate. Pre-registered Hₛ₁–Hₛ₃. No prior execution-audit work can test this (IV didn't exist).

### Paper pool (R120, finalized)
20 papers × 3 IO × 2 models. Domain SoS 8 / IS 6 / Mgmt 6 (19 stable + 1 Mgmt slot pending). Strata by predicted ECRF slope: Low 5 / Med 8 / High 6. 7 clean-IO₃ anchors (Petersen2024, Wu2019, Park2023, Bentley2023, Funk2017, Obadage2024, Liu2018-hotstreaks). 3 data-unavailable boundary cases (Maddi2024, Schaper2025, Bikard2013). Known localized breaks: Arts2021 (Indicator), Wu2019 (Model/Claim). Models: Qwen3-32B / DeepSeek-V3/V4-Pro / frontier GPT-4o+Claude Opus (robustness subset only, ~54 runs).

### Run order
M1 pilot (done) → M2 Study 2 full 120 runs (gated on R121 Layer-1 gold chains, 2-annotator, in draft) → M3 Study 3 (R₁/R₂/R₃ + M₁–M₄ adjudication + Layer-2 validity) → M4 simplicity (R₃ vs overbuilt R₃′ vs threshold-lowered R₂) → M5 frontier robustness → M6 Study 4 regression.

### Falsification
- FRR(R₂) ≈ FRR(R₃) → C1 collapses to "FactReview already fixes result-level bias"; contribution shrinks to D2+D4 (pre-registered fallback).
- No R₂="Supported"/R₃=M₁-or-M₂ case in 120 runs → "invisible by construction" becomes theoretical only; weaken to "component audit localizes breaks."
- IO gradient absent at frontier → scope statement, not theory death.
- Study 4 null → ECRF still a valid instrument; "reproducibility not correlated with impact" is itself publishable.

### Venue (open)
Scientometrics (Springer) safe default. Higher-tier candidates under review: NHB/SciAdv/PNAS; MISQ/MgmtSci/ISR; NeurIPS D&B/ICML. Core theory D1–D4 venue-agnostic.

## Specific review questions

1. **Does this land for a top venue?** Is the contribution (component-resolved ECRF + trust inflation + FactReview-as-baseline + scientometric link) strong enough for NeurIPS D&B / ICML / MISQ / NHB, or is it "FactReview but finer-grained" (incremental)?
2. **Is the FactReview-as-R₂-baseline contrast convincing?** Specifically: is the "M₁-invisible by construction" argument sound, or can FactReview be extended trivially to detect substitution (making D1 incremental)? Is faithfully replicating FactReview and then beating it a credible experimental design, or a setup where the baseline is forced to lose?
3. **Is the killer experiment sound?** The target is ≥3 human-adjudicated cases where R₂="Supported" but R₃=M₁/M₂, in 120 runs. Is N=3 persuasive? Is the case-finding protocol (automated rule → audit trace → 2-reviewer adjudication) free of confirmation bias? How would a skeptical reviewer attack the case selection?
4. **Is Study 2 (IO causal manipulation) actually causal?** The 3 IO levels are constructed by the experimenter per paper. Threats to internal validity: paper-specific IO construction, non-random assignment of papers to strata, model confounds. Is the causal claim defensible, or should it be downgraded to "input sensitivity"?
5. **Is Study 4 (scientometric linkage) defensible?** 20 deep + 115 substrate papers, observational, confounded by field/year/team-size. Is regressing ECRF on citations/CD-index credible, or over-claiming? Should Study 4 be cut or demoted to exploratory?
6. **What's the minimum experiment package for the highest acceptance lift per GPU week?** Given the pilot is already green, what additional runs/analyses most increase acceptance probability?
7. **Results-to-claims matrix:** For each possible outcome of (Study 2 IO gradient, Study 3 FRR ladder, Study 4 correlation), what claim is licensed?
8. **Mock NeurIPS review** with Summary / Strengths / Weaknesses / Questions / Score / Confidence / "what would move toward accept."

## Honest weaknesses the author already sees
- Study 4 is observational and confounded; may be over-claiming.
- N=3 killer cases is small; case-finding could be seen as cherry-picking.
- ECRF per-component scoring is LLM-judged → reliability concern; Layer-1/2 human validation is the mitigation but α may be low on some components (e.g., Claim).
- "Faithful FactReview replication" risks either (a) being a strawman if under-specified, or (b) being exactly as good as FactReview on claim-level tasks, leaving D1 (component) as the only wedge — which reviewers may call incremental.
- The agent harness is the authors' own (SciSciGPT-local) → A4 (harness artifact) confound.

Please read `refine-logs/COMPLETE_EXPERIMENT_IDEA_V8.1.md` and `refine-logs/EXPERIMENT_PLAN.md` (Block 3a has the full R₂ replication spec) for detail, then deliver the review.
