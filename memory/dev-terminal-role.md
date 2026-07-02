---
name: dev-terminal-role
description: "DEV terminal — this terminal works only in the v8-dev worktree on dev/benchmark-wiki-updates; push dev only, never touch master"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 344d8c16-083b-410f-ad0c-b2a6a5c479f2
---

**Two-terminal setup (2026-07-02, user directive):** this project runs two Claude terminals, each on its own branch, never touching the other's branch.

| Terminal | Working dir | Branch | Owns |
|---|---|---|---|
| **Master terminal** | `/mnt/mydisk/PycharmProjects/ai4sci-metrology` (main repo) | `master` | master — see [[session-start-master]] |
| **This terminal (DEV)** | `/mnt/mydisk/PycharmProjects/ai4sci-metrology/.claude/worktrees/v8-dev` | `dev/benchmark-wiki-updates` | dev only |

**This (DEV) terminal's rules:**
- Work ONLY inside the v8-dev worktree on `dev/benchmark-wiki-updates`.
- Push ONLY to `origin/dev/benchmark-wiki-updates` (non-force; verify no forbidden files first — `.litellm/`, PDFs, GCP keys, `.agents/`, `.claude/skills/`).
- **Do NOT touch `master`** — no merge into master, no push to origin/master, no checkout of master. The master terminal owns it.
- Do NOT delete `dev` or remove the v8-dev worktree.
- Latest dev push: `51e0f6c` on 2026-07-02 (origin/dev in sync). Active line: v8.1 ECRF metrology — M2 done, 6 Study-3 killer cases, next is same-trace R₂ implementation. See [[m2-and-killer-status]].

**Reboot resume (DEV terminal):** open Claude Code with cwd = `/mnt/mydisk/PycharmProjects/ai4sci-metrology/.claude/worktrees/v8-dev` (the worktree dir, NOT the main repo). That puts the session on `dev/benchmark-wiki-updates` directly. The worktree is registered in `.git/worktrees/` and persists across reboot. If missing, recreate: `git worktree add /mnt/mydisk/PycharmProjects/ai4sci-metrology/.claude/worktrees/v8-dev dev/benchmark-wiki-updates`.

**LLM backend (DEV terminal):** Qwen3.6-27B-FP8 vLLM at `http://172.17.65.42:8360/v1` (`.41:8360` hung 2026-07-01). `QWEN3_URL=http://172.17.65.42:8360/v1`. Gemma (.43:8008) + DeepSeek (no key) pending for 2nd/3rd model. External fetches (github/zenodo/arxiv): `All_PROXY=127.0.0.1:7897` works — do NOT use `--noproxy`.

**Do NOT apply `session-start-master` / `git-sync-policy` master-only rules to this terminal** — those are for the master terminal. This terminal is dev-only by design.
