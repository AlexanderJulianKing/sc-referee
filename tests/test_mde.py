"""Numerical sanity checks for the MDE formulas + the `powered` gate (C5).

These pin the two power formulas against independent hand-computations before anything
trusts the gate — a wrong MDE would silently turn honest abstention into false blockers
(or vice-versa)."""
import numpy as np
import pytest
from scipy import stats

from sc_referee.engine import (
    is_powered,
    mde_paired,
    mde_wald,
    powered_fraction,
)


def test_mde_paired_matches_definition():
    s, n = 0.5, 8
    df = n - 1
    expected = (stats.t.ppf(0.975, df) + stats.t.ppf(0.8, df)) * s / np.sqrt(n)
    assert abs(mde_paired(s, n) - expected) < 1e-12


def test_mde_paired_known_value():
    # n=8 pairs, s_diff=0.5 log2 units -> ~0.576 log2FC
    assert abs(mde_paired(0.5, 8) - 0.5764) < 1e-3


def test_mde_wald_matches_z_formula():
    se = 0.3
    expected = (stats.norm.ppf(0.975) + stats.norm.ppf(0.8)) * se
    assert abs(mde_wald(se) - expected) < 1e-12


def test_mde_shrinks_with_more_replicates():
    assert mde_paired(0.5, 20) < mde_paired(0.5, 8)


def test_smaller_alpha_widens_mde():
    assert mde_paired(0.5, 8, alpha=0.01) > mde_paired(0.5, 8, alpha=0.05)


def test_too_few_pairs_is_infinite_mde():
    assert np.isinf(mde_paired(0.5, 1))


def test_powered_fraction_counts_detectable_features():
    mdes = np.array([0.5, 0.8, 1.2, 2.0])  # ref=1.0 -> 2 of 4 detectable
    assert powered_fraction(mdes, 1.0) == 0.5


def test_powered_gate_threshold():
    assert is_powered(np.array([0.5, 0.6, 0.7, 0.9, 0.95]), 1.0) is True   # 5/5 <= 1.0
    assert is_powered(np.array([0.5, 0.8, 1.2, 2.0]), 1.0) is False        # 2/4 < 0.8


def test_non_finite_mde_counts_as_not_powered():
    """A feature with an infinite MDE is UNDETECTABLE, not absent. Dropping it from the
    denominator overstates power and lets an inadequate recompute earn a blocker.
    (This test previously asserted the opposite. It was wrong. — adversarial review, 2026-07-08)"""
    assert powered_fraction(np.array([0.5, np.inf]), 1.0) == pytest.approx(0.5)
    assert powered_fraction(np.array([0.5, np.nan, np.inf, 0.6]), 1.0) == pytest.approx(0.5)
    assert powered_fraction(np.array([np.nan, np.inf]), 1.0) == 0.0
    assert is_powered(np.array([0.5, np.inf, np.inf, np.inf]), 1.0) is False


def test_bh_runs_over_the_testable_family_only():
    """Non-testable features must NOT inflate the FDR family: n=1000 with 999 untested
    features drives a real p=0.04 discovery to padj=1.0. That is a FALSE BLOCKER generator."""
    from statsmodels.stats.multitest import multipletests

    from sc_referee.engine import _bh

    p = np.concatenate([[0.04], np.ones(999)])
    testable = np.zeros(1000, dtype=bool)
    testable[0] = True

    padj = _bh(p, testable)
    expected = multipletests(p[testable], method="fdr_bh")[1][0]
    assert padj[0] == pytest.approx(expected)      # 0.04, not 1.0
    assert (padj[~testable] == 1.0).all()          # untested rows are reported, never "lost"
