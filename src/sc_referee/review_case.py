from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from sc_referee.core.ids import canonical_json, semantic_digest

ReviewGateState = Literal["established", "refuted", "unknown", "not_applicable"]
ReviewOutputCeiling = Literal["question_only", "evaluation_candidate", "production_finding"]


class ReviewCaseError(ValueError):
    """Raised when a normalized scientific review case is incomplete or noncanonical."""


@dataclass(frozen=True, order=True)
class ReviewGate:
    gate_id: str
    state: ReviewGateState
    evidence_ids: tuple[str, ...]
    basis: str

    def __post_init__(self) -> None:
        if not self.gate_id or not self.basis:
            raise ReviewCaseError("review gate identity and basis must not be empty")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ReviewCaseError("review gate evidence identities must be unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "state": self.state,
            "evidence_ids": list(self.evidence_ids),
            "basis": self.basis,
        }


@dataclass(frozen=True)
class ReviewCase:
    """Small internal protocol joining authority, evidence, scope, and finite gates."""

    case_family: str
    case_version: str
    target_ref: dict[str, str]
    requirement: object
    observed_operand: object
    comparison_form: str
    analysis_binding: dict[str, Any]
    evidence_planes: tuple[str, ...]
    applicability_gates: tuple[ReviewGate, ...]
    counterevidence_gates: tuple[ReviewGate, ...]
    affected_descendant_refs: tuple[dict[str, str], ...]
    unresolved_dimensions: tuple[str, ...]
    unsupported_constructs: tuple[str, ...]
    output_ceiling: ReviewOutputCeiling

    def __post_init__(self) -> None:
        for value, label in (
            (self.case_family, "case_family"),
            (self.case_version, "case_version"),
            (self.comparison_form, "comparison_form"),
        ):
            if not value:
                raise ReviewCaseError(f"{label} must not be empty")
        _record_ref(self.target_ref, "target_ref")
        if not self.evidence_planes or len(self.evidence_planes) != len(set(self.evidence_planes)):
            raise ReviewCaseError("review case evidence planes must be nonempty and unique")
        if not self.applicability_gates or not self.counterevidence_gates:
            raise ReviewCaseError("review case finite gate sets must not be empty")
        gate_ids = [
            *(gate.gate_id for gate in self.applicability_gates),
            *(gate.gate_id for gate in self.counterevidence_gates),
        ]
        if len(gate_ids) != len(set(gate_ids)):
            raise ReviewCaseError("review case gate identities must be unique")
        for ref in self.affected_descendant_refs:
            _record_ref(ref, "affected descendant ref")
        for values, label in (
            (self.unresolved_dimensions, "unresolved dimensions"),
            (self.unsupported_constructs, "unsupported constructs"),
        ):
            if len(values) != len(set(values)):
                raise ReviewCaseError(f"review case {label} must be unique")
        # Reject values that cannot participate in deterministic canonical replay.
        canonical_json(self.to_dict())

    @property
    def review_case_digest(self) -> str:
        return semantic_digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_family": self.case_family,
            "case_version": self.case_version,
            "target_ref": copy.deepcopy(self.target_ref),
            "requirement": copy.deepcopy(self.requirement),
            "observed_operand": copy.deepcopy(self.observed_operand),
            "comparison_form": self.comparison_form,
            "analysis_binding": copy.deepcopy(self.analysis_binding),
            "evidence_planes": sorted(self.evidence_planes),
            "applicability_gates": [gate.to_dict() for gate in sorted(self.applicability_gates)],
            "counterevidence_gates": [
                gate.to_dict() for gate in sorted(self.counterevidence_gates)
            ],
            "affected_descendant_refs": sorted(
                (copy.deepcopy(item) for item in self.affected_descendant_refs),
                key=canonical_json,
            ),
            "unresolved_dimensions": sorted(self.unresolved_dimensions),
            "unsupported_constructs": sorted(self.unsupported_constructs),
            "output_ceiling": self.output_ceiling,
        }


def review_gates_from_counterevidence(
    executions: Sequence[Mapping[str, Any]],
) -> tuple[tuple[ReviewGate, ...], tuple[ReviewGate, ...]]:
    """Normalize the fixed five applicability and five counterevidence checks."""

    if len(executions) != 10:
        raise ReviewCaseError("analysis-method ReviewCase requires exactly ten finite checks")
    gates: list[ReviewGate] = []
    for execution in executions:
        check_id = execution.get("check_id")
        outcome = execution.get("outcome")
        notes = execution.get("notes")
        evidence_ids = execution.get("evidence_ids", [])
        if (
            not isinstance(check_id, str)
            or not isinstance(outcome, str)
            or not isinstance(notes, str)
            or not isinstance(evidence_ids, Sequence)
            or isinstance(evidence_ids, (str, bytes))
            or not all(isinstance(item, str) for item in evidence_ids)
        ):
            raise ReviewCaseError("analysis-method finite check is malformed")
        state: ReviewGateState = (
            "established"
            if outcome == "no_counterevidence"
            else "not_applicable"
            if outcome == "not_applicable"
            else "refuted"
            if outcome == "counterevidence_found"
            else "unknown"
        )
        gates.append(ReviewGate(check_id, state, tuple(evidence_ids), notes))
    return tuple(gates[:5]), tuple(gates[5:])


def _record_ref(value: Mapping[str, Any], label: str) -> None:
    if not isinstance(value.get("record_type"), str) or not isinstance(value.get("record_id"), str):
        raise ReviewCaseError(f"review case {label} must be one typed record reference")
