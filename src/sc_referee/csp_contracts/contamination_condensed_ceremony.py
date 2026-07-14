"""Four-decision human ratification gate for contamination proposals."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import Enum
import hashlib

from sc_referee.csp import (
    CspContractRecord,
    CspFieldRecord,
    CspFieldState,
    CspScope,
    component_identities_for,
)

from .contamination_basis_obligation_v1 import (
    CAUSAL_FIELDS,
    CONTRACT_TYPE,
    MANIFEST,
    MEASUREMENT_FIELDS,
    REQUIRED_FIELDS,
)


class CondensedAnswer(str, Enum):
    YES = "yes"
    NO = "no"
    NOT_SURE = "not_sure"


class CondensedGroup(str, Enum):
    MEASUREMENT = "Measurement"
    TIMING = "Timing"
    ESTIMAND = "Estimand"
    AUTHORITY = "Authority"


# This is deliberately closed and exhaustive.  The component groups define the
# measurement/causal boundary; the four ceremony statements split scope authority,
# temporal/assignment claims, and estimand obligations within those components.
GROUP_FIELDS = {
    CondensedGroup.MEASUREMENT: tuple(
        field for field in MEASUREMENT_FIELDS if field != "measurement_scope_authority"
    ),
    CondensedGroup.TIMING: (
        "pre_exposure", "non_descendancy", "assignment_context",
    ),
    CondensedGroup.ESTIMAND: (
        "outside_estimand_pathway", "required_adjustment", "exact_basis_adequacy",
    ),
    CondensedGroup.AUTHORITY: (
        "measurement_scope_authority", "causal_scope_authority",
    ),
}

if set(field for fields in GROUP_FIELDS.values() for field in fields) != set(REQUIRED_FIELDS):
    raise RuntimeError("condensed contamination ceremony does not cover the closed contract")
if sum(map(len, GROUP_FIELDS.values())) != len(REQUIRED_FIELDS):
    raise RuntimeError("condensed contamination ceremony assigns a field more than once")
if not set(GROUP_FIELDS[CondensedGroup.TIMING] + GROUP_FIELDS[CondensedGroup.ESTIMAND]).issubset(
    set(CAUSAL_FIELDS)
):
    raise RuntimeError("condensed causal ceremony groups escaped the causal component")


@dataclass(frozen=True)
class CondensedAbstention(CspContractRecord):
    """A non-authorizing ceremony record that remains readable as a CSP abstention."""

    abstention_reason: str = "condensed_confirmation_incomplete"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.authority_attested:
            raise ValueError("a condensed abstention cannot attest authority")
        if any(record.state is CspFieldState.CONFIRMED_HIGH for record in self.fields.values()):
            raise ValueError("a condensed abstention cannot contain confirmed fields")


def _answer(value: object) -> CondensedAnswer:
    if isinstance(value, CondensedAnswer):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
        try:
            return CondensedAnswer(normalized)
        except ValueError:
            pass
    raise ValueError(f"invalid condensed contamination answer: {value!r}")


def _answers(answers: Mapping[object, object]) -> dict[CondensedGroup, CondensedAnswer]:
    decisions = {group: CondensedAnswer.NOT_SURE for group in CondensedGroup}
    for key, value in answers.items():
        try:
            group = key if isinstance(key, CondensedGroup) else CondensedGroup(str(key).title())
        except ValueError as exc:
            raise ValueError(f"unknown condensed contamination group: {key!r}") from exc
        decisions[group] = _answer(value)
    return decisions


def ratify_contamination_condensed(
    proposal_values: Mapping[str, object],
    scope: CspScope,
    answers: Mapping[object, object],
) -> CspContractRecord | CondensedAbstention:
    """Translate four human decisions without altering the proposed scientific values."""

    if set(proposal_values) != set(REQUIRED_FIELDS):
        raise ValueError("contamination proposal must contain exactly the required fields")
    decisions = _answers(answers)
    all_yes = all(answer is CondensedAnswer.YES for answer in decisions.values())
    validation = tuple(MANIFEST.validate_values(proposal_values))
    if all_yes and validation:
        raise ValueError("invalid contamination proposal: " + ", ".join(validation))

    fingerprint = scope.fingerprint
    fields: dict[str, CspFieldRecord] = {}
    for group, group_fields in GROUP_FIELDS.items():
        decision = decisions[group]
        authorizing = all_yes and decision is CondensedAnswer.YES
        state = (
            CspFieldState.CONFIRMED_HIGH if authorizing
            else CspFieldState.DECLINED_FOR_CONSUMER
            if decision is CondensedAnswer.NO
            else CspFieldState.UNRESOLVED
        )
        for field_id in group_fields:
            fields[field_id] = CspFieldRecord(
                field_id=field_id,
                value=proposal_values[field_id] if authorizing else None,
                state=state,
                confidence="high" if authorizing else "low",
                scope_fingerprint=fingerprint,
                evidence_ids=(f"evidence:condensed-ceremony-{group.value.lower()}:v1",)
                if authorizing else (),
                evidence_basis="human_group_confirmation" if authorizing else None,
                selected_teach_back_id=MANIFEST.teach_back_ids[field_id]
                if authorizing else None,
                consequence_acknowledged=authorizing,
                presentation_event_id=f"present:condensed-{group.value.lower()}:v1",
                answer_event_id=f"answer:condensed-{group.value.lower()}:v1",
                confirmation_event_id=f"confirm:condensed-{group.value.lower()}:v1"
                if authorizing else None,
                actor="human scientific interpreter" if authorizing else None,
                confirmed_at="2026-07-12T00:00:00Z" if authorizing else None,
            )

    contract_suffix = hashlib.sha256(fingerprint.encode("ascii")).hexdigest()[:16]
    record_type = CspContractRecord if all_yes else CondensedAbstention
    record = record_type(
        contract_id=f"csp:contamination:condensed:{contract_suffix}",
        contract_type=CONTRACT_TYPE,
        scope=scope,
        fields=fields,
        authorized_consumers=(MANIFEST.authorized_consumer,),
        authority_attested=all_yes,
        authority_attestation=MANIFEST.authority_attestation if all_yes else None,
        validator_version=MANIFEST.validator_version,
        validator_result=validation,
        active=True,
        created_at="2026-07-12T00:00:00Z",
    )
    return replace(record, component_identities=component_identities_for(record, MANIFEST))
