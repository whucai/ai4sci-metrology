#!/usr/bin/env python3
"""R101 analysis — IO₂ v1 scoring + IO₁ vs IO₂ comparison + result-line classification."""
from __future__ import annotations
import json, glob, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from run_v72_pilot import PAPER_GOLD, parse_code
from ecrf_v1_scorer import (component_scores, has_executable_result_evidence,
                            uses_synthetic_data, b2_circularity, score_v1, adjudicate_b1,
                            SYNTH_MARKERS)

R100 = ROOT / "refine-logs" / "r100"
R101 = ROOT / "refine-logs" / "r101"


def load_runs(d):
    runs = []
    for f in sorted(d.glob("*_io*.json")):
        r = json.load(open(f))
        io = r.get("io", 1)
        resp_path = d / f"{r['paper']}_{r['model']}_io{io}_response.txt"
        resp = resp_path.read_text() if resp_path.exists() else ""
        code = parse_code(resp) or ""
        exec_ok = r.get("exec", {}).get("exit_code") == 0
        stdout = r.get("stdout", "")
        runs.append({**r, "code": code, "exec_ok": exec_ok, "stdout": stdout})
    return runs


def classify_result_lines(code, stdout):
    """Classify every RESULT line as PAPER_REPORTED / DATA_SUB / COMPUTED / SYNTHETIC."""
    lines = []
    blob = (code or "") + "\n" + (stdout or "")
    for line in blob.splitlines():
        ll = line.lower()
        if not ("result" in ll and ("=" in ll or "coef" in ll or ":" in ll)):
            continue
        if not re.search(r"-?\d+\.\d{2,}", line):
            continue
        if "paper_reported" in ll or "reported" in ll or "gold" in ll or "expected" in ll:
            cls = "PAPER_REPORTED"
        elif "data_sub" in ll or "data-sub" in ll or "substitute" in ll:
            cls = "DATA_SUB"
        elif any(m in ll for m in SYNTH_MARKERS):
            cls = "SYNTHETIC"
        else:
            cls = "COMPUTED"
        lines.append((cls, line.strip()[:90]))
    return lines


def main():
    io1 = load_runs(R100)
    io2 = load_runs(R101)
    print(f"IO1 runs: {len(io1)}  IO2 runs: {len(io2)}\n")

    # === 1. R101 run status ===
    print("=" * 80)
    print("1. R101 (IO2) RUN STATUS")
    print("=" * 80)
    for r in io2:
        ex = r.get("exec", {})
        print(f"  {r['paper']:14s} x {r['model']:16s} status={r.get('status'):14s} "
              f"exit={ex.get('exit_code')} net_blocked={ex.get('network_blocked')} "
              f"leak={any(not f.startswith('_audit') for f in ex.get('files_written',[]))}")

    # === 2. v1 scores ===
    print("\n" + "=" * 80)
    print("2. ECRF v1 SCORES (IO2)")
    print("=" * 80)
    for r in io2:
        v1 = score_v1(r["paper"], r["code"], r["stdout"], r.get("stderr",""), r["exec_ok"])
        r["v1"] = v1
        caps = ",".join(k for k,_ in v1["caps_applied"]) or "none"
        print(f"  {r['paper']:14s} x {r['model']:16s} v1={v1['final_ecrf']:.3f} caps: {caps}")

    # === 3. IO1 vs IO2 comparison ===
    # re-score IO1 with v1 (from r100b_v1_rescore.json)
    io1_rescore = json.load(open(R100 / "r100b_v1_rescore.json"))
    io1_map = {(x["paper"], x["model"]): x["v1"]["final_ecrf"] for x in io1_rescore}

    print("\n" + "=" * 80)
    print("3. IO1 vs IO2 (v1 overall)")
    print("=" * 80)
    print(f"  {'paper':14s} {'model':16s} {'IO1':>6} {'IO2':>6} {'delta':>7}")
    io2_means_by_paper = {}
    for r in io2:
        i1 = io1_map.get((r["paper"], r["model"]), None)
        i2 = r["v1"]["final_ecrf"]
        delta = i2 - i1 if i1 is not None else None
        print(f"  {r['paper']:14s} {r['model']:16s} {i1!s:>6} {i2:>6.3f} {delta!s:>7}")
        io2_means_by_paper.setdefault(r["paper"], []).append(i2)

    io1_mean = sum(io1_map.values())/len(io1_map)
    io2_mean = sum(r["v1"]["final_ecrf"] for r in io2)/len(io2)
    print(f"\n  overall mean: IO1={io1_mean:.3f}  IO2={io2_mean:.3f}  delta={io2_mean-io1_mean:+.3f}")
    print(f"  SUCCESS CRITERION (IO2 > IO1=0.490): {'PASS' if io2_mean > 0.490 else 'FAIL'}")

    # per-paper
    print("\n  per-paper IO2 mean:")
    for p, vals in sorted(io2_means_by_paper.items()):
        print(f"    {p:14s} IO2 mean={sum(vals)/len(vals):.3f}")

    # per-model
    print("\n  per-model IO2 mean:")
    for m in ["qwen3-32b","deepseek-v4-pro"]:
        vals = [r["v1"]["final_ecrf"] for r in io2 if r["model"]==m]
        print(f"    {m:16s} IO2 mean={sum(vals)/len(vals):.3f}")

    # === component means (esp Sample, Result) ===
    print("\n  component means IO1 vs IO2:")
    for c in ["data_source","sample","indicator","model","result","claim"]:
        i1c = [x["v1"]["components"][c] for x in io1_rescore]
        i2c = [r["v1"]["components"][c] for r in io2]
        print(f"    {c:12s} IO1={sum(i1c)/len(i1c):.2f}  IO2={sum(i2c)/len(i2c):.2f}  delta={sum(i2c)/len(i2c)-sum(i1c)/len(i1c):+.2f}")
    i1_res = sum(x["v1"]["components"]["result"] for x in io1_rescore)/len(io1_rescore)
    i2_res = sum(r["v1"]["components"]["result"] for r in io2)/len(io2)
    print(f"\n  RESULT criterion (IO2 Result > IO1=0.35): {'PASS' if i2_res > 0.35 else 'FAIL'} (IO2 Result={i2_res:.2f})")

    # === 4. result-line classification ===
    print("\n" + "=" * 80)
    print("4. RESULT-LINE CLASSIFICATION (IO2)")
    print("=" * 80)
    from collections import Counter
    all_cls = Counter()
    for r in io2:
        cls = classify_result_lines(r["code"], r["stdout"])
        c = Counter(x[0] for x in cls)
        all_cls += c
        print(f"  {r['paper']:14s} x {r['model']:16s}: {dict(c)}")
    print(f"\n  totals: {dict(all_cls)}")

    # === 5. verify gate (c) doesn't fire on legitimate DATA_SUB ===
    print("\n" + "=" * 80)
    print("5. SYNTHETIC GATE (c) vs DATA_SUB — does it misfire?")
    print("=" * 80)
    for r in io2:
        synth = uses_synthetic_data(r["code"])
        has_data = bool(r.get("io2_data_files"))
        cls = classify_result_lines(r["code"], r["stdout"])
        used_data_sub = any(x[0]=="DATA_SUB" for x in cls) or (has_data and not synth)
        gate_c = any(k=="c synthetic-substitute" for k,_ in r["v1"]["caps_applied"])
        flag = "⚠ MISFIRE" if (used_data_sub and gate_c and not synth) else ""
        print(f"  {r['paper']:14s} x {r['model']:16s} data_provided={has_data} synth_code={synth} "
              f"gate_c_fired={gate_c} {flag}")

    # === 6. B-candidate counts (refined) ===
    print("\n" + "=" * 80)
    print("6. B1-B4 CANDIDATES (IO2, refined rules)")
    print("=" * 80)
    bcounts = Counter()
    for r in io2:
        code, stdout = r["code"], r["stdout"]
        b1 = uses_synthetic_data(code)
        b2, _ = b2_circularity(code, stdout, r["paper"])
        b3 = any(k in code.lower() for k in ["variant","model_1","scenario","specification","loop over"])
        b4 = r["v1"]["components"]["claim"]>0 and r["v1"]["components"]["result"]==0
        flags = [x for x,y in [("B1",b1),("B2",b2),("B3",b3),("B4",b4)] if y]
        for f in flags: bcounts[f]+=1
        print(f"  {r['paper']:14s} x {r['model']:16s}: {','.join(flags) if flags else 'none'}")
    print(f"\n  totals: {dict(bcounts)}")

    # === 7. spot-adjudicate B1 candidates ===
    print("\n" + "=" * 80)
    print("7. B1 SPOT-ADJUDICATION (IO2 synth-presented-as-reproduction)")
    print("=" * 80)
    for r in io2:
        if uses_synthetic_data(r["code"]):
            adj = adjudicate_b1(r["paper"], r["model"], r["code"], r["stdout"])
            print(f"  {r['paper']:14s} x {r['model']:16s}: a={adj['a_synth_used']} b={adj['b_synth_as_reproduction']} c={adj['c_claim_depends_on_synth']} -> {adj['verdict']}")

    # save
    out = R101 / "r101_v1_rescore.json"
    out.write_text(json.dumps([{"paper":r["paper"],"model":r["model"],"io":2,
                                "v1":r["v1"],"io1_v1":io1_map.get((r["paper"],r["model"]))} for r in io2], indent=2))
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
