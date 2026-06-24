# SciSciBench Task 2 Benchmark Summary

**Date:** 2026-06-18  
**Model:** Qwen3-32B  
**Result file:** sciscibench_task2_concurrent_20260618_111833_fixed.json  
**Tracker:** EXPERIMENT_TRACKER.md

## Experiment Overview

SciSciBench Task 2 evaluates scientific conclusion inference across three information levels. The benchmark tests whether an LLM can infer paper-level conclusions from progressively richer or more complete evidence, while recognizing uncertainty under incomplete evidence.

| Level | Setting | Intended Capability |
|---|---|---|
| L1 | Minimal/abstracted evidence | Basic conclusion inference from sparse information |
| L2 | More complete evidence | High-fidelity conclusion recovery from sufficient results |
| L3 | Partial/incomplete results | Tentative inference with explicit uncertainty recognition |

The 2026-06-18 run evaluated **211 papers x 3 levels = 633 tasks** with Qwen3-32B. All 633 tasks completed with status=success.

## Main Results

| Metric | Score |
|---|---:|
| Total tasks | 633 |
| Papers | 211 |
| L1 average | 0.597 |
| L2 average | 0.907 |
| L3 average | 0.689 |
| Overall average | 0.731 |

| Level | Tasks | Average Score | Notes |
|---|---:|---:|---|
| L1 | 211 | 0.597 | Lower score driven by sparse inputs and two remaining JSON escape parse errors recorded inside successful tasks |
| L2 | 211 | 0.907 | Strongest level; same papers are largely recoverable when evidence is sufficient |
| L3 | 211 | 0.689 | Improved substantially after prompt/scoring fixes; still below L2 as expected for incomplete evidence |

## Fixes Applied

| Fix | Problem Addressed | Effect |
|---|---|---|
| L3 prompt fix | Qwen3 interpreted incomplete-result warnings as a reason to return empty conclusions | Forced at least one tentative conclusion from partial evidence |
| L3 scoring fix | Empty arrays received residual uncertainty credit, making blanket abstention a stable low-score strategy | Removed reward for empty blanket abstention |
| L1 JSON escape fix | Some L1 generations contained invalid JSON escapes | Reduced parser fragility; two successful records still retain escape-related error fields |

## Before/After Comparison

| Version | L3 Score | Change |
|---|---:|---:|
| Before fixes | 0.349 | - |
| After fixes | 0.689 | +0.340 |

The main gain came from eliminating the degenerate L3 behavior where the model returned valid JSON with empty conclusion arrays. The revised setup better matches the scientific target: infer what is supportable, mark uncertainty, and avoid unsupported claims.

## Key Findings

| Finding | Interpretation |
|---|---|
| L2 is high at 0.907 | Qwen3-32B can recover conclusions when evidence is sufficiently complete |
| L3 improved from 0.349 to 0.689 | The original L3 setup confounded uncertainty recognition with abstention |
| L3 remains below L2 | Partial evidence still makes conclusion direction difficult, which is expected |
| L3 uncertainty recognition is high | The fixed prompt preserves uncertainty behavior instead of merely forcing overconfident claims |
| L3 direction accuracy remains low | The next bottleneck is calibrated directional inference under incomplete evidence |
| Hallucination is nonzero in L2/L3 | Prompt pressure to infer conclusions should be monitored against unsupported claim generation |

## Next Steps

| Priority | Step | Purpose |
|---|---|---|
| High | Audit L3 low-direction cases | Separate true ambiguity from scoring/prompt failures |
| High | Manually review L3 hallucinated claims | Ensure the prompt fix did not trade abstention for unsupported inference |
| High | Re-test on another model | Check cross-model robustness beyond Qwen3-32B |
| Medium | Resolve remaining L1 JSON escape cases | Remove parser artifacts from L1 scoring |
| Medium | Calibrate L3 direction scoring | Consider partial credit for justified uncertainty without accepting blanket unknown answers |

## L3 Scoring Fixes (2026-06-24)

Three scoring bugs identified and fixed in `src/sciscibench/eval/task2_evaluator.py`:

| Fix | Problem | Solution | Effect |
|---|---|---|---|
| Direction partial credit | "unknown" predictions got 0.00 same as wrong answers | 0.30 partial credit for "unknown" (justified uncertainty) | L3 dir: 0.176 → 0.383 |
| Graded claim support | Binary evidence check gave 1.0 for ALL 211 L3 papers | Graded by support_strength: strong=1.0, moderate=0.6, weak=0.3 | L3 CSS: 1.000 → ~0.68 (estimated) |
| Rebalanced weights | Uncertainty overweighted vs direction | 0.30 dir + 0.15 sig + 0.25 claim + 0.10 anti-halluc + 0.20 uncert | More balanced signal |

### Rescored Results (estimated — LLM server unavailable for full re-run)

| Metric | Old | New | Delta |
|---|---:|---:|---:|
| L3 Direction Accuracy | 0.176 | 0.383 | +0.207 |
| L3 Claim Support Score | 1.000 | ~0.680 | −0.320 |
| L3 Overall Score | 0.689 | ~0.609 | −0.081 |
| Overall (all levels) | 0.731 | ~0.704 | −0.027 |

**Note**: Claim support score is estimated from available data. The raw `support_strength` values are not stored in the results file. A full re-run with the LLM server is needed for exact claim_support_score values.

### Level Ordering After Fix

L2 (0.907) > L3 (~0.609) ≈ L1 (0.597)

This ordering is coherent: L2 (complete evidence) is the easiest, L3 (partial evidence) is intermediate, L1 (sparse evidence) is the hardest. L3's high uncertainty recognition (0.768) confirms the model appropriately flags uncertainty under incomplete evidence, even as its directional inference remains limited.

### Remaining

| Priority | Step | Purpose |
|---|---|---|
| High | Re-run benchmark with LLM server | Get exact claim_support_score values |
| High | Audit L3 low-direction cases | Separate true ambiguity from scoring failures |
| Medium | Add raw prediction storage to runner | Enable re-scoring without re-running |

## Bottom Line

The benchmark fix is effective. The corrected Task 2 run produces a coherent level ordering: **L2 strongest**, **L3 meaningfully harder but no longer collapsed by abstention**, and **L1 limited by sparse evidence and residual parsing issues**. The overall score is **0.731**. With the L3 scoring fixes applied, the overall score is estimated at **~0.704**, with the most important changes being the direction partial credit (0.176 → 0.383) and the claim_support ceiling fix (1.0 → graded).
