#!/usr/bin/env python3
"""Full-pipeline benchmark using manually downloaded papers as L3 input.

Each paper's full text is used as the L3 (full-text) prompt. The LLM must:
  1. Understand the metric/method described in the paper
  2. Implement it in Python
  3. Apply it to SciSciNet data

Ground truth comes from SciSciNet's citation network for D-index computation.
Papers NOT about D-index get qualitative evaluation.

PAPERS (from bench-mark/):
  1. MS: A Dynamic Network Measure of Technological Change (DOI: 10.1287/mnsc.2015.2366)
  2. NBER w18958: Exploring Tradeoffs in the Organization of Scientific Work
  3. arXiv 2306.01949: The disruption index is biased by citation inflation
  4. arXiv 2308.02383: What do we know about the disruption index? An overview
  5. PNAS: A network-based normalized impact measure (Ke, Gates, Barabási)
  6. Nature 2023: Papers and patents are becoming less disruptive (Park, Leahey, Funk)
  7. RP 2021: CC-BY open access paper (DOI: 10.1016/j.respol.2020.104144)
  8. RP 2025: "Not like the others: Frontier scientists for inventive performance"
     — Sam Arts, Thomas Schaper, Reinhilde Veugelers
"""

import sys
import os
import json
import time
import tempfile
import argparse
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
import numpy as np
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.metric_templates import (
    get_prompt as get_metric_prompt, parse_metric_output, compute_ground_truth,
    get_primary_metric, METRIC_CONFIGS,
)
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.rei_metric import compute_rei_c, flag_silent_failure
from src.sciscigpt_local.llm_backends import load_llm_from_env


ERROR_WEIGHTS = {"syntax": 1, "import": 2, "runtime": 3, "timeout": 5}

# ── Paper registry ──
PAPERS = [
    {
        "id": "ms_dynamic_network",
        "md_path": "bench-mark/Management Science/A_Dynamic_Network_Measure_of_Technological_Change.md",
        "title": "A Dynamic Network Measure of Technological Change",
        "journal": "Management Science",
        "year": 2017, "doi": "10.1287/mnsc.2015.2366",
        "metric_type": "disruption",
    },
    {
        "id": "nber_w18958",
        "md_path": "bench-mark/Management Science/w18958.md",
        "title": "Exploring Tradeoffs in the Organization of Scientific Work: Collaboration and Scientific Reward",
        "journal": "NBER Working Paper",
        "year": 2013, "doi": "10.3386/w18958",
        "metric_type": "team_size_effect",
    },
    {
        "id": "arxiv_2306_01949",
        "md_path": "bench-mark/others/2306.01949v1.md",
        "title": "The disruption index is biased by citation inflation",
        "journal": "arXiv preprint",
        "year": 2023, "doi": "",
        "metric_type": "citation_inflation",
    },
    {
        "id": "arxiv_2308_02383",
        "md_path": "bench-mark/others/2308.02383v2.md",
        "title": "What do we know about the disruption index in scientometrics? An overview",
        "journal": "arXiv preprint",
        "year": 2024, "doi": "",
        "metric_type": "disruption",
    },
    {
        "id": "nature_2023_disruption",
        "md_path": "bench-mark/others/s41586-022-05543-x.md",
        "title": "Papers and patents are becoming less disruptive over time",
        "journal": "Nature",
        "year": 2023, "doi": "10.1038/s41586-022-05543-x",
        "metric_type": "disruption_temporal",
    },
    {
        "id": "pnas_network_impact",
        "md_path": "bench-mark/others/ke-et-al-2023-a-network-based-normalized-impact-measure-reveals-successful-periods-of-scientific-discovery-across.md",
        "title": "A network-based normalized impact measure reveals successful periods of scientific discovery across disciplines",
        "journal": "PNAS",
        "year": 2023, "doi": "10.1073/pnas.2301234120",
        "metric_type": "network_normalized_impact",
    },
    {
        "id": "rp_2021_ccby",
        "md_path": "bench-mark/rearch-policy/1-s2.0-S0048733320302195-main.md",
        "title": "Research Policy 2021 — CC-BY Open Access",
        "journal": "Research Policy",
        "year": 2021, "doi": "10.1016/j.respol.2020.104144",
        "metric_type": "disruption",
    },
    {
        "id": "rp_2025_sam_arts",
        "md_path": "bench-mark/rearch-policy/1-s2.0-S0048733325001684-main.md",
        "title": "Not like the others: Frontier scientists for inventive performance",
        "journal": "Research Policy",
        "year": 2025, "doi": "10.1016/j.respol.2025.105339",
        "metric_type": "frontier_author_impact",
    },
]


def _extract_code(text: str) -> str:
    """Extract Python code from LLM response."""
    # Try ```python ... ``` first
    if "```python" in text:
        parts = text.split("```python", 1)[1].split("```")
        if parts:
            return parts[0].strip()
    if "```" in text:
        parts = text.split("```", 1)[1].split("```")
        if parts:
            return parts[0].strip()
    return text.strip()


def fix_code(llm, code: str, error: str, metric_type: str, attempt: int) -> str:
    """Self-correction: ask LLM to fix code based on error."""
    metric_label = METRIC_CONFIGS[metric_type]["label"]
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


def classify_error(stderr: str) -> str:
    """Classify error type."""
    s = stderr.lower()
    if "syntaxerror" in s or "indentationerror" in s:
        return "syntax"
    if "modulenotfounderror" in s or "importerror" in s:
        return "import"
    if "timeout" in s or "timed out" in s:
        return "timeout"
    return "runtime"


def build_l3_prompt_with_paper(paper_text: str, paper_info: dict, test_paper: dict,
                                metric_type: str, refs_path=None, cites_path=None) -> str:
    """L3 prompt: full paper text + SciSciNet data for a test paper."""
    config = METRIC_CONFIGS[metric_type]
    task_label = config["label"]
    test_id = test_paper["paper_id"]
    test_title = test_paper.get("title", "")

    # Truncate paper text to avoid context overflow (keep first 30K and last 3K chars)
    max_chars = 30000
    if len(paper_text) > max_chars:
        paper_content = paper_text[:max_chars] + "\n\n[... paper truncated ...]\n\n" + paper_text[-3000:]
    else:
        paper_content = paper_text

    papers_path = test_paper.get("papers_path", "")
    full_path = test_paper.get("full_papers_path", "")
    dataset_path = full_path or papers_path

    # Per-paper metrics: need refs + cites for specific test paper
    PER_PAPER = {"disruption", "citation_count_prediction",
                 "network_normalized_impact"}
    # Dataset-level metrics: use full papers CSV
    DATASET = {"team_size_effect", "disruption_temporal",
               "citation_inflation", "frontier_author_impact"}

    output_hint = config.get("output_patterns", {})
    print_keys = list(output_hint.keys())[:4]

    if metric_type == "disruption" and refs_path and cites_path:
        data_section = f"""Data files:
- References CSV at '{refs_path}': columns reference_id — papers cited BY test paper {test_id}
- Citation network CSV at '{cites_path}': columns citing_paper_id, cited_paper_id
  Lists ALL citations FROM papers that cite paper {test_id}.
  Every unique citing_paper_id cites paper {test_id}, and the CSV shows every paper THEY cite.

Test paper {test_id}: "{test_title}"

Implement the metric described in the methodology paper.
Print: {', '.join(f'{k} = <value>' for k in print_keys)}
"""

    elif metric_type in PER_PAPER:
        data_section = f"""Data files:
- Papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score, author_count
{f"- Citation network CSV at '{cites_path}': columns citing_paper_id, cited_paper_id" if cites_path else ""}

Test paper {test_id}: "{test_title}"

Implement the metric from the methodology paper.
Print: {', '.join(f'{k} = <value>' for k in print_keys)}
"""

    elif metric_type in DATASET:
        data_section = f"""Data file:
- Papers CSV at '{dataset_path}': includes year, citation_count, disruption_score, author_count

This is a dataset-level analysis. Apply the method from the paper to the entire dataset.
Print: {', '.join(f'{k} = <value>' for k in print_keys)}
"""

    else:
        data_section = f"""Data file:
- Papers CSV at '{dataset_path}'

Implement the metric from the methodology paper.
Print results with appropriate labels.
"""

    prompt = f"""## Methodology Paper (full text)

{paper_content}

## Task: Reproduce the Method

{data_section}

IMPORTANT: Write Python code that implements the method described in the paper above.
Study the paper's description carefully. Output ONLY Python code in a ```python block.
"""
    return prompt


def _build_prompt(level, paper_info, test_id, test_title, metric_type,
                  refs_path, cites_path, md_text, test_paper):
    """Build the prompt for a given level."""
    config = METRIC_CONFIGS[metric_type]

    if level == "L3":
        return build_l3_prompt_with_paper(
            md_text, paper_info,
            {"paper_id": test_id, "title": test_title,
             "papers_path": test_paper.get("papers_path", ""),
             "full_papers_path": test_paper.get("full_papers_path", ""),
             "citation_count": test_paper.get("citations", 0),
             "disruption": test_paper.get("disruption", 0.0)},
            metric_type, refs_path, cites_path,
        ), "pdf_fulltext"
    elif level == "L2":
        papers_path_str = test_paper.get("papers_path", "")
        full_path_str = test_paper.get("full_papers_path", "")
        # Use full papers CSV for dataset-level metrics, filtered for per-paper
        if metric_type in {"disruption_temporal", "citation_inflation",
                           "frontier_author_impact", "team_size_effect"}:
            data_path = full_path_str or papers_path_str
        else:
            data_path = papers_path_str

        prompt_kwargs = dict(paper_id=test_id, papers_path=data_path,
                            cites_path=cites_path, refs_path=refs_path)
        prompt = f"""Read about this methodology:
{paper_info['title']}

{config['prompt'].format(**prompt_kwargs)}
"""
        return prompt, "abstract"
    else:
        # L1: formula + algorithm from config prompt
        papers_path_str = test_paper.get("papers_path", "")
        full_path_str = test_paper.get("full_papers_path", "")
        if metric_type in {"disruption_temporal", "citation_inflation",
                           "frontier_author_impact", "team_size_effect"}:
            data_path = full_path_str or papers_path_str
        else:
            data_path = papers_path_str
        prompt_kwargs = dict(paper_id=test_id, papers_path=data_path)
        if refs_path:
            prompt_kwargs["refs_path"] = refs_path
        if cites_path:
            prompt_kwargs["cites_path"] = cites_path
        return get_metric_prompt(metric_type, **prompt_kwargs), "formula"


def _run_single_task(llm, task, print_lock):
    """Execute one benchmark task: (test_paper, paper_info, level) → result_entry."""
    test_id = task["test_id"]
    test_title = task["test_title"]
    paper_info = task["paper_info"]
    level = task["level"]
    metric_type = task["metric_type"]
    gt_value = task["gt_value"]
    md_text = task["md_text"]
    test_paper = task["test_paper"]

    # Prepare per-task data files
    refs = task["refs"]
    citers = task["citers"]
    refs_path = tempfile.mktemp(suffix="_refs.csv")
    cites_path = tempfile.mktemp(suffix="_cites.csv")
    pd.DataFrame({"reference_id": refs}).to_csv(refs_path, index=False)
    citer_cites = task["pc"][task["pc"]["citing_paper_id"].isin(citers)][
        ["citing_paper_id", "cited_paper_id"]
    ].head(100000)
    citer_cites.to_csv(cites_path, index=False)

    prompt, input_source = _build_prompt(
        level, paper_info, test_id, test_title, metric_type,
        refs_path, cites_path, md_text, test_paper,
    )

    # Generate code
    response = llm.invoke([{"role": "user", "content": prompt}])
    code = _extract_code(str(response.content))

    # Execute with self-correction
    error_types = []
    fix_count = 0
    result_entry = None

    for attempt in range(4):
        result = execute_python(code, timeout=60)
        stderr = result.get("stderr", "")
        stdout = result.get("stdout", "")

        has_traceback = "Traceback (most recent call last)" in stderr
        is_error = result["exit_code"] != 0 or has_traceback

        if not is_error:
            parsed = parse_metric_output(stdout, metric_type)
            primary_key = get_primary_metric(metric_type)
            if primary_key in parsed:
                weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
                rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 0.0
                computed_val = parsed[primary_key]
                rei_c, c_ratio, silent = compute_rei_c(rei, gt_value, computed_val)
                result_entry = {
                    "paper_id": test_id, "methodology_paper": paper_info["id"],
                    "methodology_title": paper_info["title"],
                    "level": level, "metric_type": metric_type,
                    "status": "SUCCESS", "rei": rei, "rei_c": rei_c,
                    "computed_primary": computed_val,
                    "ground_truth_primary": gt_value,
                    "is_silent_failure": silent,
                    "fix_count": fix_count, "error_types": error_types,
                    "input_source": input_source,
                    "paper_chars": len(md_text),
                }
                break

        error_text = stderr or stdout
        error_cat = classify_error(error_text)
        error_types.append(error_cat)
        fix_count += 1

        if attempt < 3:
            code = fix_code(llm, code, error_text, metric_type, attempt)

    if result_entry is None:
        weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
        rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 100.0
        result_entry = {
            "paper_id": test_id, "methodology_paper": paper_info["id"],
            "methodology_title": paper_info["title"],
            "level": level, "metric_type": metric_type,
            "status": "FAILED", "rei": rei, "rei_c": rei,
            "computed_primary": None,
            "ground_truth_primary": gt_value,
            "is_silent_failure": False,
            "fix_count": fix_count, "error_types": error_types,
            "input_source": input_source,
            "paper_chars": len(md_text),
        }

    # Thread-safe print
    with print_lock:
        tag = f"[{level}] Test={test_id} Paper={paper_info['id']}"
        if result_entry["status"] == "SUCCESS":
            pk = get_primary_metric(metric_type)
            print(f"  {tag} {pk}={result_entry['computed_primary']:.4f} "
                  f"gt={gt_value:.4f} REI-c={result_entry['rei_c']:.2f}")
        else:
            print(f"  {tag} FAILED errors={error_types}")

    # Clean up temp files
    try:
        os.unlink(refs_path)
        os.unlink(cites_path)
    except OSError:
        pass

    return result_entry


def run_benchmark(llm, paper_registry, test_papers, pc, papers_df,
                  levels=("L3",), output_dir="refine-logs", workers=4):
    """Run the benchmark across papers and levels using concurrent workers."""
    all_results = []
    paper_map = {}
    print_lock = threading.Lock()

    for p in paper_registry:
        md_text = Path(p["md_path"]).read_text() if Path(p["md_path"]).exists() else ""
        paper_map[p["id"]] = {**p, "text": md_text}
        print(f"Loaded {p['id']}: {len(md_text):,} chars")

    # Build task list
    tasks = []
    gt_cache = {}  # (metric_type, test_id) → gt_dict
    PER_PAPER_METRICS = {"disruption", "citation_count_prediction",
                         "network_normalized_impact"}

    for test_paper in test_papers:
        test_id = test_paper["paper_id"]
        test_title = test_paper.get("title", "")[:80]

        # Precompute per-paper data (only needed for per-paper metrics)
        refs = pc[pc["citing_paper_id"] == test_id]["cited_paper_id"].unique()
        citers = pc[pc["cited_paper_id"] == test_id]["citing_paper_id"].unique()

        for paper_info in paper_registry:
            md_text = paper_map[paper_info["id"]]["text"]
            if len(md_text) < 500:
                continue

            metric_type = paper_info["metric_type"]
            cache_key = (metric_type, test_id)

            if cache_key not in gt_cache:
                gt = compute_ground_truth(metric_type, test_id, papers_df, pc)
                gt_cache[cache_key] = gt
            else:
                gt = gt_cache[cache_key]

            if not gt:
                primary_key = get_primary_metric(metric_type)
                # Dataset-level metrics: test_id doesn't matter, but GT must exist
                if metric_type in PER_PAPER_METRICS:
                    print(f"  SKIP test_paper {test_id} for {metric_type}: no GT")
                    continue

            gt_value = gt.get(get_primary_metric(metric_type), 0.0) if gt else 0.0

            # Only skip per-paper metrics if no refs/citers
            if metric_type in PER_PAPER_METRICS and (len(refs) == 0 or len(citers) == 0):
                continue

            for level in levels:
                tasks.append({
                    "test_id": test_id,
                    "test_title": test_title,
                    "paper_info": paper_info,
                    "level": level,
                    "metric_type": metric_type,
                    "gt_value": gt_value,
                    "md_text": md_text,
                    "test_paper": test_paper,
                    "refs": refs,
                    "citers": citers,
                    "pc": pc,
                })

    print(f"Running {len(tasks)} tasks with {workers} workers...")
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_run_single_task, llm, task, print_lock): task
            for task in tasks
        }
        for future in as_completed(futures):
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                task = futures[future]
                print(f"  ERROR [{task['level']}] Test={task['test_id']} "
                      f"Paper={task['paper_info']['id']}: {e}")

    elapsed = time.time() - t0
    print(f"\nCompleted {len(all_results)} tasks in {elapsed:.1f}s "
          f"({elapsed/len(all_results):.1f}s/task)")

    # Save results
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(output_dir) / f"manual_papers_benchmark_{ts}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "timestamp": datetime.now().isoformat(),
        "description": "Stratified benchmark using manually downloaded papers",
        "n_methodology_papers": len(paper_registry),
        "n_test_papers": len(test_papers),
        "n_results": len(all_results),
        "workers": workers,
        "results": all_results,
    }

    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nResults saved to {out_path}")
    return output


def select_test_papers(papers_df, pc, n=5, seed=42):
    """Select SciSciNet papers with good citation data as test cases.

    Uses precomputed citation_count and reference_count from papers table
    (avoids O(n) full citation graph scans on 78M rows).
    """
    rng = np.random.default_rng(seed)

    # Use precomputed columns: citation_count, reference_count
    df = papers_df.dropna(subset=["citation_count", "reference_count", "title", "year"]).copy()
    df = df[(df["reference_count"] >= 2) & (df["citation_count"] >= 5)]

    # Full papers CSV for dataset-level metrics
    full_cols = ["paper_id", "year", "citation_count", "disruption_score",
                 "author_count", "reference_count", "title"]
    full_papers_path = tempfile.mktemp(suffix="_papers_full.csv")
    papers_df.dropna(subset=["year", "citation_count"])[full_cols].to_csv(
        full_papers_path, index=False)

    # Filtered papers CSV for per-paper metrics
    papers_csv_path = tempfile.mktemp(suffix="_papers.csv")
    cols = ["paper_id", "year", "citation_count", "disruption_score", "author_count"]
    df[cols].to_csv(papers_csv_path, index=False)

    # Pick top-N cited papers with diverse disruption scores
    # Stratify: high/medium/low disruption
    df_pos = df[df["disruption_score"] > 0.05]
    df_neu = df[(df["disruption_score"] >= -0.02) & (df["disruption_score"] <= 0.05)]
    df_neg = df[df["disruption_score"] < -0.02]

    selected = []
    for subset, label in [(df_pos, "high-D"), (df_neu, "neutral-D"), (df_neg, "low-D")]:
        top = subset.nlargest(min(3, len(subset)), "citation_count")
        for _, row in top.iterrows():
            selected.append({
                "paper_id": int(row["paper_id"]),
                "title": str(row["title"])[:100],
                "year": int(row["year"]),
                "citations": int(row["citation_count"]),
                "disruption": float(row["disruption_score"]),
                "papers_path": papers_csv_path,
                "full_papers_path": full_papers_path,
            })

    # Deduplicate and limit
    seen = set()
    unique = []
    for s in selected:
        if s["paper_id"] not in seen:
            seen.add(s["paper_id"])
            unique.append(s)

    rng.shuffle(unique)
    result = unique[:n]
    print(f"Selected {len(result)} test papers from {len(df)} candidates")
    for s in result:
        print(f"  {s['paper_id']} [{s['year']}]: {s['title'][:80]} (D={s['disruption']:.4f}, cit={s['citations']})")
    return result


def main():
    parser = argparse.ArgumentParser(description="Manual papers full-pipeline benchmark")
    parser.add_argument("--n-test", type=int, default=5, help="Number of SciSciNet test papers")
    parser.add_argument("--levels", nargs="+", default=["L3"], choices=["L1", "L2", "L3"])
    parser.add_argument("--output", default="refine-logs")
    parser.add_argument("--llm", default="local", choices=["local", "mock"])
    parser.add_argument("--test-papers", help="JSON file with test paper IDs")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent workers for LLM calls")
    args = parser.parse_args()

    print("=" * 70)
    print("MANUAL PAPERS FULL-PIPELINE BENCHMARK")
    print(f"  Levels: {args.levels}")
    print(f"  Test papers: {args.n_test}")
    print("=" * 70)

    # Load SciSciNet data
    print("\nLoading SciSciNet data...")
    papers_df = load_table("papers")
    pc = load_table("paper_citations")
    print(f"  Papers: {len(papers_df)}, Citations: {len(pc)}")

    # Select test papers
    test_papers = select_test_papers(papers_df, pc, n=args.n_test)

    # Init LLM
    if args.llm == "mock":
        from src.sciscigpt_local.mock_llm import MockLLM
        llm = MockLLM()
        print("  Using MockLLM")
    else:
        llm = load_llm_from_env()
        print(f"  Using local LLM")

    # Run benchmark
    results = run_benchmark(
        llm, PAPERS, test_papers, pc, papers_df,
        levels=tuple(args.levels), output_dir=args.output,
        workers=args.workers,
    )

    # Summary
    successes = [r for r in results["results"] if r["status"] == "SUCCESS"]
    failures = [r for r in results["results"] if r["status"] == "FAILED"]
    silent = [r for r in successes if r.get("is_silent_failure")]

    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"  Total: {len(results['results'])}")
    print(f"  Success: {len(successes)}")
    print(f"  Failed: {len(failures)}")
    print(f"  Silent failures: {len(silent)}")
    if successes:
        rei_c_vals = [r["rei_c"] for r in successes]
        print(f"  REI-c mean: {np.mean(rei_c_vals):.2f}, median: {np.median(rei_c_vals):.2f}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
