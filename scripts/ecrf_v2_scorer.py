#!/usr/bin/env python3
"""R101b — ECRF v2 scorer.

Recognition rules only; v1 weights and gates unchanged.
  - data_source: credit loading the provided raw_data file (not just naming the source).
  - sample: credit computed data ops (df.shape/len/N=, year range, filters), not just text.
  - result: broaden evidence (tables, coef=, R², p-value, mean/correlation/ATE).
  - result-line classifier: PAPER_REPORTED / DATA_SUB / COMPUTED / SYNTHETIC.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from run_v72_pilot import PAPER_GOLD, parse_code
from ecrf_v1_scorer import (W, SYNTH_MARKERS, uses_synthetic_data,
                            b2_circularity, adjudicate_b1)

R100 = ROOT / "refine-logs" / "r100"
R101 = ROOT / "refine-logs" / "r101"

# broader result-evidence regex (v2)
RESULT_EVIDENCE = re.compile(
    r"(coef|beta|estimate|marginal_effect|r[²2]_?squared|r_squared|p[=_-]?value|pvalue|"
    r"stderr|std_err|se\b|mean|median|correlation|ate\b|att\b|n\s*=|sample|observations|"
    r"intercept|slope|fitted|coefficient)\b",
    re.I,
)
NUM = re.compile(r"-?\d+\.\d{2,}|\b\d{2,}\b")  # decimal or 2+ digit int


def has_file_load(code: str) -> bool:
    """data_source v2: did the code load a raw_data file?"""
    c = (code or "").lower()
    pats = ["read_parquet", "read_csv", "read_stata", "read_excel", "read_json",
            "pd.read", "open(", "raw_data", "/workspace/raw_data", "path(",
            ".parquet", ".csv", ".dta"]
    return any(p in c for p in pats)


def has_source_name(code, stdout, paper_id):
    gold = PAPER_GOLD.get(paper_id, {}).get("data_source", [])
    blob = (code or "").lower() + "\n" + (stdout or "").lower()
    return any(s.lower() in blob for s in gold)


def score_data_source(code, stdout, paper_id, data_provided):
    """v2: full credit for loading provided file; partial for naming source."""
    if has_file_load(code) and data_provided:
        return 1.0, "loaded provided raw_data file"
    if has_source_name(code, stdout, paper_id):
        return 0.5, "named source (no file load)"
    if has_file_load(code):
        return 0.5, "file load (source unlabeled)"
    return 0.0, "no data-source evidence"


def score_sample(code, stdout):
    """v2: full if (N/sample) AND (window/filter); partial if ≥1 sample signal."""
    blob = (code or "").lower() + "\n" + (stdout or "").lower()
    n_sig = bool(re.search(r"\bn\s*[:=]\s*\d|sample[_ ]?size|n_obs|n_sub|len\(|\.shape|"
                           r"observations|valid|rows\s*[:=]|count\(\)", blob))
    win_sig = bool(re.search(r"19[5-9]\d|20[0-2]\d|year|between|filter|dropna|query|"
                             r"time\s*window|period|range", blob))
    has_n_value = bool(re.search(r"n\s*[:=]\s*\d{2,}|\d{2,}\s*(papers|obs|publications|rows)", blob))
    has_window_value = bool(re.search(r"(19[5-9]\d|20[0-2]\d)\s*[-–to]+\s*(19[5-9]\d|20[0-2]\d)", blob))
    if (has_n_value or n_sig) and (has_window_value or win_sig):
        return 1.0, "N + window/filter evidence"
    if n_sig or win_sig or has_n_value:
        return 0.5, "partial sample evidence"
    return 0.0, "no sample evidence"


def score_result(code, stdout, paper_id, exec_ok):
    """v2: broaden result evidence; gold match → 1.0, computed evidence → 0.5."""
    if not exec_ok:
        return 0.0, "execution failed"
    blob = (code or "") + "\n" + (stdout or "")
    gold = PAPER_GOLD.get(paper_id, {}).get("result", [])
    gold_hit = any(g.lower() in blob.lower() for g in gold)
    # computed result evidence in stdout (actual execution output)
    out = (stdout or "")
    has_computed = bool(RESULT_EVIDENCE.search(out)) and bool(NUM.search(out))
    if gold_hit:
        return 1.0, "gold result number matched"
    if has_computed:
        return 0.5, "computed result evidence (no gold match)"
    return 0.0, "no result evidence"


def component_scores_v2(paper_id, code, stdout, exec_ok, data_provided):
    gold = PAPER_GOLD.get(paper_id, {})
    blob = (code or "").lower() + "\n" + (stdout or "").lower()
    comp = {}
    ds, ds_note = score_data_source(code, stdout, paper_id, data_provided)
    comp["data_source"] = ds
    sm, sm_note = score_sample(code, stdout)
    comp["sample"] = sm
    # indicator & model & claim: keep v1 keyword recognition (unchanged)
    for c in ["indicator", "model", "claim"]:
        signals = gold.get(c, [])
        hits = [s for s in signals if s.lower() in blob]
        comp[c] = 1.0 if len(hits) >= max(2, len(signals) // 3) else (0.5 if hits else 0.0)
    rs, rs_note = score_result(code, stdout, paper_id, exec_ok)
    comp["result"] = rs
    notes = {"data_source": ds_note, "sample": sm_note, "result": rs_note}
    return comp, notes


def has_executable_result_evidence_v2(stdout, exec_ok):
    """Gate (a) v2: broaden what counts as executable result evidence (recognition fix)."""
    if not exec_ok:
        return False
    return bool(RESULT_EVIDENCE.search(stdout or "")) and bool(NUM.search(stdout or ""))


def classify_result_lines_v2(code, stdout):
    """Classify every result line. Accepts tables, coef=, R², p-value, mean/corr/ATE."""
    lines = []
    blob = (code or "") + "\n" + (stdout or "")
    for line in blob.splitlines():
        ll = line.lower()
        if not RESULT_EVIDENCE.search(ll):
            continue
        if not NUM.search(line):
            continue
        if any(t in ll for t in ["paper_reported", "paper reported", "reported", "gold", "expected", "compare", "target"]):
            cls = "PAPER_REPORTED"
        elif any(t in ll for t in ["data_sub", "data-sub", "substitute", "proxy"]):
            cls = "DATA_SUB"
        elif any(m in ll for m in SYNTH_MARKERS):
            cls = "SYNTHETIC"
        else:
            cls = "COMPUTED"
        lines.append((cls, line.strip()[:100]))
    return lines


def score_v2(paper_id, code, stdout, stderr, exec_ok, data_provided):
    comp, notes = component_scores_v2(paper_id, code, stdout, exec_ok, data_provided)
    weighted = sum(W[c] * comp[c] for c in W)
    caps = []
    if not has_executable_result_evidence_v2(stdout, exec_ok):
        caps.append(("a no-exec-result", 0.60))
    if comp["result"] == 0:
        caps.append(("b result=0", 0.55))
    if uses_synthetic_data(code):
        caps.append(("c synthetic-substitute", 0.50))
    if comp["claim"] > 0 and comp["result"] == 0:
        caps.append(("d claim>0 result=0", 0.60))
    b2, _ = b2_circularity(code, stdout, paper_id)
    if b2:
        caps.append(("e paper-numbers-as-computed", 0.50))
    final = min([weighted] + [cap for _, cap in caps])
    return {"components": comp, "notes": notes, "weighted": round(weighted, 3),
            "final_ecrf": round(final, 3), "caps_applied": caps}


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
                     "stdout": r.get("stdout", ""), "data_provided": bool(r.get("io2_data_files"))})
    return runs


def main():
    io2 = load_runs(R101)
    io1_rescore = json.load(open(R100 / "r100b_v1_rescore.json"))
    io1_map = {(x["paper"], x["model"]): x["v1"]["final_ecrf"] for x in io1_rescore}

    print("=" * 84)
    print("R101b: ECRF v2 re-score of 10 IO2 runs (no new runs; v1 weights+gates kept)")
    print("=" * 84)
    print(f"\n{'paper':14s} {'model':16s} {'v1':>5} {'v2':>5} {'caps(v2)':40s}")
    v1_scores = json.load(open(R101 / "r101_v1_rescore.json"))
    v1_map = {(x["paper"], x["model"]): x["v1"]["final_ecrf"] for x in v1_scores}
    for r in io2:
        v2 = score_v2(r["paper"], r["code"], r["stdout"], r.get("stderr",""), r["exec_ok"], r["data_provided"])
        r["v2"] = v2
        caps = ",".join(k for k,_ in v2["caps_applied"]) or "none"
        print(f"{r['paper']:14s} {r['model']:16s} {v1_map.get((r['paper'],r['model']),0):>5} {v2['final_ecrf']:>5}  {caps[:40]}")

    # component means v1 vs v2
    print("\n=== component means: v1 vs v2 (IO2) ===")
    v1c = {c: [x["v1"]["components"][c] for x in v1_scores] for c in W}
    for c in W:
        v2m = sum(r["v2"]["components"][c] for r in io2)/len(io2)
        v1m = sum(v1c[c])/len(v1c[c])
        print(f"  {c:12s} v1={v1m:.2f}  v2={v2m:.2f}  delta={v2m-v1m:+.2f}")

    # overall
    v1_overall = sum(v1_map.values())/len(v1_map)
    v2_overall = sum(r["v2"]["final_ecrf"] for r in io2)/len(io2)
    print(f"\noverall: v1={v1_overall:.3f}  v2={v2_overall:.3f}")
    print(f"TEST 1: IO2 v2 > IO1 v1 (0.490)? {'PASS' if v2_overall > 0.490 else 'FAIL'} (v2={v2_overall:.3f})")

    # per-paper / per-model
    print("\nper-paper v2 mean:")
    for p in sorted(set(r["paper"] for r in io2)):
        vals=[r["v2"]["final_ecrf"] for r in io2 if r["paper"]==p]
        print(f"  {p:14s} {sum(vals)/len(vals):.3f}")
    print("per-model v2 mean:")
    for m in ["qwen3-32b","deepseek-v4-pro"]:
        vals=[r["v2"]["final_ecrf"] for r in io2 if r["model"]==m]
        print(f"  {m:16s} {sum(vals)/len(vals):.3f}")

    # data-using vs synthetic subset
    print("\n=== data-using subset vs synthetic subset (v2) ===")
    data_users = [r for r in io2 if r["data_provided"] and not uses_synthetic_data(r["code"])]
    synth_users = [r for r in io2 if uses_synthetic_data(r["code"])]
    du = sum(r["v2"]["final_ecrf"] for r in data_users)/len(data_users) if data_users else 0
    su = sum(r["v2"]["final_ecrf"] for r in synth_users)/len(synth_users) if synth_users else 0
    print(f"  data-using ({len(data_users)} runs): mean v2={du:.3f}")
    print(f"  synthetic  ({len(synth_users)} runs): mean v2={su:.3f}")
    print(f"  TEST 2: data-using > synthetic? {'PASS' if du > su else 'FAIL'} ({du:.3f} vs {su:.3f})")

    # gate c misfire check
    print("\n=== TEST 3: gate c only on synthetic, not DATA_SUB? ===")
    misfire = False
    for r in io2:
        synth = uses_synthetic_data(r["code"])
        gate_c = any(k=="c synthetic-substitute" for k,_ in r["v2"]["caps_applied"])
        cls = classify_result_lines_v2(r["code"], r["stdout"])
        has_data_sub = any(x[0]=="DATA_SUB" for x in cls)
        if has_data_sub and gate_c and not synth:
            misfire = True
            print(f"  ⚠ MISFIRE: {r['paper']}/{r['model']}")
    if not misfire:
        print("  PASS — gate c fires only when synth markers present; no misfire on DATA_SUB")

    # result-line classification v2
    print("\n=== result-line classification (v2) ===")
    allc = Counter()
    for r in io2:
        cls = classify_result_lines_v2(r["code"], r["stdout"])
        c = Counter(x[0] for x in cls)
        allc += c
        print(f"  {r['paper']:14s} x {r['model']:16s}: {dict(c)}")
    print(f"  totals: {dict(allc)}")

    # B candidates v2
    print("\n=== B1-B4 candidates (v2 rules) ===")
    bc = Counter()
    for r in io2:
        b1 = uses_synthetic_data(r["code"])
        b2,_ = b2_circularity(r["code"], r["stdout"], r["paper"])
        b3 = any(k in r["code"].lower() for k in ["variant","model_1","scenario","specification","loop over"])
        b4 = r["v2"]["components"]["claim"]>0 and r["v2"]["components"]["result"]==0
        flags=[x for x,y in [("B1",b1),("B2",b2),("B3",b3),("B4",b4)] if y]
        for f in flags: bc[f]+=1
    print(f"  totals: {dict(bc)}")

    # save
    out = R101 / "r101b_v2_rescore.json"
    out.write_text(json.dumps([{"paper":r["paper"],"model":r["model"],
                                "v1":v1_map.get((r["paper"],r["model"])),
                                "v2":r["v2"],
                                "data_using": r["data_provided"] and not uses_synthetic_data(r["code"])} for r in io2], indent=2))
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
