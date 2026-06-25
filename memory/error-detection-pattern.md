---
name: error-detection-pattern
description: Never use substring matching on stderr for error detection in subprocess-based benchmarks
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2f5492dc-7caa-46f5-9938-057f01c1db8f
---

Never use `any(p in stderr for p in ["Error:", "Exception", ...])` to detect errors in subprocess output. 

**Why:** Pandas and other libraries emit warnings/info to stderr that contain these substrings. `"Error:"` matches `FutureWarning: ... error ...` and similar benign messages. This causes all correct code executions to be misclassified as failures, and the self-correction loop rewrites already-correct code into broken code.

**How to apply:** Only check `exit_code != 0` and `"Traceback (most recent call last)" in stderr`. If exit_code is 0, try parsing stdout first — if the expected output is found, it's a success regardless of what stderr contains.
