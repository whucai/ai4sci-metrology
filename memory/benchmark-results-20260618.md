---
name: benchmark-results-20260618
description: Full 211-paper SciSciBench Task 2 run with 3 critical fixes
metadata: 
  node_type: memory
  type: project
  originSessionId: f22359d1-f185-4ab6-9878-0644c41c2b8d
---

Full SciSciBench Task 2 benchmark: 211 papers × 3 levels = 633 tasks with Qwen3-32B, all passed.

**Results**: L1=0.597, L2=0.907, L3=0.689, overall=0.731

**3 fixes applied 2026-06-18**:
1. L3 prompt: force at least 1 tentative conclusion (was returning empty arrays for 60% of papers)
2. L3 scoring: zero uncertainty credit for empty blanket abstention
3. L1 JSON: fix invalid backslash escapes from code blocks

**Before/after**: L3 improved from 0.349→0.689. L3 empty responses eliminated (30/50→0/50).

**Why**: The L3 prompt's uncertainty language ("be honest, don't fabricate") triggered Qwen3 to abstain entirely. Combined prompt+scoring fix resolved this.

**Next**: Audit low-direction L3 cases, test cross-model, resolve remaining L1 JSON issues.

**Relevant files**: refine-logs/sciscibench_task2_concurrent_20260618_111833_fixed.json, refine-logs/BENCHMARK_SUMMARY_20260618.md
