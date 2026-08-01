from __future__ import annotations

import csv
import platform
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.parsers.scalar_verification import (
    UnsupportedScalarVerification,
    verify_mean_difference,
)
from sc_referee.records.observed import (
    ObservedRecordError,
    build_public_verified_result,
    controller_provenance,
    typed_ref,
)
from sc_referee.version import SCHEMA_VERSION, __version__


@dataclass(frozen=True)
class BoundedLineageOutput:
    observed_results: list[dict[str, Any]]
    data_assets: list[dict[str, Any]]
    variables: list[dict[str, Any]]
    analysis_decisions: list[dict[str, Any]]
    selection_envelopes: list[dict[str, Any]]
    executions: list[dict[str, Any]]
    environments: list[dict[str, Any]]
    promotion_gap_paths: list[str]


_BOUNDED_LINEAGE_ARRAYS = (
    "observed_results",
    "data_assets",
    "variables",
    "analysis_decisions",
    "selection_envelopes",
    "executions",
    "environments",
)


def bounded_lineage_runtime_digest() -> str:
    """Bind cached auditor-runtime descendants to their observed runtime identity."""

    return semantic_digest(
        {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "system": platform.system() or "unknown",
            "machine": platform.machine() or "unknown",
            "tool_version": __version__,
            "schema_version": SCHEMA_VERSION,
        }
    )


def bounded_lineage_payload(output: BoundedLineageOutput) -> dict[str, Any]:
    return {
        name: deepcopy(getattr(output, name))
        for name in (*_BOUNDED_LINEAGE_ARRAYS, "promotion_gap_paths")
    }


def bounded_lineage_from_payload(
    payload: dict[str, Any], run_id: str, created_at: str
) -> BoundedLineageOutput:
    """Validate and materialize a cached lineage payload for the current AuditRun."""

    if any(not isinstance(payload.get(name), list) for name in _BOUNDED_LINEAGE_ARRAYS):
        raise ObservedRecordError("cached bounded-lineage payload is malformed")
    if not isinstance(payload.get("promotion_gap_paths"), list) or not all(
        isinstance(value, str) for value in payload["promotion_gap_paths"]
    ):
        raise ObservedRecordError("cached bounded-lineage gap paths are malformed")
    rebound = deepcopy(payload)
    id_map: dict[str, str] = {}
    for data_asset in rebound["data_assets"]:
        if not isinstance(data_asset, dict):
            raise ObservedRecordError("cached DataAsset is malformed")
        old_id = str(data_asset.get("data_asset_id", ""))
        artifact_id = str(data_asset.get("artifact_ref", {}).get("record_id", ""))
        content_digests = {
            str(ref["content_digest"])
            for ref in data_asset.get("source_refs", [])
            if isinstance(ref, dict) and isinstance(ref.get("content_digest"), str)
        }
        if not old_id or not artifact_id or len(content_digests) != 1:
            raise ObservedRecordError("cached DataAsset cannot be rebound exactly")
        id_map[old_id] = stable_id("data-asset", run_id, artifact_id, next(iter(content_digests)))
    for variable in rebound["variables"]:
        if not isinstance(variable, dict):
            raise ObservedRecordError("cached Variable is malformed")
        old_id = str(variable.get("variable_id", ""))
        old_data_id = str(variable.get("data_asset_ref", {}).get("record_id", ""))
        name = variable.get("observed_name")
        if not old_id or old_data_id not in id_map or not isinstance(name, str):
            raise ObservedRecordError("cached Variable cannot be rebound exactly")
        id_map[old_id] = stable_id("variable", id_map[old_data_id], name)
    for environment in rebound["environments"]:
        if not isinstance(environment, dict):
            raise ObservedRecordError("cached Environment is malformed")
        old_id = str(environment.get("environment_id", ""))
        runtime = environment.get("runtime", {})
        target = environment.get("platform", {})
        if (
            not old_id
            or not isinstance(runtime, dict)
            or not isinstance(target, dict)
            or environment.get("environment_kind") != "auditor_runtime"
        ):
            raise ObservedRecordError("cached Environment cannot be rebound exactly")
        id_map[old_id] = stable_id(
            "environment-auditor",
            run_id,
            str(runtime.get("version", "")),
            str(runtime.get("implementation", "")),
            str(target.get("system", "unknown")),
            str(target.get("machine", "unknown")),
        )

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            provenance = value.get("provenance")
            if isinstance(provenance, dict):
                actor = provenance.get("actor", {})
                if isinstance(actor, dict) and actor.get("actor_kind") in {
                    "controller",
                    "runtime",
                }:
                    provenance["created_at"] = created_at
            for key, child in list(value.items()):
                if key in {"audit_run_id", "run_id"}:
                    value[key] = run_id
                elif isinstance(child, str) and child in id_map:
                    value[key] = id_map[child]
                else:
                    visit(child)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                if isinstance(child, str) and child in id_map:
                    value[index] = id_map[child]
                else:
                    visit(child)

    visit(rebound)
    return BoundedLineageOutput(
        observed_results=deepcopy(rebound["observed_results"]),
        data_assets=deepcopy(rebound["data_assets"]),
        variables=deepcopy(rebound["variables"]),
        analysis_decisions=deepcopy(rebound["analysis_decisions"]),
        selection_envelopes=deepcopy(rebound["selection_envelopes"]),
        executions=deepcopy(rebound["executions"]),
        environments=deepcopy(rebound["environments"]),
        promotion_gap_paths=list(rebound["promotion_gap_paths"]),
    )


LineageGradeStatus = Literal["complete", "partial", "missing", "unavailable", "opaque"]
AggregateLineageStatus = Literal["complete", "partial", "missing", "unavailable"]
LINEAGE_GRADE_DIMENSIONS = (
    "report_origin",
    "result_origin",
    "computational_origin",
    "input_origin",
    "execution_origin",
    "semantic_origin",
)
_LINEAGE_GRADE_STATUSES = {"complete", "partial", "missing", "unavailable", "opaque"}


def derive_aggregate_lineage_status(
    grades: Mapping[str, LineageGradeStatus],
) -> AggregateLineageStatus:
    """Derive the only conservative aggregate from six independent grade states."""

    if set(grades) != set(LINEAGE_GRADE_DIMENSIONS):
        raise ValueError("lineage grades must contain exactly the six normative dimensions")
    values = list(grades.values())
    if any(value not in _LINEAGE_GRADE_STATUSES for value in values):
        raise ValueError("lineage grade has an unsupported status")
    if all(value == "complete" for value in values):
        return "complete"
    positive_edge_present = any(value in {"complete", "partial"} for value in values)
    if "missing" in values and not positive_edge_present:
        return "missing"
    if all(value == "unavailable" for value in values):
        return "unavailable"
    return "partial"


def reconstruct_bounded_results(
    materialized_root: Path,
    parser_results: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    run_id: str,
    created_at: str,
) -> BoundedLineageOutput:
    """Recompute only the exact filtered mean-difference profile from snapshot bytes."""

    observed_by_id: dict[str, dict[str, Any]] = {}
    plane_by_type: dict[str, dict[str, dict[str, Any]]] = {
        "data_assets": {},
        "variables": {},
        "analysis_decisions": {},
        "selection_envelopes": {},
        "executions": {},
        "environments": {},
    }
    static_decisions, static_envelopes = _static_selection_plane(
        operations,
        run_id,
        created_at,
    )
    plane_by_type["analysis_decisions"] = {
        _public_record_id(record): record for record in static_decisions
    }
    plane_by_type["selection_envelopes"] = {
        _public_record_id(record): record for record in static_envelopes
    }
    gap_paths: set[str] = set()
    for parser_result in sorted(
        parser_results, key=lambda item: str(item.get("source_ref", {}).get("path", ""))
    ):
        if parser_result.get("parser_id") != "parser:python-ast-tokenize":
            continue
        if parser_result.get("state") != "parsed":
            continue
        if parser_result.get("source_ref", {}).get("source_kind") != "file_span":
            # Container cells have static syntax coverage but no virtual-source-aware
            # numerical verifier; do not mistake the container bytes for Python source.
            continue
        logical_path = str(parser_result.get("source_ref", {}).get("path", ""))
        candidate = PurePosixPath(logical_path)
        if not logical_path or candidate.is_absolute() or ".." in candidate.parts:
            gap_paths.add(logical_path or "unknown")
            continue
        try:
            raw = verify_mean_difference(
                materialized_root / logical_path,
                run_id,
                source_path=logical_path,
            )
            public = build_public_verified_result(raw, operations, artifacts, created_at)
            plane = _build_bounded_lineage_plane(
                raw,
                public,
                operations,
                artifacts,
                materialized_root,
                run_id,
                created_at,
            )
        except (UnsupportedScalarVerification, OSError, UnicodeError, SyntaxError):
            # The bounded verifier is not applicable. Parser coverage remains authoritative.
            continue
        except ObservedRecordError:
            gap_paths.add(logical_path)
            continue
        result_id = str(public["observed_result_id"])
        existing = observed_by_id.get(result_id)
        if existing is not None and existing != public:
            gap_paths.add(logical_path)
            observed_by_id.pop(result_id, None)
            continue
        observed_by_id[result_id] = public
        for array_name, records in plane.items():
            target = plane_by_type[array_name]
            for record in records:
                record_id = _public_record_id(record)
                existing_record = target.get(record_id)
                if existing_record is not None and existing_record != record:
                    gap_paths.add(logical_path)
                    continue
                target[record_id] = record
    return BoundedLineageOutput(
        observed_results=[observed_by_id[key] for key in sorted(observed_by_id)],
        data_assets=_sorted_records(plane_by_type["data_assets"]),
        variables=_sorted_records(plane_by_type["variables"]),
        analysis_decisions=_sorted_records(plane_by_type["analysis_decisions"]),
        selection_envelopes=_sorted_records(plane_by_type["selection_envelopes"]),
        executions=_sorted_records(plane_by_type["executions"]),
        environments=_sorted_records(plane_by_type["environments"]),
        promotion_gap_paths=sorted(gap_paths),
    )


def _sorted_records(records: Mapping[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [records[key] for key in sorted(records)]


def _public_record_id(record: Mapping[str, Any]) -> str:
    candidates = [key for key in record if key.endswith("_id") and key != "audit_run_id"]
    if len(candidates) != 1:
        raise ObservedRecordError("lineage-plane record lacks one public identity")
    return str(record[candidates[0]])


def _build_bounded_lineage_plane(
    observed: dict[str, Any],
    public_result: dict[str, Any],
    operations: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    materialized_root: Path,
    run_id: str,
    created_at: str,
) -> dict[str, list[dict[str, Any]]]:
    operation_id = str(public_result["producing_operation_ref"]["record_id"])
    operation = next(
        (item for item in operations if str(item.get("operation_id")) == operation_id), None
    )
    if operation is None:
        raise ObservedRecordError("bounded lineage plane has no producing Operation")
    input_refs = operation.get("input_refs", [])
    if len(input_refs) != 1 or input_refs[0].get("record_type") != "artifact":
        raise ObservedRecordError("bounded lineage plane requires one exact input Artifact")
    input_artifact_id = str(input_refs[0]["record_id"])
    artifact = next(
        (item for item in artifacts if str(item.get("artifact_id")) == input_artifact_id), None
    )
    if artifact is None:
        raise ObservedRecordError("bounded lineage plane input Artifact is unavailable")
    input_path = str(observed["input_path"])
    data_ref = next(
        (deepcopy(ref) for ref in public_result["source_refs"] if ref.get("path") == input_path),
        None,
    )
    if data_ref is None:
        raise ObservedRecordError("bounded lineage plane lacks an exact input source")
    variables, data_asset = _inspect_delimited_data_asset(
        materialized_root / input_path,
        input_path,
        data_ref,
        artifact,
        run_id,
        created_at,
    )
    environment = _auditor_environment(run_id, created_at)
    execution = _auditor_execution(
        public_result,
        operation,
        data_asset,
        environment,
        created_at,
    )
    decision = _literal_selection_decision(
        operation,
        data_asset,
        public_result,
        created_at,
    )
    envelope = _bounded_selection_envelope(decision, public_result, created_at)
    return {
        "data_assets": [data_asset],
        "variables": variables,
        "analysis_decisions": [decision],
        "selection_envelopes": [envelope],
        "executions": [execution],
        "environments": [environment],
    }


def _inspect_delimited_data_asset(
    path: Path,
    logical_path: str,
    source_ref: dict[str, Any],
    artifact: dict[str, Any],
    run_id: str,
    created_at: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    suffix = PurePosixPath(logical_path).suffix.casefold()
    if suffix not in {".csv", ".tsv"}:
        raise ObservedRecordError("bounded DataAsset supports only CSV or TSV input")
    delimiter = "\t" if suffix == ".tsv" else ","
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ObservedRecordError("bounded DataAsset has missing or duplicate headers")
        rows = list(reader)
    data_asset_id = stable_id(
        "data-asset", run_id, str(artifact["artifact_id"]), str(source_ref["content_digest"])
    )
    variables: list[dict[str, Any]] = []
    for name in reader.fieldnames:
        values = [str(row.get(name, "")) for row in rows]
        variable_id = stable_id("variable", data_asset_id, name)
        variables.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "variable",
                "variable_id": variable_id,
                "audit_run_id": run_id,
                "data_asset_ref": typed_ref("data_asset", data_asset_id),
                "observed_name": name,
                "storage_type": _observed_storage_type(values),
                "observed_level_count": len(set(values)),
                "scientific_meaning_status": "unresolved",
                "semantic_assertion_refs": [],
                "source_refs": [deepcopy(source_ref)],
                "limitations": [
                    "Observed name, values, and storage type do not establish scientific role, unit, scale, or meaning."
                ],
                "provenance": controller_provenance(
                    "bounded_delimited_structure_inspection", created_at
                ),
            }
        )
    data_asset = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "data_asset",
        "data_asset_id": data_asset_id,
        "audit_run_id": run_id,
        "artifact_ref": typed_ref("artifact", str(artifact["artifact_id"])),
        "asset_identity_ref": deepcopy(artifact["asset_identity_ref"]),
        "role": "input",
        "format": suffix.removeprefix("."),
        "path": logical_path,
        "structure_status": "complete",
        "variable_refs": [typed_ref("variable", str(item["variable_id"])) for item in variables],
        "source_refs": [deepcopy(source_ref)],
        "limitations": [],
        "provenance": controller_provenance("bounded_delimited_structure_inspection", created_at),
    }
    return variables, data_asset


def _observed_storage_type(values: list[str]) -> str:
    present = [value for value in values if value != ""]
    if not present:
        return "unknown"
    lowered = {value.casefold() for value in present}
    if lowered <= {"true", "false"}:
        return "boolean"
    try:
        for value in present:
            int(value)
    except ValueError:
        pass
    else:
        return "integer"
    try:
        for value in present:
            float(value)
    except ValueError:
        return "string"
    return "number"


def _auditor_environment(run_id: str, created_at: str) -> dict[str, Any]:
    runtime_version = platform.python_version()
    implementation = platform.python_implementation()
    system = platform.system() or "unknown"
    machine = platform.machine() or "unknown"
    environment_id = stable_id(
        "environment-auditor", run_id, runtime_version, implementation, system, machine
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "environment",
        "environment_id": environment_id,
        "audit_run_id": run_id,
        "environment_kind": "auditor_runtime",
        "identity_status": "partial",
        "runtime": {
            "name": "Python",
            "version": runtime_version,
            "implementation": implementation,
        },
        "platform": {"system": system, "machine": machine},
        "dependency_refs": [],
        "source_refs": [
            {"source_kind": "runtime_command", "locator": "sc-referee bounded verifier runtime"}
        ],
        "limitations": [
            "Runtime and platform identity were observed, but the full dependency environment was not captured."
        ],
        "provenance": {
            "actor": {"actor_kind": "runtime", "actor_id": "runtime:sc-referee"},
            "method": "auditor_runtime_introspection",
            "created_at": created_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }


def _auditor_execution(
    result: dict[str, Any],
    operation: dict[str, Any],
    data_asset: dict[str, Any],
    environment: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    result_id = str(result["observed_result_id"])
    command_payload = {
        "method": "bounded_mean_difference_recomputation",
        "operation_id": str(operation["operation_id"]),
        "result_id": result_id,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "execution",
        "execution_id": stable_id("execution-auditor-verification", result_id),
        "audit_run_id": str(result["audit_run_id"]),
        "execution_kind": "auditor_verification",
        "actor": "sc_referee_auditor",
        "method": "bounded_mean_difference_recomputation",
        "command": {
            "display": "internal:verify_mean_difference",
            "normalized_digest": sha256_digest(canonical_json(command_payload)),
        },
        "input_refs": [typed_ref("data_asset", str(data_asset["data_asset_id"]))],
        "output_refs": [typed_ref("observed_result", result_id)],
        "environment_ref": typed_ref("environment", str(environment["environment_id"])),
        "timing": {"state": "unavailable"},
        "exit": {"state": "succeeded", "code": 0},
        "sandbox": {
            "project_code_executed": False,
            "authorization_status": "not_required",
            "network_policy": "denied",
        },
        "authorization_evidence_status": "not_required",
        "project_execution": None,
        "identity_strength": "exact",
        "source_refs": deepcopy(result["source_refs"]),
        "limitations": [
            "This auditor-owned recomputation is not evidence that the project workflow executed."
        ],
        "provenance": {
            "actor": {"actor_kind": "runtime", "actor_id": "runtime:sc-referee"},
            "method": "bounded_auditor_verification",
            "created_at": created_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }


def _literal_selection_decision(
    operation: dict[str, Any],
    data_asset: dict[str, Any],
    result: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    parameters = operation.get("literal_parameters", {})
    alternatives = []
    for role in ("left_group", "right_group"):
        value = parameters.get(role)
        if not isinstance(value, str) or not value:
            raise ObservedRecordError("bounded decision lacks exact comparison literals")
        alternatives.append(
            {
                "alternative_id": stable_id(
                    "alternative", str(operation["operation_id"]), role, value
                ),
                "label": value,
                "state": "selected",
                "source_refs": deepcopy(operation["source_refs"]),
            }
        )
    decision_id = stable_id("analysis-decision", str(operation["operation_id"]), "subgroup")
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "analysis_decision",
        "analysis_decision_id": decision_id,
        "audit_run_id": str(operation["audit_run_id"]),
        "decision_kind": "subgroup",
        "observation_status": "observed",
        "description": "Literal group membership filters observed in the supported computation.",
        "decision_input_refs": [typed_ref("data_asset", str(data_asset["data_asset_id"]))],
        "alternatives": alternatives,
        "selection_statistic": {"state": "not_applicable", "source_refs": []},
        "outcome_influence": "not_assessed",
        "downstream_refs": [
            typed_ref("operation", str(operation["operation_id"])),
            typed_ref("observed_result", str(result["observed_result_id"])),
        ],
        "source_refs": deepcopy(operation["source_refs"]),
        "limitations": [
            "Static literals establish the implemented filters, not why they were selected or whether alternatives were considered."
        ],
        "provenance": deepcopy(operation["provenance"]),
    }


def _bounded_selection_envelope(
    decision: dict[str, Any], result: dict[str, Any], created_at: str
) -> dict[str, Any]:
    decision_id = str(decision["analysis_decision_id"])
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "selection_envelope",
        "selection_envelope_id": stable_id("selection-envelope", decision_id),
        "audit_run_id": str(decision["audit_run_id"]),
        "completeness_status": "partial",
        "scope_description": "Observed literal alternatives within one bounded mean-difference operation.",
        "analysis_decision_refs": [typed_ref("analysis_decision", decision_id)],
        "candidate_alternative_count": len(decision["alternatives"]),
        "affected_claim_refs": [],
        "affected_result_refs": [typed_ref("observed_result", str(result["observed_result_id"]))],
        "source_refs": deepcopy(decision["source_refs"]),
        "limitations": [
            "Other analysis decisions and unobserved alternatives may exist outside this bounded operation."
        ],
        "provenance": controller_provenance("bounded_selection_envelope_construction", created_at),
    }


def _static_selection_plane(
    operations: list[dict[str, Any]], run_id: str, created_at: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    recognized_estimate_spans = [
        source_ref
        for operation in operations
        if operation.get("kind") == "estimate"
        and all(
            isinstance(operation.get("literal_parameters", {}).get(key), str)
            for key in ("outcome_column", "left_group", "right_group")
        )
        for source_ref in operation.get("source_refs", [])
    ]
    decisions: list[dict[str, Any]] = []
    envelopes: list[dict[str, Any]] = []
    for operation in operations:
        parameters = operation.get("literal_parameters", {})
        predicates = _literal_filter_predicates(parameters)
        if operation.get("kind") != "filter" or predicates is None:
            continue
        source_refs = deepcopy(operation.get("source_refs", []))
        if not source_refs or any(
            _source_ref_within(source_refs[0], estimate_ref)
            for estimate_ref in recognized_estimate_spans
        ):
            continue
        operation_id = str(operation["operation_id"])
        for index, predicate in enumerate(predicates):
            field = str(predicate["filter_field"])
            operator = str(predicate["filter_operator"])
            value = predicate["filter_value"]
            decision_kind = (
                "threshold"
                if operator
                in {
                    "less_than",
                    "less_than_or_equal",
                    "greater_than",
                    "greater_than_or_equal",
                }
                else "filter"
            )
            decision_id = stable_id(
                "analysis-decision",
                operation_id,
                "literal-filter",
                str(index),
                canonical_json(predicate),
            )
            label = f"{field} {_display_operator(operator)} {value!r}"
            decision = {
                "schema_version": SCHEMA_VERSION,
                "record_type": "analysis_decision",
                "analysis_decision_id": decision_id,
                "audit_run_id": run_id,
                "decision_kind": decision_kind,
                "observation_status": "observed",
                "description": (
                    "One exact literal filter predicate was observed in supported static Python "
                    "selection syntax."
                ),
                "decision_input_refs": deepcopy(operation.get("input_refs", [])),
                "alternatives": [
                    {
                        "alternative_id": stable_id(
                            "alternative", operation_id, str(index), canonical_json(predicate)
                        ),
                        "label": label,
                        "state": "selected",
                        "source_refs": source_refs,
                    }
                ],
                "selection_statistic": {"state": "not_applicable", "source_refs": []},
                "outcome_influence": "not_assessed",
                "downstream_refs": [typed_ref("operation", operation_id)],
                "source_refs": source_refs,
                "limitations": [
                    "The literal predicate is observed, but execution, runtime selection semantics, its scientific role, rationale, candidate alternatives, and outcome influence were not established."
                ],
                "provenance": deepcopy(operation["provenance"]),
            }
            envelope = {
                "schema_version": SCHEMA_VERSION,
                "record_type": "selection_envelope",
                "selection_envelope_id": stable_id("selection-envelope", decision_id),
                "audit_run_id": run_id,
                "completeness_status": "partial",
                "scope_description": (
                    "Exact literal filter alternatives observed in one supported Python operation."
                ),
                "analysis_decision_refs": [typed_ref("analysis_decision", decision_id)],
                "candidate_alternative_count": 1,
                "affected_claim_refs": [],
                "affected_result_refs": [],
                "source_refs": source_refs,
                "limitations": [
                    "Only the implemented literal predicate is known; rejected or unimplemented alternatives and broader selection decisions remain unavailable."
                ],
                "provenance": controller_provenance(
                    "bounded_static_selection_envelope", created_at
                ),
            }
            decisions.append(decision)
            envelopes.append(envelope)
    return decisions, envelopes


def _literal_filter_predicates(parameters: Any) -> list[dict[str, Any]] | None:
    if not isinstance(parameters, dict):
        return None
    if all(key in parameters for key in ("filter_field", "filter_operator", "filter_value")):
        return [
            {
                "filter_field": parameters["filter_field"],
                "filter_operator": parameters["filter_operator"],
                "filter_value": parameters["filter_value"],
            }
        ]
    fields = parameters.get("filter_fields")
    operators = parameters.get("filter_operators")
    values = parameters.get("filter_values")
    if (
        parameters.get("filter_logical_operator") != "and"
        or not isinstance(fields, list)
        or not isinstance(operators, list)
        or not isinstance(values, list)
        or not fields
        or len(fields) != len(operators)
        or len(fields) != len(values)
        or not all(isinstance(field, str) for field in fields)
        or not all(isinstance(operator, str) for operator in operators)
    ):
        return None
    return [
        {
            "filter_field": field,
            "filter_operator": operator,
            "filter_value": value,
        }
        for field, operator, value in zip(fields, operators, values, strict=True)
    ]


def _source_ref_within(inner: dict[str, Any], outer: dict[str, Any]) -> bool:
    return (
        inner.get("path") == outer.get("path")
        and isinstance(inner.get("start_line"), int)
        and isinstance(inner.get("end_line"), int)
        and isinstance(outer.get("start_line"), int)
        and isinstance(outer.get("end_line"), int)
        and inner["start_line"] >= outer["start_line"]
        and inner["end_line"] <= outer["end_line"]
    )


def _display_operator(operator: str) -> str:
    return {
        "equal": "==",
        "not_equal": "!=",
        "less_than": "<",
        "less_than_or_equal": "<=",
        "greater_than": ">",
        "greater_than_or_equal": ">=",
        "in": "in",
        "not_in": "not in",
    }[operator]


def bind_bounded_claim_lineage(
    claims: list[dict[str, Any]],
    observed_results: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    data_assets: list[dict[str, Any]] | None = None,
    executions: list[dict[str, Any]] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Bind only unique exact literal/result alignments, retaining a partial lineage grade."""

    operations_by_id = {str(item["operation_id"]): item for item in operations}
    data_assets_by_artifact = {
        str(item.get("artifact_ref", {}).get("record_id")): item for item in (data_assets or [])
    }
    executions_by_result: dict[str, list[dict[str, Any]]] = {}
    for execution in executions or []:
        for ref in execution.get("output_refs", []):
            if ref.get("record_type") == "observed_result":
                executions_by_result.setdefault(str(ref.get("record_id")), []).append(execution)
    linked_claims: list[dict[str, Any]] = []
    artifacts_by_id = {str(item["artifact_id"]): item for item in (artifacts or [])}
    for source_claim in claims:
        claim = deepcopy(source_claim)
        report_artifact_id = str(claim.get("report_ref", {}).get("record_id", ""))
        report_artifact = artifacts_by_id.get(report_artifact_id)
        report_producer_refs = [
            deepcopy(ref)
            for ref in (report_artifact or {}).get("producer_operation_refs", [])
            if ref.get("record_type") == "operation"
            and str(ref.get("record_id")) in operations_by_id
            and operations_by_id[str(ref["record_id"])].get("kind") == "write"
        ]
        claim["lineage"] = _unlinked_claim_lineage(claim, report_producer_refs)
        if report_producer_refs:
            claim.setdefault("extensions", {})["x-static-report-output-path-linked"] = True
        candidates: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for result in observed_results:
            operation_id = str(result.get("producing_operation_ref", {}).get("record_id", ""))
            operation = operations_by_id.get(operation_id)
            if operation is not None and _exact_alignment(claim, result, operation):
                candidates.append((result, operation))
        if len(candidates) != 1:
            linked_claims.append(claim)
            continue
        result, operation = candidates[0]
        result_id = str(result["observed_result_id"])
        result_artifact_ref = result.get("artifact_ref")
        static_report_result_flow = (
            len(report_producer_refs) == 1
            and isinstance(result_artifact_ref, dict)
            and report_producer_refs[0].get("record_type") == "operation"
            and result_artifact_ref
            in operations_by_id[str(report_producer_refs[0]["record_id"])].get("input_refs", [])
            and operations_by_id[str(report_producer_refs[0]["record_id"])]
            .get("literal_parameters", {})
            .get("static_result_artifact_flow")
            in {
                "direct_supported_call",
                "direct_static_formatter_call",
                "single_static_formatter_assignment",
                "static_formatter_assignment_chain",
                "function_local_direct_supported_call",
                "function_local_single_assignment_alias",
                "function_local_single_assignment_alias_chain",
                "function_parameter_bound_direct",
                "function_parameter_bound_alias_chain",
                "function_result_literal_parameters_bound_direct",
                "function_result_literal_parameters_bound_alias_chain",
                "function_result_literal_path_parameters_bound_direct",
                "function_result_literal_path_parameters_bound_alias_chain",
                "function_keyword_bound_result_flow_direct",
                "function_keyword_bound_result_flow_alias_chain",
                "single_assignment_alias",
                "single_assignment_alias_chain",
            }
        )
        input_refs = deepcopy(operation.get("input_refs", []))
        input_grade_refs: list[dict[str, str]] = []
        for ref in input_refs:
            data_asset = data_assets_by_artifact.get(str(ref.get("record_id")))
            input_grade_refs.append(
                typed_ref("data_asset", str(data_asset["data_asset_id"]))
                if data_asset is not None
                else deepcopy(ref)
            )
        auditor_executions = executions_by_result.get(result_id, [])
        grades = {
            "report_origin": {
                "status": "complete",
                "record_refs": [deepcopy(claim["report_ref"])],
                "source_refs": deepcopy(claim["source_refs"]),
                "limitations": [],
            },
            "result_origin": {
                "status": "partial",
                "record_refs": [typed_ref("observed_result", result_id)],
                "source_refs": deepcopy(result.get("source_refs", [])),
                "limitations": [
                    (
                        "Exact literal alignment and source-level result-Artifact flow reach the report writer, but no project Execution proves that writer produced the snapshotted report bytes or claim wording."
                        if static_report_result_flow
                        else "Exact literal alignment links this result to the claim, but no observed report-generation edge proves derivation of the wording."
                    )
                ],
            },
            "computational_origin": {
                "status": "complete",
                "record_refs": [typed_ref("operation", str(operation["operation_id"]))],
                "source_refs": deepcopy(operation.get("source_refs", [])),
                "limitations": [],
            },
            "input_origin": {
                "status": "complete" if input_grade_refs else "missing",
                "record_refs": input_grade_refs,
                "source_refs": [],
                "limitations": (
                    []
                    if input_grade_refs
                    else ["No exact input record was bound to the producing operation."]
                ),
            },
            "execution_origin": {
                "status": "missing",
                "record_refs": [
                    typed_ref("execution", str(item["execution_id"])) for item in auditor_executions
                ],
                "source_refs": [],
                "limitations": [
                    "Only auditor-owned verification was observed; project workflow execution was not observed."
                ],
            },
            "semantic_origin": _semantic_origin_grade(claim),
        }
        operation_refs_by_id = {
            str(ref["record_id"]): ref
            for ref in [
                typed_ref("operation", str(operation["operation_id"])),
                *report_producer_refs,
            ]
        }
        if static_report_result_flow:
            report_generation_gap = (
                "Source-level dataflow links the verified result Artifact to the exact report writer, "
                "but no project Execution establishes that the writer produced the snapshotted "
                "report bytes or this claim wording."
            )
        elif report_producer_refs:
            report_generation_gap = (
                "A static source operation targets the exact report path, but no project Execution "
                "establishes that it produced the snapshotted report bytes or wording."
            )
        else:
            report_generation_gap = (
                "No observed report-generation or project-execution edge establishes that this "
                "verified computation produced the exact report wording."
            )
        claim["lineage"] = {
            "status": derive_aggregate_lineage_status(
                {key: value["status"] for key, value in grades.items()}
            ),
            "result_refs": [typed_ref("observed_result", result_id)],
            "operation_refs": [operation_refs_by_id[key] for key in sorted(operation_refs_by_id)],
            "input_refs": input_refs,
            "missing_links": [report_generation_gap],
            "opaque_dependency_refs": [],
            "grades": grades,
        }
        claim_extensions = claim.setdefault("extensions", {})
        claim_extensions["x-lineage-link-basis"] = (
            "unique_exact_literal_alignment_with_static_report_result_artifact_flow_v1"
            if static_report_result_flow
            else "unique_exact_literal_alignment_to_verified_mean_difference_v1"
        )
        if static_report_result_flow:
            claim_extensions["x-static-report-result-artifact-flow-linked"] = True
        linked_claims.append(claim)
    return linked_claims


def _unlinked_claim_lineage(
    claim: dict[str, Any], report_producer_refs: list[dict[str, str]] | None = None
) -> dict[str, Any]:
    report_producer_refs = report_producer_refs or []
    report_grade = {
        "status": "complete",
        "record_refs": [deepcopy(claim["report_ref"])],
        "source_refs": deepcopy(claim["source_refs"]),
        "limitations": [],
    }
    grades = {
        "report_origin": report_grade,
        "result_origin": {
            "status": "missing",
            "record_refs": [],
            "source_refs": [],
            "limitations": ["No unique observed result was bound to this claim."],
        },
        "computational_origin": {
            "status": "missing",
            "record_refs": [],
            "source_refs": [],
            "limitations": ["No result-producing Operation was bound to this claim."],
        },
        "input_origin": {
            "status": "missing",
            "record_refs": [],
            "source_refs": [],
            "limitations": ["No exact input record was bound to this claim."],
        },
        "execution_origin": {
            "status": "missing",
            "record_refs": [],
            "source_refs": [],
            "limitations": ["No project workflow Execution was observed."],
        },
        "semantic_origin": _semantic_origin_grade(claim),
    }
    return {
        "status": derive_aggregate_lineage_status(
            {key: value["status"] for key, value in grades.items()}
        ),
        "result_refs": [],
        "operation_refs": deepcopy(report_producer_refs),
        "input_refs": [],
        "missing_links": [
            (
                "A static source operation targets the exact report path, but no unique observed result, result-producing computation, input record, or project Execution was bound to this literal claim."
                if report_producer_refs
                else "No unique observed result, result-producing operation, or input record was bound to this literal claim."
            )
        ],
        "opaque_dependency_refs": [],
        "grades": grades,
    }


def _semantic_origin_grade(claim: dict[str, Any]) -> dict[str, Any]:
    assertion_ids = [
        str(value)
        for value in claim.get("extraction", {}).get("semantic_assertion_ids", [])
        if isinstance(value, str)
    ]
    record_refs = [typed_ref("semantic_assertion", value) for value in assertion_ids]
    unresolved = claim.get("extensions", {}).get("x-scientific-semantics-unresolved")
    if unresolved is False and record_refs:
        return {
            "status": "complete",
            "record_refs": record_refs,
            "source_refs": [],
            "limitations": [],
        }
    if record_refs:
        return {
            "status": "partial",
            "record_refs": record_refs,
            "source_refs": [],
            "limitations": [
                "Scientist declarations resolve only a subset of the bounded semantic dimensions."
            ],
        }
    return {
        "status": "missing",
        "record_refs": [],
        "source_refs": [],
        "limitations": ["No scope-bound scientist semantic declaration is available."],
    }


def _exact_alignment(
    claim: dict[str, Any], result: dict[str, Any], operation: dict[str, Any]
) -> bool:
    parameters = operation.get("literal_parameters", {})
    if not all(
        isinstance(parameters.get(key), str)
        for key in ("outcome_column", "left_group", "right_group")
    ):
        return False
    proposition = claim.get("proposition", {})
    comparison = proposition.get("comparison")
    if not isinstance(comparison, str):
        return False
    parts = comparison.split(" versus ")
    if len(parts) != 2:
        return False
    literal_object = claim.get("extensions", {}).get("x-literal-object")
    if not isinstance(literal_object, str):
        return False
    result_comparison = result.get("comparison", {})
    if result_comparison.get("state") != "known":
        return False
    expected_comparison = f"{parameters['left_group']} versus {parameters['right_group']}"
    return (
        _normalized(parts[0]) == _normalized(str(parameters["left_group"]))
        and _normalized(parts[1]) == _normalized(str(parameters["right_group"]))
        and _normalized(literal_object) == _normalized(str(parameters["outcome_column"]))
        and _normalized(str(result_comparison.get("value"))) == _normalized(expected_comparison)
    )


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())
