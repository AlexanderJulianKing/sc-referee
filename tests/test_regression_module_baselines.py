from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.regression_baseline import (
    MODULE_BASELINE_REQUIREMENTS_VERSION,
    RegressionModuleBaselineError,
    regression_module_baseline_gaps,
    regression_module_baseline_projection,
    validate_regression_module_baselines,
)
from sc_referee_evaluation.regression_corpus import validate_regression_corpus_ledger

CALCULATION_REQUIREMENT_ROLES = {
    "positive_or_applicable": {"positive"},
    "corrected_or_conformant": {"corrected_twin"},
    "hard_negative": {"hard_negative"},
    "ambiguity_or_unsupported_boundary": {"ambiguous", "unsupported"},
    "removal_and_sibling_isolation": {"removal"},
    "semantic_replay": {"replay"},
}
QUESTION_REQUIREMENT_ROLES = {
    "positive_or_applicable": {"positive"},
    "matching_close_negative": {"hard_negative"},
    "ambiguity_or_unsupported_boundary": {"ambiguous", "unsupported"},
    "removal_and_sibling_isolation": {"removal"},
    "semantic_replay": {"replay"},
}


def _ledger(project_root: Path) -> dict[str, Any]:
    return validate_regression_corpus_ledger(project_root=project_root)


def _remove_requirement_evidence(
    ledger: dict[str, Any], component_id: str, permitted_roles: set[str]
) -> None:
    retained = []
    for case in ledger["cases"]:
        mutated = copy.deepcopy(case)
        if mutated["case_role"] in permitted_roles:
            mutated["component_refs"] = [
                item for item in mutated["component_refs"] if item != component_id
            ]
        if mutated["component_refs"]:
            retained.append(mutated)
    ledger["cases"] = retained


def test_every_active_module_has_the_exact_l03_baseline(project_root: Path) -> None:
    projection = validate_regression_module_baselines(_ledger(project_root))

    assert projection["requirements_version"] == MODULE_BASELINE_REQUIREMENTS_VERSION
    assert projection["complete"] is True
    assert len(projection["modules"]) == 32
    assert all(module["complete"] is True for module in projection["modules"])
    assert all(
        requirement["case_ids"]
        for module in projection["modules"]
        for requirement in module["requirements"]
    )


def test_each_required_role_is_independently_enforced_for_each_module(
    project_root: Path,
) -> None:
    ledger = _ledger(project_root)

    for component in ledger["component_inventory"]:
        component_id = component["component_id"]
        requirement_roles = (
            CALCULATION_REQUIREMENT_ROLES
            if component["component_kind"] == "calculation_check"
            else QUESTION_REQUIREMENT_ROLES
        )
        for requirement, permitted_roles in requirement_roles.items():
            mutated = copy.deepcopy(ledger)
            _remove_requirement_evidence(mutated, component_id, permitted_roles)

            assert regression_module_baseline_gaps(mutated) == {component_id: (requirement,)}
            with pytest.raises(
                RegressionModuleBaselineError,
                match=f"{component_id}: {requirement}",
            ):
                validate_regression_module_baselines(mutated)


def test_question_modules_do_not_invent_a_corrected_scientific_answer(
    project_root: Path,
) -> None:
    projection = regression_module_baseline_projection(_ledger(project_root))
    question_modules = [
        module for module in projection["modules"] if module["component_kind"] == "scientific_check"
    ]

    assert question_modules
    assert all(
        {item["requirement"] for item in module["requirements"]} == set(QUESTION_REQUIREMENT_ROLES)
        for module in question_modules
    )
    assert all(
        "corrected_or_conformant" not in {item["requirement"] for item in module["requirements"]}
        for module in question_modules
    )
    assert (
        "no scientifically preferred answer is invented"
        in projection["question_only_correct_arm_policy"]
    )


def test_projection_rejects_unknown_component_references_and_kinds(
    project_root: Path,
) -> None:
    unknown_reference = _ledger(project_root)
    unknown_reference["cases"][0]["component_refs"] = ["check:not-installed"]
    with pytest.raises(RegressionModuleBaselineError, match="unknown baseline component"):
        regression_module_baseline_projection(unknown_reference)

    unknown_kind = _ledger(project_root)
    unknown_kind["component_inventory"][0]["component_kind"] = "unbounded_guess"
    with pytest.raises(RegressionModuleBaselineError, match="Unknown baseline component kind"):
        regression_module_baseline_projection(unknown_kind)
