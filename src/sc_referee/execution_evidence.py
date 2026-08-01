from __future__ import annotations

import html
import json
import shlex
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.snapshot.identity import (
    build_asset_identity,
    full_digest_evidence,
    unidentified_evidence,
)
from sc_referee.storage.atomic import atomic_create_bytes, fsync_directory
from sc_referee.storage.layout import AuditLayout
from sc_referee.storage.sqlite_index import rebuild_sqlite
from sc_referee.version import SCHEMA_VERSION, __version__

_LOCK_KIND = "linked_project_execution_v1"
_LOCK_ARRAYS = (
    "asset_identities",
    "artifacts",
    "audit_runs",
    "environments",
    "executions",
    "project_execution_authorizations",
    "sandbox_capabilities",
)
_LOCK_KEYS = {
    "audit_run_id",
    "asset_identities",
    "artifacts",
    "audit_runs",
    "consumption_terminal_digest",
    "environments",
    "executions",
    "lock_kind",
    "lock_version",
    "locked_at",
    "model_access_after_lock",
    "model_calls",
    "project_execution_authorizations",
    "raw_attempt_evidence_digest",
    "sandbox_capabilities",
    "semantic_lock_digest",
    "source_audit_run_id",
    "source_semantic_lock_digest",
    "source_snapshot_ref",
    "source_snapshot_semantic_digest",
    "source_work_item_ref",
    "source_work_item_semantic_digest",
}
_RESERVED_REPLAY_PATHS = {
    "audit.bundle.json",
    "audit.db",
    "report.html",
    "semantic.lock.json",
}
_LOG_ARTIFACT_ROLES = {
    "stdout": "project workflow retained stdout",
    "stderr": "project workflow retained stderr",
    "controller_events": "authorized execution controller events",
    "output_manifest": "accepted project output manifest",
}
_SUPPORT_ARTIFACT_ROLES = {
    "attempt_evidence": "terminal authorized execution attempt evidence",
    "source_semantic_lock": "exact registered source semantic lock",
    "consumption_receipt": "single-use authorization consumption receipt",
    "consumption_terminal": "terminal authorization consumption disposition",
}
_UNAVAILABLE_OUTPUT_MANIFEST_ROLE = "accepted project output manifest unavailable"
_UNAVAILABLE_OUTPUT_MANIFEST_REASON = "No accepted output manifest was produced for this attempt."
_PUBLIC_ID_FIELDS = {
    "artifact": "artifact_id",
    "asset_identity": "asset_identity_id",
    "audit_run": "audit_run_id",
    "environment": "environment_id",
    "execution": "execution_id",
    "project_execution_authorization": "authorization_id",
    "sandbox_capability": "sandbox_capability_id",
}


@dataclass(frozen=True)
class LinkedExecutionPublication:
    semantic_lock_path: Path
    bundle_path: Path
    sqlite_path: Path
    report_path: Path
    semantic_lock: dict[str, Any]
    bundle: dict[str, Any]


@dataclass(frozen=True)
class LinkedExecutionV14Inspection:
    """Read-only v0.14 closure inventory with no clean-control or launch authority."""

    semantic_lock_digest: str
    public_record_digests: tuple[tuple[str, str, str], ...]
    source_record_digests: tuple[tuple[str, str, str], ...]
    retained_artifact_byte_digests: tuple[tuple[str, str], ...]
    coverage_limitations: tuple[str, ...]


def _canonical_object_payload(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError(f"{label} is not JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} is not an object")
    if payload != (canonical_json(value) + "\n").encode("utf-8"):
        raise ValueError(f"{label} bytes are not canonical")
    return value


def _read_canonical_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} is unavailable or unsafe")
    payload = path.read_bytes()
    value = _canonical_object_payload(payload, label)
    return value, payload


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} is malformed")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} is unavailable")
    return value


def _safe_relative_path(value: str) -> PurePosixPath:
    relative = PurePosixPath(value)
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ValueError(f"unsafe linked evidence path: {value!r}")
    if relative.as_posix() in _RESERVED_REPLAY_PATHS:
        raise ValueError(f"linked evidence path collides with a canonical output: {value!r}")
    return relative


def _safe_file(root: Path, relative: str) -> Path:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("linked execution root is unavailable or unsafe")
    logical = _safe_relative_path(relative)
    candidate = root.joinpath(*logical.parts)
    cursor = root
    for part in logical.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError(f"linked evidence path contains a symlink: {relative}")
    if not candidate.is_file():
        raise ValueError(f"linked evidence file is unavailable or unsafe: {relative}")
    if candidate.stat().st_nlink != 1:
        raise ValueError(f"linked evidence file has external hard links: {relative}")
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    if not resolved_candidate.is_relative_to(resolved_root):
        raise ValueError(f"linked evidence file escapes its root: {relative}")
    return candidate


def _relative_path(root: Path, path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"linked evidence file is unavailable or unsafe: {path}")
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"linked evidence file escapes its root: {path}") from error
    _safe_relative_path(relative)
    return relative


def _runtime_provenance(method: str, created_at: str) -> dict[str, Any]:
    return {
        "actor": {
            "actor_kind": "runtime",
            "actor_id": "runtime:sc-referee-authorized-rootless-oci",
            "display_name": "sc-referee authorized OCI runtime",
        },
        "method": method,
        "created_at": created_at,
        "tool": "sc-referee",
        "tool_version": __version__,
    }


def _artifact_with_identity(
    *,
    audit_run_id: str,
    linked_root: Path,
    logical_name: str,
    observed_role: str,
    kind: str,
    created_at: str,
    path: Path | None,
    limitations: tuple[str, ...],
    unavailable_reason: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    relative = _relative_path(linked_root, path) if path is not None else None
    artifact_id = stable_id(
        "artifact-execution",
        audit_run_id,
        logical_name,
        relative or unavailable_reason or "unavailable",
    )
    if path is not None:
        evidence = full_digest_evidence(sha256_digest(path.read_bytes()))
        source_ref = {
            "source_kind": "runtime_command",
            "locator": relative,
            "content_digest": evidence.identity_evidence["digest"],
        }
    else:
        reason = _string(unavailable_reason, "unavailable artifact reason")
        evidence = unidentified_evidence(reason, limitations=(reason,))
        source_ref = {
            "source_kind": "runtime_command",
            "locator": f"authorized execution artifact unavailable: {logical_name}",
        }
    identity = build_asset_identity(
        audit_run_id=audit_run_id,
        asset_record_type="artifact",
        asset_record_id=artifact_id,
        evidence=evidence,
        created_at=created_at,
    )
    artifact: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "artifact",
        "artifact_id": artifact_id,
        "audit_run_id": audit_run_id,
        "kind": kind,
        "observed_role": observed_role,
        "source_refs": [source_ref],
        "producer_operation_refs": [],
        "consumer_operation_refs": [],
        "asset_identity_ref": typed_ref("asset_identity", str(identity["asset_identity_id"])),
        "limitations": list(limitations),
        "provenance": controller_provenance("authorized_execution_evidence_capture", created_at),
    }
    if relative is not None:
        artifact["path"] = relative
    return artifact, identity


def _validate_output_manifest(
    linked_root: Path, manifest: dict[str, Any], accepted_output_root: Path
) -> list[tuple[str, Path]]:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("accepted output manifest entries are malformed")
    outputs: list[tuple[str, Path]] = []
    observed_total = 0
    seen: set[str] = set()
    for entry in entries:
        value = _mapping(entry, "accepted output manifest entry")
        relative = _string(value.get("path"), "accepted output path")
        _safe_relative_path(relative)
        if relative in seen:
            raise ValueError("accepted output manifest paths are duplicated")
        seen.add(relative)
        path = _safe_file(accepted_output_root, relative)
        payload = path.read_bytes()
        expected_digest = _string(value.get("digest"), "accepted output digest")
        expected_size = value.get("size_bytes")
        if sha256_digest(payload) != expected_digest or len(payload) != expected_size:
            raise ValueError(f"accepted output drifted before evidence lock: {relative}")
        observed_total += len(payload)
        _relative_path(linked_root, path)
        outputs.append((relative, path))
    if manifest.get("total_logical_bytes") != observed_total:
        raise ValueError("accepted output manifest total does not match captured bytes")
    logical_limit = manifest.get("logical_byte_limit")
    if (
        not isinstance(logical_limit, int)
        or isinstance(logical_limit, bool)
        or observed_total > logical_limit
    ):
        raise ValueError("accepted output manifest exceeds or lacks its logical-byte bound")
    return outputs


def _environment_record(
    capability: dict[str, Any], authorization: dict[str, Any], created_at: str
) -> dict[str, Any]:
    evidence = _mapping(capability.get("capability_evidence"), "sandbox capability evidence")
    backend = _mapping(evidence.get("backend"), "sandbox backend evidence")
    platform = _mapping(evidence.get("host_platform"), "sandbox platform evidence")
    oci_runtime = _mapping(evidence.get("oci_runtime"), "OCI runtime evidence")
    audit_run_id = _string(
        _mapping(
            _mapping(authorization.get("scope"), "authorization scope").get("linked_audit_run_ref"),
            "linked audit run reference",
        ).get("record_id"),
        "linked audit run identifier",
    )
    capability_id = _string(
        capability.get("sandbox_capability_id"), "sandbox capability identifier"
    )
    authorization_id = _string(
        authorization.get("authorization_id"), "project execution authorization identifier"
    )
    authorization_digest = semantic_digest(authorization)
    capability_digest = semantic_digest(capability)
    implementation = " ".join(
        value
        for value in (
            str(oci_runtime.get("name", "")).strip(),
            str(oci_runtime.get("version", "")).strip(),
        )
        if value
    )
    runtime: dict[str, str] = {
        "name": _string(capability.get("backend_name"), "sandbox backend name")
    }
    version = backend.get("version")
    if isinstance(version, str) and version:
        runtime["version"] = version
    if implementation:
        runtime["implementation"] = implementation
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "environment",
        "environment_id": stable_id(
            "environment-project-runtime", audit_run_id, capability_digest, authorization_digest
        ),
        "audit_run_id": audit_run_id,
        "environment_kind": "project_runtime",
        "identity_status": "exact",
        "runtime": runtime,
        "platform": {
            "system": _string(platform.get("system"), "sandbox platform system"),
            "machine": _string(platform.get("machine"), "sandbox platform machine"),
        },
        "dependency_refs": [
            typed_ref("project_execution_authorization", authorization_id),
            typed_ref("sandbox_capability", capability_id),
        ],
        "source_refs": [
            {
                "source_kind": "runtime_command",
                "locator": f"sandbox capability {capability_id}",
                "content_digest": capability_digest,
            },
            {
                "source_kind": "runtime_command",
                "locator": f"project execution authorization {authorization_id}",
                "content_digest": authorization_digest,
            },
        ],
        "limitations": [],
        "provenance": controller_provenance(
            "bound_sandbox_capability_environment_projection", created_at
        ),
    }


def _exit_projection(disposition: str, exit_code: object, timed_out: object) -> dict[str, Any]:
    if timed_out is True:
        return {"state": "timed_out"}
    if isinstance(exit_code, int) and not isinstance(exit_code, bool):
        return {"state": "succeeded" if exit_code == 0 else "failed", "code": exit_code}
    if disposition in {"completed", "failed_nonzero_exit"}:
        raise ValueError("terminal execution disposition lacks an observed process exit")
    return {"state": "not_observed"}


def _consumption_disposition(disposition: str) -> str:
    if disposition == "completed":
        return "completed"
    if disposition == "controller_failed_unknown":
        return "failed_unknown"
    return "failed"


def _cleanup_state(disposition: str, cleanup_observed: object) -> str:
    if cleanup_observed is True:
        return "succeeded"
    if disposition == "cleanup_failed":
        return "failed"
    return "unavailable"


def _empty_bundle(validator: LocalSchemaRegistry, lock: dict[str, Any]) -> dict[str, Any]:
    schema = validator.by_record_type["audit_bundle"]
    properties = _mapping(schema.get("properties"), "AuditBundle schema properties")
    bundle: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "audit_bundle",
        "bundle_id": stable_id("bundle-linked-execution", str(lock["audit_run_id"])),
        "audit_run_id": lock["audit_run_id"],
        "generated_at": lock["locked_at"],
        "semantic_lock_digest": lock["semantic_lock_digest"],
    }
    for name, property_schema in properties.items():
        if isinstance(property_schema, dict) and property_schema.get("type") == "array":
            bundle[name] = []
    for name in _LOCK_ARRAYS:
        bundle[name] = deepcopy(lock[name])
    bundle["extensions"] = {
        "x-linked-execution-evidence": {
            "correctness_conclusion_allowed": False,
            "source_audit_run_id": lock["source_audit_run_id"],
            "source_semantic_lock_digest": lock["source_semantic_lock_digest"],
            "source_work_item_semantic_digest": lock["source_work_item_semantic_digest"],
        }
    }
    return bundle


def _public_records(lock: dict[str, Any]) -> list[dict[str, Any]]:
    return [record for name in _LOCK_ARRAYS for record in lock[name]]


def _index_records(
    records: list[dict[str, Any]], *, id_field: str, label: str
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        record_id = _string(record.get(id_field), f"{label} identifier")
        if record_id in indexed:
            raise ValueError(f"linked execution contains duplicate {label} identifiers")
        indexed[record_id] = record
    return indexed


def _ref_id(value: object, *, record_type: str, label: str) -> str:
    reference = _mapping(value, label)
    if reference.get("record_type") != record_type:
        raise ValueError(f"{label} has the wrong record type")
    return _string(reference.get("record_id"), f"{label} identifier")


def _artifact_for_role(artifacts: dict[str, dict[str, Any]], role: str) -> dict[str, Any]:
    matches = [item for item in artifacts.values() if item.get("observed_role") == role]
    if len(matches) != 1:
        raise ValueError(f"linked execution requires exactly one artifact role: {role}")
    return matches[0]


def _validate_artifact_identity_closure(
    lock: dict[str, Any], *, audit_run_id: str, execution: dict[str, Any]
) -> None:
    artifacts = _index_records(lock["artifacts"], id_field="artifact_id", label="Artifact")
    identities = _index_records(
        lock["asset_identities"], id_field="asset_identity_id", label="AssetIdentity"
    )
    project_execution = _mapping(execution.get("project_execution"), "project execution evidence")
    log_refs = _mapping(project_execution.get("log_refs"), "project execution log references")
    if set(log_refs) != set(_LOG_ARTIFACT_ROLES):
        raise ValueError("linked execution log reference inventory is not closed")

    logical_name_by_artifact_id: dict[str, str] = {}
    for name, role in _LOG_ARTIFACT_ROLES.items():
        artifact_id = _ref_id(log_refs[name], record_type="artifact", label=f"{name} log reference")
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            raise ValueError(f"linked execution {name} log reference is unresolved")
        allowed_roles = (
            {role, _UNAVAILABLE_OUTPUT_MANIFEST_ROLE} if name == "output_manifest" else {role}
        )
        if artifact.get("observed_role") not in allowed_roles:
            raise ValueError(f"linked execution {name} log role is inconsistent")
        logical_name_by_artifact_id[artifact_id] = name

    for logical_name, role in _SUPPORT_ARTIFACT_ROLES.items():
        artifact = _artifact_for_role(artifacts, role)
        logical_name_by_artifact_id[str(artifact["artifact_id"])] = logical_name

    output_refs = execution.get("output_refs")
    if not isinstance(output_refs, list):
        raise ValueError("linked execution output references are malformed")
    for reference in output_refs:
        artifact_id = _ref_id(reference, record_type="artifact", label="accepted output reference")
        if artifact_id in logical_name_by_artifact_id:
            raise ValueError("linked execution reuses an artifact across material roles")
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            raise ValueError("linked execution accepted output reference is unresolved")
        relative = artifact.get("path")
        if not isinstance(relative, str) or not relative.startswith("accepted-output/"):
            raise ValueError("linked execution accepted output path is inconsistent")
        output_name = relative.removeprefix("accepted-output/")
        if (
            not output_name
            or artifact.get("observed_role") != f"accepted project output {output_name}"
        ):
            raise ValueError("linked execution accepted output role is inconsistent")
        logical_name_by_artifact_id[artifact_id] = f"accepted_output:{output_name}"

    if set(logical_name_by_artifact_id) != set(artifacts):
        raise ValueError("linked execution Artifact inventory has missing or extra roles")

    used_identity_ids: set[str] = set()
    for artifact_id, artifact in artifacts.items():
        if artifact.get("audit_run_id") != audit_run_id:
            raise ValueError("linked execution Artifact has the wrong audit run")
        identity_id = _ref_id(
            artifact.get("asset_identity_ref"),
            record_type="asset_identity",
            label="Artifact identity reference",
        )
        identity = identities.get(identity_id)
        if identity is None:
            raise ValueError("linked execution Artifact identity reference is unresolved")
        if identity_id in used_identity_ids:
            raise ValueError("linked execution reuses one AssetIdentity across Artifacts")
        used_identity_ids.add(identity_id)
        if identity.get("audit_run_id") != audit_run_id or identity.get("asset_ref") != {
            "record_type": "artifact",
            "record_id": artifact_id,
        }:
            raise ValueError("linked execution Artifact/AssetIdentity backlink is inconsistent")

        evidence = _mapping(identity.get("identity_evidence"), "Artifact identity evidence")
        path = artifact.get("path")
        logical_name = logical_name_by_artifact_id[artifact_id]
        if isinstance(path, str):
            digest = _string(evidence.get("digest"), "Artifact full digest")
            if identity.get("tier") != "full_digest" or evidence.get("kind") != "full_digest":
                raise ValueError("path-bearing linked Artifact lacks full-digest identity")
            source_refs = artifact.get("source_refs")
            if (
                not isinstance(source_refs, list)
                or len(source_refs) != 1
                or source_refs[0].get("locator") != path
                or source_refs[0].get("content_digest") != digest
            ):
                raise ValueError("linked Artifact source reference disagrees with its identity")
            identity_evidence = full_digest_evidence(digest)
            identity_seed = path
        else:
            if logical_name != "output_manifest":
                raise ValueError("only an unavailable output manifest may lack retained bytes")
            if (
                identity.get("tier") != "unidentified"
                or evidence.get("kind") != "unidentified"
                or evidence.get("reason") != _UNAVAILABLE_OUTPUT_MANIFEST_REASON
            ):
                raise ValueError("unavailable output manifest identity is inconsistent")
            identity_evidence = unidentified_evidence(
                _UNAVAILABLE_OUTPUT_MANIFEST_REASON,
                limitations=(_UNAVAILABLE_OUTPUT_MANIFEST_REASON,),
            )
            identity_seed = _UNAVAILABLE_OUTPUT_MANIFEST_REASON

        if artifact_id != stable_id(
            "artifact-execution", audit_run_id, logical_name, identity_seed
        ):
            raise ValueError("linked execution Artifact identifier is not deterministic")
        expected_identity = build_asset_identity(
            audit_run_id=audit_run_id,
            asset_record_type="artifact",
            asset_record_id=artifact_id,
            evidence=identity_evidence,
            created_at=_string(identity.get("created_at"), "AssetIdentity creation time"),
        )
        if identity != expected_identity:
            raise ValueError("linked execution AssetIdentity is not the deterministic projection")

    if used_identity_ids != set(identities):
        raise ValueError("linked execution AssetIdentity inventory has missing or extra records")


def _validate_linked_record_closure(lock: dict[str, Any]) -> None:
    authorization = lock["project_execution_authorizations"][0]
    capability = lock["sandbox_capabilities"][0]
    execution = lock["executions"][0]
    run = lock["audit_runs"][0]
    environment = lock["environments"][0]
    audit_run_id = _string(lock.get("audit_run_id"), "linked audit run identifier")
    authorization_id = _string(
        authorization.get("authorization_id"), "project execution authorization identifier"
    )
    capability_id = _string(
        capability.get("sandbox_capability_id"), "sandbox capability identifier"
    )
    environment_id = _string(environment.get("environment_id"), "environment identifier")

    scope = _mapping(authorization.get("scope"), "linked authorization scope")
    project_execution = _mapping(execution.get("project_execution"), "linked execution evidence")
    snapshot = _mapping(scope.get("snapshot"), "authorization snapshot binding")
    if scope.get("linked_audit_run_ref") != typed_ref("audit_run", audit_run_id):
        raise ValueError("authorization does not bind the linked audit run")
    if scope.get("source_audit_run_ref") != typed_ref(
        "audit_run", _string(lock.get("source_audit_run_id"), "source audit run identifier")
    ):
        raise ValueError("authorization does not bind the source audit run")
    if scope.get("work_item_ref") != lock.get("source_work_item_ref"):
        raise ValueError("authorization does not bind the source WorkItem reference")
    if snapshot.get("record_ref") != lock.get("source_snapshot_ref") or snapshot.get(
        "semantic_digest"
    ) != lock.get("source_snapshot_semantic_digest"):
        raise ValueError("authorization does not bind the source snapshot")

    authorization_ref = typed_ref("project_execution_authorization", authorization_id)
    capability_ref = typed_ref("sandbox_capability", capability_id)
    if execution.get("environment_ref") != typed_ref("environment", environment_id):
        raise ValueError("linked Execution does not bind its Environment")
    if (
        _mapping(execution.get("sandbox"), "linked execution sandbox").get("sandbox_capability_ref")
        != capability_ref
    ):
        raise ValueError("linked Execution does not bind its SandboxCapability")
    if project_execution.get("authorization_ref") != authorization_ref:
        raise ValueError("linked Execution does not bind its authorization")
    capability_binding = _mapping(scope.get("capability"), "authorization capability binding")
    if capability_binding.get("record_ref") != capability_ref:
        raise ValueError("authorization capability reference is inconsistent")
    if environment.get("dependency_refs") != [authorization_ref, capability_ref]:
        raise ValueError("linked Environment dependency closure is inconsistent")

    if run.get("parent_run_ref") != scope.get("source_audit_run_ref") or run.get(
        "snapshot_ref"
    ) != snapshot.get("record_ref"):
        raise ValueError("linked AuditRun parent or snapshot binding is inconsistent")
    if execution.get("input_refs") != scope.get("declared_input_refs"):
        raise ValueError("linked Execution inputs disagree with authorization")
    if project_execution.get("command") != authorization.get("command"):
        raise ValueError("linked Execution command disagrees with authorization")
    if project_execution.get("image") != authorization.get("image"):
        raise ValueError("linked Execution image disagrees with authorization")
    expected_policy = {
        "network_policy": authorization.get("network_policy"),
        "limits": authorization.get("limits"),
        "environment": authorization.get("environment"),
    }
    if project_execution.get("effective_policy") != expected_policy:
        raise ValueError("linked Execution policy disagrees with authorization")

    execution_sources = execution.get("source_refs")
    if (
        not isinstance(execution_sources, list)
        or len(execution_sources) != 1
        or execution_sources[0].get("content_digest") != lock.get("raw_attempt_evidence_digest")
    ):
        raise ValueError("linked Execution does not bind the raw attempt evidence digest")

    _validate_artifact_identity_closure(lock, audit_run_id=audit_run_id, execution=execution)


def _validate_linked_lock(lock: dict[str, Any], validator: LocalSchemaRegistry) -> None:
    if set(lock) != _LOCK_KEYS:
        raise ValueError("linked execution lock is not the closed v1 record set")
    if lock.get("lock_kind") != _LOCK_KIND or lock.get("lock_version") != SCHEMA_VERSION:
        raise ValueError("linked execution lock kind or version is unsupported")
    if lock.get("model_calls") != [] or lock.get("model_access_after_lock") is not False:
        raise ValueError("linked execution lock violates the post-lock model boundary")
    expected_digest = lock.get("semantic_lock_digest")
    digest_input = deepcopy(lock)
    digest_input.pop("semantic_lock_digest", None)
    if expected_digest != semantic_digest(digest_input):
        raise ValueError("linked execution semantic lock digest does not match")
    if any(not isinstance(lock.get(name), list) for name in _LOCK_ARRAYS):
        raise ValueError("linked execution public record arrays are malformed")
    if any(
        len(lock[name]) != 1
        for name in (
            "audit_runs",
            "environments",
            "executions",
            "project_execution_authorizations",
            "sandbox_capabilities",
        )
    ):
        raise ValueError(
            "linked execution lock requires exactly one run, environment, execution, authorization, and capability"
        )
    for record in _public_records(lock):
        if not isinstance(record, dict):
            raise ValueError("linked execution public record is malformed")
        validator.validate(record)

    authorization = lock["project_execution_authorizations"][0]
    capability = lock["sandbox_capabilities"][0]
    execution = lock["executions"][0]
    run = lock["audit_runs"][0]
    environment = lock["environments"][0]
    scope = _mapping(authorization.get("scope"), "linked authorization scope")
    project_execution = _mapping(execution.get("project_execution"), "linked execution evidence")
    if authorization.get("audit_run_id") is not None:
        raise ValueError("authorization unexpectedly carries an audit run identifier")
    if (
        execution.get("audit_run_id") != lock["audit_run_id"]
        or run.get("audit_run_id") != lock["audit_run_id"]
        or environment.get("audit_run_id") != lock["audit_run_id"]
    ):
        raise ValueError("linked public records disagree on audit run identity")
    if project_execution.get("work_item_ref") != lock["source_work_item_ref"]:
        raise ValueError("linked execution disagrees with the locked WorkItem binding")
    if scope.get("work_item_semantic_digest") != lock["source_work_item_semantic_digest"]:
        raise ValueError("linked authorization disagrees with the locked WorkItem digest")
    if scope.get("source_semantic_lock_digest") != lock["source_semantic_lock_digest"]:
        raise ValueError("linked authorization disagrees with the source semantic lock")
    capability_binding = _mapping(scope.get("capability"), "linked capability binding")
    if capability_binding.get("semantic_digest") != semantic_digest(capability):
        raise ValueError("linked sandbox capability digest does not match authorization")
    if project_execution.get("authorization_semantic_digest") != semantic_digest(authorization):
        raise ValueError("linked execution authorization digest does not match")
    _validate_linked_record_closure(lock)


def _retained_artifact_payloads(
    lock: dict[str, Any], source_root: Path
) -> list[tuple[str, str, bytes, str]]:
    identities = {str(item["asset_identity_id"]): item for item in lock["asset_identities"]}
    retained: list[tuple[str, str, bytes, str]] = []
    for artifact in lock["artifacts"]:
        relative = artifact.get("path")
        if not isinstance(relative, str):
            continue
        identity_id = _string(
            _mapping(artifact.get("asset_identity_ref"), "artifact identity reference").get(
                "record_id"
            ),
            "artifact identity identifier",
        )
        identity = _mapping(identities.get(identity_id), "artifact identity")
        evidence = _mapping(identity.get("identity_evidence"), "artifact identity evidence")
        if identity.get("tier") != "full_digest" or evidence.get("kind") != "full_digest":
            raise ValueError("a path-bearing linked artifact lacks full-digest identity")
        expected_digest = _string(evidence.get("digest"), "linked artifact digest")
        source = _safe_file(source_root, relative)
        payload = source.read_bytes()
        if sha256_digest(payload) != expected_digest:
            raise ValueError(f"linked artifact bytes drifted before replay: {relative}")
        retained.append(
            (
                _string(artifact.get("artifact_id"), "linked Artifact identifier"),
                relative,
                payload,
                expected_digest,
            )
        )
    return sorted(retained)


def _source_record_digests(
    lock: dict[str, Any],
    validator: LocalSchemaRegistry,
    retained: list[tuple[str, str, bytes, str]],
) -> tuple[tuple[str, str, str], ...]:
    artifacts = _index_records(lock["artifacts"], id_field="artifact_id", label="Artifact")
    source_artifact = _artifact_for_role(artifacts, _SUPPORT_ARTIFACT_ROLES["source_semantic_lock"])
    source_artifact_id = _string(
        source_artifact.get("artifact_id"), "source semantic-lock Artifact identifier"
    )
    retained_by_id = {artifact_id: payload for artifact_id, _path, payload, _digest in retained}
    source_payload = retained_by_id.get(source_artifact_id)
    if source_payload is None:
        raise ValueError("source semantic-lock Artifact bytes are unavailable")
    source_lock = _canonical_object_payload(source_payload, "retained source semantic lock")

    source_digest = source_lock.get("semantic_lock_digest")
    digest_input = deepcopy(source_lock)
    digest_input.pop("semantic_lock_digest", None)
    if source_digest != semantic_digest(digest_input) or source_digest != lock.get(
        "source_semantic_lock_digest"
    ):
        raise ValueError("retained source semantic-lock digest is inconsistent")
    if source_lock.get("audit_run_id") != lock.get("source_audit_run_id"):
        raise ValueError("retained source semantic lock has the wrong audit run")

    snapshot = _mapping(
        source_lock.get("repository_snapshot"), "retained source RepositorySnapshot"
    )
    validator.validate(snapshot)
    snapshot_id = _string(snapshot.get("snapshot_id"), "source RepositorySnapshot identifier")
    if lock.get("source_snapshot_ref") != typed_ref("repository_snapshot", snapshot_id):
        raise ValueError("retained source RepositorySnapshot reference is inconsistent")
    snapshot_digest = semantic_digest(snapshot)
    if snapshot_digest != lock.get("source_snapshot_semantic_digest"):
        raise ValueError("retained source RepositorySnapshot digest is inconsistent")

    work_item_ref = _mapping(lock.get("source_work_item_ref"), "source WorkItem reference")
    work_item_id = _ref_id(
        work_item_ref, record_type="work_item", label="source WorkItem reference"
    )
    work_items = source_lock.get("work_items")
    if not isinstance(work_items, list):
        raise ValueError("retained source WorkItem inventory is malformed")
    matches = [
        item
        for item in work_items
        if isinstance(item, dict) and item.get("work_item_id") == work_item_id
    ]
    if len(matches) != 1:
        raise ValueError("retained source WorkItem binding is unresolved or ambiguous")
    work_item = matches[0]
    validator.validate(work_item)
    work_item_digest = semantic_digest(work_item)
    if work_item_digest != lock.get("source_work_item_semantic_digest"):
        raise ValueError("retained source WorkItem digest is inconsistent")

    return (
        ("repository_snapshot", snapshot_id, snapshot_digest),
        ("work_item", work_item_id, work_item_digest),
    )


def inspect_linked_execution_v14(
    lock_path: Path, schema_root: Path
) -> LinkedExecutionV14Inspection:
    """Inspect exact retained v0.14 linked evidence without replay, model, or runtime access.

    The result inventories what v0.14 actually closes. It deliberately does not determine
    clean-control eligibility and cannot fill source-record or trusted-probe-origin gaps.
    """

    lock, _payload = _read_canonical_object(lock_path, "linked execution semantic lock")
    validator = LocalSchemaRegistry(schema_root)
    _validate_linked_lock(lock, validator)
    retained = _retained_artifact_payloads(lock, lock_path.parent)
    source_record_digests = _source_record_digests(lock, validator, retained)

    public_record_digests: list[tuple[str, str, str]] = []
    for record in _public_records(lock):
        record_type = _string(record.get("record_type"), "linked public record type")
        id_field = _PUBLIC_ID_FIELDS.get(record_type)
        if id_field is None:
            raise ValueError(f"linked execution contains an unsupported record type: {record_type}")
        public_record_digests.append(
            (
                record_type,
                _string(record.get(id_field), f"{record_type} identifier"),
                semantic_digest(record),
            )
        )

    return LinkedExecutionV14Inspection(
        semantic_lock_digest=_string(
            lock.get("semantic_lock_digest"), "linked semantic lock digest"
        ),
        public_record_digests=tuple(sorted(public_record_digests)),
        source_record_digests=source_record_digests,
        retained_artifact_byte_digests=tuple(
            (artifact_id, digest) for artifact_id, _relative, _payload, digest in retained
        ),
        coverage_limitations=(
            "Schema v0.14 retains the exact source RepositorySnapshot and project-execution WorkItem only inside the source-lock Artifact, not as linked public dependency records; the source AuditRun record is absent.",
            "Schema v0.14 has no public dependency-inventory record binding these semantic digests for clean-control fixture proof.",
            "Structural closure does not establish trusted capability-probe origin, scientific correctness, or launch authority.",
        ),
    )


def _render_linked_report(bundle: dict[str, Any]) -> bytes:
    execution = bundle["executions"][0]
    project = execution["project_execution"]
    authorization = bundle["project_execution_authorizations"][0]
    limitations = "".join(f"<li>{html.escape(str(item))}</li>" for item in execution["limitations"])
    command = html.escape(shlex.join(tuple(str(value) for value in project["command"]["argv"])))
    output_count = len(execution["output_refs"])
    body = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>sc-referee linked execution evidence</title><style>body{{max-width:72rem;margin:0 auto;padding:2rem;font-family:system-ui,sans-serif;line-height:1.5}}code{{overflow-wrap:anywhere}}.notice{{border-left:.35rem solid #888;padding-left:1rem}}</style></head>
<body><h1>sc-referee linked execution evidence</h1>
<p class="notice"><strong>This records an authorized process attempt. It does not establish scientific correctness, validate project-produced bytes, or show that no issues exist.</strong></p>
<p><strong>Run:</strong> <code>{html.escape(str(bundle["audit_run_id"]))}</code></p>
<p><strong>Purpose:</strong> {html.escape(str(project["purpose"]))}</p>
<p><strong>Attempt disposition:</strong> {html.escape(str(project["consumption"]["disposition"]))}; <strong>process exit:</strong> {html.escape(str(execution["exit"]["state"]))}; <strong>captured outputs:</strong> {output_count}.</p>
<p><strong>Command:</strong> <code>{command}</code></p>
<p><strong>Image:</strong> <code>{html.escape(str(project["image"]["reference"]))}</code></p>
<p><strong>Network:</strong> {html.escape(str(authorization["network_policy"]))}; <strong>authorization:</strong> <code>{html.escape(str(authorization["authorization_id"]))}</code>.</p>
<h2>Coverage limitations</h2><ul>{limitations}</ul>
<p><strong>Semantic lock:</strong> <code>{html.escape(str(bundle["semantic_lock_digest"]))}</code></p></body></html>"""
    return body.encode("utf-8")


def _write_outputs(
    lock: dict[str, Any],
    output: Path,
    schema_root: Path,
    *,
    source_root: Path | None,
) -> LinkedExecutionPublication:
    if output.is_symlink() or not output.is_dir():
        raise ValueError("linked execution output root is unavailable or unsafe")
    validator = LocalSchemaRegistry(schema_root)
    _validate_linked_lock(lock, validator)
    layout = AuditLayout(output)
    layout.create()

    if source_root is not None:
        retained = _retained_artifact_payloads(lock, source_root)
        _source_record_digests(lock, validator, retained)
        for _artifact_id, relative, payload, _digest in retained:
            target_relative = _safe_relative_path(relative)
            atomic_create_bytes(output.joinpath(*target_relative.parts), payload)

    bundle = _empty_bundle(validator, lock)
    validator.validate(bundle)
    write_normalized_json_once(layout.lock_path, lock)
    write_normalized_json_once(layout.bundle_path, bundle)
    rebuild_sqlite(layout.sqlite_path, _public_records(lock))
    atomic_create_bytes(layout.report_path, _render_linked_report(bundle))
    fsync_directory(output)
    return LinkedExecutionPublication(
        semantic_lock_path=layout.lock_path,
        bundle_path=layout.bundle_path,
        sqlite_path=layout.sqlite_path,
        report_path=layout.report_path,
        semantic_lock=lock,
        bundle=bundle,
    )


def publish_linked_execution_evidence(
    *,
    linked_output_root: Path,
    registry_root: Path,
    capability: dict[str, object],
    schema_root: Path,
    attempt_root: Path,
    evidence_path: Path,
) -> LinkedExecutionPublication:
    """Lock one terminal authorized attempt as public, non-accusatory evidence."""

    authorization, _authorization_payload = _read_canonical_object(
        registry_root / "authorization.json", "project execution authorization"
    )
    receipt, _receipt_payload = _read_canonical_object(
        registry_root / "consumption-receipt.json", "authorization consumption receipt"
    )
    terminal, _terminal_payload = _read_canonical_object(
        registry_root / "consumption-terminal.json", "authorization consumption terminal"
    )
    raw_evidence, evidence_payload = _read_canonical_object(
        evidence_path, "project execution attempt evidence"
    )
    validator = LocalSchemaRegistry(schema_root)
    validator.validate(authorization)
    validator.validate(capability)
    if evidence_path.parent.resolve() != attempt_root.resolve():
        raise ValueError("attempt evidence is not inside the exact attempt root")
    if registry_root.parents[1].resolve() != linked_output_root.resolve():
        raise ValueError("authorization registry is not bound to the linked output root")

    attempt_id = _string(receipt.get("attempt_id"), "execution attempt identifier")
    disposition = _string(raw_evidence.get("disposition"), "execution disposition")
    started_at = _string(raw_evidence.get("started_at"), "execution start time")
    finished_at = _string(raw_evidence.get("finished_at"), "execution finish time")
    if raw_evidence.get("attempt_id") != attempt_id or terminal.get("attempt_id") != attempt_id:
        raise ValueError("terminal execution evidence disagrees on attempt identity")
    if terminal.get("disposition") != disposition:
        raise ValueError("terminal execution evidence disagrees on disposition")
    if terminal.get("receipt_digest") != receipt.get("receipt_digest"):
        raise ValueError("terminal execution evidence disagrees on receipt identity")
    if terminal.get("evidence_digest") != sha256_digest(evidence_payload):
        raise ValueError("terminal execution evidence digest does not match")
    authorization_digest = semantic_digest(authorization)
    if receipt.get("authorization_semantic_digest") != authorization_digest:
        raise ValueError("consumption receipt disagrees with authorization meaning")

    scope = _mapping(authorization.get("scope"), "authorization scope")
    linked_run_ref = _mapping(scope.get("linked_audit_run_ref"), "linked audit run reference")
    source_run_ref = _mapping(scope.get("source_audit_run_ref"), "source audit run reference")
    work_item_ref = _mapping(scope.get("work_item_ref"), "source WorkItem reference")
    snapshot = _mapping(scope.get("snapshot"), "source snapshot binding")
    snapshot_ref = _mapping(snapshot.get("record_ref"), "source snapshot reference")
    audit_run_id = _string(linked_run_ref.get("record_id"), "linked audit run identifier")

    artifacts: list[dict[str, Any]] = []
    identities: list[dict[str, Any]] = []
    artifact_by_role: dict[str, dict[str, Any]] = {}
    raw_paths: tuple[tuple[str, Path, str, str], ...] = (
        ("stdout", attempt_root / "stdout.log", "project workflow retained stdout", "log"),
        ("stderr", attempt_root / "stderr.log", "project workflow retained stderr", "log"),
        (
            "controller_events",
            attempt_root / "controller-events.json",
            "authorized execution controller events",
            "log",
        ),
        (
            "attempt_evidence",
            evidence_path,
            "terminal authorized execution attempt evidence",
            "log",
        ),
        (
            "source_semantic_lock",
            registry_root / "source-semantic.lock.json",
            "exact registered source semantic lock",
            "log",
        ),
        (
            "consumption_receipt",
            registry_root / "consumption-receipt.json",
            "single-use authorization consumption receipt",
            "log",
        ),
        (
            "consumption_terminal",
            registry_root / "consumption-terminal.json",
            "terminal authorization consumption disposition",
            "log",
        ),
    )
    base_limitation = (
        "Captured bytes are untrusted execution evidence and do not establish scientific correctness.",
    )
    log_projection = _mapping(raw_evidence.get("logs"), "execution log projection")
    for role, path, observed_role, kind in raw_paths:
        role_limitations = list(base_limitation)
        projection = log_projection.get(role)
        if isinstance(projection, dict) and projection.get("truncated") is True:
            role_limitations.append("The retained log is truncated at the controller byte limit.")
        artifact, identity = _artifact_with_identity(
            audit_run_id=audit_run_id,
            linked_root=linked_output_root,
            logical_name=role,
            observed_role=observed_role,
            kind=kind,
            created_at=finished_at,
            path=path,
            limitations=tuple(role_limitations),
        )
        artifacts.append(artifact)
        identities.append(identity)
        artifact_by_role[role] = artifact

    output_manifest_value = raw_evidence.get("output_manifest")
    output_manifest_path = attempt_root / "output-manifest.json"
    accepted_outputs: list[tuple[str, Path]] = []
    if isinstance(output_manifest_value, dict):
        manifest_file, _manifest_payload = _read_canonical_object(
            output_manifest_path, "accepted output manifest"
        )
        if manifest_file != output_manifest_value:
            raise ValueError("attempt evidence and accepted output manifest disagree")
        accepted_output_root = linked_output_root / "accepted-output"
        accepted_outputs = _validate_output_manifest(
            linked_output_root, output_manifest_value, accepted_output_root
        )
        manifest_artifact, manifest_identity = _artifact_with_identity(
            audit_run_id=audit_run_id,
            linked_root=linked_output_root,
            logical_name="output_manifest",
            observed_role="accepted project output manifest",
            kind="result_file",
            created_at=finished_at,
            path=output_manifest_path,
            limitations=base_limitation,
        )
    elif output_manifest_value is None:
        manifest_artifact, manifest_identity = _artifact_with_identity(
            audit_run_id=audit_run_id,
            linked_root=linked_output_root,
            logical_name="output_manifest",
            observed_role="accepted project output manifest unavailable",
            kind="unknown",
            created_at=finished_at,
            path=None,
            limitations=(
                *base_limitation,
                "No accepted output manifest was produced for this attempt.",
            ),
            unavailable_reason="No accepted output manifest was produced for this attempt.",
        )
    else:
        raise ValueError("attempt output manifest projection is malformed")
    artifacts.append(manifest_artifact)
    identities.append(manifest_identity)
    artifact_by_role["output_manifest"] = manifest_artifact

    output_refs: list[dict[str, str]] = []
    for relative, path in accepted_outputs:
        artifact, identity = _artifact_with_identity(
            audit_run_id=audit_run_id,
            linked_root=linked_output_root,
            logical_name=f"accepted_output:{relative}",
            observed_role=f"accepted project output {relative}",
            kind="result_file",
            created_at=finished_at,
            path=path,
            limitations=(
                "Project-produced bytes are untrusted evidence and do not establish scientific correctness or semantic validity.",
            ),
        )
        artifacts.append(artifact)
        identities.append(identity)
        output_refs.append(typed_ref("artifact", str(artifact["artifact_id"])))

    environment = _environment_record(capability, authorization, finished_at)
    command = _mapping(authorization.get("command"), "authorized command")
    image = _mapping(authorization.get("image"), "authorized image")
    authorized_environment = _mapping(authorization.get("environment"), "authorized environment")
    limits = _mapping(authorization.get("limits"), "authorized limits")
    argv = command.get("argv")
    if not isinstance(argv, list) or not all(isinstance(value, str) for value in argv):
        raise ValueError("authorized command argv is malformed")
    raw_limitations = raw_evidence.get("limitations")
    if not isinstance(raw_limitations, list) or not all(
        isinstance(value, str) and value for value in raw_limitations
    ):
        raise ValueError("attempt evidence limitations are malformed")
    execution_limitations = sorted(
        {
            *raw_limitations,
            "A successful process exit or captured output does not establish scientific correctness, claim validity, or absence of issues.",
            "The linked execution record proves only the bounded authorization and observed controller evidence represented here.",
        }
    )
    execution_id = stable_id("execution-project", audit_run_id, attempt_id)
    execution: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "execution",
        "execution_id": execution_id,
        "audit_run_id": audit_run_id,
        "execution_kind": "project_workflow",
        "actor": "project_workflow",
        "method": "authorized_rootless_oci_execution",
        "command": {
            "display": shlex.join(tuple(argv)),
            "normalized_digest": command["normalized_digest"],
        },
        "input_refs": deepcopy(scope["declared_input_refs"]),
        "output_refs": output_refs,
        "environment_ref": typed_ref("environment", str(environment["environment_id"])),
        "timing": {"state": "observed", "started_at": started_at, "finished_at": finished_at},
        "exit": _exit_projection(
            disposition, raw_evidence.get("observed_exit_code"), raw_evidence.get("timed_out")
        ),
        "sandbox": {
            "project_code_executed": True,
            "authorization_status": "authorized",
            "network_policy": "denied",
            "sandbox_capability_ref": deepcopy(
                _mapping(scope.get("capability"), "authorization capability binding")["record_ref"]
            ),
        },
        "identity_strength": "exact",
        "source_refs": [
            {
                "source_kind": "runtime_command",
                "locator": f"authorized attempt {attempt_id}",
                "content_digest": sha256_digest(evidence_payload),
            }
        ],
        "limitations": execution_limitations,
        "provenance": _runtime_provenance("authorized_rootless_oci_execution", finished_at),
        "authorization_evidence_status": "complete",
        "project_execution": {
            "authorization_ref": typed_ref(
                "project_execution_authorization", str(authorization["authorization_id"])
            ),
            "authorization_semantic_digest": authorization_digest,
            "consumption": {
                "receipt_digest": receipt["receipt_digest"],
                "attempt_id": attempt_id,
                "disposition": _consumption_disposition(disposition),
            },
            "source_semantic_lock_digest": scope["source_semantic_lock_digest"],
            "work_item_ref": deepcopy(work_item_ref),
            "purpose": scope["purpose"],
            "image": deepcopy(image),
            "command": deepcopy(command),
            "effective_policy": {
                "network_policy": "denied",
                "limits": deepcopy(limits),
                "environment": deepcopy(authorized_environment),
            },
            "log_refs": {
                role: typed_ref("artifact", str(artifact_by_role[role]["artifact_id"]))
                for role in ("stdout", "stderr", "controller_events", "output_manifest")
            },
            "observed_resources": deepcopy(raw_evidence["observed_resources"]),
            "cleanup_state": _cleanup_state(disposition, raw_evidence.get("cleanup_observed")),
        },
    }
    audit_run = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "audit_run",
        "audit_run_id": audit_run_id,
        "state": "complete",
        "created_at": started_at,
        "parent_run_ref": deepcopy(source_run_ref),
        "snapshot_ref": deepcopy(snapshot_ref),
        "provenance": controller_provenance("linked_project_execution_evidence_run", finished_at),
    }

    lock_without_digest: dict[str, Any] = {
        "lock_kind": _LOCK_KIND,
        "lock_version": SCHEMA_VERSION,
        "audit_run_id": audit_run_id,
        "source_audit_run_id": source_run_ref["record_id"],
        "source_semantic_lock_digest": scope["source_semantic_lock_digest"],
        "source_work_item_ref": deepcopy(work_item_ref),
        "source_work_item_semantic_digest": scope["work_item_semantic_digest"],
        "source_snapshot_ref": deepcopy(snapshot_ref),
        "source_snapshot_semantic_digest": snapshot["semantic_digest"],
        "locked_at": finished_at,
        "model_calls": [],
        "model_access_after_lock": False,
        "raw_attempt_evidence_digest": sha256_digest(evidence_payload),
        "consumption_terminal_digest": terminal["terminal_digest"],
        "asset_identities": identities,
        "artifacts": artifacts,
        "audit_runs": [audit_run],
        "environments": [environment],
        "executions": [execution],
        "project_execution_authorizations": [authorization],
        "sandbox_capabilities": [deepcopy(capability)],
    }
    lock = {**lock_without_digest, "semantic_lock_digest": semantic_digest(lock_without_digest)}
    return _write_outputs(lock, linked_output_root, schema_root, source_root=None)


def replay_linked_execution(lock_path: Path, output: Path, schema_root: Path) -> dict[str, Any]:
    """Replay a linked evidence lock by verifying and copying bytes, never by executing code."""

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"replay output already exists: {output}")
    lock, _payload = _read_canonical_object(lock_path, "linked execution semantic lock")
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    publication = _write_outputs(lock, output, schema_root, source_root=lock_path.parent)
    return publication.bundle
