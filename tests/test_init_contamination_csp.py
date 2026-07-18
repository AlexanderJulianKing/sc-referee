from __future__ import annotations

import jsonschema
import pandas as pd
import pytest

from sc_referee.init import _roles_from_payload, proposal_tool_schema, synthesize_config


def _payload():
    return {
        "analysis_type": "condition_contrast_DE",
        "type_confidence": "high",
        "type_evidence": [],
        "plain_summary": "A donor-level condition contrast.",
        "design": {"replicate_unit": ["donor"], "condition": "condition", "batch": []},
        "analyst_adjusted_for": ["condition"],
        "confidence": {"condition": "high", "analyst_adjusted_for": "high"},
        "unresolved": [],
    }


def contamination_proposal():
    return {
        "contract_type": "contamination_basis_obligation/v1",
        "measurement_kind_candidate": "external_measurement_artifact",
        "vector_field": "rho_external",
        "artifact_identity": "artifact:empty-drops:v1",
        "source_mapping_fields": ["donor"],
        "materialized_basis_columns": ["rho_external"],
        "transform_kind_candidate": "continuous_identity",
        "causal_role_guess": "pre_exposure_nuisance",
        "fitted_result_id": "fit:contamination:v1",
        "target_coefficient": "condition[T.case]",
        "exposure_column": "condition",
        "estimand_id": "estimand:contamination:v1",
        "row_ledger_identity": "rows:donors:v1",
        "fitted_design_identity": "design:contamination:v1",
        "evidence_locations": ["empty_drops.csv", "analysis.R:42"],
    }


def _branch():
    branches = proposal_tool_schema()["properties"]["csp_proposals"]["items"]["oneOf"]
    return next(branch for branch in branches
                if branch["properties"]["contract_type"].get("const")
                == "contamination_basis_obligation/v1")


def test_proposal_excludes_load_bearing_values():
    branch = _branch()
    assert branch["additionalProperties"] is False
    assert "guess" in branch["properties"]["causal_role_guess"]["description"].lower()
    for forbidden in (
        "formula", "threshold", "threshold_provenance", "vector_values", "rho", "score",
        "coefficient_value", "r_squared", "rank", "containment", "contamination_percentage",
        "severity", "verdict", "remedy", "confirmation", "causal_rationale",
    ):
        assert forbidden not in branch["properties"]


@pytest.mark.parametrize("extra", [
    {"threshold": .18}, {"rho": [.1, .2]}, {"containment": False},
    {"causal_rationale": "technical"}, {"verdict": "major"},
])
def test_proposer_cannot_smuggle_values(extra):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _payload() | {"csp_proposals": [contamination_proposal() | extra]},
            proposal_tool_schema(),
        )


@pytest.mark.parametrize("mutation", ["phantom", "duplicate", "unknown_enum", "partial_scope"])
def test_invalid_contamination_proposal_is_rejected_atomically(mutation):
    proposal = contamination_proposal()
    if mutation == "phantom":
        proposal["vector_field"] = "invented"
    elif mutation == "duplicate":
        proposal["materialized_basis_columns"] = ["rho_external", "rho_external"]
    elif mutation == "unknown_enum":
        proposal["causal_role_guess"] = "definitely_confounder"
    else:
        del proposal["fitted_design_identity"]
    payload = _payload() | {"csp_proposals": [proposal]}
    if mutation in {"unknown_enum", "partial_scope"}:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(payload, proposal_tool_schema())
        return
    roles = _roles_from_payload(payload)
    observations = pd.DataFrame({
        "donor": ["D1", "D2"], "condition": ["control", "case"],
        "rho_external": [.1, .2],
    })
    config = synthesize_config(roles, observations)
    assert config["csp_proposals"] == []
    assert "csp_proposals" in config["unresolved"]


def test_valid_proposal_remains_only_a_proposal():
    roles = _roles_from_payload(_payload() | {"csp_proposals": [contamination_proposal()]})
    observations = pd.DataFrame({
        "donor": ["D1", "D2"], "condition": ["control", "case"],
        "rho_external": [.1, .2],
    })
    config = synthesize_config(roles, observations)
    assert config["csp_proposals"] == [contamination_proposal()]
    assert all("csp_contracts" not in contrast for contrast in config["contrasts"])
