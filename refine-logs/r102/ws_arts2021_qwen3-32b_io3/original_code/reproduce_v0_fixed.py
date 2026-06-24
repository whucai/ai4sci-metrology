import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from itertools import combinations
from scipy.spatial.distance import cosine

# Download NLTK resources if not present
nltk.download('stopwords', quiet=True)

# ---------- Data loading and preparation ----------
DATA_PATH = "/mnt/mydisk/PycharmProjects/ai4sci-metrology/data/patentsview/patents_sample_50k.parquet"
df = pd.read_parquet(DATA_PATH)

# Select first 500 after sorting by filing date (earliest first)
df = df.sort_values('date').head(500).reset_index(drop=True)

# Use abstract + claim_text as the text source; handle missing values
df['text'] = (df['patent_abstract'].fillna('') + ' ' + df['claim_text'].fillna('')).str.strip()

# ---------- Preprocessing pipeline (P1 - P10) ----------

eng_stopwords = set(stopwords.words('english'))
custom_stopwords = set([
    "said","wherein","thereof","thereby","invention","disclosure","embodiment",
    "claim","claims","claimed","describe","described","disclose","disclosed",
    "include","includes","including","comprise","comprises","comprising",
    "contain","contains","containing","patent","patents","apparatus",
    "method","methods","system","systems","device","devices","fig","figs",
    "figure","figures","prior","art","present","example","examples",
    "various","certain","another","other","may","also","can","one","two",
    "first","second","third","based","used","using","provide","provides",
    "provided","providing","configure","configured","set","make","made",
    "way","new","many","much","part","parts","least","well","without",
    "within","able","accordingly","moreover","furthermore","however",
    "therefore","consequently","subsequently","preferably","respectively"
])
all_stopwords = eng_stopwords.union(custom_stopwords)

token_pattern = re.compile(r'[a-z0-9][a-z0-9-]*[a-z0-9]+|[a-z0-9]')

# Step 1-7: tokenise, filter, remove stopwords (before rare word removal)
tokens_per_patent = []   # list of lists of raw tokens
for text in df['text']:
    # P1: concatenation already done
    # P2: lowercase
    text_lower = text.lower()
    # P3: tokenisation
    raw_tokens = token_pattern.findall(text_lower)
    # P4: pure digit removal
    raw_tokens = [t for t in raw_tokens if not t.isdigit()]
    # P5: single-char removal
    raw_tokens = [t for t in raw_tokens if len(t) > 1]
    # P6 & P7: stopword removal (English + custom)
    raw_tokens = [t for t in raw_tokens if t not in all_stopwords]
    tokens_per_patent.append(raw_tokens)

# P8: rare word removal (appear in exactly one patent)
from collections import Counter
doc_freq = Counter()
for tokens in tokens_per_patent:
    unique_tokens = set(tokens)
    doc_freq.update(unique_tokens)
rare_words = {w for w, c in doc_freq.items() if c == 1}

filtered_tokens = []
for tokens in tokens_per_patent:
    filtered_tokens.append([t for t in tokens if t not in rare_words])

# P9: stemming (Snowball)
stemmer = SnowballStemmer('english')
stemmed_tokens = []
for tokens in filtered_tokens:
    stemmed_seq = [stemmer.stem(t) for t in tokens]
    stemmed_tokens.append(stemmed_seq)

# P10: deduplicate (unique stems per patent, keeping only unique keywords)
unique_stems_per_patent = []
for seq in stemmed_tokens:
    # preserve order of first occurrence
    seen = set()
    unique_stems = [s for s in seq if not (s in seen or seen.add(s))]
    unique_stems_per_patent.append(unique_stems)

# ---------- Build vocabulary for cosine similarity (top 5000 stems) ----------
from collections import Counter
term_freq = Counter()
for seq in stemmed_tokens:
    term_freq.update(seq)

top_terms = [term for term, _ in term_freq.most_common(5000)]
vocab_index = {term: i for i, term in enumerate(top_terms)}

# Binary TF vectors for each patent
binary_vectors = []
for seq in stemmed_tokens:
    vec = np.zeros(len(vocab_index), dtype=int)
    for term in set(seq) & set(vocab_index):  # only terms in vocab
        vec[vocab_index[term]] = 1
    binary_vectors.append(vec)

# ---------- Compute novelty indicators (I1 - I5) in chronological order ----------
# For I2-I4 we need bigrams, trigrams, word combinations from each patent
# Prepare per-patent sets for later reuse
patent_data = []
for idx, row in df.iterrows():
    seq = stemmed_tokens[idx]
    unique = set(unique_stems_per_patent[idx])
    # bigrams (consecutive pairs in original order)
    bigrams = set()
    if len(seq) >= 2:
        for i in range(len(seq)-1):
            bigrams.add(seq[i] + '|||' + seq[i+1])
    # trigrams
    trigrams = set()
    if len(seq) >= 3:
        for i in range(len(seq)-2):
            trigrams.add(seq[i] + '|||' + seq[i+1] + '|||' + seq[i+2])
    # word combinations (unordered pairs from unique stems, limit 5000)
    unique_list = list(unique)
    combo_limit = min(5000, len(unique_list)*(len(unique_list)-1)//2)
    # generate combinations; use first 5000 sorted pairs to be deterministic
    # combinations returns tuples in lexicographic order of the list
    # we can iterate over combinations(unique_list, 2) and take first 5000
    combo_gen = combinations(unique_list, 2)
    combos = set()
    for i, pair in enumerate(combo_gen):
        if i >= 5000:
            break
        # order-independent: sort the two stems
        sorted_pair = sorted(pair)
        combos.add(sorted_pair[0] + '|||' + sorted_pair[1])
    patent_data.append({
        'unique': unique,
        'bigrams': bigrams,
        'trigrams': trigrams,
        'combos': combos,
        'binary_vec': binary_vectors[idx]
    })

# Global sets for novelty tracking
global_keywords = set()
global_bigrams = set()
global_trigrams = set()
global_combos = set()

novelty_indicators = []

for i, pdata in enumerate(patent_data):
    # I1: new keyword
    new_kw = pdata['unique'] - global_keywords
    global_keywords.update(pdata['unique'])
    n_new_word = len(new_kw)

    # I2: new bigram
    new_bg = pdata['bigrams'] - global_bigrams
    global_bigrams.update(pdata['bigrams'])
    n_new_bigram = len(new_bg)

    # I3: new trigram
    new_tg = pdata['trigrams'] - global_trigrams
    global_trigrams.update(pdata['trigrams'])
    n_new_trigram = len(new_tg)

    # I4: new word combination
    new_cb = pdata['combos'] - global_combos
    global_combos.update(pdata['combos'])
    n_new_combo = len(new_cb)

    # I5: cosine similarity novelty
    if i == 0:
        backward_cosine = 0.0
        cos_novelty = 1.0
    else:
        prior_vecs = [patent_data[j]['binary_vec'] for j in range(i)]
        # compute cosines with all prior
        cosines = []
        for pvec in prior_vecs:
            v1 = pdata['binary_vec']
            v2 = pvec
            # cosine similarity from scipy.spatial.distance.cosine
            # cosine distance = 1 - similarity, so similarity = 1 - distance
            sim = 1.0 - cosine(v1, v2) if np.any(v1) and np.any(v2) else 0.0
            cosines.append(sim)
        backward_cosine = np.mean(cosines)
        cos_novelty = 1.0 - backward_cosine

    novelty_indicators.append({
        'new_word': n_new_word,
        'new_bigram': n_new_bigram,
        'new_trigram': n_new_trigram,
        'new_word_comb': n_new_combo,
        'cos_novelty': cos_novelty,
        'backward_cosine': backward_cosine,
        'new_keywords_set': new_kw,
        'new_bigrams_set': new_bg,
        'new_trigrams_set': new_tg,
        'new_combos_set': new_cb
    })

# ---------- Compute impact/reuse indicators (I6 - I10) ----------
total_patents = len(patent_data)
for i in range(total_patents):
    future_keywords = 0
    future_bigrams = 0
    future_trigrams = 0
    future_combos = 0

    new_kw_set = novelty_indicators[i]['new_keywords_set']
    new_bg_set = novelty_indicators[i]['new_bigrams_set']
    new_tg_set = novelty_indicators[i]['new_trigrams_set']
    new_cb_set = novelty_indicators[i]['new_combos_set']

    # Count occurrences in future patents (j > i)
    for j in range(i+1, total_patents):
        pdata_j = patent_data[j]
        # keyword presence
        if new_kw_set:
            future_keywords += sum(1 for k in new_kw_set if k in pdata_j['unique'])
        # bigram presence
        if new_bg_set:
            future_bigrams += sum(1 for bg in new_bg_set if bg in pdata_j['bigrams'])
        # trigram presence
        if new_tg_set:
            future_trigrams += sum(1 for tg in new_tg_set if tg in pdata_j['trigrams'])
        # combo presence
        if new_cb_set:
            future_combos += sum(1 for cb in new_cb_set if cb in pdata_j['combos'])

    # I6 - I9
    reuse_word = sum(1 + future_keywords for _ in new_kw_set) if new_kw_set else 0
    reuse_bigram = sum(1 + future_bigrams for _ in new_bg_set) if new_bg_set else 0
    reuse_trigram = sum(1 + future_trigrams for _ in new_tg_set) if new_tg_set else 0
    reuse_comb = sum(1 + future_combos for _ in new_cb_set) if new_cb_set else 0

    novelty_indicators[i]['new_word_reuse'] = reuse_word
    novelty_indicators[i]['new_bigram_reuse'] = reuse_bigram
    novelty_indicators[i]['new_trigram_reuse'] = reuse_trigram
    novelty_indicators[i]['new_word_comb_reuse'] = reuse_comb

    # I10: cosine similarity impact
    backward = novelty_indicators[i]['backward_cosine']
    if i < total_patents - 1:
        future_vecs = [patent_data[j]['binary_vec'] for j in range(i+1, total_patents)]
        cosines_fwd = []
        v1 = patent_data[i]['binary_vec']
        for v2 in future_vecs:
            sim = 1.0 - cosine(v1, v2) if np.any(v1) and np.any(v2) else 0.0
            cosines_fwd.append(sim)
        forward_cosine = np.mean(cosines_fwd)
    else:
        forward_cosine = 0.0

    if backward == 0.0:
        impact = 0.0
    else:
        impact = forward_cosine / backward

    novelty_indicators[i]['cos_impact'] = impact

# ---------- Aggregate indicator statistics ----------
indicator_names = ['new_word', 'new_bigram', 'new_trigram', 'new_word_comb',
                   'cos_novelty', 'new_word_reuse', 'new_bigram_reuse',
                   'new_trigram_reuse', 'new_word_comb_reuse', 'cos_impact']
stats = {}
for name in indicator_names:
    values = [ni[name] for ni in novelty_indicators]
    stats[name] = {
        'mean': np.mean(values),
        'median': np.median(values),
        'std': np.std(values),
        'min': np.min(values),
        'max': np.max(values),
        'pct_nonzero': 100 * np.mean(np.array(values) > 0)
    }

# Number of keywords per patent (unique stems after preprocessing)
keyword_counts = [len(pdata['unique']) for pdata in patent_data]

# ---------- Output sections ----------
print("=== COMPONENT_DECOMPOSITION ===")
components = [
    {"name": "P1_TEXT_CONCAT", "category": "preprocessing",
     "formula": "text = patent_abstract + ' ' + claim_text",
     "dependencies": "raw data"},
    {"name": "P2_LOWERCASE", "category": "preprocessing",
     "formula": "text.lower()",
     "dependencies": "P1"},
    {"name": "P3_TOKENIZATION", "category": "preprocessing",
     "formula": "regex [a-z0-9][a-z0-9-]*[a-z0-9]+|[a-z0-9] findall",
     "dependencies": "P2"},
    {"name": "P4_NUMBER_REMOVAL", "category": "preprocessing",
     "formula": "remove tokens with token.isdigit()==True",
     "dependencies": "P3"},
    {"name": "P5_SINGLE_CHAR_REMOVAL", "category": "preprocessing",
     "formula": "keep tokens len > 1",
     "dependencies": "P4"},
    {"name": "P6_NLTK_STOPWORDS", "category": "preprocessing",
     "formula": "remove NLTK English stopwords",
     "dependencies": "P5"},
    {"name": "P7_CUSTOM_STOPWORDS", "category": "preprocessing",
     "formula": "remove predefined patent boilerplate list",
     "dependencies": "P6"},
    {"name": "P8_RARE_WORD_REMOVAL", "category": "preprocessing",
     "formula": "remove words with DF=1 (across all patents)",
     "dependencies": "P7"}
]
# Save results to parquet
results_df = pd.DataFrame(novelty_indicators)
results_df = results_df.rename(columns={
    "cos_novelty": "cosine_similarity",
    "cos_impact": "cosine_similarity_impact"
})
results_df["patent_id"] = df["patent_id"].values[:len(results_df)]
results_df["n_kw"] = keyword_counts
results_df.to_parquet("refine-logs/r003/patent_indicators.parquet", index=False)

print("\n=== PREPROCESSING ===")
print(f"P1-P10 executed. Patents: {len(df)}, Avg keywords: {np.mean(keyword_counts):.1f}")

print("\n=== INDICATOR_STATS ===")
for name, s in stats.items():
    print(f"{name}: mean={s['mean']:.4f}, median={s['median']:.4f}, std={s['std']:.4f}, min={s['min']:.4f}, max={s['max']:.4f}, pct_nonzero={s['pct_nonzero']:.2f}")

print("\n=== COMPONENT_DEPENDENCY_GRAPH ===")
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

print("\n=== RESULTS ===")
print(f"Total patents processed: {len(df)}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"Avg keywords per patent: {np.mean(keyword_counts):.1f}")
print(f"Median keywords per patent: {np.median(keyword_counts):.1f}")
