---
name: l3-scoring-protocol-revision-20260624
description: "L3 scoring protocol revised 2026-06-24 — direction calibration matrix, graded claim support, rebalanced weights, with rationale for write-up/rebuttal"
metadata: 
  node_type: memory
  type: project
  originSessionId: 658a3b5e-2866-4be8-ae3e-bd2ca5c8c86d
---

L3 scoring protocol was revised because the previous implementation produced a ceiling effect in claim support (1.000 for all 211 papers) and treated cautious "unknown" predictions as fully incorrect in directional inference (0.00, same as wrong answers).

**Why**: The old binary scoring (evidence not in ("none", "weak", "") → 1.0) was trivially saturated. Every L3 conclusion with any missing_evidence text got full credit. Additionally, 77% of Qwen3 predictions were "unknown" under partial evidence, getting 0 credit despite being the scientifically appropriate response.

**How to apply**: All three fixes are in `src/sciscibench/eval/task2_evaluator.py` `evaluate_l3()`. The commits are d3790b1 (scoring fixes), 81cb217 (diagnostic fields), 1529c6f (documentation).

**Three fixes implemented**:

1. **Direction calibration matrix** — partial credit for appropriate uncertainty:
   - Exact match (positive→positive): 1.0
   - Tentative correct (positive→tentative_positive): 0.75
   - Avoidance (positive→unknown): 0.25
   - Reversal (positive→negative): 0.0
   - Null correctly identified (null→unknown): 1.0

2. **Graded claim support** — replaces binary evidence check:
   - strong=1.0, moderate=0.6, weak=0.3

3. **Rebalanced weights** — new formula:
   - 0.25×dir + 0.25×css + 0.15×specificity + 0.15×limitation + 0.10×anchor_rate + 0.10×(1-halluc)
   - Removed uncertainty_recognition from aggregate, added evidence anchoring and limitation awareness

**Diagnostic fields added** per conclusion: gold_direction, pred_direction, direction_score, support_strength, support_strength_score, has_evidence_anchor, direction_commit_rate, direction_correct_when_committed.

**Protocol rationale for write-up**: "The L3 scoring protocol was revised because the previous implementation produced a ceiling effect in claim support and treated cautious 'unknown' predictions as fully incorrect in directional inference. The revised protocol introduces partial credit for uncertainty-aware direction predictions, graded evidence support, and a rebalanced overall score."

**Related files**:
- `refine-logs/BENCHMARK_SUMMARY_20260618.md` — full write-up with before/after tables
- `research-wiki/log.md` — protocol revision entry (2026-06-24)
- `scripts/rescore_task2_l3.py` — re-scoring existing results
- `scripts/ablate_l3_scoring.py` — ablation analysis
