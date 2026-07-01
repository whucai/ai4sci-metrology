#!/usr/bin/env python3
"""R125 full aggregation — IO1/IO2/IO3 across all runs + Component x IO
mixed-effects + 3-mechanism-layer Table 1 + theorem-style claim.

Reads: refine-logs/r122 (IO1), r123 (IO2), r124 (IO3) per-run JSONs.
Writes: refine-logs/r125_full_aggregation.json, R125_FULL_AGGREGATION.md
"""
from __future__ import annotations
import json, glob, statistics, pathlib
from collections import defaultdict
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIRS = {1: ROOT/"refine-logs"/"r122", 2: ROOT/"refine-logs"/"r123", 3: ROOT/"refine-logs"/"r124"}
COMPONENTS = ["data_source","sample","indicator","model","result","claim"]
SKIP = {"deng2023_enhancing_disruption","galuez2023_technology_transfer"}

def load_io(io):
    rows = []
    for f in glob.glob(str(DIRS[io]/f"*_io{io}.json")):
        r = json.load(open(f))
        if r.get("status") != "DONE": continue
        if r["paper"] in SKIP: continue
        e = r.get("ecrf",{})
        if not isinstance(e,dict): continue
        comp = e.get("components",{})
        rows.append({"paper":r["paper"],"model":r["model"],"io":io,
                     "ecrf":e.get("final_ecrf"),
                     **{f"c_{c}": comp.get(c) for c in COMPONENTS},
                     "synth": r.get("process_evidence",{}).get("synthetic_generated"),
                     "real_data": r.get("process_evidence",{}).get("real_data_used"),
                     "refcode": r.get("process_evidence",{}).get("ref_code_used")})
    return rows

def main():
    allrows = []
    for io in (1,2,3): allrows += load_io(io)
    df = pd.DataFrame(allrows)
    df["ecrf"] = pd.to_numeric(df["ecrf"], errors="coerce")
    for c in COMPONENTS:
        df["c_"+c] = pd.to_numeric(df["c_"+c], errors="coerce")
    n_runs = len(df); n_papers = df["paper"].nunique()
    # ── per-IO means + monotonicity ──
    by_io = {io: round(df[df.io==io]["ecrf"].mean(),3) for io in (1,2,3)}
    by_io_model = {f"IO{io}_{m}": round(df[(df.io==io)&(df.model==m)]["ecrf"].mean(),3)
                   for io in (1,2,3) for m in ["qwen3-32b","deepseek-v4-pro"]}
    # per-paper monotonicity IO1<IO3
    pp = {}
    mono_count = 0
    for p in sorted(df.paper.unique()):
        s = df[df.paper==p].groupby("io")["ecrf"].mean().to_dict()
        e1, e3 = s.get(1), s.get(3)
        mono = (e1 is not None and e3 is not None and e3 > e1)
        if mono: mono_count += 1
        pp[p] = {"io1":round(e1,3) if e1 else None,"io2":round(s.get(2),3) if s.get(2) else None,
                 "io3":round(e3,3) if e3 else None,"mono_io1_lt_io3":mono}
    # ── Component x IO ──
    comp_io = {}
    for c in COMPONENTS:
        comp_io[c] = {io: round(df[df.io==io]["c_"+c].dropna().mean(),3) for io in (1,2,3)}
    # Component x IO mixed-effects (linear model: ecrf ~ io * component) -- use OLS on component scores
    long = df.melt(id_vars=["paper","model","io"], value_vars=["c_"+c for c in COMPONENTS], var_name="component", value_name="score")
    long = long.dropna(subset=["score"])
    try:
        import statsmodels.formula.api as smf
        # mixed-effects: score ~ io*component, group=paper
        m = smf.mixedlm("score ~ C(io)*component", long, groups=long["paper"], re_formula="1").fit(method="lbfgs", maxiter=200, disp=False)
        fe = m.fe_params.to_dict()
        pvals = m.pvalues.to_dict()
        interaction = {k: {"coef":round(v,4),"p":round(pvals.get(k,float('nan')),4)}
                       for k,v in fe.items() if "io" in k and "component" in k and ":" in k}
        me_summary = "converged" if m.converged else "not-converged"
    except Exception as e:
        interaction = {}; me_summary = f"mixed-model failed: {e}"
    # simpler: Component x IO ANOVA-style interaction (correlation of component slope with IO)
    slopes = {}
    for c in COMPONENTS:
        s = [comp_io[c][io] for io in (1,2,3) if comp_io[c][io] is not None]
        slopes[c] = round(s[-1]-s[0],3) if len(s)==3 else None  # IO3-IO1 slope

    # ── Table 1: 3-mechanism-layer collapse ──
    io3 = df[df.io==3]
    def block(runs, label):
        e = runs["ecrf"]
        return {"mechanism":label,"n":len(runs),
                "mean_ecrf":round(e.mean(),3) if len(e) else None,
                "floor_break_rate":round((e>0.505).mean(),3) if len(e) else None,
                "synth_rate":round(runs["synth"].mean(),3) if "synth" in runs else None}
    table1 = {
      "Layer 1 — code observability ≠ uptake": {
        "code present + refcode used": block(io3[io3.refcode==True], "code present + refcode used"),
        "code present + refcode NOT used": block(io3[io3.refcode==False], "code present + refcode not used"),
        "interpretation": "Code observability does not guarantee code uptake; refcode_used runs have lower/similar ECRF and higher synth.",
      },
      "Layer 2 — uptake (real data + no synthesis) drives floor-break": {
        "real_data + synth=False": block(io3[(io3.real_data==True)&(io3.synth==False)], "real_data ∧ ¬synth"),
        "real_data + synth=True": block(io3[(io3.real_data==True)&(io3.synth==True)], "real_data ∧ synth"),
        "interpretation": "real_data ∧ ¬synth is necessary + ~sufficient for floor-break (100%); synth collapses to 0.50.",
      },
      "Layer 3 — synthetic gate is structural (agentic shortcut collapse)": {
        "synth=True overall": block(io3[io3.synth==True], "synth=True"),
        "synth=False overall": block(io3[io3.synth==False], "synth=False"),
        "interpretation": "synth=True ⇒ ECRF≈0.50 (gate c mechanical); this is an agentic failure mode, not noise.",
      },
    }

    doc = {"n_runs":n_runs,"n_papers":n_papers,
           "by_io":by_io,"by_io_model":by_io_model,
           "monotonicity_io1_lt_io3":f"{mono_count}/{n_papers} papers",
           "per_paper":pp,
           "component_x_io_means":comp_io,
           "component_io3_minus_io1_slope":slopes,
           "mixed_effects": {"summary":me_summary, "interaction_terms":interaction},
           "table1_3layer":table1,
           "theorem_claim":
            "Proposition (Evidence-Chain Uptake). Let IO denote material observability "
            "(what evidence the agent is given), U denote agentic uptake (the agent incorporating "
            "real data into its execution chain and avoiding synthetic substitution), and F denote "
            "reconstruction fidelity (ECRF). Then: (i) IO is necessary but not sufficient for F; "
            "(ii) U mediates IO→F; specifically floor-break (F>0.50) is achieved iff (real_data_used "
            "∧ ¬synth), and is independent of refcode_used; (iii) synth (synthetic substitution) is a "
            "structural agentic failure mode that collapses F to the 0.50 gate regardless of IO. "
            "Corollary: code availability (IO3 ref_code_available) does not guarantee code uptake "
            "(refcode_used), and code uptake does not guarantee grounding (¬synth). Evidence: R124, "
            "n=34 DONE IO3 runs — real_data∧¬synth: 100% break (mean 0.703); synth=True: 0% break "
            "(mean 0.497); refcode_used: 25% break (3/4 still synthesized)."}
    (ROOT/"refine-logs"/"r125_full_aggregation.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False))

    # report
    print(f"=== R125 FULL AGREGATION (n_runs={n_runs}, n_papers={n_papers}) ===\n")
    print(f"Mean ECRF by IO: IO1={by_io[1]}  IO2={by_io[2]}  IO3={by_io[3]}")
    print(f"Monotonicity IO1<IO3: {mono_count}/{n_papers} papers")
    print(f"\nBy IO x model: {by_io_model}")
    print(f"\nComponent x IO means (IO1/IO2/IO3) + slope(IO3-IO1):")
    for c in COMPONENTS:
        m=comp_io[c]; print(f"  {c:14s} {m[1]} / {m[2]} / {m[3]}   slope={slopes[c]}")
    print(f"\nMixed-effects: {me_summary}")
    print(f"\n=== TABLE 1 (3-mechanism-layer collapse, IO3) ===")
    for layer, d in table1.items():
        print(f"\n{layer}")
        for k,v in d.items():
            if isinstance(v,dict):
                print(f"  {v['mechanism']:36s} n={v['n']} mean={v['mean_ecrf']} break={v['floor_break_rate']} synth={v['synth_rate']}")
            else:
                print(f"  -> {v}")
    print(f"\n=== THEOREM-STYLE CLAIM ===\n{doc['theorem_claim']}")

if __name__ == "__main__":
    main()
