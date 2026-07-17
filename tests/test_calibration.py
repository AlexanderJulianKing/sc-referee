"""Tests for permutation calibration.

The whole point: a lone 1/sqrt(n-1) prices one test, and a candidate set needs a family-wise
correction or the tool cries wolf. These pin that the family-wise p behaves.
"""
import numpy as np

from sc_referee.inference.calibration import calibrate


def _linear(n_units=24, slope=1.0, noise=0.0, seed=0):
    rng = np.random.default_rng(seed)
    g = np.repeat(np.arange(3), n_units // 3).astype(float)[:n_units]
    q = slope * g + noise * rng.standard_normal(n_units)
    return q, g


def test_real_association_survives_family_wise_correction():
    q, g = _linear(slope=1.0, noise=0.3)
    cal = calibrate({"real": q}, g, n_permutations=2000)["real"]
    assert cal.scanwide_p < 0.05
    assert cal.permutation_p < 0.05


def test_a_pile_of_nulls_does_not_manufacture_a_finding():
    """The failure calibration exists to prevent: scan many null candidates, one clears per-test."""
    rng = np.random.default_rng(1)
    g = np.repeat(np.arange(3), 8).astype(float)
    cands = {f"null{i}": rng.standard_normal(24) for i in range(40)}
    cal = calibrate(cands, g, n_permutations=2000)
    per_test_hits = sum(1 for c in cal.values() if c.permutation_p is not None and c.permutation_p < 0.05)
    family_hits = sum(1 for c in cal.values() if c.scanwide_p is not None and c.scanwide_p < 0.05)
    # per-test will flag a few of 40 by chance; the family-wise correction should not
    assert family_hits == 0, f"family-wise flagged {family_hits} pure nulls"
    assert per_test_hits >= 1, "sanity: per-test should catch at least one by chance in 40"


def test_scanwide_p_is_never_smaller_than_per_test_p():
    """Family-wise correction can only make a p larger, never smaller."""
    rng = np.random.default_rng(2)
    g = np.repeat(np.arange(3), 8).astype(float)
    cands = {"strong": 2 * g + 0.1 * rng.standard_normal(24)}
    cands.update({f"n{i}": rng.standard_normal(24) for i in range(20)})
    cal = calibrate(cands, g, n_permutations=2000)
    for c in cal.values():
        if c.permutation_p is not None:
            assert c.scanwide_p >= c.permutation_p - 1e-9


def test_deterministic_under_seed():
    q, g = _linear(noise=0.5)
    a = calibrate({"x": q}, g, n_permutations=1000, seed=7)["x"]
    b = calibrate({"x": q}, g, n_permutations=1000, seed=7)["x"]
    assert a.permutation_p == b.permutation_p
    assert a.scanwide_p == b.scanwide_p


def test_constant_candidate_is_emitted_without_p_values():
    """No-filter rule: a constant summary can't be correlated, but it is not silently dropped."""
    g = np.repeat(np.arange(3), 8).astype(float)
    cal = calibrate({"const": np.ones(24)}, g, n_permutations=500)["const"]
    assert cal.statistic is None
    assert cal.permutation_p is None
    assert cal.scanwide_p is None


def test_small_n_reports_no_null_sd():
    cal = calibrate({"x": np.array([1.0, 2.0, 3.0])}, np.array([0.0, 1.0, 2.0]),
                    n_permutations=100)["x"]
    assert cal.null_sd_per_test is None   # n<4


def test_two_correlated_candidates_share_the_family():
    """Scan-wide p prices the max over the family, so a candidate competes with its neighbours."""
    rng = np.random.default_rng(3)
    g = np.repeat(np.arange(3), 8).astype(float)
    weak, _ = _linear(slope=0.4, noise=1.0, seed=4)
    cal_alone = calibrate({"weak": weak}, g, n_permutations=3000)["weak"]
    cal_crowd = calibrate({"weak": weak, **{f"n{i}": rng.standard_normal(24) for i in range(30)}},
                          g, n_permutations=3000)["weak"]
    # same per-test p, but the crowd can only raise (or equal) the family-wise p
    assert cal_crowd.scanwide_p >= cal_alone.scanwide_p - 1e-9
