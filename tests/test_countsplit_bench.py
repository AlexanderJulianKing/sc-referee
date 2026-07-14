"""Guards the count-split benchmark's two honest claims (GPT-5.5 Pro's bar, item 3 Option A):
naive cluster-then-test inflates the null that count-splitting calibrates, and count-splitting still
recovers real markers. Regression-guarded so the benchmark stays evidence, not a demo.
"""
import pytest

pytest.importorskip("sklearn")
pytestmark = pytest.mark.filterwarnings("ignore")

from bench.countsplit_bench import countsplit_markers, naive_markers, simulate


def test_countsplitting_calibrates_the_null_that_naive_double_dipping_inflates():
    ng = 200
    Xn, _, _, bn = simulate(n_cells=300, n_genes=ng, planted=False, seed=0)
    naive = len(naive_markers(Xn, seed=0)[0]) / ng
    csplit = len(countsplit_markers(Xn, bn, seed=0)[0]) / ng
    assert naive > csplit          # double dipping invents "markers" count-splitting does not
    assert csplit <= 0.10          # the count-split null is ~calibrated (near nominal)


def test_countsplitting_still_recovers_real_markers():
    ng = 200
    Xp, _, de, bp = simulate(n_cells=300, n_genes=ng, planted=True, n_de=30, effect=2.5, seed=0)
    sig = countsplit_markers(Xp, bp, seed=0)[0]
    assert len(sig & de) / len(de) >= 0.5     # reduced power, but recovers the real ones
