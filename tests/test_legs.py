"""Tests for leg 2a — does a candidate predict the analyst's own residuals."""
import numpy as np

from sc_referee.inference.legs import leg2a
from sc_referee.inference.replay import ModelSpec, replay


def _synth(seed=0):
    rng = np.random.default_rng(seed)
    n_units, cells_per = 24, 20
    unit = np.repeat(np.arange(n_units), cells_per)
    g_unit = np.repeat(np.arange(3), n_units // 3)[:n_units].astype(float)
    g = g_unit[unit]
    N = rng.integers(800, 1200, len(unit)).astype(float)
    # an OMITTED unit-level covariate that shifts the outcome but is independent of g
    W_unit = rng.standard_normal(n_units)
    W = W_unit[unit]
    ref = 0.02 * N
    mu = ref + N * np.exp(-3.0 + (-0.4) * g + 0.5 * W)
    y = rng.poisson(np.clip(mu, 1e-6, None)).astype(float)
    data = dict(y=y, g=g, N=N, ref=ref, unit=unit)
    summaries = {
        "W": {u: W_unit[u] for u in range(n_units)},          # the true omitted covariate
        "noise": {u: rng.standard_normal() for u in range(n_units)},
    }
    return data, summaries, unit


def _spec():
    return ModelSpec("y", ("g",), "g", family="poisson", exposure_offset="N", additive_reference="ref")


def test_leg2a_finds_an_omitted_covariate_in_the_residuals():
    data, summaries, unit = _synth()
    fit = replay(_spec(), data)
    res = leg2a(fit, unit, summaries, n_permutations=3000)
    by = {c["name"]: c for c in res.candidates}
    # the omitted W predicts the residuals; pure noise does not
    assert abs(by["W"]["statistic"]) > abs(by["noise"]["statistic"])
    assert by["W"]["permutation_p"] < 0.1


def test_leg2a_carries_the_not_a_clean_bill_caveat():
    data, summaries, unit = _synth()
    fit = replay(_spec(), data)
    res = leg2a(fit, unit, summaries, n_permutations=500)
    assert "does not certify" in res.caveat
    assert "Leg 2b" in res.caveat


def test_leg2a_pins_a_residual_contract():
    data, summaries, unit = _synth()
    fit = replay(_spec(), data)
    res = leg2a(fit, unit, summaries, n_permutations=500)
    assert res.residual_contract == "pearson_residual_nb_or_poisson_unit_mean"


def test_leg2a_is_deterministic():
    data, summaries, unit = _synth()
    fit = replay(_spec(), data)
    a = leg2a(fit, unit, summaries, n_permutations=1000, seed=5)
    b = leg2a(fit, unit, summaries, n_permutations=1000, seed=5)
    assert {c["name"]: c["scanwide_p"] for c in a.candidates} == \
        {c["name"]: c["scanwide_p"] for c in b.candidates}
