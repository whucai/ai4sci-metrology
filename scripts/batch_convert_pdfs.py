#!/usr/bin/env python3
"""Batch convert PDF papers to markdown using PyMuPDF (fast, no model downloads).

Usage:
    python3 scripts/batch_convert_pdfs.py              # Convert all selected papers
    python3 scripts/batch_convert_pdfs.py --resume     # Resume from where left off
"""

import json
import re
import sys
import time
from pathlib import Path

import fitz  # PyMuPDF

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SELECTED_PATH = PROJECT_ROOT / "bench-mark" / "selected_papers.json"
OTHERS_DIR = PROJECT_ROOT / "bench-mark" / "others"


def extract_paper_sections(text: str) -> str:
    """Try to structure the extracted text into a readable markdown document."""
    lines = text.split("\n")
    cleaned: list[str] = []
    prev_empty = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not prev_empty:
                cleaned.append("")
                prev_empty = True
            continue
        prev_empty = False

        # Detect section headers (e.g., "1. Introduction", "Abstract", "References")
        if re.match(r"^(?:\d+[\.\)]\s+)?(?:Abstract|Introduction|Background|Methods?|"
                    r"Methodology|Results?|Discussion|Conclusion|References?|"
                    r"Bibliography|Appendix|Acknowledgments?|Related Work|"
                    r"Literature Review|Data|Analysis|Findings|"
                    r"\d+[\.\)]\s+\w)", stripped, re.IGNORECASE):
            cleaned.append(f"\n## {stripped}\n")
        else:
            cleaned.append(stripped)

    return "\n\n".join(cleaned)


def pdf_to_markdown(pdf_path: Path, md_path: Path) -> int:
    """Convert a PDF to markdown using PyMuPDF. Returns char count."""
    doc = fitz.open(str(pdf_path))
    pages: list[str] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Get text blocks in reading order
        blocks = page.get_text("blocks")
        # Sort blocks by vertical position then horizontal position
        blocks.sort(key=lambda b: (b[1], b[0]))
        page_text = "\n".join(b[4].strip() for b in blocks if b[4].strip())
        pages.append(page_text)

    doc.close()

    full_text = "\n\n".join(pages)
    full_text = extract_paper_sections(full_text)

    md_path.write_text(full_text, encoding="utf-8")
    return len(full_text)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if not SELECTED_PATH.exists():
        print("ERROR: No selected papers. Run bulk_expand_benchmark.py --select-only first.")
        sys.exit(1)

    data = json.loads(SELECTED_PATH.read_text())
    papers = data["papers"]
    print(f"Converting {len(papers)} papers to markdown...")

    success = 0
    for i, paper in enumerate(papers, 1):
        arxiv_id = paper["arxiv_id"]
        pdf_name = arxiv_id.replace("/", "_") + ".pdf"
        md_name = arxiv_id.replace("/", "_") + ".md"
        pdf_path = OTHERS_DIR / pdf_name
        md_path = OTHERS_DIR / md_name

        if not pdf_path.exists():
            print(f"[{i}/{len(papers)}] SKIP (no PDF): {arxiv_id}")
            continue

        if args.resume and md_path.exists() and md_path.stat().st_size > 200:
            print(f"[{i}/{len(papers)}] EXISTS ({md_path.stat().st_size} chars): {arxiv_id}")
            success += 1
            continue

        print(f"[{i}/{len(papers)}] Converting {arxiv_id} ({pdf_path.stat().st_size/1024:.0f}KB)...",
              end=" ", flush=True)
        t0 = time.time()
        try:
            n_chars = pdf_to_markdown(pdf_path, md_path)
            elapsed = time.time() - t0
            print(f"OK ({n_chars} chars, {elapsed:.1f}s)")
            success += 1
        except Exception as e:
            elapsed = time.time() - t0
            print(f"FAIL ({elapsed:.1f}s): {e}")

    print(f"\n{'='*60}")
    print(f"Converted {success}/{len(papers)} PDFs to markdown")
    print(f"Output: {OTHERS_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
