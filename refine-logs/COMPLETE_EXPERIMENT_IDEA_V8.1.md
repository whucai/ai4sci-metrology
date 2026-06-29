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
| D2 Observability | binary code-on/off + post-hoc ablation | 3-level input-sensitivity intervention (IO₁/IO₂/IO₃) |
| D3 Trust inflation | no concept | FRR(result) vs FRR(component) = primary DV |
| D4 Scientometric link | none | ECRF ↔ citations / CD-index / altmetrics / team size (exploratory) |

**The empirical wedge (revised after review):** all regimes R₁/R₂/R₂₊/R₃ score the **same agent reproduction trace**. R₂₊ (FactReview + provenance + hard-code checks) is the "trivially extended" baseline. The wedge is that R₂/R₂₊ answer "did the agent's output match the claim?" while R₃ answers "did the agent reconstruct each *component* validly?" — a substitute data path or hard-coded value can make R₂/R₂₊="Supported" while R₃ flags the process invalid. **If R₂₊ catches most M₁/M₂ (FRR(R₂₊)≈FRR(R₃)), D1 falls back to the continuous per-component score** that enables Study 2 + localization + Study 4 (R₂₊ gives binary flags, not continuous scores).

RPC-Bench (Chen et al. 2026) is motivation only: GPT-5 = 37.46% Informativeness on paper comprehension — the comprehension ceiling that motivates a reconstruction-level instrument.

> **External review (2026-06-29, Codex gpt-5.5 xhigh, 3 rounds):** original design 5/10 (baseline-alignment flaw: R₂ on released repo vs R₃ on agent trace); revised same-trace design = **7/10 path, no fatal structural flaw remains**. See `RESEARCH_REVIEW.md`.

## 4. The four studies

### Study 1 — Construct validation: ECRF is multi-dimensional (Block 1, M0/M1 re-analysis)
Show ECRF components vary semi-independently (disagreement rate, error-localization rate, component correlation). Re-analyze M0 (6 papers, 3 STRICT) + M1 (10-paper framework validation). *Status: largely done (R110).*

### Study 2 — Controlled input-sensitivity intervention (Block 2, C2)
**20 papers × 3 IO × 2 models = 120 runs.** Hypotheses: monotonic ECRF IO₁→IO₃ (H1); significant Component×IO interaction — some components (Data, Result) steep, others (Model) flat or dipping (H2). Isolated Docker `--network none` workspaces, randomized condition order, pre-registered seeds. **Causal language limited to the within-paper randomized artifact package** (not "observability determines reproducibility" in the wild) — IO levels are experimenter-built, papers stratified by predicted slope, some IO₂/IO₃ collapse. *Pilot (R100–R103) passed all 4 green-light gates; full pool R120 finalized (19/20 + 1 Mgmt slot pending). **Gate: do not launch full Study 2 until R121 gold chains frozen.***

### Study 3 — MAIN: trust inflation + audit correction (Block 3a + 3 + 4 + 6, C1)
The dominant contribution. **Four regimes on the same agent reproduction trace** (revised after external review — the original R₂-on-released-repo vs R₃-on-agent-trace was a baseline-alignment flaw):
- **R₁** result-level (did the agent's numbers match the paper's?)
- **R₂** FactReview-style claim-level audit applied to the **agent's trace** (claim extraction → S2 lit + RefCopilot → execute the agent's code K=3 wrapper-only → 4-status verdict; no component-provenance scoring)
- **R₂₊** R₂ + two trivial bolt-ons: data/sample provenance check + hard-coded-number scanner (the "FactReview extended" baseline reviewers demand)
- **R₃** ECRF component-level audit of the same trace (task-contingent)
- **Prior-art calibration cell (separate):** original FactReview on released repos of its 35-paper benchmark — must reproduce 4.86/5 + 17%-status-change within tolerance. NOT a head-to-head baseline.

**Headline result:** FRR(R₁) > FRR(R₂) > FRR(R₂₊) > FRR(R₃), each adjacent gap McNemar p<0.05.
**Killer evidence — "process-invalid supported" panel, split into two strata (not collapsed):**
- **S-exact**: numeric match + R₃ invalid (M₂ hard-code populates; M₁-exact rare ~1–5%)
- **S-directional**: directional/qualitative match + R₃ invalid (M₁ substitution ~10–25%)
- **Fair-baseline rule (pre-register before scoring):** R₂ may call "Supported" only at the extracted claim's evidence-target granularity; numeric claims matched only by sign → "Partially-supported." Report Supported-exact vs Supported-directional separately; no post-hoc downgrading. Metric: P(R₂/R₂₊=Supported | R₃=invalid) + bootstrap CI + full denominator + blinded two-adjudicator. Target 5–8 cases across ≥2 papers/modes.
**D1 fallback (pre-registered):** if FRR(R₂₊) ≈ FRR(R₃), reframe D1 as the **continuous per-component fidelity score** enabling Study 2's Component×IO + localization + Study 4's continuous-variable correlation (R₂₊ gives binary flags, not continuous scores). Carried by Study 2 + reliability + localization, NOT Study 4.
**Generalization asymmetry:** R₂/R₂₊ Inconclusive at IO₁/IO₂ (no executable agent code); R₃ still scores. Report the coverage fraction where R₂/R₂₊ can't run but R₃ can.

### Study 4 — Exploratory ecological validation (Block 7, C3, DEMOTED)
Regress agent-measured ECRF (and component-ECRF) on citations / CD-disruption / altmetrics / team size over the 20-paper deep set + the 115-paper SciSciBench substrate (join to OpenAlex/SciSciNet). Controls: field, year, team size. Pre-registered Hₛ₁–Hₛ₃. **Exploratory, demoted after review**: observational, confounded (selection/fame/data-availability/age/team/venue/openness). Licenses "ECRF associated with impact," NOT "reproducibility predicts impact." Appendix for NeurIPS/ICML; modest main study only for Scientometrics. **No GPU spent until C1/C2 land.**

## 5. Paper pool (R120, finalized 2026-06-25)

20 papers × 3 IO × 2 models = 120 runs. Domain: SoS 8 / IS 6 / Mgmt 6 (restoring once #20 Mgmt slot filled; 19 stable now). Strata by *predicted ECRF slope* IO₁→IO₃: Low 5 / Medium 8 / High 6. Task types: STRICT 6 / METHOD 8 / DATA-SUB 5. **7 clean-IO₃ anchors** (Petersen2024, Wu2019, Park2023, Bentley2023, Funk2017, Obadage2024, Liu2018-hotstreaks). **3 data-unavailable boundary cases** (Maddi2024, Schaper2025, Bikard2013) where IO₂/IO₃ collapse — kept deliberately (1 boundary rule). Known localized breaks: Arts2021 (Indicator, R003 lines 233–236), Wu2019 (Model/Claim direction).

Models (tiered): open-weight Qwen3-32B (local) / low-cost DeepSeek-V3/V4-Pro API / frontier GPT-4o + Claude Opus (robustness subset only, ~54 runs).

## 6. Run order

M1 mini-pilot (done, R100–R103, 4 gates pass) → **freeze R121 gold chains (20/20, 2 annotators, per-component α/ICC)** → M2 Study 2 full (120 runs) → M3 Study 3 (same-trace R₁/R₂/R₂₊/R₃ re-scoring + S-exact/S-directional adjudication + Layer-2 validity) → repeat-seed stability (36 runs) → M4 simplicity (R₃ vs overbuilt R₃′ vs threshold-lowered R₂₊) → M5 frontier robustness (36 runs) → M6 Study 4 exploratory (appendix). See `RESEARCH_REVIEW.md` for the 17-item TODO + stop-the-presses gates.

## 7. What success looks like (the paper's Figure 1 + Table 3)

- **Figure 1**: the IO→ECRF→RIB chain as a measurement model, with the **same-trace 4-regime ladder R₁→R₂→R₂₊→R₃** showing FRR falling at each step and the S-exact/S-directional killer-case panel.
- **Table 3**: FRR(R₁/R₂/R₂₊/R₃) + McNemar p + bootstrap CI; the killer-case list (S-exact + S-directional) with component localization; R₂₊ ablation.
- **Table 4 (Study 4, appendix for ML venues)**: ECRF ↔ impact β, exploratory.

## 8. What would falsify it

- **FRR(R₂₊) ≈ FRR(R₃)** (provenance + hard-code checks catch most M₁/M₂) → D1 *detection* advantage collapses; fall back to D1 = continuous per-component measurement (must then show reliability + Component×IO + localization + continuous-score-predicts-validity). If reliability also fails, paper reverts to negative pilot/method note.
- **No S-exact/S-directional killer case** in 120 runs → "invisible by construction" becomes theoretical only; weaken to "component audit localizes breaks (Block 4)" without the killer contrast. Mitigations: seed with Arts2021/Wu2019, oversample High stratum, lean on M₂ + S-directional, expand to 72 extra traces + backup papers.
- **IO gradient absent at frontier** (A3) → scope statement, not theory death.
- **Capability confound dominates** (most low-IO failures are agent-capability, not observability) → IO construct weakened to "agent capability bounds reproduction, modulated by observability"; scope restriction, not theory death (Block 5b control).
- **Study 4 null** → ECRF is still a valid instrument; "reproducibility not correlated with impact" is itself publishable.

## 9. Limitations (the three the author flags)

1. **Agent capability as error term.** At IO₁/IO₂, the agent may fail from reasoning/planning/coding limits rather than paper irreproducibility — blurring "agent can't" vs "paper not reproducible." Mitigation: Block 5b gold-spec ceiling condition + failure-type decomposition (info-missing / capability-fail / ambiguity); frontier subset (Block 5) for attenuation; a dedicated Limitations paragraph. The IO→ECRF slope is reported with and without capability-fail cases (sensitivity).
2. **Gold-chain annotation subjectivity.** Data/Sample/Indicator boundaries are subjective; R121 is the load-bearing anchor. Mitigation: Block 6 codebook with explicit per-component boundary rules + worked examples; **independent-then-adjudicate** (α on independent labels, not consensus-by-construction); inter-pair reliability on a shared subset; publish the codebook; per-component α gating (low-α components → qualitative only).
3. **Killer-case probability.** 120 runs may not yield 5–8 S-exact/S-directional cases if agent errors are mostly compile/hallucination (which yield Inconclusive, not "Supported"). Mitigation: the panel only needs Supported-but-invalid cases; seed with pre-confirmed breaks (Arts2021, Wu2019); oversample High stratum; lean on M₂ + S-directional; expand-trace fallback (72 extra + backup papers); pre-registered weakening to "localizes breaks" if still <5.

## 10. Venue (recommendation)

**Primary: NeurIPS Datasets & Benchmarks** (or ICML). The external reviewer wrote a NeurIPS D&B outline; ML audience values the FactReview contrast, the same-trace audit ladder, and measurement rigor. Study 4 demoted to appendix. The measurement-instrument framing is slightly unusual for D&B but D&B accepts metric/measurement contributions.
**Fallback: Scientometrics (Springer).** If the ML framing feels too benchmark-adjacent, or if Study 4 lands and the field-facing angle is the hook — FactReview isn't competition there and the "new scientometric variable" angle is clean.
**Long-shot: Nature Human Behaviour / Science Advances** — only if Study 4 produces a striking, defensible reproducibility↔impact finding (currently exploratory, so not the base case).
Core theory D1–D4 is venue-agnostic; the choice is a framing decision once C1/C2 land. Note: D&B deadline (~Sept) sets the timeline pressure — R121 freeze + 120 runs must finish with margin.

## 11. Why this lands as a paper

It turns the closest competitor (FactReview) into a fair same-trace baseline, makes a *structural* contribution (component unit + IO input-sensitivity + trust-inflation DV + exploratory scientometric link — moves FactReview cannot make), has a pre-registered killer experiment with cases that are invisible to the baseline by construction, hardens the anchor (R121 gold chains with independent-annotation α) and the capability confound (gold-spec ceiling), and the mini-pilot already passed all 4 green-light gates.

---

**Status**: theory locked (v7.2); v8.1 novelty re-run done (FactReview = closest, D1–D4); R100–R103 pilot green; R120 pool 19/20; R121 gold-chains in draft (19/20, not frozen). Next concrete step: **R121 Layer-1 gold chains frozen → M2 Study 2 full (120 runs) → M3 Study 3 with the faithful R₂ replication**.
