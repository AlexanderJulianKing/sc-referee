"""Count splitting / data thinning — the verified primitive. (Item 3, Option A)

Splits a raw count matrix into two independent folds so latent-variable estimation (e.g. clustering)
can be done on one fold and inference on the other, without the circularity of double dipping.
Verified against the primary sources (Neufeld et al.; the data-thinning JMLR paper) — see
docs/research/countsplitting-implementation-spec.md.

This is the ENGINE only. Per GPT-5.5 Pro (2026-07-08) the live `double_dipping` check stays
STRUCTURAL-only; a per-run survival number is a footgun (users over-trust it, and low survival ≠
artifacts). The engine is proven here (tests) and in the benchmark, where a harness can legitimately
run the full train-only clustering pipeline.

`dispersion` is the NB SIZE parameter b (Var = mu + mu²/b; b -> inf is Poisson), per gene — NOT the
DESeq2/scran dispersion alpha = 1/b. Splitting with the wrong b breaks fold independence
(understating it, e.g. a Poisson split, leaves the folds positively correlated → anti-conservative).
"""
from __future__ import annotations

import numpy as np


def poisson_thin(counts, epsilon: float, rng: np.random.Generator):
    """Poisson thinning: X_train | X ~ Binomial(X, epsilon); X_test = X - X_train. Folds are
    independent iff the data are Poisson. Integer-preserving and deterministic given `rng`."""
    if not 0.0 < epsilon < 1.0:
        raise ValueError(f"epsilon must be in (0, 1), got {epsilon}")
    X = np.asarray(counts)
    if X.min() < 0:
        raise ValueError("counts must be non-negative integers")
    train = rng.binomial(X, epsilon)
    return train, X - train


def nb_thin(counts, dispersion, epsilon: float, rng: np.random.Generator):
    """Negative-binomial thinning: rho_ij ~ Beta(eps*b_j, (1-eps)*b_j), X_train | X ~ Binomial(X, rho),
    X_test = X - X_train. Folds are independent iff `dispersion` is the TRUE per-gene size parameter
    b_j. `dispersion` is broadcast across cells; a scalar applies one b to all genes."""
    if not 0.0 < epsilon < 1.0:
        raise ValueError(f"epsilon must be in (0, 1), got {epsilon}")
    X = np.asarray(counts)
    if X.min() < 0:
        raise ValueError("counts must be non-negative integers")

    b = np.asarray(dispersion, dtype=float)
    if b.ndim == 0:
        b = np.full(X.shape[1], float(b))
    if b.shape != (X.shape[1],):
        raise ValueError(f"dispersion must be a per-gene vector of length {X.shape[1]}, got {b.shape}")
    if (b <= 0).any() or not np.isfinite(b).all():
        raise ValueError("dispersion (size parameter b) must be finite and positive per gene")

    a = np.broadcast_to(epsilon * b, X.shape)
    c = np.broadcast_to((1.0 - epsilon) * b, X.shape)
    rho = rng.beta(a, c)
    train = rng.binomial(X, rho)
    return train, X - train
