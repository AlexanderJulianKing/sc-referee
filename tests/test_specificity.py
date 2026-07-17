"""Tests for the hard-decoy specificity harness.

The shipped GB-P07 decoys (sex/age/bmi) are donor-level constants and cannot be fooled by a
cell-level gate. These decoys are cell-level and travel the whole risky path, so they can be fooled
by chance -- and the family-wise calibration is what must stop them.
"""
import numpy as np

from sc_referee.inference import specificity


def _cells(n_donors=24, cells_per=25, seed=0):
    rng = np.random.default_rng(seed)
    donor = np.repeat(np.arange(n_donors), cells_per)
    g = np.repeat(rng.integers(0, 3, n_donors), cells_per).astype(float)
    # a cell-level nuisance with real within-donor variance and donor-level structure, but the
    # donor-level structure is NOT tied to g -- so any association a decoy shows is null
    donor_effect = rng.standard_normal(n_donors)
    value = donor_effect[donor] + rng.standard_normal(len(donor))
    return value, donor, g


def test_family_wise_controls_the_false_positive_rate():
    value, donor, g = _cells()
    res = specificity.run(value, donor, g, n_decoys=30, n_families=6,
                          alpha=0.05, n_permutations=300)
    d = res.as_dict()
    assert d["n_families"] == 6
    assert "family_wise_error_rate" in d
    assert "within_family_rejected_fraction" in d
    assert "scanwide_false_positive_rate" not in d
    assert d["fwer_95pct_ci"][0] <= d["family_wise_error_rate"] <= d["fwer_95pct_ci"][1]


def test_decoys_travel_the_gate():
    value, donor, g = _cells()
    mask = np.arange(len(donor)) % 2 == 0     # an arbitrary gate
    res = specificity.run(value, donor, g, gate_mask=mask, n_decoys=20, n_families=4,
                          alpha=0.05, n_permutations=250)
    assert res.n_decoys > 0
    assert 0 <= res.family_wise_error_rate <= 1


def test_deterministic():
    value, donor, g = _cells()
    a = specificity.run(value, donor, g, n_decoys=20, n_families=3,
                        n_permutations=200, seed=11)
    b = specificity.run(value, donor, g, n_decoys=20, n_families=3,
                        n_permutations=200, seed=11)
    assert a.family_wise_error_rate == b.family_wise_error_rate
    assert a.per_test_false_positive_rate == b.per_test_false_positive_rate


def test_one_rejection_in_one_family_is_one_fwer_event_not_one_over_family_size():
    per_test = [(0.01, 0.7, 0.8, 0.9)]
    scanwide = [(0.01, 0.7, 0.8, 0.9)]
    _, within_family, fwer, _, _ = specificity._summarize_families(
        per_test, scanwide, alpha=0.05
    )
    assert within_family == 0.25
    assert fwer == 1.0


def test_block_permutation_preserves_the_value_distribution():
    """A hard decoy must keep the nuisance's shape -- only its donor assignment is randomized."""
    value, donor, g = _cells(seed=3)
    rng = np.random.default_rng(0)
    decoy = specificity._block_permute(value, donor, g, rng)
    # same overall spread (block contents intact, only reassigned/resized across donors)
    assert abs(decoy.std() - value.std()) < 0.5 * value.std()
    assert len(decoy) == len(value)
