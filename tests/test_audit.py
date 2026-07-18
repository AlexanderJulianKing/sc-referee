"""The audit orchestration: folder + confirmed design -> findings -> CI conclusion."""
import pytest

from fixtures.confounding_alias.make_fixture import build
from sc_referee.audit import run_audit


def test_audit_confounding_alias_is_ci_failure(tmp_path):
    build(tmp_path)
    result = run_audit(tmp_path)

    blockers = [f for f in result.findings if f.status == "blocker"]
    assert any(f.check_id == "confounding" for f in blockers)
    assert result.ci_fails() is True
    assert result.worst_status() == "blocker"


def test_audit_returns_a_finding_per_applicable_check(tmp_path):
    build(tmp_path)
    result = run_audit(tmp_path)
    ids = {f.check_id for f in result.findings}
    # experimental_unit does NOT fire: the fixture reports at the sample level
    # (unit_of_test: sample), so there is no pseudoreplication to correct.
    assert "experimental_unit" not in ids
    assert ids == {"confounding", "confounding_strong", "multiple_testing", "count_model", "effect_size_threshold", "pairing"}
    strong = next(f for f in result.findings if f.check_id == "confounding_strong")
    from sc_referee import statuses as S
    assert strong.status == S.NOT_AUDITED
    assert S.human_state(strong) == S.NOT_CHECKED


def test_registry_carries_the_built_checks():
    from sc_referee.registry import build_checks
    assert {c.id for c in build_checks()} == {
        "confounding", "confounding_strong", "confounding_random_intercept",
        "confounding_random_intercept_conditional", "experimental_unit", "multiple_testing", "count_model", "double_dipping",
        "contamination_confound",
        "effect_size_threshold", "pseudobulk_integrity", "pairing", "allele_orientation",
        "hic_loop_strength", "eqtl_design_support", "inference.allele_harmonization",
        "inference.enrichment_universe", "inference.coordinate_consumption",
        "inference.spatial_iid", "inference.trajectory_circularity",
        "inference.confounding",
        "inference.pseudoreplication"}


def test_check_programming_error_is_not_swallowed_as_user_data():
    from sc_referee.audit import _safe_run
    from tests.factories import make_design, paired_count_bundle

    class BrokenCheck:
        id = "broken"
        max_status = "blocker"

        def run(self, design, bundle, reported):
            raise RuntimeError("implementation defect")

    with pytest.raises(RuntimeError, match="implementation defect"):
        _safe_run(BrokenCheck(), make_design(), paired_count_bundle(), None)


def test_cli_schema_invalid_config_exits_2_without_report(tmp_path):
    from typer.testing import CliRunner
    from sc_referee.cli import app

    build(tmp_path)
    (tmp_path / "sc-referee.yaml").write_text("analysis_type: condition_contrast_DE\n")
    output = tmp_path / "report.md"
    result = CliRunner().invoke(
        app, ["audit", str(tmp_path), "--engine", "simple", "--md", str(output)])
    assert result.exit_code == 2
    assert "config error" in result.stdout.lower() and "traceback" not in result.stdout.lower()
    assert not output.exists()


def test_confounding_strong_is_additive_not_a_replacement():
    from sc_referee import statuses as S
    from sc_referee.registry import build_checks
    checks = {check.id: check for check in build_checks("simple")}
    assert "confounding" in checks and "confounding_strong" in checks
    assert checks["confounding"] is not checks["confounding_strong"]
    assert checks["confounding_strong"].audit_dimensions == ("conditioning_set",)
    assert checks["confounding_strong"].max_status == S.MAJOR


def test_random_intercept_stage1_is_additive_and_cannot_escalate_to_major():
    from sc_referee import statuses as S
    from sc_referee.registry import build_checks
    checks = {check.id: check for check in build_checks()}
    assert {"confounding", "confounding_strong", "confounding_random_intercept"} <= checks.keys()
    assert checks["confounding_random_intercept"] is not checks["confounding_strong"]
    assert checks["confounding_random_intercept"].audit_dimensions == ("conditioning_set",)
    assert checks["confounding_random_intercept"].max_status == S.NEEDS_EVIDENCE
    assert checks["confounding_random_intercept_conditional"].max_status == S.MAJOR
    assert checks["confounding_random_intercept_conditional"].audit_dimensions == (
        "conditioning_set",
    )


def test_count_model_says_it_cannot_tell_rather_than_passing(tmp_path):
    """The fixture ships no analysis code. Absence of evidence is not a clean bill."""
    build(tmp_path)
    cm = next(f for f in run_audit(tmp_path).findings if f.check_id == "count_model")
    assert cm.status == "needs_evidence"
    assert "code" in cm.verdict.lower()


def _write_eqtl_audit_fixture(tmp_path, *, estimator="ols", outcome="log2_cpm_plus_1"):
    import pandas as pd
    import yaml

    from tests.factories import eqtl_count_bundle

    bundle = eqtl_count_bundle(effect_direction=1, seed=17)
    counts = pd.DataFrame(bundle.measure.counts, index=bundle.observations.index,
                          columns=bundle.measure.feature_index)
    counts.index.name = "cell_id"
    counts.to_csv(tmp_path / "counts.csv")
    obs = bundle.observations.copy()
    obs.index.name = "cell_id"
    obs.to_csv(tmp_path / "obs.csv")
    pd.DataFrame({
        "gene": ["TARGET"], "pvalue": [0.001], "padj": [0.01], "log2fc": [0.5],
    }).to_csv(tmp_path / "eqtl_results.csv", index=False)
    cfg = {
        "analysis_type": "eqtl", "confirmed_by_human": True,
        "design": {"replicate_unit": ["donor_id"], "batch": []},
        "contrasts": [{
            "name": "rs1_TARGET", "sample_unit": ["donor_id"], "variant_id": "rs1",
            "genotype_column": "dosage", "target_feature": "TARGET", "effect_allele": "A",
            "dosage_counts_allele": "A", "variant_alleles": ["A", "G"], "dosage_ploidy": 2,
            "eqtl_estimator": estimator, "eqtl_outcome_scale": outcome,
        }],
        "confidence": {"replicate_unit": "high", "allele_orientation": "high"},
    }
    (tmp_path / "sc-referee.yaml").write_text(yaml.safe_dump(cfg))


def test_eqtl_audit_routes_the_orientation_check_end_to_end(tmp_path):
    from sc_referee import statuses as S

    _write_eqtl_audit_fixture(tmp_path)

    result = run_audit(tmp_path, engine="simple")
    assert [(f.check_id, f.status) for f in result.findings] == [
        ("allele_orientation", S.PASS),
        ("eqtl_design_support", S.PASS),   # donor/genotype structure certified alongside the sign
    ]
    assert result.fully_audited() is True  # single-source eQTL is outside the joint-policy scope


def test_eqtl_not_audited_keeps_the_checks_diagnostic_metrics(tmp_path):
    from sc_referee import statuses as S

    _write_eqtl_audit_fixture(
        tmp_path, estimator="negative_binomial", outcome="ambient_corrected_counts")
    result = run_audit(tmp_path, engine="simple")
    (finding,) = [f for f in result.findings if f.check_id == "allele_orientation"]

    assert finding.status == S.NOT_AUDITED
    assert finding.metrics["estimator"] == "negative_binomial"
    assert finding.metrics["outcome_scale"] == "ambient_corrected_counts"
    assert result.fully_audited() is False


def test_hic_audit_uses_parallel_adapter_and_returns_rich_finding(tmp_path):
    import yaml

    from sc_referee import statuses as S
    from tests.factories import hic_contact_bundle

    source = hic_contact_bundle(seed=97)
    source.hic.contacts.to_csv(tmp_path / "hic_contacts.csv", index=False)
    source.hic.bins.to_csv(tmp_path / "hic_bins.csv", index=False)
    source.reported_results.to_csv(tmp_path / "hic_report.csv", index=False)
    cfg = {
        "analysis_type": "hic_loop_strength", "confirmed_by_human": True,
        "design": {"condition": "condition", "replicate_unit": ["replicate"], "batch": []},
        "contrasts": [{
            "name": "loop_stim_vs_ctrl", "reference": "ctrl", "test": "stim",
            "replicate_unit": ["replicate"], "sample_unit": ["replicate", "condition"],
            "pairing_unit": [], "hic_genome_assembly": "hg38", "hic_resolution_bp": 10000,
            "hic_target_bin_i": "b20", "hic_target_bin_j": "b25",
            "hic_background_view_start": 0, "hic_background_view_end": 640000,
            "hic_contact_scale": "raw_unbalanced_integer_counts",
            "hic_expected_model": "cis_exact_distance_arithmetic_mean_target_excluded_v1",
            "hic_mask_policy": "exclude_if_either_bin_masked_v1",
            "hic_zero_policy": "dense_including_zeros", "hic_pseudocount": 0,
            "hic_target_statistic": "single_pixel",
            "hic_replicate_functional": "equal_weight_mean_log2_oe_v1",
            "hic_report_delta_tolerance": 1e-6,
            "hic_report_delta_tolerance_authority":
                "rounding_absolute_log2_ratio_delta",
        }],
        "confidence": {"replicate_unit": "high", "hic_loop_strength": "high"},
    }
    (tmp_path / "sc-referee.yaml").write_text(yaml.safe_dump(cfg))

    result = run_audit(tmp_path, engine="simple")

    assert [(f.check_id, f.status) for f in result.findings] == [("hic_loop_strength", S.PASS)]
    assert result.findings[0].metrics["recomputed_delta"] == 1.0
