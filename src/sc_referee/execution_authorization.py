from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.execution_envelope import (
    ExecutionEnvelopeError,
    _command,
    _environment,
    _image,
    _limits,
    _normalized_relative_path,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.storage.atomic import atomic_create_bytes, fsync_directory
from sc_referee.version import SCHEMA_VERSION, __version__

_REGISTRY_PROFILE = "single-use-project-execution-authorization-registry-v1"
_RECEIPT_PROFILE = "single-use-project-execution-consumption-v1"
_TOKEN = re.compile(r"^[A-Za-z0-9._:-]{16,256}$")


class AuthorizationError(ValueError):
    """Raised before project execution when user presence or an exact binding is absent."""


class InteractiveTerminal(Protocol):
    def isatty(self) -> bool: ...

    def write(self, value: str) -> int: ...

    def flush(self) -> None: ...

    def readline(self) -> str: ...


@dataclass(frozen=True)
class AuthorizationDraft:
    """Non-authorizing launch material prepared before the direct user-presence transition."""

    linked_output_root: Path
    source_semantic_lock_path: Path
    linked_audit_run_id: str
    work_item_id: str
    capability_record: dict[str, object]
    image_reference: str
    argv: tuple[str, ...]
    declared_input_refs: tuple[dict[str, object], ...]
    allowed_output_paths: tuple[str, ...]
    environment: tuple[tuple[str, str], ...]
    wall_time_seconds: int
    cpu_quota_millis: int
    memory_bytes: int
    process_count: int
    open_files: int
    writable_bytes: int
    expires_at: str
    actor_id: str
    actor_display_name: str


@dataclass(frozen=True)
class InteractiveAuthorizationResult:
    linked_output_root: Path
    registry_root: Path
    authorization_path: Path
    registry_entry_path: Path
    source_semantic_lock_path: Path
    consumption_receipt_path: Path
    authorization: dict[str, Any]


@dataclass(frozen=True)
class ClaimBindings:
    source_semantic_lock_digest: str
    linked_audit_run_id: str
    work_item_id: str
    work_item_semantic_digest: str
    snapshot_semantic_digest: str
    capability_semantic_digest: str
    image_manifest_digest: str
    command_digest: str
    environment_digest: str
    allowed_output_paths: tuple[str, ...]
    linked_output_root: Path


@dataclass(frozen=True)
class _VerifiedWorkItemAdmission:
    source_lock_payload: bytes
    source_audit_run_id: str
    source_semantic_lock_digest: str
    work_item: dict[str, Any]
    work_item_semantic_digest: str
    snapshot_record: dict[str, Any]
    purpose: str
    target_refs: tuple[dict[str, str], ...]
    declared_input_refs: tuple[dict[str, str], ...]
    allowed_output_paths: tuple[str, ...]


def prepare_authorization_draft(
    request_audit_root: Path,
    work_item_id: str,
    capability_path: Path,
    launch_value: object,
    linked_output_root: Path,
    linked_audit_run_id: str,
    *,
    expires_at: str,
    actor_id: str,
    actor_display_name: str,
) -> AuthorizationDraft:
    """Prepare non-authorizing launch material from one locked request and closed JSON input."""

    if not isinstance(launch_value, dict):
        raise AuthorizationError("authorization launch document must be one JSON object")
    expected = {"argv", "environment_entries", "image_reference", "limits"}
    if set(launch_value) != expected:
        raise AuthorizationError("authorization launch document is not the closed v1 shape")
    argv = launch_value.get("argv")
    environment = launch_value.get("environment_entries")
    image_reference = launch_value.get("image_reference")
    limits = launch_value.get("limits")
    if not isinstance(argv, list) or any(not isinstance(value, str) for value in argv):
        raise AuthorizationError("authorization argv must be an array of strings")
    if not isinstance(environment, list):
        raise AuthorizationError("authorization environment must be an array")
    environment_pairs: list[tuple[str, str]] = []
    for entry in environment:
        if not isinstance(entry, dict) or set(entry) != {"name", "value"}:
            raise AuthorizationError("authorization environment entry is not closed")
        name = entry.get("name")
        value = entry.get("value")
        if not isinstance(name, str) or not isinstance(value, str):
            raise AuthorizationError("authorization environment entry is malformed")
        environment_pairs.append((name, value))
    if not isinstance(image_reference, str):
        raise AuthorizationError("authorization image reference must be a string")
    limit_names = {
        "cpu_quota_millis",
        "memory_bytes",
        "open_files",
        "process_count",
        "wall_time_seconds",
        "writable_bytes",
    }
    if (
        not isinstance(limits, dict)
        or set(limits) != limit_names
        or any(not isinstance(value, int) or isinstance(value, bool) for value in limits.values())
    ):
        raise AuthorizationError("authorization limits are not the closed integer profile")
    lock, _payload = _read_canonical_object(
        request_audit_root / "semantic.lock.json", "source semantic lock"
    )
    work_items = lock.get("work_items")
    matches = (
        [
            item
            for item in work_items
            if isinstance(item, dict) and item.get("work_item_id") == work_item_id
        ]
        if isinstance(work_items, list)
        else []
    )
    if len(matches) != 1 or not isinstance(matches[0].get("packet"), dict):
        raise AuthorizationError("exact locked project WorkItem is unavailable")
    packet = matches[0]["packet"]
    inputs = packet.get("declared_input_refs")
    paths = packet.get("allowed_output_paths")
    if not isinstance(inputs, list) or not isinstance(paths, list):
        raise AuthorizationError("locked WorkItem scope is malformed")
    capability, _capability_payload = _read_canonical_object(capability_path, "sandbox capability")
    return AuthorizationDraft(
        linked_output_root=linked_output_root,
        source_semantic_lock_path=request_audit_root / "semantic.lock.json",
        linked_audit_run_id=linked_audit_run_id,
        work_item_id=work_item_id,
        capability_record=capability,
        image_reference=image_reference,
        argv=tuple(argv),
        declared_input_refs=tuple(dict(value) for value in inputs),
        allowed_output_paths=tuple(str(value) for value in paths),
        environment=tuple(environment_pairs),
        wall_time_seconds=int(limits["wall_time_seconds"]),
        cpu_quota_millis=int(limits["cpu_quota_millis"]),
        memory_bytes=int(limits["memory_bytes"]),
        process_count=int(limits["process_count"]),
        open_files=int(limits["open_files"]),
        writable_bytes=int(limits["writable_bytes"]),
        expires_at=expires_at,
        actor_id=actor_id,
        actor_display_name=actor_display_name,
    )


def _timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise AuthorizationError(f"{label} timestamp is invalid") from error
    if parsed.tzinfo is None:
        raise AuthorizationError(f"{label} timestamp requires a timezone")
    return parsed


def _token(value: str, label: str) -> str:
    if not _TOKEN.fullmatch(value):
        raise AuthorizationError(f"fresh {label} has an invalid controller token shape")
    return value


def _typed_ref(record_type: str, record_id: object) -> dict[str, str]:
    if not isinstance(record_id, str) or not record_id:
        raise AuthorizationError(f"{record_type} identifier is unavailable")
    return {"record_type": record_type, "record_id": record_id}


def _normalized_refs(values: tuple[dict[str, object], ...]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for value in values:
        if set(value) != {"record_type", "record_id"}:
            raise AuthorizationError("declared input reference is not closed")
        record_type = value.get("record_type")
        record_id = value.get("record_id")
        if not isinstance(record_type, str) or not isinstance(record_id, str):
            raise AuthorizationError("declared input reference is malformed")
        result.append({"record_type": record_type, "record_id": record_id})
    normalized = sorted(result, key=canonical_json)
    if len({canonical_json(value) for value in normalized}) != len(normalized):
        raise AuthorizationError("declared input references are not unique")
    return normalized


def _normalized_public_refs(values: object, label: str) -> list[dict[str, str]]:
    if not isinstance(values, list):
        raise AuthorizationError(f"WorkItem {label} references are malformed")
    return _normalized_refs(tuple(values))


def _record_identifier(record: dict[str, Any]) -> str | None:
    for key, value in record.items():
        if key.endswith("_id") and key not in {"audit_run_id", "parent_audit_run_id"}:
            if isinstance(value, str):
                return value
    return None


def _source_lock_record_index(lock: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for value in lock.values():
        candidates: list[object]
        if isinstance(value, list):
            candidates = value
        else:
            candidates = [value]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            record_type = candidate.get("record_type")
            record_id = _record_identifier(candidate)
            if isinstance(record_type, str) and record_id is not None:
                key = (record_type, record_id)
                if key in index:
                    raise AuthorizationError("source semantic lock has duplicate public records")
                index[key] = candidate
    return index


def _bound_record(
    index: dict[tuple[str, str], dict[str, Any]], ref: dict[str, str], label: str
) -> dict[str, Any]:
    try:
        return index[(ref["record_type"], ref["record_id"])]
    except KeyError as error:
        raise AuthorizationError(
            f"WorkItem {label} reference is absent from the source lock"
        ) from error


def _limits_projection(draft: AuthorizationDraft) -> dict[str, int]:
    return {
        "cpu_quota_millis": draft.cpu_quota_millis,
        "memory_bytes": draft.memory_bytes,
        "open_files": draft.open_files,
        "process_count": draft.process_count,
        "wall_time_seconds": draft.wall_time_seconds,
        "writable_bytes": draft.writable_bytes,
    }


def _verify_launch_scope(draft: AuthorizationDraft, packet: dict[str, Any]) -> None:
    requested_inputs = _normalized_public_refs(packet.get("declared_input_refs"), "declared input")
    if _normalized_refs(draft.declared_input_refs) != requested_inputs:
        raise AuthorizationError("authorization broadens or changes WorkItem declared inputs")
    requested_paths = sorted(
        {
            _normalized_relative_path(str(value)).as_posix()
            for value in packet["allowed_output_paths"]
        }
    )
    authorized_paths = sorted(
        {_normalized_relative_path(value).as_posix() for value in draft.allowed_output_paths}
    )
    if requested_paths != authorized_paths:
        raise AuthorizationError("authorization broadens or changes WorkItem output paths")

    launch = packet.get("launch_envelope")
    if not isinstance(launch, dict):
        raise AuthorizationError("WorkItem launch envelope is malformed")
    unresolved = launch.get("unresolved_fields")
    if not isinstance(unresolved, list) or any(not isinstance(value, str) for value in unresolved):
        raise AuthorizationError("WorkItem unresolved launch fields are malformed")
    unresolved_names = set(unresolved)

    proposed_argv = launch.get("argv")
    if proposed_argv is not None and list(draft.argv) != proposed_argv:
        raise AuthorizationError("authorization broadens or changes WorkItem argv")
    if proposed_argv is None and "argv" not in unresolved_names:
        raise AuthorizationError("WorkItem argv is neither fixed nor explicitly unresolved")

    proposed_image = launch.get("image")
    if proposed_image is not None:
        try:
            proposed_reference = _image(proposed_image)
        except ExecutionEnvelopeError as error:
            raise AuthorizationError(f"WorkItem image is invalid: {error}") from error
        if draft.image_reference != proposed_reference:
            raise AuthorizationError("authorization broadens or changes WorkItem image")
    elif "image" not in unresolved_names:
        raise AuthorizationError("WorkItem image is neither fixed nor explicitly unresolved")

    proposed_environment = launch.get("environment")
    authorized_entries = tuple(sorted(draft.environment))
    if proposed_environment is not None:
        try:
            proposed_entries = _environment(proposed_environment)
        except ExecutionEnvelopeError as error:
            raise AuthorizationError(f"WorkItem environment is invalid: {error}") from error
        if not set(authorized_entries).issubset(set(proposed_entries)):
            raise AuthorizationError("authorization broadens or changes WorkItem environment")
    elif "environment" not in unresolved_names:
        raise AuthorizationError("WorkItem environment is neither fixed nor explicitly unresolved")

    proposed_limits = launch.get("limits")
    authorized_limits = _limits_projection(draft)
    if proposed_limits is not None:
        if not isinstance(proposed_limits, dict) or set(proposed_limits) != set(authorized_limits):
            raise AuthorizationError("WorkItem limits are malformed")
        for name, value in authorized_limits.items():
            proposed = proposed_limits.get(name)
            if (
                not isinstance(proposed, int)
                or isinstance(proposed, bool)
                or proposed <= 0
                or value <= 0
                or value > proposed
            ):
                raise AuthorizationError("authorization broadens WorkItem resource limits")
    elif "limits" not in unresolved_names:
        raise AuthorizationError("WorkItem limits are neither fixed nor explicitly unresolved")


def _verify_source_work_item(
    draft: AuthorizationDraft, schema_root: Path
) -> _VerifiedWorkItemAdmission:
    lock, payload = _read_canonical_object(draft.source_semantic_lock_path, "source semantic lock")
    expected_digest = lock.get("semantic_lock_digest")
    digest_input = dict(lock)
    digest_input.pop("semantic_lock_digest", None)
    if expected_digest != semantic_digest(digest_input):
        raise AuthorizationError("source semantic lock digest does not match its bytes")
    source_audit_run_id = lock.get("audit_run_id")
    if not isinstance(source_audit_run_id, str) or not source_audit_run_id:
        raise AuthorizationError("source semantic lock audit run is unavailable")
    if lock.get("model_access_after_lock") is not False:
        raise AuthorizationError("source semantic lock does not close post-lock model access")
    work_items = lock.get("work_items")
    if not isinstance(work_items, list):
        raise AuthorizationError("source semantic lock has no WorkItem collection")
    matches = [
        value
        for value in work_items
        if isinstance(value, dict) and value.get("work_item_id") == draft.work_item_id
    ]
    if len(matches) != 1:
        raise AuthorizationError("exact WorkItem is absent or duplicated in source semantic lock")
    work_item = matches[0]
    try:
        LocalSchemaRegistry(schema_root).validate(work_item)
    except RecordValidationError as error:
        raise AuthorizationError(
            f"WorkItem is not valid under the active schema: {error}"
        ) from error
    scheduling = work_item.get("scheduling")
    packet = work_item.get("packet")
    if (
        work_item.get("audit_run_id") != source_audit_run_id
        or work_item.get("kind") != "project_execution"
        or work_item.get("status") != "awaiting_authorization"
        or not isinstance(scheduling, dict)
        or scheduling.get("execution_privilege") != "project_code_execution"
        or not isinstance(packet, dict)
        or packet.get("packet_kind") != "project_execution_request_v1"
    ):
        raise AuthorizationError("WorkItem is not an awaiting project-execution request")
    packet_digest = packet.get("packet_digest")
    digest_packet = dict(packet)
    digest_packet.pop("packet_digest", None)
    if packet_digest != semantic_digest(digest_packet):
        raise AuthorizationError("WorkItem packet digest does not match its meaning")
    policy = packet.get("policy")
    expected_policy = {
        "direct_interactive_authorization_required": True,
        "host_or_hpc_escalation_allowed": False,
        "launch_authorized": False,
        "model_output_may_authorize_or_broaden": False,
        "network_policy": "denied",
        "repository_text_may_authorize_or_broaden": False,
        "scientist_output_may_authorize_or_broaden": False,
    }
    if policy != expected_policy:
        raise AuthorizationError("WorkItem policy is not the closed non-authorizing profile")

    top_targets = _normalized_public_refs(work_item.get("target_refs"), "target")
    packet_targets = _normalized_public_refs(packet.get("target_refs"), "packet target")
    if top_targets != packet_targets:
        raise AuthorizationError("WorkItem target projections disagree")
    inputs = _normalized_public_refs(packet.get("declared_input_refs"), "declared input")
    index = _source_lock_record_index(lock)
    registry = LocalSchemaRegistry(schema_root)
    for ref in [*top_targets, *inputs]:
        record = _bound_record(index, ref, "target or input")
        try:
            registry.validate(record)
        except RecordValidationError as error:
            raise AuthorizationError(f"WorkItem referenced record is invalid: {error}") from error
    source_snapshot = packet.get("source_snapshot")
    if not isinstance(source_snapshot, dict) or not isinstance(
        source_snapshot.get("record_ref"), dict
    ):
        raise AuthorizationError("WorkItem source snapshot binding is malformed")
    snapshot_ref = source_snapshot["record_ref"]
    if set(snapshot_ref) != {"record_type", "record_id"}:
        raise AuthorizationError("WorkItem source snapshot reference is not closed")
    snapshot_record = _bound_record(index, snapshot_ref, "source snapshot")
    snapshot_run_id = snapshot_record.get("audit_run_id")
    parent_audit_run_id = lock.get("parent_audit_run_id")
    snapshot_run_is_bound = snapshot_run_id == source_audit_run_id or (
        isinstance(parent_audit_run_id, str)
        and parent_audit_run_id == snapshot_run_id
        and isinstance(lock.get("parent_semantic_lock_digest"), str)
    )
    if (
        snapshot_record.get("record_type") != "repository_snapshot"
        or not snapshot_run_is_bound
        or snapshot_record.get("immutability") is not True
        or source_snapshot.get("semantic_digest") != semantic_digest(snapshot_record)
    ):
        raise AuthorizationError(
            "WorkItem source snapshot binding does not match the locked snapshot"
        )
    purpose = packet.get("purpose")
    if not isinstance(purpose, str) or not purpose:
        raise AuthorizationError("WorkItem purpose is unavailable")
    _verify_launch_scope(draft, packet)
    paths = tuple(
        sorted(
            {
                _normalized_relative_path(str(value)).as_posix()
                for value in packet["allowed_output_paths"]
            }
        )
    )
    return _VerifiedWorkItemAdmission(
        source_lock_payload=payload,
        source_audit_run_id=source_audit_run_id,
        source_semantic_lock_digest=str(expected_digest),
        work_item=work_item,
        work_item_semantic_digest=semantic_digest(work_item),
        snapshot_record=snapshot_record,
        purpose=purpose,
        target_refs=tuple(top_targets),
        declared_input_refs=tuple(inputs),
        allowed_output_paths=paths,
    )


def _create_bound_registry(linked_output_root: Path, nonce: str) -> tuple[Path, dict[str, object]]:
    if linked_output_root.exists() or linked_output_root.is_symlink():
        raise FileExistsError(f"linked output root already exists: {linked_output_root}")
    linked_output_root.mkdir(parents=True, exist_ok=False, mode=0o700)
    os.chmod(linked_output_root, 0o700)
    control_root = linked_output_root / "control"
    control_root.mkdir(mode=0o700)
    registry_root = control_root / "authorization-registry"
    registry_root.mkdir(mode=0o700)
    registry_stat = registry_root.stat(follow_symlinks=False)
    output_stat = linked_output_root.stat(follow_symlinks=False)
    real_output = linked_output_root.resolve()
    real_registry = registry_root.resolve()
    identity: dict[str, object] = {
        "linked_output_root_device": output_stat.st_dev,
        "linked_output_root_id": stable_id(
            "output-root", str(real_output), str(output_stat.st_dev), str(output_stat.st_ino), nonce
        ),
        "linked_output_root_inode": output_stat.st_ino,
        "linked_output_root_path": str(real_output),
        "registry_device": registry_stat.st_dev,
        "registry_id": stable_id(
            "authorization-registry",
            str(real_registry),
            str(registry_stat.st_dev),
            str(registry_stat.st_ino),
            nonce,
        ),
        "registry_inode": registry_stat.st_ino,
        "registry_path": str(real_registry),
    }
    return registry_root, identity


def _build_authorization(
    draft: AuthorizationDraft,
    admission: _VerifiedWorkItemAdmission,
    registry_identity: dict[str, object],
    nonce: str,
    confirmed_at: str,
) -> dict[str, Any]:
    if draft.capability_record.get("record_type") != "sandbox_capability":
        raise AuthorizationError("authorization requires a SandboxCapability")
    if (
        draft.capability_record.get("project_code_execution_supported") is not True
        or draft.capability_record.get("rootless_verified") is not True
        or draft.capability_record.get("capability_evidence_status") != "complete_effective_probe"
    ):
        raise AuthorizationError("sandbox capability is not eligible for project execution")
    if _timestamp(draft.expires_at, "authorization expiry") <= _timestamp(
        confirmed_at, "authorization confirmation"
    ):
        raise AuthorizationError("authorization expiry must follow confirmation")

    allowed_paths = sorted(
        {_normalized_relative_path(value).as_posix() for value in draft.allowed_output_paths}
    )
    if not allowed_paths:
        raise AuthorizationError("authorization requires at least one allowed output path")
    environment_entries = [
        {"name": name, "value": value} for name, value in sorted(draft.environment)
    ]
    normalized_environment = {
        "entries": environment_entries,
        "normalized_digest": semantic_digest(environment_entries),
    }
    # Reuse the executor's closed environment policy before presenting any challenge.
    _environment(normalized_environment)
    command = {"argv": list(draft.argv), "normalized_digest": semantic_digest(list(draft.argv))}
    try:
        _command(command)
        _limits(_limits_projection(draft))
    except ExecutionEnvelopeError as error:
        raise AuthorizationError(str(error)) from error
    image = {
        "manifest_digest": draft.image_reference.rsplit("@", maxsplit=1)[-1],
        "reference": draft.image_reference,
    }
    try:
        _image(image)
    except ExecutionEnvelopeError as error:
        raise AuthorizationError(str(error)) from error
    inputs = _normalized_refs(draft.declared_input_refs)
    snapshot_id = admission.snapshot_record.get("snapshot_id")
    capability_id = draft.capability_record.get("sandbox_capability_id")
    capability_digest = semantic_digest(draft.capability_record)
    snapshot_digest = semantic_digest(admission.snapshot_record)
    authorization_id = stable_id(
        "authorization",
        nonce,
        admission.source_audit_run_id,
        admission.source_semantic_lock_digest,
        draft.linked_audit_run_id,
        draft.work_item_id,
        admission.work_item_semantic_digest,
        snapshot_digest,
        capability_digest,
        str(command["normalized_digest"]),
        str(normalized_environment["normalized_digest"]),
        canonical_json(allowed_paths),
    )
    actor = {
        "actor_id": draft.actor_id,
        "actor_kind": "human",
        "display_name": draft.actor_display_name,
    }
    return {
        "acknowledgements": {
            "network_denied": True,
            "no_host_or_hpc_escalation": True,
            "output_confined_to_audit_root": True,
            "project_code_is_untrusted": True,
            "project_code_will_execute": True,
        },
        "authorization_id": authorization_id,
        "authorizing_actor": actor,
        "command": command,
        "environment": normalized_environment,
        "expires_at": draft.expires_at,
        "identity_assurance": "declared_local_user",
        "image": image,
        "limitations": [
            "Local actor identity is declared and is not externally authenticated.",
            "This record is portable evidence; launch additionally requires its original unconsumed controller registry entry.",
        ],
        "limits": {
            "cpu_quota_millis": draft.cpu_quota_millis,
            "memory_bytes": draft.memory_bytes,
            "open_files": draft.open_files,
            "process_count": draft.process_count,
            "wall_time_seconds": draft.wall_time_seconds,
            "writable_bytes": draft.writable_bytes,
        },
        "network_policy": "denied",
        "provenance": {
            "actor": actor,
            "created_at": confirmed_at,
            "method": "interactive_fresh_challenge_authorization",
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "record_type": "project_execution_authorization",
        "registry_binding": {
            "linked_output_root_id": registry_identity["linked_output_root_id"],
            "registry_id": registry_identity["registry_id"],
        },
        "schema_version": SCHEMA_VERSION,
        "scope": {
            "allowed_output_paths": allowed_paths,
            "capability": {
                "record_ref": _typed_ref("sandbox_capability", capability_id),
                "semantic_digest": capability_digest,
            },
            "declared_input_refs": inputs,
            "linked_audit_run_ref": _typed_ref("audit_run", draft.linked_audit_run_id),
            "snapshot": {
                "record_ref": _typed_ref("repository_snapshot", snapshot_id),
                "semantic_digest": snapshot_digest,
            },
            "purpose": admission.purpose,
            "source_audit_run_ref": _typed_ref("audit_run", admission.source_audit_run_id),
            "source_semantic_lock_digest": admission.source_semantic_lock_digest,
            "target_refs": list(admission.target_refs),
            "work_item_binding_status": "complete_project_execution_work_item",
            "work_item_ref": _typed_ref("work_item", draft.work_item_id),
            "work_item_semantic_digest": admission.work_item_semantic_digest,
        },
        "single_use_nonce": nonce,
    }


def authorize_execution_draft(
    draft: AuthorizationDraft,
    schema_root: Path,
    *,
    terminal_input: InteractiveTerminal,
    terminal_output: InteractiveTerminal,
    confirmed_at: str,
    nonce_factory: Any,
    challenge_factory: Any,
) -> InteractiveAuthorizationResult:
    """Perform the fresh attached-terminal transition and create one private registry entry.

    This internal primitive accepts only a non-authorizing draft, constructs the public record,
    and has no CLI exposure until the WorkItem admission contract is resolved by ADR-0014.
    """

    if not terminal_input.isatty() or not terminal_output.isatty():
        raise AuthorizationError("authorization requires attached interactive input and output")
    admission = _verify_source_work_item(draft, schema_root)
    nonce = _token(str(nonce_factory()), "authorization nonce")
    challenge = _token(str(challenge_factory()), "challenge")
    registry_root, registry_identity = _create_bound_registry(draft.linked_output_root, nonce)
    authorization = _build_authorization(draft, admission, registry_identity, nonce, confirmed_at)
    LocalSchemaRegistry(schema_root).validate(authorization)
    envelope_digest = semantic_digest(authorization)
    display = {
        "authorization_envelope": authorization,
        "authorization_semantic_digest": envelope_digest,
        "fresh_challenge": challenge,
        "notice": (
            "Project-authored code is untrusted and will execute once with network denied in the "
            "displayed rootless-OCI envelope. Type the fresh challenge exactly to authorize."
        ),
    }
    if draft.source_semantic_lock_path.read_bytes() != admission.source_lock_payload:
        raise AuthorizationError("source semantic lock changed before authorization challenge")
    terminal_output.write(canonical_json(display) + "\nChallenge: ")
    terminal_output.flush()
    response = terminal_input.readline().rstrip("\r\n")
    if response != challenge:
        raise AuthorizationError("fresh authorization challenge did not match")
    if draft.source_semantic_lock_path.read_bytes() != admission.source_lock_payload:
        raise AuthorizationError("source semantic lock changed during authorization challenge")

    authorization_path = registry_root / "authorization.json"
    entry_path = registry_root / "entry.json"
    registered_source_lock_path = registry_root / "source-semantic.lock.json"
    receipt_path = registry_root / "consumption-receipt.json"
    authorization_payload = (canonical_json(authorization) + "\n").encode("utf-8")
    entry = {
        "authorization_digest": sha256_digest(authorization_payload),
        "authorization_id": authorization["authorization_id"],
        "authorization_semantic_digest": envelope_digest,
        "authorization_path": authorization_path.name,
        "challenge_digest": sha256_digest(challenge),
        "confirmed_at": confirmed_at,
        "controller": {"tool": "sc-referee", "tool_version": __version__},
        "identity": registry_identity,
        "nonce_digest": sha256_digest(nonce),
        "profile": _REGISTRY_PROFILE,
        "source_semantic_lock_bytes_digest": sha256_digest(admission.source_lock_payload),
        "source_semantic_lock_digest": admission.source_semantic_lock_digest,
        "source_semantic_lock_path": registered_source_lock_path.name,
        "state": "unconsumed",
    }
    atomic_create_bytes(authorization_path, authorization_payload)
    atomic_create_bytes(registered_source_lock_path, admission.source_lock_payload)
    atomic_create_bytes(entry_path, (canonical_json(entry) + "\n").encode("utf-8"))
    fsync_directory(registry_root)
    return InteractiveAuthorizationResult(
        draft.linked_output_root,
        registry_root,
        authorization_path,
        entry_path,
        registered_source_lock_path,
        receipt_path,
        authorization,
    )


def _read_canonical_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise AuthorizationError(f"{label} is unavailable or unsafe")
    payload = path.read_bytes()
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise AuthorizationError(f"{label} is not JSON") from error
    if not isinstance(value, dict):
        raise AuthorizationError(f"{label} is not an object")
    if payload != (canonical_json(value) + "\n").encode("utf-8"):
        raise AuthorizationError(f"{label} bytes are not canonical")
    return value, payload


def _verify_registry_identity(
    registry_root: Path, linked_output_root: Path, identity: object
) -> None:
    if registry_root.is_symlink() or not registry_root.is_dir():
        raise AuthorizationError("authorization registry identity is unavailable or unsafe")
    values = identity if isinstance(identity, dict) else {}
    registry_stat = registry_root.stat(follow_symlinks=False)
    output_stat = linked_output_root.stat(follow_symlinks=False)
    expected = {
        "linked_output_root_device": output_stat.st_dev,
        "linked_output_root_inode": output_stat.st_ino,
        "linked_output_root_path": str(linked_output_root.resolve()),
        "registry_device": registry_stat.st_dev,
        "registry_inode": registry_stat.st_ino,
        "registry_path": str(registry_root.resolve()),
    }
    if any(values.get(name) != value for name, value in expected.items()):
        raise AuthorizationError("authorization registry identity does not match its bound root")


def _authorization_binding_projection(authorization: dict[str, Any]) -> dict[str, object]:
    scope = authorization.get("scope")
    image = authorization.get("image")
    command = authorization.get("command")
    environment = authorization.get("environment")
    if (
        not isinstance(scope, dict)
        or not isinstance(image, dict)
        or not isinstance(command, dict)
        or not isinstance(environment, dict)
    ):
        raise AuthorizationError("authorization binding projection is malformed")
    capability = scope.get("capability")
    linked_run = scope.get("linked_audit_run_ref")
    snapshot = scope.get("snapshot")
    work_item = scope.get("work_item_ref")
    if not all(isinstance(value, dict) for value in (capability, linked_run, snapshot, work_item)):
        raise AuthorizationError("authorization nested binding projection is malformed")
    assert isinstance(capability, dict)
    assert isinstance(linked_run, dict)
    assert isinstance(snapshot, dict)
    assert isinstance(work_item, dict)
    if scope.get("work_item_binding_status") != "complete_project_execution_work_item":
        raise AuthorizationError("authorization has no complete project WorkItem binding")
    return {
        "allowed_output_paths": tuple(scope["allowed_output_paths"]),
        "capability_semantic_digest": capability["semantic_digest"],
        "command_digest": command["normalized_digest"],
        "environment_digest": environment["normalized_digest"],
        "image_manifest_digest": image["manifest_digest"],
        "linked_audit_run_id": linked_run["record_id"],
        "snapshot_semantic_digest": snapshot["semantic_digest"],
        "source_semantic_lock_digest": scope["source_semantic_lock_digest"],
        "work_item_id": work_item["record_id"],
        "work_item_semantic_digest": scope["work_item_semantic_digest"],
    }


def read_registered_source_lock(
    registry_root: Path, authorization: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Verify and return the exact source lock copied into the private registry."""

    entry, _entry_payload = _read_canonical_object(registry_root / "entry.json", "registry entry")
    source_name = entry.get("source_semantic_lock_path")
    if source_name != "source-semantic.lock.json":
        raise AuthorizationError("registry source semantic-lock path is not the closed profile")
    source_lock, source_payload = _read_canonical_object(
        registry_root / source_name, "registered source semantic lock"
    )
    digest_input = dict(source_lock)
    semantic_lock_digest = digest_input.pop("semantic_lock_digest", None)
    if (
        semantic_lock_digest != semantic_digest(digest_input)
        or semantic_lock_digest != entry.get("source_semantic_lock_digest")
        or sha256_digest(source_payload) != entry.get("source_semantic_lock_bytes_digest")
    ):
        raise AuthorizationError("registered source semantic lock drifted")
    active_authorization = authorization
    if active_authorization is None:
        active_authorization, _authorization_payload = _read_canonical_object(
            registry_root / "authorization.json", "authorization"
        )
    scope = active_authorization.get("scope")
    if (
        not isinstance(scope, dict)
        or scope.get("source_semantic_lock_digest") != semantic_lock_digest
    ):
        raise AuthorizationError("authorization and registered source semantic lock disagree")
    return source_lock


def claim_authorization(
    registry_root: Path,
    bindings: ClaimBindings,
    schema_root: Path,
    *,
    claimed_at: str,
) -> dict[str, Any]:
    """Atomically consume one original registry entry before any runtime invocation."""

    entry, _entry_payload = _read_canonical_object(registry_root / "entry.json", "registry entry")
    authorization, authorization_payload = _read_canonical_object(
        registry_root / "authorization.json", "authorization"
    )
    read_registered_source_lock(registry_root, authorization)
    linked_output_root = registry_root.parents[1]
    _verify_registry_identity(registry_root, linked_output_root, entry.get("identity"))
    if linked_output_root.resolve() != bindings.linked_output_root.resolve():
        raise AuthorizationError("authorization binding mismatch: linked output root")
    LocalSchemaRegistry(schema_root).validate(authorization)
    if sha256_digest(authorization_payload) != entry.get("authorization_digest"):
        raise AuthorizationError("authorization bytes do not match the registered digest")
    if semantic_digest(authorization) != entry.get("authorization_semantic_digest"):
        raise AuthorizationError("authorization bytes do not match the registered meaning")
    if authorization.get("authorization_id") != entry.get("authorization_id"):
        raise AuthorizationError("authorization identifier does not match the registry")
    registry_binding = authorization.get("registry_binding")
    identity = entry.get("identity")
    if not isinstance(registry_binding, dict) or not isinstance(identity, dict):
        raise AuthorizationError("authorization registry binding is malformed")
    if registry_binding.get("registry_id") != identity.get("registry_id") or registry_binding.get(
        "linked_output_root_id"
    ) != identity.get("linked_output_root_id"):
        raise AuthorizationError("authorization registry binding does not match")
    nonce = authorization.get("single_use_nonce")
    if not isinstance(nonce, str) or sha256_digest(nonce) != entry.get("nonce_digest"):
        raise AuthorizationError("authorization nonce does not match the registry")
    if _timestamp(claimed_at, "claim") > _timestamp(
        str(authorization.get("expires_at")), "authorization expiry"
    ):
        raise AuthorizationError("authorization expired before consumption")

    actual = _authorization_binding_projection(authorization)
    expected = {
        "allowed_output_paths": bindings.allowed_output_paths,
        "capability_semantic_digest": bindings.capability_semantic_digest,
        "command_digest": bindings.command_digest,
        "environment_digest": bindings.environment_digest,
        "image_manifest_digest": bindings.image_manifest_digest,
        "linked_audit_run_id": bindings.linked_audit_run_id,
        "snapshot_semantic_digest": bindings.snapshot_semantic_digest,
        "source_semantic_lock_digest": bindings.source_semantic_lock_digest,
        "work_item_id": bindings.work_item_id,
        "work_item_semantic_digest": bindings.work_item_semantic_digest,
    }
    for name, expected_value in expected.items():
        if actual.get(name) != expected_value:
            raise AuthorizationError(f"authorization binding mismatch: {name}")

    authorization_digest = str(entry["authorization_semantic_digest"])
    attempt_id = stable_id("execution-attempt", authorization_digest, nonce, claimed_at)
    receipt: dict[str, Any] = {
        "attempt_id": attempt_id,
        "authorization_id": authorization["authorization_id"],
        "authorization_semantic_digest": authorization_digest,
        "claimed_at": claimed_at,
        "controller": {"tool": "sc-referee", "tool_version": __version__},
        "disposition": "claimed",
        "linked_output_root_id": identity["linked_output_root_id"],
        "nonce_digest": entry["nonce_digest"],
        "profile": _RECEIPT_PROFILE,
        "registry_id": identity["registry_id"],
        "source_semantic_lock_digest": bindings.source_semantic_lock_digest,
        "work_item_semantic_digest": bindings.work_item_semantic_digest,
    }
    receipt["receipt_digest"] = semantic_digest(receipt)
    atomic_create_bytes(
        registry_root / "consumption-receipt.json",
        (canonical_json(receipt) + "\n").encode("utf-8"),
    )
    fsync_directory(registry_root)
    return receipt


def recover_orphaned_claim(
    registry_root: Path, *, recovered_at: str, reason: str
) -> dict[str, Any]:
    """Append a terminal unknown disposition without deleting or rewriting the claim receipt."""

    if not reason.strip():
        raise AuthorizationError("orphan recovery reason must be nonempty")
    receipt, _payload = _read_canonical_object(
        registry_root / "consumption-receipt.json", "consumption receipt"
    )
    terminal: dict[str, Any] = {
        "attempt_id": receipt["attempt_id"],
        "disposition": "failed_unknown_after_controller_recovery",
        "reason": reason.strip(),
        "receipt_digest": receipt["receipt_digest"],
        "recovered_at": recovered_at,
    }
    terminal["terminal_digest"] = semantic_digest(terminal)
    atomic_create_bytes(
        registry_root / "consumption-terminal.json",
        (canonical_json(terminal) + "\n").encode("utf-8"),
    )
    fsync_directory(registry_root)
    return terminal


def finalize_claim(
    registry_root: Path,
    *,
    attempt_id: str,
    disposition: str,
    finalized_at: str,
    evidence_digest: str | None,
    limitations: tuple[str, ...],
) -> dict[str, Any]:
    """Append one terminal claim disposition without rewriting its immutable receipt."""

    allowed = {
        "completed",
        "failed_runtime_start",
        "failed_nonzero_exit",
        "timed_out",
        "cancelled",
        "output_rejected",
        "cleanup_failed",
        "controller_failed_unknown",
    }
    if disposition not in allowed:
        raise AuthorizationError("terminal consumption disposition is unsupported")
    receipt, _payload = _read_canonical_object(
        registry_root / "consumption-receipt.json", "consumption receipt"
    )
    if receipt.get("attempt_id") != attempt_id:
        raise AuthorizationError("terminal consumption attempt does not match the receipt")
    if evidence_digest is not None and not re.fullmatch(r"sha256:[a-f0-9]{64}", evidence_digest):
        raise AuthorizationError("terminal consumption evidence digest is malformed")
    if not limitations or any(not value.strip() for value in limitations):
        raise AuthorizationError("terminal consumption limitations must be explicit")
    terminal: dict[str, Any] = {
        "attempt_id": attempt_id,
        "disposition": disposition,
        "evidence_digest": evidence_digest,
        "finalized_at": finalized_at,
        "limitations": list(limitations),
        "receipt_digest": receipt["receipt_digest"],
    }
    terminal["terminal_digest"] = semantic_digest(terminal)
    atomic_create_bytes(
        registry_root / "consumption-terminal.json",
        (canonical_json(terminal) + "\n").encode("utf-8"),
    )
    fsync_directory(registry_root)
    return terminal
