import yaml

from sc_referee.config import load_designs
from sc_referee.engine import build_pseudobulk_sample_rows
from sc_referee.wizard import answers_to_config, design_questions, render_form
from tests.factories import pseudobulk_confounding_bundle


def _proposal():
    return {
        "analysis_type": "condition_contrast_DE",
        "design": {"condition": "condition", "replicate_unit": ["donor_id"], "batch": ["run"]},
        "contrasts": [{"name": "stim_vs_ctrl", "reference": "ctrl", "test": "stim", "analyst_adjusted_for": ["condition"]}],
        "reported_results": {"unit_of_test": "sample"},
        "confidence": {"condition": "high", "batch": "high", "analyst_adjusted_for": "high"},
        "unresolved": [],
        "batch_modeling": [{
            "source_column": "run", "modeled_as": "random_intercept",
            "random_group_column": "run", "fixed_source_columns": [],
            "component_scope": {"contrast_name": "stim_vs_ctrl", "target_coefficient": "condition[T.stim]", "fitted_result_id": "results#stim_vs_ctrl"},
            "unsupported_components": [], "field_confidence": {
                "source_column": "high", "modeled_as": "high", "random_group_column": "high",
                "fixed_source_columns": "high", "component_scope": "high", "unsupported_components": "high",
            }, "evidence_locations": {"modeled_as": ["analysis.R:42"]},
        }],
    }


def _answers():
    return {
        "analysis_type": "condition_contrast_DE", "condition": "condition",
        "reference": "ctrl", "test": "stim", "replicate_unit": "donor_id",
        "batch": ["run"], "unit_of_test": "sample", "analyst_adjusted_for": ["condition"],
        "aggregation_key": ["donor_id"],
        "batch_modeling.run.modeled_as": "random_intercept",
        "batch_modeling.run.random_group_column": "run",
        "batch_modeling.run.fixed_source_columns": [],
        "batch_modeling.run.rows_exact": "yes",
        "batch_modeling.run.contrast_name": "stim_vs_ctrl",
        "batch_modeling.run.target_coefficient": "condition[T.stim]",
        "batch_modeling.run.fitted_result_id": "results#stim_vs_ctrl",
        "batch_modeling.run.unsupported_components": [],
    }


def test_wizard_requires_explicit_batch_modeling_confirmation():
    questions = {q.role: q for q in design_questions(
        _proposal(), pseudobulk_confounding_bundle().observations.columns,
        analysis_types=("condition_contrast_DE",),
    )}
    question = questions["batch_modeling.run.modeled_as"]
    assert question.required is True
    assert "partially pool" in question.why.lower()
    assert "adjust" not in question.why.lower()
    assert questions["aggregation_key"].required is True
    html = render_form(questions.values())
    assert 'name="batch_modeling.run.unsupported_components_answered"' in html


def test_wizard_binds_confirmed_ledger_to_canonical_fitted_rows(tmp_path):
    bundle = pseudobulk_confounding_bundle()
    config = answers_to_config(_answers(), bundle.observations)
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(config))
    (design,) = load_designs(path)
    fitted_rows = build_pseudobulk_sample_rows(bundle.observations, design)
    ledger = design.fitted_design.batch_modeling["run"]
    assert ledger.rows_exact is True
    assert ledger.row_ledger_identity == fitted_rows.row_ledger_identity
    assert ledger.field_confidence["row_ledger_identity"] == "high"


def test_unanswered_wizard_field_stays_unratified():
    bundle = pseudobulk_confounding_bundle()
    answers = _answers()
    del answers["batch_modeling.run.unsupported_components"]
    config = answers_to_config(answers, bundle.observations)
    assert config["contrasts"][0]["fitted_design"]["batch_modeling"] == {}
    assert "batch_modeling.run.unsupported_components" in config["unresolved"]


def test_explicit_empty_checkbox_inventory_and_proposal_evidence_are_ratified(tmp_path):
    bundle = pseudobulk_confounding_bundle()
    answers = _answers()
    answers.pop("batch_modeling.run.fixed_source_columns")
    answers.pop("batch_modeling.run.unsupported_components")
    answers["batch_modeling.run.fixed_source_columns_answered"] = "1"
    answers["batch_modeling.run.unsupported_components_answered"] = "1"
    config = answers_to_config(answers, bundle.observations, proposed_config=_proposal())
    entry = config["contrasts"][0]["fitted_design"]["batch_modeling"]["run"]
    assert entry["fixed_source_columns"] == []
    assert entry["unsupported_components"] == []
    assert entry["evidence_locations"] == {"modeled_as": ["analysis.R:42"]}


def test_wizard_persists_unsupported_operator_for_nonadditive_component():
    bundle = pseudobulk_confounding_bundle()
    answers = _answers()
    answers["batch_modeling.run.modeled_as"] = "fixed"
    answers["batch_modeling.run.unsupported_components"] = ["transform"]
    config = answers_to_config(answers, bundle.observations)
    fitted = config["contrasts"][0]["fitted_design"]
    assert fitted["operator_kind"] == "unsupported"
    assert fitted["unsupported_reason"] == "unsupported_nonadditive_operator"
