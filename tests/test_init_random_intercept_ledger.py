import jsonschema

from sc_referee.init import _roles_from_payload, proposal_tool_schema


def _payload():
    return {
        "analysis_type": "condition_contrast_DE",
        "type_confidence": "high",
        "type_evidence": [],
        "plain_summary": "The source fits (1|run).",
        "design": {"replicate_unit": ["donor_id"], "condition": "condition", "batch": ["run"]},
        "analyst_adjusted_for": ["condition"],
        "confidence": {"condition": "high", "batch": "high", "analyst_adjusted_for": "high"},
        "unresolved": [],
        "batch_modeling": [],
    }


def test_llm_may_propose_only_closed_batch_structure_facts():
    item = proposal_tool_schema()["properties"]["batch_modeling"]["items"]
    assert item["properties"]["modeled_as"]["enum"] == [
        "fixed", "random_intercept", "fixed_and_random_intercept",
        "absent", "upstream_handled", "unsupported",
    ]
    for forbidden in ("formula", "model", "row_ledger_identity", "confirmed_by_human"):
        assert forbidden not in item["properties"]
    assert item["additionalProperties"] is False


def test_formula_text_never_upgrades_an_unresolved_batch_ledger():
    roles = _roles_from_payload(_payload())
    assert roles.batch_modeling == ()
    assert "batch_modeling" in roles.unresolved


def test_proposer_rejects_digest_or_confirmation_authority():
    payload = _payload()
    payload["batch_modeling"] = [{
        "source_column": "run", "modeled_as": "random_intercept",
        "random_group_column": "run", "fixed_source_columns": [],
        "component_scope": {"contrast_name": "stim_vs_ctrl", "target_coefficient": "condition[T.stim]", "fitted_result_id": "result#1"},
        "unsupported_components": [], "field_confidence": {}, "evidence_locations": {},
        "row_ledger_identity": "invented",
    }]
    try:
        jsonschema.validate(payload, proposal_tool_schema())
    except jsonschema.ValidationError:
        pass
    else:
        raise AssertionError("proposal schema accepted a row digest")
