#!/usr/bin/env python3
"""
Reproduction attempt of empirical analysis from Bikard, Murray & Gans (2013)
"Exploring Tradeoffs in the Organization of Scientific Work: Collaboration and Scientific Reward"
NBER Working Paper 18958.

Since the original raw data are not provided, this script generates a synthetic dataset
that mimics the structure described in the paper and implements the key specifications.
All numerical results are labeled SYNTHETIC and do not represent actual findings.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.iolib.summary2 import summary_col
import os, warnings
warnings.filterwarnings('ignore')

# --------------------------------------------------------------------
# 1. Attempt to load real data; if unavailable, create synthetic panel
# --------------------------------------------------------------------
DATA_PATH = "/workspace/raw_data/bikard2013_data.csv"
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
    synthetic = False
    print("Loaded real data from", DATA_PATH)
else:
    synthetic = True
    print("NOTE: Original data not found. Creating synthetic dataset for demonstration.")
    # Reproduce structure: 661 scientists, 31 years, ~5964 faculty-years, 21054 publications
    np.random.seed(2025)
    n_scientists = 661
    years = range(1976, 2007)   # 31 years
    departments = ["EECS", "ChemE", "MSE", "MechE", "Biology", "Chemistry", "Physics"]
    # Assign each scientist a primary department and an individual fixed effect for quality
    scientist_ids = [f"S{i:04d}" for i in range(1, n_scientists+1)]
    dept_assign = np.random.choice(departments, size=n_scientists, p=[0.2,0.1,0.1,0.15,0.15,0.15,0.15])
    indiv_fe = np.random.normal(0.5, 0.3, size=n_scientists)  # log citation baseline
    # Simulate career presence: each scientist appears for a random consecutive block of years within 1976-2006
    obs_list = []
    for sid, d, fe in zip(scientist_ids, dept_assign, indiv_fe):
        start = np.random.choice(range(1976, 2001))   # latest start 2000 to have at least 6 years
        end = np.random.choice(range(start+3, min(start+20, 2007)))  # at least 3 years
        for yr in range(start, end+1):
            obs_list.append((sid, yr, d, fe))
    df = pd.DataFrame(obs_list, columns=["scientist_id", "year", "department", "indiv_fe"])
    # Ensure total obs close to 5964
    if len(df) > 5964:
        df = df.sample(n=5964, random_state=2025).reset_index(drop=True)
    # Generate paper-level data -> aggregate to scientist-year
    papers = []
    # Time effect: slight increase in citations over years
    year_effect = {yr: 0.01*(yr-1985) for yr in years}
    # For each scientist-year, draw number of papers
    paper_id = 0
    for _, row in df.iterrows():
        sid = row["scientist_id"]
        yr = row["year"]
        base = row["indiv_fe"] + year_effect[yr]
        # Number of papers: Poisson with mean depending on baseline productivity
        n_papers = np.random.poisson(lam=2.5 + 1.5*row["indiv_fe"])  # avg ~3.5
        if n_papers > 20:
            n_papers = 20  # cap
        for _ in range(n_papers):
            # Number of authors (1 to 20, but exclude >20 per paper's criteria)
            nauthors = np.random.choice(range(1, 21), p=[0.3]+[0.7/19]*19)  # 30% solo
            # if solo, no collab; else collaboration. For realism, some cross-department and senior status
            cross_dept = 0
            senior = 0
            if nauthors > 1:
                # randomly assign if any collaborator is from different dept
                if np.random.rand() < 0.3:
                    cross_dept = 1
                # if any collaborator is more senior (simple heuristic)
                if np.random.rand() < 0.2:
                    senior = 1
            # Generate citations for this paper
            # Collaboration effect: log-linear with noise, larger for cross-dept, smaller for senior same-dept
            collab_effect = 0.0
            if nauthors > 1:
                # base collaboration effect: ~log(1.6)=0.47 for within-dept, not senior
                base_collab = 0.47
                if cross_dept and not senior:
                    base_collab += 0.2   # higher quality
                if senior and not cross_dept:
                    base_collab -= 0.1    # lower quality gain, maybe free-riding
                collab_effect = base_collab
            log_cites = base + collab_effect + np.random.normal(0, 0.5)
            citations = np.exp(log_cites) * 10  # scale to realistic citation counts
            papers.append({
                "scientist_id": sid,
                "year": yr,
                "nauthors": nauthors,
                "cross_dept": cross_dept,
                "senior": senior,
                "citations": max(1, int(round(citations)))
            })
            paper_id += 1
    papers_df = pd.DataFrame(papers)
    # Aggregate to scientist-year level
    # Define collaboration measures
    # 1) Fraction of papers with >1 author
    collab_frac = papers_df.groupby(["scientist_id", "year"])["nauthors"].apply(lambda x: (x > 1).mean()).reset_index(name="frac_collab")
    # 2) Average number of authors
    avg_authors = papers_df.groupby(["scientist_id", "year"])["nauthors"].mean().reset_index(name="avg_authors")
    # 3) Fractional publications: sum(1/nauthors)
    frac_pubs = papers_df.groupby(["scientist_id", "year"]).apply(lambda g: (1/g["nauthors"]).sum(), include_groups=False).reset_index(name="frac_pubs")
    # 4) Total papers
    n_papers = papers_df.groupby(["scientist_id", "year"]).size().reset_index(name="n_papers")
    # 5) Average citations per paper
    avg_cites = papers_df.groupby(["scientist_id", "year"])["citations"].mean().reset_index(name="avg_cites")
    # Merge all
    sci_year = df[["scientist_id", "year", "department", "indiv_fe"]].copy()
    sci_year = sci_year.merge(collab_frac, on=["scientist_id", "year"], how="left")
    sci_year = sci_year.merge(avg_authors, on=["scientist_id", "year"], how="left")
    sci_year = sci_year.merge(frac_pubs, on=["scientist_id", "year"], how="left")
    sci_year = sci_year.merge(n_papers, on=["scientist_id", "year"], how="left")
    sci_year = sci_year.merge(avg_cites, on=["scientist_id", "year"], how="left")
    sci_year.fillna({"frac_collab": 0, "avg_authors": 1, "frac_pubs": 0, "n_papers": 0, "avg_cites": 0}, inplace=True)
    # For scientist-years with no papers, set avg_cites to missing? The paper likely excludes years with zero pubs.
    sci_year = sci_year[sci_year["n_papers"] > 0].copy()
    # Create department-year identifier for fixed effects
    sci_year["dept_year"] = sci_year["department"] + "_" + sci_year["year"].astype(str)
    df = sci_year.copy()
    print(f"Synthetic dataset: {df.shape[0]} scientist-years, {df['scientist_id'].nunique()} scientists.")

# --------------------------------------------------------------------
# 2. Define variables
# --------------------------------------------------------------------
# Dependent variables (log transformed)
df["log_avg_cites"] = np.log(df["avg_cites"] + 1)   # +1 for zeros
df["log_frac_pubs"] = np.log(df["frac_pubs"] + 1)
df["log_n_papers"] = np.log(df["n_papers"] + 1)

# Collaboration measure (primary): fraction of collaborative papers
df["collab_frac"] = df["frac_collab"]

# Additional measures
df["has_collab"] = (df["collab_frac"] > 0).astype(int)

# --------------------------------------------------------------------
# 3. Compute attributed quality under different credit allocation rules α(N)
# --------------------------------------------------------------------
# We need to compute for each scientist-year the sum over papers of α(N)*citations.
# For this demonstration, we use the detailed papers_df we generated above.
papers_agg = papers_df.merge(df[["scientist_id","year"]], on=["scientist_id","year"], how="inner")

def compute_attributed_cites(df_papers, alpha_func):
    """alpha_func takes number of authors N (int) and returns attribution share"""
    return df_papers.groupby(["scientist_id","year"]).apply(
        lambda g: (alpha_func(g["nauthors"]) * g["citations"]).sum(), include_groups=False
    ).reset_index(name="attributed_cites")

alpha_equal = lambda N: 1.0 / N   # naive equal share
alpha_sqrt = lambda N: 1.0 / np.sqrt(N)   # sum of shares > 1
alpha_linear = lambda N: 1.0   # no discount (full credit to each)
alpha_06 = lambda N: 1.0 / N**0.6   # sum N^{0.4} > 1, used in synthetic truth

attr_equal = compute_attributed_cites(papers_agg, alpha_equal)
attr_sqrt  = compute_attributed_cites(papers_agg, alpha_sqrt)
attr_linear = compute_attributed_cites(papers_agg, alpha_linear)
attr_06 = compute_attributed_cites(papers_agg, alpha_06)

df = df.merge(attr_equal, on=["scientist_id","year"], how="left")
df = df.merge(attr_sqrt,  on=["scientist_id","year"], how="left", suffixes=("","_sqrt"))
df = df.merge(attr_linear, on=["scientist_id","year"], how="left", suffixes=("","_linear"))
df = df.merge(attr_06,    on=["scientist_id","year"], how="left", suffixes=("","_06"))
for col in ["attributed_cites", "attributed_cites_sqrt", "attributed_cites_linear", "attributed_cites_06"]:
    df[col].fillna(0, inplace=True)
for col in ["attributed_cites", "attributed_cites_sqrt", "attributed_cites_linear", "attributed_cites_06"]:
    df[f"log_{col}"] = np.log(df[col] + 1)

# --------------------------------------------------------------------
# 4. Regressions (fixed effects at individual and department-year level)
# --------------------------------------------------------------------
# We include individual and department-year dummies. With many dummies, use OLS with categoricals.
# To keep summary clean, we absorb fixed effects using statsmodels formula with C().
# This may be memory heavy; we can use a high-dimensional fixed effect estimator via `linearmodels`, 
# but to stay dependency-light, we use the demean approach via `PanelOLS` from `linearmodels` if available.
try:
    from linearmodels.panel import PanelOLS
    use_linearmodels = True
except ImportError:
    use_linearmodels = False
    print("linearmodels not installed; falling back to OLS with dummies (may be slow).")

# For simplicity and reproducibility, we'll use OLS with a formula that includes individual and dept_year fixed effects
# as categories. We'll just show a few representative specifications.

def run_fixed_effects_reg(df, y_var, x_vars, fe_individual=True, fe_dept_year=True):
    """Run a linear regression with specified fixed effects using statsmodels."""
    formula = f"{y_var} ~ " + " + ".join(x_vars)
    if fe_individual:
        formula += " + C(scientist_id)"
    if fe_dept_year:
        formula += " + C(dept_year)"
    # Use OLS with clustered standard errors on scientist_id
    model = sm.OLS.from_formula(formula, data=df)
    # Cluster by scientist
    clustered = model.fit(cov_type='cluster', cov_kwds={'groups': df['scientist_id']})
    return clustered

# For the attributed quality regressions, we use the log of attributed citations as y.
print("\n--- Regression Results (SYNTHETIC) ---")

# H1: Quality and collaboration
mod_h1 = run_fixed_effects_reg(df, "log_avg_cites", ["collab_frac"])
print("H1: log(avg citations) ~ collaboration fraction")
print(mod_h1.params.loc["collab_frac"])
print(f"coeff = {mod_h1.params.loc['collab_frac']:.4f}, p-value = {mod_h1.pvalues.loc['collab_frac']:.4f}")
print("PAPER_REPORTED: over 60% more citations for collaborative vs solo work. (SYNTHETIC coefficient should be positive and circa log(1.6)~0.47)")

# H2: Fractional publications and collaboration
mod_h2 = run_fixed_effects_reg(df, "log_frac_pubs", ["collab_frac"])
print("\nH2: log(fractional publications) ~ collaboration fraction")
print(f"coeff = {mod_h2.params.loc['collab_frac']:.4f}, p-value = {mod_h2.pvalues.loc['collab_frac']:.4f}")
print("PAPER_REPORTED: Up to 4 coauthors, collaboration is associated with more papers per author. (SYNTHETIC may show small or positive coefficient)")

# H3: Attributed quality under alternative α(N)
# Using α(N) = 1/N (equal share)
mod_h3_eq = run_fixed_effects_reg(df, "log_attributed_cites", ["collab_frac"])
print("\nH3 (α=1/N): log(attributed citations) ~ collaboration fraction")
print(f"coeff = {mod_h3_eq.params.loc['collab_frac']:.4f}, p-value = {mod_h3_eq.pvalues.loc['collab_frac']:.4f}")

# Using α(N) = 1/sqrt(N)
mod_h3_sqrt = run_fixed_effects_reg(df, "log_attributed_cites_sqrt", ["collab_frac"])
print("\nH3 (α=1/sqrt(N)): log(attributed citations) ~ collaboration fraction")
print(f"coeff = {mod_h3_sqrt.params.loc['collab_frac']:.4f}, p-value = {mod_h3_sqrt.pvalues.loc['collab_frac']:.4f}")

# Using α(N) = 1 (full credit)
mod_h3_full = run_fixed_effects_reg(df, "log_attributed_cites_linear", ["collab_frac"])
print("\nH3 (α=1, full credit): log(attributed citations) ~ collaboration fraction")
print(f"coeff = {mod_h3_full.params.loc['collab_frac']:.4f}, p-value = {mod_h3_full.pvalues.loc['collab_frac']:.4f}")

# Using α(N) = 1/N^0.6 (the true synthetic)
mod_h3_06 = run_fixed_effects_reg(df, "log_attributed_cites_06", ["collab_frac"])
print("\nH3 (α=1/N^0.6, synthetic truth): log(attributed citations) ~ collaboration fraction")
print(f"coeff = {mod_h3_06.params.loc['collab_frac']:.4f}, p-value = {mod_h3_06.pvalues.loc['collab_frac']:.4f}")
print("PAPER_REPORTED: credit sharing sums to more than 1, i.e., scientists behave as if they receive a share greater than equal division.")

# Cross-department and senior effects (additional analysis)
# We must reconstruct collaboration type dummies from the paper-level data.
# For simplicity, we compute fraction of papers that are cross-departmental, senior, etc.
papers_types = papers_df.merge(df[["scientist_id","year"]], on=["scientist_id","year"])
# compute fractions
frac_cross = papers_types.groupby(["scientist_id","year"])["cross_dept"].mean().reset_index(name="frac_cross")
frac_senior = papers_types.groupby(["scientist_id","year"])["senior"].mean().reset_index(name="frac_senior")
# for cross-senior interaction: fraction of papers that are both cross and senior? Rare. We'll only show simple.
df = df.merge(frac_cross, on=["scientist_id","year"], how="left").merge(frac_senior, on=["scientist_id","year"], how="left")
df[["frac_cross","frac_senior"]] = df[["frac_cross","frac_senior"]].fillna(0)

# Quality with collaboration types
try:
    mod_types = run_fixed_effects_reg(df, "log_avg_cites", ["frac_cross", "frac_senior"])
    print("\nQuality vs cross-dept and senior collaboration (SYNTHETIC):")
    print(mod_types.params)
    print("PAPER_REPORTED: cross-dept collab -> higher quality; senior collab -> lower quality gain (free-riding).")
except Exception as e:
    print("Could not run type regression:", e)

# --------------------------------------------------------------------
# 5. Print summary of key numbers matching paper descriptions
# --------------------------------------------------------------------
print("\n--- Summary of synthetic dataset ---")
print(f"Number of scientists: {df['scientist_id'].nunique()}")
print(f"Total scientist-years: {len(df)}")
print(f"Total publications (papers): {papers_df.shape[0]}")
print("All displayed regression results are based on SYNTHETIC data and serve only as illustration.")
