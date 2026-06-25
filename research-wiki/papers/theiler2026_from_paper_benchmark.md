---
type: paper
node_id: paper:theiler2026_from_paper_benchmark
title: "From paper to benchmark: agentic, framework-based reproduction of under-specified methods in machine health intelligence"
authors: ["Raffael Theiler", "Ludovico Comito", "David Leko", "Leandro Von Krannichfeldt", "Lev Telyatnikov", "Olga Fink"]
year: 2026
venue: "arXiv"
external_ids:
  arxiv: "2605.28371"
  doi: null
  s2: null
tags: []
added: 2026-06-24T11:27:21Z
---

# From paper to benchmark: agentic, framework-based reproduction of under-specified methods in machine health intelligence

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

> Industrial Prognostics and Health Management (PHM) provides a representative case study for a broader challenge in applied machine learning: translating published papers into executable, benchmark-ready implementations. Reproducing under-specified methods in PHM is particularly difficult due to restricted access to industrial datasets, incomplete reporting of preprocessing and evaluation protocols, and implicit design choices (e.g., windowing, target construction, data splits) that critically affect performance. Existing paper-to-code systems generate implementations for individual papers, but these artifacts are often not directly comparable due to inconsistencies in assumptions and evaluation settings. We introduce \emph{agentic, framework-based PHM paper reproduction}, where an agent translates a paper into a shared PHM benchmark framework via a \emph{slot-binding interface}. This interface maps equations and protocol descriptions into structured components (task definitions, dataset adapters, windowing, targets, models, and evaluators), while explicitly recording unresolved assumptions. The resulting implementations are validated against standardized task contracts and evaluation hooks, enabling consistent and comparable benchmarking. We evaluate this approach on 16 PHM papers, comparing framework-enhanced, skill-based and prompt-based agentic reproduction against a recent framework-free paper-reproduction agent. We assess reproduction success, model-based code evaluation, framework binding of paper assumptions, and cross-paper benchmark comparability under standardized protocols. Our results show that coupling agentic generation with a shared framework transforms paper reproduction from isolated code synthesis into executable, assumption-aware, and systematically comparable benchmark implementations.

