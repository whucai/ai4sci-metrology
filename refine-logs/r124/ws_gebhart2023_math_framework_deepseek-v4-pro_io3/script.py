import json
import networkx as nx
import numpy as np
import pandas as pd
from itertools import combinations
import sys

# Load substitute dataset
print("Loading data...")
with open("/workspace/raw_data/openalex_physics_200.json", "r") as f:
    papers_data = json.load(f)

# Build mapping from ID to index and extract years, references
nodes_info = {}
for paper in papers_data:
    pid = paper.get("id")
    year = paper.get("publication_year")
    refs = paper.get("referenced_works", [])
    if pid and year and isinstance(year, int):
        nodes_info[pid] = {
            "year": year,
            "references": [r for r in refs if r]  # filter empty strings
        }

# Keep only papers that appear in the nodes_info (i.e., have year)
# Build directed citation graph
G_full = nx.DiGraph()
for pid, info in nodes_info.items():
    G_full.add_node(pid, year=info["year"])

added_edges = 0
for pid, info in nodes_info.items():
    for ref in info["references"]:
        if ref in nodes_info:  # only internal citations
            G_full.add_edge(pid, ref)  # pid cites ref
            added_edges += 1

print(f"Graph: {G_full.number_of_nodes()} nodes, {added_edges} edges")

# Utility: create G_t+h for a given year threshold
def subgraph_up_to_year(G, max_year):
    return G.subgraph([n for n, attr in G.nodes(data=True) if attr.get("year", 9999) <= max_year])

# Compute CD Index D(v) on subgraph G_th
def compute_cd_index(G_th, v):
    if v not in G_th:
        return None
    Din = set(G_th.predecessors(v))
    Dout = set(G_th.successors(v))
    # K: nodes that cite any node in Dout, but are not in Din U Dout U {v}
    K = set()
    for u in Dout:
        K.update(G_th.predecessors(u))
    K.difference_update({v})
    K.difference_update(Din)
    K.difference_update(Dout)

    N_CD_nodes = {v}.union(Din, Dout, K)
    # Build induced subgraph on N_CD
    N_CD = G_th.subgraph(N_CD_nodes)

    nI, nJ = 0, 0
    for u in Din:
        out_edges = N_CD.out_edges(u)
        succ = set()
        for _, w in out_edges:
            if w != u:
                succ.add(w)
        if succ == {v}:
            nI += 1
        else:
            nJ += 1
    din = len(Din)
    nK = len(K)
    if din + nK == 0:
        return None
    return (nI - nJ) / (din + nK)

# Betweenness on k-hop ego network
def compute_betweenness_ego(G_th, v, k):
    if v not in G_th:
        return None
    ego = nx.ego_graph(G_th, v, radius=k, undirected=True)
    n = ego.number_of_nodes()
    if n < 2:
        return None
    bet = nx.betweenness_centrality(ego, endpoints=False, normalized=True)
    return bet.get(v, None)

# Pagerank on k-hop ego (returns normalized value)
def compute_pagerank_ego(G_th, v, k, alpha=0.1):
    if v not in G_th:
        return None
    ego = nx.ego_graph(G_th, v, radius=k, undirected=True)
    n = ego.number_of_nodes()
    if n == 0:
        return None
    pers = {node: 1.0/n for node in ego.nodes}
    pr = nx.pagerank(ego, alpha=alpha, personalization=pers, max_iter=200, tol=1e-9)
    pi_v = pr.get(v, 0.0)
    return pi_v * n / alpha

# Full network betweenness
def compute_betweenness_all(G_th, v):
    if v not in G_th:
        return None
    bc = nx.betweenness_centrality(G_th, endpoints=False, normalized=True)
    return bc.get(v, None)

# Full network pagerank
def compute_pagerank_all(G_th, v, alpha=0.1):
    if v not in G_th:
        return None
    n = G_th.number_of_nodes()
    if n == 0:
        return None
    pers = {node: 1.0/n for node in G_th.nodes}
    pr = nx.pagerank(G_th, alpha=alpha, personalization=pers, max_iter=200, tol=1e-9)
    pi_v = pr.get(v, 0.0)
    return pi_v * n / alpha

# Iterate over focal papers with year in [1900,2010] and compute measures for h=5,10
results = []
focal_papers = [pid for pid, info in nodes_info.items() if 1900 <= info["year"] <= 2010]
print(f"Focal papers in [1900,2010]: {len(focal_papers)}")

for pid in focal_papers:
    t = nodes_info[pid]["year"]
    for h in [5, 10]:
        max_year = t + h
        G_th = subgraph_up_to_year(G_full, max_year)
        if G_th.number_of_nodes() < 2:
            continue
        # Citation count
        citation_count = G_th.in_degree(pid) if pid in G_th else None
        # CD Index
        d_val = compute_cd_index(G_th, pid)
        # Pagerank hops
        pr1 = compute_pagerank_ego(G_th, pid, 1)
        pr3 = compute_pagerank_ego(G_th, pid, 3)
        pr5 = compute_pagerank_ego(G_th, pid, 5)
        pr10 = compute_pagerank_ego(G_th, pid, 10)
        pr_all = compute_pagerank_all(G_th, pid)
        # Betweenness hops
        bet1 = compute_betweenness_ego(G_th, pid, 1)
        bet3 = compute_betweenness_ego(G_th, pid, 3)
        bet5 = compute_betweenness_ego(G_th, pid, 5)
        bet10 = compute_betweenness_ego(G_th, pid, 10)
        bet_all = compute_betweenness_all(G_th, pid)

        results.append({
            "paper_id": pid,
            "year": t,
            "h": h,
            "Q": citation_count,
            "D": d_val,
            "PR1": pr1,
            "PR3": pr3,
            "PR5": pr5,
            "PR10": pr10,
            "PR_all": pr_all,
            "B1": bet1,
            "B3": bet3,
            "B5": bet5,
            "B10": bet10,
            "B_all": bet_all
        })

df = pd.DataFrame(results)
print(f"Total measurement rows: {len(df)}")

# Compute correlations for each horizon
measure_cols = ["D", "Q", "PR1", "PR3", "PR5", "PR10", "B1", "B3", "B5", "B10", "B_all", "PR_all"]
nice_names = ["CD", "CitationCount", "Pagerank1", "Pagerank3", "Pagerank5", "Pagerank10",
              "Betweenness1", "Betweenness3", "Betweenness5", "Betweenness10",
              "BetweennessAll", "PagerankAll"]

for h_val in [5, 10]:
    sub = df[df["h"] == h_val]
    corr_mat = sub[measure_cols].corr()
    print(f"\nRESULT Correlation matrix for h={h_val} (DATA_SUB):")
    # Print formatted
    with pd.option_context('display.float_format', '{:,.3f}'.format):
        corr_pretty = corr_mat.copy()
        corr_pretty.index = nice_names
        corr_pretty.columns = nice_names
        print(corr_pretty.to_string())

# Figure 7 analogous: |B1 - D| vs D, correlation
h5_sub = df[df["h"] == 5].dropna(subset=["D", "B1"])
diff_abs = (h5_sub["B1"] - h5_sub["D"]).abs()
corr_D_diff = h5_sub["D"].corr(diff_abs)
print(f"\nRESULT Correlation between D and |B1-D| (h=5, DATA_SUB) = {corr_D_diff:.3f}")
print(f"Mean(|B1-D|) = {diff_abs.mean():.3f}, Std = {diff_abs.std():.3f}")

# For h=10 similarly
h10_sub = df[df["h"] == 10].dropna(subset=["D", "B1"])
diff_abs10 = (h10_sub["B1"] - h10_sub["D"]).abs()
corr_D_diff10 = h10_sub["D"].corr(diff_abs10)
print(f"RESULT Correlation between D and |B1-D| (h=10, DATA_SUB) = {corr_D_diff10:.3f}")
print(f"Mean(|B1-D|) h=10 = {diff_abs10.mean():.3f}, Std = {diff_abs10.std():.3f}")

print("\nNOTE: All quantitative results are DATA_SUB because they are computed on the small OpenAlex physics subset (200 works) rather than the full APS dataset.")
