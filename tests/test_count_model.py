"""`count_model` — the measured frontier failure.

gpt-5.5 aggregated raw counts to donor level CORRECTLY, then ran OLS on log2(CPM+1) with a
t-test — "not a count-based method" — and reported 2,352 up / 732 down. The unit was right; the
model was wrong. sc-referee was blind to this until now.

Detection needs `code_signals`: from the data alone, a correct NB analysis and a t-test on
log-CPM are indistinguishable. With no code in the folder we return `needs_evidence`, never `pass`.
"""
import numpy as np
import pandas as pd
import pytest
from dataclasses import replace

from sc_referee import statuses as S
from sc_referee.checks.count_model import CountModelCheck, evaluate_count_model
from sc_referee.design import ReportInferenceContract
from tests.factories import make_design, paired_count_bundle

pytest.importorskip("pydeseq2")
pytestmark = pytest.mark.filterwarnings("ignore")


def _bundle_with_code(de_calls):
    b = paired_count_bundle(n_donors=6)
    b.code_signals = {"imports": ["scipy"], "de_calls": list(de_calls), "cluster_calls": [], "da_calls": []}
    return b


def _reported(bundle, sig_genes):
    genes = list(bundle.measure.feature_index)
    return pd.DataFrame({
        "feature_id": genes,
        "pvalue": [1e-6 if g in sig_genes else 0.5 for g in genes],
        "padj": [1e-4 if g in sig_genes else 0.6 for g in genes],
        "effect": [2.0 if g in sig_genes else 0.0 for g in genes],
    })


DESIGN = make_design(sample_unit=("donor_id", "condition"), pairing_unit=("donor_id",),
                     unit_of_test="sample")


def _report_contract(response_scale="raw_counts", method_family="gaussian",
                     dependence_semantics="iid_rows"):
    return ReportInferenceContract(
        producer_binding="exact", response_scale=response_scale,
        method_family=method_family, dependence_semantics=dependence_semantics,
    )


def test_count_method_name_without_exact_producer_binding_is_not_checked():
    b = _bundle_with_code(["pydeseq2", "deseqdataset"])
    f = evaluate_count_model(DESIGN, b, _reported(b, {"G_up"}))
    assert (f.status, f.coverage, S.human_state(f)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_exact_bound_count_producer_passes_with_narrow_voice():
    b = _bundle_with_code(["pydeseq2", "deseqdataset"])
    design = replace(
        DESIGN,
        report_inference_contract=_report_contract(method_family="negative_binomial"),
    )
    f = evaluate_count_model(design, b, _reported(b, {"G_up"}))
    assert f.status == S.PASS, f.verdict
    assert "bound report producer" in f.verdict.lower()


def test_valid_transformed_gaussian_analysis_abstains():
    b = _bundle_with_code(["ttest_ind"])
    design = make_design(
        sample_unit=("donor_id", "condition"), pairing_unit=("donor_id",),
        unit_of_test="sample",
        report_inference_contract=_report_contract(response_scale="transformed_continuous"),
    )
    f = evaluate_count_model(design, b, _reported(b, {"G_up"}), engine="simple")
    assert (f.status, f.coverage, S.human_state(f)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_bound_raw_count_gaussian_incompatibility_retains_major():
    b = _bundle_with_code(["ttest_ind"])
    design = make_design(
        sample_unit=("donor_id", "condition"), pairing_unit=("donor_id",),
        unit_of_test="sample", report_inference_contract=_report_contract(),
    )
    f = evaluate_count_model(design, b, _reported(b, {"G_up"}), engine="simple")
    assert f.status == S.MAJOR, f.verdict
    assert f.metrics["non_count_tests"] == ["ttest_ind"]
    assert f.judgment == S.CONCERN
    assert "bound" in f.verdict.lower() and "raw count" in f.verdict.lower()


def _extra_aggregation_key_case(*, null_batch):
    bundle = _bundle_with_code(["ttest_ind"])
    donor_number = bundle.observations["donor_id"].str.removeprefix("D").astype(int)
    bundle.observations["condition"] = np.where(donor_number % 2, "ctrl", "stim")
    bundle.observations["batch"] = "B" + donor_number.astype(str)
    if null_batch:
        bundle.observations.loc[bundle.observations.index[0], "batch"] = None
    design = make_design(
        sample_unit=("donor_id",), aggregation_key=("donor_id", "batch"),
        batch=("batch",), pairing_unit=(), unit_of_test="sample",
        report_inference_contract=_report_contract(),
    )
    return bundle, design


def test_null_in_extra_ratified_aggregation_key_abstains_before_recompute(monkeypatch):
    bundle, design = _extra_aggregation_key_case(null_batch=True)

    def recompute_must_not_run(*args, **kwargs):
        raise AssertionError("null-key guard must precede pseudobulk recomputation")

    monkeypatch.setattr(
        "sc_referee.checks.count_model.aggregate_to_pseudobulk", recompute_must_not_run
    )
    finding = evaluate_count_model(design, bundle, _reported(bundle, {"G_up"}))

    assert finding.status == S.NOT_AUDITED
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == S.NOT_CHECKED
    assert finding.metrics["machine_reason"] == "invalid_aggregation_key_value"
    assert finding.metrics["null_key_columns"] == ["batch"]


def test_well_formed_extra_ratified_aggregation_key_retains_major_verdict():
    bundle, design = _extra_aggregation_key_case(null_batch=False)

    finding = evaluate_count_model(
        design, bundle, _reported(bundle, {"G_up"}), engine="simple"
    )

    assert finding.status == S.MAJOR, finding.verdict
    assert finding.judgment == S.CONCERN


def test_wilcoxon_on_pseudobulk_is_flagged():
    b = _bundle_with_code(["mannwhitneyu"])
    design = make_design(
        sample_unit=("donor_id", "condition"), pairing_unit=("donor_id",),
        unit_of_test="sample",
        report_inference_contract=_report_contract(method_family="rank_based"),
    )
    f = evaluate_count_model(design, b, _reported(b, {"G_up"}), engine="simple")
    assert f.status == S.MAJOR, f.verdict


def test_it_reports_what_the_count_model_would_have_found():
    b = _bundle_with_code(["ttest_ind"])
    design = make_design(
        sample_unit=("donor_id", "condition"), pairing_unit=("donor_id",),
        unit_of_test="sample", report_inference_contract=_report_contract(),
    )
    f = evaluate_count_model(design, b, _reported(b, {"G_up"}), engine="simple")
    m = f.metrics
    assert m["claimed"] == 1
    assert m["nb_significant"] >= 1          # the NB recompute finds the real effect
    assert "survivors" in m and "missed_by_you" in m


def test_absent_code_means_needs_evidence_never_pass():
    """From the data alone we cannot tell an NB fit from a t-test on log-CPM. Say so."""
    b = paired_count_bundle(n_donors=6)
    b.code_signals = {}
    f = evaluate_count_model(DESIGN, b, _reported(b, {"G_up"}))
    assert f.status == S.NEEDS_EVIDENCE
    assert S.human_state(f) == "not_checked"
    assert f.coverage == S.NOT_RUN
    assert "code" in f.verdict.lower()


def test_missing_report_and_unidentified_model_are_not_checked_coverage_gaps():
    b = _bundle_with_code([])

    missing_report = evaluate_count_model(DESIGN, b, None)
    unidentified = evaluate_count_model(DESIGN, b, _reported(b, {"G_up"}))

    assert [(f.status, f.coverage, S.human_state(f)) for f in (missing_report, unidentified)] == [
        (S.NEEDS_EVIDENCE, S.NOT_RUN, "not_checked"),
        (S.NEEDS_EVIDENCE, S.NOT_RUN, "not_checked"),
    ]


def test_it_never_blocks():
    """A t-test on log-CPM is suboptimal, not un-fixable. Advisory only, by construction."""
    b = _bundle_with_code(["ttest_ind"])
    design = make_design(
        sample_unit=("donor_id", "condition"), pairing_unit=("donor_id",),
        unit_of_test="sample", report_inference_contract=_report_contract(),
    )
    f = evaluate_count_model(
        design, b, _reported(b, set(b.measure.feature_index)), engine="simple"
    )
    assert f.status != S.BLOCKER


def test_does_not_apply_to_a_cell_level_analysis():
    """That is pseudoreplication — experimental_unit's territory, not ours."""
    b = _bundle_with_code(["ttest_ind"])
    check = CountModelCheck()
    assert check.applies_to(make_design(unit_of_test="sample"), b) is True
    assert check.applies_to(make_design(unit_of_test="cell"), b) is False


def test_does_not_apply_to_proportions():
    b = _bundle_with_code(["ttest_ind"])
    b.measure.kind = "proportions"
    assert CountModelCheck().applies_to(make_design(unit_of_test="sample"), b) is False


def test_carries_real_citations():
    b = _bundle_with_code(["ttest_ind"])
    design = make_design(
        sample_unit=("donor_id", "condition"), pairing_unit=("donor_id",),
        unit_of_test="sample", report_inference_contract=_report_contract(),
    )
    f = evaluate_count_model(design, b, _reported(b, {"G_up"}), engine="simple")
    assert any("Love" in c for c in f.citations)


def test_code_mentioning_both_a_count_model_and_a_t_test_is_ambiguous():
    """A stray `import pydeseq2` must not launder a t-test into a pass. (adversarial review 2026-07-08.)"""
    b = _bundle_with_code(["pydeseq2", "ttest_ind"])
    f = evaluate_count_model(DESIGN, b, _reported(b, {"G_up"}))
    assert f.status == S.NEEDS_EVIDENCE, f.verdict
    assert f.coverage == S.NOT_RUN
    assert S.human_state(f) == "not_checked"
    assert "which produced" in f.verdict and "pydeseq2" in f.verdict and "ttest_ind" in f.verdict
