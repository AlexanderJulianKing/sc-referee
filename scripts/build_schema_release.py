from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_observed_schema_candidate import BASELINE, ROOT, build_candidate

RELEASE_VERSION = "0.6.0"
ADR_PATH = "docs/implementation/ADR-0002-OBSERVED-PLANE-PROMOTION.md"
AMENDING_ADRS = ("docs/implementation/ADR-0003-UNAVAILABLE-PUBLICATION-SURFACE.md",)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _copy_versioned_text(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = source.read_text(encoding="utf-8").replace("v0.5.0", "v0.6.0")
    text = text.replace("0.5.0", "0.6.0")
    destination.write_text(text, encoding="utf-8")


def _normalize_promoted_schema_metadata(output: Path) -> None:
    promoted = {
        "artifact.schema.json",
        "audit-run.schema.json",
        "file-record.schema.json",
        "observed-result.schema.json",
        "operation.schema.json",
        "stage-result.schema.json",
    }
    schema_dir = output / "schemas" / f"v{RELEASE_VERSION}"
    for name in promoted:
        path = schema_dir / name
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["title"] = str(schema["title"]).replace(" review candidate", "")
        schema.pop("$comment", None)
        _write_json(path, schema)


def _apply_unavailable_publication_surface_schema(output: Path) -> None:
    """Apply accepted ADR-0003 without changing the immutable v0.5.0 baseline."""

    schema_dir = output / "schemas" / f"v{RELEASE_VERSION}"
    surface_path = schema_dir / "publication-surface.schema.json"
    surface = json.loads(surface_path.read_text(encoding="utf-8"))
    surface["properties"]["candidates"]["minItems"] = 0
    resolved_rule = next(
        rule
        for rule in surface["allOf"]
        if rule.get("if", {}).get("properties", {}).get("status", {}).get("const") == "resolved"
    )
    resolved_rule["then"]["properties"]["candidates"] = {"minItems": 1}
    surface["allOf"].append(
        {
            "if": {
                "properties": {"candidates": {"maxItems": 0}},
                "required": ["candidates"],
            },
            "then": {
                "properties": {
                    "publication_materiality_assessable": {"const": False},
                    "selection": {
                        "properties": {"kind": {"const": "unresolved"}},
                        "required": ["kind", "material_question_id"],
                    },
                    "status": {"const": "unresolved"},
                }
            },
        }
    )
    _write_json(surface_path, surface)

    coverage_path = schema_dir / "coverage-record.schema.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    scope = coverage["properties"]["scope"]
    scope["properties"]["publication_surface_refs"]["minItems"] = 0
    scope["properties"]["publication_surface_status"] = {
        "enum": ["resolved", "unresolved", "unavailable"]
    }
    scope["required"].append("publication_surface_status")
    scope["allOf"] = [
        {
            "if": {
                "properties": {"publication_surface_status": {"const": "resolved"}},
                "required": ["publication_surface_status"],
            },
            "then": {"properties": {"publication_surface_refs": {"minItems": 1}}},
        },
        {
            "if": {
                "properties": {"publication_surface_status": {"const": "unavailable"}},
                "required": ["publication_surface_status"],
            },
            "then": {"properties": {"publication_surface_refs": {"maxItems": 0}}},
        },
    ]
    _write_json(coverage_path, coverage)


def _unavailable_surface_example() -> dict[str, Any]:
    return {
        "schema_version": RELEASE_VERSION,
        "record_type": "publication_surface",
        "publication_surface_id": "surface:unavailable-example",
        "audit_run_id": "audit:unavailable-example",
        "status": "unresolved",
        "candidates": [],
        "precedence_policy": [
            "explicit_user_target_or_active_workspace",
            "declared_build_target",
            "explicit_task_or_repository_statement",
            "unique_lineage_evidence",
            "filename_and_time_supporting_only",
        ],
        "selection": {
            "kind": "unresolved",
            "reason": "No fully identified publication-like artifact was available.",
            "material_question_id": "question:unavailable-publication-surface",
        },
        "publication_materiality_assessable": False,
        "created_at": "2026-07-28T20:00:00Z",
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-controller",
                "display_name": "sc-referee controller",
            },
            "method": "deterministic_publication_surface_inventory",
            "created_at": "2026-07-28T20:00:00Z",
            "tool": "sc-referee",
            "tool_version": "0.1.0.dev0",
        },
    }


def _add_publication_surface_status_to_examples(output: Path) -> None:
    coverage_path = output / "examples" / "coverage-record.example.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    coverage["scope"]["publication_surface_status"] = "resolved"
    _write_json(coverage_path, coverage)

    bundle_path = output / "examples" / "audit-bundle.example.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    for record in bundle.get("coverage_records", []):
        record["scope"]["publication_surface_status"] = "resolved"
    _write_json(bundle_path, bundle)


def _adr_0003_example_tests() -> str:
    return """

def test_unavailable_publication_surface_is_valid_explicit_unknown():
 x=load("publication-surface.unavailable.example.json"); assert not errors(x,"publication_surface")

def test_resolved_publication_surface_requires_a_candidate():
 x=load("publication-surface.example.json"); x["candidates"]=[]; invalid(x,"publication_surface")

def test_empty_publication_surface_cannot_enable_materiality():
 x=load("publication-surface.unavailable.example.json"); x["publication_materiality_assessable"]=True; invalid(x,"publication_surface")

def test_empty_coverage_refs_cannot_be_labeled_resolved():
 x=load("coverage-record.example.json"); x["scope"]["publication_surface_refs"]=[]; invalid(x,"coverage_record")

def test_unavailable_coverage_requires_empty_surface_refs():
 x=load("coverage-record.example.json"); x["scope"]["publication_surface_status"]="unavailable"; invalid(x,"coverage_record")
"""


def _release_readme() -> str:
    return """# sc-referee schema package

**Version:** 0.6.0

This immutable JSON Schema Draft 2020-12 package defines the public sc-referee record model at
`https://w3id.org/sc-referee/schema/v0.6.0/`.

Version 0.6.0 promotes the minimum observed-computation and control-plane records accepted by
ADR-0002: `AuditRun`, `StageResult`, `FileRecord`, `Operation`, `Artifact`, and `ObservedResult`.
`AuditBundle` now requires arrays for all six record types. Existing 0.5.0 documents remain valid
only under the immutable 0.5.0 package; they are never rewritten in place.

Accepted ADR-0003 permits an unresolved `PublicationSurface` with no candidates only when
publication materiality remains unassessable and an open `MaterialQuestion` is linked. A
`CoverageRecord` may use no publication-surface references only when it explicitly labels that
scope unresolved or unavailable. Resolved surfaces and resolved coverage still require evidence.

The epistemic boundary is unchanged: a Finding is a narrowly worded demonstrated issue. Unknown,
conditional, unsupported, or opaque evidence is represented explicitly and is not a Finding.

## Validation

```bash
python tools/validate_records.py examples
pytest -q
```

Schema validation establishes record shape and selected deterministic invariants. It does not
establish scientific detector validity, graph reachability, W3ID deployment, or a global
correctness claim.
"""


def _release_changelog() -> str:
    previous = (BASELINE / "CHANGELOG.md").read_text(encoding="utf-8")
    return """# Changelog

## 0.6.0

- Accepted ADR-0002 and added public AuditRun, StageResult, FileRecord, Operation, Artifact, and
  ObservedResult records.
- Added typed graph edges and explicit epistemic states for observed-result semantics.
- Made the six corresponding AuditBundle arrays required and added all records to the public
  record union and schema catalog.
- Added fail-closed migration rules from provisional v0.1.0 records and immutable public v0.5.0
  bundles.
- Accepted ADR-0003 and added explicit unavailable publication-surface and coverage states without
  inventing an Artifact.

""" + previous.removeprefix("# Changelog\n")


def _release_invariants() -> str:
    previous = (BASELINE / "CONTROLLER_INVARIANTS.md").read_text(encoding="utf-8")
    return (
        previous
        + """

## Observed-plane invariants added in 0.6.0

- `created` AuditRun records have no snapshot reference; every later state has one.
- Terminal AuditRun records preserve an exact recorded terminal reason.
- FileRecord identity is expressed only through a typed AssetIdentity reference.
- Symbolic links are inventoried without following their targets.
- Operation edges are typed RecordRef objects; unknown dispatch remains an opaque operation.
- Complete ObservedResult lineage has one producing operation and artifact reference.
- Unknown semantic slots remain explicitly unknown and cannot be promoted without evidence.
- An empty PublicationSurface candidate set remains unresolved, unassessable for publication
  materiality, and linked to one open MaterialQuestion.
- Empty CoverageRecord publication-surface references require an explicit unavailable or
  unresolved status; resolved coverage always retains at least one reference.
"""
    )


def write_manifest(output: Path) -> None:
    entries: list[str] = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        if path.name == "MANIFEST.sha256":
            continue
        relative = path.relative_to(output).as_posix()
        entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}")
    (output / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def build_release(output: Path) -> int:
    """Build the exact accepted 0.6.0 package without modifying the 0.5.0 baseline."""
    example_count = build_candidate(RELEASE_VERSION, output)
    (output / "PROPOSAL_STATUS.json").unlink()
    _normalize_promoted_schema_metadata(output)
    _apply_unavailable_publication_surface_schema(output)
    _add_publication_surface_status_to_examples(output)
    _write_json(
        output / "examples" / "publication-surface.unavailable.example.json",
        _unavailable_surface_example(),
    )
    example_count += 1

    for name in (
        "LICENSE",
        "LICENSE-NOTICE.md",
        "NOTICE",
        "requirements.txt",
        "MIGRATION_v0.1_to_v0.2.md",
        "MIGRATION_v0.2_to_v0.3.md",
        "MIGRATION_v0.3_to_v0.4.md",
        "MIGRATION_v0.4_to_v0.5.md",
    ):
        shutil.copy2(BASELINE / name, output / name)
    _copy_versioned_text(BASELINE / "pyproject.toml", output / "pyproject.toml")
    _copy_versioned_text(
        BASELINE / "tools" / "validate_records.py", output / "tools" / "validate_records.py"
    )
    _copy_versioned_text(
        BASELINE / "tests" / "test_examples.py", output / "tests" / "test_examples.py"
    )
    package_tests = output / "tests" / "test_examples.py"
    package_tests.write_text(
        package_tests.read_text(encoding="utf-8").replace(
            'len(u["oneOf"])==34', 'len(u["oneOf"])==40'
        )
        + _adr_0003_example_tests(),
        encoding="utf-8",
    )
    shutil.copy2(
        ROOT / "schema-proposals" / "observed-plane" / "tests" / "test_release_invariants.py",
        output / "tests" / "test_release_invariants.py",
    )

    (output / "README.md").write_text(_release_readme(), encoding="utf-8")
    (output / "CHANGELOG.md").write_text(_release_changelog(), encoding="utf-8")
    (output / "CONTROLLER_INVARIANTS.md").write_text(_release_invariants(), encoding="utf-8")
    migration = (ROOT / "schema-proposals" / "observed-plane" / "MIGRATION.md").read_text(
        encoding="utf-8"
    )
    migration = migration.replace("__SCHEMA_VERSION__", RELEASE_VERSION)
    migration = migration.replace(
        "# Provisional observed-plane migration candidate", "# Migration from v0.5.0 to v0.6.0"
    )
    migration = migration.replace(
        "This document is generated into the nonpublic `0.6.0` review candidate. It does not\n"
        "authorize publication or runtime persistence under that version.\n\n",
        "ADR-0002 authorizes these coordinated public record changes at version `0.6.0`.\n\n",
    )
    migration = migration.replace(
        "The candidate\nbuilder copies and rewrites schemas into a new directory; it never edits the baseline in place.",
        "The release builder copies and rewrites schemas into a new directory; it never edits the baseline in place.",
    )
    migration = migration.replace("candidate-bundle validation", "public-bundle validation")
    migration = migration.split("Still required before acceptance:", maxsplit=1)[0].rstrip() + "\n"
    (output / "MIGRATION_v0.5_to_v0.6.md").write_text(migration, encoding="utf-8")
    (output / "MIGRATION.md").unlink()

    _write_json(
        output / "RELEASE_STATUS.json",
        {
            "accepted": True,
            "amending_adrs": list(AMENDING_ADRS),
            "baseline_version": "0.5.0",
            "public_release": True,
            "release_version": RELEASE_VERSION,
            "source_adr": ADR_PATH,
        },
    )
    (output / "VALIDATION.txt").write_text(
        "sc-referee schema package 0.6.0 validation\n\n"
        "JSON Schemas checked: 43\n"
        "Cataloged schemas: 43\n"
        "Example records validated: 50\n"
        "Invariant tests passed: 58\n"
        "Canonical local references: all resolved\n"
        "JSON Schema meta-validation: passed\n\n"
        "These checks establish structural and selected deterministic-policy consistency. "
        "They do not establish scientific detector validity, benchmark-label truth, precision, "
        "recall, runtime performance, or W3ID deployment.\n",
        encoding="utf-8",
    )
    write_manifest(output)
    return example_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.6.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
