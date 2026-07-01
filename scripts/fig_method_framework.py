#!/usr/bin/env python3
import os
import textwrap
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D

OUT = "refine-logs/figures/fig_method_framework.png"

COL = {
    "grey": "#90A4AE",
    "dark": "#263238",
    "green": "#2E7D32",
    "orange": "#E65100",
    "purple": "#6A1B9A",
    "light_grey": "#ECEFF1",
}

PAPERS = {
    "arts2021": {"layer": "partial grounding uplift", "io1_mean": 0.5, "io2_mean": 0.663},
    "arts2021_patent_nlp": {"layer": "synthetic floor", "io1_mean": 0.5, "io2_mean": 0.5},
    "bentley2023_disruption": {"layer": "partial grounding uplift", "io1_mean": 0.475, "io2_mean": 0.675},
    "bikard2013": {"layer": "boundary invariance", "io1_mean": 0.5, "io2_mean": 0.5},
    "donner2024_data_inaccuracy": {"layer": "synthetic floor", "io1_mean": 0.5, "io2_mean": 0.5},
    "funk2017": {"layer": "partial grounding uplift", "io1_mean": 0.5, "io2_mean": 0.6},
    "gebhart2023_math_framework": {"layer": "partial grounding uplift", "io1_mean": 0.5, "io2_mean": 0.55},
    "ke2015_sleeping_beauties": {"layer": "partial grounding uplift", "io1_mean": 0.5, "io2_mean": 0.9},
    "liu2018_hotstreaks": {"layer": "synthetic floor", "io1_mean": 0.5, "io2_mean": 0.5},
    "maddi2024": {"layer": "boundary invariance", "io1_mean": 0.5, "io2_mean": 0.5},
    "obadage2024_citations_repro": {"layer": "partial grounding uplift", "io1_mean": 0.5, "io2_mean": 0.75},
    "park2023_disruptive": {"layer": "partial grounding uplift", "io1_mean": 0.5, "io2_mean": 0.875},
    "petersen2024": {"layer": "synthetic floor", "io1_mean": 0.5, "io2_mean": 0.5},
    "schaper2025_frontier": {"layer": "synthetic floor", "io1_mean": 0.5, "io2_mean": 0.5},
    "sun2023_ranking_mobility": {"layer": "partial grounding uplift", "io1_mean": 0.5, "io2_mean": 0.525},
    "vasarhelyi2023_who_benefits": {"layer": "boundary invariance", "io1_mean": 0.5, "io2_mean": 0.5},
    "wu2019_teams": {"layer": "partial grounding uplift", "io1_mean": 0.5, "io2_mean": 0.7},
    "zheng2025_male_female_retractions": {"layer": "boundary invariance", "io1_mean": 0.5, "io2_mean": 0.575},
}

REGIME_STYLE = {
    "partial grounding uplift": {"color": COL["green"], "marker": "o", "label": "partial grounding uplift"},
    "synthetic floor": {"color": COL["orange"], "marker": "s", "label": "synthetic grounding failure (SGF)"},
    "boundary invariance": {"color": COL["purple"], "marker": "D", "label": "boundary invariance"},
}


def add_panel_label(ax, label):
    ax.text(-0.08, 1.04, label, transform=ax.transAxes, fontsize=16, fontweight="bold", va="bottom", ha="left", color=COL["dark"])


def rounded_box(ax, xy, w, h, fc, ec, text, fontsize=10, lw=1.7, ls="-", color=None):
    patch = FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.02,rounding_size=0.035", fc=fc, ec=ec, lw=lw, linestyle=ls)
    ax.add_patch(patch)
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fontsize, color=color or COL["dark"], linespacing=1.18)
    return patch


def arrow(ax, p0, p1, color=COL["dark"], lw=2.3, ms=14, rad=0.0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=ms, lw=lw, color=color, connectionstyle=f"arc3,rad={rad}", shrinkA=4, shrinkB=4))


def panel_a(ax):
    ax.set_title("IO observability gradient", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    boxes = [
        (0.08, 0.29, "IO1  Low\npaper text only\nsynthetic floor", COL["light_grey"], COL["grey"]),
        (0.25, 0.50, "IO2  Medium\n+ data dict + docs + raw_data\nno code\npartial uplift OR SGF", "#FFF3E0", COL["orange"]),
        (0.45, 0.72, "IO3  High\n+ original executable code\nbreaks SGF?", "#E8F5E9", COL["green"]),
    ]
    w, h = 0.46, 0.16
    for x, y, txt, fc, ec in boxes:
        rounded_box(ax, (x, y), w, h, fc, ec, txt, fontsize=9.4, lw=1.8)
    arrow(ax, (0.51, 0.38), (0.42, 0.50), lw=2.0)
    arrow(ax, (0.67, 0.59), (0.61, 0.72), lw=2.0)
    ax.plot([0.10, 0.90], [0.12, 0.12], color=COL["dark"], lw=2.2)
    arrow(ax, (0.10, 0.12), (0.91, 0.12), lw=2.2, ms=13)
    ax.text(0.10, 0.075, "0", ha="center", va="top", fontsize=9, color=COL["dark"])
    ax.text(0.90, 0.075, "1", ha="center", va="top", fontsize=9, color=COL["dark"])
    ax.text(0.50, 0.035, "ECRF", ha="center", va="top", fontsize=10, fontweight="bold", color=COL["dark"])
    ax.plot([0.50, 0.50], [0.10, 0.23], color=COL["orange"], lw=1.8, ls=(0, (4, 3)))
    ax.text(0.52, 0.205, "synthetic floor\n(gate c)", ha="left", va="center", fontsize=9, color=COL["orange"], fontweight="bold")
    ax.text(0.09, 0.94, "Gate (c): synthetic/placeholder data caps final ECRF at 0.50", ha="left", va="top", fontsize=9, color=COL["dark"])


def panel_b(ax):
    ax.set_title("Three regimes (IO1→IO2)", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlim(0.4, 1.0); ax.set_ylim(0.4, 1.0); ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("ECRF(IO1)", fontsize=10); ax.set_ylabel("ECRF(IO2)", fontsize=10)
    ticks = np.arange(0.4, 1.01, 0.1); ax.set_xticks(ticks); ax.set_yticks(ticks)
    ax.grid(True, color="#CFD8DC", lw=0.65, alpha=0.85)
    for s in ax.spines.values():
        s.set_linewidth(1.0); s.set_color(COL["dark"])
    ax.plot([0.4, 1.0], [0.4, 1.0], color=COL["grey"], lw=1.5, ls=(0, (4, 3)), zorder=1)
    ax.text(0.835, 0.87, "y = x", color=COL["grey"], fontsize=9, rotation=35)
    ax.axhspan(0.485, 0.515, color=COL["orange"], alpha=0.075, zorder=0)
    ax.axhline(0.50, color=COL["orange"], lw=1.7, ls=(0, (4, 3)), zorder=1)
    ax.text(0.405, 0.522, "floor band", fontsize=8.5, color=COL["orange"], ha="left", va="bottom")
    counts = {k: sum(v["layer"] == k for v in PAPERS.values()) for k in REGIME_STYLE}
    order = ["boundary invariance", "synthetic floor", "partial grounding uplift"]
    for layer in order:
        style = REGIME_STYLE[layer]; xs, ys = [], []
        for name, d in PAPERS.items():
            if d["layer"] == layer:
                xs.append(d["io1_mean"]); ys.append(d["io2_mean"])
        offsets = np.linspace(-0.006, 0.006, len(xs)) if len(xs) > 1 else np.array([0.0])
        xs = np.array(xs) + offsets * 0.35; ys = np.array(ys) + offsets
        ax.scatter(xs, ys, s=72, marker=style["marker"], facecolor=style["color"], edgecolor="white", linewidth=0.9, alpha=0.96, zorder=3)
    legend_handles = [Line2D([0],[0], marker=REGIME_STYLE[layer]["marker"], color="none", markerfacecolor=REGIME_STYLE[layer]["color"], markeredgecolor="white", markersize=8.5, label=f"{REGIME_STYLE[layer]['label']} (n={counts[layer]})") for layer in ["partial grounding uplift", "synthetic floor", "boundary invariance"]]
    ax.legend(handles=legend_handles, loc="lower right", bbox_to_anchor=(0.995, 0.02), frameon=True, framealpha=0.96, facecolor="white", edgecolor="#CFD8DC", fontsize=8.1, handlelength=1.2, borderpad=0.55, labelspacing=0.35)
    ax.annotate("data provided but synth=True\n→ gate (c) caps 0.50", xy=(0.50, 0.50), xytext=(0.61, 0.445), fontsize=8.8, color=COL["dark"], ha="left", va="center", arrowprops=dict(arrowstyle="-|>", color=COL["dark"], lw=1.5, shrinkA=2, shrinkB=5), bbox=dict(boxstyle="round,pad=0.28", fc="white", ec=COL["orange"], lw=1.2))


def row_flow(ax, y, name, out_text, arrow_color, box_color):
    rounded_box(ax, (0.06, y - 0.045), 0.33, 0.09, "white", COL["grey"], name, fontsize=8.2, lw=1.1)
    rounded_box(ax, (0.45, y - 0.045), 0.16, 0.09, "#FFF3E0", COL["orange"], "IO2\n0.50", fontsize=8.6, lw=1.4)
    arrow(ax, (0.62, y), (0.72, y), color=arrow_color, lw=2.0, ms=13)
    rounded_box(ax, (0.74, y - 0.045), 0.19, 0.09, "white", box_color, out_text, fontsize=8.8, lw=1.5, ls=(0, (4, 2)), color=box_color)


def panel_c(ax):
    ax.set_title("SGF test (R124)", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(Rectangle((0.04, 0.58), 0.90, 0.055, fc=COL["green"], ec=COL["green"], lw=0))
    ax.text(0.06, 0.607, "Treatment (public code)", color="white", fontsize=10, fontweight="bold", va="center")
    for y, name in zip([0.51, 0.40, 0.29], ["petersen2024", "liu2018_hotstreaks", "arts2021_patent_nlp"]):
        row_flow(ax, y, name, "IO3\n> 0.50?", COL["green"], COL["green"])
    ax.add_patch(Rectangle((0.04, 0.175), 0.90, 0.055, fc=COL["purple"], ec=COL["purple"], lw=0))
    ax.text(0.06, 0.202, "Control (no code)", color="white", fontsize=10, fontweight="bold", va="center")
    for y, name in zip([0.105, -0.005], ["donner2024_data_inaccuracy", "schaper2025_frontier"]):
        y_adj = max(y, 0.025); row_flow(ax, y_adj, name, "IO3\n= 0.50", COL["purple"], COL["purple"])
    caption = "H_SGF: executable code breaks the floor for code-bearing SGF papers; SGF persists without code (internal control)."
    ax.text(0.04, 0.965, textwrap.fill(caption, width=58), ha="left", va="top", fontsize=9, color=COL["dark"], linespacing=1.2)


def main():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10, "xtick.labelsize": 8.8, "ytick.labelsize": 8.8, "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white", "pdf.fonttype": 42, "ps.fonttype": 42})
    fig = plt.figure(figsize=(15, 7.2), dpi=200)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.04, 1.08, 1.0], wspace=0.30)
    ax_a = fig.add_subplot(gs[0, 0]); ax_b = fig.add_subplot(gs[0, 1]); ax_c = fig.add_subplot(gs[0, 2])
    panel_a(ax_a); panel_b(ax_b); panel_c(ax_c)
    add_panel_label(ax_a, "A"); add_panel_label(ax_b, "B"); add_panel_label(ax_c, "C")
    fig.suptitle("Figure 1. ECRF observability gradient — three regimes and the synthetic-grounding-failure (SGF) test", fontsize=15, fontweight="bold", y=0.985, color=COL["dark"])
    fig.subplots_adjust(left=0.045, right=0.985, top=0.895, bottom=0.095)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
