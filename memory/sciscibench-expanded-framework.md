---
name: sciscibench-expanded-framework
description: "User's proposal for expanding SciSciBench from 2 tasks to a full 7-stage process chain with 8 experiment types to map capability boundaries"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6e327f22-c932-4570-baea-d48ce8c7b424
---

The user proposed expanding SciSciBench to systematically answer "where the capability boundary lies" for AutoResearch agents, rather than just "can they reproduce experiments."

## 7-Stage Process Chain (currently have S4=Task1, S5=Task2)
S1: Research question understanding — vague idea → testable hypotheses
S2: Data understanding — data description → sample/variable/cleaning plan
S3: Metric construction — idea + fields → variable definitions
S4: Experiment design — idea + data → model + robustness (Task 1)
S5: Result interpretation — result tables → claims (Task 2)
S6: Limitation recognition — full experiment + results → limitations
S7: Design improvement — original design + limitations → improved design

## 5 Information Conditions (C0-C5 progressive disclosure)
C0: vague idea only → C1: +data source → C2: +field schema → C3: +variable hints → C4: +experiment hints → C5: +result tables

## Scaffold Dependence Index
SDI = Performance(scaffolded) - Performance(autonomous)
Measures how much agent depends on human research scaffolding.

## 3 Agent Roles
Autonomous (independent researcher), Scaffolded (research assistant), Constrained (result interpreter), Oracle (text summarizer)

## Failure Taxonomy (11 types)
Data Misunderstanding, Metric Misdefinition, Sample Boundary Error, Confounder Omission, Model Mismatch, Robustness Superficiality, Direction Error, Significance Overclaim, Mechanism Hallucination, Limitation Blindness, Novelty Overstatement

## 5 Calibration Metrics
Calibration Error, Unsupported High-confidence Claim Rate, Abstention Accuracy, Evidence Citation Accuracy

**Why:** To elevate the paper from "benchmark for reconstruction" to "mapping capability boundaries of AutoResearch agents in the scientific knowledge production chain."

**How to apply:** Implement experiments 1-5 progressively; start with minimum viable enhancement (Progressive Disclosure C0-C4, SDI, Failure Taxonomy on 20 papers).
