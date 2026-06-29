#!/usr/bin/env python3
"""v7.2 mini-Study-2 runner (Evidence-Chain Theory).

Drives ONE (paper × model × IO-level) run through the v7.2 agent loop:
  1. Load the paper's IO package (IO₁ = paper.md only; no code/data).
  2. Prompt the LLM to reproduce the analysis as a self-contained Python script.
  3. Execute the generated code in the isolated no-network container
     (sciscigpt-ds:0.1, --network none, filesystem jail).
  4. Score per-component ECRF against the paper's gold chain (rules-based v0).
  5. Emit a structured JSON result + audit (isolation, leakage, schema).

This is the DRY-RUN / R100 runner. R101/R102 (IO₂/IO₃) are NOT launched here.

Usage:
  python scripts/run_v72_pilot.py --paper petersen2024 --model qwen3-32b --io 1
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sciscigpt_local.isolated_executor import execute_python_isolated  # noqa: E402

PILOT_DIR = ROOT / "pilot"
OUTPUT_DIR = Path(os.environ.get("R100_OUTPUT_DIR", str(ROOT / "refine-logs" / "r100")))
PROXY = os.environ.get("LITELLM_PROXY", "http://127.0.0.1:4000/v1")
PROXY_KEY = os.environ.get("LITELLM_KEY", "sk-local-litellm")
IMAGE = os.environ.get("R097_IMAGE", "sciscigpt-ds:0.1")

# ── model config ────────────────────────────────────────────────────────────
MODELS = {
    "qwen3-32b":   {"proxy_model": "qwen3-32b",      "max_tokens": 16000, "temperature": 0.2},
    "deepseek-v4-pro": {"proxy_model": "deepseek-v4-pro", "max_tokens": 16000, "temperature": 0.2},
    "glm-5.2":     {"proxy_model": "glm-5.2",         "max_tokens": 16000, "temperature": 0.2},
}

# ── paper gold-chain signals (from R098) for rules-based ECRF v0 ────────────
PAPER_GOLD = {
    "petersen2024": {
        "domain": "SoS", "task": "STRICT",
        "data_source": ["sciscinet", "web of science", "wos", "microsoft academic", "mag"],
        "sample": ["469,855", "469855", "102,550", "102550", "2011", "2015"],
        "indicator": ["disruption", "(ni", "n_j", "n_i", "cd", "abs("],
        "model": ["ols", "year fe", "fixed effect", "reference_count", "ln_rp", "ln_kp", "citation_inflation"],
        "result": ["-0.002322", "-0.00232", "-0.0023", "0.120403", "0.1204"],
        "claim": ["citation inflation", "biased", "downward", "negative", "decline"],
    },
    "arts2021": {
        "domain": "IS", "task": "METHOD",
        "data_source": ["uspto", "patent"],
        "sample": ["patent claim", "preprocess"],
        "indicator": ["novelty", "cosine", "tf", "n-gram", "indicator"],
        "model": ["descriptive", "aggregat"],
        "result": [],
        "claim": ["structure of innovation", "novelty", "reuse"],
    },
    "funk2017": {
        "domain": "Mgmt", "task": "STRICT",
        "data_source": ["nber", "dataverse", "uspto", "patent"],
        "sample": ["2.9 million", "2,900,000", "1977", "2005", "utility patent"],
        "indicator": ["cdt", "cd5", "mcdt", "mcd5", "n1", "n3", "destabil", "consolid"],
        "model": ["ols", "negative binomial", "regression"],
        "result": ["0.07", "0.23", "0.31", "1.75"],
        "claim": ["destabiliz", "consolid", "commercial engagement", "federal"],
    },
    "maddi2024": {
        "domain": "SoS", "task": "STRICT-DS",
        "data_source": ["publons", "web of science", "wos"],
        "sample": ["57,482", "57482", "2009", "2020", "947"],
        "indicator": ["report length", "word count", "reviewer", "iqr", "fisher"],
        "model": ["glm", "log(1", "log1p", "generalized linear", "log-link", "log_link"],
        "result": ["947", "positive"],
        "claim": ["longer", "more citations", "positive", "threshold"],
    },
    "bikard2013": {
        "domain": "Mgmt", "task": "DATA-SUB",
        "data_source": ["mit", "661", "faculty", "isi"],
        "sample": ["661", "5,964", "5964", "1976", "2006", "seven department"],
        "indicator": ["coauthor", "collaboration", "group size", "nauthors", "credit"],
        "model": ["ols", "fixed effect", "department-year", "career", "clustered"],
        "result": ["0.099", "-0.069", "0.099", "5.4", "9.6"],
        "claim": ["collaboration", "credit", "tradeoff", "free-rid"],
    },
    "wu2019_teams": {
        "domain": "SoS", "task": "STRICT",
        "data_source": ["sciscinet", "microsoft academic", "mag", "uspto", "patent", "software", "openalex"],
        "sample": ["65 million", "65,000,000", "1954", "2014", "40,000", "40000", "team size"],
        "indicator": ["disruption", "cd", "destabiliz", "consolid", "disrupt"],
        "model": ["mann", "whitney", "mean", "team size", "regression", "log"],
        "result": ["positive", "higher", "small", "large"],
        "claim": ["small teams", "disrupt", "large teams", "develop", "new ideas", "existing"],
    },
}


def call_llm(model_key: str, prompt: str) -> tuple[str, dict]:
    """Call the model via the LiteLLM proxy. Returns (content, meta)."""
    from openai import OpenAI
    cfg = MODELS[model_key]
    client = OpenAI(base_url=PROXY, api_key=PROXY_KEY, timeout=600)
    t0 = time.time()
    resp = client.chat.completions.create(
        model=cfg["proxy_model"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=cfg["max_tokens"],
        temperature=cfg["temperature"],
    )
    msg = resp.choices[0].message
    content = msg.content or ""
    meta = {
        "model": cfg["proxy_model"],
        "elapsed": round(time.time() - t0, 1),
        "usage": {"completion": getattr(resp.usage, "completion_tokens", None),
                  "prompt": getattr(resp.usage, "prompt_tokens", None)},
        "finish": resp.choices[0].finish_reason,
        "n_content_chars": len(content),
    }
    return content, meta


def parse_code(response: str) -> str | None:
    """Extract the last fenced python code block, else whole text if it looks like code."""
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", response, re.DOTALL)
    if blocks:
        return blocks[-1]
    # fallback: text that starts with import/def
    if re.search(r"^(import |from |def )", response, re.MULTILINE):
        return response
    return None


def build_prompt_io1(paper_id: str, paper_md: str) -> str:
    return f"""You are reproducing the quantitative analysis of a scientific paper.

You have ONLY the paper text below — NO external data, NO original code, NO internet access.
Write ONE self-contained Python script that reproduces the paper's main quantitative analysis.

Rules:
- If the required dataset is not contained in the paper, write the data-loading code as a clearly-marked STUB that documents exactly what data would be needed (source, schema, key columns) and constructs a small synthetic/placeholder frame with the documented schema so the script still runs end-to-end.
- Implement every indicator/formula and model specification described in the paper.
- Print every key numerical result with a clear label, e.g.  print("RESULT coef_ln_rp = ...").
- Print the final conclusion/direction the analysis supports.
- Do NOT hard-code the paper's reported numbers as if computed; if you must use them for comparison, label them as PAPER_REPORTED.
- Output only the Python script in one ```python block.

PAPER ({paper_id}):
\"\"\"
{paper_md[:60000]}
\"\"\"
"""


def build_prompt_io2(paper_id: str, paper_md: str, io2_dir: Path) -> tuple[str, list[Path]]:
    """IO₂ prompt: paper + structured docs + controlled raw data (where provided), NO original code."""
    import shutil
    docs, data_files = [], []
    for p in sorted(io2_dir.iterdir()):
        if p.suffix == ".md" and p.name != "paper.md":
            docs.append(f"### {p.name}\n\n{p.read_text()}")
    raw = io2_dir / "raw_data"
    if raw.exists():
        for p in sorted(raw.iterdir()):
            if p.suffix in (".parquet", ".csv", ".tsv", ".json"):
                data_files.append(p)
    docs_block = "\n\n".join(docs) if docs else "(no structured docs provided)"
    data_block = (f"raw_data/ contains: {', '.join(p.name for p in data_files)} (available at /workspace/raw_data/ inside the execution environment)"
                  if data_files else "NO raw data file is provided (data unavailable — see data dictionary).")
    prompt = f"""You are reproducing the quantitative analysis of a scientific paper.

You have (IO₂ condition):
  1. The paper text (below).
  2. Structured documentation: data dictionary + sample notes + indicator definitions (below).
  3. Controlled raw data files in raw_data/ (listed below) — available at /workspace/raw_data/ at runtime.
NO original code is provided. You must write your own.

Rules:
- Load the provided raw_data file(s) from /workspace/raw_data/ (use pandas). If no raw data is provided, document what is needed and clearly mark any synthetic/placeholder data as SYNTHETIC — do NOT present synthetic numbers as reproduction results.
- Implement every indicator/formula and model specification from the paper.
- Print every key numerical result with a clear label: print("RESULT <name> = <value>"). Label paper-reported comparison values as PAPER_REPORTED. If you use a substitute dataset (not the paper's original), label those results as DATA_SUB.
- Print the final conclusion/direction.
- Output only ONE Python script in a ```python block.

PAPER ({paper_id}):
\"\"\"
{paper_md[:50000]}
\"\"\"

STRUCTURED DOCUMENTATION:
{docs_block}

RAW DATA:
{data_block}
"""
    return prompt, data_files


def build_prompt_io3(paper_id: str, paper_md: str, io3_dir: Path) -> tuple[str, list[Path], list[Path]]:
    """IO₃ prompt: paper + docs + raw data + original/reference code (highest observability)."""
    docs, data_files, code_files = [], [], []
    for p in sorted(io3_dir.iterdir()):
        if p.is_file() and p.name != "paper.md":
            docs.append(f"### {p.name}\n\n{p.read_text()[:6000]}")
    raw = io3_dir / "raw_data"
    if raw.exists():
        for p in sorted(raw.iterdir()):
            if p.suffix in (".parquet", ".csv", ".tsv", ".json"):
                data_files.append(p)
    oc = io3_dir / "original_code"
    if oc.exists():
        for p in sorted(oc.iterdir()):
            if p.suffix in (".py", ".R", ".jl", ".do"):
                code_files.append(p)
    docs_block = "\n\n".join(docs) if docs else "(no structured docs)"
    data_block = (f"raw_data/ contains: {', '.join(p.name for p in data_files)} (at /workspace/raw_data/)"
                  if data_files else "NO raw data file (data unavailable).")
    code_block = (f"original_code/ contains: {', '.join(p.name for p in code_files)} (at /workspace/original_code/)"
                  if code_files else "NO original code (boundary case — write your own).")
    prompt = f"""You are reproducing the quantitative analysis of a scientific paper.

You have (IO₃ condition — highest observability):
  1. The paper text (below).
  2. Structured documentation (data dictionary, sample notes, indicator defs — below).
  3. Raw data files in raw_data/ (at /workspace/raw_data/ at runtime).
  4. Original/reference code in original_code/ (at /workspace/original_code/ at runtime) — you may study, run, or adapt it.

Rules:
- You MAY import or execute the reference code from /workspace/original_code/, or adapt it. Document whether you used it as-is, modified it, or wrote your own.
- Load raw_data and reproduce the paper's numerical results.
- Print every key result with a label: print("RESULT <name> = <value>"). Label paper-reported comparison values as PAPER_REPORTED. Do NOT embed paper-reported numbers as if computed.
- If you synthesize/placeholder any data despite real materials being available, label those outputs SYNTHETIC.
- Print the final conclusion/direction.
- Output only ONE Python script in a ```python block.

PAPER ({paper_id}):
\"\"\"
{paper_md[:45000]}
\"\"\"

DOCUMENTATION:
{docs_block}

RAW DATA:
{data_block}

REFERENCE CODE:
{code_block}
"""
    return prompt, data_files, code_files


def score_ecrf(paper_id: str, code: str, stdout: str, stderr: str, exec_ok: bool) -> dict:
    """Rules-based v0 ECRF scorer. Returns per-component 0/0.5/1.0 + rationale."""
    gold = PAPER_GOLD.get(paper_id, {})
    blob = (code or "").lower() + "\n" + (stdout or "").lower()
    comp = {}
    for component in ["data_source", "sample", "indicator", "model", "result", "claim"]:
        signals = gold.get(component, [])
        if not signals:
            comp[component] = {"score": 0.0, "rationale": "no gold signals for this component"}
            continue
        hits = [s for s in signals if s.lower() in blob]
        if len(hits) >= max(2, len(signals) // 3):
            sc, note = 1.0, f"strong: {hits}"
        elif hits:
            sc, note = 0.5, f"partial: {hits}"
        else:
            sc, note = 0.0, "no gold signal matched"
        # Result component additionally requires actual execution success
        if component == "result" and not exec_ok:
            sc = min(sc, 0.25)
            note += " | execution failed/skipped → capped"
        comp[component] = {"score": sc, "rationale": note}
    applicable = [c for c in comp]
    overall = round(sum(comp[c]["score"] for c in applicable) / len(applicable), 3)
    return {"components": comp, "overall_ecrf": overall}


def run_one(paper_id: str, model_key: str, io_level: int) -> dict:
    io_dir = PILOT_DIR / paper_id / f"IO{io_level}"
    paper_md_path = io_dir / "paper.md"
    assert paper_md_path.exists(), f"missing {paper_md_path}"
    paper_md = paper_md_path.read_text()

    if io_level == 1:
        prompt = build_prompt_io1(paper_id, paper_md)
        data_files, ref_code_files = [], []
    elif io_level == 2:
        prompt, data_files = build_prompt_io2(paper_id, paper_md, io_dir)
        ref_code_files = []
    elif io_level == 3:
        prompt, data_files, ref_code_files = build_prompt_io3(paper_id, paper_md, io_dir)
    else:
        raise NotImplementedError("only IO1/IO2/IO3 implemented in this runner")

    rec = {"paper": paper_id, "model": model_key, "io": io_level, "image": IMAGE, "t_start": int(time.time()),
           "io2_data_files": [p.name for p in data_files],
           "io3_ref_code_files": [p.name for p in ref_code_files]}

    # 1. LLM call
    try:
        content, llm_meta = call_llm(model_key, prompt)
        rec["llm"] = llm_meta
        rec["llm_response_chars"] = len(content)
        Path(OUTPUT_DIR / f"{paper_id}_{model_key}_io{io_level}_response.txt").write_text(content)
    except Exception as e:
        rec["error"] = f"LLM call failed: {e}"
        rec["status"] = "LLM_FAIL"
        return rec

    # 2. parse code
    code = parse_code(content)
    rec["code_parsed"] = code is not None
    if not code:
        rec["error"] = "no code block parsed from response"
        rec["status"] = "NO_CODE"
        return rec

    # 3. isolated execution — pre-populate workdir with IO₂/IO₃ docs + raw_data (+ original_code for IO₃)
    workdir = OUTPUT_DIR / f"ws_{paper_id}_{model_key}_io{io_level}"
    if workdir.exists():
        import shutil
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    workdir.chmod(0o755)
    if io_level in (2, 3):
        import shutil
        # copy docs (all files, non-paper.md, non-dir) and raw_data into the per-run workdir
        for p in io_dir.iterdir():
            if p.is_file() and p.name != "paper.md":
                shutil.copy2(p, workdir / p.name)
        if (io_dir / "raw_data").exists():
            shutil.copytree(io_dir / "raw_data", workdir / "raw_data", dirs_exist_ok=True)
    if io_level == 3:
        import shutil
        if (io_dir / "original_code").exists():
            shutil.copytree(io_dir / "original_code", workdir / "original_code", dirs_exist_ok=True)
    try:
        ex = execute_python_isolated(code, workdir, image=IMAGE, timeout=600)
        rec["exec"] = {
            "exit_code": ex["exit_code"], "elapsed": ex["elapsed"],
            "network_blocked": ex["network_blocked"],
            "network_probe": ex.get("network_probe"),
            "files_written": ex.get("files_written"),
            "stdout_chars": len(ex["stdout"]), "stderr_chars": len(ex["stderr"]),
        }
        rec["stdout"] = ex["stdout"][-8000:]
        rec["stderr"] = ex["stderr"][-2000:]
        exec_ok = ex["exit_code"] == 0
    except Exception as e:
        rec["error"] = f"execution failed: {e}\n{traceback.format_exc()[-1000:]}"
        rec["status"] = "EXEC_FAIL"
        ex = {"stdout": "", "stderr": str(e)}
        exec_ok = False

    # 4. isolation assertions
    rec["isolation"] = {
        "network_blocked": rec.get("exec", {}).get("network_blocked"),
        "network_egress_ok": rec.get("exec", {}).get("network_blocked") is True,
    }

    # 5. ECRF score
    rec["ecrf"] = score_ecrf(paper_id, code, rec.get("stdout", ""), rec.get("stderr", ""), exec_ok)
    rec["status"] = "DONE" if exec_ok else "EXEC_NONZERO"
    rec["t_end"] = int(time.time())
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", required=True)
    ap.add_argument("--model", required=True, choices=list(MODELS))
    ap.add_argument("--io", type=int, default=1)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rec = run_one(args.paper, args.model, args.io)
    out_path = Path(args.out) if args.out else OUTPUT_DIR / f"{args.paper}_{args.model}_io{args.io}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rec, indent=2, ensure_ascii=False))
    print(json.dumps({"paper": rec["paper"], "model": rec["model"], "io": rec["io"],
                      "status": rec.get("status"), "ecrf": rec.get("ecrf", {}).get("overall_ecrf"),
                      "isolation": rec.get("isolation"), "out": str(out_path)}, indent=2))


if __name__ == "__main__":
    main()
