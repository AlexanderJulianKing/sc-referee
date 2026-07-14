"""The schema contracts: a confirmed config and a rendered report must validate; a
malformed config must be rejected (by validate() directly and by load_designs)."""
import json

import jsonschema
import pytest
import yaml

from fixtures.confounding_alias.make_fixture import build
from sc_referee.audit import run_audit
from sc_referee.config import load_designs
from sc_referee.report import to_json
from sc_referee.schema_validation import validate


def test_fixture_config_validates(tmp_path):
    build(tmp_path)
    raw = yaml.safe_load((tmp_path / "sc-referee.yaml").read_text())
    validate(raw, "sc_referee.schema.json")  # must not raise


def test_config_missing_contrasts_is_rejected(tmp_path):
    build(tmp_path)
    bad = yaml.safe_load((tmp_path / "sc-referee.yaml").read_text())
    del bad["contrasts"]
    with pytest.raises(jsonschema.ValidationError):
        validate(bad, "sc_referee.schema.json")


def test_report_json_validates(tmp_path):
    build(tmp_path)
    report = json.loads(to_json(run_audit(tmp_path)))
    validate(report, "report.schema.json")


def test_report_json_is_strict_valid(tmp_path):
    """A blocker carries vif=inf; Python would emit bare `Infinity`, which is invalid JSON
    and breaks jq / the GitHub Action artifact / any non-Python consumer."""
    build(tmp_path)
    text = to_json(run_audit(tmp_path))

    def reject(const):
        raise ValueError(f"non-finite JSON constant emitted: {const}")

    json.loads(text, parse_constant=reject)  # must not raise


def test_load_designs_rejects_unknown_analysis_type(tmp_path):
    build(tmp_path)
    path = tmp_path / "sc-referee.yaml"
    raw = yaml.safe_load(path.read_text())
    raw["analysis_type"] = "nonsense_type"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError):
        load_designs(path)


def test_eqtl_config_without_two_level_condition_validates_and_loads(tmp_path):
    cfg = {
        "analysis_type": "eqtl",
        "confirmed_by_human": True,
        "design": {"replicate_unit": ["donor_id"], "batch": []},
        "contrasts": [{
            "name": "rs1_target", "sample_unit": ["donor_id"], "variant_id": "rs1",
            "genotype_column": "dosage", "target_feature": "TARGET", "effect_allele": "A",
            "dosage_counts_allele": "A", "variant_alleles": ["A", "G"], "dosage_ploidy": 2,
            "eqtl_estimator": "ols", "eqtl_outcome_scale": "log2_cpm_plus_1",
        }],
        "confidence": {"replicate_unit": "high", "allele_orientation": "high"},
    }
    validate(cfg, "sc_referee.schema.json")
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(cfg))
    (design,) = load_designs(path)
    assert design.analysis_type == "eqtl" and design.genotype_column == "dosage"


def test_non_eqtl_config_still_requires_condition_and_two_levels():
    cfg = {
        "analysis_type": "condition_contrast_DE",
        "design": {"replicate_unit": ["donor_id"]},
        "contrasts": [{"name": "broken", "sample_unit": ["donor_id"]}],
    }
    with pytest.raises(jsonschema.ValidationError):
        validate(cfg, "sc_referee.schema.json")


def test_effect_relevance_contract_validates_and_loads(tmp_path):
    cfg = {
        "analysis_type": "condition_contrast_DE", "confirmed_by_human": True,
        "design": {"condition": "condition", "replicate_unit": ["donor_id"], "batch": []},
        "contrasts": [{
            "name": "stim_vs_ctrl", "reference": "ctrl", "test": "stim",
            "sample_unit": ["donor_id", "condition"],
            "effect_relevance_contract": {
                "claim_type": "biologically_relevant_discovery", "threshold": 0.25,
                "threshold_scale": "log2_fold_change",
                "reported_effect_scale": "log2_fold_change",
            },
        }],
    }
    validate(cfg, "sc_referee.schema.json")
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(cfg))
    (design,) = load_designs(path)
    assert design.effect_relevance_contract.threshold == 0.25


def test_effect_relevance_contract_schema_rejects_open_scale():
    cfg = {
        "analysis_type": "condition_contrast_DE",
        "design": {"condition": "condition", "replicate_unit": ["donor_id"]},
        "contrasts": [{
            "name": "stim_vs_ctrl", "reference": "ctrl", "test": "stim",
            "sample_unit": ["donor_id", "condition"],
            "effect_relevance_contract": {
                "claim_type": "biologically_relevant_discovery", "threshold": 0.25,
                "threshold_scale": "mystery_scale", "reported_effect_scale": "mystery_scale",
            },
        }],
    }
    with pytest.raises(jsonschema.ValidationError):
        validate(cfg, "sc_referee.schema.json")


def test_multiplicity_contract_validates_and_loads(tmp_path):
    cfg = {
        "analysis_type": "condition_contrast_DE", "confirmed_by_human": True,
        "design": {"condition": "condition", "replicate_unit": ["donor_id"], "batch": []},
        "contrasts": [{
            "name": "stim_vs_ctrl", "reference": "ctrl", "test": "stim",
            "sample_unit": ["donor_id", "condition"],
            "multiplicity_contract": {
                "claim_type": "error_controlled_discovery", "error_criterion": "fdr",
                "adjustment_method": "benjamini_hochberg", "family_complete": True,
            },
        }],
    }
    validate(cfg, "sc_referee.schema.json")
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(cfg))
    (design,) = load_designs(path)
    assert design.multiplicity_contract.adjustment_method == "benjamini_hochberg"


def test_report_inference_contract_validates_and_loads(tmp_path):
    cfg = {
        "analysis_type": "condition_contrast_DE", "confirmed_by_human": True,
        "design": {"condition": "condition", "replicate_unit": ["donor_id"], "batch": []},
        "contrasts": [{
            "name": "stim_vs_ctrl", "reference": "ctrl", "test": "stim",
            "sample_unit": ["donor_id", "condition"],
            "report_inference_contract": {
                "producer_binding": "exact", "response_scale": "raw_counts",
                "method_family": "gaussian", "dependence_semantics": "iid_rows",
            },
        }],
    }
    validate(cfg, "sc_referee.schema.json")
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(cfg))
    (design,) = load_designs(path)
    assert design.report_inference_contract.response_scale == "raw_counts"


def test_pairing_mechanics_validates_and_loads(tmp_path):
    cfg = {
        "analysis_type": "condition_contrast_DE", "confirmed_by_human": True,
        "design": {"condition": "condition", "replicate_unit": ["donor_id"], "batch": []},
        "contrasts": [{
            "name": "stim_vs_ctrl", "reference": "ctrl", "test": "stim",
            "sample_unit": ["donor_id", "condition"], "pairing_unit": ["donor_id"],
            "pairing_estimand": "within_pair", "pairing_mechanics": "one_to_one",
        }],
    }
    validate(cfg, "sc_referee.schema.json")
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(cfg))
    (design,) = load_designs(path)
    assert design.pairing_mechanics == "one_to_one"


def test_hic_loop_strength_contract_validates_and_loads(tmp_path):
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
        }],
        "confidence": {"replicate_unit": "high", "hic_loop_strength": "high"},
    }
    validate(cfg, "sc_referee.schema.json")
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(cfg))

    (design,) = load_designs(path)
    assert design.analysis_type == "hic_loop_strength"
    assert design.hic_target_bin_i == "b20" and design.hic_target_bin_j == "b25"
    assert design.hic_report_delta_tolerance == 1e-6
