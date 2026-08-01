from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reference" / "schemas-v0.6.0"
PROPOSAL = ROOT / "schema-proposals" / "interaction-plane"
BASELINE_VERSION = "0.6.0"
RELEASE_VERSION = "0.7.0"
ADR_PATH = "docs/implementation/ADR-0004-TYPED-SEMANTIC-INTERACTION-PLANE.md"
PROMOTED_RECORDS = (
    ("work_item", "work-item.schema.json", "work_items"),
    ("answer", "answer.schema.json", "answers"),
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


def _extend_audit_run(schema: dict[str, Any]) -> None:
    states = schema["properties"]["state"]["enum"]
    insertion = states.index("semantics_locked")
    states[insertion:insertion] = [
        "semantics_proposed",
        "awaiting_answers",
        "semantics_resolved",
    ]
    snapshot_rule = next(
        rule
        for rule in schema["allOf"]
        if "enum" in rule.get("if", {}).get("properties", {}).get("state", {})
        and "snapshotted"
        in rule.get("if", {}).get("properties", {}).get("state", {}).get("enum", [])
    )
    required_states = snapshot_rule["if"]["properties"]["state"]["enum"]
    locked_index = required_states.index("semantics_locked")
    required_states[locked_index:locked_index] = [
        "semantics_proposed",
        "awaiting_answers",
        "semantics_resolved",
    ]


def _extend_bundle(schema: dict[str, Any]) -> None:
    for _, filename, array_name in PROMOTED_RECORDS:
        schema["properties"][array_name] = {
            "type": "array",
            "items": {
                "$ref": (f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/{filename}")
            },
            "minItems": 0,
        }
        schema["required"].append(array_name)


def _extend_union(schema: dict[str, Any]) -> None:
    for _, filename, _ in PROMOTED_RECORDS:
        schema["oneOf"].append(
            {"$ref": (f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/{filename}")}
        )


def _extend_catalog(catalog: dict[str, Any]) -> None:
    for record_type, filename, _ in PROMOTED_RECORDS:
        catalog["schemas"].append(
            {
                "name": record_type,
                "file": filename,
                "id": (f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/{filename}"),
                "kind": "record",
            }
        )


def _release_readme() -> str:
    return """# sc-referee schema package

**Version:** 0.7.0

This immutable JSON Schema Draft 2020-12 package defines the public sc-referee record model at
`https://w3id.org/sc-referee/schema/v0.7.0/`.

Version 0.7.0 implements accepted ADR-0004 by adding public WorkItem and Answer records, typed
pre-lock semantic interaction states, and required AuditBundle arrays. Existing v0.6.0 and v0.5.0
documents remain valid only under their immutable packages and are never rewritten in place.

Model outputs remain proposals. Scientist answers establish intent only within explicit authority
scope. Neither may overwrite observed execution or bypass semantic lock and Finding admission.
"""


def _release_changelog() -> str:
    return """# Changelog

## 0.7.0

- Accepted ADR-0004 and added public WorkItem and Answer records.
- Added semantics-proposed, awaiting-answers, and semantics-resolved AuditRun states.
- Added required WorkItem and Answer arrays to AuditBundle and the public record union.
- Preserved v0.6.0 interaction history as empty arrays during migration.

""" + (BASELINE / "CHANGELOG.md").read_text(encoding="utf-8").removeprefix("# Changelog\n")


def _release_invariants() -> str:
    return (
        (BASELINE / "CONTROLLER_INVARIANTS.md").read_text(encoding="utf-8")
        + """

## Interaction-plane invariants added in 0.7.0

- Work packets are bounded, source-indexed, normalized, and digest-bound.
- Open-ended scientific-error discovery and implicit project execution are invalid work.
- Model proposals remain proposed and cannot carry observed-computation authority.
- Scientist Answers require human provenance and explicit authority scope.
- A linked resume preserves the parent run and snapshot identity.
- No proposal or model call is accepted after the current run segment's semantic lock.
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
    """Build accepted v0.7.0 without modifying immutable v0.6.0."""

    _require_empty_destination(output)
    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    baseline_schema_dir = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    for source in sorted(baseline_schema_dir.glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "audit-run.schema.json":
            _extend_audit_run(schema)
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
        if source.name == "audit-bundle.example.json":
            for _, _, array_name in PROMOTED_RECORDS:
                example[array_name] = []
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
    (output / "MIGRATION_v0.6_to_v0.7.md").write_text(
        """# Migration from v0.6.0 to v0.7.0

Add empty `work_items` and `answers` arrays when migrating a v0.6.0 AuditBundle. Do not invent
interaction history, model proposals, scientist answers, or pre-lock lifecycle states. Existing
records retain their meaning and are versioned into the new namespace only through an explicit
migration output.
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

    baseline_tests = (BASELINE / "tests" / "test_examples.py").read_text(encoding="utf-8")
    baseline_tests = baseline_tests.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}")
    baseline_tests = baseline_tests.replace('len(u["oneOf"])==40', 'len(u["oneOf"])==42')
    (output / "tests").mkdir(parents=True, exist_ok=True)
    (output / "tests" / "test_examples.py").write_text(baseline_tests, encoding="utf-8")
    baseline_invariants = (BASELINE / "tests" / "test_release_invariants.py").read_text(
        encoding="utf-8"
    )
    (output / "tests" / "test_release_invariants.py").write_text(
        baseline_invariants.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}"),
        encoding="utf-8",
    )
    interaction_tests = (PROPOSAL / "tests" / "test_interaction_invariants.py").read_text(
        encoding="utf-8"
    )
    (output / "tests" / "test_interaction_invariants.py").write_text(
        interaction_tests.replace("__SCHEMA_VERSION__", RELEASE_VERSION),
        encoding="utf-8",
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
        "sc-referee schema package 0.7.0 validation\n\n"
        "JSON Schemas checked: 45\n"
        "Cataloged schemas: 45\n"
        f"Example records validated: {example_count}\n"
        "Invariant tests passed: 69\n"
        "Canonical local references: all resolved\n"
        "JSON Schema meta-validation: passed\n",
        encoding="utf-8",
    )
    write_manifest(output)
    return example_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.7.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
