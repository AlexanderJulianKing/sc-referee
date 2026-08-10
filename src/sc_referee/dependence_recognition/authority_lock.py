"""Closed, dependence-specific authorization-lock validation.

This module deliberately does not expose a generic trusted-record injection
surface.  It accepts one exact four-record dependence authorization bundle,
binds it to already frozen source, report, and material-input identities, and
returns a dataclass-replaced inspection context.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    RecordRef,
)

LOCK_KIND = "dependence_method_authorization_v1"
AUTHORITY_LIMITATIONS = (
    "Authorization is limited to this case, input digest, procedure and ordered key.",
    "It establishes no execution, numerical impact or general scientific correctness.",
)
_ROOT_KEYS = frozenset(
    {
        "lock_kind",
        "case_id",
        "records",
        "approval",
        "authority_limitations",
        "lock_digest",
    }
)
_RECORD_TYPES = (
    "analysis",
    "procedure",
    "result",
    "human_method_authorization",
)
_RECORD_ID_PREFIX = {
    "analysis": "analysis:",
    "procedure": "procedure:",
    "result": "result:",
    "human_method_authorization": "authorization:",
}
_PROCEDURES = frozenset(
    {
        "scipy.stats.ttest_ind",
        "scipy.stats.mannwhitneyu",
        "scipy.stats.ttest_rel",
    }
)
_DEFAULT_ROLE_MARKERS = frozenset(
    {
        "error_bearing",
        "corrected_twin",
        "valid_alternative",
        "hard_negative",
        "ambiguous",
        "unsupported",
        "positive_demonstrated",
        "verified_good_eligible",
        "ambiguous_control",
        "unsupported_control",
    }
)
_CASE_ID_RE = re.compile(r"case:[A-Za-z0-9][A-Za-z0-9._-]{7,127}\Z")
_RECORD_ID_RE = re.compile(r"[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._-]{7,255}\Z")
_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")


class DependenceAuthorizationLockError(ValueError):
    """Raised when a private dependence authority lock fails closed."""


@dataclass(frozen=True)
class VerifiedDependenceAuthorizationLock:
    """One closed lock after schema, digest, and case-binding verification."""

    case_id: str
    records: tuple[dict[str, Any], ...]
    approved_projection_digest: str
    lock_digest: str
    canonical_payload: bytes


def approval_projection(lock: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact projection a human approves before review."""

    return {
        "lock_kind": lock.get("lock_kind"),
        "case_id": lock.get("case_id"),
        "records": lock.get("records"),
        "authority_limitations": lock.get("authority_limitations"),
    }


def lock_projection(lock: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact lock-digest projection (everything except its digest)."""

    return {key: value for key, value in lock.items() if key != "lock_digest"}


def verify_dependence_authorization_lock(
    lock_path: Path,
    *,
    expected_case_id: str | None = None,
    source_paths: Iterable[str] | None = None,
    selected_report_path: str | None = None,
    material_input_digests: Mapping[str, str] | None = None,
    forbidden_role_markers: Iterable[str] = (),
) -> VerifiedDependenceAuthorizationLock:
    """Parse and verify one exact private dependence authorization lock.

    The optional bindings are controller facts, not caller-supplied record
    extensions.  When present they narrow the accepted source, selected report,
    material input, case id, and role-blindness envelope.
    """

    try:
        payload = lock_path.read_bytes()
    except OSError as error:
        raise DependenceAuthorizationLockError("dependence authority lock is unreadable") from error
    if not payload or len(payload) > 64 * 1024:
        raise DependenceAuthorizationLockError("dependence authority lock size is invalid")
    try:
        text = payload.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=_closed_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DependenceAuthorizationLockError(
            "dependence authority lock is not strict duplicate-free JSON"
        ) from error
    if not isinstance(value, dict) or set(value) != _ROOT_KEYS:
        raise DependenceAuthorizationLockError("dependence authority lock root is not closed")
    if value.get("lock_kind") != LOCK_KIND:
        raise DependenceAuthorizationLockError("dependence authority lock kind is invalid")

    case_id = value.get("case_id")
    if not isinstance(case_id, str) or _CASE_ID_RE.fullmatch(case_id) is None:
        raise DependenceAuthorizationLockError("dependence authority case id is not opaque")
    if expected_case_id is not None and case_id != expected_case_id:
        raise DependenceAuthorizationLockError("dependence authority lock names another case")

    markers = _normalized_markers((*_DEFAULT_ROLE_MARKERS, *forbidden_role_markers))
    if _contains_marker(value, markers):
        raise DependenceAuthorizationLockError("dependence authority lock leaks a case role")

    records = value.get("records")
    if not isinstance(records, list) or len(records) != len(_RECORD_TYPES):
        raise DependenceAuthorizationLockError(
            "dependence authority lock requires exactly four records"
        )
    if [item.get("record_type") if isinstance(item, dict) else None for item in records] != list(
        _RECORD_TYPES
    ):
        raise DependenceAuthorizationLockError(
            "dependence authority lock record types or order are invalid"
        )
    analysis, procedure, result, authorization = records
    _verify_analysis_record(analysis, source_paths)
    _verify_procedure_record(procedure)
    _verify_result_record(result, selected_report_path)
    _verify_authorization_record(
        authorization,
        analysis=analysis,
        procedure=procedure,
        material_input_digests=material_input_digests,
    )

    refs = [(str(item["record_type"]), str(item["record_id"])) for item in records]
    if len(refs) != len(set(refs)):
        raise DependenceAuthorizationLockError("dependence authority lock repeats a record ref")

    limitations = value.get("authority_limitations")
    if limitations != list(AUTHORITY_LIMITATIONS):
        raise DependenceAuthorizationLockError(
            "dependence authority limitations are not the closed v1 text"
        )
    approval = _verify_approval(value.get("approval"), authorization)
    expected_approval_digest = semantic_digest(approval_projection(value))
    if approval["approved_projection_digest"] != expected_approval_digest:
        raise DependenceAuthorizationLockError(
            "dependence authority approved projection digest does not replay"
        )
    expected_lock_digest = semantic_digest(lock_projection(value))
    if value.get("lock_digest") != expected_lock_digest:
        raise DependenceAuthorizationLockError("dependence authority lock digest does not replay")

    return VerifiedDependenceAuthorizationLock(
        case_id=case_id,
        records=tuple(dict(item) for item in records),
        approved_projection_digest=expected_approval_digest,
        lock_digest=expected_lock_digest,
        canonical_payload=(canonical_json(value) + "\n").encode("utf-8"),
    )


def apply_dependence_authorization_lock(
    context: FrozenInspectionContext,
    lock_path: Path,
    *,
    expected_case_id: str | None = None,
) -> FrozenInspectionContext:
    """Validate and append the closed four-record bundle to a frozen context."""

    selected_report_path = _selected_report_path(context)
    if selected_report_path is None:
        raise DependenceAuthorizationLockError(
            "dependence authority lock lacks one selected report binding"
        )
    if any(
        not reverify_material_digest(item.content, item.content_digest)
        for item in context.material_inputs
    ):
        raise DependenceAuthorizationLockError(
            "dependence authority material bytes do not replay their frozen digest"
        )
    verified = verify_dependence_authorization_lock(
        lock_path,
        expected_case_id=expected_case_id,
        source_paths=(item.path for item in context.documents),
        selected_report_path=selected_report_path,
        material_input_digests={item.path: item.content_digest for item in context.material_inputs},
    )

    additions: list[FrozenBaseRecord] = []
    existing_refs = {item.ref for item in context.base_records}
    for record in verified.records:
        ref = RecordRef(str(record["record_type"]), str(record["record_id"]))
        if ref in existing_refs or any(item.ref == ref for item in additions):
            raise DependenceAuthorizationLockError(
                "dependence authority record ref collides with the frozen base view"
            )
        additions.append(FrozenBaseRecord.from_record(ref, record))
    return replace(
        context,
        base_records=tuple(sorted((*context.base_records, *additions), key=lambda item: item.ref)),
    )


def _closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DependenceAuthorizationLockError(
                "dependence authority lock contains a duplicate JSON key"
            )
        value[key] = item
    return value


def _verify_analysis_record(record: object, source_paths: Iterable[str] | None) -> None:
    value = _require_record(record, "analysis", {"record_type", "record_id", "path"})
    path = _relative_path(value.get("path"), "analysis source")
    if source_paths is not None and list(source_paths).count(path) != 1:
        raise DependenceAuthorizationLockError(
            "dependence authority analysis source is not exactly frozen once"
        )


def _verify_procedure_record(record: object) -> None:
    value = _require_record(
        record,
        "procedure",
        {"record_type", "record_id", "resolved_callable"},
    )
    if value.get("resolved_callable") not in _PROCEDURES:
        raise DependenceAuthorizationLockError(
            "dependence authority procedure is outside the v1 registry"
        )


def _verify_result_record(record: object, selected_report_path: str | None) -> None:
    value = _require_record(record, "result", {"record_type", "record_id", "path"})
    path = _relative_path(value.get("path"), "selected result")
    if selected_report_path is not None and path != selected_report_path:
        raise DependenceAuthorizationLockError(
            "dependence authority result does not name the selected report"
        )


def _verify_authorization_record(
    record: object,
    *,
    analysis: dict[str, Any],
    procedure: dict[str, Any],
    material_input_digests: Mapping[str, str] | None,
) -> None:
    value = _require_record(
        record,
        "human_method_authorization",
        {
            "record_type",
            "record_id",
            "actor_id",
            "authority_state",
            "analysis_target_ref",
            "procedure_ref",
            "independent_unit_definition_id",
            "authorized_key_columns",
            "input_path",
            "input_content_digest",
        },
    )
    actor_id = value.get("actor_id")
    if not _trimmed(actor_id) or not str(actor_id).startswith("scientist:"):
        raise DependenceAuthorizationLockError("dependence authority actor is invalid")
    if value.get("authority_state") != "authorized":
        raise DependenceAuthorizationLockError("dependence authority state is not authorized")
    if value.get("analysis_target_ref") != {
        "record_type": "analysis",
        "record_id": analysis["record_id"],
    }:
        raise DependenceAuthorizationLockError("dependence authority analysis ref is invalid")
    if value.get("procedure_ref") != {
        "record_type": "procedure",
        "record_id": procedure["record_id"],
    }:
        raise DependenceAuthorizationLockError("dependence authority procedure ref is invalid")
    if not _trimmed(value.get("independent_unit_definition_id")):
        raise DependenceAuthorizationLockError("dependence authority unit-definition id is invalid")
    columns = value.get("authorized_key_columns")
    if not (
        isinstance(columns, list)
        and 1 <= len(columns) <= 4
        and all(_trimmed(item) for item in columns)
        and len(columns) == len(set(columns))
    ):
        raise DependenceAuthorizationLockError(
            "dependence authority ordered key columns are invalid"
        )
    input_path = _relative_path(value.get("input_path"), "material input")
    digest = value.get("input_content_digest")
    if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
        raise DependenceAuthorizationLockError("dependence authority input digest is invalid")
    if material_input_digests is not None and material_input_digests.get(input_path) != digest:
        raise DependenceAuthorizationLockError(
            "dependence authority input path or digest is not frozen"
        )


def _verify_approval(approval: object, authorization: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(approval, dict) or set(approval) != {
        "actor_kind",
        "actor_id",
        "approved_projection_digest",
        "approved_at",
    }:
        raise DependenceAuthorizationLockError("dependence authority approval is not closed")
    if approval.get("actor_kind") != "human":
        raise DependenceAuthorizationLockError("dependence authority approval is not human")
    if approval.get("actor_id") != authorization.get("actor_id"):
        raise DependenceAuthorizationLockError("dependence authority approval actor mismatches")
    digest = approval.get("approved_projection_digest")
    if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
        raise DependenceAuthorizationLockError("dependence authority approval digest is invalid")
    approved_at = approval.get("approved_at")
    if not _trimmed(approved_at):
        raise DependenceAuthorizationLockError("dependence authority approval time is invalid")
    try:
        parsed = datetime.fromisoformat(str(approved_at).replace("Z", "+00:00"))
    except ValueError as error:
        raise DependenceAuthorizationLockError(
            "dependence authority approval time is invalid"
        ) from error
    if parsed.tzinfo is None:
        raise DependenceAuthorizationLockError("dependence authority approval time lacks a zone")
    return approval


def _require_record(
    record: object,
    record_type: str,
    keys: set[str],
) -> dict[str, Any]:
    if not isinstance(record, dict) or set(record) != keys:
        raise DependenceAuthorizationLockError(
            f"dependence authority {record_type} record is not closed"
        )
    if record.get("record_type") != record_type:
        raise DependenceAuthorizationLockError(
            f"dependence authority {record_type} record type is invalid"
        )
    record_id = record.get("record_id")
    if (
        not isinstance(record_id, str)
        or _RECORD_ID_RE.fullmatch(record_id) is None
        or not record_id.startswith(_RECORD_ID_PREFIX[record_type])
    ):
        raise DependenceAuthorizationLockError(
            f"dependence authority {record_type} record id is invalid"
        )
    return record


def _selected_report_path(context: FrozenInspectionContext) -> str | None:
    matches = [item for item in context.base_records if item.ref == context.selected_artifact_ref]
    if len(matches) != 1:
        return None
    try:
        payload = json.loads(matches[0].canonical_payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    path = payload.get("path")
    return path if isinstance(path, str) and _is_relative_path(path) else None


def _relative_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not _is_relative_path(value):
        raise DependenceAuthorizationLockError(f"dependence authority {label} path is invalid")
    return value


def _is_relative_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        bool(value) and not path.is_absolute() and "." not in path.parts and ".." not in path.parts
    )


def _trimmed(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip()


def _normalized_markers(markers: Iterable[str]) -> frozenset[str]:
    normalized: set[str] = set()
    for marker in markers:
        if not marker:
            continue
        lowered = marker.lower()
        normalized.add(lowered)
        normalized.add(lowered.replace("_", "-"))
        normalized.add(lowered.replace("-", "_"))
    return frozenset(normalized)


def _contains_marker(value: object, markers: frozenset[str]) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in markers)
    if isinstance(value, dict):
        return any(
            _contains_marker(key, markers) or _contains_marker(item, markers)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_marker(item, markers) for item in value)
    return False


def reverify_material_digest(content: bytes, expected_digest: str) -> bool:
    """Small explicit helper used by callers holding frozen material bytes."""

    return sha256_digest(content) == expected_digest
