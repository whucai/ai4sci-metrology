---
name: git-sync-policy
description: Branch policy + periodic local-commit sync rules + the unpushed GCP key leak
metadata: 
  node_type: memory
  type: project
  originSessionId: 971ee36a-7ba1-46b5-806c-553409f7da0d
---

User directive (updated 2026-06-24): work ONLY on branch `master`; sync ONLY to `master`. Periodically local-commit.

**Sync policy (updated 2026-06-24):**
- Commit locally on `master`. Do NOT auto-push. (Earlier dev/benchmark-wiki-updates work was FF-merged into master.)
- `.gitignore` excludes: `.litellm/` (plaintext API keys), `*.pdf` (large benchmark PDFs, kept local), `.agents/` + `.claude/skills/` (symlinks into ~/下载/Auto-claude-code-research-in-sleep), `psychic-binder-*.json` / `*service_account*.json` / `*-sa.json` (GCP keys).
- Before each commit, verify `git diff --cached --name-only | grep -E '\.litellm/|psychic-binder|\.pdf$|^\.agents/|^\.claude/skills/'` is empty; abort if not.
- A session-only cron (`13,43 * * * *`, id varies per session) does this every ~30 min while idle. It dies when the session ends — recreate if needed.

**⚠️ GCP key (resolved 2026-06-24):** `psychic-binder-498910-v8-72b71230a45e.json` (service account private key) was committed at `ed8a37f` but NEVER pushed to origin (commits were local-only, ahead of origin/master). Ran `git filter-repo --path <key> --invert-paths --force` to strip it from ALL local history. Verified: `git log --all --full-history -- <key>` empty; key file kept locally (untracked, gitignored under `psychic-binder-*.json`); origin re-added; rewritten `master` is still a descendant of `origin/master` (6371449) so a **normal non-force `git push`** works. filter-repo backup lives in `.git/filter-repo/`. Since the key never reached GitHub, rotation is optional (not strictly required for this remote) — but rotate if the local repo was ever shared/clone elsewhere. Original (pre-rewrite) SHAs: master=5ca277b, dev=7664cf6 (these objects may be gc'd).

Related: [[sciscibench-engineering-defenses]]
