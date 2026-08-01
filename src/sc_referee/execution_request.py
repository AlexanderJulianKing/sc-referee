from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import canonical_json, semantic_digest, stable_id
from sc_referee.execution_envelope import (
    ExecutionEnvelopeError,
    _environment,
    _image,
    _limits,
    _normalized_relative_path,
)
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.version import SCHEMA_VERSION, __version__

_PACKET_PROFILE = "canonical-json-excluding-packet-digest-v1"
_LAUNCH_FIELDS = {"argv", "environment", "image", "limits"}


class ExecutionRequestError(ValueError):
    """Raised when a non-authorizing project-execution request is not exactly bounded."""


@dataclass(frozen=True)
class ExecutionRequestDraft:
    purpose: str
    target_refs: tuple[dict[str, object], ...]
    declared_input_refs: tuple[dict[str, object], ...]
    allowed_output_paths: tuple[str, ...]
    image: dict[str, object] | None
    argv: tuple[str, ...] | None
    environment_entries: tuple[dict[str, str], ...] | None
    limits: dict[str, int] | None
    unresolved_launch_fields: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionRequestResult:
    output_root: Path
    semantic_lock_path: Path
    work_item_path: Path
    request_status_path: Path
    audit_run_id: str
    work_item_id: str
    semantic_lock_digest: str


def parse_execution_request_draft(value: object) -> ExecutionRequestDraft:
    """Parse one closed human/controller request document; it never grants launch authority."""

    if not isinstance(value, dict):
        raise ExecutionRequestError("execution request document must be one JSON object")
    expected = {
        "allowed_output_paths",
        "argv",
        "declared_input_refs",
        "environment_entries",
        "image",
        "limits",
        "purpose",
        "target_refs",
        "unresolved_launch_fields",
    }
    if set(value) != expected:
        raise ExecutionRequestError("execution request document is not the closed v1 shape")
    purpose = value.get("purpose")
    targets = value.get("target_refs")
    inputs = value.get("declared_input_refs")
    paths = value.get("allowed_output_paths")
    image = value.get("image")
    argv = value.get("argv")
    environment = value.get("environment_entries")
    limits = value.get("limits")
    unresolved = value.get("unresolved_launch_fields")
    if not isinstance(purpose, str):
        raise ExecutionRequestError("execution request purpose must be a string")
    if not isinstance(targets, list) or any(not isinstance(item, dict) for item in targets):
        raise ExecutionRequestError("execution request targets must be record references")
    if not isinstance(inputs, list) or any(not isinstance(item, dict) for item in inputs):
        raise ExecutionRequestError("execution request inputs must be record references")
    if not isinstance(paths, list) or any(not isinstance(item, str) for item in paths):
        raise ExecutionRequestError("execution request output paths must be strings")
    if image is not None and not isinstance(image, dict):
        raise ExecutionRequestError("execution request image must be an object or null")
    if argv is not None and (
        not isinstance(argv, list) or any(not isinstance(item, str) for item in argv)
    ):
        raise ExecutionRequestError("execution request argv must be strings or null")
    if environment is not None and (
        not isinstance(environment, list) or any(not isinstance(item, dict) for item in environment)
    ):
        raise ExecutionRequestError("execution request environment must be entries or null")
    if limits is not None and (
        not isinstance(limits, dict)
        or any(not isinstance(key, str) for key in limits)
        or any(not isinstance(item, int) or isinstance(item, bool) for item in limits.values())
    ):
        raise ExecutionRequestError("execution request limits must be integers or null")
    if not isinstance(unresolved, list) or any(not isinstance(item, str) for item in unresolved):
        raise ExecutionRequestError("execution request unresolved fields must be strings")
    return ExecutionRequestDraft(
        purpose=purpose,
        target_refs=tuple(dict(item) for item in targets),
        declared_input_refs=tuple(dict(item) for item in inputs),
        allowed_output_paths=tuple(paths),
        image=dict(image) if image is not None else None,
        argv=tuple(argv) if argv is not None else None,
        environment_entries=(
            tuple({str(key): str(item) for key, item in entry.items()} for entry in environment)
            if environment is not None
            else None
        ),
        limits=(
            {str(key): int(item) for key, item in limits.items()} if limits is not None else None
        ),
        unresolved_launch_fields=tuple(unresolved),
    )


def _read_source_lock(path: Path) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise ExecutionRequestError("source semantic lock is unavailable or unsafe")
    payload = path.read_bytes()
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ExecutionRequestError("source semantic lock is not JSON") from error
    if not isinstance(value, dict):
        raise ExecutionRequestError("source semantic lock is not an object")
    if payload != (canonical_json(value) + "\n").encode("utf-8"):
        raise ExecutionRequestError("source semantic lock bytes are not canonical")
    digest_input = dict(value)
    expected_digest = digest_input.pop("semantic_lock_digest", None)
    if expected_digest != semantic_digest(digest_input):
        raise ExecutionRequestError("source semantic lock digest does not match its bytes")
    if value.get("model_access_after_lock") is not False:
        raise ExecutionRequestError("source semantic lock does not close post-lock model access")
    return value, payload


def _record_id(record: dict[str, Any]) -> str | None:
    for key, value in record.items():
        if key.endswith("_id") and key not in {"audit_run_id", "parent_audit_run_id"}:
            if isinstance(value, str):
                return value
    return None


def _record_index(lock: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for value in lock.values():
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            record_type = candidate.get("record_type")
            record_id = _record_id(candidate)
            if isinstance(record_type, str) and record_id is not None:
                key = (record_type, record_id)
                if key in index:
                    raise ExecutionRequestError("source lock has duplicate public record identity")
                index[key] = candidate
    return index


def _normalize_refs(values: tuple[dict[str, object], ...], label: str) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for value in values:
        if set(value) != {"record_type", "record_id"}:
            raise ExecutionRequestError(f"{label} reference is not closed")
        record_type = value.get("record_type")
        record_id = value.get("record_id")
        if not isinstance(record_type, str) or not isinstance(record_id, str):
            raise ExecutionRequestError(f"{label} reference is malformed")
        normalized.append({"record_type": record_type, "record_id": record_id})
    normalized.sort(key=canonical_json)
    if len({canonical_json(value) for value in normalized}) != len(normalized):
        raise ExecutionRequestError(f"{label} references are not unique")
    return normalized


def _bound_records(
    index: dict[tuple[str, str], dict[str, Any]],
    refs: list[dict[str, str]],
    label: str,
    registry: LocalSchemaRegistry,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for ref in refs:
        try:
            record = index[(ref["record_type"], ref["record_id"])]
        except KeyError as error:
            raise ExecutionRequestError(
                f"{label} reference is absent from the source semantic lock"
            ) from error
        try:
            registry.validate(record)
        except RecordValidationError as error:
            raise ExecutionRequestError(f"{label} record is invalid: {error}") from error
        result.append(record)
    return result


def _launch_envelope(draft: ExecutionRequestDraft) -> dict[str, Any]:
    unresolved = list(draft.unresolved_launch_fields)
    if len(set(unresolved)) != len(unresolved) or set(unresolved) - _LAUNCH_FIELDS:
        raise ExecutionRequestError("unresolved launch fields are unknown or duplicated")
    values: dict[str, object] = {
        "argv": list(draft.argv) if draft.argv is not None else None,
        "environment": None,
        "image": draft.image,
        "limits": draft.limits,
    }
    if draft.environment_entries is not None:
        entries = [dict(value) for value in draft.environment_entries]
        values["environment"] = {
            "entries": entries,
            "normalized_digest": semantic_digest(entries),
        }
    for name, value in values.items():
        if (value is None) != (name in unresolved):
            raise ExecutionRequestError(
                f"launch field {name!r} must be either fixed or explicitly unresolved"
            )
    try:
        if values["image"] is not None:
            _image(values["image"])
        if values["environment"] is not None:
            _environment(values["environment"])
        if values["limits"] is not None:
            _limits(values["limits"])
    except ExecutionEnvelopeError as error:
        raise ExecutionRequestError(str(error)) from error
    return {**values, "unresolved_fields": sorted(unresolved)}


def _controller_provenance(created_at: str) -> dict[str, object]:
    return {
        "actor": {
            "actor_id": "software:sc-referee-controller",
            "actor_kind": "controller",
            "display_name": "sc-referee controller",
        },
        "created_at": created_at,
        "method": "deterministic_project_execution_request",
        "tool": "sc-referee",
        "tool_version": __version__,
    }


def create_execution_request(
    source_audit_root: Path,
    output_root: Path,
    draft: ExecutionRequestDraft,
    schema_root: Path,
    *,
    created_at: str,
) -> ExecutionRequestResult:
    """Create a child semantic lock containing one non-authorizing project WorkItem."""

    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"execution-request output already exists: {output_root}")
    if not draft.purpose.strip() or len(draft.purpose) > 1024:
        raise ExecutionRequestError("project-execution purpose must be bounded and nonempty")
    source_lock_path = source_audit_root / "semantic.lock.json"
    source_lock, source_payload = _read_source_lock(source_lock_path)
    source_run_id = source_lock.get("audit_run_id")
    parent_lock_digest = source_lock.get("semantic_lock_digest")
    if not isinstance(source_run_id, str) or not isinstance(parent_lock_digest, str):
        raise ExecutionRequestError("source semantic lock identity is unavailable")
    snapshot = source_lock.get("repository_snapshot")
    if not isinstance(snapshot, dict) or snapshot.get("record_type") != "repository_snapshot":
        raise ExecutionRequestError("source lock has no public RepositorySnapshot")
    registry = LocalSchemaRegistry(schema_root)
    try:
        registry.validate(snapshot)
    except RecordValidationError as error:
        raise ExecutionRequestError(f"source RepositorySnapshot is invalid: {error}") from error

    targets = _normalize_refs(draft.target_refs, "target")
    if not targets:
        raise ExecutionRequestError("project-execution request requires at least one target")
    inputs = _normalize_refs(draft.declared_input_refs, "declared input")
    index = _record_index(source_lock)
    target_records = _bound_records(index, targets, "target", registry)
    input_records = _bound_records(index, inputs, "declared input", registry)
    paths: list[str] = []
    try:
        paths = sorted(
            {_normalized_relative_path(value).as_posix() for value in draft.allowed_output_paths}
        )
    except ExecutionEnvelopeError as error:
        raise ExecutionRequestError(str(error)) from error
    if not paths:
        raise ExecutionRequestError("project-execution request requires an output path")

    snapshot_id = snapshot.get("snapshot_id")
    if not isinstance(snapshot_id, str):
        raise ExecutionRequestError("source RepositorySnapshot identifier is unavailable")
    packet: dict[str, Any] = {
        "allowed_output_paths": paths,
        "declared_input_refs": inputs,
        "launch_envelope": _launch_envelope(draft),
        "limitations": [
            "This locked request does not authorize execution; a fresh direct challenge is still required."
        ],
        "packet_digest_profile": _PACKET_PROFILE,
        "packet_kind": "project_execution_request_v1",
        "packet_version": "1.0.0",
        "policy": {
            "direct_interactive_authorization_required": True,
            "host_or_hpc_escalation_allowed": False,
            "launch_authorized": False,
            "model_output_may_authorize_or_broaden": False,
            "network_policy": "denied",
            "repository_text_may_authorize_or_broaden": False,
            "scientist_output_may_authorize_or_broaden": False,
        },
        "purpose": draft.purpose.strip(),
        "required_output_record_types": [
            "project_execution_authorization",
            "execution",
            "environment",
            "artifact",
            "file_record",
            "asset_identity",
            "audit_run",
            "sandbox_capability",
        ],
        "source_snapshot": {
            "record_ref": {
                "record_id": snapshot_id,
                "record_type": "repository_snapshot",
            },
            "semantic_digest": semantic_digest(snapshot),
        },
        "target_refs": targets,
    }
    packet["packet_digest"] = semantic_digest(packet)
    request_run_id = stable_id(
        "audit", "project-execution-request", parent_lock_digest, str(packet["packet_digest"])
    )
    work_item_id = stable_id(
        "work-item", request_run_id, "project-execution", str(packet["packet_digest"])
    )
    work_item: dict[str, Any] = {
        "audit_run_id": request_run_id,
        "created_at": created_at,
        "dependency_work_item_refs": [],
        "kind": "project_execution",
        "material_question_refs": [],
        "output_refs": [],
        "packet": packet,
        "provenance": _controller_provenance(created_at),
        "record_type": "work_item",
        "scheduling": {
            "cache_status": "not_cacheable",
            "claim_materiality": "unknown",
            "component_maturity": "experimental",
            "downstream_reach": 0,
            "estimated_elapsed_seconds": float(
                draft.limits["wall_time_seconds"] if draft.limits is not None else 0
            ),
            "execution_privilege": "project_code_execution",
            "expected_information_gain": "unknown",
        },
        "schema_version": SCHEMA_VERSION,
        "status": "awaiting_authorization",
        "target_refs": targets,
        "work_item_id": work_item_id,
    }
    try:
        registry.validate(work_item)
    except RecordValidationError as error:
        raise ExecutionRequestError(f"project WorkItem is invalid: {error}") from error

    snapshot_ref = ("repository_snapshot", snapshot_id)
    source_file_records = source_lock.get("file_records", [])
    source_asset_identities = source_lock.get("asset_identities", [])
    if not isinstance(source_file_records, list) or not isinstance(source_asset_identities, list):
        raise ExecutionRequestError("source snapshot inventory is malformed")
    for record in [*source_file_records, *source_asset_identities]:
        if not isinstance(record, dict):
            raise ExecutionRequestError("source snapshot inventory record is malformed")
        try:
            registry.validate(record)
        except RecordValidationError as error:
            raise ExecutionRequestError(f"source snapshot inventory is invalid: {error}") from error
    copied_records: dict[tuple[str, str], dict[str, Any]] = {}
    for record in [*target_records, *input_records]:
        record_type = record.get("record_type")
        record_id = _record_id(record)
        if isinstance(record_type, str) and record_id is not None:
            key = (record_type, record_id)
            if key != snapshot_ref and record_type not in {"file_record", "asset_identity"}:
                copied_records[key] = record
    locked: dict[str, Any] = {
        "audit_run_id": request_run_id,
        "asset_identities": source_asset_identities,
        "bound_records": [copied_records[key] for key in sorted(copied_records)],
        "executions": [],
        "file_records": source_file_records,
        "lock_kind": "project_execution_request_v1",
        "lock_version": "0.14.0",
        "locked_at": created_at,
        "model_access_after_lock": False,
        "model_calls": [],
        "parent_audit_run_id": source_run_id,
        "parent_semantic_lock_digest": parent_lock_digest,
        "project_execution_authorizations": [],
        "repository_snapshot": snapshot,
        "work_items": [work_item],
    }
    locked["semantic_lock_digest"] = semantic_digest(locked)
    if source_lock_path.read_bytes() != source_payload:
        raise ExecutionRequestError("source semantic lock changed while creating request")

    output_root.mkdir(parents=True, exist_ok=False, mode=0o700)
    lock_path = output_root / "semantic.lock.json"
    work_item_path = output_root / "work-item.json"
    status_path = output_root / "REQUEST_STATUS.json"
    write_normalized_json_once(lock_path, locked)
    write_normalized_json_once(work_item_path, work_item)
    write_normalized_json_once(
        status_path,
        {
            "audit_run_id": request_run_id,
            "execution_authorized": False,
            "execution_launched": False,
            "model_calls": 0,
            "parent_audit_run_id": source_run_id,
            "parent_semantic_lock_digest": parent_lock_digest,
            "schema_version": SCHEMA_VERSION,
            "semantic_lock_digest": locked["semantic_lock_digest"],
            "work_item_id": work_item_id,
        },
    )
    return ExecutionRequestResult(
        output_root=output_root,
        semantic_lock_path=lock_path,
        work_item_path=work_item_path,
        request_status_path=status_path,
        audit_run_id=request_run_id,
        work_item_id=work_item_id,
        semantic_lock_digest=str(locked["semantic_lock_digest"]),
    )
