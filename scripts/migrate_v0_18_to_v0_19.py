from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.schema_registry import LocalSchemaRegistry

SOURCE_VERSION = "0.18.0"
TARGET_VERSION = "0.19.0"


class PublicMigrationError(ValueError):
    """Raised when v0.18 evidence cannot be projected to accepted v0.19."""


def _version(value: Any) -> Any:
    if isinstance(value, list):
        return [_version(item) for item in value]
    if isinstance(value, dict):
        migrated = {key: _version(item) for key, item in value.items()}
        if "schema_version" in migrated:
            if migrated["schema_version"] != SOURCE_VERSION:
                raise PublicMigrationError(
                    f"Mixed or unsupported schema version {migrated['schema_version']!r}"
                )
            migrated["schema_version"] = TARGET_VERSION
        if migrated.get("record_type") in {
            "qualification_metric_set",
            "detector_qualification",
        }:
            migrated["binding_scope"] = None
        return migrated
    if isinstance(value, str):
        return value.replace(
            f"https://w3id.org/sc-referee/schema/v{SOURCE_VERSION}/",
            f"https://w3id.org/sc-referee/schema/v{TARGET_VERSION}/",
        )
    return value


def migrate_public_bundle(
    source_bundle: Path,
    source_schema_root: Path,
    target_schema_root: Path,
    output: Path,
) -> dict[str, Any]:
    """Project public v0.18 to accepted v0.19 without inventing promotion authority."""

    if output.exists() and any(output.iterdir()):
        raise PublicMigrationError(f"Migration output must be absent or empty: {output}")
    source = json.loads(source_bundle.read_text(encoding="utf-8"))
    if not isinstance(source, dict) or source.get("record_type") != "audit_bundle":
        raise PublicMigrationError("Input must be an AuditBundle object")
    if source.get("schema_version") != SOURCE_VERSION:
        raise PublicMigrationError("Input must be an exact public v0.18.0 AuditBundle")
    storage_manifests = source.get("storage_manifests")
    if not isinstance(storage_manifests, list) or storage_manifests:
        raise PublicMigrationError(
            "Input storage_manifests must be empty; migration will not discard retained integrity evidence"
        )
    LocalSchemaRegistry(source_schema_root).validate(source)

    migrated = _version(copy.deepcopy(source))
    migrated["storage_manifests"] = []
    target = LocalSchemaRegistry(target_schema_root)
    for value in migrated.values():
        if not isinstance(value, list):
            continue
        for record in value:
            if isinstance(record, dict) and isinstance(record.get("record_type"), str):
                target.validate(record)
    target.validate(migrated)

    output.mkdir(parents=True, exist_ok=True)
    write_normalized_json_once(output / "audit.bundle.json", migrated)
    write_normalized_json_once(
        output / "MIGRATION_REPORT.json",
        {
            "binding_scope_invented": False,
            "numeric_threshold_invented": False,
            "qualification_invented": False,
            "finding_authority_created": False,
            "execution_launched": False,
            "storage_manifest_carried_forward": False,
            "source_schema_version": SOURCE_VERSION,
            "target_schema_version": TARGET_VERSION,
            "validation": "passed",
        },
    )
    return migrated


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate public v0.18 bundle to v0.19")
    parser.add_argument("source_bundle", type=Path)
    parser.add_argument("--source-schema-root", type=Path, required=True)
    parser.add_argument("--target-schema-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    migrated = migrate_public_bundle(
        args.source_bundle.resolve(),
        args.source_schema_root.resolve(),
        args.target_schema_root.resolve(),
        args.output.resolve(),
    )
    print(f"Migrated {migrated['bundle_id']} to public schema {TARGET_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
