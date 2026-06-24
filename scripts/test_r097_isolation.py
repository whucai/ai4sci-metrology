#!/usr/bin/env python3
"""R097 isolated-workspace test (Evidence-Chain Theory v7.2).

Proves the containment properties required before R100-R102:
  G-A  network egress is blocked            (--network none)
  G-B  cannot read host home directory      (filesystem jail)
  G-C  cannot read a sibling IO folder      (cross-condition leakage block)
  G-D  CAN write/read inside /workspace      (run is still functional)
  G-E  basic python execution succeeds       (sanity)
  G-F  container is removed after run        (no residue / anti-claim A4)

Run:  conda activate sciscigpt && python scripts/test_r097_isolation.py [image]
       default image = python:3.11-slim; pass sciscigpt-ds:0.1 to test the DS image.
Exit code 0 == all gates pass.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sciscigpt_local.isolated_executor import execute_python_isolated, is_docker_available

IMAGE = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("R097_IMAGE", "python:3.11-slim")
GATES = {}


def gate(name, cond, detail=""):
    GATES[name] = bool(cond)
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}: {detail}")
    return cond


def main():
    if not is_docker_available():
        print("SKIP: docker daemon not available")
        sys.exit(2)

    workdir = Path(tempfile.mkdtemp(prefix="r097_"))
    # create a sibling dir to prove it is NOT reachable from inside
    sibling = workdir.parent / ("sibling_leak_test_" + workdir.name.split("_")[-1])
    sibling.mkdir(exist_ok=True)
    (sibling / "SECRET.txt").write_text("should-not-be-readable")

    print(f"workdir: {workdir}")
    print(f"sibling (must be unreachable): {sibling}")

    # --- Probe code: asserts jail + records findings via exit code ---
    code = f"""
import os, sys
results = {{}}
# G-B: host home unreachable
try:
    import glob
    home_files = glob.glob('/home/*')
    results['home_glob'] = home_files[:3]
except Exception as e:
    results['home_glob_err'] = str(e)
# G-C: sibling unreachable (absolute path on host)
sib = {repr(str(sibling))}
results['sibling_exists'] = os.path.exists(sib)
# G-D: writable workspace
try:
    open('/workspace/_wtest.txt','w').write('ok')
    results['workspace_write'] = True
except Exception as e:
    results['workspace_write'] = str(e)
# G-E: basic exec + numeric
results['one_plus_one'] = 1+1
import json
open('/workspace/_probe.json','w').write(json.dumps(results))
"""
    out = execute_python_isolated(code, workdir, image=IMAGE, timeout=90)

    print("\n=== isolated run result ===")
    print(f"  exit_code={out['exit_code']}  elapsed={out['elapsed']}s")
    print(f"  network_blocked={out['network_blocked']}  probe={out.get('network_probe')}")
    if out["stderr"]:
        print(f"  stderr: {out['stderr'][:400]}")

    probe = {}
    pf = workdir / "_probe.json"
    if pf.exists():
        import json
        probe = json.loads(pf.read_text())
    print(f"  probe payload: {probe}")

    print("\n=== gates ===")
    gate("G-A network egress blocked", out.get("network_blocked") is True,
         f"reachable={out.get('network_probe', {}).get('reachable')}")
    gate("G-E container exec succeeded", out["exit_code"] == 0, f"exit={out['exit_code']}")
    gate("G-B host home unreachable", probe.get("home_glob") == [],
         f"home_glob={probe.get('home_glob')}")
    gate("G-C sibling folder unreachable", probe.get("sibling_exists") is False,
         f"sibling_exists={probe.get('sibling_exists')}")
    gate("G-D workspace writable", probe.get("workspace_write") is True,
         f"workspace_write={probe.get('workspace_write')}")
    gate("G-F basic numeric exec", probe.get("one_plus_one") == 2)

    # G-F2: container removed (docker ps should not list a lingering container of this image)
    import subprocess
    lingering = subprocess.run(
        ["docker", "ps", "--filter", f"ancestor={IMAGE}", "-q"],
        capture_output=True, text=True,
    ).stdout.strip()
    gate("G-F no lingering container", lingering == "", f"lingering={lingering[:40]}")

    passed = sum(GATES.values())
    total = len(GATES)
    print(f"\n=== {passed}/{total} gates passed ===")
    # cleanup
    import shutil
    shutil.rmtree(workdir, ignore_errors=True)
    shutil.rmtree(sibling, ignore_errors=True)
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
