"""IMRaD section splitter — extract structured sections from markdown papers.

Splits paper markdown into: abstract, introduction, methods, results, conclusion.
Uses regex patterns on markdown headings to find section boundaries.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import PROJECT_ROOT, MAX_PAPER_CHARS
from ..types import PaperEntry

# ── Section heading patterns (ordered by specificity) ──

# Patterns match both markdown headings (# Introduction) and plain-text
# numeric headings (1. Introduction) from MinerU PDF-to-markdown conversions.

INTRO_PATTERNS = [
    r"^(?:#+\s*)?(?:\d+\.?\s*)?(?:I[ .]?\s*)?introduction",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?(?:I[ .]?\s*)?background",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?(?:I[ .]?\s*)?motivation",
]

METHODS_PATTERNS = [
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:methods?|methodology)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:data\s+and\s+methods?)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:materials?\s+and\s+methods?)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:experimental\s+design)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:empirical\s+strategy)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:measuring\s+the\s+effects?)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:measurement?\s+approach)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:data\s+and\s+measurement)\s*$",
]

RESULTS_PATTERNS = [
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:results?)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:findings)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:empirical\s+results?)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:assessments?\s+of\s+face\s+validity)\s*$",
]

CONCLUSION_PATTERNS = [
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:discussion|conclusion)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:discussion\s+and\s+conclusion)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:general\s+discussion)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:summary)\s*$",
    r"^(?:#+\s*)?(?:\d+\.?\s*)?\s*(?:concluding\s+remarks)\s*$",
]

ABSTRACT_PATTERN = r"(?:^|\n)\s*(?:abstract|ABSTRACT|Abstract)\.?\s*\n"


def _find_section_boundary(
    lines: list[str], patterns: list[str], start_from: int = 0
) -> int | None:
    """Find the first line index matching any of the given heading patterns."""
    for i, line in enumerate(lines[start_from:], start=start_from):
        for pat in patterns:
            if re.match(pat, line.strip(), re.IGNORECASE):
                return i
    return None


def _extract_section(
    lines: list[str], start: int, end: int | None, max_chars: int = MAX_PAPER_CHARS
) -> str:
    """Extract text from start to end, truncating to max_chars."""
    if end is None:
        end = len(lines)
    text = "\n".join(lines[start:end]).strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[...truncated...]"
    return text


def _find_numeric_sections(lines: list[str]) -> list[tuple[int, str]]:
    """Fallback: find sections by numeric headings (1., 2., etc.) with content matching.

    Scans for lines like "1. Introduction", "2. Data and Methods",
    "3. Results", "4. Discussion" and maps them to IMRaD sections.
    """
    section_keywords = {
        "intro": ["introduction", "background", "motivation"],
        "methods": ["method", "data", "measurement", "empirical", "measuring"],
        "results": ["result", "finding", "analysis", "assessment"],
        "conclusion": ["discussion", "conclusion", "summary"],
    }

    found: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        stripped = line.strip().lower()
        if not re.match(r"^\d+\.?\s", stripped):
            continue
        for label, keywords in section_keywords.items():
            if any(kw in stripped for kw in keywords):
                found.append((i, label))
                break

    # Deduplicate by label (keep first occurrence)
    seen = set()
    result = []
    for line_idx, label in found:
        if label not in seen:
            seen.add(label)
            result.append((line_idx, label))

    result.sort(key=lambda x: x[0])
    return result


def split_paper_sections(md_path: str | Path) -> dict[str, str]:
    """Split a markdown paper into IMRaD sections.

    Args:
        md_path: Path to the markdown file.

    Returns:
        Dict with keys: abstract, intro, methods, results, conclusion, full_text
    """
    path = Path(md_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        return {
            "abstract": "", "intro": "", "methods": "",
            "results": "", "conclusion": "", "full_text": "",
        }

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    # ── Extract abstract ──
    abstract = ""
    abstract_match = re.search(ABSTRACT_PATTERN, text, re.MULTILINE)
    if abstract_match:
        abs_start = abstract_match.end()
        # Abstract ends at the next section heading (numbered or markdown)
        abs_end = len(text)
        all_section_pats = INTRO_PATTERNS + METHODS_PATTERNS + RESULTS_PATTERNS + CONCLUSION_PATTERNS
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Check if this line looks like a section heading
            if i > 0 and lines[i - 1].strip() == "":
                for pat in all_section_pats:
                    if re.match(pat, stripped, re.IGNORECASE):
                        char_pos = sum(len(l) + 1 for l in lines[:i])
                        if char_pos > abs_start + 50:  # at least some content
                            abs_end = char_pos
                            break
                if abs_end < len(text):
                    break
        abstract = text[abs_start:abs_end].strip()[:5000]

    # ── Find section boundaries ──
    # Try standard patterns first, then fall back to broader numeric headings
    boundaries: list[tuple[int, str]] = []

    intro_start = _find_section_boundary(lines, INTRO_PATTERNS)
    methods_start = _find_section_boundary(lines, METHODS_PATTERNS)
    results_start = _find_section_boundary(lines, RESULTS_PATTERNS)
    conclusion_start = _find_section_boundary(lines, CONCLUSION_PATTERNS)

    if intro_start is not None:
        boundaries.append((intro_start, "intro"))
    if methods_start is not None:
        boundaries.append((methods_start, "methods"))
    if results_start is not None:
        boundaries.append((results_start, "results"))
    if conclusion_start is not None:
        boundaries.append((conclusion_start, "conclusion"))

    # If no sections found, try broad numeric heading scan
    if len(boundaries) < 2:
        numeric_sections = _find_numeric_sections(lines)
        for line_idx, label in numeric_sections:
            boundaries.append((line_idx, label))
        boundaries.sort(key=lambda x: x[0])

    boundaries.sort(key=lambda x: x[0])

    # ── Extract each section ──
    # Map label to start line, then extract from start to next boundary
    boundary_map = {label: start for start, label in boundaries}
    ordered_labels = [label for _, label in boundaries]

    intro = ""
    methods = ""
    results = ""
    conclusion = ""

    for i, (start, label) in enumerate(boundaries):
        end = boundaries[i + 1][0] if i + 1 < len(boundaries) else None
        content = _extract_section(lines, start, end)
        if label == "intro":
            intro = content
        elif label == "methods":
            methods = content
        elif label == "results":
            results = content
        elif label == "conclusion":
            conclusion = content

    return {
        "abstract": abstract,
        "intro": intro,
        "methods": methods,
        "results": results,
        "conclusion": conclusion,
        "full_text": text[:MAX_PAPER_CHARS],
    }


def enrich_paper_entry(entry: PaperEntry) -> PaperEntry:
    """Load paper sections from the markdown file into a PaperEntry.

    Falls back to full text for any section that couldn't be extracted.
    Mutates and returns the entry for convenience.
    """
    sections = split_paper_sections(entry.md_path)
    full = sections.get("full_text", "")

    entry.abstract = sections["abstract"] or ""
    entry.intro = sections["intro"] or full
    entry.methods = sections["methods"] or full
    entry.results = sections["results"] or full
    entry.conclusion = sections["conclusion"] or full
    return entry
