from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.records.normalization import write_normalized_json
from sc_referee.records.schema_registry import LocalSchemaRegistry

SOURCE_VERSION = "0.10.0"
TARGET_VERSION = "0.11.0"


class PublicMigrationError(ValueError):
    """Raised when v0.10 evidence cannot be migrated without invention."""


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


def _migrate_case_outcomes(bundle: dict[str, Any]) -> None:
    for outcome in bundle.get("detector_case_outcomes", []):
        prior_id = str(outcome["case_outcome_id"])
        extensions = outcome.setdefault("extensions", {})
        extensions["x-v0-10-case-outcome-id"] = prior_id
        extensions["x-v0-10-metric-eligible"] = bool(outcome["metric_eligible"])
        extensions["x-v0-10-promotion-evidence-eligible"] = bool(
            outcome["promotion_evidence_eligible"]
        )
        outcome["case_outcome_id"] = stable_id(
            "detector-case-outcome-migration",
            prior_id,
            SOURCE_VERSION,
            TARGET_VERSION,
            "legacy-source-projection-unavailable",
        )
        outcome["metric_input_status"] = "legacy_source_projection_unavailable"
        outcome["detector_result_outcomes"] = []
        outcome["metric_eligible"] = False
        outcome["promotion_evidence_eligible"] = False


def _clear_legacy_metric_links(bundle: dict[str, Any]) -> None:
    for qualification in bundle.get("detector_qualifications", []):
        prior = qualification.get("quantitative_metrics")
        if prior is None:
            continue
        qualification.setdefault("extensions", {})["x-v0-10-unverified-quantitative-metrics"] = (
            copy.deepcopy(prior)
        )
        qualification["quantitative_metrics"] = None


def _validate_bundle_records(bundle: dict[str, Any], registry: LocalSchemaRegistry) -> None:
    for value in bundle.values():
        if not isinstance(value, list):
            continue
        for record in value:
            if isinstance(record, dict) and isinstance(record.get("record_type"), str):
                registry.validate(record)
    registry.validate(bundle)


def migrate_public_bundle(
    source_bundle: Path,
    source_schema_root: Path,
    target_schema_root: Path,
    output: Path,
) -> dict[str, Any]:
    """Migrate one valid v0.10.0 AuditBundle without inventing metric evidence."""

    if output.exists() and any(output.iterdir()):
        raise PublicMigrationError(f"Migration output must be absent or empty: {output}")
    source = _read_object(source_bundle)
    if (
        source.get("record_type") != "audit_bundle"
        or source.get("schema_version") != SOURCE_VERSION
    ):
        raise PublicMigrationError("Input must be an exact public v0.10.0 AuditBundle")
    _assert_source_versions(source)
    LocalSchemaRegistry(source_schema_root).validate(source)

    legacy_metric_sets = copy.deepcopy(source.get("qualification_metric_sets", []))
    migrated = copy.deepcopy(source)
    _version_existing_records(migrated)
    migrated["bundle_id"] = stable_id(
        "bundle-migration", str(source["bundle_id"]), SOURCE_VERSION, TARGET_VERSION
    )
    _migrate_case_outcomes(migrated)
    _clear_legacy_metric_links(migrated)
    migrated["qualification_metric_sets"] = []
    if legacy_metric_sets:
        migrated.setdefault("extensions", {})["x-v0-10-unverified-qualification-metric-sets"] = (
            legacy_metric_sets
        )
    migrated["storage_manifests"] = []

    _validate_bundle_records(migrated, LocalSchemaRegistry(target_schema_root))

    output.mkdir(parents=True, exist_ok=True)
    write_normalized_json(output / "audit.bundle.json", migrated)
    write_normalized_json(
        output / "MIGRATION_REPORT.json",
        {
            "source_schema_version": SOURCE_VERSION,
            "target_schema_version": TARGET_VERSION,
            "validation": "passed",
            "detector_result_states_invented": False,
            "evaluation_candidates_invented": False,
            "opportunity_projections_invented": False,
            "equivalence_decisions_invented": False,
            "qualification_metrics_invented": False,
            "legacy_metric_sets_authoritative": False,
            "storage_manifest_carried_forward": False,
            "limitations": [
                "Legacy v0.10.0 case outcomes do not preserve exact per-result metric projections.",
                "Legacy v0.10.0 metric sets do not establish the closed v0.11.0 formulas or counter stream.",
                "The source StorageManifest was not carried forward because migrated bytes require a new manifest.",
            ],
        },
    )
    return migrated


def report_standalone_metric_set(
    source_metric_set: Path,
    source_schema_root: Path,
    output: Path,
) -> dict[str, Any]:
    """Preserve and report, but do not migrate, one standalone v0.10 metric set."""

    if output.exists() and any(output.iterdir()):
        raise PublicMigrationError(f"Migration output must be absent or empty: {output}")
    source = _read_object(source_metric_set)
    if (
        source.get("record_type") != "qualification_metric_set"
        or source.get("schema_version") != SOURCE_VERSION
    ):
        raise PublicMigrationError("Input must be an exact public v0.10.0 QualificationMetricSet")
    _assert_source_versions(source)
    LocalSchemaRegistry(source_schema_root).validate(source)

    report = {
        "source_schema_version": SOURCE_VERSION,
        "target_schema_version": TARGET_VERSION,
        "source_record_type": "qualification_metric_set",
        "source_semantic_digest": semantic_digest(source),
        "source_file_sha256": f"sha256:{hashlib.sha256(source_metric_set.read_bytes()).hexdigest()}",
        "authoritative_v0_11_record_emitted": False,
        "classification": "non_authoritative_legacy_evidence",
        "reason": (
            "v0.10.0 does not preserve exact per-result opportunities or the closed v0.11.0 "
            "metric and bootstrap semantics."
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    write_normalized_json(output / "qualification-metric-set.v0.10.0.json", source)
    write_normalized_json(output / "MIGRATION_REPORT.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate public sc-referee v0.10.0 evidence to v0.11.0"
    )
    parser.add_argument("source_record", type=Path)
    parser.add_argument("--source-schemas", type=Path, required=True)
    parser.add_argument("--target-schemas", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = _read_object(args.source_record.resolve())
    if source.get("record_type") == "audit_bundle":
        if args.target_schemas is None:
            parser.error("--target-schemas is required for AuditBundle migration")
        bundle = migrate_public_bundle(
            args.source_record.resolve(),
            args.source_schemas.resolve(),
            args.target_schemas.resolve(),
            args.output.resolve(),
        )
        print(f"Migrated {bundle['bundle_id']} to schema {TARGET_VERSION}")
        return 0
    if source.get("record_type") == "qualification_metric_set":
        report_standalone_metric_set(
            args.source_record.resolve(),
            args.source_schemas.resolve(),
            args.output.resolve(),
        )
        print("Preserved non-authoritative legacy v0.10.0 QualificationMetricSet evidence")
        return 0
    raise PublicMigrationError("Input must be a v0.10.0 AuditBundle or QualificationMetricSet")


if __name__ == "__main__":
    raise SystemExit(main())
