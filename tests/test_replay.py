"""Tests for the replay executor and leg 2b.

Built on a synthetic additive-reference NB where the true structure is known, so faithfulness and
recovery can be asserted exactly rather than against a benchmark.
"""
import numpy as np
import pytest
from types import SimpleNamespace

from sc_referee.inference.replay import (
    AddedTerm,
    ModelSpec,
    Abstain,
    refit_with_term,
    replay,
)


def _synth(n_units=24, cells_per=20, beta=-0.5, gamma=0.6, seed=0):
    """Counts with an additive reference and a donor-level batch confounded with the exposure.

    Mirrors GB-P07's structure: g constant within unit, a batch B that tracks g and shifts the
    outcome. A model that omits B recovers an attenuated beta; adding B recovers it.
    """
    rng = np.random.default_rng(seed)
    unit = np.repeat(np.arange(n_units), cells_per)
    g_unit = np.repeat(np.arange(3), n_units // 3)[:n_units].astype(float)
    B_unit = (g_unit >= 1).astype(float)                 # batch tracks exposure
    g = g_unit[unit]; B = B_unit[unit]
    N = rng.integers(800, 1200, len(unit)).astype(float)
    ref = 0.02 * N                                        # additive reference (soup)
    mu = ref + N * np.exp(-3.0 + beta * g + gamma * B)
    y = rng.poisson(np.clip(mu, 1e-6, None)).astype(float)
    return dict(y=y, g=g, N=N, ref=ref, B=B - B.mean(), unit=unit,
                Bbad=np.ones(len(unit)))               # a degenerate term (collinear w/ intercept)


def _spec():
    return ModelSpec(response="y", predictors=("g",), target_term="g", family="poisson",
                     exposure_offset="N", additive_reference="ref")


def test_replay_recovers_the_fitted_effect():
    data = _spec_data = _synth()
    fit = replay(_spec(), data)
    assert fit.converged
    # omitting the batch attenuates beta toward zero (confounder rides with g)
    assert -0.5 < fit.target_effect < 0.0


def test_replay_abstains_when_it_cannot_reproduce_the_reported_number():
    data = _synth()
    with pytest.raises(Abstain, match="did not reproduce"):
        replay(_spec(), data, reported_effect=-0.9, tol=0.02)


def test_replay_abstains_on_noninteger_response():
    data = _synth(); data["y"] = data["y"] + 0.5
    with pytest.raises(Abstain, match="nonnegative integer"):
        replay(_spec(), data)


def test_replay_abstains_on_unknown_family():
    data = _synth()
    with pytest.raises(Abstain, match="family"):
        replay(ModelSpec("y", ("g",), "g", family="gaussian",
                         exposure_offset="N", additive_reference="ref"), data)


@pytest.mark.parametrize("bad", [0.0, -1.0, np.inf, -np.inf, np.nan])
def test_replay_abstains_on_nonpositive_or_nonfinite_exposure_offsets(bad):
    data = _synth()
    data["N"][3] = bad

    with pytest.raises(Abstain, match="exposure offset.*positive finite"):
        replay(_spec(), data)


@pytest.mark.parametrize("reported", [np.inf, -np.inf, np.nan])
def test_replay_abstains_on_nonfinite_reported_effect(reported):
    with pytest.raises(Abstain, match="reported effect must be finite"):
        replay(_spec(), _synth(), reported_effect=reported)


def test_replay_abstains_when_optimizer_does_not_converge(monkeypatch):
    import sc_referee.inference.replay as replay_module

    monkeypatch.setattr(replay_module, "minimize", lambda *args, **kwargs: SimpleNamespace(
        success=False,
        message="iteration limit",
        x=np.zeros(2),
        fun=1.0,
    ))

    with pytest.raises(Abstain, match="optimizer did not converge"):
        replay(_spec(), _synth())


def test_replay_abstains_on_nonfinite_or_misaligned_design_vectors():
    nonfinite = _synth()
    nonfinite["g"][0] = np.nan
    with pytest.raises(Abstain, match="predictor 'g'.*finite"):
        replay(_spec(), nonfinite)

    misaligned = _synth()
    misaligned["ref"] = misaligned["ref"][:-1]
    with pytest.raises(Abstain, match="additive reference.*length"):
        replay(_spec(), misaligned)


def test_leg2b_recovers_the_effect_when_the_batch_is_added():
    data = _synth(beta=-0.5, gamma=0.6)
    out = refit_with_term(_spec(), data, AddedTerm(name="B", basis="centered"))
    assert out["identified"]
    # adding the confounded batch moves the estimate away from zero, toward the truth
    assert out["target_effect_with_term"] < out["target_effect_without_term"]
    assert out["shift"] < 0
    assert abs(out["target_effect_with_term"] - (-0.5)) < 0.15   # near the true beta


def test_leg2b_abstains_on_an_unidentified_term():
    data = _synth()
    out = refit_with_term(_spec(), data, AddedTerm(name="Bbad", basis="degenerate"))
    assert out["identified"] is False
    assert "abstained" in out
    assert "not separately identified" in out["abstained"]


def test_leg2b_refuses_an_engine_declared_term():
    data = _synth()
    with pytest.raises(Abstain, match="engine"):
        refit_with_term(_spec(), data, AddedTerm(name="B", basis="x", declared_by="engine"))


def test_leg2b_abstains_when_the_declared_column_is_absent():
    data = _synth()
    with pytest.raises(Abstain, match="not present"):
        refit_with_term(_spec(), data, AddedTerm(name="does_not_exist", basis="x"))


def test_leg2b_reports_identification_diagnostics():
    data = _synth()
    out = refit_with_term(_spec(), data, AddedTerm(name="B", basis="centered"))
    assert out["design_rank_augmented"] == out["design_rank_base"] + 1
    assert "design_condition" in out


# --------------------------------------------------------------------------- limma-voom


def _voom_data(n_units=40, n_genes=300, true_lfc=-1.0, seed=0):
    import numpy as np
    rng = np.random.default_rng(seed)
    treatment = np.tile([0.0, 1.0], n_units // 2)
    lib = rng.integers(1_000_000, 3_000_000, n_units).astype(float)
    target = rng.poisson(200.0 * 2.0 ** (true_lfc * treatment) * lib / 1e6).astype(float)
    other = rng.poisson(rng.uniform(5, 500, n_genes)[None, :] * lib[:, None] / 1e6).astype(float)
    allc = np.column_stack([target, other])
    return dict(y=target, treatment=treatment, __all_counts__=allc), treatment, lib


def _voom_spec(offset=None):
    return ModelSpec("y", ("treatment",), "treatment", family="limma_voom", exposure_offset=offset)


def test_limma_voom_recovers_the_log2_fold_change():
    data, _, _ = _voom_data(true_lfc=-1.0)
    fit = replay(_voom_spec(), data)
    assert abs(fit.target_effect - (-1.0)) < 0.2      # the weighted logCPM model recovers the true LFC


def test_limma_voom_faithfulness_gate():
    data, _, _ = _voom_data(true_lfc=-1.0)
    replay(_voom_spec(), data, reported_effect=-1.0, tol=0.2)   # passes
    with pytest.raises(Abstain, match="did not reproduce"):
        replay(_voom_spec(), data, reported_effect=2.0, tol=0.2)


def test_limma_voom_leg2b_refit():
    import numpy as np
    data, _, _ = _voom_data()
    data["batch"] = (np.arange(len(data["treatment"])) % 3).astype(float)
    out = refit_with_term(_voom_spec(), data, AddedTerm("batch", "centered"))
    assert out["identified"]
    assert "shift" in out


def test_limma_voom_ols_fallback_when_no_matrix():
    data, _, lib = _voom_data(true_lfc=-1.0)
    del data["__all_counts__"]
    data["lib"] = lib
    fit = replay(_voom_spec(offset="lib"), data)
    assert abs(fit.target_effect - (-1.0)) < 0.25     # cruder, still recovers the LFC


def test_limma_voom_abstains_without_matrix_or_offset():
    data, _, _ = _voom_data()
    del data["__all_counts__"]
    with pytest.raises(Abstain, match="needs the full count matrix"):
        replay(_voom_spec(), data)
