#!/usr/bin/env python3
"""Debug script: run a single L3 test and save ALL intermediate outputs."""

import sys, os, json, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.metric_templates import (
    get_prompt, parse_metric_output, compute_ground_truth,
    get_primary_metric, METRIC_CONFIGS,
)
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.rei_metric import compute_rei_c


ERROR_WEIGHTS = {"syntax": 1, "import": 2, "runtime": 3, "timeout": 5}


def _extract_code(text: str) -> str:
    if "```python" in text:
        parts = text.split("```python", 1)[1].split("```")
        if parts:
            return parts[0].strip()
    if "```" in text:
        parts = text.split("```", 1)[1].split("```")
        if parts:
            return parts[0].strip()
    return text.strip()


def classify_error(stderr: str) -> str:
    s = stderr.lower()
    if "syntaxerror" in s or "indentationerror" in s:
        return "syntax"
    if "modulenotfounderror" in s or "importerror" in s:
        return "import"
    if "timeout" in s or "timed out" in s:
        return "timeout"
    return "runtime"


def fix_code(llm, code: str, error: str, metric_type: str, attempt: int) -> str:
    metric_label = METRIC_CONFIGS.get(metric_type, {}).get("label", metric_type)
    prompt = f"""Your Python code for "{metric_label}" produced this error:

```
{error[:800]}
```

Your previous code:
```python
{code[:2000]}
```

Fix the error. Output ONLY the corrected Python code in a ```python block.
The code must print results as: <primary_key> = <value>
"""
    response = llm.invoke([{"role": "user", "content": prompt}])
    return _extract_code(str(response.content))


def build_l3_prompt(paper_text, paper_info, test_id, test_title, metric_type,
                    refs_path, cites_path, papers_path=""):
    """Build the L3 prompt from full paper text."""
    config = METRIC_CONFIGS[metric_type]
    task_label = config["label"]

    # Truncate paper text
    max_chars = 30000
    if len(paper_text) > max_chars:
        paper_content = paper_text[:max_chars] + "\n\n[... paper truncated ...]\n\n" + paper_text[-3000:]
    else:
        paper_content = paper_text

    data_section = ""
    if metric_type == "disruption" and refs_path and cites_path:
        papers_section = f"- Papers CSV at '{papers_path}': paper metadata\n" if papers_path else ""
        data_section = f"""Data files provided:
- References CSV at '{refs_path}': papers cited BY test paper {test_id}
- Citation network CSV at '{cites_path}': papers that cite test paper {test_id} and their references
{papers_section}
The task: read the methodology paper below, then implement the {task_label} for test paper {test_id}
(title: "{test_title}").

Your code must:
  1. Load the data files using pandas
  2. Compute the {task_label} described in the methodology paper
  3. Print 'D_INDEX = <value>' (float), plus 'n_i = <value>', 'n_j = <value>' (integers)
"""
    elif metric_type == "citation_count_prediction":
        data_section = f"""Data file provided:
- Papers CSV at '{papers_path}': paper metadata

The task: read the methodology paper below, then implement the {task_label} for test paper {test_id}
(title: "{test_title}").

Your code must:
  1. Load the papers CSV
  2. Compute the impact metric described in the methodology paper
  3. Print 'CITATION_COUNT_PREDICTED = <value>'
"""
    elif metric_type == "team_size_effect":
        data_section = f"""Data file provided:
- Papers CSV at '{papers_path}': paper metadata

The task: read the methodology paper below, then implement the {task_label} for the dataset.
"""

    prompt = f"""## Methodology Paper (full text)

{paper_content}

## Task

{data_section}

IMPORTANT: Output ONLY Python code in a ```python code block. Do NOT include explanations.
The code must print results EXACTLY as specified above.
"""
    return prompt


def debug_single(paper_id="rp_2021_ccby", test_id=None):
    """Debug a single paper-test pair with full output capture."""
    out_dir = Path("refine-logs/debug_l3")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print("Loading SciSciNet data...")
    papers_df = load_table("papers")
    pc = load_table("paper_citations")
    print(f"  Papers: {len(papers_df)}, Citations: {len(pc)}")

    # Load methodology paper
    from scripts.run_manual_papers_benchmark import PAPERS
    paper_registry = {p["id"]: p for p in PAPERS}
    paper_info = paper_registry[paper_id]
    md_path = paper_info["md_path"]
    md_text = Path(md_path).read_text()
    print(f"Methodology paper: {paper_info['title']} ({len(md_text):,} chars)")

    # Find test paper
    if test_id is None:
        df = papers_df.dropna(subset=["citation_count", "reference_count", "title"]).copy()
        df = df[(df["reference_count"] >= 2) & (df["citation_count"] >= 5)]
        row = df[df["disruption_score"].abs() < 0.5].sample(1, random_state=42).iloc[0]
        test_id = int(row["paper_id"])
    else:
        row = papers_df[papers_df["paper_id"] == test_id].iloc[0]

    test_title = str(row.get("title", ""))[:100]
    print(f"Test paper: {test_id} \"{test_title}\"")

    # Compute ground truth
    gt = compute_ground_truth("disruption", test_id, papers_df, pc)
    if not gt:
        print("ERROR: No ground truth")
        return
    gt_value = gt.get("D_index", 0.0)
    print(f"Ground truth D-index: {gt_value:.6f}, n_i={gt.get('n_i')}, n_j={gt.get('n_j')}")

    # Prepare data files
    refs = pc[pc["citing_paper_id"] == test_id]["cited_paper_id"].unique()
    citers = pc[pc["cited_paper_id"] == test_id]["citing_paper_id"].unique()
    print(f"  refs: {len(refs)}, citers: {len(citers)}")

    refs_path = tempfile.mktemp(suffix="_refs.csv")
    cites_path = tempfile.mktemp(suffix="_cites.csv")
    pd.DataFrame({"reference_id": refs}).to_csv(refs_path, index=False)
    citer_cites = pc[pc["citing_paper_id"].isin(citers)][
        ["citing_paper_id", "cited_paper_id"]
    ].head(5000)
    citer_cites.to_csv(cites_path, index=False)
    print(f"  Data files: refs={refs_path}, cites={cites_path}")

    # LLM
    os.environ.setdefault("OPENAI_API_KEY", "not-needed")
    os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
    os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
    from src.sciscigpt_local.llm_backends import load_llm_from_env
    llm = load_llm_from_env()
    print(f"LLM: {llm.model_name}")

    # Build prompt
    metric_type = paper_info["metric_type"]
    prompt = build_l3_prompt(
        md_text, paper_info, test_id, test_title, metric_type,
        refs_path, cites_path, ""
    )

    # Save prompt
    prompt_file = out_dir / f"{paper_id}_test{test_id}_prompt.txt"
    prompt_file.write_text(prompt)
    print(f"Prompt saved to {prompt_file} ({len(prompt):,} chars)")

    # Generate code
    print("\n--- Generating code ---")
    response = llm.invoke([{"role": "user", "content": prompt}])
    code = _extract_code(str(response.content))

    code_file = out_dir / f"{paper_id}_test{test_id}_code_0.py"
    code_file.write_text(code)
    print(f"Initial code saved to {code_file} ({len(code)} chars)")

    # Execute with self-correction
    error_types = []
    for attempt in range(4):
        print(f"\n--- Attempt {attempt + 1} ---")
        result = execute_python(code, timeout=60)
        stderr = result.get("stderr", "")
        stdout = result.get("stdout", "")

        # Save outputs
        (out_dir / f"{paper_id}_test{test_id}_stdout_{attempt}.txt").write_text(stdout)
        (out_dir / f"{paper_id}_test{test_id}_stderr_{attempt}.txt").write_text(stderr)

        has_traceback = "Traceback (most recent call last)" in stderr
        is_error = result["exit_code"] != 0 or has_traceback

        print(f"  exit_code={result['exit_code']}, stderr_len={len(stderr)}, has_traceback={has_traceback}")
        if stderr:
            print(f"  stderr (first 500): {stderr[:500]}")
        if stdout:
            print(f"  stdout (first 500): {stdout[:500]}")

        if not is_error:
            parsed = parse_metric_output(stdout, metric_type)
            primary_key = get_primary_metric(metric_type)
            if primary_key in parsed:
                computed_val = parsed[primary_key]
                weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
                rei = round(weights / max(len(error_types), 1), 2) if error_types else 0.0
                rei_c, c_ratio, silent = compute_rei_c(rei, gt_value, computed_val)
                print(f"\n  SUCCESS: {primary_key}={computed_val} (gt={gt_value})")
                print(f"  REI={rei}, REI-c={rei_c:.2f}, silent={silent}")
                (out_dir / f"{paper_id}_test{test_id}_result.json").write_text(json.dumps({
                    "status": "SUCCESS", "computed": computed_val, "gt": gt_value,
                    "rei": rei, "rei_c": rei_c, "silent": silent,
                }, indent=2))
                return

        error_text = stderr or stdout
        error_cat = classify_error(error_text)
        error_types.append(error_cat)
        print(f"  Error type: {error_cat}")

        if attempt < 3:
            print(f"  Fix attempt {attempt + 1}...")
            code = fix_code(llm, code, error_text, metric_type, attempt)
            code_file = out_dir / f"{paper_id}_test{test_id}_code_{attempt + 1}.py"
            code_file.write_text(code)
            print(f"  Fixed code saved to {code_file} ({len(code)} chars)")

    print(f"\n  FAILED after 4 attempts. Errors: {error_types}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", default="rp_2021_ccby")
    parser.add_argument("--test-id", type=int, default=None)
    args = parser.parse_args()
    debug_single(paper_id=args.paper, test_id=args.test_id)
