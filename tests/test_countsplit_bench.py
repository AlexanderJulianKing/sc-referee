"""Smoke-test count splitting and guard the independent-family calibration estimator.

One simulated dataset is only a deterministic algorithm smoke test. The benchmark's calibration
claim comes from ``evaluate_many`` over unique independent dataset seeds.
"""
import pytest

pytest.importorskip("sklearn")
pytestmark = pytest.mark.filterwarnings("ignore")

from bench.countsplit_bench import countsplit_markers, evaluate_many, naive_markers, simulate


def test_countsplitting_single_dataset_smoke_separates_from_double_dipping():
    ng = 200
    Xn, _, _, bn = simulate(n_cells=300, n_genes=ng, planted=False, seed=0)
    naive = len(naive_markers(Xn, seed=0)[0]) / ng
    csplit = len(countsplit_markers(Xn, bn, seed=0)[0]) / ng
    assert naive > csplit          # double dipping invents "markers" count-splitting does not
    assert csplit <= 0.10          # one-realization sanity ceiling, not a calibration estimate


def test_countsplitting_calibration_aggregates_independent_null_families():
    rows = {
        10: (True, False),
        11: (True, True),
        12: (False, False),
        13: (True, False),
    }

    def fake_evaluate(*, seed, **_kwargs):
        naive, split = rows[seed]
        return {
            "naive_null_any": naive,
            "countsplit_null_any": split,
            "countsplit_recall": 0.5,
            "countsplit_fp_rate": 0.01,
        }

    result = evaluate_many(rows, evaluator=fake_evaluate)
    assert result["n_null_families"] == 4
    assert result["naive_null_family_error"] == 0.75
    assert result["countsplit_null_family_error"] == 0.25
    assert result["countsplit_null_family_error"] != 1 / (4 * 400)
    low, high = result["countsplit_null_family_error_ci95"]
    assert 0 <= low < 0.25 < high <= 1


def test_countsplitting_calibration_rejects_duplicate_or_empty_seeds():
    with pytest.raises(ValueError, match="unique"):
        evaluate_many([0, 0])
    with pytest.raises(ValueError, match="at least one"):
        evaluate_many([])


def test_countsplitting_still_recovers_real_markers():
    ng = 200
    Xp, _, de, bp = simulate(n_cells=300, n_genes=ng, planted=True, n_de=30, effect=2.5, seed=0)
    sig = countsplit_markers(Xp, bp, seed=0)[0]
    assert len(sig & de) / len(de) >= 0.5     # reduced power, but recovers the real ones
