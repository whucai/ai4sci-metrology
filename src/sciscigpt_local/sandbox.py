"""Local sandbox executor — runs Python/R/Julia code in subprocess.

Replacement for SciSciGPT's Jupyter kernel sandbox (func/jupyter.py).
No GCP, no container yet — just subprocess isolation.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import os
import json
import time
from pathlib import Path


def _capture_env(python_exe: str) -> dict:
    """Capture Python version and installed packages for environment reporting."""
    try:
        ver = subprocess.run([python_exe, "--version"], capture_output=True, text=True, timeout=10)
        pkgs = subprocess.run(
            [python_exe, "-c", "import pkg_resources; "
             "dists = sorted(pkg_resources.working_set, key=lambda d: d.key); "
             "print(','.join(f'{d.key}=={d.version}' for d in dists[:20]))"],
            capture_output=True, text=True, timeout=10,
        )
        return {
            "python_version": ver.stdout.strip() or ver.stderr.strip(),
            "top_packages": pkgs.stdout.strip()[:500],
        }
    except Exception:
        return {"python_version": "unknown", "top_packages": "unknown"}


def execute_python(code: str, timeout: int = 30, workdir: str | None = None) -> dict:
    """Execute Python code in a subprocess sandbox.

    Args:
        code: Python code to execute.
        timeout: Max execution seconds.
        workdir: Working directory for the subprocess.

    Returns:
        {"stdout": str, "stderr": str, "exit_code": int, "elapsed": float}
    """
    workdir = workdir or tempfile.mkdtemp(prefix="sandbox_")
    script_path = Path(workdir) / "script.py"
    script_path.write_text(code)

    # Use the same Python that's running this process (conda env, not system python)
    python_exe = os.environ.get("SANDBOX_PYTHON", sys.executable)

    # Add project root to PYTHONPATH so sandboxed code can import project modules
    project_root = str(Path(__file__).resolve().parent.parent.parent)
    sandbox_env = {**os.environ, "PYTHONUNBUFFERED": "1",
                   "PYTHONPATH": project_root + ":" + os.environ.get("PYTHONPATH", "")}

    # Capture environment info before execution
    env_info = _capture_env(python_exe)

    start = time.time()
    try:
        result = subprocess.run(
            [python_exe, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
            env=sandbox_env,
        )
        elapsed = time.time() - start
        return {
            "stdout": result.stdout[-50000:],
            "stderr": result.stderr[-5000:],
            "exit_code": result.returncode,
            "elapsed": round(elapsed, 2),
            "environment": env_info,
        }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return {
            "stdout": "",
            "stderr": f"Execution timed out after {timeout}s",
            "exit_code": -1,
            "elapsed": round(elapsed, 2),
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "stdout": "",
            "stderr": f"Execution error: {e}",
            "exit_code": -1,
            "elapsed": round(elapsed, 2),
        }


def execute_r(code: str, timeout: int = 30, workdir: str | None = None) -> dict:
    """Execute R code in a subprocess sandbox."""
    workdir = workdir or tempfile.mkdtemp(prefix="sandbox_r_")
    script_path = Path(workdir) / "script.R"
    script_path.write_text(code)

    start = time.time()
    try:
        result = subprocess.run(
            ["Rscript", str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
        )
        elapsed = time.time() - start
        return {
            "stdout": result.stdout[-50000:],
            "stderr": result.stderr[-5000:],
            "exit_code": result.returncode,
            "elapsed": round(elapsed, 2),
        }
    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": "Rscript not found. Install R or skip R tests.",
            "exit_code": -1,
            "elapsed": 0.0,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "", "stderr": f"Timed out after {timeout}s",
            "exit_code": -1, "elapsed": round(time.time() - start, 2),
        }


def execute_julia(code: str, timeout: int = 30, workdir: str | None = None) -> dict:
    """Execute Julia code in a subprocess sandbox."""
    workdir = workdir or tempfile.mkdtemp(prefix="sandbox_jl_")
    script_path = Path(workdir) / "script.jl"
    script_path.write_text(code)

    start = time.time()
    try:
        result = subprocess.run(
            ["julia", str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
        )
        elapsed = time.time() - start
        return {
            "stdout": result.stdout[-50000:],
            "stderr": result.stderr[-5000:],
            "exit_code": result.returncode,
            "elapsed": round(elapsed, 2),
        }
    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": "Julia not found. Install Julia or skip Julia tests.",
            "exit_code": -1,
            "elapsed": 0.0,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "", "stderr": f"Timed out after {timeout}s",
            "exit_code": -1, "elapsed": round(time.time() - start, 2),
        }
