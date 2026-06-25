---
name: benchmark-refactor-20260606
description: "Benchmark redesign Phase 1-4 complete — unified package, stages, runner, eval, smoke-tested"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9903a3c4-14b9-47c8-a1da-1ed79da95e06
---

Completed Phases 1-4 of benchmark redesign (2026-06-06). The unified 4-stage framework is built and smoke-tested.

**Why**: Previous 3 benchmark scripts had ~40% code duplication and couldn't test the full reproduction chain from research design to conclusion judgment.

**How to apply**: New package at `src/ai_metrology_benchmark/` with:
- `papers/registry.py` — unified paper+claims registry (8 papers, 24 claims)
- `papers/sections.py` — IMRaD section splitter (regex + numeric fallback, falls back to full text)
- `stages/base.py` — abstract BaseStage with Oracle/Chain prompt building
- `stages/stage2_reproduction.py` — wraps manual_papers_benchmark core logic, supports L1/L2/L3
- `stages/stage4_judgment.py` — wraps stage4_benchmark core logic  
- `eval/judge.py` — LLM-as-judge for Stages 1/3 evaluation
- `eval/analysis.py` — aggregated metrics (by level, model, metric, paper)
- `scripts/run_benchmark.py` — unified CLI runner replacing 3 old scripts

**Smoke test**: 8 papers × 1 test paper × Stage 2 with MockLLM ran end-to-end. Data loading, task dispatch, sandbox execution, self-correction, result saving all work.

**What's left**:
- Stage 1 and Stage 3 implementations (stubs needed)
- Test with real LLM (qwen3-32b or deepseek-v4-pro)
- Human annotations for LLM-as-judge calibration
- [[benchmark-redesign-20260605]] contains the original design plan
