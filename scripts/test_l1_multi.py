#!/usr/bin/env python3
"""Test L1 D-index on multiple test papers."""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OPENAI_API_KEY"] = "not-needed"
os.environ["OPENAI_BASE_URL"] = "http://172.17.65.41:8032/v1"
os.environ["LLM_MODEL"] = "/public/data_share/model_hub/Qwen3-32B/"

import pandas as pd
from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.metric_templates import get_prompt, compute_ground_truth, parse_metric_output
from src.sciscigpt_local.sandbox import execute_python

papers_df = load_table("papers")
pc = load_table("paper_citations")

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

    llm = load_llm_from_env()
    prompt = get_prompt("disruption", paper_id=test_id,
                        refs_path=refs_path, cites_path=cites_path)
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
    print(f"ID={test_id}: D={d} gt={gt['D_index']:.6f} {match} "
          f"n_i={ni}/{gt['n_i']} n_j={nj}/{gt['n_j']} exit={result['exit_code']}")
    if match == "WRONG":
        print(f"  Code: {code[:400]}")
        print()
