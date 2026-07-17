"""Tests for auto-binding a recovered ModelSpec's variables to data.

The binder resolves code-level names (amb, Nfree, y, g) through the analyst's own assignments and
evaluates them against the bound data. Sound over complete: abstains loudly outside its grammar.
"""
import numpy as np
import pandas as pd
import pytest

from sc_referee.inference.bind import bind_fit_data
from sc_referee.inference.materialization import Abstain

# The GB-P07 fit chain: a derived column, a fitted-population subset, .values noise, a rate dict,
# and arithmetic building amb / Nfree.
SOURCE = '''
genes = ["HBB", "CXCL10"]
p_amb = {gene: empty[gene].sum()/empty.total_umi.sum() for gene in genes}
c["rho"] = np.clip(c.HBB/(c.total_umi*p_amb["HBB"]), 0, 1)
act = c[c.activated == 1].copy().reset_index(drop=True)
y   = act.CXCL10.values.astype(float)
tu  = act.total_umi.values.astype(float)
g   = act.g.values.astype(float)
rho = act.rho.values
amb = rho*tu*p_amb["CXCL10"]
Nfree = (1-rho)*tu
'''


def _data(n=120, seed=0):
    rng = np.random.default_rng(seed)
    c = pd.DataFrame({
        "HBB": rng.integers(0, 40, n).astype(float),
        "CXCL10": rng.integers(0, 60, n).astype(float),
        "total_umi": rng.integers(800, 1200, n).astype(float),
        "g": rng.integers(0, 3, n).astype(float),
        "activated": rng.integers(0, 2, n),
    })
    empty = pd.DataFrame({"HBB": [100.0], "CXCL10": [50.0], "total_umi": [1000.0]})
    return c, empty


def test_binds_the_derived_ambient_term_matching_hand_computation():
    c, empty = _data()
    mask = (c.activated == 1).values
    bound = bind_fit_data(SOURCE, ["amb", "Nfree", "y", "g"], {"c": c, "empty": empty},
                          fitted_mask=mask)
    # hand-compute amb on the fitted population
    pH = empty.HBB.sum() / empty.total_umi.sum()
    pC = empty.CXCL10.sum() / empty.total_umi.sum()
    rho = np.clip(c.HBB / (c.total_umi * pH), 0, 1)
    hand_amb = (rho * c.total_umi * pC).values[mask]
    assert np.allclose(bound["amb"], hand_amb)
    assert np.allclose(bound["Nfree"], ((1 - rho) * c.total_umi).values[mask])


def test_everything_is_aligned_to_the_fitted_population():
    c, empty = _data()
    mask = (c.activated == 1).values
    bound = bind_fit_data(SOURCE, ["amb", "Nfree", "y", "g"], {"c": c, "empty": empty},
                          fitted_mask=mask)
    k = int(mask.sum())
    assert all(v.shape == (k,) for v in bound.values())


def test_resolves_a_derived_column_through_the_subset():
    """`c["rho"] = ...` then `rho = act.rho.values` where act is the gate subset."""
    c, empty = _data()
    mask = (c.activated == 1).values
    bound = bind_fit_data(SOURCE, ["y"], {"c": c, "empty": empty}, fitted_mask=mask)
    assert np.allclose(bound["y"], c.CXCL10.values[mask])


def test_abstains_without_a_mask_when_the_fit_uses_a_subset():
    c, empty = _data()
    with pytest.raises(Abstain, match="fitted subset|fitted_mask"):
        bind_fit_data(SOURCE, ["amb"], {"c": c, "empty": empty}, fitted_mask=None)


def test_abstains_on_a_name_that_is_not_defined():
    c, empty = _data()
    mask = (c.activated == 1).values
    with pytest.raises(Abstain, match="not a module-scope|not directly bindable"):
        bind_fit_data(SOURCE, ["nonexistent"], {"c": c, "empty": empty}, fitted_mask=mask)


def test_abstains_on_a_call_outside_the_grammar():
    src = SOURCE + "\nweird = some_model.predict(act.total_umi.values)\n"
    c, empty = _data()
    mask = (c.activated == 1).values
    with pytest.raises(Abstain, match="outside the binder grammar"):
        bind_fit_data(src, ["weird"], {"c": c, "empty": empty}, fitted_mask=mask)


def test_no_subset_flat_data_binds_directly():
    """A flat fit (no gate): module vars read columns of a bound frame directly."""
    src = '''
logN = np.log(df.library_size)
mu_off = df.library_size
resp = df.y.values
'''
    df = pd.DataFrame({"y": [1.0, 2, 3, 4], "library_size": [100.0, 200, 150, 300]})
    bound = bind_fit_data(src, ["resp"], {"df": df})
    assert np.allclose(bound["resp"], df.y.values)
