import jsonschema
import pandas as pd

from sc_referee.init import _roles_from_payload, proposal_tool_schema, synthesize_config


def _payload():
    return {
        "analysis_type": "condition_contrast_DE",
        "type_confidence": "high",
        "type_evidence": [],
        "plain_summary": "A condition contrast grouped by run.",
        "design": {
            "replicate_unit": ["donor_id"], "condition": "condition", "batch": ["run"],
        },
        "analyst_adjusted_for": ["condition"],
        "confidence": {"condition": "high", "batch": "high",
                       "analyst_adjusted_for": "high"},
        "unresolved": [],
    }


def test_csp_proposal_is_closed_evidence_only_and_cannot_ratify():
    item = proposal_tool_schema()["properties"]["csp_proposals"]["items"]
    assert len(item["oneOf"]) == 3
    branch = item["oneOf"][0]
    assert branch["additionalProperties"] is False
    assert branch["properties"]["contract_type"]["const"] == \
        "between_group_adjustment_obligation/v1"
    for forbidden in (
        "formula", "expression", "model", "verdict", "contract_id",
        "scope_fingerprint", "confirmation_state", "confirmed_high",
        "between_group_policy", "may_rely_on_re_exogeneity",
    ):
        assert forbidden not in branch["properties"]


def target_proposal():
    return {
        "contract_type": "target_population_estimand/v1",
        "reported_scalar_id": "results.csv#IL7R:effect",
        "target_population_id": "registry:california:v4",
        "census_stratum_columns": ["age_band", "sex"],
        "evaluation_stratum_columns": ["age_band", "sex"],
        "stratum_levels": [["18-39", "F"], ["18-39", "M"]],
        "stratum_ledger_identity": "strata:v1:age-sex:abc123",
        "census_artifact_identity": "artifact:registry-v4:sha256:abc123",
        "census_count_ledger_identity": "counts:v1:sha256:def456",
        "census_total_n": 500,
        "census_stratum_counts": [300, 200],
        "weight_vector_identity": "weights:v1:sha256:fedcba",
        "weight_vector": [[300, 500], [200, 500]],
        "functional_candidate": "population_average",
        "support_policy_candidate": "require_observed_evaluation_support",
        "evidence_locations": ["registry.yaml:1", "results.csv:IL7R"],
    }


@__import__("pytest").mark.parametrize("smuggled", [
    {"formula": "sum"}, {"filter": "age >= 18"}, {"verdict": "wrong"},
    {"confirmation_state": "confirmed_high"}, {"authority_attested": True},
])
def test_target_llm_cannot_smuggle_formula_verdict_or_authority(smuggled):
    payload = _payload() | {"csp_proposals": [target_proposal() | smuggled]}
    with __import__("pytest").raises(jsonschema.ValidationError):
        jsonschema.validate(payload, proposal_tool_schema())


def observations_with_strata():
    return pd.DataFrame({
        "donor_id": ["D1", "D2"], "condition": ["ctrl", "stim"],
        "run": ["R1", "R2"], "age_band": ["18-39", "18-39"],
        "sex": ["F", "M"],
    })


def test_unknown_column_invalidates_whole_target_proposal():
    proposal = target_proposal()
    proposal["evaluation_stratum_columns"] = ["age_band", "invented"]
    roles = _roles_from_payload(_payload() | {"csp_proposals": [proposal]})
    config = synthesize_config(roles, observations_with_strata())
    assert config["csp_proposals"] == []
    assert "csp_proposals" in config["unresolved"]


def test_target_proposal_never_materializes_contract():
    roles = _roles_from_payload(_payload() | {"csp_proposals": [target_proposal()]})
    config = synthesize_config(roles, observations_with_strata())
    assert config["csp_proposals"] == [target_proposal()]
    assert all("csp_contracts" not in contrast for contrast in config["contrasts"])
    assert "confirmed_high" not in repr(config["csp_proposals"])


def test_llm_cannot_smuggle_formula_or_confirmation_into_csp_proposal():
    payload = _payload() | {"csp_proposals": [{
        "contract_type": "between_group_adjustment_obligation/v1",
        "group_source_column": "run",
        "evidence_locations": ["analysis.R:42"],
        "formula": "condition plus random run",
        "confirmation_state": "confirmed_high",
    }]}
    with __import__("pytest").raises(jsonschema.ValidationError):
        jsonschema.validate(payload, proposal_tool_schema())


def test_proposal_synthesizes_only_an_unresolved_draft():
    roles = _roles_from_payload(_payload() | {"csp_proposals": [{
        "contract_type": "between_group_adjustment_obligation/v1",
        "group_source_column": "run",
        "evidence_locations": ["analysis.R:42"],
    }]})
    assert roles.csp_proposals[0]["group_source_column"] == "run"
    assert "between_group_policy" not in roles.csp_proposals[0]


def test_unknown_group_column_invalidates_whole_csp_proposal():
    roles = _roles_from_payload(_payload() | {"csp_proposals": [{
        "contract_type": "between_group_adjustment_obligation/v1",
        "group_source_column": "invented",
        "evidence_locations": ["analysis.R:42"],
    }]})
    obs = pd.DataFrame({"donor_id": ["D1", "D2"], "condition": ["ctrl", "stim"],
                        "run": ["R1", "R2"]})
    config = synthesize_config(roles, obs)
    assert config["csp_proposals"] == []
    assert "csp_proposals" in config["unresolved"]
