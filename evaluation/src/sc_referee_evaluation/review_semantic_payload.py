from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.root_cause import REVIEW_LOCAL_IDENTITY_PROFILE, root_cause_candidate_id
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.version import SCHEMA_VERSION
from sc_referee_evaluation.review_protocol import (
    ReviewProtocolError,
    validate_stage1_review_submission,
)


class ReviewSemanticPayloadError(ValueError):
    """A semantic-only reviewer response cannot be projected into public review records."""


_VERDICTS = [
    "demonstrated_issue",
    "no_demonstrated_issue_within_scope",
    "conditional_or_unknown",
    "insufficient_evidence",
]


def build_stage1_batch_output_schema(
    participant_id: str, case_ids: Sequence[str], canonical_issue_class: str
) -> dict[str, Any]:
    """Return the strict semantic-only schema for one prospectively batched Stage-1 call."""

    cases = list(case_ids)
    if (
        not participant_id
        or not canonical_issue_class
        or not cases
        or len(cases) != len(set(cases))
    ):
        raise ReviewSemanticPayloadError(
            "A Stage-1 batch requires one participant and unique cases."
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
            "evidence_atoms": {"type": "array", "minItems": 1, "items": atom},
            "counterevidence_atoms": {"type": "array", "minItems": 1, "items": atom},
            "falsification_attempt": {"type": "string", "minLength": 1},
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
            "evidence_atoms",
            "counterevidence_atoms",
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
                    }
                },
                "else": {
                    "properties": {
                        "bounded_statement": {"type": "null"},
                        "root_cause": {"type": "null"},
                        "issue_class": {"type": "null"},
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


def project_stage1_semantic_batch(
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
    """Validate one semantic response and deterministically construct Stage-1 AgentReviews."""

    try:
        Draft202012Validator(dict(output_schema)).validate(dict(payload))
    except Exception as error:
        raise ReviewSemanticPayloadError(f"Stage-1 semantic payload is invalid: {error}") from error
    if payload.get("reviewer_participant_id") != participant_id:
        raise ReviewSemanticPayloadError(
            "Stage-1 semantic payload participant does not match the requested participant."
        )
    _timestamp(completed_at)
    reviews = payload.get("reviews")
    if not isinstance(reviews, list):  # pragma: no cover - schema invariant
        raise ReviewSemanticPayloadError("Stage-1 semantic payload reviews are absent.")
    case_ids = [str(item["case_id"]) for item in reviews]
    expected_cases = set(packets_by_case)
    if len(case_ids) != len(set(case_ids)) or set(case_ids) != expected_cases:
        raise ReviewSemanticPayloadError("Stage-1 semantic payload must cover each packet once.")
    if set(workspace_payloads_by_case) != expected_cases:
        raise ReviewSemanticPayloadError("Stage-1 workspace payloads do not match the packets.")
    for packet in packets_by_case.values():
        expected_agent = deepcopy(dict(participant_reviewer_agent))
        expected_agent["task_prompt_digest"] = packet.get("prompt", {}).get("prompt_digest")
        if packet.get("expected_reviewer_agent") != expected_agent:
            raise ReviewSemanticPayloadError(
                "A Stage-1 packet reviewer configuration does not match the bound participant."
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
        issue_class = semantic["issue_class"]
        review_id = stable_id(
            "review",
            "stage1-blind",
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
            "stage": "stage1_blind",
            "reviewer_agent": deepcopy(packet["expected_reviewer_agent"]),
            "blindness": {
                "answer_key_hidden": True,
                "benchmark_grade_hidden": True,
                "detector_identity_hidden": True,
                "exceptions": [],
                "other_reviews_hidden": True,
                "sc_referee_output_hidden": True,
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
            "issue_class": issue_class,
            "evidence": evidence,
            "counterevidence_considered": counterevidence,
            "affected_record_refs": [],
            "unresolved_material_questions": list(semantic["unresolved_material_questions"]),
            "self_reported_confidence": semantic["self_reported_confidence"],
            "extensions": {
                "x-review-packet-digest": packet["packet_digest"],
                "x-stage1-falsification-attempt": semantic["falsification_attempt"],
                "x-cross-case-evidence-used": semantic["cross_case_evidence_used"],
            },
        }
        if verdict == "demonstrated_issue":
            review["root_cause_identity"] = {
                "candidate_root_cause_id": root_cause_candidate_id(review),
                "identity_profile": REVIEW_LOCAL_IDENTITY_PROFILE,
                "reconciled_stage1_candidates": [],
                "equivalence_evidence": [],
            }
        try:
            LocalSchemaRegistry(schema_root).validate(review)
            validate_stage1_review_submission(review, packet, schema_root)
        except (RecordValidationError, ReviewProtocolError) as error:
            raise ReviewSemanticPayloadError(str(error)) from error
        projected.append(review)
    return sorted(projected, key=lambda item: str(item["case_id"]))


def _evidence_items(
    atoms: Any,
    *,
    case_id: str,
    participant_id: str,
    support_role: str,
    payloads: Mapping[str, bytes],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, atom in enumerate(atoms, start=1):
        source_refs = [_source_ref(span, payloads=payloads) for span in atom["source_spans"]]
        item: dict[str, Any] = {
            "evidence_id": stable_id(
                "evidence",
                "stage1",
                case_id,
                participant_id,
                support_role,
                str(index),
                semantic_digest({"atom": atom, "source_refs": source_refs}),
            ),
            "description": atom["description"],
            "support_role": support_role,
            "source_refs": source_refs,
            "record_refs": [],
        }
        if "observed_value" in atom:
            item["observed_value"] = atom["observed_value"]
        items.append(item)
    return items


def _source_ref(span: Mapping[str, Any], *, payloads: Mapping[str, bytes]) -> dict[str, Any]:
    path_value = str(span["path"])
    relative = PurePosixPath(path_value)
    if (
        not path_value
        or relative.is_absolute()
        or "." in relative.parts
        or ".." in relative.parts
        or path_value not in payloads
    ):
        raise ReviewSemanticPayloadError(f"Review evidence cites unavailable path {path_value!r}.")
    try:
        text = payloads[path_value].decode("utf-8")
    except UnicodeDecodeError as error:
        raise ReviewSemanticPayloadError(
            f"Review evidence path {path_value!r} is not UTF-8 text."
        ) from error
    lines = text.splitlines()
    start = int(span["start_line"])
    end = int(span["end_line"])
    if start > end or end > len(lines):
        raise ReviewSemanticPayloadError(
            f"Review evidence span {path_value}:{start}-{end} is outside the visible file."
        )
    exact = "\n".join(lines[start - 1 : end])
    if span["quoted_text"] != exact:
        raise ReviewSemanticPayloadError(
            f"Review evidence quote does not equal exact complete lines at {path_value}:{start}-{end}."
        )
    return {
        "source_kind": "file_span",
        "locator": f"{path_value}:L{start}-L{end}",
        "path": path_value,
        "content_digest": sha256_digest(payloads[path_value]),
        "start_line": start,
        "end_line": end,
        "quoted_text": exact,
        "external": False,
    }


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ReviewSemanticPayloadError(f"Invalid review timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise ReviewSemanticPayloadError("Review timestamps must include an offset.")
    return parsed
