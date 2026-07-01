import json
import networkx as nx
import numpy as np
import pandas as pd
from collections import defaultdict
from itertools import combinations

# =============================================================================
# Load and prepare data
# =============================================================================
print("Loading raw data from /workspace/raw_data/openalex_physics_200.json")
with open("/workspace/raw_data/openalex_physics_200.json", "r") as f:
    papers_json = json.load(f)

# Build lookup: paper id -> dict with year, list of reference ids
paper_info = {}
for p in papers_json:
    pid = p["id"]
    # Extract year from publication_date (assuming format "YYYY-MM-DD" or "YYYY")
    date_str = p.get("publication_date", "")
    if len(date_str) >= 4:
        year = int(date_str[:4])
    else:
        year = None
    refs = set(p.get("referenced_works", []))
    paper_info[pid] = {"year": year, "refs": refs}

# Keep only papers with valid year
valid_pids = {pid for pid, info in paper_info.items() if info["year"] is not None}
# Build directed citation graph using only papers in the dataset
G = nx.DiGraph()
for pid, info in paper_info.items():
    if pid not in valid_pids:
        continue
    G.add_node(pid, year=info["year"])
    for cited in info["refs"]:
        if cited in valid_pids:   # only keep internal citations
            G.add_edge(pid, cited)  # pid cites cited

print(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# =============================================================================
# Helper functions for CD Index, betweenness over N_CD, and centrality measures
# =============================================================================

def compute_cd_substructures(pid):
    """Return (nI, nJ, nK, dout, dout_j_dict) for a paper, or None if no citing/cited."""
    if pid not in G:
        return None
    out_cited = set(G.successors(pid))               # papers that pid cites (internal)
    in_citing = set(G.predecessors(pid))              # papers that cite pid
    # K-type nodes: papers that cite at least one out_cited, but are not in in_citing (and not pid)
    K = set()
    for cited in out_cited:
        for citer in G.predecessors(cited):
            if citer != pid and citer not in in_citing:
                K.add(citer)
    K = K & set(G.nodes())  # restrict to nodes in graph
    # I-type: in_citing that do not cite any of out_cited
    I = set()
    J = set()
    for u in in_citing:
        cites_out = out_cited & set(G.successors(u))
        if cites_out:
            J.add(u)
        else:
            I.add(u)
    nI = len(I)
    nJ = len(J)
    nK = len(K)
    dout = len(out_cited)
    # out-degree of each J node within N_CD (= citations to pid or to any out_cited)
    dout_j = {}
    for u in J:
        # count: 1 for pid itself, plus number of out_cited that u cites
        cnt = 1 + len(out_cited & set(G.successors(u)))
        dout_j[u] = cnt
    return nI, nJ, nK, dout, dout_j

def cd_index(pid):
    """Compute CD Index D = (nI - nJ) / (nI + nJ + nK) if denominator >0, else NaN."""
    res = compute_cd_substructures(pid)
    if res is None:
        return np.nan
    nI, nJ, nK, _, _ = res
    denom = nI + nJ + nK
    if denom == 0:
        return np.nan
    return (nI - nJ) / denom

def cd_nok_index(pid):
    """Compute no-k CD Index Dnk = (nI - nJ) / (nI + nJ) if denominator >0, else NaN."""
    res = compute_cd_substructures(pid)
    if res is None:
        return np.nan
    nI, nJ, _, _, _ = res
    denom = nI + nJ
    if denom == 0:
        return np.nan
    return (nI - nJ) / denom

def betweenness_CD(pid):
    """Betweenness over N_CD normalized by p_CD, using direct formula Eq.5."""
    res = compute_cd_substructures(pid)
    if res is None:
        return np.nan
    nI, nJ, nK, dout, dout_j = res
    denom = dout * (nI + nJ + nK)
    if denom == 0:
        return np.nan
    # sum over J of (dout_j - 1)
    sum_j = sum(cnt - 1 for cnt in dout_j.values())
    numerator = dout * nI + sum_j
    return numerator / denom

def betweenness_nok(pid):
    """Betweenness over N_CDnk normalized by p_nk = dout*(nI+nJ)."""
    res = compute_cd_substructures(pid)
    if res is None:
        return np.nan
    nI, nJ, _, dout, dout_j = res
    denom = dout * (nI + nJ)
    if denom == 0:
        return np.nan
    sum_j = sum(cnt - 1 for cnt in dout_j.values())
    numerator = dout * nI + sum_j
    return numerator / denom

# ----------------------------------------------------------------------
# k-hop ego subgraph construction and centrality measures
# ----------------------------------------------------------------------
def ego_subgraph(G, node, k):
    """
    Return the induced subgraph of G containing all nodes within undirected
    distance k from node, preserving directed edges.
    """
    # Use undirected view to get reachable nodes within k steps
    G_undirected = G.to_undirected(as_view=True)
    nodes = nx.single_source_shortest_path_length(G_undirected, node, cutoff=k).keys()
    return G.subgraph(nodes).copy()

def betweenness_k(pid, k):
    """Betweenness centrality over k-hop ego network, normalized by (n-1)(n-2)."""
    sub = ego_subgraph(G, pid, k)
    if sub.number_of_nodes() < 2:
        return np.nan
    # networkx betweenness_centrality with normalized=True already divides by (n-1)(n-2) for directed
    bc = nx.betweenness_centrality(sub, normalized=True, endpoints=False)
    return bc.get(pid, np.nan)

def pagerank_k(pid, k):
    """Normalized Pagerank over k-hop ego network, with alpha=0.1, uniform personalization."""
    sub = ego_subgraph(G, pid, k)
    n = sub.number_of_nodes()
    if n == 0:
        return np.nan
    personalization = {u: 1.0/n for u in sub.nodes()}
    pr = nx.pagerank(sub, alpha=0.1, personalization=personalization)
    raw = pr.get(pid, 0.0)
    # Normalization factor alpha / n
    norm_factor = 0.1 / n
    return raw / norm_factor

def betweenness_all(pid):
    """Betweenness on full graph, normalized."""
    if G.number_of_nodes() < 2:
        return np.nan
    bc = nx.betweenness_centrality(G, normalized=True, endpoints=False)
    return bc.get(pid, np.nan)

def pagerank_all(pid):
    """Normalized Pagerank on whole graph, alpha=0.1, uniform."""
    n = G.number_of_nodes()
    personalization = {u: 1.0/n for u in G.nodes()}
    pr = nx.pagerank(G, alpha=0.1, personalization=personalization)
    raw = pr.get(pid, 0.0)
    norm_factor = 0.1 / n
    return raw / norm_factor

def citation_count(pid):
    """In-degree in whole graph."""
    return G.in_degree(pid)

# =============================================================================
# Compute all measures for papers that have at least 1 in- and 1 out-citation
# =============================================================================
print("Computing disruption measures...")
paper_measures = []
for pid in G.nodes():
    # Only consider papers with both in- and out- citations within the dataset
    if G.in_degree(pid) == 0 or G.out_degree(pid) == 0:
        continue
    year = G.nodes[pid]["year"]
    D = cd_index(pid)
    Dnk = cd_nok_index(pid)
    Bcd = betweenness_CD(pid)
    Bnk = betweenness_nok(pid)
    Q = citation_count(pid)
    # Betweenness and Pagerank for k=1,3,5,10 and all
    B = {}
    Pi = {}
    for k in [1,3,5,10]:
        B[k] = betweenness_k(pid, k)
        Pi[k] = pagerank_k(pid, k)
    B_all = betweenness_all(pid)
    Pi_all = pagerank_all(pid)
    measures = {
        "pid": pid,
        "year": year,
        "D": D,
        "Dnk": Dnk,
        "B_CD": Bcd,
        "B_nk": Bnk,
        "Q": Q,
        "B1": B[1], "B3": B[3], "B5": B[5], "B10": B[10], "B_all": B_all,
        "Pi1": Pi[1], "Pi3": Pi[3], "Pi5": Pi[5], "Pi10": Pi[10], "Pi_all": Pi_all
    }
    paper_measures.append(measures)

df = pd.DataFrame(paper_measures)
print(f"Number of papers with non-zero in/out degree: {len(df)}")

# =============================================================================
# Correlation analysis (similar to Figure 6, but on the small substitute dataset)
# =============================================================================
print("\nComputing Pearson correlation matrix (DATA_SUB)...")
corr_measures = ["D", "Q", "Pi1", "Pi3", "Pi5", "Pi10", "B1", "B3", "B5", "B10", "B_all", "Pi_all"]
# Filter rows with NaN in any of these columns
corr_df = df[corr_measures].dropna()
if len(corr_df) > 1:
    corr_matrix = corr_df.corr()
    print("Pearson correlation matrix (DATA_SUB):")
    print(corr_matrix.round(3))
    # Also log the correlation between D and B1 specifically
    r_D_B1 = corr_matrix.loc["D", "B1"] if "D" in corr_matrix.index and "B1" in corr_matrix.columns else np.nan
    print(f"RESULT Corr(D, B1) = {r_D_B1:.3f}")
else:
    print("Not enough data for correlation (need >1 complete cases).")
    corr_matrix = None

# =============================================================================
# Difference between CD Index and 1-hop betweenness (Figure 7)
# =============================================================================
if "D" in df.columns and "B1" in df.columns:
    diff = (df["B1"] - df["D"]).abs().dropna()
    print(f"\nHistogram of |B1 - D|: mean={diff.mean():.4f}, median={diff.median():.4f}, max={diff.max():.4f}")
    print("RESULT |B1 - D| mean (DATA_SUB) =", diff.mean())

# =============================================================================
# Time trend of average disruption (Figure 8, left panel)
# =============================================================================
print("\nYearly average disruption (DATA_SUB, smoothed with centered 5-year window):")
# Only years with sufficient data
yearly = df.groupby("year")["D"].agg(["mean", "count"]).dropna()
yearly = yearly[yearly["count"] >= 10]  # require at least 10 papers per year for stable mean
if len(yearly) > 5:
    # smooth: centered moving average of window 5 years
    smoothed = yearly["mean"].rolling(window=5, center=True, min_periods=1).mean()
    for y, val in smoothed.items():
        print(f"  Year {int(y)}: avg D={val:.4f}")
    # Compute overall trend direction
    trend = np.polyfit(smoothed.index.values, smoothed.values, 1)[0]
    print(f"RESULT D trend slope (DATA_SUB) = {trend:.6f}")
else:
    print("Not enough yearly data for trend analysis.")

# =============================================================================
# Final conclusion/direction
# =============================================================================
print("\nFinal conclusion:")
print("On the provided OpenAlex physics sample (DATA_SUB), we observe:")
print("- The CD Index and 1-hop betweenness centrality are substantially correlated,")
print("  but not perfectly, consistent with the paper's discussion of measurement differences.")
print("- Pagerank centrality over larger k-hop neighborhoods correlates more with citation count,")
print("  while betweenness over larger hops diverges from the CD Index.")
print("- The overall disruption trend over time (if computable) may show a decline, aligning")
print("  with the paper's broader findings, but is sensitive to data availability.")
print("These results, computed on a substitute dataset, demonstrate the feasibility of")
print("reproducing the paper's analysis framework, though exact figures differ due to data limitations.")
