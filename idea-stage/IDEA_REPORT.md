# Idea Discovery Report: Evidence-Chain Theory of AI Reproduction Auditing

**Direction**: When Can We Trust AI-Generated Scientific Reproductions? An Evidence-Chain Theory of Generative Agent Auditing
**Date**: 2026-06-24 (v7 — theory compression: IO → ECRF → TCE, 4 Propositions)
**Target Venue**: UTD journals — ISR / MISQ / Management Science

---

## Executive Summary

Generative AI agents can now execute computational research — finding data, writing code, running models, producing results. When they succeed, organizations face a governance question: **can these AI-generated reproductions be trusted?**

This paper develops an **evidence-chain theory of AI reproduction auditing**. The core theoretical claim: AI reproduction is not limited by model accuracy, but by the **partial observability of the scientific evidence chain**. The evidence chain (Data → Sample → Indicator → Model → Result → Claim) is unevenly reconstructible — some components are fully observable from paper text, others remain opaque regardless of how much information is provided. This asymmetry produces a systematic gap between perceived reproduction success (result-level evaluation) and actual reproduction validity (component-level audit). We call this gap **trust calibration error**.

**One theoretical chain**: Information Observability → Evidence Chain Reconstruction Fidelity → Trust Calibration Error.

---

## 1. Theory: Information Observability → Reconstruction Fidelity → Trust Calibration

### 1.1 The Core Theoretical Construct: Information Observability (IO)

Computational papers describe a chain of evidentiary operations: where data came from, how samples were constructed, which indicators were computed, what models were estimated, what results were obtained, and what claims were drawn. But this chain is never fully visible to a reader — or to an AI agent. Some components are explicitly described (formulas, table values). Others are compressed into phrases like "standard preprocessing" or "following prior work." Still others are entirely implicit — the analyst's judgment calls about outlier treatment, bandwidth selection, or specification choice.

We define **Information Observability (IO)** as the degree to which each component of the scientific evidence chain is explicitly specified and directly accessible to an AI agent attempting reproduction. IO varies across components within the same paper — a formula may be fully observable while the sample filtering logic is only partially specified — and across papers — some papers provide code and data, others provide only narrative.

IO is the independent variable in our theory.

### 1.2 The Mediating Mechanism: Evidence Chain Reconstruction Fidelity (ECRF)

An AI agent attempting reproduction must reconstruct each component of the evidence chain from observable information. **Evidence Chain Reconstruction Fidelity (ECRF)** measures how accurately the agent reconstructs each component: Did it identify the correct data source? Did it apply the correct filtering rules? Did it implement the correct indicator formula? Did it specify the correct model? Do its results match? Do its conclusions follow from its results?

The key theoretical claim: **ECRF is not uniform across components.** Components with high observability (explicit formulas, target table values) can be reconstructed with high fidelity. Components with low observability (implicit preprocessing, undocumented specification choices) resist reconstruction. Model capability matters, but its effect is bounded by the observability of the evidence chain. This asymmetry, beyond model capability alone, is a primary mechanism governing AI reproduction quality.

ECRF is the mediating mechanism in our theory.

### 1.3 The Outcome Variable: Trust Calibration Error (TCE)

When organizations evaluate AI-generated reproductions, they rely on observable signals. The most accessible signal is result-level agreement: do the reproduced numbers match the paper's reported numbers? But result-level agreement is a systematically misleading signal. It can be high when ECRF is low — the agent produced the right number through the wrong process, or hard-coded the paper's values, or used a different sample that coincidentally produced similar results.

We define **Trust Calibration Error (TCE)** as the gap between perceived reproduction success (result-level evaluation) and actual reproduction validity (component-level audit):

> TCE = P(result-level success) − P(component-valid success)

TCE captures the governance failure: organizations that rely on result-level evaluation systematically overestimate the trustworthiness of AI-generated reproductions. Component-level auditing reduces TCE by detecting evidence-chain breaks that result-level evaluation misses.

TCE is the outcome variable in our theory.

### 1.4 Four Theoretical Propositions

**P1 (Observability Bound)**: AI reproduction fidelity is bounded by the partial observability of the scientific evidence chain. Components with higher observability are reconstructed with higher fidelity.

→ Tested in Study 2 via the IO gradient (C1: narrative-only → C2: structured descriptions → C3: full materials).

**P2 (Asymmetric Reconstructability)**: Errors arise from asymmetric reconstructability across evidence-chain components. Sample construction, indicator operationalization, and model specification — components where judgment and implicit knowledge matter most — are systematically harder to reconstruct than data source identification or result reporting.

→ Tested in Studies 1-2 via per-component ECRF variation and the Component × IO interaction.

**P3 (Trust Inflation)**: Result-level evaluation produces systematic trust calibration error. Because observable agreement at the result level can mask unobservable failures at upstream components, organizations relying on result-level evaluation will overestimate reproduction validity.

→ Tested in Study 3 via the three-protocol comparison: Protocol A (result-level) vs Protocol C (component-level) against human-adjudicated labels.

**P4 (Audit Correction)**: Component-level auditing reduces trust calibration error by surfacing evidence-chain breaks that result-level evaluation fails to detect.

→ Tested in Study 3 via TCE reduction when moving from Protocol A to Protocol C, and via the evidence break type taxonomy.

### 1.5 From Propositions to Empirical Hypotheses

Theory propositions are translated into testable empirical hypotheses:

| Theory Proposition | Empirical Hypothesis | Study |
|-------------------|---------------------|-------|
| P1: Observability Bound | H1: ECRF increases from IO₁ to IO₃ | Study 2 |
| P2: Asymmetric Reconstructability | H2: IO effect varies systematically across evidence-chain components | Study 2 |
| P3: Trust Inflation | H3: Result-level regime has positive Trust Inflation Rate | Study 3 |
| P4: Audit Correction | H4: Component-level audit reduces Trust Inflation Rate relative to result-level evaluation | Study 3 |

---

## 2. Theoretical Positioning

### 2.1 What Kind of Theory Is This?

This is an **explanatory mechanism theory** in the IS tradition. It does not predict *whether* AI can reproduce papers (a performance question). It explains *why* AI reproductions fail in ways invisible to conventional evaluation, *where* in the evidence chain failures concentrate, and *how* organizations can detect them.

### 2.2 Relationship to Existing Theory Streams

| Stream | Core Concept | Our Extension |
|--------|-------------|---------------|
| **Information processing theory** (Galbraith, Tushman & Nadler) | Organizations process information to reduce uncertainty | AI agents face the same information-processing constraint — but the "information" is the evidence chain, and its observability determines reconstruction fidelity |
| **Algorithmic auditing** (Metaxa et al., Raji et al.) | Automated decisions require independent audit | Extends auditing from fairness/accountability to scientific validity — the audit target is evidence-chain integrity, not decision bias |
| **Scientific reproducibility** (NASEM, ACM Artifact Badging) | Reproducibility requires artifacts and verification | Extends from human-submitted artifacts to AI-generated reproductions — the reproducing entity is the variable, not the artifact |
| **AI governance / trust** (Glikson & Woolley, Lebovitz et al.) | Trust in AI requires understanding capability boundaries | Introduces trust calibration error as a measurable governance metric specific to AI-generated knowledge outputs |

### 2.3 What This Theory Is NOT

- NOT a benchmark performance paper ("LLMs score X on task Y")
- NOT an evaluation system paper ("we built a tool that scores reproductions")
- NOT a model comparison paper ("GPT-4o outperforms Qwen3 on reproduction")
- It IS a theory about **why AI-generated scientific outputs create a specific, measurable governance failure — and how to correct it.**

---

## 3. Empirical Strategy: Three Studies

### Study 1: Construct Validation (ECRF Dimensionality)

**Theoretical purpose**: Establish that ECRF is multi-dimensional — evidence-chain components vary independently, confirming that component-level measurement captures structure invisible to aggregate scores.

**Key evidence**: Disagreement rate (P(result-success ≠ component-success)), error localization rate, inter-component correlation structure.

**Status**: Existing M0/M1 pilot data. Calibration, not main experiment.

---

### Study 2: Observability → Reconstruction Fidelity (P1, P2)

**Theoretical purpose**: Test the core mechanism — IO causally affects ECRF, and the effect is asymmetric across components.

**Design**: 20 papers × 3 IO levels × 2 primary models = 120 runs. Robustness: 8-10 papers × 2 frontier models.

**IO Gradient**:

| Level | Observability | Agent Access Boundary |
|-------|-------------|----------------------|
| **IO₁ (Low)** | Narrative evidence only | Paper text; no web, no data, no code |
| **IO₂ (Medium)** | Structured documentation, no executable code | Paper + data dictionary + variable documentation + sample construction notes; controlled raw data access where task requires it, but **no original code or reproduction scripts** |
| **IO₃ (High)** | Full executable materials | Paper + data + original code; provided materials only |

**Critical design rules**: Fresh isolated workspace per run; condition order randomized; no cross-condition context leakage.

**Analysis**: Paired ECRF differences across IO levels per component; Component × IO interaction (mixed-effects model).

**Success criteria**: Monotonic ECRF increase from IO₁ to IO₃; significant improvement in ≥2 components; Component × IO interaction confirms asymmetric reconstructability.

---

### Study 3: Trust Calibration Error (P3, P4) — **MAIN CONTRIBUTION**

**Theoretical purpose**: Demonstrate that result-level evaluation produces systematic TCE, and component-level auditing corrects it by detecting evidence-chain breaks.

**Design**: All runs from Studies 1-2 scored under three evaluation regimes against human-adjudicated validity labels.

#### Three Evaluation Regimes

| Regime | Observability Assumption | Trust Signal | Expected TCE |
|--------|-------------------------|-------------|-------------|
| **R₁: Result-level** | Assumes result agreement implies valid reproduction | Final numbers match → trust | High |
| **R₂: Aggregate composite** | Assumes weighted combination captures validity | Composite score > threshold → trust | Moderate |
| **R₃: Component-level audit** | Requires evidence at each task-critical chain component | All **task-critical** components pass + no evidence break flagged → trust | Low |

**R₃ is task-contingent**: Not all six components apply to every task type. The audit requires components that are *applicable to the task type* to pass.

**Trust Calibration Error (TCE)** — the aggregate calibration construct:

> TCE^r = P(Regime r says trust) − P(Human says valid)

TCE captures the overall trust deviation: positive values indicate net trust inflation, negative values indicate net trust deflation.

**Trust Inflation Rate (TIR)** — the primary empirical measure:

> TIR = P(Human says invalid | Regime says trust)

We use TCE as the aggregate calibration construct and TIR as the primary empirical measure of trust inflation (P3). TIR is the paper's main dependent variable in Study 3: among reproductions a regime deems trustworthy, what fraction are actually invalid? Compared via McNemar test on paired classifications (each run scored by all three regimes against the same human label).

#### Evidence Break Types (Mechanisms of Trust Inflation)

Result-level trust inflation (P3) operates through four structural mechanisms. Each describes *why* result-level agreement can be high while component-level validity is low:

| Evidence Break Type | Mechanism | Observable at Result Level? | Detected by Component Audit? |
|--------------------|-----------|---------------------------|---------------------------|
| **B₁: Substitution** | Agent uses wrong data/sample/indicator that coincidentally produces similar results | No — result looks correct | Yes — DSF or VMF low despite RRF moderate |
| **B₂: Circularity** | Agent embeds paper's reported values as computational outputs without genuine computation | No — result is "correct" by construction | Yes — code audit with semantic review distinguishes legitimate constants from target leakage |
| **B₃: Shopping** | Agent iterates through model variants until results approximate the paper's reported values, without documented theoretical or methodological justification | No — final result matches | Yes — model iteration log reveals selection by paper-proximity |
| **B₄: Assertion** | Agent claims conclusions that its own computational outputs do not support | No — claims appear plausible | Yes — claim-evidence traceability check fails |

**Three-layer evidence per type**: automated screening rule → audit trace documentation → human adjudication.

#### Human Validation (Two-Layer)

- **Layer 1 (Gold evidence chain)**: 2 annotators per paper establish gold data source, sample, indicator, model, results, claims. Component-stratified reliability targets: Data Source α ≥ 0.75, Sample/Indicator/Model α ≥ 0.67, Result α ≥ 0.80, Claim α ≥ 0.60. Claim-level labels involve higher interpretive judgment (claims are stated in natural language with varying specificity), so lower raw agreement is expected; all disagreements are adjudicated. Components below target are flagged and reported transparently.
- **Layer 2 (Validity adjudication)**: Human experts review all flagged cases + random sample of unflagged cases (recall estimation). Two adjudicators, resolve by discussion.

#### Success Criteria
1. ≥5 human-confirmed evidence break cases
2. Trust Inflation Rate(R₁) > Trust Inflation Rate(R₃), McNemar p<0.05
3. ≥2 evidence break types confirmed
4. Component audit correctly localizes the break in majority of confirmed cases

---

## 4. Paper Pool: Stratified by Observability Variation

**Selection rule**: Paper selection is finalized before agent execution to avoid outcome-driven sampling. Each paper is pre-annotated on data availability, code availability, indicator complexity, sample ambiguity, model multiplicity, and claim-result distance.

| Stratum | Observability Profile | Target N |
|---------|----------------------|----------|
| **Low variation** | Data, formulas, and model clearly specified; code available | 8 |
| **Medium variation** | Multi-step indicators or complex samples; some components under-specified | 12 |
| **High variation** | Key components ambiguously described; data unavailable or claims exceed results | 10 |

**Domain distribution**: Science of Science (10), IS/Innovation (10), Management/Strategy (10).

---

## 5. Model Configuration

Models identified by capability tier; specific versions and access dates reported in experimental setup.

| Tier | Representative Model | Deployment | Scope |
|------|---------------------|-----------|-------|
| Open-weight reasoning | Qwen3-32B | Local GPU | Study 2 full 120 runs |
| Low-cost API | DeepSeek-V3/V4-Pro | API | Study 2 full 120 runs |
| Commercial frontier A | GPT-4o | API | Study 2 robustness subset |
| Commercial frontier B | Claude Opus 4 / Sonnet 4 | API | Study 2 robustness subset |

**Rationale**: Primary analysis estimates within-model effects of information observability (IO₁→IO₃); the frontier subset tests whether the observed pattern generalizes to stronger commercial agents.

---

## 6. Paper Structure

1. **Introduction** — AI agents in research, the trust question, P1-P4 preview
2. **Theory** — Information Observability → Evidence Chain Reconstruction Fidelity → Trust Calibration Error
3. **Study 1** — Construct validation (ECRF dimensionality)
4. **Study 2** — Observability → Reconstruction (P1, P2)
5. **Study 3** — Trust Calibration Error and Audit Correction (P3, P4) — **main results**
6. **General Discussion** — Theory contributions, governance implications, limitations
7. **Conclusion**

---

## 7. Terminology Discipline

| Prefer | Avoid (engineering-oriented uses) |
|--------|----------------------------------|
| theory, theoretical construct, mechanism | pipeline, system, benchmark |
| observability, reconstruction fidelity | scoring, metric |
| governance, audit, trust calibration | evaluation system, scoring system |
| evidence chain, evidence break | component failure, error type |
| proposition (theory) → hypothesis (empirical) | — |

Note: "theoretical framework" is acceptable in the IS tradition when referring to the theory structure; the concern is engineering-oriented uses of "framework" (e.g., "evaluation framework").

---

## 8. What Was Deleted

| Deleted | Reason |
|---------|--------|
| All "framework" / "pipeline" / "benchmark" language | Replaced with theory language |
| R000-R007 narrative | Absorbed into Study 1 calibration |
| SciSciBench details | One-paragraph motivation only |
| retracted-paper-detection | Different paper |
| ARIS/Codex/Claude engineering | Not relevant |
| "Spurious reproduction taxonomy" | Renamed: Evidence Break Types (mechanisms, not classification) |
| "Three evaluation protocols" | Renamed: Three evaluation regimes (embody different observability assumptions) |
| "H1/H2/H3" hypothesis language | Renamed: P1-P4 (theoretical propositions) |
