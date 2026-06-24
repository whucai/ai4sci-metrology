# sciscigpt-ds:0.1 — reproducible data-science execution image (R097b)
#
# Build-time: network ALLOWED (pip install).
# Run-time:   network BLOCKED via `docker run --network none` (enforced by isolated_executor).
#
# Hardening contract (must hold at runtime):
#   --network none            (no egress)
#   --user <uid>:<gid>        (match host; no DAC_OVERRIDE needed)
#   --read-only               (rootfs read-only)
#   --tmpfs /tmp:rw,size=256m,mode=1777
#   only per-run workdir mounted rw at /workspace
#   no home dirs / caches / benchmark pool / sibling IO folders mounted
#
# Model/control plane (LLM that GENERATES code) runs OUTSIDE this image.
# Only CODE EXECUTION happens inside.

FROM python:3.11-slim

# Build-time deps for the scientific stack (compiled wheels need these at install).
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/sciscigpt-ds

COPY requirements.txt /opt/sciscigpt-ds/requirements.txt
RUN pip install --no-cache-dir -r /opt/sciscigpt-ds/requirements.txt

# Smoke-verify the stack importsable (build-time, network-independent).
RUN python -c "import numpy,pandas,scipy,statsmodels,sklearn,pyarrow,openpyxl,matplotlib,networkx,tqdm; print('DS stack OK')"

# Pre-create /workspace as a mount point (owned by root, but runtime --user writes via bind mount).
RUN mkdir -p /workspace && chmod 0755 /workspace

# Default command is a no-op; the executor overrides with `sh -c "python ..."` per run.
CMD ["python", "-c", "print('sciscigpt-ds:0.1 ready')"]
