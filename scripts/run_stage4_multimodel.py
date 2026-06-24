#!/usr/bin/env python3
"""Multi-model Stage 4 benchmark runner.

Runs the Stage 4 conclusion-evidence judgment task across multiple LLMs
and compares their judgment quality.
"""

import sys, os, json, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscigpt_local.llm_backends import LLMConfig, load_llm_from_config

# Import Stage 4 components
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_stage4_benchmark import (
    PAPER_CLAIMS, build_stage4_prompt, parse_stage4_response, summarize,
)


def get_available_models() -> list[dict]:
    """Discover available models from environment.

    Returns list of {name, provider, model, config} dicts.
    """
    models = []

    # Qwen3-32B via local vLLM
    models.append({
        "name": "Qwen3-32B",
        "provider": "openai",
        "model": "/public/data_share/model_hub/Qwen3-32B/",
        "config": LLMConfig(
            name="qwen3-32b", provider="openai",
            model="/public/data_share/model_hub/Qwen3-32B/",
            api_key="not-needed",
            base_url="http://172.17.65.41:8032/v1",
            temperature=0.0, max_tokens=4096,
        ),
    })

    # DeepSeek-V4-Pro via Anthropic-compatible API
    anthro_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if anthro_key:
        models.append({
            "name": "DeepSeek-V4-Pro",
            "provider": "anthropic",
            "model": "deepseek-v4-pro",
            "config": LLMConfig(
                name="deepseek-v4-pro", provider="anthropic",
                model="deepseek-v4-pro",
                api_key=anthro_key,
                base_url=os.environ.get("ANTHROPIC_BASE_URL", ""),
                temperature=0.0, max_tokens=4096,
            ),
        })

    return models


def run_stage4_for_model(model_info: dict, stage2_results_path: str,
                         max_tasks: int | None = None,
                         output_dir: str = "refine-logs") -> dict:
    """Run Stage 4 benchmark for a single model."""
    from run_stage4_benchmark import _run_stage4_task

    print(f"\n{'='*60}")
    print(f"Model: {model_info['name']} ({model_info['provider']}:{model_info['model']})")

    llm = load_llm_from_config(model_info["config"])
    model_name = model_info["name"]

    with open(stage2_results_path) as f:
        stage2_data = json.load(f)
    stage2_results = stage2_data.get("results", stage2_data)
    if isinstance(stage2_results, dict):
        stage2_results = [stage2_results]

    # Build tasks
    tasks = []
    for r in stage2_results:
        mp = r.get("methodology_paper", "")
        if mp in PAPER_CLAIMS:
            tasks.append({"methodology_paper": mp, "stage2_result": r})

    if max_tasks:
        tasks = tasks[:max_tasks]

    print(f"  Running {len(tasks)} Stage 4 judgments...")
    t0 = time.time()
    all_results = []

    from concurrent.futures import ThreadPoolExecutor, as_completed
    workers = 4 if model_info["provider"] == "openai" else 2  # lower concurrency for API

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_run_stage4_task, llm, t): t for t in tasks}
            for i, future in enumerate(as_completed(futures)):
                try:
                    all_results.append(future.result())
                except Exception as e:
                    task = futures[future]
                    all_results.append({
                        "methodology_paper": task["methodology_paper"],
                        "error": str(e),
                    })
                if (i + 1) % 20 == 0:
                    print(f"    {i+1}/{len(tasks)} tasks done...")
    else:
        for i, task in enumerate(tasks):
            all_results.append(_run_stage4_task(llm, task))
            if (i + 1) % 10 == 0:
                print(f"    {i+1}/{len(tasks)} tasks done...")

    elapsed = time.time() - t0
    print(f"  Completed in {elapsed:.1f}s ({elapsed/len(tasks):.1f}s/task)")

    # Save per-model results
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = model_name.lower().replace(" ", "_")
    out_path = Path(output_dir) / f"stage4_{safe_name}_{ts}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    model_meta = {k: v for k, v in model_info.items() if k != "config"}
    output = {
        "timestamp": datetime.now().isoformat(),
        "model": model_meta,
        "stage2_source": stage2_results_path,
        "n_tasks": len(all_results),
        "results": all_results,
    }
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"  Saved to {out_path}")
    return output


def compare_models(model_results: list[dict]):
    """Print cross-model comparison of Stage 4 judgments."""
    from collections import Counter

    print(f"\n{'='*70}")
    print(f"CROSS-MODEL STAGE 4 COMPARISON")
    print(f"{'='*70}")

    for mr in model_results:
        name = mr.get("model", {}).get("name", "unknown")
        results = mr.get("results", [])
        j_counts = Counter()
        quality_counts = Counter()
        parsed = 0
        main_supported = 0

        for r in results:
            for jt, count in r.get("judgment_counts", {}).items():
                j_counts[jt] += count
            oa = r.get("overall_assessment", {})
            if "error" not in oa:
                parsed += 1
                quality_counts[oa.get("reproduction_quality", "?")] += 1
                if oa.get("main_finding_supported"):
                    main_supported += 1

        print(f"\n  {name}:")
        print(f"    Parsed: {parsed}/{len(results)}")
        print(f"    Judgments: SUPPORTED={j_counts.get('SUPPORTED',0)} "
              f"PARTIAL={j_counts.get('PARTIALLY SUPPORTED',0)} "
              f"NOT_SUPPORTED={j_counts.get('NOT SUPPORTED',0)} "
              f"NOT_TESTABLE={j_counts.get('NOT TESTABLE',0)}")
        print(f"    Quality: {dict(quality_counts)}")
        print(f"    Main finding supported: {main_supported}/{parsed}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Multi-model Stage 4 benchmark")
    parser.add_argument("--stage2-results", required=True,
                        help="Path to Stage 2 benchmark JSON")
    parser.add_argument("--max-tasks", type=int, default=None)
    parser.add_argument("--output", default="refine-logs")
    parser.add_argument("--models", nargs="+", default=None,
                        help="Model names to use (default: all available)")
    args = parser.parse_args()

    all_models = get_available_models()
    if args.models:
        all_models = [m for m in all_models if m["name"] in args.models]

    print(f"Available models: {[m['name'] for m in all_models]}")

    all_outputs = []
    for model_info in all_models:
        output = run_stage4_for_model(
            model_info, args.stage2_results, args.max_tasks, args.output)
        all_outputs.append(output)

    if len(all_outputs) >= 2:
        compare_models(all_outputs)
    elif len(all_outputs) == 1:
        summarize(all_outputs[0])
