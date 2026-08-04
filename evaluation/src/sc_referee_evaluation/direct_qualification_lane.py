from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from sc_referee.core.ids import semantic_digest
from sc_referee_evaluation.prospective_qualification import (
    freeze_prospective_qualification_protocol,
)

PARTICIPANT_ENROLLMENT_VERSION = "1.0.0"
AUTHORING_BRIEF_MANIFEST_VERSION = "1.0.0"
DIRECT_LANE_FREEZE_VERSION = "1.0.0"

_PROTOCOL_ROLES = {
    "author",
    "stage1_reviewer",
    "stage2_reviewer",
    "detector_implementer",
}
_ENROLLMENT_ROLES = _PROTOCOL_ROLES | {"evidence_validator"}
_AUTHOR_VISIBLE_KEYS = {
    "brief_version",
    "case_id",
    "scientific_task",
    "available_inputs",
    "required_artifacts",
    "construction_constraints",
}
_STANDARD_HIDDEN_TERMS = {
    "ambiguous",
    "benchmark answer",
    "canonical issue",
    "corrected twin",
    "corrected_twin",
    "detector output",
    "error bearing",
    "error-bearing",
    "error_bearing",
    "expected answer",
    "hard negative",
    "hard_negative",
    "held-out",
    "heldout",
    "issue-class:",
    "qualification_heldout",
    "renamed implementation",
    "renamed_implementation",
    "sc-referee",
    "threshold pilot",
    "threshold_pilot",
    "unsupported cell",
    "valid alternative",
    "valid_alternative",
}


class DirectQualificationLaneError(ValueError):
    """A direct qualification lane is not frozen, blind, or replayable."""


def freeze_participant_enrollment(
    specification: Mapping[str, Any], *, frozen_at: str
) -> dict[str, Any]:
    """Freeze declared exact actor configurations without authenticating future sessions."""

    spec = deepcopy(dict(specification))
    _exact_keys(
        spec,
        {"enrollment_id", "precase_freeze_digest", "participants"},
        "participant enrollment specification",
    )
    _timestamp(frozen_at)
    enrollment_id = _text(spec["enrollment_id"], "enrollment_id")
    precase_digest = _digest(spec["precase_freeze_digest"], "precase_freeze_digest")
    participants = [_participant(item) for item in _sequence(spec["participants"], "participants")]
    _validate_participant_panel(participants)
    participants.sort(key=lambda item: str(item["participant_id"]))
    record: dict[str, Any] = {
        "artifact_kind": "direct_qualification_participant_enrollment",
        "enrollment_version": PARTICIPANT_ENROLLMENT_VERSION,
        "enrollment_id": enrollment_id,
        "precase_freeze_digest": precase_digest,
        "participants": participants,
        "frozen_at": _iso(_timestamp(frozen_at)),
        "authentication_status": "declared_not_authenticated",
        "calibration_gate": "reviewer_configurations_must_pass_before_participation",
        "qualification_authority": "none_enrollment_only",
    }
    record["enrollment_digest"] = semantic_digest(record)
    return record


def validate_participant_enrollment(value: Mapping[str, Any]) -> dict[str, Any]:
    """Replay one exact participant-enrollment declaration."""

    record = deepcopy(dict(value))
    supplied = record.pop("enrollment_digest", None)
    if supplied != semantic_digest(record):
        raise DirectQualificationLaneError("Participant enrollment digest does not replay.")
    if (
        record.get("artifact_kind") != "direct_qualification_participant_enrollment"
        or record.get("enrollment_version") != PARTICIPANT_ENROLLMENT_VERSION
        or record.get("authentication_status") != "declared_not_authenticated"
        or record.get("calibration_gate")
        != "reviewer_configurations_must_pass_before_participation"
        or record.get("qualification_authority") != "none_enrollment_only"
    ):
        raise DirectQualificationLaneError("Unsupported participant enrollment artifact.")
    replayed = freeze_participant_enrollment(
        {
            "enrollment_id": record["enrollment_id"],
            "precase_freeze_digest": record["precase_freeze_digest"],
            "participants": [
                {key: item[key] for key in _PARTICIPANT_INPUT_KEYS}
                for item in record["participants"]
            ],
        },
        frozen_at=str(record["frozen_at"]),
    )
    record["enrollment_digest"] = supplied
    if replayed != record:
        raise DirectQualificationLaneError("Participant enrollment semantics do not replay.")
    return record


def freeze_authoring_brief_manifest(
    specification: Mapping[str, Any], *, frozen_at: str
) -> dict[str, Any]:
    """Freeze author-visible briefs and a finite literal leakage screen before assignment."""

    spec = deepcopy(dict(specification))
    _exact_keys(
        spec,
        {
            "manifest_id",
            "lane_id",
            "precase_freeze_digest",
            "expected_case_count",
            "additional_hidden_terms",
            "briefs",
        },
        "authoring brief manifest specification",
    )
    _timestamp(frozen_at)
    expected_count = spec["expected_case_count"]
    if (
        not isinstance(expected_count, int)
        or isinstance(expected_count, bool)
        or expected_count < 1
    ):
        raise DirectQualificationLaneError("expected_case_count must be a positive integer.")
    hidden_terms = sorted(
        _STANDARD_HIDDEN_TERMS
        | {
            _text(item, "additional hidden term").casefold()
            for item in _sequence(spec["additional_hidden_terms"], "additional_hidden_terms")
        }
    )
    briefs = [
        _authoring_brief(item, hidden_terms=hidden_terms)
        for item in _sequence(spec["briefs"], "briefs")
    ]
    if len(briefs) != expected_count:
        raise DirectQualificationLaneError(
            f"Expected {expected_count} authoring briefs, received {len(briefs)}."
        )
    if len({str(item["case_id"]) for item in briefs}) != len(briefs):
        raise DirectQualificationLaneError("Authoring brief case identities must be unique.")
    if len({str(item["brief_id"]) for item in briefs}) != len(briefs):
        raise DirectQualificationLaneError("Authoring brief identities must be unique.")
    briefs.sort(key=lambda item: str(item["case_id"]))
    record: dict[str, Any] = {
        "artifact_kind": "direct_qualification_authoring_brief_manifest",
        "manifest_version": AUTHORING_BRIEF_MANIFEST_VERSION,
        "manifest_id": _text(spec["manifest_id"], "manifest_id"),
        "lane_id": _text(spec["lane_id"], "lane_id"),
        "precase_freeze_digest": _digest(spec["precase_freeze_digest"], "precase_freeze_digest"),
        "expected_case_count": expected_count,
        "literal_hidden_terms": hidden_terms,
        "briefs": briefs,
        "frozen_at": _iso(_timestamp(frozen_at)),
        "leakage_screen_scope": "finite_literal_and_field_screen_only",
        "qualification_authority": "none_brief_manifest_only",
    }
    record["manifest_digest"] = semantic_digest(record)
    return record


def validate_authoring_brief_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    """Replay one authoring-brief manifest and its finite leakage screen."""

    record = deepcopy(dict(value))
    supplied = record.pop("manifest_digest", None)
    if supplied != semantic_digest(record):
        raise DirectQualificationLaneError("Authoring brief manifest digest does not replay.")
    if (
        record.get("artifact_kind") != "direct_qualification_authoring_brief_manifest"
        or record.get("manifest_version") != AUTHORING_BRIEF_MANIFEST_VERSION
        or record.get("leakage_screen_scope") != "finite_literal_and_field_screen_only"
        or record.get("qualification_authority") != "none_brief_manifest_only"
    ):
        raise DirectQualificationLaneError("Unsupported authoring brief manifest artifact.")
    additional = sorted(set(record["literal_hidden_terms"]) - _STANDARD_HIDDEN_TERMS)
    replayed = freeze_authoring_brief_manifest(
        {
            "manifest_id": record["manifest_id"],
            "lane_id": record["lane_id"],
            "precase_freeze_digest": record["precase_freeze_digest"],
            "expected_case_count": record["expected_case_count"],
            "additional_hidden_terms": additional,
            "briefs": [
                {
                    "brief_id": item["brief_id"],
                    "case_id": item["case_id"],
                    "author_visible_brief": item["author_visible_brief"],
                }
                for item in record["briefs"]
            ],
        },
        frozen_at=str(record["frozen_at"]),
    )
    record["manifest_digest"] = supplied
    if replayed != record:
        raise DirectQualificationLaneError("Authoring brief manifest semantics do not replay.")
    return record


def freeze_direct_qualification_lane(
    specification: Mapping[str, Any],
    *,
    precase_freeze: Mapping[str, Any],
    participant_enrollment: Mapping[str, Any],
    brief_manifest: Mapping[str, Any],
    frozen_at: str,
) -> dict[str, Any]:
    """Bind one existing prospective protocol to exact enrollment, briefs, and precase bytes."""

    precase = _precase_freeze(precase_freeze)
    enrollment = validate_participant_enrollment(participant_enrollment)
    briefs = validate_authoring_brief_manifest(brief_manifest)
    if (
        enrollment["precase_freeze_digest"] != precase["freeze_digest"]
        or briefs["precase_freeze_digest"] != precase["freeze_digest"]
    ):
        raise DirectQualificationLaneError("Lane inputs do not bind the exact precase freeze.")
    spec = deepcopy(dict(specification))
    protocol_spec = deepcopy(_mapping(spec.pop("prospective_protocol"), "prospective_protocol"))
    _exact_keys(spec, {"lane_id", "heldout_access_policy"}, "direct lane specification")
    if spec["heldout_access_policy"] != "withhold_author_access_until_approved_threshold":
        raise DirectQualificationLaneError("Held-out author access policy is not sealed.")
    expected_participants = _protocol_participants(enrollment)
    if protocol_spec.get("participants") != expected_participants:
        raise DirectQualificationLaneError(
            "Prospective protocol participants do not equal the enrolled role projection."
        )
    brief_by_case = {str(item["case_id"]): item for item in briefs["briefs"]}
    assignments = _sequence(protocol_spec.get("assignments"), "prospective assignments")
    if set(brief_by_case) != {str(item.get("case_id")) for item in assignments}:
        raise DirectQualificationLaneError("Assignments do not equal the frozen brief case set.")
    for assignment in assignments:
        brief = brief_by_case[str(assignment["case_id"])]
        if assignment.get("authoring_brief_digest") != brief["brief_digest"]:
            raise DirectQualificationLaneError("Assignment does not bind its exact author brief.")
    envelope = _sequence(protocol_spec.get("envelopes"), "prospective envelopes")
    if len(envelope) != 1 or any(
        envelope[0].get(key) != precase["envelope"][key]
        for key in ("envelope_id", "check_id", "candidate_id", "binding_digest")
    ):
        raise DirectQualificationLaneError("Prospective envelope does not equal the precase tuple.")
    detector_lock = protocol_spec.get("detector_lock")
    if not isinstance(detector_lock, Mapping) or any(
        detector_lock.get(key) != precase["detector"][key]
        for key in (
            "detector_id",
            "detector_version",
            "detector_manifest_digest",
            "implementation_digest",
        )
    ):
        raise DirectQualificationLaneError(
            "Prospective detector lock does not equal the precase tuple."
        )
    protocol = freeze_prospective_qualification_protocol(protocol_spec, frozen_at=frozen_at)
    heldout_blocks = {
        str(item["block_id"])
        for item in protocol["blocks"]
        if item["evidence_role"] == "qualification_heldout"
    }
    heldout_cases = sorted(
        str(item["case_id"])
        for item in protocol["assignments"]
        if item["block_id"] in heldout_blocks
    )
    record: dict[str, Any] = {
        "artifact_kind": "direct_qualification_lane_freeze",
        "lane_freeze_version": DIRECT_LANE_FREEZE_VERSION,
        "lane_id": _text(spec["lane_id"], "lane_id"),
        "precase_freeze_digest": precase["freeze_digest"],
        "participant_enrollment_digest": enrollment["enrollment_digest"],
        "authoring_brief_manifest_digest": briefs["manifest_digest"],
        "prospective_protocol": protocol,
        "heldout_seal": {
            "block_ids": sorted(heldout_blocks),
            "case_ids": heldout_cases,
            "author_access_state": "withheld_until_approved_threshold",
            "scientific_labels_present": False,
            "detector_outcomes_present": False,
        },
        "frozen_at": _iso(_timestamp(frozen_at)),
        "study_state": "assignments_frozen_labels_unopened",
        "qualification_authority": "none_lane_freeze_only",
    }
    record["lane_freeze_digest"] = semantic_digest(record)
    return record


def validate_direct_qualification_lane(
    value: Mapping[str, Any],
    *,
    precase_freeze: Mapping[str, Any],
    participant_enrollment: Mapping[str, Any],
    brief_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Replay a lane freeze from its exact controller-side source artifacts."""

    record = deepcopy(dict(value))
    supplied = record.pop("lane_freeze_digest", None)
    if supplied != semantic_digest(record):
        raise DirectQualificationLaneError("Direct lane freeze digest does not replay.")
    if (
        record.get("artifact_kind") != "direct_qualification_lane_freeze"
        or record.get("lane_freeze_version") != DIRECT_LANE_FREEZE_VERSION
        or record.get("study_state") != "assignments_frozen_labels_unopened"
        or record.get("qualification_authority") != "none_lane_freeze_only"
    ):
        raise DirectQualificationLaneError("Unsupported direct qualification lane freeze.")
    protocol = _mapping(record["prospective_protocol"], "prospective_protocol")
    protocol_spec = {
        key: protocol[key]
        for key in (
            "protocol_id",
            "expected_envelope_count",
            "detector_lock",
            "participants",
            "envelopes",
            "blocks",
            "assignments",
            "governance",
        )
    }
    replayed = freeze_direct_qualification_lane(
        {
            "lane_id": record["lane_id"],
            "heldout_access_policy": "withhold_author_access_until_approved_threshold",
            "prospective_protocol": protocol_spec,
        },
        precase_freeze=precase_freeze,
        participant_enrollment=participant_enrollment,
        brief_manifest=brief_manifest,
        frozen_at=str(record["frozen_at"]),
    )
    record["lane_freeze_digest"] = supplied
    if replayed != record:
        raise DirectQualificationLaneError("Direct lane freeze semantics do not replay.")
    return record


_PARTICIPANT_INPUT_KEYS = {
    "participant_id",
    "role",
    "provider",
    "agent_surface",
    "agent_version",
    "model_name",
    "model_id",
    "reasoning_configuration",
    "execution_context_id",
    "system_prompt_digest",
    "tool_policy_digest",
    "environment_digest",
    "calibration_suite_digest",
    "calibration_status",
}


def _participant(value: Any) -> dict[str, Any]:
    participant = deepcopy(_mapping(value, "participant"))
    _exact_keys(participant, _PARTICIPANT_INPUT_KEYS, "participant")
    for key in (
        "participant_id",
        "provider",
        "agent_surface",
        "agent_version",
        "model_name",
        "model_id",
        "reasoning_configuration",
        "execution_context_id",
    ):
        _text(participant[key], f"participant {key}")
    if participant["role"] not in _ENROLLMENT_ROLES:
        raise DirectQualificationLaneError(f"Unsupported participant role {participant['role']!r}.")
    for key in (
        "system_prompt_digest",
        "tool_policy_digest",
        "environment_digest",
        "calibration_suite_digest",
    ):
        _digest(participant[key], f"participant {key}")
    allowed_calibration = (
        {"required_before_participation", "passed"}
        if participant["role"] in {"stage1_reviewer", "stage2_reviewer"}
        else {"not_applicable"}
    )
    if participant["calibration_status"] not in allowed_calibration:
        raise DirectQualificationLaneError("Unsupported participant calibration status.")
    participant["configuration_digest"] = semantic_digest(participant)
    return participant


def _validate_participant_panel(participants: Sequence[Mapping[str, Any]]) -> None:
    if not participants:
        raise DirectQualificationLaneError("Participant enrollment is empty.")
    if len({str(item["participant_id"]) for item in participants}) != len(participants):
        raise DirectQualificationLaneError("Participant identities must be unique.")
    if len({str(item["execution_context_id"]) for item in participants}) != len(participants):
        raise DirectQualificationLaneError("Participant execution contexts must be unique.")
    roles = Counter(str(item["role"]) for item in participants)
    if roles["author"] < 2 or roles["evidence_validator"] < 1 or roles["detector_implementer"] < 1:
        raise DirectQualificationLaneError(
            "Enrollment requires two authors, one evidence validator, and one detector implementer."
        )
    stage1 = [item for item in participants if item["role"] == "stage1_reviewer"]
    stage2 = [item for item in participants if item["role"] == "stage2_reviewer"]
    stage1_providers = Counter(str(item["provider"]) for item in stage1)
    stage2_providers = Counter(str(item["provider"]) for item in stage2)
    if len(stage1) != 4 or sorted(stage1_providers.values()) != [2, 2]:
        raise DirectQualificationLaneError(
            "Enrollment requires exactly two Stage-1 reviewers from each of two providers."
        )
    if len(stage2) != 2 or sorted(stage2_providers.values()) != [1, 1]:
        raise DirectQualificationLaneError(
            "Enrollment requires one fresh Stage-2 reviewer from each of two providers."
        )
    if set(stage2_providers) != set(stage1_providers):
        raise DirectQualificationLaneError(
            "Stage-1 and Stage-2 enrollment must use the same two provider families."
        )


def _authoring_brief(value: Any, *, hidden_terms: Sequence[str]) -> dict[str, Any]:
    brief = deepcopy(_mapping(value, "authoring brief"))
    _exact_keys(brief, {"brief_id", "case_id", "author_visible_brief"}, "authoring brief")
    brief_id = _text(brief["brief_id"], "brief_id")
    case_id = _case_id(brief["case_id"])
    visible = deepcopy(_mapping(brief["author_visible_brief"], "author_visible_brief"))
    _exact_keys(visible, _AUTHOR_VISIBLE_KEYS, "author_visible_brief")
    if visible["brief_version"] != "1.0.0" or visible["case_id"] != case_id:
        raise DirectQualificationLaneError("Author-visible brief identity or version is invalid.")
    _text(visible["scientific_task"], "scientific_task")
    for key in ("available_inputs", "required_artifacts", "construction_constraints"):
        values = _sequence(visible[key], key)
        if not values:
            raise DirectQualificationLaneError(f"{key} must not be empty.")
        visible[key] = [_text(item, key) for item in values]
    serialized = json.dumps(visible, sort_keys=True, ensure_ascii=True).casefold()
    leaks = sorted(term for term in hidden_terms if term and term.casefold() in serialized)
    if leaks:
        raise DirectQualificationLaneError(
            f"Author-visible brief contains hidden qualification terms: {leaks}."
        )
    return {
        "brief_id": brief_id,
        "case_id": case_id,
        "author_visible_brief": visible,
        "brief_digest": semantic_digest(visible),
        "literal_leakage_screen_passed": True,
    }


def _protocol_participants(enrollment: Mapping[str, Any]) -> list[dict[str, Any]]:
    projected = [
        {
            "participant_id": item["participant_id"],
            "role": item["role"],
            "provider": item["provider"],
            "execution_context_id": item["execution_context_id"],
            "identity_evidence_digest": item["configuration_digest"],
        }
        for item in enrollment["participants"]
        if item["role"] in _PROTOCOL_ROLES
    ]
    return sorted(projected, key=lambda item: str(item["participant_id"]))


def _precase_freeze(value: Mapping[str, Any]) -> dict[str, Any]:
    record = deepcopy(dict(value))
    supplied = record.pop("freeze_digest", None)
    if supplied != semantic_digest(record):
        raise DirectQualificationLaneError("Precase freeze digest does not replay.")
    if (
        record.get("artifact_kind") != "direct_envelope_precase_freeze"
        or record.get("metric_case_count") != 0
        or record.get("scientific_label_count") != 0
        or record.get("detector_outcome_count") != 0
    ):
        raise DirectQualificationLaneError("Precase artifact is not a clean zero-case freeze.")
    record["freeze_digest"] = supplied
    return record


def _case_id(value: Any) -> str:
    case_id = _text(value, "case_id")
    suffix = case_id.removeprefix("case:")
    if (
        not case_id.startswith("case:")
        or len(suffix) != 20
        or any(character not in "0123456789abcdef" for character in suffix)
    ):
        raise DirectQualificationLaneError("case_id must use one opaque 20-hex suffix.")
    return case_id


def _digest(value: Any, label: str) -> str:
    digest = _text(value, label)
    if not digest.startswith("sha256:") or len(digest) != 71:
        raise DirectQualificationLaneError(f"{label} must use one full SHA-256 digest.")
    try:
        int(digest.removeprefix("sha256:"), 16)
    except ValueError as error:
        raise DirectQualificationLaneError(f"{label} must use one full SHA-256 digest.") from error
    return digest


def _timestamp(value: Any) -> datetime:
    text = _text(value, "timestamp")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise DirectQualificationLaneError("Timestamp must use ISO 8601.") from error
    if parsed.tzinfo is None:
        raise DirectQualificationLaneError("Timestamp must include a timezone.")
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise DirectQualificationLaneError(f"{label} must be an object.")
    return dict(value)


def _sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise DirectQualificationLaneError(f"{label} must be an array.")
    return list(value)


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise DirectQualificationLaneError(f"{label} must be nonempty text.")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise DirectQualificationLaneError(
            f"{label} has unexpected fields; expected={sorted(expected)}, received={sorted(value)}."
        )
