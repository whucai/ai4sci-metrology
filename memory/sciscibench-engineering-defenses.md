---
name: sciscibench-engineering-defenses
description: "Three critical engineering defenses for SciSciBench: forced JSON output for Task 1, 3-layer contamination defense, dual-track evaluation"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6e327f22-c932-4570-baea-d48ce8c7b424
---

# SciSciBench Engineering Defenses (2026-06-11)

Three critical technical challenges identified during framework design review, each with a concrete engineering defense.

**Why**: User flagged three non-obvious problems that would make SciSciBench unreviewable if unaddressed: (1) free-text experiment design cannot be auto-evaluated, (2) LLM memorization of benchmark papers, (3) the "ground truth" paradox.

**How to apply**: These are design constraints, not optional. Task 1 must use JSON Schema. Every paper must have a contamination suspicion score. Expert-quality evaluation is a 20-case subset, not the primary metric.

## Defense 1: Forced Structured JSON Output (Task 1)

Task 1 output is NOT free text. Agent must produce strict JSON Schema:
- independent_variables, dependent_variables, control_variables (with name/type/definition)
- statistical_method (family + specification)
- network_construction (node_type, edge_type, directed, weighted)
- sample_scope (time_window, fields, filters)
- robustness_checks (method + rationale)

Comparison: Exact Match (binary fields) + Semantic Similarity (cosine > 0.85 on variable definitions) + Set Overlap (F1 on control variables) + Feasibility (sandbox execution check)

## Defense 2: Three-Layer Contamination Defense

Layer 1 (Blind Setting): Remove title, authors, journal, year; paraphrase idea
Layer 2 (Variable Obfuscation): Rename all variables to neutral tokens (X1, X2, Y)
Layer 3 (Logic-Only Extraction): Give only abstract mathematical formalism, no natural language context

Per-paper contamination suspicion score: High (>100 citations, Nature/Science/PNAS), Medium (field journals), Low (post-cutoff or 2025-2026). Report high-risk vs low-risk performance gap transparently.

## Defense 3: Dual-Track Evaluation

Original-Fidelity: Primary automated metric, ALL tasks, JSON field comparison
Expert-Quality: 20-case human blind review subset, pairwise comparison on validity dimensions

Report separately. Never merge into one score.

## Framework Implications

- Task 1 JSON Schema is a hard constraint — agent must output valid JSON or the task is scored 0
- Gold JSON for each paper must be validated by sandbox execution before benchmark release
- 25% hardest subset uses Logic-Only extraction (Layer 3) — this is the most diagnostic split
