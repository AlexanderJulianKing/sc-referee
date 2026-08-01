from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import semantic_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.root_cause import (
    ADJUDICATED_IDENTITY_PROFILE,
    REVIEW_LOCAL_IDENTITY_PROFILE,
    adjudicated_root_cause_id,
    canonical_candidate_refs,
    root_cause_candidate_id,
    root_cause_candidate_ref,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.version import SCHEMA_VERSION


class RootCauseReconciliationError(ValueError):
    """Review-local candidates cannot support one canonical adjudicated root cause."""


def validate_review_local_candidate(review: dict[str, Any]) -> None:
    """Recompute one demonstrated review's local candidate without asserting equivalence."""

    identity = review.get("root_cause_identity")
    if review.get("verdict") != "demonstrated_issue":
        if identity is not None:
            raise RootCauseReconciliationError(
                "A non-demonstrated review cannot carry a root-cause identity."
            )
        return
    if not isinstance(identity, dict):
        raise RootCauseReconciliationError(
            "A demonstrated review requires one review-local root-cause identity."
        )
    if identity.get("identity_profile") != REVIEW_LOCAL_IDENTITY_PROFILE:
        raise RootCauseReconciliationError("The review-local identity profile is unsupported.")
    expected = root_cause_candidate_id(review)
    if identity.get("candidate_root_cause_id") != expected:
        raise RootCauseReconciliationError(
            "The review-local candidate ID does not match the exact review content."
        )


def build_adjudicated_root_cause(
    stage1_reviews: list[dict[str, Any]],
    stage2_reviews: list[dict[str, Any]],
    schema_root: Path,
    *,
    adjudicated_at: str,
    statement_source_review_id: str,
    required_scientific_premises: list[str],
    stronger_claims_excluded: list[str],
    output: Path | None = None,
) -> dict[str, Any]:
    """Create one public root cause only from an exact cross-provider candidate-set decision."""

    if output is not None and (output.exists() or output.is_symlink()):
        raise RootCauseReconciliationError(f"AdjudicatedRootCause output already exists: {output}")
    registry = LocalSchemaRegistry(schema_root)
    try:
        for review in [*stage1_reviews, *stage2_reviews]:
            registry.validate(review)
    except RecordValidationError as error:
        raise RootCauseReconciliationError(str(error)) from error
    case_id, issue_class, candidate_refs = _validate_reconciliation_panel(
        stage1_reviews, stage2_reviews
    )
    stage2_by_id = {str(review["review_id"]): review for review in stage2_reviews}
    statement_source = stage2_by_id.get(statement_source_review_id)
    if statement_source is None:
        raise RootCauseReconciliationError(
            "The statement source must name one of the supporting Stage-2 reviews."
        )
    if not stronger_claims_excluded or any(not item for item in stronger_claims_excluded):
        raise RootCauseReconciliationError(
            "At least one explicit nonempty stronger-claim exclusion is required."
        )
    if any(not item for item in required_scientific_premises):
        raise RootCauseReconciliationError(
            "Required scientific premises must be nonempty when supplied."
        )
    last_stage2 = max(_timestamp(str(review["completed_at"])) for review in stage2_reviews)
    if _timestamp(adjudicated_at) <= last_stage2:
        raise RootCauseReconciliationError(
            "Root-cause adjudication must follow every supporting Stage-2 review."
        )

    evidence = _canonical_objects(
        [
            evidence_item
            for review in stage2_reviews
            for evidence_item in review["root_cause_identity"]["equivalence_evidence"]
        ]
    )
    affected_record_refs = _canonical_objects(
        [
            record_ref
            for review in [*stage1_reviews, *stage2_reviews]
            for record_ref in review.get("affected_record_refs", [])
        ]
    )
    root_cause: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "adjudicated_root_cause",
        "adjudicated_root_cause_id": adjudicated_root_cause_id(
            case_id, issue_class, candidate_refs
        ),
        "case_id": case_id,
        "identity_profile": ADJUDICATED_IDENTITY_PROFILE,
        "stage1_candidate_refs": candidate_refs,
        "stage2_review_refs": sorted(
            [
                {"record_type": "agent_review", "record_id": review["review_id"]}
                for review in stage2_reviews
            ],
            key=lambda item: str(item["record_id"]),
        ),
        "statement_source_review_ref": {
            "record_type": "agent_review",
            "record_id": statement_source_review_id,
        },
        "bounded_statement": statement_source["bounded_statement"],
        "issue_class": issue_class,
        "evidence": evidence,
        "affected_record_refs": affected_record_refs,
        "required_scientific_premises": sorted(set(required_scientific_premises)),
        "stronger_claims_excluded": sorted(set(stronger_claims_excluded)),
        "material_dissent": False,
        "confidence_used_for_identity": False,
        "adjudicated_at": adjudicated_at,
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-eval",
                "display_name": "sc-referee evaluation controller",
            },
            "method": "deterministic_root_cause_reconciliation",
            "created_at": adjudicated_at,
            "tool": "sc-referee-eval",
            "tool_version": "0.1.0",
        },
    }
    try:
        registry.validate(root_cause)
    except RecordValidationError as error:  # pragma: no cover - construction invariant
        raise RootCauseReconciliationError(str(error)) from error
    if output is not None:
        write_normalized_json_once(output, root_cause)
    return root_cause


def validate_adjudicated_root_cause(
    root_cause: dict[str, Any],
    stage1_reviews: list[dict[str, Any]],
    stage2_reviews: list[dict[str, Any]],
    schema_root: Path,
) -> None:
    """Require a public root record to equal the deterministic panel construction."""

    try:
        LocalSchemaRegistry(schema_root).validate(root_cause)
    except RecordValidationError as error:
        raise RootCauseReconciliationError(str(error)) from error
    expected = build_adjudicated_root_cause(
        stage1_reviews,
        stage2_reviews,
        schema_root,
        adjudicated_at=str(root_cause["adjudicated_at"]),
        statement_source_review_id=str(root_cause["statement_source_review_ref"]["record_id"]),
        required_scientific_premises=list(root_cause["required_scientific_premises"]),
        stronger_claims_excluded=list(root_cause["stronger_claims_excluded"]),
    )
    if root_cause != expected:
        raise RootCauseReconciliationError(
            "AdjudicatedRootCause does not equal the deterministic reconciliation record."
        )


def _validate_reconciliation_panel(
    stage1_reviews: list[dict[str, Any]], stage2_reviews: list[dict[str, Any]]
) -> tuple[str, str, list[dict[str, Any]]]:
    if len(stage1_reviews) < 2 or len(stage2_reviews) < 2:
        raise RootCauseReconciliationError(
            "Reconciliation requires at least two Stage-1 and two Stage-2 reviews."
        )
    reviews = [*stage1_reviews, *stage2_reviews]
    if any(review.get("verdict") != "demonstrated_issue" for review in reviews):
        raise RootCauseReconciliationError(
            "Canonical positive reconciliation requires demonstrated-issue reviews only."
        )
    if any(review.get("stage") != "stage1_blind" for review in stage1_reviews) or any(
        review.get("stage") != "stage2_scientific_adjudication" for review in stage2_reviews
    ):
        raise RootCauseReconciliationError("Root-cause reviews are assigned to the wrong stage.")
    case_ids = {str(review.get("case_id")) for review in reviews}
    issue_classes = {str(review.get("issue_class")) for review in reviews}
    if len(case_ids) != 1 or len(issue_classes) != 1:
        raise RootCauseReconciliationError(
            "Every reconciled review must share one case and issue class."
        )
    for review in reviews:
        validate_review_local_candidate(review)
    for review in stage1_reviews:
        identity = review["root_cause_identity"]
        if identity["reconciled_stage1_candidates"] or identity["equivalence_evidence"]:
            raise RootCauseReconciliationError(
                "Stage-1 local candidates cannot contain cross-review reconciliation."
            )
    stage1_by_id = {str(review["review_id"]): review for review in stage1_reviews}
    if len(stage1_by_id) != len(stage1_reviews):
        raise RootCauseReconciliationError("Stage-1 review identities are not unique.")
    stage2_by_id = {str(review["review_id"]): review for review in stage2_reviews}
    if len(stage2_by_id) != len(stage2_reviews):
        raise RootCauseReconciliationError("Stage-2 review identities are not unique.")
    stage1_providers = {_provider(review) for review in stage1_reviews}
    stage2_providers = {_provider(review) for review in stage2_reviews}
    if len(stage1_providers) < 2 or stage2_providers != stage1_providers:
        raise RootCauseReconciliationError(
            "Stage-2 reconciliation requires every Stage-1 provider family."
        )

    selections: list[list[dict[str, Any]]] = []
    for review in stage2_reviews:
        falsification = review.get("falsification_attempt", {})
        if (
            review.get("unresolved_material_questions")
            or falsification.get("material_dissent") is not False
            or falsification.get("outcome") != "root_cause_survived"
        ):
            raise RootCauseReconciliationError(
                "Stage-2 reconciliation retains material dissent, an unresolved question, or failed falsification."
            )
        selection = canonical_candidate_refs(
            list(review["root_cause_identity"]["reconciled_stage1_candidates"])
        )
        for candidate_ref in selection:
            review_id = str(candidate_ref["review_ref"]["record_id"])
            stage1_review = stage1_by_id.get(review_id)
            if stage1_review is None:
                raise RootCauseReconciliationError(
                    "A Stage-2 candidate reference does not resolve to the frozen Stage-1 panel."
                )
            if candidate_ref != root_cause_candidate_ref(stage1_review):
                raise RootCauseReconciliationError(
                    "A Stage-2 candidate reference does not match exact Stage-1 content."
                )
        selected_providers = {
            _provider(stage1_by_id[str(item["review_ref"]["record_id"])]) for item in selection
        }
        if selected_providers != stage1_providers:
            raise RootCauseReconciliationError(
                "A Stage-2 candidate set must include every required provider family."
            )
        selections.append(selection)
    candidate_refs = selections[0]
    if any(selection != candidate_refs for selection in selections[1:]):
        raise RootCauseReconciliationError(
            "Fresh Stage-2 providers did not select the identical Stage-1 candidate set."
        )
    return next(iter(case_ids)), next(iter(issue_classes)), candidate_refs


def _provider(review: dict[str, Any]) -> str:
    return str(review["reviewer_agent"]["provider"])


def _canonical_objects(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_digest = {semantic_digest(value): deepcopy(value) for value in values}
    return [by_digest[digest] for digest in sorted(by_digest)]


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RootCauseReconciliationError(
            f"Invalid root-cause reconciliation timestamp {value!r}."
        ) from error
    if parsed.tzinfo is None:
        raise RootCauseReconciliationError(
            "Root-cause reconciliation timestamps must include an offset."
        )
    return parsed
