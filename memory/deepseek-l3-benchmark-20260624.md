---
name: deepseek-l3-benchmark-20260624
description: "First L3 re-run with DeepSeek V4 Pro + new scoring protocol — 211 papers, overall=0.298, support_strength 100% weak, direction commit 23.4%"
metadata: 
  node_type: memory
  type: project
  originSessionId: 658a3b5e-2866-4be8-ae3e-bd2ca5c8c86d
---

DeepSeek V4 Pro L3 benchmark re-run (2026-06-24) with new scoring protocol. 211/211 papers, 0 failures, 1072s.

**Why**: Needed exact claim_support_score values after the scoring protocol revision. Qwen3-32B vLLM server was down, switched to DeepSeek API.

**How to apply**: Set `ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`. The benchmark runner auto-detects DeepSeek vs Qwen. Run: `python scripts/run_sciscibench_concurrent.py --task task2 --levels L3 --output-dir refine-logs/l3_exact_rerun_20260624 --workers 5`.

**Results**: `refine-logs/l3_exact_rerun_20260624/sciscibench_task2_concurrent_20260624_112630.json`

**Key metrics**:
- Overall: 0.298 (min 0.065, max 0.550)
- Direction accuracy (calibrated): 0.325
- Claim support (graded): 0.300
- Direction commit rate: 23.4% (102/211 papers commit to non-"unknown")
- Direction correct when committed: 63.6%

**Critical finding — support_strength 100% "weak"**: DeepSeek reports "weak" for ALL 583 conclusions. This is the opposite of Qwen3 which reported 100% "moderate" (inflating CSS to 1.0). Under old binary scoring, DeepSeek's CSS would be 0.000 (all "weak" filtered out). The graded scoring recovers CSS to 0.300.

**Cross-model comparison**:
| Metric | Qwen3 (old scoring) | DeepSeek (old scoring) | DeepSeek (new scoring) |
|---|---|---|---|
| Direction | 0.176 | 0.171 | 0.325 |
| Claim Support | 1.000 (ceiling) | 0.000 | 0.300 |
| Overall | 0.689 (inflated) | 0.390 | 0.298 |

**Ablation (DeepSeek, same predictions, different scoring)**:
| Setting | L3_Dir | L3_CSS | L3_Overall |
|---|---|---|---|
| Original | 0.171 | 0.000 | 0.390 |
| + Direction partial | 0.325 | 0.000 | 0.418 |
| + Graded support | 0.325 | 0.300 | 0.485 |
| Full revised | 0.325 | 0.300 | 0.298 |

**Score distribution**: 0.00-0.15: 36, 0.15-0.30: 58, 0.30-0.45: 105, 0.45-0.55: 12.

**Interpretation**: The 0.298 is a "floor" estimate. DeepSeek is honest about weak evidence. Qwen3's 0.689 was inflated by the CSS ceiling. True model capability for L3 is likely 0.3-0.5 range. Next step: improve prompt to encourage the model to use a range of support_strength values (not just "weak").

**Ablation data**: `refine-logs/l3_exact_rerun_20260624/sciscibench_task2_concurrent_20260624_112630_ablation.json`
