"""Semantic-only Stage-2 payload schema and deterministic AgentReview projection.

Mirrors ``review_semantic_payload`` for the Stage-2 scientific adjudication:
one compact, strictly validated reviewer payload per batched call is projected
into public AgentReview records bound to the frozen Stage-2 packets. The
reviewer states verdict, issue class, evidence with exact complete-line spans,
a falsification attempt, and the frozen Stage-1 candidate identities it
reconciles with; every semantic field of the public record derives from that
payload plus frozen inputs, never from controller-authored summaries.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from jsonschema import Draft202012Validator

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import sha256_digest, stable_id
from sc_referee.records.root_cause import REVIEW_LOCAL_IDENTITY_PROFILE, root_cause_candidate_id
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.version import SCHEMA_VERSION
from sc_referee_evaluation.review_protocol import (
    ReviewProtocolError,
    validate_stage2_review_submission,
)
from sc_referee_evaluation.review_semantic_payload import (
    ReviewSemanticPayloadError,
    _evidence_items,
    _timestamp,
)

_VERDICTS = [
    "demonstrated_issue",
    "no_demonstrated_issue_within_scope",
    "conditional_or_unknown",
    "insufficient_evidence",
]

_STAGE2_BLINDNESS = {
    "answer_key_hidden": False,
    "benchmark_grade_hidden": False,
    "detector_identity_hidden": True,
    "other_reviews_hidden": False,
    "sc_referee_output_hidden": True,
}


def build_stage2_batch_output_schema(
    participant_id: str, case_ids: Sequence[str], canonical_issue_class: str
) -> dict[str, Any]:
    """Return the strict semantic-only schema for one prospectively batched Stage-2 call."""

    cases = list(case_ids)
    if (
        not participant_id
        or not canonical_issue_class
        or not cases
        or len(cases) != len(set(cases))
    ):
        raise ReviewSemanticPayloadError(
            "A Stage-2 batch requires one participant and unique cases."
        )
    span = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "path": {"type": "string", "minLength": 1},
            "start_line": {"type": "integer", "minimum": 1},
            "end_line": {"type": "integer", "minimum": 1},
            "quoted_text": {"type": "string", "minLength": 1},
        },
        "required": ["path", "start_line", "end_line", "quoted_text"],
    }
    atom = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "description": {"type": "string", "minLength": 1},
            "observed_value": {},
            "source_spans": {"type": "array", "minItems": 1, "items": span},
        },
        "required": ["description", "source_spans"],
    }
    review = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "case_id": {"type": "string", "enum": cases},
            "verdict": {"type": "string", "enum": _VERDICTS},
            "bounded_statement": {"type": ["string", "null"]},
            "root_cause": {"type": ["string", "null"]},
            "issue_class": {"type": ["string", "null"]},
            "reconciled_stage1_candidate_ids": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "uniqueItems": True,
            },
            "evidence_atoms": {"type": "array", "minItems": 1, "items": atom},
            "counterevidence_atoms": {"type": "array", "minItems": 1, "items": atom},
            "equivalence_atoms": {"type": "array", "items": atom},
            "falsification_attempt": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "strongest_innocent_explanation": {"type": "string", "minLength": 1},
                    "reversing_premises": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "uniqueItems": True,
                    },
                    "outcome": {
                        "type": "string",
                        "enum": ["root_cause_survived", "label_reversed", "unresolved"],
                    },
                    "material_dissent": {"type": "boolean"},
                },
                "required": [
                    "strongest_innocent_explanation",
                    "reversing_premises",
                    "outcome",
                    "material_dissent",
                ],
            },
            "cross_case_evidence_used": {"type": "boolean", "const": False},
            "unresolved_material_questions": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "uniqueItems": True,
            },
            "self_reported_confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
            },
        },
        "required": [
            "case_id",
            "verdict",
            "bounded_statement",
            "root_cause",
            "issue_class",
            "reconciled_stage1_candidate_ids",
            "evidence_atoms",
            "counterevidence_atoms",
            "equivalence_atoms",
            "falsification_attempt",
            "cross_case_evidence_used",
            "unresolved_material_questions",
            "self_reported_confidence",
        ],
        "allOf": [
            {
                "if": {
                    "properties": {"verdict": {"const": "demonstrated_issue"}},
                    "required": ["verdict"],
                },
                "then": {
                    "properties": {
                        "bounded_statement": {"type": "string", "minLength": 1},
                        "root_cause": {"type": "string", "minLength": 1},
                        "issue_class": {
                            "type": "string",
                            "const": canonical_issue_class,
                        },
                        "reconciled_stage1_candidate_ids": {"minItems": 2},
                        "equivalence_atoms": {"minItems": 1},
                    }
                },
                "else": {
                    "properties": {
                        "bounded_statement": {"type": "null"},
                        "root_cause": {"type": "null"},
                        "issue_class": {"type": "null"},
                        "reconciled_stage1_candidate_ids": {"maxItems": 0},
                        "equivalence_atoms": {"maxItems": 0},
                    }
                },
            }
        ],
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "reviewer_participant_id": {"type": "string", "const": participant_id},
            "reviews": {
                "type": "array",
                "minItems": len(cases),
                "maxItems": len(cases),
                "items": review,
            },
        },
        "required": ["reviewer_participant_id", "reviews"],
    }


def _frozen_candidates(packet: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    available: dict[str, dict[str, Any]] = {}
    for item in packet.get("frozen_stage1_reviews", []):
        identity = item.get("root_cause_identity")
        if isinstance(identity, dict):
            candidate_id = str(identity["candidate_root_cause_id"])
            available[candidate_id] = {
                "review_ref": deepcopy(item["review_ref"]),
                "candidate_root_cause_id": candidate_id,
            }
    return available


def project_stage2_semantic_batch(
    payload: Mapping[str, Any],
    *,
    output_schema: Mapping[str, Any],
    participant_id: str,
    participant_reviewer_agent: Mapping[str, Any],
    packets_by_case: Mapping[str, Mapping[str, Any]],
    workspace_payloads_by_case: Mapping[str, Mapping[str, bytes]],
    canonical_issue_class: str,
    transcript: bytes,
    completed_at: str,
    schema_root: Any,
) -> list[dict[str, Any]]:
    """Validate one semantic response and deterministically construct Stage-2 AgentReviews."""

    try:
        Draft202012Validator(dict(output_schema)).validate(dict(payload))
    except Exception as error:
        raise ReviewSemanticPayloadError(f"Stage-2 semantic payload is invalid: {error}") from error
    if payload.get("reviewer_participant_id") != participant_id:
        raise ReviewSemanticPayloadError(
            "Stage-2 semantic payload participant does not match the requested participant."
        )
    _timestamp(completed_at)
    reviews = payload.get("reviews")
    if not isinstance(reviews, list):  # pragma: no cover - schema invariant
        raise ReviewSemanticPayloadError("Stage-2 semantic payload reviews are absent.")
    case_ids = [str(item["case_id"]) for item in reviews]
    expected_cases = set(packets_by_case)
    if len(case_ids) != len(set(case_ids)) or set(case_ids) != expected_cases:
        raise ReviewSemanticPayloadError("Stage-2 semantic payload must cover each packet once.")
    if set(workspace_payloads_by_case) != expected_cases:
        raise ReviewSemanticPayloadError("Stage-2 workspace payloads do not match the packets.")
    for packet in packets_by_case.values():
        expected_agent = deepcopy(dict(participant_reviewer_agent))
        expected_agent["task_prompt_digest"] = packet.get("prompt", {}).get("prompt_digest")
        if packet.get("expected_reviewer_agent") != expected_agent:
            raise ReviewSemanticPayloadError(
                "A Stage-2 packet reviewer configuration does not match the bound participant."
            )

    transcript_digest = sha256_digest(transcript)
    projected: list[dict[str, Any]] = []
    for semantic in reviews:
        case_id = str(semantic["case_id"])
        packet = dict(packets_by_case[case_id])
        paths = workspace_payloads_by_case[case_id]
        reviewed_paths = sorted(paths)
        evidence = _evidence_items(
            semantic["evidence_atoms"],
            case_id=case_id,
            participant_id=participant_id,
            support_role="supports",
            payloads=paths,
        )
        counterevidence = _evidence_items(
            semantic["counterevidence_atoms"],
            case_id=case_id,
            participant_id=participant_id,
            support_role="counterevidence",
            payloads=paths,
        )
        verdict = str(semantic["verdict"])
        equivalence = (
            _evidence_items(
                semantic["equivalence_atoms"],
                case_id=case_id,
                participant_id=participant_id,
                support_role="context",
                payloads=paths,
            )
            if semantic["equivalence_atoms"]
            else []
        )
        falsification = dict(semantic["falsification_attempt"])
        available_candidates = _frozen_candidates(packet)
        selected_ids = [str(value) for value in semantic["reconciled_stage1_candidate_ids"]]
        unknown = sorted(set(selected_ids) - set(available_candidates))
        if unknown:
            raise ReviewSemanticPayloadError(
                f"Stage-2 reconciliation cites unknown Stage-1 candidates: {unknown}"
            )
        review_id = stable_id(
            "review",
            "stage2-scientific-adjudication",
            case_id,
            participant_id,
            str(packet["packet_digest"]),
            transcript_digest,
        )
        review: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "agent_review",
            "review_id": review_id,
            "case_id": case_id,
            "stage": "stage2_scientific_adjudication",
            "reviewer_agent": deepcopy(packet["expected_reviewer_agent"]),
            "blindness": {
                **_STAGE2_BLINDNESS,
                "exceptions": [],
            },
            "scope": {
                "claim_refs": [],
                "issue_class_scope": [canonical_issue_class],
                "reviewed_paths": reviewed_paths,
            },
            "verdict": verdict,
            "confidence_used_for_labeling": False,
            "transcript_digest": transcript_digest,
            "completed_at": completed_at,
            "provenance": {
                "actor": {
                    "actor_kind": "controller",
                    "actor_id": "software:sc-referee-eval",
                    "display_name": "sc-referee evaluation controller",
                },
                "method": "deterministic_semantic_review_projection",
                "created_at": completed_at,
                "tool": "sc-referee-eval",
                "tool_version": "0.1.0",
            },
            "root_cause_identity": None,
            "bounded_statement": semantic["bounded_statement"],
            "root_cause": semantic["root_cause"],
            "issue_class": semantic["issue_class"],
            "evidence": evidence,
            "counterevidence_considered": counterevidence,
            "falsification_attempt": {
                "strongest_innocent_explanation": falsification["strongest_innocent_explanation"],
                "reversing_premises": list(falsification["reversing_premises"]),
                "evidence_tested": deepcopy(counterevidence),
                "outcome": falsification["outcome"],
                "material_dissent": falsification["material_dissent"],
                "notes": None,
            },
            "affected_record_refs": [],
            "unresolved_material_questions": list(semantic["unresolved_material_questions"]),
            "self_reported_confidence": semantic["self_reported_confidence"],
            "extensions": {
                "x-review-packet-digest": packet["packet_digest"],
                "x-stage1-freeze-digest": packet["stage1_freeze_digest"],
                "x-cross-case-evidence-used": semantic["cross_case_evidence_used"],
            },
        }
        if verdict == "demonstrated_issue":
            review["root_cause_identity"] = {
                "candidate_root_cause_id": root_cause_candidate_id(review),
                "identity_profile": REVIEW_LOCAL_IDENTITY_PROFILE,
                "reconciled_stage1_candidates": [
                    deepcopy(available_candidates[candidate_id])
                    for candidate_id in sorted(selected_ids)
                ],
                "equivalence_evidence": equivalence,
            }
        try:
            LocalSchemaRegistry(schema_root).validate(review)
            validate_stage2_review_submission(review, packet, schema_root)
        except (RecordValidationError, ReviewProtocolError) as error:
            raise ReviewSemanticPayloadError(str(error)) from error
        projected.append(review)
    return sorted(projected, key=lambda item: str(item["case_id"]))
