from dataclasses import replace

import pytest

from sc_referee.csp import (
    CspAbstention,
    CspFieldState,
    CspReadRequest,
    CspScope,
    RatifiedFactSet,
    read_ratified_contract,
    invalidate_contract_for_scope,
    transition_field,
    assignment_identity,
)
import pandas as pd
from sc_referee.csp_contracts.between_group_adjustment_obligation_v1 import (
    CONTRACT_TYPE,
    REQUIRED_FIELDS,
)
from tests.csp_factories import (
    ratified_between_group_contract,
    ratified_target_population_contract,
    target_scope,
)
from sc_referee.csp_contracts.target_population_estimand_v1 import (
    CONTRACT_TYPE as TARGET_TYPE,
    REQUIRED_FIELDS as TARGET_FIELDS,
)


def _scope():
    return CspScope(
        fitted_result_id="fixture-results#contrast",
        contrast_name="contrast",
        target_coefficient="condition[T.stim]",
        exposure_column="condition",
        row_ledger_identity="rows:v1:abc",
        estimand_id="condition-effect/v1",
        group_source_column="run",
        assignment_identity="csp-assign:v1:" + "a" * 64,
    )


def test_every_target_scope_identity_changes_fingerprint():
    scope = target_scope()
    for key in scope.contract_scope:
        changed = dict(scope.contract_scope)
        changed[key] += ":changed"
        assert replace(scope, contract_scope=changed).fingerprint != scope.fingerprint


def test_empty_extension_preserves_frozen_between_group_fingerprint():
    assert _scope().fingerprint == (
        "csp-scope:v2:60cc9d7aa798e603c72d9236ceef11222bdaf2eca43139349b27409e7d52cfe5"
    )


def test_shared_reader_returns_immutable_structured_facts():
    scope = target_scope()
    record = ratified_target_population_contract(scope=scope)
    result = read_ratified_contract((record,), CspReadRequest(
        TARGET_TYPE, scope, TARGET_FIELDS, "target_population"))
    assert isinstance(result, RatifiedFactSet)
    assert result.values["stratum_levels"][0] == ("18-39", "F")
    with pytest.raises(TypeError):
        result.values["stratum_levels"][0] = ("changed", "F")


def test_scope_value_disagreement_is_value_free():
    scope = target_scope()
    record = ratified_target_population_contract(scope=scope)
    bad = replace(record.fields["target_population_id"], value="registry:other:v1")
    record = replace(record, fields={**record.fields, "target_population_id": bad})
    result = read_ratified_contract((record,), CspReadRequest(
        TARGET_TYPE, scope, TARGET_FIELDS, "target_population"))
    assert result == CspAbstention("scope_value_mismatch", record.contract_id)
    assert not hasattr(result, "values")


def test_target_reader_releases_only_exact_all_high_facts():
    scope = target_scope()
    record = ratified_target_population_contract(scope=scope)
    result = read_ratified_contract((record,), CspReadRequest(
        TARGET_TYPE, scope, TARGET_FIELDS, "target_population"))
    assert isinstance(result, RatifiedFactSet)
    assert tuple(result.values) == TARGET_FIELDS
    assert result.values["functional"] == "population_average"


def _changed_target_scope(scope, axis):
    base = {
        "fit": ("fitted_result_id", "changed-fit"),
        "coefficient": ("target_coefficient", "changed-coefficient"),
        "rows": ("row_ledger_identity", "changed-rows"),
        "estimand": ("estimand_id", "changed-estimand"),
    }
    if axis in base:
        field, value = base[axis]
        return replace(scope, **{field: value})
    key = {
        "scalar": "reported_scalar_id", "population": "target_population_id",
        "census": "census_artifact_identity", "strata": "stratum_ledger_identity",
        "weights": "weight_vector_identity",
    }[axis]
    extension = dict(scope.contract_scope)
    extension[key] += ":changed"
    return replace(scope, contract_scope=extension)


@pytest.mark.parametrize("axis", [
    "fit", "coefficient", "rows", "estimand", "scalar", "population",
    "census", "strata", "weights",
])
def test_every_target_scope_axis_mismatch_is_value_free(axis):
    scope = target_scope()
    record = ratified_target_population_contract(scope=scope)
    result = read_ratified_contract((record,), CspReadRequest(
        TARGET_TYPE, _changed_target_scope(scope, axis), TARGET_FIELDS,
        "target_population"))
    assert result == CspAbstention("scope_mismatch", record.contract_id)
    assert not hasattr(result, "values")


@pytest.mark.parametrize("consumer", [
    "confounding_random_intercept_conditional", "target_population_v2", "report",
])
def test_only_exact_future_consumer_is_authorized(consumer):
    scope = target_scope()
    record = ratified_target_population_contract(scope=scope)
    result = read_ratified_contract((record,), CspReadRequest(
        TARGET_TYPE, scope, TARGET_FIELDS, consumer))
    assert result == CspAbstention("consumer_not_authorized", record.contract_id)


def test_target_required_fields_cannot_be_subsetted_or_reordered():
    scope = target_scope()
    record = ratified_target_population_contract(scope=scope)
    for fields in (TARGET_FIELDS[:-1], tuple(reversed(TARGET_FIELDS))):
        result = read_ratified_contract((record,), CspReadRequest(
            TARGET_TYPE, scope, fields, "target_population"))
        assert result == CspAbstention("required_fields_mismatch", record.contract_id)


def test_duplicate_active_exact_scope_contracts_abstain():
    scope = target_scope()
    first = ratified_target_population_contract(scope=scope, contract_id="first")
    second = ratified_target_population_contract(scope=scope, contract_id="second")
    result = read_ratified_contract((first, second), CspReadRequest(
        TARGET_TYPE, scope, TARGET_FIELDS, "target_population"))
    assert result == CspAbstention("ambiguous_contracts", None)


def test_csp_field_state_machine_has_no_proposed_to_confirmed_shortcut():
    state = transition_field(CspFieldState.ABSENT, "propose")
    assert state is CspFieldState.PROPOSED_UNCONFIRMED
    with pytest.raises(ValueError, match="illegal CSP transition"):
        transition_field(state, "confirm_high")
    state = transition_field(state, "present")
    assert transition_field(state, "confirm_high") is CspFieldState.CONFIRMED_HIGH


@pytest.mark.parametrize("event, expected", [
    ("not_sure", CspFieldState.UNRESOLVED),
    ("skip", CspFieldState.UNRESOLVED),
    ("decline_for_consumer", CspFieldState.DECLINED_FOR_CONSUMER),
])
def test_every_nonaffirmative_presented_answer_is_non_authorizing(event, expected):
    assert transition_field(CspFieldState.PRESENTED, event) is expected


def test_bound_identity_change_invalidates_a_confirmed_field():
    assert transition_field(
        CspFieldState.CONFIRMED_HIGH, "scope_identity_changed"
    ) is CspFieldState.INVALIDATED


def test_transition_matrix_is_closed():
    legal = {
        (CspFieldState.ABSENT, "propose"): CspFieldState.PROPOSED_UNCONFIRMED,
        (CspFieldState.PROPOSED_UNCONFIRMED, "present"): CspFieldState.PRESENTED,
        (CspFieldState.PRESENTED, "confirm_high"): CspFieldState.CONFIRMED_HIGH,
        (CspFieldState.PRESENTED, "not_sure"): CspFieldState.UNRESOLVED,
        (CspFieldState.PRESENTED, "skip"): CspFieldState.UNRESOLVED,
        (CspFieldState.PRESENTED, "decline_for_consumer"):
            CspFieldState.DECLINED_FOR_CONSUMER,
        (CspFieldState.PROPOSED_UNCONFIRMED, "scope_identity_changed"):
            CspFieldState.INVALIDATED,
        (CspFieldState.PRESENTED, "scope_identity_changed"): CspFieldState.INVALIDATED,
        (CspFieldState.CONFIRMED_HIGH, "scope_identity_changed"):
            CspFieldState.INVALIDATED,
        (CspFieldState.UNRESOLVED, "scope_identity_changed"): CspFieldState.INVALIDATED,
        (CspFieldState.DECLINED_FOR_CONSUMER, "scope_identity_changed"):
            CspFieldState.INVALIDATED,
    }
    events = {event for _, event in legal} | {"confirm_high", "present", "propose"}
    for state in CspFieldState:
        for event in events:
            if (state, event) in legal:
                assert transition_field(state, event) is legal[state, event]
            else:
                with pytest.raises(ValueError, match="illegal CSP transition"):
                    transition_field(state, event)


def test_consumer_reads_only_exact_ratified_high_confidence_fields():
    scope = _scope()
    record = ratified_between_group_contract(scope=scope)
    result = read_ratified_contract(
        (record,), CspReadRequest(CONTRACT_TYPE, scope, REQUIRED_FIELDS,
                                 consumer_id="confounding_random_intercept_conditional"),
    )
    assert isinstance(result, RatifiedFactSet)
    assert dict(result.values) == {
        "between_group_policy": "remove_arbitrary",
        "may_rely_on_re_exogeneity": False,
    }
    assert result.contract_id == record.contract_id


def test_scope_change_returns_typed_abstention_and_no_draft_values():
    scope = _scope()
    record = ratified_between_group_contract(scope=scope)
    stale = replace(scope, estimand_id="different-estimand/v1")
    result = read_ratified_contract(
        (record,), CspReadRequest(CONTRACT_TYPE, stale, REQUIRED_FIELDS,
                                 "confounding_random_intercept_conditional"),
    )
    assert result == CspAbstention(reason="scope_mismatch", contract_id=record.contract_id)
    assert not hasattr(result, "values")


def test_scope_fingerprint_changes_for_every_bound_identity():
    scope = _scope()
    for field in (
        "fitted_result_id", "contrast_name", "target_coefficient", "exposure_column",
        "row_ledger_identity", "estimand_id", "group_source_column", "assignment_identity",
    ):
        assert replace(scope, **{field: getattr(scope, field) + "-changed"}).fingerprint != scope.fingerprint


def test_assignment_identity_binds_typed_exposure_and_group_values_in_order():
    rows = pd.DataFrame({"condition": ["ctrl", "stim"], "run": [1, 2]})
    original = assignment_identity(rows, "condition", "run")
    assert assignment_identity(rows.copy(), "condition", "run") == original
    swapped_exposure = rows.copy()
    swapped_exposure["condition"] = swapped_exposure["condition"].iloc[::-1].to_numpy()
    swapped_group = rows.copy()
    swapped_group["run"] = swapped_group["run"].iloc[::-1].to_numpy()
    typed_group = rows.copy()
    typed_group["run"] = typed_group["run"].astype(str)
    assert len({original,
                assignment_identity(swapped_exposure, "condition", "run"),
                assignment_identity(swapped_group, "condition", "run"),
                assignment_identity(typed_group, "condition", "run")}) == 4


@pytest.mark.parametrize("defect, reason", [
    ("state", "field_not_confirmed_high"),
    ("confidence", "field_confidence_not_high"),
    ("value", "field_value_missing"),
    ("teach_back", "teach_back_failed"),
    ("consequence", "consequence_not_acknowledged"),
    ("evidence", "evidence_basis_missing"),
    ("metadata", "confirmation_metadata_missing"),
    ("consumer", "consumer_not_authorized"),
    ("attestation", "self_attestation_missing"),
    ("inconsistent", "inconsistent_values"),
    ("inactive", "contract_invalidated"),
    ("validator", "validator_version_mismatch"),
    ("field_scope", "field_scope_mismatch"),
])
def test_every_authorizing_defect_returns_value_free_typed_abstention(defect, reason):
    scope = _scope()
    record = ratified_between_group_contract(scope=scope)
    request = CspReadRequest(CONTRACT_TYPE, scope, REQUIRED_FIELDS,
                             "confounding_random_intercept_conditional")
    if defect in {"consumer", "attestation", "inactive", "validator"}:
        changes = {
            "consumer": {"authorized_consumers": ("someone_else",)},
            "attestation": {"authority_attested": False},
            "inactive": {"active": False},
            "validator": {"validator_version": "wrong-validator"},
        }[defect]
        record = replace(record, **changes)
    else:
        field = record.fields["may_rely_on_re_exogeneity"]
        changes = {
            "state": {"state": CspFieldState.PRESENTED},
            "confidence": {"confidence": "low"},
            "value": {"value": None},
            "teach_back": {"selected_teach_back_id": "may_rely"},
            "consequence": {"consequence_acknowledged": False},
            "evidence": {"evidence_ids": ()},
            "metadata": {"answer_event_id": None},
            "inconsistent": {"value": True},
            "field_scope": {"scope_fingerprint": "csp-scope:v1:stale"},
        }[defect]
        field = replace(field, **changes)
        record = replace(record, fields={**record.fields,
                                         "may_rely_on_re_exogeneity": field})
    result = read_ratified_contract((record,), request)
    assert result == CspAbstention(reason=reason, contract_id=record.contract_id)
    assert not hasattr(result, "values")


def test_unknown_contract_version_fails_closed_without_values():
    scope = _scope()
    result = read_ratified_contract(
        (), CspReadRequest("between_group_adjustment_obligation/v999", scope,
                           REQUIRED_FIELDS, "confounding_random_intercept_conditional"),
    )
    assert result == CspAbstention("unknown_contract_type", None)
    assert not hasattr(result, "values")


def test_scope_change_invalidates_fields_instead_of_migrating_them():
    scope = _scope()
    record = ratified_between_group_contract(scope=scope)
    changed = replace(scope, fitted_result_id="new-result")
    invalidated = invalidate_contract_for_scope(record, changed)
    assert invalidated.active is False
    assert invalidated.scope == scope
    assert all(field.state is CspFieldState.INVALIDATED
               for field in invalidated.fields.values())
    assert all(field.confidence == "low" for field in invalidated.fields.values())
