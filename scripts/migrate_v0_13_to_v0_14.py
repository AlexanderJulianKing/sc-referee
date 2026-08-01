from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.schema_registry import LocalSchemaRegistry

SOURCE_VERSION = "0.13.0"
TARGET_VERSION = "0.14.0"


class PublicMigrationError(ValueError):
    """Raised when v0.13 evidence cannot migrate without invented WorkItem authority."""


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


def _migrate_work_item(work_item: dict[str, Any]) -> None:
    packet = work_item.get("packet")
    if not isinstance(packet, dict):
        raise PublicMigrationError("v0.13 WorkItem packet is malformed")
    packet["packet_kind"] = "semantic_or_auditor_work_v1"
    packet.pop("packet_digest", None)
    packet["packet_digest"] = semantic_digest(packet)


def _migrate_authorization(authorization: dict[str, Any]) -> None:
    scope = authorization.get("scope")
    if not isinstance(scope, dict):
        raise PublicMigrationError("v0.13 authorization scope is malformed")
    scope["work_item_binding_status"] = "legacy_work_item_semantics_unavailable"
    scope["work_item_semantic_digest"] = None
    scope["purpose"] = None
    scope["target_refs"] = None


def _migrate_execution(execution: dict[str, Any]) -> bool:
    if execution.get("execution_kind") != "project_workflow":
        return False
    execution["authorization_evidence_status"] = "legacy_authorization_projection_unavailable"
    execution["project_execution"] = None
    return True


def _fixture_depends_on_execution(fixture: dict[str, Any], legacy_execution_ids: set[str]) -> bool:
    proof = fixture.get("proof_evidence")
    if not isinstance(proof, dict):
        return False
    public_inputs = proof.get("public_inputs")
    if not isinstance(public_inputs, dict):
        return False
    entries = public_inputs.get("executions", [])
    if not isinstance(entries, list):
        return False
    execution_ids = {
        str(entry.get("record_ref", {}).get("record_id", ""))
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("record_ref"), dict)
    }
    return bool(execution_ids & legacy_execution_ids)


def _downgrade_fixture(fixture: dict[str, Any]) -> None:
    fixture["qualification_proof_status"] = "legacy_proof_projection_unavailable"
    fixture["proof_evidence"] = None


def _migrate_dependent_outcomes(bundle: dict[str, Any], downgraded_fixture_ids: set[str]) -> bool:
    if not downgraded_fixture_ids:
        return False
    fixtures = {
        str(fixture["fixture_id"]): fixture for fixture in bundle.get("benchmark_fixtures", [])
    }
    changed = False
    for outcome in bundle.get("detector_case_outcomes", []):
        fixture_id = str(outcome.get("fixture_ref", {}).get("record_id", ""))
        if fixture_id not in downgraded_fixture_ids:
            continue
        fixture = fixtures.get(fixture_id)
        if fixture is None:
            continue
        prior_id = str(outcome["case_outcome_id"])
        outcome["fixture_semantic_digest"] = semantic_digest(fixture)
        outcome["qualification_proof_status"] = fixture["qualification_proof_status"]
        outcome["metric_eligible"] = False
        outcome["promotion_evidence_eligible"] = False
        outcome.setdefault("extensions", {})["x-v0-13-case-outcome-id"] = prior_id
        outcome["case_outcome_id"] = stable_id(
            "detector-case-outcome-work-item-migration",
            prior_id,
            SOURCE_VERSION,
            TARGET_VERSION,
            str(outcome["fixture_semantic_digest"]),
        )
        changed = True
    return changed


def _remove_authoritative_metrics(bundle: dict[str, Any]) -> None:
    metric_sets = copy.deepcopy(bundle.get("qualification_metric_sets", []))
    if metric_sets:
        bundle.setdefault("extensions", {})["x-v0-13-unverified-qualification-metric-sets"] = (
            metric_sets
        )
    bundle["qualification_metric_sets"] = []
    for qualification in bundle.get("detector_qualifications", []):
        prior = qualification.get("quantitative_metrics")
        if prior is not None:
            qualification.setdefault("extensions", {})[
                "x-v0-13-unverified-quantitative-metrics"
            ] = copy.deepcopy(prior)
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
    """Migrate one v0.13 AuditBundle without inventing a launchable WorkItem binding."""

    if output.exists() and any(output.iterdir()):
        raise PublicMigrationError(f"Migration output must be absent or empty: {output}")
    source = _read_object(source_bundle)
    if (
        source.get("record_type") != "audit_bundle"
        or source.get("schema_version") != SOURCE_VERSION
    ):
        raise PublicMigrationError("Input must be an exact public v0.13.0 AuditBundle")
    _assert_source_versions(source)
    LocalSchemaRegistry(source_schema_root).validate(source)

    migrated = _version_existing_records(copy.deepcopy(source))
    migrated["bundle_id"] = stable_id(
        "bundle-migration", str(source["bundle_id"]), SOURCE_VERSION, TARGET_VERSION
    )
    for work_item in migrated.get("work_items", []):
        _migrate_work_item(work_item)
    for authorization in migrated.get("project_execution_authorizations", []):
        _migrate_authorization(authorization)

    legacy_execution_ids: set[str] = set()
    for execution in migrated.get("executions", []):
        if _migrate_execution(execution):
            legacy_execution_ids.add(str(execution["execution_id"]))

    downgraded_fixture_ids: set[str] = set()
    for fixture in migrated.get("benchmark_fixtures", []):
        if _fixture_depends_on_execution(fixture, legacy_execution_ids):
            _downgrade_fixture(fixture)
            downgraded_fixture_ids.add(str(fixture["fixture_id"]))
    outcomes_changed = _migrate_dependent_outcomes(migrated, downgraded_fixture_ids)
    if downgraded_fixture_ids or outcomes_changed:
        _remove_authoritative_metrics(migrated)
    migrated["storage_manifests"] = []

    _validate_bundle_records(migrated, LocalSchemaRegistry(target_schema_root))
    output.mkdir(parents=True, exist_ok=True)
    write_normalized_json_once(output / "audit.bundle.json", migrated)
    write_normalized_json_once(
        output / "MIGRATION_REPORT.json",
        {
            "authorization_authority_invented": False,
            "controller_registry_entry_created": False,
            "downgraded_fixture_count": len(downgraded_fixture_ids),
            "execution_launched": False,
            "execution_work_item_invented": False,
            "legacy_authorization_count": len(migrated.get("project_execution_authorizations", [])),
            "legacy_project_execution_count": len(legacy_execution_ids),
            "limitations": [
                "A v0.13 authorization has no verified v0.14 WorkItem semantic binding.",
                "Migrated public records create no private controller registry state.",
                "Storage manifests are cleared because canonical bytes changed.",
            ],
            "source_schema_version": SOURCE_VERSION,
            "storage_manifest_carried_forward": False,
            "target_schema_version": TARGET_VERSION,
            "validation": "passed",
            "work_item_digest_invented": False,
        },
    )
    return migrated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate a public sc-referee v0.13.0 AuditBundle to v0.14.0"
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
