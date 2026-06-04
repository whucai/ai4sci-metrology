#!/usr/bin/env python3
"""Test paper understanding module end-to-end.

Feeds Wu et al. (2019) paper text → extracts structure → formats plan → generates code.
This bridges the gap from "structured data" to "paper-based reproduction."
"""
import sys, os, re, json, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OPENAI_API_KEY", "not-needed")
os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
os.environ.setdefault("LLM_MAX_TOKENS", "8192")

from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.paper_ingestion import extract_paper_structure, format_analysis_plan
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.reproduction_pipeline import validate_generated_code


WU2019_ABSTRACT = """
Large teams develop and small teams disrupt science and technology.
Lingfei Wu, Dashun Wang, James A. Evans. Nature 566, 378-382 (2019).

Abstract: One of the most universal trends in science and technology today is the growth
of large teams in all areas, as solitary researchers and small teams diminish in prevalence.
Increases in team size have been attributed to the specialization of scientific activities,
improvements in communication technology, and the need for large-scale computation and data
collection. The shift toward large teams has spurred a rich policy debate about the viability
of different modes of scientific inquiry. Here we analyze more than 65 million papers, patents
and software products that span the period 1954-2014, and demonstrate across all three domains
that smaller teams tend to disrupt science and technology with new ideas and opportunities,
whereas larger teams tend to develop existing ones.

Methods: We use a citation-based measure called the Disruption Index (D-index), which
quantifies the degree to which a paper disrupts or consolidates existing knowledge.
D = (n_i - n_j) / (n_i + n_j + n_k), where n_i counts subsequent papers that cite the
focal paper but not its references, n_j counts papers that cite both, and n_k counts papers
that cite only the references. We compute D for 42 million papers in the Web of Science
database and link them to team size (number of authors).

We use the SciSciNet dataset containing citation relationships between papers.
The analysis computes the mean disruption score for small teams (1 author), medium teams
(2-5 authors), and large teams (>5 authors). We aggregate at the field level and year level
to verify robustness.

Key findings:
1. Small teams are more disruptive: mean D = 0.42 for solo-authored papers vs D = 0.21
   for papers with 10+ authors
2. This pattern holds across all 275 fields and all years (1954-2014)
3. Large teams are increasingly prevalent: from 5% to 38% of all papers
4. The effect is robust to alternative metrics and data sources

Data sources: Web of Science, USPTO, GitHub. The SciSciNet dataset provides the citation
graph and paper metadata for reproducible computation.

Analysis steps:
1. Load paper metadata and citation edges from SciSciNet
2. Compute Disruption Index for each paper using citation graph
3. Group papers by team size (1, 2-5, 6-10, 11+)
4. Compute mean D for each team-size group
5. Verify field-level trends: for each of 275 fields, is D higher for small teams?
6. Verify year-level trends: does the small-team advantage hold across 1954-2014?
7. Statistical testing: bootstrap confidence intervals, Cohen's d effect size
"""


def generate_code_from_plan(plan_text: str, llm) -> str:
    """Generate Python code to execute the analysis plan."""
    prompt = f"""You are a scientific code generator. Based on the following analysis plan
extracted from a paper, generate Python code to reproduce the analysis.

## Analysis Plan
{plan_text}

## Available Data
- SciSciNet dataset: `src.sciscigpt_local.sciscinet_connector.load_table(table_name)`
  - tables: papers, paper_citations, paper_fields, fields
- Papers columns: paper_id, year, author_count, disruption_score, citation_count, title
- Paper_citations: citing_paper_id, cited_paper_id
- Paper_fields: paper_id, field_id, normalized_citations

## Requirements
1. Write complete, runnable Python code
2. Use pandas and numpy
3. Include print() statements for all key results
4. Handle edge cases (missing data, division by zero)
5. Print results in format: METRIC_NAME = <value>

Output ONLY the Python code, nothing else."""

    response = llm.invoke([{"role": "user", "content": prompt}])
    text = str(response.content)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    match = re.search(r"```(?:python)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback
    code = text.strip()
    if code.startswith("```"):
        code = re.sub(r"^```(?:python)?\s*\n?", "", code)
        code = re.sub(r"\n?\s*```$", "", code)
    return code


def main():
    print("=" * 70)
    print("PAPER UNDERSTANDING MODULE — End-to-End Test")
    print("=" * 70)

    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}\n")

    # Step 1: Extract paper structure
    print("--- Step 1: Extract Paper Structure ---")
    structure = extract_paper_structure(WU2019_ABSTRACT, llm)
    if "error" in structure:
        print(f"  ERROR: {structure['error']}")
        print(f"  Raw: {structure.get('raw_extraction', '')[:500]}")
        return 1

    print(f"  Title: {structure.get('title', 'N/A')}")
    print(f"  Methods found: {len(structure.get('methods', []))}")
    print(f"  Datasets found: {len(structure.get('datasets', []))}")
    print(f"  Analysis steps: {len(structure.get('analysis_steps', []))}")
    print(f"  Dependencies: {structure.get('dependencies', [])}")
    print(f"  Expected metrics: {structure.get('evaluation', {}).get('metrics', [])}")

    # Step 2: Format analysis plan
    print("\n--- Step 2: Format Analysis Plan ---")
    plan = format_analysis_plan(structure)
    print(plan[:800])
    if len(plan) > 800:
        print(f"  ... ({len(plan)} chars total)")

    # Step 3: Generate code from plan
    print("\n--- Step 3: Generate Code from Plan ---")
    code = generate_code_from_plan(plan, llm)

    guard = validate_generated_code(code)
    print(f"  Code length: {len(code)} chars, {len(code.split(chr(10)))} lines")
    print(f"  Guardrail: valid={guard['valid']}, failures={guard['failures']}")

    if not guard["valid"]:
        print(f"  WARNING: Code may not be runnable. Failures: {guard['failures']}")
        # Try to fix: strip thinking tags
        code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL)
        guard2 = validate_generated_code(code)
        print(f"  After stripping: valid={guard2['valid']}, failures={guard2['failures']}")

    # Show code snippet
    print("\n  --- Generated Code (first 600 chars) ---")
    print(code[:600])

    # Step 4: Execute code in sandbox
    print("\n--- Step 4: Execute in Sandbox ---")
    result = execute_python(code, timeout=60)
    print(f"  Exit code: {result['exit_code']}")
    print(f"  Elapsed: {result['elapsed']}s")
    if result.get("environment"):
        print(f"  Python: {result['environment'].get('python_version', 'unknown')}")

    if result["exit_code"] == 0 and result["stdout"]:
        print("  --- Output ---")
        for line in result["stdout"].split("\n")[:20]:
            print(f"  {line}")
    elif result["stderr"]:
        # Check for actual errors
        error_keywords = ["Traceback", "Error:", "Exception"]
        has_error = any(k in result["stderr"] for k in error_keywords)
        print(f"  Has error: {has_error}")
        if has_error:
            print(f"  --- Stderr (first 400 chars) ---")
            print(result["stderr"][:400])

    # Save results
    out = {
        "structure": structure,
        "plan_length": len(plan),
        "code_length": len(code),
        "guardrail": guard,
        "execution": {
            "exit_code": result["exit_code"],
            "elapsed": result["elapsed"],
            "stdout_preview": result["stdout"][:500],
        },
    }
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "paper_understanding_test.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved to {out_path}")

    success = result["exit_code"] == 0 and len(result["stdout"]) > 50
    print(f"\nOverall: {'SUCCESS' if success else 'NEEDS WORK'}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
