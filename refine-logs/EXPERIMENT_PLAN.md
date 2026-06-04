# Experiment Plan: SciSciGPT Reproduction + Containerized AI Reproducibility Pipeline

**Date**: 2026-06-01
**Target Paper**: SciSciGPT (Shao et al., Nature Computational Science 2025)
**GitHub**: https://github.com/Northwestern-CSSI/SciSciGPT
**Goal**: Reproduce SciSciGPT's multi-agent architecture, then build the Step 1 auto-reproduction pipeline on top of it

## Context

SciSciGPT is a 5-agent LangGraph system (ResearchManager, LiteratureSpecialist, DatabaseSpecialist, AnalyticsSpecialist, EvaluationSpecialist) that automates SciSci research. It uses GCP (BigQuery, Vertex AI Claude, Cloud Storage) + Pinecone. We don't have those cloud credentials.

**Strategy**: Extract the core multi-agent framework, adapt to local infrastructure (Qwen3-32B, local DB, local sandbox), verify the architecture works, then layer on the containerized paper reproduction pipeline.

## Infrastructure Mapping

| SciSciGPT (original) | Our replacement |
|----------------------|-----------------|
| Vertex AI Claude 3.5 Sonnet | Qwen3-32B (local 4090) via vLLM or llama.cpp |
| BigQuery + SciSciNet (~11M papers) | Local SQLite/Parquet with SciSciNet subset |
| Pinecone vector DB | FAISS or ChromaDB |
| Google Cloud Storage | Local filesystem |
| Jupyter kernel sandbox | Subprocess + Docker sandbox |
| Frontend (Next.js) | Skip — CLI-first, API server only |

## Experiment Milestones

### M0: Sanity — LangGraph Agent Graph Smoke Test

**Goal**: Verify the SciSciGPT LangGraph state machine runs end-to-end with a dummy LLM and mock tools.

**Tasks**:
- Extract `define_sciscigpt_graph()` and dependent modules into our own `src/` directory
- Eliminate GCP/Pinecone/Redis dependencies; replace with stubs
- Run the graph with a mock LLM that returns canned responses
- Verify: START → ResearchManager → Specialist → Evaluation → END cycle works

**Metric**: State machine completes without errors, reaches END state
**Priority**: MUST-RUN
**Est. GPU-hours**: 0 (mock LLM, no GPU needed)

### M1: Baseline — Single Specialist with Real LLM

**Goal**: Run the AnalyticsSpecialist with Qwen3-32B on a simple analysis task.

**Tasks**:
- Wire Qwen3-32B (via vLLM API or llama.cpp server) as the LLM backend
- Implement a local sandbox executor (Python subprocess, no Docker yet)
- Task: "Load a CSV, compute summary statistics, plot a histogram"
- Compare: mock LLM vs Qwen3-32B on task completion rate
- Measure: code execution success rate, output correctness

**Metric**: >70% task completion rate with Qwen3-32B
**Priority**: MUST-RUN
**Est. GPU-hours**: ~2 (inference only)

### M2: Main — Paper Reproduction Pipeline

**Goal**: Feed the SciSciGPT paper itself to the system and attempt to reproduce one of its described analyses.

**Tasks**:
- Paper ingestion: extract method section, identify datasets, analysis steps, and expected outputs from SciSciGPT paper PDF
- Database preparation: download SciSciNet sample from HuggingFace, load into local DB
- Agent execution: ResearchManager decomposes paper's method → DatabaseSpecialist fetches data → AnalyticsSpecialist runs analysis
- Result comparison: compare agent's output with paper's reported figures/tables
- Produce reproducibility report with Reproducibility Effort Index (REI)

**Sub-experiments**:
| ID | Description | Tool/Reference |
|----|-------------|----------------|
| M2a | Extract method from SciSciGPT PDF | Grobid/PyMuPDF + LLM |
| M2b | Replicate "Large teams develop, small teams disrupt" (Wu et al. 2019) figure | SciSciGPT Case Study 2 |
| M2c | Replicate SciSciGPT's self-evaluation metrics | EvaluationSpecialist prompt |

**Metric**: At least 1 analysis step reproduces with <20% deviation from paper's reported values
**Priority**: MUST-RUN
**Est. GPU-hours**: ~8

### M3: Ablation — Self-Correction Loop + REI

**Goal**: Measure how many fix iterations are needed per paper, validating REI as a metric.

**Tasks**:
- Instrument the pipeline to count: (a) environment fix iterations, (b) code fix iterations, (c) data fix iterations
- Run on 3 papers of varying difficulty (easy: Wu et al. 2019, medium: SciSciGPT, hard: TBD)
- Compute REI = total fix iterations / successful reproduction
- Ablate: with vs without EvaluationSpecialist feedback loop

**Metric**: REI correlates with paper difficulty; EvaluationSpecialist reduces REI
**Priority**: MUST-RUN
**Est. GPU-hours**: ~6

## Success Criteria

| Milestone | Criterion |
|-----------|-----------|
| M0 | Graph state machine completes successfully |
| M1 | >70% task completion with Qwen3-32B |
| M2 | At least 1 analysis step reproduces (Δ <20%) |
| M3 | REI differentiates easy/medium/hard papers |

## Estimated Budget

- Total: ~16 GPU-hours on 1x 4090
- Wall time: ~2 days (parallelizable within milestones)

## Run Order

```
M0 (sanity, 0 GPU-hr) → M1 (baseline, 2 GPU-hr) → M2 (main, 8 GPU-hr) → M3 (ablation, 6 GPU-hr)
```
