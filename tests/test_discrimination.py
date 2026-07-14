"""Guard the detector-discrimination apparatus itself.

If these break, our coverage map is lying to us — which is worse than having no coverage map.
"""
import pytest
from dataclasses import replace

from bench.analyses import bench_design, bundle_from
from bench.error_classes import (
    add_batch,
    batched_design,
    reported_clean,
    reported_pseudoreplication,
)
from bench.muscat_sim import simulate
from sc_referee.checks.confounding import evaluate_confounding
from sc_referee.checks.experimental_unit import evaluate_experimental_unit
from sc_referee.engine import aggregate_to_pseudobulk
from sc_referee.design import ReportInferenceContract

pytest.importorskip("pydeseq2")
pytestmark = pytest.mark.filterwarnings("ignore")

FAST = dict(n_donors=6, n_genes=400, cells_per_donor=60, frac_DE=0.05)
ACCUSED = ("blocker", "major")


@pytest.fixture(scope="module")
def world():
    from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute

    adata = add_batch(simulate(seed=0, **FAST), aliased=False)   # crossed batch -> estimable
    bundle, design = bundle_from(adata), batched_design(bench_design())
    pb, meta = aggregate_to_pseudobulk(bundle, design)
    return adata, bundle, design, pydeseq2_recompute(pb, meta, design)


def test_clean_analysis_is_not_accused(world):
    """Specificity of the apparatus. Without this, every 'DETECTED' below is meaningless."""
    _, bundle, design, res = world
    f = evaluate_experimental_unit(design, bundle, reported_clean(res), "pydeseq2", recompute=res)
    assert f.status not in ACCUSED, f.verdict


def test_injected_pseudoreplication_is_detected(world):
    adata, bundle, design, res = world
    bound = replace(design, unit_of_test="cell", report_inference_contract=ReportInferenceContract(
        producer_binding="exact", response_scale="transformed_continuous",
        method_family="rank_based", dependence_semantics="iid_rows",
    ))
    f = evaluate_experimental_unit(
        bound, bundle, reported_pseudoreplication(adata), "pydeseq2", recompute=res
    )
    assert f.status in ACCUSED, f.verdict


def test_injected_confounding_is_detected():
    adata = add_batch(simulate(seed=0, **FAST), aliased=True)   # run perfectly aliased with condition
    bundle, design = bundle_from(adata), batched_design(bench_design())
    f = evaluate_confounding(bundle.observations, design)
    assert f.status == "blocker", f.verdict


def test_crossed_batch_is_not_flagged_as_confounded():
    adata = add_batch(simulate(seed=0, **FAST), aliased=False)
    bundle, design = bundle_from(adata), batched_design(bench_design())
    f = evaluate_confounding(bundle.observations, design)
    assert f.status not in ACCUSED, f.verdict


def test_normalized_matrix_is_flagged_and_the_recompute_abstains():
    """The error gpt-5.4 actually made: hand the tool log-normalized values, not raw counts.
    We no longer refuse the whole run (that threw away confounding + multiple_testing, which don't
    touch the matrix). Ingest flags `measure.kind = "normalized"`, and the COUNT recomputes abstain
    (`not_audited`), never a silent pass. (Item 2, 2026-07-08.)"""
    import tempfile
    from pathlib import Path

    import anndata as ad
    import numpy as np

    from sc_referee.adapters.anndata_adapter import read_anndata
    from sc_referee.checks.experimental_unit import ExperimentalUnitCheck
    from tests.factories import make_design

    a = simulate(seed=0, **FAST)
    norm = ad.AnnData(X=np.log1p(np.asarray(a.X, dtype=float)), obs=a.obs.copy(), var=a.var.copy())
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "normalized.h5ad"
        norm.write_h5ad(p)
        b = read_anndata(p)                                  # no raise
        assert b.measure.kind == "normalized" and b.measure.counts is None
        reason = ExperimentalUnitCheck().cannot_evaluate(make_design(unit_of_test="cell"), b)
        assert reason and "raw" in reason.lower()            # abstains, loudly


def test_trajectory_policy_is_registered_but_abstains_without_a_live_contract():
    """The live trajectory policy is registered, but missing ratified evidence stays unaudited."""
    from dataclasses import replace

    from sc_referee.registry import checks_for

    unbuilt = replace(bench_design(), analysis_type="trajectory")
    checks = checks_for(unbuilt, None)
    assert [check.id for check in checks] == ["inference.trajectory_circularity"]
    assert checks[0].cannot_evaluate(unbuilt, None)


def test_double_dipping_is_now_built_and_routes_on_marker_detection():
    """The formerly-unbuilt case now has a structural detector that routes on marker_detection +
    a cell-level marker call + a clustering call."""
    from dataclasses import replace
    from types import SimpleNamespace

    from sc_referee.registry import checks_for

    marker = replace(bench_design(), analysis_type="marker_detection", unit_of_test="cell")
    bundle = SimpleNamespace(code_signals={"de_calls": ["rank_genes_groups"],
                                           "cluster_calls": ["leiden"], "safeguards": []})
    ids = {c.id for c in checks_for(marker, bundle)}
    assert "double_dipping" in ids
