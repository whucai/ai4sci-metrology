# Hot streaks in artistic, scientific, and other careers
Liu, Wang, Aghini & Jones (2018), Nature 559:396-399.

> Structured stub (full text not locally available); reference code + data carry the method.

## Thesis
Across careers in art (auction prices), film (director ratings), and science (citation
impact), individuals experience "hot streaks" — bursty, consecutive periods of
unusually high-impact output — that are statistically non-random (not explained by
the base rate of high-impact works). Hot streaks tend to be localized in time and
are followed (and sometimes preceded) by lower-impact periods.

## Data
Career-level work sequences:
- scientists_c10.txt: 20,040 scientist careers; each line one career; works split by '|';
  each work = (raw_C10, rescaled_C10, year). rescaled_C10 is the per-work impact.
- artists.txt (hammer price, year); directors.txt (IMDB rating, year).

## Method
- For each career, compute the impact sequence (rescaled_C10 by year).
- Define a hot streak as a consecutive run of works with impact above a high threshold
  (e.g., career top-quartile or mean+1SD).
- Compare observed streak lengths / counts to a within-career shuffled null (random
  reordering of works across years) — hot streaks are real only if observed > null.

## Key result
Hot streaks appear in all three domains; the phenomenon is non-random and
career-universal. Most individuals have at least one hot streak; streaks are
brief (often ~2-5 years) and high-impact.

## Claim
Creative careers exhibit hot streaks: bursty, exceptional, non-random runs of high-impact work.
