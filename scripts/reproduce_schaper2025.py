#!/usr/bin/env python3
"""
Reproduce: "Not like the others: Frontier scientists for inventive performance"
Schaper, Arts, Veugelers (2025, Research Policy) — CORRECTED VERSION

Fixes applied (per Codex audit):
  1. Look-ahead bias: frontier status from papers ≥1yr BEFORE focal paper year
  2. Table 6 colinearity: omit reference category explicitly
  3. Wald tests + confidence intervals for key comparisons
  4. Distinguish "no refs" from data-missing; use has_ref as filter

Methodology mapping (patent → paper):
  Frontier-author patent → Paper whose authors had recent top-journal pubs
  Patent forward citations → paper citation_count
  Frontier SNPR → frontier reference (cites recent top-journal paper)
  Patent class×year FE → journal×decade FE
"""

import sys, json
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.sciscigpt_local.sciscinet_connector import load_table

# ── Constants ──
TOP_GENERAL_JOURNALS = {
    "Nature", "Science", "Cell",
    "Proceedings of the National Academy of Sciences of the United States of America",
    "The Lancet", "The New England Journal of Medicine",
    "JAMA", "The BMJ", "BMJ",
}
RECENCY_WINDOW = 3        # frontier = top journal within 3 years
LOOKAHEAD_LAG = 1          # frontier pubs must be ≥1 year before focal paper

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "refine-logs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════
# 1. LOAD DATA
# ══════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("Schaper, Arts, Veugelers (2025) — Corrected Reproduction")
print("=" * 70)

print("\n[1/5] Loading data...")
papers = load_table("papers")
pc   = load_table("paper_citations")
pa   = load_table("paper_author_affiliations")
print(f"  Papers: {len(papers):,}")
print(f"  Citations: {len(pc):,}")
print(f"  Paper-author links: {len(pa):,}")

# ══════════════════════════════════════════════════════════════════════════
# 2. BUILD AUTHOR PUBLICATION HISTORIES (look-ahead-bias-free)
# ══════════════════════════════════════════════════════════════════════════
print("\n[2/5] Building author publication histories (no look-ahead)...")

papers_clean = papers.dropna(subset=["year", "citation_count", "journal_name"]).copy()
papers_clean["year"] = papers_clean["year"].astype(int)

# Per author: set of years they published in a top journal
author_pubs = defaultdict(list)
pa_with_meta = pa.merge(
    papers_clean[["paper_id", "year", "journal_name"]],
    on="paper_id", how="inner"
)
for row in pa_with_meta.itertuples():
    author_pubs[row.author_id].append((row.paper_id, row.year, row.journal_name))

def get_frontier_eligible_years(pub_list):
    """
    An author is 'frontier-eligible' in year Y if they published
    a top-journal paper in any year in [Y - RECENCY_WINDOW, Y - LOOKAHEAD_LAG].

    LOOKAHEAD_LAG = 1 ensures the focal paper itself cannot retroactively
    make its own author "frontier".
    """
    top_years = set()
    for pid, yr, jn in pub_list:
        if isinstance(jn, str) and jn in TOP_GENERAL_JOURNALS:
            top_years.add(yr)

    eligible_years = set()
    for ty in top_years:
        # Author is frontier from ty+LOOKAHEAD_LAG to ty+RECENCY_WINDOW
        for future_yr in range(ty + LOOKAHEAD_LAG, ty + RECENCY_WINDOW + 1):
            eligible_years.add(future_yr)
    return eligible_years

print("  Computing frontier eligible years per author...")
author_frontier_years = {}
for aid, pubs in author_pubs.items():
    ey = get_frontier_eligible_years(pubs)
    if ey:
        author_frontier_years[aid] = ey

n_frontier = len(author_frontier_years)
print(f"  Authors ever frontier-eligible: {n_frontier:,} "
      f"({n_frontier/len(author_pubs)*100:.1f}%)")

# ══════════════════════════════════════════════════════════════════════════
# 3. BUILD PAPER-LEVEL DATASET
# ══════════════════════════════════════════════════════════════════════════
print("\n[3/5] Building paper-level dataset...")

paper_authors_map = pa.groupby("paper_id")["author_id"].apply(list)

# --- classify each sampled paper ---
def classify_paper(pid, paper_year):
    """Returns 'frontier_author' | 'non_frontier_author' | 'no_author_pub'."""
    author_list = paper_authors_map.get(pid, [])
    if len(author_list) == 0:
        return "no_author_pub"

    has_frontier = False
    has_any_pub  = False
    for aid in author_list:
        f_years = author_frontier_years.get(aid, set())
        if paper_year in f_years:
            has_frontier = True
        if aid in author_pubs:
            has_any_pub = True

    if has_frontier:
        return "frontier_author"
    elif has_any_pub:
        return "non_frontier_author"
    else:
        return "no_author_pub"

# Sample for tractability
paper_ids_all = list(set(papers_clean["paper_id"]) & set(paper_authors_map.index))
sample_size = min(80000, len(paper_ids_all))
sampled_ids = paper_ids_all[:sample_size]

# Build year lookup
paper_year_lookup = dict(zip(papers_clean["paper_id"], papers_clean["year"]))

print(f"  Classifying {len(sampled_ids):,} papers...")
classifications = {}
for i, pid in enumerate(sampled_ids):
    if i % 20000 == 0 and i > 0:
        print(f"    {i}/{len(sampled_ids)}...")
    yr = paper_year_lookup.get(pid, 0)
    classifications[pid] = classify_paper(pid, yr)

# Merge into regression dataframe
class_s = pd.Series(classifications, name="author_class")
df = papers_clean[papers_clean["paper_id"].isin(sampled_ids)].copy()
df = df.merge(class_s, left_on="paper_id", right_index=True, how="inner")

# --- Binary indicators ---
df["frontier_author"]     = (df["author_class"] == "frontier_author").astype(int)
df["non_frontier_author"] = (df["author_class"] == "non_frontier_author").astype(int)
df["no_author_pub"]       = (df["author_class"] == "no_author_pub").astype(int)

# --- Detailed author types (Table 2 Col 3 analogue) ---
MAX_YR = int(df["year"].max())
df["in_top_journal"] = df["journal_name"].isin(TOP_GENERAL_JOURNALS).astype(int)
df["is_recent"]      = (df["year"] >= MAX_YR - RECENCY_WINDOW).astype(int)

df["fa_frontier"]       = df["frontier_author"]
df["fa_top_old"]        = ((df["author_class"] == "non_frontier_author") & df["in_top_journal"]).astype(int)
df["fa_recent_only"]    = ((df["author_class"] == "non_frontier_author") & ~df["in_top_journal"].astype(bool) & df["is_recent"]).astype(int)
df["fa_other"]          = ((df["author_class"] == "non_frontier_author") & ~df["in_top_journal"].astype(bool) & ~df["is_recent"].astype(bool)).astype(int)
df["fa_no_pub"]         = df["no_author_pub"]

# --- FE construction ---
df["journal_decade"] = (df["journal_name"].astype(str) + "_" +
                         (df["year"] // 10 * 10).astype(str))
jd_counts = df.groupby("journal_decade").size()
valid_jd = jd_counts[jd_counts >= 15].index
df = df[df["journal_decade"].isin(valid_jd)].copy()

# Hit paper: top 5% within journal-decade
df["cit_pct"] = df.groupby("journal_decade")["citation_count"].transform(
    lambda x: x.rank(pct=True))
df["hit_paper"] = (df["cit_pct"] >= 0.95).astype(int)

# Derived variables
df["log_cit"]      = np.log1p(df["citation_count"])
df["has_ref"]      = (df["reference_count"].fillna(0) > 0).astype(int)

# Drop rows with missing controls
df = df.dropna(subset=["citation_count", "author_count", "year", "reference_count"])
print(f"\n  Regression sample: {len(df):,}")
print(f"  Frontier-author papers:   {df['frontier_author'].sum():,} "
      f"({df['frontier_author'].mean()*100:.1f}%)")
print(f"  Non-frontier-author:      {df['non_frontier_author'].sum():,} "
      f"({df['non_frontier_author'].mean()*100:.1f}%)")
print(f"  No-author-pub papers:     {df['no_author_pub'].sum():,} "
      f"({df['no_author_pub'].mean()*100:.1f}%)")

# --- Frontier reference indicator ---
print("\n  Computing frontier reference flags...")
paper_year_d = dict(zip(papers["paper_id"], papers["year"]))
paper_jrnl_d = dict(zip(papers["paper_id"], papers["journal_name"]))

relevant_ids = set(df["paper_id"])
citing_subset = pc[pc["citing_paper_id"].isin(relevant_ids)]
cited_lookup = citing_subset.groupby("citing_paper_id")["cited_paper_id"].apply(list)

def is_frontier_ref(citing_id, citing_yr):
    cited = cited_lookup.get(citing_id, [])
    for cid in cited:
        c_yr = paper_year_d.get(cid)
        if c_yr is None:
            continue
        c_j = paper_jrnl_d.get(cid, "")
        if (isinstance(c_j, str) and c_j in TOP_GENERAL_JOURNALS
            and (citing_yr - int(c_yr)) >= LOOKAHEAD_LAG
            and (citing_yr - int(c_yr)) <= RECENCY_WINDOW):
            return True
    return False

df["has_frontier_ref"] = df.apply(
    lambda r: int(is_frontier_ref(r["paper_id"], r["year"])), axis=1)

print(f"  Papers with frontier refs: {df['has_frontier_ref'].sum():,} "
      f"({df['has_frontier_ref'].mean()*100:.2f}%)")

# --- Interaction categories (Table 6) ---
# FA = frontier_author, NFA = non_frontier_author, NAP = no_author_pub
# FREF = has_frontier_ref, NONFREF = has_ref but no frontier ref, NOREF = no refs

def assign_t6_cat(row):
    if row["frontier_author"]:
        if row["has_frontier_ref"]:
            return "FA_FREF"
        elif row["has_ref"]:
            return "FA_NONFREF"
        else:
            return "FA_NOREF"
    elif row["non_frontier_author"]:
        if row["has_frontier_ref"]:
            return "NFA_FREF"
        elif row["has_ref"]:
            return "NFA_NONFREF"
        else:
            return "NFA_NOREF"       # ← reference category
    else:  # no_author_pub
        if row["has_frontier_ref"]:
            return "NAP_FREF"
        elif row["has_ref"]:
            return "NAP_NONFREF"
        else:
            return "NAP_NOREF"

df["t6_cat"] = df.apply(assign_t6_cat, axis=1)
print(f"\n  Table 6 category distribution:")
for cat in sorted(df["t6_cat"].unique()):
    n = (df["t6_cat"] == cat).sum()
    print(f"    {cat:20s}: {n:6,}  ({n/len(df)*100:5.2f}%)")

# ══════════════════════════════════════════════════════════════════════════
# 4. REGRESSION ANALYSES
# ══════════════════════════════════════════════════════════════════════════
print("\n[4/5] Running regressions...")
print("=" * 70)

CTRL = "+ year + author_count + reference_count"        # core controls
CTRL_FE = "+ C(journal_decade) + year + author_count"    # with journal-decade FE

def report_coef(model, var, label="", model_type="ols"):
    """Print coefficient with SE and significance."""
    coef = model.params.get(var, np.nan)
    se   = model.bse.get(var, np.nan)
    if np.isnan(coef):
        return coef, se
    if model_type == "ppml":
        effect = f"exp={np.exp(coef):.3f}"
    else:
        effect = f"{coef:.4f}"
    stars = ""
    if not np.isnan(se):
        t = abs(coef / se) if se > 0 else 0
        p  = 2 * (1 - stats.norm.cdf(t)) if t > 0 else 1.0
        if   p < 0.01: stars = "***"
        elif p < 0.05: stars = "**"
        elif p < 0.10: stars = "*"
        print(f"  {label:30s}: {coef:10.4f}  (SE={se:.4f})  [{effect}]{stars}")
    else:
        print(f"  {label:30s}: {coef:10.4f}  [{effect}]")
    return coef, se

def wald_test(model, var1, var2, label=""):
    """Wald test H0: coef[var1] = coef[var2]."""
    b1 = model.params.get(var1)
    b2 = model.params.get(var2)
    # var2 may be reference category (omitted from model, b2=0)
    if b2 is None:
        b2 = 0.0
    if b1 is None:
        b1 = 0.0
    if np.isnan(b1) if isinstance(b1, float) else False:
        print(f"  Wald({label}): skipped (NaN coef)")
        return np.nan
    if np.isnan(b2) if isinstance(b2, float) else False:
        print(f"  Wald({label}): skipped (NaN coef)")
        return np.nan
    vcov = model.cov_params()
    v1 = vcov.loc[var1, var1] if var1 in vcov.index else 0.0
    v2 = vcov.loc[var2, var2] if var2 in vcov.index else 0.0  # reference category → var=0
    cv = vcov.loc[var1, var2] if var1 in vcov.index and var2 in vcov.index else 0.0
    se_diff = np.sqrt(max(v1 + v2 - 2*cv, 0))
    if se_diff == 0 or np.isnan(se_diff):
        print(f"  Wald({label}): skipped (zero/NaN SE)")
        return np.nan
    z = (b1 - b2) / se_diff
    p  = 2 * (1 - stats.norm.cdf(abs(z)))
    diff_pct = (np.exp(b1 - b2) - 1) * 100
    stars = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""
    print(f"  Wald[{label}]: diff={b1-b2:.4f} SE={se_diff:.4f} z={z:.2f} p={p:.4f} "
          f"[Δ={diff_pct:+.1f}%]{stars}")
    return p

# ── TABLE 1: Summary Statistics ──
print("\n── TABLE 1: Summary Statistics ──\n")
for name, mask in [
    ("Frontier-author paper",      df["frontier_author"] == 1),
    ("Non-frontier-author paper",  df["non_frontier_author"] == 1),
    ("No-author-pub paper",        df["no_author_pub"] == 1),
]:
    g = df[mask]
    print(f"  {name:35s}: N={len(g):,}  hit_rate={g['hit_paper'].mean():.3f}"
          f"  mean_cit={g['citation_count'].mean():.1f}  "
          f"med_cit={g['citation_count'].median():.1f}  "
          f"mean_refs={g['reference_count'].mean():.1f}  "
          f"frontier_ref={g['has_frontier_ref'].mean():.3f}  "
          f"mean_auth={g['author_count'].mean():.1f}")

# ── TABLE 2: Citation Impact ──
print("\n── TABLE 2: Frontier-author papers and citation impact ──\n")

# Check which categories are present
has_no_author_pub = (df["no_author_pub"].sum() > 0)
has_non_frontier    = (df["non_frontier_author"].sum() > 0)
has_frontier        = (df["frontier_author"].sum() > 0)
print(f"  Categories present: no_author_pub={has_no_author_pub}, "
      f"non_frontier={has_non_frontier}, frontier={has_frontier}")

# Col 1: Frontier-author (vs non-frontier) — the core H1 test
b_fa_ppml = np.nan
b_nfa_ppml = np.nan
b_fa_log = np.nan
b_nfa_log = np.nan

if not has_no_author_pub:
    # No "no_author_pub" papers → use non_frontier_author as reference
    # H1: frontier_author > 0 means FA papers receive more citations than NFA
    print("  Using non_frontier_author as reference (no no_author_pub papers in sample)\n")
    print("  Column 1: Frontier-author vs. Non-frontier-author (PPML)")
    try:
        m_t2c1 = smf.glm(
            f"citation_count ~ frontier_author {CTRL_FE}",
            data=df, family=sm.families.Poisson(link=sm.families.links.Log()),
        ).fit(method="bfgs", maxiter=200, disp=0)
        b_fa_ppml, _ = report_coef(m_t2c1, "frontier_author",
                                    "Frontier-author (ref=NFA)", "ppml")
    except Exception as e:
        print(f"  PPML failed: {e}")
        m_t2c1 = None

    print("\n  Column 1b: OLS log-linear (primary)")
    m_ols_main = smf.ols(f"log_cit ~ frontier_author {CTRL_FE}", data=df).fit()
    b_fa_log, _ = report_coef(m_ols_main, "frontier_author",
                               "Frontier-author (ref=NFA)")
    b_nfa_log = 0.0  # reference category
    print(f"  Intercept (base NFA log-cit): {m_ols_main.params.get('Intercept', np.nan):.4f}")

    # Col 2: Decompose frontier into top-journal × recency
    print("\n  Column 2: Detailed author categories (ref=other_author_pub, OLS)")
    # fa_other is the largest category and serves as reference
    m_t2c2 = smf.ols(
        f"log_cit ~ fa_frontier + fa_top_old + fa_recent_only {CTRL_FE}",
        data=df).fit()
    b_fa_log, _ = report_coef(m_t2c2, "fa_frontier", "Frontier (top+recent)")
    report_coef(m_t2c2, "fa_top_old", "Top journal, not recent")
    report_coef(m_t2c2, "fa_recent_only", "Recent, not top journal")
    wald_test(m_t2c2, "fa_frontier", "fa_top_old", "Frontier vs Top-old")
    wald_test(m_t2c2, "fa_frontier", "fa_recent_only", "Frontier vs Recent-only")
    print(f"  Adj R²: {m_t2c2.rsquared_adj:.3f}")

else:
    # Has no_author_pub papers — use as reference
    print("  Using no_author_pub as reference\n")
    print("  Column 1: Frontier vs Non-frontier vs No-pub (PPML)")
    try:
        m_t2c1 = smf.glm(
            f"citation_count ~ frontier_author + non_frontier_author {CTRL_FE}",
            data=df, family=sm.families.Poisson(link=sm.families.links.Log()),
        ).fit(method="bfgs", maxiter=200, disp=0)
        b_fa_ppml, _ = report_coef(m_t2c1, "frontier_author", "Frontier author", "ppml")
        b_nfa_ppml, _ = report_coef(m_t2c1, "non_frontier_author", "Non-frontier author", "ppml")
    except Exception as e:
        print(f"  PPML failed: {e}")

    print("\n  Column 1b: OLS log-linear")
    m_ols_main = smf.ols(
        f"log_cit ~ frontier_author + non_frontier_author {CTRL_FE}", data=df).fit()
    b_fa_log, _ = report_coef(m_ols_main, "frontier_author", "Frontier author (OLS)")
    b_nfa_log, _ = report_coef(m_ols_main, "non_frontier_author", "Non-frontier author (OLS)")
    wald_test(m_ols_main, "frontier_author", "non_frontier_author", "FA vs NFA (OLS)")

    # Col 3: Decompose frontier
    print("\n  Column 3: Detailed author categories (ref=no_author_pub, OLS)")
    m_t2c2 = smf.ols(
        f"log_cit ~ fa_frontier + fa_top_old + fa_recent_only + fa_other {CTRL_FE}",
        data=df).fit()
    for var, label in [("fa_frontier", "Frontier (top+recent)"),
                        ("fa_top_old", "Top journal, not recent"),
                        ("fa_recent_only", "Recent, not top journal"),
                        ("fa_other", "Other author-pub")]:
        report_coef(m_t2c2, var, label)
    wald_test(m_t2c2, "fa_frontier", "fa_top_old", "Frontier vs Top-old")
    wald_test(m_t2c2, "fa_frontier", "fa_recent_only", "Frontier vs Recent-only")
    print(f"  Adj R²: {m_t2c2.rsquared_adj:.3f}")

# ── TABLE 3: Alternative Impact ──
print("\n── TABLE 3: Frontier-author papers and alternative impact (OLS) ──\n")

# Build formula adaptively: use only frontier_author when no_author_pub absent
if has_no_author_pub:
    fa_formula = "frontier_author + non_frontier_author"
    fa_terms = [("frontier_author", "Frontier author"), ("non_frontier_author", "Non-frontier author")]
else:
    fa_formula = "frontier_author"
    fa_terms = [("frontier_author", "Frontier author (ref=NFA)")]

print("  Column 1: Hit paper [0/1]")
m_hit = smf.ols(f"hit_paper ~ {fa_formula} {CTRL_FE}", data=df).fit()
for var, label in fa_terms:
    report_coef(m_hit, var, label)
if has_no_author_pub:
    wald_test(m_hit, "frontier_author", "non_frontier_author", "FA vs NFA (hit)")
print(f"  Adj R²: {m_hit.rsquared_adj:.3f}")

print("\n  Column 2: Log citations (Table 2 revisited)")
for var, label in fa_terms:
    report_coef(m_ols_main, var, label)
print(f"  Adj R²: {m_ols_main.rsquared_adj:.3f}")

# ── TABLE 5: Frontier Reference Likelihood ──
print("\n── TABLE 5: Frontier-author papers and frontier-ref likelihood ──\n")

print("  Column 1: Has any reference [0/1]")
m_hasref = smf.ols(f"has_ref ~ {fa_formula} {CTRL_FE}", data=df).fit()
b_hr_fa = np.nan; b_hr_nfa = np.nan
for var, label in fa_terms:
    coef, _ = report_coef(m_hasref, var, label)
    if var == "frontier_author": b_hr_fa = coef
    if var == "non_frontier_author": b_hr_nfa = coef
if has_no_author_pub:
    wald_test(m_hasref, "frontier_author", "non_frontier_author", "FA vs NFA (has ref)")
print(f"  Adj R²: {m_hasref.rsquared_adj:.3f}")

# Col 2: Number of refs | has_ref
print("\n  Column 2: Log references | has_ref (OLS)")
df_ref = df[df["has_ref"] == 1].copy()
df_ref["log_refs"] = np.log(df_ref["reference_count"])
m_nrefs = smf.ols(f"log_refs ~ {fa_formula} {CTRL_FE}", data=df_ref).fit()
b_nr_fa = np.nan; b_nr_nfa = np.nan
for var, label in fa_terms:
    coef, _ = report_coef(m_nrefs, var, label)
    if var == "frontier_author": b_nr_fa = coef
    if var == "non_frontier_author": b_nr_nfa = coef
print(f"  Adj R² (df_ref): {m_nrefs.rsquared_adj:.3f}, N={len(df_ref):,}")

# Col 3: Has frontier ref | has_ref
print("\n  Column 3: Has frontier ref | has_ref (OLS LPM)")
m_fref = smf.ols(f"has_frontier_ref ~ {fa_formula} {CTRL_FE}",
                 data=df_ref).fit()
b_fr_fa = np.nan; b_fr_nfa = np.nan
for var, label in fa_terms:
    coef, _ = report_coef(m_fref, var, label)
    if var == "frontier_author": b_fr_fa = coef
    if var == "non_frontier_author": b_fr_nfa = coef
if has_no_author_pub:
    wald_test(m_fref, "frontier_author", "non_frontier_author", "FA vs NFA (frontier ref)")
print(f"  Adj R² (df_ref): {m_fref.rsquared_adj:.3f}")

# ── TABLE 6: Interaction Model (CORRECTED: reference = NFA_NOREF) ──
print("\n── TABLE 6: Frontier-author × frontier-ref interactions (CORRECTED) ──")
print("  Reference category: NFA_NOREF (non-frontier author, no references)")

# Only keep categories with data
all_t6_cats = ["FA_FREF", "FA_NONFREF", "FA_NOREF",
               "NFA_FREF", "NFA_NONFREF",
               "NAP_FREF", "NAP_NONFREF", "NAP_NOREF"]
t6_cats = [c for c in all_t6_cats if (df["t6_cat"] == c).sum() > 0]
t6_missing = [c for c in all_t6_cats if c not in t6_cats]
if t6_missing:
    print(f"  Dropped (no data): {', '.join(t6_missing)}")
# NFA_NOREF is the omitted reference

for cat in t6_cats:
    df[f"d_{cat}"] = (df["t6_cat"] == cat).astype(int)

# Verify reference category
ref_mask = df["t6_cat"] == "NFA_NOREF"
print(f"  Reference group NFA_NOREF: N={ref_mask.sum():,} "
      f"({ref_mask.mean()*100:.1f}%)\n")

all_dummies = " + ".join([f"d_{c}" for c in t6_cats])

print("  Column 1: Log citations (OLS) — with journal-decade FE")
m_t6_log = smf.ols(f"log_cit ~ {all_dummies} {CTRL_FE}", data=df).fit()
for cat in t6_cats:
    report_coef(m_t6_log, f"d_{cat}", cat)
print(f"\n  Adj R²: {m_t6_log.rsquared_adj:.3f}")

# Key Wald tests for H3
print("\n  Key Hypothesis Tests (H3):")
p1 = np.nan; p2 = np.nan; p3 = np.nan; p4 = np.nan
if "FA_FREF" in t6_cats and "NFA_FREF" in t6_cats:
    p1 = wald_test(m_t6_log, "d_FA_FREF", "d_NFA_FREF",
                   "FA_FREF vs NFA_FREF [does FA add premium beyond FREF?]")
if "FA_NOREF" in t6_cats:
    p2 = wald_test(m_t6_log, "d_FA_NOREF", "d_NFA_NOREF",
                   "FA_NOREF vs NFA_NOREF [FA premium WITHOUT frontier refs? — THE KEY TEST]")
if "FA_FREF" in t6_cats and "FA_NOREF" in t6_cats:
    p3 = wald_test(m_t6_log, "d_FA_FREF", "d_FA_NOREF",
                   "FA_FREF vs FA_NOREF [does frontier ref boost FA papers?]")
if "NFA_FREF" in t6_cats:
    p4 = wald_test(m_t6_log, "d_NFA_FREF", "d_NFA_NOREF",
                   "NFA_FREF vs NFA_NOREF [does frontier ref boost NFA papers?]")

print("\n  Column 2: Hit paper (OLS LPM)")
m_t6_hit = smf.ols(f"hit_paper ~ {all_dummies} {CTRL_FE}", data=df).fit()
for cat in t6_cats:
    report_coef(m_t6_hit, f"d_{cat}", cat)
print(f"\n  Adj R²: {m_t6_hit.rsquared_adj:.3f}")

print("\n  Column 3: Citation count (PPML)")
try:
    m_t6_ppml = smf.glm(
        f"citation_count ~ {all_dummies} {CTRL_FE}",
        data=df, family=sm.families.Poisson(link=sm.families.links.Log()),
    ).fit(method="bfgs", maxiter=200, disp=0)
    for cat in t6_cats:
        report_coef(m_t6_ppml, f"d_{cat}", cat, "ppml")
except Exception as e:
    print(f"  PPML Table 6 failed: {e}")
    m_t6_ppml = None

# ══════════════════════════════════════════════════════════════════════════
# 5. SUMMARY COMPARISON
# ══════════════════════════════════════════════════════════════════════════
print("\n[5/5] Comparison with original paper...\n" + "=" * 70)

# Extract the critical H3 test result
fa_noref_coef = m_t6_log.params.get("d_FA_NOREF", np.nan) if "FA_NOREF" in t6_cats else np.nan
fa_noref_se   = m_t6_log.bse.get("d_FA_NOREF", np.nan) if "FA_NOREF" in t6_cats else np.nan
# NFA_NOREF is the reference (coef = 0 by definition)

# Safe formatting helpers
def _pct(x): return f"{x*100:+.1f}%" if not np.isnan(x) else "N/A"
def _fmt(x):  return f"{x:+.3f}" if not np.isnan(x) else "N/A"
def _pfmt(p): return f"{p:.4f}" if not (p is None or np.isnan(p)) else "N/A"

h1_result = "CONSISTENT (FA > NFA)" if (not np.isnan(b_fa_log) and b_fa_log > 0) else "CHECK"
h2_result = "CONSISTENT (FA > NFA)" if (not np.isnan(b_fr_fa) and not np.isnan(b_fr_nfa) and b_fr_fa > b_fr_nfa) else "CHECK"
h3_critical = ("CONSISTENT (both weak/ns)" if (p2 is not None and not np.isnan(p2) and p2 > 0.10)
               else "INCONSISTENT (FA no-ref premium found)" if (not np.isnan(fa_noref_coef) and fa_noref_coef > 0
                       and p2 is not None and not np.isnan(p2) and p2 < 0.10)
               else "CHECK")
h3_fref = ("CONSISTENT: frontier refs benefit all" if (p3 is not None and p4 is not None
           and not np.isnan(p3) and not np.isnan(p4) and p3 < 0.10 and p4 < 0.10) else "PARTIAL/CHECK")

print(f"""
┌─────────────────────────────────────────────────────────────────────────┐
│           CORRECTED REPRODUCTION: Key Findings vs. Original             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ H1: Frontier > non-frontier citation impact                             │
│   Original (PPML): FA +30% vs NFA +14%, diff = +14% (p<0.01)          │
│   Corrected (PPML): FA {_pct(np.exp(b_fa_ppml)-1 if not np.isnan(b_fa_ppml) else np.nan)} vs NFA (ref)    │
│   Corrected (OLS):  FA {_fmt(b_fa_log)} vs NFA (ref) log pts           │
│   → {h1_result}                                                         │
│                                                                         │
│ H2: Frontier authors more likely to cite frontier science               │
│   Original: FA +17.6pp vs NFA +0.4pp (ns) in frontier ref likelihood   │
│   Corrected: FA {_fmt(b_fr_fa)} vs NFA (ref) frontier ref likelihood   │
│   → {h2_result}                                                         │
│                                                                         │
│ H3: Frontier authors WITHOUT frontier refs — is there still a premium? │
│   Original: FA_NOREF=+0.217 vs NFA_NOREF=+0.125 (ref=no_author)       │
│             → diff=+0.092, NOT significant at 10%                       │
│   Corrected: FA_NOREF={_fmt(fa_noref_coef)} (SE={_fmt(fa_noref_se)})   │
│             NFA_NOREF = 0 (reference)                                   │
│             → diff={_fmt(fa_noref_coef)}, p={_pfmt(p2)}                 │
│   → {h3_critical}                                                       │
│                                                                         │
│ H3: Frontier refs boost impact for ALL author types?                    │
│   FA_FREF vs FA_NOREF: p = {_pfmt(p3)}                                  │
│   NFA_FREF vs NFA_NOREF: p = {_pfmt(p4)}                                │
│   → {h3_fref}                                                           │
│                                                                         │
│ CORRECTIONS APPLIED:                                                    │
│   1. Look-ahead bias eliminated (frontier pubs ≥{LOOKAHEAD_LAG}yr before focal)          │
│   2. Table 6 reference category explicitly specified (NFA_NOREF)        │
│   3. Wald tests with p-values for all key comparisons                   │
│   4. NFA_NOREF as clean baseline (non-frontier, no refs)                │
│   5. Journal-decade FE + year trend for within-field comparison         │
│                                                                         │
│ DATA NOTE:                                                              │
│   Sample: {len(df):,} papers, {int(df['frontier_author'].sum())} FA, {int(df['non_frontier_author'].sum())} NFA        │
│   No no_author_pub papers in sample (all papers have author histories)  │
│   Frontier ref rate: {df['has_frontier_ref'].mean()*100:.2f}% overall                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
""")

# ── Save results ──
def _safe_float(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    return float(x)

results = {
    "paper": "Schaper, Arts, Veugelers (2025) — Corrected Reproduction",
    "corrections": [
        "Look-ahead bias: frontier pubs >=1yr before focal paper year",
        "Table 6 colinearity fixed: NFA_NOREF = reference category",
        "Wald tests for all key H1/H2/H3 comparisons",
        "Journal-decade FE for within-field comparison",
        "Distinguished no-refs from has-refs in all models",
    ],
    "sample": {
        "n_total": len(df),
        "n_frontier_author": int(df["frontier_author"].sum()),
        "n_non_frontier_author": int(df["non_frontier_author"].sum()),
        "n_no_author_pub": int(df["no_author_pub"].sum()),
        "frontier_ref_rate": float(df["has_frontier_ref"].mean()),
    },
    "h1_ols": {
        "frontier_author_coef": _safe_float(b_fa_log),
        "non_frontier_coef": _safe_float(b_nfa_log),
        "h1_consistent": h1_result,
    },
    "h2_frontier_ref": {
        "fa_coef": _safe_float(b_fr_fa),
        "nfa_coef": _safe_float(b_fr_nfa),
        "h2_consistent": h2_result,
    },
    "h3_critical_test": {
        "fa_noref_vs_nfa_noref_coef": _safe_float(fa_noref_coef),
        "fa_noref_se": _safe_float(fa_noref_se),
        "wald_p_value": _safe_float(p2),
        "interpretation": h3_critical,
    },
    "table6_wald_tests": {
        "FA_FREF_vs_NFA_FREF_p": _safe_float(p1),
        "FA_NOREF_vs_NFA_NOREF_p": _safe_float(p2),
        "FA_FREF_vs_FA_NOREF_p": _safe_float(p3),
        "NFA_FREF_vs_NFA_NOREF_p": _safe_float(p4),
    },
}

out_path = OUTPUT_DIR / "reproduce_schaper2025_corrected.json"
out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(f"Results saved to {out_path}")
print("Done!")
