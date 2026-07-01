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
    
    # n_k: papers that cite at least one reference of focal but do NOT cite focal itself
    citing_focal_set = set(citing_focal_ids)
    n_k = sum(1 for c in citing_refs_ids if c not in citing_focal_set)
    
    # Compute D-index
    denominator = n_i + n_j + n_k
    if denominator == 0:
        return None
    D = (n_i - n_j) / denominator
    return D

# Validate on a few papers
valid_results = []
for idx, row in papers_valid.iterrows():
    pid = row['paper_id']
    computed = compute_d_index_single(pid, citations, papers)
    if computed is not None:
        error = abs(computed - row['disruption_score'])
        valid_results.append({'pid': pid, 'computed_D': computed, 'original_D': row['disruption_score'], 'error': error})
    else:
        print(f"Could not compute D for pid {pid}")

valid_df = pd.DataFrame(valid_results)
print("=== VALIDATION ===")
print(f"valid_n: {len(valid_df)}")
print(f"valid_mean_abs_error: {valid_df['error'].mean():.6f}")
print(f"valid_max_abs_error: {valid_df['error'].max():.6f}")
print(f"valid_pearson_r: {valid_df['computed_D'].corr(valid_df['original_D']):.6f}")

# -------------------------------
# 4. Regression analysis
# -------------------------------
print("=== REGRESSION ===")
# Prepare regression data from the sample
reg_data = papers_sample[['year', 'author_count', 'disruption_score']].dropna().copy()
reg_data['log_author_count'] = np.log(reg_data['author_count'] + 1)
reg_data['year_centered'] = reg_data['year'] - reg_data['year'].mean()

# Run regression: disruption_score ~ year_centered + log_author_count
X = reg_data[['year_centered', 'log_author_count']]
X = sm.add_constant(X)
y = reg_data['disruption_score']
model = sm.OLS(y, X).fit()
print(model.summary().as_text())

# Extract coefficients
coef_year = model.params['year_centered']
coef_authors = model.params['log_author_count']
pval_year = model.pvalues['year_centered']
pval_authors = model.pvalues['log_author_count']
print(f"year_coef: {coef_year:.6f} (p={pval_year:.6e})")
print(f"log_author_count_coef: {coef_authors:.6f} (p={pval_authors:.6e})")

# -------------------------------
# 5. Additional analysis: comparison with original D
# -------------------------------
print("=== COMPARISON ===")
# Compare computed D with original for all validation papers
if len(valid_df) > 1:
    r, p = pearsonr(valid_df['computed_D'], valid_df['original_D'])
    print(f"correlation_computed_original: {r:.6f}")
    print(f"p_value_correlation: {p:.6e}")
else:
    print("Not enough validation points for correlation.")