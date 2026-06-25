# Novelty Assertion (v8, re-run 2026-06-25)

**Trigger:** RPC-Bench (chen2026, arXiv:2601.14289) + FactReview (yue2026, arXiv:2604.04074) ingested into research-wiki (60 papers, 17 edges). Both post-date the 2026-06-24 v8 novelty check (59 papers) and were missed.

**Verdict:** The original v8 novelty claim — "no verified prior work combines (a) agent reproduces a published computational paper + (b) evidence-chain-component fidelity metric + (c) reproduction-as-measurement-instrument" — is **partially breached by FactReview**, which does (a) + partial-(b) at the *claim* level. The novelty must be re-grounded on four **structural** differentiators (D1–D4), not on the absence of execution-audit prior art.

---

## Closest-prior-art ranking (revised)

| Rank | Work | What it does | What it lacks (ECRF novelty space) |
|------|------|--------------|------------------------------------|
| **1 (closest)** | **FactReview (Yue et al. 2026)** | Agent executes released code (K=3 wrapper repair) → 4-status claim verdicts (Supported/Partial/In-conflict/Inconclusive); manuscript+lit+execution evidence; 35 ML papers/463 claims; **17% verdict change on removing execution** | D1 claim-level not component-level; D2 binary code-on/off + observational ablation, not causal IO; D3 no trust-inflation concept; D4 no scientometric link; B₁-invisible by construction (agent runs given repo, never chooses data) |
| 2 | Theiler et al. 2026 | Paper→benchmark agent (slot-binding interface, 16 PHM papers) | Domain-locked to PHM; outputs benchmark implementation, not a *measurement of where reproduction fails* |
| 3 | SRI / Hossain et al. 2025 | Per-cell notebook reproducibility index | Notebook reruns, no AI agent, no paper→code; components are notebook cells, not evidence-chain links |
| 4 | Kapoor & Narayanan 2022 | Leakage audit across ML-science | *Human* retrospective audit, not agent reproduction; no live per-component failure map |
| (motivation) | RPC-Bench (Chen et al. 2026) | 15K QA, 9-cat comprehension taxonomy; GPT-5 37.46% Informativeness | Comprehension only — no execution, no IO, no components, no fidelity metric. **Not a competitor**; establishes the comprehension ceiling that motivates a reconstruction-level instrument |

## The four structural differentiators (the new novelty core)

| Axis | FactReview (claim-level) | ECRF (component-level) |
|------|--------------------------|------------------------|
| **D1 — Unit of analysis** | The *claim* → 4 statuses | The **evidence-chain component** (Data→Sample→Indicator→Model→Result→Claim), per-component fidelity score that *localizes where* reconstruction breaks |
| **D2 — Information observability** | Code availability = **binary**; ablation is *post-hoc source removal* (observational) | IO = **3-level manipulated treatment** (IO₁ narrative / IO₂ structured-docs-no-code / IO₃ executable); causal identification of IO→fidelity |
| **D3 — Trust inflation (primary DV)** | No concept; "Partial" flags overbroad scope only | **Result-vs-component validity gap** (RIB / FRR) — the gap between "numbers reproduced" and "components validly reconstructed" |
| **D4 — Scientometric linkage** | None | **Study 4**: ECRF ↔ citations / CD-disruption / altmetrics / team size — a field instrument producing a new scientometric variable |

**Plus:** B₁–B₄ **structural break taxonomy** (Substitution / Circularity / Shopping / Assertion) vs FactReview's *pipeline* failures (env/runtime/metric/alignment). FactReview executes the *released* repo, so its agent never chooses data/sample — it is **structurally blind to B₁ (data/sample substitution)**, which is exactly where ECRF's killer cases live.

## Re-derived novelty statement

> No prior work treats AI paper reproduction as a **component-resolved measurement instrument** with (D1) a Data→Sample→Indicator→Model→Result→Claim unit of analysis, (D2) information observability as a causally manipulated 3-level treatment, (D3) trust inflation — the gap between result-level and component-level validity — as the primary dependent variable, and (D4) a link from reproduction fidelity to scientometric impact. FactReview (Yue et al., 2026) is the closest prior work: it executes released code to assign claim-level verdicts and shows execution evidence changes 17% of verdicts. ECRF generalizes FactReview's binary code-on/off ablation into a 3-level causal IO ladder, shifts the unit of analysis from claim to evidence-chain component, introduces trust inflation as the primary DV (showing even FactReview-style claim audit inflates trust relative to component audit), and connects fidelity to scientometric impact — none of which FactReview, Theiler, SRI, or Kapoor do.

## Strongest empirical move (turns closest competitor into a baseline)

Study 3 re-specification: R₂ = **FactReview-style claim-level execution audit** (manuscript+lit+code-execution+4-status verdicts). R₃ = ECRF component-level audit. **H4: TIR(R₂) > TIR(R₃)** — even execution-based claim audit inflates trust relative to component audit. Killer result: cases where FactReview would label "Supported" (numbers reproduce) but ECRF reveals B₁ (data-path substitution → coincidentally similar numbers) or B₂ (paper values hard-coded as outputs). These are **invisible to FactReview by construction**. N=3–5 human-adjudicated cases = decisive.

## Venue note (open)

Originally targeted at *Scientometrics* (Springer). Given D1–D4 + the FactReview-as-baseline contrast, the contribution is strong enough for higher-tier venues. Candidates (no commitment):
- **Nature Human Behaviour / Science Advances** — if Study 4 (reproducibility-as-scientometric-variable) lands as a field-facing finding.
- **PNAS** — measurement-of-science fit.
- **MISQ / Management Science / ISR** — if the trust-inflation/governance angle (v7 lineage) is re-emphasized for an IS-governance audience.
- **NeurIPS Datasets & Benchmarks / ICML** — if the component-resolved benchmark + FactReview contrast is the headline.
- **Scientometrics (Springer)** — retained as a safe default; FactReview is a CS/ML tool, so Scientometrics readers won't see it as direct competition, and the "new scientometric variable" angle is clean there.

Decision deferred to external review (/research-review). The core theory (D1–D4, FactReview-as-R₂-baseline) is venue-agnostic.

## Status

- [x] RPC-Bench + FactReview ingested into research-wiki (60 papers, 17 edges)
- [x] Closest-prior-art ranking revised (FactReview = #1)
- [x] Novelty re-grounded on D1–D4
- [x] Study 3 R₂ re-specification (FactReview-style baseline) drafted
- [x] Venue opened (not locked to Scientometrics)
- [ ] Apply to `idea-stage/IDEA_REPORT.md` §5 + title/§8/§9
- [ ] Apply to `refine-logs/FINAL_PROPOSAL.md` + `EXPERIMENT_PLAN.md` Study 3
- [ ] External /research-review on the re-grounded framing
