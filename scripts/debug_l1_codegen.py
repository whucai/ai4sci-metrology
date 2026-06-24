#!/usr/bin/env python3
"""Debug L1 D-index code generation quality."""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OPENAI_API_KEY"] = "not-needed"
os.environ["OPENAI_BASE_URL"] = "http://172.17.65.41:8032/v1"
os.environ["LLM_MODEL"] = "/public/data_share/model_hub/Qwen3-32B/"

import pandas as pd
import numpy as np
from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.metric_templates import get_prompt, compute_ground_truth, parse_metric_output
from src.sciscigpt_local.sandbox import execute_python

# Load data
print("Loading data...")
papers_df = load_table("papers")
pc = load_table("paper_citations")

test_id = 1968388660
row = papers_df[papers_df["paper_id"] == test_id].iloc[0]
print(f"Test paper: {test_id} - {row['title'][:80]}")

# Ground truth
gt = compute_ground_truth("disruption", test_id, papers_df, pc)
print(f"GT: D={gt['D_index']}, n_i={gt['n_i']}, n_j={gt['n_j']}")

# Prepare data
refs = pc[pc["citing_paper_id"] == test_id]["cited_paper_id"].unique()
citers = pc[pc["cited_paper_id"] == test_id]["citing_paper_id"].unique()
print(f"refs={len(refs)}, citers={len(citers)}")

refs_path = tempfile.mktemp(suffix="_refs.csv")
cites_path = tempfile.mktemp(suffix="_cites.csv")
pd.DataFrame({"reference_id": refs}).to_csv(refs_path, index=False)
citer_cites = pc[pc["citing_paper_id"].isin(citers)][
    ["citing_paper_id", "cited_paper_id"]
].head(5000)
citer_cites.to_csv(cites_path, index=False)
print(f"cites CSV: {len(citer_cites)} rows, {citer_cites['citing_paper_id'].nunique()} unique citers")

# Check data
print(f"Rows where cited_paper_id == {test_id}: {(citer_cites['cited_paper_id'] == test_id).sum()}")
print(f"First few rows:")
print(citer_cites.head(10))

# LLM
llm = load_llm_from_env()
prompt = get_prompt("disruption", paper_id=test_id, refs_path=refs_path, cites_path=cites_path)
print(f"\nPrompt ({len(prompt)} chars):")
print(prompt)
print()

response = llm.invoke([{"role": "user", "content": prompt}])
raw = str(response.content)
print(f"Raw response ({len(raw)} chars):")
print(raw[:1500])
print()

# Extract code
if "```python" in raw:
    code = raw.split("```python", 1)[1].split("```")[0].strip()
elif "```" in raw:
    code = raw.split("```", 1)[1].split("```")[0].strip()
else:
    code = raw.strip()

print("=== EXTRACTED CODE ===")
print(code)
print()

# Execute
result = execute_python(code, timeout=30)
print(f"exit_code={result['exit_code']}")
print(f"stdout: {result['stdout']}")
if result["stderr"]:
    print(f"stderr: {result['stderr'][:500]}")

parsed = parse_metric_output(result["stdout"], "disruption")
print(f"Parsed: {parsed}")
if "D_index" in parsed:
    print(f"D_computed={parsed['D_index']:.6f} vs D_gt={gt['D_index']:.6f}")
    print(f"n_i: computed={parsed.get('n_i')} vs gt={gt['n_i']}")
    print(f"n_j: computed={parsed.get('n_j')} vs gt={gt['n_j']}")
