from __future__ import annotations

from copy import deepcopy
from typing import Any

from sc_referee.core.ids import semantic_digest, stable_id


def evaluation_candidate_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    """Return the closed semantic payload identifying one evaluation-only candidate."""

    return {
        "semantic_lock_digest": candidate.get("semantic_lock_digest"),
        "detector_id": candidate.get("detector_id"),
        "detector_version": candidate.get("detector_version"),
        "detector_manifest_digest": candidate.get("detector_manifest_digest"),
        "source_detector_result_ref": deepcopy(candidate.get("source_detector_result_ref")),
        "source_detector_result_digest": candidate.get("source_detector_result_digest"),
        "title": candidate.get("title"),
        "bounded_statement": candidate.get("bounded_statement"),
        "issue_class": candidate.get("issue_class"),
        "root_locator": deepcopy(candidate.get("root_locator")),
        "subject_refs": deepcopy(candidate.get("subject_refs")),
        "affected_record_refs": deepcopy(candidate.get("affected_record_refs")),
        "evidence": deepcopy(candidate.get("evidence")),
        "admission_checks": deepcopy(candidate.get("admission_checks")),
    }


def evaluation_candidate_id(candidate: dict[str, Any]) -> str:
    """Derive a stable identity without granting production Finding authority."""

    return stable_id(
        "detector-evaluation-candidate",
        str(candidate.get("case_id")),
        str(candidate.get("fixture_ref", {}).get("record_id")),
        str(candidate.get("scientific_label_freeze_digest")),
        str(candidate.get("audit_bundle_digest")),
        semantic_digest(evaluation_candidate_payload(candidate)),
    )
