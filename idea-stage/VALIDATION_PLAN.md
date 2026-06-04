# Step 1 + Step 2 Validation Plan

**Date**: 2026-06-01
**Core Goal**: Validate the auto paper reproduction pipeline and SciSci SDK

---

## Experiment Design Overview

```
Experiment 1: SciSciGPT Architecture Reproduction
  ├── E1a: Multi-agent graph smoke test (M0 — done)
  ├── E1b: Single-specialist task execution with real LLM (M1 — done)
  └── E1c: Full paper reproduction pipeline (M2)

Experiment 2: SciSci SDK Core Functions
  ├── E2a: disruption_index() validation against known values
  ├── E2b: cem_match() correctness on benchmark dataset
  └── E2c: SDK usability — agent task completion rate with SDK vs raw code

Experiment 3: Self-Correction Loop & REI
  ├── E3a: Fix iteration count on 3 papers of varying difficulty
  └── E3b: REI correlation with ground truth reproducibility
```

---

## Experiment 1: SciSciGPT Architecture Reproduction

### E1a: Multi-Agent Graph Smoke Test (M0) ✓

**Status**: COMPLETED
**Result**: Full agent cycle (RM → Specialist → Tool → Evaluation → RM → END) works.

### E1b: Single-Specialist Task Execution (M1) ✓

**Status**: COMPLETED (MockLLM), PENDING (Real LLM)
**Result**: Python sandbox executes correctly. Agent graph routes through all nodes with MockLLM.

**Metric**: >70% task completion rate with real LLM (pending API key)

### E1c: Full Paper Reproduction Pipeline (M2)

**Goal**: Feed SciSciGPT paper PDF to the system, reproduce one analysis.

**Tasks**:
- Extract method section from SciSciGPT paper (Grobid/PyMuPDF + LLM)
- Identify dataset references (SciSciNet, OpenAlex)
- Execute reproduced analysis in sandbox
- Compare output with paper's reported figures

**Metrics**:
- Method extraction accuracy (human-verified)
- Analysis reproduction fidelity (Δ from reported values)
- REI (Reproducibility Effort Index) = fix iterations needed

**Criteria**: At least 1 analysis step reproduces with <20% deviation

---

## Experiment 2: SciSci SDK Core Functions

### E2a: disruption_index() Validation

**Goal**: Validate SDK's D-index computation against Wu et al. (2019) known values.

**Dataset**: Wu et al. 2019 replication dataset (Web of Science subset)
- 5 papers with known D-index values
- Compare: our SDK vs reference implementation

**Metric**: Spearman ρ > 0.95 with reference values

### E2b: cem_match() Correctness

**Goal**: Validate CEM matching on SciSciNet sample.

**Test**: Match 100 papers by journal × year × type. Compare with manual matching.
**Metric**: Match rate >95%, balance check p > 0.1

### E2c: SDK Usability

**Goal**: Measure whether Agent + SDK outperforms Agent + raw code.

**Task**: "Compute D-index for paper X and identify top 5 disruptors in field Y"
**Comparison**:
- Agent with SDK: `sci.disruption_index(doi)` — expected ~1 call
- Agent without SDK: raw pandas/networkx code — expected ~50+ lines, high failure rate

**Metric**: Task completion rate, code lines generated, execution errors

---

## Experiment 3: Self-Correction Loop & REI

### E3a: Fix Iterations by Paper Difficulty

**Papers**:
| Difficulty | Paper | Expected Issues |
|-----------|-------|----------------|
| Easy | Wu et al. (2019) | Standard dependencies, well-documented |
| Medium | SciSciGPT (2025) | Multiple languages (Python/R/Julia), GCP deps |
| Hard | TBD custom paper | Missing data, ambiguous methods |

**Metric**: REI = Σ(fix iterations per step) / (successful steps)
**Hypothesis**: REI(easy) < REI(medium) < REI(hard)

### E3b: REI Validation

**Goal**: Correlate REI with ground truth reproducibility.
**Method**: Run on ReproNLP Shared Task papers (known reproducibility outcomes).
**Metric**: REI rank-correlation with human reproducibility labels. Spearman ρ > 0.6.

---

## Run Order

```
E1a (smoke test) → E1b (real LLM) → E2a (D-index) → E1c (paper repro)
    → E2b (CEM) → E2c (SDK usability) → E3a (REI) → E3b (REI validation)
```
