#!/usr/bin/env python3
"""Figure 1 sketch — renders the Codex-debated layout JSON (fig1_layout.json).
This is the SKETCH (step 2 of the pipeline) to be used as a condition for
step-3 native image generation."""
import json, math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, FancyArrowPatch

LAYOUT = json.loads(Path("refine-logs/figures/fig1_layout.json").read_text())

def center(e):
    p=e["position"]; return p["x"], p["y"]
def bbox(e):
    p=e["position"]; return p["x"]-p["width"]/2, p["y"]-p["height"]/2, p["width"], p["height"]
def boundary_point(e, target):
    x,y=center(e); tx,ty=target; p=e["position"]; w,h=p["width"],p["height"]
    dx,dy=tx-x,ty-y
    if abs(dx)<1e-9 and abs(dy)<1e-9: return x,y
    if e["type"]=="diamond":
        s=1.0/(abs(dx)/(w/2)+abs(dy)/(h/2)); return x+dx*s, y+dy*s
    s=min((w/2)/abs(dx) if abs(dx)>1e-9 else math.inf, (h/2)/abs(dy) if abs(dy)>1e-9 else math.inf)
    return x+dx*s, y+dy*s
def draw_text(ax,e):
    x,y=center(e)
    ax.text(x,y,e["text"],ha="center",va="center",fontsize=e["font_size"],
            fontweight=e["font_weight"],color=e.get("text_color","#263238"),linespacing=1.15,zorder=6)
def draw_box(ax,e):
    x0,y0,w,h=bbox(e); rounding=0.018 if e["type"]=="gate-bar" else 0.012
    lw=1.6 if e["type"]=="callout" else 1.4
    ax.add_patch(FancyBboxPatch((x0,y0),w,h,boxstyle=f"round,pad=0.008,rounding_size={rounding}",
                 linewidth=lw,edgecolor=e["edge_color"],facecolor=e["fill_color"],zorder=2))
    draw_text(ax,e)
def draw_diamond(ax,e):
    x,y=center(e); p=e["position"]; w,h=p["width"],p["height"]
    ax.add_patch(Polygon([(x,y+h/2),(x+w/2,y),(x,y-h/2),(x-w/2,y)],closed=True,
                 linewidth=1.5,edgecolor=e["edge_color"],facecolor=e["fill_color"],zorder=2))
    draw_text(ax,e)
def draw_arrow(ax,e,reg):
    src,dst=reg[e["connects_to"][0]],reg[e["connects_to"][1]]
    sx,sy=boundary_point(src,center(dst)); ex,ey=boundary_point(dst,center(src))
    is_callout=e["id"].startswith("arrow_callout")
    ls=(0,(4,3)) if is_callout else "solid"
    rad=0.0
    if e["id"]=="arrow_callout1_to_synth": rad=-0.12
    elif e["id"]=="arrow_callout2_to_uptake": rad=0.10
    elif e["id"]=="arrow_callout3_to_real": rad=0.12
    elif e["id"]=="arrow_gate_to_floor": rad=-0.12
    ax.add_patch(FancyArrowPatch((sx,sy),(ex,ey),arrowstyle="-|>",mutation_scale=18,
                 linewidth=2.0 if not is_callout else 1.6,color=e["edge_color"],linestyle=ls,
                 connectionstyle=f"arc3,rad={rad}",shrinkA=3,shrinkB=3,zorder=3))
    lbl=e["text"]
    if lbl and lbl!="dashed":
        px,py=e["position"]["x"],e["position"]["y"]
        ax.text(px,py,lbl,ha="center",va="center",fontsize=e["font_size"],fontweight=e["font_weight"],
                color=e.get("text_color",e["edge_color"]),
                bbox=dict(facecolor="#FFFFFF",edgecolor="none",pad=1.2,alpha=0.92),zorder=5)
def flatten():
    out=[]
    for r in LAYOUT["regions"].values(): out.extend(r)
    return out

def main():
    fig,ax=plt.subplots(figsize=(16,9),dpi=200)
    fig.patch.set_facecolor("#FFFFFF"); ax.set_facecolor("#FFFFFF")
    ax.set_xlim(0,1); ax.set_ylim(1,0); ax.axis("off")
    elems=flatten(); reg={e["id"]:e for e in elems}
    for e in elems:
        if e["type"] in {"box","callout","gate-bar"}: draw_box(ax,e)
        elif e["type"]=="diamond": draw_diamond(ax,e)
        elif e["type"]=="text": draw_text(ax,e)
    for e in elems:
        if e["type"]=="arrow": draw_arrow(ax,e,reg)
    for e in elems:
        if e["type"] in {"box","callout","gate-bar","diamond","text"}: draw_text(ax,e)
    out=Path("refine-logs/figures/fig1_sketch.png"); out.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(out,dpi=200,bbox_inches="tight",pad_inches=0.08,facecolor="#FFFFFF")
    plt.close(fig); print(f"sketch -> {out}")

if __name__=="__main__":
    main()
