from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from sc_referee.dependence_adapters import (
    LONGITUDINAL_PROFILE_ID,
    NESTED_EXPERIMENT_PROFILE_ID,
    SINGLE_CELL_PROFILE_ID,
    LongitudinalDependenceDeclarationAdapter,
    NestedExperimentDependenceDeclarationAdapter,
    SingleCellDependenceDeclarationAdapter,
    adapt_dependence_declaration,
)
from sc_referee.dependence_core import SAFEGUARD_IDS, evaluate_dependence_case

TARGET_REF = {"record_type": "analysis", "record_id": "analysis:primary"}
PROCEDURE_REF = {"record_type": "procedure", "record_id": "procedure:model-fit"}
AFFECTED_REF = {"record_type": "result", "record_id": "result:primary"}


def _common(profile_id: str, unit_definition_id: str) -> dict[str, Any]:
    safeguards = [
        {
            "safeguard_id": safeguard_id,
            "state": "absent",
            "analysis_target_ref": TARGET_REF,
            "procedure_ref": PROCEDURE_REF,
            "independent_unit_definition_id": unit_definition_id,
            "evidence_ids": [f"evidence:{index}:safeguard-check"],
            "basis": "The exact bound declaration records this safeguard as absent.",
        }
        for index, safeguard_id in enumerate(SAFEGUARD_IDS)
    ]
    return {
        "record_type": "development_dependence_declaration",
        "profile_id": profile_id,
        "profile_version": "1.0.0",
        "case_id": f"case:{profile_id}",
        "authority": {
            "record_type": "human_method_authorization",
            "record_id": f"authorization:{profile_id}",
            "actor_id": "human:method-owner",
            "authority_state": "authorized",
            "analysis_target_ref": TARGET_REF,
            "procedure_ref": PROCEDURE_REF,
            "independent_unit_definition_id": unit_definition_id,
        },
        "analysis_target_ref": TARGET_REF,
        "procedure_ref": PROCEDURE_REF,
        "analysis_binding": {
            "analysis_target_ref": TARGET_REF,
            "procedure_ref": PROCEDURE_REF,
            "input_binding_state": "established",
            "separate_observation_entry_state": "established",
            "procedure_binding_state": "established",
            "row_independence_state": "established",
        },
        "safeguard_checks": safeguards,
        "affected_target_ref": AFFECTED_REF,
        "affected_target_state": "established",
        "membership_state": "established",
        "unresolved_dimensions": [],
        "unsupported_constructs": [],
        "output_ceiling": "evaluation_candidate",
    }


def _single_cell() -> dict[str, Any]:
    record = _common(SINGLE_CELL_PROFILE_ID, "unit-definition:participant")
    record.update(
        {
            "participant_unit_definition_id": "unit-definition:participant",
            "cell_memberships": [
                {
                    "cell_id": "cell:c1",
                    "sample_id": "sample:s1",
                    "participant_id": "participant:p1",
                    "evidence_ids": ["evidence:cell:c1:membership"],
                },
                {
                    "cell_id": "cell:c2",
                    "sample_id": "sample:s1",
                    "participant_id": "participant:p1",
                    "evidence_ids": ["evidence:cell:c2:membership"],
                },
                {
                    "cell_id": "cell:c3",
                    "sample_id": "sample:s2",
                    "participant_id": "participant:p2",
                    "evidence_ids": ["evidence:cell:c3:membership"],
                },
            ],
        }
    )
    return record


def _longitudinal() -> dict[str, Any]:
    record = _common(LONGITUDINAL_PROFILE_ID, "unit-definition:participant")
    record.update(
        {
            "participant_unit_definition_id": "unit-definition:participant",
            "measurement_memberships": [
                {
                    "measurement_id": "measurement:m1",
                    "participant_id": "participant:p1",
                    "timepoint_id": "timepoint:t1",
                    "evidence_ids": ["evidence:measurement:m1:membership"],
                },
                {
                    "measurement_id": "measurement:m2",
                    "participant_id": "participant:p1",
                    "timepoint_id": "timepoint:t2",
                    "evidence_ids": ["evidence:measurement:m2:membership"],
                },
                {
                    "measurement_id": "measurement:m3",
                    "participant_id": "participant:p2",
                    "timepoint_id": "timepoint:t1",
                    "evidence_ids": ["evidence:measurement:m3:membership"],
                },
            ],
        }
    )
    return record


def _nested_experiment() -> dict[str, Any]:
    record = _common(NESTED_EXPERIMENT_PROFILE_ID, "unit-definition:animal")
    record.update(
        {
            "animal_unit_definition_id": "unit-definition:animal",
            "observation_memberships": [
                {
                    "observation_id": "field:f1",
                    "field_id": "field:f1",
                    "well_id": "well:w1",
                    "specimen_id": "specimen:s1",
                    "animal_id": "animal:a1",
                    "evidence_ids": ["evidence:field:f1:membership"],
                },
                {
                    "observation_id": "field:f2",
                    "field_id": "field:f2",
                    "well_id": "well:w2",
                    "specimen_id": "specimen:s1",
                    "animal_id": "animal:a1",
                    "evidence_ids": ["evidence:field:f2:membership"],
                },
                {
                    "observation_id": "field:f3",
                    "field_id": "field:f3",
                    "well_id": "well:w3",
                    "specimen_id": "specimen:s2",
                    "animal_id": "animal:a2",
                    "evidence_ids": ["evidence:field:f3:membership"],
                },
            ],
        }
    )
    return record


@pytest.mark.parametrize("record", [_single_cell(), _longitudinal(), _nested_experiment()])
def test_three_materially_different_profiles_map_to_neutral_candidate(
    record: dict[str, Any],
) -> None:
    adapted = adapt_dependence_declaration(record)

    assert adapted.status == "adapted"
    assert adapted.case is not None
    projection = adapted.case.to_dict()
    assert projection["case_family"] == "dependence"
    assert "cell_id" not in projection
    assert "timepoint_id" not in projection
    assert "well_id" not in projection
    evaluated = evaluate_dependence_case(adapted.case)
    assert evaluated.outcome == "evaluation_candidate"
    assert evaluated.reason_code == "repeated_units_without_dependence_safeguard"
    assert len(evaluated.repeated_independent_unit_ids) == 1


def test_reordering_and_identifier_renaming_preserve_the_decision() -> None:
    original = _single_cell()
    reordered = deepcopy(original)
    reordered["cell_memberships"].reverse()
    reordered["safeguard_checks"].reverse()
    renamed = _longitudinal()
    for row in renamed["measurement_memberships"]:
        row["measurement_id"] = "renamed:" + row["measurement_id"]
        row["participant_id"] = "renamed:" + row["participant_id"]

    outcomes = []
    for record in (original, reordered, renamed):
        adapted = adapt_dependence_declaration(record)
        assert adapted.case is not None
        outcomes.append(evaluate_dependence_case(adapted.case))

    assert outcomes[0].case_digest == outcomes[1].case_digest
    assert {item.outcome for item in outcomes} == {"evaluation_candidate"}
    assert {item.reason_code for item in outcomes} == {
        "repeated_units_without_dependence_safeguard"
    }


def test_exact_bound_safeguard_changes_the_neutral_result() -> None:
    record = _nested_experiment()
    record["safeguard_checks"][2]["state"] = "present"

    adapted = adapt_dependence_declaration(record)
    assert adapted.case is not None
    evaluated = evaluate_dependence_case(adapted.case)

    assert evaluated.outcome == "covered_negative"
    assert evaluated.reason_code == "applicable_safeguard_present"
    assert evaluated.applicable_safeguard_ids == (SAFEGUARD_IDS[2],)


def test_authority_and_safeguards_must_bind_exact_grouping_and_procedure() -> None:
    authority_mismatch = _longitudinal()
    authority_mismatch["authority"]["independent_unit_definition_id"] = "unit-definition:visit"
    safeguard_mismatch = _single_cell()
    safeguard_mismatch["safeguard_checks"][0]["procedure_ref"] = {
        "record_type": "procedure",
        "record_id": "procedure:other",
    }

    for record in (authority_mismatch, safeguard_mismatch):
        outcome = adapt_dependence_declaration(record)
        assert outcome.status == "unsupported"
        assert outcome.case is None


def test_wrapper_ambiguous_and_malformed_declarations_abstain() -> None:
    wrapped = adapt_dependence_declaration({"payload": _single_cell()})
    ambiguous = adapt_dependence_declaration(
        _single_cell(),
        adapters=(
            SingleCellDependenceDeclarationAdapter(),
            SingleCellDependenceDeclarationAdapter(),
        ),
    )
    malformed_record = _single_cell()
    del malformed_record["authority"]
    malformed = adapt_dependence_declaration(malformed_record)

    assert wrapped.status == "not_applicable" and wrapped.case is None
    assert ambiguous.status == "ambiguous" and ambiguous.case is None
    assert malformed.status == "unsupported" and malformed.case is None


def test_adapter_removal_isolated_from_sibling_profiles() -> None:
    installed = (
        LongitudinalDependenceDeclarationAdapter(),
        NestedExperimentDependenceDeclarationAdapter(),
    )

    removed = adapt_dependence_declaration(_single_cell(), adapters=installed)
    longitudinal = adapt_dependence_declaration(_longitudinal(), adapters=installed)
    nested = adapt_dependence_declaration(_nested_experiment(), adapters=installed)

    assert removed.status == "unsupported" and removed.case is None
    assert longitudinal.status == "adapted" and longitudinal.case is not None
    assert nested.status == "adapted" and nested.case is not None
