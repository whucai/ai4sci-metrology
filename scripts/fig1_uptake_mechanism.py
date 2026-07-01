#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon, Circle
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe

OUT = "refine-logs/figures/fig1_uptake_mechanism.png"
COL = {"grey":"#90A4AE","green":"#2E7D32","orange":"#E65100","purple":"#6A1B9A","dark":"#263238","light_grey":"#ECEFF1","pale_green":"#E8F5E9","pale_orange":"#FFF3E0","pale_purple":"#F3E5F5","red":"#C62828","white":"#FFFFFF"}
plt.rcParams.update({"figure.facecolor":"white","axes.facecolor":"white","savefig.facecolor":"white","font.family":"DejaVu Sans","font.size":9,"axes.linewidth":0,"pdf.fonttype":42,"ps.fonttype":42})

def rounded_box(ax,xy,w,h,text,fc,ec=None,lw=1.8,fontsize=9,color=None,weight="regular",ha="center",va="center",radius=0.018,z=3,pad=0.012,linespacing=1.18):
    ec=ec or COL["dark"]; color=color or COL["dark"]
    ax.add_patch(FancyBboxPatch(xy,w,h,boxstyle=f"round,pad={pad},rounding_size={radius}",transform=ax.transAxes,fc=fc,ec=ec,lw=lw,zorder=z))
    ax.text(xy[0]+w/2,xy[1]+h/2,text,transform=ax.transAxes,ha=ha,va=va,fontsize=fontsize,color=color,fontweight=weight,linespacing=linespacing,zorder=z+1)

def arrow(ax,start,end,color=None,lw=2.4,ms=16,style="-|>",rad=0.0,z=2,linestyle="-",alpha=1.0):
    color=color or COL["dark"]
    ax.add_patch(FancyArrowPatch(start,end,transform=ax.transAxes,arrowstyle=style,mutation_scale=ms,lw=lw,color=color,linestyle=linestyle,connectionstyle=f"arc3,rad={rad}",zorder=z,alpha=alpha,shrinkA=2,shrinkB=2))

def label_text(ax,x,y,s,fontsize=9,color=None,weight="regular",ha="center",va="center",bbox=None,z=8,rotation=0):
    color=color or COL["dark"]
    ax.text(x,y,s,transform=ax.transAxes,ha=ha,va=va,fontsize=fontsize,color=color,fontweight=weight,bbox=bbox,zorder=z,rotation=rotation)

def draw_broken_link(ax,cx,cy,scale=1.0):
    r=0.018*scale; dx=0.014*scale
    for sx in (-1,1): ax.add_patch(Circle((cx+sx*dx,cy),r,transform=ax.transAxes,fill=False,ec=COL["orange"],lw=2.2,zorder=7))
    ax.add_line(Line2D([cx-0.032*scale,cx+0.032*scale],[cy-0.032*scale,cy+0.032*scale],transform=ax.transAxes,color=COL["red"],lw=2.8,solid_capstyle="round",zorder=8))
    ax.add_line(Line2D([cx-0.032*scale,cx+0.032*scale],[cy+0.032*scale,cy-0.032*scale],transform=ax.transAxes,color=COL["red"],lw=2.8,solid_capstyle="round",zorder=8))

fig,ax=plt.subplots(figsize=(14,7.5)); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
for x0,w,fc in [(0.035,0.27,"#FAFAFA"),(0.365,0.27,"#FFFFFF"),(0.695,0.27,"#FAFAFA")]:
    rounded_box(ax,(x0,0.205),w,0.61,"",fc,ec="#CFD8DC",lw=0.8,radius=0.012,z=0,pad=0.0)
fig.suptitle("Figure 1. Evidence-chain uptake mechanism: observability is necessary but not sufficient; agentic uptake mediates IO → ECRF.",fontsize=15,fontweight="bold",color=COL["dark"],y=0.965)
label_text(ax,0.17,0.84,"IO: material observability",fontsize=12,weight="bold")
label_text(ax,0.50,0.84,"Agent uptake U",fontsize=12,weight="bold")
label_text(ax,0.83,0.84,"ECRF: reconstruction fidelity",fontsize=12,weight="bold")
label_text(ax,0.17,0.785,"what the agent is GIVEN",fontsize=8.5,color=COL["grey"],weight="bold")
rounded_box(ax,(0.075,0.315),0.19,0.085,"IO₁\npaper text",fc=COL["light_grey"],ec=COL["grey"],fontsize=9.5,weight="bold")
rounded_box(ax,(0.075,0.455),0.19,0.085,"IO₂\n+ data + docs",fc="#F5F7F8",ec=COL["grey"],fontsize=9.5,weight="bold")
rounded_box(ax,(0.075,0.595),0.19,0.085,"IO₃\n+ executable code",fc="#FFFFFF",ec=COL["grey"],fontsize=9.5,weight="bold")
arrow(ax,(0.17,0.405),(0.17,0.448),color=COL["grey"],lw=1.8,ms=10)
arrow(ax,(0.17,0.545),(0.17,0.588),color=COL["grey"],lw=1.8,ms=10)
label_text(ax,0.17,0.255,"Mean ECRF by IO:\nIO₁ 0.499   IO₂ 0.601   IO₃ 0.591",fontsize=8.2,color=COL["dark"],bbox=dict(boxstyle="round,pad=0.35,rounding_size=0.08",fc="white",ec="#CFD8DC",lw=1.0))
arrow(ax,(0.275,0.515),(0.395,0.515),color=COL["dark"],lw=3.0,ms=18)
label_text(ax,0.335,0.565,"material availability",fontsize=8.5,weight="bold")
draw_broken_link(ax,0.335,0.515,scale=1.0)
label_text(ax,0.335,0.463,"NOT automatic",fontsize=8.5,color=COL["orange"],weight="bold",bbox=dict(boxstyle="round,pad=0.25,rounding_size=0.05",fc="#FFF8E1",ec=COL["orange"],lw=1.2))
cx,cy=0.50,0.535; dw,dh=0.13,0.145
ax.add_patch(Polygon([(cx,cy+dh/2),(cx+dw/2,cy),(cx,cy-dh/2),(cx-dw/2,cy)],closed=True,transform=ax.transAxes,fc=COL["pale_purple"],ec=COL["purple"],lw=2.2,zorder=4))
label_text(ax,cx,cy+0.014,"UPTAKE",fontsize=10,color=COL["purple"],weight="bold")
label_text(ax,cx,cy-0.020,"fork",fontsize=9,color=COL["dark"],weight="bold")
rounded_box(ax,(0.392,0.645),0.205,0.065,"real_data_used = True ∧ synth = False",fc=COL["pale_green"],ec=COL["green"],fontsize=8.1,weight="bold")
label_text(ax,0.499,0.728,"grounding",fontsize=8.5,color=COL["green"],weight="bold")
rounded_box(ax,(0.392,0.335),0.205,0.065,"synth = True\n(synthetic shortcut)",fc=COL["pale_orange"],ec=COL["orange"],fontsize=8.3,weight="bold")
label_text(ax,0.499,0.318,"shortcut collapse",fontsize=8.5,color=COL["orange"],weight="bold")
arrow(ax,(0.535,0.590),(0.440,0.645),color=COL["green"],lw=2.6,ms=14,rad=0.12)
arrow(ax,(0.535,0.478),(0.440,0.400),color=COL["orange"],lw=2.6,ms=14,rad=-0.12)
rounded_box(ax,(0.435,0.225),0.13,0.055,"refcode_used:\nneither necessary nor sufficient",fc="#F5F5F5",ec=COL["grey"],fontsize=7.4,color=COL["dark"])
callout=dict(fc="white",ec="#B0BEC5",lw=1.2)
rounded_box(ax,(0.360,0.735),0.27,0.060,"arts2021 / obadage2024: code present → synth=True → 0.50\n(code ≠ grounding)",fc=callout["fc"],ec=callout["ec"],lw=callout["lw"],fontsize=7.2,radius=0.010)
rounded_box(ax,(0.352,0.152),0.285,0.060,"liu2018: refcode_used=True but synth=True → 0.50\n(even code use ≠ grounding)",fc=callout["fc"],ec=callout["ec"],lw=callout["lw"],fontsize=7.2,radius=0.010)
rounded_box(ax,(0.342,0.062),0.305,0.060,"petersen2024 / park2023: real_data=True, refcode=False → break\n(data > code)",fc=callout["fc"],ec=callout["ec"],lw=callout["lw"],fontsize=7.2,radius=0.010)
arrow(ax,(0.598,0.678),(0.735,0.682),color=COL["green"],lw=3.0,ms=18)
label_text(ax,0.665,0.725,"evidence use",fontsize=8.8,color=COL["green"],weight="bold")
arrow(ax,(0.598,0.368),(0.735,0.408),color=COL["orange"],lw=2.4,ms=15,alpha=0.9)
label_text(ax,0.665,0.345,"synthetic substitution",fontsize=8.2,color=COL["orange"],weight="bold")
rounded_box(ax,(0.735,0.600),0.21,0.145,"F > 0.50  floor-break\n\nreal_data∧¬synth:\n100% break, mean 0.703 (n=15)",fc=COL["pale_green"],ec=COL["green"],lw=2.2,fontsize=9.1,weight="bold")
rounded_box(ax,(0.735,0.335),0.21,0.145,"F ≈ 0.50  synthetic floor\n\nsynth=True:\n0% break, mean 0.497 (n=17)",fc=COL["pale_orange"],ec=COL["orange"],lw=2.2,fontsize=9.1,weight="bold")

label_text(ax,0.84,0.535,"synth=False: 94% break, mean 0.685 (n=17)\nrefcode_used: 25% break; 3/4 still synthesized",fontsize=7.7,color=COL["dark"],bbox=dict(boxstyle="round,pad=0.28,rounding_size=0.05",fc="white",ec="#CFD8DC",lw=1.0))
rounded_box(ax,(0.045,0.020),0.91,0.105,"",fc="#FFFFFF",ec="#CFD8DC",lw=1.0,radius=0.012,z=0,pad=0.0)
label_text(ax,0.39,0.102,"Gate (c): synthetic data → cap ECRF at 0.50 (mechanical)",fontsize=10,color=COL["orange"],weight="bold")
label_text(ax,0.39,0.058,"structural agentic failure mode",fontsize=9,color=COL["dark"],weight="bold")
ax.add_line(Line2D([0.735,0.945],[0.100,0.100],transform=ax.transAxes,color=COL["orange"],lw=2.8,linestyle=(0,(6,4)),zorder=6))
label_text(ax,0.952,0.100,"0.50",fontsize=8.8,color=COL["orange"],weight="bold",ha="left")
label_text(ax,0.50,0.885,"IO  →  material availability  →  U  →  evidence use  →  ECRF",fontsize=10.5,color=COL["dark"],weight="bold",bbox=dict(boxstyle="round,pad=0.35,rounding_size=0.05",fc="#FFFFFF",ec="#CFD8DC",lw=1.0))
fig.text(0.5,0.012,"IO → material availability; U (uptake) → evidence use; ECRF → reconstruction fidelity. H_EUC.",ha="center",va="bottom",fontsize=8.5,color=COL["dark"])
os.makedirs(os.path.dirname(OUT),exist_ok=True)
fig.savefig(OUT,dpi=200,bbox_inches="tight",pad_inches=0.18)
plt.close(fig)
