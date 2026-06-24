# Final Proposal: Evidence-Chain Theory of AI Reproduction Auditing

**Date**: 2026-06-24 (v7.1 — 9 micro-adjustments applied)
**Target Venue**: ISR / MISQ / Management Science

---

## Problem Anchor

Generative AI agents can execute computational research — finding data, writing code, running models, producing results. When they succeed, organizations face a governance question: **can these AI-generated reproductions be trusted?** The most accessible trust signal — result-level agreement — is systematically misleading. An agent can produce the right number through the wrong process, and conventional evaluation cannot tell the difference.

## Core Theory

AI reproduction is not limited by model accuracy, but by the **partial observability of the scientific evidence chain**. The evidence chain (Data → Sample → Indicator → Model → Result → Claim) is unevenly reconstructible — components vary in how completely they are specified in papers, and this variation directly determines whether an AI agent can faithfully reproduce them.

**Theoretical chain**: Information Observability (IO) → Evidence Chain Reconstruction Fidelity (ECRF) → Trust Calibration Error (TCE).

## Propositions → Hypotheses

| Theory Proposition | Empirical Hypothesis | Study |
|-------------------|---------------------|-------|
| **P1 (Observability Bound)**: AI reproduction fidelity is bounded by IO | H1: ECRF increases from IO₁ to IO₃ | Study 2 |
| **P2 (Asymmetric Reconstructability)**: IO effect varies across evidence-chain components | H2: Component × IO interaction is significant | Study 2 |
| **P3 (Trust Inflation)**: Result-level evaluation produces systematic trust inflation | H3: Trust Inflation Rate(R₁) > 0 | Study 3 |
| **P4 (Audit Correction)**: Component-level auditing reduces trust inflation | H4: TIR(R₁) > TIR(R₃) | Study 3 |

## Three Studies

| Study | Theoretical Role | Design | Status |
|-------|-----------------|--------|--------|
| **Study 1**: Construct Validation | Establish ECRF multi-dimensionality | 10-15 papers × 2 models, 3 task types | Re-analyze M0/M1 |
| **Study 2**: IO → ECRF (P1, P2) | Causal test of core mechanism | 20 papers × 3 IO levels × 2 models = 120 runs + frontier subset | TODO |
| **Study 3**: Trust Inflation + Audit (P3, P4) | **Main contribution** | 3-regime comparison against human labels | TODO |

## Key Innovation

This is NOT a benchmark paper, an evaluation system paper, or a model comparison paper. It is a **theory about why AI-generated scientific outputs create systematic trust inflation — and how component-level auditing corrects it.**

The paper's strongest empirical claim: result-level evaluation will systematically overestimate AI reproduction validity (Trust Inflation Rate > 0), and the magnitude is measurable (TIR), mechanistically explainable (B₁-B₄ evidence break types), and correctable (component-level audit → lower TIR).

## Methodology Hardening (v7.1 Improvements)

1. **IO₂ tightened**: "structured documentation without executable code" — IO₂ adds structured semantic information (variable definitions, sample rules) while IO₃ adds executable evidence (original code)
2. **R₃ task-contingent**: Not "all components pass" but "all task-critical components pass" — applicable components vary by task type
3. **TIR as primary metric**: Trust Inflation Rate = P(Human says invalid | Regime says trust) — more intuitive than raw TCE difference
4. **B₂/B₃ safeguards**: Semantic code review distinguishes legitimate constants from target leakage; specification shopping requires paper-proximity selection without theoretical justification
5. **Stratified α targets**: Data Source ≥ 0.75, Sample/Indicator/Model ≥ 0.67, Result ≥ 0.80, Claim ≥ 0.60
6. **Pre-agent selection**: Paper pool finalized and pre-annotated before any agent execution
7. **Tier-based model naming**: Open-weight / Low-cost API / Commercial frontier A/B; specific versions in setup table
8. **P→H mapping**: Theory section states propositions; empirical section derives hypotheses

## Differentiators

| Dimension | Our Work | Closest Competitor |
|-----------|----------|-------------------|
| Theoretical construct | IO → ECRF → TCE causal chain | CORE-Bench: difficulty levels (no theory) |
| Governance metric | Trust Inflation Rate (measurable, decomposable) | No existing benchmark has governance metrics |
| Evidence break mechanisms | B₁-B₄ with detection rules + safeguards | COBA: benchmark flaws (different domain) |
| Human validation | 2-layer, component-stratified α, recall estimation | Most benchmarks: no human validation |

## Risks

| Risk | Mitigation |
|------|------------|
| Theory read as "just a framework" | Explicit constructs (IO, ECRF, TCE) with causal relationships |
| Evidence break cases too few | Stratified sampling by observability variation |
| B₂/B₃ false positives | Semantic code review + justification requirement |
| Single-model-family concern | Frontier robustness subset |
| Low α on Claim component | Transparent reporting, adjudication protocol |
