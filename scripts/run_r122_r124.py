#!/usr/bin/env python3
"""R122-R124 batch driver — full Study 2 (IO1/IO2/IO3 x 20 papers x 2 models).

Drives (paper x model x IO) runs through the v7.2 agent loop with:
  - frozen v2 scorer + v1 weights/gates (refine-logs/r122_freeze/)
  - frozen PAPER_GOLD for 20 papers (refine-logs/r122_freeze/paper_gold.json)
  - isolated Docker execution (--network none, per-run workdir, no siblings)
  - process-evidence fields embedded in per-run JSON
  - concurrency (ThreadPoolExecutor for LLM + Docker)
  - run-id + NO overwrite (corrections via patch record, not silent edits)

Usage:
  python scripts/run_r122_r124.py --io 1 --concurrency 4            # R122 (IO1)
  python scripts/run_r122_r124.py --io 1 --paper petersen2024       # smoke test
  python scripts/run_r122_r124.py --io 1 --papers p1,p2 --models qwen3-32b
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, traceback, shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from sciscigpt_local.isolated_executor import execute_python_isolated  # noqa
import run_v72_pilot as pilot               # call_llm, parse_code, build_prompt_*
import ecrf_v2_scorer as v2                  # score_v2 + detection fns

# ── freeze: load 20-paper PAPER_GOLD into the v2 scorer (override 5-paper pilot gold) ──
FREEZE = ROOT / "refine-logs" / "r122_freeze"
PAPER_GOLD_20 = json.loads((FREEZE / "paper_gold.json").read_text())
v2.PAPER_GOLD = PAPER_GOLD_20          # frozen contract
pilot.PAPER_GOLD = PAPER_GOLD_20       # for build_prompt (not strictly needed)

PILOT_DIR = ROOT / "pilot"
PROXY = os.environ.get("LITELLM_PROXY", "http://127.0.0.1:4000/v1")
PROXY_KEY = os.environ.get("LITELLM_KEY", "sk-local-litellm")
IMAGE = os.environ.get("R097_IMAGE", "sciscigpt-ds:0.1")

MODELS = ["qwen3-32b", "deepseek-v4-pro"]
PAPERS = list(PAPER_GOLD_20.keys())

OUT_DIRS = {1: ROOT / "refine-logs" / "r122",
            2: ROOT / "refine-logs" / "r123",
            3: ROOT / "refine-logs" / "r124"}


def io_manifest_flags(paper_id, io):
    """Read frozen IO manifest: data_provided + ref_code_available for this paper/IO."""
    man = json.loads((FREEZE / "io_manifests.json").read_text())
    pkg = man["packages"].get(f"{paper_id}__io{io}", {})
    return bool(pkg.get("data_provided")), bool(pkg.get("ref_code_available"))


def unique_path(out_dir, paper, model, io):
    """No-overwrite: if base path exists, append _r2, _r3, ..."""
    base = out_dir / f"{paper}_{model}_io{io}"
    p = base.with_suffix(".json")
    if not p.exists():
        return p, base
    i = 2
    while (out_dir / f"{base.name}_r{i}.json").exists():
        i += 1
    return out_dir / f"{base.name}_r{i}.json", out_dir / f"{base.name}_r{i}"


def capture_process_evidence(paper_id, code, stdout, exec_ok, data_provided, ref_code_avail):
    """Embed the 6 process-evidence fields in the run record."""
    # real_data_used: agent loaded a raw_data file AND data was provided
    real_data_used = bool(v2.has_file_load(code or "")) and data_provided
    # ref_code_used: agent imported/adapted original_code (IO3 only meaningful)
    code_lc = (code or "").lower()
    ref_patterns = ["original_code", "import reproduce", "from reproduce", "reproduce_final",
                    "reproduce_v0", "cdindex_ref", "code_bursts", "reproduce_a0", "ccair", "respol_patents_code"]
    ref_code_used = ref_code_avail and any(p in code_lc for p in ref_patterns)
    # synthetic_generated
    synthetic_generated = bool(v2.uses_synthetic_data(code or ""))
    # paper_reported_copied (B2)
    try:
        paper_reported_copied, _ = v2.b2_circularity(code or "", stdout or "", paper_id)
    except Exception:
        paper_reported_copied = False
    # executable_code_generated
    executable_code_generated = code is not None and len(code) > 0
    # execution_succeeded
    execution_succeeded = bool(exec_ok)
    # result-line classification (for R125 audit)
    try:
        line_classes = v2.classify_result_lines_v2(code or "", stdout or "")
    except Exception:
        line_classes = []
    from collections import Counter
    cls_counts = dict(Counter(c for c, _ in line_classes))
    return {
        "real_data_used": real_data_used,
        "ref_code_used": ref_code_used,
        "synthetic_generated": synthetic_generated,
        "paper_reported_copied": paper_reported_copied,
        "executable_code_generated": executable_code_generated,
        "execution_succeeded": execution_succeeded,
        "result_line_classification": cls_counts,
        "n_result_lines": len(line_classes),
    }


def run_one(paper_id, model_key, io_level, run_idx):
    out_dir = OUT_DIRS[io_level]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path, base_path = unique_path(out_dir, paper_id, model_key, io_level)
    data_provided, ref_code_avail = io_manifest_flags(paper_id, io_level)

    io_dir = PILOT_DIR / paper_id / f"IO{io_level}"
    paper_md_path = io_dir / "paper.md"
    if not paper_md_path.exists():
        # fallback: IO1 paper.md is often shared across IO levels
        for alt_io in (1, 2, 3):
            ap = PILOT_DIR / paper_id / f"IO{alt_io}" / "paper.md"
            if ap.exists():
                paper_md_path = ap; break
    rec = {"run_id": f"r{run_idx}", "paper": paper_id, "model": model_key, "io": io_level,
           "image": IMAGE, "t_start": int(time.time()),
           "freeze": {"scorer": "ecrf_v2 frozen", "gold": "v1_r3", "data_provided": data_provided,
                      "ref_code_available": ref_code_avail},
           "out_path": str(out_path)}
    if not paper_md_path.exists():
        rec["error"] = f"missing paper.md for {paper_id} (assemble IO package first)"
        rec["status"] = "NO_PACKAGE"
        out_path.write_text(json.dumps(rec, indent=2, ensure_ascii=False))
        return rec
    paper_md = paper_md_path.read_text()

    # build prompt
    try:
        if io_level == 1:
            prompt = pilot.build_prompt_io1(paper_id, paper_md)
            data_files, ref_code_files = [], []
        elif io_level == 2:
            prompt, data_files = pilot.build_prompt_io2(paper_id, paper_md, io_dir)
            ref_code_files = []
        elif io_level == 3:
            prompt, data_files, ref_code_files = pilot.build_prompt_io3(paper_id, paper_md, io_dir)
        else:
            raise ValueError(f"IO{io_level}")
    except Exception as e:
        rec["error"] = f"prompt build failed: {e}"; rec["status"] = "PROMPT_FAIL"
        out_path.write_text(json.dumps(rec, indent=2, ensure_ascii=False)); return rec

    rec["io2_data_files"] = [p.name for p in data_files]
    rec["io3_ref_code_files"] = [p.name for p in ref_code_files]

    # LLM
    try:
        content, llm_meta = pilot.call_llm(model_key, prompt)
        rec["llm"] = llm_meta; rec["llm_response_chars"] = len(content)
        (out_dir / f"{base_path.name}_response.txt").write_text(content)
    except Exception as e:
        rec["error"] = f"LLM fail: {e}"; rec["status"] = "LLM_FAIL"
        out_path.write_text(json.dumps(rec, indent=2, ensure_ascii=False)); return rec

    code = pilot.parse_code(content)
    rec["code_parsed"] = code is not None
    if not code:
        rec["status"] = "NO_CODE"; out_path.write_text(json.dumps(rec, indent=2, ensure_ascii=False)); return rec

    # isolated execution — per-run workdir, pre-populate with IO2/IO3 materials only
    workdir = out_dir / f"ws_{base_path.name}"
    if workdir.exists(): shutil.rmtree(workdir)
    workdir.mkdir(parents=True); workdir.chmod(0o755)
    if io_level in (2, 3) and io_dir.exists():
        for p in io_dir.iterdir():
            if p.is_file() and p.name != "paper.md": shutil.copy2(p, workdir / p.name)
        if (io_dir / "raw_data").exists(): shutil.copytree(io_dir / "raw_data", workdir / "raw_data", dirs_exist_ok=True)
    if io_level == 3 and io_dir.exists() and (io_dir / "original_code").exists():
        shutil.copytree(io_dir / "original_code", workdir / "original_code", dirs_exist_ok=True)

    try:
        ex = execute_python_isolated(code, workdir, image=IMAGE, timeout=600)
        rec["exec"] = {"exit_code": ex["exit_code"], "elapsed": ex["elapsed"],
                       "network_blocked": ex["network_blocked"], "network_probe": ex.get("network_probe"),
                       "files_written": ex.get("files_written"),
                       "stdout_chars": len(ex["stdout"]), "stderr_chars": len(ex["stderr"])}
        rec["stdout"] = ex["stdout"][-8000:]; rec["stderr"] = ex["stderr"][-2000:]
        exec_ok = ex["exit_code"] == 0
    except Exception as e:
        rec["error"] = f"exec fail: {e}\n{traceback.format_exc()[-800:]}"; rec["status"] = "EXEC_FAIL"
        exec_ok = False; ex = {"stdout": "", "stderr": str(e)}

    rec["isolation"] = {"network_blocked": rec.get("exec", {}).get("network_blocked"),
                        "network_egress_blocked": rec.get("exec", {}).get("network_blocked") is True}

    # score with FROZEN v2
    try:
        rec["ecrf"] = v2.score_v2(paper_id, code, rec.get("stdout", ""), rec.get("stderr", ""), exec_ok, data_provided)
    except Exception as e:
        rec["ecrf_error"] = str(e)

    # process evidence
    rec["process_evidence"] = capture_process_evidence(paper_id, code, rec.get("stdout", ""),
                                                        exec_ok, data_provided, ref_code_avail)
    rec["status"] = "DONE" if exec_ok else "EXEC_NONZERO"
    rec["t_end"] = int(time.time())
    out_path.write_text(json.dumps(rec, indent=2, ensure_ascii=False))
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--io", type=int, required=True, choices=[1, 2, 3])
    ap.add_argument("--papers", default=None, help="comma-separated subset")
    ap.add_argument("--models", default=None, help="comma-separated subset")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--dry", action="store_true", help="list runs, don't execute")
    args = ap.parse_args()

    papers = args.papers.split(",") if args.papers else PAPERS
    models = args.models.split(",") if args.models else MODELS
    jobs = [(p, m, args.io) for p in papers for m in models]

    if args.dry:
        print(f"IO{args.io}: {len(jobs)} runs across {len(papers)} papers x {len(models)} models")
        for p, m, io in jobs:
            dp, rc = io_manifest_flags(p, io)
            pkg = PILOT_DIR / p / f"IO{io}"
            print(f"  {p:32s} {m:16s} data_provided={dp} ref_code={rc} paper_md={'Y' if (pkg/'paper.md').exists() else 'N'}")
        return

    out_dir = OUT_DIRS[args.io]; out_dir.mkdir(parents=True, exist_ok=True)
    print(f"R{120+args.io}: IO{args.io} — {len(jobs)} runs, concurrency={args.concurrency}")
    t0 = time.time()
    done = 0; results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(run_one, p, m, args.io, i+1): (p, m) for i, (p, m, _io) in enumerate(jobs)}
        for fut in as_completed(futs):
            p, m = futs[fut]
            try:
                rec = fut.result()
            except Exception as e:
                rec = {"paper": p, "model": m, "io": args.io, "status": "CRASH", "error": str(e)}
            done += 1
            ecrf = rec.get("ecrf", {}).get("final_ecrf") if isinstance(rec.get("ecrf"), dict) else None
            pe = rec.get("process_evidence", {})
            print(f"[{done}/{len(jobs)}] {p:30s} {m:16s} {rec.get('status'):12s} ecrf={ecrf} "
                  f"exec={pe.get('execution_succeeded')} realdata={pe.get('real_data_used')} "
                  f"synth={pe.get('synthetic_generated')} refcode={pe.get('ref_code_used')}", flush=True)
            results.append(rec)
    # aggregate
    agg = aggregate(results, args.io)
    (out_dir / f"r{120+args.io}_io{args.io}_aggregation.json").write_text(json.dumps(agg, indent=2, ensure_ascii=False))
    print(f"\nIO{args.io} done in {time.time()-t0:.0f}s. mean ECRF={agg.get('mean_ecrf')}. "
          f"n_done={agg.get('n_done')}/{len(jobs)}. agg -> {out_dir}/r{120+args.io}_io{args.io}_aggregation.json")


def aggregate(results, io):
    done = [r for r in results if r.get("ecrf")]
    ecrfs = [r["ecrf"]["final_ecrf"] for r in done]
    import statistics
    by_paper = {}
    for r in done:
        by_paper.setdefault(r["paper"], []).append(r["ecrf"]["final_ecrf"])
    by_model = {}
    for r in done:
        by_model.setdefault(r["model"], []).append(r["ecrf"]["final_ecrf"])
    n_exec = sum(1 for r in results if r.get("process_evidence", {}).get("execution_succeeded"))
    n_synth = sum(1 for r in results if r.get("process_evidence", {}).get("synthetic_generated"))
    n_realdata = sum(1 for r in results if r.get("process_evidence", {}).get("real_data_used"))
    n_refcode = sum(1 for r in results if r.get("process_evidence", {}).get("ref_code_used"))
    return {
        "io": io, "n_runs": len(results), "n_done": len(done),
        "mean_ecrf": round(statistics.mean(ecrfs), 3) if ecrfs else None,
        "by_paper": {k: round(statistics.mean(v), 3) for k, v in by_paper.items()},
        "by_model": {k: round(statistics.mean(v), 3) for k, v in by_model.items()},
        "process_evidence_totals": {"execution_succeeded": n_exec, "real_data_used": n_realdata,
                                     "synthetic_generated": n_synth, "ref_code_used": n_refcode},
    }


if __name__ == "__main__":
    main()
