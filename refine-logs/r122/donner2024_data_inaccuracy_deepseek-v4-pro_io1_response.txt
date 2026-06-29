```python
import numpy as np
from math import log, exp, lgamma

# Set seeds for reproducibility
np.random.seed(42)

# =============================================================================
# 1. Create synthetic data for the citation error empirical sample
#    (matches the paper's Table 2 and summary statistics)
# =============================================================================
print("=" * 60)
print("SYNTHETIC CITATION ERROR DATA")
print("=" * 60)

n = 372
target_sum_ci = 6120   # total WoS citations
target_sum_oi = 255    # total missed citations

# Frequencies of missed citations from Table 2
oi_freq = {
    0: 263,
    1: 67,
    2: 20,
    3: 5,
    4: 5,
    5: 2,
    6: 3,
    8: 1,
    9: 4,
    15: 1,
    26: 1
}

# Build oi vector exactly as Table 2
oi_list = []
for val, freq in oi_freq.items():
    oi_list.extend([val] * freq)
oi_list = np.array(oi_list)
np.random.shuffle(oi_list)  # will sort later

# Generate observed citation counts ci such that sum ~ 6120, avg ~ 16.45
# Use a lognormal and scale/round to approximate.
mu_ci = 2.5
sigma_ci = 1.2
ci_raw = np.random.lognormal(mean=mu_ci, sigma=sigma_ci, size=n)
ci_raw = np.round(ci_raw).astype(int)
ci_raw = np.maximum(0, ci_raw)  # ensure non-negative

# Scale to match target sum
current_sum = ci_raw.sum()
ci = np.floor(ci_raw * target_sum_ci / current_sum).astype(int)
# Adjust to hit exact sum
diff = target_sum_ci - ci.sum()
if diff != 0:
    # add/subtract diff to randomly chosen elements
    idx = np.random.choice(n, size=abs(diff), replace=False)
    if diff > 0:
        ci[idx] += 1
    else:
        ci[idx] = np.maximum(0, ci[idx] - 1)

# Sort ci and assign sorted oi to get positive correlation (aim ~0.31)
sorted_idx = np.argsort(ci)
ci_sorted = ci[sorted_idx]
oi_sorted = np.sort(oi_list)   # ascending
oi = np.zeros(n, dtype=int)
oi[sorted_idx] = oi_sorted

corr = np.corrcoef(ci, oi)[0, 1]
print(f"Generated {n} records")
print(f"Sum of ci: {ci.sum()} (target {target_sum_ci})")
print(f"Sum of oi: {oi.sum()} (target {target_sum_oi})")
print(f"Average ci : {ci.mean():.2f}  (paper: 16.4)")
print(f"Average oi : {oi.mean():.2f}  (paper: 0.685)")
print(f"Correlation ci vs oi: {corr:.3f}  (paper: 0.31)")

# =============================================================================
# 2. Bayesian negative binomial regression for oi ~ log(ci+1)
#    using Metropolis-Hastings MCMC
# =============================================================================
print("\n" + "=" * 60)
print("BAYESIAN NEGATIVE BINOMIAL REGRESSION (MCMC)")
print("=" * 60)

# Helper functions
def nbinom_logpmf(k, mu, phi):
    """Log PMF of negative binomial: mean mu, dispersion phi."""
    if phi <= 0 or mu <= 0:
        return -np.inf
    return (lgamma(k + phi) - lgamma(phi) - lgamma(k + 1) +
            phi * log(phi / (phi + mu)) + k * log(mu / (phi + mu)))

def log_likelihood(b0, b1, phi, ci, oi):
    mu = np.exp(b0 + b1 * np.log(ci + 1))
    return np.sum(nbinom_logpmf(oi, mu, phi))

def log_prior(b0, b1, log_phi):
    # b0 ~ N(0, 0.8^2)
    lp_b0 = -0.5 * (b0 / 0.8)**2
    # b1 ~ N(0, 1^2)
    lp_b1 = -0.5 * b1**2
    # log_phi ~ N(0, 2^2)
    lp_log_phi = -0.5 * (log_phi / 2)**2
    return lp_b0 + lp_b1 + lp_log_phi

def log_posterior(b0, b1, log_phi, ci, oi):
    phi = exp(log_phi)
    return log_prior(b0, b1, log_phi) + log_likelihood(b0, b1, phi, ci, oi)

# MCMC settings
n_iter = 5000
burnin = 1000
thin = 2
n_samples = (n_iter - burnin) // thin

# Initial values
b0_cur, b1_cur, log_phi_cur = 0.0, 0.0, 0.0
logpost_cur = log_posterior(b0_cur, b1_cur, log_phi_cur, ci, oi)
# Proposal standard deviations (tuned manually)
sd_b0, sd_b1, sd_log_phi = 0.3, 0.3, 0.5

chain = np.zeros((n_samples, 3))
sample_count = 0
accept = 0

for i in range(n_iter):
    # propose new parameters
    b0_prop = b0_cur + np.random.normal(0, sd_b0)
    b1_prop = b1_cur + np.random.normal(0, sd_b1)
    log_phi_prop = log_phi_cur + np.random.normal(0, sd_log_phi)
    logpost_prop = log_posterior(b0_prop, b1_prop, log_phi_prop, ci, oi)
    # Metropolis acceptance
    if logpost_prop > logpost_cur or np.random.rand() < exp(logpost_prop - logpost_cur):
        b0_cur, b1_cur, log_phi_cur = b0_prop, b1_prop, log_phi_prop
        logpost_cur = logpost_prop
        accept += 1
    # store after burnin and thinning
    if i >= burnin and (i - burnin) % thin == 0:
        chain[sample_count, :] = [b0_cur, b1_cur, exp(log_phi_cur)]
        sample_count += 1

print(f"MCMC acceptance rate: {accept / n_iter:.2f}")
print(f"Posterior samples saved: {sample_count}")

# Summarize posterior
medians = np.median(chain, axis=0)
low = np.percentile(chain, 2.5, axis=0)
high = np.percentile(chain, 97.5, axis=0)
print("Posterior summaries (median and 95% CI):")
print(f"  b0  : {medians[0]:.3f}  [{low[0]:.3f}, {high[0]:.3f}]")
print(f"  b1  : {medians[1]:.3f}  [{low[1]:.3f}, {high[1]:.3f}]")
print(f"  phi : {medians[2]:.3f}  [{low[2]:.3f}, {high[2]:.3f}]")

# =============================================================================
# 3. Document type error model (confusion matrix)
# =============================================================================
print("\n" + "=" * 60)
print("DOCUMENT TYPE ERROR MODEL (PLACEHOLDER)")
print("=" * 60)
# Global distribution of true document types (article, letter, review, other)
prior_dt = np.array([0.68, 0.03, 0.04, 0.25])
dt_names = ['Article', 'Letter', 'Review', 'Other']

# Forward misclassification matrix P(observed | true)
# rows: true type, columns: observed type
forward = np.array([
    [0.95, 0.01, 0.02, 0.02],   # true article
    [0.05, 0.80, 0.05, 0.10],   # true letter
    [0.05, 0.00, 0.90, 0.05],   # true review
    [0.05, 0.01, 0.02, 0.92]    # true other
])
# Normalise rows
forward = forward / forward.sum(axis=1, keepdims=True)

# Compute inverse matrix P(true | observed)
joint = forward * prior_dt[:, np.newaxis]
marginal_obs = joint.sum(axis=0)
inverse = (joint / marginal_obs).T  # rows: observed, columns: true

print("Global true document type distribution:", prior_dt)
print("Inverse matrix P(true|observed) used for prediction:")
print("Observed -> True")
print(f"{'':12} Article Letter Review Other")
for i, name in enumerate(dt_names):
    row_str = f"{name:12} " + " ".join(f"{inverse[i,j]:.3f}" for j in range(4))
    print(row_str)

# =============================================================================
# 4. Simulation Exercise 1 – micro-level predictions for three publications
# =============================================================================
print("\n" + "=" * 60)
print("EXERCISE 1 – PREDICTED ERROR-FREE VALUES FOR THREE PUBLICATIONS")
print("=" * 60)

# Observed data
pubs_ex1 = [
    {'obs_dt': 0, 'obs_cit': 5, 'name': 'P1'},   # Article, 5 citations
    {'obs_dt': 2, 'obs_cit': 10, 'name': 'P2'},  # Review, 10 citations
    {'obs_dt': 1, 'obs_cit': 0, 'name': 'P3'}    # Letter, 0 citations
]

n_draws = 2000
np.random.seed(123)  # separate seed for prediction

# Predict document types
dt_predictions = {pub['name']: np.zeros(4, dtype=int) for pub in pubs_ex1}
for pub in pubs_ex1:
    obs_dt = pub['obs_dt']
    pred_dt = np.random.choice(4, size=n_draws, p=inverse[obs_dt, :])
    for j in range(4):
        dt_predictions[pub['name']][j] = np.sum(pred_dt == j)

# Predict citation counts
# Randomly select parameter samples from the posterior chain
param_idx = np.random.choice(len(chain), size=n_draws, replace=True)
cit_predictions = {pub['name']: {} for pub in pubs_ex1}
for pub in pubs_ex1:
    ci = pub['obs_cit']
    counts = {}
    for idx in param_idx:
        b0, b1, phi = chain[idx]
        mu = exp(b0 + b1 * log(ci + 1))
        o_pred = np.random.negative_binomial(phi, phi/(phi+mu))
        c_pred = ci + o_pred
        counts[c_pred] = counts.get(c_pred, 0) + 1
    cit_predictions