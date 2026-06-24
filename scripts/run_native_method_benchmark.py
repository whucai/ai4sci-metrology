#!/usr/bin/env python3
"""
Native Method Reproduction Benchmark (v3)
=========================================
Each paper is tested on its OWN methodology — the model must:
1. Read the paper
2. Understand what computational method it describes
3. Implement that method in Python
4. Run it on SciSciNet data
5. Draw conclusions from the results

No pre-defined metric types. No pre-written algorithm templates.
"""
import sys, os, json, tempfile, argparse, time, re
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.llm_backends import load_llm_from_env


# ── Paper Registry ──

TIER1 = "tier1"  # Full quantitative evaluation
TIER2 = "tier2"  # Directional evaluation
TIER3 = "tier3"  # Qualitative evaluation

@dataclass
class PaperEntry:
    id: str
    md_path: str
    title: str
    journal: str
    year: int
    tier: str  # tier1/tier2/tier3
    expected_method: str  # Short description for evaluation
    expected_conclusion: str  # What conclusion the paper should reach
    test_type: str  # "per_paper" or "dataset"
    evaluation: str  # "quantitative", "directional", "qualitative"
    ground_truth_fn: str = ""  # Name of GT function for tier1


PAPER_REGISTRY = [
    # ── Tier 1: Full quantitative evaluation ──
    PaperEntry(
        id="ms_dynamic_network",
        md_path="bench-mark/Management Science/A_Dynamic_Network_Measure_of_Technological_Change.md",
        title="A Dynamic Network Measure of Technological Change",
        journal="Management Science", year=2017,
        tier=TIER1, test_type="per_paper", evaluation="quantitative",
        expected_method="CD index: D = (N_i - N_j) / (N_i + N_j + N_k) from citation subgraph",
        expected_conclusion="CD index quantifies whether a paper is disruptive (D>0) or consolidating (D<0)",
        ground_truth_fn="gt_disruption",
    ),
    PaperEntry(
        id="nature_2023_disruption",
        md_path="bench-mark/others/s41586-022-05543-x.md",
        title="Papers and patents are becoming less disruptive over time",
        journal="Nature", year=2023,
        tier=TIER1, test_type="dataset", evaluation="quantitative",
        expected_method="CD5 decade trend: mean disruption by decade, Pearson correlation",
        expected_conclusion="Disruption scores are declining over time across all fields",
        ground_truth_fn="gt_disruption_temporal",
    ),
    PaperEntry(
        id="arxiv_2306_01949",
        md_path="bench-mark/others/2306.01949v1.md",
        title="The disruption index is biased by citation inflation",
        journal="arXiv", year=2023,
        tier=TIER1, test_type="dataset", evaluation="quantitative",
        expected_method="Correlation between reference_count and disruption_score",
        expected_conclusion="Reference count inflation biases disruption index downward over time",
        ground_truth_fn="gt_citation_inflation",
    ),

    # ── Tier 2: Directional evaluation ──
    PaperEntry(
        id="pnas_network_impact",
        md_path="bench-mark/others/ke-et-al-2023-a-network-based-normalized-impact-measure-reveals-successful-periods-of-scientific-discovery-across.md",
        title="A network-based normalized impact measure reveals successful periods of scientific discovery",
        journal="PNAS", year=2023,
        tier=TIER2, test_type="per_paper", evaluation="directional",
        expected_method="C-hat: normalize citations by co-cited papers' mean citations",
        expected_conclusion="Network-normalized impact identifies impactful papers that raw citation counts miss",
    ),
    PaperEntry(
        id="nber_w18958",
        md_path="bench-mark/Management Science/w18958.md",
        title="Exploring Tradeoffs in the Organization of Scientific Work",
        journal="NBER", year=2013,
        tier=TIER2, test_type="dataset", evaluation="directional",
        expected_method="Compare disruption between small vs large teams (by author_count)",
        expected_conclusion="Large teams produce less disruptive science than small teams",
    ),

    # ── Tier 3: Qualitative evaluation ──
    PaperEntry(
        id="arxiv_2308_02383",
        md_path="bench-mark/others/2308.02383v2.md",
        title="What do we know about the disruption index in scientometrics?",
        journal="arXiv", year=2023,
        tier=TIER3, test_type="review", evaluation="qualitative",
        expected_method="N/A - literature review",
        expected_conclusion="This is a review paper cataloging D-index variants, not proposing a new method",
    ),
    PaperEntry(
        id="rp_2021_ccby",
        md_path="bench-mark/rearch-policy/1-s2.0-S0048733320302195-main.md",
        title="Natural language processing to identify the creation and impact of new technologies",
        journal="Research Policy", year=2021,
        tier=TIER3, test_type="unavailable", evaluation="qualitative",
        expected_method="NLP on patent text (keywords, cosine similarity)",
        expected_conclusion="Requires raw patent text — not available in SciSciNet",
    ),
    PaperEntry(
        id="rp_2025_sam_arts",
        md_path="bench-mark/rearch-policy/1-s2.0-S0048733325001684-main.md",
        title="Not like the others: Frontier scientists for inventive performance",
        journal="Research Policy", year=2025,
        tier=TIER3, test_type="unavailable", evaluation="qualitative",
        expected_method="Regression with inventor-author linked data + frontier scientist dummy",
        expected_conclusion="Requires inventor-author disambiguation — PatentsView + OpenAlex data available but needs fusion",
    ),
]


# ── Ground Truth Functions ──

def gt_disruption(papers, pc, paper_id):
    """Compute D-index from citation subgraph."""
    refs = pc[pc["citing_paper_id"] == paper_id]["cited_paper_id"].unique()
    citers = pc[pc["cited_paper_id"] == paper_id]["citing_paper_id"].unique()
    if len(citers) == 0:
        return {"D_index": 0.0, "ni": 0, "nj": 0, "nk": 0}
    ni = 0
    nj = 0
    nk = 0
    for citer in citers:
        citer_refs = set(pc[pc["citing_paper_id"] == citer]["cited_paper_id"].unique())
        cites_focal = paper_id in citer_refs
        cites_predecessor = bool(citer_refs & set(refs))
        if cites_focal and not cites_predecessor:
            ni += 1
        elif cites_focal and cites_predecessor:
            nj += 1
        elif not cites_focal and cites_predecessor:
            nk += 1
    denom = ni + nj + nk
    if denom == 0:
        return {"D_index": 0.0, "ni": ni, "nj": nj, "nk": nk}
    d = (ni - nj) / denom
    return {"D_index": round(float(d), 6), "ni": ni, "nj": nj, "nk": nk}


def gt_disruption_temporal(papers, pc, paper_id=None):
    """Decade trend of disruption scores."""
    df = papers.dropna(subset=["year", "disruption_score"]).copy()
    df["decade"] = (df["year"] // 10) * 10
    decades = df.groupby("decade")["disruption_score"].mean()
    decades = decades[decades.index >= 1900]  # Skip sparse early years
    if len(decades) < 2:
        return {}
    r = np.corrcoef(decades.index.values.astype(float), decades.values)[0, 1]
    return {
        "trend_correlation": round(float(r), 6),
        "earliest_decade": int(decades.index.min()),
        "earliest_mean_d": round(float(decades.iloc[0]), 6),
        "latest_decade": int(decades.index.max()),
        "latest_mean_d": round(float(decades.iloc[-1]), 6),
    }


def gt_citation_inflation(papers, pc, paper_id=None):
    """Correlation between reference_count and disruption_score."""
    df = papers.dropna(subset=["reference_count", "disruption_score"]).copy()
    df = df[(df["reference_count"] >= 1) & (df["reference_count"] <= 500)]
    r = np.corrcoef(df["reference_count"].values.astype(float),
                    df["disruption_score"].values.astype(float))[0, 1]
    # Also compute decile means for trend
    try:
        df["ref_decile"] = pd.qcut(df["reference_count"], 10, labels=False, duplicates="drop")
        decile_means = df.groupby("ref_decile")["disruption_score"].mean()
        return {
            "correlation": round(float(r), 6),
            "n_papers": len(df),
            "lowest_ref_mean_d": round(float(decile_means.iloc[0]), 6),
            "highest_ref_mean_d": round(float(decile_means.iloc[-1]), 6),
        }
    except ValueError:
        return {"correlation": round(float(r), 6), "n_papers": len(df)}


# ── Data Schema (shown to the model) ──

DATA_SCHEMA = """
Papers CSV columns (111,927 papers):
- paper_id (int), year (int), citation_count (int), citation_count_5y (int),
  citation_count_10y (int), reference_count (int), author_count (int),
  disruption_score (float, range [-1,1]), novelty_score (float),
  conventionality_score (float), title (str), abstract (str),
  journal_name (str)

Citation edges CSV (78M rows):
- citing_paper_id (int), cited_paper_id (int)"""


# ── Prompt Template ──

PHASE1_PROMPT = """You are a bibliometrics researcher reproducing a scientific paper. Read the paper text below, then write Python code to implement its MAIN computational method.

## Paper Text
{paper_text}

## Available Data
The following data files are available on disk:{data_schema}

Specific files for this task:
- Papers CSV: {papers_path}
- Citation edges CSV: {cites_path}
{focal_section}

## Your Task
1. **IDENTIFY** the main computational method described in this paper — what does it measure, and how is it computed?
2. **IMPLEMENT** the method as Python code using ONLY pandas and numpy

## Output Format
Your response must follow this EXACT structure:

METHOD: <1-3 sentences describing what computation you will perform and what it measures>

```python
<your code here>
```

## CRITICAL Rules
- Read the CSV files with pd.read_csv("{papers_path}") and pd.read_csv("{cites_path}")
- The Papers CSV has these EXACT columns: paper_id, year, citation_count, citation_count_5y, citation_count_10y, reference_count, author_count, disruption_score, novelty_score, conventionality_score, title, abstract, journal_name
- Use numpy.corrcoef(x, y)[0, 1] for correlation, NOT scipy
- Print each numerical result as "KEY=VALUE" on its own line (e.g., "D_index=0.123456")
- Do NOT print thousands of rows — only summary statistics
- Do NOT write RESULTS or CONCLUSION yet — those will be added after execution
"""

PHASE2_PROMPT = """Your Python code has been executed. Here are the actual results:

## Code Execution Output (stdout)
{stdout}

## Code Execution Errors (stderr)
{stderr}

## Your Original Method Description
{method}

## Paper Claims
The paper claims: {paper_claims}

## Your Task
Based on the ACTUAL execution output above:

1. **REPORT** the key numerical findings from stdout
2. **CONCLUDE** — do the results support or contradict the paper's claims? Be specific about what the numbers mean.
3. If stdout is empty or the code failed, state that the reproduction was unsuccessful and why.

## Output Format

RESULTS: <key numerical values from stdout, one per line>

CONCLUSION: <2-4 sentences interpreting the ACTUAL results. Reference specific numbers. State whether they support the paper's claims. If the computation failed or returned unexpected values, say so honestly.>"""


def build_native_prompt(paper_entry, paper_text, papers_path, cites_path, test_paper=None):
    """Build the generic prompt for a paper."""
    focal_section = ""
    if paper_entry.test_type == "per_paper" and test_paper:
        focal_section = f"""- Focal paper ID: {test_paper['paper_id']}
  Title: {test_paper.get('title', 'Unknown')[:150]}"""

    # Include data schema hint
    data_schema = DATA_SCHEMA
    if paper_entry.tier == TIER3:
        data_schema += "\n\nNOTE: The data above may NOT be sufficient to fully reproduce this paper's method. If the method requires data not listed above, clearly state what is missing."

    return PHASE1_PROMPT.format(
        paper_text=paper_text,
        data_schema=data_schema,
        papers_path=papers_path,
        cites_path=cites_path,
        focal_section=focal_section,
    )


def extract_sections(response_text):
    """Parse the model's response into METHOD, CODE, RESULTS, CONCLUSION sections."""
    result = {"method": "", "code": "", "results": "", "conclusion": ""}

    # Extract METHOD
    m = re.search(r'^METHOD:\s*(.+?)(?=```python|\Z)', response_text, re.DOTALL | re.MULTILINE)
    if m:
        result["method"] = m.group(1).strip()

    # Extract CODE
    m = re.search(r'```python\s*\n(.+?)```', response_text, re.DOTALL)
    if m:
        result["code"] = m.group(1).strip()
    else:
        m = re.search(r'```\s*\n(.+?)```', response_text, re.DOTALL)
        if m:
            result["code"] = m.group(1).strip()

    # Extract RESULTS
    # After ``` block, before CONCLUSION
    code_end = response_text.rfind("```")
    if code_end > 0:
        after_code = response_text[code_end+3:]
        m = re.search(r'RESULTS:\s*(.+?)(?=CONCLUSION:|\Z)', after_code, re.DOTALL)
        if m:
            result["results"] = m.group(1).strip()

    # Extract CONCLUSION
    m = re.search(r'CONCLUSION:\s*(.+?)$', response_text, re.DOTALL)
    if m:
        result["conclusion"] = m.group(1).strip()

    return result


def extract_numeric_output(stdout):
    """Extract all KEY=VALUE pairs from stdout."""
    pairs = {}
    for line in stdout.strip().split("\n"):
        line = line.strip()
        # Match "KEY = VALUE" or "KEY=VALUE" or "KEY: VALUE"
        for pattern in [
            r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(-?[\d.]+(?:e[+-]?\d+)?)',
            r'^([a-zA-Z_][a-zA-Z0-9_]*):\s*(-?[\d.]+(?:e[+-]?\d+)?)',
        ]:
            m = re.match(pattern, line)
            if m:
                key = m.group(1).strip()
                try:
                    pairs[key] = float(m.group(2))
                except ValueError:
                    pairs[key] = m.group(2)
                break
    return pairs


def evaluate_task(paper_entry, response_text, stdout, stderr, exit_code, computed_values, execution_ok=None):
    """
    Evaluate a completed task across 3 levels.
    Returns score 0-5 and detailed breakdown.
    """
    if execution_ok is None:
        execution_ok = exit_code == 0 and "Traceback (most recent call last)" not in stderr
    evaluation = {
        "score": 0,
        "execution_ok": False,
        "method_ok": False,
        "results_ok": False,
        "conclusion_ok": False,
        "details": [],
    }

    # ── Level 1: Execution ──
    has_traceback = "Traceback (most recent call last)" in stderr
    if exit_code == 0 and not has_traceback and computed_values:
        evaluation["execution_ok"] = True
        evaluation["score"] = max(evaluation["score"], 1)
        evaluation["details"].append("✓ Code executed successfully")
    else:
        error_summary = (stderr or stdout)[:200]
        evaluation["details"].append(f"✗ Execution failed: {error_summary}")
        return evaluation  # Can't evaluate further

    # ── Level 2: Method Identification ──
    sections = extract_sections(response_text)
    method_desc = sections.get("method", "")

    # Basic checks on method identification
    method_lower = method_desc.lower()
    expected_lower = paper_entry.expected_method.lower()

    # Check if method mentions key concepts from the paper
    key_terms = {
        "disruption": ["disruption", "d-index", "cd index", "cd5", "n_i", "n_j"],
        "trend": ["decade", "trend", "correlation", "over time"],
        "inflation": ["reference", "inflation", "bias", "correlation"],
        "network": ["network", "normalize", "co-cited", "cocited", "impact"],
        "team": ["team", "author", "small", "large", "collaboration"],
        "review": ["review", "overview", "catalog", "survey", "literature"],
        "nlp": ["nlp", "text", "natural language", "keyword", "cosine"],
        "frontier": ["frontier", "inventor", "patent", "regression", "scientist"],
    }

    paper_type = {
        "ms_dynamic_network": "disruption",
        "nature_2023_disruption": "trend",
        "arxiv_2306_01949": "inflation",
        "pnas_network_impact": "network",
        "nber_w18958": "team",
        "arxiv_2308_02383": "review",
        "rp_2021_ccby": "nlp",
        "rp_2025_sam_arts": "frontier",
    }.get(paper_entry.id, "")

    expected_terms = key_terms.get(paper_type, [])
    matched_terms = [t for t in expected_terms if t in method_lower]

    # For tier3 review/unavailable papers: correct identification = recognizing it's a review or needs unavailable data
    if paper_entry.tier == TIER3:
        if paper_entry.test_type == "review":
            if any(t in method_lower for t in ["review", "overview", "catalog", "survey"]):
                evaluation["method_ok"] = True
                evaluation["score"] = max(evaluation["score"], 3)
                evaluation["details"].append("✓ Correctly identified as review paper")
            else:
                evaluation["details"].append("✗ Failed to identify as review paper")
        elif paper_entry.test_type == "unavailable":
            if any(t in method_lower for t in ["unavailable", "missing", "require", "not available", "cannot"]):
                evaluation["method_ok"] = True
                evaluation["score"] = max(evaluation["score"], 3)
                evaluation["details"].append("✓ Correctly identified data limitations")
            elif matched_terms:
                evaluation["method_ok"] = True
                evaluation["score"] = max(evaluation["score"], 2)
                evaluation["details"].append("⚠ Correctly identified method but may not have noted data unavailability")
            else:
                evaluation["details"].append("✗ Failed to identify correct method")
    else:
        if len(matched_terms) >= 2:
            evaluation["method_ok"] = True
            evaluation["score"] = max(evaluation["score"], 3)
            evaluation["details"].append(f"✓ Method correctly identified (matched: {matched_terms})")
        elif len(matched_terms) >= 1:
            evaluation["method_ok"] = True
            evaluation["score"] = max(evaluation["score"], 2)
            evaluation["details"].append(f"⚠ Method partially identified (matched: {matched_terms})")
        else:
            evaluation["details"].append(f"✗ Method not correctly identified (looked for: {expected_terms})")

    # ── Level 3: Results & Conclusions ──
    # Check if results section has actual numbers
    results_text = sections.get("results", "")
    has_numbers = bool(re.search(r'\d+\.?\d*', results_text))

    # CRITICAL: Check for fabricated results (response numbers ≠ stdout numbers)
    if evaluation["execution_ok"] and computed_values and has_numbers:
        # Extract numbers from the RESULTS text
        result_nums = {}
        for line in results_text.strip().split("\n"):
            line = line.strip()
            for pattern in [
                r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(-?[\d.]+(?:e[+-]?\d+)?)',
                r'^([a-zA-Z_][a-zA-Z0-9_]*):\s*(-?[\d.]+(?:e[+-]?\d+)?)',
            ]:
                m = re.match(pattern, line)
                if m:
                    result_nums[m.group(1)] = float(m.group(2))
                    break
        # Compare with stdout values
        if result_nums:
            mismatches = []
            for k, v in result_nums.items():
                if k in computed_values:
                    stdout_v = computed_values[k]
                    if abs(v - stdout_v) > 0.001 and abs(stdout_v) > 1e-10:
                        mismatches.append(f"{k}: claimed={v:.4f}, actual={stdout_v:.4f}")
            if mismatches:
                evaluation["score"] = max(0, evaluation["score"] - 2)
                evaluation["details"].append(f"🚨 FABRICATED RESULTS: {', '.join(mismatches[:3])}")

    # Check conclusion against expected
    conclusion_text = sections.get("conclusion", "")
    conclusion_lower = conclusion_text.lower()

    if not has_numbers and paper_entry.tier != TIER3:
        evaluation["details"].append("✗ No numerical results reported")
    else:
        evaluation["results_ok"] = True

    # Check if conclusion is substantive (not just boilerplate)
    if len(conclusion_text) < 30:
        evaluation["details"].append("✗ Conclusion too short or missing")
    elif paper_entry.tier == TIER1:
        # For tier1: check conclusion against expected direction
        expected_conclusion_lower = paper_entry.expected_conclusion.lower()
        # Simple keyword overlap
        conclusion_keywords = set(conclusion_lower.split()) & set(expected_conclusion_lower.split())
        if len(conclusion_keywords) >= 3:
            evaluation["conclusion_ok"] = True
            evaluation["score"] = min(5, evaluation["score"] + 1)
            evaluation["details"].append("✓ Conclusion aligns with paper's claims")
        else:
            evaluation["score"] = min(4, evaluation["score"])
            evaluation["details"].append("⚠ Conclusion present but may not fully align with paper")
    elif paper_entry.tier == TIER2:
        if has_numbers and len(conclusion_text) >= 30:
            evaluation["conclusion_ok"] = True
            evaluation["score"] = min(5, evaluation["score"] + 1)
            evaluation["details"].append("✓ Results and conclusion present")
    elif paper_entry.tier == TIER3:
        if len(conclusion_text) >= 20:
            evaluation["conclusion_ok"] = True
            evaluation["details"].append("✓ Qualitative assessment provided")
            # Bonus: if it correctly identifies data needs
            if any(w in conclusion_lower for w in ["patent", "text", "inventor", "openalex", "patentsview"]):
                evaluation["score"] = min(5, evaluation["score"] + 1)

    return evaluation


def run_native_task(paper_entry, papers_path, cites_path, test_paper, llm, papers_df, pc):
    """Execute a single paper reproduction task with two-pass design:
    Pass 1: read paper → generate code
    Pass 2: execute code → feed stdout back → generate RESULTS + CONCLUSION
    """
    result = {
        "paper_id": paper_entry.id,
        "paper_title": paper_entry.title,
        "tier": paper_entry.tier,
        "test_type": paper_entry.test_type,
        "test_paper_id": test_paper.get("paper_id") if test_paper else None,
        "status": "FAILED",
        "score": 0,
        "evaluation": {},
        "response_text": "",
        "computed_values": {},
        "stdout": "",
        "stderr": "",
        "fix_count": 0,
        "elapsed": 0,
    }

    t0 = time.time()

    # Read paper text
    try:
        paper_text = Path(paper_entry.md_path).read_text()
    except FileNotFoundError:
        result["status"] = "SKIPPED"
        result["evaluation"] = {"details": [f"Paper file not found: {paper_entry.md_path}"]}
        return result

    # Truncate if too long
    max_chars = 30000
    if len(paper_text) > max_chars:
        paper_text = paper_text[:max_chars] + "\n\n[... truncated ...]\n\n" + paper_text[-3000:]

    # Build prompt
    prompt = build_native_prompt(paper_entry, paper_text, papers_path, cites_path, test_paper)

    # ── Phase 1: Read paper → generate code ──
    phase1_response = llm.invoke([{"role": "user", "content": prompt}])
    phase1_text = str(phase1_response.content)
    sections = extract_sections(phase1_text)
    method_desc = sections["method"]
    code = sections["code"]

    if not code:
        result["status"] = "FAILED"
        result["evaluation"] = {"score": 0, "details": ["✗ No Python code found in response"]}
        result["elapsed"] = time.time() - t0
        return result

    # ── Self-correction loop for code execution (up to 4 attempts) ──
    stdout = ""
    stderr = ""
    exit_code = -1
    fix_count = 0

    for attempt in range(4):
        exec_result = execute_python(code, timeout=120)
        stdout = exec_result.get("stdout", "")
        stderr = exec_result.get("stderr", "")
        exit_code = exec_result.get("exit_code", -1)
        has_traceback = "Traceback (most recent call last)" in stderr
        is_error = exit_code != 0 or has_traceback

        if not is_error:
            break

        fix_count = attempt + 1
        error_text = stderr or stdout
        if attempt < 3:
            fix_prompt = f"""Your Python code produced an error:

```
{error_text[:800]}
```

Your previous code:
```python
{code[:2000]}
```

Fix the error and output ONLY the corrected Python code in a ```python block.
"""
            fix_response = llm.invoke([{"role": "user", "content": fix_prompt}])
            raw_fix = str(fix_response.content)
            if "```python" in raw_fix:
                code = raw_fix.split("```python", 1)[1].split("```")[0].strip()
            elif "```" in raw_fix:
                code = raw_fix.split("```", 1)[1].split("```")[0].strip()
            else:
                code = raw_fix.strip()

    computed_values = extract_numeric_output(stdout)
    execution_ok = exit_code == 0 and not ("Traceback (most recent call last)" in stderr)

    # ── Phase 2: Feed stdout back → generate RESULTS + CONCLUSION ──
    phase2_text = ""
    if stdout.strip() or stderr.strip():
        phase2_prompt = PHASE2_PROMPT.format(
            stdout=stdout[:2000] if stdout else "(empty)",
            stderr=stderr[:500] if stderr else "(none)",
            method=method_desc[:1000],
            paper_claims=paper_entry.expected_conclusion,
        )
        phase2_response = llm.invoke([{"role": "user", "content": phase2_prompt}])
        phase2_text = str(phase2_response.content)

    # Combine for evaluation
    full_response = phase1_text + "\n\n" + phase2_text
    result["response_text"] = full_response[:8000]
    result["stdout"] = stdout[:2000]
    result["stderr"] = stderr[:500]
    result["computed_values"] = computed_values
    result["fix_count"] = fix_count
    result["elapsed"] = time.time() - t0

    # ── Step 3: Evaluate ──
    evaluation = evaluate_task(
        paper_entry, full_response, stdout, stderr, exit_code,
        computed_values, execution_ok
    )
    result["evaluation"] = evaluation
    result["score"] = evaluation["score"]
    result["status"] = "SUCCESS" if execution_ok else "FAILED"

    return result


def main():
    parser = argparse.ArgumentParser(description="Native Method Reproduction Benchmark (v3)")
    parser.add_argument("--n-test", type=int, default=3, help="Number of test papers (for tier1/tier2)")
    parser.add_argument("--workers", type=int, default=6, help="Concurrent workers")
    parser.add_argument("--tier", choices=["1", "2", "3", "all"], default="all")
    parser.add_argument("--papers", help="Comma-separated paper IDs to test")
    args = parser.parse_args()

    # Setup
    os.environ.setdefault("OPENAI_API_KEY", "not-needed")
    os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
    os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")

    print("=" * 70)
    print("NATIVE METHOD REPRODUCTION BENCHMARK (v3)")
    print("  Each paper tested on its OWN methodology")
    print("=" * 70)

    # Load data
    print("\nLoading SciSciNet data...")
    papers_df = load_table("papers")
    pc = load_table("paper_citations")
    llm = load_llm_from_env()
    print(f"  Papers: {len(papers_df):,}, Citations: {len(pc):,}")

    # Prepare data files
    full_cols = ["paper_id", "year", "citation_count", "citation_count_5y",
                 "citation_count_10y", "reference_count", "author_count",
                 "disruption_score", "novelty_score", "conventionality_score",
                 "title", "abstract", "journal_name"]
    papers_path = tempfile.mktemp(suffix="_papers_full.csv")
    papers_df.dropna(subset=["year", "citation_count"])[full_cols].to_csv(
        papers_path, index=False)

    # Citation edges sample (too large for full 78M, take subset)
    cites_sample = pc.head(5000000)  # 5M rows
    cites_path = tempfile.mktemp(suffix="_cites.csv")
    cites_sample.to_csv(cites_path, index=False)

    # Select test papers for tier1/tier2 (per-paper type)
    test_pool = papers_df.dropna(subset=["citation_count", "disruption_score"])
    test_pool = test_pool[test_pool["citation_count"] >= 10]
    # Stratify by disruption
    test_pool["d_bucket"] = pd.cut(test_pool["disruption_score"],
                                    bins=[-1, -0.5, -0.05, 0.05, 0.5, 1],
                                    labels=["very_low", "low", "neutral", "high", "very_high"])
    test_papers = []
    for bucket in ["very_high", "high", "neutral", "low"]:
        bucket_papers = test_pool[test_pool["d_bucket"] == bucket].nlargest(2, "citation_count")
        for _, row in bucket_papers.iterrows():
            test_papers.append({
                "paper_id": int(row["paper_id"]),
                "title": str(row.get("title", ""))[:150],
                "year": int(row["year"]),
                "disruption": float(row["disruption_score"]),
            })
    test_papers = test_papers[:args.n_test]
    print(f"  Test papers: {len(test_papers)}")

    # Filter papers
    if args.papers:
        selected_papers = [p for p in PAPER_REGISTRY if p.id in args.papers.split(",")]
    elif args.tier != "all":
        tier_map = {"1": TIER1, "2": TIER2, "3": TIER3}
        selected_papers = [p for p in PAPER_REGISTRY if p.tier == tier_map[args.tier]]
    else:
        selected_papers = list(PAPER_REGISTRY)

    print(f"  Methodology papers to test: {len(selected_papers)}")
    for p in selected_papers:
        print(f"    [{p.tier}] {p.id} — {p.title[:80]}")

    # Run tasks
    tasks = []
    for paper_entry in selected_papers:
        if paper_entry.test_type == "per_paper":
            for tp in test_papers:
                tasks.append((paper_entry, tp))
        elif paper_entry.test_type == "dataset":
            tasks.append((paper_entry, None))
        elif paper_entry.test_type in ("review", "unavailable"):
            tasks.append((paper_entry, None))

    print(f"\n  Total tasks: {len(tasks)}")
    print(f"  Workers: {args.workers}")
    print()

    all_results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        for i, (paper_entry, test_paper) in enumerate(tasks):
            future = executor.submit(
                run_native_task, paper_entry, papers_path, cites_path,
                test_paper, llm, papers_df, pc
            )
            futures[future] = (paper_entry.id, test_paper.get("paper_id") if test_paper else "dataset", i+1)

        for future in as_completed(futures):
            paper_id, test_id, task_num = futures[future]
            try:
                result = future.result(timeout=300)
                all_results.append(result)

                # Print progress
                status_icon = "✓" if result["status"] == "SUCCESS" else "✗"
                score = result.get("score", 0)
                print(f"  [{task_num}/{len(tasks)}] {status_icon} {result['paper_id'][:30]} "
                      f"score={score}/5 fixes={result['fix_count']} "
                      f"({result['elapsed']:.0f}s)")
                if result["evaluation"].get("details"):
                    for d in result["evaluation"]["details"][:2]:
                        print(f"       {d}")
            except Exception as e:
                print(f"  [{task_num}/{len(tasks)}] ✗ ERROR: {e}")
                all_results.append({
                    "paper_id": paper_id, "status": "ERROR",
                    "error": str(e), "score": 0,
                })

    # ── Summary ──
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)

    # By tier
    for tier in [TIER1, TIER2, TIER3]:
        tier_results = [r for r in all_results if r.get("tier") == tier]
        if not tier_results:
            continue
        succ = sum(1 for r in tier_results if r["status"] == "SUCCESS")
        avg_score = np.mean([r.get("score", 0) for r in tier_results])
        exec_ok = sum(1 for r in tier_results if r.get("evaluation", {}).get("execution_ok"))
        method_ok = sum(1 for r in tier_results if r.get("evaluation", {}).get("method_ok"))
        conclusion_ok = sum(1 for r in tier_results if r.get("evaluation", {}).get("conclusion_ok"))
        avg_fixes = np.mean([r.get("fix_count", 0) for r in tier_results])
        print(f"\n  {tier.upper()} ({len(tier_results)} tasks):")
        print(f"    Success: {succ}/{len(tier_results)} | Avg score: {avg_score:.1f}/5")
        print(f"    Execution OK: {exec_ok}/{len(tier_results)} | Method OK: {method_ok}/{len(tier_results)} | Conclusion OK: {conclusion_ok}/{len(tier_results)}")
        print(f"    Avg fixes: {avg_fixes:.1f}")

    # By paper
    print("\n  --- By Paper ---")
    by_paper = defaultdict(list)
    for r in all_results:
        by_paper[r["paper_id"]].append(r)
    for pid in sorted(by_paper):
        pr = by_paper[pid]
        succ = sum(1 for r in pr if r["status"] == "SUCCESS")
        avg_score = np.mean([r.get("score", 0) for r in pr])
        print(f"    {pid}: {succ}/{len(pr)} success, avg score {avg_score:.1f}/5")

    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = f"refine-logs/native_method_benchmark_{timestamp}.json"
    os.makedirs("refine-logs", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "description": "Native method reproduction benchmark — each paper on its own methodology",
            "n_tasks": len(tasks),
            "workers": args.workers,
            "results": all_results,
        }, f, indent=2, default=str)
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
