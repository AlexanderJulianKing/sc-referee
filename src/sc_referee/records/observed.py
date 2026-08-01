from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Any

from sc_referee.snapshot.identity import (
    build_asset_identity,
    full_digest_evidence,
    unidentified_evidence,
)
from sc_referee.version import SCHEMA_VERSION, __version__

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


class ObservedRecordError(ValueError):
    """Raised when an observed record cannot be emitted without inventing evidence."""


@dataclass(frozen=True)
class PublicObservedGraph:
    operations: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]
    observed_result: dict[str, Any]
    artifact_identities: list[dict[str, Any]]


@dataclass(frozen=True)
class PublicStaticGraph:
    operations: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]
    artifact_identities: list[dict[str, Any]]


def known_semantic_value(slot: Any) -> str | None:
    """Return a value only from an explicitly known public epistemic slot."""
    if not isinstance(slot, dict) or slot.get("state") != "known":
        return None
    value = slot.get("value")
    return value if isinstance(value, str) and value else None


def typed_ref(record_type: str, record_id: str) -> dict[str, str]:
    return {"record_type": record_type, "record_id": record_id}


def controller_provenance(method: str, created_at: str) -> dict[str, Any]:
    return {
        "actor": {
            "actor_kind": "controller",
            "actor_id": "software:sc-referee-controller",
            "display_name": "sc-referee controller",
        },
        "method": method,
        "created_at": created_at,
        "tool": "sc-referee",
        "tool_version": __version__,
    }


def build_audit_run_record(
    audit_run_id: str,
    state: str,
    created_at: str,
    *,
    snapshot_id: str | None = None,
    parent_run_id: str | None = None,
    terminal_reason: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "audit_run",
        "audit_run_id": audit_run_id,
        "state": state,
        "created_at": created_at,
        "provenance": controller_provenance("append_only_run_state", created_at),
    }
    if parent_run_id is not None:
        record["parent_run_ref"] = typed_ref("audit_run", parent_run_id)
    snapshot_required_states = {
        "snapshotted",
        "inventoried",
        "parsed",
        "semantics_proposed",
        "awaiting_answers",
        "semantics_resolved",
        "semantics_locked",
        "detected",
        "reported",
        "complete",
    }
    if state in snapshot_required_states:
        if not snapshot_id:
            raise ObservedRecordError(f"AuditRun state {state!r} requires a snapshot")
        record["snapshot_ref"] = typed_ref("repository_snapshot", snapshot_id)
    elif snapshot_id:
        record["snapshot_ref"] = typed_ref("repository_snapshot", snapshot_id)
    if state in _TERMINAL_STATES:
        if not terminal_reason:
            raise ObservedRecordError(f"terminal AuditRun state {state!r} requires a reason")
        record["terminal_reason"] = terminal_reason
    return record


def build_stage_result_record(
    audit_run_id: str,
    stage_result_id: str,
    stage: str,
    sequence: int,
    status: str,
    details: str,
    created_at: str,
    *,
    error_code: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "stage_result",
        "stage_result_id": stage_result_id,
        "audit_run_id": audit_run_id,
        "stage": stage,
        "sequence": sequence,
        "status": status,
        "details": details,
        "produced_record_refs": [],
        "provenance": controller_provenance("record_stage_result", created_at),
    }
    if status in {"failed", "timed_out"} and not error_code:
        raise ObservedRecordError(f"StageResult status {status!r} requires an error code")
    if error_code:
        record["error"] = {"code": error_code, "message": details, "details_known": True}
    return record


def build_file_records(
    inventory: list[dict[str, Any]],
    identities: list[dict[str, Any]],
    snapshot_id: str,
    created_at: str,
) -> list[dict[str, Any]]:
    identity_by_file = {
        str(identity["asset_ref"]["record_id"]): identity
        for identity in identities
        if identity.get("asset_ref", {}).get("record_type") == "file_record"
    }
    result: list[dict[str, Any]] = []
    for observed in inventory:
        file_id = str(observed["file_id"])
        identity = identity_by_file.get(file_id)
        if identity is None:
            raise ObservedRecordError(f"FileRecord {file_id!r} has no AssetIdentity")
        path = str(observed["path"])
        role = str(observed["role"])
        entry_kind = str(observed.get("entry_kind", "regular_file"))
        limitations = [str(value) for value in identity.get("limitations", [])]
        classification = "unknown" if role == "data_or_result" else _ROLE_CLASSIFICATION.get(role)
        if classification is None:
            raise ObservedRecordError(f"unsupported observed file role {role!r}")
        if role == "data_or_result":
            limitations.append(
                "Static inventory did not distinguish whether this path is an input or output."
            )
        evidence = identity.get("identity_evidence", {})
        reason = evidence.get("reason")
        if entry_kind == "symlink":
            disposition = "symlink_not_followed"
            limitations.append("The symbolic link was inventoried and not followed.")
        elif entry_kind == "special":
            disposition = "special_file"
        elif identity.get("tier") == "unidentified" and isinstance(reason, str):
            disposition = "unreadable" if "read" in reason.lower() else "not_selected"
        else:
            disposition = "not_selected"
        if disposition in {"unreadable", "special_file"} and not limitations:
            if not isinstance(reason, str) or not reason:
                raise ObservedRecordError(f"Boundary {path!r} has no exact limitation")
            limitations.append(reason)
        record: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "file_record",
            "file_record_id": file_id,
            "audit_run_id": str(observed["run_id"]),
            "snapshot_ref": typed_ref("repository_snapshot", snapshot_id),
            "path": path,
            "entry_kind": entry_kind,
            "byte_size": int(observed["size_bytes"]),
            "classification": classification,
            "inspection_disposition": disposition,
            "identity_disposition": "recorded",
            "asset_identity_ref": typed_ref("asset_identity", str(identity["asset_identity_id"])),
            "limitations": sorted(set(limitations)),
            "provenance": controller_provenance("safe_file_inventory", created_at),
        }
        if entry_kind == "symlink":
            record["symlink_followed"] = False
            target = observed.get("symlink_target")
            if isinstance(target, str):
                record["symlink_target"] = target
        result.append(record)
    return result


def build_public_observed_graph(
    raw_operations: list[dict[str, Any]],
    raw_artifacts: list[dict[str, Any]],
    raw_observed_result: dict[str, Any],
    parser_result: dict[str, Any],
    claim: dict[str, Any],
    created_at: str,
) -> PublicObservedGraph:
    operations = _build_operations(raw_operations, raw_artifacts, parser_result)
    artifacts, identities = _build_artifacts(raw_artifacts, operations, [claim], created_at)
    observed_result = _build_observed_result(raw_observed_result, operations, [claim], created_at)
    return PublicObservedGraph(operations, artifacts, observed_result, identities)


def build_public_static_graph(
    parser_results: list[dict[str, Any]], created_at: str
) -> PublicStaticGraph:
    """Promote parser-emitted static operations and artifacts without inventing results."""

    raw_artifacts_by_id: dict[str, dict[str, Any]] = {}
    for parser_result in parser_results:
        extensions = parser_result.get("extensions", {})
        for raw_artifact in extensions.get("x-artifacts", []):
            artifact_id = str(raw_artifact["artifact_id"])
            existing = raw_artifacts_by_id.get(artifact_id)
            if existing is None:
                raw_artifacts_by_id[artifact_id] = copy.deepcopy(raw_artifact)
                continue
            comparable_keys = {"record_type", "artifact_id", "run_id", "kind", "path", "identity"}
            if any(existing.get(key) != raw_artifact.get(key) for key in comparable_keys):
                raise ObservedRecordError(
                    f"Parser Artifact {artifact_id!r} has conflicting observations"
                )
            existing["producer_operation_ids"] = sorted(
                {
                    *map(str, existing.get("producer_operation_ids", [])),
                    *map(str, raw_artifact.get("producer_operation_ids", [])),
                }
            )

    raw_artifacts = list(raw_artifacts_by_id.values())
    operations: list[dict[str, Any]] = []
    seen_operation_ids: set[str] = set()
    for parser_result in parser_results:
        raw_operations = list(parser_result.get("extensions", {}).get("x-operations", []))
        public_operations = _build_operations(raw_operations, raw_artifacts, parser_result)
        for operation in public_operations:
            operation_id = str(operation["operation_id"])
            if operation_id in seen_operation_ids:
                raise ObservedRecordError(f"Duplicate Operation identity {operation_id!r}")
            seen_operation_ids.add(operation_id)
            operations.append(operation)

    operations.sort(key=lambda item: str(item["operation_id"]))
    artifacts, identities = _build_artifacts(raw_artifacts, operations, [], created_at)
    artifacts.sort(key=lambda item: str(item["artifact_id"]))
    identities.sort(key=lambda item: str(item["asset_identity_id"]))
    return PublicStaticGraph(operations, artifacts, identities)


def build_public_verified_result(
    observed: dict[str, Any],
    operations: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    created_at: str,
) -> dict[str, Any]:
    """Promote one auditor-recomputed scalar with exact static graph linkage."""

    operation_id = str(observed.get("producer_operation_id", ""))
    artifact_id = str(observed.get("artifact_id", ""))
    input_artifact_id = str(observed.get("input_artifact_id", ""))
    matching_operations = [
        item for item in operations if str(item.get("operation_id")) == operation_id
    ]
    if len(matching_operations) != 1:
        raise ObservedRecordError("verified scalar lacks one exact producing Operation")
    operation = matching_operations[0]
    if operation.get("inspection_status") != "supported":
        raise ObservedRecordError("verified scalar producer is not statically supported")
    if operation.get("output_refs") != [typed_ref("artifact", artifact_id)]:
        raise ObservedRecordError("verified scalar output disagrees with the static graph")
    if typed_ref("artifact", input_artifact_id) not in operation.get("input_refs", []):
        raise ObservedRecordError("verified scalar input disagrees with the static graph")
    artifact_ids = {str(item.get("artifact_id")) for item in artifacts}
    if artifact_id not in artifact_ids or input_artifact_id not in artifact_ids:
        raise ObservedRecordError("verified scalar graph references an unavailable Artifact")

    source_refs = copy.deepcopy(observed["source_refs"])
    analysis_path = str(observed["analysis_path"])
    input_path = str(observed["input_path"])
    analysis_refs = [ref for ref in source_refs if ref.get("path") == analysis_path]
    input_refs = [ref for ref in source_refs if ref.get("path") == input_path]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "observed_result",
        "observed_result_id": str(observed["result_id"]),
        "audit_run_id": str(observed["run_id"]),
        "value_kind": "scalar",
        "scalar_value": observed["value"],
        "observation_method": "deterministic_verification",
        "producing_operation_ref": typed_ref("operation", operation_id),
        "artifact_ref": typed_ref("artifact", artifact_id),
        "source_refs": source_refs,
        "lineage_status": "complete",
        "lineage_limitations": [],
        "comparison": _semantic_slot(observed.get("comparison"), analysis_refs, "comparison"),
        "orientation": _semantic_slot(observed.get("orientation"), analysis_refs, "orientation"),
        "scale": _semantic_slot(
            None,
            input_refs,
            "measurement scale; the observed outcome column name is not sufficient to establish it",
        ),
        "unit": _semantic_slot(None, [], "unit"),
        "population": _semantic_slot(None, [], "population"),
        "timing": _semantic_slot(None, [], "timing"),
        "provenance": controller_provenance("deterministic_scalar_verification", created_at),
    }


def _build_operations(
    records: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    parser_result: dict[str, Any],
) -> list[dict[str, Any]]:
    known_artifacts = {str(record["artifact_id"]) for record in artifacts}
    emitted = {
        str(ref["record_id"])
        for ref in parser_result.get("emitted_record_refs", [])
        if ref.get("record_type") == "operation"
    }
    opaque_reasons = [
        str(boundary["reason"])
        for boundary in parser_result.get("opaque_constructs", [])
        if isinstance(boundary.get("reason"), str) and boundary["reason"]
    ]
    result: list[dict[str, Any]] = []
    for observed in records:
        operation_id = str(observed["operation_id"])
        if operation_id not in emitted:
            raise ObservedRecordError(f"Operation {operation_id!r} is not parser-linked")
        kind = str(observed["kind"])
        inspection_status = str(observed["inspection_status"])
        boundaries = opaque_reasons if kind == "opaque_operation" else []
        if kind == "opaque_operation" and not boundaries:
            boundaries = ["Static dispatch could not resolve the callable target."]
        implementation = observed.get("implementation")
        if not isinstance(implementation, str) or not implementation:
            raise ObservedRecordError(f"Operation {operation_id!r} has no implementation")
        result.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "operation",
                "operation_id": operation_id,
                "audit_run_id": str(observed["run_id"]),
                "kind": kind,
                "source_refs": copy.deepcopy(observed["source_refs"]),
                "input_refs": [
                    _artifact_ref(value, known_artifacts)
                    for value in observed.get("input_refs", [])
                ],
                "output_refs": [
                    _artifact_ref(value, known_artifacts)
                    for value in observed.get("output_refs", [])
                ],
                "literal_parameters": copy.deepcopy(observed.get("literal_parameters", {})),
                "implementation": {"name": implementation},
                "determinism": "unknown",
                "parser_result_ref": typed_ref(
                    "parser_result", str(parser_result["parser_result_id"])
                ),
                "inspection_status": inspection_status,
                "opaque_boundaries": boundaries,
                "provenance": copy.deepcopy(parser_result["provenance"]),
            }
        )
    return result


def _artifact_ref(value: Any, known_artifacts: set[str]) -> dict[str, str]:
    if not isinstance(value, str) or value not in known_artifacts:
        raise ObservedRecordError(f"Operation edge {value!r} has no exact Artifact target")
    return typed_ref("artifact", value)


def _build_artifacts(
    records: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    artifacts: list[dict[str, Any]] = []
    identities: list[dict[str, Any]] = []
    for observed in records:
        artifact_id = str(observed["artifact_id"])
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
        if {str(item) for item in observed.get("producer_operation_ids", [])} != {
            str(item["operation_id"]) for item in producers
        }:
            raise ObservedRecordError(
                f"Artifact {artifact_id!r} producer declarations conflict with operation edges"
            )
        identity = _artifact_identity(observed, created_at)
        kind = _ARTIFACT_KIND.get(str(observed["kind"]))
        if kind is None:
            raise ObservedRecordError(f"unsupported Artifact kind {observed['kind']!r}")
        record: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "artifact",
            "artifact_id": artifact_id,
            "audit_run_id": str(observed["run_id"]),
            "kind": kind,
            "observed_role": str(observed["kind"]),
            "source_refs": _artifact_sources(artifact_id, producers, consumers, claims),
            "producer_operation_refs": [
                typed_ref("operation", str(item["operation_id"])) for item in producers
            ],
            "consumer_operation_refs": [
                typed_ref("operation", str(item["operation_id"])) for item in consumers
            ],
            "asset_identity_ref": typed_ref("asset_identity", str(identity["asset_identity_id"])),
            "limitations": [
                "Observed structure and lineage do not establish scientific correctness."
            ],
            "provenance": controller_provenance("record_observed_artifact", created_at),
        }
        if isinstance(observed.get("path"), str):
            record["path"] = observed["path"]
        artifacts.append(record)
        identities.append(identity)
    return artifacts, identities


def _artifact_identity(observed: dict[str, Any], created_at: str) -> dict[str, Any]:
    identity = observed.get("identity")
    artifact_id = str(observed["artifact_id"])
    if isinstance(identity, str) and _DIGEST.fullmatch(identity):
        evidence = full_digest_evidence(identity)
    elif isinstance(identity, str) and identity.startswith("derived-from:"):
        evidence = unidentified_evidence(
            "The artifact has producer lineage but no serialized content identity.",
            reported_location=identity,
            limitations=(
                "Producer lineage is not a substitute for exact artifact content identity.",
            ),
        )
    elif isinstance(identity, str) and identity.startswith("unavailable:path:"):
        evidence = unidentified_evidence(
            "The output path was observed statically; project-authored code was not executed.",
            reported_location=identity.removeprefix("unavailable:path:"),
            limitations=("No output bytes existed in the immutable source snapshot.",),
        )
    else:
        raise ObservedRecordError(f"Artifact {artifact_id!r} lacks usable identity evidence")
    return build_asset_identity(
        audit_run_id=str(observed["run_id"]),
        asset_record_type="artifact",
        asset_record_id=artifact_id,
        evidence=evidence,
        created_at=created_at,
    )


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
        if claim.get("report_ref", {}).get("record_id") == artifact_id:
            sources.extend(copy.deepcopy(claim.get("source_refs", [])))
    unique = {repr(sorted(source.items())): source for source in sources}
    return [unique[key] for key in sorted(unique)]


def _build_observed_result(
    observed: dict[str, Any],
    operations: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    created_at: str,
) -> dict[str, Any]:
    result_id = str(observed["result_id"])
    matching_claims = [
        claim
        for claim in claims
        if any(
            ref.get("record_type") == "observed_result" and ref.get("record_id") == result_id
            for ref in claim.get("lineage", {}).get("result_refs", [])
        )
    ]
    if len(matching_claims) != 1:
        raise ObservedRecordError(f"ObservedResult {result_id!r} lacks unique claim lineage")
    operation_ids = {
        ref.get("record_id")
        for ref in matching_claims[0].get("lineage", {}).get("operation_refs", [])
    }
    producers = [item for item in operations if item["operation_id"] in operation_ids]
    if len(producers) != 1 or len(producers[0]["output_refs"]) != 1:
        raise ObservedRecordError(f"ObservedResult {result_id!r} lacks unique producer lineage")
    source_refs = copy.deepcopy(observed["source_refs"])
    analysis_refs = [ref for ref in source_refs if ref.get("path") == "analysis.py"]
    data_refs = [ref for ref in source_refs if ref.get("path") == "data.csv"]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "observed_result",
        "observed_result_id": result_id,
        "audit_run_id": str(observed["run_id"]),
        "value_kind": "scalar",
        "scalar_value": observed["value"],
        "observation_method": "deterministic_verification",
        "producing_operation_ref": typed_ref("operation", str(producers[0]["operation_id"])),
        "artifact_ref": copy.deepcopy(producers[0]["output_refs"][0]),
        "source_refs": source_refs,
        "lineage_status": "complete",
        "lineage_limitations": [],
        "comparison": _semantic_slot(observed.get("comparison"), analysis_refs, "comparison"),
        "orientation": _semantic_slot(observed.get("orientation"), analysis_refs, "orientation"),
        "scale": _semantic_slot(observed.get("scale"), data_refs, "scale"),
        "unit": _semantic_slot(None, [], "unit"),
        "population": _semantic_slot(None, [], "population"),
        "timing": _semantic_slot(None, [], "timing"),
        "provenance": controller_provenance("deterministic_scalar_verification", created_at),
    }


def _semantic_slot(value: Any, refs: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if not isinstance(value, str) or not value or value.lower() == "unknown":
        return {
            "state": "unknown",
            "rationale": f"The {label} was not established by bounded deterministic evidence.",
            "evidence_refs": [],
        }
    if not refs:
        raise ObservedRecordError(f"Known {label} has no exact evidence reference")
    return {"state": "known", "value": value, "evidence_refs": copy.deepcopy(refs)}
