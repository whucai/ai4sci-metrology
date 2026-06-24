"""Isolated code executor — R097 hardening (Evidence-Chain Theory v7.2).

Design (per user decision 2026-06-24):
  * Model/control plane (LLM that GENERATES code) runs OUTSIDE — it may use network.
  * Execution workspace (code that RUNS) is isolated: a Docker container with
    --network none and a filesystem jail.

Isolation guarantees enforced per run:
  * --network none              → no outbound/inbound network (enforces IO₁ "no web",
                                   blocks paper-value fetch / B₂ external lookup)
  * --rm                        → container + filesystem wiped after each run (no
                                   cross-condition leakage; anti-claim A4)
  * only `workdir` is mounted   → cannot read host home, caches, benchmark pool,
                                   or sibling IOx/ folders (filesystem jail)
  * workdir mounted read-write at /workspace; everything else default read-only image fs
  * per-run audit log           → stdout/stderr/exit + manifest of workdir files

The image for real runs should contain the scientific stack (numpy/pandas/statsmodels/
scikit-learn). For the R097 isolation TEST we use python:3.11-slim to prove the
containment properties; data-science image built separately before R100.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

WORKSPACE_MOUNT = "/workspace"  # in-container path


def execute_python_isolated(
    code: str,
    workdir: str | Path,
    *,
    image: str = "python:3.11-slim",
    timeout: int = 120,
    mem_limit: str = "2g",
    cpus: str = "2",
) -> dict:
    """Run `code` in a no-network, filesystem-jailed container.

    Args:
        code: Python source to execute.
        workdir: HOST path mounted read-write at /workspace. Must be a per-run
                directory containing ONLY the IOx/ materials for this condition.
        image: Docker image with the needed runtime.
        timeout: Wall-clock seconds (container is killed past this).
        mem_limit / cpus: Resource caps.

    Returns:
        {"stdout", "stderr", "exit_code", "elapsed", "files_written", "network_blocked"}
        `files_written` lists workdir contents after the run (process-integrity audit).
        `network_blocked` reports whether a reachability probe inside the run failed
        (True = blocked, as required).
    """
    workdir = Path(workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    # Make workdir traversable so the container (run as host uid) can access it;
    # tempfile.mkdtemp creates 0700 which blocks bind-mount access.
    workdir.chmod(0o755)
    script = workdir / "script.py"
    script.write_text(code)

    # Audit: snapshot workdir contents before/after.
    before = {p.name for p in workdir.iterdir()}

    # Run the user code. The audit wrapper also probes network reachability.
    wrapper = (
        "import socket,sys,json\n"
        "net={'reachable':False,'err':''}\n"
        "try:\n"
        "    s=socket.create_connection(('1.1.1.1',53),timeout=3); net['reachable']=True; s.close()\n"
        "except Exception as e: net['err']=type(e).__name__\n"
        "open('/workspace/_audit_net.json','w').write(json.dumps(net))\n"
    )
    (workdir / "_audit_probe.py").write_text(wrapper)
    user_cmd = f"{WORKSPACE_MOUNT}/script.py; python {WORKSPACE_MOUNT}/_audit_probe.py"

    import os as _os
    uid_gid = f"{_os.getuid()}:{_os.getgid()}"

    cmd = [
        "docker", "run", "--rm",
        "--network", "none",            # hard egress block
        f"--memory={mem_limit}",
        f"--cpus={cpus}",
        "--security-opt=no-new-privileges",
        "--cap-drop=ALL",
        "--user", uid_gid,              # match host uid:gid (no DAC_OVERRIDE needed)
        "--read-only",                  # container rootfs read-only
        "--tmpfs", "/tmp:rw,size=256m,mode=1777",  # writable scratch (pip/etc.)
        "-v", f"{workdir}:{WORKSPACE_MOUNT}:rw",
        "-w", WORKSPACE_MOUNT,
        image,
        "sh", "-c", f"python {user_cmd}",
    ]

    start = time.time()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
        stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return {
            "stdout": "", "stderr": f"Isolated execution timed out after {timeout}s",
            "exit_code": -1, "elapsed": round(time.time() - start, 2),
            "files_written": [], "network_blocked": None, "timed_out": True,
        }

    elapsed = round(time.time() - start, 2)
    after = {p.name for p in workdir.iterdir()}
    net_audit = {}
    net_file = workdir / "_audit_net.json"
    if net_file.exists():
        try:
            net_audit = json.loads(net_file.read_text())
        except Exception:
            net_audit = {"err": "unreadable"}

    return {
        "stdout": stdout[-50000:],
        "stderr": stderr[-5000:],
        "exit_code": exit_code,
        "elapsed": elapsed,
        "files_written": sorted(after - before),
        "network_blocked": not net_audit.get("reachable", False),
        "network_probe": net_audit,
    }


def is_docker_available() -> bool:
    return shutil.which("docker") is not None and subprocess.run(
        ["docker", "ps"], capture_output=True
    ).returncode == 0
