"""Does count-splitting actually defeat double dipping? (Item 3, Option A benchmark.)

The honesty bar (GPT-5.5 Pro, 2026-07-08): show BOTH
  (1) NULL calibration — with NO true subpopulation structure, naive cluster-then-test invents
      "significant" markers (anti-conservative), while count-splitting does NOT; and
  (2) alternative power — with a REAL two-group structure, count-splitting still recovers the true
      markers (at reduced power).
No leakage: for the count-split arm, all clustering is done on the TRAIN fold only; the DE test uses
the independent TEST fold. The naive arm double-dips (clusters and tests on the same cells).

    PYTHONPATH=src:. python bench/countsplit_bench.py
"""
from __future__ import annotations

import math

import numpy as np

from sc_referee.countsplit import nb_thin


def simulate(n_cells=600, n_genes=400, planted=False, n_de=40, effect=2.0, b=5.0, seed=0):
    """NB counts. `planted` => two equal groups with `n_de` genes up-regulated in group B."""
    rng = np.random.default_rng(seed)
    lam = rng.gamma(2.0, 1.0, size=n_genes) + 0.5             # per-gene base mean
    mu = np.tile(lam, (n_cells, 1)).astype(float)
    labels, de = None, set()
    if planted:
        labels = (np.arange(n_cells) >= n_cells // 2).astype(int)
        de_idx = rng.choice(n_genes, n_de, replace=False)
        mu[np.ix_(np.where(labels == 1)[0], de_idx)] *= effect
        de = set(int(i) for i in de_idx)
    X = rng.negative_binomial(b, b / (b + mu)).astype(int)
    return X, labels, de, np.full(n_genes, float(b))


def _cluster(counts_fold, k=2, seed=0):
    """Cluster cells from a fold: log-CPM -> PCA -> KMeans. (KMeans always splits noise into k groups
    — that is the point of the null test.)"""
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA

    libs = counts_fold.sum(1, keepdims=True) + 1e-9
    Y = np.log1p(counts_fold / libs * 1e4)
    Z = PCA(n_components=min(20, Y.shape[1] - 1, Y.shape[0] - 1), random_state=seed).fit_transform(Y)
    return KMeans(n_clusters=k, n_init=10, random_state=seed).fit_predict(Z)


def _bh_significant(test_fold, labels, alpha=0.05):
    """BH-significant genes for a Mann–Whitney test between the two label groups on `test_fold`."""
    from scipy.stats import mannwhitneyu
    from statsmodels.stats.multitest import multipletests

    a, bb = test_fold[labels == 0], test_fold[labels == 1]
    if a.shape[0] < 2 or bb.shape[0] < 2:
        return set(), np.ones(test_fold.shape[1])
    p = np.array([mannwhitneyu(a[:, j], bb[:, j], alternative="two-sided").pvalue
                  for j in range(test_fold.shape[1])])
    p = np.nan_to_num(p, nan=1.0)
    padj = multipletests(p, method="fdr_bh")[1]
    return set(int(j) for j in np.where(padj <= alpha)[0]), p


def naive_markers(X, k=2, seed=0):
    """DOUBLE DIP: cluster on the full data, then test the SAME cells between those clusters."""
    labels = _cluster(X, k=k, seed=seed)
    sig, p = _bh_significant(np.log1p(X), labels)
    return sig, p


def countsplit_markers(X, dispersion, k=2, epsilon=0.5, seed=0):
    """Cluster on the TRAIN fold only; test the independent TEST fold against those labels."""
    rng = np.random.default_rng(seed)
    train, test = nb_thin(X, dispersion, epsilon, rng)
    labels = _cluster(train, k=k, seed=seed)                  # no X_test leakage
    sig, p = _bh_significant(np.log1p(test), labels)
    return sig, p


def evaluate(seed=0, *, n_cells=600, n_genes=400, n_de=40, effect=2.0):
    # (1) NULL: no true structure — false-positive rate = fraction of genes called "significant"
    Xn, _, _, bn = simulate(n_cells=n_cells, n_genes=n_genes, planted=False, seed=seed)
    naive_null_calls = len(naive_markers(Xn, seed=seed)[0])
    csplit_null_calls = len(countsplit_markers(Xn, bn, seed=seed)[0])
    naive_null = naive_null_calls / n_genes
    csplit_null = csplit_null_calls / n_genes

    # (2) TWO-GROUP: recall of the planted DE genes, and false positives among the rest
    Xp, _, de, bp = simulate(n_cells=n_cells, n_genes=n_genes, planted=True, n_de=n_de,
                             effect=effect, seed=seed)
    cs_sig = countsplit_markers(Xp, bp, seed=seed)[0]
    recall = len(cs_sig & de) / max(len(de), 1)
    fp = len(cs_sig - de) / max(n_genes - len(de), 1)
    return dict(naive_null_fpr=naive_null, countsplit_null_fpr=csplit_null,
                naive_null_any=bool(naive_null_calls), countsplit_null_any=bool(csplit_null_calls),
                naive_null_calls=naive_null_calls, countsplit_null_calls=csplit_null_calls,
                countsplit_recall=recall, countsplit_fp_rate=fp, n_de=len(de))


def _wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        raise ValueError("at least one independent seed is required")
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return max(0.0, center - radius), min(1.0, center + radius)


def evaluate_many(seeds=range(20), *, evaluator=evaluate, **kwargs):
    """Estimate global-null family error over independent simulated datasets.

    Under the global null, FDR equals the probability of at least one rejection. The previous
    one-seed, per-gene fraction could not support a calibration claim.
    """
    seeds = tuple(int(seed) for seed in seeds)
    if len(set(seeds)) != len(seeds):
        raise ValueError("calibration seeds must be unique independent dataset identifiers")
    rows = tuple(evaluator(seed=seed, **kwargs) for seed in seeds)
    n = len(rows)
    if n == 0:
        raise ValueError("at least one calibration seed is required")
    naive_events = sum(bool(row["naive_null_any"]) for row in rows)
    countsplit_events = sum(bool(row["countsplit_null_any"]) for row in rows)
    return {
        "seeds": seeds,
        "n_null_families": n,
        "naive_null_family_error": naive_events / n,
        "naive_null_family_error_ci95": _wilson(naive_events, n),
        "countsplit_null_family_error": countsplit_events / n,
        "countsplit_null_family_error_ci95": _wilson(countsplit_events, n),
        "mean_countsplit_recall": float(np.mean([row["countsplit_recall"] for row in rows])),
        "mean_countsplit_fp_rate": float(np.mean([row["countsplit_fp_rate"] for row in rows])),
        "runs": rows,
    }


if __name__ == "__main__":
    r = evaluate_many()
    print(f"NULL calibration over {r['n_null_families']} independent simulated datasets:")
    print(f"  naive family error:       {r['naive_null_family_error']:.2f} "
          f"(95% CI {r['naive_null_family_error_ci95'][0]:.2f}–{r['naive_null_family_error_ci95'][1]:.2f})")
    print(f"  count-split family error: {r['countsplit_null_family_error']:.2f} "
          f"(95% CI {r['countsplit_null_family_error_ci95'][0]:.2f}–"
          f"{r['countsplit_null_family_error_ci95'][1]:.2f})")
    print("\nPLANTED alternatives — count-splitting:")
    print(f"  mean recall:              {r['mean_countsplit_recall']:.2f}")
    print(f"  mean false-positive rate: {r['mean_countsplit_fp_rate']:.2f}")
