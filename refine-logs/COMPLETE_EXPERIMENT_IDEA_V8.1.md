# Complete Experiment Idea (v8.1) — An AI-Agent Metrology of Computational Reproducibility

**Date**: 2026-06-29 (v8.1, dev worktree)
**One-line**: Treat an AI agent that reproduces a computational paper as a **measurement instrument**, define a component-resolved reproduction-fidelity metric (ECRF), and show that the field's accessible reproducibility signal (result-matching, and even FactReview-style claim-level execution audit) carries systematic **trust inflation** that component-level audit corrects — then link that fidelity to scientometric impact.

---

## 1. The question

Can we measure, at scale and per-component, whether a published computational finding actually re-executes and reproduces — and does the most accessible verdict ("the numbers reproduced") systematically overstate true reproducibility?

Scientometrics measures impact, disruption, collaboration. It has **no instrument for execution-level reproducibility** of individual findings. Existing signals (data badges, code-on-GitHub flags, registered reports, rare human replications) are proxies; none produce a continuous, component-resolved, comparable fidelity measure. The closest automated prior art, **FactReview** (Yue et al. 2026), executes released code to label claims Supported/Partial/In-conflict/Inconclusive — but it operates at the *claim* level and treats code availability as binary.

## 2. Theory chain (one measurement model)

**IO → ECRF → RIB**

- **IO (Information Observability)**: degree to which each evidence-chain component is explicitly specified and accessible to the agent. Manipulated as 3 levels: IO₁ narrative (paper text only) / IO₂ structured docs + raw data, no code / IO₃ full executable (data + reference code).
- **ECRF (Evidence-Chain Reconstruction Fidelity)**: how accurately the agent reconstructs each component of Data → Sample → Indicator → Model → Result → Claim. Scored *per component*, not per claim.
- **RIB (Result-Indicator Bias)**: the gap between result-level verdict ("numbers reproduced") and component-level validity. Operationalized as **FRR (False Reproduction Rate)** = P(verdict = valid | components invalid).

Four structural failure modes (B₁–B₄ / M₁–M₄): **M₁ Substitution** (right number, wrong data path), **M₂ Circularity** (paper values hard-coded as outputs), **M₃ Shopping** (undisclosed spec search), **M₄ Assertion** (claims unsupported by outputs).

## 3. What's new vs. closest prior art (the novelty core)

| Axis | FactReview (closest) | This work |
|---|---|---|
| D1 Unit of analysis | the *claim* (4 statuses) | the *evidence-chain component* (6 components, per-component fidelity) |
| D2 Observability | binary code-on/off + post-hoc ablation | 3-level causal treatment (IO₁/IO₂/IO₃) |
| D3 Trust inflation | no concept | FRR(result) vs FRR(component) = primary DV |
| D4 Scientometric link | none | ECRF ↔ citations / CD-index / altmetrics / team size |

**Why R₂ (FactReview-style) is M₁-invisible by construction:** R₂ executes the *released* repo; its agent never chooses data/sample, so it cannot witness substitution. ECRF's setting — agent reconstructs *from the paper* at IO₁/IO₂ — is precisely where M₁ lives. That structural asymmetry is the empirical wedge.

RPC-Bench (Chen et al. 2026) is motivation only: GPT-5 = 37.46% Informativeness on paper comprehension — the comprehension ceiling that motivates a reconstruction-level instrument.

## 4. The four studies

### Study 1 — Construct validation: ECRF is multi-dimensional (Block 1, M0/M1 re-analysis)
Show ECRF components vary semi-independently (disagreement rate, error-localization rate, component correlation). Re-analyze M0 (6 papers, 3 STRICT) + M1 (10-paper framework validation). *Status: largely done (R110).*

### Study 2 — Input sensitivity: IO causally drives ECRF, asymmetrically (Block 2, C2)
**20 papers × 3 IO × 2 models = 120 runs.** Hypotheses: monotonic ECRF IO₁→IO₃ (H1); significant Component×IO interaction — some components (Data, Result) steep, others (Model) flat or dipping (H2). Isolated Docker `--network none` workspaces, randomized condition order, pre-registered seeds. *Pilot (R100–R103) already passed all 4 green-light gates; full pool R120 finalized (19/20 + 1 Mgmt slot pending).*

### Study 3 — MAIN: trust inflation + audit correction (Block 3a + 3 + 4 + 6, C1)
The dominant contribution. Three regimes on the **same runs**:
- **R₁** result-level (did numbers match?)
- **R₂** FactReview-style claim-level execution audit — **faithfully replicated** (MinerU parse → schema-constrained claim extraction → Semantic Scholar lit + RefCopilot → Docker Run-Review-Fix K=3 wrapper-only → 4-status verdicts). Calibrated against FactReview's own 35-paper benchmark (must reproduce their 4.86/5 rubric + 17%-status-change ablation within tolerance before trusting R₂ on our pool).
- **R₃** ECRF component-level audit (task-contingent).

**Headline result:** FRR(R₁) > FRR(R₂) > FRR(R₃), each gap McNemar p<0.05.
**Killer evidence:** ≥3 human-adjudicated cases where R₂ = "Supported" (released-code output matches the claimed number) but R₃ reveals M₁ (data-path substitution → coincidentally similar numbers) or M₂ (paper values hard-coded). These are invisible to R₂ by construction. Each case: automated rule → audit trace → two-reviewer adjudication.
**Generalization asymmetry:** R₂ is Inconclusive at IO₁/IO₂ (no executable); R₃ still scores components. Report the coverage fraction where R₂ can't run but R₃ can.

### Study 4 — Scientometric linkage (Block 7, C3, the field-facing capstone)
Regress agent-measured ECRF (and component-ECRF) on citations / CD-disruption / altmetrics / team size over the 20-paper deep set + the 115-paper SciSciBench substrate (join to OpenAlex/SciSciNet). Controls: field, year, team size. Pre-registered Hₛ₁–Hₛ₃. **No prior execution-audit work (incl. FactReview) can test this** — the IV didn't exist.

## 5. Paper pool (R120, finalized 2026-06-25)

20 papers × 3 IO × 2 models = 120 runs. Domain: SoS 8 / IS 6 / Mgmt 6 (restoring once #20 Mgmt slot filled; 19 stable now). Strata by *predicted ECRF slope* IO₁→IO₃: Low 5 / Medium 8 / High 6. Task types: STRICT 6 / METHOD 8 / DATA-SUB 5. **7 clean-IO₃ anchors** (Petersen2024, Wu2019, Park2023, Bentley2023, Funk2017, Obadage2024, Liu2018-hotstreaks). **3 data-unavailable boundary cases** (Maddi2024, Schaper2025, Bikard2013) where IO₂/IO₃ collapse — kept deliberately (1 boundary rule). Known localized breaks: Arts2021 (Indicator, R003 lines 233–236), Wu2019 (Model/Claim direction).

Models (tiered): open-weight Qwen3-32B (local) / low-cost DeepSeek-V3/V4-Pro API / frontier GPT-4o + Claude Opus (robustness subset only, ~54 runs).

## 6. Run order

M1 mini-pilot (done, R100–R103, 4 gates pass) → M2 Study 2 full (120 runs, gated on R121 Layer-1 gold chains, 2-annotator) → M3 Study 3 (R₁/R₂/R₃ re-scoring + M₁–M₄ adjudication + Layer-2 validity) → M4 simplicity (R₃ vs overbuilt R₃′ vs threshold-lowered R₂) → M5 frontier robustness → M6 Study 4 scientometric regression.

## 7. What success looks like (the paper's Figure 1 + Table 3)

- **Figure 1**: the IO→ECRF→RIB chain as a measurement model, with the 3-regime ladder R₁→R₂→R₃ showing FRR falling at each step and the R₂="Supported"/R₃=M₁ killer-case panel.
- **Table 3**: FRR(R₁), FRR(R₂), FRR(R₃) + McNemar p + bootstrap CI; the killer-case list with component localization.
- **Table 4 (Study 4)**: ECRF ↔ impact β, with component-ECRF ΔR² over result-match.

## 8. What would falsify it

- **FRR(R₂) ≈ FRR(R₃)** (no trust-inflation gap over claim-level audit) → C1 collapses to "result-level is biased, FactReview already fixes it"; contribution shrinks to D2 + D4. Pre-registered fallback.
- **No R₂="Supported"/R₃=M₁-or-M₂ case** in 120 runs → the "invisible by construction" claim is theoretical only; weaken to "component audit localizes breaks (Block 4)" without the killer contrast.
- **IO gradient absent at frontier** (A3) → scope statement, not theory death.
- **Study 4 null** → ECRF is still a valid measurement instrument; the scientometric capstone becomes "reproducibility is *not* correlated with impact" (itself a publishable finding).

## 9. Venue (open)

Scientometrics (Springer) is the safe default — FactReview is a CS/ML tool, not direct competition there; the "new scientometric variable" angle is clean. Given D1–D4 + the FactReview-as-baseline contrast, higher-tier candidates under external review: Nature Human Behaviour / Science Advances / PNAS (if Study 4 lands field-facing); MISQ / Management Science / ISR (v7 governance lineage); NeurIPS Datasets & Benchmarks / ICML (benchmark + contrast headline). Core theory D1–D4 is venue-agnostic.

## 10. Why this lands as a paper

It turns the closest competitor (FactReview) into the baseline, makes a *structural* not "deeper" contribution (component unit + causal IO + trust-inflation DV + scientometric link — four moves FactReview cannot make), has a pre-registered killer experiment with cases that are invisible to the baseline by construction, and delivers a field-facing capstone (Study 4) no prior execution-audit work can produce. Mini-pilot already passed all 4 green-light gates; the 20-paper pool is finalized.

---

**Status**: theory locked (v7.2); v8.1 novelty re-run done (FactReview = closest, D1–D4); R100–R103 pilot green; R120 pool 19/20; R121 gold-chains in draft (19/20, not frozen). Next concrete step: **R121 Layer-1 gold chains frozen → M2 Study 2 full (120 runs) → M3 Study 3 with the faithful R₂ replication**.
