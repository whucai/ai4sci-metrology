# Patch 002 — bikard2013 IO2 legacy parquet removal

**Date**: 2026-06-30
**Paper**: bikard2013
**IO**: 2
**Frozen manifest says**: data_provided = False (MIT faculty data private, no public substitute; DATA-SUB boundary case).
**Issue**: A legacy `sciscinet_sample.parquet` from the pilot (R100-R103) remained in `pilot/bikard2013/IO2/raw_data/`, contradicting the frozen data_provided=False flag.
**Patch**: Removed the legacy parquet so bikard2013 IO2 runs as a true boundary (no raw_data), consistent with the frozen manifest and the R120 design (bikard is the DATA-SUB boundary case alongside maddi2024/vasarhelyi2023/zheng2025_male).
**Effect on gold ceiling**: None. bikard2013's gold ceiling (Sample/Claim = 0.5, DATA-SUB) is unchanged; this is a materials-cleanup to match the frozen IO definition.
**Runs affected**: bikard2013 × {qwen3-32b, deepseek-v4-pro} × IO2 now run as boundary (no raw_data).
