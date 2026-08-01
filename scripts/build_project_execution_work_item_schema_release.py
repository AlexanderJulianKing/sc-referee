from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reference" / "schemas-v0.13.0"
BASELINE_VERSION = "0.13.0"
RELEASE_VERSION = "0.14.0"
SOURCE_ADRS = ["docs/implementation/ADR-0014-TYPED-PROJECT-EXECUTION-WORK-ITEM.md"]


def write_manifest(output: Path) -> None:
    entries = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        if path.name == "MANIFEST.sha256" or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(output).as_posix()
        entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}")
    (output / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


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


def _relative_path() -> dict[str, Any]:
    return {
        "maxLength": 4096,
        "minLength": 1,
        "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))(?!.*[*?\\[\\]{}])[^\\u0000]+$",
        "type": "string",
    }


def _positive_integer() -> dict[str, Any]:
    return {"minimum": 1, "type": "integer"}


def _limits() -> dict[str, Any]:
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


def _environment() -> dict[str, Any]:
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


def _image() -> dict[str, Any]:
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


def _argv() -> dict[str, Any]:
    return {
        "items": {"maxLength": 4096, "minLength": 1, "type": "string"},
        "maxItems": 128,
        "minItems": 1,
        "type": "array",
    }


def _nullable(schema: dict[str, Any]) -> dict[str, Any]:
    return {"oneOf": [schema, {"type": "null"}]}


def _launch_envelope() -> dict[str, Any]:
    field_schemas = {
        "argv": _argv(),
        "environment": _environment(),
        "image": _image(),
        "limits": _limits(),
    }
    all_of: list[dict[str, Any]] = []
    for name, field_schema in field_schemas.items():
        all_of.append(
            {
                "if": {
                    "properties": {"unresolved_fields": {"contains": {"const": name}}},
                    "required": ["unresolved_fields"],
                },
                "then": {"properties": {name: {"type": "null"}}},
                "else": {"properties": {name: field_schema}},
            }
        )
    return {
        "additionalProperties": False,
        "allOf": all_of,
        "properties": {
            **{name: _nullable(schema) for name, schema in field_schemas.items()},
            "unresolved_fields": {
                "items": {"enum": sorted(field_schemas)},
                "maxItems": len(field_schemas),
                "type": "array",
                "uniqueItems": True,
            },
        },
        "required": [*sorted(field_schemas), "unresolved_fields"],
        "type": "object",
    }


def _execution_packet() -> dict[str, Any]:
    evidence_types = [
        "artifact",
        "asset_identity",
        "audit_run",
        "environment",
        "execution",
        "file_record",
        "project_execution_authorization",
        "sandbox_capability",
    ]
    return {
        "additionalProperties": False,
        "properties": {
            "allowed_output_paths": {
                "items": _relative_path(),
                "maxItems": 256,
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "declared_input_refs": {
                "items": _common_ref("RecordRef"),
                "maxItems": 256,
                "type": "array",
                "uniqueItems": True,
            },
            "launch_envelope": _launch_envelope(),
            "limitations": {
                "items": {"minLength": 1, "type": "string"},
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "packet_digest": _common_ref("Digest"),
            "packet_digest_profile": {"const": "canonical-json-excluding-packet-digest-v1"},
            "packet_kind": {"const": "project_execution_request_v1"},
            "packet_version": {"const": "1.0.0"},
            "policy": {
                "additionalProperties": False,
                "properties": {
                    "direct_interactive_authorization_required": {"const": True},
                    "host_or_hpc_escalation_allowed": {"const": False},
                    "launch_authorized": {"const": False},
                    "model_output_may_authorize_or_broaden": {"const": False},
                    "network_policy": {"const": "denied"},
                    "repository_text_may_authorize_or_broaden": {"const": False},
                    "scientist_output_may_authorize_or_broaden": {"const": False},
                },
                "required": [
                    "launch_authorized",
                    "direct_interactive_authorization_required",
                    "network_policy",
                    "repository_text_may_authorize_or_broaden",
                    "model_output_may_authorize_or_broaden",
                    "scientist_output_may_authorize_or_broaden",
                    "host_or_hpc_escalation_allowed",
                ],
                "type": "object",
            },
            "purpose": {"maxLength": 1024, "minLength": 1, "type": "string"},
            "required_output_record_types": {
                "items": {"enum": evidence_types},
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "source_snapshot": _bound_ref("repository_snapshot"),
            "target_refs": {
                "items": _common_ref("RecordRef"),
                "maxItems": 256,
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
        },
        "required": [
            "packet_kind",
            "packet_version",
            "packet_digest",
            "packet_digest_profile",
            "source_snapshot",
            "purpose",
            "target_refs",
            "declared_input_refs",
            "allowed_output_paths",
            "launch_envelope",
            "required_output_record_types",
            "limitations",
            "policy",
        ],
        "type": "object",
    }


def _extend_work_item(schema: dict[str, Any]) -> None:
    properties = schema["properties"]
    properties["kind"]["enum"].append("project_execution")
    properties["status"]["enum"].append("awaiting_authorization")
    semantic_packet = copy.deepcopy(properties["packet"])
    semantic_packet["properties"]["packet_kind"] = {"const": "semantic_or_auditor_work_v1"}
    semantic_packet["required"].insert(0, "packet_kind")
    properties["packet"] = {"oneOf": [semantic_packet, _execution_packet()]}
    schema["allOf"].extend(
        [
            {
                "if": {
                    "properties": {"kind": {"const": "project_execution"}},
                    "required": ["kind"],
                },
                "then": {
                    "properties": {
                        "packet": {
                            "properties": {
                                "packet_kind": {"const": "project_execution_request_v1"}
                            },
                            "required": ["packet_kind"],
                        },
                        "scheduling": {
                            "properties": {
                                "execution_privilege": {"const": "project_code_execution"}
                            }
                        },
                        "status": {"const": "awaiting_authorization"},
                    }
                },
                "else": {
                    "properties": {
                        "packet": {
                            "properties": {"packet_kind": {"const": "semantic_or_auditor_work_v1"}},
                            "required": ["packet_kind"],
                        },
                        "scheduling": {
                            "properties": {
                                "execution_privilege": {"not": {"const": "project_code_execution"}}
                            }
                        },
                        "status": {"not": {"const": "awaiting_authorization"}},
                    }
                },
            }
        ]
    )


def _extend_authorization(schema: dict[str, Any]) -> None:
    scope = schema["properties"]["scope"]
    scope["properties"]["purpose"] = {
        "oneOf": [
            {"maxLength": 1024, "minLength": 1, "type": "string"},
            {"type": "null"},
        ]
    }
    scope["properties"]["target_refs"] = {
        "oneOf": [
            {
                "items": _common_ref("RecordRef"),
                "maxItems": 256,
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            {"type": "null"},
        ]
    }
    scope["properties"]["work_item_binding_status"] = {
        "enum": [
            "complete_project_execution_work_item",
            "legacy_work_item_semantics_unavailable",
        ]
    }
    scope["properties"]["work_item_semantic_digest"] = {
        "oneOf": [_common_ref("Digest"), {"type": "null"}]
    }
    scope["required"].extend(
        [
            "purpose",
            "target_refs",
            "work_item_binding_status",
            "work_item_semantic_digest",
        ]
    )
    scope["allOf"] = [
        {
            "if": {
                "properties": {
                    "work_item_binding_status": {"const": "complete_project_execution_work_item"}
                },
                "required": ["work_item_binding_status"],
            },
            "then": {
                "properties": {
                    "purpose": {"maxLength": 1024, "minLength": 1, "type": "string"},
                    "target_refs": {
                        "items": _common_ref("RecordRef"),
                        "maxItems": 256,
                        "minItems": 1,
                        "type": "array",
                        "uniqueItems": True,
                    },
                    "work_item_semantic_digest": _common_ref("Digest"),
                }
            },
            "else": {
                "properties": {
                    "purpose": {"type": "null"},
                    "target_refs": {"type": "null"},
                    "work_item_semantic_digest": {"type": "null"},
                }
            },
        }
    ]


def _refresh_packet_digest(packet: dict[str, Any]) -> None:
    packet.pop("packet_digest", None)
    packet["packet_digest"] = semantic_digest(packet)


def _project_work_item(base: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    snapshot_ref = {
        "record_id": snapshot["snapshot_id"],
        "record_type": "repository_snapshot",
    }
    target_ref = copy.deepcopy(snapshot_ref)
    environment_entries = [{"name": "PYTHONHASHSEED", "value": "0"}]
    packet: dict[str, Any] = {
        "allowed_output_paths": ["result.json"],
        "declared_input_refs": [snapshot_ref],
        "launch_envelope": {
            "argv": ["python", "/project/analysis.py", "--output", "/output/result.json"],
            "environment": {
                "entries": environment_entries,
                "normalized_digest": semantic_digest(environment_entries),
            },
            "image": {
                "manifest_digest": "sha256:" + "3" * 64,
                "reference": "localhost/sc-referee-python@sha256:" + "3" * 64,
            },
            "limits": {
                "cpu_quota_millis": 1000,
                "memory_bytes": 268435456,
                "open_files": 64,
                "process_count": 32,
                "wall_time_seconds": 60,
                "writable_bytes": 1048576,
            },
            "unresolved_fields": [],
        },
        "limitations": [
            "This locked request does not authorize execution; a fresh direct challenge is still required."
        ],
        "packet_digest_profile": "canonical-json-excluding-packet-digest-v1",
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
        "purpose": "Run the exact bounded example analysis selected before semantic lock.",
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
            "record_ref": snapshot_ref,
            "semantic_digest": semantic_digest(snapshot),
        },
        "target_refs": [target_ref],
    }
    _refresh_packet_digest(packet)
    value = copy.deepcopy(base)
    value.update(
        {
            "audit_run_id": snapshot["audit_run_id"],
            "dependency_work_item_refs": [],
            "kind": "project_execution",
            "material_question_refs": [],
            "output_refs": [],
            "packet": packet,
            "scheduling": {
                "cache_status": "not_cacheable",
                "claim_materiality": "unknown",
                "component_maturity": "experimental",
                "downstream_reach": 1,
                "estimated_elapsed_seconds": 60,
                "execution_privilege": "project_code_execution",
                "expected_information_gain": "unknown",
            },
            "schema_version": RELEASE_VERSION,
            "status": "awaiting_authorization",
            "target_refs": [target_ref],
            "work_item_id": "work-item:execute-example",
        }
    )
    value.pop("completed_at", None)
    return value


def _release_readme() -> str:
    return f"""# sc-referee schema release {RELEASE_VERSION}

This immutable accepted local release implements ADR-0014's typed, non-model
`project_execution` WorkItem request and exact authorization binding. A locked request is not
authority: a fresh direct single-use authorization and qualifying rootless OCI capability remain
mandatory before any launch.

The package is forward-only from v{BASELINE_VERSION}. It does not claim W3ID deployment, public
backend availability, or authorization of any particular workflow.
"""


def _release_changelog() -> str:
    return f"""# Changelog

## {RELEASE_VERSION}

- Added the closed `project_execution_request_v1` WorkItem packet and
  `awaiting_authorization` state.
- Kept semantic/model packets closed as `semantic_or_auditor_work_v1`.
- Bound authorization evidence to the exact WorkItem semantic digest and an explicit binding
  status.
- Added a fail-closed migration from v{BASELINE_VERSION}; no request, digest, registry entry,
  launch authority, qualifying execution, fixture proof, or metric is invented.
"""


def _release_invariants() -> str:
    return """# Controller invariants

1. A project-execution WorkItem is a locked request, never authority to launch.
2. Project requests are controller packets and are never submitted to a model.
3. Repository text, model output, scientist output, imported records, and replay cannot authorize
   or broaden a request.
4. The authorization controller verifies the exact source run, source lock, WorkItem digest,
   snapshot, targets, inputs, output paths, purpose, network policy, and proposed launch bounds
   before displaying a fresh challenge.
5. Only `complete_project_execution_work_item` can enter the private registry; migrated legacy
   evidence remains non-launchable.
6. Source semantic-lock bytes remain immutable. Execution evidence belongs to a linked run.
"""


def _migration_text() -> str:
    return f"""# Migration from v{BASELINE_VERSION} to v{RELEASE_VERSION}

- Mark existing WorkItem packets `semantic_or_auditor_work_v1` and recompute their packet digest.
- Create no project-execution WorkItem and no private controller state.
- Mark existing ProjectExecutionAuthorization evidence
  `legacy_work_item_semantics_unavailable` and set its WorkItem digest to null.
- Demote project-workflow Executions depending on legacy authorization to unavailable projection.
- Downgrade dependent fixtures and remove authoritative metrics.
- Clear StorageManifests because canonical bytes change.
"""


def _v14_tests() -> str:
    return """from copy import deepcopy
def test_project_work_item_is_closed_non_authority():
 x=load("work-item.project-execution.example.json"); x["packet"]["policy"]["launch_authorized"]=True; invalid(x,"work_item")
def test_project_packet_has_no_prompt_identity():
 x=load("work-item.project-execution.example.json"); x["packet"]["prompt_template_id"]="prompt:invented"; invalid(x,"work_item")
def test_semantic_packet_cannot_be_project_request():
 x=load("work-item.ready.example.json"); y=load("work-item.project-execution.example.json"); x["packet"]=deepcopy(y["packet"]); invalid(x,"work_item")
def test_complete_authorization_requires_work_item_digest():
 x=load("project-execution-authorization.example.json"); x["scope"]["work_item_semantic_digest"]=None; invalid(x,"project_execution_authorization")
"""


def build_release(output: Path) -> int:
    """Build accepted v0.14.0 without modifying immutable v0.13.0."""

    _require_empty_destination(output)
    baseline_schema_dir = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    for source in sorted(baseline_schema_dir.glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "work-item.schema.json":
            _extend_work_item(schema)
        elif source.name == "project-execution-authorization.schema.json":
            _extend_authorization(schema)
        _write_json(schema_output / source.name, schema)

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    _write_json(output / "schema-catalog.json", catalog)

    base_work_item: dict[str, Any] | None = None
    authorization: dict[str, Any] | None = None
    capability: dict[str, Any] | None = None
    project_execution: dict[str, Any] | None = None
    snapshot: dict[str, Any] | None = None
    example_count = 0
    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        if example.get("record_type") == "work_item":
            example["packet"]["packet_kind"] = "semantic_or_auditor_work_v1"
            _refresh_packet_digest(example["packet"])
            if source.name == "work-item.ready.example.json":
                base_work_item = copy.deepcopy(example)
        elif source.name == "project-execution-authorization.example.json":
            authorization = example
        elif source.name == "execution.project-workflow.example.json":
            project_execution = example
        elif source.name == "repository-snapshot.example.json":
            snapshot = example
        elif source.name == "sandbox-capability.example.json":
            capability = example
        _write_json(output / "examples" / source.name, example)
        example_count += 1

    if any(
        value is None
        for value in (base_work_item, authorization, capability, project_execution, snapshot)
    ):
        raise ValueError("Baseline project-execution examples are incomplete")
    assert base_work_item is not None
    assert authorization is not None
    assert capability is not None
    assert project_execution is not None
    assert snapshot is not None
    project_work_item = _project_work_item(base_work_item, snapshot)
    launch = project_work_item["packet"]["launch_envelope"]
    authorization["command"] = {
        "argv": copy.deepcopy(launch["argv"]),
        "normalized_digest": semantic_digest(launch["argv"]),
    }
    authorization["environment"] = copy.deepcopy(launch["environment"])
    authorization["image"] = copy.deepcopy(launch["image"])
    authorization["limits"] = copy.deepcopy(launch["limits"])
    authorization["scope"]["allowed_output_paths"] = copy.deepcopy(
        project_work_item["packet"]["allowed_output_paths"]
    )
    authorization["scope"]["capability"]["semantic_digest"] = semantic_digest(capability)
    authorization["scope"]["declared_input_refs"] = copy.deepcopy(
        project_work_item["packet"]["declared_input_refs"]
    )
    authorization["scope"]["snapshot"] = {
        "record_ref": copy.deepcopy(project_work_item["packet"]["source_snapshot"]["record_ref"]),
        "semantic_digest": semantic_digest(snapshot),
    }
    authorization["scope"]["source_audit_run_ref"]["record_id"] = project_work_item["audit_run_id"]
    authorization["scope"]["work_item_binding_status"] = "complete_project_execution_work_item"
    authorization["scope"]["work_item_semantic_digest"] = semantic_digest(project_work_item)
    authorization["scope"]["purpose"] = project_work_item["packet"]["purpose"]
    authorization["scope"]["target_refs"] = project_work_item["packet"]["target_refs"]
    project_execution["project_execution"]["authorization_semantic_digest"] = semantic_digest(
        authorization
    )
    project_execution["project_execution"]["command"] = copy.deepcopy(authorization["command"])
    project_execution["project_execution"]["effective_policy"]["environment"] = copy.deepcopy(
        authorization["environment"]
    )
    project_execution["project_execution"]["effective_policy"]["limits"] = copy.deepcopy(
        authorization["limits"]
    )
    project_execution["project_execution"]["image"] = copy.deepcopy(authorization["image"])
    project_execution["project_execution"]["purpose"] = project_work_item["packet"]["purpose"]
    _write_json(output / "examples" / "execution.project-workflow.example.json", project_execution)
    _write_json(output / "examples" / "project-execution-authorization.example.json", authorization)
    _write_json(output / "examples" / "work-item.project-execution.example.json", project_work_item)
    example_count += 1

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(_release_readme(), encoding="utf-8")
    (output / "CHANGELOG.md").write_text(_release_changelog(), encoding="utf-8")
    (output / "CONTROLLER_INVARIANTS.md").write_text(_release_invariants(), encoding="utf-8")
    (output / "MIGRATION_v0.13_to_v0.14.md").write_text(_migration_text(), encoding="utf-8")
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
    (tests_output / "test_v014_invariants.py").write_text(_v14_tests(), encoding="utf-8")

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
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.14.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
