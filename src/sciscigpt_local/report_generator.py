"""Reproducibility Report Generator — Module 4 of IDEA_REPORT.

Generates structured evaluation reports from reproduction results:
  - REI score with interpretation
  - Per-step assessment
  - Error log with classification
  - Environment info
  - Comparison with original claims
"""

from __future__ import annotations

import json, os, time
from pathlib import Path
from typing import Any


REI_SCALE = {
    (0, 0): "一键复现（黄金标准）",
    (1, 2): "低努力（常规可复现）",
    (3, 5): "中等努力（需要专业调试）",
    (6, 10): "高努力（可能需要原作者介入）",
    (11, float("inf")): "不可复现",
}


def _rei_label(rei: float) -> str:
    for (lo, hi), label in REI_SCALE.items():
        if lo <= rei <= hi:
            return label
    return "未知"


def generate_report(
    reproduction_result: dict[str, Any],
    paper_info: dict[str, Any] | None = None,
) -> str:
    """Generate a structured reproducibility report in Markdown.

    Args:
        reproduction_result: Output from reproduction pipeline
            (e.g., run_e2e_reproduction.py output or hard_reproduction output).
        paper_info: Optional paper metadata (title, authors, DOI).

    Returns:
        Markdown report string.
    """
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    paper = paper_info or {}

    lines = [
        "# Reproducibility Assessment Report",
        "",
        f"**Generated**: {now}",
        f"**Paper**: {paper.get('title', reproduction_result.get('paper_title', 'Unknown'))}",
    ]

    if paper.get("doi"):
        lines.append(f"**DOI**: {paper['doi']}")
    lines.append("")

    # Status and REI
    status = reproduction_result.get("status", "UNKNOWN")
    rei = reproduction_result.get("REI", 0.0)
    icon = {"SUCCESS": "✅", "FAILED": "❌", "PARTIAL": "⚠️"}.get(status, "❓")
    lines.extend([
        "## Overall Assessment",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Status | {icon} {status} |",
        f"| REI (Reproducibility Effort Index) | **{rei}** |",
        f"| REI Level | {_rei_label(rei)} |",
        f"| Fix iterations | {reproduction_result.get('fix_iterations', 0)} |",
        "",
    ])

    # Error breakdown
    error_types = reproduction_result.get("error_types", [])
    if error_types:
        from collections import Counter
        ec = Counter(error_types)
        lines.extend([
            "### Error Type Distribution",
            "",
            "| Error Type | Count |",
            "|------------|-------|",
        ])
        for etype, count in ec.most_common():
            lines.append(f"| {etype} | {count} |")
        lines.append("")

    # Attempts detail
    attempts = reproduction_result.get("attempts", [])
    if attempts:
        lines.extend([
            "### Attempt Log",
            "",
            "| Attempt | Exit Code | Has Error | Error Preview |",
            "|---------|-----------|-----------|---------------|",
        ])
        for a in attempts:
            err_preview = a.get("stderr_preview", "")[:60].replace("|", "\\|")
            lines.append(f"| {a['attempt']} | {a['exit_code']} | {a['has_error']} | {err_preview} |")
        lines.append("")

    # Metrics comparison
    computed = reproduction_result.get("parsed_metrics") or reproduction_result.get("computed_D")
    if computed:
        lines.extend([
            "### Computed Results",
            "",
            "```json",
            json.dumps(computed, indent=2, ensure_ascii=False) if isinstance(computed, dict)
            else f"D-index: {computed}",
            "```",
            "",
        ])

    # Ground truth comparison
    if reproduction_result.get("computed_rho") is not None:
        gt = reproduction_result.get("gt_rho")
        comp = reproduction_result["computed_rho"]
        lines.extend([
            "### Ground Truth Comparison",
            "",
            f"| Metric | Computed | Ground Truth | Deviation |",
            f"|--------|----------|-------------|-----------|",
            f"| Spearman ρ | {comp:.4f} | {gt:.4f} | {abs(comp - gt):.6f} |",
            "",
        ])

    if reproduction_result.get("computed_D") is not None:
        gt_d = reproduction_result.get("ground_truth_D") or reproduction_result.get("subgraph_D")
        comp_d = reproduction_result["computed_D"]
        if gt_d is not None:
            lines.extend([
                "| Metric | Computed | Ground Truth | Deviation |",
                "|--------|----------|-------------|-----------|",
                f"| D-index | {comp_d:.6f} | {gt_d:.6f} | {abs(comp_d - gt_d):.6f} |",
                "",
            ])

    # Environment info
    env = reproduction_result.get("env_info") or reproduction_result.get("environment")
    if env:
        lines.extend([
            "### Environment",
            "",
            f"- Python: {env.get('python_version', 'unknown')}",
            f"- Packages: {env.get('top_packages', 'not captured')[:200]}",
            "",
        ])

    # REI interpretation guide
    lines.extend([
        "---",
        "",
        "## REI Scale Reference",
        "",
        "| REI Range | Level | Description |",
        "|-----------|-------|-------------|",
        "| 0 | Gold | One-click reproducible |",
        "| 0.1–2 | Low | Minor fixes needed |",
        "| 2.1–5 | Medium | Requires debugging effort |",
        "| 5.1–10 | High | May need author assistance |",
        "| >10 | Critical | Not practically reproducible |",
        "",
        "---",
        "",
        f"*Report generated by AI Reproducibility Metrology v0.1*",
    ])

    return "\n".join(lines)


def save_report(
    report_text: str,
    output_dir: str | None = None,
) -> str:
    """Save the report to a file, return the path."""
    output_dir = output_dir or str(Path(__file__).resolve().parent.parent.parent / "refine-logs")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"reproducibility_report_{timestamp}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)
    return path


def generate_report_from_json(
    result_json_path: str,
    paper_info: dict[str, Any] | None = None,
    output_dir: str | None = None,
) -> str:
    """Convenience: load a result JSON and generate + save a report.

    Args:
        result_json_path: Path to a reproduction result JSON file.
        paper_info: Optional paper metadata.
        output_dir: Where to save the report.

    Returns:
        Path to the saved report.
    """
    with open(result_json_path, "r") as f:
        data = json.load(f)
    report = generate_report(data, paper_info)
    return save_report(report, output_dir)
