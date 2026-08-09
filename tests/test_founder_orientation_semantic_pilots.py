"""Permanent v3 regression over all five founder pilots and ten controls."""

from __future__ import annotations

from pathlib import Path

import pytest

from sc_referee.parsers.python_ast import PARSER_ID as PYTHON_PARSER_ID
from sc_referee.parsers.python_ast import PARSER_VERSION as PYTHON_PARSER_VERSION
from sc_referee.scientific_checks.founder_orientation_semantic import (
    resolve_founder_orientation_semantic,
)
from sc_referee.scientific_checks.profiles import scientific_check_release_registry
from tests.test_founder_pilot_burned_case_regression import (
    CASES,
    CASES_B,
    CASES_C,
    CASES_D,
    CONTROLS,
    CONTROLS_B,
    CONTROLS_C,
    CONTROLS_D,
    DIRECT_OPERAND,
    ERROR_BEARING,
    ERROR_BEARING_B,
    ERROR_BEARING_C,
    ERROR_BEARING_D,
    FOUNDER_CHECK,
    REPAIRED_OPERAND,
    _case_context,
    _inspection_context,
)

CASES_E = Path(
    "evaluation/qualification/founder-orientation-before-hmm-emission-v2.2.6-lane/"
    "pilot-e/authoring/cases"
)
ERROR_BEARING_E = "fa196cf85ce845a1c7c5"
CONTROLS_E = ("451fb08825730b6e453b", "0d34701fd3b3847d3e22")
REPORT_PATH = Path("results/report.md")
WORKFLOW_PATH = Path("workflow/analysis.py")

PILOTS = (
    (CASES, ERROR_BEARING, CONTROLS),
    (CASES_B, ERROR_BEARING_B, CONTROLS_B),
    (CASES_C, ERROR_BEARING_C, CONTROLS_C),
    (CASES_D, ERROR_BEARING_D, CONTROLS_D),
    (CASES_E, ERROR_BEARING_E, CONTROLS_E),
)


def _context(project_root: Path, cases: Path, slug: str):
    if cases != CASES_E:
        return _case_context(project_root, slug, cases)
    case = project_root / cases / slug
    return _inspection_context(
        (case / REPORT_PATH).read_bytes(), (case / WORKFLOW_PATH).read_bytes()
    )


def _resolution(context):
    return resolve_founder_orientation_semantic(
        context,
        direct_operand=DIRECT_OPERAND,
        repaired_operand=REPAIRED_OPERAND,
        parser_id=PYTHON_PARSER_ID,
        parser_version=PYTHON_PARSER_VERSION,
    )


def _v3_observation(context):
    registry = scientific_check_release_registry()
    module = next(item for item in registry.modules if item.manifest.check_id == FOUNDER_CHECK)
    adapter = next(item for item in module.adapters if item.adapter_version == "3.0.1")
    observation = adapter.inspect(context)
    return (
        observation.applicability,
        None if observation.observed_operand is None else str(observation.observed_operand.value),
    )


@pytest.mark.parametrize(("cases", "slug", "_controls"), PILOTS)
def test_all_five_error_bearing_pilots_abstain_without_a_proved_csv_domain(
    project_root: Path, cases: Path, slug: str, _controls: tuple[str, ...]
) -> None:
    context = _context(project_root, cases, slug)
    resolution = _resolution(context)
    assert resolution.state != "unique"
    assert resolution.orientation is None
    assert resolution.operand_value is None
    assert resolution.certificate is None
    assert _v3_observation(context) == ("unsupported", None)


CONTROL_CASES = tuple(
    (cases, control) for cases, _error, controls in PILOTS for control in controls
)


@pytest.mark.parametrize(("cases", "slug"), CONTROL_CASES)
def test_all_ten_controls_never_emit_the_repaired_operand(
    project_root: Path, cases: Path, slug: str
) -> None:
    context = _context(project_root, cases, slug)
    resolution = _resolution(context)
    assert resolution.orientation != "repaired"
    applicability, operand = _v3_observation(context)
    assert operand != REPAIRED_OPERAND
    assert applicability != "applicable" or operand == DIRECT_OPERAND


@pytest.mark.parametrize(
    ("cases", "slug"),
    tuple((cases, slug) for cases, error, controls in PILOTS for slug in (error, *controls)),
)
def test_all_fifteen_v3_pilot_answers_are_deterministic(
    project_root: Path, cases: Path, slug: str
) -> None:
    context = _context(project_root, cases, slug)
    assert _resolution(context) == _resolution(context)
    assert _v3_observation(context) == _v3_observation(context)


def test_shadow_wiring_keeps_v2_and_v3_as_independent_adapters() -> None:
    registry = scientific_check_release_registry()
    module = next(item for item in registry.modules if item.manifest.check_id == FOUNDER_CHECK)
    identities = {(item.adapter_id, item.adapter_version) for item in module.adapters}
    assert identities == {
        (
            "adapter:founder-orientation-before-hmm-emission:orientation-dataflow-v1",
            "2.2.6",
        ),
        (
            "adapter:founder-orientation-before-hmm-emission:orientation-semantic-v3",
            "3.0.1",
        ),
    }
