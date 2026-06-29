# Experiment Plan: An AI-Agent Metrology of Computational Reproducibility (v8.1)

**Problem**: Scientometrics has no instrument measuring whether a published computational analysis re-executes and reproduces its claimed results. The accessible evaluator signal — result-level numerical agreement — is a systematically biased reproducibility indicator: an agent can reproduce a number through the wrong process.
**Method Thesis**: Reproduction fidelity is bounded by the **partial observability of the evidence chain** (IO → ECRF → RIB); the result-based indicator carries systematic measurement bias (False Reproduction Rate > 0), and component-level auditing corrects it. ECRF is a new scientometric variable linked to impact indicators.
**Date**: 2026-06-24 (v8); **revised 2026-06-25 (v8.1)** — novelty re-run after RPC-Bench + FactReview (`refine-logs/NOVELTY_ASSERTION_V8.md`). Key change: **R₂ re-specified as a FactReview-style claim-level execution audit** (closest-prior-art baseline), not a strawman aggregate composite.
**Proposal**: refine-logs/FINAL_PROPOSAL.md
**Target Venue (open)**: *Scientometrics* default; higher-tier candidates under external review.

---

## Claim Map

| Claim | Why It Matters | Minimum Convincing Evidence | Linked Blocks |
|-------|----------------|------------------------------|---------------|
| **C1 (primary)** On the **same agent trace**, the result-based indicator carries systematic measurement bias (FRR > 0), and component-level audit corrects it — **FRR(R₁) > FRR(R₂) > FRR(R₂₊) > FRR(R₃)**, where R₂ = FactReview-style claim-level audit and R₂₊ = R₂ + provenance/hard-code checks | Dominant contribution — a measurable measurement-validity failure + a correctable instrument that beats the closest prior-art baseline (and its trivial extension) on the *same object* | FRR(R₁) > 0 (CI not overlapping 0); each adjacent gap McNemar p<0.05; **P(R₂/R₂₊=Supported \| R₃=invalid) > 0** with bootstrap CI; ≥5 human-confirmed killer cases across ≥2 modes, S-exact + S-directional strata; **pre-registered D1 fallback** if FRR(R₂₊)≈FRR(R₃) | B3a, B4, B6 |
| **C2 (supporting)** A controlled IO input-sensitivity intervention changes agent reconstruction fidelity, asymmetrically across evidence-chain components | Establishes the *mechanism* behind C1 — why bias arises and why component-level audit can localize it. **Causal language limited to the within-paper randomized artifact package** (not "observability determines reproducibility" in the wild) | Monotonic ECRF increase IO₁→IO₃; significant Component×IO interaction (mixed-effects); ≥2 components improve significantly | B2, B3a |
| **C3 (exploratory ecological validation, demoted)** Agent-measured ECRF is *associated with* established impact indicators | Field-facing but **exploratory** — observational, confounded (selection/fame/data-availability/age/team/venue/openness). Licenses "ECRF associated with impact," NOT "reproducibility predicts impact." Appendix for NeurIPS/ICML; modest main study only for Scientometrics | ECRF (and component-ECRF) associated with citations/CD-index/altmetrics/team size, controlling for field+year; effect direction consistent across deep-set + SciSciBench substrate; **no GPU spent until C1/C2 land** | B7 |
| **Anti-claim to rule out (A1)**: "FRR is just noise / thresholding artifact" | If bias is within scoring noise, the measurement-validity story collapses | Bootstrap CI on FRR; pre-registered thresholds; sensitivity at 0.10/0.15/0.20 disagreement cutoffs | B3, B4 |
| **Anti-claim to rule out (A2)**: "Component audit only wins because it is a stricter gate, not because it localizes breaks" | If R₃ just lowers trust by being harsher, it adds no information beyond a stricter threshold on R₂ | R₃ localizes the break component in the majority of confirmed cases; R₃≠R₂-at-lower-threshold | B4, B5 |
| **Anti-claim to rule out (A3)**: "The IO bound dissolves with frontier models" | If GPT-4o/Claude reproduce everything regardless of IO, the theory is model-specific | Frontier robustness subset shows the same IO pattern (attenuated but not eliminated) | B6 |
| **Anti-claim to rule out (A4)**: "The whole effect is a prompt-engineering artifact of our agent harness" | Reviewers will attribute the IO gradient to implementation details, not theory | Fresh isolated workspace, randomized condition order, pre-registered seed, cross-harness robustness (ARIS vs. raw SciSciGPT graph) | B2 |

---

## Paper Storyline

- **Main paper must prove**:
  - ECRF is multi-dimensional and varies systematically (Study 1 — establishes the construct)
  - IO causally drives ECRF, asymmetrically across components (Study 2 — establishes the mechanism)
  - Result-indicator bias is real, measurable, mechanistically decomposable (M₁–M₄), and correctable by component audit (Study 3 — the main contribution)
- **Appendix can support**:
  - Frontier-model robustness subset (attenuation pattern)
  - Full per-paper evidence-chain heatmaps and failure-mode adjudication traces
  - Inter-annotator α tables and adjudication protocols
- **Experiments intentionally cut**:
  - SciSciBench full benchmark (→ one motivation paragraph: L3 true capability ~0.3–0.5 establishes the *need* for audit; not a benchmark paper)
  - retracted-paper-detection / paper-mill work (different project)
  - ARIS/Codex/Claude engineering narrative (irrelevant to scientometrics readers)
  - Multi-model radar charts as a *headline* (kept only as robustness, not as model comparison contribution)

---

## Experiment Blocks

### Block 1: Main Anchor Result — STRICT reproduction pathway is achievable and measurable
- **Claim tested**: The framework can measure faithful reproduction where it should exist (calibrates the "valid" end of the validity scale).
- **Why this block exists**: Before claiming result-indicator bias, we must show the measurement instrument correctly recognizes genuine reproductions.
- **Dataset / split / task**: 3 STRICT papers (Petersen2024, Park2023, Bentley2023) — already DONE (R002/R004/R007).
- **Compared systems**: DeepSeek-V4-Pro agent vs. gold numerical targets.
- **Metrics**: D3 numerical accuracy (8/8, 6/6, 9/9 = 100%), sample-N exact, R² exact, significance match.
- **Setup details**: C1 condition (paper only), single seed per paper, DeepSeek-V4-Pro via Anthropic-compatible path.
- **Success criterion**: ≥3 STRICT papers at D3≥0.95 — **MET (3/3 at 1.00)**.
- **Failure interpretation**: If STRICT failed, the framework could not anchor the "valid" pole, undermining the FRR metric.
- **Table / figure target**: Motivation paragraph + appendix calibration table.
- **Priority**: DONE — evidence already in hand.

### Block 2: Controlled Input-Sensitivity Intervention — IO package changes ECRF, asymmetrically across components (Study 2, C2)
- **Claim tested**: C2 — a controlled IO input-sensitivity intervention changes agent reconstruction fidelity, asymmetrically across components. **Causal language limited to "the within-paper randomized artifact package changes agent behavior under this harness"** (not a population claim that observability determines reproducibility).
- **Why this block exists**: Isolates information observability as the manipulated variable, separating theory from generic "harder papers" explanations. Caveat: IO levels are experimenter-built per paper, paper selection is stratified by predicted slope, several papers have IO₂/IO₃ collapse — so this is a controlled intervention, not a population causal effect.
- **Dataset / split / task**: 20 papers × 3 IO levels (IO₁ narrative / IO₂ structured docs no code / IO₃ full executable) × 2 primary models = 120 runs. Pre-registered paper pool selected and pre-annotated before agent execution.
- **Compared systems**: Within-model IO₁ vs IO₂ vs IO₃ (the input-sensitivity manipulation); 2 primary models (Qwen3-32B open-weight, DeepSeek-V4-Pro low-cost API).
- **Metrics**: Per-component ECRF (6 components × applicable dimensions); Component×IO interaction (mixed-effects, paper random intercepts); maturity distribution shift.
- **Setup details**: Fresh isolated workspace per run; randomized condition order (pre-registered seed); agent session terminated between runs; no cross-condition context leakage.
- **Success criterion**: (1) Monotonic ECRF increase IO₁→IO₃; (2) ≥2 components improve significantly; (3) Component×IO interaction significant → asymmetric reconstructability (H2).
- **Failure interpretation**: If ECRF is flat across IO levels, IO is not the bounding construct → theory must be reframed around a different bottleneck (e.g., task complexity).
- **Table / figure target**: Main-paper Table 2 (ECRF×IO×Component) + Figure (component-wise ECRF slope).
- **Priority**: MUST-RUN. **Gate:** do NOT launch full Study 2 until R121 Layer-1 gold chains frozen (20/20, 2 annotators, per-component α/ICC).

### Block 3: Simplicity / Elegance Check — task-contingent audit vs. overbuilt variants
- **Claim tested**: The chosen R₃ design (task-contingent component audit) is not overbuilt; simpler variants are weaker, stricter variants add no information.
- **Why this block exists**: Defends against "you over-engineered the audit to win" and A2 (stricter-gate confound).
- **Dataset / split / task**: Same Study 2/3 runs, re-scored under four regimes (R₁ result-level / **R₂ FactReview-style claim-level execution audit** = manuscript+lit+code-execution+4-status verdicts (Supported/Partial/In-conflict/Inconclusive), K=3 wrapper-only repair, implemented to match Yue et al. 2026 / R₃ task-contingent component audit / **R₃′ overbuilt** = all-6-components-must-pass regardless of task type).
- **Compared systems**: R₃ vs R₃′(overbuilt) vs R₂(FactReview-style)-lowered-threshold.
- **Metrics**: FRR under each regime; failure-localization rate; over-rejection rate.
- **Setup details**: Re-scoring only — no new agent runs.
- **Success criterion**: R₃ (task-contingent) achieves lower FRR than R₁ *without* the excess over-rejection of R₃′; R₃ ≠ R₂-at-lower-threshold on localization (defends A2).
- **Failure interpretation**: If R₃′ beats R₃ meaningfully, task-contingency is unnecessary complexity → simplify. If R₂-at-lower-threshold matches R₃, the component structure adds nothing → theory weakened.
- **Table / figure target**: Appendix ablation table.
- **Priority**: MUST-RUN (defends simplicity + A2).

### Block 3a: Study 3 Main Result — same-trace audit ladder R₁/R₂/R₂₊/R₃ + trust-inflation contrast (C1, the dominant contribution)
> **Revised 2026-06-29 after external review** (`RESEARCH_REVIEW.md`, threadId `019f1188-…`). The original design had R₂ audit the *released repo* while R₃ audited the *agent's reconstruction* — two different objects, which made "R₂=Supported, R₃=M₁" uninterpretable. Fix: **all regimes score the same agent reproduction trace.** Original FactReview-on-released-repo moves to a separate prior-art calibration cell.

- **Claim tested**: Trust inflation is not an artifact of a weak or mis-aligned baseline. On the **same agent reproduction trace**, FRR(R₁) > FRR(R₂) > FRR(R₂₊) > FRR(R₃): even a provenance-augmented FactReview (R₂₊) systematically misses process-level invalidity that component-level audit catches — OR, if R₂₊ ties R₃ on FRR, R₃'s value is the **continuous per-component measurement** that R₂₊'s binary flags cannot provide (pre-registered fallback).
- **Why this block exists**: Turns the closest competitor into a *fair, same-object* baseline. If R₂/R₂₊ are strawmen or mis-aligned, C1 is reviewer-killed. The same-trace ladder + R₂₊ + pre-registered granularity rules are the novelty defense.
- **Dataset / split / task**: The same Study-2/3 runs (20 deep papers × 3 IO × 2 models = 120 traces), re-scored under R₁/R₂/R₂₊/R₃ on **identical agent traces** (the agent's own code, the data it chose, the outputs it produced) at each IO level. All four scorers consume the same trace log.
- **Same-trace regimes**:
  - **R₁** = result-level: do the agent's reproduced numbers match the paper's reported numbers (within tolerance)? Binary pass/fail.
  - **R₂** = FactReview-style claim-level audit applied to the **agent's trace**: claim extraction (schema-constrained, typed {empirical/methodological/theoretical}, scope, source span, evidence targets) → literature grounding (Semantic Scholar comparison set + RefCopilot) → execute the **agent's** code under K=3 wrapper-only repair (env|deps|path|encoding|data|runtime|other; forbid changes to model/loss/datasets/eval-logic/baselines) → 4-status verdict (Supported / Partially-supported / In-conflict / Inconclusive). **No component-provenance scoring.**
  - **R₂₊** = R₂ + two trivial bolt-ons reviewers will demand: (i) **data/sample provenance check** (did the agent use the paper's data file / sample spec?), (ii) **hard-coded-paper-number scanner** (M₂). This is "FactReview extended by 2 checks" — the baseline that tests whether D1 (component unit) adds anything beyond obvious patches.
  - **R₃** = ECRF component-level audit of the **same trace**: decompose each claim into Data→Sample→Indicator→Model→Result→Claim, score each component's reconstruction fidelity, task-contingent pass (task-critical components must pass).
- **Prior-art calibration cell (SEPARATE, not head-to-head)**: original FactReview run on the *released repos* of FactReview's own 35-paper benchmark. Purpose: show our R₂ implementation is faithful (reproduces their 4.86/5 rubric + 17%-status-change ablation within tolerance) before we trust R₂ on our pool. Reported as "how the published system behaves," NOT as a baseline R₃ must beat.
- **Fidelity safeguards**: (a) reuse FactReview's public code (github.com/DEFENSE-SEU/FactReview) where license permits; (b) pre-register any deviations (our non-ML pool may need claim-type extensions); (c) calibration cell must pass before main claims.
- **Metrics**: FRR(R₁), FRR(R₂), FRR(R₂₊), FRR(R₃) with bootstrap CI; **McNemar p<0.05 on each adjacent gap** (paired, same traces); trust-inflation gaps Δ₂=FRR(R₂)−FRR(R₂₊), Δ₃=FRR(R₂₊)−FRR(R₃); localization rate (% of confirmed breaks where R₃ names the broken component); **P(R₂/R₂₊=Supported | R₃=process-invalid)** overall + by stratum.
- **Killer result (the decisive evidence) — "process-invalid supported" panel, split into two strata (NOT collapsed)**:
  - **S-exact**: agent's reproduced number matches the paper's reported value within tolerance AND R₃ flags a component invalid (M₂ hard-code expected to populate; M₁-exact rare, ~1–5% of M₁).
  - **S-directional**: agent's reproduced *direction / sign / qualitative claim* matches the paper AND R₃ flags a component invalid (M₁ substitution expected here, ~10–25% of M₁).
  - **Fair-baseline granularity rule (PRE-REGISTER before scoring):** R₂ may call "Supported" only at the granularity of the extracted claim's evidence target. Numeric / table-cell / effect-size claims matched only by sign → "Partially-supported," NOT "Supported." Report **Supported-exact** and **Supported-directional** as separate support types; no post-hoc downgrading of numeric claims.
  - **Case selection**: from all 120 traces take ALL R₂/R₂₊-Supported-and-R₃-invalid candidates + ALL M₁/M₂ automated-flagged cases + a random sample of R₃-valid cases (recall anchor). Two adjudicators **blinded to hypothesis and to R₂/R₃ labels**, resolve by discussion, record agreement. Target 5–8 confirmed cases across ≥2 papers and ≥2 modes. Report **rate + bootstrap CI**, not just "≥N examples."
  - **Panel-population risk mitigation (added 2026-06-29):** the killer specifically needs R₂/R₂₊="Supported" (agent matched the claim) AND R₃=process-invalid — compile errors / hallucinations produce Inconclusive/In-conflict, not "Supported," so they don't enter the panel. To ensure the panel populates: (i) **seed with pre-confirmed break papers** — Arts2021 (R003 localized Indicator bug) and Wu2019 (Model/Claim direction) are guaranteed process-invalid cases; run them first. (ii) **Oversample the High-observable-slope stratum** where M₁/M₂ are likelier. (iii) **Lean on M₂ (hard-code) and S-directional (coarse/directional match)** — both more populous than M₁-exact (reviewer prior: M₁-exact ~1–5%, M₁-directional ~10–25%, M₂ easier). (iv) **Expand-trace fallback**: if 120 runs yield <5 cases, draw on the repeat-seed 36 + frontier 36 = 72 additional traces, then R120 backup papers (schaper2025, w23913, deng2023, zheng2025, ke2018, park2023). (v) If still <5, weaken the killer to "component audit localizes breaks" (Block 4) without the Supported-but-invalid contrast — pre-registered.
- **Generalization asymmetry (secondary finding)**: R₂/R₂₊ require the agent to have produced executable code (IO₃ subset; at IO₁/IO₂ the agent's trace may have no runnable code → R₂/R₂₊ = Inconclusive). R₃ produces component scores at all IO levels. Report the fraction of the pool where R₂/R₂₊ cannot run but R₃ can — ECRF's coverage advantage over execution-only audit.
- **Success criterion**: FRR(R₁) > FRR(R₂) > FRR(R₂₊) > FRR(R₃), each adjacent gap McNemar p<0.05; calibration cell passes (reproduces FactReview's 17% within tolerance); killer panel ≥5 confirmed cases with rate+CI across ≥2 modes; localization rate > R₂₊ flag-only.
- **Failure interpretation / D1 fallback (PRE-REGISTERED)**: If FRR(R₂₊) ≈ FRR(R₃) (the two bolt-on checks catch most M₁/M₂), D1's *detection* advantage collapses. Reframe D1 as: R₃ provides a **reliable continuous, component-resolved measurement instrument** supporting (a) Study 2's Component×IO sensitivity, (b) failure localization beyond binary flags, (c) Study 4's continuous-variable correlation — none of which R₂₊'s binary flags enable. NOT defensible to claim "R₃ beats extended FactReview" if FRR equal. D1 carried by Study 2 + reliability + localization, NOT Study 4. If even reliability/ICC fails, the continuous-measurement fallback also collapses → paper reverts to negative pilot/method note.
- **Table / figure target**: Main-paper Table 3 (FRR ladder R₁→R₂→R₂₊→R₃ + McNemar + bootstrap CI) + Figure (same-trace ladder schematic + trust-inflation decomposition + S-exact/S-directional killer-case panel with trace excerpts).
- **Priority**: MUST-RUN (this IS the main contribution; gates C1). **Stop-the-presses:** do NOT run full Study 2 before R121 gold chains frozen; do NOT claim R₃ beats FactReview unless R₂/R₂₊ are same-trace; do NOT count directional support unless claim granularity pre-registered.

### Block 4: Failure Analysis / Measurement Failure Modes (M₁–M₄) — the mechanism of result-indicator bias
- **Claim tested**: Result-indicator bias is mechanistically decomposable into M₁–M₄, each with an automated detection rule that survives human adjudication.
- **Why this block exists**: Makes "result-indicator bias" concrete and falsifiable rather than a residual statistic.
- **Dataset / split / task**: All flagged cases from Study 2/3 runs + random sample of unflagged cases (recall estimation).
- **Compared systems**: Automated screening rule → audit trace → human adjudication (two reviewers, resolve by discussion).
- **Metrics**: Rule precision, rule recall, confirmed-break rate per B-type; ≥5 human-confirmed failure-mode cases across ≥2 types.
- **Setup details**:
  - **M₁ Substitution**: DSF or VMF low, RRF moderate.
  - **M₂ Circularity**: regex scan for paper numerics in code **+ semantic code review** to exclude legitimate constants (years, sample sizes, thresholds).
  - **M₃ Shopping**: ≥3 model variants with paper-proximity selection *without* theoretical/methodological justification.
  - **M₄ Assertion**: claim-evidence traceability check, PRF low + CRS high.
- **Success criterion**: ≥5 human-confirmed failure-mode cases; ≥2 modes confirmed; M₂/M₃ false-positive rate controlled by semantic review.
- **Failure interpretation**: If <5 breaks confirm or false positives dominate, the B-typology is not empirically grounded → collapse to a single "process invalid" category.
- **Table / figure target**: Main-paper Table 3 (failure-mode matrix with examples) + Figure (result-indicator bias decomposition).
- **Priority**: MUST-RUN.

### Block 5: Frontier Necessity Check — does the IO bound survive frontier models?
- **Claim tested**: The IO→ECRF mechanism is not an artifact of weak models; it persists (attenuated) with frontier agents.
- **Why this block exists**: The paper's central construct is the *agent* in "generative agent auditing"; reviewers will demand evidence that stronger models do not trivially dissolve the bound (A3).
- **Dataset / split / task**: 8–10 papers × 3 IO levels × 2 frontier models (GPT-4o, Claude Sonnet/Opus) = ~54 runs.
- **Compared systems**: Frontier models vs. primary open-weight/low-cost models on the same IO gradient.
- **Metrics**: ECRF slope across IO per model tier; FRR(R₁) per tier; failure-localization consistency.
- **Setup details**: API access; same isolation protocol; pre-registered subset.
- **Success criterion**: IO gradient direction consistent with primary pattern (attenuation allowed); FRR(R₁) > 0 for frontier tier.
- **Failure interpretation**: If frontier models reproduce at ceiling regardless of IO, scope the theory's claim explicitly to open-weight/mid-tier agents and reframe frontier as boundary condition (not failure — a clean scope statement).
- **Table / figure target**: Appendix robustness table; one main-panel sentence.
- **Priority**: HIGH (robustness, not blocking the core claim).

### Block 6: Two-Layer Human Validation — gold evidence chain + validity adjudication
- **Claim tested**: The ECRF and FRR measurements are reliable against human ground truth.
- **Why this block exists**: Without human labels, FRR is an insider metric and the whole measurement-validity story is unfalsifiable (the project's documented fatal weakness). R121 gold chains are the **load-bearing anchor** — if the Data/Sample/Indicator boundaries are subjective or unreliable, C1/C2 both fall.
- **Dataset / split / task**: Layer 1 — 2 annotators per paper on the 20-paper pool; Layer 2 — validity adjudication on all flagged + sample of unflagged.
- **Compared systems**: Component-stratified α targets: Data Source ≥0.75, Sample/Indicator/Model ≥0.67, Result ≥0.80, Claim ≥0.60.
- **Metrics**: Inter-annotator α per component; rule precision/recall; confirmed-break rate; **inter-pair reliability** (different annotator pairs on a shared 4-paper subset).
- **Setup details**: Pre-registered annotation protocol; adjudication by discussion; transparent reporting of below-target components. **Boundary subjectivity controls (added 2026-06-29):**
  - **Codebook with explicit per-component boundary rules** (build on R095 DSF/SMF/INF/MDF/RRF/CRS/PRF): Data = raw dataset + access path; Sample = inclusion/exclusion criteria + N + unit-of-analysis; Indicator = operationalized variable/metric **formula**; Model = estimator/architecture/spec; Result = reported numeric/figure; Claim = inference sentence. Each with 2+ worked examples.
  - **Independent-then-adjudicate protocol**: annotators label independently first (α computed on independent labels), THEN adjudicate by discussion — so α reflects genuine disagreement, not consensus-by-construction.
  - **Publish the codebook + example annotations** so reviewers can audit boundary calls.
  - **Per-component α gating**: if a component's α is below target after independent annotation, restrict quantitative FRR for that component to the adjudicated subset and report it qualitatively.
- **Success criterion**: ≥80% of components at or above target α (on independent labels, not post-adjudication); components below target reported transparently with adjudication.
- **Failure interpretation**: If Claim α < 0.60 even after adjudication, restrict quantitative FRR claims to higher-α components and treat Claim qualitatively.
- **Table / figure target**: Methods section reliability table (α by component, independent vs adjudicated, inter-pair).
- **Priority**: MUST-RUN (unblocks Study 3). **Stop-the-presses:** do NOT launch full Study 2 until R121 frozen with independent-annotation α.

### Block 5b: Capability-baseline control — separating "agent can't" from "paper not reproducible"
- **Claim tested / confound addressed**: At IO₁/IO₂, low ECRF may reflect **agent capability limits** (reasoning/planning/coding failure), not low observability — blurring the IO→ECRF slope and inflating FRR at low IO. This is the "agent capability as error term" threat to construct validity.
- **Why this block exists**: The frontier subset (Block 5) shows attenuation but not separation. A stronger control is needed: if the agent fails even when handed the gold component spec, that's capability failure, not observability failure.
- **Dataset / split / task**: On the 20-paper pool, at each IO level, run a **gold-spec ceiling condition**: give the agent the R121 gold-chain component spec for one held-out component (Data/Sample/Indicator formula/Model spec) and ask it to execute/reconstruct. Compare to the standard (no-gold-spec) condition.
- **Compared systems**: standard IO₁/IO₂/IO₃ vs gold-spec-ceiling at each IO level.
- **Metrics**: **Failure-type decomposition** per failed reconstruction: (a) *info-missing* (component not specified in paper → genuine IO effect), (b) *capability-fail* (component specified / gold-spec given but agent couldn't execute → capability confound), (c) *ambiguity* (component ambiguous). Report the capability-fail fraction by IO level and model tier.
- **Setup details**: Gold-spec condition uses the R121 frozen spec (so this block is gated on R121). Reuse the isolated executor.
- **Success criterion**: capability-fail fraction is bounded and reported; the IO→ECRF slope survives after subtracting capability-fail cases (sensitivity analysis). If the slope vanishes after removing capability-fails, the IO construct is confounded → reframe.
- **Failure interpretation**: If most low-IO failures are capability-fail, the IO→ECRF claim weakens to "agent capability bounds reproduction, modulated by observability" — a scope restriction, not theory death.
- **Table / figure target**: Appendix capability-decomposition table + a Methods limitation paragraph ("Agent capability as error term").
- **Priority**: SHOULD (strong construct-validity control; MUST if reviewers raise capability confound).

### Block 7: Exploratory Ecological Validation — ECRF association with impact indicators (Study 4, C3, DEMOTED)
- **Claim tested**: C3 — agent-measured ECRF is *associated with* (NOT "predicts") established impact indicators. **Exploratory, demoted after external review.**
- **Why this block exists**: Field-facing payoff, but observational and confounded (selection, fame, data-availability, age, team resources, venue, openness). Field/year/team controls do NOT remove these. Licenses "ECRF is associated with impact indicators," NOT "reproducibility predicts impact." Appendix for NeurIPS/ICML; a modest main exploratory study only for Scientometrics. **Do NOT spend GPU on Study 4 until C1/C2 land** — it cannot rescue a failed C1.
- **Dataset / split / task**: 20-paper deep-stratified set (component-ECRF already measured in Blocks 2–3) + 115-paper SciSciBench substrate (L2/ECRF already measured). Join to OpenAlex/SciSciNet for citations, CD-disruption index (Park et al. 2023), altmetric attention, team size (Wu, Wang & Evans 2019).
- **Compared systems**: OLS / mixed-effects regression of ECRF (and per-component ECRF) on impact indicators, controlling for field, year, team size.
- **Metrics**: standardized β for ECRF → citations; ECRF × CD-index interaction (Hₛ₂: disruption trades off against reproducibility); component-ECRF predictive gain over result-match (Hₛ₃, ΔR²).
- **Setup details**: impact data fetched post-reproduction (no leakage into agent); pre-registered Hₛ₁–Hₛ₃; exploratory + confirmatory split.
- **Success criterion**: ECRF associated with ≥1 impact indicator (p<0.05) with consistent direction across deep-set and SciSciBench substrate; component-ECRF adds predictive power over aggregate result-match. **Reported as exploratory ecological validation, not a causal/main claim.**
- **Failure interpretation**: If no association, ECRF is still a valid measurement instrument (Studies 1–3 stand) — "reproducibility is not correlated with impact" is itself a publishable finding. Not fatal.
- **Table / figure target**: Appendix Figure (ECRF ↔ impact) for NeurIPS/ICML; main Table 4 only for Scientometrics.
- **Priority**: SHOULD (NICE for ML venues; SHOULD for Scientometrics). **Does not carry D1** — D1 is carried by Study 2 + reliability + localization.

---

## Run Order and Milestones

| Milestone | Goal | Runs | Decision Gate | Cost | Risk |
|-----------|------|------|---------------|------|------|
| **M0 — Calibration** | Re-analyze M0/M1 (16 papers) under theory framing; confirm ECRF dimensionality | Study 1 analyses (no new runs) | Disagreement >0.15; localization >0.60 | ~0 GPU (re-analysis) | Low — most evidence exists |
| **M1 — Mini Study 2 Pilot** | De-risk IO gradient + break detection before scaling | 5 papers × 3 IO × 2 models = 30 runs | (1) IO₁<IO₂<IO₃ monotonic; (2) Component×IO visible; (3) ≥1 break detected; (4) result≠component on ≥1 case | ~15 GPU-h + API | **Highest-risk assumption**: IO₂ manipulation cleanly isolates documentation from code |
| **M2 — Study 2 Full** | Causal test of IO→ECRF (C2) | 120 primary runs + paper-pool finalization + Layer 1 annotation | Monotonic ECRF; significant Component×IO interaction | ~80 GPU-h + API | Paper-pool selection bias; mitigation = pre-agent annotation |
| **M3 — Study 3** | Result-indicator bias + audit correction (C1, main contribution; Block 3a) | 3-regime re-scoring (R₁ / **R₂ FactReview-style claim-level execution audit, faithfully replicated + calibrated on FactReview's 35-paper set** / R₃ component) + M₁–M₄ adjudication + Layer 2 validity | FRR(R₁)>0; **FRR(R₁)>FRR(R₂)>FRR(R₃), McNemar p<0.05**; R₂ calibration reproduces 17%-status-change within tolerance; ≥3 confirmed R₂="Supported"/R₃=M₁-or-M₂ killer cases | ~$200 API + human adjudication | False positives in M₂/M₃; mitigation = semantic review + justification requirement; R₂ strawman risk → pre-register faithful config |
| **M4 — Simplicity** | R₃ vs overbuilt R₃′ vs threshold-lowered R₂ | Re-scoring only | R₃ not dominated by simpler/stricter variants | ~0 compute | Low |
| **M5 — Frontier Robustness** | A3 boundary check | 8–10 papers × 3 IO × 2 frontier models ≈54 runs | IO direction consistent; FRR(R₁)>0 for frontier | API | Frontier at ceiling → scope statement, not failure |
| **M6 — Scientometric Linkage** | C3 — ECRF ↔ impact indicators | Join 30-paper deep set + 115-paper SciSciBench to OpenAlex/SciSciNet; regress ECRF on citations/CD-index/altmetrics/team size | ECRF significantly associated with ≥1 impact indicator, consistent direction across both sets | ~0 compute (OpenAlex/SciSciNet queries) | Confounded correlations; mitigation = field/year/team-size controls, pre-registered Hₛ₁–Hₛ₃ |

---

## Paper Pool: Stratified by Observability Variation

Selection finalized **before** agent execution (pre-registered). Each paper pre-annotated on: data availability, code availability, indicator complexity, sample ambiguity, model multiplicity, claim-result distance.

| Stratum | Observability Profile | Target N | Anchor Example |
|---------|----------------------|----------|----------------|
| Low variation | Data/formulas/models clearly specified; code available | 8 | Petersen2024 |
| Medium variation | Multi-step indicators or complex samples; some components under-specified | 12 | Arts2021 |
| High variation | Key components ambiguous; data unavailable or claims exceed results | 10 | TBD |

**Domains**: Science of Science (10), IS/Innovation (10), Management/Strategy (10).

---

## Model Configuration

Models identified by capability tier; specific versions and access dates reported in the setup table.

| Tier | Representative Model | Deployment | Scope |
|------|---------------------|-----------|-------|
| Open-weight reasoning | Qwen3-32B | Local GPU (1×4090) | Study 2: 120 runs |
| Low-cost API | DeepSeek-V3/V4-Pro | API (Anthropic-compatible path) | Study 2: 120 runs |
| Commercial frontier A | GPT-4o | API | Study 2/3 robustness |
| Commercial frontier B | Claude Sonnet 4 / Opus 4 | API | Study 2/3 robustness |

**Rationale**: The primary analysis estimates within-model effects of information observability (IO₁→IO₃); the frontier subset tests whether the observed pattern generalizes to stronger commercial agents.

---

## Immediate Next Step: Mini Study 2 (5-Paper Pilot, M1)

**Purpose**: Validate IO gradient and failure-mode detection before committing to full 120-run experiment.

**Design**: 5 papers × 3 IO levels × 2 models = 30 runs.

**Papers**: One from each observability stratum (Low/Medium/High), spanning ≥2 domains. Include ≥2 papers with complex indicators or ambiguous samples. Candidate anchors: Petersen2024 (Low), Arts2021 (Medium), + 3 TBD from the 20-paper pool.

**Pass criteria (green-light for full Study 2)**:
1. IO₁ < IO₂ < IO₃ monotonic ECRF increase observed
2. Component × IO interaction visible (not flat across components)
3. ≥1 failure-mode case detected (M₁–M₄)
4. Result-level success ≠ component-level validity on ≥1 case

**If mini Study 2 fails any criterion**: Re-examine IO level definitions, paper-pool composition, or model prompt design before scaling. Do not scale a broken manipulation.

---

## Compute and Data Budget

| Resource | Estimate |
|----------|----------|
| GPU-hours (local 4090) | ~80 (Qwen3-32B primary + pilot) |
| API costs | ~$300–500 (DeepSeek + GPT-4o + Claude) |
| Human annotation | ~3–5 weeks (Layer 1 gold chain + Layer 2 adjudication) |
| Total wall time | ~8–10 weeks |
| Biggest bottleneck | Human annotation (Layer 1/2) — not compute |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Theory read as "just a framework" | Explicit constructs (IO, ECRF, TCE) with causal propositions P1–P4 → falsifiable hypotheses |
| Evidence-break cases too few (<5) | Stratified sampling by observability variation; mini Study 2 de-risks before scaling |
| M₂/M₃ false positives | Semantic code review + theoretical-justification requirement for shopping |
| Single-model-family concern (A3) | Frontier robustness subset (M5) |
| Low α on Claim component | Pre-registered component-stratified α targets; transparent reporting; quantitative FRR restricted to high-α components |
| IO₂ manipulation not clean | Mini Study 2 explicitly tests IO₂ isolation before scaling |
| Prompt-engineering artifact (A4) | Fresh workspace, randomized order, pre-registered seed; cross-harness check if time permits |

---

## Final Checklist

- [x] Main paper tables are covered (Study 2 Table 2, Study 3 Table 3)
- [x] Novelty is isolated (Block 2 — IO as causal variable)
- [x] Simplicity is defended (Block 3 — R₃ vs overbuilt R₃′ vs threshold R₂)
- [x] Frontier contribution is justified (Block 5 — IO bound survives frontier, or scope statement)
- [x] Nice-to-have runs separated from must-run (frontier robustness = HIGH, not blocking)
- [ ] Mini Study 2 pilot executed and passed (gate to full Study 2)
