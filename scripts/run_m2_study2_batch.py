#!/usr/bin/env python3
"""M2 Study-2 full batch runner (v8.1) — 20 papers x 3 IO x 2 models = 120 runs.

Engine layer over scripts/run_v72_pilot.py:
  - Routes Qwen3-32B to the DIRECT vLLM endpoint (LiteLLM proxy is down),
    DeepSeek-V4-Pro to the DeepSeek API (requires DEEPSEEK_API_KEY).
  - Loads the frozen R121 gold chain (r121_gold_v1_frozen.json) as the
    human ground-truth target; the automated scorer (v0/v2) still uses
    run_v72_pilot.PAPER_GOLD keyword signals — papers without keyword gold
    are flagged and skipped (engine does not fabricate signals).
  - Batch loop over (paper, io, model); per-run JSON to refine-logs/r122/.
  - Isolation via sciscigpt-ds:0.1, --network none (R097).

Usage:
  python scripts/run_m2_study2_batch.py --smoke          # 1 run (petersen2024, qwen3-32b, io1)
  python scripts/run_m2_study2_batch.py --paper petersen2024 --io 1 --model qwen3-32b
  python scripts/run_m2_study2_batch.py --full           # all 120 (requires IO packages + gold for 20)
  python scripts/run_m2_study2_batch.py --full --io 1    # all papers x io1 x 2 models
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

# Import the per-run engine (prompt builders, isolated executor, v0 scorer, run_one)
import run_v72_pilot as pilot
from run_v72_pilot import run_one, MODELS

GOLD_FROZEN = ROOT / "refine-logs" / "r121_gold_v1_frozen.json"
OUT_DIR = Path(os.environ.get("R122_OUTPUT_DIR", str(ROOT / "refine-logs" / "r122")))

# Per-model vLLM backends (direct; LiteLLM proxy is down).
# Qwen3.6-27B-FP8 is up on .41:8360 (and .42:8360). Gemma-4-31B-IT should be
# on .43:8008 but is currently connection-refused — start that server to use it.
BACKENDS = {
    "qwen3-32b":   {"base_url": os.environ.get("QWEN3_URL", "http://172.17.65.41:8360/v1"),
                    "model": os.environ.get("QWEN3_MODEL", "qwen3.6-27b-fp8")},
    "gemma-4-31b": {"base_url": os.environ.get("GEMMA_URL", "http://172.17.65.43:8008/v1"),
                    "model": os.environ.get("GEMMA_MODEL", "gemma-4-31b-it")},
}
# register gemma in MODELS if absent
MODELS.setdefault("gemma-4-31b", {"proxy_model": "gemma-4-31b-it", "max_tokens": 16000, "temperature": 0.2})


def _probe(url: str) -> bool:
    import urllib.request
    try:
        urllib.request.urlopen(url + "/models", timeout=4)
        return True
    except Exception:
        return False


def reroute_backends() -> list:
    """Override pilot.call_llm with a per-model router. Returns list of live model keys."""
    live = []
    for k, b in BACKENDS.items():
        if _probe(b["base_url"]):
            live.append(k)
        else:
            print(f"[backend] {k} @ {b['base_url']} NOT reachable — skipping its runs.")
    MODELS["qwen3-32b"]["proxy_model"] = BACKENDS["qwen3-32b"]["model"]
    MODELS["gemma-4-31b"]["proxy_model"] = BACKENDS["gemma-4-31b"]["model"]

    from openai import OpenAI

    def call_llm(model_key: str, prompt: str) -> tuple:
        b = BACKENDS[model_key]
        cfg = MODELS[model_key]
        client = OpenAI(base_url=b["base_url"], api_key="sk-vllm-local", timeout=600)
        t0 = time.time()
        resp = client.chat.completions.create(
            model=cfg["proxy_model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=cfg["max_tokens"],
            temperature=cfg["temperature"],
        )
        msg = resp.choices[0].message
        content = msg.content or ""
        meta = {"model": cfg["proxy_model"], "base_url": b["base_url"],
                "elapsed": round(time.time() - t0, 1),
                "usage": {"completion": getattr(resp.usage, "completion_tokens", None),
                          "prompt": getattr(resp.usage, "prompt_tokens", None)},
                "finish": resp.choices[0].finish_reason, "n_content_chars": len(content)}
        return content, meta

    pilot.call_llm = call_llm  # monkeypatch the per-run engine's LLM call
    return live


def load_frozen_gold() -> dict:
    if not GOLD_FROZEN.exists():
        print(f"[gold] frozen gold not found at {GOLD_FROZEN}; running without ground-truth target.")
        return {}
    d = json.loads(GOLD_FROZEN.read_text())
    papers = d.get("papers", d) if isinstance(d, dict) else d
    if isinstance(papers, dict):
        papers = papers.values()
    return {p["paper_id"]: p for p in papers}


def paper_has_inputs(pid: str) -> tuple[bool, str]:
    """Check IO package + keyword gold exist for a paper."""
    io_pkg = ROOT / "pilot" / pid
    has_pkg = io_pkg.exists()
    has_kwgold = pid in pilot.PAPER_GOLD
    if not has_pkg:
        return False, f"no IO package at pilot/{pid}"
    if not has_kwgold:
        return False, f"no keyword gold in PAPER_GOLD (only {sorted(pilot.PAPER_GOLD)})"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="1 run: petersen2024 qwen3-32b io1")
    ap.add_argument("--paper")
    ap.add_argument("--papers", help="comma-separated paper slugs to include (with --full)")
    ap.add_argument("--io", type=int, choices=[1, 2, 3])
    ap.add_argument("--model", choices=list(MODELS))
    ap.add_argument("--full", action="store_true", help="all ready (paper x io x model) combos")
    ap.add_argument("--skip-existing", action="store_true", help="skip runs whose _result.json already exists and is DONE")
    ap.add_argument("--dry-run", action="store_true", help="list what would run, then exit")
    args = ap.parse_args()

    live_models = reroute_backends()
    gold = load_frozen_gold()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build the run list
    if args.smoke:
        runs = [("petersen2024", 1, "qwen3-32b")]
    elif args.paper:
        runs = [(args.paper, args.io or 1, args.model or "qwen3-32b")]
    elif args.full:
        papers = sorted(gold.keys()) if gold else sorted(pilot.PAPER_GOLD)
        if args.papers:
            want = {p.strip() for p in args.papers.split(",")}
            papers = [p for p in papers if p in want]
        ios = [args.io] if args.io else [1, 2, 3]
        models = [m for m in MODELS if m in live_models]
        runs = [(p, io, m) for p in papers for io in ios for m in models]
    else:
        ap.error("specify --smoke, --paper, or --full")
    # filter smoke/single to live model
    runs = [(p, io, m) for (p, io, m) in runs if m in live_models or not live_models]

    # Filter to ready runs
    ready, blocked = [], []
    for p, io, m in runs:
        ok, why = paper_has_inputs(p)
        # IO2/IO3 need the io{io} subdir in the pilot package; run_one checks internally.
        if ok or (io == 1 and (ROOT / "pilot" / p).exists()):
            ready.append((p, io, m))
        else:
            blocked.append((p, io, m, why))

    # Skip existing DONE runs if requested
    if args.skip_existing:
        fresh = []
        for p, io, m in ready:
            out = OUT_DIR / f"ws_{p}_{m}_io{io}" / "_result.json"
            if out.exists():
                try:
                    if json.loads(out.read_text()).get("status") == "DONE":
                        continue
                except Exception:
                    pass
            fresh.append((p, io, m))
        ready = fresh

    print(f"[plan] {len(ready)} ready, {len(blocked)} blocked")
    for b in blocked[:10]:
        print(f"  BLOCKED {b[0]} io{b[1]} {b[2]}: {b[3]}")
    if args.dry_run:
        for r in ready:
            print(f"  RUN {r[0]} io{r[1]} {r[2]}")
        return

    # Execute
    t0 = time.time()
    for i, (p, io, m) in enumerate(ready, 1):
        out = OUT_DIR / f"ws_{p}_{m}_io{io}"
        out.mkdir(parents=True, exist_ok=True)
        pilot.OUTPUT_DIR = out  # run_one reads the module global at call time
        print(f"\n[{i}/{len(ready)}] {p} io{io} {m} -> {out}")
        try:
            rec = run_one(p, m, io)
            rec["r122_batch"] = True
            rec["gold_target"] = gold.get(p, {}).get("components", {})
            (out / "_result.json").write_text(json.dumps(rec, indent=2, default=str))
            ecrf = rec.get("ecrf", {}).get("overall_ecrf")
            print(f"  status={rec.get('status')} ecrf(v0)={ecrf}")
        except Exception as e:
            print(f"  ERROR: {e}")
    print(f"\n[done] {len(ready)} runs in {round(time.time()-t0,1)}s -> {OUT_DIR}")


if __name__ == "__main__":
    main()
