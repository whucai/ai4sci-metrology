# Experiment Plan: Evidence-Chain Theory of AI Reproduction Auditing (v7.2)

**Problem**: AI-generated scientific reproductions produce a misleading trust signal at the result level — agents can produce the right number through the wrong process. Organizations need to know which reproductions can be trusted.
**Method Thesis**: AI reproduction fidelity is bounded by the **partial observability of the evidence chain** (IO → ECRF → TCE); result-level evaluation systematically inflates trust, and component-level auditing corrects it.
**Date**: 2026-06-24
**Proposal**: refine-logs/FINAL_PROPOSAL.md
**Target Venue**: ISR / MISQ / Management Science

---

## Claim Map

| Claim | Why It Matters | Minimum Convincing Evidence | Linked Blocks |
|-------|----------------|------------------------------|---------------|
| **C1 (primary)** Result-level evaluation produces systematic trust inflation (TIR > 0), and component-level audit corrects it (TIR(R₁) > TIR(R₃)) | This is the paper's dominant contribution — a measurable governance failure + a correctable mechanism | TIR(R₁) > 0 with confidence interval not overlapping 0; TIR(R₁) > TIR(R₃), McNemar p<0.05; ≥5 human-confirmed evidence-break cases across ≥2 break types | B3, B5 |
| **C2 (supporting)** The IO gradient causally determines reconstruction fidelity, and the effect is asymmetric across evidence-chain components | Establishes the *mechanism* behind C1 — why inflation arises and why component-level audit can localize it | Monotonic ECRF increase IO₁→IO₃; significant Component×IO interaction (mixed-effects); ≥2 components improve significantly | B2, B3 |
| **Anti-claim to rule out (A1)**: "TIR is just noise / thresholding artifact" | If inflation is within scoring noise, the governance story collapses | Bootstrap CI on TIR; pre-registered thresholds; sensitivity at 0.10/0.15/0.20 disagreement cutoffs | B3, B4 |
| **Anti-claim to rule out (A2)**: "Component audit only wins because it is a stricter gate, not because it localizes breaks" | If R₃ just lowers trust by being harsher, it adds no information beyond a stricter threshold on R₂ | R₃ localizes the break component in the majority of confirmed cases; R₃≠R₂-at-lower-threshold | B4, B5 |
| **Anti-claim to rule out (A3)**: "The IO bound dissolves with frontier models" | If GPT-4o/Claude reproduce everything regardless of IO, the theory is model-specific | Frontier robustness subset shows the same IO pattern (attenuated but not eliminated) | B6 |
| **Anti-claim to rule out (A4)**: "The whole effect is a prompt-engineering artifact of our agent harness" | Reviewers will attribute the IO gradient to implementation details, not theory | Fresh isolated workspace, randomized condition order, pre-registered seed, cross-harness robustness (ARIS vs. raw SciSciGPT graph) | B2 |

---

## Paper Storyline

- **Main paper must prove**:
  - ECRF is multi-dimensional and varies systematically (Study 1 — establishes the construct)
  - IO causally drives ECRF, asymmetrically across components (Study 2 — establishes the mechanism)
  - Result-level trust inflation is real, measurable, mechanistically decomposable (B₁–B₄), and correctable by component audit (Study 3 — the main contribution)
- **Appendix can support**:
  - Frontier-model robustness subset (attenuation pattern)
  - Full per-paper evidence-chain heatmaps and break adjudication traces
  - Inter-annotator α tables and adjudication protocols
- **Experiments intentionally cut**:
  - SciSciBench full benchmark (→ one motivation paragraph: L3 true capability ~0.3–0.5 establishes the *need* for audit; not a benchmark paper)
  - retracted-paper-detection / paper-mill work (different project)
  - ARIS/Codex/Claude engineering narrative (irrelevant to IS/management readers)
  - Multi-model radar charts as a *headline* (kept only as robustness, not as model comparison contribution)

---

## Experiment Blocks

### Block 1: Main Anchor Result — STRICT reproduction pathway is achievable and measurable
- **Claim tested**: The framework can measure faithful reproduction where it should exist (calibrates the "valid" end of the trust scale).
- **Why this block exists**: Before claiming trust inflation, we must show the measurement instrument correctly recognizes genuine reproductions.
- **Dataset / split / task**: 3 STRICT papers (Petersen2024, Park2023, Bentley2023) — already DONE (R002/R004/R007).
- **Compared systems**: DeepSeek-V4-Pro agent vs. gold numerical targets.
- **Metrics**: D3 numerical accuracy (8/8, 6/6, 9/9 = 100%), sample-N exact, R² exact, significance match.
- **Setup details**: C1 condition (paper only), single seed per paper, DeepSeek-V4-Pro via Anthropic-compatible path.
- **Success criterion**: ≥3 STRICT papers at D3≥0.95 — **MET (3/3 at 1.00)**.
- **Failure interpretation**: If STRICT failed, the framework could not anchor the "valid" pole, undermining the TIR metric.
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
- **Dataset / split / task**: Same Study 2/3 runs, re-scored under four regimes (R₁ result-level / R₂ aggregate composite / R₃ task-contingent component audit / **R₃′ overbuilt** = all-6-components-must-pass regardless of task type).
- **Compared systems**: R₃ vs R₃′(overbuilt) vs R₂-lowered-threshold.
- **Metrics**: TIR under each regime; break-localization rate; trust deflation rate.
- **Setup details**: Re-scoring only — no new agent runs.
- **Success criterion**: R₃ (task-contingent) achieves lower TIR than R₁ *without* the excess trust deflation of R₃′; R₃ ≠ R₂-at-lower-threshold on localization (defends A2).
- **Failure interpretation**: If R₃′ beats R₃ meaningfully, task-contingency is unnecessary complexity → simplify. If R₂-at-lower-threshold matches R₃, the component structure adds nothing → theory weakened.
- **Table / figure target**: Appendix ablation table.
- **Priority**: MUST-RUN (defends simplicity + A2).

### Block 4: Failure Analysis / Evidence Break Types (B₁–B₄) — the mechanism of inflation
- **Claim tested**: Trust inflation is mechanistically decomposable into B₁–B₄, each with an automated detection rule that survives human adjudication.
- **Why this block exists**: Makes "trust inflation" concrete and falsifiable rather than a residual statistic.
- **Dataset / split / task**: All flagged cases from Study 2/3 runs + random sample of unflagged cases (recall estimation).
- **Compared systems**: Automated screening rule → audit trace → human adjudication (two reviewers, resolve by discussion).
- **Metrics**: Rule precision, rule recall, confirmed-break rate per B-type; ≥5 human-confirmed breaks across ≥2 types.
- **Setup details**:
  - **B₁ Substitution**: DSF or VMF low, RRF moderate.
  - **B₂ Circularity**: regex scan for paper numerics in code **+ semantic code review** to exclude legitimate constants (years, sample sizes, thresholds).
  - **B₃ Shopping**: ≥3 model variants with paper-proximity selection *without* theoretical/methodological justification.
  - **B₄ Assertion**: claim-evidence traceability check, PRF low + CRS high.
- **Success criterion**: ≥5 human-confirmed breaks; ≥2 break types confirmed; B₂/B₃ false-positive rate controlled by semantic review.
- **Failure interpretation**: If <5 breaks confirm or false positives dominate, the B-typology is not empirically grounded → collapse to a single "process invalid" category.
- **Table / figure target**: Main-paper Table 3 (break-type matrix with examples) + Figure (trust inflation decomposition).
- **Priority**: MUST-RUN.

### Block 5: Frontier Necessity Check — does the IO bound survive frontier models?
- **Claim tested**: The IO→ECRF mechanism is not an artifact of weak models; it persists (attenuated) with frontier agents.
- **Why this block exists**: The paper's central construct is the *agent* in "generative agent auditing"; reviewers will demand evidence that stronger models do not trivially dissolve the bound (A3).
- **Dataset / split / task**: 8–10 papers × 3 IO levels × 2 frontier models (GPT-4o, Claude Sonnet/Opus) = ~54 runs.
- **Compared systems**: Frontier models vs. primary open-weight/low-cost models on the same IO gradient.
- **Metrics**: ECRF slope across IO per model tier; TIR(R₁) per tier; break-localization consistency.
- **Setup details**: API access; same isolation protocol; pre-registered subset.
- **Success criterion**: IO gradient direction consistent with primary pattern (attenuation allowed); TIR(R₁) > 0 for frontier tier.
- **Failure interpretation**: If frontier models reproduce at ceiling regardless of IO, scope the theory's claim explicitly to open-weight/mid-tier agents and reframe frontier as boundary condition (not failure — a clean scope statement).
- **Table / figure target**: Appendix robustness table; one main-panel sentence.
- **Priority**: HIGH (robustness, not blocking the core claim).

### Block 6: Two-Layer Human Validation — gold evidence chain + validity adjudication
- **Claim tested**: The ECRF and TIR measurements are reliable against human ground truth.
- **Why this block exists**: Without human labels, TIR is an insider metric and the whole governance story is unfalsifiable (the project's documented fatal weakness).
- **Dataset / split / task**: Layer 1 — 2 annotators per paper on the 20-paper pool; Layer 2 — validity adjudication on all flagged + sample of unflagged.
- **Compared systems**: Component-stratified α targets: Data Source ≥0.75, Sample/Indicator/Model ≥0.67, Result ≥0.80, Claim ≥0.60.
- **Metrics**: Inter-annotator α per component; rule precision/recall; confirmed-break rate.
- **Setup details**: Pre-registered annotation protocol; adjudication by discussion; transparent reporting of below-target components.
- **Success criterion**: ≥80% of components at or above target α; components below target reported transparently with adjudication.
- **Failure interpretation**: If Claim α < 0.60 even after adjudication, restrict quantitative TIR claims to higher-α components and treat Claim qualitatively.
- **Table / figure target**: Methods section reliability table.
- **Priority**: MUST-RUN (unblocks Study 3).

---

## Run Order and Milestones

| Milestone | Goal | Runs | Decision Gate | Cost | Risk |
|-----------|------|------|---------------|------|------|
| **M0 — Calibration** | Re-analyze M0/M1 (16 papers) under theory framing; confirm ECRF dimensionality | Study 1 analyses (no new runs) | Disagreement >0.15; localization >0.60 | ~0 GPU (re-analysis) | Low — most evidence exists |
| **M1 — Mini Study 2 Pilot** | De-risk IO gradient + break detection before scaling | 5 papers × 3 IO × 2 models = 30 runs | (1) IO₁<IO₂<IO₃ monotonic; (2) Component×IO visible; (3) ≥1 break detected; (4) result≠component on ≥1 case | ~15 GPU-h + API | **Highest-risk assumption**: IO₂ manipulation cleanly isolates documentation from code |
| **M2 — Study 2 Full** | Causal test of IO→ECRF (C2) | 120 primary runs + paper-pool finalization + Layer 1 annotation | Monotonic ECRF; significant Component×IO interaction | ~80 GPU-h + API | Paper-pool selection bias; mitigation = pre-agent annotation |
| **M3 — Study 3** | Trust inflation + audit correction (C1, main contribution) | 3-regime re-scoring + B₁–B₄ adjudication + Layer 2 validity | TIR(R₁)>0; TIR(R₁)>TIR(R₃) p<0.05; ≥5 confirmed breaks | ~$200 API + human adjudication | False positives in B₂/B₃; mitigation = semantic review + justification requirement |
| **M4 — Simplicity** | R₃ vs overbuilt R₃′ vs threshold-lowered R₂ | Re-scoring only | R₃ not dominated by simpler/stricter variants | ~0 compute | Low |
| **M5 — Frontier Robustness** | A3 boundary check | 8–10 papers × 3 IO × 2 frontier models ≈54 runs | IO direction consistent; TIR(R₁)>0 for frontier | API | Frontier at ceiling → scope statement, not failure |

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

**Purpose**: Validate IO gradient and evidence-break detection before committing to full 120-run experiment.

**Design**: 5 papers × 3 IO levels × 2 models = 30 runs.

**Papers**: One from each observability stratum (Low/Medium/High), spanning ≥2 domains. Include ≥2 papers with complex indicators or ambiguous samples. Candidate anchors: Petersen2024 (Low), Arts2021 (Medium), + 3 TBD from the 20-paper pool.

**Pass criteria (green-light for full Study 2)**:
1. IO₁ < IO₂ < IO₃ monotonic ECRF increase observed
2. Component × IO interaction visible (not flat across components)
3. ≥1 evidence-break case detected (B₁–B₄)
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
| B₂/B₃ false positives | Semantic code review + theoretical-justification requirement for shopping |
| Single-model-family concern (A3) | Frontier robustness subset (M5) |
| Low α on Claim component | Pre-registered component-stratified α targets; transparent reporting; quantitative TIR restricted to high-α components |
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
