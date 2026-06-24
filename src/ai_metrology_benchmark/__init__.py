"""AI Metrology Benchmark — 4-Stage Paper Reproduction Chain.

Stage 1: Research Design Inference (Intro → proposed methods)
Stage 2: Experiment Reproduction (Methods → code → execute → REI-c)
Stage 3: Conclusion Derivation (Results → scientific conclusions)
Stage 4: Conclusion-Evidence Judgment (Claims + Results → verdict)

Two conditions:
  - Oracle: each stage receives the correct paper text section
  - Chain: each stage receives the previous stage's LLM output
"""

__version__ = "0.1.0"
