"""Dynamic Dockerfile generation — LLM reads paper → generates environment → builds container.

Module 2 of the IDEA_REPORT: the "environment construction" module.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any


DOCKERFILE_PROMPT = """You are a DevOps engineer. Generate a Dockerfile for reproducing a scientific paper.

Analysis plan from the paper:
{analysis_plan}

Dependencies extracted from the paper:
{dependencies}

Generate a Dockerfile that:
1. Uses a suitable base image (python:3.11-slim, rocker/r-ver, etc.)
2. Installs ALL listed dependencies via pip/conda/apt
3. Copies necessary source files
4. Sets WORKDIR and PYTHONPATH
5. Makes the container runnable with: docker run --rm <image> python reproduce.py

Include common scientific packages (numpy, scipy, pandas, matplotlib).
For R packages, use install2.r from littler or install.packages().

Output ONLY the Dockerfile content, no explanation. Start with FROM."""


def generate_dockerfile(
    paper_structure: dict[str, Any],
    llm: Any,
) -> str:
    """Generate a Dockerfile based on extracted paper structure.

    Args:
        paper_structure: Output from paper_ingestion.extract_paper_structure().
        llm: Language model.

    Returns:
        Dockerfile content as string.
    """
    from .paper_ingestion import format_analysis_plan

    plan = format_analysis_plan(paper_structure)
    deps = paper_structure.get("dependencies", [])
    deps_str = ", ".join(deps) if deps else "none detected"

    prompt = DOCKERFILE_PROMPT.format(analysis_plan=plan[:3000], dependencies=deps_str)

    response = llm.invoke([{"role": "user", "content": prompt}])
    text = str(response.content)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    # Extract Dockerfile from markdown code block
    match = re.search(r"```(?:dockerfile)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: text starting with FROM
    lines = text.strip().split("\n")
    for i, line in enumerate(lines):
        if line.strip().startswith("FROM "):
            return "\n".join(lines[i:]).strip()

    return text.strip()


def build_docker_image(
    dockerfile_content: str,
    image_name: str = "paper-reproduction",
    context_dir: str | None = None,
) -> dict[str, Any]:
    """Build a Docker image from generated Dockerfile.

    Args:
        dockerfile_content: Dockerfile text.
        image_name: Tag for the built image.
        context_dir: Build context directory (default: temp dir).

    Returns:
        {"success": bool, "image_name": str, "build_log": str}
    """
    context_dir = context_dir or tempfile.mkdtemp(prefix="docker_ctx_")
    df_path = os.path.join(context_dir, "Dockerfile")
    with open(df_path, "w") as f:
        f.write(dockerfile_content)

    try:
        result = subprocess.run(
            ["docker", "build", "-t", image_name, context_dir],
            capture_output=True, text=True, timeout=300,
        )
        return {
            "success": result.returncode == 0,
            "image_name": image_name,
            "build_log": (result.stdout + result.stderr)[-3000:],
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "image_name": image_name, "build_log": "Build timed out after 300s"}
    except FileNotFoundError:
        return {"success": False, "image_name": image_name, "build_log": "Docker not available"}


def run_in_container(
    image_name: str,
    command: str = "python reproduce.py",
    timeout: int = 120,
) -> dict[str, Any]:
    """Run a command inside a Docker container.

    Args:
        image_name: Docker image tag.
        command: Command to execute.
        timeout: Max execution seconds.

    Returns:
        {"exit_code": int, "stdout": str, "stderr": str}
    """
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", image_name] + command.split(),
            capture_output=True, text=True, timeout=timeout,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout[-5000:],
            "stderr": result.stderr[-5000:],
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": f"Timed out after {timeout}s"}
    except FileNotFoundError:
        return {"exit_code": -1, "stdout": "", "stderr": "Docker not available"}
