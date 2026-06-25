---
name: llm-backend-switching
description: How to switch between DeepSeek API (Anthropic path) and Qwen3 vLLM (OpenAI path) for benchmarks
metadata: 
  node_type: memory
  type: reference
  originSessionId: 658a3b5e-2866-4be8-ae3e-bd2ca5c8c86d
---

The benchmark runner (`scripts/run_sciscibench_concurrent.py`) auto-detects the LLM backend:

**DeepSeek V4 Pro** (via Anthropic-compatible API):
```bash
export ANTHROPIC_AUTH_TOKEN="sk-..."
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro"
```

**Qwen3-32B** (via vLLM OpenAI-compatible API):
```bash
export OPENAI_API_KEY="not-needed"
export OPENAI_BASE_URL="http://172.17.65.41:8032/v1"
export LLM_MODEL="/public/data_share/model_hub/Qwen3-32B/"
```

**Priority**: `ANTHROPIC_AUTH_TOKEN` > `OPENAI_API_KEY`. If neither is set, falls back to `ANTHROPIC_AUTH_TOKEN` (Anthropic path) which is always set in this environment.

**Key differences**:
- DeepSeek: slower (~30s/task), supports thinking mode, returns list-of-blocks content (handled by `_extract_text()`)
- Qwen3 vLLM: faster (~6s/task), no thinking mode, returns string content

**Implementation**: `scripts/run_sciscibench_concurrent.py:load_llm()` — committed in 7f93aa7.
