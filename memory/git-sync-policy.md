---
name: git-sync-policy
description: Branch policy — MASTER only (2026-06-29 directive) + commit/secrets rules
metadata:
  node_type: memory
  type: project
  originSessionId: 971ee36a-7ba1-46b5-806c-553409f7da0d
---

**User directive (updated 2026-06-29, supersedes all earlier): work ONLY on `master`.** Do NOT use `dev/benchmark-wiki-updates` and do NOT enter any worktree for this project's main line of work. Next session loads on `master` — the repo is on master; just resume there. (Earlier 2026-06-25 directive said dev-only; superseded 2026-06-29 by the user's explicit "保持主分支 且只在主分支工作".)

**Sync policy:**
- Commit locally on `master`. Periodic local commits; no auto-push unless asked.
- `.gitignore` excludes: `.litellm/` (plaintext API keys — an Aliyun MaaS glm-5.2 key was pasted into .litellm/config.yaml on 2026-07-01; confirmed gitignored, never committed), `*.pdf`, `.agents/` + `.claude/skills/` (symlinks into ~/下载/Auto-claude-code-research-in-sleep), `psychic-binder-*.json` / `*service_account*.json` / `*-sa.json` (GCP keys).
- Before each commit, verify `git diff --cached --name-only | grep -E '\.litellm/|psychic-binder|\.pdf$|^\.agents/|^\.claude/skills/'` is empty; abort if not.

**⚠️ GCP key (resolved 2026-06-24):** `psychic-binder-498910-v8-72b71230a45e.json` was committed at `ed8a37f` but NEVER pushed. Stripped from all local history via `git filter-repo --invert-paths`. Normal non-force `git push` works (rewritten master descends from origin/master 6371449). Rotate only if the local repo was shared/cloned elsewhere.

Related: [[sciscibench-engineering-defenses]], [[study2-euc-mechanism-2026-07-02]]
