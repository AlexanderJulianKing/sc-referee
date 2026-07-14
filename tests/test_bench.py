"""The benchmark harness: does it reproduce Squair 2021, and does sc-referee score correctly?

Fast parameters here (few genes/cells) — the headline number lives in bench/metrics.json,
produced by `bench/run_benchmark.py --seeds 20` and guarded by bench/expected_metrics.json.
"""
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from bench.analyses import (
    bench_design,
    bundle_from,
    hits,
    per_cell_wilcoxon,
    prf,
    reported_pseudobulk_ttest,
)
from bench.muscat_sim import simulate
from sc_referee.checks.experimental_unit import evaluate_experimental_unit
from sc_referee.engine import aggregate_to_pseudobulk
from sc_referee.design import ReportInferenceContract

pytest.importorskip("pydeseq2")
pytestmark = pytest.mark.filterwarnings("ignore")

FAST = dict(n_genes=400, cells_per_donor=60, frac_DE=0.05, donor_dispersion=0.30)


def _bound_iid_cell(design):
    return replace(design, unit_of_test="cell", report_inference_contract=ReportInferenceContract(
        producer_binding="exact", response_scale="transformed_continuous",
        method_family="rank_based", dependence_semantics="iid_rows",
    ))


@pytest.fixture(scope="module")
def sim():
    """One dataset + its recompute, shared across tests (pydeseq2 is the slow part)."""
    from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute

    adata = simulate(n_donors=6, seed=0, **FAST)
    bundle, design = bundle_from(adata), bench_design()
    pb, meta = aggregate_to_pseudobulk(bundle, design)
    res = pydeseq2_recompute(pb, meta, design)
    return adata, bundle, design, res


def test_simulator_plants_a_known_truth():
    adata = simulate(n_donors=4, seed=1, **FAST)
    truth = adata.uns["true_DE"]
    assert truth.sum() == int(round(FAST["frac_DE"] * FAST["n_genes"]))
    assert adata.X.dtype == np.int32 and adata.X.min() >= 0     # raw counts
    assert set(adata.obs["condition"]) == {"ctrl", "stim"}
    # donors are UNPAIRED (nested within condition) — load-bearing for the phenomenon
    per_donor_conds = adata.obs.groupby("donor_id", observed=True)["condition"].nunique()
    assert (per_donor_conds == 1).all()


def test_percell_inflates_false_positives_and_pseudobulk_does_not(sim):
    """The Squair 2021 result, reproduced: cells-as-replicates destroys precision."""
    adata, _, _, res = sim
    truth = adata.uns["true_DE"]

    percell = prf(hits(per_cell_wilcoxon(adata)["padj"].to_numpy()), truth)
    pseudobulk = prf(hits(res.table["padj"].to_numpy(), res.table["testable"].to_numpy()), truth)

    assert percell["fp"] > 5 * pseudobulk["fp"]           # the inflation is real
    assert pseudobulk["precision"] > 3 * percell["precision"]
    assert pseudobulk["precision"] > 0.70                 # and the recompute is RIGHT, not just smaller


def test_pseudoreplicated_analysis_is_never_green_lit(sim):
    adata, bundle, design, res = sim
    f = evaluate_experimental_unit(
        _bound_iid_cell(design), bundle, per_cell_wilcoxon(adata), "pydeseq2", recompute=res
    )
    assert f.status != "pass"
    assert f.status in ("blocker", "major", "needs_evidence")


def test_correct_analysis_is_never_accused(sim):
    """Specificity — the metric that matters most. A referee that cries wolf is worse than none.

    The correct-unit arm is an INDEPENDENT replicate-aware estimator (pseudobulk + Welch t on
    log2CPM + BH), not the recompute echoed back. Echoing made `survival_rate == 1.0` an identity
    and specificity a tautology. Here survival is a real number that could be low — and isn't.
    """
    adata, bundle, design, res = sim
    from sc_referee.engine import aggregate_to_pseudobulk
    pb, meta = aggregate_to_pseudobulk(bundle, design)
    reported = reported_pseudobulk_ttest(pb, meta, design)

    f = evaluate_experimental_unit(design, bundle, reported, "pydeseq2", recompute=res)
    assert f.status not in ("blocker", "major"), f.verdict
    assert 0.0 <= f.metrics["survival_rate"] <= 1.0


def test_injected_recompute_matches_a_fresh_one(sim):
    """The benchmark injects one recompute for both audits; it must be identical to recomputing."""
    adata, bundle, design, res = sim
    reported = per_cell_wilcoxon(adata)
    bound = _bound_iid_cell(design)
    injected = evaluate_experimental_unit(bound, bundle, reported, "pydeseq2", recompute=res)
    fresh = evaluate_experimental_unit(bound, bundle, reported, "pydeseq2")
    assert injected.status == fresh.status
    assert injected.metrics["survival_rate"] == pytest.approx(fresh.metrics["survival_rate"])
    assert injected.metrics["valid_reported_sig"] == fresh.metrics["valid_reported_sig"]


def test_committed_benchmark_meets_its_floors():
    """Guards the recorded headline number against regression."""
    root = Path(__file__).resolve().parents[1] / "bench"
    committed = json.loads((root / "metrics.json").read_text())
    metrics, by_n = committed["overall"], committed["by_n_donors"]
    spec = json.loads((root / "expected_metrics.json").read_text())

    for key, floor in spec["floors"].items():
        assert metrics[key] >= floor, f"{key}={metrics[key]:.3f} below floor {floor}"
    for key, ceil in spec["ceilings"].items():
        assert metrics[key] <= ceil, f"{key}={metrics[key]:.3f} above ceiling {ceil}"
    for key, want in spec["invariants"].items():
        if not key.startswith("_"):
            assert metrics[key] == want, f"{key}={metrics[key]!r}, expected {want!r}"

    cal = spec["calibration"]
    assert by_n["3"]["abstain_rate"] >= cal["abstain_rate_min_at_n3"]   # abstains when underpowered
    for n in ("4", "6", "8", "12"):
        assert by_n[n]["blocker_rate"] >= cal["blocker_rate_min_at_n4_plus"]  # blocks when powered

    # The correct-unit arm earns its pass only where there is power to earn it. Under the old
    # echoed-recompute arm this was pinned at 1.00 for every n. Variation == a real measurement.
    assert by_n["3"]["good_pass_rate"] <= cal["good_pass_rate_max_at_n3"]
    for n in ("6", "8", "12"):
        assert by_n[n]["good_pass_rate"] >= cal["good_pass_rate_min_at_n6_plus"]


def test_the_committed_specificity_number_is_not_an_identity():
    """`specificity: 1.000` is only meaningful if it COULD have been lower. It could: the
    correct-unit arm's survival is not pinned at 1.0, and its pass rate climbs with n.
    If someone reverts the arm to `reported_from_recompute`, this test is the tripwire."""
    root = Path(__file__).resolve().parents[1] / "bench"
    committed = json.loads((root / "metrics.json").read_text())
    assert committed["overall"]["good_survival_is_degenerate"] is False
    by_n = committed["by_n_donors"]
    assert by_n["3"]["good_pass_rate"] < by_n["12"]["good_pass_rate"]
