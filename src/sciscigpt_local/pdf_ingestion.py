"""PDF ingestion via MinerU — parse PDF into structured Markdown for paper extraction.

Workflow:
  1. MinerU extracts PDF → Markdown (with tables, formulas, reading order)
  2. LLM reads Markdown → structured JSON (via paper_ingestion.extract_paper_structure)
  3. Structured JSON feeds into code generation + execution pipeline
"""

from __future__ import annotations

import os
import tempfile
import shutil
from pathlib import Path
from typing import Any


def parse_pdf_to_markdown(
    pdf_path: str,
    output_dir: str | None = None,
    method: str = "auto",
    lang: str | None = None,
    start_page: int = 0,
    end_page: int | None = None,
) -> dict[str, Any]:
    """Parse a PDF file into structured Markdown using MinerU.

    Args:
        pdf_path: Path to PDF file.
        output_dir: Where to write output (default: temp dir).
        method: 'auto', 'ocr', or 'txt'.
        lang: OCR language code (e.g. 'en', 'zh').
        start_page: First page to parse (0-indexed).
        end_page: Last page to parse (0-indexed, exclusive).

    Returns:
        {"markdown": str, "output_dir": str, "images_dir": str, "pages": int}
    """
    from magic_pdf.tools.common import do_parse
    from magic_pdf.data.data_reader_writer import FileBasedDataReader

    pdf_path = str(Path(pdf_path).resolve())
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    file_stem = Path(pdf_path).stem
    output_dir = output_dir or tempfile.mkdtemp(prefix="mineru_")

    reader = FileBasedDataReader(os.path.dirname(pdf_path))
    pdf_bytes = reader.read(os.path.basename(pdf_path))

    do_parse(
        output_dir,
        file_stem,
        pdf_bytes,
        [],
        method,
        start_page_id=start_page,
        end_page_id=end_page,
        lang=lang,
        f_dump_md=True,
        f_dump_middle_json=False,
        f_dump_model_json=False,
        f_dump_orig_pdf=False,
        f_dump_content_list=False,
    )

    # MinerU outputs to {output_dir}/{file_stem}/{method}/{file_stem}.md
    base_dir = os.path.join(output_dir, file_stem)
    md_path = os.path.join(base_dir, method, f"{file_stem}.md")
    if not os.path.exists(md_path):
        # Fallback: older MinerU or auto method may use different layout
        md_path = os.path.join(base_dir, f"{file_stem}.md")

    markdown_text = ""
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            markdown_text = f.read()

    images_dir = os.path.join(base_dir, method, "images")
    if not os.path.isdir(images_dir):
        images_dir = os.path.join(base_dir, "images")

    return {
        "markdown": markdown_text,
        "output_dir": os.path.join(output_dir, file_stem),
        "images_dir": images_dir if os.path.isdir(images_dir) else None,
        "pages": _count_pdf_pages(pdf_path),
    }


def _count_pdf_pages(pdf_path: str) -> int:
    """Count pages in a PDF file."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        n = len(doc)
        doc.close()
        return n
    except Exception:
        return -1


def extract_paper_from_pdf(
    pdf_path: str,
    llm: Any,
    output_dir: str | None = None,
    method: str = "auto",
) -> dict[str, Any]:
    """Full pipeline: PDF → MinerU markdown → LLM structured extraction.

    Args:
        pdf_path: Path to the paper PDF.
        llm: LangChain-compatible LLM for structured extraction.
        output_dir: Working directory for MinerU output.
        method: MinerU parse method.

    Returns:
        Dict with keys: markdown, structure, output_dir, pages
    """
    from .paper_ingestion import extract_paper_structure, format_analysis_plan

    result = parse_pdf_to_markdown(pdf_path, output_dir, method)

    if not result["markdown"]:
        return {**result, "structure": {}, "error": "MinerU produced empty output"}

    structure = extract_paper_structure(result["markdown"], llm)
    plan = format_analysis_plan(structure)

    return {
        **result,
        "structure": structure,
        "analysis_plan": plan,
    }
