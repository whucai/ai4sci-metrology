---
type: paper
node_id: paper:wang2026_firebench_evaluating_agents
title: "FIRE-Bench: Evaluating Agents on the Rediscovery of Scientific Insights"
authors: ["Zhen Wang", "Fan Bai", "Zhongyan Luo", "Jinyan Su", "Kaiser Sun", "Xinle Yu", "Jieyuan Liu", "Kun Zhou", "Claire Cardie", "Mark Dredze", "Eric P. Xing", "Zhiting Hu"]
year: 2026
venue: "arXiv"
external_ids:
  arxiv: "2602.02905"
  doi: null
  s2: null
tags: ["benchmark", "scientific-discovery", "agent-evaluation", "reproducibility"]
added: 2026-06-11T09:45:59Z
---

# FIRE-Bench: Evaluating Agents on the Rediscovery of Scientific Insights

## One-line thesis
AI agents autonomously rediscover established scientific findings — even strongest models show limited success (<50 F1), revealing a clear 'science gap' in experimental design and reasoning.

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

> Autonomous agents powered by large language models (LLMs) promise to accelerate scientific discovery end-to-end, but rigorously evaluating their capacity for verifiable discovery remains a central challenge. Existing benchmarks face a trade-off: they either heavily rely on LLM-as-judge evaluations of automatically generated research outputs or optimize convenient yet isolated performance metrics that provide coarse proxies for scientific insight. To address this gap, we introduce FIRE-Bench (Full-cycle Insight Rediscovery Evaluation), a benchmark that evaluates agents through the rediscovery of established findings from recent, high-impact machine learning research. Agents are given only a high-level research question extracted from a published, verified study and must autonomously explore ideas, design experiments, implement code, execute their plans, and derive conclusions supported by empirical evidence. We evaluate a range of state-of-the-art agents with frontier LLMs backbones like gpt-5 on FIRE-Bench. Our results show that full-cycle scientific research remains challenging for current agent systems: even the strongest agents achieve limited rediscovery success (<50 F1), exhibit high variance across runs, and display recurring failure modes in experimental design, execution, and evidence-based reasoning. FIRE-Bench provides a rigorous and diagnostic framework for measuring progress toward reliable agent-driven scientific discovery.

