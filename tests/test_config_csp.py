from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from sc_referee.config import load_designs
from sc_referee.init import confirm_config
from sc_referee.csp import CspAbstention, CspReadRequest, read_ratified_contract
from sc_referee.csp_contracts.between_group_adjustment_obligation_v1 import (
    CONTRACT_TYPE,
    REQUIRED_FIELDS,
)
from tests.csp_factories import (
    ratified_contract_yaml,
    ratified_target_contract_yaml,
    scope_from_design,
)


def test_target_yaml_round_trips_typed_immutable(tmp_path):
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(ratified_target_contract_yaml()))
    record = load_designs(path)[0].csp_contracts[0]
    assert record.fields["stratum_levels"].value[0] == ("18-39", "F")
    assert record.scope.contract_scope["weight_vector_identity"] == \
        "weights:v1:sha256:fedcba"


@pytest.mark.parametrize("forbidden", [
    "formula", "filter", "verdict", "confirmed_by_human", "confidence",
])
def test_target_contract_rejects_smuggled_keys(tmp_path, forbidden):
    raw = ratified_target_contract_yaml()
    raw["contrasts"][0]["csp_contracts"][0][forbidden] = "smuggled"
    path = tmp_path / "x.yaml"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError, match="schema validation"):
        load_designs(path)


def test_broad_population_value_is_not_an_identity(tmp_path):
    raw = ratified_target_contract_yaml()
    raw["contrasts"][0]["csp_contracts"][0]["fields"] \
        ["target_population_id"]["value"] = "across the population"
    path = tmp_path / "x.yaml"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError, match="schema validation"):
        load_designs(path)


def test_legacy_confirm_cannot_mint_target_contract(tmp_path):
    from tests.test_init_csp import target_proposal

    raw = ratified_contract_yaml(include_csp=False)
    raw["csp_proposals"] = [target_proposal()]
    path = tmp_path / "x.yaml"
    path.write_text(yaml.safe_dump(raw))
    confirm_config(path)
    assert load_designs(path)[0].csp_contracts == ()


def test_closed_csp_yaml_round_trips_to_typed_immutable_record(tmp_path):
    raw = ratified_contract_yaml()
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(raw))
    (loaded,) = load_designs(path)
    assert loaded.estimand_id == "condition-effect/v1"
    assert loaded.csp_contracts[0].contract_type == CONTRACT_TYPE
    with pytest.raises(TypeError):
        loaded.csp_contracts[0].fields["between_group_policy"] = None


def test_legacy_confirmed_by_human_does_not_confer_csp_confirmation(tmp_path):
    raw = ratified_contract_yaml(include_csp=False)
    raw["confirmed_by_human"] = True
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(raw))
    (design,) = load_designs(path)
    result = read_ratified_contract(
        design.csp_contracts,
        CspReadRequest(CONTRACT_TYPE, scope_from_design(design), REQUIRED_FIELDS,
                       "confounding_random_intercept_conditional"),
    )
    assert result == CspAbstention(reason="contract_absent", contract_id=None)


@pytest.mark.parametrize("forbidden", ["formula", "verdict", "confirmed_by_human"])
def test_contract_forbidden_extra_keys_are_rejected(tmp_path, forbidden):
    raw = ratified_contract_yaml()
    raw["contrasts"][0]["csp_contracts"][0][forbidden] = "smuggled"
    path = tmp_path / "sc-referee.yaml"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError, match="schema validation"):
        load_designs(path)


def test_field_values_and_page_level_authority_are_closed(tmp_path):
    for mutate in ("bad_value", "page_confirmed", "contract_confidence"):
        raw = deepcopy(ratified_contract_yaml())
        contract = raw["contrasts"][0]["csp_contracts"][0]
        if mutate == "bad_value":
            contract["fields"]["between_group_policy"]["value"] = "sometimes"
        elif mutate == "page_confirmed":
            contract["confirmed"] = True
        else:
            contract["confidence"] = "high"
        path = tmp_path / f"{mutate}.yaml"
        path.write_text(yaml.safe_dump(raw))
        with pytest.raises(ValueError, match="schema validation"):
            load_designs(path)


def test_coverage_boundary_documents_trusted_csp_config():
    text = Path("docs/coverage-boundary.md").read_text().lower()
    assert "## trust boundary" in text
    assert "trusted analyst assertion" in text
    assert "wizard is the intended authoring" in text
    assert "auditable" in text and "cryptographically prove" in text
    assert "no provenance token" in text
    assert "partial-r2-decision-v2" in text
