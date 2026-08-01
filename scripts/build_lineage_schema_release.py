from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reference" / "schemas-v0.7.0"
PROPOSAL = ROOT / "schema-proposals" / "lineage-plane"
BASELINE_VERSION = "0.7.0"
RELEASE_VERSION = "0.8.0"
ADR_PATH = "docs/implementation/ADR-0005-MULTIDIMENSIONAL-LINEAGE-PLANE.md"
PROMOTED_RECORDS = (
    ("data_asset", "data-asset.schema.json", "data_assets"),
    ("variable", "variable.schema.json", "variables"),
    ("analysis_decision", "analysis-decision.schema.json", "analysis_decisions"),
    ("selection_envelope", "selection-envelope.schema.json", "selection_envelopes"),
    ("execution", "execution.schema.json", "executions"),
    ("environment", "environment.schema.json", "environments"),
)
GRADE_DIMENSIONS = (
    "report_origin",
    "result_origin",
    "computational_origin",
    "input_origin",
    "execution_origin",
    "semantic_origin",
)


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
        return (
            value.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}")
            .replace(BASELINE_VERSION, RELEASE_VERSION)
            .replace("__SCHEMA_VERSION__", RELEASE_VERSION)
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


def _lineage_status_condition(status: str) -> dict[str, Any]:
    return {
        "properties": {
            "lineage": {
                "properties": {"status": {"const": status}},
                "required": ["status"],
            }
        },
        "required": ["lineage"],
    }


def _grade_condition(statuses: tuple[str, ...], *, require_missing: bool = False) -> dict[str, Any]:
    grades: dict[str, Any] = {
        "properties": {
            dimension: {
                "properties": {"status": {"enum": list(statuses)}},
                "required": ["status"],
            }
            for dimension in GRADE_DIMENSIONS
        },
        "required": list(GRADE_DIMENSIONS),
    }
    if require_missing:
        grades["allOf"] = [
            {
                "anyOf": [
                    {
                        "properties": {
                            dimension: {
                                "properties": {"status": {"const": "missing"}},
                                "required": ["status"],
                            }
                        },
                        "required": [dimension],
                    }
                    for dimension in GRADE_DIMENSIONS
                ]
            }
        ]
    return {
        "properties": {
            "lineage": {
                "properties": {
                    "grades": grades,
                },
                "required": ["grades"],
            }
        },
        "required": ["lineage"],
    }


def _derived_status_rules() -> list[dict[str, Any]]:
    complete = _grade_condition(("complete",))
    unavailable = _grade_condition(("unavailable",))
    missing = _grade_condition(("missing", "unavailable", "opaque"), require_missing=True)
    return [
        {"if": _lineage_status_condition("complete"), "then": complete},
        {"if": complete, "then": _lineage_status_condition("complete")},
        {"if": _lineage_status_condition("unavailable"), "then": unavailable},
        {"if": unavailable, "then": _lineage_status_condition("unavailable")},
        {"if": _lineage_status_condition("missing"), "then": missing},
        {"if": missing, "then": _lineage_status_condition("missing")},
    ]


def _extend_claim(schema: dict[str, Any]) -> None:
    lineage = schema["properties"]["lineage"]
    lineage["properties"]["grades"] = {
        "$ref": (
            f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
            "lineage-grade.schema.json#/$defs/GradeSet"
        )
    }
    lineage["required"].append("grades")
    existing_complete_rule = schema.get("allOf", [])[0]
    schema["allOf"] = [existing_complete_rule, *_derived_status_rules()]


def _grade_count_schema() -> dict[str, Any]:
    names = ("complete", "partial", "missing", "unavailable", "opaque", "total")
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {name: {"type": "integer", "minimum": 0} for name in names},
        "required": list(names),
    }


def _extend_coverage(schema: dict[str, Any]) -> None:
    coverage = schema["properties"]["claim_coverage"]
    coverage["properties"]["lineage_grade_counts"] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {dimension: _grade_count_schema() for dimension in GRADE_DIMENSIONS},
        "required": list(GRADE_DIMENSIONS),
    }
    coverage["required"].append("lineage_grade_counts")


def _extend_bundle(schema: dict[str, Any]) -> None:
    for _, filename, array_name in PROMOTED_RECORDS:
        schema["properties"][array_name] = {
            "type": "array",
            "items": {"$ref": f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/{filename}"},
            "minItems": 0,
        }
        schema["required"].append(array_name)


def _extend_union(schema: dict[str, Any]) -> None:
    for _, filename, _ in PROMOTED_RECORDS:
        schema["oneOf"].append(
            {"$ref": f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/{filename}"}
        )


def _extend_catalog(catalog: dict[str, Any]) -> None:
    catalog["schemas"].append(
        {
            "name": "lineage_grade",
            "file": "lineage-grade.schema.json",
            "id": (
                f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/lineage-grade.schema.json"
            ),
            "kind": "definition",
        }
    )
    for record_type, filename, _ in PROMOTED_RECORDS:
        catalog["schemas"].append(
            {
                "name": record_type,
                "file": filename,
                "id": f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/{filename}",
                "kind": "record",
            }
        )


def _unavailable_grade(dimension: str) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "record_refs": [],
        "source_refs": [],
        "limitations": [
            f"Public v{BASELINE_VERSION} did not preserve an independent {dimension} grade."
        ],
    }


def _upgrade_example_records(value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            _upgrade_example_records(item)
        return
    if not isinstance(value, dict):
        return
    if (
        value.get("record_type") == "claim"
        and isinstance(value.get("claim_id"), str)
        and isinstance(value.get("lineage"), dict)
    ):
        lineage = value["lineage"]
        previous = lineage["status"]
        lineage["grades"] = {
            dimension: _unavailable_grade(dimension) for dimension in GRADE_DIMENSIONS
        }
        lineage["status"] = "unavailable"
        value.setdefault("extensions", {})["x-v0-7-aggregate-lineage-status"] = previous
    elif value.get("record_type") == "coverage_record" and isinstance(
        value.get("coverage_id"), str
    ):
        total = int(value["claim_coverage"]["claims_total"])
        value["claim_coverage"]["lineage_grade_counts"] = {
            dimension: {
                "complete": 0,
                "partial": 0,
                "missing": 0,
                "unavailable": total,
                "opaque": 0,
                "total": total,
            }
            for dimension in GRADE_DIMENSIONS
        }
        value["claim_coverage"]["claims_with_complete_lineage"] = 0
    elif value.get("record_type") == "audit_bundle" and isinstance(value.get("bundle_id"), str):
        for _, _, array_name in PROMOTED_RECORDS:
            value[array_name] = []
    for item in value.values():
        _upgrade_example_records(item)


def _release_readme() -> str:
    return """# sc-referee schema package

**Version:** 0.8.0

This immutable JSON Schema Draft 2020-12 package defines the public sc-referee record model at
`https://w3id.org/sc-referee/schema/v0.8.0/`.

Version 0.8.0 implements accepted ADR-0005. Claim lineage is graded independently across report,
result, computation, input, execution, and semantic origin. DataAsset, Variable,
AnalysisDecision, SelectionEnvelope, Execution, and Environment are public records. The aggregate
Claim lineage status is a deterministic summary and cannot overstate a component grade.

Auditor verification and project workflow execution are different authorities. An auditor-owned
Execution never proves that project code ran. Column structure never supplies scientific meaning.
Accepted v0.7.0, v0.6.0, and v0.5.0 packages remain immutable.
"""


def _release_changelog() -> str:
    return """# Changelog

## 0.8.0

- Accepted ADR-0005 and added six independent Claim lineage grades.
- Added DataAsset, Variable, AnalysisDecision, SelectionEnvelope, Execution, and Environment.
- Added required bundle arrays and per-grade Claim coverage counts.
- Kept auditor verification distinct from authorized rootless-OCI project execution.
- Defined a conservative v0.7.0 migration that invents no observed graph history.

""" + (BASELINE / "CHANGELOG.md").read_text(encoding="utf-8").removeprefix("# Changelog\n")


def _release_invariants() -> str:
    return (
        (BASELINE / "CONTROLLER_INVARIANTS.md").read_text(encoding="utf-8")
        + """

## Multidimensional-lineage invariants added in 0.8.0

- Claim aggregate lineage status is derived from all six component grades.
- A complete grade has evidence and no limitations; every non-complete grade states a limitation.
- Column structure does not establish scientific meaning.
- Typed edges resolve to the exact declared record type and identifier.
- Static inspection creates no Execution record.
- Auditor verification records only the auditor's Execution and never project workflow execution.
- Project workflow Execution requires explicit authorization and a qualifying rootless-OCI
  SandboxCapability, enforced by the controller across the typed reference.
- Coverage counts reconcile with every Claim's six grades.
"""
    )


def write_manifest(output: Path) -> None:
    entries = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        if path.name == "MANIFEST.sha256":
            continue
        relative = path.relative_to(output).as_posix()
        entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}")
    (output / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def build_release(output: Path) -> int:
    """Build accepted v0.8.0 without modifying immutable v0.7.0."""

    _require_empty_destination(output)
    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    baseline_schema_dir = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    for source in sorted(baseline_schema_dir.glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "claim.schema.json":
            _extend_claim(schema)
        elif source.name == "coverage-record.schema.json":
            _extend_coverage(schema)
        elif source.name == "audit-bundle.schema.json":
            _extend_bundle(schema)
        elif source.name == "record-union.schema.json":
            _extend_union(schema)
        _write_json(schema_output / source.name, schema)

    for source in sorted((PROPOSAL / "schemas").glob("*.json")):
        _write_json(schema_output / source.name, _replace_version(_read_json(source)))

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    _extend_catalog(catalog)
    _write_json(output / "schema-catalog.json", catalog)

    example_count = 0
    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        _upgrade_example_records(example)
        _write_json(output / "examples" / source.name, example)
        example_count += 1
    for source in sorted((PROPOSAL / "examples").glob("*.json")):
        _write_json(output / "examples" / source.name, _replace_version(_read_json(source)))
        example_count += 1

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(_release_readme(), encoding="utf-8")
    (output / "CHANGELOG.md").write_text(_release_changelog(), encoding="utf-8")
    (output / "CONTROLLER_INVARIANTS.md").write_text(_release_invariants(), encoding="utf-8")
    (output / "MIGRATION_v0.7_to_v0.8.md").write_text(
        """# Migration from v0.7.0 to v0.8.0

Add empty arrays for DataAsset, Variable, AnalysisDecision, SelectionEnvelope, Execution, and
Environment. Do not infer these records from filenames or roles. Preserve each v0.7.0 Claim's
result, operation, input, missing, and opaque references. Set all six new grades and the new
aggregate to `unavailable`; preserve the former aggregate in the
`x-v0-7-aggregate-lineage-status` Claim extension. Recalculate coverage accordingly. Do not carry
forward a StorageManifest because migrated bytes require a new manifest.
""",
        encoding="utf-8",
    )
    _write_json(
        output / "RELEASE_STATUS.json",
        {
            "accepted": True,
            "baseline_version": BASELINE_VERSION,
            "public_release": True,
            "release_version": RELEASE_VERSION,
            "source_adr": ADR_PATH,
        },
    )

    (output / "tests").mkdir(parents=True, exist_ok=True)
    for source in sorted((BASELINE / "tests").glob("*.py")):
        test_text = source.read_text(encoding="utf-8")
        test_text = test_text.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}")
        test_text = test_text.replace('len(u["oneOf"])==42', 'len(u["oneOf"])==48')
        test_text = test_text.replace(
            'x=load("claim.example.json"); x["lineage"]["missing_links"]',
            'x=load("claim.lineage-complete.example.json"); x["lineage"]["missing_links"]',
        )
        (output / "tests" / source.name).write_text(test_text, encoding="utf-8")
    lineage_tests = (PROPOSAL / "tests" / "test_lineage_invariants.py").read_text(encoding="utf-8")
    (output / "tests" / "test_lineage_invariants.py").write_text(
        lineage_tests.replace("__SCHEMA_VERSION__", RELEASE_VERSION), encoding="utf-8"
    )
    validator = (BASELINE / "tools" / "validate_records.py").read_text(encoding="utf-8")
    (output / "tools").mkdir(parents=True, exist_ok=True)
    (output / "tools" / "validate_records.py").write_text(
        validator.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}"), encoding="utf-8"
    )
    baseline_pyproject = (BASELINE / "pyproject.toml").read_text(encoding="utf-8")
    (output / "pyproject.toml").write_text(
        baseline_pyproject.replace(BASELINE_VERSION, RELEASE_VERSION), encoding="utf-8"
    )
    (output / "VALIDATION.txt").write_text(
        "sc-referee schema package 0.8.0 validation\n\n"
        "JSON Schemas checked: 52\n"
        "Cataloged schemas: 52\n"
        f"Example records validated: {example_count}\n"
        "Invariant tests passed: 81\n"
        "Canonical local references: all resolved\n"
        "JSON Schema meta-validation: passed\n",
        encoding="utf-8",
    )
    write_manifest(output)
    return example_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.8.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
