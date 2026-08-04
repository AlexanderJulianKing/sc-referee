from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Literal, cast

from sc_referee.core.ids import canonical_json, semantic_digest
from sc_referee.review_case import ReviewCase, ReviewGate, ReviewOutputCeiling
from sc_referee.scientific_checks.core import (
    CanonicalOperand,
    EvidencePlane,
    MethodConflictBinding,
    RecordRef,
    ScopeJoinEdge,
)

RelationOutcome = Literal["compatible", "conflict", "abstained"]


class RelationCaseError(ValueError):
    """Raised when a closed relation case cannot support deterministic evaluation."""


@dataclass(frozen=True)
class RelationObservation:
    """One adapter-normalized operand from one binding-required evidence plane."""

    evidence_plane: EvidencePlane
    operand: CanonicalOperand
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.evidence_ids or any(not value for value in self.evidence_ids):
            raise RelationCaseError("relation observation evidence IDs must be non-empty")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise RelationCaseError("relation observation evidence IDs must be unique")
        canonical_json(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_plane": self.evidence_plane,
            "operand": self.operand.to_dict(),
            "evidence_ids": sorted(self.evidence_ids),
        }


@dataclass(frozen=True)
class RelationCase:
    """Domain-neutral, closed comparison between one requirement and workflow evidence."""

    target_ref: RecordRef
    contract_ref: RecordRef
    binding: MethodConflictBinding
    requirement: CanonicalOperand
    observations: tuple[RelationObservation, ...]
    scope_join_path: tuple[ScopeJoinEdge, ...]
    applicability_gates: tuple[ReviewGate, ...]
    counterevidence_gates: tuple[ReviewGate, ...]
    affected_descendant_refs: tuple[RecordRef, ...]
    unresolved_dimensions: tuple[str, ...]
    unsupported_constructs: tuple[str, ...]
    output_ceiling: ReviewOutputCeiling

    def __post_init__(self) -> None:
        if self.contract_ref.record_type != "scientific_contract":
            raise RelationCaseError(
                "relation case contract ref must identify a scientific contract"
            )
        if self.requirement.kind != self.binding.operand_kind:
            raise RelationCaseError("relation requirement kind does not match its binding")
        _validate_observations(self.binding, self.observations)
        _validate_scope_path(self.target_ref, self.scope_join_path)
        _validate_gates(self.applicability_gates, self.counterevidence_gates)
        _validate_unique_text(self.unresolved_dimensions, "unresolved dimensions")
        _validate_unique_text(self.unsupported_constructs, "unsupported constructs")
        if self.output_ceiling == "production_finding" and not (
            self.binding.production_finding_permitted
        ):
            raise RelationCaseError("relation case exceeds its binding output ceiling")
        if (
            self.binding.comparison_form == "step_precedes"
            and len(_operand_strings(self.requirement)) != 2
        ):
            raise RelationCaseError("step_precedes requires exactly two required steps")
        canonical_json(self.to_dict())

    @property
    def observed_operand(self) -> CanonicalOperand:
        # Construction proves non-emptiness and exact plane agreement.
        return self.observations[0].operand

    @property
    def scope_join_digest(self) -> str:
        return semantic_digest([edge.to_dict() for edge in self.scope_join_path])

    @property
    def relation_case_digest(self) -> str:
        return semantic_digest(self.to_dict())

    def to_review_case(self) -> ReviewCase:
        """Project into the existing shared ReviewCase protocol without changing its meaning."""

        return ReviewCase(
            case_family="analysis_method_requirement_consistency",
            case_version="1.0.0",
            target_ref=self.target_ref.to_dict(),
            requirement=self.requirement.to_dict(),
            observed_operand=self.observed_operand.to_dict(),
            comparison_form=self.binding.comparison_form,
            analysis_binding={
                "binding_id": self.binding.binding_id,
                "binding_digest": self.binding.binding_digest,
                "contract_id": self.contract_ref.record_id,
                "scientific_check_id": self.binding.check_id,
                "scope_join_path": [edge.to_dict() for edge in self.scope_join_path],
                "scope_join_digest": self.scope_join_digest,
            },
            evidence_planes=tuple(observation.evidence_plane for observation in self.observations),
            applicability_gates=self.applicability_gates,
            counterevidence_gates=self.counterevidence_gates,
            affected_descendant_refs=tuple(ref.to_dict() for ref in self.affected_descendant_refs),
            unresolved_dimensions=self.unresolved_dimensions,
            unsupported_constructs=self.unsupported_constructs,
            output_ceiling=self.output_ceiling,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_case_profile": "method_relation_case_v1",
            "target_ref": self.target_ref.to_dict(),
            "contract_ref": self.contract_ref.to_dict(),
            "binding": self.binding.to_dict(),
            "binding_digest": self.binding.binding_digest,
            "requirement": self.requirement.to_dict(),
            "observations": [
                observation.to_dict()
                for observation in sorted(self.observations, key=lambda item: item.evidence_plane)
            ],
            "scope_join_path": [edge.to_dict() for edge in self.scope_join_path],
            "scope_join_digest": self.scope_join_digest,
            "applicability_gates": [gate.to_dict() for gate in sorted(self.applicability_gates)],
            "counterevidence_gates": [
                gate.to_dict() for gate in sorted(self.counterevidence_gates)
            ],
            "affected_descendant_refs": sorted(
                (ref.to_dict() for ref in self.affected_descendant_refs), key=canonical_json
            ),
            "unresolved_dimensions": sorted(self.unresolved_dimensions),
            "unsupported_constructs": sorted(self.unsupported_constructs),
            "output_ceiling": self.output_ceiling,
        }


@dataclass(frozen=True)
class RelationEvaluation:
    outcome: RelationOutcome
    basis: str
    details: dict[str, Any]
    gaps: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.basis:
            raise RelationCaseError("relation evaluation basis must not be empty")
        if self.outcome == "abstained" and not self.gaps:
            raise RelationCaseError("an abstained relation evaluation must identify a gap")
        if self.outcome != "abstained" and self.gaps:
            raise RelationCaseError("a completed relation evaluation cannot contain gaps")
        _validate_unique_text(self.gaps, "evaluation gaps")
        canonical_json(self.to_dict())

    @property
    def evaluation_digest(self) -> str:
        return semantic_digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "basis": self.basis,
            "details": copy.deepcopy(self.details),
            "gaps": sorted(self.gaps),
        }


def evaluate_closed_relation(case: RelationCase) -> RelationEvaluation:
    """Evaluate only the binding's closed relation; unresolved meaning always abstains."""

    gaps = _case_gaps(case)
    if gaps:
        return RelationEvaluation(
            outcome="abstained",
            basis="The closed relation cannot be evaluated while material semantics are unresolved.",
            details={},
            gaps=gaps,
        )

    required = case.requirement
    observed = case.observed_operand
    if case.binding.comparison_form == "value_equals":
        equal = required.canonical_value == observed.canonical_value
        return RelationEvaluation(
            outcome="compatible" if equal else "conflict",
            basis=(
                "The exact canonical operands are equal."
                if equal
                else "The exact canonical operands differ."
            ),
            details={"values_equal": equal},
        )

    if case.binding.comparison_form == "set_relation":
        required_members = _operand_strings(required)
        observed_members = _operand_strings(observed)
        forbidden_members = case.binding.forbidden_members
        contradictory = sorted(set(required_members) & set(forbidden_members))
        if contradictory:
            gap = "The relation requires and forbids the same canonical member."
            return RelationEvaluation(
                outcome="abstained",
                basis=gap,
                details={"contradictory_members": contradictory},
                gaps=(gap,),
            )
        missing = sorted(set(required_members) - set(observed_members))
        present_forbidden = sorted(set(forbidden_members) & set(observed_members))
        compatible = not missing and not present_forbidden
        return RelationEvaluation(
            outcome="compatible" if compatible else "conflict",
            basis=(
                "Every required member is present and no forbidden member is present."
                if compatible
                else "A required member is missing or a forbidden member is present."
            ),
            details={
                "required_members": list(required_members),
                "forbidden_members": list(forbidden_members),
                "observed_members": list(observed_members),
                "missing_required_members": missing,
                "present_forbidden_members": present_forbidden,
            },
        )

    if case.binding.comparison_form == "step_precedes":
        required_steps = _operand_strings(required)
        observed_steps = _operand_strings(observed)
        earlier, later = required_steps
        missing_steps = tuple(step for step in required_steps if step not in observed_steps)
        if missing_steps:
            gap = "The observed sequence does not establish both required steps."
            return RelationEvaluation(
                outcome="abstained",
                basis=gap,
                details={
                    "required_steps": list(required_steps),
                    "observed_steps": list(observed_steps),
                    "missing_steps": list(missing_steps),
                },
                gaps=(gap,),
            )
        earlier_index = observed_steps.index(earlier)
        later_index = observed_steps.index(later)
        precedes = earlier_index < later_index
        return RelationEvaluation(
            outcome="compatible" if precedes else "conflict",
            basis=(
                "The exact observed sequence has the required order."
                if precedes
                else "The exact observed sequence reverses the required order."
            ),
            details={
                "earlier_step": earlier,
                "later_step": later,
                "observed_steps": list(observed_steps),
                "earlier_index": earlier_index,
                "later_index": later_index,
                "required_order_satisfied": precedes,
            },
        )

    # MethodConflictBinding currently prevents this, but preserve a local fail-closed boundary.
    gap = "The relation comparison form is unsupported."
    return RelationEvaluation(
        outcome="abstained",
        basis=gap,
        details={},
        gaps=(gap,),
    )


def _validate_observations(
    binding: MethodConflictBinding,
    observations: tuple[RelationObservation, ...],
) -> None:
    if not observations:
        raise RelationCaseError("relation case observations must not be empty")
    planes = tuple(observation.evidence_plane for observation in observations)
    if len(planes) != len(set(planes)):
        raise RelationCaseError("relation case evidence planes must be unique")
    if set(planes) != set(binding.required_evidence_planes):
        raise RelationCaseError("relation case does not contain every binding-required plane")
    if any(observation.operand.kind != binding.operand_kind for observation in observations):
        raise RelationCaseError("relation observation kind does not match its binding")
    operands = {observation.operand.canonical_value for observation in observations}
    if len(operands) != 1:
        raise RelationCaseError("relation case evidence planes disagree on the observed operand")


def _validate_scope_path(target_ref: RecordRef, path: tuple[ScopeJoinEdge, ...]) -> None:
    if not path:
        raise RelationCaseError("relation case scope path must not be empty")
    if any(path[index].target_ref != path[index + 1].source_ref for index in range(len(path) - 1)):
        raise RelationCaseError("relation case scope path is not contiguous")
    if path[-1].target_ref != target_ref:
        raise RelationCaseError("relation case scope path does not end at its target")


def _validate_gates(
    applicability: tuple[ReviewGate, ...], counterevidence: tuple[ReviewGate, ...]
) -> None:
    if len(applicability) != 5 or len(counterevidence) != 5:
        raise RelationCaseError(
            "relation case requires five applicability and five safeguard gates"
        )
    gate_ids = [
        *(gate.gate_id for gate in applicability),
        *(gate.gate_id for gate in counterevidence),
    ]
    if len(gate_ids) != len(set(gate_ids)):
        raise RelationCaseError("relation case gate identities must be unique")


def _validate_unique_text(values: tuple[str, ...], label: str) -> None:
    if len(values) != len(set(values)) or any(not value for value in values):
        raise RelationCaseError(f"relation case {label} must be unique non-empty text")


def _case_gaps(case: RelationCase) -> tuple[str, ...]:
    gaps = [
        *(f"unresolved dimension: {value}" for value in case.unresolved_dimensions),
        *(f"unsupported construct: {value}" for value in case.unsupported_constructs),
    ]
    for gate in (*case.applicability_gates, *case.counterevidence_gates):
        if gate.state not in {"established", "not_applicable"}:
            gaps.append(f"gate {gate.gate_id} is {gate.state}")
    return tuple(sorted(gaps))


def _operand_strings(operand: CanonicalOperand) -> tuple[str, ...]:
    value = operand.value
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RelationCaseError("closed collection operand is malformed")
    return tuple(cast(list[str], value))
