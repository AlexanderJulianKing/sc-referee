from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import stable_id
from sc_referee.records.normalization import write_normalized_json
from sc_referee.records.schema_registry import LocalSchemaRegistry

SOURCE_VERSION = "0.9.0"
TARGET_VERSION = "0.10.0"


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


def _migrate_fixtures(bundle: dict[str, Any]) -> None:
    for fixture in bundle.get("benchmark_fixtures", []):
        # A public legacy fixture is necessarily known to evaluator developers. Treating it as
        # held out would invent an access-control fact that v0.9 did not preserve.
        fixture["corpus_partition"] = "public_development"


def _migrate_adjudications(bundle: dict[str, Any]) -> None:
    for adjudication in bundle.get("benchmark_adjudications", []):
        prior_refs = copy.deepcopy(adjudication.get("stage3_detector_comparison_refs", []))
        if prior_refs:
            extensions = adjudication.setdefault("extensions", {})
            extensions["x-v0-9-stage3-detector-comparison-refs"] = prior_refs
        adjudication["stage3_detector_comparison_refs"] = []


def _migrate_qualifications(bundle: dict[str, Any]) -> None:
    for qualification in bundle.get("detector_qualifications", []):
        extensions = qualification.setdefault("extensions", {})
        prior_metrics = copy.deepcopy(qualification.get("quantitative_metrics"))
        if prior_metrics is not None:
            extensions["x-v0-9-quantitative-metrics"] = prior_metrics
        qualification["quantitative_metrics"] = None

        if qualification.get("outcome") != "promoted":
            continue
        extensions["x-v0-9-outcome"] = qualification["outcome"]
        extensions["x-v0-9-effective-maturity"] = qualification["effective_maturity"]
        extensions["x-v0-9-qualification-basis-disclosure"] = qualification[
            "qualification_basis_disclosure"
        ]
        qualification["outcome"] = "deferred"
        qualification["effective_maturity"] = "experimental"
        qualification["qualification_basis_disclosure"] = (
            "Legacy v0.9.0 promotion is deferred because it lacks typed Stage-3 case outcomes, "
            "cluster-aware metric evidence, and an accepted numeric threshold policy."
        )


def migrate_public_bundle(
    source_bundle: Path,
    source_schema_root: Path,
    target_schema_root: Path,
    output: Path,
) -> dict[str, Any]:
    """Migrate one valid v0.9.0 bundle without inventing Stage-3 evidence."""

    if output.exists() and any(output.iterdir()):
        raise PublicMigrationError(f"Migration output must be absent or empty: {output}")
    source = _read_object(source_bundle)
    if (
        source.get("record_type") != "audit_bundle"
        or source.get("schema_version") != SOURCE_VERSION
    ):
        raise PublicMigrationError("Input must be an exact public v0.9.0 AuditBundle")
    _assert_source_versions(source)
    LocalSchemaRegistry(source_schema_root).validate(source)

    migrated = copy.deepcopy(source)
    _version_existing_records(migrated)
    migrated["bundle_id"] = stable_id(
        "bundle-migration", str(source["bundle_id"]), SOURCE_VERSION, TARGET_VERSION
    )
    migrated["detector_evaluation_candidates"] = []
    migrated["stage3_comparison_reviews"] = []
    migrated["detector_case_outcomes"] = []
    migrated["qualification_metric_sets"] = []
    _migrate_fixtures(migrated)
    _migrate_adjudications(migrated)
    _migrate_qualifications(migrated)
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
            "evaluation_candidates_invented": False,
            "detector_root_equivalence_invented": False,
            "case_outcomes_invented": False,
            "qualification_metrics_invented": False,
            "legacy_promotions_retained": False,
            "held_out_status_invented": False,
            "legacy_stage3_refs_authoritative": False,
            "storage_manifest_carried_forward": False,
            "limitations": [
                "All legacy fixtures are classified public_development because v0.9.0 did not preserve a qualification partition.",
                "Legacy Stage-3 references remain opaque migration metadata and do not establish root-cause equivalence.",
                "Legacy open-ended quantitative metrics do not become typed QualificationMetricSet records.",
                "Legacy promoted qualifications are deferred and experimental until the accepted Stage-3 protocol is rerun.",
                "The source StorageManifest was not carried forward because migrated bytes require a new manifest.",
            ],
        },
    )
    return migrated


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate a public v0.9.0 AuditBundle to v0.10.0")
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
