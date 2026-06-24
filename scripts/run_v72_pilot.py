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
OUTPUT_DIR = ROOT / "refine-logs" / "r100"
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

    prompt = build_prompt_io1(paper_id, paper_md) if io_level == 1 else None
    assert prompt, "only IO1 implemented in this runner"

    rec = {"paper": paper_id, "model": model_key, "io": io_level, "image": IMAGE, "t_start": int(time.time())}

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

    # 3. isolated execution
    workdir = OUTPUT_DIR / f"ws_{paper_id}_{model_key}_io{io_level}"
    workdir.mkdir(parents=True, exist_ok=True)
    workdir.chmod(0o755)
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
