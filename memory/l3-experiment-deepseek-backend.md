---
name: l3-experiment-deepseek-backend
description: L3 prompt experiment switched to DeepSeek API after vLLM server went down
metadata: 
  node_type: memory
  type: project
  originSessionId: f22359d1-f185-4ab6-9878-0644c41c2b8d
---

## Current state (2026-06-24)

Remote vLLM server at 172.17.65.41:8032 is down (HTTP 502). Switched L3 experiment to DeepSeek-v4-pro via Anthropic-compatible API (`ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`).

**Why:** The user asked to try Gemma or DeepSeek instead of vLLM local models. DeepSeek API is already configured in the environment.

**How to apply:** When running LLM experiments, auto-detect backend in `run_l3_experiment.py` (already implemented): if `OPENAI_API_KEY` is set, use OpenAI/vLLM; otherwise fall back to Anthropic/DeepSeek. The `ANTHROPIC_AUTH_TOKEN` env var controls DeepSeek access.

**Implication:** Results from this run are NOT numerically comparable to the Qwen3-32B baseline from 2026-06-18. Within-model comparisons (original vs v2_nofewshot vs v2_fewshot) are valid for measuring prompt effect.
