from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from sc_referee.core.ids import canonical_json, semantic_digest

EvidenceState = Literal["established", "refuted", "unknown", "unsupported"]
SafeguardState = Literal["present", "absent", "not_applicable", "unknown", "unsupported"]
DependenceOutcome = Literal[
    "evaluation_candidate",
    "covered_negative",
    "question",
    "unsupported",
]
DependenceOutputCeiling = Literal["question_only", "evaluation_candidate"]
_EVIDENCE_STATES = frozenset(("established", "refuted", "unknown", "unsupported"))
_SAFEGUARD_STATES = frozenset(("present", "absent", "not_applicable", "unknown", "unsupported"))
_OUTPUT_CEILINGS = frozenset(("question_only", "evaluation_candidate"))


class DependenceCaseError(ValueError):
    """Raised when a normalized dependence case is internally inconsistent."""


@dataclass(frozen=True, order=True)
class RecordRef:
    record_type: str
    record_id: str

    def __post_init__(self) -> None:
        if not _present(self.record_type) or not _present(self.record_id):
            raise DependenceCaseError("record references require nonempty type and identity")

    def to_dict(self) -> dict[str, str]:
        return {"record_type": self.record_type, "record_id": self.record_id}


@dataclass(frozen=True, order=True)
class Membership:
    observation_id: str
    independent_unit_id: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _present(self.observation_id) or not _present(self.independent_unit_id):
            raise DependenceCaseError("membership identities must not be empty")
        _unique_nonempty(self.evidence_ids, "membership evidence identities", allow_empty=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "independent_unit_id": self.independent_unit_id,
            "evidence_ids": sorted(self.evidence_ids),
        }


@dataclass(frozen=True, order=True)
class RegisteredSafeguard:
    safeguard_id: str
    description: str


SAFEGUARD_REGISTRY: tuple[RegisteredSafeguard, ...] = (
    RegisteredSafeguard(
        "safeguard:unit-level-aggregation",
        "Aggregation to one analyzed observation per independent unit before fitting or testing.",
    ),
    RegisteredSafeguard(
        "safeguard:grouped-random-effects",
        "A grouped random-effect structure bound to the governing independent unit.",
    ),
    RegisteredSafeguard(
        "safeguard:cluster-correlated-estimation",
        "A correlated estimator bound to the governing cluster operand.",
    ),
    RegisteredSafeguard(
        "safeguard:cluster-adjusted-uncertainty",
        "Cluster-adjusted uncertainty bound to the governing cluster operand.",
    ),
    RegisteredSafeguard(
        "safeguard:paired-or-blocked-procedure",
        "A paired or blocked procedure bound to the governing grouping operand.",
    ),
    RegisteredSafeguard(
        "safeguard:unit-level-resampling",
        "Permutation, bootstrap, or randomization performed at the independent-unit level.",
    ),
    RegisteredSafeguard(
        "safeguard:registered-dependence-aware-procedure",
        "A separately registered dependence-aware procedure with the governing grouping operand.",
    ),
)
SAFEGUARD_IDS: tuple[str, ...] = tuple(item.safeguard_id for item in SAFEGUARD_REGISTRY)
_SAFEGUARD_ID_SET = frozenset(SAFEGUARD_IDS)


@dataclass(frozen=True, order=True)
class SafeguardCheck:
    safeguard_id: str
    state: SafeguardState
    analysis_target_ref: RecordRef
    procedure_ref: RecordRef
    independent_unit_definition_id: str
    evidence_ids: tuple[str, ...]
    basis: str

    def __post_init__(self) -> None:
        if self.safeguard_id not in _SAFEGUARD_ID_SET:
            raise DependenceCaseError(f"unregistered safeguard identity: {self.safeguard_id}")
        if self.state not in _SAFEGUARD_STATES:
            raise DependenceCaseError(f"invalid safeguard state: {self.state}")
        if not _present(self.independent_unit_definition_id) or not _present(self.basis):
            raise DependenceCaseError("safeguard binding and basis must not be empty")
        _unique_nonempty(
            self.evidence_ids,
            "safeguard evidence identities",
            allow_empty=self.state in {"unknown", "unsupported"},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "safeguard_id": self.safeguard_id,
            "state": self.state,
            "analysis_target_ref": self.analysis_target_ref.to_dict(),
            "procedure_ref": self.procedure_ref.to_dict(),
            "independent_unit_definition_id": self.independent_unit_definition_id,
            "evidence_ids": sorted(self.evidence_ids),
            "basis": self.basis,
        }


@dataclass(frozen=True)
class DependenceCase:
    """Domain-neutral evidence needed for one bounded dependence decision."""

    case_id: str
    analyzed_observation_ids: tuple[str, ...]
    independent_unit_definition_id: str
    unit_definition_state: EvidenceState
    memberships: tuple[Membership, ...]
    membership_state: EvidenceState
    analysis_target_ref: RecordRef | None
    analysis_input_binding_state: EvidenceState
    separate_observation_entry_state: EvidenceState
    procedure_ref: RecordRef | None
    procedure_binding_state: EvidenceState
    row_independence_state: EvidenceState
    safeguard_checks: tuple[SafeguardCheck, ...]
    affected_target_ref: RecordRef | None
    affected_target_state: EvidenceState
    unresolved_dimensions: tuple[str, ...]
    unsupported_constructs: tuple[str, ...]
    output_ceiling: DependenceOutputCeiling

    def __post_init__(self) -> None:
        if not _present(self.case_id) or not _present(self.independent_unit_definition_id):
            raise DependenceCaseError(
                "case and independent-unit definition identities are required"
            )
        state_fields = (
            self.unit_definition_state,
            self.membership_state,
            self.analysis_input_binding_state,
            self.separate_observation_entry_state,
            self.procedure_binding_state,
            self.row_independence_state,
            self.affected_target_state,
        )
        invalid_states = sorted({state for state in state_fields if state not in _EVIDENCE_STATES})
        if invalid_states:
            raise DependenceCaseError(f"invalid evidence state(s): {', '.join(invalid_states)}")
        if self.output_ceiling not in _OUTPUT_CEILINGS:
            raise DependenceCaseError(f"invalid dependence output ceiling: {self.output_ceiling}")
        _unique_nonempty(
            self.analyzed_observation_ids,
            "analyzed observation identities",
            allow_empty=False,
        )
        _unique_nonempty(self.unresolved_dimensions, "unresolved dimensions", allow_empty=True)
        _unique_nonempty(self.unsupported_constructs, "unsupported constructs", allow_empty=True)
        membership_observations = tuple(item.observation_id for item in self.memberships)
        if len(membership_observations) != len(set(membership_observations)):
            raise DependenceCaseError("each analyzed observation may have only one membership")
        unknown_observations = set(membership_observations) - set(self.analyzed_observation_ids)
        if unknown_observations:
            raise DependenceCaseError("memberships may refer only to analyzed observations")
        if self.membership_state == "established" and set(membership_observations) != set(
            self.analyzed_observation_ids
        ):
            raise DependenceCaseError(
                "established membership evidence must cover every analyzed observation"
            )
        check_ids = tuple(item.safeguard_id for item in self.safeguard_checks)
        if len(check_ids) != len(set(check_ids)):
            raise DependenceCaseError("safeguard checks must have unique identities")
        for ref, state, label in (
            (self.analysis_target_ref, self.analysis_input_binding_state, "analysis target"),
            (self.procedure_ref, self.procedure_binding_state, "procedure"),
            (self.affected_target_ref, self.affected_target_state, "affected target"),
        ):
            if state in {"established", "refuted"} and ref is None:
                raise DependenceCaseError(f"{label} reference is required when its state is closed")
        canonical_json(self.to_dict())

    @property
    def case_digest(self) -> str:
        return semantic_digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_family": "dependence",
            "case_version": "1.0.0",
            "analyzed_observation_ids": sorted(self.analyzed_observation_ids),
            "independent_unit_definition_id": self.independent_unit_definition_id,
            "unit_definition_state": self.unit_definition_state,
            "memberships": [item.to_dict() for item in sorted(self.memberships)],
            "membership_state": self.membership_state,
            "analysis_target_ref": (
                self.analysis_target_ref.to_dict() if self.analysis_target_ref is not None else None
            ),
            "analysis_input_binding_state": self.analysis_input_binding_state,
            "separate_observation_entry_state": self.separate_observation_entry_state,
            "procedure_ref": self.procedure_ref.to_dict()
            if self.procedure_ref is not None
            else None,
            "procedure_binding_state": self.procedure_binding_state,
            "row_independence_state": self.row_independence_state,
            "safeguard_checks": [
                item.to_dict()
                for item in sorted(self.safeguard_checks, key=lambda check: check.safeguard_id)
            ],
            "affected_target_ref": (
                self.affected_target_ref.to_dict() if self.affected_target_ref is not None else None
            ),
            "affected_target_state": self.affected_target_state,
            "unresolved_dimensions": sorted(self.unresolved_dimensions),
            "unsupported_constructs": sorted(self.unsupported_constructs),
            "output_ceiling": self.output_ceiling,
        }


@dataclass(frozen=True)
class DependenceEvaluation:
    outcome: DependenceOutcome
    reason_code: str
    basis: str
    repeated_independent_unit_ids: tuple[str, ...]
    applicable_safeguard_ids: tuple[str, ...]
    unresolved_dimensions: tuple[str, ...]
    unsupported_constructs: tuple[str, ...]
    case_digest: str
    output_ceiling: DependenceOutputCeiling

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "reason_code": self.reason_code,
            "basis": self.basis,
            "repeated_independent_unit_ids": list(self.repeated_independent_unit_ids),
            "applicable_safeguard_ids": list(self.applicable_safeguard_ids),
            "unresolved_dimensions": list(self.unresolved_dimensions),
            "unsupported_constructs": list(self.unsupported_constructs),
            "case_digest": self.case_digest,
            "output_ceiling": self.output_ceiling,
        }


def evaluate_dependence_case(case: DependenceCase) -> DependenceEvaluation:
    """Evaluate one normalized case without execution, inference, or external state."""

    digest = case.case_digest
    unsupported = set(case.unsupported_constructs)
    state_by_dimension = {
        "independent_unit_definition": case.unit_definition_state,
        "membership_relation": case.membership_state,
        "analysis_input_binding": case.analysis_input_binding_state,
        "separate_observation_entry": case.separate_observation_entry_state,
        "procedure_binding": case.procedure_binding_state,
        "row_independence": case.row_independence_state,
        "affected_target": case.affected_target_state,
    }
    unsupported.update(
        dimension for dimension, state in state_by_dimension.items() if state == "unsupported"
    )
    if unsupported:
        return _evaluation(
            case,
            digest,
            "unsupported",
            "unsupported_evidence",
            "At least one required evidence path is outside the bounded evaluator.",
            unsupported=unsupported,
        )

    unresolved = set(case.unresolved_dimensions)
    unresolved.update(
        dimension for dimension, state in state_by_dimension.items() if state == "unknown"
    )
    if unresolved:
        return _evaluation(
            case,
            digest,
            "question",
            "unresolved_semantics",
            "Required unit, input, procedure, or target semantics remain unresolved.",
            unresolved=unresolved,
        )

    if case.unit_definition_state != "established" or case.membership_state != "established":
        return _evaluation(
            case,
            digest,
            "question",
            "unit_membership_not_established",
            "The independent-unit definition and complete membership relation are not established.",
            unresolved={"independent_unit_membership"},
        )

    repeated_units = _repeated_units(case.memberships)
    if not repeated_units:
        return _evaluation(
            case,
            digest,
            "covered_negative",
            "one_observation_per_independent_unit",
            "Every analyzed observation has a distinct independent-unit membership.",
        )

    if case.analysis_input_binding_state == "refuted":
        return _evaluation(
            case,
            digest,
            "covered_negative",
            "observations_not_bound_to_analysis",
            "The repeated observations are established not to be inputs to the bound analysis.",
            repeated=repeated_units,
        )
    if case.procedure_binding_state == "refuted":
        return _evaluation(
            case,
            digest,
            "covered_negative",
            "procedure_not_bound_to_analysis",
            "The inspected procedure is established not to be the procedure for the bound analysis.",
            repeated=repeated_units,
        )

    checks_by_id = {item.safeguard_id: item for item in case.safeguard_checks}
    missing_checks = _SAFEGUARD_ID_SET - checks_by_id.keys()
    if missing_checks:
        return _evaluation(
            case,
            digest,
            "question",
            "incomplete_safeguard_protocol",
            "The finite safeguard protocol did not complete every registered check.",
            repeated=repeated_units,
            unresolved={f"safeguard_check:{item}" for item in missing_checks},
        )

    check_unsupported = {
        f"safeguard_check:{item.safeguard_id}"
        for item in case.safeguard_checks
        if item.state == "unsupported"
    }
    if check_unsupported:
        return _evaluation(
            case,
            digest,
            "unsupported",
            "unsupported_safeguard_check",
            "At least one registered safeguard check could not inspect its bounded construct.",
            repeated=repeated_units,
            unsupported=check_unsupported,
        )
    check_unknown = {
        f"safeguard_check:{item.safeguard_id}"
        for item in case.safeguard_checks
        if item.state == "unknown"
    }
    if check_unknown:
        return _evaluation(
            case,
            digest,
            "question",
            "unresolved_safeguard_check",
            "At least one registered safeguard check remains unresolved.",
            repeated=repeated_units,
            unresolved=check_unknown,
        )

    assert case.analysis_target_ref is not None
    assert case.procedure_ref is not None
    binding_mismatches = {
        item.safeguard_id
        for item in case.safeguard_checks
        if item.analysis_target_ref != case.analysis_target_ref
        or item.procedure_ref != case.procedure_ref
        or item.independent_unit_definition_id != case.independent_unit_definition_id
    }
    if binding_mismatches:
        return _evaluation(
            case,
            digest,
            "question",
            "unresolved_safeguard_binding",
            "A safeguard check is not bound to the exact analysis, procedure, and unit definition.",
            repeated=repeated_units,
            unresolved={f"safeguard_binding:{item}" for item in binding_mismatches},
        )

    present_safeguards = tuple(
        sorted(item.safeguard_id for item in case.safeguard_checks if item.state == "present")
    )
    if present_safeguards:
        return _evaluation(
            case,
            digest,
            "covered_negative",
            "applicable_safeguard_present",
            "At least one registered dependence safeguard is present with exact operand bindings.",
            repeated=repeated_units,
            safeguards=present_safeguards,
        )

    if case.separate_observation_entry_state == "refuted":
        return _evaluation(
            case,
            digest,
            "covered_negative",
            "observations_not_entered_separately",
            "The repeated observations are established not to enter the analysis separately.",
            repeated=repeated_units,
        )
    if case.row_independence_state == "refuted":
        return _evaluation(
            case,
            digest,
            "covered_negative",
            "row_independence_not_used",
            "The bound procedure is established not to use row-level independence.",
            repeated=repeated_units,
        )
    if case.affected_target_state != "established" or case.affected_target_ref is None:
        return _evaluation(
            case,
            digest,
            "question",
            "affected_target_not_established",
            "The exact affected result or claim has not been established.",
            repeated=repeated_units,
            unresolved={"affected_target"},
        )
    if case.output_ceiling != "evaluation_candidate":
        return _evaluation(
            case,
            digest,
            "question",
            "output_ceiling_blocks_candidate",
            "The authorized output ceiling permits a question but not an evaluation candidate.",
            repeated=repeated_units,
            unresolved={"candidate_authority"},
        )
    if (
        case.analysis_input_binding_state != "established"
        or case.separate_observation_entry_state != "established"
        or case.procedure_binding_state != "established"
        or case.row_independence_state != "established"
    ):
        return _evaluation(
            case,
            digest,
            "question",
            "candidate_premise_not_established",
            "Every structural candidate premise must be established explicitly.",
            repeated=repeated_units,
            unresolved={"structural_candidate_premise"},
        )
    return _evaluation(
        case,
        digest,
        "evaluation_candidate",
        "repeated_units_without_dependence_safeguard",
        "Repeated observations from shared independent units entered the bound procedure separately; row-level independence and the absence of every registered safeguard are established for the exact affected target.",
        repeated=repeated_units,
    )


def _evaluation(
    case: DependenceCase,
    digest: str,
    outcome: DependenceOutcome,
    reason_code: str,
    basis: str,
    *,
    repeated: tuple[str, ...] = (),
    safeguards: tuple[str, ...] = (),
    unresolved: set[str] | None = None,
    unsupported: set[str] | None = None,
) -> DependenceEvaluation:
    return DependenceEvaluation(
        outcome=outcome,
        reason_code=reason_code,
        basis=basis,
        repeated_independent_unit_ids=tuple(sorted(repeated)),
        applicable_safeguard_ids=tuple(sorted(safeguards)),
        unresolved_dimensions=tuple(sorted(unresolved or ())),
        unsupported_constructs=tuple(sorted(unsupported or ())),
        case_digest=digest,
        output_ceiling=case.output_ceiling,
    )


def _repeated_units(memberships: tuple[Membership, ...]) -> tuple[str, ...]:
    counts: dict[str, int] = {}
    for membership in memberships:
        counts[membership.independent_unit_id] = counts.get(membership.independent_unit_id, 0) + 1
    return tuple(sorted(unit_id for unit_id, count in counts.items() if count > 1))


def _unique_nonempty(values: tuple[str, ...], label: str, *, allow_empty: bool) -> None:
    if not allow_empty and not values:
        raise DependenceCaseError(f"{label} must not be empty")
    if any(not _present(item) for item in values) or len(values) != len(set(values)):
        raise DependenceCaseError(f"{label} must contain unique nonempty values")


def _present(value: str) -> bool:
    return bool(value) and value == value.strip()
