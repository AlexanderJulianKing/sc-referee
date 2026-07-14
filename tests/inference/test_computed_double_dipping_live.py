from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from sc_referee import statuses as S
from sc_referee.inference.double_dipping import (
    DOUBLE_DIPPING_PREMISES,
    compute_double_dipping_evidence,
)
from sc_referee.inference.live import build_engine_verifiers


PBMC_DEX_SOURCE = """
from sklearn.mixture import GaussianMixture
import scanpy as sc
adata = sc.read_h5ad('confounding_alias.h5ad')
labels = GaussianMixture(n_components=4).fit_predict(adata.obsm['X_pca'])
adata.obs['gmm'] = labels
sc.tl.rank_genes_groups(adata, groupby='gmm', method='wilcoxon')
markers = sc.get.rank_genes_groups_df(adata, group=None)
markers.to_csv('results/de.csv', index=False)
"""


def _reported():
    return pd.DataFrame({
        "feature_id": ["IL7R", "NKG7"],
        "pvals": [0.001, 0.002],
        "pvals_adj": [0.01, 0.02],
    })


def _compute(source):
    return compute_double_dipping_evidence(
        (source,), _reported(), report_relative_path="results/de.csv",
        data_relative_path="confounding_alias.h5ad",
    )


def _check():
    return next(check for check in build_engine_verifiers()
                if check.policy_id == "double_dipping.v1")


def _run(source: str, *, confirmed: bool, reported=None):
    return _run_sources((source,), confirmed=confirmed, reported=reported)


def _run_sources(sources, *, confirmed: bool, reported=None):
    reported = _reported() if reported is None else reported
    bundle = SimpleNamespace(
        code_signals={"sources": list(sources)},
        reported_results=reported,
        _inference_live_contracts={},
        _inference_verifier_observation=SimpleNamespace(
            report_artifact_digest="sha256:measured-report",
            report_locator_digest="sha256:measured-locator",
            report_relative_path="results/de.csv",
            data_relative_path="confounding_alias.h5ad",
        ),
    )
    design = SimpleNamespace(
        analysis_type="marker_detection",
        unit_of_test="cell",
        confirmed_by_human=confirmed,
        confidence={},
        name="markers",
    )
    return _check().run(design, bundle, bundle.reported_results)


def test_pbmc_dex_six_premises_are_computed_from_code_and_whole_dag_slices():
    evidence = _compute(PBMC_DEX_SOURCE)

    assert evidence.relations == {premise: "PROVED" for premise in DOUBLE_DIPPING_PREMISES}
    assert evidence.claim_slice.unavoidable_producers == frozenset({evidence.test_producer})
    assert evidence.grouping_slice.unavoidable_producers == frozenset({evidence.selection_producer})
    assert evidence.claim_slice.coverage_complete
    assert evidence.grouping_slice.coverage_complete
    assert all(binding.module and binding.symbol and binding.version
               and binding.package_or_source_digest and binding.summary_digest
               for binding in evidence.summary_bindings)
    assert evidence.premise_sources == {
        "ClaimMustProducedByTest": "backward_must_slice:report_claim",
        "GroupingMustProducedBySelection": "backward_must_slice:grouping_field",
        "TestDefinitelyNaive": "calibration:exact_sink_summary",
        "RelevantRegionOverlapDefinite": "region:definite_feature_intersection",
        "SelectionReuseDependentUnderNull": "selection_reuse:exact_shared_expression_contract",
        "PinnedReachable": "cfg:unconditional_top_level_call",
    }


def test_a_variable_named_adata_does_not_bind_itself_to_the_measured_artifact():
    source = PBMC_DEX_SOURCE.replace(
        "adata = sc.read_h5ad('confounding_alias.h5ad')\n", ""
    )

    evidence = _compute(source)

    assert evidence.relations["GroupingMustProducedBySelection"] == "UNKNOWN"
    assert evidence.relations["ClaimMustProducedByTest"] == "UNKNOWN"


def test_monkey_patched_fit_predict_cannot_resolve_the_selection_summary():
    source = PBMC_DEX_SOURCE.replace(
        "adata = sc.read_h5ad",
        "GaussianMixture.fit_predict = forged_selection\nadata = sc.read_h5ad",
    )

    evidence = _compute(source)

    assert evidence.relations["GroupingMustProducedBySelection"] == "UNKNOWN"


def test_an_external_overwrite_of_x_pca_breaks_expression_region_proof():
    source = PBMC_DEX_SOURCE.replace(
        "labels = GaussianMixture",
        "adata.obsm['X_pca'] = external_embedding\nlabels = GaussianMixture",
    )

    evidence = _compute(source)

    assert evidence.relations["RelevantRegionOverlapDefinite"] == "UNKNOWN"


def test_independent_selection_and_test_layers_are_not_collapsed_into_shared_reuse():
    source = (PBMC_DEX_SOURCE
              .replace("adata.obsm['X_pca']", "adata.layers['selection_split']")
              .replace("groupby='gmm', method='wilcoxon'",
                       "groupby='gmm', layer='heldout_split', method='wilcoxon'"))

    evidence = _compute(source)
    finding = _run(source, confirmed=True)

    assert evidence.relations["SelectionReuseDependentUnderNull"] != "PROVED"
    assert evidence.relations["RelevantRegionOverlapDefinite"] != "PROVED"
    assert finding.status != "blocker"


def test_logreg_marker_scores_never_prove_naive_pvalue_calibration():
    source = PBMC_DEX_SOURCE.replace(
        "method='wilcoxon'", "method='logreg'",
    )

    evidence = _compute(source)
    finding = _run(source, confirmed=True)

    assert evidence.relations["TestDefinitelyNaive"] == "UNKNOWN"
    assert finding.status != "blocker"


def test_empty_or_nan_pvalue_columns_do_not_create_an_inferential_claim():
    reported = pd.DataFrame({
        "feature_id": ["IL7R", "NKG7"],
        "pvals": [float("nan"), float("nan")],
        "pvals_adj": [None, None],
    })

    evidence = compute_double_dipping_evidence(
        (PBMC_DEX_SOURCE,), reported, report_relative_path="results/de.csv",
        data_relative_path="confounding_alias.h5ad",
    )
    finding = _run(PBMC_DEX_SOURCE, confirmed=True, reported=reported)

    assert evidence.relations["ClaimMustProducedByTest"] == "UNKNOWN"
    assert "report_has_no_pvalue_claim" in evidence.unknown_reasons
    assert finding.status != "blocker"


def test_report_without_exact_feature_ids_cannot_prove_claim_overlap():
    reported = pd.DataFrame({"pvals": [0.001], "pvals_adj": [0.01]})

    evidence = compute_double_dipping_evidence(
        (PBMC_DEX_SOURCE,), reported, report_relative_path="results/de.csv",
        data_relative_path="confounding_alias.h5ad",
    )
    finding = _run(PBMC_DEX_SOURCE, confirmed=True, reported=reported)

    assert evidence.relations["ClaimMustProducedByTest"] == "UNKNOWN"
    assert finding.status != "blocker"


def test_raw_reported_features_disjoint_from_hvg_selection_do_not_overlap():
    source = (PBMC_DEX_SOURCE
              .replace("adata.obsm['X_pca']", "adata[:, ['HVG_ONLY']].X")
              .replace("groupby='gmm', method='wilcoxon'",
                       "groupby='gmm', use_raw=True, method='wilcoxon'"))

    evidence = _compute(source)
    finding = _run(source, confirmed=True)

    assert evidence.relations["RelevantRegionOverlapDefinite"] == "REFUTED"
    assert evidence.relations["SelectionReuseDependentUnderNull"] == "REFUTED"
    assert finding.status != "blocker"


def test_mismatched_scanpy_result_key_cannot_bind_report_to_the_marker_test():
    source = (PBMC_DEX_SOURCE
              .replace("groupby='gmm', method='wilcoxon'",
                       "groupby='gmm', method='wilcoxon', key_added='markers_A'")
              .replace("group=None", "group=None, key='markers_B'"))

    evidence = _compute(source)
    finding = _run(source, confirmed=True)

    assert evidence.relations["ClaimMustProducedByTest"] == "UNKNOWN"
    assert "marker_result_key_mismatch" in evidence.unknown_reasons
    assert finding.status != "blocker"


def test_mismatched_scanpy_result_group_cannot_bind_the_report_claim():
    source = (PBMC_DEX_SOURCE
              .replace("method='wilcoxon'",
                       "method='wilcoxon', groups=['A']")
              .replace("group=None", "group='B'"))

    evidence = _compute(source)
    finding = _run(source, confirmed=True)

    assert evidence.relations["ClaimMustProducedByTest"] == "UNKNOWN"
    assert "marker_result_group_mismatch" in evidence.unknown_reasons
    assert finding.status != "blocker"


def test_possible_dataframe_mutation_breaks_the_exact_report_claim_binding():
    source = PBMC_DEX_SOURCE.replace(
        "markers.to_csv", "markers['pvals'] = independently_produced\nmarkers.to_csv",
    )

    evidence = _compute(source)
    finding = _run(source, confirmed=True)

    assert evidence.relations["ClaimMustProducedByTest"] == "UNKNOWN"
    assert "possible_marker_result_mutation" in evidence.unknown_reasons
    assert finding.status != "blocker"


def test_nested_dataframe_mutation_target_also_breaks_report_binding():
    source = PBMC_DEX_SOURCE.replace(
        "markers.to_csv", "markers.loc[:, 'pvals'] = independently_produced\nmarkers.to_csv",
    )

    evidence = _compute(source)

    assert evidence.relations["ClaimMustProducedByTest"] == "UNKNOWN"
    assert "possible_marker_result_mutation" in evidence.unknown_reasons


def test_possible_dataframe_alias_mutation_breaks_report_binding():
    source = PBMC_DEX_SOURCE.replace(
        "markers.to_csv",
        "alias = markers\nalias['pvals'] = independently_produced\nmarkers.to_csv",
    )

    evidence = _compute(source)

    assert evidence.relations["ClaimMustProducedByTest"] == "UNKNOWN"
    assert "possible_marker_result_mutation" in evidence.unknown_reasons


def test_same_grouping_field_on_different_anndata_receivers_is_not_linked():
    source = """
from sklearn.mixture import GaussianMixture
import scanpy as sc
adata_A = sc.read_h5ad('confounding_alias.h5ad')
adata_B = sc.read_h5ad('confounding_alias.h5ad')
labels = GaussianMixture(4).fit_predict(adata_A.obsm['X_pca'])
adata_A.obs['g'] = labels
sc.tl.rank_genes_groups(adata_B, groupby='g', method='wilcoxon')
markers = sc.get.rank_genes_groups_df(adata_B, group=None)
markers.to_csv('results/de.csv', index=False)
"""

    evidence = _compute(source)
    finding = _run(source, confirmed=True)

    assert evidence.relations["GroupingMustProducedBySelection"] == "UNKNOWN"
    assert finding.status != "blocker"


def test_a_pvalue_table_is_not_assumed_to_come_from_the_only_marker_call():
    source_without_egress = PBMC_DEX_SOURCE.split("markers =", 1)[0]

    evidence = _compute(source_without_egress)

    assert evidence.relations["ClaimMustProducedByTest"] == "UNKNOWN"
    assert "report_has_no_exact_test_egress" in evidence.unknown_reasons


def test_a_possible_later_writer_to_the_report_path_breaks_the_claim_must_link():
    source = PBMC_DEX_SOURCE + "unrelated.to_csv('results/de.csv', index=False)\n"

    evidence = _compute(source)

    assert evidence.relations["ClaimMustProducedByTest"] == "UNKNOWN"
    assert "possible_report_overwrite" in evidence.unknown_reasons


@pytest.mark.parametrize(
    ("source", "premise"),
    (
        (
            PBMC_DEX_SOURCE.replace(
                "labels = GaussianMixture(n_components=4).fit_predict",
                "model = GaussianMixture(n_components=4)\nmodel = custom_model\n"
                "labels = model.fit_predict",
            ),
            "GroupingMustProducedBySelection",
        ),
        (
            PBMC_DEX_SOURCE.replace(
                "adata.obs['gmm'] = labels",
                "labels = adata.obs['sample']\nadata.obs['gmm'] = labels",
            ),
            "GroupingMustProducedBySelection",
        ),
        (
            PBMC_DEX_SOURCE.replace(
                "markers.to_csv",
                "markers = unrelated\nmarkers.to_csv",
            ),
            "ClaimMustProducedByTest",
        ),
    ),
)
def test_intervening_strong_overwrite_invalidates_the_must_flow(source, premise):
    evidence = _compute(source)

    assert evidence.relations[premise] == "UNKNOWN"


def test_leiden_requires_an_exact_expression_neighbors_producer_not_just_the_method_name():
    source = """
import scanpy as sc
adata = sc.read_h5ad('confounding_alias.h5ad')
adata.obsp['connectivities'] = external_graph
sc.tl.leiden(adata, key_added='g')
sc.tl.rank_genes_groups(adata, groupby='g', method='wilcoxon')
markers = sc.get.rank_genes_groups_df(adata, group=None)
markers.to_csv('results/de.csv', index=False)
"""

    evidence = _compute(source)

    assert evidence.relations["GroupingMustProducedBySelection"] == "UNKNOWN"


def test_leiden_after_exact_expression_neighbors_creates_a_must_selection_event():
    source = """
import scanpy as sc
adata = sc.read_h5ad('confounding_alias.h5ad')
sc.pp.neighbors(adata, use_rep='X_pca')
sc.tl.leiden(adata, key_added='g')
sc.tl.rank_genes_groups(adata, groupby='g', method='wilcoxon')
markers = sc.get.rank_genes_groups_df(adata, group=None)
markers.to_csv('results/de.csv', index=False)
"""

    evidence = _compute(source)

    assert evidence.relations == {premise: "PROVED" for premise in DOUBLE_DIPPING_PREMISES}


def test_pbmc_dex_rich_witness_is_capped_at_needs_evidence_even_when_confirmed():
    unconfirmed = _run(PBMC_DEX_SOURCE, confirmed=False)
    confirmed = _run(PBMC_DEX_SOURCE, confirmed=True)

    assert unconfirmed.status == "needs_evidence"
    assert confirmed.status == "needs_evidence"
    assert unconfirmed.metrics["engine_outcome"] == "VIOLATION_WITNESS"
    assert confirmed.metrics["engine_outcome"] == "VIOLATION_WITNESS"
    assert confirmed.metrics["evidence_origin"] == "parsed_source_and_measured_report"
    assert confirmed.metrics["proved_relations"] == sorted(DOUBLE_DIPPING_PREMISES)
    assert confirmed.metrics["claim_slice_unavoidable"]
    assert confirmed.metrics["grouping_slice_unavoidable"]
    assert confirmed.metrics["summary_bindings"]
    assert confirmed.metrics["test_producer"]
    assert confirmed.metrics["selection_producer"]


def test_heldout_data_preinstalled_in_raw_and_x_can_never_be_adverse():
    source = PBMC_DEX_SOURCE.replace(
        "adata.obsm['X_pca']", "adata.raw.X",
    ).replace(
        "method='wilcoxon'", "method='wilcoxon', use_raw=False",
    )

    finding = _run(source, confirmed=True)

    assert finding.status == "needs_evidence"
    assert finding.status not in {"blocker", "major"}
    assert (finding.coverage, S.human_state(finding)) == (S.NOT_RUN, S.NOT_CHECKED)


def test_pca_hvg_selection_with_disjoint_raw_claims_can_never_be_adverse():
    source = PBMC_DEX_SOURCE.replace(
        "method='wilcoxon'", "method='wilcoxon', use_raw=True",
    )

    finding = _run(source, confirmed=True)

    assert finding.status == "needs_evidence"
    assert finding.status not in {"blocker", "major"}


def test_inplace_replacement_of_selected_labels_can_never_be_adverse():
    source = PBMC_DEX_SOURCE.replace(
        "adata.obs['gmm'] = labels",
        "labels[:] = adata.obs['condition']\nadata.obs['gmm'] = labels",
    )

    finding = _run(source, confirmed=True)

    assert finding.status == "needs_evidence"
    assert finding.status not in {"blocker", "major"}


def test_cross_file_same_spelled_locals_can_never_be_adverse():
    selection_source = """
from sklearn.mixture import GaussianMixture
import scanpy as sc
adata = sc.read_h5ad('confounding_alias.h5ad')
labels = GaussianMixture(4).fit_predict(adata.X)
adata.obs['gmm'] = labels
"""
    reporting_source = """
import scanpy as sc
adata = sc.read_h5ad('confounding_alias.h5ad')
sc.tl.rank_genes_groups(adata, groupby='gmm', method='wilcoxon')
markers = sc.get.rank_genes_groups_df(adata, group=None)
markers.to_csv('results/de.csv', index=False)
"""

    finding = _run_sources((selection_source, reporting_source), confirmed=True)

    assert finding.status == "needs_evidence"
    assert finding.status not in {"blocker", "major"}


def test_engine_double_dipping_has_a_structural_nonadverse_cap_for_any_input():
    from sc_referee import statuses as S
    from sc_referee.audit import _clamp_to_entitlement
    from sc_referee.checks.base import Finding

    check = _check()
    violation = next(rule for rule in check.policy.rules
                     if rule.outcome == "VIOLATION_WITNESS")

    assert check.max_status == S.NEEDS_EVIDENCE
    assert violation.max_external_status == S.NEEDS_EVIDENCE
    forced = _clamp_to_entitlement(check, Finding(check.id, S.BLOCKER, "forced"))
    assert forced.status == S.NEEDS_EVIDENCE


@pytest.mark.parametrize(
    "source",
    (
        # Count splitting is opaque in this supported subset: honest abstention, never accusation.
        """
from sklearn.mixture import GaussianMixture
import scanpy as sc
selection_counts, heldout_counts = count_split(adata.X)
labels = GaussianMixture(3).fit_predict(selection_counts)
adata.obs['g'] = labels
sc.tl.rank_genes_groups(heldout_counts, groupby='g')
""",
        # Exact literal feature regions are disjoint.
        """
from sklearn.mixture import GaussianMixture
import scanpy as sc
labels = GaussianMixture(3).fit_predict(adata[:, ['MS4A1']].X)
adata.obs['g'] = labels
sc.tl.rank_genes_groups(adata, groupby='g', mask_var=['NKG7'])
""",
        # Spatial coordinates are external to the tested expression features.
        """
from sklearn.cluster import KMeans
import scanpy as sc
labels = KMeans(3).fit_predict(adata.obsm['spatial'])
adata.obs['region'] = labels
sc.tl.rank_genes_groups(adata, groupby='region')
""",
        # Data-independent metadata relabel.
        """
import scanpy as sc
adata.obs['ct'] = adata.obs['sample'].map({'s1': 'T', 's2': 'B'})
sc.tl.rank_genes_groups(adata, groupby='ct')
""",
        # A selection-aware test outside the exact sink registry is unknown, not naively calibrated.
        """
from tradeseq import selection_aware_test
result = selection_aware_test(adata, exclude_selection_features=True)
""",
    ),
)
def test_specificity_cases_never_produce_a_double_dipping_accusation(source):
    finding = _run(source, confirmed=True)

    assert finding.status in {"pass", "informational", "needs_evidence", "not_audited"}
    assert finding.status != "blocker"
    assert finding.metrics.get("engine_outcome") != "VIOLATION_WITNESS"


def test_unknown_or_conditional_flow_cannot_be_promoted_to_a_must_witness():
    source = """
from sklearn.cluster import KMeans
import scanpy as sc
if choose_clusters:
    adata.obs['g'] = KMeans(3).fit_predict(adata.X)
else:
    adata.obs['g'] = adata.obs['condition']
sc.tl.rank_genes_groups(adata, groupby='g')
"""

    evidence = compute_double_dipping_evidence(
        (source,), _reported(), report_relative_path="results/de.csv"
    )

    assert evidence.relations["GroupingMustProducedBySelection"] == "UNKNOWN"
    assert _run(source, confirmed=True).status != "blocker"


def test_pbmc_dex_routes_through_the_shipped_audit_with_measured_report_digests(tmp_path):
    import yaml

    from fixtures.confounding_alias.make_fixture import build
    from sc_referee.audit import run_audit

    build(tmp_path)
    config_path = tmp_path / "sc-referee.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["analysis_type"] = "marker_detection"
    config["reported_results"]["unit_of_test"] = "cell"
    config["confirmed_by_human"] = False
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    (tmp_path / "analysis.py").write_text(PBMC_DEX_SOURCE)

    unconfirmed = run_audit(tmp_path, engine="simple")
    unconfirmed_finding = next(item for item in unconfirmed.findings
                               if item.check_id == "double_dipping")
    assert unconfirmed_finding.status == "needs_evidence"
    assert unconfirmed_finding.metrics["engine_outcome"] == "VIOLATION_WITNESS"
    assert unconfirmed_finding.metrics["closed_world_complete"] is True

    config["confirmed_by_human"] = True
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    confirmed = run_audit(tmp_path, engine="simple")
    confirmed_finding = next(item for item in confirmed.findings
                             if item.check_id == "double_dipping")
    assert confirmed_finding.status == "needs_evidence"
    assert confirmed_finding.metrics["evidence_origin"] == \
        "parsed_source_and_measured_report"
