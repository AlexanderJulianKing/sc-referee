from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

MODULE_BASELINE_REQUIREMENTS_VERSION = "1.0.0"

_CALCULATION_REQUIREMENTS: dict[str, frozenset[str]] = {
    "positive_or_applicable": frozenset({"positive"}),
    "corrected_or_conformant": frozenset({"corrected_twin"}),
    "hard_negative": frozenset({"hard_negative"}),
    "ambiguity_or_unsupported_boundary": frozenset({"ambiguous", "unsupported"}),
    "removal_and_sibling_isolation": frozenset({"removal"}),
    "semantic_replay": frozenset({"replay"}),
}
_QUESTION_REQUIREMENTS: dict[str, frozenset[str]] = {
    "positive_or_applicable": frozenset({"positive"}),
    "matching_close_negative": frozenset({"hard_negative"}),
    "ambiguity_or_unsupported_boundary": frozenset({"ambiguous", "unsupported"}),
    "removal_and_sibling_isolation": frozenset({"removal"}),
    "semantic_replay": frozenset({"replay"}),
}


class RegressionModuleBaselineError(ValueError):
    """An active module lacks one required L03 regression-control class."""


def regression_module_baseline_projection(ledger: Mapping[str, Any]) -> dict[str, Any]:
    """Project exact per-module evidence for the L03 mandatory baseline contract."""

    components = _object_array(ledger.get("component_inventory"), "component_inventory")
    cases = _object_array(ledger.get("cases"), "cases")
    cases_by_component: dict[str, list[Mapping[str, Any]]] = {
        str(component["component_id"]): [] for component in components
    }
    for case in cases:
        refs = case.get("component_refs")
        if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)):
            raise RegressionModuleBaselineError("Regression case component_refs must be an array.")
        for component_ref in refs:
            if not isinstance(component_ref, str) or component_ref not in cases_by_component:
                raise RegressionModuleBaselineError(
                    "Regression case references an unknown baseline component."
                )
            cases_by_component[component_ref].append(case)

    module_results: list[dict[str, Any]] = []
    for component in components:
        component_id = str(component["component_id"])
        component_kind = str(component["component_kind"])
        requirements = (
            _CALCULATION_REQUIREMENTS
            if component_kind == "calculation_check"
            else _QUESTION_REQUIREMENTS
            if component_kind == "scientific_check"
            else None
        )
        if requirements is None:
            raise RegressionModuleBaselineError("Unknown baseline component kind.")
        retained = cases_by_component[component_id]
        evidence = []
        for requirement, permitted_roles in sorted(requirements.items()):
            case_ids = sorted(
                str(case["case_id"])
                for case in retained
                if str(case.get("case_role")) in permitted_roles
            )
            evidence.append(
                {
                    "requirement": requirement,
                    "permitted_case_roles": sorted(permitted_roles),
                    "case_ids": case_ids,
                    "satisfied": bool(case_ids),
                }
            )
        module_results.append(
            {
                "component_id": component_id,
                "component_kind": component_kind,
                "requirements": evidence,
                "complete": all(item["satisfied"] for item in evidence),
            }
        )

    module_results.sort(key=lambda item: (item["component_kind"], item["component_id"]))
    return {
        "record_type": "regression_module_baseline_projection",
        "requirements_version": MODULE_BASELINE_REQUIREMENTS_VERSION,
        "ledger_id": ledger.get("ledger_id"),
        "ledger_digest": ledger.get("ledger_digest"),
        "question_only_correct_arm_policy": (
            "Question-only modules require an applicable case, a matching close negative, and "
            "an unresolved boundary; no scientifically preferred answer is invented."
        ),
        "modules": module_results,
        "complete": all(item["complete"] for item in module_results),
    }


def regression_module_baseline_gaps(ledger: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    """Return each incomplete active component and its exact missing requirement names."""

    projection = regression_module_baseline_projection(ledger)
    return {
        str(module["component_id"]): tuple(
            str(item["requirement"])
            for item in cast(list[dict[str, Any]], module["requirements"])
            if item["satisfied"] is not True
        )
        for module in cast(list[dict[str, Any]], projection["modules"])
        if module["complete"] is not True
    }


def validate_regression_module_baselines(ledger: Mapping[str, Any]) -> dict[str, Any]:
    """Require every active module to satisfy the exact L03 evidence profile."""

    projection = regression_module_baseline_projection(ledger)
    gaps = regression_module_baseline_gaps(ledger)
    if gaps:
        details = "; ".join(
            f"{component_id}: {', '.join(requirements)}"
            for component_id, requirements in sorted(gaps.items())
        )
        raise RegressionModuleBaselineError("Incomplete module regression baselines: " + details)
    return projection


def _object_array(value: object, label: str) -> list[Mapping[str, Any]]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not all(isinstance(item, Mapping) for item in value)
    ):
        raise RegressionModuleBaselineError(f"{label} must be an array of objects.")
    return [cast(Mapping[str, Any], item) for item in value]
