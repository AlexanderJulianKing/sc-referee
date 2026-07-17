"""Tests for reconstructing a ModelSpec from analyst code.

The point: the diagnostic should recover the model STRUCTURE from the code, not be told it. Sound
over complete -- when it fires it is right; otherwise it abstains and the human sets the spec.
"""
import numpy as np

from sc_referee.inference.model_recovery import recover
from sc_referee.inference.replay import replay

# The GB-P07 shape: a hand-rolled NB NLL with an additive reference, minimised. Exactly what all
# five frontier runs wrote, because a log link cannot express additive contamination.
HANDROLLED = '''
from scipy.optimize import minimize
from scipy.special import gammaln
import numpy as np
def nll(params, dist="nb"):
    alpha, beta = params[0], params[1]
    mu_e = Nfree*np.exp(alpha + beta*g)
    mu = amb + mu_e
    mu = np.clip(mu, 1e-9, None)
    if dist=="poisson":
        return -np.sum(y*np.log(mu) - mu - gammaln(y+1))
    theta = np.exp(params[2])
    return -np.sum(gammaln(y+theta)-gammaln(theta)-gammaln(y+1)
                   +theta*np.log(theta/(theta+mu))+y*np.log(mu/(theta+mu)))
rnb = minimize(nll, [np.log(0.01), 0.0, 1.0], args=("nb",), method="Nelder-Mead")
'''

STATSMODELS = '''
import statsmodels.formula.api as smf
import statsmodels.api as sm
model = smf.glm("y ~ treatment", data=df, family=sm.families.NegativeBinomial(), offset=df.logN).fit()
beta = model.params["treatment"]
'''


def test_recovers_the_handrolled_nll_structure():
    rm = recover(HANDROLLED, exposure="g")
    assert rm.recognised
    assert rm.pattern == "handrolled_nll"
    assert rm.family == "nb"
    assert rm.response == "y"
    assert rm.offset == "Nfree"
    assert rm.additive_reference == "amb"          # the additive contamination term, recovered
    assert rm.predictors == ("g",)
    assert rm.target_term == "g"


def test_sees_through_the_clip_rebinding():
    """`mu = amb + mu_e` then `mu = np.clip(mu, ...)`. The mean is the first, not the clip."""
    rm = recover(HANDROLLED, exposure="g")
    assert rm.additive_reference == "amb"          # not "np.clip(...)"


def test_the_recovered_spec_replays_faithfully():
    """Recover the structure, bind it to data, and confirm it reproduces the true coefficient.

    A confounded synthetic where the naive fit is attenuated; the recovered spec must reproduce
    that same attenuated estimate (faithful replay), which is the precondition for the legs.
    """
    rng = np.random.default_rng(0)
    n = 400
    g = rng.integers(0, 3, n).astype(float)
    tu = rng.integers(800, 1200, n).astype(float)
    rho = 0.15 + 0.0 * g
    amb = rho * tu * 0.02
    Nfree = (1 - rho) * tu
    mu = amb + Nfree * np.exp(-3.0 - 0.5 * g)
    y = rng.poisson(np.clip(mu, 1e-6, None)).astype(float)

    rm = recover(HANDROLLED, exposure="g")
    spec = rm.to_model_spec()
    fit = replay(spec, {"y": y, "amb": amb, "Nfree": Nfree, "g": g})
    # the recovered structure reproduces the true coefficient (~ -0.5); that faithfulness is the
    # point, not the optimiser's success flag (Nelder-Mead's is unreliable at this size)
    assert -0.7 < fit.target_effect < -0.3


def test_recovers_statsmodels_formula():
    rm = recover(STATSMODELS, exposure="treatment")
    assert rm.recognised
    assert rm.pattern == "statsmodels_formula"
    assert rm.family == "nb"
    assert rm.response == "y"
    assert rm.offset == "logN"                       # df.logN normalised to a bindable column name
    assert rm.additive_reference is None             # a GLM cannot express one
    assert rm.target_term == "treatment"


def test_statsmodels_poisson_family():
    rm = recover(STATSMODELS.replace("NegativeBinomial", "Poisson"), exposure="treatment")
    assert rm.family == "poisson"


def test_abstains_when_the_exposure_is_not_in_the_model():
    rm = recover(HANDROLLED, exposure="not_a_predictor")
    assert not rm.recognised
    assert "not among predictors" in " ".join(rm.reasons)


def test_abstains_on_an_unrecognised_fit():
    for src in ("m = LinearRegression().fit(X, y)",
                "result = my_custom_solver(data)",
                "x = 1"):
        rm = recover(src, exposure="g")
        assert not rm.recognised
        assert rm.reasons


def test_abstains_on_unparseable_source_with_no_fit():
    # unparseable-as-Python (e.g. R) is no longer a hard error -- it falls through to the
    # language-agnostic text path. With no fit tokens, it still abstains.
    rm = recover("def broken(:", exposure="g")
    assert not rm.recognised
    assert rm.reasons


def test_to_model_spec_raises_when_not_recognised():
    rm = recover("x = 1", exposure="g")
    import pytest
    with pytest.raises(ValueError):
        rm.to_model_spec()


# --------------------------------------------------------------------------- broadened patterns


def test_recovers_r_deseq2_from_text():
    src = "dds <- DESeqDataSetFromMatrix(cts, meta, design = ~ batch + g)\ndds <- DESeq(dds)"
    rm = recover(src, exposure="g", outcome="CXCL10")
    assert rm.recognised
    assert rm.pattern == "count_glm_text"
    assert rm.family == "nb"
    assert rm.response == "CXCL10"
    assert set(rm.predictors) == {"batch", "g"}
    assert rm.proxy is True          # size factors not reproduced -> must be faithfulness-gated


def test_recovers_r_glm_poisson_with_offset():
    rm = recover("m <- glm(CXCL10 ~ g, family=poisson, offset=log(total_umi))",
                 exposure="g")
    assert rm.recognised
    assert rm.family == "poisson"
    assert rm.offset == "total_umi"   # log(total_umi) unwrapped to the multiplicative offset
    assert rm.proxy is True


def test_recovers_pydeseq2_design_factors():
    rm = recover('dds = DeseqDataSet(counts=counts, metadata=meta, design_factors="g")',
                 exposure="g", outcome="CXCL10")
    assert rm.recognised
    assert rm.family == "nb"
    assert rm.predictors == ("g",)


def test_count_glm_abstains_when_response_unnamed_and_no_outcome():
    rm = recover("dds <- DESeqDataSetFromMatrix(cts, meta, design = ~ g)\nDESeq(dds)", exposure="g")
    assert not rm.recognised
    assert "response is unnamed" in " ".join(rm.reasons)


def test_handrolled_is_not_marked_proxy():
    rm = recover(HANDROLLED, exposure="g")
    assert rm.recognised
    assert rm.proxy is False          # exact replay, no faithfulness gate required


def test_proxy_model_legs_skipped_without_a_reported_effect():
    """Soundness: an approximate fit may not match; without a reported effect to check it, the model
    legs must not run. Leg 1 still runs."""
    import numpy as np, pandas as pd
    from sc_referee.inference.confounder_candidate import diagnose
    src = "dds <- DESeqDataSetFromMatrix(cts, meta, design = ~ g)\nDESeq(dds)\nc['rho']=c.HBB/c.total_umi"
    n = 60
    c = pd.DataFrame({"donor": np.repeat(np.arange(6), 10), "g": np.repeat(np.arange(3), 20).astype(float),
                      "HBB": np.arange(n, dtype=float), "total_umi": np.full(n, 1000.0), "CXCL10": np.arange(n, dtype=float)})
    rec = diagnose(src, {"c": c}, unit="donor", exposure="g", outcome="CXCL10",
                   fit_data={"CXCL10": c.CXCL10.values, "g": c.g.values},
                   reported_effect=None)
    assert rec.model_recovery["recognised"] is True
    assert rec.model_recovery["proxy"] is True
    assert rec.leg2a is None or rec.leg2a.get("abstained") or "candidates" not in rec.leg2a
