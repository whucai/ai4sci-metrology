#!/usr/bin/env python3
"""Fix the R003 generated code: unescape newlines and fix syntax error."""
import re

with open("refine-logs/r003/reproduce_v0_llm.py", "r") as f:
    content = f.read()

# The file has literal \\n (two chars: backslash + n)
# When Python reads it, it becomes \\n as a Python string
content = content.replace("\\n", "\n")

# Fix escaped single quotes: \' -> '
content = content.replace("\\'", "'")

# Now fix the broken line
# The broken text is: "dependencies": "P7', 'type': 'text'}]
# We replace it with: "dependencies": "P7"}
old = """"dependencies": "P7', 'type': 'text'}]"""
new = """"dependencies": "P7"}
]"""
content = content.replace(old, new)

# Also add missing print sections
appendix = '''
# Save results to parquet
results_df = pd.DataFrame(novelty_indicators)
results_df = results_df.rename(columns={
    "cos_novelty": "cosine_similarity",
    "cos_impact": "cosine_similarity_impact"
})
results_df["patent_id"] = df["patent_id"].values[:len(results_df)]
results_df["n_kw"] = keyword_counts
results_df.to_parquet("refine-logs/r003/patent_indicators.parquet", index=False)

print("\\n=== PREPROCESSING ===")
print(f"P1-P10 executed. Patents: {len(df)}, Avg keywords: {np.mean(keyword_counts):.1f}")

print("\\n=== INDICATOR_STATS ===")
for name, s in stats.items():
    print(f"{name}: mean={s['mean']:.4f}, median={s['median']:.4f}, std={s['std']:.4f}, min={s['min']:.4f}, max={s['max']:.4f}, pct_nonzero={s['pct_nonzero']:.2f}")

print("\\n=== COMPONENT_DEPENDENCY_GRAPH ===")
deps = {
    "new_word": ["P1-P10"],
    "new_bigram": ["P1-P10"],
    "new_trigram": ["P1-P10"],
    "new_word_comb": ["P1-P10"],
    "cosine_similarity": ["P1-P10"],
    "new_word_reuse": ["P1-P10", "new_word"],
    "new_bigram_reuse": ["P1-P10", "new_bigram"],
    "new_trigram_reuse": ["P1-P10", "new_trigram"],
    "new_word_comb_reuse": ["P1-P10", "new_word_comb"],
    "cosine_similarity_impact": ["P1-P10", "cosine_similarity"],
}
for ind, dep in deps.items():
    print(f"{ind} <- {dep}")

print("\\n=== RESULTS ===")
print(f"Total patents processed: {len(df)}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"Avg keywords per patent: {np.mean(keyword_counts):.1f}")
print(f"Median keywords per patent: {np.median(keyword_counts):.1f}")
'''

content += appendix

with open("refine-logs/r003/reproduce_v0_fixed.py", "w") as f:
    f.write(content)

# Verify syntax
try:
    compile(content, "reproduce_v0_fixed.py", "exec")
    print(f"Syntax OK! {len(content.splitlines())} lines")
except SyntaxError as e:
    print(f"Syntax error at line {e.lineno}: {e.msg}")
    lines = content.splitlines()
    for i in range(max(0, e.lineno - 3), min(len(lines), e.lineno + 2)):
        marker = ">>>" if i == e.lineno - 1 else "   "
        print(f"{marker} {i+1}: {lines[i][:200]}")
