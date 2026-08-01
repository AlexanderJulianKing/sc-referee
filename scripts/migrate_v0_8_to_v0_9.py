from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from sc_referee.core.ids import stable_id
from sc_referee.records.normalization import write_normalized_json
from sc_referee.records.root_cause import (
    root_cause_candidate_id as _shared_candidate_id,
)
from sc_referee.records.root_cause import (
    root_cause_candidate_payload as _shared_candidate_payload,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry

SOURCE_VERSION = "0.8.0"
TARGET_VERSION = "0.9.0"


class PublicMigrationError(ValueError):
    """Raised when a public bundle cannot be migrated without inventing identity."""


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


def root_cause_candidate_payload(review: dict[str, Any]) -> dict[str, Any]:
    """Return the exact v0.9 review-local identity payload."""

    return _shared_candidate_payload(review)


def root_cause_candidate_id(review: dict[str, Any]) -> str:
    """Derive one noncanonical review-local root-cause candidate ID."""

    return _shared_candidate_id(review)


def _migrate_reviews(bundle: dict[str, Any]) -> None:
    for review in bundle.get("agent_reviews", []):
        verdict = review.get("verdict")
        stage = review.get("stage")
        if verdict == "demonstrated_issue" and stage != "stage2_scientific_adjudication":
            review["root_cause_identity"] = {
                "candidate_root_cause_id": root_cause_candidate_id(review),
                "identity_profile": "review-local-root-cause-v1",
                "reconciled_stage1_candidates": [],
                "equivalence_evidence": [],
            }
            continue
        if verdict == "demonstrated_issue":
            extensions = review.setdefault("extensions", {})
            extensions["x-v0-8-verdict"] = verdict
            extensions["x-v0-8-root-cause"] = review.get("root_cause")
            extensions["x-v0-8-bounded-statement"] = review.get("bounded_statement")
            extensions["x-v0-8-issue-class"] = review.get("issue_class")
            review["verdict"] = "insufficient_evidence"
            questions = review.setdefault("unresolved_material_questions", [])
            limitation = (
                "Public v0.8.0 did not preserve an exact Stage-2 candidate reconciliation set."
            )
            if limitation not in questions:
                questions.append(limitation)
        review["root_cause_identity"] = None


def _migrate_adjudications(bundle: dict[str, Any]) -> None:
    for adjudication in bundle.get("benchmark_adjudications", []):
        prior_status = str(adjudication.get("label_status"))
        extensions = adjudication.setdefault("extensions", {})
        for field in ("bounded_root_cause_statement", "issue_class"):
            prior = adjudication.pop(field, None)
            if prior is not None:
                extensions[f"x-v0-8-{field.replace('_', '-')}"] = prior
        adjudication["adjudicated_root_cause_refs"] = []
        if prior_status == "positive_demonstrated":
            extensions["x-v0-8-label-status"] = prior_status
            adjudication["label_status"] = "insufficient_evidence"
            adjudication["exclusion_reason"] = (
                "Legacy v0.8.0 positive lacks canonical Stage-2 root-cause reconciliation."
            )
            adjudication["root_cause_reconciliation_status"] = "unresolved"
        elif prior_status in {"verified_good_eligible", "hard_negative_eligible"}:
            adjudication["root_cause_reconciliation_status"] = "not_applicable"
        else:
            adjudication["root_cause_reconciliation_status"] = "unresolved"


def _migrate_fixtures(bundle: dict[str, Any]) -> None:
    for fixture in bundle.get("benchmark_fixtures", []):
        fixture["expected_root_cause_refs"] = []
        if fixture.get("fixture_kind") != "positive_issue_fixture":
            continue
        extensions = fixture.setdefault("extensions", {})
        extensions["x-v0-8-fixture-kind"] = "positive_issue_fixture"
        extensions["x-v0-8-expected-issue-labels"] = copy.deepcopy(
            fixture.get("expected_issue_labels", [])
        )
        fixture["fixture_kind"] = "ambiguous_fixture"
        fixture["expected_issue_labels"] = []
        fixture.setdefault("proof_obligations", {})["positive_root_cause_documented"] = False
        limitation = (
            "Legacy positive identity is excluded until canonical Stage-2 reconciliation is rerun."
        )
        if limitation not in fixture.setdefault("limitations", []):
            fixture["limitations"].append(limitation)


def migrate_public_bundle(
    source_bundle: Path,
    source_schema_root: Path,
    target_schema_root: Path,
    output: Path,
) -> dict[str, Any]:
    """Migrate one valid v0.8.0 bundle without inventing root-cause equivalence."""

    if output.exists() and any(output.iterdir()):
        raise PublicMigrationError(f"Migration output must be absent or empty: {output}")
    source = _read_object(source_bundle)
    if (
        source.get("record_type") != "audit_bundle"
        or source.get("schema_version") != SOURCE_VERSION
    ):
        raise PublicMigrationError("Input must be an exact public v0.8.0 AuditBundle")
    _assert_source_versions(source)
    LocalSchemaRegistry(source_schema_root).validate(source)

    migrated = copy.deepcopy(source)
    _version_existing_records(migrated)
    migrated["bundle_id"] = stable_id(
        "bundle-migration", str(source["bundle_id"]), SOURCE_VERSION, TARGET_VERSION
    )
    migrated["adjudicated_root_causes"] = []
    _migrate_reviews(migrated)
    _migrate_adjudications(migrated)
    _migrate_fixtures(migrated)
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
            "review_local_candidate_ids_derived_from_exact_content": True,
            "stage2_reconciliation_invented": False,
            "root_cause_equivalence_invented": False,
            "legacy_positive_labels_admitted": False,
            "storage_manifest_carried_forward": False,
            "limitations": [
                "Public v0.8.0 did not preserve exact Stage-2 candidate-set reconciliation.",
                "Legacy Stage-2 demonstrated reviews and positive adjudications are insufficient evidence after migration.",
                "Legacy positive fixtures are ambiguous after migration.",
                "No AdjudicatedRootCause record was inferred from prose or confidence.",
                "The source StorageManifest was not carried forward because migrated bytes require a new manifest.",
            ],
        },
    )
    return migrated


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate a public v0.8.0 AuditBundle to v0.9.0")
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
