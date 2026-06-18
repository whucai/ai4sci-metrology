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

## Bottom Line

The benchmark fix is effective. The corrected Task 2 run produces a coherent level ordering: **L2 strongest**, **L3 meaningfully harder but no longer collapsed by abstention**, and **L1 limited by sparse evidence and residual parsing issues**. The overall score is **0.731**, with the most important improvement being the L3 recovery from **0.349 to 0.689**.
