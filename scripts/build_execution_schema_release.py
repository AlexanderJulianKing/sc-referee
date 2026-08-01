from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reference" / "schemas-v0.12.0"
BASELINE_VERSION = "0.12.0"
RELEASE_VERSION = "0.13.0"
SOURCE_ADRS = ["docs/implementation/ADR-0013-AUTHORIZED-ROOTLESS-OCI-EXECUTION.md"]


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _replace_version(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}").replace(
            BASELINE_VERSION, RELEASE_VERSION
        )
    if isinstance(value, list):
        return [_replace_version(item) for item in value]
    if isinstance(value, dict):
        return {key: _replace_version(item) for key, item in value.items()}
    return value


def _require_empty_destination(output: Path) -> None:
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Release output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)


def _common_ref(name: str) -> dict[str, str]:
    return {
        "$ref": (
            f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
            f"common.schema.json#/$defs/{name}"
        )
    }


def _typed_ref(record_type: str) -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "record_id": _common_ref("Identifier"),
            "record_type": {"const": record_type},
        },
        "required": ["record_type", "record_id"],
        "type": "object",
    }


def _bound_ref(record_type: str) -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "record_ref": _typed_ref(record_type),
            "semantic_digest": _common_ref("Digest"),
        },
        "required": ["record_ref", "semantic_digest"],
        "type": "object",
    }


def _positive_integer() -> dict[str, Any]:
    return {"minimum": 1, "type": "integer"}


def _limit_schema() -> dict[str, Any]:
    properties = {
        "cpu_quota_millis": _positive_integer(),
        "memory_bytes": _positive_integer(),
        "open_files": _positive_integer(),
        "process_count": _positive_integer(),
        "wall_time_seconds": _positive_integer(),
        "writable_bytes": _positive_integer(),
    }
    return {
        "additionalProperties": False,
        "properties": properties,
        "required": sorted(properties),
        "type": "object",
    }


def _environment_allowlist_schema() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "entries": {
                "items": {
                    "additionalProperties": False,
                    "properties": {
                        "name": {
                            "maxLength": 128,
                            "pattern": "^[A-Za-z_][A-Za-z0-9_]*$",
                            "type": "string",
                        },
                        "value": {"maxLength": 4096, "type": "string"},
                    },
                    "required": ["name", "value"],
                    "type": "object",
                },
                "maxItems": 64,
                "type": "array",
                "uniqueItems": True,
            },
            "normalized_digest": _common_ref("Digest"),
        },
        "required": ["entries", "normalized_digest"],
        "type": "object",
    }


def _image_schema() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "manifest_digest": _common_ref("Digest"),
            "reference": {
                "maxLength": 2048,
                "pattern": "^.+@sha256:[a-f0-9]{64}$",
                "type": "string",
            },
        },
        "required": ["reference", "manifest_digest"],
        "type": "object",
    }


def _authorization_schema() -> dict[str, Any]:
    relative_path = {
        "maxLength": 4096,
        "minLength": 1,
        "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))(?!.*[*?\\[\\]{}])[^\\u0000]+$",
        "type": "string",
    }
    acknowledgements = {
        "additionalProperties": False,
        "properties": {
            "network_denied": {"const": True},
            "no_host_or_hpc_escalation": {"const": True},
            "output_confined_to_audit_root": {"const": True},
            "project_code_is_untrusted": {"const": True},
            "project_code_will_execute": {"const": True},
        },
        "required": [
            "project_code_will_execute",
            "project_code_is_untrusted",
            "output_confined_to_audit_root",
            "network_denied",
            "no_host_or_hpc_escalation",
        ],
        "type": "object",
    }
    registry_binding = {
        "additionalProperties": False,
        "properties": {
            "linked_output_root_id": _common_ref("Identifier"),
            "registry_id": _common_ref("Identifier"),
        },
        "required": ["registry_id", "linked_output_root_id"],
        "type": "object",
    }
    scope = {
        "additionalProperties": False,
        "properties": {
            "allowed_output_paths": {
                "items": relative_path,
                "maxItems": 256,
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "capability": _bound_ref("sandbox_capability"),
            "declared_input_refs": {
                "items": _common_ref("RecordRef"),
                "maxItems": 256,
                "type": "array",
                "uniqueItems": True,
            },
            "linked_audit_run_ref": _typed_ref("audit_run"),
            "snapshot": _bound_ref("repository_snapshot"),
            "source_audit_run_ref": _typed_ref("audit_run"),
            "source_semantic_lock_digest": _common_ref("Digest"),
            "work_item_ref": _typed_ref("work_item"),
        },
        "required": [
            "source_audit_run_ref",
            "source_semantic_lock_digest",
            "linked_audit_run_ref",
            "work_item_ref",
            "snapshot",
            "capability",
            "declared_input_refs",
            "allowed_output_paths",
        ],
        "type": "object",
    }
    return {
        "$id": (
            f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
            "project-execution-authorization.schema.json"
        ),
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "acknowledgements": acknowledgements,
            "authorization_id": _common_ref("Identifier"),
            "authorizing_actor": _common_ref("Actor"),
            "command": {
                "additionalProperties": False,
                "properties": {
                    "argv": {
                        "items": {"maxLength": 4096, "minLength": 1, "type": "string"},
                        "maxItems": 128,
                        "minItems": 1,
                        "type": "array",
                    },
                    "normalized_digest": _common_ref("Digest"),
                },
                "required": ["argv", "normalized_digest"],
                "type": "object",
            },
            "environment": _environment_allowlist_schema(),
            "expires_at": _common_ref("Timestamp"),
            "identity_assurance": {"const": "declared_local_user"},
            "image": _image_schema(),
            "limitations": {
                "items": {"minLength": 1, "type": "string"},
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "limits": _limit_schema(),
            "network_policy": {"const": "denied"},
            "provenance": _common_ref("Provenance"),
            "record_type": {"const": "project_execution_authorization"},
            "registry_binding": registry_binding,
            "schema_version": _common_ref("SchemaVersion"),
            "scope": scope,
            "single_use_nonce": {
                "maxLength": 256,
                "minLength": 16,
                "pattern": "^[A-Za-z0-9._:-]+$",
                "type": "string",
            },
        },
        "required": [
            "schema_version",
            "record_type",
            "authorization_id",
            "scope",
            "image",
            "command",
            "environment",
            "network_policy",
            "limits",
            "expires_at",
            "single_use_nonce",
            "authorizing_actor",
            "identity_assurance",
            "acknowledgements",
            "registry_binding",
            "limitations",
            "provenance",
        ],
        "title": "sc-referee Project Execution Authorization",
        "type": "object",
    }


def _effective_controls_schema() -> dict[str, Any]:
    names = (
        "capabilities_dropped",
        "cpu_limit_enforced",
        "device_access_restricted",
        "memory_limit_enforced",
        "network_denied",
        "no_new_privileges",
        "open_file_limit_enforced",
        "process_limit_enforced",
        "repository_read_only",
        "separate_writable_root",
        "wall_time_enforced",
        "writable_bytes_enforced",
    )
    return {
        "additionalProperties": False,
        "properties": {name: {"const": True} for name in names},
        "required": list(names),
        "type": "object",
    }


def _capability_evidence_schema() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "backend": {
                "additionalProperties": False,
                "properties": {
                    "backend_kind": {"enum": ["podman_rootless", "docker_rootless"]},
                    "executable_digest": _common_ref("Digest"),
                    "executable_path": {"minLength": 1, "type": "string"},
                    "version": {"minLength": 1, "type": "string"},
                },
                "required": ["backend_kind", "executable_path", "executable_digest", "version"],
                "type": "object",
            },
            "captured_at": _common_ref("Timestamp"),
            "effective_controls": _effective_controls_schema(),
            "endpoint": {
                "additionalProperties": False,
                "properties": {
                    "arbitrary_remote": {"const": False},
                    "connection_id": _common_ref("Identifier"),
                    "machine_id": {
                        "oneOf": [_common_ref("Identifier"), {"type": "null"}],
                    },
                    "service_id": _common_ref("Identifier"),
                    "transport": {"enum": ["local_unix_socket", "podman_managed_machine"]},
                },
                "required": [
                    "transport",
                    "connection_id",
                    "service_id",
                    "machine_id",
                    "arbitrary_remote",
                ],
                "type": "object",
            },
            "expires_at": _common_ref("Timestamp"),
            "host_platform": {
                "additionalProperties": False,
                "properties": {
                    "machine": {"minLength": 1, "type": "string"},
                    "release": {"minLength": 1, "type": "string"},
                    "system": {"minLength": 1, "type": "string"},
                },
                "required": ["system", "release", "machine"],
                "type": "object",
            },
            "normalized_info_digest": _common_ref("Digest"),
            "oci_runtime": {
                "additionalProperties": False,
                "properties": {
                    "name": {"minLength": 1, "type": "string"},
                    "version": {"minLength": 1, "type": "string"},
                },
                "required": ["name", "version"],
                "type": "object",
            },
            "probe_artifact_digest": _common_ref("Digest"),
            "probe_log_refs": {
                "items": _typed_ref("artifact"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "probe_outcome": {"const": "passed"},
            "probe_profile": {"const": "rootless-oci-capability-probe-v1"},
            "tested_limits": _limit_schema(),
        },
        "required": [
            "probe_profile",
            "probe_outcome",
            "backend",
            "endpoint",
            "normalized_info_digest",
            "probe_log_refs",
            "probe_artifact_digest",
            "effective_controls",
            "tested_limits",
            "host_platform",
            "oci_runtime",
            "captured_at",
            "expires_at",
        ],
        "type": "object",
    }


def _extend_sandbox_capability(schema: dict[str, Any]) -> None:
    properties = schema["properties"]
    controls = properties["controls"]
    for name in (
        "no_new_privileges",
        "open_file_limits_enforced",
        "wall_time_enforced",
        "writable_bytes_enforced",
    ):
        controls["properties"][name] = {"type": "boolean"}
        controls["required"].append(name)
    properties["capability_evidence_status"] = {
        "enum": [
            "complete_effective_probe",
            "not_supported",
            "legacy_probe_projection_unavailable",
        ]
    }
    properties["capability_evidence"] = {"oneOf": [_capability_evidence_schema(), {"type": "null"}]}
    schema["required"].extend(
        ["rootless_verified", "capability_evidence_status", "capability_evidence"]
    )
    schema["allOf"].extend(
        [
            {
                "if": {
                    "properties": {"project_code_execution_supported": {"const": True}},
                    "required": ["project_code_execution_supported"],
                },
                "then": {
                    "properties": {
                        "backend_kind": {"const": "rootless_oci"},
                        "capability_evidence": _capability_evidence_schema(),
                        "capability_evidence_status": {"const": "complete_effective_probe"},
                        "controls": {
                            "properties": {
                                "no_new_privileges": {"const": True},
                                "open_file_limits_enforced": {"const": True},
                                "wall_time_enforced": {"const": True},
                                "writable_bytes_enforced": {"const": True},
                            }
                        },
                        "rootless_verified": {"const": True},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "capability_evidence_status": {
                            "enum": ["not_supported", "legacy_probe_projection_unavailable"]
                        }
                    },
                    "required": ["capability_evidence_status"],
                },
                "then": {
                    "properties": {
                        "capability_evidence": {"type": "null"},
                        "project_code_execution_supported": {"const": False},
                        "rootless_verified": {"const": False},
                    }
                },
            },
        ]
    )


def _project_execution_schema() -> dict[str, Any]:
    nullable_number = {"oneOf": [{"minimum": 0, "type": "number"}, {"type": "null"}]}
    nullable_integer = {"oneOf": [{"minimum": 0, "type": "integer"}, {"type": "null"}]}
    return {
        "additionalProperties": False,
        "properties": {
            "authorization_ref": _typed_ref("project_execution_authorization"),
            "authorization_semantic_digest": _common_ref("Digest"),
            "cleanup_state": {"enum": ["succeeded", "failed", "unavailable"]},
            "command": {
                "additionalProperties": False,
                "properties": {
                    "argv": {
                        "items": {"maxLength": 4096, "minLength": 1, "type": "string"},
                        "maxItems": 128,
                        "minItems": 1,
                        "type": "array",
                    },
                    "normalized_digest": _common_ref("Digest"),
                },
                "required": ["argv", "normalized_digest"],
                "type": "object",
            },
            "consumption": {
                "additionalProperties": False,
                "properties": {
                    "attempt_id": _common_ref("Identifier"),
                    "disposition": {"enum": ["completed", "failed", "failed_unknown"]},
                    "receipt_digest": _common_ref("Digest"),
                },
                "required": ["receipt_digest", "attempt_id", "disposition"],
                "type": "object",
            },
            "effective_policy": {
                "additionalProperties": False,
                "properties": {
                    "environment": _environment_allowlist_schema(),
                    "limits": _limit_schema(),
                    "network_policy": {"const": "denied"},
                },
                "required": ["network_policy", "limits", "environment"],
                "type": "object",
            },
            "image": _image_schema(),
            "log_refs": {
                "additionalProperties": False,
                "properties": {
                    "controller_events": _typed_ref("artifact"),
                    "output_manifest": _typed_ref("artifact"),
                    "stderr": _typed_ref("artifact"),
                    "stdout": _typed_ref("artifact"),
                },
                "required": ["stdout", "stderr", "controller_events", "output_manifest"],
                "type": "object",
            },
            "observed_resources": {
                "additionalProperties": False,
                "properties": {
                    "cpu_time_seconds": nullable_number,
                    "open_files_peak": nullable_integer,
                    "peak_memory_bytes": nullable_integer,
                    "process_count_peak": nullable_integer,
                    "written_bytes": nullable_integer,
                },
                "required": [
                    "cpu_time_seconds",
                    "peak_memory_bytes",
                    "process_count_peak",
                    "open_files_peak",
                    "written_bytes",
                ],
                "type": "object",
            },
            "purpose": {"maxLength": 1024, "minLength": 1, "type": "string"},
            "source_semantic_lock_digest": _common_ref("Digest"),
            "work_item_ref": _typed_ref("work_item"),
        },
        "required": [
            "authorization_ref",
            "authorization_semantic_digest",
            "consumption",
            "source_semantic_lock_digest",
            "work_item_ref",
            "purpose",
            "image",
            "command",
            "effective_policy",
            "log_refs",
            "observed_resources",
            "cleanup_state",
        ],
        "type": "object",
    }


def _extend_execution(schema: dict[str, Any]) -> None:
    schema.setdefault("$defs", {})["ProjectExecutionEvidence"] = _project_execution_schema()
    properties = schema["properties"]
    properties["authorization_evidence_status"] = {
        "enum": [
            "complete",
            "not_required",
            "imported",
            "legacy_authorization_projection_unavailable",
        ]
    }
    properties["project_execution"] = {
        "oneOf": [
            {"$ref": "#/$defs/ProjectExecutionEvidence"},
            {"type": "null"},
        ]
    }
    schema["required"].extend(["authorization_evidence_status", "project_execution"])
    schema["allOf"].extend(
        [
            {
                "if": {
                    "properties": {"execution_kind": {"const": "auditor_verification"}},
                    "required": ["execution_kind"],
                },
                "then": {
                    "properties": {
                        "authorization_evidence_status": {"const": "not_required"},
                        "project_execution": {"type": "null"},
                    }
                },
            },
            {
                "if": {
                    "properties": {"execution_kind": {"const": "imported"}},
                    "required": ["execution_kind"],
                },
                "then": {
                    "properties": {
                        "authorization_evidence_status": {"const": "imported"},
                        "project_execution": {"type": "null"},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "authorization_evidence_status": {"const": "complete"},
                        "execution_kind": {"const": "project_workflow"},
                    },
                    "required": ["execution_kind", "authorization_evidence_status"],
                },
                "then": {
                    "properties": {
                        "project_execution": {"$ref": "#/$defs/ProjectExecutionEvidence"}
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "authorization_evidence_status": {
                            "const": "legacy_authorization_projection_unavailable"
                        }
                    },
                    "required": ["authorization_evidence_status"],
                },
                "then": {"properties": {"project_execution": {"type": "null"}}},
            },
        ]
    )


def _extend_bundle(schema: dict[str, Any]) -> None:
    schema["properties"]["project_execution_authorizations"] = {
        "items": {
            "$ref": (
                f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                "project-execution-authorization.schema.json"
            )
        },
        "minItems": 0,
        "type": "array",
    }
    schema["required"].append("project_execution_authorizations")


def _extend_union(schema: dict[str, Any]) -> None:
    schema["oneOf"].append(
        {
            "$ref": (
                f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                "project-execution-authorization.schema.json"
            )
        }
    )


def _authorization_example() -> dict[str, Any]:
    return {
        "acknowledgements": {
            "network_denied": True,
            "no_host_or_hpc_escalation": True,
            "output_confined_to_audit_root": True,
            "project_code_is_untrusted": True,
            "project_code_will_execute": True,
        },
        "authorization_id": "authorization:example-once",
        "authorizing_actor": {
            "actor_id": "local-user:declared",
            "actor_kind": "human",
            "display_name": "Declared local user",
        },
        "command": {
            "argv": ["python", "/project/analysis.py", "--output", "/output/result.json"],
            "normalized_digest": "sha256:" + "1" * 64,
        },
        "environment": {
            "entries": [{"name": "PYTHONHASHSEED", "value": "0"}],
            "normalized_digest": "sha256:" + "2" * 64,
        },
        "expires_at": "2026-07-29T20:05:00Z",
        "identity_assurance": "declared_local_user",
        "image": {
            "manifest_digest": "sha256:" + "3" * 64,
            "reference": "localhost/sc-referee-python@sha256:" + "3" * 64,
        },
        "limitations": ["Local actor identity is declared and is not externally authenticated."],
        "limits": {
            "cpu_quota_millis": 1000,
            "memory_bytes": 268435456,
            "open_files": 64,
            "process_count": 32,
            "wall_time_seconds": 60,
            "writable_bytes": 1048576,
        },
        "network_policy": "denied",
        "provenance": {
            "actor": {"actor_id": "local-user:declared", "actor_kind": "human"},
            "created_at": "2026-07-29T20:00:00Z",
            "method": "interactive_fresh_challenge_authorization",
            "tool": "sc-referee",
            "tool_version": "0.3.0.dev0",
        },
        "record_type": "project_execution_authorization",
        "registry_binding": {
            "linked_output_root_id": "output-root:example-once",
            "registry_id": "authorization-registry:example-once",
        },
        "schema_version": RELEASE_VERSION,
        "scope": {
            "allowed_output_paths": ["result.json"],
            "capability": {
                "record_ref": {
                    "record_id": "sandbox:rootless-podman",
                    "record_type": "sandbox_capability",
                },
                "semantic_digest": "sha256:" + "4" * 64,
            },
            "declared_input_refs": [
                {"record_id": "snapshot:example", "record_type": "repository_snapshot"}
            ],
            "linked_audit_run_ref": {
                "record_id": "audit:linked-reproduction",
                "record_type": "audit_run",
            },
            "snapshot": {
                "record_ref": {
                    "record_id": "snapshot:example",
                    "record_type": "repository_snapshot",
                },
                "semantic_digest": "sha256:" + "5" * 64,
            },
            "source_audit_run_ref": {
                "record_id": "audit:source",
                "record_type": "audit_run",
            },
            "source_semantic_lock_digest": "sha256:" + "6" * 64,
            "work_item_ref": {
                "record_id": "work-item:execute-example",
                "record_type": "work_item",
            },
        },
        "single_use_nonce": "nonce:example-once-0001",
    }


def _upgrade_capability_example(value: dict[str, Any]) -> None:
    value["controls"].update(
        {
            "no_new_privileges": True,
            "open_file_limits_enforced": True,
            "wall_time_enforced": True,
            "writable_bytes_enforced": True,
        }
    )
    value["capability_evidence_status"] = "complete_effective_probe"
    value["capability_evidence"] = {
        "backend": {
            "backend_kind": "podman_rootless",
            "executable_digest": "sha256:" + "7" * 64,
            "executable_path": "/opt/homebrew/bin/podman",
            "version": "5.0",
        },
        "captured_at": value["captured_at"],
        "effective_controls": {
            "capabilities_dropped": True,
            "cpu_limit_enforced": True,
            "device_access_restricted": True,
            "memory_limit_enforced": True,
            "network_denied": True,
            "no_new_privileges": True,
            "open_file_limit_enforced": True,
            "process_limit_enforced": True,
            "repository_read_only": True,
            "separate_writable_root": True,
            "wall_time_enforced": True,
            "writable_bytes_enforced": True,
        },
        "endpoint": {
            "arbitrary_remote": False,
            "connection_id": "connection:podman-machine-default",
            "machine_id": "machine:podman-default",
            "service_id": "service:podman-rootless",
            "transport": "podman_managed_machine",
        },
        "expires_at": "2026-07-29T13:00:00Z",
        "host_platform": {"machine": "arm64", "release": "6.12", "system": "Linux"},
        "normalized_info_digest": "sha256:" + "8" * 64,
        "oci_runtime": {"name": "crun", "version": "1.17"},
        "probe_artifact_digest": "sha256:" + "9" * 64,
        "probe_log_refs": [{"record_id": "artifact:probe-log", "record_type": "artifact"}],
        "probe_outcome": "passed",
        "probe_profile": "rootless-oci-capability-probe-v1",
        "tested_limits": {
            "cpu_quota_millis": 1000,
            "memory_bytes": 268435456,
            "open_files": 64,
            "process_count": 32,
            "wall_time_seconds": 60,
            "writable_bytes": 1048576,
        },
    }


def _upgrade_nonproject_execution(value: dict[str, Any]) -> None:
    value["authorization_evidence_status"] = (
        "imported" if value.get("execution_kind") == "imported" else "not_required"
    )
    value["project_execution"] = None


def _project_execution_example(
    base: dict[str, Any], authorization: dict[str, Any]
) -> dict[str, Any]:
    value = dict(base)
    value.update(
        {
            "actor": "project_workflow",
            "audit_run_id": "audit:linked-reproduction",
            "authorization_evidence_status": "complete",
            "execution_id": "execution:project-example",
            "execution_kind": "project_workflow",
            "method": "authorized_rootless_oci_execution",
            "project_execution": {
                "authorization_ref": {
                    "record_id": authorization["authorization_id"],
                    "record_type": "project_execution_authorization",
                },
                "authorization_semantic_digest": "sha256:" + "a" * 64,
                "cleanup_state": "succeeded",
                "command": authorization["command"],
                "consumption": {
                    "attempt_id": "execution-attempt:example-once",
                    "disposition": "completed",
                    "receipt_digest": "sha256:" + "b" * 64,
                },
                "effective_policy": {
                    "environment": authorization["environment"],
                    "limits": authorization["limits"],
                    "network_policy": "denied",
                },
                "image": authorization["image"],
                "log_refs": {
                    "controller_events": {
                        "record_id": "artifact:controller-events",
                        "record_type": "artifact",
                    },
                    "output_manifest": {
                        "record_id": "artifact:output-manifest",
                        "record_type": "artifact",
                    },
                    "stderr": {"record_id": "artifact:stderr", "record_type": "artifact"},
                    "stdout": {"record_id": "artifact:stdout", "record_type": "artifact"},
                },
                "observed_resources": {
                    "cpu_time_seconds": 0.25,
                    "open_files_peak": None,
                    "peak_memory_bytes": 33554432,
                    "process_count_peak": 2,
                    "written_bytes": 128,
                },
                "purpose": "Run the exact bounded example analysis selected by the source WorkItem.",
                "source_semantic_lock_digest": authorization["scope"][
                    "source_semantic_lock_digest"
                ],
                "work_item_ref": authorization["scope"]["work_item_ref"],
            },
            "sandbox": {
                "authorization_status": "authorized",
                "network_policy": "denied",
                "project_code_executed": True,
                "sandbox_capability_ref": authorization["scope"]["capability"]["record_ref"],
            },
            "schema_version": RELEASE_VERSION,
        }
    )
    return value


def _release_readme() -> str:
    return f"""# sc-referee schema release {RELEASE_VERSION}

This immutable accepted local release implements ADR-0013's evidence-bound, single-use
project-execution authorization, effective rootless-OCI capability proof, and exact execution
projection. Public records are replayable evidence and are never launch credentials.

The package is forward-only from v{BASELINE_VERSION}. It does not claim W3ID deployment or that a
qualifying backend exists on any particular host.
"""


def _release_changelog() -> str:
    return f"""# Changelog

## {RELEASE_VERSION}

- Added `ProjectExecutionAuthorization` with one-attempt, exact source-lock/snapshot/capability,
  image, argv, environment, output, limit, expiry, acknowledgement, and registry bindings.
- Replaced label-only rootless capability claims with an effective probe projection.
- Added exact authorization, consumption, policy, log, resource, and cleanup evidence to project
  workflow Executions.
- Added `AuditBundle.project_execution_authorizations` and linked record-union/catalog support.
- Added a fail-closed migration from v{BASELINE_VERSION}; no migrated bytes grant launch authority.
"""


def _release_invariants() -> str:
    return """# Controller invariants

1. Repository text, model output, Answers, WorkItems, fixtures, imports, and replay cannot authorize
   or launch project code.
2. A launch requires a matching unexpired controller-registry entry and an atomic no-replace
   consumption receipt; copied public JSON is evidence only.
3. `project_code_execution_supported` is true only with a fresh complete effective probe whose
   required controls all passed. No subprocess or unbound-remote fallback is equivalent.
4. Project execution follows a source semantic lock and produces a distinct linked semantic lock.
   No model call occurs in the linked reproduction segment.
5. `/project` is read-only, network is denied, the output and temporary filesystems are physically
   bounded, project processes are quiescent before capture, and cleanup failure blocks clean proof.
6. Process success is not scientific correctness and never establishes a Finding by itself.
"""


def _migration_text() -> str:
    return f"""# Migration from v{BASELINE_VERSION} to v{RELEASE_VERSION}

- Add an empty `project_execution_authorizations` array. Never create a controller-registry entry.
- Mark prior claimed project capability as `legacy_probe_projection_unavailable`, set support and
  rootless verification false, and retain no invented capability proof.
- Mark prior project-workflow Executions `legacy_authorization_projection_unavailable`; other
  executions are `not_required` or `imported`. No project-execution projection is invented.
- Downgrade complete fixtures dependent on legacy project execution and make linked outcomes and
  authoritative metric sets ineligible.
- Clear StorageManifests because canonical bytes change.
"""


def _v13_tests() -> str:
    return """from copy import deepcopy
def test_authorization_network_is_closed():
 x=load("project-execution-authorization.example.json"); x["network_policy"]="allowed"; invalid(x,"project_execution_authorization")
def test_supported_capability_requires_probe():
 x=load("sandbox-capability.example.json"); x["capability_evidence"]=None; invalid(x,"sandbox_capability")
def test_project_execution_requires_exact_projection():
 x=load("execution.project-workflow.example.json"); x["project_execution"]=None; invalid(x,"execution")
def test_auditor_execution_cannot_claim_project_projection():
 x=load("execution.auditor-verification.example.json"); y=load("execution.project-workflow.example.json"); x["project_execution"]=deepcopy(y["project_execution"]); invalid(x,"execution")
def test_bundle_requires_authorization_collection():
 x=load("audit-bundle.example.json"); x.pop("project_execution_authorizations"); invalid(x,"audit_bundle")
"""


def write_manifest(output: Path) -> None:
    entries = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        if path.name == "MANIFEST.sha256" or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(output).as_posix()
        entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}")
    (output / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def build_release(output: Path) -> int:
    """Build accepted v0.13.0 without modifying immutable v0.12.0."""

    _require_empty_destination(output)
    baseline_schema_dir = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    for source in sorted(baseline_schema_dir.glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "audit-bundle.schema.json":
            _extend_bundle(schema)
        elif source.name == "execution.schema.json":
            _extend_execution(schema)
        elif source.name == "record-union.schema.json":
            _extend_union(schema)
        elif source.name == "sandbox-capability.schema.json":
            _extend_sandbox_capability(schema)
        _write_json(schema_output / source.name, schema)
    _write_json(
        schema_output / "project-execution-authorization.schema.json", _authorization_schema()
    )

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    catalog["schemas"].append(
        {
            "file": "project-execution-authorization.schema.json",
            "id": (
                f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                "project-execution-authorization.schema.json"
            ),
            "kind": "record",
            "name": "project_execution_authorization",
        }
    )
    catalog["schemas"] = sorted(catalog["schemas"], key=lambda item: str(item["name"]))
    _write_json(output / "schema-catalog.json", catalog)

    authorization = _authorization_example()
    auditor_example: dict[str, Any] | None = None
    example_count = 0
    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        if source.name == "audit-bundle.example.json":
            example["project_execution_authorizations"] = []
            for execution in example.get("executions", []):
                _upgrade_nonproject_execution(execution)
            for capability in example.get("sandbox_capabilities", []):
                capability["project_code_execution_supported"] = False
                capability["rootless_verified"] = False
                capability["capability_evidence_status"] = "legacy_probe_projection_unavailable"
                capability["capability_evidence"] = None
                capability["controls"].update(
                    {
                        "no_new_privileges": False,
                        "open_file_limits_enforced": False,
                        "wall_time_enforced": False,
                        "writable_bytes_enforced": False,
                    }
                )
        elif source.name == "execution.auditor-verification.example.json":
            _upgrade_nonproject_execution(example)
            auditor_example = example
        elif source.name == "sandbox-capability.example.json":
            _upgrade_capability_example(example)
        _write_json(output / "examples" / source.name, example)
        example_count += 1

    if auditor_example is None:
        raise ValueError("Baseline auditor Execution example is missing")
    _write_json(output / "examples" / "project-execution-authorization.example.json", authorization)
    _write_json(
        output / "examples" / "execution.project-workflow.example.json",
        _project_execution_example(auditor_example, authorization),
    )
    example_count += 2

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(_release_readme(), encoding="utf-8")
    (output / "CHANGELOG.md").write_text(_release_changelog(), encoding="utf-8")
    (output / "CONTROLLER_INVARIANTS.md").write_text(_release_invariants(), encoding="utf-8")
    (output / "MIGRATION_v0.12_to_v0.13.md").write_text(_migration_text(), encoding="utf-8")
    _write_json(
        output / "RELEASE_STATUS.json",
        {
            "accepted": True,
            "baseline_version": BASELINE_VERSION,
            "public_release": True,
            "release_version": RELEASE_VERSION,
            "source_adrs": SOURCE_ADRS,
        },
    )

    tests_output = output / "tests"
    tests_output.mkdir(parents=True, exist_ok=True)
    for source in sorted((BASELINE / "tests").glob("*.py")):
        source_text = source.read_text(encoding="utf-8").replace(
            f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}"
        )
        (tests_output / source.name).write_text(source_text, encoding="utf-8")
    (tests_output / "test_v013_invariants.py").write_text(_v13_tests(), encoding="utf-8")

    validator = (BASELINE / "tools" / "validate_records.py").read_text(encoding="utf-8")
    (output / "tools").mkdir(parents=True, exist_ok=True)
    (output / "tools" / "validate_records.py").write_text(
        validator.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}"), encoding="utf-8"
    )
    baseline_pyproject = (BASELINE / "pyproject.toml").read_text(encoding="utf-8")
    (output / "pyproject.toml").write_text(
        baseline_pyproject.replace(BASELINE_VERSION, RELEASE_VERSION), encoding="utf-8"
    )

    test_count = 0
    for test_path in tests_output.glob("*.py"):
        module = ast.parse(test_path.read_text(encoding="utf-8"))
        test_count += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in module.body
        )
    schema_count = len(catalog["schemas"])
    (output / "VALIDATION.txt").write_text(
        f"sc-referee schema package {RELEASE_VERSION} validation\n\n"
        f"JSON Schemas checked: {schema_count}\n"
        f"Cataloged schemas: {schema_count}\n"
        f"Example records validated: {example_count}\n"
        f"Invariant tests declared: {test_count}\n"
        "Canonical local references: all resolved\n"
        "JSON Schema meta-validation: passed\n",
        encoding="utf-8",
    )
    write_manifest(output)
    return example_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.13.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
