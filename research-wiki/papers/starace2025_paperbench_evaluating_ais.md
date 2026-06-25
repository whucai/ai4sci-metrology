---
type: paper
node_id: paper:starace2025_paperbench_evaluating_ais
title: "PaperBench: Evaluating AI's Ability to Replicate AI Research"
authors: ["Giulio Starace", "Oliver Jaffe", "Dane Sherburn", "James Aung", "Jun Shern Chan", "Leon Maksin", "Rachel Dias", "Evan Mays", "Benjamin Kinsella", "Wyatt Thompson", "Johannes Heidecke", "Amelia Glaese", "Tejal Patwardhan"]
year: 2025
venue: "arXiv"
external_ids:
  arxiv: "2504.01848"
  doi: null
  s2: null
tags: []
added: 2026-06-24T11:27:15Z
---

# PaperBench: Evaluating AI's Ability to Replicate AI Research

## One-line thesis
_TODO: fill in after reading._

## Problem / Gap
_TODO._

## Method
_TODO._

## Key Results
_TODO._

## Assumptions
_TODO._

## Limitations / Failure Modes
_TODO._

## Reusable Ingredients
_TODO._

## Open Questions
_TODO._

## Claims
_TODO._

## Connections
_Edges are recorded in `graph/edges.jsonl`; summarize here for human readers._

## Relevance to This Project
_TODO._

## Abstract (original)

> We introduce PaperBench, a benchmark evaluating the ability of AI agents to replicate state-of-the-art AI research. Agents must replicate 20 ICML 2024 Spotlight and Oral papers from scratch, including understanding paper contributions, developing a codebase, and successfully executing experiments. For objective evaluation, we develop rubrics that hierarchically decompose each replication task into smaller sub-tasks with clear grading criteria. In total, PaperBench contains 8,316 individually gradable tasks. Rubrics are co-developed with the author(s) of each ICML paper for accuracy and realism. To enable scalable evaluation, we also develop an LLM-based judge to automatically grade replication attempts against rubrics, and assess our judge's performance by creating a separate benchmark for judges. We evaluate several frontier models on PaperBench, finding that the best-performing tested agent, Claude 3.5 Sonnet (New) with open-source scaffolding, achieves an average replication score of 21.0%. Finally, we recruit top ML PhDs to attempt a subset of PaperBench, finding that models do not yet outperform the human baseline. We open-source our code (https://github.com/openai/preparedness) to facilitate future research in understanding the AI engineering capabilities of AI agents.

