"""Allele-orientation eQTL check: contract gates, specificity, abstention, and blockers."""
from __future__ import annotations

import pytest
import yaml

from sc_referee import statuses as S
from tests.factories import eqtl_count_bundle, make_eqtl_design


def _reported(bundle, effect):
    import pandas as pd

    bundle.reported_results = pd.DataFrame({
        "feature_id": ["TARGET"], "pvalue": [0.001], "padj": [0.01], "effect": [effect],
    })
    return bundle


def test_eqtl_contract_schema_and_config_round_trip(tmp_path):
    from sc_referee.config import load_designs

    cfg = {
        "analysis_type": "eqtl",
        "confirmed_by_human": True,
        "design": {"replicate_unit": ["donor_id"], "batch": []},
        "contrasts": [{
            "name": "rs1_CXCL10",
            "sample_unit": ["donor_id"],
            "variant_id": "rs1",
            "genotype_column": "rs1_dosage",
            "target_feature": "CXCL10",
            "effect_allele": "A",
            "dosage_counts_allele": "A",
            "variant_alleles": ["A", "G"],
            "dosage_ploidy": 2,
            "effect_allele_frequency_interval": [0.30, 0.40],
            "effect_allele_frequency_scope": "audited_donors",
            "eqtl_estimator": "ols",
            "eqtl_outcome_scale": "log2_cpm_plus_1",
        }],
        "confidence": {"replicate_unit": "high", "allele_orientation": "high"},
    }
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(cfg))

    (design,) = load_designs(path)
    assert design.analysis_type == "eqtl"
    assert design.condition is None and design.reference is None and design.test is None
    assert design.variant_id == "rs1"
    assert design.genotype_column == "rs1_dosage"
    assert design.target_feature == "CXCL10"
    assert design.effect_allele == "A"
    assert design.dosage_counts_allele == "A"
    assert design.variant_alleles == ("A", "G")
    assert design.dosage_ploidy == 2
    assert design.effect_allele_frequency_interval == (0.30, 0.40)
    assert design.effect_allele_frequency_scope == "audited_donors"
    assert design.eqtl_estimator == "ols"
    assert design.eqtl_outcome_scale == "log2_cpm_plus_1"


def test_check_is_blocker_entitled_but_still_self_gates():
    from sc_referee.checks.allele_orientation import AlleleOrientationCheck

    assert AlleleOrientationCheck.max_status == S.BLOCKER


def test_missing_eqtl_contract_facts_remain_schema_valid(tmp_path):
    from sc_referee.config import load_designs

    cfg = {
        "analysis_type": "eqtl",
        "confirmed_by_human": False,
        "design": {"replicate_unit": ["donor_id"], "batch": []},
        "contrasts": [{"name": "unresolved_eqtl", "sample_unit": ["donor_id"]}],
        "confidence": {},
    }
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(cfg))
    (design,) = load_designs(path)
    assert design.effect_allele is None
    assert design.genotype_column is None


def test_correct_identity_is_proved_conformant():
    from sc_referee.checks.allele_orientation import evaluate_allele_orientation

    bundle = _reported(eqtl_count_bundle(effect_direction=1, seed=0), effect=0.5)
    finding = evaluate_allele_orientation(make_eqtl_design(), bundle, bundle.reported_results)
    assert finding.status == S.PASS
    assert finding.metrics["reported_sign"] == finding.metrics["recomputed_sign"] == 1


def test_correct_complement_is_proved_conformant_never_false_accused():
    from sc_referee.checks.allele_orientation import evaluate_allele_orientation

    bundle = _reported(eqtl_count_bundle(effect_direction=-1, seed=4), effect=0.5)
    design = make_eqtl_design(effect_allele="A", dosage_counts_allele="G")
    finding = evaluate_allele_orientation(design, bundle, bundle.reported_results)
    assert finding.status == S.PASS
    assert finding.metrics["transform"] == "complement"
    assert finding.metrics["reported_sign"] == finding.metrics["recomputed_sign"] == 1


def test_frequency_resolved_correct_is_proved_conformant():
    from sc_referee.checks.allele_orientation import evaluate_allele_orientation

    bundle = _reported(
        eqtl_count_bundle(class_counts=(3, 3, 6), effect_direction=-1, seed=6), effect=0.4)
    design = make_eqtl_design(
        dosage_counts_allele=None,
        effect_allele_frequency_interval=(0.35, 0.40),
        effect_allele_frequency_scope="audited_donors",
    )
    finding = evaluate_allele_orientation(design, bundle, bundle.reported_results)
    assert finding.status == S.PASS
    assert finding.metrics["orientation_source"] == "exact_cohort_frequency"
    assert finding.metrics["transform"] == "complement"


def test_external_panel_frequency_difference_never_blocks():
    from sc_referee.checks.allele_orientation import evaluate_allele_orientation

    bundle = _reported(
        eqtl_count_bundle(class_counts=(3, 3, 6), effect_direction=-1, seed=8), effect=0.4)
    design = make_eqtl_design(
        dosage_counts_allele=None,
        effect_allele_frequency_interval=(0.35, 0.40),
        effect_allele_frequency_scope="external_panel",
    )
    finding = evaluate_allele_orientation(design, bundle, bundle.reported_results)
    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.status != S.BLOCKER


def _evaluate(design=None, bundle=None, effect=0.5):
    from sc_referee.checks.allele_orientation import evaluate_allele_orientation

    design = design or make_eqtl_design()
    bundle = bundle or eqtl_count_bundle(seed=2)
    if bundle.reported_results is None:
        _reported(bundle, effect)
    return evaluate_allele_orientation(design, bundle, bundle.reported_results)


def test_unratified_effect_allele_is_needs_evidence():
    finding = _evaluate(make_eqtl_design(effect_allele=None))
    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == "not_checked"
    assert "effect_allele" in finding.metrics["unresolved_contract"]


def test_unratified_verdict_names_the_specific_effect():
    """The catch must be explicit about WHICH effect it won't certify — the target feature and the
    reported value — not a generic 'the effect'."""
    finding = _evaluate(make_eqtl_design(effect_allele=None), effect=0.5)
    assert finding.status == S.NEEDS_EVIDENCE
    assert "TARGET" in finding.verdict         # the specific gene, named
    assert "rs1" in finding.verdict            # the specific variant, named


def test_no_orientation_footprint_is_needs_evidence():
    finding = _evaluate(make_eqtl_design(dosage_counts_allele=None))
    assert finding.status == S.NEEDS_EVIDENCE
    assert "orientation_footprint" in finding.metrics["unresolved_contract"]


def test_conflicting_direct_and_frequency_footprints_are_needs_evidence():
    bundle = eqtl_count_bundle(class_counts=(3, 3, 6), effect_direction=1, seed=1)
    design = make_eqtl_design(
        dosage_counts_allele="A",  # identity
        effect_allele_frequency_interval=(0.35, 0.40),  # p_raw=.625 -> complement
        effect_allele_frequency_scope="audited_donors",
    )
    finding = _evaluate(design, bundle)
    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == "not_checked"
    assert finding.metrics["orientation_reason"] == "orientation_footprints_conflict"


def test_frequency_near_half_is_ambiguous_needs_evidence():
    bundle = eqtl_count_bundle(class_counts=(3, 6, 3), effect_direction=1, seed=3)
    design = make_eqtl_design(
        dosage_counts_allele=None,
        effect_allele_frequency_interval=(0.45, 0.55),
        effect_allele_frequency_scope="audited_donors",
    )
    finding = _evaluate(design, bundle)
    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == "not_checked"
    assert finding.metrics["orientation_reason"] == "frequency_orientation_ambiguous"


@pytest.mark.parametrize("class_counts", [(6, 0, 0), (2, 2, 2)])
def test_one_class_or_fewer_than_three_per_class_is_not_audited(class_counts):
    finding = _evaluate(bundle=eqtl_count_bundle(class_counts=class_counts, seed=5))
    assert finding.status == S.NOT_AUDITED


def test_near_zero_association_is_not_audited():
    bundle = eqtl_count_bundle(class_counts=(8, 8, 8), effect_strength=0, seed=21)
    finding = _evaluate(bundle=bundle)
    assert finding.status == S.NOT_AUDITED


def test_monomorphic_target_is_not_audited():
    bundle = eqtl_count_bundle(seed=9)
    bundle.measure.counts[:, 0] = 0
    finding = _evaluate(bundle=bundle)
    assert finding.status == S.NOT_AUDITED


def test_nonconstant_donor_genotype_is_not_audited():
    bundle = eqtl_count_bundle(seed=5)
    bundle.observations.iloc[0, bundle.observations.columns.get_loc("dosage")] = 2
    finding = _evaluate(bundle=bundle)
    assert finding.status == S.NOT_AUDITED


def test_missing_report_row_is_not_audited():
    import pandas as pd

    bundle = eqtl_count_bundle(seed=2)
    bundle.reported_results = pd.DataFrame({
        "feature_id": ["OTHER"], "pvalue": [0.1], "padj": [0.2], "effect": [0.5]})
    finding = _evaluate(bundle=bundle)
    assert finding.status == S.NOT_AUDITED


def test_duplicate_report_rows_are_not_audited():
    import pandas as pd

    bundle = eqtl_count_bundle(seed=2)
    bundle.reported_results = pd.DataFrame({
        "feature_id": ["TARGET", "TARGET"], "pvalue": [0.1, 0.2], "padj": [0.2, 0.3],
        "effect": [0.5, -0.5]})
    finding = _evaluate(bundle=bundle)
    assert finding.status == S.NOT_AUDITED


@pytest.mark.parametrize("effect", [0.0, float("nan"), float("inf")])
def test_zero_or_nonfinite_reported_effect_is_not_audited(effect):
    finding = _evaluate(effect=effect)
    assert finding.status == S.NOT_AUDITED


def test_normalized_only_bundle_is_not_audited():
    from sc_referee.bundle import Measure

    bundle = eqtl_count_bundle(seed=2)
    bundle.measure = Measure("normalized", None, None, list(bundle.measure.feature_index))
    finding = _evaluate(bundle=bundle)
    assert finding.status == S.NOT_AUDITED


@pytest.mark.parametrize(
    "estimator,outcome",
    [("negative_binomial", "ambient_corrected_counts"),
     ("ols_adjusted", "log2_cpm_plus_1"),
     ("mixed", "log2_cpm_plus_1")],
)
def test_unsupported_nb_or_covariate_model_is_not_audited(estimator, outcome):
    finding = _evaluate(make_eqtl_design(eqtl_estimator=estimator, eqtl_outcome_scale=outcome))
    assert finding.status == S.NOT_AUDITED


def test_ols_formula_with_covariate_is_not_estimator_equivalent():
    finding = _evaluate(make_eqtl_design(model="~ dosage + batch"))
    assert finding.status == S.NOT_AUDITED


def test_gb_p07_shaped_unratified_nb_claim_is_needs_evidence_not_a_violation():
    design = make_eqtl_design(
        dosage_counts_allele=None, eqtl_estimator="negative_binomial",
        eqtl_outcome_scale="ambient_corrected_counts")
    finding = _evaluate(design)
    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.status != S.BLOCKER


def test_gb_p07_shaped_ratified_nb_claim_is_not_audited_never_blocked():
    design = make_eqtl_design(
        eqtl_estimator="negative_binomial", eqtl_outcome_scale="ambient_corrected_counts")
    finding = _evaluate(design)
    assert finding.status == S.NOT_AUDITED
    assert finding.status != S.BLOCKER


def test_conflicting_footprints_precede_unsupported_estimator():
    bundle = eqtl_count_bundle(class_counts=(3, 3, 6), effect_direction=1, seed=15)
    design = make_eqtl_design(
        dosage_counts_allele="A",
        effect_allele_frequency_interval=(0.35, 0.40),
        effect_allele_frequency_scope="audited_donors",
        eqtl_estimator="negative_binomial", eqtl_outcome_scale="ambient_corrected_counts",
    )
    finding = _evaluate(design, bundle)
    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.metrics["orientation_reason"] == "orientation_footprints_conflict"


def test_low_confidence_agreement_without_entitlement_is_not_checked():
    finding = _evaluate(make_eqtl_design(allele_orientation_confidence_high=False))
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_low_replicate_confidence_agreement_without_entitlement_is_not_checked():
    finding = _evaluate(make_eqtl_design(confidence_high=False))
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_low_confidence_disagreement_is_needs_evidence_never_blocker():
    finding = _evaluate(make_eqtl_design(allele_orientation_confidence_high=False), effect=-0.5)
    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.status != S.BLOCKER
    assert (finding.coverage, S.human_state(finding)) == (S.NOT_RUN, S.NOT_CHECKED)


def test_unconfirmed_disagreement_is_needs_evidence_never_blocker():
    finding = _evaluate(make_eqtl_design(confirmed=False), effect=-0.5)
    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.status != S.BLOCKER
    assert (finding.coverage, S.human_state(finding)) == (S.NOT_RUN, S.NOT_CHECKED)


def test_reported_sign_flip_under_identity_contract_is_a_blocker():
    bundle = eqtl_count_bundle(effect_direction=1, seed=10)
    finding = _evaluate(make_eqtl_design(), bundle, effect=-0.5)
    assert finding.status == S.BLOCKER
    assert finding.judgment == S.VIOLATION
    assert finding.metrics["reported_sign"] == -finding.metrics["recomputed_sign"]
    assert finding.metrics["transform"] == "identity"
    assert "effect-allele orientation" in finding.verdict.lower()
    assert finding.metrics["magnitude_reproduced"] is False


def test_label_flip_with_direct_footprint_is_a_blocker():
    # Stored dosage counts G and expression rises with raw G dosage. Per A dosage (2-g), the correct
    # sign is negative; retaining the raw positive sign is the orientation error.
    bundle = eqtl_count_bundle(effect_direction=1, seed=12)
    design = make_eqtl_design(effect_allele="A", dosage_counts_allele="G")
    finding = _evaluate(design, bundle, effect=0.5)
    assert finding.status == S.BLOCKER
    assert finding.metrics["reported_sign"] == -finding.metrics["recomputed_sign"]
    assert finding.metrics["transform"] == "complement"
    assert finding.metrics["orientation_source"] == "direct"


def test_label_flip_with_frequency_footprint_is_a_blocker():
    bundle = eqtl_count_bundle(class_counts=(3, 3, 6), effect_direction=1, seed=14)
    design = make_eqtl_design(
        dosage_counts_allele=None,
        effect_allele_frequency_interval=(0.35, 0.40),
        effect_allele_frequency_scope="audited_donors",
    )
    finding = _evaluate(design, bundle, effect=0.5)
    assert finding.status == S.BLOCKER
    assert finding.metrics["reported_sign"] == -finding.metrics["recomputed_sign"]
    assert finding.metrics["transform"] == "complement"
    assert finding.metrics["orientation_source"] == "exact_cohort_frequency"
