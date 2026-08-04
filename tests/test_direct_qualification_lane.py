from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from sc_referee_evaluation.direct_qualification_lane import (
    DirectQualificationLaneError,
    freeze_authoring_brief_manifest,
    freeze_direct_qualification_lane,
    freeze_participant_enrollment,
    validate_authoring_brief_manifest,
    validate_direct_qualification_lane,
    validate_participant_enrollment,
)

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id

FROZEN_AT = "2026-08-05T01:00:00Z"
ASSIGNED_AT = "2026-08-05T00:30:00Z"
DETECTOR_FROZEN_AT = "2026-08-04T22:33:52Z"
DIGEST = "sha256:" + "a" * 64
ENVELOPE = {
    "envelope_id": "relation-envelope:complete-domain-exposure-denominator",
    "check_id": "check:complete-domain-exposure-denominator",
    "candidate_id": "complete-declared-domain-exposure",
    "binding_digest": "sha256:" + "b" * 64,
}
CELL_TYPES = (
    "error_bearing",
    "corrected_twin",
    "valid_alternative",
    "hard_negative",
    "ambiguous",
    "unsupported",
    "renamed_implementation",
)


def _precase() -> dict[str, Any]:
    record: dict[str, Any] = {
        "artifact_kind": "direct_envelope_precase_freeze",
        "metric_case_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "envelope": deepcopy(ENVELOPE),
        "detector": {
            "detector_id": "detector:bounded-analysis-method-conflict",
            "detector_version": "0.3.0",
            "detector_manifest_digest": "sha256:" + "c" * 64,
            "implementation_digest": "sha256:" + "d" * 64,
        },
    }
    record["freeze_digest"] = semantic_digest(record)
    return record


def _participant(identifier: str, role: str, provider: str) -> dict[str, str]:
    return {
        "participant_id": identifier,
        "role": role,
        "provider": provider,
        "agent_surface": "qualification test agent",
        "agent_version": "1.0.0",
        "model_name": "test model",
        "model_id": f"model:{provider}",
        "reasoning_configuration": "high",
        "execution_context_id": f"context:{identifier}",
        "system_prompt_digest": sha256_digest(f"system:{role}"),
        "tool_policy_digest": sha256_digest(f"tools:{role}"),
        "environment_digest": sha256_digest(f"environment:{provider}"),
        "calibration_suite_digest": sha256_digest("calibration:v1"),
        "calibration_status": (
            "required_before_participation"
            if role in {"stage1_reviewer", "stage2_reviewer"}
            else "not_applicable"
        ),
    }


def _enrollment_spec() -> dict[str, Any]:
    return {
        "enrollment_id": "enrollment:first-lane-v1",
        "precase_freeze_digest": _precase()["freeze_digest"],
        "participants": [
            _participant("actor:author-a", "author", "Provider A"),
            _participant("actor:author-b", "author", "Provider B"),
            _participant("actor:s1-a1", "stage1_reviewer", "Provider A"),
            _participant("actor:s1-a2", "stage1_reviewer", "Provider A"),
            _participant("actor:s1-b1", "stage1_reviewer", "Provider B"),
            _participant("actor:s1-b2", "stage1_reviewer", "Provider B"),
            _participant("actor:s2-a", "stage2_reviewer", "Provider A"),
            _participant("actor:s2-b", "stage2_reviewer", "Provider B"),
            _participant("actor:validator", "evidence_validator", "Deterministic"),
            _participant("actor:detector", "detector_implementer", "Provider A"),
        ],
    }


def _case_ids() -> list[str]:
    return [stable_id("case", "first-direct-lane", str(index)) for index in range(14)]


def _brief_spec() -> dict[str, Any]:
    briefs = []
    for index, case_id in enumerate(_case_ids()):
        briefs.append(
            {
                "brief_id": stable_id("brief", "first-direct-lane", str(index)),
                "case_id": case_id,
                "author_visible_brief": {
                    "brief_version": "1.0.0",
                    "case_id": case_id,
                    "scientific_task": (
                        "Build a small analysis of planned observations and report one selected "
                        f"scientific summary for scenario {index + 1}."
                    ),
                    "available_inputs": ["A supplied table of planned and observed units."],
                    "required_artifacts": [
                        "One static Python producer.",
                        "One selected Markdown report.",
                    ],
                    "construction_constraints": [
                        "Use original identifiers and retain missing-unit accounting."
                    ],
                },
            }
        )
    return {
        "manifest_id": "brief-manifest:first-direct-lane-v1",
        "lane_id": "lane:complete-domain-exposure-denominator-v1",
        "precase_freeze_digest": _precase()["freeze_digest"],
        "expected_case_count": 14,
        "additional_hidden_terms": [
            ENVELOPE["envelope_id"],
            ENVELOPE["check_id"],
            ENVELOPE["candidate_id"],
        ],
        "briefs": briefs,
    }


def _protocol_spec(enrollment: dict[str, Any], brief_manifest: dict[str, Any]) -> dict[str, Any]:
    participants = [
        {
            "participant_id": item["participant_id"],
            "role": item["role"],
            "provider": item["provider"],
            "execution_context_id": item["execution_context_id"],
            "identity_evidence_digest": item["configuration_digest"],
        }
        for item in enrollment["participants"]
        if item["role"] != "evidence_validator"
    ]
    participants.sort(key=lambda item: str(item["participant_id"]))
    brief_by_case = {str(item["case_id"]): item for item in brief_manifest["briefs"]}
    assignments = []
    case_ids = _case_ids()
    for block_index, block_id in enumerate(("block:pilot", "block:heldout")):
        error_case = case_ids[block_index * 7]
        for cell_index, cell_type in enumerate(CELL_TYPES):
            case_id = case_ids[block_index * 7 + cell_index]
            assignments.append(
                {
                    "case_id": case_id,
                    "envelope_id": ENVELOPE["envelope_id"],
                    "block_id": block_id,
                    "cell_type": cell_type,
                    "source_kind": "independent_prospective",
                    "reference_case_id": (
                        error_case
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
                    "stage2_reviewer_ids": ["actor:s2-a", "actor:s2-b"],
                    "authoring_brief_digest": brief_by_case[case_id]["brief_digest"],
                    "assigned_at": ASSIGNED_AT,
                }
            )
    return {
        "protocol_id": "prospective-protocol:first-direct-lane-v1",
        "expected_envelope_count": 1,
        "detector_lock": {
            **deepcopy(_precase()["detector"]),
            "frozen_at": DETECTOR_FROZEN_AT,
        },
        "participants": participants,
        "envelopes": [deepcopy(ENVELOPE)],
        "blocks": [
            {"block_id": "block:pilot", "evidence_role": "threshold_pilot"},
            {"block_id": "block:heldout", "evidence_role": "qualification_heldout"},
        ],
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


def _lane() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    precase = _precase()
    enrollment = freeze_participant_enrollment(_enrollment_spec(), frozen_at=FROZEN_AT)
    briefs = freeze_authoring_brief_manifest(_brief_spec(), frozen_at=FROZEN_AT)
    lane = freeze_direct_qualification_lane(
        {
            "lane_id": "lane:complete-domain-exposure-denominator-v1",
            "heldout_access_policy": "withhold_author_access_until_approved_threshold",
            "prospective_protocol": _protocol_spec(enrollment, briefs),
        },
        precase_freeze=precase,
        participant_enrollment=enrollment,
        brief_manifest=briefs,
        frozen_at=FROZEN_AT,
    )
    return lane, enrollment, briefs


def test_participant_enrollment_binds_exact_configurations_and_replays() -> None:
    enrollment = freeze_participant_enrollment(_enrollment_spec(), frozen_at=FROZEN_AT)

    assert enrollment["authentication_status"] == "declared_not_authenticated"
    assert (
        enrollment["calibration_gate"] == "reviewer_configurations_must_pass_before_participation"
    )
    assert len(enrollment["participants"]) == 10
    assert validate_participant_enrollment(enrollment) == enrollment


def test_author_visible_briefs_exclude_controller_fields_and_hidden_terms() -> None:
    manifest = freeze_authoring_brief_manifest(_brief_spec(), frozen_at=FROZEN_AT)

    assert len(manifest["briefs"]) == 14
    assert all(item["literal_leakage_screen_passed"] for item in manifest["briefs"])
    assert validate_authoring_brief_manifest(manifest) == manifest

    leaked = _brief_spec()
    leaked["briefs"][0]["author_visible_brief"]["scientific_task"] += " This is heldout."
    with pytest.raises(DirectQualificationLaneError, match="hidden qualification terms"):
        freeze_authoring_brief_manifest(leaked, frozen_at=FROZEN_AT)

    extra_field = _brief_spec()
    extra_field["briefs"][0]["author_visible_brief"]["cell_type"] = "positive"
    with pytest.raises(DirectQualificationLaneError, match="unexpected fields"):
        freeze_authoring_brief_manifest(extra_field, frozen_at=FROZEN_AT)


def test_direct_lane_freezes_fourteen_assignments_and_seals_heldout() -> None:
    lane, enrollment, briefs = _lane()

    assert lane["study_state"] == "assignments_frozen_labels_unopened"
    assert lane["qualification_authority"] == "none_lane_freeze_only"
    assert lane["prospective_protocol"]["coverage"]["required_case_count"] == 14
    assert lane["heldout_seal"] == {
        "block_ids": ["block:heldout"],
        "case_ids": sorted(_case_ids()[7:]),
        "author_access_state": "withheld_until_approved_threshold",
        "scientific_labels_present": False,
        "detector_outcomes_present": False,
    }
    assert (
        validate_direct_qualification_lane(
            lane,
            precase_freeze=_precase(),
            participant_enrollment=enrollment,
            brief_manifest=briefs,
        )
        == lane
    )


@pytest.mark.parametrize("mutation", ("brief", "participant", "envelope", "detector"))
def test_direct_lane_rejects_unbound_inputs(mutation: str) -> None:
    _lane_record, enrollment, briefs = _lane()
    protocol = _protocol_spec(enrollment, briefs)
    precase = _precase()
    if mutation == "brief":
        protocol["assignments"][0]["authoring_brief_digest"] = DIGEST
    elif mutation == "participant":
        protocol["participants"][0]["identity_evidence_digest"] = DIGEST
    elif mutation == "envelope":
        protocol["envelopes"][0]["candidate_id"] = "different-candidate"
    else:
        protocol["detector_lock"]["implementation_digest"] = DIGEST

    with pytest.raises(DirectQualificationLaneError):
        freeze_direct_qualification_lane(
            {
                "lane_id": "lane:complete-domain-exposure-denominator-v1",
                "heldout_access_policy": "withhold_author_access_until_approved_threshold",
                "prospective_protocol": protocol,
            },
            precase_freeze=precase,
            participant_enrollment=enrollment,
            brief_manifest=briefs,
            frozen_at=FROZEN_AT,
        )
