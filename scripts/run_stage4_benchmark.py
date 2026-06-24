#!/usr/bin/env python3
"""Stage 4: Conclusion-Evidence Consistency Judgment benchmark.

Given a methodology paper's claims + reproduced experimental results (from Stage 2),
LLMs judge whether the reproduced evidence supports each claim.

This tests LLM's scientific reasoning capability:
  Can an LLM act as a peer reviewer and evaluate whether data supports conclusions?

Unlike Stage 2 (code generation + execution), Stage 4 is a pure reasoning task:
  Input: paper claims + numerical results
  Output: support judgment + rationale
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscigpt_local.llm_backends import load_llm_from_env, LLMConfig, load_llm_from_config
from src.sciscigpt_local.metric_templates import METRIC_CONFIGS, get_primary_metric


# ── Paper Claims ──────────────────────────────────────────────────────
# Key testable claims extracted from each methodology paper's Discussion/Findings.
# Each claim has: id, text, claim_type (method | finding | interpretation), testability

PAPER_CLAIMS = {
    "ms_dynamic_network": {
        "title": "A Dynamic Network Measure of Technological Change",
        "journal": "Management Science (2017)",
        "metric_type": "disruption",
        "claims": [
            {
                "id": "D1",
                "text": "The disruption index D = (n_i - n_j)/(n_i + n_j + n_k) measures "
                        "whether an innovation disrupts or consolidates existing knowledge.",
                "type": "method",
                "testable_with": "disruption computation on any paper with citation data",
            },
            {
                "id": "D2",
                "text": "The dynamic network measure captures technological evolution better "
                        "than static citation counts alone.",
                "type": "finding",
                "testable_with": "comparison of D-index vs raw citation count on same papers",
            },
            {
                "id": "D3",
                "text": "The method can be applied to any citation network to identify "
                        "disruptive technologies.",
                "type": "method",
                "testable_with": "successful computation across diverse test papers",
            },
        ],
    },
    "nber_w18958": {
        "title": "Exploring Tradeoffs in the Organization of Scientific Work: "
                 "Collaboration and Scientific Reward",
        "journal": "NBER Working Paper (2013)",
        "metric_type": "team_size_effect",
        "claims": [
            {
                "id": "T1",
                "text": "There is a tradeoff between collaboration scale and individual "
                        "scientific contribution recognition.",
                "type": "finding",
                "testable_with": "team size effect (small vs large team disruption difference)",
            },
            {
                "id": "T2",
                "text": "Small teams (≤3 authors) produce more individually disruptive work "
                        "than large teams (>3 authors).",
                "type": "finding",
                "testable_with": "SMALL_MEAN - LARGE_MEAN > 0 → supported",
            },
            {
                "id": "T3",
                "text": "The team size effect is a robust pattern that should replicate "
                        "across different datasets.",
                "type": "interpretation",
                "testable_with": "consistency of effect direction across test conditions",
            },
        ],
    },
    "arxiv_2306_01949": {
        "title": "The disruption index is biased by citation inflation",
        "journal": "arXiv preprint (2023)",
        "metric_type": "citation_inflation",
        "claims": [
            {
                "id": "C1",
                "text": "The disruption index is systematically biased by citation inflation — "
                        "papers with longer reference lists produce lower D-index values.",
                "type": "finding",
                "testable_with": "negative correlation between reference_count and disruption_score",
            },
            {
                "id": "C2",
                "text": "Temporal normalization is needed to compare disruption scores "
                        "across different time periods.",
                "type": "interpretation",
                "testable_with": "correlation magnitude indicates bias severity",
            },
            {
                "id": "C3",
                "text": "The bias exists in standard bibliometric datasets including SciSciNet.",
                "type": "finding",
                "testable_with": "replication on SciSciNet data",
            },
        ],
    },
    "arxiv_2308_02383": {
        "title": "What do we know about the disruption index in scientometrics? An overview",
        "journal": "arXiv preprint (2024)",
        "metric_type": "disruption",
        "claims": [
            {
                "id": "R1",
                "text": "The disruption index D = (n_i - n_j)/(n_i + n_j + n_k) is the "
                        "standard formula for measuring scientific disruption.",
                "type": "method",
                "testable_with": "disruption computation matches SciSciNet ground truth",
            },
            {
                "id": "R2",
                "text": "Multiple variants of the disruption index exist (D-index, CD-index), "
                        "each capturing different aspects of disruption.",
                "type": "method",
                "testable_with": "implementation can distinguish D from CD variants",
            },
            {
                "id": "R3",
                "text": "The disruption index has known limitations including sensitivity to "
                        "citation window and field effects.",
                "type": "interpretation",
                "testable_with": "consistency of results across different test papers",
            },
        ],
    },
    "nature_2023_disruption": {
        "title": "Papers and patents are becoming less disruptive over time",
        "journal": "Nature (2023)",
        "metric_type": "disruption_temporal",
        "claims": [
            {
                "id": "N1",
                "text": "Papers and patents are becoming less disruptive over time across "
                        "all fields of science and technology.",
                "type": "finding",
                "testable_with": "negative trend correlation between decade and mean disruption",
            },
            {
                "id": "N2",
                "text": "The decline in disruptiveness persists after controlling for "
                        "changes in citation and authorship practices.",
                "type": "finding",
                "testable_with": "trend remains negative after controlling for reference_count",
            },
            {
                "id": "N3",
                "text": "The CD-index (a variant of D-index) shows the same declining trend.",
                "type": "finding",
                "testable_with": "trend consistency between D and CD variants",
            },
        ],
    },
    "pnas_network_impact": {
        "title": "A network-based normalized impact measure reveals successful periods "
                 "of scientific discovery across disciplines",
        "journal": "PNAS (2023)",
        "metric_type": "network_normalized_impact",
        "claims": [
            {
                "id": "P1",
                "text": "Network-normalized impact better identifies breakthrough discoveries "
                        "than raw citation counts.",
                "type": "finding",
                "testable_with": "network_impact ≠ focal_citations (normalization changes ranking)",
            },
            {
                "id": "P2",
                "text": "The measure normalizes by co-cited papers' mean citations, "
                        "comparing a paper against its citation context.",
                "type": "method",
                "testable_with": "NETWORK_IMPACT = focal_cit / mean_co_cited",
            },
            {
                "id": "P3",
                "text": "The method reveals hidden impact in fields with lower absolute citation rates.",
                "type": "interpretation",
                "testable_with": "network_impact > 1.0 for papers in low-citation fields",
            },
        ],
    },
    "rp_2021_ccby": {
        "title": "Research Policy 2021 — CC-BY Open Access",
        "journal": "Research Policy (2021)",
        "metric_type": "disruption",
        "claims": [
            {
                "id": "O1",
                "text": "The disruption index can be computed from standard citation data "
                        "and reflects a paper's novel contribution.",
                "type": "method",
                "testable_with": "disruption computation on SciSciNet test papers",
            },
            {
                "id": "O2",
                "text": "Disruption patterns differ across research fields and publication types.",
                "type": "finding",
                "testable_with": "variation in D-index across test papers of different types",
            },
        ],
    },
    "rp_2025_sam_arts": {
        "title": "Not like the others: Frontier scientists for inventive performance",
        "journal": "Research Policy (2025)",
        "metric_type": "frontier_author_impact",
        "claims": [
            {
                "id": "F1",
                "text": "Frontier scientists produce more inventive and higher-impact work "
                        "than non-frontier scientists.",
                "type": "finding",
                "testable_with": "FRONTIER_MEAN_CITATIONS > NON_FRONTIER_MEAN_CITATIONS",
            },
            {
                "id": "F2",
                "text": "Being 'not like the others' (statistically distinct research profile) "
                        "predicts inventive performance.",
                "type": "finding",
                "testable_with": "FRONTIER_MEAN_D differs from NON_FRONTIER_MEAN_D",
            },
            {
                "id": "F3",
                "text": "The frontier effect is distinct from simple citation-based measures "
                        "of research quality.",
                "type": "interpretation",
                "testable_with": "frontier classification differs from citation percentile ranking",
            },
        ],
    },
}


# ── Stage 4 Prompt ────────────────────────────────────────────────────

def build_stage4_prompt(paper_claims: dict, result_entry: dict) -> str:
    """Build the Stage 4 conclusion-evidence judgment prompt.

    Args:
        paper_claims: Claims dict from PAPER_CLAIMS for one methodology paper.
        result_entry: Single result from Stage 2 benchmark (one task).

    Returns:
        Prompt string for the LLM.
    """
    claims_text = "\n".join(
        f"  [{c['id']}] ({c['type']}) {c['text']}"
        for c in paper_claims["claims"]
    )

    # Format result evidence
    level = result_entry["level"]
    metric_type = result_entry.get("metric_type", "disruption")
    metric_label = METRIC_CONFIGS.get(metric_type, {}).get("label", metric_type)
    primary_key = get_primary_metric(metric_type)

    computed = result_entry.get("computed_primary")
    gt = result_entry.get("ground_truth_primary")
    status = result_entry["status"]
    rei_c = result_entry.get("rei_c", result_entry.get("rei", 100))
    silent = result_entry.get("is_silent_failure", False)

    if status == "SUCCESS" and computed is not None:
        # Compute relative error
        denom = max(abs(gt), 1e-8) if gt != 0 else 1.0
        rel_err = abs(computed - gt) / denom
        evidence = (
            f"**Stage 2 Reproduction Result:**\n"
            f"- Methodology paper: {paper_claims['title']}\n"
            f"- Information level: {level} "
            f"({'formula given' if level == 'L1' else 'abstract only' if level == 'L2' else 'full paper text'})\n"
            f"- Metric: {metric_label}\n"
            f"- Computed {primary_key}: {computed}\n"
            f"- Ground truth (SciSciNet): {gt}\n"
            f"- Relative error: {rel_err:.4%}\n"
            f"- REI-c: {rei_c:.2f} (0=perfect, >10=serious failure)\n"
            f"- Silent failure: {'YES — code ran but result is wrong' if silent else 'NO — result is numerically correct'}\n"
            f"- Test paper: {result_entry.get('paper_id')} "
            f"({result_entry.get('methodology_title', '')[:60]})\n"
        )
    else:
        evidence = (
            f"**Stage 2 Reproduction Result:**\n"
            f"- Methodology paper: {paper_claims['title']}\n"
            f"- Information level: {level}\n"
            f"- Metric: {metric_label}\n"
            f"- Status: FAILED — could not produce valid output\n"
            f"- REI-c: {rei_c:.2f}\n"
            f"- Errors: {result_entry.get('error_types', [])}\n"
        )

    prompt = f"""You are a scientific peer reviewer evaluating whether reproduced experimental results support a published paper's claims.

## Paper Under Review

**Title**: {paper_claims['title']}
**Journal**: {paper_claims['journal']}

### Paper's Claims

{claims_text}

## Reproduced Evidence

{evidence}

## Task

For EACH claim listed above, judge whether the reproduced evidence supports it.

Use this scale:
- **SUPPORTED**: The evidence directly confirms the claim
- **PARTIALLY SUPPORTED**: The evidence is consistent with the claim but incomplete or weak
- **NOT SUPPORTED**: The evidence contradicts or fails to confirm the claim
- **NOT TESTABLE**: The reproduced evidence does not directly address this claim

Important considerations:
1. A FAILED reproduction does NOT necessarily mean the claim is wrong — it means the method could not be implemented
2. A numerically correct result (REI-c < 1) provides strong evidence; a silent failure (code ran but wrong) provides misleading evidence
3. Consider whether the test is appropriate for the claim (e.g., computing D-index for one paper ≠ testing "declining trend over decades")

Respond in this JSON format:
```json
{{
  "judgments": [
    {{
      "claim_id": "D1",
      "judgment": "SUPPORTED",
      "confidence": "high|medium|low",
      "rationale": "One sentence explaining why."
    }}
  ],
  "overall_assessment": {{
    "reproduction_quality": "good|acceptable|poor",
    "main_finding_supported": true,
    "summary": "2-3 sentence overall assessment of what this reproduction tells us about the paper."
  }}
}}
```

Output ONLY the JSON (no other text)."""
    return prompt


# ── Result Parsing ─────────────────────────────────────────────────────

def parse_stage4_response(response_text: str) -> dict | None:
    """Parse LLM's Stage 4 judgment JSON from response."""
    import re
    # Extract JSON block
    text = str(response_text)
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        # Try to find JSON object directly
        m = re.search(r'\{.*"judgments".*\}', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return None


# ── Run Single Task ────────────────────────────────────────────────────

def _extract_text_content(response) -> str:
    """Extract text from LLM response, handling Anthropic's content-block format."""
    content = response.content
    if isinstance(content, list):
        # Anthropic format: list of {'type': 'text'/'thinking', ...}
        text_parts = [b["text"] for b in content if b.get("type") == "text" and "text" in b]
        return "\n".join(text_parts)
    return str(content)


def _run_stage4_task(llm, task: dict) -> dict:
    """Execute one Stage 4 judgment task."""
    paper_id = task["methodology_paper"]
    claims = PAPER_CLAIMS[paper_id]
    prompt = build_stage4_prompt(claims, task["stage2_result"])

    response = llm.invoke([{"role": "user", "content": prompt}])
    text_content = _extract_text_content(response)
    parsed = parse_stage4_response(text_content)

    result = {
        "methodology_paper": paper_id,
        "test_paper_id": task["stage2_result"]["paper_id"],
        "level": task["stage2_result"]["level"],
        "metric_type": task["stage2_result"].get("metric_type", "disruption"),
        "stage2_status": task["stage2_result"]["status"],
        "stage2_rei_c": task["stage2_result"].get("rei_c"),
        "parsed": parsed is not None,
    }

    if parsed:
        result["judgments"] = parsed.get("judgments", [])
        result["overall_assessment"] = parsed.get("overall_assessment", {})
        # Count judgment types
        j_types = {}
        for j in result["judgments"]:
            jt = j.get("judgment", "UNKNOWN")
            j_types[jt] = j_types.get(jt, 0) + 1
        result["judgment_counts"] = j_types
    else:
        result["judgments"] = []
        result["overall_assessment"] = {"error": "Failed to parse LLM response"}
        result["judgment_counts"] = {"PARSE_ERROR": len(claims["claims"])}

    return result


# ── Main Benchmark ─────────────────────────────────────────────────────

def run_stage4(llm, stage2_results_path: str, output_dir: str = "refine-logs",
               workers: int = 4, max_tasks: int | None = None) -> dict:
    """Run Stage 4 benchmark on Stage 2 results.

    Args:
        llm: LangChain-compatible LLM.
        stage2_results_path: Path to a Stage 2 benchmark JSON file.
        output_dir: Where to save results.
        workers: Number of concurrent LLM call workers.
        max_tasks: Optional cap on number of tasks (for quick testing).

    Returns:
        Dict with results summary.
    """
    with open(stage2_results_path) as f:
        stage2_data = json.load(f)

    stage2_results = stage2_data.get("results", stage2_data)
    if isinstance(stage2_results, dict):
        stage2_results = [stage2_results]

    # Build task list: one Stage 4 judgment per Stage 2 result
    tasks = []
    for r in stage2_results:
        mp = r.get("methodology_paper", "")
        if mp in PAPER_CLAIMS:
            tasks.append({"methodology_paper": mp, "stage2_result": r})

    if max_tasks:
        tasks = tasks[:max_tasks]

    print(f"Stage 4: {len(tasks)} judgment tasks from {stage2_results_path}")
    t0 = time.time()
    all_results = []

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
                    print(f"  {i+1}/{len(tasks)} tasks done...")
    else:
        for i, task in enumerate(tasks):
            all_results.append(_run_stage4_task(llm, task))
            if (i + 1) % 10 == 0:
                print(f"  {i+1}/{len(tasks)} tasks done...")

    elapsed = time.time() - t0
    print(f"Completed {len(all_results)} Stage 4 judgments in {elapsed:.1f}s")

    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(output_dir) / f"stage4_benchmark_{ts}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "timestamp": datetime.now().isoformat(),
        "description": "Stage 4: Conclusion-Evidence Consistency Judgment",
        "stage2_source": stage2_results_path,
        "n_tasks": len(all_results),
        "results": all_results,
    }
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"Results saved to {out_path}")
    return output


def summarize(results: dict):
    """Print Stage 4 result summary."""
    all_r = results["results"]

    # Judgment distribution
    from collections import Counter
    j_counts = Counter()
    overall_quality = Counter()
    main_supported = 0
    total_parsed = 0

    for r in all_r:
        for jt, count in r.get("judgment_counts", {}).items():
            j_counts[jt] += count
        oa = r.get("overall_assessment", {})
        if "error" not in oa:
            total_parsed += 1
            overall_quality[oa.get("reproduction_quality", "unknown")] += 1
            if oa.get("main_finding_supported"):
                main_supported += 1

    print(f"\n{'='*60}")
    print(f"STAGE 4 SUMMARY")
    print(f"  Total judgments: {len(all_r)}")
    print(f"  Parsed responses: {total_parsed}/{len(all_r)}")
    print(f"\n  Claim-level judgments:")
    for jt in ["SUPPORTED", "PARTIALLY SUPPORTED", "NOT SUPPORTED",
               "NOT TESTABLE", "PARSE_ERROR"]:
        if jt in j_counts:
            print(f"    {jt}: {j_counts[jt]}")
    print(f"\n  Reproduction quality assessment:")
    for q, c in overall_quality.most_common():
        print(f"    {q}: {c}")
    print(f"  Main finding supported: {main_supported}/{total_parsed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stage 4: Conclusion-Evidence Consistency Benchmark")
    parser.add_argument("--stage2-results", required=True,
                        help="Path to Stage 2 benchmark JSON")
    parser.add_argument("--output", default="refine-logs")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-tasks", type=int, default=None,
                        help="Limit number of tasks (for quick testing)")
    parser.add_argument("--summary-only", action="store_true",
                        help="Only print summary of existing Stage 4 results")
    args = parser.parse_args()

    if args.summary_only:
        with open(args.stage2_results) as f:
            existing = json.load(f)
        summarize(existing)
    else:
        print("Loading LLM...")
        llm = load_llm_from_env()
        results = run_stage4(llm, args.stage2_results, args.output,
                            args.workers, args.max_tasks)
        summarize(results)
