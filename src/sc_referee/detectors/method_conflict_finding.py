from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from sc_referee.core.ids import stable_id
from sc_referee.records.observed import controller_provenance
from sc_referee.scientific_checks.core import MethodConflictBinding
from sc_referee.version import SCHEMA_VERSION


class MethodConflictFindingDraftError(ValueError):
    """Raised when an evaluation result cannot support one bounded Finding draft."""


def draft_method_conflict_finding(
    result: Mapping[str, Any], binding: MethodConflictBinding
) -> dict[str, Any]:
    """Build the authority-neutral draft consumed only after qualification applies."""

    candidate = result.get("candidate")
    applicability = result.get("applicability")
    coverage = result.get("coverage")
    targets = result.get("target_refs")
    evidence = result.get("evidence")
    extensions = result.get("extensions")
    if (
        result.get("record_type") != "detector_result"
        or result.get("detector_id") != binding.detector_id
        or result.get("detector_version") != binding.detector_version
        or result.get("state") not in {"evaluation_finding_candidate", "finding_candidate"}
        or not isinstance(candidate, Mapping)
        or candidate.get("assessment_type") != "finding"
        or not isinstance(applicability, Mapping)
        or applicability.get("status") != "applicable"
        or not isinstance(coverage, Mapping)
        or coverage.get("status") != "covered"
        or not isinstance(targets, list)
        or len(targets) != 1
        or not isinstance(targets[0], Mapping)
        or targets[0].get("record_type") != "publication_surface"
        or not isinstance(evidence, list)
        or not evidence
        or not isinstance(extensions, Mapping)
        or not isinstance(extensions.get("x-review-case-digest"), str)
    ):
        raise MethodConflictFindingDraftError(
            "detector result is outside the complete method-conflict draft envelope"
        )
    result_id = result.get("result_id")
    run_id = result.get("audit_run_id")
    created_at = result.get("evaluated_at")
    title = candidate.get("title")
    statement = candidate.get("bounded_statement")
    target = deepcopy(dict(targets[0]))
    target_id = target.get("record_id")
    if not all(
        isinstance(value, str) and value
        for value in (result_id, run_id, created_at, title, statement, target_id)
    ):
        raise MethodConflictFindingDraftError("detector result lacks stable Finding identities")
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "finding",
        "finding_id": stable_id(
            "finding-analysis-method-conflict",
            str(run_id),
            str(result_id),
            binding.binding_digest,
            str(extensions["x-review-case-digest"]),
        ),
        "audit_run_id": run_id,
        "grouping_key": f"{binding.detector_id}|{target_id}|{binding.dimension}",
        "issue_class": "x-review-scoped-analysis-method-requirement-mismatch",
        "title": title,
        "summary": statement,
        "demonstration_status": "demonstrated",
        "severity": {
            "level": "moderate",
            "rationale": (
                "The selected analysis declaration conflicts with one exact pre-authorized "
                "review requirement; numerical and broader scientific consequences were not "
                "established."
            ),
        },
        "publication_materiality": {
            "state": "assessed",
            "level": "local",
            "rationale": (
                "The demonstrated conflict is localized to the exact selected publication "
                "surface and is not projected to other claims or analyses."
            ),
            "publication_surface_ids": [target_id],
        },
        "root_cause": {
            "root_ref": target,
            "violated_semantic_dimension": binding.dimension,
            "explanation": (
                "The binding-required observed operand and the exact pre-analysis human "
                "requirement differ under the registered closed comparison relation."
            ),
        },
        "subject_refs": [target],
        "affected_descendants": [],
        "evidence": deepcopy(evidence),
        "logical_basis": (
            "One verified pre-analysis requirement and one binding-complete selected-analysis "
            "operand conflict after every finite applicability and counterevidence check "
            "completed."
        ),
        "detector_result_ids": [result_id],
        "coverage_limitations": [
            "Static evidence does not establish that project code executed.",
            "The Finding does not establish numerical causality, bias direction, universal "
            "scientific correctness, or effects outside the selected analysis.",
        ],
        "next_action": (
            "Align the selected analysis with the governing requirement or document an "
            "authorized amendment and re-audit."
        ),
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_analysis_method_finding_draft_v1", str(created_at)
        ),
        "extensions": {
            "x-method-conflict-binding-id": binding.binding_id,
            "x-method-conflict-binding-digest": binding.binding_digest,
            "x-review-case-digest": extensions["x-review-case-digest"],
        },
    }
