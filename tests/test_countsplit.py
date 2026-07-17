"""Item 3 (Option A): the count-split / data-thinning primitive, numerically validated.

Verified against the primary sources (Neufeld et al.; the data-thinning JMLR paper) — see
docs/research/countsplitting-implementation-spec.md. The live double_dipping check stays
STRUCTURAL-only (GPT-5.5 Pro, 2026-07-08); this is the corrected-number ENGINE, proven here and in
the benchmark, not wired into a per-run verdict.

Poisson thinning: X_train | X ~ Binomial(X, eps); folds independent iff the data are Poisson.
NB thinning:      rho ~ Beta(eps*b, (1-eps)*b) per entry, X_train | X ~ Binomial(X, rho); folds
                  independent iff the split uses the TRUE per-gene dispersion b (the SIZE param,
                  Var = mu + mu^2/b, b->inf = Poisson). Splitting NB data with a Poisson split
                  (b'=inf, i.e. understated dispersion) leaves the folds POSITIVELY correlated.
"""
import numpy as np

from sc_referee.countsplit import nb_thin, poisson_thin


def test_poisson_thin_preserves_counts_and_is_deterministic():
    X = np.random.default_rng(0).poisson(8, size=(200, 5))
    tr1, te1 = poisson_thin(X, 0.5, np.random.default_rng(1))
    tr2, te2 = poisson_thin(X, 0.5, np.random.default_rng(1))
    assert np.array_equal(tr1 + te1, X)                 # X_train + X_test == X (integer preserving)
    assert np.array_equal(tr1, tr2)                     # deterministic given the seed
    assert (tr1 >= 0).all() and (tr1 <= X).all()


def test_poisson_thin_splits_the_mean_by_epsilon():
    X = np.random.default_rng(2).poisson(10, size=(20000, 1))
    tr, te = poisson_thin(X, 0.3, np.random.default_rng(3))
    assert abs(tr.mean() - 0.3 * X.mean()) < 0.1
    assert abs(te.mean() - 0.7 * X.mean()) < 0.1


def test_poisson_thin_folds_are_independent_on_poisson_data():
    X = np.random.default_rng(4).poisson(12, size=(50000, 1))
    tr, te = poisson_thin(X, 0.5, np.random.default_rng(5))
    assert abs(np.corrcoef(tr.ravel(), te.ravel())[0, 1]) < 0.02


def test_nb_thin_preserves_counts():
    b = 5.0
    X = np.random.default_rng(6).negative_binomial(b, b / (b + 10), size=(200, 3))
    tr, te = nb_thin(X, np.full(3, b), 0.5, np.random.default_rng(7))
    assert np.array_equal(tr + te, X)
    assert (tr >= 0).all() and (tr <= X).all()


def test_nb_thin_independent_with_true_dispersion_but_poisson_split_is_positively_correlated():
    """The load-bearing validity condition + the covariance DIRECTION the consult got backwards
    (a Poisson split understates dispersion -> anti-conservative positive correlation)."""
    b, mu, n = 3.0, 15.0, 60000
    X = np.random.default_rng(8).negative_binomial(b, b / (b + mu), size=(n, 1))
    tr_nb, te_nb = nb_thin(X, np.array([b]), 0.5, np.random.default_rng(9))
    tr_po, te_po = poisson_thin(X, 0.5, np.random.default_rng(10))    # WRONG model for NB data

    assert abs(np.corrcoef(tr_nb.ravel(), te_nb.ravel())[0, 1]) < 0.03   # correct b -> independent
    assert np.corrcoef(tr_po.ravel(), te_po.ravel())[0, 1] > 0.10        # Poisson split -> positive corr
