# Final Proposal: An AI-Agent Metrology of Computational Reproducibility

**Date**: 2026-06-24 (v8 — Scientometrics pivot)
**Target Venue**: *Scientometrics* (Springer); alternates QSS / Journal of Informetrics

---

## Problem Anchor

Scientometrics measures science through citation networks — impact, disruptiveness, collaboration — but has **no instrument that measures whether a published computational analysis actually re-executes and reproduces its claimed results.** Existing reproducibility signals are proxies (data-availability badges, registered reports, code-on-GitHub flags) or rare, small-N human-replication campaigns. None produce a continuous, component-resolved reproduction-fidelity metric at scale. The most accessible evaluator signal — result-level numerical agreement — is systematically biased: an agent can reproduce a number through the wrong process.

## Core Measurement Model

Reproducibility is not bounded by model accuracy but by the **partial observability of the scientific evidence chain**. The evidence chain (Data → Sample → Indicator → Model → Result → Claim) is unevenly reconstructible; components vary in how completely the paper specifies them, and this variation directly determines whether an AI agent can faithfully reproduce each component.

**Measurement chain**: Information Observability (IO, input quality) → Evidence-Chain Reconstruction Fidelity (ECRF, measured construct) → Result-Indicator Bias (RIB, measurement-validity failure).

## Constructs → Empirical Tests

| Construct | Operationalization | Empirical test | Study |
|-----------|-------------------|----------------|-------|
| **ECRF multi-dimensionality** | per-component reconstruction fidelity varies independently | disagreement rate, localization rate, component correlation | Study 1 |
| **IO → ECRF (input sensitivity)** | IO causally drives ECRF, asymmetrically across components | monotonic ECRF IO₁→IO₃; Component×IO interaction | Study 2 |
| **RIB / False Reproduction Rate** | result-level indicator over-reads true reproducibility | FRR(R₁) > 0; FRR(R₁) > FRR(R₃), McNemar p<0.05 | Study 3 |
| **Scientometric linkage** | ECRF as a new scientometric variable correlated with impact | ECRF ↔ citations / CD-index / altmetrics / team size | Study 4 |

## Four Studies

| Study | Role | Design | Status |
|-------|------|--------|--------|
| **Study 1**: Construct validation | establish ECRF dimensionality | 10–15 papers × 2 models, re-analyze M0/M1 | Re-analyze existing |
| **Study 2**: IO → ECRF | input-sensitivity test of the instrument | 20 papers × 3 IO × 2 models = 120 runs + frontier subset | TODO |
| **Study 3**: RIB + audit correction | **main measurement-validity result** | 3-regime comparison vs human labels; M₁–M₄ failure modes | TODO |
| **Study 4**: Scientometric linkage | **field-facing capstone** — ECRF as a scientometric variable | regress ECRF on citations/CD-index/altmetrics/team size over 30-paper deep set + 115-paper SciSciBench substrate | TODO |

## Key Innovation

This is NOT a benchmark leaderboard, an evaluation system, or a model comparison. It is a **reproducibility metrology**: a new measurement instrument (the AI-agent reproduction pipeline) that operationalizes an unmeasured latent construct — *execution-level reproduction fidelity* — at bibliometric scale, complementing the existing proxy chain (badges → data availability → registered reports → human replications).

The paper's strongest empirical claims: (1) the result-based reproducibility indicator carries systematic measurement bias (False Reproduction Rate > 0), measurable (FRR), mechanistically decomposable (M₁–M₄), and correctable (component-level audit → lower FRR); (2) agent-measured ECRF correlates with established scientometric impact indicators — the first test of a hypothesis the field could not previously formulate because the independent variable did not exist.

## Metric & Construct Renames (v7 → v8)

| v7 (UTD) | v8 (Scientometrics) | Rationale |
|----------|---------------------|-----------|
| Trust Calibration Error (TCE) | Result-Indicator Bias (RIB) | measurement-validity framing, not governance |
| Trust Inflation Rate (TIR) | False Reproduction Rate (FRR) | diagnostic-indicator false-positive analogy |
| Evidence break types B₁–B₄ | Measurement failure modes M₁–M₄ | indicator failure modes, not governance mechanisms |
| Three evaluation regimes | Same (R₁/R₂/R₃) — unchanged | — |
| P1–P4 propositions | Trimmed to a measurement model | scientometrics is empirical/methodological, not theory-heavy |

## Differentiators

| Dimension | Our Work | Closest Competitor |
|-----------|----------|-------------------|
| Measured construct | ECRF — component-resolved reproduction fidelity | SRI (Hossain 2025): notebook-cell reproducibility, no agent, no paper-to-code |
| Agent reproduces published paper | Yes, full evidence chain | Theiler 2026: domain-locked PHM, outputs benchmark not measurement |
| Reproduction-as-measurement | FRR + M₁–M₄ failure modes | Kapoor 2022: human retrospective audit, no live agent reproduction |
| Scientometric linkage | ECRF ↔ citations/CD-index/altmetrics | None — no prior work has the IV |
| Human validation | 2-layer, component-stratified α, recall estimation | Most benchmarks: no human validation |

## Risks

| Risk | Mitigation |
|------|------------|
| Read as "just a benchmark" | Frame as measurement instrument + Study 4 scientometric linkage |
| Failure-mode cases too few (<5) | Stratified sampling by observability variation; mini Study 2 de-risks |
| M₂/M₃ false positives | Semantic code review + theoretical-justification requirement |
| Study 4 correlations are confounded | Control for field, team size, year; report as exploratory + confirmatory; pre-register |
| Frontier models at ceiling | Scope statement (open-weight/mid-tier boundary), not failure |
| Low α on Claim component | Transparent reporting; restrict quantitative FRR to high-α components |
