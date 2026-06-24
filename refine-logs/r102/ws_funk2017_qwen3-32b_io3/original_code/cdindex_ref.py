"""Reference CD-index implementation for funk2017 (IO₃ original_code).

Implements the CDt / CD5 disruption index from Funk & Haltiwanger (2017),
Management Science, Eq. (1). Pure numpy/networkx — runs in sciscigpt-ds:0.1
without compiling the upstream `cdindex` C extension.

Upstream reference: code at http://www.cdindex.info (vendored as
wheels/cdindex-1.0.20.tar.gz for offline install if the C extension is wanted).

Definition (per paper §2):
  For focal patent f, predecessors b (cited by f), future patents i (cite f
  and/or b within the measurement window, default 5 years → CD5):
    n1 = #future patents citing f but NONE of f's predecessors   (destabilizing)
    n2 = #future patents citing f's predecessors but NOT f        (consolidating, neutral here)
    n3 = #future patents citing BOTH f and f's predecessors       (consolidating)
    n  = n1 + n2 + n3
    CD5 = (n1 - n3) / n           # ranges -1..+1; + = destabilizing
  mCD5 = impact-weighted variant (weight w_i = forward citations of i).
"""
from __future__ import annotations
import numpy as np


def cd_index(focal: str, predecessors: set, future_citations: dict, years_window: int = 5) -> dict:
    """Compute CD5 for one focal patent.

    Args:
      focal: focal patent id.
      predecessors: set of patent ids cited by focal.
      future_citations: {future_patent_id: {"year": int, "cites": set([patent_id, ...])}}
        where cites includes focal and/or predecessors.
      years_window: citation window (5 → CD5).
    """
    n1 = n2 = n3 = 0
    for fid, info in future_citations.items():
        cites = set(info.get("cites", ()))
        cites_f = focal in cites
        cites_b = bool(cites & predecessors)
        if cites_f and not cites_b:
            n1 += 1
        elif cites_b and not cites_f:
            n2 += 1
        elif cites_f and cites_b:
            n3 += 1
    n = n1 + n2 + n3
    cd = (n1 - n3) / n if n > 0 else float("nan")
    return {"n1": n1, "n2": n2, "n3": n3, "n": n, "CD5": cd}


def mcd_index(focal, predecessors, future_citations, weights: dict | None = None) -> dict:
    """mCD5 — impact-weighted (w_i = forward citations of i)."""
    num = den = 0.0
    for fid, info in future_citations.items():
        w = (weights or {}).get(fid, info.get("weight", 1.0))
        cites = set(info.get("cites", ()))
        cites_f = focal in cites
        cites_b = bool(cites & predecessors)
        if cites_f and not cites_b:
            num += w
        elif cites_f and cites_b:
            num -= w
        if cites_f or cites_b:
            den += w
    return {"mCD5": (num / den) if den > 0 else float("nan"), "den": den}


if __name__ == "__main__":
    # Smoke test from paper Figure 1 (destabilizing case): 6 future patents, none cite predecessors
    focal = "F"
    preds = {"p1", "p2", "p3", "p4"}
    future = {f"i{k}": {"year": 2000, "cites": {"F"}} for k in range(6)}  # all cite F, none cite preds
    r = cd_index(focal, preds, future)
    print("destabilizing case (expect CD5=+1.0):", r)
    assert abs(r["CD5"] - 1.0) < 1e-9
    # consolidating case: all 6 cite both F and a predecessor
    future2 = {f"i{k}": {"year": 2000, "cites": {"F", "p1"}} for k in range(6)}
    r2 = cd_index(focal, preds, future2)
    print("consolidating case (expect CD5=-1.0):", r2)
    assert abs(r2["CD5"] - (-1.0)) < 1e-9
    print("cdindex_ref smoke OK")
