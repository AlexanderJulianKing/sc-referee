from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import canonical_json, semantic_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee_evaluation.snapshot_evidence import (
    SnapshotEvidenceError,
    read_full_digest_snapshot_file,
    validate_content_addressed_snapshot,
)


class ExactJsonGraderError(ValueError):
    """An exact JSON grading input violates the bounded non-executing profile."""


def grade_exact_json_output(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    snapshot: dict[str, Any],
    file_records: list[dict[str, Any]],
    asset_identities: list[dict[str, Any]],
    materialized_root: Path,
    grader_spec: dict[str, Any],
    schema_root: Path,
    *,
    graded_at: str,
    output: Path,
) -> dict[str, Any]:
    """Compare one exact JSON value without executing or interpreting the workflow."""

    if output.exists() or output.is_symlink():
        raise ExactJsonGraderError(f"Exact JSON grade output already exists: {output}")
    _validate_public_records(
        fixture, adjudication, snapshot, file_records, asset_identities, schema_root
    )
    _validate_grader_spec(fixture, adjudication, grader_spec)
    if _timestamp(graded_at) < _timestamp(str(snapshot["captured_at"])):
        raise ExactJsonGraderError("Exact JSON grading cannot precede snapshot capture.")
    snapshot_id = str(snapshot["snapshot_id"])
    fixture_snapshot_ref = fixture["snapshot_ref"]
    if fixture_snapshot_ref != {
        "record_type": "repository_snapshot",
        "record_id": snapshot_id,
    }:
        raise ExactJsonGraderError(
            "BenchmarkFixture snapshot_ref does not resolve to the supplied snapshot."
        )
    actual_spec = grader_spec["actual"]
    path_value = str(actual_spec["path"])
    try:
        snapshot_index = validate_content_addressed_snapshot(
            snapshot, file_records, asset_identities
        )
        file_record, identity, payload, content_digest = read_full_digest_snapshot_file(
            snapshot_index, materialized_root, path_value
        )
    except SnapshotEvidenceError as error:
        raise ExactJsonGraderError(str(error)) from error
    identity_id = str(identity["asset_identity_id"])

    document = _load_strict_json(payload, path_value)
    actual_value = _resolve_json_pointer(document, str(actual_spec["json_pointer"]))
    expected_value = grader_spec["expected_value"]
    try:
        actual_digest = semantic_digest({"value": actual_value})
    except (TypeError, ValueError, UnicodeError) as error:
        raise ExactJsonGraderError("Actual value is not canonical JSON data.") from error
    expected_digest = semantic_digest({"value": expected_value})
    exact_match = canonical_json(actual_value) == canonical_json(expected_value)
    grader_spec_digest = semantic_digest(grader_spec)
    grade: dict[str, Any] = {
        "evaluation_protocol_version": "0.1.0",
        "record_type": "evaluation_exact_json_grade",
        "grade_id": stable_id(
            "exact-json-grade",
            str(fixture["fixture_id"]),
            str(snapshot["snapshot_digest"]),
            grader_spec_digest,
        ),
        "case_id": grader_spec["case_id"],
        "fixture_id": fixture["fixture_id"],
        "adjudication_ref": {
            "record_type": "benchmark_adjudication",
            "record_id": adjudication["adjudication_id"],
        },
        "snapshot_ref": {
            "record_type": "repository_snapshot",
            "record_id": snapshot_id,
        },
        "snapshot_digest": snapshot["snapshot_digest"],
        "grader_spec_digest": grader_spec_digest,
        "comparison_profile": "exact_canonical_json_v1",
        "actual": {
            "path": path_value,
            "json_pointer": actual_spec["json_pointer"],
            "content_digest": content_digest,
            "file_record_ref": {
                "record_type": "file_record",
                "record_id": file_record["file_record_id"],
            },
            "asset_identity_ref": {
                "record_type": "asset_identity",
                "record_id": identity_id,
            },
            "value_digest": actual_digest,
        },
        "expected_value_digest": expected_digest,
        "grade_status": "exact_match" if exact_match else "exact_mismatch",
        "exact_match": exact_match,
        "metric_eligible": False,
        "project_code_executed": False,
        "graded_at": graded_at,
        "non_inferences": [
            "Exact final-value agreement does not establish scientific or analytical validity.",
            "Exact mismatch does not establish a demonstrated scientific issue.",
            "This grade does not admit a benchmark label, detector metric, or Finding.",
        ],
    }
    grade["grade_digest"] = semantic_digest(grade)
    write_normalized_json_once(output, grade)
    return grade


def _validate_public_records(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    snapshot: dict[str, Any],
    file_records: list[dict[str, Any]],
    asset_identities: list[dict[str, Any]],
    schema_root: Path,
) -> None:
    registry = LocalSchemaRegistry(schema_root)
    try:
        for record in [fixture, adjudication, snapshot, *file_records, *asset_identities]:
            registry.validate(record)
    except RecordValidationError as error:
        raise ExactJsonGraderError(str(error)) from error


def _validate_grader_spec(
    fixture: dict[str, Any], adjudication: dict[str, Any], grader_spec: dict[str, Any]
) -> None:
    if set(grader_spec) != {
        "case_id",
        "fixture_id",
        "comparison_profile",
        "actual",
        "expected_value",
    }:
        raise ExactJsonGraderError("Exact JSON grader specification has unexpected fields.")
    if grader_spec.get("fixture_id") != fixture.get("fixture_id"):
        raise ExactJsonGraderError("Grader specification fixture_id does not match the fixture.")
    if fixture.get("adjudication_ref") != {
        "record_type": "benchmark_adjudication",
        "record_id": adjudication.get("adjudication_id"),
    } or grader_spec.get("case_id") != adjudication.get("case_id"):
        raise ExactJsonGraderError(
            "Fixture, adjudication, and grader specification case identity do not match."
        )
    if grader_spec.get("comparison_profile") != "exact_canonical_json_v1":
        raise ExactJsonGraderError("Unsupported exact JSON comparison profile.")
    actual = grader_spec.get("actual")
    if not isinstance(actual, dict) or set(actual) != {"path", "json_pointer"}:
        raise ExactJsonGraderError("Grader actual locator must contain path and json_pointer.")
    if not isinstance(actual.get("path"), str) or not isinstance(actual.get("json_pointer"), str):
        raise ExactJsonGraderError("Grader actual path and json_pointer must be strings.")
    try:
        canonical_json(grader_spec["expected_value"])
    except (TypeError, ValueError) as error:
        raise ExactJsonGraderError("Expected value is not canonical JSON data.") from error


def _load_strict_json(payload: bytes, path_value: str) -> Any:
    def reject_constant(value: str) -> None:
        raise ExactJsonGraderError(
            f"Graded JSON {path_value!r} contains non-finite constant {value!r}."
        )

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ExactJsonGraderError(
                    f"Graded JSON {path_value!r} contains duplicate key {key!r}."
                )
            result[key] = value
        return result

    try:
        return json.loads(
            payload.decode("utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=unique_object,
        )
    except UnicodeDecodeError as error:
        raise ExactJsonGraderError(f"Graded JSON {path_value!r} is not UTF-8.") from error
    except json.JSONDecodeError as error:
        raise ExactJsonGraderError(f"Graded JSON {path_value!r} is invalid.") from error


def _resolve_json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ExactJsonGraderError("JSON Pointer must be empty or begin with '/'.")
    current = document
    for raw_token in pointer[1:].split("/"):
        token = _unescape_pointer_token(raw_token)
        if isinstance(current, dict):
            if token not in current:
                raise ExactJsonGraderError(f"JSON Pointer key {token!r} does not exist.")
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit() or (len(token) > 1 and token.startswith("0")):
                raise ExactJsonGraderError(f"JSON Pointer array index {token!r} is invalid.")
            index = int(token)
            if index >= len(current):
                raise ExactJsonGraderError(f"JSON Pointer array index {index} is out of range.")
            current = current[index]
        else:
            raise ExactJsonGraderError("JSON Pointer traverses a scalar value.")
    return current


def _unescape_pointer_token(token: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(token):
        character = token[index]
        if character != "~":
            result.append(character)
            index += 1
            continue
        if index + 1 >= len(token) or token[index + 1] not in {"0", "1"}:
            raise ExactJsonGraderError("JSON Pointer contains an invalid '~' escape.")
        result.append("~" if token[index + 1] == "0" else "/")
        index += 2
    return "".join(result)


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ExactJsonGraderError(f"Invalid exact JSON grade timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise ExactJsonGraderError("Exact JSON grade timestamps must include an offset.")
    return parsed
