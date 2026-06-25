---
name: benchmark-redesign-20260605
description: "Benchmark redesign: 4-stage paper reproduction chain framework, Phase 1 in progress"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9903a3c4-14b9-47c8-a1da-1ed79da95e06
---

Redesigning the AI metrology benchmark from 3 fragmented scripts into a unified 4-stage paper reproduction chain framework.

**Why**: Current benchmark has 3 problems: (1) conceptual confusion between "implement formula" vs "reproduce paper", (2) ~40% code duplication across 3 independent scripts, (3) only Stages 2 and 4 implemented.

**How to apply**: New package at `src/ai_metrology_benchmark/` reuses (imports) existing stable modules from `src/sciscigpt_local/` — sandbox, metric_templates, rei_metric, sciscinet_connector, llm_backends. Do not copy or modify those modules.

**Architecture**:
- Stage 1 (Design): Abstract+Intro → LLM proposes methods → judge vs actual Methods
- Stage 2 (Reproduce): Methods → code generation → sandbox execute → REI-c
- Stage 3 (Derive): Results → LLM derives conclusions → judge vs actual Conclusion
- Stage 4 (Judge): Claims + Results → LLM judges evidence support
- Two conditions: Oracle (paper text input) vs Chain (previous stage output)

**Current progress** (2026-06-05): Phase 1 — creating package structure, types, config, paper registry, section splitter.
