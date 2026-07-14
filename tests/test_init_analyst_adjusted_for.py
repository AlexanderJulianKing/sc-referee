import json
from pathlib import Path

import pandas as pd

from sc_referee.init import _roles_from_payload, proposal_tool_schema, synthesize_config
from sc_referee.roles import Roles


def _obs():
    return pd.DataFrame(
        {
            "donor": [f"D{i}" for i in range(6)],
            "condition": ["ctrl", "stim"] * 3,
            "run": ["a", "b"] * 3,
        }
    )


def _roles(**overrides):
    return Roles(
        analysis_type="condition_contrast_DE",
        condition="condition",
        replicate_unit=("donor",),
        batch=("run",),
        reference="ctrl",
        confidence={"condition": "high", "analyst_adjusted_for": "high"},
        **overrides,
    )


def test_all_valid_columns_are_preserved():
    config = synthesize_config(
        _roles(analyst_adjusted_for=("run", "condition")), _obs()
    )

    assert set(config["contrasts"][0]["analyst_adjusted_for"]) == {"run", "condition"}


def test_any_unknown_item_invalidates_the_whole_set_to_none():
    config = synthesize_config(
        _roles(analyst_adjusted_for=("run", "C(run)")), _obs()
    )

    assert config["contrasts"][0]["analyst_adjusted_for"] is None
    assert "analyst_adjusted_for" in config["unresolved"]
    assert config["confidence"]["analyst_adjusted_for"] == "low"


def test_uncaptured_stays_none_not_empty_and_unresolved():
    config = synthesize_config(_roles(analyst_adjusted_for=None), _obs())

    assert config["contrasts"][0]["analyst_adjusted_for"] is None
    assert "analyst_adjusted_for" in config["unresolved"]
    assert config["confidence"]["analyst_adjusted_for"] == "low"


def test_payload_preserves_absent_none_and_explicit_empty():
    base = {
        "analysis_type": "condition_contrast_DE",
        "design": {"condition": "condition", "replicate_unit": ["donor"], "batch": ["run"]},
    }

    assert _roles_from_payload(base).analyst_adjusted_for is None
    assert _roles_from_payload({**base, "analyst_adjusted_for": []}).analyst_adjusted_for == ()


def test_proposal_schema_accepts_only_a_list_of_column_labels():
    adjusted = proposal_tool_schema()["properties"]["analyst_adjusted_for"]

    assert adjusted == {"type": "array", "items": {"type": "string"}}


def test_config_schema_declares_field_specific_confidence():
    schema_path = (Path(__file__).parents[1] / "src" / "sc_referee" / "schemas"
                   / "sc_referee.schema.json")
    schema = json.loads(schema_path.read_text())

    assert schema["properties"]["confidence"]["properties"]["analyst_adjusted_for"] == {
        "enum": ["high", "low"]
    }
