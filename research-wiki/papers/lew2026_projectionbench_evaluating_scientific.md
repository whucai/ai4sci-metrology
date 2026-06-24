---
type: paper
node_id: paper:lew2026_projectionbench_evaluating_scientific
title: "ProjectionBench: Evaluating Scientific Hypothesis Generation in LLMs Under Progressive Information Disclosure"
authors: ["A. J. Lew", "Y. Cao", "M. J. Buehler"]
year: 2026
venue: "arXiv"
external_ids:
  arxiv: "2605.30284"
  doi: null
  s2: null
tags: ["benchmark", "hypothesis-generation", "LLM-evaluation", "scientific-discovery"]
added: 2026-06-11T09:46:00Z
---

# ProjectionBench: Evaluating Scientific Hypothesis Generation in LLMs Under Progressive Information Disclosure

## One-line thesis
LLM hypothesis generation evaluated under progressive information disclosure — GPT-5.4 maintains 0.7 F1 alignment with ground truth even under minimal context, testing both innovativeness and grounded reasoning.

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

> Scientific discovery is an inherently creative and uncertain process, requiring reasoning beyond the recall of known knowledge. While many benchmarks have been proposed to evaluate large language model (LLM) performance on deep research tasks via multi-hop retrieval, their innovative reasoning abilities essential for true scientific discovery remain largely untested. We introduce a benchmark framework for evaluating model performance in scientific discovery and reasoning, building up from a raw problem to the classical null hypothesis test. In our framework, models initially receive only the topic and research question from a recent paper, with technical details progressively revealed. At each stage of information disclosure, the model is tasked with generating hypotheses that address the research question, which is compared with the conclusions from the original paper and evaluated via automated semantic similarity of constituent atomic claims. This progressive evaluation of semantic divergence from ground-truth conclusions enables assessment of a model's innovativeness (under minimal information) to grounded reasoning capabilities (under full experimental details), both critical for using LLMs for scientific discovery purposes. Our framework provides a foundation for systematically evaluating scientific reasoning and discovery capabilities in LLMs, crucial for advancing the development of next-generation AI scientist/co-scientist systems. Specifically, here we evaluate GPT-5, GPT-5.4, Gemini 2.5 pro, and Gemini 3.1 pro preview across 45 papers spanning bioactive materials, mechanical materials, and nanomaterials. We find that GPT-5.4 and Gemini 3.1 pro outperform their previous generation counterparts as expected, and GPT-5.4 in particular maintains 0.7 F1 score alignment with ground truth conclusions even under minimal context.

