from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.schema_registry import LocalSchemaRegistry


class DetectorComparisonError(ValueError):
    """A Stage-3 detector comparison violates its bounded integrity protocol."""


_EXCLUDED_LABELS = {
    "ambiguous_excluded",
    "insufficient_evidence",
    "adjudication_failed",
}
_ELIGIBLE_LABELS = {
    "positive_demonstrated",
    "verified_good_eligible",
    "hard_negative_eligible",
}


def compare_detector_output(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    scientific_label_freeze: dict[str, Any],
    audit_bundle: dict[str, Any],
    detector_id: str,
    schema_root: Path,
    *,
    compared_at: str,
    output: Path,
) -> dict[str, Any]:
    """Bind one detector's post-freeze output without scoring scientific correctness."""

    if output.exists() or output.is_symlink():
        raise DetectorComparisonError(f"Stage-3 comparison output already exists: {output}")
    if not detector_id:
        raise DetectorComparisonError("Stage-3 detector_id must be non-empty.")
    _validate_public_records(fixture, adjudication, audit_bundle, schema_root)
    _validate_case_binding(fixture, adjudication, scientific_label_freeze)
    _validate_fixture_snapshot_binding(fixture, audit_bundle)
    if _timestamp(compared_at) <= _timestamp(str(scientific_label_freeze["frozen_at"])):
        raise DetectorComparisonError(
            "Stage-3 comparison must occur after the scientific-label freeze."
        )

    declared_detector_ids = {str(value) for value in fixture["declared_scope"]["detector_ids"]}
    if detector_id not in declared_detector_ids:
        raise DetectorComparisonError(
            f"Detector {detector_id!r} is outside the fixture's declared detector scope."
        )

    detector_results = _list_of_objects(audit_bundle.get("detector_results"), "detector_results")
    findings = _list_of_objects(audit_bundle.get("findings"), "findings")
    results_by_id = _unique_index(detector_results, "result_id", "DetectorResult")
    _unique_index(findings, "finding_id", "Finding")
    _validate_bundle_audit_identity(audit_bundle, detector_results, findings)
    selected_results = [
        record for record in detector_results if record.get("detector_id") == detector_id
    ]
    if not selected_results:
        raise DetectorComparisonError(
            f"AuditBundle contains no DetectorResult for declared detector {detector_id!r}."
        )
    detector_versions = {str(record["detector_version"]) for record in selected_results}
    manifest_digests = {str(record["detector_manifest_digest"]) for record in selected_results}
    if len(detector_versions) != 1 or len(manifest_digests) != 1:
        raise DetectorComparisonError(
            "One Stage-3 comparison requires one exact detector version and manifest digest."
        )

    selected_result_ids = {str(record["result_id"]) for record in selected_results}
    solely_attributable: list[dict[str, Any]] = []
    mixed_attribution: list[dict[str, Any]] = []
    for finding in findings:
        linked_ids = {str(value) for value in finding["detector_result_ids"]}
        missing = sorted(linked_ids - set(results_by_id))
        if missing:
            raise DetectorComparisonError(
                f"Finding {finding['finding_id']!r} references absent DetectorResult IDs: {missing}"
            )
        overlap = linked_ids & selected_result_ids
        if not overlap:
            continue
        if linked_ids <= selected_result_ids:
            solely_attributable.append(finding)
        else:
            mixed_attribution.append(finding)

    in_scope, out_of_scope, unresolved_scope = _classify_scope(fixture, solely_attributable)
    label_status = str(adjudication["label_status"])
    if label_status in _EXCLUDED_LABELS:
        comparison_status = "excluded_scientific_label"
    elif label_status in _ELIGIBLE_LABELS:
        comparison_status = "withheld_pending_independent_label_admission"
    else:  # pragma: no cover - public schema closes this enum
        raise DetectorComparisonError(f"Unsupported scientific label {label_status!r}.")

    selected_results_sorted = sorted(selected_results, key=lambda item: str(item["result_id"]))
    result_state_counts = Counter(str(record["state"]) for record in selected_results_sorted)
    audit_bundle_digest = semantic_digest(audit_bundle)
    comparison: dict[str, Any] = {
        "evaluation_protocol_version": "0.1.0",
        "record_type": "evaluation_stage3_detector_comparison",
        "comparison_id": stable_id(
            "stage3-comparison",
            str(adjudication["case_id"]),
            detector_id,
            str(scientific_label_freeze["freeze_digest"]),
            audit_bundle_digest,
        ),
        "case_id": adjudication["case_id"],
        "fixture_id": fixture["fixture_id"],
        "adjudication_ref": {
            "record_type": "benchmark_adjudication",
            "record_id": adjudication["adjudication_id"],
        },
        "scientific_label": {
            "label_status": label_status,
            "fixture_kind": fixture["fixture_kind"],
            "label_freeze_digest": scientific_label_freeze["freeze_digest"],
            "adjudication_digest": scientific_label_freeze["adjudication_digest"],
        },
        "detector_output": {
            "audit_bundle_id": audit_bundle["bundle_id"],
            "audit_bundle_digest": audit_bundle_digest,
            "audit_run_id": audit_bundle["audit_run_id"],
            "detector_id": detector_id,
            "detector_version": next(iter(detector_versions)),
            "detector_manifest_digest": next(iter(manifest_digests)),
            "detector_result_refs": [
                {"record_type": "detector_result", "record_id": record["result_id"]}
                for record in selected_results_sorted
            ],
            "detector_result_state_counts": dict(sorted(result_state_counts.items())),
            "attributable_finding_refs": _finding_refs(solely_attributable),
            "exact_in_scope_finding_refs": _finding_refs(in_scope),
            "exact_out_of_scope_finding_refs": _finding_refs(out_of_scope),
            "unresolved_scope_finding_refs": _finding_refs(unresolved_scope),
            "mixed_detector_attribution_finding_refs": _finding_refs(mixed_attribution),
        },
        "comparison_status": comparison_status,
        "metric_eligible": False,
        "detector_output_observed": True,
        "compared_at": compared_at,
        "non_inferences": [
            "Detector observations are not classified as true positives, false positives, true negatives, or false negatives.",
            "This comparison does not qualify the detector or alter the frozen scientific label.",
            "Exact identifier overlap does not establish semantic root-cause equivalence.",
        ],
    }
    comparison["comparison_digest"] = semantic_digest(comparison)
    write_normalized_json_once(output, comparison)
    return comparison


def _validate_public_records(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    audit_bundle: dict[str, Any],
    schema_root: Path,
) -> None:
    registry = LocalSchemaRegistry(schema_root)
    try:
        for record in (fixture, adjudication, audit_bundle):
            registry.validate(record)
    except RecordValidationError as error:
        raise DetectorComparisonError(str(error)) from error


def _validate_case_binding(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    scientific_label_freeze: dict[str, Any],
) -> None:
    freeze_digest = scientific_label_freeze.get("freeze_digest")
    digest_input = dict(scientific_label_freeze)
    digest_input.pop("freeze_digest", None)
    if freeze_digest != semantic_digest(digest_input):
        raise DetectorComparisonError("Scientific-label freeze digest is invalid.")
    if scientific_label_freeze.get("record_type") != "evaluation_scientific_label_freeze":
        raise DetectorComparisonError("Scientific-label freeze record kind is invalid.")
    if scientific_label_freeze.get("detector_output_observed") is not False:
        raise DetectorComparisonError(
            "Scientific-label freeze must precede observation of detector output."
        )
    adjudication_id = str(adjudication["adjudication_id"])
    fixture_ref = fixture["adjudication_ref"]
    freeze_ref = scientific_label_freeze.get("adjudication_ref", {})
    if (
        fixture_ref.get("record_type") != "benchmark_adjudication"
        or fixture_ref.get("record_id") != adjudication_id
        or freeze_ref.get("record_type") != "benchmark_adjudication"
        or freeze_ref.get("record_id") != adjudication_id
    ):
        raise DetectorComparisonError(
            "Fixture and scientific-label freeze do not bind the supplied adjudication."
        )
    if (
        scientific_label_freeze.get("case_id") != adjudication.get("case_id")
        or scientific_label_freeze.get("label_status") != adjudication.get("label_status")
        or scientific_label_freeze.get("adjudication_digest") != semantic_digest(adjudication)
    ):
        raise DetectorComparisonError(
            "Scientific-label freeze identity, label, or adjudication digest has drifted."
        )
    frozen_stage2_refs = {
        (
            str(item.get("review_ref", {}).get("record_type")),
            str(item.get("review_ref", {}).get("record_id")),
        )
        for item in _list_of_objects(
            scientific_label_freeze.get("stage2_reviews"), "frozen Stage-2 reviews"
        )
    }
    adjudication_stage2_refs = {
        (str(item.get("record_type")), str(item.get("record_id")))
        for item in adjudication["stage2_review_refs"]
    }
    if frozen_stage2_refs != adjudication_stage2_refs:
        raise DetectorComparisonError(
            "Scientific-label freeze Stage-2 review refs do not match the adjudication."
        )
    frozen_root_refs = {
        (
            str(item.get("root_cause_ref", {}).get("record_type")),
            str(item.get("root_cause_ref", {}).get("record_id")),
        )
        for item in _list_of_objects(
            scientific_label_freeze.get("adjudicated_root_causes", []),
            "frozen adjudicated root causes",
        )
    }
    adjudication_root_refs = {
        (str(item.get("record_type")), str(item.get("record_id")))
        for item in adjudication["adjudicated_root_cause_refs"]
    }
    if frozen_root_refs != adjudication_root_refs:
        raise DetectorComparisonError(
            "Scientific-label freeze root-cause refs do not match the adjudication."
        )


def _validate_bundle_audit_identity(
    audit_bundle: dict[str, Any],
    detector_results: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> None:
    audit_run_id = audit_bundle["audit_run_id"]
    if any(record.get("audit_run_id") != audit_run_id for record in detector_results):
        raise DetectorComparisonError(
            "Every DetectorResult must belong to the AuditBundle audit_run_id."
        )
    if any(record.get("audit_run_id") != audit_run_id for record in findings):
        raise DetectorComparisonError("Every Finding must belong to the AuditBundle audit_run_id.")


def _validate_fixture_snapshot_binding(
    fixture: dict[str, Any], audit_bundle: dict[str, Any]
) -> None:
    snapshot_ref = fixture["snapshot_ref"]
    if snapshot_ref.get("record_type") != "repository_snapshot":
        raise DetectorComparisonError("BenchmarkFixture snapshot_ref has the wrong record type.")
    snapshot_id = str(snapshot_ref.get("record_id"))
    snapshots = _list_of_objects(audit_bundle.get("repository_snapshots"), "repository_snapshots")
    snapshots_by_id = _unique_index(snapshots, "snapshot_id", "RepositorySnapshot")
    snapshot = snapshots_by_id.get(snapshot_id)
    if snapshot is None or snapshot.get("immutability") is not True:
        raise DetectorComparisonError(
            "BenchmarkFixture snapshot does not resolve to one immutable AuditBundle snapshot."
        )
    audit_runs = _list_of_objects(audit_bundle.get("audit_runs"), "audit_runs")
    audit_runs_by_id = _unique_index(audit_runs, "audit_run_id", "AuditRun")
    root_run = audit_runs_by_id.get(str(audit_bundle["audit_run_id"]))
    if root_run is None or root_run.get("snapshot_ref") != snapshot_ref:
        raise DetectorComparisonError(
            "AuditBundle root AuditRun does not bind the BenchmarkFixture snapshot."
        )


def _classify_scope(
    fixture: dict[str, Any], findings: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    scope = fixture["declared_scope"]
    scope_refs = {
        (str(item.get("record_type")), str(item.get("record_id")))
        for item in [*scope["claim_refs"], *scope["operation_refs"]]
    }
    issue_classes = {str(value) for value in scope["issue_classes"]}
    in_scope: list[dict[str, Any]] = []
    out_of_scope: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for finding in findings:
        if not scope_refs:
            unresolved.append(finding)
            continue
        subject_refs = {
            (str(item.get("record_type")), str(item.get("record_id")))
            for item in finding["subject_refs"]
        }
        if finding.get("issue_class") in issue_classes and subject_refs & scope_refs:
            in_scope.append(finding)
        else:
            out_of_scope.append(finding)
    return in_scope, out_of_scope, unresolved


def _finding_refs(findings: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"record_type": "finding", "record_id": str(finding["finding_id"])}
        for finding in sorted(findings, key=lambda item: str(item["finding_id"]))
    ]


def _unique_index(
    records: list[dict[str, Any]], identity_key: str, label: str
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        identity = str(record[identity_key])
        if identity in index:
            raise DetectorComparisonError(f"Duplicate {label} identity {identity!r}.")
        index[identity] = record
    return index


def _list_of_objects(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise DetectorComparisonError(f"Expected {label} to be a list of objects.")
    return value


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise DetectorComparisonError(f"Invalid Stage-3 timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise DetectorComparisonError("Stage-3 timestamps must include an offset.")
    return parsed
