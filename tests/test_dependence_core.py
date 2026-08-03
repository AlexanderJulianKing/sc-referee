from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from sc_referee.dependence_core import (
    SAFEGUARD_IDS,
    DependenceCase,
    DependenceCaseError,
    Membership,
    RecordRef,
    SafeguardCheck,
    evaluate_dependence_case,
)


def _case(
    *,
    safeguard_states: dict[str, str] | None = None,
    memberships: tuple[Membership, ...] | None = None,
    **changes: object,
) -> DependenceCase:
    analysis_ref = RecordRef("analysis", "analysis:primary")
    procedure_ref = RecordRef("procedure", "procedure:fit")
    states = safeguard_states or {}
    values: dict[str, object] = {
        "case_id": "dependence-case:one",
        "analyzed_observation_ids": ("obs-1", "obs-2", "obs-3"),
        "independent_unit_definition_id": "unit-definition:governing",
        "unit_definition_state": "established",
        "memberships": memberships
        or (
            Membership("obs-1", "unit-a", ("evidence:membership-1",)),
            Membership("obs-2", "unit-a", ("evidence:membership-2",)),
            Membership("obs-3", "unit-b", ("evidence:membership-3",)),
        ),
        "membership_state": "established",
        "analysis_target_ref": analysis_ref,
        "analysis_input_binding_state": "established",
        "separate_observation_entry_state": "established",
        "procedure_ref": procedure_ref,
        "procedure_binding_state": "established",
        "row_independence_state": "established",
        "safeguard_checks": tuple(
            SafeguardCheck(
                safeguard_id,
                states.get(safeguard_id, "absent"),  # type: ignore[arg-type]
                analysis_ref,
                procedure_ref,
                "unit-definition:governing",
                (f"evidence:{safeguard_id}",),
                "The bounded inspection completed.",
            )
            for safeguard_id in SAFEGUARD_IDS
        ),
        "affected_target_ref": RecordRef("result", "result:reported"),
        "affected_target_state": "established",
        "unresolved_dimensions": (),
        "unsupported_constructs": (),
        "output_ceiling": "evaluation_candidate",
    }
    values.update(changes)
    return DependenceCase(**values)  # type: ignore[arg-type]


def test_closed_repeated_memberships_without_safeguard_yield_evaluation_candidate() -> None:
    result = evaluate_dependence_case(_case())

    assert result.outcome == "evaluation_candidate"
    assert result.reason_code == "repeated_units_without_dependence_safeguard"
    assert result.repeated_independent_unit_ids == ("unit-a",)
    assert result.applicable_safeguard_ids == ()


@pytest.mark.parametrize("safeguard_id", SAFEGUARD_IDS)
def test_each_exact_registered_safeguard_yields_covered_negative(safeguard_id: str) -> None:
    result = evaluate_dependence_case(_case(safeguard_states={safeguard_id: "present"}))

    assert result.outcome == "covered_negative"
    assert result.reason_code == "applicable_safeguard_present"
    assert result.applicable_safeguard_ids == (safeguard_id,)


def test_complete_registry_is_finite_unique_and_stable() -> None:
    assert SAFEGUARD_IDS == (
        "safeguard:unit-level-aggregation",
        "safeguard:grouped-random-effects",
        "safeguard:cluster-correlated-estimation",
        "safeguard:cluster-adjusted-uncertainty",
        "safeguard:paired-or-blocked-procedure",
        "safeguard:unit-level-resampling",
        "safeguard:registered-dependence-aware-procedure",
    )
    assert len(SAFEGUARD_IDS) == len(set(SAFEGUARD_IDS))


def test_not_applicable_safeguard_checks_complete_without_claiming_coverage() -> None:
    result = evaluate_dependence_case(
        _case(safeguard_states={item: "not_applicable" for item in SAFEGUARD_IDS})
    )

    assert result.outcome == "evaluation_candidate"
    assert result.applicable_safeguard_ids == ()


def test_one_observation_per_independent_unit_yields_covered_negative() -> None:
    result = evaluate_dependence_case(
        _case(
            memberships=(
                Membership("obs-1", "unit-a", ("evidence:m-1",)),
                Membership("obs-2", "unit-b", ("evidence:m-2",)),
                Membership("obs-3", "unit-c", ("evidence:m-3",)),
            )
        )
    )

    assert result.outcome == "covered_negative"
    assert result.reason_code == "one_observation_per_independent_unit"


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("analysis_input_binding_state", "observations_not_bound_to_analysis"),
        ("procedure_binding_state", "procedure_not_bound_to_analysis"),
        ("separate_observation_entry_state", "observations_not_entered_separately"),
        ("row_independence_state", "row_independence_not_used"),
    ],
)
def test_refuted_candidate_premises_yield_covered_negative(field: str, reason: str) -> None:
    result = evaluate_dependence_case(_case(**{field: "refuted"}))

    assert result.outcome == "covered_negative"
    assert result.reason_code == reason


@pytest.mark.parametrize(
    ("field", "dimension"),
    [
        ("unit_definition_state", "independent_unit_definition"),
        ("membership_state", "membership_relation"),
        ("analysis_input_binding_state", "analysis_input_binding"),
        ("separate_observation_entry_state", "separate_observation_entry"),
        ("procedure_binding_state", "procedure_binding"),
        ("row_independence_state", "row_independence"),
        ("affected_target_state", "affected_target"),
    ],
)
def test_each_unknown_material_state_yields_question(field: str, dimension: str) -> None:
    result = evaluate_dependence_case(_case(**{field: "unknown"}))

    assert result.outcome == "question"
    assert dimension in result.unresolved_dimensions


@pytest.mark.parametrize(
    ("field", "dimension"),
    [
        ("unit_definition_state", "independent_unit_definition"),
        ("membership_state", "membership_relation"),
        ("analysis_input_binding_state", "analysis_input_binding"),
        ("separate_observation_entry_state", "separate_observation_entry"),
        ("procedure_binding_state", "procedure_binding"),
        ("row_independence_state", "row_independence"),
        ("affected_target_state", "affected_target"),
    ],
)
def test_each_unsupported_material_state_is_localized(field: str, dimension: str) -> None:
    result = evaluate_dependence_case(_case(**{field: "unsupported"}))

    assert result.outcome == "unsupported"
    assert dimension in result.unsupported_constructs


def test_explicit_unsupported_construct_is_localized() -> None:
    result = evaluate_dependence_case(_case(unsupported_constructs=("opaque_wrapper",)))

    assert result.outcome == "unsupported"
    assert result.unsupported_constructs == ("opaque_wrapper",)


def test_explicit_unresolved_dimension_yields_question() -> None:
    result = evaluate_dependence_case(_case(unresolved_dimensions=("unit_authority",)))

    assert result.outcome == "question"
    assert result.unresolved_dimensions == ("unit_authority",)


def test_missing_registered_check_blocks_candidate() -> None:
    case = _case()
    result = evaluate_dependence_case(replace(case, safeguard_checks=case.safeguard_checks[:-1]))

    assert result.outcome == "question"
    assert result.reason_code == "incomplete_safeguard_protocol"
    assert len(result.unresolved_dimensions) == 1


@pytest.mark.parametrize(
    ("state", "outcome", "reason"),
    [
        ("unknown", "question", "unresolved_safeguard_check"),
        ("unsupported", "unsupported", "unsupported_safeguard_check"),
    ],
)
def test_unclosed_safeguard_check_abstains(state: str, outcome: str, reason: str) -> None:
    case = _case()
    first = case.safeguard_checks[0]
    changed = replace(first, state=state, evidence_ids=())  # type: ignore[arg-type]
    result = evaluate_dependence_case(
        replace(case, safeguard_checks=(changed, *case.safeguard_checks[1:]))
    )

    assert result.outcome == outcome
    assert result.reason_code == reason


@pytest.mark.parametrize("binding", ["analysis", "procedure", "unit"])
def test_mismatched_safeguard_binding_cannot_cover_or_support_candidate(binding: str) -> None:
    case = _case(safeguard_states={SAFEGUARD_IDS[0]: "present"})
    first = case.safeguard_checks[0]
    if binding == "analysis":
        first = replace(first, analysis_target_ref=RecordRef("analysis", "analysis:other"))
    elif binding == "procedure":
        first = replace(first, procedure_ref=RecordRef("procedure", "procedure:other"))
    else:
        first = replace(first, independent_unit_definition_id="unit-definition:other")
    result = evaluate_dependence_case(
        replace(case, safeguard_checks=(first, *case.safeguard_checks[1:]))
    )

    assert result.outcome == "question"
    assert result.reason_code == "unresolved_safeguard_binding"
    assert result.applicable_safeguard_ids == ()


def test_question_only_ceiling_blocks_evaluation_candidate() -> None:
    result = evaluate_dependence_case(_case(output_ceiling="question_only"))

    assert result.outcome == "question"
    assert result.reason_code == "output_ceiling_blocks_candidate"


def test_row_and_finite_check_order_do_not_change_digest_or_result() -> None:
    case = _case()
    reordered = replace(
        case,
        analyzed_observation_ids=tuple(reversed(case.analyzed_observation_ids)),
        memberships=tuple(reversed(case.memberships)),
        safeguard_checks=tuple(reversed(case.safeguard_checks)),
    )

    assert reordered.case_digest == case.case_digest
    assert evaluate_dependence_case(reordered) == evaluate_dependence_case(case)


def test_identifier_renaming_does_not_change_decision() -> None:
    original = _case()
    renamed = _case(
        case_id="dependence-case:renamed",
        analyzed_observation_ids=("x", "y", "z"),
        memberships=(
            Membership("x", "group-one", ("evidence:x",)),
            Membership("y", "group-one", ("evidence:y",)),
            Membership("z", "group-two", ("evidence:z",)),
        ),
    )

    assert evaluate_dependence_case(original).outcome == evaluate_dependence_case(renamed).outcome
    assert original.case_digest != renamed.case_digest


def test_unregistered_safeguard_is_rejected() -> None:
    with pytest.raises(DependenceCaseError, match="unregistered safeguard"):
        SafeguardCheck(
            "safeguard:unregistered",
            "absent",
            RecordRef("analysis", "analysis:primary"),
            RecordRef("procedure", "procedure:fit"),
            "unit-definition:governing",
            ("evidence:check",),
            "Inspected.",
        )


def test_unknown_runtime_literal_values_are_rejected_before_evaluation() -> None:
    with pytest.raises(DependenceCaseError, match="invalid evidence state"):
        _case(row_independence_state="assumed")
    with pytest.raises(DependenceCaseError, match="invalid safeguard state"):
        _case(safeguard_states={SAFEGUARD_IDS[0]: "assumed"})
    with pytest.raises(DependenceCaseError, match="invalid dependence output ceiling"):
        _case(output_ceiling="production_finding")


def test_whitespace_only_or_padded_identities_are_rejected() -> None:
    with pytest.raises(DependenceCaseError, match="record references"):
        RecordRef("analysis", " ")
    with pytest.raises(DependenceCaseError, match="membership identities"):
        Membership(" obs-1", "unit-a", ("evidence:one",))
    with pytest.raises(DependenceCaseError, match="unique nonempty"):
        Membership("obs-1", "unit-a", (" evidence:one",))


def test_duplicate_or_incomplete_established_memberships_are_rejected() -> None:
    with pytest.raises(DependenceCaseError, match="only one membership"):
        _case(
            memberships=(
                Membership("obs-1", "unit-a", ("evidence:one",)),
                Membership("obs-1", "unit-b", ("evidence:two",)),
            )
        )
    with pytest.raises(DependenceCaseError, match="cover every analyzed observation"):
        _case(memberships=(Membership("obs-1", "unit-a", ("evidence:one",)),))


def test_production_core_uses_only_domain_neutral_vocabulary(project_root: Path) -> None:
    source = (project_root / "src/sc_referee/dependence_core.py").read_text().casefold()
    forbidden_words = ("cell", "patient", "well", "animal", "image", "visit", "site")

    tokens = {token.strip(".,:;!?()[]{}\"'") for token in source.split()}
    assert tokens.isdisjoint(forbidden_words)
