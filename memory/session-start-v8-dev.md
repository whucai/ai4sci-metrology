---
name: session-start-v8-dev
description: "At session start in ai4sci-metrology, auto-enter the v8-dev worktree (dev/benchmark-wiki-updates) before any v8.1 work"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 344d8c16-083b-410f-ad0c-b2a6a5c479f2
---

**At session start** in the ai4sci-metrology project (when the working directory is the main repo `/mnt/mydisk/PycharmProjects/ai4sci-metrology`, which is on `master` and used by the parallel Cursor session), **immediately enter the v8-dev worktree** before doing any v8.1 work:

```
EnterWorktree(path="/mnt/mydisk/PycharmProjects/ai4sci-metrology/.claude/worktrees/v8-dev")
```

This switches the session onto branch `dev/benchmark-wiki-updates` in an isolated working tree, so Claude (dev) and Cursor (master, main dir) don't collide on the shared working tree/HEAD. See [[parallel-worktree-setup]] for why.

**If the worktree is missing** (e.g., removed): recreate it —
```
git worktree add /mnt/mydisk/PycharmProjects/ai4sci-metrology/.claude/worktrees/v8-dev dev/benchmark-wiki-updates
```
then EnterWorktree(path=...).

**Do NOT** do v8.1 work in the main repo dir on master — that races with Cursor's commits and causes the "打架" checkout conflicts. The main dir is Cursor's; v8.1 is in the worktree.

After entering, the active line of work is on dev: v8.1 evidence-chain ECRF metrology, M2 runs, Study 3 killer cases. See [[research-review-v8.1-outcome]], [[factreview-closest-prior-art]], [[m2-and-killer-status]].

**LLM backend**: Qwen3.6-27B-FP8 vLLM — use `172.17.65.42:8360` (`.42` is the live one; `.41:8360` hung on 2026-07-01). Set `QWEN3_URL=http://172.17.65.42:8360/v1`. Gemma (.43:8008) and DeepSeek (no key) still pending for the 2nd/3rd model.

**Proxy for external fetches** (github/zenodo/arxiv): `All_PROXY=127.0.0.1:7897` works — do NOT use `--noproxy` (it bypasses a working proxy and fails).
