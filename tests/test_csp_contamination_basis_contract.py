from __future__ import annotations

import pytest
from dataclasses import replace

from sc_referee.csp_contracts import get_manifest
from sc_referee.csp_contracts.contamination_basis_obligation_v1 import (
    CAUSAL_FIELDS,
    MEASUREMENT_FIELDS,
    validate_values,
)
from tests.contamination_factories import complete_contamination_values
from sc_referee.csp import RatifiedFactSet, read_ratified_contract
from tests.contamination_factories import (
    contamination_read_request,
    contamination_scope,
    ratified_contamination_record,
    with_field_answer,
)


def test_contract_is_one_atomic_c_stage_2_record():
    manifest = get_manifest("contamination_basis_obligation/v1")
    assert manifest.authorized_consumer == "contamination_confound"
    assert manifest.stage == "C-Stage-2"
    assert manifest.required_fields == MEASUREMENT_FIELDS + CAUSAL_FIELDS
    assert dict(manifest.component_field_groups) == {
        "measurement_contract_identity": MEASUREMENT_FIELDS,
        "causal_contract_identity": CAUSAL_FIELDS,
    }


@pytest.mark.parametrize(
    "kind",
    [
        "ambient_enrichment",
        "low_observed_expression",
        "marker_list_omission",
        "algorithm_label",
        "exposure_separation",
        "non_containment",
        "desired_verdict",
    ],
)
def test_insufficient_measurement_signal_never_authorizes(kind):
    values = complete_contamination_values()
    values["positive_evidence"] = {"kind": kind, "records": ()}
    assert "positive_nonexpression_evidence_missing" in validate_values(values)


@pytest.mark.parametrize(
    "reason", ["association", "r_squared", "coefficient_movement", "technical"]
)
def test_forbidden_causal_reason_never_authorizes(reason):
    values = complete_contamination_values()
    values["required_adjustment"] = {"required": True, "basis": reason}
    assert "design_based_adjustment_reason_missing" in validate_values(values)


def test_contamination_kind_empty_droplet_per_donor_axis_is_admissible():
    values = complete_contamination_values()
    assert values["measurement_kind"] != "expression_proxy_with_positive_nonexpression"
    assert values["positive_evidence"]["kind"] == "empty_droplet_derived_external_fraction"
    assert validate_values(values) == ()


@pytest.mark.parametrize("field", MEASUREMENT_FIELDS + CAUSAL_FIELDS)
def test_every_field_is_required_and_structured(field):
    values = complete_contamination_values()
    del values[field]
    assert validate_values(values)


def test_continuous_transform_rejects_threshold_fields():
    values = complete_contamination_values()
    values["transform_detail"] = dict(values["transform_detail"], threshold=0.18)
    assert "continuous_transform_detail_invalid" in validate_values(values)


def test_external_transform_and_basis_column_order_must_match_exactly():
    values = complete_contamination_values()
    values["transform_kind"] = "frozen_external_basis"
    values["axis_identity"]["vector_field"] = None
    values["transform_detail"] = {
        "policy_id": "policy:external-basis:v1", "policy_version": "1",
        "input_identities": ("artifact:z1:v1", "artifact:z2:v1"),
        "ordered_columns": ("z1", "z2"),
        "replay_identity": "replay:external-basis:v1",
        "source_vector_digest": values["basis_identity"]["output_digest"],
        "output_digest": values["basis_identity"]["output_digest"],
    }
    values["basis_identity"] = {
        **values["basis_identity"], "ordered_columns": ("z2", "z1"),
    }
    values["exact_basis_adequacy"] = {
        **values["exact_basis_adequacy"], "transform_kind": "frozen_external_basis",
    }
    assert "external_basis_column_order_mismatch" in validate_values(values)


@pytest.mark.parametrize("threshold", [float("nan"), float("inf"), float("-inf")])
def test_binary_threshold_must_be_finite_and_abstains_without_hash_exception(threshold):
    from dataclasses import replace

    from sc_referee import statuses as S
    from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
    from tests.contamination_factories import contamination_case
    from tests.test_contamination_confound_redteam import _thaw

    design, bundle = contamination_case(ratified=True)
    record = design.csp_contracts[0]
    values = {field: _thaw(entry.value) for field, entry in record.fields.items()}
    values["transform_kind"] = "binary_threshold"
    values["transform_detail"] = {
        "source_vector_digest": values["axis_identity"]["value_digest"],
        "threshold": threshold,
        "threshold_provenance": "threshold:independent-protocol:v1",
        "comparison": "strict_greater_than", "equality": "false",
        "missing_rule": "abstain", "numeric_representation": "float64",
        "output_digest": values["basis_identity"]["output_digest"],
    }
    values["exact_basis_adequacy"]["transform_kind"] = "binary_threshold"
    assert "binary_transform_detail_invalid" in validate_values(values)
    fields = {
        field_id: replace(record.fields[field_id], value=value)
        for field_id, value in values.items()
    }
    invalid = replace(record, fields=fields, component_identities={})
    finding = ContaminationConfoundCheck().run(
        replace(design, csp_contracts=(invalid,)), bundle
    )
    assert (finding.coverage, S.human_state(finding), finding.conditional_on) == (
        S.NOT_RUN, S.NOT_CHECKED, None,
    )


def test_reader_recomputes_both_identities_atomically():
    record = ratified_contamination_record()
    got = read_ratified_contract((record,), contamination_read_request(record.scope))
    assert isinstance(got, RatifiedFactSet)
    assert set(got.component_identities) == {
        "measurement_contract_identity", "causal_contract_identity"
    }
    stale = replace(record, component_identities={
        **record.component_identities,
        "causal_contract_identity": "sha256:" + "0" * 64,
    })
    got = read_ratified_contract((stale,), contamination_read_request(stale.scope))
    assert got.reason == "component_identity_mismatch"
    assert not hasattr(got, "values")


def test_complete_contamination_kind_axis_releases_ratified_fact_set():
    record = ratified_contamination_record(values=complete_contamination_values())
    got = read_ratified_contract((record,), contamination_read_request(record.scope))
    assert isinstance(got, RatifiedFactSet)
    assert got.values["positive_evidence"]["kind"] == "empty_droplet_derived_external_fraction"


@pytest.mark.parametrize(
    "field", ["non_descendancy", "outside_estimand_pathway", "required_adjustment"]
)
def test_benign_refutation_is_value_free(field):
    record = with_field_answer(
        ratified_contamination_record(), field,
        state="declined_for_consumer", value=None,
    )
    got = read_ratified_contract((record,), contamination_read_request(record.scope))
    assert got.kind == "benign_non_authorization"
    assert got.reason == f"benign_non_authorization:{field}"
    assert not hasattr(got, "values")


def test_not_sure_remains_needs_evidence_and_value_free():
    record = with_field_answer(
        ratified_contamination_record(), "pre_exposure", state="unresolved", value=None
    )
    got = read_ratified_contract((record,), contamination_read_request(record.scope))
    assert got.kind == "needs_evidence"
    assert not hasattr(got, "values")


def test_contamination_scope_is_complete_and_closed():
    scope = contamination_scope()
    changed = dict(scope.contract_scope)
    changed.pop("basis_output_digest")
    with pytest.raises(ValueError, match="complete and closed"):
        replace(scope, contract_scope=changed)
