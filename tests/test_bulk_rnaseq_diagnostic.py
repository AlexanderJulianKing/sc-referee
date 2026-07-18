"""Second study class: the three-leg diagnostic on a bulk RNA-seq DE workflow.

Structurally different from GB-P07 (flat samples, binary treatment, tier-1 unread confounder, no
additive reference), so these exercise the diagnostic beyond one benchmark. Ground truth is
controlled by the generator (`fixtures.bulk_rnaseq`), so each scenario asserts a known outcome.

The battery spans the outcome space the user asked for:
  works       -- a real confounder the diagnostic CATCHES
  borderline  -- a weak/under-powered confounder the diagnostic refuses to over-claim (MIGHT NOT)
  blind       -- a U-shaped confounder LEG 1 misses but leg 2a rescues (complementarity)
  unmeasured  -- a confounder not in the data: the diagnostic WON'T catch it, and cannot (the limit)
  clean       -- a null covariate the diagnostic SHOULD NOT flag (specificity)
"""
import json

import numpy as np
import pytest

from tests.fixtures.bulk_rnaseq import make
from sc_referee.inference.confounder_candidate import diagnose
from sc_referee.inference.replay import AddedTerm, ModelSpec, replay


def _run(scenario, n, seed=1):
    src, tables, mk, fit_data, gt = make(scenario, n=n, seed=seed)
    df = tables["df"]
    spec = ModelSpec(**mk)
    beta = replay(spec, fit_data).target_effect
    rec = diagnose(
        src, tables, unit="sample", exposure="treatment",
        model_spec=spec, fit_data=fit_data, obs_unit=df["sample"].values,
        residual_candidates={
            "rin": df.set_index("sample").rin.to_dict(),
            "age": df.set_index("sample").age.to_dict(),
            "batch": df.set_index("sample").batch.to_dict(),
        },
        declared_terms=(AddedTerm("rin_c", "centered_continuous"),),
    )
    d = json.loads(rec.to_json())
    leg1 = json.loads(d["leg1"]["record"])
    l1 = {u["name"]: u["association"]["calibration"]["scanwide_p"]
          for u in leg1["unread_columns"] if u["association"].get("calibration")}
    l2a = {c["name"]: c["permutation_p"]
           for c in (d["leg2a"]["candidates"] if d["leg2a"] and "candidates" in d["leg2a"] else [])}
    l2a_fw = {c["name"]: c["scanwide_p"]
              for c in (d["leg2a"]["candidates"] if d["leg2a"] and "candidates" in d["leg2a"] else [])}
    return beta, l1, l2a, d["leg2b"][0], gt, l2a_fw


def test_replay_is_faithful_on_the_second_study_class():
    """A different model structure (NB, offset, NO additive reference) must still replay."""
    src, tables, mk, fit_data, gt = make("clean", n=48, seed=1)
    fit = replay(ModelSpec(**mk), fit_data)
    assert fit.converged
    assert -1.0 < fit.target_effect < 0.0    # near the true -0.6 in the clean case


def test_works_the_confounder_is_caught_and_the_effect_recovered():
    beta, l1, l2a, l2b, gt, l2a_fw = _run("works", n=48)
    # naive estimate is badly biased by the confounder
    assert beta < -1.0
    # leg 1 flags rin family-wise; the decoys are not flagged
    assert l1["rin"] < 0.01
    assert l1["age"] > 0.1 and l1["batch"] > 0.1
    # leg 2b recovers the effect toward the truth (-0.6) with a large shift
    assert l2b["shift"] > 0.5
    assert abs(l2b["target_effect_with_term"] - (-0.6)) < 0.2


def test_borderline_a_weak_confounder_is_not_family_wise_over_claimed():
    """MIGHT NOT WORK: under-powered signal. The tool must not confidently flag it in leg 1, and the
    refit must show the confounding is immaterial -- surfacing weak evidence without a verdict."""
    beta, l1, l2a, l2b, gt, l2a_fw = _run("borderline", n=30)
    # the estimate is barely biased (the confounding is weak)
    assert abs(beta - (-0.6)) < 0.15
    # leg 1 does NOT family-wise flag rin -- no crying wolf on under-powered signal
    assert l1["rin"] > 0.05
    # and the refit confirms the confounding is immaterial
    assert abs(l2b["shift"]) < 0.1


def test_blind_leg1_misses_the_u_shaped_confounder_but_leg2a_rescues():
    """WON'T CATCH (with leg 1 alone): a U-shaped confounder defeats Pearson-of-mean. This is the
    documented §3 blind spot -- and the reason no single leg is sufficient."""
    beta, l1, l2a, l2b, gt, l2a_fw = _run("blind", n=48)
    # leg 1 is blind: the U-shape makes the mean-correlation with the exposure ~0
    assert l1["rin"] > 0.3
    # leg 2a rescues it: rin still predicts the residuals because it affects the outcome
    assert l2a["rin"] < 0.05


def test_unmeasured_the_diagnostic_cannot_surface_what_is_not_in_the_data():
    """WON'T CATCH (genuine, fundamental): the confounder is a latent variable in no table and
    derivable from no code. The estimate is badly biased, yet nothing measurable flags -- because a
    data-bound tool can only surface materialisable candidates. This is the honest hard limit."""
    beta, l1, l2a, l2b, gt, l2a_fw = _run("unmeasured", n=48)
    # the latent confounder badly biases the estimate (here it even flips the sign vs truth -0.6)
    assert abs(beta - (-0.6)) > 0.4
    # yet NOTHING measured flags family-wise -- and critically, no false alarm on the decoys.
    # (batch draws a per-test p ~0.26 by chance here; the family-wise correction is exactly what
    # stops that from becoming a false finding.)
    assert min(l1.values()) > 0.3
    assert min(l2a_fw.values()) > 0.05


def test_clean_a_null_covariate_is_not_flagged():
    """SHOULDN'T CATCH: a covariate independent of treatment and outcome. Specificity on the second
    study class -- the diagnostic must report it null across every leg."""
    beta, l1, l2a, l2b, gt, l2a_fw = _run("clean", n=48)
    # the estimate is unbiased
    assert abs(beta - (-0.6)) < 0.15
    # nothing flags: not leg 1, not leg 2a, and the refit barely moves
    assert min(l1.values()) > 0.2
    assert l2a["rin"] > 0.2
    assert abs(l2b["shift"]) < 0.05


def test_the_second_class_mirrors_contamination_classification():
    """The confounder pattern (leg 1 strong, leg 2a weak/absorbed, leg 2b big shift) reproduces
    GB-P07 in a different structure -- evidence the diagnostic is not GB-P07-specific."""
    _, l1, l2a, l2b, _, l2a_fw = _run("works", n=48)
    assert l1["rin"] < 0.01                 # leg 1 strong (tracks exposure)
    assert l2a["rin"] > l1["rin"]           # leg 2a weaker (confounder absorbed into the exposure)
    assert l2b["shift"] > 0.5               # leg 2b large (refit moves the effect)
