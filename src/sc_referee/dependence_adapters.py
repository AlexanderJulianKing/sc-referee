from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

from sc_referee.dependence_core import (
    SAFEGUARD_IDS,
    DependenceCase,
    DependenceOutputCeiling,
    EvidenceState,
    Membership,
    RecordRef,
    SafeguardCheck,
    SafeguardState,
)

DEPENDENCE_DECLARATION_RECORD_TYPE = "development_dependence_declaration"
DEPENDENCE_DECLARATION_PROFILE_VERSION = "1.0.0"
SINGLE_CELL_PROFILE_ID = "single_cell_participant_dependence_v1"
LONGITUDINAL_PROFILE_ID = "longitudinal_participant_dependence_v1"
NESTED_EXPERIMENT_PROFILE_ID = "nested_experiment_animal_dependence_v1"

AdaptationStatus = Literal["adapted", "not_applicable", "unsupported", "ambiguous"]


@dataclass(frozen=True)
class DependenceAdapterOutcome:
    status: AdaptationStatus
    adapter_ids: tuple[str, ...]
    case: DependenceCase | None
    basis: str


class DependenceDeclarationAdapter(Protocol):
    adapter_id: str
    profile_id: str

    def adapt(self, record: Mapping[str, object]) -> DependenceAdapterOutcome: ...


@dataclass(frozen=True)
class _ProfileShape:
    adapter_id: str
    profile_id: str
    unit_definition_key: str
    memberships_key: str
    membership_keys: frozenset[str]
    observation_key: str
    independent_unit_key: str


_COMMON_KEYS = frozenset(
    {
        "record_type",
        "profile_id",
        "profile_version",
        "case_id",
        "authority",
        "analysis_target_ref",
        "procedure_ref",
        "analysis_binding",
        "safeguard_checks",
        "affected_target_ref",
        "affected_target_state",
        "membership_state",
        "unresolved_dimensions",
        "unsupported_constructs",
        "output_ceiling",
    }
)
_AUTHORITY_KEYS = frozenset(
    {
        "record_type",
        "record_id",
        "actor_id",
        "authority_state",
        "analysis_target_ref",
        "procedure_ref",
        "independent_unit_definition_id",
    }
)
_BINDING_KEYS = frozenset(
    {
        "analysis_target_ref",
        "procedure_ref",
        "input_binding_state",
        "separate_observation_entry_state",
        "procedure_binding_state",
        "row_independence_state",
    }
)
_SAFEGUARD_KEYS = frozenset(
    {
        "safeguard_id",
        "state",
        "analysis_target_ref",
        "procedure_ref",
        "independent_unit_definition_id",
        "evidence_ids",
        "basis",
    }
)


class _ClosedDeclarationAdapter:
    def __init__(self, shape: _ProfileShape) -> None:
        self._shape = shape
        self.adapter_id = shape.adapter_id
        self.profile_id = shape.profile_id

    def adapt(self, record: Mapping[str, object]) -> DependenceAdapterOutcome:
        try:
            case = self._adapt(record)
        except _UnsupportedDeclaration as error:
            return DependenceAdapterOutcome(
                status="unsupported",
                adapter_ids=(self.adapter_id,),
                case=None,
                basis=str(error),
            )
        return DependenceAdapterOutcome(
            status="adapted",
            adapter_ids=(self.adapter_id,),
            case=case,
            basis="The exact typed development declaration was bound to one neutral dependence case.",
        )

    def _adapt(self, record: Mapping[str, object]) -> DependenceCase:
        shape = self._shape
        expected = _COMMON_KEYS | {shape.unit_definition_key, shape.memberships_key}
        _require_exact_keys(record, expected, "dependence declaration")
        _require_equal(record.get("record_type"), DEPENDENCE_DECLARATION_RECORD_TYPE, "record_type")
        _require_equal(record.get("profile_id"), shape.profile_id, "profile_id")
        _require_equal(
            record.get("profile_version"),
            DEPENDENCE_DECLARATION_PROFILE_VERSION,
            "profile_version",
        )
        case_id = _string(record.get("case_id"), "case_id")
        analysis_target_ref = _record_ref(record.get("analysis_target_ref"), "analysis_target_ref")
        procedure_ref = _record_ref(record.get("procedure_ref"), "procedure_ref")
        affected_target_ref = _record_ref(record.get("affected_target_ref"), "affected_target_ref")
        unit_definition_id = _string(
            record.get(shape.unit_definition_key), shape.unit_definition_key
        )

        authority = _mapping(record.get("authority"), "authority")
        _require_exact_keys(authority, _AUTHORITY_KEYS, "authority")
        _require_equal(
            authority.get("record_type"), "human_method_authorization", "authority record_type"
        )
        _string(authority.get("record_id"), "authority record_id")
        _string(authority.get("actor_id"), "authority actor_id")
        _require_equal(authority.get("authority_state"), "authorized", "authority_state")
        _require_ref_equal(
            authority.get("analysis_target_ref"), analysis_target_ref, "authority analysis target"
        )
        _require_ref_equal(authority.get("procedure_ref"), procedure_ref, "authority procedure")
        _require_equal(
            authority.get("independent_unit_definition_id"),
            unit_definition_id,
            "authority independent-unit definition",
        )

        binding = _mapping(record.get("analysis_binding"), "analysis_binding")
        _require_exact_keys(binding, _BINDING_KEYS, "analysis binding")
        _require_ref_equal(
            binding.get("analysis_target_ref"), analysis_target_ref, "binding analysis target"
        )
        _require_ref_equal(binding.get("procedure_ref"), procedure_ref, "binding procedure")

        memberships = _memberships(record.get(shape.memberships_key), shape)
        safeguard_checks = _safeguards(
            record.get("safeguard_checks"),
            analysis_target_ref=analysis_target_ref,
            procedure_ref=procedure_ref,
            unit_definition_id=unit_definition_id,
        )
        return DependenceCase(
            case_id=case_id,
            analyzed_observation_ids=tuple(
                sorted(membership.observation_id for membership in memberships)
            ),
            independent_unit_definition_id=unit_definition_id,
            unit_definition_state="established",
            memberships=memberships,
            membership_state=_evidence_state(record.get("membership_state"), "membership_state"),
            analysis_target_ref=analysis_target_ref,
            analysis_input_binding_state=_evidence_state(
                binding.get("input_binding_state"), "input_binding_state"
            ),
            separate_observation_entry_state=_evidence_state(
                binding.get("separate_observation_entry_state"),
                "separate_observation_entry_state",
            ),
            procedure_ref=procedure_ref,
            procedure_binding_state=_evidence_state(
                binding.get("procedure_binding_state"), "procedure_binding_state"
            ),
            row_independence_state=_evidence_state(
                binding.get("row_independence_state"), "row_independence_state"
            ),
            safeguard_checks=safeguard_checks,
            affected_target_ref=affected_target_ref,
            affected_target_state=_evidence_state(
                record.get("affected_target_state"), "affected_target_state"
            ),
            unresolved_dimensions=_string_tuple(
                record.get("unresolved_dimensions"), "unresolved_dimensions"
            ),
            unsupported_constructs=_string_tuple(
                record.get("unsupported_constructs"), "unsupported_constructs"
            ),
            output_ceiling=_output_ceiling(record.get("output_ceiling")),
        )


class SingleCellDependenceDeclarationAdapter(_ClosedDeclarationAdapter):
    def __init__(self) -> None:
        super().__init__(
            _ProfileShape(
                adapter_id="dependence-adapter:single-cell-participant-v1",
                profile_id=SINGLE_CELL_PROFILE_ID,
                unit_definition_key="participant_unit_definition_id",
                memberships_key="cell_memberships",
                membership_keys=frozenset(
                    {"cell_id", "sample_id", "participant_id", "evidence_ids"}
                ),
                observation_key="cell_id",
                independent_unit_key="participant_id",
            )
        )


class LongitudinalDependenceDeclarationAdapter(_ClosedDeclarationAdapter):
    def __init__(self) -> None:
        super().__init__(
            _ProfileShape(
                adapter_id="dependence-adapter:longitudinal-participant-v1",
                profile_id=LONGITUDINAL_PROFILE_ID,
                unit_definition_key="participant_unit_definition_id",
                memberships_key="measurement_memberships",
                membership_keys=frozenset(
                    {"measurement_id", "participant_id", "timepoint_id", "evidence_ids"}
                ),
                observation_key="measurement_id",
                independent_unit_key="participant_id",
            )
        )


class NestedExperimentDependenceDeclarationAdapter(_ClosedDeclarationAdapter):
    def __init__(self) -> None:
        super().__init__(
            _ProfileShape(
                adapter_id="dependence-adapter:nested-experiment-animal-v1",
                profile_id=NESTED_EXPERIMENT_PROFILE_ID,
                unit_definition_key="animal_unit_definition_id",
                memberships_key="observation_memberships",
                membership_keys=frozenset(
                    {
                        "observation_id",
                        "field_id",
                        "well_id",
                        "specimen_id",
                        "animal_id",
                        "evidence_ids",
                    }
                ),
                observation_key="observation_id",
                independent_unit_key="animal_id",
            )
        )


DEFAULT_DEPENDENCE_DECLARATION_ADAPTERS: tuple[DependenceDeclarationAdapter, ...] = (
    SingleCellDependenceDeclarationAdapter(),
    LongitudinalDependenceDeclarationAdapter(),
    NestedExperimentDependenceDeclarationAdapter(),
)


def adapt_dependence_declaration(
    record: object,
    *,
    adapters: Sequence[DependenceDeclarationAdapter] = DEFAULT_DEPENDENCE_DECLARATION_ADAPTERS,
) -> DependenceAdapterOutcome:
    """Dispatch one exact root declaration without inferring a domain or scientific role."""

    if not isinstance(record, Mapping):
        return DependenceAdapterOutcome(
            status="not_applicable",
            adapter_ids=(),
            case=None,
            basis="The input is not a typed dependence-declaration object.",
        )
    if record.get("record_type") != DEPENDENCE_DECLARATION_RECORD_TYPE:
        return DependenceAdapterOutcome(
            status="not_applicable",
            adapter_ids=(),
            case=None,
            basis="No exact root development dependence declaration was selected.",
        )
    profile_id = record.get("profile_id")
    selected = tuple(adapter for adapter in adapters if adapter.profile_id == profile_id)
    if not selected:
        return DependenceAdapterOutcome(
            status="unsupported",
            adapter_ids=(),
            case=None,
            basis="The declared dependence profile is not installed.",
        )
    if len(selected) != 1:
        return DependenceAdapterOutcome(
            status="ambiguous",
            adapter_ids=tuple(sorted(adapter.adapter_id for adapter in selected)),
            case=None,
            basis="More than one installed adapter claims the exact declared profile.",
        )
    return selected[0].adapt(record)


class _UnsupportedDeclaration(ValueError):
    pass


def _memberships(value: object, shape: _ProfileShape) -> tuple[Membership, ...]:
    rows = _sequence(value, shape.memberships_key)
    memberships: list[Membership] = []
    observation_ids: set[str] = set()
    for index, item in enumerate(rows):
        row = _mapping(item, f"{shape.memberships_key}[{index}]")
        _require_exact_keys(row, shape.membership_keys, f"{shape.memberships_key}[{index}]")
        observation_id = _string(row.get(shape.observation_key), shape.observation_key)
        independent_unit_id = _string(
            row.get(shape.independent_unit_key), shape.independent_unit_key
        )
        for key in shape.membership_keys - {"evidence_ids"}:
            _string(row.get(key), key)
        if observation_id in observation_ids:
            raise _UnsupportedDeclaration("an analyzed observation is declared more than once")
        observation_ids.add(observation_id)
        memberships.append(
            Membership(
                observation_id=observation_id,
                independent_unit_id=independent_unit_id,
                evidence_ids=_string_tuple(row.get("evidence_ids"), "evidence_ids"),
            )
        )
    if len(memberships) < 2:
        raise _UnsupportedDeclaration("at least two analyzed observations must be declared")
    return tuple(
        sorted(memberships, key=lambda item: (item.observation_id, item.independent_unit_id))
    )


def _safeguards(
    value: object,
    *,
    analysis_target_ref: RecordRef,
    procedure_ref: RecordRef,
    unit_definition_id: str,
) -> tuple[SafeguardCheck, ...]:
    rows = _sequence(value, "safeguard_checks")
    checks: list[SafeguardCheck] = []
    seen: set[str] = set()
    for index, item in enumerate(rows):
        row = _mapping(item, f"safeguard_checks[{index}]")
        _require_exact_keys(row, _SAFEGUARD_KEYS, f"safeguard_checks[{index}]")
        safeguard_id = _string(row.get("safeguard_id"), "safeguard_id")
        if safeguard_id not in SAFEGUARD_IDS or safeguard_id in seen:
            raise _UnsupportedDeclaration(
                "safeguard IDs must exactly and uniquely cover the registry"
            )
        seen.add(safeguard_id)
        _require_ref_equal(
            row.get("analysis_target_ref"), analysis_target_ref, "safeguard analysis target"
        )
        _require_ref_equal(row.get("procedure_ref"), procedure_ref, "safeguard procedure")
        _require_equal(
            row.get("independent_unit_definition_id"),
            unit_definition_id,
            "safeguard independent-unit definition",
        )
        evidence_ids = _string_tuple(row.get("evidence_ids"), "evidence_ids")
        checks.append(
            SafeguardCheck(
                safeguard_id=safeguard_id,
                state=_safeguard_state(row.get("state")),
                analysis_target_ref=analysis_target_ref,
                procedure_ref=procedure_ref,
                independent_unit_definition_id=unit_definition_id,
                evidence_ids=evidence_ids,
                basis=_string(row.get("basis"), "basis"),
            )
        )
    if seen != set(SAFEGUARD_IDS):
        raise _UnsupportedDeclaration("safeguard declarations do not cover the exact registry")
    return tuple(sorted(checks, key=lambda item: item.safeguard_id))


def _record_ref(value: object, label: str) -> RecordRef:
    mapping = _mapping(value, label)
    _require_exact_keys(mapping, frozenset({"record_type", "record_id"}), label)
    return RecordRef(
        record_type=_string(mapping.get("record_type"), f"{label} record_type"),
        record_id=_string(mapping.get("record_id"), f"{label} record_id"),
    )


def _require_ref_equal(value: object, expected: RecordRef, label: str) -> None:
    if _record_ref(value, label) != expected:
        raise _UnsupportedDeclaration(f"{label} does not match the exact declared binding")


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise _UnsupportedDeclaration(f"{label} must be an object with string keys")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise _UnsupportedDeclaration(f"{label} must be an array")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise _UnsupportedDeclaration(f"{label} must be a trimmed nonempty string")
    return value


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    result = tuple(_string(item, label) for item in _sequence(value, label))
    if len(result) != len(set(result)):
        raise _UnsupportedDeclaration(f"{label} must not contain duplicate values")
    return tuple(sorted(result))


def _require_exact_keys(
    value: Mapping[str, object], expected: frozenset[str] | set[str], label: str
) -> None:
    if set(value) != set(expected):
        raise _UnsupportedDeclaration(f"{label} has unsupported or missing fields")


def _require_equal(value: object, expected: object, label: str) -> None:
    if value != expected:
        raise _UnsupportedDeclaration(f"{label} is unsupported or does not match its binding")


def _evidence_state(value: object, label: str) -> EvidenceState:
    if value not in {"established", "refuted", "unknown", "unsupported"}:
        raise _UnsupportedDeclaration(f"{label} is outside the closed evidence-state vocabulary")
    return value


def _safeguard_state(value: object) -> SafeguardState:
    if value not in {"present", "absent", "not_applicable", "unknown", "unsupported"}:
        raise _UnsupportedDeclaration("safeguard state is outside the closed vocabulary")
    return value


def _output_ceiling(value: object) -> DependenceOutputCeiling:
    if value not in {"question_only", "evaluation_candidate"}:
        raise _UnsupportedDeclaration("adapter output ceiling cannot permit a production Finding")
    return value
