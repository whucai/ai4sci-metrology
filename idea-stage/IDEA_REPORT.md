# Idea Report (Scientometrics Pivot): An AI-Agent Metrology of Computational Reproducibility

**Direction**: Measuring the Reproducibility of Computational Science with Generative AI Agents
**Date**: 2026-06-24 (v8 — Scientometrics pivot; supersedes v7 UTD/IS-governance framing, recoverable from git history)
**Target Venue**: *Scientometrics* (Springer, ISSN 0138-9130) — with *Quantitative Science Studies* / *Journal of Informetrics* as alternates
**Pipeline**: research-lit (59 papers ingested) → novelty-check → reframing

---

## Executive Summary

Scientometrics measures science through citation networks — productivity, impact, disruptiveness, collaboration. It has **no instrument that measures whether a published computational analysis actually re-executes and reproduces its claimed results.** Existing reproducibility signals are proxies: data-availability badges, registered reports, code-on-GitHub flags, or rare human-replication campaigns. None produce a continuous, comparable, component-resolved measure of reproduction fidelity at scale.

This paper introduces **Evidence-Chain Reconstruction Fidelity (ECRF)** — a reproducibility construct operationalized by a generative-AI agent that walks a computational paper's evidence chain (Data → Sample → Indicator → Model → Result → Claim) and is scored, per component, on whether its reconstruction matches the paper's reported analysis. We treat the agent not as a benchmark competitor but as a **measurement instrument**: a new metrology that extends the Science-of-Science agenda one level deeper — from measuring *impact* and *disruptiveness* to measuring *reproducibility* of individual findings.

Three claims: (1) ECRF is a multi-dimensional, component-resolved construct invisible to aggregate result-matching; (2) the conventional result-based reproducibility indicator carries systematic **measurement bias** — it overestimates true reproducibility because an agent can reproduce a number through the wrong process (four failure modes: substitution, circularity, shopping, assertion); (3) component-level auditing corrects this bias. As a scientometric capstone, we correlate agent-measured ECRF against established impact indicators (citations, CD-disruption index, altmetrics) — testing whether execution-level reproducibility is a measurable scientific variable linked to downstream impact, a hypothesis the field has been unable to test because the independent variable did not exist.

**One measurement chain**: Information Observability (input quality) → Evidence-Chain Reconstruction Fidelity (measured construct) → Result-Indicator Bias (measurement-validity failure).

---

## 1. Positioning within the Science-of-Science Tradition

The SciSci program quantifies inputs, processes, and outputs of the scientific enterprise via large-scale bibliographic/citation data to find universal regularities (Fortunato et al. 2018; Liu et al. 2023). Measurement is operationalized through citation-network constructs — the mechanistic citation model (Wang, Song & Barabási 2013), the CD/disruption index (Park, Leahey & Funk 2023) — and shared data infrastructure (SciSciNet, Lin et al. 2023).

**A structural observation**: in this tradition, "reproducibility" has meant *replicability of observed patterns across datasets or time periods* — never *reproducibility of an individual paper's reported analysis*. The measurement stack therefore stops at the citation topology of outputs; it does not reach inside a paper to ask whether the analysis itself re-derives.

Our contribution mirrors how the disruption index entered the field: **define a measurable quantity, show it is computable at scale, link it to existing SciSci variables.** ECRF is that quantity; the AI-agent reproduction pipeline is the instrument that computes it; the correlation with impact indicators is the scientometric linkage. This reframes SciSci from *correlational metrology* (measuring associations among output indicators) toward *causal reproducibility* (measuring whether results stand up to re-execution).

---

## 2. The Measurement Construct: Evidence-Chain Reconstruction Fidelity (ECRF)

A computational paper is not reproduced by matching a final number; it is reproduced by reconstructing the evidence chain linking data, sample, indicator, model, results, and claims. An AI agent attempting reproduction must reconstruct each component from what the paper makes observable.

**ECRF** measures reconstruction fidelity **per component** (Data Source, Sample, Indicator, Model, Result, Claim), not as an aggregate. The core measurement claim: ECRF is **not uniform across components** — components the paper specifies explicitly (formulas, target table values) are reconstructible; components relying on implicit judgment (preprocessing, specification choice) resist reconstruction. This asymmetry, beyond model capability, is the primary structure governing reproduction fidelity.

**Information Observability (IO)** — the degree to which each component is explicitly specified and accessible — is the measurement input (the independent variable). IO varies across components within a paper and across papers.

ECRF is the **measured construct**; IO is the input quality that drives it.

---

## 3. Measurement-Validity Failure: Result-Indicator Bias

Scientometric and bibliometric reproducibility signals most accessible to evaluators are result-level: do the reproduced numbers match the reported numbers? This is a **systematically biased indicator** of true reproducibility. It can read "success" when ECRF is low — the agent produced the right number through the wrong process.

We define **Result-Indicator Bias (RIB)** as the gap between result-based reproduction success and component-valid reproduction:

> RIB = P(result-level success) − P(component-valid success)

The primary empirical measure is the **False Reproduction Rate (FRR)**:

> FRR = P(component-invalid | result-level success)

— among reproductions a result-based indicator deems successful, what fraction are actually invalid at the component level? This is a measurement-validity statistic, directly analogous to the false-positive rate of a diagnostic indicator.

### Four Measurement Failure Modes (how the result indicator over-reads)

| Mode | Mechanism | Detectable at result level? | Detected by component audit? |
|------|-----------|------------------------------|------------------------------|
| **M₁ Substitution** | Agent uses wrong data/sample/indicator that coincidentally yields similar results | No | Yes — component fidelity low despite result match |
| **M₂ Circularity** | Agent embeds paper's reported values as outputs without genuine computation | No — "correct" by construction | Yes — code audit with semantic review |
| **M₃ Shopping** | Agent iterates model variants until results approximate reported values, without justification | No — final result matches | Yes — iteration log reveals paper-proximity selection |
| **M₄ Assertion** | Agent claims conclusions its own outputs do not support | No — claims look plausible | Yes — claim-evidence traceability fails |

These are **measurement failure modes of the result-based indicator**, not a taxonomy of bugs. Each has an automated screening rule → audit trace → human adjudication.

---

## 4. Empirical Strategy: Three Measurement-Validation Studies + Scientometric Linkage

### Study 1 — Construct validation: ECRF is multi-dimensional
**Purpose**: establish that ECRF varies independently across components, confirming component-level measurement captures structure invisible to aggregate scores.
**Design**: re-analyze existing M0/M1 pilot data (16 papers, 2 models).
**Evidence**: result-vs-component disagreement rate; error-localization rate; inter-component correlation structure.
**Status**: calibration, re-analysis of existing data.

### Study 2 — Input sensitivity: IO drives ECRF, asymmetrically
**Purpose**: test the measurement instrument's sensitivity — IO causally affects ECRF, and the effect differs across components.
**Design**: 20 papers × 3 IO levels × 2 models = 120 runs.
| IO level | Observability | Agent access |
|----------|---------------|--------------|
| IO₁ (low) | Narrative only | Paper text; no web/data/code |
| IO₂ (medium) | Structured docs, no executable code | Paper + data dictionary + variable/sample docs; no original code |
| IO₃ (high) | Full executable materials | Paper + data + original code |
**Analysis**: per-component ECRF slope across IO; Component × IO interaction (mixed-effects).
**Success**: monotonic ECRF increase IO₁→IO₃; ≥2 components improve significantly; significant interaction.

### Study 3 — Measurement-validity: result-indicator bias + audit correction (MAIN)
**Purpose**: show the result-based indicator carries systematic bias (FRR > 0) and component-level audit corrects it.
**Design**: all Study-1/2 runs scored under three regimes against human-adjudicated validity labels.
| Regime | Assumption | Trust signal | Expected FRR |
|--------|-----------|--------------|--------------|
| R₁ Result-level | result match ⇒ valid | numbers match | High |
| R₂ Aggregate composite | weighted score ⇒ valid | composite > threshold | Moderate |
| R₃ Component audit | task-critical components pass + no failure mode flagged | component-level | Low |
**Primary test**: FRR(R₁) > FRR(R₃), McNemar p<0.05; ≥5 human-confirmed failure-mode cases across ≥2 modes.
R₃ is task-contingent: only components applicable to the task type must pass.

### Study 4 — Scientometric linkage (the field-facing capstone)
**Purpose**: establish ECRF as a *scientometric variable* by linking it to established impact indicators — the hypothesis the field could not previously test.
**Design**: for the measured paper set, regress ECRF (and component-level ECRF) against citations, CD-disruption index (Park et al. 2023), altmetric attention, team size (Wu, Wang & Evans 2019).
**Hypotheses (exploratory + confirmatory)**:
- Hₛ₁: papers with higher ECRF receive more citations (reproducibility → impact), controlling for field and team size.
- Hₛ₂: disruptive papers (high CD-index) have *lower* ECRF (disruption trades off against reproducibility of established methods).
- Hₛ₃: component-level ECRF (especially Indicator/Model) predicts impact more strongly than aggregate result-match.
**Why this matters**: this is the scientometric payoff — a new latent variable (execution-level reproducibility) measured by AI agents and shown to relate to the field's existing impact constructs. No prior work could test this because the IV did not exist.

---

## 5. Novelty vs. Closest Prior Art

| Axis | Closest verified prior work | Our differentiation |
|------|-----------------------------|--------------------|
| (a) Agent reproduces a *published computational paper* | Theiler et al. 2026 (arXiv 2605.28371) — paper-to-benchmark agent | Domain-locked to industrial PHM; outputs a normalized benchmark implementation, not a *measurement of where reproduction fails* |
| (b) Component-level reproducibility metric | SRI / Hossain et al. 2025 (arXiv 2509.23645) — per-cell notebook reproducibility index | Measures *notebook reruns*, no AI agent, no paper-to-code step; components are notebook cells, not a paper's evidence/claim chain |
| (c) Reproduction-as-measurement (not leaderboard) | Kapoor & Narayanan 2022 (arXiv 2207.07048) — leakage audit across ML-science | *Human* retrospective audit, not agent reproduction; no per-component failure map of a live reproduction attempt |

**No verified prior work combines (a)+(b)+(c).** The intersection — an AI agent that walks a paper's evidence chain and whose *output is a measurement of where the chain breaks*, then linked to scientometric impact — is genuinely novel. Existing agent benchmarks (PaperBench, ScienceAgentBench, SciCode, MLE-bench, MLAgentBench) are leaderboards measuring task success; they do not produce a component-resolved reproduction-fidelity metric nor treat reproduction as a measurement instrument.

---

## 6. Paper Pool, Scale, and Data

**Selection finalized before agent execution** (pre-registered). Each paper pre-annotated on data availability, code availability, indicator complexity, sample ambiguity, model multiplicity, claim-result distance.

| Stratum | Observability profile | N |
|---------|----------------------|---|
| Low variation | data/formulas/models clearly specified; code available | 8 |
| Medium variation | multi-step indicators or complex samples; some under-specified | 12 |
| High variation | key components ambiguous; data unavailable or claims exceed results | 10 |

**Domain distribution**: Science of Science (10), IS/Innovation (10), Management/Strategy (10) — retained from the v7 design because cross-disciplinary variation is a scientometric strength.

**Large-N extension for Study 4**: the 115-paper SciSciBench corpus (already measured, L2=0.907) provides the bibliometric-scale substrate to correlate ECRF with impact indicators, complementing the 30-paper deep-stratified set. This is the scale *Scientometrics* expects.

**Models** (by tier, versions + access dates in setup): open-weight (Qwen3-32B, local), low-cost API (DeepSeek-V3/V4-Pro), commercial frontier (GPT-4o, Claude Sonnet/Opus 4) — frontier used as robustness subset, not as a model-comparison headline.

---

## 7. Existing Evidence (pre-pilot)

- M0: 6 papers, 3 STRICT at D3=100% (anchors the "valid" pole of the measurement scale)
- M1: 10-paper framework validation, all 4 tests PASS
- SciSciBench: 115 papers, L2=0.907 (only discriminating level) — motivates the need for component-level measurement
- L3 DeepSeek: overall=0.298, direction-commit rate=23.4% — establishes that result-level and component-level diverge (preliminary FRR evidence)
- Error localization proven: R003 (Arts 2021) localized a formula bug to lines 233–236 — component-level audit works

---

## 8. Paper Structure (Scientometrics-style)

1. **Introduction** — reproducibility as the unmeasured layer in scientometrics; the AI-agent-as-instrument proposal
2. **Background** — SciSci measurement tradition (Fortunato 2018; Liu 2023); reproducibility-as-metric literature (OSC 2015; Nosek 2021; Kapoor 2022); LLM-as-measurement-instrument stream (Thelwall 2025/2026; Bornmann 2024; de Winter 2024)
3. **The ECRF construct** — evidence chain, component decomposition, IO as input
4. **Measurement-validity framework** — result-indicator bias, false reproduction rate, four failure modes
5. **Study 1** — construct validation (ECRF dimensionality)
6. **Study 2** — IO → ECRF input sensitivity
7. **Study 3** — result-indicator bias + audit correction (main measurement-validity result)
8. **Study 4** — scientometric linkage of ECRF to impact indicators (field-facing capstone)
9. **Discussion** — a reproducibility metrology for science; implications for research assessment; limitations
10. **Conclusion**

---

## 9. What Changed from the UTD (v7) Framing

| Element | v7 (UTD / IS governance) | v8 (Scientometrics) |
|---------|--------------------------|---------------------|
| Core contribution | IS governance theory + trust calibration concept | A new reproducibility *metrology* + scientometric variable |
| Theory apparatus | P1–P4 propositions, information-processing/algorithmic-auditing theory | Trimmed to a measurement model; SciSci measurement tradition as anchor |
| TCE construct | "Trust Calibration Error" (governance failure) | "Result-Indicator Bias" (measurement-validity failure) |
| Primary metric | Trust Inflation Rate (governance) | False Reproduction Rate (measurement bias) |
| B₁–B₄ | "Evidence break types" (governance mechanisms) | "Measurement failure modes" (indicator failure modes) |
| Field linkage | IS/AI-governance literature | SciSci + reproducibility-as-metric + LLM-as-instrument |
| New capstone | — | **Study 4**: ECRF ↔ citations/CD-index/altmetrics/team size |
| Cut | Lebovitz/Metaxa/Raji/governance framing; "organizational trust" language | — |
| Kept | Evidence chain, component-level fidelity, IO gradient, 3-regime comparison, B-typology, stratified paper pool, 2-layer human validation | — |

---

## 10. Terminology Discipline

| Prefer | Avoid |
|--------|-------|
| measurement instrument, construct, metrology, indicator, bias | governance, trust calibration, audit system, scoring system |
| evidence chain, component fidelity, failure mode | pipeline, component failure, error type |
| reproducibility fidelity, false reproduction rate | trust inflation rate |
| scientometric variable, impact indicator | benchmark, leaderboard |

---

## Next Steps

- [ ] Update `refine-logs/FINAL_PROPOSAL.md` to the v8 scientometrics framing (Study 4 added; metric rename TIR→FRR, TCE→RIB)
- [ ] Update `refine-logs/EXPERIMENT_PLAN.md` claim map: add Study-4 claim block (ECRF ↔ impact), rename C1 to measurement-bias framing
- [ ] External review (/research-review) on the v8 framing — does Study 4 land for a *Scientometrics* reviewer?
- [ ] Pilot: re-score existing M0/M1 + L3 data under R₁/R₃ to produce a preliminary FRR estimate before scaling
