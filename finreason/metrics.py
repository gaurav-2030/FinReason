"""Statistics: bootstrap confidence intervals, McNemar's test and Holm correction."""
import numpy as np
from scipy.stats import binomtest

from .config import SEED


def bootstrap_ci(flags, n_resamples=2000, alpha=0.05, seed=SEED):
    """95% percentile-bootstrap confidence interval for the mean of 0/1 correctness flags."""
    flags = np.asarray(flags, dtype=float)
    if len(flags) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = rng.choice(flags, size=(n_resamples, len(flags)), replace=True).mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def mcnemar(flags_a, flags_b):
    """Exact McNemar test for two systems evaluated on the same questions.
    Only discordant pairs matter: b = A right & B wrong, c = A wrong & B right.
    Under H0 (equal accuracy) b ~ Binomial(b + c, 0.5). Returns (b, c, two-sided p-value)."""
    a, b_ = np.asarray(flags_a, dtype=bool), np.asarray(flags_b, dtype=bool)
    b = int(np.sum(a & ~b_))
    c = int(np.sum(~a & b_))
    if b + c == 0:
        return b, c, 1.0
    return b, c, float(binomtest(b, b + c, 0.5).pvalue)


def holm(p_values):
    """Holm-Bonferroni adjusted p-values (controls the chance of any false positive)."""
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(p)
    adjusted = np.empty_like(p)
    running_max = 0.0
    for rank, idx in enumerate(order):
        running_max = max(running_max, (len(p) - rank) * p[idx])
        adjusted[idx] = min(1.0, running_max)
    return adjusted.tolist()
