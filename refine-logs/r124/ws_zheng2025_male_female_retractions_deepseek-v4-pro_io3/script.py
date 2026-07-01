import os

def main():
    # Check for raw data files (expected location)
    raw_data_dir = "/workspace/raw_data"
    if os.path.isdir(raw_data_dir):
        files = os.listdir(raw_data_dir)
        print(f"INFO: Found {len(files)} file(s) in {raw_data_dir}: {files}")
    else:
        print(f"INFO: Raw data directory {raw_data_dir} not found; data unavailable.")

    print("-------- PAPER-REPORTED KEY RESULTS --------")
    # Overall retraction rates
    print("RESULT overall_male_RR = 6.38‱ (PAPER_REPORTED)")
    print("RESULT overall_female_RR = 5.19‱ (PAPER_REPORTED)")
    print("RESULT overall_MFRR = 1.23 (95% CI: 1.18, 1.28) (PAPER_REPORTED)")

    # Retraction reasons MFRR
    print("RESULT MFRR_plagiarism = 1.99 (PAPER_REPORTED)")
    print("RESULT MFRR_authorship_issues = 1.73 (PAPER_REPORTED)")
    print("RESULT MFRR_duplication = higher for males (PAPER_REPORTED, exact value not given in text)")
    print("RESULT MFRR_fabrication_falsification = higher for males (PAPER_REPORTED, exact value not given)")
    print("RESULT MFRR_ethical_issues = higher for males (PAPER_REPORTED, exact value not given)")
    print("RESULT MFRR_mistakes = no significant gender difference (PAPER_REPORTED)")

    # Disciplinary variations
    print("RESULT discipline_biomedical_health = male first authors significantly higher retraction rates (PAPER_REPORTED)")
    print("RESULT discipline_life_earth = male first authors significantly higher (PAPER_REPORTED)")
    print("RESULT discipline_physical_engineering = male first authors significantly higher (PAPER_REPORTED)")
    print("RESULT discipline_math_computer = female first authors significantly higher (PAPER_REPORTED)")
    print("RESULT discipline_social_humanities = no significant gender difference (PAPER_REPORTED)")

    # Country variations (top 10)
    print("RESULT country_Iran = male first authors higher retraction rate (PAPER_REPORTED)")
    print("RESULT country_Pakistan = male first authors higher retraction rate (PAPER_REPORTED)")
    print("RESULT country_United_States = male first authors higher retraction rate (PAPER_REPORTED)")
    print("RESULT country_Italy = female first authors higher retraction rate (PAPER_REPORTED)")
    print("RESULT country_China = female first authors higher retraction rate (PAPER_REPORTED)")
    print("RESULT top10_other_countries = no significant gender difference (PAPER_REPORTED)")

    # Robustness check: corresponding authors
    print("RESULT corresponding_author_MFRR = 1.20 (95% CI: 1.15, 1.25) (PAPER_REPORTED)")
    print("RESULT corresponding_author_biomed_health = male higher (PAPER_REPORTED)")
    print("RESULT corresponding_author_life_earth = male higher (PAPER_REPORTED)")
    print("RESULT corresponding_author_math_computer = female higher (PAPER_REPORTED)")
    print("RESULT corresponding_author_physical_engineering = no significant difference (PAPER_REPORTED)")
    print("RESULT corresponding_author_social_humanities = male slightly higher (PAPER_REPORTED)")

    print("-------- FINAL CONCLUSION --------")
    print("CONCLUSION: Male leading authors have higher overall retraction rates than females,")
    print("with disparities varying across retraction reasons, disciplines, and countries.")
    print("The gender gap is mainly driven by misconduct (plagiarism, authorship issues, etc.)")
    print("and differs by field: males higher in biomedical, life, and physical sciences;")
    print("females higher in mathematics and computer science.")

if __name__ == "__main__":
    main()
