from __future__ import annotations

import json
from pathlib import Path

from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "v0.9.0"
EXAMPLES = ROOT / "examples"
CATALOG = json.loads((ROOT / "schema-catalog.json").read_text(encoding="utf-8"))
REGISTRY = Registry()
SCHEMAS = {}
ALIASES = {}
for item in CATALOG["schemas"]:
    schema = json.loads((SCHEMA_DIR / item["file"]).read_text(encoding="utf-8"))
    REGISTRY = REGISTRY.with_resource(schema["$id"], Resource.from_contents(schema))
    SCHEMAS[schema["$id"]] = schema
    ALIASES[item["name"]] = schema["$id"]


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def invalid(value: dict, alias: str) -> None:
    schema = SCHEMAS[ALIASES[alias]]
    validator = validator_for(schema)(schema, registry=REGISTRY, format_checker=FormatChecker())
    assert list(validator.iter_errors(value))


def test_created_run_cannot_fabricate_snapshot() -> None:
    value = load("audit-run.created.example.json")
    value["snapshot_ref"] = {
        "record_type": "repository_snapshot",
        "record_id": "snapshot:fabricated",
    }
    invalid(value, "audit_run")


def test_post_snapshot_run_requires_snapshot() -> None:
    value = load("audit-run.terminal.example.json")
    value["state"] = "parsed"
    value.pop("snapshot_ref")
    value.pop("terminal_reason")
    invalid(value, "audit_run")


def test_symlink_cannot_be_followed() -> None:
    value = load("file-record.symlink.example.json")
    value["symlink_followed"] = True
    invalid(value, "file_record")


def test_operation_edges_are_typed() -> None:
    value = load("operation.example.json")
    value["input_refs"] = ["artifact:data"]
    invalid(value, "operation")


def test_opaque_operation_cannot_be_supported() -> None:
    value = load("operation.opaque.example.json")
    value["inspection_status"] = "supported"
    invalid(value, "operation")


def test_unknown_orientation_cannot_become_unsupported_known_assertion() -> None:
    value = load("observed-result.unknown.example.json")
    value["orientation"] = {"state": "known", "value": "treated_minus_control"}
    invalid(value, "observed_result")


def test_bundle_requires_all_observed_plane_arrays() -> None:
    value = load("audit-bundle.example.json")
    value.pop("operations")
    invalid(value, "audit_bundle")
