#!/usr/bin/env python3
"""R125 SGF verdict (final format) — does IO3 break the synthetic floor,
and via what mechanism?

6-condition table + 3-category verdict + locked theoretical statement.
Does NOT modify prompts, scorer, gates, refcode detection, synth classifier,
or package structure (analysis-only on already-emitted R124 runs).

Conditions:
  1. has code + refcode used
  2. has code + refcode not used
  3. no code + real data used
  4. real data used + synth false
  5. real data used + synth true
  6. synth true overall
For each: n, mean ECRF, floor_break rate, real_data rate, synth rate.

3-category verdict (per run):
  - Clean SGF break:        real_data=True, synth=False, ECRF>0.50
  - Ambiguous SGF break:    ECRF>0.50 but refcode=False (code not the driver)
  - SGF persistence/counterexample: code available or refcode=True but synth=True and ECRF=0.50
"""
from __future__ import annotations
import json, glob, statistics, pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
R124 = ROOT / "refine-logs" / "r124"
MAN = json.loads((ROOT / "refine-logs" / "r122_freeze" / "io_manifests.json").read_text())["packages"]
MAN["zheng2025_male_female_retractions__io3"]["ref_code_available"] = False  # patch_001

def has_code(paper): return bool(MAN.get(f"{paper}__io3", {}).get("ref_code_available"))
FLOOR = 0.505
def broke(e): return e is not None and e > FLOOR

def load():
    runs = []
    for f in glob.glob(str(R124 / "*_io3.json")):
        r = json.load(open(f))
        if r.get("status") != "DONE":
            continue
        e = r.get("ecrf", {}).get("final_ecrf") if isinstance(r.get("ecrf"), dict) else None
        pe = r.get("process_evidence", {})
        runs.append({
            "paper": r["paper"], "model": r["model"], "ecrf": e,
            "has_code": has_code(r["paper"]),
            "refcode_used": bool(pe.get("ref_code_used")),
            "real_data_used": bool(pe.get("real_data_used")),
            "synth": bool(pe.get("synthetic_generated")),
            "exec_ok": bool(pe.get("execution_succeeded")),
            "paper_copied": bool(pe.get("paper_reported_copied")),
            "floor_break": broke(e),
        })
    return runs

def cond(runs, pred, label):
    sub = [r for r in runs if pred(r)]
    ecrfs = [r["ecrf"] for r in sub if r["ecrf"] is not None]
    return {
        "condition": label, "n": len(sub),
        "mean_ecrf": round(statistics.mean(ecrfs), 3) if ecrfs else None,
        "floor_break_rate": round(sum(r["floor_break"] for r in sub)/max(len(sub),1), 3) if sub else None,
        "real_data_rate": round(sum(r["real_data_used"] for r in sub)/max(len(sub),1), 3) if sub else None,
        "synth_rate": round(sum(r["synth"] for r in sub)/max(len(sub),1), 3) if sub else None,
    }

def categorize(r):
    if r["ecrf"] is not None and r["ecrf"] > FLOOR:
        if r["real_data_used"] and not r["synth"]:
            return "clean SGF break" if r["refcode_used"] else "ambiguous SGF break (refcode not used)"
        return "ambiguous SGF break (refcode not used)"
    # ECRF <= 0.50
    if (r["has_code"] or r["refcode_used"]) and r["synth"]:
        return "SGF persistence / counterexample"
    return "SGF persistence (no break)"

def main():
    runs = load()
    if not runs:
        print("no DONE IO3 runs yet"); return
    # ── 6-condition table ──
    conds = [
        cond(runs, lambda r: r["has_code"] and r["refcode_used"], "1. has code + refcode used"),
        cond(runs, lambda r: r["has_code"] and not r["refcode_used"], "2. has code + refcode NOT used"),
        cond(runs, lambda r: not r["has_code"] and r["real_data_used"], "3. no code + real data used"),
        cond(runs, lambda r: r["real_data_used"] and not r["synth"], "4. real data used + synth false"),
        cond(runs, lambda r: r["real_data_used"] and r["synth"], "5. real data used + synth true"),
        cond(runs, lambda r: r["synth"], "6. synth true overall"),
    ]
    # ── 3-category verdict ──
    for r in runs: r["category"] = categorize(r)
    cat_counts = Counter(r["category"] for r in runs)
    bypaper = {}
    for p in sorted(set(r["paper"] for r in runs)):
        pr = [r for r in runs if r["paper"] == p]
        c = Counter(r["category"] for r in pr).most_common(1)[0][0]
        bypaper[p] = {"has_code": pr[0]["has_code"], "category": c,
                      "per_model": [{"model": r["model"], "ecrf": r["ecrf"], "category": r["category"],
                                     "refcode_used": r["refcode_used"], "real_data_used": r["real_data_used"],
                                     "synth": r["synth"]} for r in pr]}

    # ITT + per-protocol (for the 4-layer narrative)
    treat = [r for r in runs if r["has_code"]]; ctrl = [r for r in runs if not r["has_code"]]
    used = [r for r in runs if r["refcode_used"]]; notused = [r for r in runs if not r["refcode_used"]]
    itt = {"treat_n":len(treat),"ctrl_n":len(ctrl),
           "treat_break":round(sum(r["floor_break"] for r in treat)/max(len(treat),1),3),
           "ctrl_break":round(sum(r["floor_break"] for r in ctrl)/max(len(ctrl),1),3)}
    pp = {"used_n":len(used),"notused_n":len(notused),
          "used_break":round(sum(r["floor_break"] for r in used)/max(len(used),1),3),
          "notused_break":round(sum(r["floor_break"] for r in notused)/max(len(notused),1),3)}

    doc = {"n_runs":len(runs),"n_papers":len(bypaper),
           "conditions":conds,"category_counts":dict(cat_counts),
           "ITT":itt,"per_protocol":pp,"verdict_per_paper":bypaper,
           "locked_theoretical_statement":
            "The IO3 rerun does not provide clean support for the simple code-availability "
            "hypothesis. Instead, the emerging evidence suggests a stronger uptake mechanism: "
            "executable evidence improves reconstruction only when the agent grounds its workflow "
            "in real data and avoids synthetic substitution. Code availability alone is insufficient. "
            "Mechanism: IO -> material availability; agent uptake -> evidence use; ECRF -> reconstruction fidelity."}
    (ROOT/"refine-logs"/"r125_sgf_verdict.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False))

    print(f"=== SGF VERDICT (R124 IO3, n_runs={len(runs)}, n_papers={len(bypaper)}) ===\n")
    print("6-condition table:")
    print(f"{'condition':42s} {'n':>3} {'meanECRF':>8} {'break%':>7} {'realdata%':>9} {'synth%':>6}")
    for c in conds:
        me = f"{c['mean_ecrf']:.3f}" if c['mean_ecrf'] is not None else "—"
        fb = f"{c['floor_break_rate']:.2f}" if c['floor_break_rate'] is not None else "—"
        rd = f"{c['real_data_rate']:.2f}" if c['real_data_rate'] is not None else "—"
        sy = f"{c['synth_rate']:.2f}" if c['synth_rate'] is not None else "—"
        print(f"{c['condition']:42s} {c['n']:>3} {me:>8} {fb:>7} {rd:>9} {sy:>6}")
    print(f"\nITT (has_code): treat break={itt['treat_break']} (n={itt['treat_n']}), ctrl break={itt['ctrl_break']} (n={itt['ctrl_n']})")
    print(f"Per-protocol (refcode_used): used break={pp['used_break']} (n={pp['used_n']}), not-used break={pp['notused_break']} (n={pp['notused_n']})")
    print(f"\n3-category verdict (per run): {dict(cat_counts)}")
    print("\nPer-paper verdict:")
    for p,v in bypaper.items():
        print(f"  [{v['category']:42s}] {'T' if v['has_code'] else 'C'} {p}")
    print("\nLocked theoretical statement:")
    print("  " + doc["locked_theoretical_statement"])

if __name__ == "__main__":
    main()
