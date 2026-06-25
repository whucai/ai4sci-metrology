---
type: paper
node_id: paper:yue2026_factreview_execution_claim_verification
title: "FactReview: Evidence-grounded peer review with execution-based claim verification"
authors: ["Ling Yue", "Chaoqian Ouyang", "Hang Xu", "Ruijun Huang", "Yuchen Liu", "Libin Zheng", "Wei Liu", "Shaowu Pan", "Shimin Di", "Min-Ling Zhang"]
year: 2026
venue: "arXiv"
external_ids:
  arxiv: "2604.04074"
  doi: "10.48550/arXiv.2604.04074"
  s2: null
tags: ["claim-verification", "code-execution", "peer-review", "LLM-reviewer", "evidence-grounded"]
added: 2026-06-25T08:16:44Z
---

# FactReview: Evidence-grounded peer review with execution-based claim verification

## One-line thesis
A reviewing system that extracts claims from a manuscript, grounds them in related work, and — when code is available — executes released artifacts under a fixed repair budget (K=3, wrapper-only) to audit empirical claims; explicitly avoids accept/reject decisions and shows removing execution evidence changes 17% of claim verdicts.

## Problem / Gap
LLM-based reviewers take only the manuscript as input, leaving literature-based and code-based claims unverifiable. Existing automated review makes accept/reject decisions without grounding claims in executable evidence. No prior system combines manuscript analysis + literature grounding + code execution at the claim level.

## Method
- **Input**: manuscript PDF (+ optional released repo) → MinerU parses to section-aware blocks, tables, equations, captions, citation anchors, page locations. Semantic Scholar retrieves related work; RefCopilot verifies bibliography against arXiv/S2/OpenReview/OpenAlex.
- **Claim extraction**: schema-constrained LLM extractor → typed records (claim text, type, scope, source span, linked manuscript evidence, evidence targets). Multi-scope claims decomposed into subclaims. **Claim types**: empirical / methodological / theoretical. Inclusion: claim must affect novelty, validity, contribution, reproducibility, or scope.
- **Three evidence sources**: (a) manuscript evidence (MinerU blocks); (b) literature evidence (comparison set from cited methods, named baselines, semantically similar papers; structured comparison table, not a generic novelty score); (c) **execution evidence**.
- **Execution (Run-Review-Fix loop)**: align repo with paper → derive candidate tasks from README/configs/entry scripts → run in Linux Docker under time/resource budgets → judge compares observed outputs vs claims/reported numbers. **Fixed repair budget K=3**, restricted to wrapper-level fixes (env | deps | path | encoding | data | runtime | other); explicitly does NOT change model architectures, loss, datasets, evaluation logic, or baselines. Verdicts: pass / fail / inconclusive (if execution succeeds but outputs can't be aligned to a claim → inconclusive, not forced).
- **Claim status (4 labels)**: Supported / Partially-supported / In-conflict / Inconclusive. Provenance (which source) tracked separately.
- **Eval rubric (1–5)**: Groundedness / Specificity / Coverage / Overall.

## Key Results
- **35 ML papers, 463 benchmark major claims** (13.23/paper). Label dist: 38.4% Supported, 56.4% Partial, 0.6% In-conflict, 4.5% Inconclusive.
- FactReview extracts 435 claims (12.43/paper), **84.4% coverage**. Its dist: 149 Supported / 250 Partial / 4 In-conflict / 32 Inconclusive.
- **Quality**: FactReview 4.86/5 overall vs DeepReview-v2 4.17 vs GPT-5.4 3.63 vs human OpenReview 3.33. Groundedness 4.97, Specificity 4.94.
- **Execution**: paper success 55.0%→65.0% after 2 repair rounds; claim pass 67.7%→82.3%. RRF overhead 2.30 attempts, 1.45× runtime, 1.58× tokens. Claude Opus 4.6 83.3% exec success vs GPT-5.4 75.0%.
- **17% ablation (Table 3)**: removing execution changes 17.0% of claim statuses — largest single-source effect. Removing literature 5.7%, removing S2 retrieval 8.4%, manuscript-only changes 26.1%.
- **Reviewer-assistance**: paper-only 50.6 min/86.9% coverage → +report 31.6 min (−37.5%)/97.8% → +teaser 21.3 min (−57.9%)/98.9%. Coverage 87%→99%.
- Cost: 357K tokens, 773s/paper (~$0.5–0.7).

## Assumptions
- Empirical ML papers with released code; theoretical/dataset/systems papers need different taxonomies.
- Wrapper-level repair suffices (won't touch model/loss/data/eval logic) — so it audits whether released code runs and matches claims, not whether the experimental logic is valid.
- Camera-ready manuscript + released repo are the unit of review.
- A claim is "Supported" if released-code output aligns with the reported number (within tolerance).

## Limitations / Failure Modes
- **Binary code availability** — no IO variable; cannot manipulate narrative vs structured-docs vs executable.
- **Claim-level only** — no Data→Sample→Indicator→Model→Result→Claim component decomposition; no per-component fidelity.
- **No trust-inflation measurement** — "Partial" flags overbroad scope but doesn't quantify the result-vs-component validity gap.
- **No scientometric link** — no correlation of verdicts with citations, CD-index, team size, venue.
- **Observational ablation** — removes sources post-hoc; not a causal manipulation of observability.
- **B₁-invisible by construction** — agent executes the *released* repo, never chooses data/sample, so cannot detect data/sample substitution (the agent isn't reconstructing from the paper, it's running given code).
- 0.6% In-conflict — rarely tested on detecting false claims.
- 35 papers, single detailed case study (CompGCN); small reviewer pool.
- Pipeline failures (env/runtime/metric/alignment) are not structural evidence-chain breaks.

## Reusable Ingredients
- Claim-extraction schema (empirical/methodological/theoretical, with scope + source span + evidence targets) — directly reusable for ECRF's claim→component decomposition.
- 4-status verdict taxonomy + provenance tracking — ECRF's R₂ (claim-level audit) baseline.
- Run-Review-Fix loop with bounded wrapper repair (K=3, fix categories) — reusable for IO₃ execution cell.
- Evidence-aware rubric (Groundedness/Specificity/Coverage) — reusable for human-adjudication layer.
- 35-paper/463-claim benchmark — candidate shared eval set.

## Open Questions
- On the same 35 papers, how often would FactReview's "Supported" verdicts disagree with a component-level audit (B₁/B₂ cases)? (This is ECRF's killer experiment.)
- Does IO level (narrative vs structured-docs vs executable) change claim verdicts more than FactReview's binary code-on/off? (Causal vs observational.)
- Can claim-level verdicts be decomposed into per-component fidelity scores that predict trust inflation?

## Claims
- Execution-based evidence changes claim assessments more than any other single source (17%).
- LLM reviewers should audit empirical claims, not make accept/reject decisions.
- Bounded wrapper repair (K=3) is cost-effective (recovers 2/9 failed papers, 1.58× tokens).
- Evidence-aware rubric achieves 4.86/5, beating DeepReview-v2 and human OpenReview comments.

## Connections
_Edges recorded in `graph/edges.jsonl`._

## Relevance to This Project
**Closest prior work — high novelty threat, but also the strongest baseline to fold in.** FactReview does (a) agent executes paper code + (partial b) claim-level verification — partially breaching the v8 novelty claim ("no prior work combines agent-reproduces-paper + evidence-chain-component-fidelity + reproduction-as-measurement-instrument"). The defensible ECRF novelty against FactReview rests on FOUR structural moves FactReview cannot make: **D1** unit of analysis = evidence-chain component (not claim); **D2** IO as a 3-level causal treatment (not binary code availability + post-hoc ablation); **D3** trust inflation as primary DV (result-vs-component gap — FactReview has no concept of this); **D4** scientometric correlation (Study 4 — FactReview has none). Plus B₁–B₄ structural break taxonomy vs FactReview's pipeline failures. 

**Strongest repositioning:** make FactReview the R₂ baseline in Study 3 (claim-level execution audit). Hypothesis H4 becomes TIR(R₂=FactReview-style) > TIR(R₃=component) — even execution-based claim audit inflates trust relative to component audit. The 17% ablation *supports* the ECRF premise (evidence regime changes conclusions); ECRF generalizes it from binary code-on/off to a 3-level causal IO ladder with component-resolved effects. FactReview is structurally blind to B₁ (agent never chooses data) — exactly where ECRF's killer cases live.
