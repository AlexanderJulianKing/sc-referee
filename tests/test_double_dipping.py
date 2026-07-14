"""`double_dipping` — the STRUCTURAL detector (Phase 3, design doc §9.4).

Reviewed by GPT-5.5 Pro (2026-07-08): the blocker must be structural and its claim must be about
CALIBRATION ("the reported p-values are not valid for post-clustering inference"), never about
truth ("the markers are false"). A count-split recompute is a separate NON-blocking diagnostic and
is deferred. These tests pin the structural detector and its specificity scoping.
"""
import pandas as pd

from sc_referee import statuses as S
from tests.factories import make_design, paired_count_bundle


def _marker_bundle(de=("rank_genes_groups",), cluster=("leiden",), safeguards=(), pvalues=True):
    b = paired_count_bundle(n_donors=4)
    b.code_signals = {"de_calls": list(de), "cluster_calls": list(cluster),
                      "da_calls": [], "safeguards": list(safeguards), "imports": []}
    b.reported_results = (
        pd.DataFrame({"feature_id": ["g0", "g1"], "pvalue": [1e-5, 1e-4], "padj": [1e-3, 1e-2]})
        if pvalues else pd.DataFrame({"feature_id": ["g0", "g1"], "score": [3.1, 2.4]}))
    return b


def test_cluster_then_marker_test_caps_at_needs_evidence_in_phase_a():
    """Phase A provenance is MAY-level, so it must ESCALATE, never accuse: a confirmed de-novo-cluster
    marker test is `needs_evidence`, not `blocker`. A blocker awaits the deferred must/overlap machinery
    (adversarial code-review finding 1). The claim is still about calibration, never truth."""
    from sc_referee.checks.double_dipping import DoubleDippingCheck

    b = _marker_bundle()
    d = make_design(analysis_type="marker_detection", unit_of_test="cell")
    chk = DoubleDippingCheck()

    assert chk.applies_to(d, b) is True
    f = chk.run(d, b, b.reported_results)
    assert f.status == S.NEEDS_EVIDENCE
    assert f.status != S.BLOCKER
    assert "are false" not in f.verdict.lower()


def test_may_level_dependence_never_reaches_blocker():
    """adversarial-review finding 1: obs['G'] = np.where(X>0, genotype, genotype) reads X syntactically but G *is*
    genotype. A may-level read must never produce a blocker even when confirmed."""
    from sc_referee.checks.double_dipping import DoubleDippingCheck
    b = _marker_bundle(cluster=())
    b.code_signals["sources"] = [
        "import numpy as np\n"
        "adata.obs['G'] = np.where(adata.X[:, 0] > 0, adata.obs['genotype'], adata.obs['genotype'])\n"
        "sc.tl.rank_genes_groups(adata, groupby='G')\n"]
    d = make_design(analysis_type="marker_detection", unit_of_test="cell")
    assert DoubleDippingCheck().run(d, b, b.reported_results).status != S.BLOCKER


def test_incidental_clustering_with_predefined_grouping_is_vetoed():
    """adversarial-review finding 1: clustering for a UMAP + a marker test on a PREDEFINED column is not
    double-dipping. A provably-predefined tested grouping vetoes the incidental clustering hit."""
    from sc_referee.checks.double_dipping import DoubleDippingCheck
    b = _marker_bundle(cluster=("leiden",))
    b.code_signals["sources"] = [
        "sc.tl.leiden(adata)                      # for the UMAP only\n"
        "sc.tl.rank_genes_groups(adata, groupby='genotype')\n"]
    d = make_design(analysis_type="marker_detection", unit_of_test="cell")
    assert DoubleDippingCheck().applies_to(d, b) is False


def test_scanpy_pvalue_columns_count_as_calibrated_claims():
    """adversarial-review finding 2: scanpy names its p-value columns pvals / pvals_adj — omitting them (and
    case-sensitivity) exonerates a real circular Scanpy analysis as 'descriptive'."""
    import pandas as pd
    from sc_referee.checks.double_dipping import _claims_calibrated_pvalues
    for col in ("pvals", "pvals_adj", "PValue", "qval", "FDR",
                "p_val", "p_val_adj", "adj.P.Val"):        # + Seurat / limma names (re-review #4)
        assert _claims_calibrated_pvalues(pd.DataFrame({col: [0.01]})) is True


def test_a_documented_safeguard_is_review_not_pass():
    """A safeguard KEYWORD (count-split / held-out / ClusterDE) is evidence for review, not a
    sanitizer: it does not prove the safeguard is correctly applied — naive row-splitting can remain
    anti-conservative (Chen & Witten 2023). So it is `needs_evidence` (verify the contract), never a
    clean `pass`. Not accused (no blocker) — but not cleared either. (spec rev. 5 §5)"""
    from sc_referee.checks.double_dipping import DoubleDippingCheck

    b = _marker_bundle(safeguards=("countsplit",))
    d = make_design(analysis_type="marker_detection", unit_of_test="cell")
    f = DoubleDippingCheck().run(d, b, b.reported_results)
    assert f.status == S.NEEDS_EVIDENCE
    assert (f.coverage, S.human_state(f)) == (S.NOT_RUN, S.NOT_CHECKED)
    assert any(w in f.verdict.lower() for w in ("verify", "contract", "not proof", "correctly applied"))


def test_applies_to_custom_clustering_via_provenance():
    """Audit path: a bespoke clustering method (no vocab token) feeding a marker test still triggers
    the check, via Layer-2 provenance — the audit path must not be fooled by the method name either."""
    from sc_referee.checks.double_dipping import DoubleDippingCheck

    b = _marker_bundle(cluster=())                       # NO recognized cluster token
    b.code_signals["sources"] = [
        "labels = discover_subpops(adata.obsm['X_pca'])\n"
        "adata.obs['subpop'] = labels\n"
        "sc.tl.rank_genes_groups(adata, groupby='subpop')\n"]
    d = make_design(analysis_type="marker_detection", unit_of_test="cell")
    assert DoubleDippingCheck().applies_to(d, b) is True


def test_applies_to_false_for_predefined_grouping():
    """Specificity: provenance must not over-trigger — a marker test on a predefined column, with no
    clustering, is not this check's business."""
    from sc_referee.checks.double_dipping import DoubleDippingCheck

    b = _marker_bundle(cluster=())
    b.code_signals["sources"] = ["sc.tl.rank_genes_groups(adata, groupby='genotype')\n"]
    d = make_design(analysis_type="marker_detection", unit_of_test="cell")
    assert DoubleDippingCheck().applies_to(d, b) is False


def test_descriptive_rankings_without_pvalues_do_not_block():
    """No calibrated p-values claimed → not a post-clustering-inference blocker (GPT-5.5 Pro §Q5)."""
    from sc_referee.checks.double_dipping import DoubleDippingCheck

    b = _marker_bundle(pvalues=False)
    d = make_design(analysis_type="marker_detection", unit_of_test="cell")
    finding = DoubleDippingCheck().run(d, b, b.reported_results)
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.INFORMATIONAL, S.COMPLETE, S.CLEAR
    )


def test_all_null_conventional_pvalue_column_is_descriptive_not_inferential():
    from sc_referee.checks.double_dipping import DoubleDippingCheck

    bundle = _marker_bundle()
    bundle.reported_results = pd.DataFrame({
        "feature_id": ["g0", "g1"], "pvalue": [None, float("nan")], "score": [3.1, 2.4],
    })
    finding = DoubleDippingCheck().run(
        make_design(analysis_type="marker_detection", unit_of_test="cell"),
        bundle,
        bundle.reported_results,
    )
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.INFORMATIONAL, S.COMPLETE, S.CLEAR
    )


def test_nothing_blocks_before_a_human_confirms():
    from sc_referee.checks.double_dipping import DoubleDippingCheck

    b = _marker_bundle()
    d = make_design(analysis_type="marker_detection", unit_of_test="cell", confirmed=False)
    assert DoubleDippingCheck().run(d, b, b.reported_results).status == S.NEEDS_EVIDENCE


def test_predefined_group_DE_is_not_double_dipping():
    """A condition contrast on predefined groups (donor/genotype/treatment) is not our business."""
    from sc_referee.checks.double_dipping import DoubleDippingCheck

    b = _marker_bundle(cluster=())
    d = make_design(analysis_type="condition_contrast_DE", unit_of_test="cell")
    assert DoubleDippingCheck().applies_to(d, b) is False


def test_marker_detection_without_a_clustering_call_does_not_fire():
    """Pre-defined marker genes inspected, no de-novo clustering → not double-dipping."""
    from sc_referee.checks.double_dipping import DoubleDippingCheck

    b = _marker_bundle(cluster=())
    d = make_design(analysis_type="marker_detection", unit_of_test="cell")
    assert DoubleDippingCheck().applies_to(d, b) is False


def test_cannot_evaluate_when_the_unit_is_unresolved():
    from sc_referee.checks.double_dipping import DoubleDippingCheck

    b = _marker_bundle()
    d = make_design(analysis_type="marker_detection", unit_of_test=None)
    assert DoubleDippingCheck().cannot_evaluate(d, b)


def test_reachable_from_the_registry_and_carries_a_citation():
    from sc_referee.citations import CITATIONS
    from sc_referee.registry import build_checks

    assert "double_dipping" in {c.id for c in build_checks("pydeseq2")}
    assert CITATIONS.get("double_dipping")


def test_its_block_entitlement_is_blocker():
    from sc_referee.checks.double_dipping import DoubleDippingCheck

    assert DoubleDippingCheck().max_status == S.BLOCKER
