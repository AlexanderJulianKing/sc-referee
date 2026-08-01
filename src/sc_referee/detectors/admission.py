from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True)
class AdmissionContext:
    """Controller-verified inputs that are outside a detector result record."""

    finding_draft: Mapping[str, Any]
    source_references_resolved: bool
    detector_qualification_applies: bool
    wording_constraints_satisfied: bool
    expected_deterministic_input_digest: str
    required_counterevidence_check_ids: tuple[str, ...]
    non_inferences: tuple[str, ...]


def admit_finding(result: Mapping[str, Any], context: AdmissionContext) -> dict[str, Any] | None:
    """Admit a demonstrated Finding only when every conservative gate passes."""

    if (
        result.get("record_type") != "detector_result"
        or result.get("state") != "finding_candidate"
        or result.get("detector_maturity") not in {"validated", "publication_grade"}
        or not context.detector_qualification_applies
    ):
        return None
    admission = evaluate_non_maturity_finding_admission(result, context)
    if admission is None:
        return None

    finding = deepcopy(dict(context.finding_draft))
    finding["admission"] = {
        **admission,
        "detector_maturity": result["detector_maturity"],
    }
    return finding


def evaluate_non_maturity_finding_admission(
    result: Mapping[str, Any], context: AdmissionContext
) -> dict[str, Any] | None:
    """Return shared deterministic Finding checks without a maturity/qualification grant."""

    candidate = result.get("candidate")
    applicability = result.get("applicability")
    coverage = result.get("coverage")
    if (
        result.get("record_type") != "detector_result"
        or not isinstance(candidate, Mapping)
        or candidate.get("assessment_type") != "finding"
        or not isinstance(applicability, Mapping)
        or applicability.get("status") != "applicable"
        or bool(applicability.get("unsupported_constructs", []))
        or not isinstance(coverage, Mapping)
        or coverage.get("status") != "covered"
        or bool(coverage.get("gaps", []))
        or bool(result.get("unavailable_evidence", []))
    ):
        return None

    material_premise_ids = candidate.get("material_premise_ids")
    unresolved_premise_ids = candidate.get("unresolved_material_premise_ids")
    premise_evaluations = result.get("premise_evaluations")
    if (
        not _is_unique_string_list(material_premise_ids, nonempty=True)
        or not _is_unique_string_list(unresolved_premise_ids, nonempty=False)
        or unresolved_premise_ids
        or not isinstance(premise_evaluations, list)
    ):
        return None
    material_premise_ids = cast(list[str], material_premise_ids)
    unresolved_premise_ids = cast(list[str], unresolved_premise_ids)

    evaluated_material_ids: list[str] = []
    for premise in premise_evaluations:
        if not isinstance(premise, Mapping) or premise.get("material") is not True:
            continue
        premise_id = premise.get("premise_id")
        if (
            not isinstance(premise_id, str)
            or premise.get("state") != "established"
            or not _is_unique_string_list(premise.get("evidence_ids"), nonempty=True)
        ):
            return None
        evaluated_material_ids.append(premise_id)
    if set(evaluated_material_ids) != set(material_premise_ids):
        return None

    if not _counterevidence_is_complete(
        result.get("counterevidence_execution"), context.required_counterevidence_check_ids
    ):
        return None

    draft = context.finding_draft
    result_id = result.get("result_id")
    detector_result_ids = draft.get("detector_result_ids")
    if (
        draft.get("record_type") != "finding"
        or draft.get("demonstration_status") != "demonstrated"
        or "admission" in draft
        or not isinstance(result_id, str)
        or not isinstance(detector_result_ids, list)
        or result_id not in detector_result_ids
        or draft.get("audit_run_id") != result.get("audit_run_id")
        or draft.get("title") != candidate.get("title")
        or draft.get("summary") != candidate.get("bounded_statement")
        or draft.get("evidence") != result.get("evidence")
        or not context.wording_constraints_satisfied
        or not context.source_references_resolved
        or not context.non_inferences
        or result.get("deterministic_input_digest") != context.expected_deterministic_input_digest
    ):
        return None

    return {
        "direct_entailment": True,
        "no_reversing_unknown": True,
        "exact_detector_applicability": True,
        "counterevidence_protocol_complete": True,
        "bounded_wording": True,
        "deterministic_replay": True,
        "source_references_resolved": True,
        "material_premise_ids": list(material_premise_ids),
        "unresolved_material_premise_ids": [],
        "non_inferences": list(context.non_inferences),
    }


def _counterevidence_is_complete(executions: Any, required_check_ids: tuple[str, ...]) -> bool:
    if not required_check_ids or len(set(required_check_ids)) != len(required_check_ids):
        return False
    if not isinstance(executions, list):
        return False

    observed_ids: list[str] = []
    for execution in executions:
        if not isinstance(execution, Mapping):
            return False
        check_id = execution.get("check_id")
        status = execution.get("status")
        outcome = execution.get("outcome")
        if not isinstance(check_id, str):
            return False
        observed_ids.append(check_id)
        if (status, outcome) not in {
            ("completed", "no_counterevidence"),
            ("not_applicable", "not_applicable"),
        }:
            return False
    return len(set(observed_ids)) == len(observed_ids) and set(observed_ids) == set(
        required_check_ids
    )


def _is_unique_string_list(value: Any, *, nonempty: bool) -> bool:
    if not isinstance(value, list) or (nonempty and not value):
        return False
    return all(isinstance(item, str) and item for item in value) and len(set(value)) == len(value)
