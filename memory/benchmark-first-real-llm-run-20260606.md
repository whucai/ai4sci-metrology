---
name: benchmark-first-real-llm-run-20260606
description: "First end-to-end Stage 2+4 benchmark run with real Qwen3-32B — 24 tasks, 95.8% success, REI-c mean=1.59"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9903a3c4-14b9-47c8-a1da-1ed79da95e06
---

First successful end-to-end benchmark run with real LLM (Qwen3-32B) on 2026-06-06.

**Why**: Validates the unified benchmark runner after fixing two critical bugs (model_name override + cites_path for dataset metrics).

**Results**: 3 test papers × 8 methodology papers = 24 tasks
- Stage 2: 23/24 success (95.8%), 4 silent failures (17.4%), REI-c mean=1.59 median=0.0
- Stage 4: 24/24 parsed (100%), judgments: 43 NOT TESTABLE, 16 SUPPORTED, 9 PARTIALLY, 1 NOT SUPPORTED
- Stage 2 time: 473.5s (19.7s/task), Stage 4 time: 77.4s
- 1 failure: nature_2023_disruption with test paper 1968388660 (runtime errors exhausted 4 fix attempts)

**Bugs fixed before this run**:
1. `create_llm()` in run_benchmark.py: `llm.model_name = model_name` overrode ChatOpenAI's API model path, sending "qwen3-32b" to API instead of the real model path.
2. `run_with_execution()` only generated `cites_path` for PER_PAPER_METRICS, but `disruption_temporal` and `citation_inflation` (DATASET_METRICS) also need it in their prompt templates.

**Output**: `refine-logs/benchmark_20260606_172006.json`
