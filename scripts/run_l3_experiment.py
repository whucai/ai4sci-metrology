#!/usr/bin/env python3
"""L3 prompt experiment: compare original vs v2 vs v2+few-shot."""

from __future__ import annotations

import json, sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscibench.annotation import SciSciPaper
from src.sciscibench.tasks.task2_conclusion import Task2Prompt, Task2Runner
from src.sciscibench.eval.task2_evaluator import Task2Evaluator
from src.sciscigpt_local.llm_backends import LLMConfig, load_llm_from_config

print_lock = threading.Lock()

def _print(msg):
    with print_lock:
        print(msg)

def load_llm():
    import os
    provider = os.environ.get("LLM_PROVIDER", "")
    if not provider:
        # Auto-detect: try OpenAI first, fall back to Anthropic
        if os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        elif os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            provider = "anthropic"
        else:
            provider = "openai"

    if provider == "anthropic":
        config = LLMConfig(
            name="deepseek-v4-pro", provider="anthropic",
            model=os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "deepseek-v4-pro"),
            api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN", ""),
            base_url=os.environ.get("ANTHROPIC_BASE_URL", ""),
            temperature=0.0, max_tokens=4096,
        )
    else:
        config = LLMConfig(
            name="qwen3-32b", provider="openai",
            model=os.environ.get("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/"),
            api_key=os.environ.get("OPENAI_API_KEY", "not-needed"),
            base_url=os.environ.get("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1"),
            temperature=0.0, max_tokens=4096,
        )
    return load_llm_from_config(config)


# Original L3 prompt text (before v2 changes), for Arm A baseline
_ORIGINAL_L3_PROMPT_TEMPLATE = """## Task L3: Recognize Uncertainty from Partial Results

You are given: research question, experiment design, and PARTIAL experimental results.
The results are incomplete — some analyses failed, some data is missing,
some effects are marginal. Your job is to identify what can and CANNOT be concluded.

## Context

{research_context}

## Experiment Specification

{experiment_spec}

## Partial Results (INCOMPLETE)

{partial_str}

## Critical Guidance

These results are INCOMPLETE. Be honest about uncertainty.
Do NOT fabricate conclusions the data doesn't support.
If evidence is insufficient, say so explicitly.

IMPORTANT: Even when evidence is partial, you MUST infer at least
ONE tentative conclusion based on what IS available. State the
direction (positive/negative/null) if any trend is visible, and
note the uncertainty. An empty response is NOT acceptable.

## Output Format

Output a JSON object with:
- `supported_conclusions`: Claims that CAN be made given the available evidence, each with:
  - `claim`: The conclusion statement
  - `support_strength`: strong/moderate/weak
  - `missing_evidence`: What additional evidence would strengthen this claim
- `unsupported_claims`: Claims that CANNOT be made yet, each with:
  - `claim`: The unsupported conclusion
  - `why_unsupported`: Why the current evidence is insufficient
  - `whats_needed`: What additional data/analysis would be needed
- `uncertainty_assessment`: Overall assessment of uncertainty (high/moderate/low)
- `insufficient_evidence_flag`: true if the evidence is broadly insufficient

Output ONLY the JSON."""


def run_single(llm, paper: SciSciPaper, level: str, evaluator: Task2Evaluator,
               arm: str = "v2_fewshot") -> dict:
    """Run one paper × level.

    Arms:
      - "original": Original L3 prompt (pre-v2)
      - "v2_nofewshot": v2 prompt without few-shot examples
      - "v2_fewshot": v2 prompt with few-shot examples
    """
    import json as _json

    prompt = Task2Prompt(paper=paper, level=level)

    if arm == "original":
        # Override _build_l3_prompt with original text
        saved_build = prompt._build_l3_prompt
        partial_str = _json.dumps(prompt.experimental_results, indent=2) if prompt.experimental_results else (
            "\n".join(f"- {_json.dumps(c)}" for c in prompt.paper.partial_results)
        )
        prompt._build_l3_prompt = lambda: _ORIGINAL_L3_PROMPT_TEMPLATE.format(
            research_context=prompt._research_context(),
            experiment_spec=prompt._experiment_spec(),
            partial_str=partial_str,
        )
        prompt._build_l3_few_shot = lambda: ""
    elif arm == "v2_nofewshot":
        prompt._build_l3_few_shot = lambda: ""

    runner = Task2Runner(llm=llm)
    t0 = time.time()
    output = runner.run(prompt)
    elapsed = time.time() - t0

    result = {
        "paper_id": paper.paper_id,
        "level": level,
        "arm": arm,
        "elapsed": round(elapsed, 1),
    }

    if output["status"] == "success":
        gold = paper.to_gold_json()
        eval_result = evaluator.evaluate(
            gold=gold, pred=output, level=level, paper_id=paper.paper_id,
        )
        result.update(eval_result.to_dict())
        result["status"] = "success"
        result["raw_output"] = output.get("raw", "")[:500]
    else:
        result["status"] = output["status"]
        result["error"] = output.get("error", "")[:200]
        result["raw_output"] = output.get("raw", "")[:500]

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=str, required=True)
    parser.add_argument("--registry", type=str, default="bench-mark/extracted_registry.json")
    parser.add_argument("--arm", choices=["all", "original", "v2_nofewshot", "v2_fewshot", "both"], default="both")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=str, default="refine-logs")
    args = parser.parse_args()

    sample_pids = json.loads(Path(args.sample).read_text())
    _print(f"Sample: {len(sample_pids)} papers")

    reg = json.loads(Path(args.registry).read_text())
    papers = {}
    for pid in sample_pids:
        entry = reg.get(pid)
        if not entry:
            _print(f"  SKIP {pid}: not in registry")
            continue
        try:
            p = SciSciPaper(
                paper_id=pid,
                title=entry.get("title", ""), authors=entry.get("authors", []),
                venue=entry.get("venue", ""), year=entry.get("year", 0),
                doi=entry.get("doi", ""),
                research_idea=entry.get("research_idea", ""),
                research_question=entry.get("research_question", ""),
                hypotheses=entry.get("hypotheses", []),
                data_source=entry.get("data_source", ""),
                data_description=entry.get("data_description", ""),
                independent_variables=entry.get("independent_variables", []),
                dependent_variables=entry.get("dependent_variables", []),
                control_variables=entry.get("control_variables", []),
                experiment_design_gold={
                    "statistical_method": entry.get("statistical_method", {}),
                    "network_construction": entry.get("network_construction", {}),
                    "grouping_strategy": entry.get("grouping_strategy", {}),
                },
                result_claims=entry.get("result_claims", []),
                partial_results=entry.get("partial_results", []),
                conclusion_claims=entry.get("conclusion_claims", []),
                limitations=entry.get("limitations", []),
                robustness_checks=entry.get("robustness_checks", []),
                available_fields=entry.get("available_fields", []),
            )
            papers[pid] = p
        except Exception as e:
            _print(f"  SKIP {pid}: {e}")

    _print(f"Loaded {len(papers)} papers")

    llm = load_llm()
    evaluator = Task2Evaluator()
    arms = (["original", "v2_nofewshot", "v2_fewshot"] if args.arm == "all"
            else ["v2_fewshot", "v2_nofewshot"] if args.arm == "both"
            else [args.arm])
    ts = time.strftime("%Y%m%d_%H%M%S")

    for arm in arms:
        _print(f"\n{'='*60}")
        _print(f"Arm: {arm}")
        _print(f"{'='*60}")

        results = []
        tasks = [(pid, paper) for pid, paper in papers.items()]

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(run_single, llm, paper, "L3", evaluator, arm): pid
                for pid, paper in tasks
            }
            done = 0
            for future in as_completed(futures):
                r = future.result()
                results.append(r)
                done += 1
                if done % 20 == 0:
                    _print(f"  [{done}/{len(tasks)}]")

        success = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] != "success"]
        _print(f"Arm {arm}: {len(success)}/{len(results)} success, {len(failed)} failed")

        if success:
            scores = [r["overall_score"] for r in success]
            dirs = [r["direction_accuracy"] for r in success]
            halls = [r["hallucinated_claim_rate"] for r in success]
            lims = [r["limitation_awareness"] for r in success]
            _print(f"  overall: mean={sum(scores)/len(scores):.3f} min={min(scores):.3f} max={max(scores):.3f}")
            _print(f"  direction: mean={sum(dirs)/len(dirs):.3f}")
            _print(f"  hallucination: mean={sum(halls)/len(halls):.3f}")
            _print(f"  limitation: mean={sum(lims)/len(lims):.3f}")

        outpath = Path(args.output) / f"l3_experiment_{arm}_{ts}.json"
        outpath.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        _print(f"Results: {outpath}")

    _print("\nExperiment complete.")


if __name__ == "__main__":
    main()
