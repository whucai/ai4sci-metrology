---
name: parallel-worktree-setup
description: "Two AI sessions share this repo via git worktrees — Cursor on master (main dir), Claude on dev (v8-dev worktree); sync by merge"
metadata: 
  node_type: memory
  type: project
  originSessionId: 344d8c16-083b-410f-ad0c-b2a6a5c479f2
---

As of 2026-06-29 this repo is worked by **two concurrent AI sessions** to avoid checkout/working-tree races:

| Session | Working directory | Branch | Owns |
|---------|-------------------|--------|------|
| Cursor (other) | `/mnt/mydisk/PycharmProjects/ai4sci-metrology` (main) | `master` | R110/R120/R121 paper-pool + gold-chain work; commits to master |
| Claude (this session) | `/mnt/mydisk/PycharmProjects/ai4sci-metrology/.claude/worktrees/v8-dev` | `dev/benchmark-wiki-updates` | v8.1 idea/ECRF theory, novelty, Study design, wiki |

**Why worktrees:** previously both sessions shared one working tree + HEAD; one session's `git checkout`/`git add -A` clobbered the other's (the "打架" — Cursor's auto-commit-to-master cron kept switching HEAD off dev and staging the other's edits). `git worktree` gives each session its own working tree + HEAD on a different branch while sharing `.git`; no more races.

**Sync protocol:**
- Claude pulls Cursor's latest: from v8-dev worktree, `git merge master` (fast, same .git).
- Cursor pulls Claude's latest: from main dir, `git merge dev/benchmark-wiki-updates`.
- Conflicts only at merge time on same-file-same-line — normal git collaboration, not a race.
- `.claude/worktrees/` is gitignored, so worktrees don't pollute the main repo's status.

**History note:** dev was FF'd to master tip `15e3aab` (R120 verification + R121 gold v1 draft, 19/20 not frozen) on 2026-06-29, so dev carries my v8.1 work + Cursor's R110/R120/R121 work. master and dev share history; divergence begins from the respective sessions' new commits.

**Do NOT** go back to running two sessions in the main working directory — that reintroduces the race. If only one session is needed, `git worktree remove .claude/worktrees/v8-dev` and work in the main dir.

Related: [[git-sync-policy]], [[factreview-closest-prior-art]], [[scientometrics-pivot-v8]]
