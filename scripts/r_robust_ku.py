#!/usr/bin/env python3
"""R-robust-KU + clean-anchor + boundary-excluded robustness checks.

Pure re-analysis on frozen R125 outputs (R122/R123/R124 run JSONs).
No changes to experiments, prompts, packages, scorer, refcode detection, or synth classifier.

Checks:
  1. KU Leuven/Arts exclusion (drop arts2021, schaper2025, arts2021_patent_nlp)
  2. KU Leuven/Arts grouped sensitivity (keep full, flag cluster)
  3. Clean-anchor-only (only ref_code_available=True papers)
  4. Boundary-excluded (drop IO2/IO3-collapse papers per manifest+patch_001)

For each: mean ECRF by IO, IO1<IO2/IO1<IO3/IO2<IO3 status,
real_data^¬synth mean+break, synth=True mean+break, refcode used vs not,
H_EUC holds?
"""
from __future__ import annotations
import json, glob, statistics, pathlib
import pandas as pd
ROOT = pathlib.Path(__file__).resolve().parent.parent
DIRS = {1: ROOT/"refine-logs"/"r122", 2: ROOT/"refine-logs"/"r123", 3: ROOT/"refine-logs"/"r124"}
COMPONENTS = ["data_source","sample","indicator","model","result","claim"]
SKIP = {"deng2023_enhancing_disruption","galuez2023_technology_transfer"}
MAN = json.loads((ROOT/"refine-logs"/"r122_freeze"/"io_manifests.json").read_text())["packages"]
MAN["zheng2025_male_female_retractions__io2"]["data_provided"] = False
MAN["zheng2025_male_female_retractions__io3"]["ref_code_available"] = False
MAN["zheng2025_male_female_retractions__io3"]["data_provided"] = False

KU = {"arts2021","schaper2025_frontier","arts2021_patent_nlp"}
BOUNDARY = {"maddi2024","bikard2013","vasarhelyi2023_who_benefits","zheng2025_male_female_retractions","schaper2025_frontier"}
CLEAN_ANCHORS = {k.split("__")[0] for k in MAN if k.endswith("__io3") and MAN[k].get("ref_code_available")}  # ref_code available at IO3

def load():
    rows=[]
    for io in (1,2,3):
        for f in glob.glob(str(DIRS[io]/f"*_io{io}.json")):
            r=json.load(open(f))
            if r.get("status")!="DONE" or r["paper"] in SKIP: continue
            e=r.get("ecrf",{})
            if not isinstance(e,dict): continue
            comp=e.get("components",{})
            pe=r.get("process_evidence",{})
            rows.append({"paper":r["paper"],"model":r["model"],"io":io,
                         "ecrf":e.get("final_ecrf"),
                         **{f"c_{c}":comp.get(c) for c in COMPONENTS},
                         "synth":bool(pe.get("synthetic_generated")),
                         "real_data":bool(pe.get("real_data_used")),
                         "refcode":bool(pe.get("ref_code_used"))})
    df=pd.DataFrame(rows)
    df["ecrf"]=pd.to_numeric(df["ecrf"],errors="coerce")
    for c in COMPONENTS: df["c_"+c]=pd.to_numeric(df["c_"+c],errors="coerce")
    return df

def analyze(df, label, excluded_note=""):
    n_papers=df["paper"].nunique()
    by_io={io:round(df[df.io==io]["ecrf"].mean(),3) for io in (1,2,3)}
    def cmp(a,b):
        if by_io.get(a) is None or by_io.get(b) is None: return "n/a"
        return "YES" if by_io[b]>by_io[a] else "NO"
    # uptake splits (pooled across IO where process-evidence exists; IO2+IO3 have data; IO1 all synth)
    d=df[df.io>=2]  # uptake only meaningful at IO2/IO3 (data provided)
    def block(sub):
        e=sub["ecrf"]
        return {"n":len(sub),"mean":round(e.mean(),3) if len(e) else None,
                "break":round((e>0.505).mean(),3) if len(e) else None} if len(sub) else {"n":0,"mean":None,"break":None}
    ground=block(d[(d.real_data==True)&(d.synth==False)])
    synth=block(d[d.synth==True])
    used=block(d[d.refcode==True]); notused=block(d[d.refcode==False])
    # component x IO slopes
    slopes={}
    for c in COMPONENTS:
        m={io:df[df.io==io]["c_"+c].dropna().mean() for io in (1,2,3)}
        slopes[c]=round(m[3]-m[1],3) if pd.notna(m[1]) and pd.notna(m[3]) else None
    holds = (ground["break"] is not None and ground["break"]>=0.9 and
             synth["break"] is not None and synth["break"]<=0.1)
    return {"check":label,"excluded":excluded_note,"n_runs":len(df),"n_papers":n_papers,
            "mean_ecrf_IO":by_io,
            "IO1_lt_IO2":cmp(1,2),"IO1_lt_IO3":cmp(1,3),"IO2_lt_IO3":cmp(2,3),
            "real_data_AND_not_synth":ground,"synth_true":synth,
            "refcode_used":used,"refcode_not_used":notused,
            "component_IO3_minus_IO1_slope":slopes,
            "H_EUC_holds":holds}

def main():
    df=load()
    # 1. KU exclusion
    r1=analyze(df[~df.paper.isin(KU)], "1. KU Leuven/Arts EXCLUDED", f"dropped {sorted(KU)}")
    # 2. grouped sensitivity (full sample, KU vs non-KU)
    ku_runs=df[df.paper.isin(KU)]; nonku=df[~df.paper.isin(KU)]
    def grp(d):
        g=d[(d.real_data)&(~d.synth)]; s=d[d.synth]
        return {"n_runs":len(d),"n_papers":d.paper.nunique(),
                "mean_ecrf_IO":{io:round(d[d.io==io]["ecrf"].mean(),3) for io in (1,2,3)},
                "real_data_not_synth_break":round((g["ecrf"]>0.505).mean(),3) if len(g) else None,
                "synth_true_break":round((s["ecrf"]>0.505).mean(),3) if len(s) else None}
    r2={"check":"2. KU grouped sensitivity (full sample, KU vs non-KU)",
        "KU_cluster":grp(ku_runs),"non_KU":grp(nonku),
        "interpretation":"if non-KU shows the same uptake pattern (ground->break, synth->0.50), the result is NOT driven only by the KU cluster."}
    # 3. clean-anchor-only
    r3=analyze(df[df.paper.isin(CLEAN_ANCHORS)], "3. Clean-IO3-anchor ONLY", f"kept {sorted(CLEAN_ANCHORS)}")
    # 4. boundary-excluded
    r4=analyze(df[~df.paper.isin(BOUNDARY)], "4. Boundary EXCLUDED", f"dropped {sorted(BOUNDARY)}")
    # full (baseline)
    r0=analyze(df, "0. BASELINE (full sample)", "none")

    doc={"date":"2026-07-01","frozen":"R125 outputs + v2 scorer + v1 gates + gold v1-r3 (unchanged)",
         "baseline":r0,"checks":[r1,r2,r3,r4],
         "interpretation_rule":"Do NOT claim simple monotonic observability. Correct conclusion: observability increases material availability, but realized reconstruction fidelity depends on agentic uptake. Code availability alone is incomplete; real-data uptake + avoidance of synthetic substitution mediate ECRF."}
    (ROOT/"refine-logs"/"r_robust_ku.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False,default=str))

    # print
    for r in [r0,r1,r3,r4]:
        print(f"\n=== {r['check']} ===")
        print(f"  n_runs={r['n_runs']} n_papers={r['n_papers']}  excluded: {r['excluded']}")
        print(f"  mean ECRF: IO1={r['mean_ecrf_IO'][1]} IO2={r['mean_ecrf_IO'][2]} IO3={r['mean_ecrf_IO'][3]}")
        print(f"  IO1<IO2={r['IO1_lt_IO2']}  IO1<IO3={r['IO1_lt_IO3']}  IO2<IO3={r['IO2_lt_IO3']}")
        g=r['real_data_AND_not_synth']; s=r['synth_true']
        print(f"  real_data∧¬synth: n={g['n']} mean={g['mean']} break={g['break']}")
        print(f"  synth=True:       n={s['n']} mean={s['mean']} break={s['break']}")
        u=r['refcode_used']; nu=r['refcode_not_used']
        print(f"  refcode used:    n={u['n']} mean={u['mean']} break={u['break']}")
        print(f"  refcode not used:n={nu['n']} mean={nu['mean']} break={nu['break']}")
        print(f"  data_source slope={r['component_IO3_minus_IO1_slope']['data_source']}  model slope={r['component_IO3_minus_IO1_slope']['model']}  result slope={r['component_IO3_minus_IO1_slope']['result']}")
        print(f"  H_EUC holds (ground>=0.9 break & synth<=0.1 break): {r['H_EUC_holds']}")
    print("\n=== 2. KU grouped sensitivity ===")
    for k in ["KU_cluster","non_KU"]:
        v=r2[k]; print(f"  {k}: n_runs={v['n_runs']} n_papers={v['n_papers']} mean_IO={v['mean_ecrf_IO']} ground_break={v['real_data_not_synth_break']} synth_break={v['synth_true_break']}")

if __name__=="__main__":
    main()
