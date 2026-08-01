from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.schema_registry import LocalSchemaRegistry

SOURCE_VERSION = "0.15.0"
TARGET_VERSION = "0.16.0"
STATIC_KINDS = {"static_scope_verified_good", "static_scope_hard_negative"}


class PublicMigrationError(ValueError):
    """Raised when v0.15 evidence cannot migrate without invented profile authority."""


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


def _remove_static_evidence(bundle: dict[str, Any], source: dict[str, Any]) -> set[str]:
    removed_fixture_ids = {
        str(fixture["fixture_id"])
        for fixture in bundle.get("benchmark_fixtures", [])
        if fixture.get("fixture_kind") in STATIC_KINDS
    }
    legacy = {
        "static_qualification_profiles": copy.deepcopy(
            source.get("static_qualification_profiles", [])
        ),
        "static_qualification_proofs": copy.deepcopy(source.get("static_qualification_proofs", [])),
        "benchmark_fixtures": [
            copy.deepcopy(value)
            for value in source.get("benchmark_fixtures", [])
            if value.get("fixture_kind") in STATIC_KINDS
        ],
        "detector_case_outcomes": [
            copy.deepcopy(value)
            for value in source.get("detector_case_outcomes", [])
            if value.get("fixture_ref", {}).get("record_id") in removed_fixture_ids
        ],
    }
    if any(legacy.values()):
        bundle.setdefault("extensions", {})["x-v0-15-static-qualification-evidence"] = legacy
    bundle["static_qualification_profiles"] = []
    bundle["static_qualification_proofs"] = []
    bundle["benchmark_fixtures"] = [
        value
        for value in bundle.get("benchmark_fixtures", [])
        if str(value.get("fixture_id")) not in removed_fixture_ids
    ]
    bundle["detector_case_outcomes"] = [
        value
        for value in bundle.get("detector_case_outcomes", [])
        if value.get("fixture_ref", {}).get("record_id") not in removed_fixture_ids
    ]
    return removed_fixture_ids


def _refresh_remaining_outcomes(bundle: dict[str, Any]) -> None:
    fixtures = {
        str(fixture["fixture_id"]): fixture for fixture in bundle.get("benchmark_fixtures", [])
    }
    for outcome in bundle.get("detector_case_outcomes", []):
        fixture_id = str(outcome.get("fixture_ref", {}).get("record_id", ""))
        fixture = fixtures.get(fixture_id)
        if fixture is None:
            raise PublicMigrationError(
                f"DetectorCaseOutcome fixture {fixture_id!r} is absent after migration"
            )
        old_id = str(outcome["case_outcome_id"])
        outcome["fixture_semantic_digest"] = semantic_digest(fixture)
        outcome.setdefault("extensions", {})["x-v0-15-case-outcome-id"] = old_id
        outcome["case_outcome_id"] = stable_id(
            "detector-case-outcome-second-static-profile-migration",
            old_id,
            SOURCE_VERSION,
            TARGET_VERSION,
            str(outcome["fixture_semantic_digest"]),
        )


def _remove_authoritative_metrics(bundle: dict[str, Any], source: dict[str, Any]) -> int:
    metrics = copy.deepcopy(source.get("qualification_metric_sets", []))
    if metrics:
        bundle.setdefault("extensions", {})["x-v0-15-unverified-qualification-metric-sets"] = (
            metrics
        )
    bundle["qualification_metric_sets"] = []
    for qualification in bundle.get("detector_qualifications", []):
        prior = qualification.get("quantitative_metrics")
        if prior is not None:
            qualification.setdefault("extensions", {})[
                "x-v0-15-unverified-quantitative-metrics"
            ] = copy.deepcopy(prior)
        qualification["quantitative_metrics"] = None
        qualification["qualification_proof_families"] = []
        qualification["static_scope_disclosure"] = None
        qualification["safety_gates"]["proof_families_stratified"] = False
    return len(metrics)


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
    """Migrate v0.15 without inventing a second static-profile proof."""

    if output.exists() and any(output.iterdir()):
        raise PublicMigrationError(f"Migration output must be absent or empty: {output}")
    source = _read_object(source_bundle)
    if (
        source.get("record_type") != "audit_bundle"
        or source.get("schema_version") != SOURCE_VERSION
    ):
        raise PublicMigrationError("Input must be an exact public v0.15.0 AuditBundle")
    _assert_source_versions(source)
    LocalSchemaRegistry(source_schema_root).validate(source)

    migrated = _version_existing_records(copy.deepcopy(source))
    migrated["bundle_id"] = stable_id(
        "bundle-migration", str(source["bundle_id"]), SOURCE_VERSION, TARGET_VERSION
    )
    removed_fixture_ids = _remove_static_evidence(migrated, source)
    _refresh_remaining_outcomes(migrated)
    removed_metric_count = _remove_authoritative_metrics(migrated, source)
    migrated["storage_manifests"] = []

    _validate_bundle_records(migrated, LocalSchemaRegistry(target_schema_root))
    output.mkdir(parents=True, exist_ok=True)
    write_normalized_json_once(output / "audit.bundle.json", migrated)
    write_normalized_json_once(
        output / "MIGRATION_REPORT.json",
        {
            "answer_invented": False,
            "execution_launched": False,
            "finding_authority_created": False,
            "limitations": [
                "v0.15 static evidence remains only as namespaced historical payload.",
                "Private source-validation closure is not reconstructed by migration.",
                "Storage manifests are cleared because canonical bytes changed.",
            ],
            "profile_or_proof_invented": False,
            "removed_authoritative_metric_set_count": removed_metric_count,
            "removed_static_fixture_count": len(removed_fixture_ids),
            "source_schema_version": SOURCE_VERSION,
            "storage_manifest_carried_forward": False,
            "target_schema_version": TARGET_VERSION,
            "validation": "passed",
        },
    )
    return migrated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate a public sc-referee v0.15.0 AuditBundle to v0.16.0"
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
