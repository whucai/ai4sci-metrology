---
name: benchmark-results-20260612
description: "Full 118-paper SciSciBench Task 1+2 benchmark with gold registry: Task 1 F1=0.435, Task 2 score=0.654 with Qwen3-32B"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7cf4ce5a-8f17-49f6-b135-0f9238bfef6a
---

# Benchmark Results 2026-06-12

Full gold registry benchmark: 118 papers × 575 tasks (Task 1: blind+obfuscated × 115, Task 2: L1/L2/L3 × 115).

**Why**: First full-scale SciSciBench run with 115 LLM-extracted gold annotations + 3 manual pilot papers. Validates the annotation pipeline and establishes baseline performance.

**How to apply**: These are baseline scores. Future runs should compare against these numbers. Blind vs obfuscated gap (+0.245) is a key diagnostic metric for Task 1 difficulty.

## Task 1: Experiment Design Reconstruction
- 230/230 success (100%)
- Overall F1: mean=0.435, min=0.000, max=0.685
- Blind: mean=0.313 (n=115)
- Obfuscated: mean=0.558 (n=115)
- Obfuscated > Blind by +0.245 — structured variable info helps more than natural language

## Task 2: Conclusion Inference  
- 344/345 success (99.7%), 1 failure (mir2026_forsaking/L1)
- Overall: mean=0.654, min=0.330, max=0.900
- L1: mean=0.643 (n=114)
- L2: mean=0.677 (n=115)
- L3: mean=0.643 (n=115)
- Scores cluster around 0.64-0.68 — limited differentiation between levels

## Data
- Results saved to: refine-logs/sciscibench_task1_concurrent_20260612_134206.json
- Results saved to: refine-logs/sciscibench_task2_concurrent_20260612_134206.json
