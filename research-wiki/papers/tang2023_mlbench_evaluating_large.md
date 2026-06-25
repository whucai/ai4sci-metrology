---
type: paper
node_id: paper:tang2023_mlbench_evaluating_large
title: "ML-Bench: Evaluating Large Language Models and Agents for Machine Learning Tasks on Repository-Level Code"
authors: ["Xiangru Tang", "Yuliang Liu", "Zefan Cai", "Yanjun Shao", "Junjie Lu", "Yichi Zhang", "Zexuan Deng", "Helan Hu", "Kaikai An", "Ruijun Huang", "Shuzheng Si", "Sheng Chen", "Haozhe Zhao", "Liang Chen", "Yan Wang", "Tianyu Liu", "Zhiwei Jiang", "Baobao Chang", "Yin Fang", "Yujia Qin", "Wangchunshu Zhou", "Yilun Zhao", "Arman Cohan", "Mark Gerstein"]
year: 2023
venue: "arXiv"
external_ids:
  arxiv: "2311.09835"
  doi: null
  s2: null
tags: []
added: 2026-06-24T11:27:14Z
---

# ML-Bench: Evaluating Large Language Models and Agents for Machine Learning Tasks on Repository-Level Code

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

> Despite Large Language Models (LLMs) like GPT-4 achieving impressive results in function-level code generation, they struggle with repository-scale code understanding (e.g., coming up with the right arguments for calling routines), requiring a deeper comprehension of complex file interactions. Also, recently, people have developed LLM agents that attempt to interact with repository code (e.g., compiling and evaluating its execution), prompting the need to evaluate their performance. These gaps have motivated our development of ML-Bench, a benchmark rooted in real-world programming applications that leverage existing code repositories to perform tasks. Addressing the need for LLMs to interpret long code contexts and translate instructions into precise, executable scripts, ML-Bench encompasses annotated 9,641 examples across 18 GitHub repositories, challenging LLMs to accommodate user-specified arguments and documentation intricacies effectively. To evaluate both LLMs and AI agents, two setups are employed: ML-LLM-Bench for assessing LLMs' text-to-code conversion within a predefined deployment environment, and ML-Agent-Bench for testing autonomous agents in an end-to-end task execution within a Linux sandbox environment. Our findings indicate that while GPT-4o leads with a Pass@5 rate surpassing 50%, there remains significant scope for improvement, highlighted by issues such as hallucinated outputs and difficulties with bash script generation. Notably, in the more demanding ML-Agent-Bench, GPT-4o achieves a 76.47% success rate, reflecting the efficacy of iterative action and feedback in complex task resolution. Our code, dataset, and models are available at https://github.com/gersteinlab/ML-bench.

