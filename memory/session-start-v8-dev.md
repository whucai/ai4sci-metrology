---
name: session-start-master
description: "At session start in ai4sci-metrology, STAY on master — do not enter any worktree (2026-06-29 directive)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 344d8c16-083b-4150-ad0c-b2a6a5c479f2
---

**At session start** in the ai4sci-metrology project, **STAY on `master`** in the main repo dir `/mnt/mydisk/PycharmProjects/ai4sci-metrology`. Do **NOT** enter the v8-dev worktree and do **NOT** switch to `dev/benchmark-wiki-updates` — that earlier instruction (pre-2026-06-29) is superseded by the user's "保持主分支 且只在主分支工作" directive. Just resume on master.

(The v8-dev worktree at `.claude/worktrees/v8-dev` may still exist on disk from the old parallel-Cursor setup; ignore it unless the user explicitly asks to enter a worktree. The Scientometrics-pivot worktree is also intentionally unmerged — see [[scientometrics-pivot-v8]].)

**LLM backend (LiteLLM proxy `http://127.0.0.1:4000/v1`, key `sk-local-litellm`):** routes `qwen3-32b` (local vLLM — try `172.17.65.42:8360`, .41:8360 hung 2026-07-01), `deepseek-v4-pro` (Anthropic-compatible API), `glm-5.2` (Aliyun MaaS), `gemma-4-31b` (.43:8008). Settings: ANTHROPIC_BASE_URL=127.0.0.1:4000, SONNET=glm-5.2, HAIKU=deepseek-v4-pro. Start proxy: `nohup litellm --config .litellm/config.yaml --port 4000`.

**Proxy for external fetches** (github/zenodo/arxiv/semantic-scholar): `All_PROXY=127.0.0.1:7897` works — do NOT use `--noproxy`. Semantic Scholar API rate-limits hard (429) — prefer Crossref + Unpaywall + Europe PMC for OA paper recovery.

Related: [[git-sync-policy]], [[study2-euc-mechanism-2026-07-02]], [[codex-image2-mcp-wiring]]
