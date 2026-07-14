import pytest
import pandas as pd

from sc_referee.design import (
    BatchComponentScope,
    BatchModelingDeclaration,
    EffectRelevanceContract,
    FittedDesignDeclaration,
    MultiplicityContract,
    ReportInferenceContract,
)
from tests.factories import fitted_design_declaration, make_design


def test_two_key_test_mapping_is_schema_invalid_and_typed(tmp_path):
    import yaml
    from sc_referee.config import load_designs
    from sc_referee.design import DesignError

    cfg = {"analysis_type": "condition_contrast_DE", "confirmed_by_human": False,
           "design": {"condition": "condition", "replicate_unit": [], "batch": []},
           "contrasts": [{"name": "bad", "reference": "ctrl",
                          "test": {"condition": "stim", "batch": "B2"},
                          "sample_unit": ["condition"]}]}
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(DesignError, match="schema"):
        load_designs(path)


def test_equal_reference_and_test_refuses_before_checks_run():
    from sc_referee.design import DesignError, validate_design_against

    obs = pd.DataFrame({"condition": ["ctrl", "ctrl"]})
    with pytest.raises(DesignError, match="distinct"):
        validate_design_against(obs, make_design(reference="ctrl", test="ctrl"))


def test_design_defaults_analyst_adjusted_for_to_none():
    design = make_design()
    assert design.analyst_adjusted_for is None

    captured = make_design(analyst_adjusted_for=["batch"])
    assert captured.analyst_adjusted_for == ["batch"]


def test_effect_relevance_contract_is_optional_and_scale_specific():
    assert make_design().effect_relevance_contract is None
    contract = EffectRelevanceContract(
        claim_type="biologically_relevant_discovery", threshold=0.2,
        threshold_scale="log2_fold_change", reported_effect_scale="log2_fold_change",
    )
    assert make_design(effect_relevance_contract=contract).effect_relevance_contract == contract


@pytest.mark.parametrize("threshold", [0, -0.1])
def test_effect_relevance_contract_requires_positive_threshold(threshold):
    with pytest.raises(ValueError):
        EffectRelevanceContract(
            claim_type="biologically_relevant_discovery", threshold=threshold,
            threshold_scale="log2_fold_change", reported_effect_scale="log2_fold_change",
        )


def test_multiplicity_contract_is_optional_and_closed():
    assert make_design().multiplicity_contract is None
    contract = MultiplicityContract(
        claim_type="error_controlled_discovery", error_criterion="fdr",
        adjustment_method="benjamini_hochberg", family_complete=True,
    )
    assert make_design(multiplicity_contract=contract).multiplicity_contract == contract


def test_report_inference_contract_is_optional_and_typed():
    assert make_design().report_inference_contract is None
    contract = ReportInferenceContract(
        producer_binding="exact", response_scale="raw_counts",
        method_family="gaussian", dependence_semantics="iid_rows",
    )
    assert make_design(report_inference_contract=contract).report_inference_contract == contract


def test_pairing_mechanics_is_optional_and_separate_from_estimand():
    assert make_design(pairing_estimand="within_pair").pairing_mechanics is None
    design = make_design(pairing_estimand="within_pair", pairing_mechanics="repeated_measures")
    assert design.pairing_estimand == "within_pair"
    assert design.pairing_mechanics == "repeated_measures"


def test_fitted_design_is_separate_and_unresolved_by_default():
    design = make_design(analyst_adjusted_for=["condition"])
    assert design.fitted_design is None
    assert design.confidence.get("fitted_design") != "high"


def test_fitted_design_declaration_freezes_nested_maps():
    kinds = {"condition": "categorical", "run": "categorical"}
    declaration = FittedDesignDeclaration(
        rows_exact=True,
        operator_kind="ordinary_fixed_effects",
        intercept=True,
        column_kinds=kinds,
        categorical_levels={"condition": ("ctrl", "stim"), "run": ("R1", "R2")},
        transforms={"condition": "identity", "run": "identity"},
    )
    kinds["run"] = "continuous"
    assert declaration.column_kinds["run"] == "categorical"
    with pytest.raises(TypeError):
        declaration.transforms["run"] = "spline"


def _batch_entry(**overrides):
    values = dict(
        source_column="run",
        modeled_as="random_intercept",
        random_group_column="run",
        fixed_source_columns=(),
        rows_exact=True,
        row_ledger_identity="sha256:rows-v1",
        component_scope=BatchComponentScope(
            contrast_name="stim_vs_ctrl",
            target_coefficient="condition[T.stim]",
            fitted_result_id="results.csv#stim_vs_ctrl",
        ),
        unsupported_components=(),
        field_confidence={
            "source_column": "high", "modeled_as": "high",
            "random_group_column": "high", "fixed_source_columns": "high",
            "rows_exact": "high", "row_ledger_identity": "high",
            "component_scope": "high", "unsupported_components": "high",
        },
        evidence_locations={"modeled_as": ("analysis.R:42",)},
    )
    values.update(overrides)
    return BatchModelingDeclaration(**values)


def test_per_batch_modeling_ledger_is_additive_and_deeply_immutable():
    entry = _batch_entry()
    ledger = {"run": entry}
    declaration = fitted_design_declaration(batch_modeling=ledger)
    ledger.clear()

    assert declaration.operator_kind == "ordinary_fixed_effects"
    assert declaration.batch_modeling["run"].modeled_as == "random_intercept"
    with pytest.raises(TypeError):
        declaration.batch_modeling["run"] = entry
    with pytest.raises(TypeError):
        entry.field_confidence["modeled_as"] = "low"


@pytest.mark.parametrize("override", [
    {"modeled_as": "random_slope"},
    {"fixed_source_columns": ("run", "run")},
    {"unsupported_components": ("mystery_component",)},
    {"field_confidence": {"modeled_as": "high"}},
])
def test_batch_ledger_rejects_open_or_incomplete_semantics(override):
    with pytest.raises((TypeError, ValueError)):
        fitted_design_declaration(batch_modeling={"run": _batch_entry(**override)})


def test_batch_ledger_rejects_mapping_key_source_mismatch():
    with pytest.raises(ValueError, match="key"):
        fitted_design_declaration(batch_modeling={"run": _batch_entry(source_column="plate")})


def test_legacy_fitted_design_has_empty_unratified_batch_ledger():
    assert dict(fitted_design_declaration().batch_modeling) == {}
