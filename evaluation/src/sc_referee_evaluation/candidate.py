from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import semantic_digest
from sc_referee.detectors.admission import (
    AdmissionContext,
    evaluate_non_maturity_finding_admission,
)
from sc_referee.records.evaluation_candidate import evaluation_candidate_id
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.version import SCHEMA_VERSION


class EvaluationCandidateProjectionError(ValueError):
    """An experimental detector result cannot be projected without inventing authority."""


def project_evaluation_candidate(
    detector_result: dict[str, Any],
    context: AdmissionContext,
    fixture: dict[str, Any],
    scientific_label_freeze: dict[str, Any],
    audit_bundle: dict[str, Any],
    schema_root: Path,
    *,
    candidate_created_at: str,
    output: Path | None = None,
    expected_candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Project a qualification-only candidate after every non-maturity gate passes."""

    if output is not None and (output.exists() or output.is_symlink()):
        raise EvaluationCandidateProjectionError(
            f"DetectorEvaluationCandidate output already exists: {output}"
        )
    registry = LocalSchemaRegistry(schema_root)
    try:
        for record in (detector_result, fixture, audit_bundle):
            registry.validate(record)
    except RecordValidationError as error:
        raise EvaluationCandidateProjectionError(str(error)) from error

    if (
        detector_result.get("state") != "evaluation_finding_candidate"
        or detector_result.get("detector_maturity") != "experimental"
    ):
        raise EvaluationCandidateProjectionError(
            "Evaluation projection requires an experimental evaluation_finding_candidate result."
        )
    _validate_label_freeze(scientific_label_freeze, candidate_created_at)
    _validate_fixture_binding(fixture, scientific_label_freeze, detector_result)
    _validate_source_bundle_binding(detector_result, audit_bundle)

    admission_checks = evaluate_non_maturity_finding_admission(detector_result, context)
    if admission_checks is None:
        raise EvaluationCandidateProjectionError(
            "The source result failed a shared non-maturity Finding-admission check."
        )
    draft = dict(context.finding_draft)
    subject_refs = _typed_refs(
        draft.get("subject_refs"), "Finding draft subject_refs", nonempty=True
    )
    affected_record_refs = _affected_refs(draft)
    root_locator = draft.get("root_cause")
    issue_class = draft.get("issue_class")
    if not isinstance(root_locator, dict) or not isinstance(issue_class, str) or not issue_class:
        raise EvaluationCandidateProjectionError(
            "The Finding draft lacks an exact root locator or issue class."
        )

    non_inferences = sorted(
        {
            *context.non_inferences,
            "This qualification-only candidate is not a production Finding.",
            "Bypassing maturity for evaluation does not grant Finding authority.",
        }
    )
    candidate: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "detector_evaluation_candidate",
        "evaluation_candidate_id": "pending",
        "case_id": scientific_label_freeze["case_id"],
        "fixture_ref": _ref("benchmark_fixture", str(fixture["fixture_id"])),
        "scientific_label_freeze_digest": scientific_label_freeze["freeze_digest"],
        "audit_bundle_ref": _ref("audit_bundle", str(audit_bundle["bundle_id"])),
        "audit_bundle_digest": semantic_digest(audit_bundle),
        "semantic_lock_digest": audit_bundle["semantic_lock_digest"],
        "detector_id": detector_result["detector_id"],
        "detector_version": detector_result["detector_version"],
        "detector_manifest_digest": detector_result["detector_manifest_digest"],
        "source_detector_result_ref": _ref("detector_result", str(detector_result["result_id"])),
        "source_detector_result_digest": semantic_digest(detector_result),
        "proposed_assessment_type": "finding",
        "title": draft["title"],
        "bounded_statement": draft["summary"],
        "issue_class": issue_class,
        "root_locator": deepcopy(root_locator),
        "subject_refs": subject_refs,
        "affected_record_refs": affected_record_refs,
        "evidence": deepcopy(detector_result["evidence"]),
        "admission_checks": admission_checks,
        "maturity_gate_bypassed_for_evaluation": True,
        "production_admission_permitted": False,
        "production_finding_ref": None,
        "candidate_created_at": candidate_created_at,
        "non_inferences": non_inferences,
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-eval",
                "display_name": "sc-referee evaluation controller",
            },
            "method": "deterministic_evaluation_candidate_projection",
            "created_at": candidate_created_at,
            "tool": "sc-referee-eval",
            "tool_version": "0.1.0",
        },
    }
    candidate["evaluation_candidate_id"] = evaluation_candidate_id(candidate)
    try:
        registry.validate(candidate)
    except RecordValidationError as error:  # pragma: no cover - construction invariant
        raise EvaluationCandidateProjectionError(str(error)) from error
    if expected_candidate is not None and candidate != expected_candidate:
        raise EvaluationCandidateProjectionError(
            "Model-free evaluation-candidate replay does not equal the source candidate."
        )
    if output is not None:
        write_normalized_json_once(output, candidate)
    return candidate


def _validate_label_freeze(label_freeze: dict[str, Any], created_at: str) -> None:
    digest_input = dict(label_freeze)
    expected_digest = digest_input.pop("freeze_digest", None)
    if (
        label_freeze.get("record_type") != "evaluation_scientific_label_freeze"
        or label_freeze.get("detector_output_observed") is not False
        or expected_digest != semantic_digest(digest_input)
    ):
        raise EvaluationCandidateProjectionError(
            "The scientific-label freeze is invalid or already observed detector output."
        )
    if _timestamp(created_at) <= _timestamp(str(label_freeze.get("frozen_at"))):
        raise EvaluationCandidateProjectionError(
            "Evaluation candidate creation must follow the scientific-label freeze."
        )


def _validate_fixture_binding(
    fixture: dict[str, Any], label_freeze: dict[str, Any], result: dict[str, Any]
) -> None:
    if fixture.get("adjudication_ref") != label_freeze.get("adjudication_ref"):
        raise EvaluationCandidateProjectionError(
            "Fixture and scientific-label freeze do not share an adjudication."
        )
    scope = fixture.get("declared_scope")
    detector_ids = scope.get("detector_ids") if isinstance(scope, dict) else None
    if not isinstance(detector_ids, list) or result.get("detector_id") not in detector_ids:
        raise EvaluationCandidateProjectionError(
            "The experimental detector is outside the fixture's declared scope."
        )


def _validate_source_bundle_binding(
    detector_result: dict[str, Any], audit_bundle: dict[str, Any]
) -> None:
    results = audit_bundle.get("detector_results")
    if not isinstance(results, list):
        raise EvaluationCandidateProjectionError("AuditBundle detector_results is unavailable.")
    matches = [
        value
        for value in results
        if isinstance(value, dict) and value.get("result_id") == detector_result.get("result_id")
    ]
    if len(matches) != 1 or semantic_digest(matches[0]) != semantic_digest(detector_result):
        raise EvaluationCandidateProjectionError(
            "The exact source DetectorResult is absent from the supplied AuditBundle."
        )


def _affected_refs(draft: dict[str, Any]) -> list[dict[str, Any]]:
    descendants = draft.get("affected_descendants")
    if not isinstance(descendants, list):
        raise EvaluationCandidateProjectionError(
            "Finding draft affected_descendants must be a list."
        )
    refs = []
    for descendant in descendants:
        if not isinstance(descendant, dict):
            raise EvaluationCandidateProjectionError(
                "Finding draft affected_descendants must contain objects."
            )
        refs.append(descendant.get("target_ref"))
    return _typed_refs(refs, "Finding draft affected descendant refs", nonempty=False)


def _typed_refs(value: Any, label: str, *, nonempty: bool) -> list[dict[str, Any]]:
    if not isinstance(value, list) or (nonempty and not value):
        raise EvaluationCandidateProjectionError(f"{label} must be a typed-reference list.")
    refs: dict[tuple[str, str], dict[str, Any]] = {}
    for item in value:
        if not isinstance(item, dict):
            raise EvaluationCandidateProjectionError(f"{label} must contain only objects.")
        record_type = item.get("record_type")
        record_id = item.get("record_id")
        if not isinstance(record_type, str) or not isinstance(record_id, str):
            raise EvaluationCandidateProjectionError(f"{label} contains an invalid reference.")
        refs[(record_type, record_id)] = deepcopy(item)
    return [refs[key] for key in sorted(refs)]


def _ref(record_type: str, record_id: str) -> dict[str, str]:
    return {"record_type": record_type, "record_id": record_id}


def _timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise EvaluationCandidateProjectionError(f"Invalid timestamp: {value!r}") from error
