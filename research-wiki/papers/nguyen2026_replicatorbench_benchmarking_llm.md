---
type: paper
node_id: paper:nguyen2026_replicatorbench_benchmarking_llm
title: "ReplicatorBench: Benchmarking LLM Agents for Replicability in Social and Behavioral Sciences"
authors: ["Bang Nguyen", "Dominik Soós", "Qian Ma", "Rochana R. Obadage", "Zack Ranjan", "Sai Koneru", "Anna Szabelska", "Adam Gill", "Timothy M. Errington", "Shakhlo Nematova", "Sarah Rajtmajer", "Jian Wu", "Meng Jiang"]
year: 2026
venue: "arXiv"
external_ids:
  arxiv: "2602.11354"
  doi: null
  s2: null
tags: ["benchmark", "replicability", "social-sciences", "agent-evaluation"]
added: 2026-06-11T09:46:04Z
---

# ReplicatorBench: Benchmarking LLM Agents for Replicability in Social and Behavioral Sciences

## One-line thesis
End-to-end benchmark for replication in social/behavioral sciences — tests both replicable and non-replicable claims across extraction, execution, and interpretation stages; data retrieval is primary bottleneck.

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

> The literature has witnessed an emerging interest in AI agents for automated assessment of scientific papers. Existing benchmarks focus primarily on the computational aspect of this task, testing agents' ability to reproduce or replicate research outcomes when having access to the code and data. This setting, while foundational, (1) fails to capture the inconsistent availability of new data for replication as opposed to reproduction, and (2) lacks ground-truth diversity by focusing only on reproducible papers, thereby failing to evaluate an agent's ability to identify non-replicable research. Furthermore, most benchmarks only evaluate outcomes rather than the replication process. In response, we introduce ReplicatorBench, an end-to-end benchmark, including human-verified replicable and non-replicable research claims in social and behavioral sciences for evaluating AI agents in research replication across three stages: (1) extraction and retrieval of replication data; (2) design and execution of computational experiments; and (3) interpretation of results, allowing a test of AI agents' capability to mimic the activities of human replicators in real world. To set a baseline of AI agents' capability, we develop ReplicatorAgent, an agentic framework equipped with necessary tools, like web search and iterative interaction with sandboxed environments, to accomplish tasks in ReplicatorBench. We evaluate ReplicatorAgent across four underlying large language models (LLMs), as well as different design choices of programming language and levels of code access. Our findings reveal that while current LLM agents are capable of effectively designing and executing computational experiments, they struggle with retrieving resources, such as new data, necessary to replicate a claim. All code and data are publicly available at https://github.com/CenterForOpenScience/llm-benchmarking.

