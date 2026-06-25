---
type: paper
node_id: paper:chen2026_rpcbench_finegrained_comprehension
title: "RPC-Bench: A fine-grained benchmark for research paper comprehension"
authors: ["Yelin Chen", "Fanjin Zhang", "Suping Sun", "Yunhe Pang", "Yuanchun Wang", "Jian Song", "Xiaoyan Li", "Lei Hou", "Shu Zhao", "Jie Tang", "Juanzi Li"]
year: 2026
venue: "arXiv"
external_ids:
  arxiv: "2601.14289"
  doi: "10.48550/arXiv.2601.14289"
  s2: null
tags: ["paper-comprehension", "QA-benchmark", "LLM-as-judge", "review-rebuttal"]
added: 2026-06-25T08:16:44Z
---

# RPC-Bench: A fine-grained benchmark for research paper comprehension

## One-line thesis
A large-scale QA benchmark (15K human-verified pairs) built from review–rebuttal exchanges of CS papers, with a fine-grained taxonomy aligned to the research flow, showing even GPT-5 reaches only 37.46% Informativeness — establishing a comprehension ceiling for foundation models on scholarly text.

## Problem / Gap
Existing paper-understanding benchmarks lack fine-grained, large-scale evaluation. ROUGE-L/BERTScore are unreliable proxies (a model can score high on surface overlap while being wrong). No benchmark systematically tests why/what/how understanding across the full research flow using authentic expert-generated questions.

## Method
- **Source**: 44.7K peer-reviewed papers with review–rebuttal pairs on OpenReview (2013–2024), AMiner-matched for quality, impact-aware sampled to 4,243 papers (3,521 accepted with 50+ citations + 361 highly-cited rejected + 361 random rejected as negatives). Final: 4,150 papers, 61.3K QA pairs (train/val/test 45,651/12,895/2,787). ~15K human-verified (val+test).
- **Taxonomy** (9 categories across 4 dimensions, what→how→why):
  - 1 Concept Understanding (4.27%)
  - 2.1 Method Disambiguation (8.91%, what) / 2.2 Method Mechanics (9.91%, how) / 2.3 Motivation Analysis (6.29%, why) / 2.4 Method Comparison (11.75%)
  - 3.1 Experimental Exposition (13.07%, what) / 3.2 Experimental Setup (6.77%, how) / 3.3 Experimental Analysis (14.08%, why)
  - 4 Claim Verification (24.95%, binary T/F)
- **Annotation pipeline**: GPT-4o decomposes reviews into comment–response pairs; GLM-4-Plus + DeepSeek-V3 rewrite to QA under taxonomy; filter removes unanswerable. 4 annotators (Master's+), 5–6 min/Q, 80/day cap. Kappa 0.72 (annotators) / 0.78 (reviewers); retention 0.81/0.85.
- **Eval (LLM-as-a-Judge)**: 3 dimensions on 0–5 decimal scale — Correctness (precision-like), Completeness (recall-like), Conciseness. F1-like = H(Correctness, Completeness); Informativeness = F1-like × Conciseness / 5. Judge = avg of 2 best of {GPT-5, Claude-4.5, Gemini-3} with title+abstract augmentation; P-BT Pearson 0.9213.

## Key Results
- GPT-5: 68.20% F1-like, **37.46% Informativeness** (after conciseness adjustment).
- Gemini-2.5 33.35%, Claude-4 24.19%, DeepSeek-V3.2 32.04%, GLM-4.7 28.81%, Qwen3 23.31% Informativeness.
- Text→image drops hard: Qwen3 F1-like 56.26%→20.16%; Claude-4 conciseness 41.37%→31.63%.
- Small (~8B) models: 8–18% F1-like. RAG models underperform (retrieval failures + weak reasoning).
- ROUGE-L/BERTScore misleading: Monkey(V) best ROUGE-L (20.16%) + strong BERTScore (55.19%) but correctness 17.08% / completeness 11.27%.
- Fine-tuning Qwen-8B/LLaMA-8B on train set: +11.38%/+10.64% Informativeness, but gains come from conciseness, not correctness/completeness.

## Assumptions
- Camera-ready paper text is ground truth; factual errors in source paper propagate into gold answers.
- Single-paper understanding only (no cross-document reasoning).
- Review–rebuttal exchanges on OpenReview are representative of expert comprehension questions (CS-biased: ML Theory 24.8%, CV 16.87%, NLP 15.17%).

## Limitations / Failure Modes
- **No code execution, no reproduction, no IO manipulation, no component decomposition, no fidelity metric** — comprehension only.
- CS/OpenReview only; non-English venues absent.
- Taxonomy is structurally flat within categories; doesn't test cross-category reasoning chains (method→design→result→interpretation).
- Claim Verification (24.95%) is binary T/F against the paper's own claims, NOT against independently verified ground truth.
- Gold answers authored from the paper, so a model that faithfully repeats a paper's false claim scores full marks.

## Reusable Ingredients
- 15K human-verified QA pairs + 9-category taxonomy (potential eval set for ECRF's comprehension prerequisite).
- LLM-as-a-Judge decimal-scoring protocol with P-BT calibration (reusable for ECRF human-agreement design).
- Impact-aware sampling recipe (cited-accepted + highly-cited-rejected + random-rejected).

## Open Questions
- Does comprehension (RPC-Bench) predict reconstruction fidelity (ECRF)? I.e., is the 37.46% ceiling a *cause* of low ECRF, or do models understand enough but fail at execution?
- Can cross-document reasoning (future RPC-Bench) close the gap to component-level reconstruction?

## Claims
- Fine-grained QA from authentic review–rebuttal is a valid large-scale probe of paper understanding.
- LLM-as-a-Judge with decimal scoring + dimension separation achieves high human agreement (Pearson 0.9213).
- Frontier models have substantial comprehension gaps (GPT-5 < 40% Informativeness).

## Connections
_Edges recorded in `graph/edges.jsonl`._

## Relevance to This Project
**Motivation, not competition.** RPC-Bench establishes the *comprehension ceiling* (GPT-5 37.46% Informativeness) that motivates a reconstruction-level instrument: if models cannot precisely understand papers, claim-level and result-level reproduction verdicts inherit that error — a direct source of trust inflation. RPC-Bench has **no structural overlap with ECRF**: no execution, no IO manipulation, no Data→Sample→Indicator→Model→Result→Claim decomposition, no fidelity metric, no trust-gap measurement. Its Claim Verification category is binary T/F against the paper's own claims, not against independently reconstructed ground truth. Cite as the comprehension baseline ECRF must clear, and as a candidate comprehension covariate in Study 2 (does IO affect comprehension the same way it affects reconstruction?).
