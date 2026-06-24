#!/usr/bin/env python3
"""Debug L2 code generation failures."""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["OPENAI_API_KEY"] = "not-needed"
os.environ["OPENAI_BASE_URL"] = "http://172.17.65.41:8032/v1"
os.environ["LLM_MODEL"] = "/public/data_share/model_hub/Qwen3-32B/"

import pandas as pd
from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.metric_templates import compute_ground_truth, parse_metric_output
from src.sciscigpt_local.sandbox import execute_python


def _extract_code(text):
    if "```python" in text:
        return text.split("```python", 1)[1].split("```")[0].strip()
    if "```" in text:
        return text.split("```", 1)[1].split("```")[0].strip()
    return text.strip()


papers_df = load_table("papers")
pc = load_table("paper_citations")
llm = load_llm_from_env()

# Test a specific L2 case
paper_title = "A Dynamic Network Measure of Technological Change"
test_id = 2166706824
test_row = papers_df[papers_df["paper_id"] == test_id].iloc[0]
test_title = str(test_row.get("title", ""))[:100]

gt = compute_ground_truth("disruption", test_id, papers_df, pc)
print(f"GT: D={gt['D_index']}, n_i={gt['n_i']}, n_j={gt['n_j']}")

refs = pc[pc["citing_paper_id"] == test_id]["cited_paper_id"].unique()
citers = pc[pc["cited_paper_id"] == test_id]["citing_paper_id"].unique()
refs_path = tempfile.mktemp(suffix="_refs.csv")
cites_path = tempfile.mktemp(suffix="_cites.csv")
pd.DataFrame({"reference_id": refs}).to_csv(refs_path, index=False)
citer_cites = pc[pc["citing_paper_id"].isin(citers)][
    ["citing_paper_id", "cited_paper_id"]
].head(100000)
citer_cites.to_csv(cites_path, index=False)

# Current L2 prompt (has formula leak)
l2_prompt = f"""Read about this methodology:
{paper_title}

Task: Compute the disruption index (D-index) for test paper {test_id}: "{test_title}"

The disruption index D = (n_i - n_j) / (n_i + n_j) where:
- n_i = number of citing papers that cite the focal paper but NOT its references
- n_j = number of citing papers that cite BOTH the focal paper and at least one of its references

Data files:
- References CSV at '{refs_path}': papers cited BY test paper {test_id}
- Citation network CSV at '{cites_path}': papers that cite test paper {test_id} and their references

Print 'D_INDEX = <value>' plus 'n_i = <value>', 'n_j = <value>'.
"""

print(f"\nL2 Prompt ({len(l2_prompt)} chars):")
print(l2_prompt[:500])
print("...")

response = llm.invoke([{"role": "user", "content": l2_prompt}])
raw = str(response.content)
print(f"\nRaw response ({len(raw)} chars):")
print(raw[:1000])

code = _extract_code(raw)
print(f"\nExtracted code ({len(code)} chars):")
print(code[:800])

# Execute
for attempt in range(4):
    result = execute_python(code, timeout=30)
    print(f"\nAttempt {attempt+1}: exit={result['exit_code']}, stdout_len={len(result['stdout'])}, stderr_len={len(result['stderr'])}")
    if result["stdout"]:
        print(f"  stdout: {result['stdout'][:500]}")
    if result["stderr"]:
        print(f"  stderr: {result['stderr'][:500]}")

    has_traceback = "Traceback (most recent call last)" in result.get("stderr", "")
    is_error = result["exit_code"] != 0 or has_traceback

    if not is_error:
        parsed = parse_metric_output(result["stdout"], "disruption")
        if "D_index" in parsed:
            print(f"  SUCCESS: D={parsed['D_index']} gt={gt['D_index']}")
            break

    if attempt < 3:
        error_text = result.get("stderr") or result["stdout"]
        fix_prompt = f"""Your Python code for "Disruption Index (D)" produced this error:

```
{error_text[:800]}
```

Your previous code:
```python
{code[:2000]}
```

Fix the error. Output ONLY the corrected Python code in a ```python block.
The code must print results as: D_INDEX = <value>
"""
        print(f"  Asking LLM to fix...")
        response = llm.invoke([{"role": "user", "content": fix_prompt}])
        code = _extract_code(str(response.content))
        print(f"  New code ({len(code)} chars)")
