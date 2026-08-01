from __future__ import annotations

import argparse
import copy
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from sc_referee.core.ids import stable_id
from sc_referee.parsers.scalar_verification import (
    UnsupportedScalarVerification,
    verify_mean_difference,
)
from sc_referee.records.normalization import write_normalized_json
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.snapshot.identity import (
    build_asset_identity,
    full_digest_evidence,
    unidentified_evidence,
)
from sc_referee.storage.jsonl import JsonlRecordStore

_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")
_TERMINAL_STATES = {
    "partial_deadline",
    "partial_host_limit",
    "cancelled",
    "failed_controller",
}
_ROLE_CLASSIFICATION = {
    "analysis_source": "analysis_source",
    "report_candidate": "report_candidate",
    "other": "other",
    "symlink_not_followed": "unknown",
    "unsupported_special_file": "unknown",
}
_ARTIFACT_KIND = {
    "input_file": "data_file",
    "output_file": "result_file",
    "computed_scalar": "computed_value",
    "publication_report": "report",
}


class CandidateMigrationError(ValueError):
    """The provisional evidence cannot be promoted without inventing information."""


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CandidateMigrationError(f"Expected a JSON object in {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        value = json.loads(line)
        if not isinstance(value, dict):
            raise CandidateMigrationError(f"Expected a JSON object at {path}:{number}")
        records.append(value)
    return records


def _candidate_version(candidate_schema_root: Path) -> str:
    status = _read_json(candidate_schema_root / "PROPOSAL_STATUS.json")
    if status.get("accepted") is not False or status.get("public_release") is not False:
        raise CandidateMigrationError(
            "Candidate migration accepts only unaccepted nonpublic packages"
        )
    catalog = _read_json(candidate_schema_root / "schema-catalog.json")
    version = catalog.get("schema_version")
    if not isinstance(version, str) or not version:
        raise CandidateMigrationError("Candidate schema catalog has no exact version")
    if status.get("candidate_version") != version:
        raise CandidateMigrationError("Candidate status and schema catalog versions disagree")
    return version


def _provenance(method: str, created_at: str) -> dict[str, Any]:
    return {
        "actor": {
            "actor_kind": "controller",
            "actor_id": "controller:observed-schema-candidate-migration",
            "display_name": "sc-referee candidate migration",
        },
        "method": method,
        "created_at": created_at,
        "tool": "sc-referee",
        "tool_version": "0.0.0",
        "notes": "Nonpublic ADR-0002 review-candidate transformation.",
    }


def _typed_ref(record_type: str, record_id: str) -> dict[str, str]:
    return {"record_type": record_type, "record_id": record_id}


def _collect_source_paths(value: Any) -> set[str]:
    paths: set[str] = set()
    if isinstance(value, list):
        for item in value:
            paths.update(_collect_source_paths(item))
    elif isinstance(value, dict):
        if value.get("source_kind") and isinstance(value.get("path"), str):
            paths.add(str(value["path"]))
        for item in value.values():
            paths.update(_collect_source_paths(item))
    return paths


def _migrate_audit_runs(
    records: list[dict[str, Any]],
    stages: list[dict[str, Any]],
    version: str,
) -> list[dict[str, Any]]:
    last_stage_by_run: dict[str, dict[str, Any]] = {}
    for stage in stages:
        last_stage_by_run[str(stage["run_id"])] = stage
    migrated: list[dict[str, Any]] = []
    for record in records:
        run_id = str(record["run_id"])
        state = str(record["state"])
        created_at = str(record["created_at"])
        result: dict[str, Any] = {
            "schema_version": version,
            "record_type": "audit_run",
            "audit_run_id": run_id,
            "state": state,
            "created_at": created_at,
            "provenance": _provenance("migrate_provisional_audit_run", created_at),
        }
        if state != "created":
            snapshot_id = record.get("snapshot_id")
            if not isinstance(snapshot_id, str) or not snapshot_id:
                raise CandidateMigrationError(
                    f"Post-created AuditRun state {state!r} has no snapshot identity"
                )
            result["snapshot_ref"] = _typed_ref("repository_snapshot", snapshot_id)
        parent = record.get("parent_run_id")
        if isinstance(parent, str) and parent:
            result["parent_run_ref"] = _typed_ref("audit_run", parent)
        if state in _TERMINAL_STATES:
            stage = last_stage_by_run.get(run_id)
            details = stage.get("details") if stage else None
            if not isinstance(details, str) or not details:
                raise CandidateMigrationError(
                    f"Terminal AuditRun state {state!r} has no exact recorded reason"
                )
            result["terminal_reason"] = details
        migrated.append(result)
    return migrated


def _migrate_stages(
    records: list[dict[str, Any]], version: str, created_at: str
) -> list[dict[str, Any]]:
    sequences: defaultdict[str, int] = defaultdict(int)
    migrated: list[dict[str, Any]] = []
    for record in records:
        run_id = str(record["run_id"])
        sequences[run_id] += 1
        status = str(record["status"])
        details = str(record["details"])
        result: dict[str, Any] = {
            "schema_version": version,
            "record_type": "stage_result",
            "stage_result_id": str(record["stage_result_id"]),
            "audit_run_id": run_id,
            "stage": str(record["stage"]),
            "sequence": sequences[run_id],
            "status": status,
            "details": details,
            "produced_record_refs": [],
            "provenance": _provenance("migrate_provisional_stage_result", created_at),
        }
        error_code = record.get("error_code")
        if status in {"failed", "timed_out"}:
            if not isinstance(error_code, str) or not error_code:
                raise CandidateMigrationError(
                    f"StageResult {record['stage_result_id']!r} lacks a typed error code"
                )
            result["error"] = {
                "code": error_code,
                "message": details,
                "details_known": True,
            }
        elif isinstance(error_code, str) and error_code:
            result["error"] = {
                "code": error_code,
                "message": details,
                "details_known": True,
            }
        migrated.append(result)
    return migrated


def _identity_by_file_id(
    identities: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for identity in identities:
        asset_ref = identity.get("asset_ref", {})
        if asset_ref.get("record_type") != "file_record":
            continue
        file_id = asset_ref.get("record_id")
        if not isinstance(file_id, str) or not file_id:
            raise CandidateMigrationError("File AssetIdentity has no typed file identifier")
        if file_id in result:
            raise CandidateMigrationError(f"Multiple AssetIdentity records target {file_id!r}")
        result[file_id] = identity
    return result


def _check_legacy_identity(record: dict[str, Any], identity: dict[str, Any]) -> None:
    expected_strength = {
        "full_digest": "strong",
        "immutable_external": "strong",
        "manifest": "manifest",
        "weak_fingerprint": "weak",
        "unidentified": "unidentified",
    }[str(identity["tier"])]
    if record.get("identity_strength") != expected_strength:
        raise CandidateMigrationError(
            f"FileRecord {record['file_id']!r} identity strength conflicts with AssetIdentity"
        )
    digest = record.get("digest")
    evidence = identity["identity_evidence"]
    if identity["tier"] == "full_digest":
        if digest != evidence.get("digest"):
            raise CandidateMigrationError(
                f"FileRecord {record['file_id']!r} digest conflicts with AssetIdentity"
            )
    elif digest is not None:
        raise CandidateMigrationError(
            f"FileRecord {record['file_id']!r} has a digest unsupported by its identity tier"
        )


def _migrate_files(
    records: list[dict[str, Any]],
    identities: list[dict[str, Any]],
    snapshot_id: str,
    inspected_paths: set[str],
    version: str,
    created_at: str,
) -> list[dict[str, Any]]:
    by_file_id = _identity_by_file_id(identities)
    migrated: list[dict[str, Any]] = []
    for record in records:
        file_id = str(record["file_id"])
        identity = by_file_id.get(file_id)
        if identity is None:
            raise CandidateMigrationError(f"FileRecord {file_id!r} has no AssetIdentity")
        _check_legacy_identity(record, identity)
        role = str(record["role"])
        path = str(record["path"])
        if role == "symlink_not_followed":
            raise CandidateMigrationError(
                f"Symlink {path!r} lacks serialized target text and cannot be migrated"
            )
        entry_kind = "special" if role == "unsupported_special_file" else "regular_file"
        limitations = [str(item) for item in identity.get("limitations", [])]
        reason = identity.get("identity_evidence", {}).get("reason")
        if entry_kind == "special":
            disposition = "special_file"
        elif identity.get("tier") == "unidentified" and isinstance(reason, str):
            disposition = "unreadable" if "read" in reason.lower() else "not_selected"
        elif path in inspected_paths:
            disposition = "inspected"
        else:
            disposition = "not_selected"
        if disposition in {"unreadable", "special_file"} and not limitations:
            if not isinstance(reason, str) or not reason:
                raise CandidateMigrationError(f"Boundary {path!r} has no exact limitation")
            limitations = [reason]
        classification = "unknown" if role == "data_or_result" else _ROLE_CLASSIFICATION.get(role)
        if classification is None:
            raise CandidateMigrationError(f"Unsupported provisional file role {role!r}")
        if role == "data_or_result":
            limitations.append(
                "The provisional data_or_result role did not distinguish input data from output."
            )
        result: dict[str, Any] = {
            "schema_version": version,
            "record_type": "file_record",
            "file_record_id": file_id,
            "audit_run_id": str(record["run_id"]),
            "snapshot_ref": _typed_ref("repository_snapshot", snapshot_id),
            "path": path,
            "entry_kind": entry_kind,
            "byte_size": int(record["size_bytes"]),
            "classification": classification,
            "inspection_disposition": disposition,
            "identity_disposition": "recorded",
            "asset_identity_ref": _typed_ref("asset_identity", str(identity["asset_identity_id"])),
            "limitations": limitations,
            "provenance": _provenance("migrate_provisional_file_record", created_at),
        }
        migrated.append(result)
    return migrated


def _parser_for_emitted_record(
    record_id: str, parser_results: list[dict[str, Any]]
) -> dict[str, Any]:
    matches = [
        parser
        for parser in parser_results
        if any(ref.get("record_id") == record_id for ref in parser.get("emitted_record_refs", []))
    ]
    if len(matches) != 1:
        raise CandidateMigrationError(
            f"Record {record_id!r} requires exactly one emitting ParserResult, found {len(matches)}"
        )
    return matches[0]


def _artifact_edge(value: Any, known_artifacts: set[str]) -> dict[str, str]:
    if not isinstance(value, str) or value not in known_artifacts:
        raise CandidateMigrationError(f"Bare operation edge {value!r} has no exact Artifact target")
    return _typed_ref("artifact", value)


def _migrate_operations(
    records: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    parser_results: list[dict[str, Any]],
    version: str,
) -> list[dict[str, Any]]:
    known_artifacts = {str(record["artifact_id"]) for record in artifacts}
    migrated: list[dict[str, Any]] = []
    for record in records:
        operation_id = str(record["operation_id"])
        parser = _parser_for_emitted_record(operation_id, parser_results)
        kind = str(record["kind"])
        inspection_status = str(record["inspection_status"])
        opaque_boundaries: list[str] = []
        if kind == "opaque_operation" or inspection_status == "opaque":
            opaque_boundaries = [
                str(boundary["reason"])
                for boundary in parser.get("opaque_constructs", [])
                if isinstance(boundary.get("reason"), str) and boundary["reason"]
            ]
            if not opaque_boundaries:
                raise CandidateMigrationError(
                    f"Opaque operation {operation_id!r} has no recorded opaque boundary"
                )
        implementation = record.get("implementation")
        if not isinstance(implementation, str) or not implementation:
            raise CandidateMigrationError(f"Operation {operation_id!r} has no implementation")
        migrated.append(
            {
                "schema_version": version,
                "record_type": "operation",
                "operation_id": operation_id,
                "audit_run_id": str(record["run_id"]),
                "kind": kind,
                "source_refs": copy.deepcopy(record["source_refs"]),
                "input_refs": [
                    _artifact_edge(value, known_artifacts) for value in record.get("input_refs", [])
                ],
                "output_refs": [
                    _artifact_edge(value, known_artifacts)
                    for value in record.get("output_refs", [])
                ],
                "literal_parameters": {},
                "implementation": {"name": implementation},
                "determinism": "unknown",
                "parser_result_ref": _typed_ref("parser_result", str(parser["parser_result_id"])),
                "inspection_status": inspection_status,
                "opaque_boundaries": opaque_boundaries,
                "provenance": copy.deepcopy(parser["provenance"]),
            }
        )
    return migrated


def _artifact_sources(
    artifact_id: str,
    producers: list[dict[str, Any]],
    consumers: list[dict[str, Any]],
    claims: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for operation in [*producers, *consumers]:
        sources.extend(copy.deepcopy(operation["source_refs"]))
    for claim in claims:
        report_ref = claim.get("report_ref", {})
        if report_ref.get("record_id") == artifact_id:
            sources.extend(copy.deepcopy(claim.get("source_refs", [])))
    unique: dict[str, dict[str, Any]] = {}
    for source in sources:
        unique[json.dumps(source, sort_keys=True, separators=(",", ":"))] = source
    return [unique[key] for key in sorted(unique)]


def _artifact_identity(record: dict[str, Any], version: str, created_at: str) -> dict[str, Any]:
    identity = record.get("identity")
    artifact_id = str(record["artifact_id"])
    if isinstance(identity, str) and _DIGEST.fullmatch(identity):
        evidence = full_digest_evidence(identity)
    elif isinstance(identity, str) and identity.startswith("derived-from:"):
        evidence = unidentified_evidence(
            "The artifact has producer lineage but no independent serialized content identity.",
            reported_location=identity,
            limitations=(
                "Producer lineage is not a substitute for exact artifact content identity.",
            ),
        )
    elif isinstance(identity, str) and identity.startswith("unavailable:path:"):
        evidence = unidentified_evidence(
            "The output path was observed statically, but project-authored code was not executed.",
            reported_location=identity.removeprefix("unavailable:path:"),
            limitations=("No output bytes existed in the immutable source snapshot.",),
        )
    else:
        raise CandidateMigrationError(f"Artifact {artifact_id!r} has unsupported identity evidence")
    result = build_asset_identity(
        audit_run_id=str(record["run_id"]),
        asset_record_type="artifact",
        asset_record_id=artifact_id,
        evidence=evidence,
        created_at=created_at,
    )
    result["schema_version"] = version
    return result


def _migrate_artifacts(
    records: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    version: str,
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    migrated: list[dict[str, Any]] = []
    identities: list[dict[str, Any]] = []
    for record in records:
        artifact_id = str(record["artifact_id"])
        producers = [
            operation
            for operation in operations
            if any(ref["record_id"] == artifact_id for ref in operation["output_refs"])
        ]
        consumers = [
            operation
            for operation in operations
            if any(ref["record_id"] == artifact_id for ref in operation["input_refs"])
        ]
        declared_producers = {str(item) for item in record.get("producer_operation_ids", [])}
        observed_producers = {str(item["operation_id"]) for item in producers}
        if declared_producers != observed_producers:
            raise CandidateMigrationError(
                f"Artifact {artifact_id!r} producer declarations conflict with operation edges"
            )
        identity = _artifact_identity(record, version, created_at)
        kind = _ARTIFACT_KIND.get(str(record["kind"]))
        if kind is None:
            raise CandidateMigrationError(
                f"Artifact {artifact_id!r} has unsupported provisional kind {record['kind']!r}"
            )
        result: dict[str, Any] = {
            "schema_version": version,
            "record_type": "artifact",
            "artifact_id": artifact_id,
            "audit_run_id": str(record["run_id"]),
            "kind": kind,
            "observed_role": str(record["kind"]),
            "source_refs": _artifact_sources(artifact_id, producers, consumers, claims),
            "producer_operation_refs": [
                _typed_ref("operation", str(item["operation_id"])) for item in producers
            ],
            "consumer_operation_refs": [
                _typed_ref("operation", str(item["operation_id"])) for item in consumers
            ],
            "asset_identity_ref": _typed_ref("asset_identity", str(identity["asset_identity_id"])),
            "limitations": [
                "Observed artifact and lineage records do not establish scientific correctness."
            ],
            "provenance": _provenance("migrate_provisional_artifact", created_at),
        }
        if isinstance(record.get("path"), str):
            result["path"] = record["path"]
        migrated.append(result)
        identities.append(identity)
    return migrated, identities


def _known_or_unknown_slot(
    value: Any,
    evidence_refs: list[dict[str, Any]],
    *,
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, str) or not value or value.lower() == "unknown":
        return {
            "state": "unknown",
            "rationale": f"The provisional {label} remained unknown during migration.",
            "evidence_refs": [],
        }
    if not evidence_refs:
        raise CandidateMigrationError(f"Known {label} has no exact evidence reference")
    return {"state": "known", "value": value, "evidence_refs": copy.deepcopy(evidence_refs)}


def _is_explicit_unknown(value: Any) -> bool:
    return not isinstance(value, str) or not value or value.lower() == "unknown"


def _claim_for_result(result_id: str, claims: list[dict[str, Any]]) -> dict[str, Any] | None:
    matches = [
        claim
        for claim in claims
        if any(
            ref.get("record_type") == "observed_result" and ref.get("record_id") == result_id
            for ref in claim.get("lineage", {}).get("result_refs", [])
        )
    ]
    if len(matches) > 1:
        raise CandidateMigrationError(f"ObservedResult {result_id!r} has ambiguous claim lineage")
    return matches[0] if matches else None


def _migrate_observed_result(
    record: dict[str, Any],
    operations: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    materialized_root: Path,
    version: str,
    created_at: str,
) -> dict[str, Any]:
    result_id = str(record["result_id"])
    run_id = str(record["run_id"])
    try:
        verified = verify_mean_difference(materialized_root / "analysis.py", run_id)
    except UnsupportedScalarVerification as error:
        raise CandidateMigrationError(
            "Observed scalar could not be independently reverified during migration"
        ) from error
    for field in ("result_id", "value", "source_refs"):
        if verified.get(field) != record.get(field):
            raise CandidateMigrationError(
                f"ObservedResult {result_id!r} conflicts with independent verification at {field}"
            )
    for field in ("comparison", "orientation", "scale"):
        if not _is_explicit_unknown(record.get(field)) and verified.get(field) != record.get(field):
            raise CandidateMigrationError(
                f"Known ObservedResult {result_id!r} conflicts with verification at {field}"
            )

    claim = _claim_for_result(result_id, claims)
    producer: dict[str, Any] | None = None
    artifact_ref: dict[str, str] | None = None
    if claim is not None:
        operation_refs = claim.get("lineage", {}).get("operation_refs", [])
        matching = [
            operation
            for operation in operations
            if any(ref.get("record_id") == operation["operation_id"] for ref in operation_refs)
        ]
        if len(matching) == 1:
            producer = matching[0]
            if len(producer["output_refs"]) == 1:
                artifact_ref = copy.deepcopy(producer["output_refs"][0])

    lineage_status = str(record["lineage_status"])
    lineage_limitations: list[str] = []
    if lineage_status == "complete":
        if producer is None or artifact_ref is None:
            raise CandidateMigrationError(
                f"Complete ObservedResult {result_id!r} lacks unique producer/artifact linkage"
            )
    else:
        lineage_limitations = [
            f"The provisional lineage status remained {lineage_status}; missing links were not synthesized."
        ]

    analysis_refs = [ref for ref in verified["source_refs"] if ref.get("path") == "analysis.py"]
    data_refs = [ref for ref in verified["source_refs"] if ref.get("path") == "data.csv"]
    migrated: dict[str, Any] = {
        "schema_version": version,
        "record_type": "observed_result",
        "observed_result_id": result_id,
        "audit_run_id": run_id,
        "value_kind": "scalar",
        "scalar_value": record["value"],
        "observation_method": "deterministic_verification",
        "source_refs": copy.deepcopy(verified["source_refs"]),
        "lineage_status": lineage_status,
        "lineage_limitations": lineage_limitations,
        "comparison": _known_or_unknown_slot(
            record.get("comparison"), analysis_refs, label="comparison"
        ),
        "orientation": _known_or_unknown_slot(
            record.get("orientation"), analysis_refs, label="orientation"
        ),
        "scale": _known_or_unknown_slot(record.get("scale"), data_refs, label="scale"),
        "unit": _known_or_unknown_slot(None, [], label="unit"),
        "population": _known_or_unknown_slot(None, [], label="population"),
        "timing": _known_or_unknown_slot(None, [], label="timing"),
        "provenance": _provenance("reverify_and_migrate_bounded_csv_mean_difference", created_at),
    }
    if producer is not None:
        migrated["producing_operation_ref"] = _typed_ref("operation", str(producer["operation_id"]))
    if artifact_ref is not None:
        migrated["artifact_ref"] = artifact_ref
    return migrated


def _version_public_bundle(bundle: dict[str, Any], version: str) -> dict[str, Any]:
    migrated = copy.deepcopy(bundle)
    migrated["schema_version"] = version
    migrated["bundle_id"] = stable_id("bundle-candidate", str(bundle["bundle_id"]), version)
    for key, records in migrated.items():
        if key == "storage_manifests" or not isinstance(records, list):
            continue
        for record in records:
            if isinstance(record, dict) and "schema_version" in record:
                record["schema_version"] = version
    migrated["storage_manifests"] = []
    return migrated


def _prepare_output(output: Path) -> None:
    if output.exists() and any(output.iterdir()):
        raise CandidateMigrationError(f"Migration output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)


def migrate_walking_skeleton_candidate(
    audit_root: Path,
    candidate_schema_root: Path,
    output: Path,
) -> dict[str, Any]:
    """Promote one generated walking-skeleton audit into an unaccepted review candidate."""
    version = _candidate_version(candidate_schema_root)
    _prepare_output(output)
    bundle = _read_json(audit_root / "audit.bundle.json")
    snapshot = _read_json(audit_root / "observed" / "snapshot.json")
    created_at = str(bundle["generated_at"])
    audit_runs_raw = _read_jsonl(audit_root / "observed" / "audit-run.jsonl")
    stages_raw = _read_jsonl(audit_root / "observed" / "stage-result.jsonl")
    files_raw = _read_jsonl(audit_root / "observed" / "files.jsonl")
    operations_raw = _read_jsonl(audit_root / "observed" / "operation.jsonl")
    artifacts_raw = _read_jsonl(audit_root / "observed" / "artifact.jsonl")
    observed_raw = _read_jsonl(audit_root / "observed" / "observed-result.jsonl")
    if len(observed_raw) != 1:
        raise CandidateMigrationError(
            "The bounded candidate migration requires exactly one ObservedResult"
        )

    public_identities = copy.deepcopy(bundle["asset_identities"])
    for identity in public_identities:
        identity["schema_version"] = version
    inspected_paths = _collect_source_paths(bundle)
    audit_runs = _migrate_audit_runs(audit_runs_raw, stages_raw, version)
    stages = _migrate_stages(stages_raw, version, created_at)
    files = _migrate_files(
        files_raw,
        public_identities,
        str(snapshot["snapshot_id"]),
        inspected_paths,
        version,
        created_at,
    )
    operations = _migrate_operations(
        operations_raw, artifacts_raw, bundle["parser_results"], version
    )
    artifacts, artifact_identities = _migrate_artifacts(
        artifacts_raw, operations, bundle["claims"], version, created_at
    )
    observed = _migrate_observed_result(
        observed_raw[0],
        operations,
        bundle["claims"],
        audit_root / "observed" / "snapshot" / "materialized",
        version,
        created_at,
    )

    candidate_bundle = _version_public_bundle(bundle, version)
    candidate_bundle["asset_identities"] = [*public_identities, *artifact_identities]
    candidate_bundle["audit_runs"] = audit_runs
    candidate_bundle["stage_results"] = stages
    candidate_bundle["file_records"] = files
    candidate_bundle["operations"] = operations
    candidate_bundle["artifacts"] = artifacts
    candidate_bundle["observed_results"] = [observed]

    registry = LocalSchemaRegistry(candidate_schema_root)
    for records in (
        audit_runs,
        stages,
        files,
        operations,
        artifacts,
        [observed],
        artifact_identities,
    ):
        for record in records:
            registry.validate(record)
    registry.validate(candidate_bundle)

    observed_store = JsonlRecordStore(output / "observed")
    for records in (audit_runs, stages, files, operations, artifacts, [observed]):
        for record in records:
            observed_store.append(record)
    for identity in candidate_bundle["asset_identities"]:
        observed_store.append(identity)
    write_normalized_json(output / "audit.bundle.candidate.json", candidate_bundle)
    report = {
        "accepted": False,
        "candidate_version": version,
        "public_release": False,
        "source_audit_run_id": bundle["audit_run_id"],
        "source_semantic_lock_digest": bundle["semantic_lock_digest"],
        "storage_manifest_carried_forward": False,
        "validation": "passed",
        "limitations": [
            "The migration supports only the bounded walking-skeleton scalar path.",
            "The candidate bundle has no StorageManifest because its bytes are not a public release artifact.",
            "Candidate validation does not accept ADR-0002 or publish W3ID schemas.",
        ],
    }
    write_normalized_json(output / "MIGRATION_REPORT.json", report)
    return candidate_bundle


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate a walking-skeleton audit into a nonpublic ADR-0002 candidate."
    )
    parser.add_argument("audit_root", type=Path)
    parser.add_argument("candidate_schema_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bundle = migrate_walking_skeleton_candidate(
        args.audit_root.resolve(),
        args.candidate_schema_root.resolve(),
        args.output.resolve(),
    )
    print(f"Validated nonpublic candidate {bundle['bundle_id']} at {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
