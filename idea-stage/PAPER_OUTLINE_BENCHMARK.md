# Paper Outline: LLM Bibliometric Computation Benchmark

**Working Title**: *Can Large Language Models Serve as Reliable Bibliometric Computation Engines? A Multi-Model, Multi-Metric Benchmark*

**Target Venues** (in order): Scientometrics / JASIST / Quantitative Science Studies (QSS)
**Backup**: Scientific Data, PLOS ONE

---

## 1. Abstract (~250 words)

**Background**: LLMs are increasingly used to generate code for scientific data analysis, but their reliability for bibliometric computation — calculations that underpin science policy, research evaluation, and meta-science — has never been systematically evaluated.

**Methods**: We introduce a benchmark of 6 bibliometric metrics (disruption index, novelty, conventionality, citation prediction, team-size effect, field-normalized impact) across 150 focal papers drawn from SciSciNet. Four LLMs (Qwen3-32B, GPT-4o, Claude Sonnet 4, DeepSeek-V3) generate Python code at two information levels: formula-given (tests code translation) and description-only (tests formula inference). We evaluate using two novel metrics: the Reproducibility Effort Index (REI), which weights fix iterations by error severity, and REI-c, which penalizes silent failures — cases where code runs without errors but produces numerically wrong results.

**Results**: [to be filled after multi-model experiments]

**Conclusion**: [to be filled]

---

## 2. Introduction (~800 words)

### 2.1 The Rise of LLM-Generated Scientific Code
- LLMs as coding assistants for scientists (Copilot, Cursor, ChatGPT Code Interpreter)
- Increasing reliance on LLM-generated code for data analysis in scientometrics
- The gap: no one has systematically tested whether LLM-generated bibliometric code is numerically correct

### 2.2 Why Bibliometrics is a Critical Test Case
- Bibliometric indicators (D-index, impact factors, h-index) influence hiring, funding, and policy
- Errors in computation have real-world consequences
- The formulas are mathematically simple but require precise implementation with large-scale citation data
- This makes bibliometrics an ideal domain for testing LLM computational reliability

### 2.3 The Silent Failure Problem
- Prior work on LLM code generation focuses on whether code runs (syntax, runtime errors)
- We identify a more dangerous failure mode: code that runs without errors but produces wrong numbers
- Example: LLM confidently computes D-index = +0.14 when ground truth is −0.76 — a sign error that would reverse a paper's conclusion
- We formalize this as "silent failure" and propose REI-c to detect it

### 2.4 Contributions
1. **First multi-metric, multi-model benchmark** for LLM bibliometric computation (6 metrics × 4 models × 150 papers = 3,600 evaluation points)
2. **Two novel evaluation metrics**: REI (effort-weighted reliability) and REI-c (correctness-aware REI that penalizes silent failures)
3. **Empirical findings on silent failure rates** across models and metric types
4. **Practical guidance** for when LLMs can and cannot be trusted for bibliometric computation

---

## 3. Related Work (~600 words)

### 3.1 LLMs for Code Generation
- Codex, Copilot, StarCoder — benchmarks: HumanEval, MBPP
- These test general programming, not scientific/statistical computation
- Key gap: scientific correctness requires numerical accuracy, not just functional correctness

### 3.2 LLMs for Scientific Computation
- SciReplicate-Bench: 100 NLP tasks, 39% execution accuracy
- Paper2Code: 77% code rated "best" but only for ML papers
- AI Scientist (Sakana): 42% experiment failure rate
- Our work differs: (a) focuses on bibliometric computation specifically, (b) measures numerical correctness not just executability, (c) multi-model comparison

### 3.3 Bibliometric Reproducibility
- SciSciGPT (Shao et al., 2025): multi-agent SciSci automation, did not evaluate code reliability
- SciSciNet (Lin et al., 2023): provides ground truth for our benchmark
- Prior reproducibility studies in scientometrics (Strumia & Torre, 2019) — manual, not AI-driven

### 3.4 Silent Failures in AI Systems
- Overoptimization in RLHF (Gao et al., 2023)
- Hallucination in LLM factuality (Ji et al., 2023)
- Our contribution: identifying and quantifying silent failures in LLM-generated scientific computation

---

## 4. Benchmark Design (~1200 words)

### 4.1 Research Questions

| RQ | Question |
|----|----------|
| RQ1 | How reliably can LLMs compute bibliometric indicators when given the exact formula? |
| RQ2 | How reliably can LLMs infer and implement a bibliometric formula from a natural-language description? |
| RQ3 | How do silent failure rates vary across models and metric types? |
| RQ4 | Does REI-c meaningfully differentiate models beyond simple success rate? |

### 4.2 Metrics Under Test

Six bibliometric indicators with ground truth from SciSciNet:

| # | Metric | Ground Truth Source | Data Required | Difficulty |
|---|--------|---------------------|---------------|------------|
| M1 | Disruption Index (D) | `disruption_score` | paper_citations (subgraph) | Medium |
| M2 | Novelty Score | `novelty_score` | papers table | Easy |
| M3 | Conventionality Score | `conventionality_score` | papers table | Easy |
| M4 | Citation Count Prediction | `citation_count` (cohort mean) | papers table | Easy |
| M5 | Team Size Effect | author_count vs disruption | papers table | Medium |
| M6 | Field-Normalized Citation Impact | citation_count / field mean | papers + paper_fields + fields | Hard |

M1 (Disruption) is the primary metric: it requires non-trivial graph operations (set intersection between citing papers and references) and is the most widely-used disruption indicator in Science of Science.

### 4.3 Information Conditions (Within-Subjects)

Each paper × metric is tested at two levels:

**Condition A — Formula-Given (FG)**:
- LLM receives: exact mathematical formula, variable definitions, step-by-step algorithm, data file paths
- Tests: code translation ability (can the LLM faithfully implement a given specification?)
- This is the baseline — failure here means the LLM cannot reliably code even when told exactly what to do

**Condition B — Description-Only (DO)**:
- LLM receives: metric name, natural-language description of what it measures, data file paths
- Tests: formula inference ability (can the LLM derive the correct computation from a conceptual description?)
- This represents the realistic use case where a scientist says "compute the disruption index for this paper"

### 4.4 Paper Sampling

- N = 150 focal papers from SciSciNet
- Stratified by: disruption score tercile (high/medium/low) × citation count quartile
- Ensures coverage across the full range of paper characteristics
- All papers must have: non-null ground truth for all 6 metrics, ≥5 citations, ≥2 references
- Journal diversity: Nature, Science, PNAS, Management Science, Research Policy, PLOS ONE, Physical Review, plus broad sampling

### 4.5 Models Under Test

| Model | Provider | Size | Access |
|-------|----------|------|--------|
| Qwen3-32B | Alibaba | 32B | Local (vLLM) |
| GPT-4o | OpenAI | ~1.7T (est.) | API |
| Claude Sonnet 4 | Anthropic | ~1.7T (est.) | API |
| DeepSeek-V3 | DeepSeek | 671B MoE | API |

Selection rationale: (a) covers both open-weight and proprietary models, (b) spans 32B → 671B+ parameter range, (c) all models released in 2024-2025, (d) practical relevance — these are the models scientists actually use.

### 4.6 Evaluation Protocol

For each (model, metric, paper, condition) tuple:

```
1. LLM receives prompt → generates Python code
2. Code executed in subprocess sandbox (Python 3.11, pandas, numpy)
3. If execution error → self-correction loop (max 3 attempts):
   - Fix attempt 1: syntax/import errors
   - Fix attempt 2: runtime errors
   - Fix attempt 3: logic simplification
4. Parse output → compare with ground truth
5. Compute REI, REI-c, silent failure flag
```

### 4.7 Evaluation Metrics

**REI (Reproducibility Effort Index)**:
```
REI = Σ(ERROR_WEIGHTS[error_type]) / max(fix_iterations, 1)
```
- Syntax error: weight 1
- Import error: weight 2
- Runtime error: weight 3
- Timeout: weight 5
- REI = 0: first-attempt success (gold standard)
- REI = 100: failed after all fix attempts

**REI-c (Correctness-Aware REI)**:
```
REI-c = REI + correctness_ratio × 10
correctness_ratio = |computed - ground_truth| / max(|ground_truth|, ε)
```
- Penalizes silent failures proportionally to numerical error
- REI-c ≈ REI when results are correct
- REI-c ≫ REI when code runs but outputs are wrong

**Silent Failure**:
- Defined as: REI ≤ 0.5 (code ran without meaningful errors) AND correctness_ratio > 0.1 (output is wrong by >10%)
- The most dangerous failure mode: everything looks fine, but the numbers are wrong

---

## 5. Results (~2000 words)

### 5.1 Formula-Given: Code Translation Reliability (RQ1)

| Model | Success Rate | Mean REI | Mean REI-c | Silent Failure Rate |
|-------|-------------|----------|------------|---------------------|
| GPT-4o | [TBD] | [TBD] | [TBD] | [TBD] |
| Claude Sonnet 4 | [TBD] | [TBD] | [TBD] | [TBD] |
| DeepSeek-V3 | [TBD] | [TBD] | [TBD] | [TBD] |
| Qwen3-32B | 98% | 0.03 | 0.04 | 2% |

*[Preliminary Qwen3-32B data from 150-paper benchmark]*

**Key analysis**:
- Per-metric breakdown
- Error type distribution
- Fix iteration distribution
- Paper characteristic effects (does D-index magnitude predict failure?)

### 5.2 Description-Only: Formula Inference (RQ2)

*[This is where we expect dramatic differences between models]*

**Key analysis**:
- Which models can infer formulas from descriptions?
- Per-metric comparison — which metrics are hardest to infer?
- Case studies: examples where LLMs invented plausible-but-wrong formulas

### 5.3 Silent Failure Analysis (RQ3)

**Key finding to test**: Do stronger models (GPT-4o, Claude) have lower silent failure rates than weaker models (Qwen3-32B)?

**Breakdown**:
- Silent failure rate by model × metric × condition
- Distribution of correctness_ratio for silent failures
- The "confidence" problem: all models produce syntactically valid code regardless of correctness
- Why silent failures matter: they would pass automated CI/CD but produce wrong science

### 5.4 REI-c Discrimination (RQ4)

**Key analysis**:
- Does REI-c separate models better than binary success/failure?
- ROC analysis: can REI-c detect silent failures?
- Threshold calibration: what REI-c value corresponds to "trustworthy"?

### 5.5 Cost-Efficiency Analysis

| Model | Cost per 100 papers | Success Rate | Silent Failure Rate |
|-------|---------------------|-------------|---------------------|
| Qwen3-32B | $0 (local) | [TBD] | [TBD] |
| GPT-4o | ~$X | [TBD] | [TBD] |
| Claude | ~$X | [TBD] | [TBD] |
| DeepSeek-V3 | ~$X | [TBD] | [TBD] |

---

## 6. Discussion (~800 words)

### 6.1 When Can We Trust LLMs for Bibliometrics?
- Formula-given: yes, for strong models (98%+ correct)
- Description-only: [TBD based on results — likely no for Qwen3, maybe yes for GPT-4/Claude]
- Recommendation: always provide the formula; never trust description-only code without verification

### 6.2 The Silent Failure Problem is Real
- Binary success/failure misses the most dangerous failure mode
- REI-c should be adopted as standard evaluation for LLM scientific computation
- Implications for AI-assisted systematic reviews, meta-analyses, and evidence synthesis

### 6.3 Implications for SciSci Automation
- SciSciGPT-style multi-agent systems need ground-truth validation at every computation step
- The "Evaluation Agent" in SciSciGPT must check numerical correctness, not just execution success
- Our REI-c framework provides a principled way to implement this

### 6.4 Limitations
- Bibliometric computation is just one domain; generalizability to other scientific computation TBD
- Ground truth from SciSciNet may itself contain errors (but impact is symmetric across models)
- Only D-index uses raw citation graph; other metrics use pre-computed scores
- Self-correction limited to 3 attempts with simple strategies
- Prompt engineering effects: results sensitive to prompt wording

---

## 7. Conclusion (~300 words)

- First systematic benchmark of LLM reliability for bibliometric computation
- REI/REI-c provide principled evaluation beyond binary success/failure
- [Key result to be filled after experiments]
- Practical recommendation: [TBD]
- Code, data, and benchmark released as open-source package

---

## 8. References (projected ~30-40 refs)

Key references to cite:
1. Wu, Wang & Evans (2019). Large teams develop and small teams disrupt science and technology. *Nature*.
2. Shao et al. (2025). SciSciGPT: Advancing human-AI collaboration in the science of science. *Nature Computational Science*.
3. Lin et al. (2023). SciSciNet: A large-scale open data lake for the science of science research. *Scientific Data*.
4. Park, Leahey & Funk (2023). Papers and patents are becoming less disruptive over time. *Nature*.
5. Wang, Song & Barabási (2013). Quantifying long-term scientific impact. *Science*.
6. Chen et al. (2024). Self-Debugging: Teaching LLMs to debug their own code. *ICLR*.
7. Madaan et al. (2023). Self-Refine: Iterative refinement with self-feedback. *NeurIPS*.
8. Yang et al. (2024). SWE-Agent: Agent-computer interfaces for autonomous software engineering.
9. Belz et al. (2025). ReproNLP Shared Task on reproducibility. *ACL/GEM*.
10. Siddiq et al. (2025). Reproducibility crisis in LLMs for SE. *arXiv*.

---

## Appendix A: Prompt Templates

[Include FG and DO prompts for each metric]

## Appendix B: Per-Model Detailed Results

[Full result tables]

## Appendix C: Case Studies of Silent Failures

[3-5 annotated examples showing LLM code that runs but produces wrong results]

---

## 实验工作量估算

| 任务 | 估计时间 |
|------|---------|
| 重写 metric_templates（5 个新指标 prompt） | 1 天 |
| 跑 Qwen3-32B 全量（150 papers × 6 metrics × 2 conditions = 1800 runs） | ~6 GPU-hours |
| 跑 GPT-4o（API） | 1 天 + ~$50 API |
| 跑 Claude Sonnet 4（API） | 1 天 + ~$50 API |
| 跑 DeepSeek-V3（API） | 1 天 + ~$10 API |
| 结果分析 + 图表 | 1 天 |
| 撰写初稿 | 3-4 天 |

**总计**: 约 2 周可完成实验 + 撰写
