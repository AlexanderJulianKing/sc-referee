from __future__ import annotations

from copy import deepcopy

import pytest

from sc_referee.core.ids import semantic_digest
from sc_referee.review_case import (
    ReviewCase,
    ReviewCaseError,
    ReviewGate,
    review_gates_from_counterevidence,
)


def _checks() -> list[dict[str, object]]:
    return [
        {
            "check_id": f"check:gate-{index}",
            "status": "completed",
            "outcome": "no_counterevidence",
            "evidence_ids": [f"evidence:gate-{index}"],
            "notes": "The finite gate completed without a suppressor.",
        }
        for index in range(10)
    ]


def _case() -> ReviewCase:
    applicability, counterevidence = review_gates_from_counterevidence(_checks())
    return ReviewCase(
        case_family="analysis_method_requirement_consistency",
        case_version="1.0.0",
        target_ref={
            "record_type": "publication_surface",
            "record_id": "publication-surface:test",
        },
        requirement="repair_before_fit",
        observed_operand="use_supplied_values",
        comparison_form="value_equals",
        analysis_binding={
            "binding_id": "binding:test",
            "scope_join_digest": "sha256:" + "a" * 64,
        },
        evidence_planes=("reported_text", "static_source"),
        applicability_gates=applicability,
        counterevidence_gates=counterevidence,
        affected_descendant_refs=(),
        unresolved_dimensions=(),
        unsupported_constructs=(),
        output_ceiling="evaluation_candidate",
    )


def test_review_case_is_canonical_generic_and_replay_stable() -> None:
    case = _case()

    assert case.review_case_digest == semantic_digest(case.to_dict())
    assert case.review_case_digest == _case().review_case_digest
    assert len(case.applicability_gates) == len(case.counterevidence_gates) == 5
    projection = case.to_dict()
    assert projection["requirement"] == "repair_before_fit"
    assert projection["observed_operand"] == "use_supplied_values"
    assert not {"genebench", "task_id", "fixture_path", "answer_key"} & set(projection)


def test_review_case_rejects_duplicate_or_incomplete_finite_gates() -> None:
    with pytest.raises(ReviewCaseError, match="exactly ten"):
        review_gates_from_counterevidence(_checks()[:-1])

    case = _case()
    duplicated = deepcopy(case.applicability_gates)
    duplicated = (*duplicated[:-1], duplicated[0])
    with pytest.raises(ReviewCaseError, match="gate identities must be unique"):
        ReviewCase(
            **{
                **case.__dict__,
                "applicability_gates": duplicated,
            }
        )


def test_review_gate_marks_counterevidence_as_refuted() -> None:
    checks = _checks()
    checks[7]["outcome"] = "counterevidence_found"
    applicability, counterevidence = review_gates_from_counterevidence(checks)

    assert all(isinstance(item, ReviewGate) for item in applicability)
    assert counterevidence[2].state == "refuted"
