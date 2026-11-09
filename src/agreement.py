"""Agreement metrics between two raters (e.g. human vs. autograder).

Cohen's kappa = (observed agreement - chance agreement) / (1 - chance agreement)
  1.0 = perfect agreement, 0 = no better than chance, < 0 = worse than chance.
Weighted kappa (quadratic) is used for ordered scales like 1-5 stars:
  being off by 1 counts as a small disagreement, off by 4 as a big one.
"""
from collections import Counter


def percent_agreement(a, b):
    return sum(x == y for x, y in zip(a, b)) / len(a)


def cohen_kappa(a, b):
    """Unweighted Cohen's kappa for categorical labels. Returns None if undefined
    (both raters used a single identical label for every item - no variation to measure)."""
    n = len(a)
    po = percent_agreement(a, b)
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if pe == 1:
        return None
    return (po - pe) / (1 - pe)


def weighted_kappa(a, b, categories=(1, 2, 3, 4, 5)):
    """Quadratic-weighted Cohen's kappa for ordered scores."""
    k = len(categories)
    idx = {c: i for i, c in enumerate(categories)}
    n = len(a)
    obs = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[idx[x]][idx[y]] += 1
    ra = [sum(obs[i]) for i in range(k)]
    rb = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    w = lambda i, j: ((i - j) ** 2) / ((k - 1) ** 2)
    num = sum(w(i, j) * obs[i][j] for i in range(k) for j in range(k))
    den = sum(w(i, j) * ra[i] * rb[j] / n for i in range(k) for j in range(k))
    if den == 0:
        return None
    return 1 - num / den


def within_one(a, b):
    """Share of items where two 1-5 scores differ by at most 1 point."""
    return sum(abs(x - y) <= 1 for x, y in zip(a, b)) / len(a)


def interpret(k):
    """Landis & Koch (1977) labels, a common rule of thumb."""
    if k is None:
        return "n/a (no variation)"
    for limit, label in [(0, "poor"), (0.2, "slight"), (0.4, "fair"), (0.6, "moderate"), (0.8, "substantial")]:
        if k <= limit:
            return label
    return "almost perfect"
