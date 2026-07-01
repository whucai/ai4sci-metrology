"""
Reproduction script for: Maddi, A., & Miotti, L. (2024). On the peer review reports: does size matter? Scientometrics.
Code origin: Written from scratch (no reference code provided).
Data status: DATA BLOCKED. Raw Publons/WoS matched dataset is unavailable per documentation.
This script documents the required data, outlines the analytical pipeline, and reports paper values as PAPER_REPORTED.
"""

def main():
    # 1. Document missing data and pipeline requirements
    print("=== REPRODUCTION STATUS ===")
    print("RESULT reproduction_status = DATA_BLOCKED")
    print("RESULT data_needed = ['Publons reviewer report word counts', 'WoS citation counts', 'Journal impact factors', 'Funding info', 'Country info', 'Discipline codes', 'Publication years', 'Open access status']")
    
    # 2. Report paper values explicitly as PAPER_REPORTED
    print("\n=== PAPER REPORTED VALUES ===")
    print("PAPER_REPORTED N_initial_matched = 61197")
    print("PAPER_REPORTED N_after_year_filter = 57694")
    print("PAPER_REPORTED N_after_outlier_removal = 57482")
    print("PAPER_REPORTED outlier_threshold_words = 13671")
    print("PAPER_REPORTED N_excluded_influential = 30")
    print("PAPER_REPORTED DV_transform = log(1 + citations)")
    print("PAPER_REPORTED IV_discretization_method = Fisher")
    print("PAPER_REPORTED IV_classes = ['<232', '232-535', '536-946', '947-1612', '1613-2891']")
    print("PAPER_REPORTED significant_threshold_words = 947")
    print("PAPER_REPORTED significant_intervals = ['[947, 1612]', '[1613, 2891]']")
    print("PAPER_REPORTED estimator = GLM_robust_standard_errors")
    print("PAPER_REPORTED adjustment_method = Raking_Ratio")
    
    # 3. Outline the analytical pipeline (documented stub)
    print("\n=== ANALYTICAL PIPELINE (STUB) ===")
    pipeline_steps = [
        "1. Load Publons data (UT, word_count) and WoS data (citations, IF, OA, funders, countries, discipline, year).",
        "2. Merge on UT. Keep 1 random report per publication if multiple exist.",
        "3. Filter: year >= 2009, citable documents, complete metadata. -> N=57,694",
        "4. Outlier removal: IQR * 5 on word_count. Max allowed = 13,671. Remove 212 obs. -> N=57,482",
        "5. Raking Ratio adjustment: Weight sample to match WoS population margins (year, OA, funders, countries, discipline, IF class).",
        "6. Discretize word_count using Fisher method into 5 classes.",
        "7. Fit GLM: DV = log(1+citations), IV = discretized word_count, Controls = IF, OA, log(funders), log(countries), discipline, year.",
        "8. Diagnostics: VIF < 5, Cook's D < 0.02, Hat < 0.01. Remove 30 influential obs.",
        "9. Refit with robust standard errors (Breusch-Pagan test indicated heteroscedasticity).",
        "10. Extract coefficients for word_count classes. Check significance."
    ]
    for step in pipeline_steps:
        print(f"  {step}")
        
    # 4. Final conclusion/direction
    print("\n=== CONCLUSION / DIRECTION ===")
    print("RESULT conclusion = Reproduction is data-blocked due to unavailability of the original Publons/WoS matched dataset. The paper reports a statistically significant positive association between reviewer report length (>=947 words) and citation impact, after controlling for journal impact, OA status, funding, collaboration, discipline, and year, using a raking-adjusted GLM with robust standard errors.")
    print("RESULT direction = To fully reproduce, obtain the matched Publons-WoS dataset (N=57,482) and implement the raking ratio weighting, Fisher discretization, and robust GLM pipeline outlined above.")

if __name__ == "__main__":
    main()
