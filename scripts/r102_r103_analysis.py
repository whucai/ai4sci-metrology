#!/usr/bin/env python3
"""R102 (IO3) v2 scoring + IO3 code-usage detection + R103 aggregation.

Scorer v2 exactly as R101b (no changes to weights/gates). Re-scores IO1 and IO2
with v2 for a consistent IO1<IO2<IO3 monotonicity test. Then R103 gates.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from run_v72_pilot import PAPER_GOLD, parse_code
from ecrf_v1_scorer import uses_synthetic_data, b2_circularity, adjudicate_b1, SYNTH_MARKERS, W
from ecrf_v2_scorer import (score_v2, classify_result_lines_v2,
                            component_scores_v2, has_executable_result_evidence_v2)

R100 = ROOT / "refine-logs" / "r100"
R101 = ROOT / "refine-logs" / "r101"
R102 = ROOT / "refine-logs" / "r102"


def load_runs(d):
    runs = []
    for f in sorted(d.glob("*_io*.json")):
        r = json.load(open(f))
        io = r.get("io", 1)
        resp_path = d / f"{r['paper']}_{r['model']}_io{io}_response.txt"
        resp = resp_path.read_text() if resp_path.exists() else ""
        code = parse_code(resp) or ""
        exec_ok = r.get("exec", {}).get("exit_code") == 0
        runs.append({**r, "code": code, "exec_ok": exec_ok,
                     "stdout": r.get("stdout", ""),
                     "data_provided": bool(r.get("io2_data_files") or r.get("io3_ref_code_files") and (Path(d.parent)/"pilot"/r["paper"]/f"IO{io}"/"raw_data").exists())})
    return runs


def io3_code_usage(code, ref_code_files):
    """Detect: used_reference, modified_reference, synthesized_despite_io3, embedded_paper_values."""
    c = (code or "").lower()
    ref_avail = bool(ref_code_files)
    used_ref = ref_avail and any(
        p in c for p in ["original_code", "reproduce_final", "reproduce_v0_fixed", "cdindex_ref",
                         "import reproduce", "from reproduce", "exec(open(", "runpy.run_path",
                         "/workspace/original_code"])
    # modified reference: mentions original_code AND has own edits (proxy: ref path mentioned + own def/main)
    modified = used_ref and bool(re.search(r"^def |^class |if __name__", code or "", re.M))
    synth_despite = ref_avail and uses_synthetic_data(code)
    return {"ref_available": ref_avail, "used_reference": used_ref,
            "modified_reference": modified, "synth_despite_io3": synth_despite}


def main():
    io1 = load_runs(R100)
    io2 = load_runs(R101)
    io3 = load_runs(R102)

    # score all three with v2 (consistent scorer)
    for runs, lvl in [(io1,1),(io2,2),(io3,3)]:
        for r in runs:
            dp = bool(r.get("io2_data_files")) or (lvl==3 and bool(r.get("io3_ref_code_files")))
            # for IO1 data_provided is always False
            if lvl == 1: dp = False
            r["v2"] = score_v2(r["paper"], r["code"], r["stdout"], r.get("stderr",""), r["exec_ok"], dp)
            r["data_provided"] = dp

    # === R102 run status + IO3 code usage ===
    print("=" * 84)
    print("R102 (IO3) — 10 runs, scorer v2 (unchanged from R101b)")
    print("=" * 84)
    print(f"\n{'paper':14s} {'model':16s} {'v2':>5} {'ref?':>5} {'mod?':>5} {'synth?':>6} {'caps':34s}")
    usage_counts = Counter()
    for r in io3:
        u = io3_code_usage(r["code"], r.get("io3_ref_code_files", []))
        r["io3_usage"] = u
        for k in ["used_reference","modified_reference","synth_despite_io3"]:
            if u[k]: usage_counts[k]+=1
        caps = ",".join(k for k,_ in r["v2"]["caps_applied"]) or "none"
        print(f"{r['paper']:14s} {r['model']:16s} {r['v2']['final_ecrf']:>5} "
              f"{u['used_reference']!s:>5} {u['modified_reference']!s:>5} {u['synth_despite_io3']!s:>6}  {caps[:34]}")
    print(f"\nIO3 code-usage: used_ref={usage_counts['used_reference']}/10, "
          f"modified={usage_counts['modified_reference']}/10, synth_despite_io3={usage_counts['synth_despite_io3']}/10")

    # === R103: monotonicity ===
    print("\n" + "=" * 84)
    print("R103 — IO1 (v2) vs IO2 (v2) vs IO3 (v2)")
    print("=" * 84)
    m1 = sum(r["v2"]["final_ecrf"] for r in io1)/len(io1)
    m2 = sum(r["v2"]["final_ecrf"] for r in io2)/len(io2)
    m3 = sum(r["v2"]["final_ecrf"] for r in io3)/len(io3)
    print(f"\noverall means: IO1={m1:.3f}  IO2={m2:.3f}  IO3={m3:.3f}")
    print(f"GATE 1 (monotonic IO1<IO2<IO3): {'PASS' if m1<m2<m3 else 'FAIL'}")

    print("\nper-paper × IO-level (v2):")
    print(f"  {'paper':14s} {'IO1':>6} {'IO2':>6} {'IO3':>6} {'monotonic?'}")
    mono_papers = 0
    for p in sorted(set(r["paper"] for r in io1)):
        a = [r["v2"]["final_ecrf"] for r in io1 if r["paper"]==p]
        b = [r["v2"]["final_ecrf"] for r in io2 if r["paper"]==p]
        c = [r["v2"]["final_ecrf"] for r in io3 if r["paper"]==p]
        ma,mb,mc = sum(a)/len(a), sum(b)/len(b), sum(c)/len(c)
        m = ma<mb<mc
        if m: mono_papers+=1
        print(f"  {p:14s} {ma:>6.3f} {mb:>6.3f} {mc:>6.3f} {'✓' if m else '✗'}")
    print(f"\nGATE 1 detail: monotonic in {mono_papers}/5 papers (criterion: ≥4/5)")

    # component heterogeneity (component × IO slope)
    print("\ncomponent means across IO levels:")
    print(f"  {'component':12s} {'IO1':>6} {'IO2':>6} {'IO3':>6} {'slope(1->3)':>12}")
    hetero = 0
    for c in W:
        a = sum(r["v2"]["components"][c] for r in io1)/len(io1)
        b = sum(r["v2"]["components"][c] for r in io2)/len(io2)
        cc = sum(r["v2"]["components"][c] for r in io3)/len(io3)
        slope = cc - a
        if abs(slope) > 0.1: hetero += 1
        print(f"  {c:12s} {a:>6.2f} {b:>6.2f} {cc:>6.2f} {slope:>+12.2f}")
    print(f"\nGATE 2 (component heterogeneity, ≥2 components |slope|>0.1): {'PASS' if hetero>=2 else 'FAIL'} ({hetero})")

    # result vs component disagreement
    print("\nresult-vs-component disagreement (components OK but Result=0):")
    disagree = 0
    for runs,lvl in [(io1,1),(io2,2),(io3,3)]:
        for r in runs:
            others = sum(r["v2"]["components"][c] for c in ["indicator","model","claim"])/3
            if others > 0.5 and r["v2"]["components"]["result"] == 0:
                disagree += 1
    print(f"  disagreement cases across 30 runs: {disagree}")
    print(f"GATE 3 (≥1 result≠component disagreement): {'PASS' if disagree>=1 else 'FAIL'} ({disagree})")

    # evidence-break feasibility (B1-B4 across all 30)
    print("\nevidence-break candidates (B1-B4) across IO1+IO2+IO3 (30 runs):")
    bc = Counter()
    confirm_b1 = 0
    for runs,lvl in [(io1,1),(io2,2),(io3,3)]:
        for r in runs:
            b1 = uses_synthetic_data(r["code"])
            b2,_ = b2_circularity(r["code"], r["stdout"], r["paper"])
            b3 = any(k in r["code"].lower() for k in ["variant","model_1","scenario","specification","loop over"])
            b4 = r["v2"]["components"]["claim"]>0 and r["v2"]["components"]["result"]==0
            for f,y in [("B1",b1),("B2",b2),("B3",b3),("B4",b4)]:
                if y: bc[f]+=1
            if b1:
                adj = adjudicate_b1(r["paper"], r["model"], r["code"], r["stdout"])
                if "CONFIRM" in adj["verdict"]: confirm_b1 += 1
    print(f"  totals: {dict(bc)}")
    print(f"  B1 confirmed (R132-lite): {confirm_b1}")
    print(f"GATE 4 (≥1 B1-B4 candidate with audit trace): {'PASS' if sum(bc.values())>=1 else 'FAIL'} (candidates={sum(bc.values())})")

    # overall R103 verdict
    gates = {"G1 monotonicity (overall)": m1<m2<m3,
             "G1 monotonicity (≥4/5 papers)": mono_papers>=4,
             "G2 component heterogeneity": hetero>=2,
             "G3 disagreement exists": disagree>=1,
             "G4 break feasibility": sum(bc.values())>=1}
    print("\n" + "=" * 84)
    print("R103 VERDICT")
    print("=" * 84)
    for g,v in gates.items(): print(f"  {'PASS' if v else 'FAIL'} — {g}")
    passed = sum(gates.values())
    print(f"\n{passed}/{len(gates)} gates pass. (R103 pass rule: ≥3/4 of the original 4; G1 mandatory)")

    # save
    out = R102 / "r102_r103_aggregation.json"
    out.write_text(json.dumps({
        "io1_v2_mean": m1, "io2_v2_mean": m2, "io3_v2_mean": m3,
        "per_paper": {p: {"IO1": sum(r["v2"]["final_ecrf"] for r in io1 if r["paper"]==p)/2,
                          "IO2": sum(r["v2"]["final_ecrf"] for r in io2 if r["paper"]==p)/2,
                          "IO3": sum(r["v2"]["final_ecrf"] for r in io3 if r["paper"]==p)/2}
                      for p in sorted(set(r["paper"] for r in io1))},
        "gates": gates, "b_candidates": dict(bc), "b1_confirmed": confirm_b1,
        "io3_code_usage": dict(usage_counts),
        "io3_runs": [{"paper":r["paper"],"model":r["model"],"v2":r["v2"],"io3_usage":r.get("io3_usage")} for r in io3],
    }, indent=2, ensure_ascii=False))
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
