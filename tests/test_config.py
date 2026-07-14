import yaml
import pytest

from sc_referee.config import load_designs
from sc_referee.row_ledger import EvaluationRelation


def test_config_round_trips_analyst_adjusted_for(tmp_path):
    config = {
        "analysis_type": "condition_contrast_DE",
        "confirmed_by_human": True,
        "design": {"condition": "condition", "replicate_unit": ["donor"], "batch": ["run"]},
        "contrasts": [
            {
                "name": "s_vs_c",
                "reference": "c",
                "test": "s",
                "sample_unit": ["donor"],
                "analyst_adjusted_for": ["run"],
            }
        ],
        "confidence": {"condition": "high"},
    }
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(config))

    (design,) = load_designs(path)

    assert design.analyst_adjusted_for == ["run"]


def _fitted_config():
    return {
        "analysis_type": "condition_contrast_DE", "confirmed_by_human": True,
        "design": {"condition": "condition", "replicate_unit": ["donor"], "batch": ["run"]},
        "contrasts": [{
            "name": "s_vs_c", "reference": "c", "test": "s", "sample_unit": ["donor"],
            "aggregation_key": ["donor"], "analyst_adjusted_for": ["run", "condition"],
            "fitted_design": {
                "rows_exact": True, "operator_kind": "ordinary_fixed_effects", "intercept": True,
                "column_kinds": {"run": "categorical", "condition": "categorical"},
                "categorical_levels": {"run": ["R1", "R2"], "condition": ["c", "s"]},
                "transforms": {"run": "identity", "condition": "identity"},
                "weight_role": "precision",
            },
        }],
        "confidence": {"condition": "high", "batch": "high", "analyst_adjusted_for": "high",
                       "aggregation_key": "high", "fitted_design": "high"},
    }


def _clean_row_ledger_config():
    return {
        "schema_version": "row-ledger-schema-v1",
        "source_snapshot_identity": "sha256:observations-v1",
        "count_layer_identity": "sha256:raw-counts-v1",
        "source_occurrence_id_columns": ["cell_id"],
        "fitted_source_occurrence_ids": [["c1"], ["c2"]],
        "operations": [
            {"kind": "declared_subset", "operation_id": "subset", "column_id": "cell_type",
             "allowed_values": ["T"], "confidence": "high"},
            {"kind": "declared_qc_threshold", "operation_id": "qc", "column_id": "n_genes",
             "comparison": "ge", "threshold": 200, "missing_policy": "drop", "confidence": "high"},
            {"kind": "aggregation", "operation_id": "aggregate", "key_columns": ["donor"],
             "order": "stable_first_occurrence", "confidence": "high"},
        ],
        "evaluation_relation": "verified_same_as_fitted", "evaluation_relation_confidence": "high",
        "fitted_result_id": "results.csv#s_vs_c", "target_coefficient": "condition[T.s]",
        "field_confidence": {
            "source_snapshot_identity": "high", "count_layer_identity": "high",
            "source_occurrence_id_columns": "high", "fitted_source_occurrence_ids": "high",
            "evaluation_relation": "high", "fitted_result_id": "high", "target_coefficient": "high",
        },
    }


def test_config_round_trips_closed_row_ledger_without_inference(tmp_path):
    config = _fitted_config(); config["contrasts"][0]["row_ledger"] = _clean_row_ledger_config()
    path = tmp_path / "sc-referee.yaml"; path.write_text(yaml.safe_dump(config))
    (design,) = load_designs(path)
    assert design.row_ledger.operations[1].column_id == "n_genes"
    assert design.row_ledger.evaluation_relation is EvaluationRelation.VERIFIED_SAME_AS_FITTED


def test_legacy_config_has_no_inferred_row_ledger(tmp_path):
    config = _fitted_config(); path = tmp_path / "sc-referee.yaml"; path.write_text(yaml.safe_dump(config))
    (design,) = load_designs(path)
    assert design.row_ledger is None


@pytest.mark.parametrize("bad", [
    {"predicate": "n_genes >= 200"}, {"formula": "~ condition"},
    {"callback": "filter_cells"}, {"comparison": "python_eval"},
])
def test_config_rejects_open_row_ledger_operations(tmp_path, bad):
    config = _fitted_config(); ledger = _clean_row_ledger_config(); ledger["operations"][1].update(bad)
    config["contrasts"][0]["row_ledger"] = ledger
    path = tmp_path / "sc-referee.yaml"; path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError): load_designs(path)


def test_config_round_trips_exact_fitted_design(tmp_path):
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(_fitted_config()))
    (design,) = load_designs(path)
    assert design.fitted_design.operator_kind == "ordinary_fixed_effects"
    assert design.fitted_design.categorical_levels["run"] == ("R1", "R2")
    assert design.fitted_design.weight_role == "precision"


def test_config_rejects_missing_transform_entry(tmp_path):
    config = _fitted_config()
    del config["contrasts"][0]["fitted_design"]["transforms"]["run"]
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="transform"):
        load_designs(path)


def test_legacy_config_leaves_fitted_design_unresolved(tmp_path):
    config = _fitted_config()
    del config["contrasts"][0]["fitted_design"]
    config["confidence"].pop("fitted_design")
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(config))
    (design,) = load_designs(path)
    assert design.fitted_design is None
    assert design.confidence.get("fitted_design") != "high"


def _batch_ledger_config():
    config = _fitted_config()
    config["contrasts"][0]["fitted_design"]["batch_modeling"] = {
        "run": {
            "source_column": "run", "modeled_as": "random_intercept",
            "random_group_column": "run", "fixed_source_columns": [],
            "rows_exact": True, "row_ledger_identity": "sha256:rows-v1",
            "component_scope": {
                "contrast_name": "s_vs_c",
                "target_coefficient": "condition[T.s]",
                "fitted_result_id": "results.csv#s_vs_c",
            },
            "unsupported_components": [],
            "field_confidence": {
                "source_column": "high", "modeled_as": "high",
                "random_group_column": "high", "fixed_source_columns": "high",
                "rows_exact": "high", "row_ledger_identity": "high",
                "component_scope": "high", "unsupported_components": "high",
            },
            "evidence_locations": {"modeled_as": ["analysis.R:42"]},
        }
    }
    return config


def test_config_round_trips_confirmed_random_intercept_batch_ledger(tmp_path):
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(_batch_ledger_config()))
    (design,) = load_designs(path)
    entry = design.fitted_design.batch_modeling["run"]
    assert entry.random_group_column == "run"
    assert entry.fixed_source_columns == ()
    assert entry.component_scope.contrast_name == "s_vs_c"


def test_legacy_config_does_not_infer_batch_ledger_from_formula(tmp_path):
    config = _fitted_config()
    config["contrasts"][0]["model"] = "~ condition + (1|run)"
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(config))
    (design,) = load_designs(path)
    assert dict(design.fitted_design.batch_modeling) == {}


@pytest.mark.parametrize("mutate", [
    lambda entry: entry.update(modeled_as="random_slope"),
    lambda entry: entry.update(unsupported_components=["mystery_component"]),
    lambda entry: entry["component_scope"].pop("fitted_result_id"),
    lambda entry: entry["field_confidence"].pop("rows_exact"),
    lambda entry: entry.update(extra="not-closed"),
    lambda entry: entry.update(fixed_source_columns=["run", "run"]),
])
def test_config_rejects_open_or_incomplete_batch_ledger(tmp_path, mutate):
    config = _batch_ledger_config()
    mutate(config["contrasts"][0]["fitted_design"]["batch_modeling"]["run"])
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError):
        load_designs(path)


def test_config_rejects_batch_ledger_key_source_mismatch(tmp_path):
    config = _batch_ledger_config()
    config["contrasts"][0]["fitted_design"]["batch_modeling"]["run"]["source_column"] = "plate"
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="key"):
        load_designs(path)
