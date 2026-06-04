# Human Baseline Protocol for Reproducibility Measurement

**Version**: 1.0  
**Date**: 2026-06-02  
**Status**: Design — not yet executed

## 1. Objective

Measure human REI (Reproducibility Effort Index) as a baseline to calibrate AI-agent
reproducibility metrics. The key question: how much effort do humans need to reproduce
the same computational analyses that AI agents attempt?

Compare human REI distribution against LLM REI distributions from the multi-LLM
benchmark to establish whether AI agents are:
- Below human performance (higher REI)
- At human parity (similar REI)
- Above human performance (lower REI, but potentially more silent failures)

## 2. Paper Selection

N = 10 papers, sampled from the 100-paper AI benchmark results to span
representative difficulty levels:

| Category | N | Criteria | Example REI |
|----------|---|----------|-------------|
| Trivial | 2 | AI REI=0, correct D-index | 0.0 (gold standard) |
| Silent failure | 3 | AI REI=0, wrong D-index | 0.0 (deceptive) |
| Moderate | 3 | AI REI 0-3, successful after fixes | 1.0-3.0 |
| Hard | 2 | AI REI > 3 or failed | 3.0-100.0 |

Papers selected AFTER the 100-paper AI benchmark completes, to enable
matched comparison. Each selected paper must have:
- Paper ID, title, year from SciSciNet
- Ground truth D-index (computed from paper_citations subgraph)
- AI reproduction results (REI, REI-c, code, error log)

## 3. Participant Requirements

- Target: 3-5 graduate students or postdocs in computational/quantitative fields
- Required skills: Python, pandas, basic statistics, reading scientific papers
- Each participant reproduces all 10 papers independently (~3-5 hours total)
- Participants must NOT use LLMs/chatbots for code generation
- Participants MAY use: Stack Overflow, Python documentation, package docs

## 4. Instructions to Participants

```
You are participating in a study on scientific reproducibility.

TASK: For each paper, write Python code to compute a metric from the
paper's description, using provided CSV data files. Your goal is to
produce the correct numerical result.

PROVIDED:
- A short description of the metric and formula
- CSV data files (refs and citations) on disk
- Python environment with pandas, numpy

RULES:
- Record your start time before beginning each paper
- Record every error you encounter and how you fixed it
- You may NOT use AI coding assistants (ChatGPT, Copilot, etc.)
- You MAY use Stack Overflow, documentation, and other reference materials
- Target: working code that prints the correct metric value

WHEN DONE: Submit your code, the output, and your error log.
```

## 5. Measurement Protocol

For each (participant, paper) pair, record:

### Time Metrics
- `time_to_first_run`: Minutes from start to first code execution
- `time_to_correct`: Minutes from start to correct output (or abandonment)
- `total_time`: Total minutes spent (cap at 30 min per paper)

### Error Metrics
- `fix_iterations`: Number of code-fix cycles (analogous to AI fix_iterations)
- `error_types`: Classified using same ERROR_PATTERNS as AI benchmark
  (syntax, import, runtime, timeout, logic)
- `error_log`: Free-text description of each error and fix

### Correctness Metrics
- `computed_D`: D-index value from participant's code output
- `ground_truth_D`: Pre-computed ground truth
- `d_deviation`: Absolute difference
- `is_correct`: Deviation < 0.01 (1% tolerance)

### Subjective Metrics
- `self_reported_difficulty`: 1-10 Likert scale
- `confidence`: 1-5 scale ("How confident are you that your answer is correct?")

### Composite Metrics
- `human_REI`: Σ(ERROR_WEIGHTS[error_type]) / (fix_iterations + 1)
  (same formula as AI REI for direct comparison)
- `human_REI_c`: human_REI + correctness_ratio × 10
  (same formula as AI REI-c)

## 6. Data Collection Form

```csv
participant_id,paper_id,paper_category,time_first_run_min,time_correct_min,
total_time_min,fix_iterations,error_types,computed_D,self_reported_difficulty,
confidence,notes
```

## 7. Comparison Dimensions

### Primary
1. **Human REI vs AI REI distribution**: Mann-Whitney U test, effect size (Cohen's d)
2. **Human silent failure rate vs AI silent failure rate**: Fisher's exact test
3. **Per-paper paired comparison**: Within-subject (AI vs human on same paper)

### Secondary
4. **Error type distribution**: Do humans make different types of errors than LLMs?
   (Expected: LLMs make more logic errors, humans make more syntax errors)
5. **Time efficiency**: Human minutes vs AI seconds (AI is ~100x faster)
6. **Confidence calibration**: Do participants know when they're wrong?
   (Compare self-reported confidence vs actual correctness)

### Exploratory
7. **Category effect**: Does the AI difficulty category predict human difficulty?
8. **Learning effect**: Do participants improve across the 10 papers?

## 8. Statistical Analysis Plan

```python
# Primary: Mann-Whitney U test on REI distributions
from scipy.stats import mannwhitneyu
u_stat, p_value = mannwhitneyu(human_rei_values, ai_rei_values)

# Silent failure rate comparison
from scipy.stats import fisher_exact
# Contingency table: [human_silent, human_correct; ai_silent, ai_correct]
odds_ratio, p_value = fisher_exact(contingency_table)

# Per-paper paired comparison (within-subjects)
from scipy.stats import wilcoxon
w_stat, p_value = wilcoxon(human_rei_paired, ai_rei_paired)
```

## 9. Ethical Considerations

- **IRB**: Institutional Review Board approval required before recruiting
- **Consent**: Written informed consent explaining study purpose, data use, time commitment
- **Compensation**: Market-rate compensation for time (~$25-30/hour equivalent)
- **Privacy**: De-identified data; participant IDs not linked to personal information
- **No deception**: Full disclosure that this is a metrology study measuring reproducibility effort
- **Right to withdraw**: Participants may stop at any time without penalty

## 10. Expected Outcomes

Based on AI benchmark results (25 papers):

| Hypothesis | Expected | Rationale |
|------------|----------|-----------|
| Human REI > AI REI | Likely | Humans slower but more careful |
| Human silent failure rate < AI rate | Very likely | Humans understand formula semantics better |
| Human logic errors < AI logic errors | Likely | AI's main weakness is semantic understanding |
| Human syntax errors > AI syntax errors | Likely | AI rarely makes syntax mistakes |
| Human time >> AI time | Certain | AI: ~5-20s/paper, Human: ~5-20 min/paper |
| Human confidence correlates with correctness | Unclear | Experts may calibrate well; non-experts may not |

## 11. Limitations

- Small N (10 papers, 3-5 participants) limits statistical power
- Participants are convenience sample (graduate students), not representative
- Task is simplified (only D-index computation, not full paper reproduction)
- No blinding to paper difficulty category
- Single metric type (disruption); multi-metric comparison would require more time

## 12. Next Steps After Data Collection

1. Run statistical comparison against AI benchmark results
2. Publish as "Human-Calibrated Reproducibility Effort Index" technical report
3. If human silent failure rate is significantly lower than AI, this validates REI-c
   as a necessary correction to REI
4. Use human REI distribution to set meaningful thresholds for AI reproducibility
