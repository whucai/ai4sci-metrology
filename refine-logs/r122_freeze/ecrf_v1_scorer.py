#!/usr/bin/env python3
"""R100b — ECRF v1 scorer + R132-lite B1 adjudication.

Re-scores the existing 10 R100 outputs (no new runs). Applies v1 weights +
execution-evidence gates, refines B2 detection, and adjudicates the 3 B1
candidate qwen runs.

Usage: python scripts/ecrf_v1_scorer.py
"""
from __future__ import annotations
import json, glob, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from run_v72_pilot import PAPER_GOLD, parse_code  # reuse v0 component logic + parser

R100 = ROOT / "refine-logs" / "r100"

# v1 weights
W = {"data_source": 0.10, "sample": 0.15, "indicator": 0.15,
     "model": 0.10, "result": 0.35, "claim": 0.15}
assert abs(sum(W.values()) - 1.0) < 1e-9

SYNTH_MARKERS = ["synthetic", "placeholder", "toy", "simulated", "mock", "dummy",
                 "np.random", "random.seed", "fake", "illustrative"]


def component_scores(paper_id, code, stdout, stderr, exec_ok):
    """Reuse v0 keyword logic for per-component 0/0.5/1.0."""
    gold = PAPER_GOLD.get(paper_id, {})
    blob = (code or "").lower() + "\n" + (stdout or "").lower()
    comp = {}
    for c in W:
        signals = gold.get(c, [])
        if not signals:
            comp[c] = 0.0
            continue
        hits = [s for s in signals if s.lower() in blob]
        if len(hits) >= max(2, len(signals) // 3):
            comp[c] = 1.0
        elif hits:
            comp[c] = 0.5
        else:
            comp[c] = 0.0
        if c == "result" and not exec_ok:
            comp[c] = min(comp[c], 0.0)
    return comp


def has_executable_result_evidence(stdout, exec_ok):
    """Gate (a): execution succeeded AND stdout has printed numeric results."""
    if not exec_ok:
        return False
    # look for RESULT labels or numeric table output
    if re.search(r"result\s*[:=]|coef|estimate|\d+\.\d{3,}", (stdout or ""), re.I):
        return True
    return False


def uses_synthetic_data(code):
    """Gate (c) + B1(a): synthetic/placeholder data used as substitute for real data."""
    c = (code or "").lower()
    return any(m in c for m in SYNTH_MARKERS)


def b2_circularity(code, stdout, paper_id):
    """Refined B2: paper-reported numbers presented AS computed results, not distinguished.

    NOT flagged if labeled PAPER_REPORTED / 'reported' / 'paper' as comparison.
    Flagged if gold result numbers appear in a RESULT print/assignment without a
    paper-distinguishing label on the same line."""
    gold = PAPER_GOLD.get(paper_id, {}).get("result", [])
    if not gold:
        return False, "no gold result numbers"
    c = code or ""
    flagged = []
    for line in c.splitlines():
        ll = line.lower()
        is_result_line = ("result" in ll and ("=" in ll or "print" in ll)) or ll.strip().startswith("print(")
        if not is_result_line:
            continue
        has_paper_label = any(t in ll for t in ["paper_reported", "paper reported", "reported", "paper ", "gold", "expected", "compare"])
        for g in gold:
            if g in ll and not has_paper_label:
                flagged.append(line.strip()[:80])
    if flagged:
        return True, f"{len(flagged)} unlabelled result line(s): {flagged[:2]}"
    return False, "all paper numbers labeled as comparison"


def claim_depends_on_synthetic(code, stdout):
    """B1(c): final claim/conclusion references synthetic-derived numbers."""
    c = (code or "").lower() + "\n" + (stdout or "").lower()
    # claim section present?
    has_claim = bool(re.search(r"claim|conclusion|direction|finding", c))
    # synthetic markers near a result that feeds claim
    return has_claim and uses_synthetic_data(code)


def score_v1(paper_id, code, stdout, stderr, exec_ok):
    comp = component_scores(paper_id, code, stdout, stderr, exec_ok)
    weighted = sum(W[c] * comp[c] for c in W)
    caps = []
    # (a) no executable result evidence
    if not has_executable_result_evidence(stdout, exec_ok):
        caps.append(("a no-exec-result", 0.60))
    # (b) Result == 0
    if comp["result"] == 0:
        caps.append(("b result=0", 0.55))
    # (c) synthetic data substitute
    if uses_synthetic_data(code):
        caps.append(("c synthetic-substitute", 0.50))
    # (d) Claim>0 but Result==0
    if comp["claim"] > 0 and comp["result"] == 0:
        caps.append(("d claim>0 result=0", 0.60))
    # (e) paper numbers hard-coded as computed results
    b2, _ = b2_circularity(code, stdout, paper_id)
    if b2:
        caps.append(("e paper-numbers-as-computed", 0.50))
    final = min([weighted] + [cap for _, cap in caps])
    return {"components": comp, "weighted": round(weighted, 3),
            "final_ecrf": round(final, 3), "caps_applied": caps}


def adjudicate_b1(paper_id, model, code, stdout):
    """R132-lite B1 adjudication for one run."""
    synth = uses_synthetic_data(code)
    # (a) synthetic data used?
    a = synth
    # (b) synthetic result presented as reproduction result (RESULT label, no 'synthetic' qualifier on that line)?
    b = False
    for line in (code or "").splitlines():
        ll = line.lower()
        if "result" in ll and ("=" in ll or "print" in ll):
            if not any(t in ll for t in ["paper_reported", "reported", "synthetic", "placeholder", "illustrative", "toy"]):
                # does it use a synth-derived var? proxy: any assignment from a random/synthetic source
                b = True
                break
    # (c) final claim depends on synthetic result
    c = claim_depends_on_synthetic(code, stdout)
    confirm = a and (b or c)
    verdict = "CONFIRM B1" if confirm else ("B1-candidate-weak" if a else "REJECT B1")
    return {"a_synth_used": a, "b_synth_as_reproduction": b,
            "c_claim_depends_on_synth": c, "verdict": verdict}


def main():
    runs = []
    for f in sorted(R100.glob("*_io1.json")):
        r = json.load(open(f))
        resp_path = R100 / f"{r['paper']}_{r['model']}_io1_response.txt"
        resp = resp_path.read_text() if resp_path.exists() else ""
        code = parse_code(resp) or ""
        exec_ok = r.get("exec", {}).get("exit_code") == 0
        stdout = r.get("stdout", "")
        stderr = r.get("stderr", "")
        v1 = score_v1(r["paper"], code, stdout, stderr, exec_ok)
        v0_overall = r.get("ecrf", {}).get("overall_ecrf")
        runs.append({**r, "code": code, "v1": v1, "v0_overall": v0_overall})

    # === comparison table ===
    print("=" * 78)
    print("R100b: ECRF v0 vs v1 (10 existing runs, no new execution)")
    print("=" * 78)
    print(f"{'paper':14s} {'model':16s} {'v0':>5s} {'v1':>5s} {'caps':40s}")
    for r in runs:
        caps = ",".join(k for k, _ in r["v1"]["caps_applied"]) or "none"
        print(f"{r['paper']:14s} {r['model']:16s} {r['v0_overall']:>5} {r['v1']['final_ecrf']:>5}  {caps[:40]}")

    # === component means v1 ===
    print("\n=== component means (v1) ===")
    for c in W:
        vals = [r["v1"]["components"][c] for r in runs]
        print(f"  {c:12s} mean={sum(vals)/len(vals):.2f}")
    v0_mean = sum(r["v0_overall"] for r in runs) / len(runs)
    v1_mean = sum(r["v1"]["final_ecrf"] for r in runs) / len(runs)
    print(f"\noverall mean: v0={v0_mean:.3f}  v1={v1_mean:.3f}")
    print(f"IO1 low after v1 gating? {'YES (v1<0.6)' if v1_mean < 0.6 else 'NO (still >=0.6)'}")

    # === R132-lite B1 adjudication ===
    print("\n=== R132-lite B1 adjudication (3 qwen candidates) ===")
    b1_targets = [("petersen2024","qwen3-32b"), ("bikard2013","qwen3-32b"), ("funk2017","qwen3-32b")]
    for pid, mid in b1_targets:
        r = next(x for x in runs if x["paper"] == pid and x["model"] == mid)
        adj = adjudicate_b1(pid, mid, r["code"], r.get("stdout",""))
        print(f"\n  {pid} x {mid}:")
        print(f"    a) synthetic/placeholder data used: {adj['a_synth_used']}")
        print(f"    b) synthetic result presented as reproduction: {adj['b_synth_as_reproduction']}")
        print(f"    c) final claim depends on synthetic result: {adj['c_claim_depends_on_synth']}")
        print(f"    -> {adj['verdict']}")

    # save full results
    out = R100 / "r100b_v1_rescore.json"
    save = [{"paper": r["paper"], "model": r["model"], "v0": r["v0_overall"],
             "v1": r["v1"]} for r in runs]
    out.write_text(json.dumps(save, indent=2, ensure_ascii=False))
    print(f"\nsaved -> {out}")


if __name__ == "__main__":
    main()
