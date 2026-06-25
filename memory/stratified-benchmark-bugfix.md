---
name: stratified-benchmark-bugfix
description: Error detection false positive bug in stratified benchmark — fixed 2026-06-03
metadata: 
  node_type: memory
  type: project
  originSessionId: 2f5492dc-7caa-46f5-9938-057f01c1db8f
---

Three related bugs were causing L2/L3 benchmark to show 0% success rate (all correct code was misclassified as FAILED):

1. `has_error = any(p in stderr for p in ["Error:", ...])` — the `"Error:"` substring matches benign pandas warnings/info messages. Fix: use `exit_code != 0 or "Traceback (most recent call last)" in stderr` instead.
2. `parse_metric_output` regex `D_INDEX\s*=\s*` too strict — LLM outputs `Disruption Index (D): 1.0`. Fix: support multiple patterns per key in METRIC_CONFIGS.
3. L2/L3 prompts didn't specify required output format. Fix: added metric-specific output format to prompts.

**Why:** All three must be fixed for the benchmark to produce meaningful results. Error detection #1 alone doesn't solve it — the parser (#2) and prompt (#3) must also align.

**How to apply:** When writing subprocess-based benchmarks, never substring-match stderr for error detection. Only check exit_code and actual tracebacks. Always specify exact output format in prompts and handle multiple output formats in parsers.

Affected files:
- `scripts/run_stratified_benchmark.py` (lines 322-365)
- `scripts/run_e2e_benchmark.py` (lines 359-393)
- `scripts/run_benchmark.py` (lines 130-140)
- `src/sciscigpt_local/metric_templates.py` (METRIC_CONFIGS, parse_metric_output)
