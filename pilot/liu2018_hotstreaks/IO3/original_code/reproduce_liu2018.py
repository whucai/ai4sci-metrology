#!/usr/bin/env python3
"""Reference reproduction of Liu, Wang, Aghini & Jones (2018) — 'Hot streaks in
artistic, scientific, and other careers', Nature 559:396-399.

Detects hot streaks in scientist careers from scientists_sample.txt: consecutive
runs of high-impact (top-quartile rescaled_C10) works, and compares the observed
mean streak length to a within-career shuffled null.
"""
import random
from statistics import mean

random.seed(42)

def load_careers(path):
    careers = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        works = []
        for w in line.split("|"):
            parts = w.split(",")
            if len(parts) >= 2:
                try:
                    impact = float(parts[1])  # rescaled_C10
                    works.append(impact)
                except ValueError:
                    continue
        if len(works) >= 5:
            careers.append(works)
    return careers

def longest_streak(impacts, q_thr):
    above = [1 if x >= q_thr else 0 for x in impacts]
    best = cur = 0
    for a in above:
        cur = cur + 1 if a else 0
        best = max(best, cur)
    return best

careers = load_careers("/workspace/raw_data/scientists_sample.txt")
observed = []
null = []
for c in careers:
    # career-specific top-quartile threshold
    s = sorted(c)
    q_thr = s[int(0.75 * len(s))] if len(s) > 3 else s[-1]
    observed.append(longest_streak(c, q_thr))
    sh = c[:]
    random.shuffle(sh)
    null.append(longest_streak(sh, q_thr))

obs_mean = mean(observed)
null_mean = mean(null)
frac_with_streak = sum(1 for x in observed if x >= 2) / len(observed)

print(f"RESULT n_careers = {len(careers)}")
print(f"RESULT observed_mean_longest_streak = {round(obs_mean,3)}")
print(f"RESULT null_mean_longest_streak = {round(null_mean,3)}")
print(f"RESULT observed_minus_null = {round(obs_mean - null_mean,3)}")
print(f"RESULT frac_careers_with_streak_ge2 = {round(frac_with_streak,3)}")
print(f"RESULT direction = {'hot streaks non-random (observed > null)' if obs_mean > null_mean else 'no streak effect'}")
print("PAPER_REPORTED claim = careers exhibit non-random hot streaks")
print("PAPER_REPORTED conclusion = hot streaks are a universal, bursty, high-impact phenomenon")
