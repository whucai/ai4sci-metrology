---
name: sciscibench-agent-ablations
description: "User's design for comparing agent settings (not models) — LLM-only → structured prompt → code-agent → AutoResearch agent → evidence-checked agent, to diagnose which automation components matter"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6e327f22-c932-4570-baea-d48ce8c7b424
---

Rather than benchmarking many different AutoResearch systems or base models, the paper should compare agent **settings** along the research automation spectrum:

## Agent Settings (S0-S5)
S0: LLM-only — bare prompt, no tools, no structure
S1: Structured LLM — fixed template (1. Define variables, 2. Specify sample, 3. Choose model, 4. Add controls, 5. Robustness, 6. Conclusions)
S2: Code-agent — planning + code execution + data inspection
S3: Research-agent (AutoResearch loop) — planning + design + execute + reflect + revise + conclude
S4: Evidence-checked agent — S3 + evidence cross-checker (reduces hallucinated claims)
S5: Oracle scaffold — full human scaffolding + high info disclosure

## Core Ablation Questions
- Does planning help?
- Does code execution reduce errors?
- Does self-reflection improve conclusions?
- Does evidence checking reduce hallucinated conclusions?
- How much does high-scaffold condition boost performance?
- How much does agent degrade without human scaffolding?

## Comparison Logic
Compare same base model (Qwen3-32B) across different automation settings. Optionally add 1-2 other models (GPT, Claude) for robustness. Optionally small-sample human baseline (2-3 grad students, 5 papers).

## Key Narrative
"We do not rank existing AutoResearch systems. We compare different degrees of research autonomy and scaffolding to diagnose where AutoResearch agents succeed or fail in the scientific production chain."

**Why:** The paper's contribution is mapping capability boundaries, not leaderboard-style model comparison. Ablation across agent settings provides mechanistic explanation.

**How to apply:** Implement S0-S4 as configurable agent settings in the benchmark runner. S0-S1 use Task1Runner/Task2Runner directly. S2-S4 add tool use/reflection loops.
