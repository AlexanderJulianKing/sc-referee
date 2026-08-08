"""Soundness controls for the founder-orientation dataflow trace.

The invariant under test: the trace either classifies correctly or abstains;
it never answers wrongly and never crashes. The cardinal rule is that
``direct`` is never a fallthrough. The six differently named transform
shapes below are the wrong-answer family the audit of the retired v1.3.0
adapter found: each one moved an orientation repair onto the panel path
under a name the old vocabulary did not carry, and each one was reported as
the direct orientation.
"""

from __future__ import annotations

import ast

import pytest

from sc_referee.scientific_checks.founder_orientation_adapter import _identified_orientations
from sc_referee.scientific_checks.founder_orientation_dataflow import _document_orientations
from sc_referee.scientific_checks.quantity_consistency_adapter import _number_tokens

DIRECT = "DIRECT"
REPAIRED = "REPAIRED"

_HEAD = """import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
"""
_TAIL = """report = f'emission likelihood {likelihood}'
Path('results/report.md').write_text(report)
"""


def _emission(source: str) -> str:
    return (
        "likelihood = math.prod(\n"
        f"    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in {source}\n"
        ")\n"
    )


def _workflow(body: str, *, source: str = "rows") -> str:
    return _HEAD + body + _emission(source) + _TAIL


def _resolve(source: str) -> tuple[bool, set[str]]:
    outcome = _document_orientations(ast.parse(source))
    return outcome["unsupported"], {item.state for item in outcome["classifications"]}


def _assert_never_direct(source: str) -> set[str]:
    unsupported, states = _resolve(source)
    assert "direct" not in states
    assert states in ({"repaired"}, set())
    if not states:
        assert unsupported
    return states


def _report_operands(text: str) -> set[str]:
    tokens = _number_tokens(text)
    integers = [item for item in tokens if item.is_integer and not item.is_percent]
    rates = [item for item in tokens if not item.is_integer or item.is_percent]
    found, _conflicted = _identified_orientations(
        integers, rates, direct_operand=DIRECT, repaired_operand=REPAIRED
    )
    return {item.operand_value for item in found}


# ---------------------------------------------------------------------------
# The wrong-answer family: differently named involutive transforms.

_LOADER = """
def load_panel(path):
    return list(csv.DictReader(Path(path).open()))
"""


def _named_transform_workflow(definition: str, call: str) -> str:
    return (
        "import csv\nimport math\nfrom pathlib import Path\n"
        + _LOADER
        + definition
        + f"\npanel = {call}\n"
        + _emission("panel")
        + _TAIL
    )


WRONG_ANSWER_SHAPES = {
    "swap_alleles": (
        "def swap_alleles(panel):\n"
        "    return [{**row, 'founder': 1 - int(row['founder'])} for row in panel]\n",
        "swap_alleles(load_panel('inputs/markers.csv'))",
    ),
    "reorient": (
        "def reorient(panel):\n"
        "    return [{**row, 'founder': int(row['founder']) ^ 1} for row in panel]\n",
        "reorient(load_panel('inputs/markers.csv'))",
    ),
    "harmonise": (
        "def harmonise(panel):\n"
        "    return [{**row, 'founder': abs(int(row['founder']) - 1)} for row in panel]\n",
        "harmonise(load_panel('inputs/markers.csv'))",
    ),
    "polarize": (
        "def polarize(panel):\n"
        "    return [{**row, 'founder': {0: 1, 1: 0}[int(row['founder'])]} for row in panel]\n",
        "polarize(load_panel('inputs/markers.csv'))",
    ),
    "orient_two_argument": (
        "def orient(panel, reference):\n"
        "    return [{**row, 'founder': 1 - int(row['founder'])} for row in panel]\n",
        "orient(load_panel('inputs/markers.csv'), 'reference-a')",
    ),
    "orient_keyword": (
        "def orient(x):\n    return [{**row, 'founder': 1 - int(row['founder'])} for row in x]\n",
        "orient(x=load_panel('inputs/markers.csv'))",
    ),
}


@pytest.mark.parametrize("shape", sorted(WRONG_ANSWER_SHAPES))
def test_named_orientation_transforms_are_never_read_as_direct(shape: str) -> None:
    definition, call = WRONG_ANSWER_SHAPES[shape]
    assert _assert_never_direct(_named_transform_workflow(definition, call)) == {"repaired"}


def test_transform_whose_body_is_not_in_the_repository_abstains() -> None:
    """A helper defined nowhere the trace can read is not the direct orientation."""

    source = _named_transform_workflow("", "swap_alleles(load_panel('inputs/markers.csv'))")
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def test_unrecognized_column_arithmetic_abstains() -> None:
    source = _workflow(
        "panel = [{**row, 'founder': recode(row['founder'])} for row in rows]\n",
        source="panel",
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


# ---------------------------------------------------------------------------
# Recognized involutive forms.


@pytest.mark.parametrize(
    "expression",
    [
        "1 - int(row['founder'])",
        "int(row['founder']) ^ 1",
        "1 ^ int(row['founder'])",
        "abs(int(row['founder']) - 1)",
        "abs(1 - int(row['founder']))",
        "int(not int(row['founder']))",
        "1 if int(row['founder']) == 0 else 0",
        "0 if int(row['founder']) == 1 else 1",
        "{0: 1, 1: 0}[int(row['founder'])]",
        "[1, 0][int(row['founder'])]",
        "(1, 0)[int(row['founder'])]",
    ],
)
def test_each_involutive_recode_form_is_a_repair(expression: str) -> None:
    source = _workflow(
        "panel = [{**row, 'founder': " + expression + "} for row in rows]\n", source="panel"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"repaired"}


@pytest.mark.parametrize(
    "expression",
    [
        "int(row['founder'])",
        "row['founder'].strip()",
        "0 if int(row['founder']) == 0 else 1",
        "{0: 0, 1: 1}[int(row['founder'])]",
        "[0, 1][int(row['founder'])]",
    ],
)
def test_each_identity_preserving_form_stays_direct(expression: str) -> None:
    source = _workflow(
        "panel = [{**row, 'founder': " + expression + "} for row in rows]\n", source="panel"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"direct"}


def test_helper_function_repair_under_its_own_naming_is_a_repair() -> None:
    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "def fix(v):\n    return 1 - v\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': fix(int(row['founder']))} for row in rows]\n"
        + _emission("panel")
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"repaired"}


def test_recursive_helper_abstains_instead_of_crashing() -> None:
    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "def fix(v):\n    return fix(1 - v)\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': fix(int(row['founder']))} for row in rows]\n"
        + _emission("panel")
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def test_loop_built_repaired_panel_is_a_repair() -> None:
    source = _workflow(
        "panel = []\n"
        "for row in rows:\n"
        "    panel.append({**row, 'founder': 1 - int(row['founder'])})\n",
        source="panel",
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"repaired"}


def test_accumulation_loop_emission_classifies() -> None:
    source = (
        _HEAD
        + "likelihood = 1.0\n"
        + "for row in rows:\n"
        + "    likelihood = likelihood * (\n"
        + "        0.99 if int(row['call']) == int(row['founder']) else 0.01\n"
        + "    )\n"
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"direct"}


def test_two_element_probability_container_indexed_by_the_comparison_classifies() -> None:
    source = (
        _HEAD
        + "likelihood = math.prod(\n"
        + "    [0.01, 0.99][int(row['call']) == int(row['founder'])] for row in rows\n"
        + ")\n"
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"direct"}


# ---------------------------------------------------------------------------
# Parity boundaries.


def test_a_joint_flip_of_both_operands_is_not_a_repair() -> None:
    """Complementing both panels leaves every comparison unchanged."""

    source = _workflow(
        "panel = [\n"
        "    {'call': 1 - int(row['call']), 'founder': 1 - int(row['founder'])} for row in rows\n"
        "]\n",
        source="panel",
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"direct"}


def test_a_joint_flip_with_one_unreadable_side_abstains() -> None:
    source = _workflow(
        "panel = [\n"
        "    {'call': recode(row['call']), 'founder': 1 - int(row['founder'])} for row in rows\n"
        "]\n",
        source="panel",
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def test_two_recognized_flips_on_one_path_compose_to_the_direct_reading() -> None:
    source = _workflow(
        "once = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        "twice = [{**row, 'founder': 1 - int(row['founder'])} for row in once]\n",
        source="twice",
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"direct"}


def test_two_flips_on_one_path_abstain_when_the_second_is_unreadable() -> None:
    source = _workflow(
        "once = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        "twice = [{**row, 'founder': recode(row['founder'])} for row in once]\n",
        source="twice",
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def test_an_off_path_mask_flip_does_not_change_the_classification() -> None:
    source = _workflow("mask = [1 - int(row['flag']) for row in rows]\n")
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"direct"}


def test_a_diagnostic_flip_that_never_reaches_the_report_is_ignored() -> None:
    source = (
        _HEAD
        + "flipped = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + "diagnostic = math.prod(\n"
        + "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in flipped\n"
        + ")\n"
        + _emission("rows")
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"direct"}


def test_an_emission_that_never_reaches_the_report_never_classifies() -> None:
    source = (
        _HEAD + _emission("rows") + "Path('results/report.md').write_text('a static summary')\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == set()


def test_conflicting_report_reaching_emissions_abstain() -> None:
    source = (
        _HEAD
        + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + "supplied = math.prod(\n"
        + "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in rows\n"
        + ")\n"
        + "repaired = math.prod(\n"
        + "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in panel\n"
        + ")\n"
        + "report = f'{supplied} {repaired}'\n"
        + "Path('results/report.md').write_text(report)\n"
    )
    _unsupported, states = _resolve(source)
    assert states == {"direct", "repaired"}


def test_a_column_compared_with_itself_is_not_an_emission_comparison() -> None:
    source = (
        _HEAD
        + "likelihood = math.prod(\n"
        + "    0.99 if int(row['founder']) == int(row['founder']) else 0.01 for row in rows\n"
        + ")\n"
        + _TAIL
    )
    _unsupported, states = _resolve(source)
    assert states == set()


def test_a_mutated_row_set_loses_its_staged_provenance() -> None:
    source = _HEAD + "rows.pop()\n" + _emission("rows") + _TAIL
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


# ---------------------------------------------------------------------------
# Conditional repair.

_CROSS_PANEL_GUARD = (
    "if sum(1 for row in rows if int(row['call']) == int(row['founder'])) * 2 < len(rows):\n"
    "    rows = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
)
_UNRELATED_GUARD = (
    "if len(rows) > 10:\n    rows = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
)


def test_a_repair_guarded_by_a_cross_panel_comparison_is_a_repair() -> None:
    unsupported, states = _resolve(_workflow(_CROSS_PANEL_GUARD))
    assert not unsupported
    assert states == {"repaired"}


def test_a_repair_guarded_by_anything_else_abstains() -> None:
    """An unrecognized branch leaves the whole document unsupported."""

    unsupported, _states = _resolve(_workflow(_UNRELATED_GUARD))
    assert unsupported


def test_a_repair_guarded_by_a_stored_cross_panel_count_is_a_repair() -> None:
    body = (
        "agreement = sum(1 for row in rows if int(row['call']) == int(row['founder']))\n"
        "if agreement * 2 < len(rows):\n"
        "    rows = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
    )
    unsupported, states = _resolve(_workflow(body))
    assert not unsupported
    assert states == {"repaired"}


# ---------------------------------------------------------------------------
# The report plane.


def test_report_complement_arithmetic_is_recognized() -> None:
    text = (
        "The parental marker panel as supplied and the progeny calls were compared marker by "
        "marker: 372 of the 480 markers agree.\n\n"
        "The emission model used a per-marker agreement rate of 0.225.\n"
    )
    assert _report_operands(text) == {REPAIRED}


def test_report_direct_arithmetic_is_recognized() -> None:
    text = (
        "The parental marker panel and the progeny calls were compared marker by marker: "
        "372 of the 480 markers agree.\n\n"
        "The emission model used a per-marker agreement rate of 0.775.\n"
    )
    assert _report_operands(text) == {DIRECT}


def test_report_percent_marked_complement_arithmetic_is_recognized() -> None:
    text = "Of 480 markers, 372 agree; the emission used a 22.5% per-marker agreement rate.\n"
    assert _report_operands(text) == {REPAIRED}


def test_report_half_agreement_degeneracy_is_silent() -> None:
    """At 240 of 480 both orientations reconcile with the same rate."""

    text = (
        "The parental marker panel and the progeny calls were compared marker by marker: "
        "240 of the 480 markers agree.\n\n"
        "The emission model used a per-marker agreement rate of 0.5.\n"
    )
    assert _report_operands(text) == set()


def test_report_without_a_reconciling_rate_is_silent() -> None:
    text = (
        "The parental marker panel and the progeny calls were compared marker by marker: "
        "372 of the 480 markers agree.\n\n"
        "The selected emission log-likelihood ratio is 0.31.\n"
    )
    assert _report_operands(text) == set()


def test_report_with_two_reconciling_accountings_identifies_neither() -> None:
    """Three free numbers joined by one ratio reconcile by coincidence."""

    text = (
        "Of 150 assay wells, 6 were repeats; of 250 roster rows, 10 were repeats. "
        "The reported rate is 0.04.\n"
    )
    assert _report_operands(text) == set()


def test_emission_inside_a_helper_with_a_parameter_row_set_abstains() -> None:
    """A function body is traced with its parameters masked, so the staged read
    is out of scope and the comparison cannot be resolved either way."""

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "def emission(panel):\n"
        "    return math.prod(\n"
        "        0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in panel\n"
        "    )\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "likelihood = emission(rows)\n" + _TAIL
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported
