# Natural language processing to identify the creation and impact of new technologies in patent text
Arts, Hou & Gomez (2020), Research Policy. DOI: 10.1016/j.respol.2020.104144.

> Structured stub (full text not locally available); reference code + data dictionary carry the method.

## Thesis
NLP measures on patent text (new word, new word combination, new n-gram, backward cosine)
identify the creation and impact of new technologies. These text-based novelty measures
predict patent impact (citations, awards) better than conventional patent-class measures.

## Data
USPTO patent claims + titles/abstracts (Zenodo 10.5281/zenodo.3515985): claim_full_till2018.csv,
patent_title_abstract_till_2018.csv. Large — NOT shipped in the sandbox (external on Zenodo).

## Method (reference code in original_code/)
- step_01_concatenate_patents.py: concatenate raw patent files.
- 5 metrics: new_word, new_word_comb, new_bigram, new_trigram, backward_cosine — each in its own folder with numbered steps.
- Validate against patent citations + awards (breakthrough).

## Key result
Text-based novelty measures predict patent impact; backward cosine and new-word-combination perform strongly.

## Claim
NLP on patent text measures technological novelty and predicts impact better than traditional classes.
