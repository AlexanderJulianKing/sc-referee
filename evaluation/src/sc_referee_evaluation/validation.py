from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from sc_referee.core.errors import RecordValidationError
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee_evaluation.root_cause import (
    RootCauseReconciliationError,
    validate_adjudicated_root_cause,
)
from sc_referee_evaluation.snapshot_evidence import (
    SnapshotEvidenceError,
    SnapshotEvidenceIndex,
    read_full_digest_snapshot_file,
    validate_content_addressed_snapshot,
)


class EvaluationValidationError(ValueError):
    """A case packet is internally inconsistent or exceeds the verified envelope."""


_ELIGIBLE_LABELS = {
    "positive_demonstrated",
    "verified_good_eligible",
    "hard_negative_eligible",
}
_EXCLUDED_LABELS = {
    "ambiguous_excluded",
    "insufficient_evidence",
    "adjudication_failed",
}
_FIXTURE_KINDS_BY_LABEL = {
    "positive_demonstrated": {"positive_issue_fixture"},
    "verified_good_eligible": {
        "verified_good_fixture",
        "scope_verified_good",
        "static_scope_verified_good",
    },
    "hard_negative_eligible": {
        "hard_negative_fixture",
        "static_scope_hard_negative",
    },
    "ambiguous_excluded": {"ambiguous_fixture"},
    "insufficient_evidence": {"ambiguous_fixture"},
    "adjudication_failed": {"ambiguous_fixture"},
}


def validate_case_packet(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    reviews: list[dict[str, Any]],
    schema_root: Path,
    *,
    adjudicated_root_causes: list[dict[str, Any]] | None = None,
    snapshot: dict[str, Any] | None = None,
    file_records: list[dict[str, Any]] | None = None,
    asset_identities: list[dict[str, Any]] | None = None,
    materialized_root: Path | None = None,
) -> dict[str, Any]:
    """Reconcile one exact answer-side panel without admitting an unverified label."""

    snapshot_inputs = (snapshot, file_records, asset_identities, materialized_root)
    if any(item is not None for item in snapshot_inputs) and not all(
        item is not None for item in snapshot_inputs
    ):
        raise EvaluationValidationError(
            "Snapshot evidence requires the snapshot, FileRecords, AssetIdentities, and materialized root."
        )
    roots = adjudicated_root_causes or []
    _validate_public_records(
        fixture,
        adjudication,
        reviews,
        roots,
        schema_root,
        snapshot=snapshot,
        file_records=file_records,
        asset_identities=asset_identities,
    )
    review_index = _review_index(reviews)
    stage1 = _resolve_reviews(adjudication, review_index, "stage1")
    stage2 = _resolve_reviews(adjudication, review_index, "stage2")
    referenced_ids = {str(item["review_id"]) for item in [*stage1, *stage2]}
    if referenced_ids != set(review_index):
        raise EvaluationValidationError(
            "The supplied case packet must contain exactly the adjudication-referenced reviews."
        )

    _validate_case_identity(fixture, adjudication, [*stage1, *stage2])
    _validate_stage_order(stage1, stage2)
    participation = _validate_provider_participation(adjudication, stage1, stage2)
    label_status = str(adjudication["label_status"])
    _validate_root_cause_links(
        fixture,
        adjudication,
        roots,
        stage1,
        stage2,
        schema_root,
        label_status,
    )
    fixture_kind = str(fixture["fixture_kind"])
    allowed_kinds = _FIXTURE_KINDS_BY_LABEL[label_status]
    if fixture_kind not in allowed_kinds:
        raise EvaluationValidationError(
            f"The fixture kind {fixture_kind!r} is incompatible with label {label_status!r}."
        )

    if label_status in _ELIGIBLE_LABELS:
        _validate_eligible_panel(label_status, roots, stage1, stage2)
        panel_consistency = "consistent"
        label_admission = "withheld_pending_independent_evidence_checks"
        unverified_checks = ["source_references_resolve_against_fixture_snapshot"]
    elif label_status in _EXCLUDED_LABELS:
        panel_consistency = "consistent_exclusion"
        label_admission = "excluded_by_adjudication"
        unverified_checks = []
    else:  # pragma: no cover - the public schema closes this enum
        raise EvaluationValidationError(f"Unsupported adjudication label {label_status!r}.")

    resolved_source_ref_count = 0
    independently_checked = [
        "public_schema_validity",
        "record_reference_resolution",
        "case_identity",
        "independent_execution_contexts",
        "provider_participation_counts",
        "stage_chronology",
        "material_dissent_exclusion",
        "fixture_label_compatibility",
    ]
    if label_status == "positive_demonstrated":
        independently_checked.append("canonical_root_cause_reconciliation")
    if (
        snapshot is not None
        and file_records is not None
        and asset_identities is not None
        and materialized_root is not None
    ):
        resolved_source_ref_count = _validate_snapshot_source_refs(
            fixture,
            [*stage1, *stage2],
            snapshot,
            file_records,
            asset_identities,
            materialized_root,
            require_each_review=label_status in _ELIGIBLE_LABELS,
        )
        unverified_checks = [
            check
            for check in unverified_checks
            if check != "source_references_resolve_against_fixture_snapshot"
        ]
        independently_checked.append("source_references_resolve_against_fixture_snapshot")
    if label_status in _ELIGIBLE_LABELS and not unverified_checks:
        label_admission = "admitted_for_declared_fixture_scope"

    return {
        "case_id": adjudication["case_id"],
        "fixture_id": fixture["fixture_id"],
        "adjudication_id": adjudication["adjudication_id"],
        "panel_consistency": panel_consistency,
        "label_status": label_status,
        "label_admission": label_admission,
        "provider_participation": participation,
        "resolved_source_ref_count": resolved_source_ref_count,
        "independently_checked": independently_checked,
        "unverified_checks": unverified_checks,
    }


def _validate_public_records(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    reviews: list[dict[str, Any]],
    adjudicated_root_causes: list[dict[str, Any]],
    schema_root: Path,
    *,
    snapshot: dict[str, Any] | None,
    file_records: list[dict[str, Any]] | None,
    asset_identities: list[dict[str, Any]] | None,
) -> None:
    registry = LocalSchemaRegistry(schema_root)
    try:
        additional_records = [
            *([snapshot] if snapshot is not None else []),
            *(file_records or []),
            *(asset_identities or []),
        ]
        for record in [
            fixture,
            adjudication,
            *reviews,
            *adjudicated_root_causes,
            *additional_records,
        ]:
            registry.validate(record)
    except RecordValidationError as error:
        raise EvaluationValidationError(str(error)) from error


def _review_index(reviews: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for review in reviews:
        review_id = str(review["review_id"])
        if review_id in index:
            raise EvaluationValidationError(f"Duplicate AgentReview identity {review_id!r}.")
        index[review_id] = review
    return index


def _resolve_reviews(
    adjudication: dict[str, Any],
    review_index: dict[str, dict[str, Any]],
    stage: str,
) -> list[dict[str, Any]]:
    expected_stage = {
        "stage1": "stage1_blind",
        "stage2": "stage2_scientific_adjudication",
    }[stage]
    refs = adjudication[f"{stage}_review_refs"]
    resolved: list[dict[str, Any]] = []
    for ref in refs:
        if ref.get("record_type") != "agent_review":
            raise EvaluationValidationError(f"A {stage} reference is not an AgentReview.")
        review_id = str(ref.get("record_id"))
        review = review_index.get(review_id)
        if review is None:
            raise EvaluationValidationError(f"Unresolved {stage} AgentReview {review_id!r}.")
        if review.get("stage") != expected_stage:
            raise EvaluationValidationError(
                f"AgentReview {review_id!r} does not have the referenced {stage} stage."
            )
        resolved.append(review)
    return resolved


def _validate_case_identity(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    reviews: list[dict[str, Any]],
) -> None:
    adjudication_id = str(adjudication["adjudication_id"])
    adjudication_ref = fixture["adjudication_ref"]
    if (
        adjudication_ref.get("record_type") != "benchmark_adjudication"
        or adjudication_ref.get("record_id") != adjudication_id
    ):
        raise EvaluationValidationError(
            "BenchmarkFixture adjudication_ref does not resolve to this adjudication."
        )
    case_id = adjudication["case_id"]
    if any(review.get("case_id") != case_id for review in reviews):
        raise EvaluationValidationError("Every AgentReview must match the adjudication case_id.")


def _validate_stage_order(stage1: list[dict[str, Any]], stage2: list[dict[str, Any]]) -> None:
    last_stage1 = max(_timestamp(str(review["completed_at"])) for review in stage1)
    first_stage2 = min(_timestamp(str(review["completed_at"])) for review in stage2)
    if first_stage2 < last_stage1:
        raise EvaluationValidationError(
            "A Stage-2 review cannot complete before the frozen Stage-1 panel."
        )


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _validate_provider_participation(
    adjudication: dict[str, Any],
    stage1: list[dict[str, Any]],
    stage2: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    all_reviews = [*stage1, *stage2]
    contexts = [str(review["reviewer_agent"]["execution_context_id"]) for review in all_reviews]
    if len(contexts) != len(set(contexts)):
        raise EvaluationValidationError(
            "Every linked review must use a distinct independent execution context."
        )

    stage1_counts = Counter(str(review["reviewer_agent"]["provider"]) for review in stage1)
    stage2_counts = Counter(str(review["reviewer_agent"]["provider"]) for review in stage2)
    contexts_by_provider: dict[str, set[str]] = defaultdict(set)
    for review in all_reviews:
        agent = review["reviewer_agent"]
        contexts_by_provider[str(agent["provider"])].add(str(agent["execution_context_id"]))
    actual_providers = set(contexts_by_provider)
    if set(str(item) for item in adjudication["provider_families"]) != actual_providers:
        raise EvaluationValidationError(
            "Adjudication provider_families do not equal the linked review providers."
        )

    declared: dict[str, dict[str, Any]] = {}
    for item in adjudication["provider_participation"]:
        provider = str(item["provider_family"])
        if provider in declared:
            raise EvaluationValidationError(
                f"Provider participation is declared more than once for {provider!r}."
            )
        declared[provider] = item
    if set(declared) != actual_providers:
        raise EvaluationValidationError(
            "Provider participation rows do not equal the linked review providers."
        )

    result: dict[str, dict[str, int]] = {}
    for provider in sorted(actual_providers):
        actual = {
            "stage1": stage1_counts[provider],
            "stage2": stage2_counts[provider],
            "distinct_contexts": len(contexts_by_provider[provider]),
        }
        expected = declared[provider]
        if (
            expected["stage1_review_count"] != actual["stage1"]
            or expected["stage2_review_count"] != actual["stage2"]
            or expected["distinct_execution_context_count"] != actual["distinct_contexts"]
        ):
            raise EvaluationValidationError(
                f"Declared provider participation does not reconcile for {provider!r}."
            )
        result[provider] = actual
    return result


def _validate_eligible_panel(
    label_status: str,
    adjudicated_root_causes: list[dict[str, Any]],
    stage1: list[dict[str, Any]],
    stage2: list[dict[str, Any]],
) -> None:
    if any(review.get("unresolved_material_questions") for review in [*stage1, *stage2]):
        raise EvaluationValidationError(
            "An eligible label cannot retain unresolved material review questions."
        )
    for review in stage2:
        falsification = review["falsification_attempt"]
        if falsification["material_dissent"] or falsification["outcome"] == "unresolved":
            raise EvaluationValidationError(
                "An eligible label cannot conceal material dissent in Stage-2 falsification."
            )

    if label_status == "positive_demonstrated":
        expected_verdict = "demonstrated_issue"
        if any(review.get("verdict") != expected_verdict for review in [*stage1, *stage2]):
            raise EvaluationValidationError(
                "This bounded first slice requires every linked review to support a positive label."
            )
        issue_class = adjudicated_root_causes[0]["issue_class"]
        if any(review.get("issue_class") != issue_class for review in [*stage1, *stage2]):
            raise EvaluationValidationError(
                "Every positive review must match the adjudicated issue class."
            )
        if any(
            review["falsification_attempt"]["outcome"] != "root_cause_survived" for review in stage2
        ):
            raise EvaluationValidationError(
                "Every positive Stage-2 falsification must retain the root cause."
            )
    else:
        if any(
            review.get("verdict") != "no_demonstrated_issue_within_scope"
            for review in [*stage1, *stage2]
        ):
            raise EvaluationValidationError(
                "This bounded first slice requires every linked review to support the negative label."
            )


def _validate_snapshot_source_refs(
    fixture: dict[str, Any],
    reviews: list[dict[str, Any]],
    snapshot: dict[str, Any],
    file_records: list[dict[str, Any]],
    asset_identities: list[dict[str, Any]],
    materialized_root: Path,
    *,
    require_each_review: bool,
) -> int:
    snapshot_id = str(snapshot["snapshot_id"])
    snapshot_ref = fixture["snapshot_ref"]
    if (
        snapshot_ref.get("record_type") != "repository_snapshot"
        or snapshot_ref.get("record_id") != snapshot_id
    ):
        raise EvaluationValidationError(
            "BenchmarkFixture snapshot_ref does not resolve to the supplied immutable snapshot."
        )
    try:
        snapshot_index = validate_content_addressed_snapshot(
            snapshot, file_records, asset_identities
        )
    except SnapshotEvidenceError as error:
        raise EvaluationValidationError(str(error)) from error

    resolved = 0
    for review in reviews:
        source_refs = _review_source_refs(review)
        if require_each_review and not source_refs:
            raise EvaluationValidationError(
                f"Eligible AgentReview {review['review_id']!r} has no exact source reference."
            )
        for source_ref in source_refs:
            validate_file_source_ref(
                source_ref,
                snapshot_index,
                materialized_root,
            )
            resolved += 1
    return resolved


def _review_source_refs(review: dict[str, Any]) -> list[dict[str, Any]]:
    evidence_items = [*review.get("evidence", []), *review.get("counterevidence_considered", [])]
    falsification = review.get("falsification_attempt")
    if isinstance(falsification, dict):
        evidence_items.extend(falsification.get("evidence_tested", []))
    root_cause_identity = review.get("root_cause_identity")
    if isinstance(root_cause_identity, dict):
        evidence_items.extend(root_cause_identity.get("equivalence_evidence", []))
    return [
        source_ref for evidence in evidence_items for source_ref in evidence.get("source_refs", [])
    ]


def _validate_root_cause_links(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    roots: list[dict[str, Any]],
    stage1: list[dict[str, Any]],
    stage2: list[dict[str, Any]],
    schema_root: Path,
    label_status: str,
) -> None:
    roots_by_id = {str(root["adjudicated_root_cause_id"]): root for root in roots}
    if len(roots_by_id) != len(roots):
        raise EvaluationValidationError("Duplicate AdjudicatedRootCause identity.")
    supplied_refs = {("adjudicated_root_cause", root_id) for root_id in roots_by_id}
    adjudication_refs = {
        (str(ref.get("record_type")), str(ref.get("record_id")))
        for ref in adjudication["adjudicated_root_cause_refs"]
    }
    fixture_refs = {
        (str(ref.get("record_type")), str(ref.get("record_id")))
        for ref in fixture["expected_root_cause_refs"]
    }
    if label_status == "positive_demonstrated":
        if len(roots) != 1:
            raise EvaluationValidationError(
                "This first reconciliation slice requires exactly one canonical root cause."
            )
        if supplied_refs != adjudication_refs or fixture_refs != adjudication_refs:
            raise EvaluationValidationError(
                "Fixture, adjudication, and supplied root-cause references do not resolve exactly."
            )
        root = roots[0]
        if root.get("case_id") != adjudication.get("case_id"):
            raise EvaluationValidationError(
                "AdjudicatedRootCause case does not match the adjudication."
            )
        if root.get("adjudicated_at") != adjudication.get("adjudicated_at"):
            raise EvaluationValidationError(
                "Root-cause and benchmark adjudication timestamps must match exactly."
            )
        try:
            validate_adjudicated_root_cause(root, stage1, stage2, schema_root)
        except RootCauseReconciliationError as error:
            raise EvaluationValidationError(str(error)) from error
    elif roots or adjudication_refs or fixture_refs:
        raise EvaluationValidationError(
            "A nonpositive label cannot carry an admitted positive root cause."
        )


def validate_file_source_ref(
    source_ref: dict[str, Any],
    snapshot_index: SnapshotEvidenceIndex,
    materialized_root: Path,
) -> None:
    if source_ref.get("source_kind") != "file_span" or source_ref.get("external") is True:
        raise EvaluationValidationError(
            "This first evidence resolver supports only in-snapshot file_span references."
        )
    path_value = source_ref.get("path")
    if not isinstance(path_value, str):
        raise EvaluationValidationError("A file_span evidence reference requires an exact path.")
    try:
        _file_record, _identity, payload, digest = read_full_digest_snapshot_file(
            snapshot_index, materialized_root, path_value
        )
    except SnapshotEvidenceError as error:
        raise EvaluationValidationError(str(error)) from error
    if source_ref.get("content_digest") != digest:
        raise EvaluationValidationError(
            f"Evidence digest for {path_value!r} does not match the immutable fixture bytes."
        )
    _validate_text_span(source_ref, payload)


def _validate_text_span(source_ref: dict[str, Any], payload: bytes) -> None:
    start_line = source_ref.get("start_line")
    end_line = source_ref.get("end_line")
    quoted_text = source_ref.get("quoted_text")
    if start_line is None and end_line is None and quoted_text is None:
        return
    if not isinstance(start_line, int) or not isinstance(end_line, int):
        raise EvaluationValidationError("Text evidence requires both start_line and end_line.")
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise EvaluationValidationError(
            "Text evidence does not reference valid UTF-8 bytes."
        ) from error
    if start_line > end_line or end_line > len(lines):
        raise EvaluationValidationError("Evidence line span falls outside the immutable file.")
    if quoted_text is None:
        return
    selected = lines[start_line - 1 : end_line]
    start_column = source_ref.get("start_column")
    end_column = source_ref.get("end_column")
    if start_line == end_line and isinstance(start_column, int) and isinstance(end_column, int):
        selected_text = selected[0][start_column - 1 : end_column - 1]
    else:
        selected_text = "\n".join(selected)
    if selected_text != quoted_text:
        raise EvaluationValidationError(
            "Evidence quoted_text does not match the immutable fixture span."
        )
