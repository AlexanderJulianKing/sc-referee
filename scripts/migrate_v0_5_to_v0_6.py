from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import stable_id
from sc_referee.records.normalization import write_normalized_json
from sc_referee.records.schema_registry import LocalSchemaRegistry

SOURCE_VERSION = "0.5.0"
TARGET_VERSION = "0.6.0"
OBSERVED_ARRAYS = (
    "audit_runs",
    "stage_results",
    "file_records",
    "operations",
    "artifacts",
    "observed_results",
)


class PublicMigrationError(ValueError):
    """Raised when a public bundle cannot be migrated without inventing evidence."""


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PublicMigrationError(f"Expected a JSON object in {path}")
    return value


def _assert_source_versions(value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            _assert_source_versions(item)
    elif isinstance(value, dict):
        if "schema_version" in value and value["schema_version"] != SOURCE_VERSION:
            raise PublicMigrationError(
                f"Mixed or unsupported schema version {value['schema_version']!r}"
            )
        for item in value.values():
            _assert_source_versions(item)


def _version_existing_records(value: Any) -> Any:
    if isinstance(value, list):
        for index, item in enumerate(value):
            value[index] = _version_existing_records(item)
    elif isinstance(value, dict):
        if "schema_version" in value:
            value["schema_version"] = TARGET_VERSION
        for key, item in value.items():
            value[key] = _version_existing_records(item)
    elif isinstance(value, str):
        return value.replace(
            f"https://w3id.org/sc-referee/schema/v{SOURCE_VERSION}/",
            f"https://w3id.org/sc-referee/schema/v{TARGET_VERSION}/",
        )
    return value


def _preserve_unknown_publication_surface_status(bundle: dict[str, Any]) -> None:
    """Represent the v0.5.0 omission as unresolved rather than inventing resolution."""

    for coverage in bundle.get("coverage_records", []):
        scope = coverage.get("scope")
        if isinstance(scope, dict):
            scope["publication_surface_status"] = "unresolved"


def migrate_public_bundle(
    source_bundle: Path,
    source_schema_root: Path,
    target_schema_root: Path,
    output: Path,
) -> dict[str, Any]:
    """Migrate one valid 0.5.0 bundle without fabricating observed-plane evidence."""
    if output.exists() and any(output.iterdir()):
        raise PublicMigrationError(f"Migration output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    source = _read_object(source_bundle)
    if (
        source.get("record_type") != "audit_bundle"
        or source.get("schema_version") != SOURCE_VERSION
    ):
        raise PublicMigrationError("Input must be an exact public 0.5.0 AuditBundle")
    _assert_source_versions(source)
    LocalSchemaRegistry(source_schema_root).validate(source)

    migrated = copy.deepcopy(source)
    _version_existing_records(migrated)
    _preserve_unknown_publication_surface_status(migrated)
    migrated["bundle_id"] = stable_id(
        "bundle-migration", str(source["bundle_id"]), SOURCE_VERSION, TARGET_VERSION
    )
    for field in OBSERVED_ARRAYS:
        migrated[field] = []
    migrated["storage_manifests"] = []

    target_registry = LocalSchemaRegistry(target_schema_root)
    for value in migrated.values():
        if not isinstance(value, list):
            continue
        for record in value:
            if isinstance(record, dict) and isinstance(record.get("record_type"), str):
                target_registry.validate(record)
    target_registry.validate(migrated)

    write_normalized_json(output / "audit.bundle.json", migrated)
    write_normalized_json(
        output / "MIGRATION_REPORT.json",
        {
            "source_schema_version": SOURCE_VERSION,
            "target_schema_version": TARGET_VERSION,
            "validation": "passed",
            "observed_plane_evidence_invented": False,
            "storage_manifest_carried_forward": False,
            "limitations": [
                "Public v0.5.0 did not contain the six observed-plane record types; their arrays remain empty.",
                "Public v0.5.0 CoverageRecord did not encode publication-surface resolution; migrated records preserve that omission as unresolved.",
                "The source StorageManifest was not carried forward because migrated bytes require a new manifest.",
            ],
        },
    )
    return migrated


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate a public 0.5.0 AuditBundle to 0.6.0")
    parser.add_argument("source_bundle", type=Path)
    parser.add_argument("--source-schemas", type=Path, required=True)
    parser.add_argument("--target-schemas", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bundle = migrate_public_bundle(
        args.source_bundle.resolve(),
        args.source_schemas.resolve(),
        args.target_schemas.resolve(),
        args.output.resolve(),
    )
    print(f"Migrated {bundle['bundle_id']} to schema {TARGET_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
