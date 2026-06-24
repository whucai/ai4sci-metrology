#!/usr/bin/env python3
"""
Export PatentsView patent metadata from Google BigQuery for Schaper 2025 reproduction.

BigQuery public dataset: patents-public-data.patentsview
Free tier: 1 TB/month. Total scan: ~4 GB (~0.4% of quota).

Exports to: data/uspto-pubmed/patentsview/

Tables exported:
  1. patents.parquet       — patent metadata (id, date, type, num_claims)
  2. forward_cites.parquet — forward citation counts per patent
  3. wipo_class.parquet    — primary IPC/WIPO class per patent
  4. nber_cat.parquet      — NBER technology categories
  5. patent_inventor.parquet — patent-inventor links
"""

import os
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "uspto-pubmed" / "patentsview"
DATA_DIR.mkdir(parents=True, exist_ok=True)

KEY_FILE = PROJECT_ROOT / "psychic-binder-498910-v8-72b71230a45e.json"
if KEY_FILE.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(KEY_FILE)

client = bigquery.Client()
print(f"Project: {client.project}")

# Common subquery: patent sample 1976-2022
PATENT_SAMPLE = """
    SELECT id, date, type, num_claims
    FROM `patents-public-data.patentsview.patent`
    WHERE date >= '1976-01-01'
      AND date < '2023-01-01'
      AND REGEXP_CONTAINS(id, r'^[0-9]')
"""

# ══════════════════════════════════════════════════════════════════════════
# 1. Patent metadata
# ══════════════════════════════════════════════════════════════════════════
print("\n[1/5] Exporting patent metadata (1976-2022, US utility patents)...")

patents = client.query(f"""
    SELECT
      id AS patent_id,
      CAST(date AS STRING) AS patent_date,
      SUBSTR(type, 1, 20) AS patent_type,
      num_claims
    FROM `patents-public-data.patentsview.patent`
    WHERE date >= '1976-01-01'
      AND date < '2023-01-01'
      AND REGEXP_CONTAINS(id, r'^[0-9]')
""").to_dataframe()

patents["patent_year"] = pd.to_datetime(patents["patent_date"]).dt.year
print(f"  Patents: {len(patents):,}")
patents.to_parquet(DATA_DIR / "patents.parquet", index=False)

# ══════════════════════════════════════════════════════════════════════════
# 2. Forward citation counts (citations RECEIVED by each patent)
# ══════════════════════════════════════════════════════════════════════════
print("\n[2/5] Computing forward citation counts...")

fwd_cites = client.query(f"""
    SELECT
      citation_id AS patent_id,
      COUNT(*) AS num_cited_by_us_patents
    FROM `patents-public-data.patentsview.uspatentcitation`
    WHERE citation_id IN (
      SELECT id FROM `patents-public-data.patentsview.patent`
      WHERE date >= '1976-01-01'
        AND date < '2023-01-01'
        AND REGEXP_CONTAINS(id, r'^[0-9]')
    )
    GROUP BY citation_id
""").to_dataframe()

print(f"  Patents with ≥1 forward citation: {len(fwd_cites):,}")
fwd_cites.to_parquet(DATA_DIR / "forward_cites.parquet", index=False)

# ══════════════════════════════════════════════════════════════════════════
# 3. Primary IPC/WIPO class per patent
# ══════════════════════════════════════════════════════════════════════════
print("\n[3/5] Exporting WIPO/IPC technology classes...")

ipcr = client.query(f"""
    SELECT
      patent_id,
      section,
      ipc_class,
      subclass,
      main_group,
      subgroup,
      sequence,
      CONCAT(section, ipc_class, subclass, '/', main_group) AS ipc_code
    FROM `patents-public-data.patentsview.ipcr`
    WHERE patent_id IN (
      SELECT id FROM `patents-public-data.patentsview.patent`
      WHERE date >= '1976-01-01'
        AND date < '2023-01-01'
    )
    ORDER BY patent_id, sequence
""").to_dataframe()

# Keep first-listed IPC class per patent (primary class)
wipo = ipcr.groupby("patent_id").first().reset_index()
wipo = wipo.drop(columns=["sequence"])
print(f"  Unique patent WIPO records: {len(wipo):,}")
wipo.to_parquet(DATA_DIR / "wipo_class.parquet", index=False)

# ══════════════════════════════════════════════════════════════════════════
# 4. NBER technology categories
# ══════════════════════════════════════════════════════════════════════════
print("\n[4/5] Exporting NBER technology categories...")

nber = client.query(f"""
    SELECT patent_id, category_id, subcategory_id
    FROM `patents-public-data.patentsview.nber`
    WHERE patent_id IN (
      SELECT id FROM `patents-public-data.patentsview.patent`
      WHERE date >= '1976-01-01'
        AND date < '2023-01-01'
    )
""").to_dataframe()

print(f"  NBER records: {len(nber):,}")
nber.to_parquet(DATA_DIR / "nber_cat.parquet", index=False)

# ══════════════════════════════════════════════════════════════════════════
# 5. Patent-inventor links (batched by 5-year windows)
# ══════════════════════════════════════════════════════════════════════════
print("\n[5/5] Exporting patent-inventor links...")

all_inventors = []
for start_year in range(1976, 2023, 5):
    end_year = min(start_year + 5, 2023)
    inv_query = f"""
    SELECT
      pi.patent_id,
      pi.inventor_id,
      pi.location_id
    FROM
      `patents-public-data.patentsview.patent_inventor` pi
    JOIN
      `patents-public-data.patentsview.patent` p ON pi.patent_id = p.id
    WHERE
      p.date >= '{start_year}-01-01'
      AND p.date < '{end_year}-01-01'
      AND REGEXP_CONTAINS(p.id, r'^[0-9]')
    """

    try:
        batch = client.query(inv_query).to_dataframe()
        all_inventors.append(batch)
        print(f"  {start_year}-{end_year}: {len(batch):,} links")
    except Exception as e:
        print(f"  {start_year}-{end_year}: ERROR - {e}")

if all_inventors:
    patent_inventors = pd.concat(all_inventors, ignore_index=True)
    # Add inventor count per patent
    inv_counts = (patent_inventors.groupby("patent_id")
                  .size()
                  .rename("number_of_inventors")
                  .reset_index())
    print(f"\n  Total patent-inventor links: {len(patent_inventors):,}")
    patent_inventors.to_parquet(DATA_DIR / "patent_inventor.parquet", index=False)
    inv_counts.to_parquet(DATA_DIR / "inventor_counts.parquet", index=False)
else:
    print("  WARNING: No inventor data exported!")

# ══════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Export complete!")
print(f"Files saved to: {DATA_DIR}")
for f in sorted(DATA_DIR.glob("*.parquet")):
    size_mb = f.stat().st_size / 1e6
    print(f"  {f.name:30s}: {size_mb:8.1f} MB")
print(f"\nTotal scan: ~4 GB")
print("=" * 60)
