import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import sys
import time
from scipy.stats import pearsonr

# Import the connector (assumed available)
from src.sciscigpt_local.sciscinet_connector import load_table

# -------------------------------
# 1. Load data
# -------------------------------
print("=== DATA_LOAD ===")
papers = load_table("papers")
citations = load_table("paper_citations")
print(f"papers_loaded: {len(papers)}")
print(f"citations_loaded: {len(citations)}")

# -------------------------------
# 2. Preprocess and sample
# -------------------------------
papers = papers[['paper_id', 'year', 'author_count', 'disruption_score']]

mask = (papers['year'] >= 1954) & (papers['year'] <= 2014) & (papers['author_count'] > 0)
papers_filtered = papers[mask].copy()
print(f"=== SAMPLE ===")
print(f"sample_size: {len(papers_filtered)}")
print(f"time_window: 1954-2014")
print(f"filters_applied: ['year in [1954,2014]', 'author_count > 0']")

np.random.seed(42)
sample_indices = np.random.choice(papers_filtered.index, size=20000, replace=False)
papers_sample = papers_filtered.loc[sample_indices].reset_index(drop=True)

papers_valid = papers_sample[papers_sample['disruption_score'].notna()].head(10).copy()

# -------------------------------
# 3. Validation: Compute D-index from scratch for 5-10 papers
# -------------------------------
print("=== INDICATOR_STATS ===")
d_scores = papers_sample['disruption_score'].dropna()
print(f"D_mean: {d_scores.mean():.6f}")
print(f"D_std: {d_scores.std():.6f}")
print(f"D_min: {d_scores.min():.6f}")
print(f"D_max: {d_scores.max():.6f}")

def compute_d_index_single(focal_id, citations_df, papers_df):
    """
    Compute D-index for a single focal paper using the citation network.
    Returns D or None if cannot compute.
    """
    # Get focal paper info
    focal_row = papers_df.loc[papers_df['paper_id'] == focal_id]
    if focal_row.empty:
        return None
    focal_year = focal_row.iloc[0]['year']
    
    # Get references of focal paper (papers it cites)
    refs = citations_df[citations_df['citing_paper_id'] == focal_id]['cited_paper_id'].unique()
    if len(refs) == 0:
        return None
    
    # Get all papers that cite the focal paper
    citing_focal = citations_df[citations_df['cited_paper_id'] == focal_id]
    citing_focal_ids = citing_focal['citing_paper_id'].unique()
    
    # Get all papers that cite any reference of focal (excluding focal itself)
    citing_refs = citations_df[citations_df['cited_paper_id'].isin(refs)]
    citing_refs_ids = citing_refs['citing_paper_id'].unique()
    
    # Classify citing papers into n_i (also cite a reference) and n_j (only cite focal)
    set_focal_refs = set(refs)
    n_i = 0
    n_j = 0
    for citer_id in citing_focal_ids:
        citer_refs = citations_df[citations_df['citing_paper_id'] == citer_id]['cited_paper_id'].unique()
        if set_focal_refs.intersection(set(citer_refs)):
            n_i += 1
        else:
            n_j += 1
    
    total = n_i + n_j
    if total == 0:
        return None
    D = (n_i - n_j) / total
    return D