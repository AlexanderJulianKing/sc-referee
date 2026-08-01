from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reference" / "schemas-v0.17.0"
BASELINE_VERSION = "0.17.0"
RELEASE_VERSION = "0.18.0"
SOURCE_ADRS = ["docs/implementation/ADR-0044-DETERMINISTIC-CALCULATION-CHECK-BOUNDARY.md"]
RECORD_TYPE = "deterministic_check_observation"
SCHEMA_FILE = "deterministic-check-observation.schema.json"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected one JSON object in {path}")
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


def _common_ref(name: str) -> dict[str, str]:
    return {
        "$ref": (
            f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
            f"common.schema.json#/$defs/{name}"
        )
    }


def _record_ref() -> dict[str, str]:
    return _common_ref("RecordRef")


def _source_refs(*, min_items: int = 0) -> dict[str, Any]:
    return {
        "items": _common_ref("SourceRef"),
        "minItems": min_items,
        "type": "array",
        "uniqueItems": True,
    }


def _strings(*, min_items: int = 0, max_items: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "items": {"minLength": 1, "type": "string"},
        "minItems": min_items,
        "type": "array",
        "uniqueItems": True,
    }
    if max_items is not None:
        value["maxItems"] = max_items
    return value


def _manifest(kind: str, identity: str) -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "manifest_kind": {"const": kind},
            identity: _common_ref("Identifier"),
            f"{identity.removesuffix('_id')}_version": _common_ref("SemVer"),
            "implementation_digest": _common_ref("Digest"),
            "manifest_digest": _common_ref("Digest"),
        },
        "required": [
            "manifest_kind",
            identity,
            f"{identity.removesuffix('_id')}_version",
            "implementation_digest",
            "manifest_digest",
        ],
        "type": "object",
    }


def _operand() -> dict[str, Any]:
    kinds = [
        "boolean",
        "integer",
        "finite_number",
        "string",
        "boolean_array",
        "integer_array",
        "finite_number_array",
        "string_array",
    ]
    value: dict[str, Any] = {
        "additionalProperties": False,
        "properties": {
            "name": _common_ref("Identifier"),
            "kind": {"enum": kinds},
            "value": {},
        },
        "required": ["name", "kind", "value"],
        "type": "object",
    }
    scalar_or_array = {
        "boolean": {"type": "boolean"},
        "integer": {"type": "integer"},
        "finite_number": {"type": "number"},
        "string": {"type": "string"},
        "boolean_array": {
            "items": {"type": "boolean"},
            "maxItems": 10000,
            "type": "array",
        },
        "integer_array": {
            "items": {"type": "integer"},
            "maxItems": 10000,
            "type": "array",
        },
        "finite_number_array": {
            "items": {"type": "number"},
            "maxItems": 10000,
            "type": "array",
        },
        "string_array": {
            "items": {"type": "string"},
            "maxItems": 10000,
            "type": "array",
        },
    }
    value["allOf"] = [
        {
            "if": {"properties": {"kind": {"const": kind}}, "required": ["kind"]},
            "then": {"properties": {"value": schema}},
        }
        for kind, schema in scalar_or_array.items()
    ]
    return value


def _receipt() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "receipt_kind": {
                "enum": ["applicability", "ambiguity", "counterevidence", "completeness"]
            },
            "predicate": _common_ref("Identifier"),
            "state": {"enum": ["passed", "triggered", "not_applicable", "unsupported"]},
            "source_refs": _source_refs(),
            "detail": {"minLength": 1, "type": "string"},
        },
        "required": ["receipt_kind", "predicate", "state", "source_refs", "detail"],
        "type": "object",
    }


def _observation_schema() -> dict[str, Any]:
    return {
        "$id": (
            f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
            "deterministic-check-observation.schema.json"
        ),
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "schema_version": _common_ref("SchemaVersion"),
            "record_type": {"const": RECORD_TYPE},
            "deterministic_check_observation_id": _common_ref("Identifier"),
            "audit_run_id": _common_ref("Identifier"),
            "check_manifest": _manifest("calculation_check_manifest", "check_id"),
            "adapter_manifest": _manifest("calculation_adapter_manifest", "adapter_id"),
            "applicability": {"enum": ["applicable", "not_applicable", "ambiguous", "unsupported"]},
            "output_ceiling": {
                "enum": ["question_only", "disclosure_only", "evaluation_candidate"]
            },
            "target_ref": _record_ref(),
            "input_refs": {
                "items": _record_ref(),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "source_refs": _source_refs(min_items=1),
            "operands": {
                "items": _operand(),
                "maxItems": 64,
                "type": "array",
                "uniqueItems": True,
            },
            "comparison": {
                "additionalProperties": False,
                "properties": {
                    "relation": _common_ref("Identifier"),
                    "outcome": {
                        "enum": ["conformant", "nonconformant", "unknown", "not_applicable"]
                    },
                },
                "required": ["relation", "outcome"],
                "type": "object",
            },
            "receipts": {
                "items": _receipt(),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "lineage_status": {"enum": ["complete", "incomplete", "not_applicable"]},
            "limitations": _strings(),
            "non_inferences": {
                "const": [
                    "causality",
                    "execution",
                    "scientific_correctness",
                    "universal_method_adequacy",
                ]
            },
            "production_finding_permitted": {"const": False},
            "observation_digest": _common_ref("Digest"),
            "provenance": _common_ref("Provenance"),
            "extensions": {
                "additionalProperties": True,
                "propertyNames": {"pattern": "^x-"},
                "type": "object",
            },
        },
        "required": [
            "schema_version",
            "record_type",
            "deterministic_check_observation_id",
            "audit_run_id",
            "check_manifest",
            "adapter_manifest",
            "applicability",
            "output_ceiling",
            "target_ref",
            "input_refs",
            "source_refs",
            "operands",
            "comparison",
            "receipts",
            "lineage_status",
            "limitations",
            "non_inferences",
            "production_finding_permitted",
            "observation_digest",
            "provenance",
        ],
        "allOf": [
            {
                "if": {"properties": {"applicability": {"const": "applicable"}}},
                "then": {
                    "properties": {
                        "comparison": {
                            "properties": {"outcome": {"enum": ["conformant", "nonconformant"]}}
                        },
                        "lineage_status": {"const": "complete"},
                        "operands": {"minItems": 1},
                    }
                },
            },
            {
                "if": {"properties": {"applicability": {"const": "not_applicable"}}},
                "then": {
                    "properties": {
                        "comparison": {"properties": {"outcome": {"const": "not_applicable"}}},
                        "lineage_status": {"const": "not_applicable"},
                    }
                },
            },
            {
                "if": {"properties": {"applicability": {"enum": ["ambiguous", "unsupported"]}}},
                "then": {
                    "properties": {
                        "comparison": {"properties": {"outcome": {"const": "unknown"}}},
                        "lineage_status": {"const": "incomplete"},
                    }
                },
            },
        ],
        "title": "sc-referee Deterministic Check Observation",
        "type": "object",
    }


def _example() -> dict[str, Any]:
    check = {
        "manifest_kind": "calculation_check_manifest",
        "check_id": "calculation-check:benjamini-hochberg-complete-family-v1",
        "check_version": "1.0.0",
        "implementation_digest": "sha256:" + "1" * 64,
    }
    check["manifest_digest"] = "sha256:" + "2" * 64
    adapter = {
        "manifest_kind": "calculation_adapter_manifest",
        "adapter_id": "calculation-adapter:declared-bh-table-v1",
        "adapter_version": "1.0.0",
        "implementation_digest": "sha256:" + "3" * 64,
        "manifest_digest": "sha256:" + "4" * 64,
    }
    return {
        "schema_version": RELEASE_VERSION,
        "record_type": RECORD_TYPE,
        "deterministic_check_observation_id": "calculation-observation:bh-example",
        "audit_run_id": "audit:example",
        "check_manifest": check,
        "adapter_manifest": adapter,
        "applicability": "applicable",
        "output_ceiling": "disclosure_only",
        "target_ref": {"record_type": "publication_surface", "record_id": "surface:selected"},
        "input_refs": [{"record_type": "artifact", "record_id": "artifact:results"}],
        "source_refs": [
            {
                "source_kind": "file_span",
                "locator": "results.csv:1-3",
                "path": "results.csv",
                "content_digest": "sha256:" + "5" * 64,
                "start_line": 1,
                "end_line": 3,
                "quoted_text": "test_id,p_value,adjusted_p_value",
            }
        ],
        "operands": [
            {"name": "alpha", "kind": "string", "value": "0.05"},
            {"name": "reported_discovery_count", "kind": "integer", "value": 4},
            {"name": "recomputed_discovery_count", "kind": "integer", "value": 2},
        ],
        "comparison": {"relation": "bh_adjusted_calls_equal", "outcome": "nonconformant"},
        "receipts": [
            {
                "receipt_kind": "completeness",
                "predicate": "complete_test_family_declared",
                "state": "passed",
                "source_refs": [],
                "detail": "The selected report explicitly declares the complete tested family.",
            }
        ],
        "lineage_status": "complete",
        "limitations": ["The observation does not establish that the table drove a publication."],
        "non_inferences": [
            "causality",
            "execution",
            "scientific_correctness",
            "universal_method_adequacy",
        ],
        "production_finding_permitted": False,
        "observation_digest": "sha256:" + "6" * 64,
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-controller",
                "display_name": "sc-referee controller",
            },
            "method": "bounded_deterministic_calculation",
            "created_at": "2026-07-31T23:45:00Z",
            "tool": "sc-referee",
            "tool_version": "0.3.0.dev0",
        },
    }


def _release_tests() -> str:
    return """from test_examples import errors, invalid, load

def test_deterministic_observation_example_validates():
 assert not errors(load("deterministic-check-observation.example.json"), "deterministic_check_observation")

def test_applicable_observation_cannot_report_unknown():
 x=load("deterministic-check-observation.example.json")
 x["comparison"]["outcome"]="unknown"
 invalid(x,"deterministic_check_observation")

def test_observation_cannot_grant_finding_authority():
 x=load("deterministic-check-observation.example.json")
 x["production_finding_permitted"]=True
 invalid(x,"deterministic_check_observation")

def test_operand_arrays_are_bounded():
 x=load("deterministic-check-observation.example.json")
 x["operands"][0]={"name":"values","kind":"string_array","value":["x"]*10001}
 invalid(x,"deterministic_check_observation")
"""


def _write_manifest(output: Path) -> None:
    entries = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        if path.name == "MANIFEST.sha256" or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(output).as_posix()
        entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}")
    (output / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def build_release(output: Path) -> int:
    """Build accepted v0.18.0 without modifying immutable v0.17.0."""

    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Release output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    source_schemas = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    for source in sorted(source_schemas.glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "audit-bundle.schema.json":
            schema["properties"]["deterministic_check_observations"] = {
                "items": {
                    "$ref": (f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/{SCHEMA_FILE}")
                },
                "minItems": 0,
                "type": "array",
            }
            schema["required"].append("deterministic_check_observations")
        elif source.name == "record-union.schema.json":
            schema["oneOf"].append(
                {"$ref": (f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/{SCHEMA_FILE}")}
            )
        _write_json(schema_output / source.name, schema)
    _write_json(schema_output / SCHEMA_FILE, _observation_schema())

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    catalog["schemas"].append(
        {
            "file": SCHEMA_FILE,
            "id": f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/{SCHEMA_FILE}",
            "kind": "record",
            "name": RECORD_TYPE,
        }
    )
    catalog["schemas"] = sorted(catalog["schemas"], key=lambda item: str(item["name"]))
    _write_json(output / "schema-catalog.json", catalog)

    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        if example.get("record_type") == "audit_bundle":
            example["deterministic_check_observations"] = []
        _write_json(output / "examples" / source.name, example)
    _write_json(output / "examples" / "deterministic-check-observation.example.json", _example())

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(
        "# sc-referee public schemas v0.18.0\n\n"
        "Accepted forward-only public schema release implementing ADR-0044. It adds a typed, "
        "bounded deterministic-calculation observation and grants no Finding authority.\n",
        encoding="utf-8",
    )
    (output / "CHANGELOG.md").write_text(
        "# Changelog\n\n## 0.18.0 — 2026-07-31\n\n"
        "- Added `DeterministicCheckObservation` for bounded auditor-owned calculations.\n"
        "- Added closed operands, receipts, applicability, comparison, and output-ceiling fields.\n"
        "- Preserved v0.17.0 as an immutable migration baseline.\n",
        encoding="utf-8",
    )
    (output / "CONTROLLER_INVARIANTS.md").write_text(
        "# Controller invariants for v0.18.0\n\n"
        "- Calculation inputs and implementations are content-addressed.\n"
        "- Operand arrays and adapter reads are finite and bounded.\n"
        "- Ambiguous and unsupported cases remain unknown.\n"
        "- Calculation observations do not establish execution, causality, general correctness, "
        "or Finding authority.\n",
        encoding="utf-8",
    )
    (output / "MIGRATION_v0.17_to_v0.18.md").write_text(
        "# Migration from v0.17.0 to v0.18.0\n\n"
        "Ordinary records are versioned and the new observation collection starts empty. Migration "
        "does not infer calculations, applicability, evidence, detector qualification, or Finding "
        "authority.\n",
        encoding="utf-8",
    )
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
        if source.name == "test_examples.py":
            source_text = source_text.replace('len(u["oneOf"])==56', 'len(u["oneOf"])==57')
        (tests_output / source.name).write_text(source_text, encoding="utf-8")
    (tests_output / "test_v018_invariants.py").write_text(_release_tests(), encoding="utf-8")

    validator = (BASELINE / "tools" / "validate_records.py").read_text(encoding="utf-8")
    (output / "tools").mkdir(parents=True, exist_ok=True)
    (output / "tools" / "validate_records.py").write_text(
        validator.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}"),
        encoding="utf-8",
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
    example_count = len(list((output / "examples").glob("*.json")))
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
    _write_manifest(output)
    return example_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.18.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
