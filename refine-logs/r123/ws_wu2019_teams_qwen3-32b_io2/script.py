import pandas as pd
import numpy as np
import json
import os
from scipy import stats

# 1. Load Data
data_path = '/workspace/raw_data/sciscinet_sample.parquet'
if not os.path.exists(data_path):
    raise FileNotFoundError(f"Data file not found at {data_path}")

df = pd.read_parquet(data_path)

# 2. Robust Column Identification & Parsing
def find_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

col_pid = find_col(df, ['paper_id', 'id', 'doc_id', 'citation_key'])
col_authors = find_col(df, ['authors', 'author_list', 'author_names'])
col_refs = find_col(df, ['references', 'cited_references', 'ref_list'])
col_cites = find_col(df, ['citations', 'citing_papers', 'forward_citations'])

# Fallback to standard names if not found
if not all([col_pid, col_authors, col_refs, col_cites]):
    col_pid, col_authors, col_refs, col_cites = 'paper_id', 'authors', 'references', 'citations'

def parse_list(val):
    if isinstance(val, list): return val
    if isinstance(val, str):
        try: return json.loads(val)
        except: return [v.strip() for v in val.split(',') if v.strip()]
    return []

df['authors_parsed'] = df[col_authors].apply(parse_list)
df['refs_parsed'] = df[col_refs].apply(parse_list)
df['cites_parsed'] = df[col_cites].apply(parse_list)

df['team_size'] = df['authors_parsed'].apply(len)

# 3. Build Citation Lookup (Paper ID -> Set of Citing Paper IDs)
pid_to_cites = dict(zip(df[col_pid], df['cites_parsed']))
for pid in df[col_pid]:
    if pid not in pid_to_cites:
        pid_to_cites[pid] = set()
    else:
        pid_to_cites[pid] = set(pid_to_cites[pid])

# 4. Compute Disruption Index (D-index) per paper
# Formula from Wang et al. (2013) / Wu et al. (2019):
# D_i = sum_j (N_not_i_j - N_i_not_j) / sum_j (N_not_i_j + N_i_not_j)
# where j iterates over references of paper i.
d_vals = []
valid_flags = []

for _, row in df.iterrows():
    pid = row[col_pid]
    refs = row['refs_parsed']
    citing_i = pid_to_cites.get(pid, set())

    num_sum = 0.0
    den_sum = 0.0

    for ref in refs:
        citing_j = pid_to_cites.get(ref, set())
        # N_i_not_j: citing papers cite i but not j
        n_i_not_j = len(citing_i - citing_j)
        # N_not_i_j: citing papers cite j but not i
        n_not_i_j = len(citing_j - citing_i)
        
        num_sum += (n_not_i_j - n_i_not_j)
        den_sum += (n_not_i_j + n_i_not_j)

    if den_sum > 0:
        d_vals.append(num_sum / den_sum)
        valid_flags.append(True)
    else:
        d_vals.append(np.nan)
        valid_flags.append(False)

df['D_index'] = d_vals
df_valid = df[valid_flags].copy()
df_valid = df_valid[df_valid['team_size'] > 0].copy()

# 5. Statistical Analysis (Team Size vs D-index)
df_valid['log_team_size'] = np.log(df_valid['team_size'])

corr_val = df_valid['log_team_size'].corr(df_valid['D_index'])
slope, intercept, r_val, p_val, std_err = stats.linregress(df_valid['log_team_size'], df_valid['D_index'])

# Mean D-index by team size quintiles
df_valid['ts_bin'] = pd.qcut(df_valid['team_size'], q=5, labels=False, duplicates='drop')
mean_d_bins = df_valid.groupby('ts_bin')['D_index'].mean()

# Small vs Large teams comparison
small_teams = df_valid[df_valid['team_size'] <= 2]['D_index'].mean()
large_teams = df_valid[df_valid['team_size'] > 5]['D_index'].mean()

# 6. Print Results
print(f"RESULT_DATA_SUB N_VALID_PAPERS = {len(df_valid)}")
print(f"RESULT_DATA_SUB MEAN_D_INDEX = {df_valid['D_index'].mean():.4f}")
print(f"RESULT_DATA_SUB CORR_LOG_TEAM_SIZE_D_INDEX = {corr_val:.4f}")
print(f"RESULT_DATA_SUB REGRESSION_SLOPE_LOG_TEAM_SIZE = {slope:.4f}")
print(f"RESULT_DATA_SUB MEAN_D_SMALL_TEAMS_LE2 = {small_teams:.4f}")
print(f"RESULT_DATA_SUB MEAN_D_LARGE_TEAMS_GT5 = {large_teams:.4f}")
print(f"PAPER_REPORTED CORRELATION_DIRECTION = Negative")
print(f"PAPER_REPORTED FINDING = Small teams disrupt (high D), large teams develop (low D)")

# 7. Final Conclusion
if slope < 0 and corr_val < 0:
    print("CONCLUSION: Reproduction confirms the paper's core finding: team size is negatively correlated with the disruption index. Small teams tend to produce more disruptive work, while large teams tend to develop existing ideas.")
else:
    print("CONCLUSION: Reproduction on the sample data does not strongly replicate the negative correlation. This may be due to sample size, domain specificity, or citation window effects in the provided subset.")
