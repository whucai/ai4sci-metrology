#!/usr/bin/env python3
"""Quick test of fixed L2 prompt."""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OPENAI_API_KEY"] = "not-needed"
os.environ["OPENAI_BASE_URL"] = "http://172.17.65.41:8032/v1"
os.environ["LLM_MODEL"] = "/public/data_share/model_hub/Qwen3-32B/"

import pandas as pd
from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.metric_templates import parse_metric_output, compute_ground_truth
from src.sciscigpt_local.sandbox import execute_python

papers_df = load_table("papers")
pc = load_table("paper_citations")
llm = load_llm_from_env()

for test_id in [2166706824, 2781525129, 1968388660]:
    row = papers_df[papers_df["paper_id"] == test_id].iloc[0]
    gt = compute_ground_truth("disruption", test_id, papers_df, pc)
    refs = pc[pc["citing_paper_id"] == test_id]["cited_paper_id"].unique()
    citers = pc[pc["cited_paper_id"] == test_id]["citing_paper_id"].unique()
    refs_path = tempfile.mktemp(suffix="_refs.csv")
    cites_path = tempfile.mktemp(suffix="_cites.csv")
    pd.DataFrame({"reference_id": refs}).to_csv(refs_path, index=False)
    citer_cites = pc[pc["citing_paper_id"].isin(citers)][
        ["citing_paper_id", "cited_paper_id"]
    ].head(100000)
    citer_cites.to_csv(cites_path, index=False)

    prompt = f"""Read about this methodology:
A Dynamic Network Measure of Technological Change

Task: Compute the disruption index (D-index) for test paper {test_id}: "{row['title'][:80]}"

Data files:
- References CSV at '{refs_path}': columns reference_id -- papers cited BY paper {test_id}
- Citation network CSV at '{cites_path}': columns citing_paper_id, cited_paper_id

The cites CSV lists all citation edges FROM papers that cite paper {test_id}.
Every unique citing_paper_id cites paper {test_id}. For each citer, the CSV shows ALL papers it cites.

Compute D = (n_i - n_j) / (n_i + n_j):
- n_i = citing papers that cite paper {test_id} but NOT its references
- n_j = citing papers that cite BOTH paper {test_id} AND at least one of its references

Algorithm:
1. Read refs CSV -> set R of reference_id values
2. Read cites CSV -> group by citing_paper_id, collect each citing paper's cited_paper_id set
3. For each citing paper: if cited_papers overlap with R -> n_j, else -> n_i
4. D = (n_i - n_j) / (n_i + n_j)

Use pandas. Print EXACTLY: D_INDEX = <value>, n_i = <value>, n_j = <value>
Output ONLY Python code. No markdown notes or commentary.
"""

    response = llm.invoke([{"role": "user", "content": prompt}])
    raw = str(response.content)
    if "```python" in raw:
        code = raw.split("```python", 1)[1].split("```")[0].strip()
    else:
        code = raw.strip()

    result = execute_python(code, timeout=30)
    parsed = parse_metric_output(result["stdout"], "disruption")
    d = parsed.get("D_index", "N/A")
    ni = parsed.get("n_i", "N/A")
    nj = parsed.get("n_j", "N/A")
    match = "MATCH" if abs(float(d) - gt["D_index"]) < 0.001 else "WRONG"
    status = "OK" if result["exit_code"] == 0 else f"exit={result['exit_code']}"
    print(f"ID={test_id}: D={d} gt={gt['D_index']:.6f} {match} "
          f"n_i={ni}/{gt['n_i']} n_j={nj}/{gt['n_j']} {status}")
    if match == "WRONG":
        print(f"  stdout: {result['stdout'][:200]}")
        print(f"  stderr: {(result.get('stderr') or '')[:300]}")
    print()
