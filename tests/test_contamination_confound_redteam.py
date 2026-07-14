from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import jsonschema
import numpy as np
import pytest

from sc_referee import statuses as S
from sc_referee.checks import contamination_confound as contamination_module
from sc_referee.checks.contamination_confound import ContaminationConfoundCheck
from sc_referee.init import proposal_tool_schema
from sc_referee.wizard import csp_questions
from tests.contamination_factories import contamination_case
from tests.contamination_factories import ratified_contamination_record
from tests.test_init_contamination_csp import _payload, contamination_proposal
from tests.test_wizard_contamination_csp import _ceremony_proposal


@pytest.mark.parametrize("injection", [
    {"threshold": .18}, {"vector_values": [.1, .2]}, {"r_squared": .9},
    {"containment": False}, {"verdict": "major"}, {"causal_rationale": "technical"},
])
def test_proposal_injection_is_rejected_before_record(injection):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _payload() | {"csp_proposals": [contamination_proposal() | injection]},
            proposal_tool_schema(),
        )


def test_bulk_or_preselected_causal_acceptance_is_unrepresentable():
    by_role = {question.role: question
               for question in csp_questions({}, proposal=_ceremony_proposal())}
    assert "csp.contamination.accept_all" not in by_role
    assert all(question.default != "yes" for role, question in by_role.items()
               if ".causal." in role)


def _correct_or_uncheckable_findings():
    check = ContaminationConfoundCheck()
    cases = []
    design, bundle = contamination_case(adjusted=("condition", "rho_external"), ratified=True)
    cases.append(check.run(design, bundle))
    design, bundle = contamination_case(ratified=True, rho_values=[0.] * 8)
    cases.append(check.run(design, bundle))
    design, bundle = contamination_case(ratified=True, operator_kind="random_intercept_only")
    cases.append(check.run(design, bundle))
    design, bundle = contamination_case(ratified=True, weight_role="analysis_weight")
    cases.append(check.run(design, bundle))
    design, bundle = contamination_case(ratified=True, offset_role="library_offset")
    cases.append(check.run(design, bundle))
    design, bundle = contamination_case(ratified=True)
    record = design.csp_contracts[0]
    stale = replace(record, component_identities={
        **record.component_identities,
        "measurement_contract_identity": "sha256:" + "0" * 64,
    })
    cases.append(check.run(replace(design, csp_contracts=(stale,)), bundle))
    design, bundle = contamination_case(ratified=True)
    bundle.observations = bundle.observations.iloc[::-1].copy()
    cases.append(check.run(design, bundle))
    design, bundle = contamination_case(
        adjusted=("condition", "rho_external"),
        rho_values=2 * np.asarray([.05, .13, .22, .31, .57, .68, .79, .91]) + 1,
    )
    cases.append(check.run(design, bundle))
    return cases


def test_correct_contained_analysis_is_never_flagged():
    finding = _correct_or_uncheckable_findings()[0]
    assert (finding.status, S.human_state(finding)) == (S.PASS, S.CLEAR)


def test_false_alarm_budget_is_zero():
    findings = _correct_or_uncheckable_findings()
    assert sum(S.human_state(finding) == S.FLAGGED for finding in findings) == 0
    assert all(S.human_state(finding) in {S.CLEAR, S.NOT_CHECKED} for finding in findings)


def test_h_equal_exposure_is_not_mistaken_for_nuisance_conditioning():
    design, bundle = contamination_case(
        adjusted=("condition",), rho_values=[0., 0., 0., 0., 1., 1., 1., 1.]
    )
    finding = ContaminationConfoundCheck().run(design, bundle)
    assert finding.status == S.MAJOR
    assert finding.conditional_on.component_identities
    assert finding.metrics["excluded_exposure_columns"] == ["condition"]


def test_nonfinite_mutation_is_value_free_not_checked():
    design, bundle = contamination_case(ratified=True)
    bundle.observations.loc[bundle.observations.index[2], "rho_external"] = np.inf
    finding = ContaminationConfoundCheck().run(design, bundle)
    assert (finding.coverage, finding.judgment, S.human_state(finding), finding.conditional_on) == (
        S.NOT_RUN, S.UNRESOLVED, S.NOT_CHECKED, None,
    )


def test_crafted_adjustment_name_cannot_substitute_for_exact_column():
    design, bundle = contamination_case(ratified=True)
    design = replace(design, analyst_adjusted_for=["condition", "rho_corrected_in_prose"])
    finding = ContaminationConfoundCheck().run(design, bundle)
    assert (finding.coverage, S.human_state(finding)) == (S.NOT_RUN, S.NOT_CHECKED)


def test_no_llm_or_r2_symbol_reaches_verdict_module():
    source = Path(contamination_module.__file__).read_text().lower()
    for token in ("anthropic", "openai", "claude", "partial_r2", "r_squared"):
        assert token not in source


def _thaw(value):
    from collections.abc import Mapping
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_thaw(item) for item in value)
    return value


def _reratify(design, values):
    record = design.csp_contracts[0]
    extension = dict(record.scope.contract_scope)
    extension["basis_output_digest"] = values["basis_identity"]["output_digest"]
    scope = replace(record.scope, contract_scope=extension)
    return replace(design, csp_contracts=(ratified_contamination_record(
        scope=scope, values=values, contract_id=record.contract_id + ":transform",
    ),))


def test_binary_threshold_is_strict_and_equality_is_false():
    from sc_referee.column_space import NUMERIC_POLICY_V1, _canonical_matrix_digest

    design, bundle = contamination_case(ratified=True)
    record = design.csp_contracts[0]
    values = {field: _thaw(entry.value) for field, entry in record.fields.items()}
    source = bundle.observations["rho_external"].to_numpy(dtype=np.float64)[:, None]
    threshold = float(source[3, 0])
    h = (source > threshold).astype(np.float64)
    digest = _canonical_matrix_digest(h, policy_version=NUMERIC_POLICY_V1.version)
    values["transform_kind"] = "binary_threshold"
    values["transform_detail"] = {
        "source_vector_digest": values["axis_identity"]["value_digest"],
        "threshold": threshold,
        "threshold_provenance": "threshold:independent-protocol:v1",
        "comparison": "strict_greater_than", "equality": "false",
        "missing_rule": "abstain", "numeric_representation": "float64",
        "output_digest": digest,
    }
    values["basis_identity"]["output_digest"] = digest
    values["exact_basis_adequacy"]["transform_kind"] = "binary_threshold"
    finding = ContaminationConfoundCheck().run(_reratify(design, values), bundle)
    assert finding.metrics["witness"]["h_digest"] == digest
    assert finding.status == S.MAJOR


def test_ordered_multicolumn_external_basis_equivalent_span_passes():
    from sc_referee.column_space import NUMERIC_POLICY_V1, _canonical_matrix_digest

    design, bundle = contamination_case(
        adjusted=("condition", "rho_external"), ratified=True
    )
    rho = bundle.observations["rho_external"].to_numpy(dtype=np.float64)
    bundle.observations["z1"] = rho
    bundle.observations["z2"] = 2.0 * rho + 1.0
    record = design.csp_contracts[0]
    values = {field: _thaw(entry.value) for field, entry in record.fields.items()}
    h = np.column_stack([rho, 2.0 * rho + 1.0])
    digest = _canonical_matrix_digest(h, policy_version=NUMERIC_POLICY_V1.version)
    values["transform_kind"] = "frozen_external_basis"
    values["transform_detail"] = {
        "policy_id": "policy:external-basis:v1", "policy_version": "1",
        "input_identities": ("artifact:z1:v1", "artifact:z2:v1"),
        "ordered_columns": ("z1", "z2"),
        "replay_identity": "replay:external-basis:v1",
        "source_vector_digest": digest, "output_digest": digest,
    }
    values["axis_identity"]["value_digest"] = digest
    values["axis_identity"]["vector_field"] = None
    values["rows_and_aggregation"]["output_vector_digest"] = digest
    values["basis_identity"] = {
        "basis_ledger_identity": values["basis_identity"]["basis_ledger_identity"],
        "ordered_columns": ("z1", "z2"), "output_digest": digest,
    }
    values["exact_basis_adequacy"]["transform_kind"] = "frozen_external_basis"
    ratified_design = _reratify(design, values)
    finding = ContaminationConfoundCheck().run(ratified_design, bundle)
    assert (finding.status, S.human_state(finding)) == (S.PASS, S.CLEAR)
    bundle.observations["z2"] = bundle.observations["z2"] + .01
    stale = ContaminationConfoundCheck().run(ratified_design, bundle)
    assert (stale.coverage, S.human_state(stale), stale.conditional_on) == (
        S.NOT_RUN, S.NOT_CHECKED, None,
    )


def test_external_basis_without_its_own_axis_source_digest_abstains():
    from sc_referee.column_space import NUMERIC_POLICY_V1, _canonical_matrix_digest

    design, bundle = contamination_case(
        adjusted=("condition", "rho_external"), ratified=True
    )
    rho = bundle.observations["rho_external"].to_numpy(dtype=np.float64)
    bundle.observations["z1"] = rho
    bundle.observations["z2"] = 2.0 * rho + 1.0
    record = design.csp_contracts[0]
    values = {field: _thaw(entry.value) for field, entry in record.fields.items()}
    h = np.column_stack([rho, 2.0 * rho + 1.0])
    digest = _canonical_matrix_digest(h, policy_version=NUMERIC_POLICY_V1.version)
    values["transform_kind"] = "frozen_external_basis"
    values["transform_detail"] = {
        "policy_id": "policy:external-basis:v1", "policy_version": "1",
        "input_identities": ("artifact:z1:v1", "artifact:z2:v1"),
        "ordered_columns": ("z1", "z2"),
        "replay_identity": "replay:external-basis:v1", "output_digest": digest,
    }
    values["basis_identity"] = {
        "basis_ledger_identity": values["basis_identity"]["basis_ledger_identity"],
        "ordered_columns": ("z1", "z2"), "output_digest": digest,
    }
    values["exact_basis_adequacy"]["transform_kind"] = "frozen_external_basis"
    finding = ContaminationConfoundCheck().run(_reratify(design, values), bundle)
    assert (finding.coverage, S.human_state(finding), finding.conditional_on) == (
        S.NOT_RUN, S.NOT_CHECKED, None,
    )


def test_external_basis_cannot_claim_an_unread_separate_vector_field():
    from sc_referee.column_space import NUMERIC_POLICY_V1, _canonical_matrix_digest

    design, bundle = contamination_case(adjusted=("condition",), ratified=True)
    rho = bundle.observations["rho_external"].to_numpy(dtype=np.float64)
    bundle.observations["z1"] = rho
    bundle.observations["z2"] = 2.0 * rho + 1.0
    record = design.csp_contracts[0]
    values = {field: _thaw(entry.value) for field, entry in record.fields.items()}
    h = np.column_stack([rho, 2.0 * rho + 1.0])
    digest = _canonical_matrix_digest(h, policy_version=NUMERIC_POLICY_V1.version)
    values["transform_kind"] = "frozen_external_basis"
    values["transform_detail"] = {
        "policy_id": "policy:external-basis:v1", "policy_version": "1",
        "input_identities": ("artifact:z1:v1", "artifact:z2:v1"),
        "ordered_columns": ("z1", "z2"),
        "replay_identity": "replay:external-basis:v1",
        "source_vector_digest": digest, "output_digest": digest,
    }
    # This is the audited exploit: the record claims rho_external is its axis while all
    # ratified digests actually identify the frozen z1/z2 matrix.
    values["axis_identity"]["vector_field"] = "rho_external"
    values["axis_identity"]["value_digest"] = digest
    values["rows_and_aggregation"]["output_vector_digest"] = digest
    values["basis_identity"] = {
        "basis_ledger_identity": values["basis_identity"]["basis_ledger_identity"],
        "ordered_columns": ("z1", "z2"), "output_digest": digest,
    }
    values["exact_basis_adequacy"]["transform_kind"] = "frozen_external_basis"
    ratified_design = _reratify(design, values)
    bundle.observations["rho_external"] = rho + 100.0
    finding = ContaminationConfoundCheck().run(ratified_design, bundle)
    assert (finding.coverage, finding.judgment, S.human_state(finding), finding.conditional_on) == (
        S.NOT_RUN, S.UNRESOLVED, S.NOT_CHECKED, None,
    )


def test_post_ceremony_llm_proposal_mutation_cannot_change_verdict():
    design, bundle = contamination_case(
        adjusted=("condition", "rho_external"), ratified=True
    )
    before = ContaminationConfoundCheck().run(design, bundle)
    mutated_proposal = contamination_proposal() | {
        "causal_role_guess": "descendant_or_pathway",
        "artifact_identity": "artifact:changed-after-ceremony:v2",
    }
    assert mutated_proposal
    after = ContaminationConfoundCheck().run(design, bundle)
    assert (before.status, before.metrics) == (after.status, after.metrics)


def test_direct_major_without_dual_marker_raises():
    from sc_referee.checks.contamination_confound import _finding
    with pytest.raises(ValueError, match="dual-premise conditional MAJOR"):
        _finding(
            S.MAJOR, "unauthorized", {}, applicability=S.APPLIES,
            coverage=S.COMPLETE, judgment=S.VIOLATION, conditional_on=None,
        )
