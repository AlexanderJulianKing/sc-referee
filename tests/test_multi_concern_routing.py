"""One workflow can exhibit multiple independent concerns; routing follows proved structure."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import anndata as ad
import numpy as np
import pandas as pd
import pytest
import yaml

from sc_referee.audit import run_audit
from sc_referee.checks.double_dipping import DoubleDippingCheck
from sc_referee.checks.experimental_unit import ExperimentalUnitCheck
from sc_referee.checks.pairing import PairingCheck
from sc_referee.code_signals import parse_code_signals
from tests.factories import make_design
from tests.inference._serialization import public_bytes


SOURCE = """\
import scanpy as sc
from sklearn.mixture import GaussianMixture
labels = GaussianMixture(2).fit_predict(adata.X)
adata.obs['gmm'] = labels
sc.tl.rank_genes_groups(adata, groupby='gmm', method='wilcoxon')
"""
ORACLES = Path(__file__).parent / "frozen_oracles" / "multi_concern_routing_oracles.json"


def _cluster_de_folder(folder, analysis_type, normalized=False):
    donors = [f"D{i}" for i in range(1, 5) for _ in range(4)]
    groups = [value for _ in range(4) for value in ("0", "0", "1", "1")]
    counts = np.tile(np.array([
        [10, 4, 2], [9, 5, 2], [2, 4, 10], [3, 5, 9],
    ], dtype=int), (4, 1))
    # A normalized matrix has no raw counts to aggregate — the pseudoreplication recompute
    # needs raw ints, so the count-dependent cross-route must abstain (not apply) on it.
    matrix = np.log1p(counts.astype(float)) if normalized else counts
    ad.AnnData(
        X=matrix,
        obs=pd.DataFrame({"donor_id": donors, "gmm": groups},
                         index=[f"c{i}" for i in range(len(donors))]),
        var=pd.DataFrame(index=["g0", "g1", "g2"]),
    ).write_h5ad(folder / "data.h5ad")
    (folder / "analysis.py").write_text(SOURCE)
    pd.DataFrame({
        "gene": ["g0", "g1", "g2"],
        "pvalue": [1e-8, 0.02, 1e-8],
        "padj": [1e-7, 0.03, 1e-7],
        "logfc": [2.0, 0.1, -2.0],
    }).to_csv(folder / "markers.csv", index=False)
    config = {
        "analysis_type": analysis_type,
        "confirmed_by_human": True,
        "design": {"condition": "gmm", "replicate_unit": ["donor_id"], "batch": []},
        "contrasts": [{
            "name": "gmm_1_vs_0", "reference": "0", "test": "1",
            "replicate_unit": ["donor_id"],
            "sample_unit": ["donor_id", "gmm"],
            "pairing_unit": [],
            "model": "~ gmm", "target_coefficient": "gmm[T.1]",
        }],
        "reported_results": {"path": "markers.csv", "unit_of_test": "cell"},
        "confidence": {"replicate_unit": "high", "condition": "high"},
    }
    (folder / "sc-referee.yaml").write_text(yaml.safe_dump(config, sort_keys=False))


@pytest.mark.parametrize("analysis_type", ["marker_detection", "condition_contrast_DE"])
def test_cluster_then_cell_de_routes_all_three_independent_concerns(tmp_path, analysis_type):
    """The label may differ, but the same proved structure must expose all three invariants."""
    _cluster_de_folder(tmp_path, analysis_type)

    result = run_audit(tmp_path, engine="simple")
    by_id = {finding.check_id: finding for finding in result.findings}

    assert by_id["double_dipping"].status == "needs_evidence"
    assert "experimental_unit" in by_id
    assert by_id["pairing"].status == "needs_evidence"
    assert "paired" in by_id["pairing"].verdict.lower()

    frozen = json.loads(ORACLES.read_text())["fixtures"][analysis_type]["new_findings"]
    for check_id in ("double_dipping", "experimental_unit", "pairing"):
        assert public_bytes(by_id[check_id]).decode() == frozen[check_id]


def _bundle(tmp_path, source, observations, reported=True):
    (tmp_path / "analysis.py").write_text(source)
    return SimpleNamespace(
        code_signals=parse_code_signals(tmp_path),
        observations=observations,
        reported_results=(pd.DataFrame({"feature_id": ["g0"], "pvalue": [0.01]})
                          if reported else None),
    )


def test_condition_de_does_not_cross_route_double_dipping_for_predefined_grouping(tmp_path):
    source = """\
import scanpy as sc
sc.tl.leiden(adata, key_added='incidental_qc_cluster')
sc.tl.rank_genes_groups(adata, groupby='condition', method='wilcoxon')
"""
    obs = pd.DataFrame({
        "donor_id": ["D1", "D1", "D2", "D2"],
        "condition": ["ctrl", "stim", "ctrl", "stim"],
    })
    bundle = _bundle(tmp_path, source, obs)
    design = make_design(analysis_type="condition_contrast_DE", unit_of_test="cell")

    assert DoubleDippingCheck().applies_to(design, bundle) is False


def test_condition_de_inference_cross_route_requires_a_nonempty_report_claim(tmp_path):
    from sc_referee.inference.live import build_engine_verifiers

    obs = pd.DataFrame({
        "donor_id": ["D1", "D1", "D2", "D2"],
        "gmm": ["0", "1", "0", "1"],
    })
    bundle = _bundle(tmp_path, SOURCE, obs)
    bundle.reported_results = pd.DataFrame(columns=["feature_id", "pvalue"])
    design = make_design(
        analysis_type="condition_contrast_DE", condition="gmm", reference="0", test="1",
        unit_of_test="cell", sample_unit=("donor_id", "gmm"), pairing_unit=(),
    )
    verifier = next(check for check in build_engine_verifiers() if check.id == "double_dipping")

    assert verifier.applies_to(design, bundle) is False


@pytest.mark.parametrize("why", [
    "between_replicates", "unconfirmed", "sample_sink", "no_report", "empty_report", "normalized",
])
def test_marker_does_not_cross_route_unit_checks_without_every_structural_fact(tmp_path, why):
    source = SOURCE
    obs = pd.DataFrame({
        "donor_id": ["D1", "D1", "D2", "D2"],
        "gmm": ["0", "0", "1", "1"] if why == "between_replicates" else ["0", "1", "0", "1"],
    })
    if why == "sample_sink":
        source = "from pydeseq2.dds import DeseqDataSet\ndds = DeseqDataSet(counts=pb, metadata=m)\n"
    bundle = _bundle(tmp_path, source, obs, reported=why != "no_report")
    if why == "empty_report":
        bundle.reported_results = pd.DataFrame(columns=["feature_id", "pvalue"])
    if why == "normalized":
        # raw counts are a precondition of the pseudobulk recompute; a normalized matrix must
        # not cross-route (else evaluate reaches aggregate_to_pseudobulk(None) and leaks an error).
        bundle.measure = SimpleNamespace(kind="normalized", counts=None)
    design = make_design(
        analysis_type="marker_detection", condition="gmm", reference="0", test="1",
        unit_of_test="cell", sample_unit=("donor_id", "gmm"), pairing_unit=(),
        confirmed=why != "unconfirmed",
    )

    assert ExperimentalUnitCheck(engine="simple").applies_to(design, bundle) is False
    assert PairingCheck().applies_to(design, bundle) is False


def test_normalized_marker_keeps_primary_signal_without_leaking_recompute_error(tmp_path):
    """End-to-end: a normalized marker bundle abstains by NOT applying the count-dependent
    checks — double_dipping still carries the signal — instead of leaking an internal recompute
    error (aggregate_to_pseudobulk on absent raw counts) into a finding."""
    _cluster_de_folder(tmp_path, "marker_detection", normalized=True)

    result = run_audit(tmp_path, engine="simple")
    by_id = {finding.check_id: finding for finding in result.findings}

    assert by_id["double_dipping"].status == "needs_evidence"
    for finding in result.findings:
        assert "could not be completed" not in finding.verdict
        assert "IndexError" not in finding.verdict
