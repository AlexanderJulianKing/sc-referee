from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reference" / "schemas-v0.5.0"
PROPOSAL = ROOT / "schema-proposals" / "observed-plane"
BASELINE_VERSION = "0.5.0"
VERSION_TOKEN = "__SCHEMA_VERSION__"
SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
PROMOTED_RECORDS = (
    ("audit_run", "audit-run.schema.json", "audit_runs"),
    ("stage_result", "stage-result.schema.json", "stage_results"),
    ("file_record", "file-record.schema.json", "file_records"),
    ("operation", "operation.schema.json", "operations"),
    ("artifact", "artifact.schema.json", "artifacts"),
    ("observed_result", "observed-result.schema.json", "observed_results"),
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


def _replace_version(value: Any, release_version: str) -> Any:
    if isinstance(value, str):
        return value.replace(f"v{BASELINE_VERSION}", f"v{release_version}").replace(
            VERSION_TOKEN, release_version
        )
    if isinstance(value, list):
        return [_replace_version(item, release_version) for item in value]
    if isinstance(value, dict):
        return {key: _replace_version(item, release_version) for key, item in value.items()}
    return value


def _set_schema_version_fields(value: Any, release_version: str) -> None:
    if isinstance(value, list):
        for item in value:
            _set_schema_version_fields(item, release_version)
    elif isinstance(value, dict):
        if "schema_version" in value:
            value["schema_version"] = release_version
        for item in value.values():
            _set_schema_version_fields(item, release_version)


def _require_empty_destination(output: Path) -> None:
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Candidate output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)


def _add_bundle_arrays(bundle: dict[str, Any], release_version: str) -> None:
    required = bundle["required"]
    properties = bundle["properties"]
    for _, filename, array_name in PROMOTED_RECORDS:
        required.append(array_name)
        properties[array_name] = {
            "type": "array",
            "items": {
                "$ref": (f"https://w3id.org/sc-referee/schema/v{release_version}/{filename}")
            },
            "minItems": 0,
        }


def _add_union_refs(union: dict[str, Any], release_version: str) -> None:
    for _, filename, _ in PROMOTED_RECORDS:
        union["oneOf"].append(
            {"$ref": (f"https://w3id.org/sc-referee/schema/v{release_version}/{filename}")}
        )


def _add_catalog_entries(catalog: dict[str, Any], release_version: str) -> None:
    for record_type, filename, _ in PROMOTED_RECORDS:
        catalog["schemas"].append(
            {
                "name": record_type,
                "file": filename,
                "id": (f"https://w3id.org/sc-referee/schema/v{release_version}/{filename}"),
                "kind": "record",
            }
        )


def build_candidate(release_version: str, output: Path) -> int:
    """Build a review candidate without accepting or publishing its version."""
    if not SEMVER.fullmatch(release_version):
        raise ValueError(f"release_version must be exact SemVer, got {release_version!r}")
    if release_version == BASELINE_VERSION:
        raise ValueError("The immutable v0.5.0 baseline cannot be overwritten or reissued")
    _require_empty_destination(output)

    schema_output = output / "schemas" / f"v{release_version}"
    baseline_schema_dir = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    for source in sorted(baseline_schema_dir.glob("*.json")):
        schema = _replace_version(_read_json(source), release_version)
        if source.name == "common.schema.json":
            schema["$defs"]["SchemaVersion"]["const"] = release_version
        elif source.name == "record-union.schema.json":
            _add_union_refs(schema, release_version)
        elif source.name == "audit-bundle.schema.json":
            _add_bundle_arrays(schema, release_version)
        _write_json(schema_output / source.name, schema)

    for source in sorted((PROPOSAL / "schemas").glob("*.json")):
        _write_json(
            schema_output / source.name,
            _replace_version(_read_json(source), release_version),
        )

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"), release_version)
    catalog["schema_version"] = release_version
    _add_catalog_entries(catalog, release_version)
    _write_json(output / "schema-catalog.json", catalog)

    example_count = 0
    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source), release_version)
        _set_schema_version_fields(example, release_version)
        if source.name == "audit-bundle.example.json":
            for _, _, array_name in PROMOTED_RECORDS:
                example[array_name] = []
        _write_json(output / "examples" / source.name, example)
        example_count += 1
    for source in sorted((PROPOSAL / "examples").glob("*.json")):
        example = _replace_version(_read_json(source), release_version)
        _set_schema_version_fields(example, release_version)
        _write_json(output / "examples" / source.name, example)
        example_count += 1

    status = {
        "accepted": False,
        "baseline_version": BASELINE_VERSION,
        "candidate_version": release_version,
        "public_release": False,
        "source_adr": "docs/implementation/ADR-0002-OBSERVED-PLANE-PROMOTION.md",
        "warning": (
            "Review candidate only. Building this directory does not accept ADR-0002, "
            "publish W3ID schemas, or authorize runtime persistence under this version."
        ),
    }
    _write_json(output / "PROPOSAL_STATUS.json", status)
    (output / "VERSION").write_text(release_version + "\n", encoding="utf-8")
    (output / "MIGRATION.md").write_text(
        (PROPOSAL / "MIGRATION.md")
        .read_text(encoding="utf-8")
        .replace(VERSION_TOKEN, release_version),
        encoding="utf-8",
    )
    return example_count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the nonpublic ADR-0002 observed-plane schema review candidate."
    )
    parser.add_argument("--release-version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_candidate(args.release_version, args.output.resolve())
    print(f"Built nonpublic schema candidate with {count} examples at {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
