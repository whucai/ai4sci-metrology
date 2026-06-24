# Research Brief: Auditing Scientific Knowledge with Generative AI

**Date**: 2026-06-24 (v4 — UTD strategic reframing)
**Direction**: A Task-Component Framework for Reproducible Computational Research
**Target Venue**: UTD journals — Information Systems Research / Management Science / Organization Science

## Paper Title (candidates)

1. **Auditing Scientific Knowledge with Generative AI: A Task-Component Framework for Reproducible Computational Research** (IS-leaning)
2. **When Can AI Agents Reliably Reproduce Computational Studies? Evidence from a Task-Component Benchmark of Scientific Reproducibility** (Management Science-leaning)
3. **Can Generative AI Reproduce Computational Research? A Task-Component Theory of AI Reproducibility Governance** (theory-leaning)

## Core Research Questions

- **RQ1**: Under what information conditions can generative AI agents reproduce computational research faithfully?
- **RQ2**: Which components of the research evidence chain create the greatest bottlenecks for AI-based reproduction?
- **RQ3**: Can an audit-oriented evaluation framework detect spurious reproductions that would otherwise appear successful?

## Single Contribution Chain

This paper proposes a **task-component theory of AI reproduction quality**; validates it through multi-paper, multi-model, multi-condition experiments that map the capability boundaries of generative AI in computational research reproduction; and demonstrates that **result-level success metrics systematically overestimate reproduction quality** — while **component-level auditing identifies spurious reproduction** and traces failures to specific evidence-chain components.

## Theoretical Framework: Task—Component—Governance Model

### Layer 1: Task Type
AI reproduction is not a single task but a family of tasks:
- **Exact reproduction under identical data conditions** (formerly STRICT)
- **Robustness reproduction under substitute data** (formerly DATA-SUB)
- **Procedural reproduction without numerical targets** (formerly METHOD)
- **Claim robustness under external data conditions** (formerly CLAIM-ROBUST)

### Layer 2: Evidence Chain Components
> A computational paper is not reproduced by matching a final number alone; it is reproduced by reconstructing the evidence chain that links data, operationalization, model estimation, numerical results, and substantive claims.

Data Source → Sample → Indicator → Model → Result Table → Claim

### Layer 3: Auditability (Governance)
Maturity levels operationalize different degrees of **organizational trust** in AI-generated reproduction outputs:
- L0 Failure
- L1 Executable Attempt
- L2 Partial Reproduction
- L3 Numerically Verified Reproduction
- L4 Claim-Consistent Reproduction
- L5 Auditable Reproduction

## Five Testable Hypotheses

- **H1 (Information Condition Effect)**: AI reproduction fidelity increases with information completeness, but marginal gain is larger for upstream components (data, sample) than downstream claims.
- **H2 (Component Bottleneck)**: Errors in sample construction, indicator operationalization, and model specification mediate the relationship between information condition and final result accuracy.
- **H3 (Spurious Reproduction)**: Result-level evaluation overestimates AI reproduction quality relative to component-level audit evaluation.
- **H4 (Task Complexity Moderation)**: The performance gap between AI agents is larger for high-ambiguity reproduction tasks than for strict numerical reproduction tasks.
- **H5 (Audit Framework Value)**: An audit-oriented evaluation protocol reduces false-positive reproduction success by identifying spurious agreement.

## How Line A (SciSciBench) Fits

Downgraded from core contribution to **motivating evidence**: "Before evaluating AI agents as executable reproducers, we conducted a diagnostic benchmark showing that conclusion inference under partial evidence remains unreliable (L3 true capability ~0.3-0.5). This motivates the need for an audit-oriented reproduction framework rather than relying on unverified LLM scientific reasoning."

## Required Experimental Scale

Minimum for UTD submission:
- 30 papers (Group A: Science of Science, Group B: IS/Innovation, Group C: Management/Strategy)
- × 3 information conditions (C1: Abstract+methods, C2: Full paper, C3: Full paper + data/code)
- × 3-4 models (Qwen3-32B, DeepSeek-V3, GPT-4o, Claude Opus 4)
- × 2 independent runs
- ≈ 720 agent-paper-condition runs (minimum: 20 × 3 × 3 = 180)

## Paper Structure

1. Introduction — GenAI in research workflows, reproduction as knowledge governance
2. Theory — AI agents as knowledge-work infrastructure, reproduction as evidence-chain reconstruction
3. Framework — 4 task types, 6 evidence-chain components, 5 evaluation dimensions, L0-L5 maturity
4. Empirical Design — paper sample, models, information conditions, human validation
5. Results — overall fidelity, information condition effects, component bottlenecks, spurious detection, model comparison
6. Discussion — contributions to IS/AI governance/knowledge work, practical implications
7. Conclusion

## Existing Evidence (pre-pilot)

- M0: 6 papers, 3 STRICT D3=100%, 1 DATA-SUB, 1 METHOD, 1 COMPONENT_DIAGNOSIS
- M1: 10-paper framework validation (all 4 tests PASS)
- SciSciBench: 115 papers, L2=0.907 (only discriminating level)
- L3 DeepSeek: overall=0.298, direction commit rate=23.4%, honest weakness acknowledgment
- Error localization proven: R003 (Arts2021) localized formula bug to lines 233-236

## Constraints

- Compute: local 1×4090 GPU
- Data: public (SciSciNet, OpenAlex, other open scholarly metadata)
- Models: Qwen3-32B (local), DeepSeek-V3 (API), GPT-4o/Claude (API, ~$200)
- Human annotation: needs 2-3 domain experts for gold validation (~30 papers)
