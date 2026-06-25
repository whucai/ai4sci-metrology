---
name: m1-full-benchmark-20260618
description: "M1 10-paper full benchmark — initial run + context window fix, Gemma 8192 limit required prompt truncation"
metadata: 
  node_type: memory
  type: project
  originSessionId: 658a3b5e-2866-4be8-ae3e-bd2ca5c8c86d
---

M1 10-paper full benchmark built and run with Gemma-4-26B-A4B-it. Pipeline: gold annotation → LLM extraction → dimension scoring → M1 analysis (4 tests).

**Why**: Extend M1 framework validation from 3 pilot papers to 10 papers spanning SciSciPaper annotations and raw .md files.

**How to apply**:
- `python scripts/m1_full_benchmark.py --model gemma` for full 10-paper run
- `--papers 1-3` for pilot-only, `--papers 5,8` for specific papers

**Initial run results (2026-06-18)**:
- 8/10 papers succeeded; 2 failed with context window overflow (park2023, deng2023)
- Root cause: Gemma max 8192 tokens; 15000-char prompt (~4097 tokens) + 4096 max_tokens = 8193 > 8192
- Fix: reduce truncation to 10000 chars, reduce max_tokens to 3072
- After fix: 10/10 papers successful
- Pilot papers (1-3): fidelity 0.72-0.77, maturity L1-L2 — consistent with smoke test
- Group B papers (4-10): fidelity 0.20-0.44 — lower because full text extraction is harder than structured annotations
- Model component consistently weak (spec_elements mismatch); claim component also weak for Group B
- executability=1.0 and auditability>0.5 across all papers (extraction-only, no code execution)
- M1 tests: all PASS (correlation, failure diversity, spurious)
- Maturity distribution: L0(2), L1(2), L1(ds)(1), L1(m)(2), L2(2), L3(m)(1)

**Key bugs fixed**: Gemma 8192-token context window overflow — 15000-char prompts (~4097 tokens) + 4096 max_tokens exceeded limit. Fixed by truncating to 10000 chars and reducing max_tokens to 3072.
