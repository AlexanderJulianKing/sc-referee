from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.prospective_qualification import (
    REQUIRED_CELL_TYPES,
    ProspectiveQualificationError,
    freeze_pilot_threshold_decision,
    freeze_prospective_qualification_protocol,
    seal_prospective_outcome_ledger,
)

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.scientific_checks.profiles import default_scientific_check_registry

_DETECTOR_FROZEN_AT = "2026-08-03T12:00:00Z"
_ASSIGNED_AT = "2026-08-03T12:30:00Z"
_PROTOCOL_FROZEN_AT = "2026-08-03T13:00:00Z"
_PILOT_LABEL_AT = "2026-08-04T12:00:00Z"
_PILOT_COMPLETED_AT = "2026-08-04T13:00:00Z"
_PILOT_SEALED_AT = "2026-08-04T14:00:00Z"
_THRESHOLD_AT = "2026-08-04T15:00:00Z"
_HELDOUT_LABEL_AT = "2026-08-05T12:00:00Z"
_HELDOUT_COMPLETED_AT = "2026-08-05T13:00:00Z"
_HELDOUT_SEALED_AT = "2026-08-05T14:00:00Z"


def _digest(value: str) -> str:
    return sha256_digest(value)


def _participant(identifier: str, role: str, provider: str) -> dict[str, str]:
    return {
        "participant_id": identifier,
        "role": role,
        "provider": provider,
        "execution_context_id": f"context:{identifier}",
        "identity_evidence_digest": _digest(f"identity:{identifier}"),
    }


def _specification(*, development: bool = False) -> dict[str, Any]:
    participants = [
        _participant("actor:author-a", "author", "author-provider-a"),
        _participant("actor:author-b", "author", "author-provider-b"),
        _participant("actor:s1-a1", "stage1_reviewer", "review-provider-a"),
        _participant("actor:s1-a2", "stage1_reviewer", "review-provider-a"),
        _participant("actor:s1-b1", "stage1_reviewer", "review-provider-b"),
        _participant("actor:s1-b2", "stage1_reviewer", "review-provider-b"),
        _participant("actor:s2-c", "stage2_reviewer", "review-provider-c"),
        _participant("actor:s2-d", "stage2_reviewer", "review-provider-d"),
        _participant("actor:detector", "detector_implementer", "implementation-provider"),
    ]
    envelopes = [
        {
            "envelope_id": f"relation:{index:02d}",
            "check_id": f"check:atomic-{index:02d}",
            "candidate_id": f"candidate:atomic-{index:02d}",
            "binding_digest": _digest(f"binding:{index}"),
        }
        for index in range(10)
    ]
    blocks = [
        {"block_id": "block:pilot", "evidence_role": "threshold_pilot"},
        {"block_id": "block:heldout", "evidence_role": "qualification_heldout"},
    ]
    if development:
        blocks.append({"block_id": "block:development", "evidence_role": "development_regression"})
    assignments: list[dict[str, Any]] = []
    counter = 0
    for block in blocks:
        for envelope in envelopes:
            error_id = stable_id("case", "qualification-study", str(counter))
            for cell_type in REQUIRED_CELL_TYPES:
                case_id = stable_id("case", "qualification-study", str(counter))
                counter += 1
                assignments.append(
                    {
                        "case_id": case_id,
                        "envelope_id": envelope["envelope_id"],
                        "block_id": block["block_id"],
                        "cell_type": cell_type,
                        "source_kind": (
                            "internal_development"
                            if block["evidence_role"] == "development_regression"
                            else "independent_prospective"
                        ),
                        "reference_case_id": (
                            error_id
                            if cell_type in {"corrected_twin", "renamed_implementation"}
                            else None
                        ),
                        "author_id": (
                            "actor:author-b"
                            if cell_type == "renamed_implementation"
                            else "actor:author-a"
                        ),
                        "stage1_reviewer_ids": [
                            "actor:s1-a1",
                            "actor:s1-a2",
                            "actor:s1-b1",
                            "actor:s1-b2",
                        ],
                        "stage2_reviewer_ids": ["actor:s2-c", "actor:s2-d"],
                        "authoring_brief_digest": _digest(f"brief:{case_id}"),
                        "assigned_at": _ASSIGNED_AT,
                    }
                )
    return {
        "protocol_id": "prospective-protocol:ten-relations-v1",
        "expected_envelope_count": 10,
        "detector_lock": {
            "detector_id": "detector:generic-method-conflict",
            "detector_version": "0.3.0",
            "detector_manifest_digest": _digest("manifest"),
            "implementation_digest": _digest("implementation"),
            "frozen_at": _DETECTOR_FROZEN_AT,
        },
        "participants": participants,
        "envelopes": envelopes,
        "blocks": blocks,
        "assignments": assignments,
        "governance": {
            "all_outcomes_retained": True,
            "no_replacement": True,
            "public_benchmark_qualification_excluded": True,
            "development_case_qualification_excluded": True,
            "detector_implementers_label_blind": True,
            "review_detector_output_hidden": True,
            "independent_review_contexts_required": True,
        },
    }


def _protocol(*, development: bool = False) -> dict[str, Any]:
    return freeze_prospective_qualification_protocol(
        _specification(development=development), frozen_at=_PROTOCOL_FROZEN_AT
    )


def _expected_label(cell_type: str) -> str:
    return {
        "error_bearing": "issue_present",
        "corrected_twin": "issue_absent",
        "valid_alternative": "issue_absent",
        "hard_negative": "issue_absent",
        "ambiguous": "indeterminate",
        "unsupported": "unsupported",
        "renamed_implementation": "issue_present",
    }[cell_type]


def _outcomes(
    protocol: dict[str, Any], block_id: str, *, label_at: str, completed_at: str
) -> list[dict[str, Any]]:
    result = []
    for assignment in protocol["assignments"]:
        if assignment["block_id"] != block_id:
            continue
        label = _expected_label(str(assignment["cell_type"]))
        result.append(
            {
                "case_id": assignment["case_id"],
                "retention_disposition": "retained_complete",
                "contamination_status": "clean",
                "author_authentication_status": "externally_verified",
                "review_authentication_status": "externally_verified",
                "scientific_label": label,
                "detector_observation": (
                    "evaluation_finding_candidate"
                    if label == "issue_present"
                    else (
                        "no_issue_detected_within_coverage"
                        if label == "issue_absent"
                        else (
                            "insufficient_semantics"
                            if label == "indeterminate"
                            else "unsupported_path"
                        )
                    )
                ),
                "label_frozen_at": label_at,
                "completed_at": completed_at,
                "artifact_digests": {
                    key: _digest(f"{assignment['case_id']}:{key}")
                    for key in (
                        "case_material",
                        "stage1_panel",
                        "stage2_panel",
                        "scientific_label",
                        "detector_output",
                    )
                },
            }
        )
    return result


def _pilot_ledger(protocol: dict[str, Any]) -> dict[str, Any]:
    return seal_prospective_outcome_ledger(
        protocol,
        _outcomes(
            protocol,
            "block:pilot",
            label_at=_PILOT_LABEL_AT,
            completed_at=_PILOT_COMPLETED_AT,
        ),
        block_id="block:pilot",
        sealed_at=_PILOT_SEALED_AT,
    )


def _threshold_decision(protocol: dict[str, Any]) -> dict[str, Any]:
    return freeze_pilot_threshold_decision(
        protocol,
        _pilot_ledger(protocol),
        {
            "decision_id": "threshold-decision:ten-relations-v1",
            "metric_definitions": {
                "sensitivity": (
                    "adjudicated issue-present cases with an "
                    "evaluation_finding_candidate detector state"
                ),
                "false_accusations": (
                    "adjudicated non-issue cases with an "
                    "evaluation_finding_candidate detector state"
                ),
            },
            "promotion_thresholds": {
                "minimum_sensitivity": 0.9,
                "maximum_false_accusations": 0,
            },
            "zero_high_severity_false_accusations_required": True,
            "approved_for_heldout_opening": True,
        },
        decided_at=_THRESHOLD_AT,
    )


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(value) + "\n" for value in values), encoding="utf-8")


def test_freeze_requires_complete_ten_relation_control_matrix() -> None:
    protocol = _protocol()
    assert protocol["coverage"] == {
        "required_cell_types": list(REQUIRED_CELL_TYPES),
        "matrix_blocks": {
            "block:heldout": "qualification_heldout",
            "block:pilot": "threshold_pilot",
        },
        "required_case_count": 140,
        "matrix_complete": True,
    }
    assert protocol["qualification_authority"] == "none_protocol_only"
    assert protocol["study_state"] == "assignments_frozen_labels_unopened"


def test_ten_envelope_template_matches_current_generic_registry() -> None:
    template_path = (
        Path(__file__).resolve().parents[1]
        / "evaluation"
        / "prospective-qualification-v1"
        / "ten-envelope-study.template.json"
    )
    template = json.loads(template_path.read_text(encoding="utf-8"))
    expected_digest = template.pop("template_digest")
    assert semantic_digest(template) == expected_digest
    assert template["qualification_authority"] == "none_template_only"
    assert template["minimum_frozen_case_count"] == 140
    assert len(template["envelopes"]) == 10

    registry = default_scientific_check_registry()
    modules = {module.manifest.check_id: module for module in registry.modules}
    bindings = {binding.check_id: binding for binding in registry.method_conflict_bindings}
    for envelope in template["envelopes"]:
        module = modules[envelope["check_id"]]
        assert envelope["candidate_id"] in {
            candidate.candidate_id for candidate in module.manifest.requirement_candidates
        }
        assert (
            semantic_digest(bindings[envelope["check_id"]].to_dict()) == envelope["binding_digest"]
        )
    mvmr = next(
        item
        for item in template["envelopes"]
        if item["check_id"] == "check:phase-split-mvmr-instrument-construction"
    )
    assert mvmr["candidate_id"] == ("phase1-ld-conditional-signals-phase2-joint-coefficients")
    assert "genebench" not in json.dumps(template).lower()


def test_protocol_artifact_matches_evaluation_private_schema() -> None:
    root = Path(__file__).resolve().parents[1] / "evaluation" / "prospective-qualification-v1"
    schema = json.loads(
        (root / "prospective-qualification-protocol.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(_protocol())


def test_freeze_rejects_missing_cell_without_replacement() -> None:
    spec = _specification()
    spec["assignments"].pop()
    with pytest.raises(ProspectiveQualificationError, match="exactly one of every control cell"):
        freeze_prospective_qualification_protocol(spec, frozen_at=_PROTOCOL_FROZEN_AT)


def test_freeze_rejects_development_case_in_heldout_block() -> None:
    spec = _specification()
    heldout = next(item for item in spec["assignments"] if item["block_id"] == "block:heldout")
    heldout["source_kind"] = "public_development"
    with pytest.raises(ProspectiveQualificationError, match="independently authored prospective"):
        freeze_prospective_qualification_protocol(spec, frozen_at=_PROTOCOL_FROZEN_AT)


def test_freeze_rejects_role_or_context_reuse() -> None:
    spec = _specification()
    spec["participants"][1]["execution_context_id"] = spec["participants"][0][
        "execution_context_id"
    ]
    with pytest.raises(ProspectiveQualificationError, match="globally unique"):
        freeze_prospective_qualification_protocol(spec, frozen_at=_PROTOCOL_FROZEN_AT)


def test_freeze_requires_independently_authored_renamed_case() -> None:
    spec = _specification()
    renamed = next(
        item for item in spec["assignments"] if item["cell_type"] == "renamed_implementation"
    )
    renamed["author_id"] = "actor:author-a"
    with pytest.raises(ProspectiveQualificationError, match="author independent"):
        freeze_prospective_qualification_protocol(spec, frozen_at=_PROTOCOL_FROZEN_AT)


def test_outcome_ledger_refuses_omission_and_duplicate() -> None:
    protocol = _protocol()
    outcomes = _outcomes(
        protocol,
        "block:pilot",
        label_at=_PILOT_LABEL_AT,
        completed_at=_PILOT_COMPLETED_AT,
    )
    with pytest.raises(ProspectiveQualificationError, match="missing="):
        seal_prospective_outcome_ledger(
            protocol,
            outcomes[:-1],
            block_id="block:pilot",
            sealed_at=_PILOT_SEALED_AT,
        )
    with pytest.raises(ProspectiveQualificationError, match="Duplicate retained outcomes"):
        seal_prospective_outcome_ledger(
            protocol,
            [*outcomes, deepcopy(outcomes[0])],
            block_id="block:pilot",
            sealed_at=_PILOT_SEALED_AT,
        )


def test_pilot_ledger_and_threshold_decision_match_schemas() -> None:
    protocol = _protocol()
    ledger = _pilot_ledger(protocol)
    decision = _threshold_decision(protocol)
    root = Path(__file__).resolve().parents[1] / "evaluation" / "prospective-qualification-v1"
    ledger_schema = json.loads(
        (root / "prospective-qualification-outcome-ledger.schema.json").read_text(encoding="utf-8")
    )
    decision_schema = json.loads(
        (root / "prospective-pilot-threshold-decision.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(ledger_schema).validate(ledger)
    Draft202012Validator(decision_schema).validate(decision)
    assert ledger["retention_summary"]["all_assigned_outcomes_retained"] is True
    assert decision["qualification_authority"] == "none_thresholds_only"


def test_heldout_ledger_requires_threshold_freeze_before_labels() -> None:
    protocol = _protocol()
    outcomes = _outcomes(
        protocol,
        "block:heldout",
        label_at=_HELDOUT_LABEL_AT,
        completed_at=_HELDOUT_COMPLETED_AT,
    )
    with pytest.raises(ProspectiveQualificationError, match="requires the frozen pilot"):
        seal_prospective_outcome_ledger(
            protocol,
            outcomes,
            block_id="block:heldout",
            sealed_at=_HELDOUT_SEALED_AT,
        )
    decision = _threshold_decision(protocol)
    outcomes[0]["label_frozen_at"] = _PILOT_LABEL_AT
    with pytest.raises(ProspectiveQualificationError, match="before its permitted boundary"):
        seal_prospective_outcome_ledger(
            protocol,
            outcomes,
            block_id="block:heldout",
            sealed_at=_HELDOUT_SEALED_AT,
            threshold_decision=decision,
            pilot_ledger=_pilot_ledger(protocol),
        )


def test_heldout_ledger_marks_only_clean_authenticated_confirmed_cases_eligible() -> None:
    protocol = _protocol()
    outcomes = _outcomes(
        protocol,
        "block:heldout",
        label_at=_HELDOUT_LABEL_AT,
        completed_at=_HELDOUT_COMPLETED_AT,
    )
    by_case = {item["case_id"]: item for item in outcomes}
    assignments = [item for item in protocol["assignments"] if item["block_id"] == "block:heldout"]
    error_case = next(item for item in assignments if item["cell_type"] == "error_bearing")
    corrected_case = next(item for item in assignments if item["cell_type"] == "corrected_twin")
    alternative_case = next(
        item for item in assignments if item["cell_type"] == "valid_alternative"
    )
    hard_negative_case = next(item for item in assignments if item["cell_type"] == "hard_negative")
    by_case[error_case["case_id"]]["scientific_label"] = "issue_absent"
    by_case[corrected_case["case_id"]]["contamination_status"] = "contaminated"
    by_case[corrected_case["case_id"]]["retention_disposition"] = "retained_contaminated"
    by_case[alternative_case["case_id"]]["review_authentication_status"] = "unverified"
    by_case[hard_negative_case["case_id"]]["author_authentication_status"] = "unverified"
    ledger = seal_prospective_outcome_ledger(
        protocol,
        outcomes,
        block_id="block:heldout",
        sealed_at=_HELDOUT_SEALED_AT,
        threshold_decision=_threshold_decision(protocol),
        pilot_ledger=_pilot_ledger(protocol),
    )
    assert len(ledger["outcomes"]) == 70
    assert ledger["retention_summary"]["retained_outcome_count"] == 70
    assert ledger["retention_summary"]["cell_mismatch_or_unavailable_count"] == 1
    assert (
        sum(
            item["metric_eligibility"] == "included_heldout_metric_input"
            for item in ledger["outcomes"]
        )
        == 66
    )
    assert ledger["qualification_authority"] == "none_metric_input_only"
    assert ledger["promotion_decision_present"] is False


def test_development_block_is_retained_but_always_metric_ineligible() -> None:
    protocol = _protocol(development=True)
    ledger = seal_prospective_outcome_ledger(
        protocol,
        _outcomes(
            protocol,
            "block:development",
            label_at=_PILOT_LABEL_AT,
            completed_at=_PILOT_COMPLETED_AT,
        ),
        block_id="block:development",
        sealed_at=_PILOT_SEALED_AT,
    )
    assert {item["metric_eligibility"] for item in ledger["outcomes"]} == {
        "excluded_nonqualification_block"
    }


def test_digest_mutation_is_rejected() -> None:
    protocol = _protocol()
    protocol["assignments"][0]["author_id"] = "actor:author-b"
    with pytest.raises(ProspectiveQualificationError, match="digest does not replay"):
        seal_prospective_outcome_ledger(
            protocol,
            [],
            block_id="block:pilot",
            sealed_at=_PILOT_SEALED_AT,
        )


def test_cli_freezes_protocol_pilot_thresholds_and_heldout_ledger(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    protocol_path = tmp_path / "protocol.json"
    pilot_outcomes_path = tmp_path / "pilot-outcomes.jsonl"
    pilot_ledger_path = tmp_path / "pilot-ledger.json"
    decision_spec_path = tmp_path / "threshold-spec.json"
    decision_path = tmp_path / "threshold-decision.json"
    heldout_outcomes_path = tmp_path / "heldout-outcomes.jsonl"
    heldout_ledger_path = tmp_path / "heldout-ledger.json"
    _write_json(spec_path, _specification())

    assert (
        evaluation_main(
            [
                "freeze-prospective-protocol",
                "--spec",
                str(spec_path),
                "--frozen-at",
                _PROTOCOL_FROZEN_AT,
                "--output",
                str(protocol_path),
            ]
        )
        == 0
    )
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    _write_jsonl(
        pilot_outcomes_path,
        _outcomes(
            protocol,
            "block:pilot",
            label_at=_PILOT_LABEL_AT,
            completed_at=_PILOT_COMPLETED_AT,
        ),
    )
    assert (
        evaluation_main(
            [
                "seal-prospective-outcomes",
                "--protocol",
                str(protocol_path),
                "--outcomes-jsonl",
                str(pilot_outcomes_path),
                "--block-id",
                "block:pilot",
                "--sealed-at",
                _PILOT_SEALED_AT,
                "--output",
                str(pilot_ledger_path),
            ]
        )
        == 0
    )
    _write_json(
        decision_spec_path,
        {
            "decision_id": "threshold-decision:ten-relations-v1",
            "metric_definitions": {"finding_rate": "frozen case outcome proportion"},
            "promotion_thresholds": {"minimum_finding_rate_on_issues": 0.9},
            "zero_high_severity_false_accusations_required": True,
            "approved_for_heldout_opening": True,
        },
    )
    assert (
        evaluation_main(
            [
                "freeze-pilot-thresholds",
                "--protocol",
                str(protocol_path),
                "--pilot-ledger",
                str(pilot_ledger_path),
                "--decision-spec",
                str(decision_spec_path),
                "--decided-at",
                _THRESHOLD_AT,
                "--output",
                str(decision_path),
            ]
        )
        == 0
    )
    _write_jsonl(
        heldout_outcomes_path,
        _outcomes(
            protocol,
            "block:heldout",
            label_at=_HELDOUT_LABEL_AT,
            completed_at=_HELDOUT_COMPLETED_AT,
        ),
    )
    assert (
        evaluation_main(
            [
                "seal-prospective-outcomes",
                "--protocol",
                str(protocol_path),
                "--outcomes-jsonl",
                str(heldout_outcomes_path),
                "--block-id",
                "block:heldout",
                "--sealed-at",
                _HELDOUT_SEALED_AT,
                "--threshold-decision",
                str(decision_path),
                "--pilot-ledger",
                str(pilot_ledger_path),
                "--output",
                str(heldout_ledger_path),
            ]
        )
        == 0
    )
    heldout = json.loads(heldout_ledger_path.read_text(encoding="utf-8"))
    assert heldout["retention_summary"]["retained_outcome_count"] == 70
    assert heldout["promotion_decision_present"] is False
