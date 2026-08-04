from __future__ import annotations

from dataclasses import replace

import pytest

from sc_referee.core.ids import semantic_digest
from sc_referee.relation_case import (
    RelationCase,
    RelationCaseError,
    RelationObservation,
    evaluate_closed_relation,
)
from sc_referee.review_case import ReviewGate
from sc_referee.scientific_checks.core import (
    METHOD_CONFLICT_COUNTEREVIDENCE_PREDICATES,
    CanonicalOperand,
    MethodConflictBinding,
    RecordRef,
    ScopeJoinEdge,
)


def _binding(
    comparison_form: str = "value_equals",
    *,
    forbidden_members: tuple[str, ...] = (),
    two_planes: bool = True,
) -> MethodConflictBinding:
    kind = {
        "value_equals": "canonical_scalar",
        "set_relation": "unique_string_array",
        "step_precedes": "ordered_step_names",
    }[comparison_form]
    planes = ("reported_text", "static_source") if two_planes else ("static_source",)
    roles = ("observed", "reported") if two_planes else ("observed",)
    return MethodConflictBinding(
        binding_id="binding:opaque-relation",
        check_id="check:opaque-relation",
        check_version="1.0.0",
        check_manifest_digest="sha256:" + "a" * 64,
        detector_id="detector:closed-relation",
        detector_version="1.0.0",
        detector_manifest_digest="sha256:" + "b" * 64,
        dimension="measurement_model",
        comparison_form=comparison_form,
        operand_kind=kind,  # type: ignore[arg-type]
        required_evidence_planes=planes,  # type: ignore[arg-type]
        required_semantic_roles=("input", "output"),
        required_assertion_roles=roles,
        counterevidence_predicates=METHOD_CONFLICT_COUNTEREVIDENCE_PREDICATES,
        forbidden_members=forbidden_members,
    )


def _gates() -> tuple[tuple[ReviewGate, ...], tuple[ReviewGate, ...]]:
    gates = tuple(
        ReviewGate(
            gate_id=f"gate:{index}",
            state="established",
            evidence_ids=(f"evidence:{index}",),
            basis="The finite gate completed.",
        )
        for index in range(10)
    )
    return gates[:5], gates[5:]


def _case(
    *,
    binding: MethodConflictBinding | None = None,
    requirement: CanonicalOperand | None = None,
    observed: CanonicalOperand | None = None,
    reverse_planes: bool = False,
) -> RelationCase:
    selected_binding = binding or _binding()
    required = requirement or CanonicalOperand.scalar("option-a")
    observed_operand = observed or CanonicalOperand.scalar("option-a")
    observations = tuple(
        RelationObservation(
            evidence_plane=plane,
            operand=observed_operand,
            evidence_ids=(f"evidence:{plane}",),
        )
        for plane in selected_binding.required_evidence_planes
    )
    if reverse_planes:
        observations = tuple(reversed(observations))
    applicability, counterevidence = _gates()
    target = RecordRef("publication_surface", "surface:one")
    artifact = RecordRef("artifact", "artifact:one")
    return RelationCase(
        target_ref=target,
        contract_ref=RecordRef("scientific_contract", "contract:one"),
        binding=selected_binding,
        requirement=required,
        observations=observations,
        scope_join_path=(ScopeJoinEdge(artifact, "selected_by_surface", target),),
        applicability_gates=applicability,
        counterevidence_gates=counterevidence,
        affected_descendant_refs=(),
        unresolved_dimensions=(),
        unsupported_constructs=(),
        output_ceiling="evaluation_candidate",
    )


def test_relation_case_is_canonical_replay_stable_and_projects_to_review_case() -> None:
    case = _case()
    reordered = _case(reverse_planes=True)

    assert case.relation_case_digest == semantic_digest(case.to_dict())
    assert case.relation_case_digest == reordered.relation_case_digest
    review = case.to_review_case()
    assert review.requirement == {"kind": "canonical_scalar", "value": "option-a"}
    assert review.observed_operand == review.requirement
    assert review.case_family == "analysis_method_requirement_consistency"
    assert review.analysis_binding["binding_digest"] == case.binding.binding_digest
    assert review.analysis_binding["contract_id"] == "contract:one"
    assert review.analysis_binding["scope_join_digest"] == case.scope_join_digest


def test_relation_case_rejects_incomplete_disagreeing_or_wrong_kind_planes() -> None:
    case = _case()
    with pytest.raises(RelationCaseError, match="every binding-required plane"):
        RelationCase(**{**case.__dict__, "observations": case.observations[:1]})

    disagreement = replace(
        case.observations[1],
        operand=CanonicalOperand.scalar("option-b"),
    )
    with pytest.raises(RelationCaseError, match="disagree"):
        RelationCase(**{**case.__dict__, "observations": (case.observations[0], disagreement)})

    wrong_kind = replace(
        case.observations[1],
        operand=CanonicalOperand.string_set(("option-a",)),
    )
    with pytest.raises(RelationCaseError, match="kind"):
        RelationCase(**{**case.__dict__, "observations": (case.observations[0], wrong_kind)})


def test_value_equals_reports_only_exact_compatibility_or_conflict() -> None:
    compatible = evaluate_closed_relation(_case())
    conflict = evaluate_closed_relation(_case(observed=CanonicalOperand.scalar("option-b")))

    assert compatible.outcome == "compatible"
    assert compatible.details == {"values_equal": True}
    assert conflict.outcome == "conflict"
    assert conflict.details == {"values_equal": False}
    assert compatible.evaluation_digest == semantic_digest(compatible.to_dict())


def test_set_relation_requires_all_members_and_rejects_forbidden_members() -> None:
    binding = _binding("set_relation", forbidden_members=("blocked",), two_planes=False)
    compatible = evaluate_closed_relation(
        _case(
            binding=binding,
            requirement=CanonicalOperand.string_set(("required",)),
            observed=CanonicalOperand.string_set(("extra", "required")),
        )
    )
    missing = evaluate_closed_relation(
        _case(
            binding=binding,
            requirement=CanonicalOperand.string_set(("required",)),
            observed=CanonicalOperand.string_set(("extra",)),
        )
    )
    forbidden = evaluate_closed_relation(
        _case(
            binding=binding,
            requirement=CanonicalOperand.string_set(("required",)),
            observed=CanonicalOperand.string_set(("blocked", "required")),
        )
    )

    assert compatible.outcome == "compatible"
    assert missing.outcome == forbidden.outcome == "conflict"
    assert missing.details["missing_required_members"] == ["required"]
    assert forbidden.details["present_forbidden_members"] == ["blocked"]


def test_set_relation_abstains_on_a_contradictory_obligation() -> None:
    result = evaluate_closed_relation(
        _case(
            binding=_binding("set_relation", forbidden_members=("same",), two_planes=False),
            requirement=CanonicalOperand.string_set(("same",)),
            observed=CanonicalOperand.string_set(("same",)),
        )
    )

    assert result.outcome == "abstained"
    assert result.details == {"contradictory_members": ["same"]}


def test_step_precedes_distinguishes_order_from_missing_semantics() -> None:
    binding = _binding("step_precedes", two_planes=False)
    requirement = CanonicalOperand.ordered_steps(("earlier", "later"))
    compatible = evaluate_closed_relation(
        _case(
            binding=binding,
            requirement=requirement,
            observed=CanonicalOperand.ordered_steps(("earlier", "middle", "later")),
        )
    )
    reversed_order = evaluate_closed_relation(
        _case(
            binding=binding,
            requirement=requirement,
            observed=CanonicalOperand.ordered_steps(("later", "earlier")),
        )
    )
    missing = evaluate_closed_relation(
        _case(
            binding=binding,
            requirement=requirement,
            observed=CanonicalOperand.ordered_steps(("earlier", "other")),
        )
    )

    assert compatible.outcome == "compatible"
    assert reversed_order.outcome == "conflict"
    assert missing.outcome == "abstained"
    assert missing.details["missing_steps"] == ["later"]


def test_unknown_gate_or_opaque_semantics_forces_abstention() -> None:
    case = _case()
    gates = list(case.applicability_gates)
    gates[2] = replace(gates[2], state="unknown")
    gated = RelationCase(**{**case.__dict__, "applicability_gates": tuple(gates)})
    opaque = RelationCase(**{**case.__dict__, "unsupported_constructs": ("computed dispatch",)})

    assert evaluate_closed_relation(gated).outcome == "abstained"
    assert evaluate_closed_relation(opaque).outcome == "abstained"
    assert "gate gate:2 is unknown" in evaluate_closed_relation(gated).gaps


def test_scope_gate_count_and_output_ceiling_fail_closed() -> None:
    case = _case()
    wrong_target = RecordRef("publication_surface", "surface:other")
    with pytest.raises(RelationCaseError, match="does not end"):
        RelationCase(**{**case.__dict__, "target_ref": wrong_target})
    with pytest.raises(RelationCaseError, match="five applicability"):
        RelationCase(**{**case.__dict__, "applicability_gates": case.applicability_gates[:-1]})
    with pytest.raises(RelationCaseError, match="output ceiling"):
        RelationCase(**{**case.__dict__, "output_ceiling": "production_finding"})


def test_step_precedes_rejects_a_nonbinary_requirement() -> None:
    binding = _binding("step_precedes", two_planes=False)
    with pytest.raises(RelationCaseError, match="exactly two"):
        _case(
            binding=binding,
            requirement=CanonicalOperand.ordered_steps(("first", "second", "third")),
            observed=CanonicalOperand.ordered_steps(("first", "second", "third")),
        )
