from __future__ import annotations

from copy import deepcopy
from typing import Any

from sc_referee.core.ids import semantic_digest, stable_id

REVIEW_LOCAL_IDENTITY_PROFILE = "review-local-root-cause-v1"
ADJUDICATED_IDENTITY_PROFILE = "cross-review-candidate-set-v1"


def root_cause_candidate_payload(review: dict[str, Any]) -> dict[str, Any]:
    """Return the closed public payload that identifies one review-local candidate."""

    return {
        "case_id": review.get("case_id"),
        "review_id": review.get("review_id"),
        "issue_class": review.get("issue_class"),
        "bounded_statement": review.get("bounded_statement"),
        "root_cause": review.get("root_cause"),
        "evidence": review.get("evidence"),
        "affected_record_refs": review.get("affected_record_refs"),
        "scope": review.get("scope"),
    }


def root_cause_candidate_id(review: dict[str, Any]) -> str:
    """Derive one review-local ID without asserting cross-review equivalence."""

    return stable_id(
        "root-cause-candidate",
        str(review.get("case_id")),
        str(review.get("review_id")),
        semantic_digest(root_cause_candidate_payload(review)),
    )


def root_cause_candidate_ref(review: dict[str, Any]) -> dict[str, Any]:
    """Build the typed reference for one exact review-local candidate."""

    return {
        "review_ref": {
            "record_type": "agent_review",
            "record_id": review.get("review_id"),
        },
        "candidate_root_cause_id": root_cause_candidate_id(review),
    }


def canonical_candidate_refs(refs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize a candidate set into the order used by canonical public identity."""

    return sorted(
        deepcopy(refs),
        key=lambda item: (
            str(item.get("review_ref", {}).get("record_id")),
            str(item.get("candidate_root_cause_id")),
        ),
    )


def adjudicated_root_cause_id(
    case_id: str,
    issue_class: str,
    stage1_candidate_refs: list[dict[str, Any]],
) -> str:
    """Derive the prose-independent ID for one adjudicated candidate set."""

    return stable_id(
        "adjudicated-root-cause",
        case_id,
        ADJUDICATED_IDENTITY_PROFILE,
        issue_class,
        semantic_digest(canonical_candidate_refs(stage1_candidate_refs)),
    )
