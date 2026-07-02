---
name: scientometrics-pivot-v8
description: v8 pivot of evidence-chain idea from UTD to Scientometrics venue; lives on worktree branch
metadata: 
  node_type: memory
  type: project
  originSessionId: 971ee36a-7ba1-46b5-806c-553409f7da0d
---

On 2026-06-24/25 the evidence-chain idea was pivoted from the UTD/IS-governance framing (v7, see [[evidence-chain-theory-v7.2]]) to a **Scientometrics** (Springer) submission framing (v8). Work was done in an isolated git worktree on branch **`worktree-scientometrics-pivot`** (created from origin/master) to avoid interfering with master/dev. NOT yet merged — merge explicitly when ready.

**Key reframing:**
- AI agent repositioned as a **measurement instrument** (not a governance tool). Core construct: **ECRF** (Evidence-Chain Reconstruction Fidelity) — execution-level reproducibility, component-resolved.
- Metric renames: TCE→**RIB** (Result-Indicator Bias); TIR→**FRR** (False Reproduction Rate); B₁–B₄→**M₁–M₄** measurement failure modes.
- New **Study 4 / Block 7 / claim C3**: correlate agent-measured ECRF with scientometric impact indicators (citations, CD-disruption index, altmetrics, team size) — the field-facing capstone; hypothesis the field could not previously test (IV didn't exist).
- Positioning: extends SciSci measurement tradition one level deeper (from impact/disruptiveness to reproducibility of individual findings). Mirrors how the CD-index entered the field.

**Novelty (verified, 59 papers ingested into research-wiki):** no prior work combines (a) agent reproduces a published computational paper + (b) evidence-chain-component fidelity metric + (c) reproduction-as-measurement-instrument. Closest: Theiler 2026 (a, PHM domain-locked), SRI/Hossain 2025 (b, notebook-only no agent), Kapoor 2022 (c, human audit).

**Deliverables on the branch (commit c074cf0):** `idea-stage/IDEA_REPORT.md` (v8), `refine-logs/FINAL_PROPOSAL.md` (v8), `refine-logs/EXPERIMENT_PLAN.md` (v8 + Block 7 + M6 run-order row), +28 research-wiki paper pages + 3 edges + pivot log. UTD v7 recoverable from git history.

**Next:** external /research-review on v8 (does Study 4 land for a Scientometrics reviewer?); then merge `worktree-scientometrics-pivot` → master when approved. Remember the master-protection policy ([[git-sync-policy]]) — do not push until ready.

Related: [[evidence-chain-theory-v7.2]], [[git-sync-policy]], [[sciscibench-engineering-defenses]]
