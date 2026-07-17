"""End-to-end tests for the assembled three-leg diagnostic."""
import json

import numpy as np
import pandas as pd

from sc_referee.inference.confounder_candidate import diagnose
from sc_referee.inference.replay import AddedTerm, ModelSpec

SOURCE = '''
genes = ["HBB","CXCL10"]
p_amb = {g: empty[g].sum()/empty.total_umi.sum() for g in genes}
c["rho"] = np.clip(c.HBB/(c.total_umi*p_amb["HBB"]), 0, 1)
'''


def _tables():
    rng = np.random.default_rng(0)
    empty = pd.DataFrame({"total_umi": [1000], "HBB": [100], "CXCL10": [50]})
    rows = []
    for d in range(24):
        g = d % 3
        rho = 0.1 + 0.1 * g                       # ambient tracks genotype
        for _ in range(20):
            rows.append({"donor": f"D{d}", "g": g, "total_umi": 1000,
                         "HBB": rho * 1000 * 0.1, "CXCL10": 5, "sex": d % 2})
    return {"c": pd.DataFrame(rows).reset_index(drop=True), "empty": empty}


def test_leg1_only_runs_without_a_model():
    t = _tables()
    rec = diagnose(SOURCE, t, unit="donor", exposure="g")
    assert rec.leg1["kind"] == "single"
    assert rec.leg2a is None
    assert rec.leg2b == ()
    assert "scientist" in rec.standing_statement


def test_proxy_recovery_without_effect_or_fit_data_still_runs_leg1_and_skips_model_legs():
    source = '''
dds = DeseqDataSet(counts=counts, metadata=meta, design_factors="g")
c["rho"] = c.HBB / c.total_umi
'''
    rec = diagnose(source, _tables(), unit="donor", exposure="g", outcome="CXCL10",
                   fit_data=None, reported_effect=None)
    assert rec.leg1["kind"] == "single"
    assert rec.leg2a is None
    assert rec.leg2b == ()
    assert rec.model_recovery["proxy"] is True
    assert "model legs skipped" in rec.model_recovery["binding"]["abstained"]


def test_dual_leg1_when_a_mask_is_given():
    t = _tables()
    c = t["c"]
    mask = pd.Series(c.index % 3 != 0, index=c.index)
    rec = diagnose(SOURCE, t, unit="donor", exposure="g", fitted_mask=mask)
    assert rec.leg1["kind"] == "dual"
    leg1 = json.loads(rec.leg1["record"])
    assert "pre_gate" in leg1 and "post_gate" in leg1 and "deltas" in leg1


def test_full_record_serialises_and_carries_the_standing_statement():
    t = _tables()
    rec = diagnose(SOURCE, t, unit="donor", exposure="g")
    blob = json.loads(rec.to_json())
    assert blob["standing_statement"]
    assert "undecidable from" in blob["standing_statement"]
    # the record renders no verdict
    low = rec.to_json().lower()
    for word in ("confounder detected", "is a confounder", "error in", "the correct model"):
        assert word not in low


def test_leg2b_records_a_declared_term_when_a_model_is_present():
    """Synthetic additive-reference model where an omitted batch term recovers the effect."""
    rng = np.random.default_rng(1)
    n_units, cells_per = 24, 20
    unit = np.repeat(np.arange(n_units), cells_per)
    g_unit = np.repeat(np.arange(3), n_units // 3)[:n_units].astype(float)
    g = g_unit[unit]
    B = (g_unit >= 1).astype(float)[unit]
    N = rng.integers(800, 1200, len(unit)).astype(float)
    ref = 0.02 * N
    y = rng.poisson(np.clip(ref + N * np.exp(-3 - 0.5 * g + 0.6 * B), 1e-6, None)).astype(float)
    fit_data = dict(y=y, g=g, N=N, ref=ref, B=B - B.mean())
    spec = ModelSpec("y", ("g",), "g", family="poisson", exposure_offset="N",
                     additive_reference="ref")
    # leg 1 needs some table; reuse a trivial one carrying unit+exposure
    t = _tables()
    rec = diagnose(SOURCE, t, unit="donor", exposure="g",
                   model_spec=spec, fit_data=fit_data,
                   declared_terms=(AddedTerm("B", "centered"),))
    assert len(rec.leg2b) == 1
    out = rec.leg2b[0]
    assert out["identified"]
    assert out["shift"] < 0            # adding the confounded batch moves beta away from zero


def test_leg2b_abstains_without_a_model():
    t = _tables()
    rec = diagnose(SOURCE, t, unit="donor", exposure="g",
                   declared_terms=(AddedTerm("x", "y"),))
    assert rec.leg2b[0]["abstained"]


def test_to_md_renders_evidence_without_a_verdict():
    t = _tables()
    rec = diagnose(SOURCE, t, unit="donor", exposure="g")
    md = rec.to_md()
    assert "evidence, not a verdict" in md
    assert "Leg 1" in md
    assert "scientist's to answer" in md
    low = md.lower()
    for word in ("is a confounder", "confounder detected", "the correct model", "you should"):
        assert word not in low


def test_diagnose_auto_recovers_the_model_from_code():
    """No hand-set model_spec: the spec is recovered from a hand-rolled NLL in the source."""
    import numpy as np
    handrolled = '''
from scipy.optimize import minimize
from scipy.special import gammaln
def nll(params):
    alpha, beta = params[0], params[1]
    mu = amb + Nfree*np.exp(alpha + beta*g)
    mu = np.clip(mu, 1e-9, None)
    theta = np.exp(params[2])
    return -np.sum(gammaln(y+theta)-gammaln(theta)-gammaln(y+1)+theta*np.log(theta/(theta+mu))+y*np.log(mu/(theta+mu)))
rnb = minimize(nll, [0.0,0.0,1.0])
'''
    rng = np.random.default_rng(0); n = 400
    g = rng.integers(0, 3, n).astype(float); tu = rng.integers(800, 1200, n).astype(float)
    amb = 0.15 * tu * 0.02; Nfree = 0.85 * tu
    y = rng.poisson(np.clip(amb + Nfree * np.exp(-3 - 0.5 * g), 1e-6, None)).astype(float)
    fit_data = {"y": y, "amb": amb, "Nfree": Nfree, "g": g, "g_c": g - g.mean()}
    t = _tables()
    rec = diagnose(handrolled, t, unit="donor", exposure="g",
                   model_spec=None, fit_data=fit_data)   # no spec -> auto-recover
    assert rec.model_recovery["recognised"] is True
    assert rec.model_recovery["pattern"] == "handrolled_nll"
    assert rec.model_recovery["additive_reference"] == "amb"


def test_diagnose_is_fully_automatic_recover_and_bind():
    """Only source + tables + unit + exposure + mask. No model_spec, no fit_data: the tool recovers
    the model AND binds its variables from the analyst's own code."""
    import numpy as np
    import pandas as pd
    src = '''
genes = ["HBB", "CXCL10"]
p_amb = {gene: empty[gene].sum()/empty.total_umi.sum() for gene in genes}
c["rho"] = np.clip(c.HBB/(c.total_umi*p_amb["HBB"]), 0, 1)
act = c[c.activated == 1].copy().reset_index(drop=True)
y = act.CXCL10.values.astype(float)
tu = act.total_umi.values.astype(float)
g = act.g.values.astype(float)
rho = act.rho.values
amb = rho*tu*p_amb["CXCL10"]
Nfree = (1-rho)*tu
def nll(params):
    alpha, beta = params[0], params[1]
    mu = amb + Nfree*np.exp(alpha + beta*g)
    mu = np.clip(mu, 1e-9, None)
    theta = np.exp(params[2])
    return -np.sum(gammaln(y+theta)-gammaln(theta)-gammaln(y+1)+theta*np.log(theta/(theta+mu))+y*np.log(mu/(theta+mu)))
rnb = minimize(nll, [0.0, 0.0, 1.0])
'''
    rng = np.random.default_rng(0); n = 300
    c = pd.DataFrame({"donor": np.repeat(np.arange(24), n // 24 + 1)[:n],
                      "HBB": rng.integers(0, 40, n).astype(float),
                      "CXCL10": rng.integers(0, 60, n).astype(float),
                      "total_umi": rng.integers(800, 1200, n).astype(float),
                      "activated": rng.integers(0, 2, n)})
    c["g"] = (c.donor % 3).astype(float)
    empty = pd.DataFrame({"HBB": [100.0], "CXCL10": [50.0], "total_umi": [1000.0]})
    mask = pd.Series(c.activated == 1, index=c.index)
    rec = diagnose(src, {"c": c, "empty": empty}, unit="donor", exposure="g", fitted_mask=mask)
    mr = rec.model_recovery
    assert mr["recognised"] is True
    assert mr["binding"]["source"] == "auto (analyst definitions)"
    assert set(mr["binding"]["bound"]) == {"amb", "Nfree", "y", "g"}
