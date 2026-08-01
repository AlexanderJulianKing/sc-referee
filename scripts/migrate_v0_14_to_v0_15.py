from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.schema_registry import LocalSchemaRegistry

SOURCE_VERSION = "0.14.0"
TARGET_VERSION = "0.15.0"


class PublicMigrationError(ValueError):
    """Raised when v0.14 evidence cannot migrate without invented static authority."""


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
        return [_version_existing_records(item) for item in value]
    if isinstance(value, dict):
        migrated = {key: _version_existing_records(item) for key, item in value.items()}
        if "schema_version" in migrated:
            migrated["schema_version"] = TARGET_VERSION
        return migrated
    if isinstance(value, str):
        return value.replace(
            f"https://w3id.org/sc-referee/schema/v{SOURCE_VERSION}/",
            f"https://w3id.org/sc-referee/schema/v{TARGET_VERSION}/",
        )
    return value


def _proof_family(fixture_kind: str) -> str:
    families = {
        "verified_good_fixture": "clean_execution",
        "hard_negative_fixture": "clean_execution",
        "scope_verified_good": "documented_external_execution",
        "positive_issue_fixture": "positive_issue",
        "ambiguous_fixture": "excluded_ambiguous",
    }
    try:
        return families[fixture_kind]
    except KeyError as error:
        raise PublicMigrationError(f"Unknown v0.14 fixture kind {fixture_kind!r}") from error


def _migrate_outcomes(bundle: dict[str, Any]) -> None:
    fixtures = {
        str(fixture["fixture_id"]): fixture for fixture in bundle.get("benchmark_fixtures", [])
    }
    for outcome in bundle.get("detector_case_outcomes", []):
        fixture_ref = outcome.get("fixture_ref")
        fixture_id = str(fixture_ref.get("record_id", "")) if isinstance(fixture_ref, dict) else ""
        fixture = fixtures.get(fixture_id)
        if fixture is None:
            raise PublicMigrationError(
                f"DetectorCaseOutcome fixture {fixture_id!r} is absent after migration"
            )
        old_id = str(outcome["case_outcome_id"])
        outcome["fixture_semantic_digest"] = semantic_digest(fixture)
        outcome["qualification_proof_family"] = _proof_family(str(fixture["fixture_kind"]))
        outcome["static_qualification_proof_ref"] = None
        outcome.setdefault("extensions", {})["x-v0-14-case-outcome-id"] = old_id
        outcome["case_outcome_id"] = stable_id(
            "detector-case-outcome-static-proof-migration",
            old_id,
            SOURCE_VERSION,
            TARGET_VERSION,
            str(outcome["fixture_semantic_digest"]),
        )


def _remove_unstratified_metrics(bundle: dict[str, Any]) -> int:
    metric_sets = copy.deepcopy(bundle.get("qualification_metric_sets", []))
    if metric_sets:
        bundle.setdefault("extensions", {})["x-v0-14-unstratified-qualification-metric-sets"] = (
            metric_sets
        )
    bundle["qualification_metric_sets"] = []
    for qualification in bundle.get("detector_qualifications", []):
        prior = qualification.get("quantitative_metrics")
        if prior is not None:
            qualification.setdefault("extensions", {})[
                "x-v0-14-unstratified-quantitative-metrics"
            ] = copy.deepcopy(prior)
        qualification["quantitative_metrics"] = None
        qualification["qualification_proof_families"] = []
        qualification["static_scope_disclosure"] = None
        qualification["safety_gates"]["proof_families_stratified"] = False
    return len(metric_sets)


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
    """Migrate one v0.14 AuditBundle without inventing a static proof or authority."""

    if output.exists() and any(output.iterdir()):
        raise PublicMigrationError(f"Migration output must be absent or empty: {output}")
    source = _read_object(source_bundle)
    if (
        source.get("record_type") != "audit_bundle"
        or source.get("schema_version") != SOURCE_VERSION
    ):
        raise PublicMigrationError("Input must be an exact public v0.14.0 AuditBundle")
    _assert_source_versions(source)
    LocalSchemaRegistry(source_schema_root).validate(source)

    migrated = _version_existing_records(copy.deepcopy(source))
    migrated["bundle_id"] = stable_id(
        "bundle-migration", str(source["bundle_id"]), SOURCE_VERSION, TARGET_VERSION
    )
    migrated["static_qualification_profiles"] = []
    migrated["static_qualification_proofs"] = []
    _migrate_outcomes(migrated)
    removed_metric_count = _remove_unstratified_metrics(migrated)
    migrated["storage_manifests"] = []

    _validate_bundle_records(migrated, LocalSchemaRegistry(target_schema_root))
    output.mkdir(parents=True, exist_ok=True)
    write_normalized_json_once(output / "audit.bundle.json", migrated)
    write_normalized_json_once(
        output / "MIGRATION_REPORT.json",
        {
            "execution_launched": False,
            "finding_authority_created": False,
            "limitations": [
                "Static proof-family evidence cannot be inferred from a v0.14 bundle.",
                "Unstratified metric sets are retained only as non-authoritative extensions.",
                "Storage manifests are cleared because canonical bytes changed.",
            ],
            "removed_unstratified_metric_set_count": removed_metric_count,
            "source_schema_version": SOURCE_VERSION,
            "static_fixture_created": False,
            "static_profile_created": False,
            "static_proof_created": False,
            "storage_manifest_carried_forward": False,
            "target_schema_version": TARGET_VERSION,
            "validation": "passed",
        },
    )
    return migrated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate a public sc-referee v0.14.0 AuditBundle to v0.15.0"
    )
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
    print(f"Migrated {migrated['bundle_id']} to schema {TARGET_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
