from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.schema_registry import LocalSchemaRegistry

SOURCE_VERSION = "0.12.0"
TARGET_VERSION = "0.13.0"


class PublicMigrationError(ValueError):
    """Raised when v0.12 evidence cannot migrate without invented execution authority."""


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


def _migrate_capability(capability: dict[str, Any]) -> bool:
    previously_supported = bool(capability.get("project_code_execution_supported"))
    previously_rootless = bool(capability.get("rootless_verified"))
    if previously_supported or previously_rootless:
        capability.setdefault("extensions", {})["x-v0-12-claimed-capability"] = {
            "project_code_execution_supported": previously_supported,
            "rootless_verified": previously_rootless,
        }
    capability["project_code_execution_supported"] = False
    capability["rootless_verified"] = False
    capability["capability_evidence_status"] = (
        "legacy_probe_projection_unavailable"
        if previously_supported or previously_rootless
        else "not_supported"
    )
    capability["capability_evidence"] = None
    controls = capability["controls"]
    controls["no_new_privileges"] = False
    controls["open_file_limits_enforced"] = False
    controls["wall_time_enforced"] = False
    controls["writable_bytes_enforced"] = False
    return previously_supported or previously_rootless


def _migrate_execution(execution: dict[str, Any]) -> bool:
    execution_kind = execution.get("execution_kind")
    if execution_kind == "project_workflow":
        execution["authorization_evidence_status"] = "legacy_authorization_projection_unavailable"
        legacy = True
    elif execution_kind == "imported":
        execution["authorization_evidence_status"] = "imported"
        legacy = False
    else:
        execution["authorization_evidence_status"] = "not_required"
        legacy = False
    execution["project_execution"] = None
    return legacy


def _record_id(record: dict[str, Any]) -> str | None:
    for key, value in record.items():
        if key.endswith("_id") and key not in {"audit_run_id"} and isinstance(value, str):
            return value
    return None


def _record_index(bundle: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for value in bundle.values():
        if not isinstance(value, list):
            continue
        for record in value:
            if not isinstance(record, dict) or not isinstance(record.get("record_type"), str):
                continue
            record_id = _record_id(record)
            if record_id is not None:
                index[(str(record["record_type"]), record_id)] = record
    return index


def _refresh_fixture_public_digests(
    fixture: dict[str, Any], index: dict[tuple[str, str], dict[str, Any]]
) -> None:
    proof = fixture.get("proof_evidence")
    if not isinstance(proof, dict):
        return
    public_inputs = proof.get("public_inputs")
    if not isinstance(public_inputs, dict):
        return
    for entries in public_inputs.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("record_ref"), dict):
                continue
            ref = entry["record_ref"]
            record = index.get((str(ref.get("record_type", "")), str(ref.get("record_id", ""))))
            if record is not None:
                entry["semantic_digest"] = semantic_digest(record)


def _fixture_depends_on_legacy_execution(
    fixture: dict[str, Any], legacy_execution_ids: set[str], legacy_capability_ids: set[str]
) -> bool:
    proof = fixture.get("proof_evidence")
    if not isinstance(proof, dict):
        return False
    public_inputs = proof.get("public_inputs")
    if not isinstance(public_inputs, dict):
        return False

    def ids(collection: str) -> set[str]:
        entries = public_inputs.get(collection, [])
        if not isinstance(entries, list):
            return set()
        return {
            str(entry.get("record_ref", {}).get("record_id", ""))
            for entry in entries
            if isinstance(entry, dict) and isinstance(entry.get("record_ref"), dict)
        }

    return bool(ids("executions") & legacy_execution_ids) or bool(
        ids("sandbox_capabilities") & legacy_capability_ids
    )


def _downgrade_fixture(fixture: dict[str, Any]) -> None:
    fixture["qualification_proof_status"] = "legacy_proof_projection_unavailable"
    fixture["proof_evidence"] = None


def _migrate_outcomes(
    bundle: dict[str, Any], downgraded_fixture_ids: set[str]
) -> tuple[bool, dict[str, str]]:
    fixtures = {
        str(fixture["fixture_id"]): fixture for fixture in bundle.get("benchmark_fixtures", [])
    }
    changed = False
    id_map: dict[str, str] = {}
    for outcome in bundle.get("detector_case_outcomes", []):
        fixture_id = str(outcome.get("fixture_ref", {}).get("record_id", ""))
        fixture = fixtures.get(fixture_id)
        if fixture is None:
            continue
        prior_id = str(outcome["case_outcome_id"])
        outcome["fixture_semantic_digest"] = semantic_digest(fixture)
        outcome["qualification_proof_status"] = fixture["qualification_proof_status"]
        if fixture_id in downgraded_fixture_ids:
            outcome["metric_eligible"] = False
            outcome["promotion_evidence_eligible"] = False
            changed = True
        new_id = stable_id(
            "detector-case-outcome-execution-migration",
            prior_id,
            SOURCE_VERSION,
            TARGET_VERSION,
            str(outcome["fixture_semantic_digest"]),
            str(outcome["qualification_proof_status"]),
        )
        outcome.setdefault("extensions", {})["x-v0-12-case-outcome-id"] = prior_id
        outcome["case_outcome_id"] = new_id
        id_map[prior_id] = new_id
        # Every outcome identity changes because the v0.13 fixture proof projection is part
        # of its canonical meaning. Metrics that still cite the v0.12 identity are therefore
        # not authoritative even when the fixture itself did not require a legacy downgrade.
        changed = True
    return changed, id_map


def _remove_authoritative_metrics(bundle: dict[str, Any]) -> None:
    metric_sets = copy.deepcopy(bundle.get("qualification_metric_sets", []))
    if metric_sets:
        bundle.setdefault("extensions", {})["x-v0-12-unverified-qualification-metric-sets"] = (
            metric_sets
        )
    bundle["qualification_metric_sets"] = []
    for qualification in bundle.get("detector_qualifications", []):
        prior = qualification.get("quantitative_metrics")
        if prior is not None:
            qualification.setdefault("extensions", {})[
                "x-v0-12-unverified-quantitative-metrics"
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
    """Migrate one valid v0.12 AuditBundle without creating execution authority."""

    if output.exists() and any(output.iterdir()):
        raise PublicMigrationError(f"Migration output must be absent or empty: {output}")
    source = _read_object(source_bundle)
    if (
        source.get("record_type") != "audit_bundle"
        or source.get("schema_version") != SOURCE_VERSION
    ):
        raise PublicMigrationError("Input must be an exact public v0.12.0 AuditBundle")
    _assert_source_versions(source)
    LocalSchemaRegistry(source_schema_root).validate(source)

    migrated = _version_existing_records(copy.deepcopy(source))
    migrated["bundle_id"] = stable_id(
        "bundle-migration", str(source["bundle_id"]), SOURCE_VERSION, TARGET_VERSION
    )
    migrated["project_execution_authorizations"] = []

    legacy_capability_ids: set[str] = set()
    for capability in migrated.get("sandbox_capabilities", []):
        if _migrate_capability(capability):
            legacy_capability_ids.add(str(capability["sandbox_capability_id"]))

    legacy_execution_ids: set[str] = set()
    for execution in migrated.get("executions", []):
        if _migrate_execution(execution):
            legacy_execution_ids.add(str(execution["execution_id"]))

    index = _record_index(migrated)
    downgraded_fixture_ids: set[str] = set()
    for fixture in migrated.get("benchmark_fixtures", []):
        if _fixture_depends_on_legacy_execution(
            fixture, legacy_execution_ids, legacy_capability_ids
        ):
            _downgrade_fixture(fixture)
            downgraded_fixture_ids.add(str(fixture["fixture_id"]))
        else:
            _refresh_fixture_public_digests(fixture, index)

    outcomes_changed, _ = _migrate_outcomes(migrated, downgraded_fixture_ids)
    if downgraded_fixture_ids or outcomes_changed:
        _remove_authoritative_metrics(migrated)
    migrated["storage_manifests"] = []

    _validate_bundle_records(migrated, LocalSchemaRegistry(target_schema_root))
    output.mkdir(parents=True, exist_ok=True)
    write_normalized_json_once(output / "audit.bundle.json", migrated)
    write_normalized_json_once(
        output / "MIGRATION_REPORT.json",
        {
            "authorization_invented": False,
            "capability_probe_invented": False,
            "controller_registry_entry_created": False,
            "downgraded_fixture_count": len(downgraded_fixture_ids),
            "execution_launched": False,
            "legacy_capability_count": len(legacy_capability_ids),
            "legacy_project_execution_count": len(legacy_execution_ids),
            "linked_run_invented": False,
            "source_schema_version": SOURCE_VERSION,
            "storage_manifest_carried_forward": False,
            "target_schema_version": TARGET_VERSION,
            "validation": "passed",
            "limitations": [
                "A v0.12 rootless/support label has no v0.13 effective-probe projection.",
                "A v0.12 project-workflow Execution has no v0.13 one-use authorization projection.",
                "Migration creates no launchable controller-registry state.",
                "Storage manifests are cleared because migrated canonical bytes changed.",
            ],
        },
    )
    return migrated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate a public sc-referee v0.12.0 AuditBundle to v0.13.0"
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
