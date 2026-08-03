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


class CandidateMigrationError(ValueError):
    """Raised when v0.18 evidence cannot be projected to the fail-closed candidate."""


def _version(value: Any) -> Any:
    if isinstance(value, list):
        return [_version(item) for item in value]
    if isinstance(value, dict):
        migrated = {key: _version(item) for key, item in value.items()}
        if "schema_version" in migrated:
            if migrated["schema_version"] != SOURCE_VERSION:
                raise CandidateMigrationError(
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


def migrate_public_bundle_to_candidate(
    source_bundle: Path,
    source_schema_root: Path,
    target_schema_root: Path,
    output: Path,
) -> dict[str, Any]:
    """Project v0.18 to the nonpublic candidate without inventing promotion authority."""

    if output.exists() and any(output.iterdir()):
        raise CandidateMigrationError(f"Migration output must be absent or empty: {output}")
    source = json.loads(source_bundle.read_text(encoding="utf-8"))
    if not isinstance(source, dict) or source.get("record_type") != "audit_bundle":
        raise CandidateMigrationError("Input must be an AuditBundle object")
    if source.get("schema_version") != SOURCE_VERSION:
        raise CandidateMigrationError("Input must be an exact public v0.18.0 AuditBundle")
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
    parser = argparse.ArgumentParser(description="Project v0.18 bundle to v0.19 candidate")
    parser.add_argument("source_bundle", type=Path)
    parser.add_argument("--source-schema-root", type=Path, required=True)
    parser.add_argument("--target-schema-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    migrated = migrate_public_bundle_to_candidate(
        args.source_bundle.resolve(),
        args.source_schema_root.resolve(),
        args.target_schema_root.resolve(),
        args.output.resolve(),
    )
    print(f"Projected {migrated['bundle_id']} to schema candidate {TARGET_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
