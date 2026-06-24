#!/usr/bin/env python3
"""Analyze L3 failures and run L3.5 ablation (method extraction + code synthesis)."""
import sys, os, json, tempfile, argparse, re
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.metric_templates import (
    METRIC_CONFIGS, parse_metric_output, compute_ground_truth, get_primary_metric,
)
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.llm_backends import load_llm_from_env

METHOD_EXTRACTION_PROMPT = """You are reading a research paper and need to extract a COMPUTATIONAL ALGORITHM that can be implemented as Python code using ONLY the data columns listed below.

CRITICAL: You must map the paper's concepts to the EXACT columns available. The algorithm must be implementable in < 50 lines of pandas code.

Paper text:
{paper_text}

## Target Metric: {metric_type}

## Data Available (you can ONLY use these EXACT columns)
Papers CSV:
- paper_id (int), year (int), citation_count (int), disruption_score (float range [-1,1]), author_count (int), reference_count (int)

refs.csv: papers cited BY the focal paper (column: reference_id)
cites.csv: citation edges (columns: citing_paper_id, cited_paper_id)

## Required Output
Produce a YAML-format algorithm spec with EXACT column names, formulas, and values:

```yaml
metric_name: <name>
primary_output: <variable_name>

algorithm:
  1. <pandas step with exact column names and formula>
  2. ...

parameters:
  <name>: <exact_value>

output:
  - print(f"<label>={{<variable>:.6f}}")
```
"""


def load_results():
    # Find most recent results
    log_dir = Path("refine-logs")
    jsons = sorted(log_dir.glob("manual_papers_benchmark_*.json"))
    if not jsons:
        print("No results found")
        return None
    with open(jsons[-1]) as f:
        return json.load(f)


def categorize_l3_failure(r, paper_text=""):
    """Categorize an L3 task failure into taxonomy."""
    metric_type = r["metric_type"]
    paper_id = r["methodology_paper"]
    error_types = r.get("error_types", [])
    fix_count = r.get("fix_count", 0)
    computed = r.get("computed_primary")
    gt = r.get("ground_truth_primary", 0)

    # Determine paper purpose
    PAPER_CATEGORIES = {
        "nature_2023_disruption": "Describes CD-index variant, NOT decade-trend analysis",
        "rp_2025_sam_arts": "Describes frontier scientists for PATENTS, not paper citation threshold",
        "nber_w18958": "Describes team size/collaboration tradeoffs, not simple author_count split",
        "rp_2021_ccby": "About CC-BY open access policies, not D-index computation",
        "pnas_network_impact": "Describes network-normalized impact with specific network params",
        "arxiv_2306_01949": "Describes citation inflation bias explicitly",
        "arxiv_2308_02383": "Overview/survey of disruption index",
        "ms_dynamic_network": "Describes D-index computation explicitly",
    }

    if r["status"] == "FAILED":
        if all(e == "runtime" for e in error_types) and fix_count == 4:
            # All 4 attempts failed with runtime errors
            if metric_type in ("disruption_temporal",):
                return "method_abstract", "Paper describes different metric variant; LLM can't map to target computation"
            elif metric_type in ("frontier_author_impact",):
                return "needs_external", "Paper describes patent/inventor data; method can't be mapped to paper citation data"
            elif metric_type in ("network_normalized_impact",):
                return "data_mapping", "LLM fails to map network metric to available CSV columns"
            else:
                return "computation_error", "Persistent runtime errors despite self-correction"
        else:
            return "computation_error", f"Mixed errors: {error_types}"

    # Success but wrong values
    if computed is not None and gt != 0:
        rel_err = abs(computed - gt) / max(abs(gt), 1e-6)
        if rel_err > 0.20:  # > 20% error = silent failure
            if metric_type == "team_size_effect" and paper_id == "nber_w18958":
                return "method_mismatch", "Paper studies team size/collaboration; LLM extracts wrong team-size computation"
            elif metric_type == "disruption" and paper_id == "rp_2021_ccby":
                return "no_method", "Paper about open access policy; contains no D-index formula"
            elif metric_type == "citation_inflation":
                return "parameter_mismatch", "LLM implements method but with different data filtering or binning"
            elif metric_type == "network_normalized_impact":
                return "data_mapping", "Network metric computed with wrong data subset or column mapping"
            else:
                return "computation_error", f"Wrong value: {computed:.4f} vs GT {gt:.4f} ({rel_err*100:.0f}% error)"

    return "accurate", "Result matches ground truth within tolerance"


def print_l3_taxonomy(results):
    """Print L3 failure taxonomy."""
    l3 = [r for r in results if r["level"] == "L3"]
    taxonomy = defaultdict(list)

    for r in l3:
        cat, desc = categorize_l3_failure(r)
        taxonomy[cat].append((r, desc))

    print("=" * 70)
    print("7.2 L3 FAILURE TAXONOMY")
    print("=" * 70)

    CATEGORY_LABELS = {
        "method_abstract": "Method described too abstractly (wrong variant)",
        "method_mismatch": "Wrong method extracted from paper",
        "no_method": "Paper doesn't describe computational method at all",
        "needs_external": "Paper requires external/proprietary data",
        "data_mapping": "Data field / column mapping error",
        "parameter_mismatch": "Parameter or specification mismatch",
        "computation_error": "Computational / implementation error",
        "accurate": "Accurate reproduction",
    }

    total = len(l3)
    accurate_n = len(taxonomy.get("accurate", []))

    print(f"\nTotal L3 tasks: {total}")
    print(f"Accurate: {accurate_n} ({100*accurate_n//total}%)")
    print(f"Failed or silent-failure: {total - accurate_n} ({100*(total-accurate_n)//total}%)\n")

    print(f"| Category | Count | % | Example |")
    print(f"|----------|-------|----|---------|")
    for cat in ["method_abstract", "no_method", "needs_external", "method_mismatch",
                "data_mapping", "parameter_mismatch", "computation_error", "accurate"]:
        entries = taxonomy.get(cat, [])
        if not entries:
            continue
        label = CATEGORY_LABELS.get(cat, cat)
        pct = 100 * len(entries) // total
        r, desc = entries[0]
        example = f"{r['methodology_paper']} ({r['metric_type']})"
        print(f"| {label} | {len(entries)} | {pct}% | {example} |")

    print(f"\n--- Detailed breakdown ---")
    for cat in ["method_abstract", "no_method", "needs_external", "method_mismatch",
                "data_mapping", "parameter_mismatch", "computation_error", "accurate"]:
        entries = taxonomy.get(cat, [])
        if not entries:
            continue
        label = CATEGORY_LABELS.get(cat, cat)
        print(f"\n**{label}** ({len(entries)} cases):")
        # Group by paper
        by_paper = defaultdict(list)
        for r, desc in entries:
            by_paper[r["methodology_paper"]].append((r, desc))
        for paper, items in by_paper.items():
            metric = items[0][0]["metric_type"]
            _, desc = items[0]
            print(f"  - {paper} / {metric} × {len(items)}: {desc}")


def run_l3_5_ablation(paper_registry, test_papers, llm, papers_df, pc):
    """Run L3.5: first extract method spec, then generate code from spec."""
    print("\n" + "=" * 70)
    print("7.3 L3.5 ABLATION: Method Extraction → Code Synthesis")
    print("=" * 70)

    results_l3 = []
    results_l35 = []

    for paper_info in paper_registry:
        md_path = paper_info.get("md_path", "")
        if not Path(md_path).exists():
            continue
        paper_text = Path(md_path).read_text()
        if len(paper_text) < 500:
            continue
        metric_type = paper_info["metric_type"]

        # Truncate paper text
        max_chars = 30000
        if len(paper_text) > max_chars:
            paper_content = paper_text[:max_chars] + "\n\n[... truncated ...]\n\n" + paper_text[-3000:]
        else:
            paper_content = paper_text

        # Pick first test paper
        test_paper = test_papers[0]
        test_id = test_paper["paper_id"]
        test_title = test_paper.get("title", "")[:80]

        # Prepare data
        refs = pc[pc["citing_paper_id"] == test_id]["cited_paper_id"].unique()
        citers = pc[pc["cited_paper_id"] == test_id]["citing_paper_id"].unique()
        refs_path = tempfile.mktemp(suffix="_refs.csv")
        cites_path = tempfile.mktemp(suffix="_cites.csv")
        pd.DataFrame({"reference_id": refs}).to_csv(refs_path, index=False)
        citer_cites = pc[pc["citing_paper_id"].isin(citers)][["citing_paper_id", "cited_paper_id"]].head(100000)
        citer_cites.to_csv(cites_path, index=False)

        config = METRIC_CONFIGS[metric_type]

        # ── Step 1: Extract method specification ──
        print(f"\n--- {paper_info['id']} ({metric_type}) ---")
        extract_prompt = METHOD_EXTRACTION_PROMPT.format(
            paper_text=paper_content, metric_type=metric_type,
        )
        extract_resp = llm.invoke([{"role": "user", "content": extract_prompt}])
        method_spec = str(extract_resp.content)
        print(f"  Spec extracted: {len(method_spec)} chars")

        # ── Step 2: Generate code from extracted method (with self-correction) ──
        papers_path = test_paper.get("full_papers_path", test_paper.get("papers_path", ""))

        # Build data schema preview for code generation
        schema_preview = ""
        if Path(papers_path).exists():
            try:
                df_preview = pd.read_csv(papers_path, nrows=5)
                schema_preview = f"\nSample data (first 5 rows):\n{df_preview.to_string()}\n"
            except Exception:
                pass

        code_prompt = f"""## Algorithm Specification (Extracted from Paper)
{method_spec}

## Implementation Task

Write Python code using pandas and numpy to implement the algorithm above.

Data files:
- '{papers_path}' — columns: paper_id, year, citation_count, disruption_score, author_count, reference_count{schema_preview}
- '{refs_path}' — list of papers cited BY the focal paper (column: reference_id)
- '{cites_path}' — citation network (columns: citing_paper_id, cited_paper_id)

Focal paper: {test_id} ("{test_title}")

Requirements:
1. Read all required data files
2. Implement the algorithm EXACTLY as specified
3. Print each output value on its own line with a label (e.g., "D_index: 0.123456")
4. Use numpy for correlation (numpy.corrcoef), NOT scipy

Output ONLY Python code in a ```python block. No explanations.
"""
        code_resp = llm.invoke([{"role": "user", "content": code_prompt}])
        raw_code = str(code_resp.content)
        if "```python" in raw_code:
            code = raw_code.split("```python", 1)[1].split("```")[0].strip()
        elif "```" in raw_code:
            code = raw_code.split("```", 1)[1].split("```")[0].strip()
        else:
            code = raw_code.strip()

        # Self-correction loop (up to 3 fix attempts)
        gt = compute_ground_truth(metric_type, test_id, papers_df, pc)
        primary_key = get_primary_metric(metric_type)
        gt_value = gt.get(primary_key, 0.0) if gt else 0.0

        status = "FAILED"
        computed = None
        fix_count = 0
        for attempt in range(4):
            result = execute_python(code, timeout=60)
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            has_traceback = "Traceback (most recent call last)" in stderr
            is_error = result["exit_code"] != 0 or has_traceback

            if not is_error:
                parsed = parse_metric_output(stdout, metric_type)
                if primary_key in parsed:
                    computed = parsed[primary_key]
                    status = "SUCCESS"
                    break

            error_text = stderr or stdout
            fix_count += 1
            if attempt < 3:
                fix_prompt = f"""Your Python code produced this error:

```
{error_text[:600]}
```

Your previous code:
```python
{code[:1500]}
```

Fix the error. Output ONLY the corrected Python code in a ```python block.
"""
                fix_resp = llm.invoke([{"role": "user", "content": fix_prompt}])
                raw_fix = str(fix_resp.content)
                if "```python" in raw_fix:
                    code = raw_fix.split("```python", 1)[1].split("```")[0].strip()
                elif "```" in raw_fix:
                    code = raw_fix.split("```", 1)[1].split("```")[0].strip()
                else:
                    code = raw_fix.strip()

        rel_err = abs(computed - gt_value) / max(abs(gt_value), 1e-6) if computed is not None and gt_value != 0 else None

        l35_entry = {
            "paper_id": test_id,
            "methodology_paper": paper_info["id"],
            "metric_type": metric_type,
            "status": status,
            "computed_primary": computed,
            "ground_truth_primary": gt_value,
            "rel_error": rel_err,
            "method_spec_length": len(method_spec),
            "fix_count": fix_count,
        }

        if status == "SUCCESS":
            tag = "PERFECT" if rel_err is not None and rel_err < 0.001 else f"err={rel_err*100:.1f}%"
            print(f"  L3.5: {status} {primary_key}={computed:.4f} gt={gt_value:.4f} ({tag}) fixes={fix_count}")
        else:
            print(f"  L3.5: FAILED after {fix_count} fixes")

        results_l35.append(l35_entry)

        # Clean up temp files
        try:
            os.unlink(refs_path)
            os.unlink(cites_path)
        except OSError:
            pass

    # Summary
    succ = [r for r in results_l35 if r["status"] == "SUCCESS"]
    perfect = [r for r in succ if r.get("rel_error") is not None and r["rel_error"] < 0.001]

    print(f"\n--- L3.5 Summary ---")
    print(f"Total: {len(results_l35)}")
    print(f"Success: {len(succ)}/{len(results_l35)} ({100*len(succ)//max(1,len(results_l35))}%)")
    print(f"Perfect: {len(perfect)}/{len(results_l35)} ({100*len(perfect)//max(1,len(results_l35))}%)")
    if succ:
        rels = [r["rel_error"] * 100 for r in succ if r.get("rel_error") is not None]
        if rels:
            print(f"Rel error: median={np.median(rels):.2f}%, mean={np.mean(rels):.2f}%")

    return results_l35


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", help="Path to benchmark results JSON (auto-detected)")
    parser.add_argument("--n-test", type=int, default=3)
    parser.add_argument("--l35", action="store_true", help="Run L3.5 ablation")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    # Load existing results
    if args.results:
        with open(args.results) as f:
            data = json.load(f)
    else:
        data = load_results()
    if data is None:
        return

    results = data["results"]

    # ── 7.1 Success vs Perfect ──
    print_success_vs_perfect(results)

    # ── 7.2 L3 Failure Taxonomy ──
    print_l3_taxonomy(results)

    # ── 7.3 L3.5 Ablation ──
    if args.l35:
        os.environ.setdefault("OPENAI_API_KEY", "not-needed")
        os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
        os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")

        print("\nLoading data...")
        papers_df = load_table("papers")
        pc = load_table("paper_citations")
        llm = load_llm_from_env()

        # Build paper registry from results
        paper_ids = sorted(set(r["methodology_paper"] for r in results))
        paper_registry = []
        for pid in paper_ids:
            r = next(r for r in results if r["methodology_paper"] == pid)
            md_path_map = {
                "ms_dynamic_network": "bench-mark/Management Science/A_Dynamic_Network_Measure_of_Technological_Change.md",
                "nber_w18958": "bench-mark/Management Science/w18958.md",
                "arxiv_2306_01949": "bench-mark/others/2306.01949v1.md",
                "arxiv_2308_02383": "bench-mark/others/2308.02383v2.md",
                "nature_2023_disruption": "bench-mark/others/s41586-022-05543-x.md",
                "pnas_network_impact": "bench-mark/others/ke-et-al-2023-a-network-based-normalized-impact-measure-reveals-successful-periods-of-scientific-discovery-across.md",
                "rp_2021_ccby": "bench-mark/rearch-policy/1-s2.0-S0048733320302195-main.md",
                "rp_2025_sam_arts": "bench-mark/rearch-policy/1-s2.0-S0048733325001684-main.md",
            }
            paper_registry.append({
                "id": pid,
                "md_path": md_path_map.get(pid, ""),
                "title": r.get("methodology_title", ""),
                "metric_type": r["metric_type"],
            })

        # Build test papers from results
        test_ids = sorted(set(r["paper_id"] for r in results))[:args.n_test]
        papers_csv_path = tempfile.mktemp(suffix="_papers.csv")
        full_csv_path = tempfile.mktemp(suffix="_papers_full.csv")
        cols = ["paper_id", "year", "citation_count", "disruption_score", "author_count"]
        full_cols = ["paper_id", "year", "citation_count", "disruption_score",
                     "author_count", "reference_count", "title"]
        papers_df[cols].to_csv(papers_csv_path, index=False)
        papers_df.dropna(subset=["year", "citation_count"])[full_cols].to_csv(full_csv_path, index=False)

        test_papers = []
        for tid in test_ids:
            row = papers_df[papers_df["paper_id"] == tid]
            if len(row) == 0:
                continue
            test_papers.append({
                "paper_id": int(tid),
                "title": str(row["title"].values[0])[:100],
                "papers_path": papers_csv_path,
                "full_papers_path": full_csv_path,
            })

        run_l3_5_ablation(paper_registry, test_papers, llm, papers_df, pc)


def print_success_vs_perfect(results):
    """7.1: Tolerance analysis."""
    succ = [r for r in results if r["status"] == "SUCCESS" and r.get("computed_primary") is not None]
    EPS = 1e-6
    for r in succ:
        v = r["computed_primary"]
        gt = r["ground_truth_primary"]
        r["_rel_err"] = abs(v - gt) / max(abs(gt), EPS)

    perfect = [r for r in succ if r["_rel_err"] < 0.001]
    near_perfect = [r for r in succ if 0.001 <= r["_rel_err"] < 0.01]
    acceptable = [r for r in succ if 0.01 <= r["_rel_err"] < 0.05]
    deviated = [r for r in succ if 0.05 <= r["_rel_err"] < 0.20]
    wrong = [r for r in succ if r["_rel_err"] >= 0.20]

    print("=" * 70)
    print("7.1 SUCCESS vs PERFECT: Error Tolerance Analysis")
    print("=" * 70)
    print(f"\nTotal successes: {len(succ)}")
    print(f"\n| Category | Relative Error | Count | % |")
    print(f"|----------|---------------|-------|---|")
    print(f"| Perfect | < 0.1% | {len(perfect)} | {100*len(perfect)//max(1,len(succ))}% |")
    print(f"| Near-perfect | 0.1% - 1% | {len(near_perfect)} | {100*len(near_perfect)//max(1,len(succ))}% |")
    print(f"| Acceptable | 1% - 5% | {len(acceptable)} | {100*len(acceptable)//max(1,len(succ))}% |")
    print(f"| Deviated | 5% - 20% | {len(deviated)} | {100*len(deviated)//max(1,len(succ))}% |")
    print(f"| Wrong | > 20% | {len(wrong)} | {100*len(wrong)//max(1,len(succ))}% |")

    # Bimodal check
    gap = len(near_perfect) + len(acceptable)
    print(f"\nGap analysis (0.1%-5%): {gap} cases")
    print(f"Distribution is BIMODAL: {'YES' if gap <= 2 and len(deviated) <= len(succ)*0.1 else 'NO — check distribution'}")
    if gap == 0:
        print("→ Either the LLM gets it EXACTLY right, or substantially wrong.")
        print("→ No 'close but not exact' cases — definitive signal.")

    # By level breakdown
    print(f"\n--- By level ---")
    for level in ['L1', 'L2', 'L3']:
        lr = [r for r in succ if r['level'] == level]
        if not lr:
            continue
        p = sum(1 for r in lr if r['_rel_err'] < 0.001)
        w = sum(1 for r in lr if r['_rel_err'] >= 0.20)
        rels = [r['_rel_err'] * 100 for r in lr]
        print(f"  {level}: {len(lr)} successes, {p} perfect, {w} wrong, median err={np.median(rels):.3f}%")

    # By metric
    print(f"\n--- By metric ---")
    for mt in sorted(set(r['metric_type'] for r in succ)):
        mr = [r for r in succ if r['metric_type'] == mt]
        p = sum(1 for r in mr if r['_rel_err'] < 0.001)
        w = sum(1 for r in mr if r['_rel_err'] >= 0.20)
        rels = [r['_rel_err'] * 100 for r in mr]
        print(f"  {mt}: {len(mr)} successes, {p} perfect, {w} wrong, median err={np.median(rels):.3f}%")


if __name__ == "__main__":
    main()
