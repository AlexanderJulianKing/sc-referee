from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import stable_id
from sc_referee.records.normalization import write_normalized_json
from sc_referee.records.schema_registry import LocalSchemaRegistry

SOURCE_VERSION = "0.7.0"
TARGET_VERSION = "0.8.0"
NEW_ARRAYS = (
    "data_assets",
    "variables",
    "analysis_decisions",
    "selection_envelopes",
    "executions",
    "environments",
)
GRADE_DIMENSIONS = (
    "report_origin",
    "result_origin",
    "computational_origin",
    "input_origin",
    "execution_origin",
    "semantic_origin",
)


class PublicMigrationError(ValueError):
    """Raised when a public bundle cannot be migrated without inventing history."""


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


def _unavailable_grade(dimension: str) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "record_refs": [],
        "source_refs": [],
        "limitations": [
            f"Public v{SOURCE_VERSION} did not preserve an independent {dimension} grade."
        ],
    }


def _migrate_claims(bundle: dict[str, Any]) -> None:
    for claim in bundle.get("claims", []):
        lineage = claim["lineage"]
        prior = lineage["status"]
        lineage["grades"] = {
            dimension: _unavailable_grade(dimension) for dimension in GRADE_DIMENSIONS
        }
        lineage["status"] = "unavailable"
        claim.setdefault("extensions", {})["x-v0-7-aggregate-lineage-status"] = prior


def _migrate_coverage(bundle: dict[str, Any]) -> None:
    for coverage in bundle.get("coverage_records", []):
        claim_coverage = coverage["claim_coverage"]
        total = int(claim_coverage["claims_total"])
        claim_coverage["claims_with_complete_lineage"] = 0
        claim_coverage["lineage_grade_counts"] = {
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


def migrate_public_bundle(
    source_bundle: Path,
    source_schema_root: Path,
    target_schema_root: Path,
    output: Path,
) -> dict[str, Any]:
    """Migrate one valid 0.7.0 bundle without fabricating lineage-plane history."""

    if output.exists() and any(output.iterdir()):
        raise PublicMigrationError(f"Migration output must be absent or empty: {output}")
    source = _read_object(source_bundle)
    if (
        source.get("record_type") != "audit_bundle"
        or source.get("schema_version") != SOURCE_VERSION
    ):
        raise PublicMigrationError("Input must be an exact public 0.7.0 AuditBundle")
    _assert_source_versions(source)
    LocalSchemaRegistry(source_schema_root).validate(source)

    migrated = copy.deepcopy(source)
    _version_existing_records(migrated)
    migrated["bundle_id"] = stable_id(
        "bundle-migration", str(source["bundle_id"]), SOURCE_VERSION, TARGET_VERSION
    )
    for array_name in NEW_ARRAYS:
        migrated[array_name] = []
    _migrate_claims(migrated)
    _migrate_coverage(migrated)
    migrated["storage_manifests"] = []

    target_registry = LocalSchemaRegistry(target_schema_root)
    for value in migrated.values():
        if not isinstance(value, list):
            continue
        for record in value:
            if isinstance(record, dict) and isinstance(record.get("record_type"), str):
                target_registry.validate(record)
    target_registry.validate(migrated)

    output.mkdir(parents=True, exist_ok=True)
    write_normalized_json(output / "audit.bundle.json", migrated)
    write_normalized_json(
        output / "MIGRATION_REPORT.json",
        {
            "source_schema_version": SOURCE_VERSION,
            "target_schema_version": TARGET_VERSION,
            "validation": "passed",
            "observed_graph_history_invented": False,
            "prior_aggregate_status_preserved": True,
            "storage_manifest_carried_forward": False,
            "limitations": [
                "Public v0.7.0 did not preserve six independent Claim lineage grades.",
                "All six grades and the new aggregate are unavailable after migration.",
                "No DataAsset, Variable, AnalysisDecision, SelectionEnvelope, Execution, or Environment record was inferred.",
                "The source StorageManifest was not carried forward because migrated bytes require a new manifest.",
            ],
        },
    )
    return migrated


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate a public 0.7.0 AuditBundle to 0.8.0")
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
