#!/usr/bin/env python3
"""R125 (interim) — IO1 -> IO2 delta analysis + 3-layer structural figure.

Core metric: dECRF = ECRF(IO2) - ECRF(IO1), per paper x model.
Three layers (paper-level classification):
  - synthetic floor: IO2 stayed ~0.5 (agent synthesized despite data; gate c capped)
  - partial grounding uplift: IO2 > 0.5 (agent loaded real data, synth=False)
  - boundary invariance: no data provided (data_provided=False), IO2 flat at 0.5

Outputs:
  refine-logs/r125_io1_io2_delta.json   (per-paper deltas + layer classification)
  refine-logs/figures/fig_io1_io2_3layer.png  (paper Figure 2/3 candidate)
  refine-logs/R125_IO1_IO2_DELTA_REPORT.md
"""
from __future__ import annotations
import json, glob, os, statistics, pathlib
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
R122 = ROOT / "refine-logs" / "r122"
R123 = ROOT / "refine-logs" / "r123"
FIG = ROOT / "refine-logs" / "figures"; FIG.mkdir(parents=True, exist_ok=True)

# frozen manifest for data_provided (boundary classification)
MAN = json.loads((ROOT / "refine-logs" / "r123" / "r123_io2_manifest.json").read_text())
# apply patch_001 (zheng2025_male -> boundary)
MAN["packages"]["zheng2025_male_female_retractions"]["data_provided"] = False
BOUNDARY = {pid for pid, e in MAN["packages"].items() if e.get("assembled") and not e.get("data_provided")}
SKIP = {"deng2023_enhancing_disruption", "galuez2023_technology_transfer"}

def load_runs(d, io):
    out = {}
    for f in glob.glob(str(d / f"*_io{io}.json")):
        r = json.load(open(f))
        if r.get("status") != "DONE":
            continue
        ecrf = r.get("ecrf", {}).get("final_ecrf") if isinstance(r.get("ecrf"), dict) else None
        pe = r.get("process_evidence", {})
        out[(r["paper"], r["model"])] = {
            "ecrf": ecrf, "exec": pe.get("execution_succeeded"),
            "real_data_used": pe.get("real_data_used"), "synth": pe.get("synthetic_generated"),
        }
    return out

io1 = load_runs(R122, 1)
io2 = load_runs(R123, 2)

# per paper-model delta
rows = []
for k in sorted(set(io1) | set(io2)):
    p, m = k
    if p in SKIP:
        continue
    e1 = io1.get(k, {}).get("ecrf")
    e2 = io2.get(k, {}).get("ecrf")
    if e1 is None or e2 is None:
        continue
    rows.append({"paper": p, "model": m, "io1": e1, "io2": e2, "delta": round(e2 - e1, 3),
                 "real_data_used": io2[k].get("real_data_used"), "synth_io2": io2[k].get("synth")})

# layer classification (paper-level: based on whether IO2 broke the floor using real data)
def layer_for(paper):
    if paper in BOUNDARY:
        return "boundary invariance"
    # look at the runs for this paper
    pr = [r for r in rows if r["paper"] == paper]
    if not pr:
        return "unknown"
    # if any run broke the floor with real data -> partial uplift
    uplift = [r for r in pr if r["io2"] > 0.52 and r["real_data_used"] and not r["synth_io2"]]
    if uplift:
        return "partial grounding uplift"
    # if runs stayed at floor despite data -> synthetic floor
    return "synthetic floor"

paper_layer = {p: layer_for(p) for p in sorted({r["paper"] for r in rows})}

# aggregate
deltas = [r["delta"] for r in rows]
uplift_deltas = [r["delta"] for r in rows if paper_layer[r["paper"]] == "partial grounding uplift"]
floor_deltas = [r["delta"] for r in rows if paper_layer[r["paper"]] == "synthetic floor"]
bound_deltas = [r["delta"] for r in rows if paper_layer[r["paper"]] == "boundary invariance"]

by_paper = {}
for p in sorted({r["paper"] for r in rows}):
    pr = [r for r in rows if r["paper"] == p]
    by_paper[p] = {"layer": paper_layer[p],
                   "io1_mean": round(statistics.mean(r["io1"] for r in pr), 3),
                   "io2_mean": round(statistics.mean(r["io2"] for r in pr), 3),
                   "delta_mean": round(statistics.mean(r["delta"] for r in pr), 3),
                   "n": len(pr)}

doc = {
    "metric": "dECRF = ECRF(IO2) - ECRF(IO1)",
    "n_runs": len(rows), "n_papers": len(by_paper),
    "mean_io1": round(statistics.mean(r["io1"] for r in rows), 3),
    "mean_io2": round(statistics.mean(r["io2"] for r in rows), 3),
    "mean_delta": round(statistics.mean(deltas), 3),
    "by_layer": {
        "partial grounding uplift": {"n_papers": sum(1 for p in by_paper if by_paper[p]["layer"]=="partial grounding uplift"),
            "mean_io1": round(statistics.mean(r["io1"] for r in rows if paper_layer[r["paper"]]=="partial grounding uplift"), 3) if uplift_deltas else None,
            "mean_delta": round(statistics.mean(uplift_deltas), 3) if uplift_deltas else None,
            "mean_io2": round(statistics.mean(r["io2"] for r in rows if paper_layer[r["paper"]]=="partial grounding uplift"), 3) if uplift_deltas else None},
        "synthetic floor": {"n_papers": sum(1 for p in by_paper if by_paper[p]["layer"]=="synthetic floor"),
            "mean_io1": round(statistics.mean(r["io1"] for r in rows if paper_layer[r["paper"]]=="synthetic floor"), 3) if floor_deltas else None,
            "mean_delta": round(statistics.mean(floor_deltas), 3) if floor_deltas else None,
            "mean_io2": round(statistics.mean(r["io2"] for r in rows if paper_layer[r["paper"]]=="synthetic floor"), 3) if floor_deltas else None},
        "boundary invariance": {"n_papers": sum(1 for p in by_paper if by_paper[p]["layer"]=="boundary invariance"),
            "mean_io1": round(statistics.mean(r["io1"] for r in rows if paper_layer[r["paper"]]=="boundary invariance"), 3) if bound_deltas else None,
            "mean_delta": round(statistics.mean(bound_deltas), 3) if bound_deltas else None,
            "mean_io2": round(statistics.mean(r["io2"] for r in rows if paper_layer[r["paper"]]=="boundary invariance"), 3) if bound_deltas else None},
    },
    "by_paper": by_paper,
    "per_run": rows,
}
(ROOT / "refine-logs" / "r125_io1_io2_delta.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False))

# ── FIGURE: 3-layer structural ──────────────────────────────────────────────
# Design: per-paper slope chart IO1 -> IO2, sorted by delta, colored by layer.
# Three horizontal bands visible: boundary (flat bottom), synthetic floor (flat mid),
# partial uplift (rising). Paper Figure 2/3 candidate.
LAYER_COLOR = {"partial grounding uplift": "#2E7D32",   # green (uplift)
               "synthetic floor": "#E65100",            # orange (stuck at synth floor)
               "boundary invariance": "#6A1B9A"}        # purple (boundary, no data)
LAYER_ORDER = {"partial grounding uplift": 0, "synthetic floor": 1, "boundary invariance": 2}

# sort papers: uplift (largest delta first), then floor, then boundary
papers_sorted = sorted(by_paper.keys(), key=lambda p: (LAYER_ORDER[paper_layer[p]], -by_paper[p]["delta_mean"]))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9), gridspec_kw={"width_ratios": [3, 2]})

# Panel A: slope chart per paper (mean across models), IO1 -> IO2
ypos = np.arange(len(papers_sorted))
io1_means = [by_paper[p]["io1_mean"] for p in papers_sorted]
io2_means = [by_paper[p]["io2_mean"] for p in papers_sorted]
colors = [LAYER_COLOR[paper_layer[p]] for p in papers_sorted]
for i, p in enumerate(papers_sorted):
    ax1.plot([io1_means[i], io2_means[i]], [i, i], "-", color=colors[i], lw=2.2, alpha=0.85)
    ax1.plot(io1_means[i], i, "o", color=colors[i], markersize=7)
    ax1.plot(io2_means[i], i, "s", color=colors[i], markersize=9)
    ax1.text(io2_means[i] + 0.015, i, f" +{by_paper[p]['delta_mean']:.2f}" if by_paper[p]['delta_mean']>=0 else f" {by_paper[p]['delta_mean']:.2f}",
             va="center", fontsize=8, color=colors[i])
ax1.axvline(0.5, color="grey", ls=":", lw=1, alpha=0.7)
ax1.set_yticks(ypos)
ax1.set_yticklabels(papers_sorted, fontsize=8)
ax1.set_xlabel("ECRF  (○ IO₁  →  ■ IO₂)", fontsize=11)
ax1.set_title("A.  Per-paper IO₁ → IO₂  (ΔECRF = IO₂ − IO₁)", fontsize=12, fontweight="bold")
ax1.set_xlim(0.42, 1.02)
ax1.invert_yaxis()
# legend
from matplotlib.lines import Line2D
handles = [Line2D([0],[0],color=c,lw=3,label=l.replace(" grounding"," ").replace(" invariance","")) for l,c in LAYER_COLOR.items()]
ax1.legend(handles=handles, loc="lower right", fontsize=9, framealpha=0.9)

# Panel B: 3-layer bar (mean IO1, IO2, delta by layer)
layers = ["partial grounding uplift", "synthetic floor", "boundary invariance"]
ld = doc["by_layer"]
x = np.arange(len(layers))
io1_b = [ld[l]["mean_io1"] for l in layers]  # all ~0.5
io2_b = [ld[l]["mean_io2"] for l in layers]
db = [ld[l]["mean_delta"] for l in layers]
wb = 0.38
ax2.bar(x - wb/2, io1_b, wb, color="#90A4AE", label="IO₁ (floor)")
ax2.bar(x + wb/2, io2_b, wb, color=[LAYER_COLOR[l] for l in layers], label="IO₂")
for i in range(len(layers)):
    ax2.text(x[i]+wb/2, io2_b[i]+0.01, f"Δ=+{db[i]:.2f}" if db[i]>=0 else f"Δ={db[i]:.2f}",
             ha="center", fontsize=9, fontweight="bold")
ax2.axhline(0.5, color="grey", ls=":", lw=1)
ax2.set_xticks(x)
ax2.set_xticklabels(["partial\nuplift", "synthetic\nfloor", "boundary\ninvariance"], fontsize=9)
ax2.set_ylabel("mean ECRF", fontsize=11)
ax2.set_title("B.  Three-layer structure", fontsize=12, fontweight="bold")
ax2.set_ylim(0, 1.05)
ax2.legend(loc="upper right", fontsize=9)

fig.suptitle("Figure 2.  IO₁ → IO₂ observability gradient — ΔECRF three-layer structure",
             fontsize=13, fontweight="bold", y=0.98)
fig.tight_layout(rect=[0,0,1,0.96])
fig.savefig(FIG / "fig_io1_io2_3layer.png", dpi=160, bbox_inches="tight")
print(f"Figure -> {FIG/'fig_io1_io2_3layer.png'}")
print(f"Delta JSON -> refine-logs/r125_io1_io2_delta.json")
print(f"\nmean IO1={doc['mean_io1']}  mean IO2={doc['mean_io2']}  mean Δ={doc['mean_delta']}")
for l in layers:
    d=doc["by_layer"][l]
    print(f"  {l:28s} n={d['n_papers']:2d}  mean_IO2={d['mean_io2']}  mean_Δ={d['mean_delta']}")
