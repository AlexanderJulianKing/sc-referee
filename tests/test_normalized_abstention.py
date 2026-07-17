"""Item 2: per-check abstention on normalized data (replaces the global ingest refusal).

A normalized matrix must not throw away the WHOLE audit. `confounding` (reads only `.obs`) and
`multiple_testing` (reads only the reported table) can still run and catch real problems; only the
COUNT-dependent recomputes (`experimental_unit`, `count_model`) must abstain. Ingest succeeds and
flags `measure.kind = "normalized"`; the count checks return `not_audited` ("raw counts required"),
never a silent pass and never a crash. (Alex, 2026-07-08 — the global refusal was too blunt.)
"""
import anndata as ad
import numpy as np
import pandas as pd
import pytest
import yaml

from sc_referee import statuses as S


def _normalized_h5ad(path):
    rng = np.random.default_rng(0)
    n_cells, n_genes = 16, 6
    X = np.log1p(rng.poisson(6, size=(n_cells, n_genes)).astype(float))  # non-integer => "normalized"
    obs = pd.DataFrame({"donor_id": [f"D{i % 8}" for i in range(n_cells)],
                        "condition": ["ctrl"] * 8 + ["stim"] * 8},
                       index=[f"c{i}" for i in range(n_cells)])
    var = pd.DataFrame(index=[f"g{j}" for j in range(n_genes)])
    ad.AnnData(X=X, obs=obs, var=var).write_h5ad(path)
    return path


def test_read_anndata_ingests_normalized_without_refusing(tmp_path):
    from sc_referee.adapters.anndata_adapter import read_anndata

    b = read_anndata(_normalized_h5ad(tmp_path / "n.h5ad"))
    assert b.measure.kind == "normalized"     # flagged, not refused
    assert b.measure.counts is None           # we hold no raw counts to recompute from
    assert b.replicate_var == "donor_id"      # .obs still fully usable


def test_experimental_unit_abstains_on_normalized(tmp_path):
    from sc_referee.adapters.anndata_adapter import read_anndata
    from sc_referee.checks.experimental_unit import ExperimentalUnitCheck
    from tests.factories import make_design

    b = read_anndata(_normalized_h5ad(tmp_path / "n.h5ad"))
    reason = ExperimentalUnitCheck().cannot_evaluate(make_design(unit_of_test="cell"), b)
    assert reason and "raw" in reason.lower() and "count" in reason.lower()


def test_count_model_abstains_on_normalized(tmp_path):
    from sc_referee.adapters.anndata_adapter import read_anndata
    from sc_referee.checks.count_model import CountModelCheck
    from tests.factories import make_design

    b = read_anndata(_normalized_h5ad(tmp_path / "n.h5ad"))
    reason = CountModelCheck().cannot_evaluate(make_design(unit_of_test="sample"), b)
    assert reason and "raw" in reason.lower() and "count" in reason.lower()


def test_normalized_run_audits_confounding_but_abstains_the_recompute(tmp_path):
    """The whole point: a normalized matrix is NOT a global refusal. confounding still runs; the
    replicate-aware recompute abstains; the overall conclusion is neutral (never a silent pass)."""
    from sc_referee.audit import run_audit

    _normalized_h5ad(tmp_path / "n.h5ad")
    cfg = {"analysis_type": "condition_contrast_DE", "confirmed_by_human": True,
           "design": {"replicate_unit": ["donor_id"], "condition": "condition", "batch": []},
           "confidence": {"replicate_unit": "high", "condition": "high"},
           "reported_results": {"unit_of_test": "cell"},
           "contrasts": [{"name": "stim_vs_ctrl", "reference": "ctrl", "test": "stim",
                          "replicate_unit": ["donor_id"], "sample_unit": ["donor_id", "condition"],
                          "pairing_unit": [], "model": "~ condition",
                          "target_coefficient": "condition[T.stim]"}]}
    (tmp_path / "sc-referee.yaml").write_text(yaml.safe_dump(cfg))

    result = run_audit(tmp_path, tmp_path / "sc-referee.yaml")
    by_id = {f.check_id: f for f in result.findings}

    assert "confounding" in by_id and by_id["confounding"].status != S.NOT_AUDITED   # it still ran
    assert by_id["experimental_unit"].status == S.NOT_AUDITED                        # abstained, not silent
    assert result.ci_conclusion() == "fail"                                          # never a false green
    assert result.fully_audited() is False
