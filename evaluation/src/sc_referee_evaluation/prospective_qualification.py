from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime
from typing import Any

from sc_referee.core.ids import semantic_digest


class ProspectiveQualificationError(ValueError):
    """A prospective qualification artifact violates its frozen study protocol."""


PROTOCOL_VERSION = "1.0.0"
REQUIRED_CELL_TYPES = (
    "error_bearing",
    "corrected_twin",
    "valid_alternative",
    "hard_negative",
    "ambiguous",
    "unsupported",
    "renamed_implementation",
)

_EXPECTED_LABEL = {
    "error_bearing": "issue_present",
    "corrected_twin": "issue_absent",
    "valid_alternative": "issue_absent",
    "hard_negative": "issue_absent",
    "ambiguous": "indeterminate",
    "unsupported": "unsupported",
    "renamed_implementation": "issue_present",
}
_GOVERNANCE_FLAGS = {
    "all_outcomes_retained",
    "no_replacement",
    "public_benchmark_qualification_excluded",
    "development_case_qualification_excluded",
    "detector_implementers_label_blind",
    "review_detector_output_hidden",
    "independent_review_contexts_required",
}
_PARTICIPANT_ROLES = {
    "author",
    "stage1_reviewer",
    "stage2_reviewer",
    "detector_implementer",
}
_BLOCK_ROLES = {"threshold_pilot", "qualification_heldout", "development_regression"}
_SOURCE_KINDS = {"independent_prospective", "public_development", "internal_development"}
_LABEL_STATUSES = {
    "issue_present",
    "issue_absent",
    "indeterminate",
    "unsupported",
    "unavailable",
}
_DETECTOR_OBSERVATIONS = {
    "evaluation_finding_candidate",
    "no_issue_detected_within_coverage",
    "insufficient_semantics",
    "unsupported_path",
    "unavailable",
}
_RETENTION_DISPOSITIONS = {
    "retained_complete",
    "retained_contaminated",
    "retained_failure",
    "retained_withdrawal",
}
_CONTAMINATION_STATUSES = {"clean", "contaminated", "unknown"}
_AUTHENTICATION_STATUSES = {"externally_verified", "unverified"}


def freeze_prospective_qualification_protocol(
    specification: Mapping[str, Any], *, frozen_at: str
) -> dict[str, Any]:
    """Freeze a complete, label-unopened study design without creating evidence.

    The caller supplies opaque case and participant identities. This function checks study shape,
    chronology, isolation, and the required control matrix; it does not recruit people, authenticate
    them, assign scientific labels, or qualify a detector.
    """

    frozen_time = _timestamp(frozen_at)
    spec = deepcopy(dict(specification))
    _exact_keys(
        spec,
        {
            "protocol_id",
            "expected_envelope_count",
            "detector_lock",
            "participants",
            "envelopes",
            "blocks",
            "assignments",
            "governance",
        },
        "prospective protocol specification",
    )
    protocol_id = _nonempty(spec["protocol_id"], "protocol_id")
    expected_count = spec["expected_envelope_count"]
    if (
        not isinstance(expected_count, int)
        or isinstance(expected_count, bool)
        or expected_count <= 0
    ):
        raise ProspectiveQualificationError("expected_envelope_count must be a positive integer.")

    detector_lock = _validate_detector_lock(spec["detector_lock"])
    if frozen_time < _timestamp(str(detector_lock["frozen_at"])):
        raise ProspectiveQualificationError("Protocol freeze predates the detector lock.")
    governance = _mapping(spec["governance"], "governance")
    _exact_keys(governance, _GOVERNANCE_FLAGS, "governance")
    if any(governance[key] is not True for key in _GOVERNANCE_FLAGS):
        raise ProspectiveQualificationError(
            "Every prospective qualification governance flag must be true."
        )

    participants = _validate_participants(spec["participants"])
    envelopes = _validate_envelopes(spec["envelopes"], expected_count)
    blocks = _validate_blocks(spec["blocks"])
    assignments = _validate_assignments(
        spec["assignments"],
        participants=participants,
        envelopes=envelopes,
        blocks=blocks,
        detector_frozen_at=str(detector_lock["frozen_at"]),
        protocol_frozen_at=frozen_at,
    )
    coverage = _validate_required_matrix(assignments, envelopes, blocks)

    record: dict[str, Any] = {
        "artifact_kind": "prospective_qualification_protocol",
        "protocol_version": PROTOCOL_VERSION,
        "protocol_id": protocol_id,
        "expected_envelope_count": expected_count,
        "detector_lock": detector_lock,
        "participants": participants,
        "envelopes": envelopes,
        "blocks": blocks,
        "assignments": assignments,
        "governance": governance,
        "coverage": coverage,
        "frozen_at": frozen_at,
        "study_state": "assignments_frozen_labels_unopened",
        "qualification_authority": "none_protocol_only",
        "external_actions_required": [
            "prospective_case_authoring",
            "participant_identity_authentication",
            "answer_blind_stage1_review",
            "independent_stage2_adjudication",
            "all_outcome_capture",
            "pilot_threshold_decision",
            "heldout_evaluation",
            "maintainer_promotion_decision",
        ],
    }
    record["protocol_digest"] = semantic_digest(record)
    return record


def seal_prospective_outcome_ledger(
    protocol: Mapping[str, Any],
    outcomes: Sequence[Mapping[str, Any]],
    *,
    block_id: str,
    sealed_at: str,
    threshold_decision: Mapping[str, Any] | None = None,
    pilot_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Seal exactly one retained outcome for every preassigned case in one block."""

    protocol_record = _validate_frozen_protocol(protocol)
    block = _item_by_id(protocol_record["blocks"], "block_id", block_id, "block")
    assignments = [item for item in protocol_record["assignments"] if item["block_id"] == block_id]
    if not assignments:
        raise ProspectiveQualificationError(f"Block {block_id!r} has no frozen assignments.")
    sealed_time = _timestamp(sealed_at)
    if sealed_time < _timestamp(str(protocol_record["frozen_at"])):
        raise ProspectiveQualificationError("Outcome ledger seal predates the protocol freeze.")

    decision_ref: dict[str, str] | None = None
    role = str(block["evidence_role"])
    if role == "qualification_heldout":
        if threshold_decision is None or pilot_ledger is None:
            raise ProspectiveQualificationError(
                "A held-out outcome ledger requires the frozen pilot ledger and threshold decision."
            )
        decision = _validate_threshold_decision(threshold_decision, protocol_record, pilot_ledger)
        if decision["approved_for_heldout_opening"] is not True:
            raise ProspectiveQualificationError(
                "The threshold decision did not open held-out labels."
            )
        decision_ref = {
            "decision_id": str(decision["decision_id"]),
            "decision_digest": str(decision["decision_digest"]),
        }
        label_not_before = _timestamp(str(decision["decided_at"]))
    else:
        if threshold_decision is not None or pilot_ledger is not None:
            raise ProspectiveQualificationError(
                "Only the held-out block may consume a pilot ledger and threshold decision."
            )
        label_not_before = _timestamp(str(protocol_record["frozen_at"]))

    assignment_by_case = {str(item["case_id"]): item for item in assignments}
    supplied = [_mapping(value, "outcome") for value in outcomes]
    supplied_ids = [_nonempty(value.get("case_id"), "outcome case_id") for value in supplied]
    duplicates = sorted(case_id for case_id, count in Counter(supplied_ids).items() if count > 1)
    if duplicates:
        raise ProspectiveQualificationError(f"Duplicate retained outcomes: {duplicates}.")
    missing = sorted(set(assignment_by_case) - set(supplied_ids))
    extra = sorted(set(supplied_ids) - set(assignment_by_case))
    if missing or extra:
        raise ProspectiveQualificationError(
            f"All assigned outcomes must be retained exactly once; missing={missing}, extra={extra}."
        )

    retained: list[dict[str, Any]] = []
    for value in supplied:
        assignment = assignment_by_case[str(value["case_id"])]
        retained.append(
            _validate_outcome(
                value,
                assignment=assignment,
                role=role,
                label_not_before=label_not_before,
                sealed_at=sealed_at,
            )
        )
    retained.sort(key=lambda item: str(item["case_id"]))
    eligibility_counts = dict(
        sorted(Counter(item["metric_eligibility"] for item in retained).items())
    )
    mismatch_count = sum(item["cell_confirmation"] != "confirmed" for item in retained)
    complete_count = sum(item["retention_disposition"] == "retained_complete" for item in retained)
    ledger: dict[str, Any] = {
        "artifact_kind": "prospective_qualification_outcome_ledger",
        "protocol_version": PROTOCOL_VERSION,
        "protocol_ref": {
            "protocol_id": protocol_record["protocol_id"],
            "protocol_digest": protocol_record["protocol_digest"],
        },
        "block": deepcopy(block),
        "threshold_decision_ref": decision_ref,
        "outcomes": retained,
        "retention_summary": {
            "assigned_case_count": len(assignments),
            "retained_outcome_count": len(retained),
            "retained_complete_count": complete_count,
            "cell_mismatch_or_unavailable_count": mismatch_count,
            "metric_eligibility_counts": eligibility_counts,
            "all_assigned_outcomes_retained": True,
        },
        "sealed_at": sealed_at,
        "qualification_authority": "none_metric_input_only",
        "promotion_decision_present": False,
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    return ledger


def freeze_pilot_threshold_decision(
    protocol: Mapping[str, Any],
    pilot_ledger: Mapping[str, Any],
    decision_specification: Mapping[str, Any],
    *,
    decided_at: str,
) -> dict[str, Any]:
    """Freeze thresholds after the complete pilot and before any held-out label is opened."""

    protocol_record = _validate_frozen_protocol(protocol)
    ledger = _validate_outcome_ledger(pilot_ledger, protocol_record)
    if ledger["block"]["evidence_role"] != "threshold_pilot":
        raise ProspectiveQualificationError(
            "Threshold decisions require the threshold-pilot ledger."
        )
    if _timestamp(decided_at) < _timestamp(str(ledger["sealed_at"])):
        raise ProspectiveQualificationError("Threshold decision predates the sealed pilot ledger.")
    summary = ledger["retention_summary"]
    if summary["retained_complete_count"] != summary["assigned_case_count"]:
        raise ProspectiveQualificationError(
            "Pilot thresholds cannot be frozen until every assigned pilot case is complete."
        )
    if summary["cell_mismatch_or_unavailable_count"] != 0:
        raise ProspectiveQualificationError(
            "Pilot thresholds cannot be frozen from an unconfirmed required-cell matrix."
        )

    spec = deepcopy(dict(decision_specification))
    _exact_keys(
        spec,
        {
            "decision_id",
            "metric_definitions",
            "promotion_thresholds",
            "zero_high_severity_false_accusations_required",
            "approved_for_heldout_opening",
        },
        "pilot threshold decision specification",
    )
    decision_id = _nonempty(spec["decision_id"], "threshold decision_id")
    metric_definitions = _nonempty_mapping(spec["metric_definitions"], "metric_definitions")
    promotion_thresholds = _nonempty_mapping(spec["promotion_thresholds"], "promotion_thresholds")
    if spec["zero_high_severity_false_accusations_required"] is not True:
        raise ProspectiveQualificationError(
            "The pilot decision must preserve the zero-known-high-severity-false-accusation gate."
        )
    if not isinstance(spec["approved_for_heldout_opening"], bool):
        raise ProspectiveQualificationError("approved_for_heldout_opening must be boolean.")

    decision: dict[str, Any] = {
        "artifact_kind": "prospective_pilot_threshold_decision",
        "protocol_version": PROTOCOL_VERSION,
        "decision_id": decision_id,
        "protocol_ref": {
            "protocol_id": protocol_record["protocol_id"],
            "protocol_digest": protocol_record["protocol_digest"],
        },
        "pilot_ledger_ref": {
            "block_id": ledger["block"]["block_id"],
            "ledger_digest": ledger["ledger_digest"],
        },
        "metric_definitions": metric_definitions,
        "promotion_thresholds": promotion_thresholds,
        "zero_high_severity_false_accusations_required": True,
        "approved_for_heldout_opening": spec["approved_for_heldout_opening"],
        "decided_at": decided_at,
        "qualification_authority": "none_thresholds_only",
    }
    decision["decision_digest"] = semantic_digest(decision)
    return decision


def _validate_detector_lock(value: Any) -> dict[str, Any]:
    lock = deepcopy(_mapping(value, "detector_lock"))
    _exact_keys(
        lock,
        {
            "detector_id",
            "detector_version",
            "detector_manifest_digest",
            "implementation_digest",
            "frozen_at",
        },
        "detector_lock",
    )
    for key in ("detector_id", "detector_version"):
        _nonempty(lock[key], f"detector_lock {key}")
    for key in ("detector_manifest_digest", "implementation_digest"):
        _digest(lock[key], f"detector_lock {key}")
    _timestamp(str(lock["frozen_at"]))
    return lock


def _validate_participants(value: Any) -> list[dict[str, Any]]:
    participants = [
        deepcopy(_mapping(item, "participant")) for item in _sequence(value, "participants")
    ]
    if not participants:
        raise ProspectiveQualificationError("The protocol requires participants.")
    ids: set[str] = set()
    contexts: set[str] = set()
    for participant in participants:
        _exact_keys(
            participant,
            {
                "participant_id",
                "role",
                "provider",
                "execution_context_id",
                "identity_evidence_digest",
            },
            "participant",
        )
        participant_id = _nonempty(participant["participant_id"], "participant_id")
        context = _nonempty(participant["execution_context_id"], "execution_context_id")
        if participant_id in ids or context in contexts:
            raise ProspectiveQualificationError(
                "Participant and execution-context identities must be globally unique."
            )
        ids.add(participant_id)
        contexts.add(context)
        if participant["role"] not in _PARTICIPANT_ROLES:
            raise ProspectiveQualificationError(
                f"Unsupported participant role {participant['role']!r}."
            )
        _nonempty(participant["provider"], "participant provider")
        _digest(participant["identity_evidence_digest"], "participant identity_evidence_digest")
    present_roles = {str(item["role"]) for item in participants}
    missing_roles = sorted(_PARTICIPANT_ROLES - present_roles)
    if missing_roles:
        raise ProspectiveQualificationError(
            f"The frozen study must bind every isolation role; missing={missing_roles}."
        )
    participants.sort(key=lambda item: str(item["participant_id"]))
    return participants


def _validate_envelopes(value: Any, expected_count: int) -> list[dict[str, Any]]:
    envelopes = [deepcopy(_mapping(item, "envelope")) for item in _sequence(value, "envelopes")]
    if len(envelopes) != expected_count:
        raise ProspectiveQualificationError(
            f"Expected {expected_count} relation envelopes, received {len(envelopes)}."
        )
    ids: set[str] = set()
    for envelope in envelopes:
        _exact_keys(
            envelope,
            {"envelope_id", "check_id", "candidate_id", "binding_digest"},
            "relation envelope",
        )
        envelope_id = _nonempty(envelope["envelope_id"], "envelope_id")
        if envelope_id in ids:
            raise ProspectiveQualificationError(f"Duplicate relation envelope {envelope_id!r}.")
        ids.add(envelope_id)
        _nonempty(envelope["check_id"], "envelope check_id")
        _nonempty(envelope["candidate_id"], "envelope candidate_id")
        _digest(envelope["binding_digest"], "envelope binding_digest")
    envelopes.sort(key=lambda item: str(item["envelope_id"]))
    return envelopes


def _validate_blocks(value: Any) -> list[dict[str, Any]]:
    blocks = [deepcopy(_mapping(item, "block")) for item in _sequence(value, "blocks")]
    ids: set[str] = set()
    roles: Counter[str] = Counter()
    for block in blocks:
        _exact_keys(block, {"block_id", "evidence_role"}, "study block")
        block_id = _nonempty(block["block_id"], "block_id")
        role = str(block["evidence_role"])
        if block_id in ids or role not in _BLOCK_ROLES:
            raise ProspectiveQualificationError(f"Duplicate or unsupported study block {block!r}.")
        ids.add(block_id)
        roles[role] += 1
    if roles["threshold_pilot"] != 1 or roles["qualification_heldout"] != 1:
        raise ProspectiveQualificationError(
            "The protocol requires exactly one threshold-pilot and one qualification-heldout block."
        )
    if roles["development_regression"] > 1:
        raise ProspectiveQualificationError("At most one development-regression block is allowed.")
    blocks.sort(key=lambda item: str(item["block_id"]))
    return blocks


def _validate_assignments(
    value: Any,
    *,
    participants: Sequence[Mapping[str, Any]],
    envelopes: Sequence[Mapping[str, Any]],
    blocks: Sequence[Mapping[str, Any]],
    detector_frozen_at: str,
    protocol_frozen_at: str,
) -> list[dict[str, Any]]:
    assignments = [
        deepcopy(_mapping(item, "assignment")) for item in _sequence(value, "assignments")
    ]
    participant_by_id = {str(item["participant_id"]): item for item in participants}
    envelope_ids = {str(item["envelope_id"]) for item in envelopes}
    block_by_id = {str(item["block_id"]): item for item in blocks}
    case_ids: set[str] = set()
    frozen_start = _timestamp(detector_frozen_at)
    frozen_end = _timestamp(protocol_frozen_at)
    for assignment in assignments:
        _exact_keys(
            assignment,
            {
                "case_id",
                "envelope_id",
                "block_id",
                "cell_type",
                "source_kind",
                "reference_case_id",
                "author_id",
                "stage1_reviewer_ids",
                "stage2_reviewer_ids",
                "authoring_brief_digest",
                "assigned_at",
            },
            "case assignment",
        )
        case_id = _nonempty(assignment["case_id"], "case_id")
        case_suffix = case_id.removeprefix("case:")
        if (
            not case_id.startswith("case:")
            or len(case_suffix) != 20
            or any(character not in "0123456789abcdef" for character in case_suffix)
        ):
            raise ProspectiveQualificationError(
                "case_id must be an opaque case: identity with a 20-character hex suffix."
            )
        if case_id in case_ids:
            raise ProspectiveQualificationError(f"Duplicate case assignment {case_id!r}.")
        case_ids.add(case_id)
        if assignment["envelope_id"] not in envelope_ids:
            raise ProspectiveQualificationError(
                f"Unknown assignment envelope {assignment['envelope_id']!r}."
            )
        if assignment["block_id"] not in block_by_id:
            raise ProspectiveQualificationError(
                f"Unknown assignment block {assignment['block_id']!r}."
            )
        if assignment["cell_type"] not in REQUIRED_CELL_TYPES:
            raise ProspectiveQualificationError(
                f"Unsupported control cell {assignment['cell_type']!r}."
            )
        if assignment["source_kind"] not in _SOURCE_KINDS:
            raise ProspectiveQualificationError(
                f"Unsupported source_kind {assignment['source_kind']!r}."
            )
        block_role = block_by_id[str(assignment["block_id"])]["evidence_role"]
        if (
            block_role in {"threshold_pilot", "qualification_heldout"}
            and assignment["source_kind"] != "independent_prospective"
        ):
            raise ProspectiveQualificationError(
                "Pilot and held-out assignments must be independently authored prospective cases."
            )
        if (
            block_role == "development_regression"
            and assignment["source_kind"] == "independent_prospective"
        ):
            raise ProspectiveQualificationError(
                "Development assignments must retain an explicit development source kind."
            )
        author = _participant(participant_by_id, assignment["author_id"], "author")
        stage1_ids = _participant_ids(assignment["stage1_reviewer_ids"], "stage1_reviewer_ids", 4)
        stage2_ids = _participant_ids(assignment["stage2_reviewer_ids"], "stage2_reviewer_ids", 2)
        if set(stage1_ids) & set(stage2_ids) or str(author["participant_id"]) in set(
            stage1_ids + stage2_ids
        ):
            raise ProspectiveQualificationError(
                "Author, Stage-1, and Stage-2 participant identities must be disjoint per case."
            )
        stage1 = [_participant(participant_by_id, item, "stage1_reviewer") for item in stage1_ids]
        stage2 = [_participant(participant_by_id, item, "stage2_reviewer") for item in stage2_ids]
        if (
            len({str(item["provider"]) for item in stage1}) < 2
            or len({str(item["provider"]) for item in stage2}) < 2
        ):
            raise ProspectiveQualificationError(
                "Each review stage requires participants from at least two providers."
            )
        _digest(assignment["authoring_brief_digest"], "assignment authoring_brief_digest")
        assigned = _timestamp(str(assignment["assigned_at"]))
        if assigned < frozen_start or assigned > frozen_end:
            raise ProspectiveQualificationError(
                "Every case assignment must occur after detector freeze and no later than protocol freeze."
            )
    assignment_by_id = {str(item["case_id"]): item for item in assignments}
    for assignment in assignments:
        reference_id = assignment["reference_case_id"]
        cell_type = str(assignment["cell_type"])
        if cell_type not in {"corrected_twin", "renamed_implementation"}:
            if reference_id is not None:
                raise ProspectiveQualificationError(
                    "Only corrected-twin and renamed-implementation cells may cite a reference case."
                )
            continue
        reference_key = _nonempty(reference_id, f"{cell_type} reference_case_id")
        reference = assignment_by_id.get(reference_key)
        if (
            reference is None
            or reference["cell_type"] != "error_bearing"
            or reference["envelope_id"] != assignment["envelope_id"]
            or reference["block_id"] != assignment["block_id"]
        ):
            raise ProspectiveQualificationError(
                f"{cell_type} must cite the error-bearing case in the same envelope and block."
            )
        if cell_type == "corrected_twin" and reference["author_id"] != assignment["author_id"]:
            raise ProspectiveQualificationError(
                "A corrected twin must retain the error-bearing case author."
            )
        if (
            cell_type == "renamed_implementation"
            and reference["author_id"] == assignment["author_id"]
        ):
            raise ProspectiveQualificationError(
                "A renamed implementation must use an author independent of its error-bearing reference."
            )
    assignments.sort(key=lambda item: str(item["case_id"]))
    return assignments


def _validate_required_matrix(
    assignments: Sequence[Mapping[str, Any]],
    envelopes: Sequence[Mapping[str, Any]],
    blocks: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    qualifying_blocks = {
        str(item["block_id"]): str(item["evidence_role"])
        for item in blocks
        if item["evidence_role"] in {"threshold_pilot", "qualification_heldout"}
    }
    counts = Counter(
        (str(item["block_id"]), str(item["envelope_id"]), str(item["cell_type"]))
        for item in assignments
        if item["block_id"] in qualifying_blocks
    )
    invalid: list[str] = []
    for block_id in sorted(qualifying_blocks):
        for envelope in envelopes:
            envelope_id = str(envelope["envelope_id"])
            for cell_type in REQUIRED_CELL_TYPES:
                count = counts[(block_id, envelope_id, cell_type)]
                if count != 1:
                    invalid.append(f"{block_id}/{envelope_id}/{cell_type}={count}")
    if invalid:
        raise ProspectiveQualificationError(
            "Pilot and held-out blocks require exactly one of every control cell per envelope: "
            + ", ".join(invalid)
        )
    return {
        "required_cell_types": list(REQUIRED_CELL_TYPES),
        "matrix_blocks": dict(sorted(qualifying_blocks.items())),
        "required_case_count": len(qualifying_blocks) * len(envelopes) * len(REQUIRED_CELL_TYPES),
        "matrix_complete": True,
    }


def _validate_outcome(
    value: Mapping[str, Any],
    *,
    assignment: Mapping[str, Any],
    role: str,
    label_not_before: datetime,
    sealed_at: str,
) -> dict[str, Any]:
    outcome = deepcopy(dict(value))
    _exact_keys(
        outcome,
        {
            "case_id",
            "retention_disposition",
            "contamination_status",
            "author_authentication_status",
            "review_authentication_status",
            "scientific_label",
            "detector_observation",
            "label_frozen_at",
            "completed_at",
            "artifact_digests",
        },
        "retained outcome",
    )
    if outcome["retention_disposition"] not in _RETENTION_DISPOSITIONS:
        raise ProspectiveQualificationError("Unsupported retention disposition.")
    if outcome["contamination_status"] not in _CONTAMINATION_STATUSES:
        raise ProspectiveQualificationError("Unsupported contamination status.")
    if outcome["author_authentication_status"] not in _AUTHENTICATION_STATUSES:
        raise ProspectiveQualificationError("Unsupported author authentication status.")
    if outcome["review_authentication_status"] not in _AUTHENTICATION_STATUSES:
        raise ProspectiveQualificationError("Unsupported review authentication status.")
    if outcome["scientific_label"] not in _LABEL_STATUSES:
        raise ProspectiveQualificationError("Unsupported scientific label.")
    if outcome["detector_observation"] not in _DETECTOR_OBSERVATIONS:
        raise ProspectiveQualificationError("Unsupported detector observation.")
    completed = _timestamp(str(outcome["completed_at"]))
    label_frozen = _timestamp(str(outcome["label_frozen_at"]))
    if label_frozen < label_not_before:
        raise ProspectiveQualificationError(
            "A scientific label was opened before its permitted boundary."
        )
    if completed < label_frozen or _timestamp(sealed_at) < completed:
        raise ProspectiveQualificationError("Outcome chronology is inconsistent.")
    digests = _mapping(outcome["artifact_digests"], "outcome artifact_digests")
    _exact_keys(
        digests,
        {"case_material", "stage1_panel", "stage2_panel", "scientific_label", "detector_output"},
        "outcome artifact_digests",
    )
    complete = outcome["retention_disposition"] == "retained_complete"
    if complete and outcome["contamination_status"] != "clean":
        raise ProspectiveQualificationError(
            "A retained-complete outcome must have a clean contamination screen."
        )
    if (
        outcome["retention_disposition"] == "retained_contaminated"
        and outcome["contamination_status"] != "contaminated"
    ):
        raise ProspectiveQualificationError(
            "A retained-contaminated outcome must preserve the contaminated status."
        )
    for key, digest in digests.items():
        if complete:
            _digest(digest, f"outcome artifact digest {key}")
        elif digest is not None:
            _digest(digest, f"outcome artifact digest {key}")
    if complete and (
        outcome["scientific_label"] == "unavailable"
        or outcome["detector_observation"] == "unavailable"
    ):
        raise ProspectiveQualificationError("A retained-complete outcome cannot be unavailable.")

    expected = _EXPECTED_LABEL[str(assignment["cell_type"])]
    cell_confirmation = "confirmed" if outcome["scientific_label"] == expected else "not_confirmed"
    eligibility = "excluded_nonqualification_block"
    if role == "qualification_heldout":
        failures: list[str] = []
        if not complete:
            failures.append("not_complete")
        if outcome["contamination_status"] != "clean":
            failures.append("contamination_not_clean")
        if outcome["author_authentication_status"] != "externally_verified":
            failures.append("author_not_externally_verified")
        if outcome["review_authentication_status"] != "externally_verified":
            failures.append("review_not_externally_verified")
        if cell_confirmation != "confirmed":
            failures.append("required_cell_not_confirmed")
        eligibility = (
            "included_heldout_metric_input"
            if not failures
            else "retained_ineligible:" + "+".join(failures)
        )

    outcome["frozen_assignment"] = deepcopy(dict(assignment))
    outcome["expected_cell_label"] = expected
    outcome["cell_confirmation"] = cell_confirmation
    outcome["metric_eligibility"] = eligibility
    return outcome


def _validate_frozen_protocol(value: Mapping[str, Any]) -> dict[str, Any]:
    protocol = deepcopy(dict(value))
    expected_digest = protocol.pop("protocol_digest", None)
    if expected_digest != semantic_digest(protocol):
        raise ProspectiveQualificationError("Prospective protocol digest does not replay.")
    protocol["protocol_digest"] = expected_digest
    if (
        protocol.get("artifact_kind") != "prospective_qualification_protocol"
        or protocol.get("protocol_version") != PROTOCOL_VERSION
    ):
        raise ProspectiveQualificationError("Unsupported prospective protocol artifact.")
    replayed = freeze_prospective_qualification_protocol(
        {
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
        },
        frozen_at=str(protocol["frozen_at"]),
    )
    if replayed != protocol:
        raise ProspectiveQualificationError("Prospective protocol semantics do not replay.")
    return protocol


def _validate_outcome_ledger(
    value: Mapping[str, Any], protocol: Mapping[str, Any]
) -> dict[str, Any]:
    ledger = deepcopy(dict(value))
    expected_digest = ledger.pop("ledger_digest", None)
    if expected_digest != semantic_digest(ledger):
        raise ProspectiveQualificationError("Pilot outcome ledger digest does not replay.")
    ledger["ledger_digest"] = expected_digest
    expected_ref = {
        "protocol_id": protocol["protocol_id"],
        "protocol_digest": protocol["protocol_digest"],
    }
    if (
        ledger.get("artifact_kind") != "prospective_qualification_outcome_ledger"
        or ledger.get("protocol_ref") != expected_ref
    ):
        raise ProspectiveQualificationError("Outcome ledger is not bound to this protocol.")
    if ledger.get("block", {}).get("evidence_role") != "threshold_pilot":
        raise ProspectiveQualificationError("Threshold replay requires a pilot outcome ledger.")
    raw_keys = {
        "case_id",
        "retention_disposition",
        "contamination_status",
        "author_authentication_status",
        "review_authentication_status",
        "scientific_label",
        "detector_observation",
        "label_frozen_at",
        "completed_at",
        "artifact_digests",
    }
    replayed = seal_prospective_outcome_ledger(
        protocol,
        [{key: item[key] for key in raw_keys} for item in ledger["outcomes"]],
        block_id=str(ledger["block"]["block_id"]),
        sealed_at=str(ledger["sealed_at"]),
    )
    if replayed != ledger:
        raise ProspectiveQualificationError("Pilot outcome ledger semantics do not replay.")
    return ledger


def _validate_threshold_decision(
    value: Mapping[str, Any],
    protocol: Mapping[str, Any],
    pilot_ledger: Mapping[str, Any],
) -> dict[str, Any]:
    decision = deepcopy(dict(value))
    expected_digest = decision.pop("decision_digest", None)
    if expected_digest != semantic_digest(decision):
        raise ProspectiveQualificationError("Pilot threshold decision digest does not replay.")
    decision["decision_digest"] = expected_digest
    expected_ref = {
        "protocol_id": protocol["protocol_id"],
        "protocol_digest": protocol["protocol_digest"],
    }
    if (
        decision.get("artifact_kind") != "prospective_pilot_threshold_decision"
        or decision.get("protocol_ref") != expected_ref
    ):
        raise ProspectiveQualificationError("Threshold decision is not bound to this protocol.")
    replayed = freeze_pilot_threshold_decision(
        protocol,
        pilot_ledger,
        {
            key: decision[key]
            for key in (
                "decision_id",
                "metric_definitions",
                "promotion_thresholds",
                "zero_high_severity_false_accusations_required",
                "approved_for_heldout_opening",
            )
        },
        decided_at=str(decision["decided_at"]),
    )
    if replayed != decision:
        raise ProspectiveQualificationError("Pilot threshold decision semantics do not replay.")
    return decision


def _participant(
    participants: Mapping[str, Mapping[str, Any]], participant_id: Any, role: str
) -> Mapping[str, Any]:
    identifier = _nonempty(participant_id, f"{role} participant_id")
    participant = participants.get(identifier)
    if participant is None or participant["role"] != role:
        raise ProspectiveQualificationError(
            f"Participant {identifier!r} is not registered as {role}."
        )
    return participant


def _participant_ids(value: Any, label: str, expected_count: int) -> list[str]:
    identifiers = [_nonempty(item, label) for item in _sequence(value, label)]
    if len(identifiers) != expected_count or len(set(identifiers)) != expected_count:
        raise ProspectiveQualificationError(
            f"{label} requires exactly {expected_count} distinct participant identities."
        )
    return identifiers


def _item_by_id(
    values: Sequence[Mapping[str, Any]], key: str, identifier: str, label: str
) -> Mapping[str, Any]:
    matches = [item for item in values if item.get(key) == identifier]
    if len(matches) != 1:
        raise ProspectiveQualificationError(f"Unknown or duplicate {label} {identifier!r}.")
    return matches[0]


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ProspectiveQualificationError(
            f"{label} has unexpected fields; expected={sorted(expected)}, received={sorted(value)}."
        )


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ProspectiveQualificationError(f"{label} must be an object.")
    return dict(value)


def _nonempty_mapping(value: Any, label: str) -> dict[str, Any]:
    result = deepcopy(_mapping(value, label))
    if not result:
        raise ProspectiveQualificationError(f"{label} must not be empty.")
    return result


def _sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ProspectiveQualificationError(f"{label} must be an array.")
    return list(value)


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProspectiveQualificationError(f"{label} must be a non-empty string.")
    return value


def _digest(value: Any, label: str) -> str:
    digest = _nonempty(value, label)
    if not digest.startswith("sha256:") or len(digest) != 71:
        raise ProspectiveQualificationError(f"{label} must be a full sha256 digest.")
    try:
        int(digest[7:], 16)
    except ValueError as error:
        raise ProspectiveQualificationError(f"{label} must be a full sha256 digest.") from error
    return digest


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ProspectiveQualificationError(f"Invalid timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise ProspectiveQualificationError("Qualification timestamps must include a timezone.")
    return parsed
