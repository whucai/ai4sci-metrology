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
| **C1 (primary)** The result-based reproducibility indicator carries systematic measurement bias (FRR > 0), and component-level audit corrects it (FRR(R₂) > FRR(R₃)) — **even when R₂ is a FactReview-style claim-level execution audit** | This is the paper's dominant contribution — a measurable measurement-validity failure + a correctable instrument that beats the closest prior-art baseline | FRR(R₁) > 0 (CI not overlapping 0); **FRR(R₂) > FRR(R₃), McNemar p<0.05** where R₂ = FactReview-style manuscript+lit+code-execution+4-status-claim-verdict; ≥5 human-confirmed failure-mode cases across ≥2 modes (M₁–M₄), **including ≥1 case R₂ labels "Supported" but R₃ reveals M₁/M₂** | B3, B5 |
| **C2 (supporting)** The IO gradient causally determines reconstruction fidelity, and the effect is asymmetric across evidence-chain components | Establishes the *mechanism* behind C1 — why bias arises and why component-level audit can localize it | Monotonic ECRF increase IO₁→IO₃; significant Component×IO interaction (mixed-effects); ≥2 components improve significantly | B2, B3 |
| **C3 (scientometric capstone)** Agent-measured ECRF is a scientometric variable correlated with established impact indicators | The field-facing payoff — a latent variable the field could not previously measure, linked to its existing constructs | ECRF (and component-ECRF) significantly associated with citations/CD-index/altmetrics/team size, controlling for field+year; effect direction consistent across deep-set + SciSciBench substrate | B7 |
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

### Block 2: Novelty Isolation — IO gradient drives ECRF (Study 2, P1/P2)
- **Claim tested**: C2 — IO causally determines ECRF, asymmetrically across components.
- **Why this block exists**: Isolates information observability as the causal variable, separating theory from generic "harder papers" explanations.
- **Dataset / split / task**: 20 papers × 3 IO levels (IO₁ narrative / IO₂ structured docs no code / IO₃ full executable) × 2 primary models = 120 runs. Pre-registered paper pool selected and pre-annotated before agent execution.
- **Compared systems**: Within-model IO₁ vs IO₂ vs IO₃ (the causal manipulation); 2 primary models (Qwen3-32B open-weight, DeepSeek-V4-Pro low-cost API).
- **Metrics**: Per-component ECRF (6 components × applicable dimensions); Component×IO interaction (mixed-effects, paper random intercepts); maturity distribution shift.
- **Setup details**: Fresh isolated workspace per run; randomized condition order (pre-registered seed); agent session terminated between runs; no cross-condition context leakage.
- **Success criterion**: (1) Monotonic ECRF increase IO₁→IO₃; (2) ≥2 components improve significantly; (3) Component×IO interaction significant → asymmetric reconstructability (H2).
- **Failure interpretation**: If ECRF is flat across IO levels, IO is not the bounding construct → theory must be reframed around a different bottleneck (e.g., task complexity).
- **Table / figure target**: Main-paper Table 2 (ECRF×IO×Component) + Figure (component-wise ECRF slope).
- **Priority**: MUST-RUN.

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

### Block 3a: Study 3 Main Result — FactReview-style R₂ baseline, faithfully implemented + trust-inflation contrast (C1, the dominant contribution)
- **Claim tested**: Trust inflation is not an artifact of a weak baseline. Even a faithful replication of the closest prior-art system (FactReview, Yue et al. 2026) — claim-level execution audit with bounded repair — produces FRR(R₂) > FRR(R₃); i.e., claim-level "Supported" verdicts systematically miss process-level invalidity that component-level audit catches.
- **Why this block exists**: Turns the closest competitor into the baseline. If R₂ is a strawman, C1 is reviewer-killed. So R₂ must be a *faithful, pre-registered* replication of FactReview on our paper pool, then shown to still underperform R₃. This is the single most important block for novelty defense.
- **Dataset / split / task**: The same Study-2/3 runs (20 deep papers × 3 IO × 2 models), re-scored under R₁ / R₂ / R₃ on identical runs. R₂ applies to the IO₃ subset (papers with released code); for IO₁/IO₂ papers R₂ is recorded as "Inconclusive — no executable artifact" (this asymmetry is itself a result: see *Generalization* below).
- **R₂ pipeline — faithful FactReview replication** (must match Yue et al. 2026 §3; deviations pre-registered + reported):
  1. **Manuscript parsing**: MinerU → section-aware text blocks, tables, equations, figure captions, citation anchors, page locations (same parser as FactReview; reuse our existing R098 MinerU setup).
  2. **Claim extraction**: schema-constrained LLM extractor → typed records {claim text, type ∈ {empirical, methodological, theoretical}, scope, source span, linked manuscript evidence, evidence targets}. Multi-scope claims decomposed into subclaims. Inclusion rule: claim affects novelty / validity / contribution / reproducibility / scope.
  3. **Literature evidence**: Semantic Scholar comparison set (cited methods, named baselines, semantically similar papers) → structured technical comparison table (NOT a generic novelty score). RefCopilot bibliography check against arXiv/S2/OpenReview/OpenAlex.
  4. **Execution evidence (Run-Review-Fix)**: Linux Docker, `--network none` (reuse our R097 isolated executor). Derive candidate tasks from README/configs/entry scripts. **K=3 repair rounds, wrapper-only** (fix categories: env | deps | path | encoding | data | runtime | other); explicitly forbid changes to model architecture, loss, datasets, evaluation logic, baselines. Judge compares observed outputs vs claimed/reported numbers → pass / fail / inconclusive (inconclusive if run succeeds but outputs can't be aligned to a claim — not forced).
  5. **Claim status**: 4 labels — Supported / Partially-supported / In-conflict / Inconclusive. Provenance (manuscript / lit / execution / combined) tracked separately.
  6. **Fidelity safeguards**: (a) reuse FactReview's public code (github.com/DEFENSE-SEU/FactReview) as the reference implementation where license permits; (b) pre-register any deviations (e.g., our non-ML paper pool may need claim-type extensions); (c) run R₂ on FactReview's own 35-paper benchmark as a calibration check — our R₂ must reproduce their 4.86/5 rubric and 17%-status-change ablation within tolerance before we trust R₂ on our pool.
- **Compared systems (the C1 ladder)**:
  - **R₁** = result-level only: did the agent's reproduced numbers match the paper's reported numbers (within tolerance)? Binary pass/fail.
  - **R₂** = FactReview-style claim-level execution audit (above).
  - **R₃** = ECRF component-level audit: each claim decomposed into Data→Sample→Indicator→Model→Result→Claim components, each scored for reconstruction fidelity; task-contingent pass (task-critical components must pass).
- **Metrics**: FRR(R₁), FRR(R₂), FRR(R₃) with bootstrap CI; **McNemar p<0.05 on FRR(R₂)>FRR(R₃)** (paired, same runs); trust-inflation gap Δ = FRR(R₂) − FRR(R₃); localization rate (% of confirmed breaks where R₃ names the broken component).
- **Killer result (the decisive evidence)**: ≥1 human-adjudicated case where **R₂ = "Supported"** (released-code output aligns with the claimed number) **but R₃ reveals M₁ (data/sample substitution: the agent reproduced the number via a different data path) or M₂ (paper values hard-coded as outputs)**. This case is **invisible to R₂ by construction** — R₂ executes the *released* repo, so its agent never chooses data/sample; it cannot see substitution. Target N=3–5 such cases across ≥2 break modes. Each case: automated rule → audit trace → two-reviewer human adjudication.
- **Generalization asymmetry (secondary finding)**: R₂ is undefined/Inconclusive at IO₁/IO₂ (no executable). ECRF produces component scores at all IO levels. Report the fraction of the pool where R₂ cannot run but R₃ can — this quantifies ECRF's coverage advantage over execution-only audit.
- **Success criterion**: FRR(R₁) > FRR(R₂) > FRR(R₃), each gap McNemar p<0.05; ≥3 human-confirmed R₂="Supported"/R₃=M₁-or-M₂ cases; R₂ calibration check passes (reproduces FactReview's 17% within tolerance on their 35-paper set).
- **Failure interpretation**: If FRR(R₂) ≈ FRR(R₃) (no trust-inflation gap), the component decomposition adds no measurement-validity value over claim-level execution audit → C1 collapses to "result-level is biased, FactReview already fixes it" → the paper's contribution shrinks to D2 (IO) + D4 (scientometric), and D1/D3 are empirically unsupported. Pre-register this fallback.
- **Table / figure target**: Main-paper Table 3 (FRR ladder R₁→R₂→R₃ + McNemar) + Figure (trust-inflation decomposition + the R₂="Supported"/R₃=M₁ killer-case panel).
- **Priority**: MUST-RUN (this IS the main contribution; gates C1).

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
- **Why this block exists**: Without human labels, FRR is an insider metric and the whole measurement-validity story is unfalsifiable (the project's documented fatal weakness).
- **Dataset / split / task**: Layer 1 — 2 annotators per paper on the 20-paper pool; Layer 2 — validity adjudication on all flagged + sample of unflagged.
- **Compared systems**: Component-stratified α targets: Data Source ≥0.75, Sample/Indicator/Model ≥0.67, Result ≥0.80, Claim ≥0.60.
- **Metrics**: Inter-annotator α per component; rule precision/recall; confirmed-break rate.
- **Setup details**: Pre-registered annotation protocol; adjudication by discussion; transparent reporting of below-target components.
- **Success criterion**: ≥80% of components at or above target α; components below target reported transparently with adjudication.
- **Failure interpretation**: If Claim α < 0.60 even after adjudication, restrict quantitative FRR claims to higher-α components and treat Claim qualitatively.
- **Table / figure target**: Methods section reliability table.
- **Priority**: MUST-RUN (unblocks Study 3).

### Block 7: Scientometric Linkage — ECRF as a new scientometric variable (Study 4, C3)
- **Claim tested**: C3 — agent-measured ECRF correlates with established impact indicators (the field-facing capstone).
- **Why this block exists**: This is the *scientometric* payoff that justifies the venue choice. No prior work could test "does execution-level reproducibility relate to impact?" because the IV did not exist. Without Block 7 the paper reads as a measurement-instrument paper; with it, ECRF enters the scientometric variable stack alongside citations/CD-index.
- **Dataset / split / task**: 30-paper deep-stratified set (component-ECRF already measured in Blocks 2–3) + 115-paper SciSciBench substrate (L2/ECRF already measured). Join to OpenAlex/SciSciNet for citations, CD-disruption index (Park et al. 2023), altmetric attention, team size (Wu, Wang & Evans 2019).
- **Compared systems**: OLS / mixed-effects regression of ECRF (and per-component ECRF) on impact indicators, controlling for field, year, team size.
- **Metrics**: standardized β for ECRF → citations; ECRF × CD-index interaction (Hₛ₂: disruption trades off against reproducibility); component-ECRF predictive gain over result-match (Hₛ₃, ΔR²).
- **Setup details**: impact data fetched post-reproduction (no leakage into agent); pre-registered Hₛ₁–Hₛ₃; exploratory + confirmatory split.
- **Success criterion**: ECRF significantly associated with ≥1 impact indicator (p<0.05) with consistent direction across deep-set and SciSciBench substrate; component-ECRF adds predictive power over aggregate result-match.
- **Failure interpretation**: If no association, ECRF is still a valid measurement instrument (Studies 1–3 stand) but lacks scientometric linkage — reframe Study 4 as a measurement-independence result and scope the scientometric claim. Not fatal to the paper.
- **Table / figure target**: Main-paper Table 4 (ECRF ↔ impact regression) + Figure (component-ECRF vs CD-index).
- **Priority**: HIGH (defines the venue fit; not blocking the core measurement-validity claim C1).

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
