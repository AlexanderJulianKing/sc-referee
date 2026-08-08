"""Soundness controls for the founder-orientation dataflow trace.

The invariant under test: the trace either classifies correctly or abstains;
it never answers wrongly and never crashes. The cardinal rule is that
``direct`` is never a fallthrough. The six differently named transform
shapes below are the wrong-answer family the audit of the retired v1.3.0
adapter found: each one moved an orientation repair onto the panel path
under a name the old vocabulary did not carry, and each one was reported as
the direct orientation.

The v2.0.1 blocks at the end of this module are the counterexamples an
adversarial review of v2.0.0 demonstrated: match-count selectors masking the
real emission, stale provenance surviving alias mutation, reversed
dict-spread precedence, static call resolution ignoring runtime rebinding,
false conditional-repair corroboration, report-plane coincidence, fusion
reversing an abstention, and two crashes. Each block names its finding.
"""

from __future__ import annotations

import ast
from dataclasses import replace

import pytest

from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.parsers.python_ast import PARSER_ID as PYTHON_PARSER_ID
from sc_referee.parsers.python_ast import PARSER_VERSION as PYTHON_PARSER_VERSION
from sc_referee.scientific_checks import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    InspectionDocument,
    RecordRef,
)
from sc_referee.scientific_checks.founder_orientation_adapter import _identified_orientations
from sc_referee.scientific_checks.founder_orientation_dataflow import _document_orientations
from sc_referee.scientific_checks.profiles import default_scientific_check_registry
from sc_referee.scientific_checks.quantity_consistency_adapter import _number_tokens
from sc_referee.scientific_checks.scope_joins import build_static_scope_join_graph

DIRECT = "DIRECT"
REPAIRED = "REPAIRED"
FOUNDER_CHECK = "check:founder-orientation-before-hmm-emission"
DIRECT_OPERAND = "use_supplied_founder_alleles_directly_in_hmm_emission"
REPAIRED_OPERAND = "repair_ril_founder_orientation_before_hmm_emission"

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


def _fused_observation(
    report_text: str, analysis_text: str = "value = 1\n"
) -> tuple[str, str | None]:
    """Run the released founder adapter over one report and one workflow."""

    report = report_text.encode("utf-8")
    analysis = analysis_text.encode("utf-8")
    surface_ref = RecordRef("publication_surface", "publication-surface:soundness")
    artifact_ref = RecordRef("artifact", "artifact:soundness-report")
    identity_ref = RecordRef("asset_identity", "asset-identity:soundness-report")
    report_file_ref = RecordRef("file_record", "file:soundness-report")
    report_parser_ref = RecordRef("parser_result", "parser-result:soundness-report")
    analysis_file_ref = RecordRef("file_record", "file:soundness-analysis")
    analysis_parser_ref = RecordRef("parser_result", "parser-result:soundness-analysis")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:soundness")
    report_parser = canonical_json(
        {
            "parser_id": "parser:markdown-inventory",
            "parser_version": "0.2.0",
            "state": "parsed",
        }
    ).encode("utf-8")
    analysis_parser = canonical_json(
        {
            "parser_id": PYTHON_PARSER_ID,
            "parser_version": PYTHON_PARSER_VERSION,
            "state": "parsed",
        }
    ).encode("utf-8")
    records = (
        (
            surface_ref,
            {
                "publication_surface_id": surface_ref.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact_ref.to_dict()]},
            },
        ),
        (
            artifact_ref,
            {
                "artifact_id": artifact_ref.record_id,
                "kind": "report",
                "path": "report.md",
                "asset_identity_ref": identity_ref.to_dict(),
            },
        ),
        (
            identity_ref,
            {
                "asset_identity_id": identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": artifact_ref.to_dict(),
                "identity_evidence": {"kind": "full_digest", "digest": sha256_digest(report)},
            },
        ),
        (snapshot_ref, {"snapshot_id": snapshot_ref.record_id}),
        (report_file_ref, {"file_record_id": report_file_ref.record_id}),
        (report_parser_ref, {"parser_result_id": report_parser_ref.record_id}),
        (analysis_file_ref, {"file_record_id": analysis_file_ref.record_id}),
        (analysis_parser_ref, {"parser_result_id": analysis_parser_ref.record_id}),
    )
    context = FrozenInspectionContext(
        snapshot_digest=sha256_digest("snapshot"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(
            InspectionDocument(
                path="report.md",
                file_ref=report_file_ref,
                content=report,
                content_digest=sha256_digest(report),
                media_type="text/markdown",
                parser_result_ref=report_parser_ref,
                parser_result_payload=report_parser,
                parser_result_digest=sha256_digest(report_parser),
            ),
            InspectionDocument(
                path="analysis.py",
                file_ref=analysis_file_ref,
                content=analysis,
                content_digest=sha256_digest(analysis),
                media_type="text/x-python",
                parser_result_ref=analysis_parser_ref,
                parser_result_payload=analysis_parser,
                parser_result_digest=sha256_digest(analysis_parser),
            ),
        ),
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in records),
    )
    context = replace(
        context,
        scope_join_graph=build_static_scope_join_graph(
            snapshot_digest=context.snapshot_digest,
            snapshot_ref=snapshot_ref,
            selected_surface_ref=surface_ref,
            selected_artifact_ref=artifact_ref,
            documents=context.documents,
            base_records=context.base_records,
        ),
    )
    module = next(
        item
        for item in default_scientific_check_registry().modules
        if item.manifest.check_id == FOUNDER_CHECK
    )
    observation = module.adapters[0].inspect(context)
    operand = observation.observed_operand
    return observation.applicability, None if operand is None else str(operand.value)


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
# Conditional repair, dropped in v2.0.1 (review finding 5).
#
# v2.0.0 read a guard that compared two panel columns as proof that the repair
# inside it ran. It is not proof: the branch also depends on every other
# conjunct and on the measured outcome, neither of which a static reading
# settles. Every guarded rebinding of a row set now leaves the document
# unsupported.

_CROSS_PANEL_GUARD = (
    "if sum(1 for row in rows if int(row['call']) == int(row['founder'])) * 2 < len(rows):\n"
    "    rows = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
)
_UNRELATED_GUARD = (
    "if len(rows) > 10:\n    rows = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
)
_DEAD_CONJUNCT_GUARD = (
    "agreement = sum(1 for row in rows if int(row['call']) == int(row['founder']))\n"
    "enable_repair = False\n"
    "if enable_repair and agreement * 2 < len(rows):\n"
    "    rows = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
)
_STORED_COUNT_GUARD = (
    "agreement = sum(1 for row in rows if int(row['call']) == int(row['founder']))\n"
    "if agreement * 2 < len(rows):\n"
    "    rows = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
)


@pytest.mark.parametrize(
    "guard",
    [_CROSS_PANEL_GUARD, _UNRELATED_GUARD, _DEAD_CONJUNCT_GUARD, _STORED_COUNT_GUARD],
)
def test_every_guarded_row_set_rebinding_abstains(guard: str) -> None:
    unsupported, _states = _resolve(_workflow(guard))
    assert unsupported


def test_a_conditional_expression_choosing_between_row_sets_abstains() -> None:
    """The conditional-expression form of the same branch abstains too."""

    source = _workflow(
        "repaired = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        "enable_repair = False\n"
        "panel = repaired if enable_repair else rows\n",
        source="panel",
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def test_a_guard_on_two_columns_of_one_staged_origin_abstains() -> None:
    """Distinct output column names do not make a guard a cross-panel test."""

    source = _workflow(
        "paired = [\n"
        "    {'left': int(row['founder']), 'right': int(row['founder']), "
        "'call': int(row['call']), 'founder': int(row['founder'])}\n"
        "    for row in rows\n"
        "]\n"
        "if any(int(p['left']) != int(p['right']) for p in paired):\n"
        "    paired = [{**p, 'founder': 1 - int(p['founder'])} for p in paired]\n",
        source="paired",
    )
    unsupported, _states = _resolve(source)
    assert unsupported


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


# ---------------------------------------------------------------------------
# v2.0.1 controls: every counterexample the adversarial review of v2.0.0
# demonstrated. Each block names the review finding it closes.


_STDLIB_HEAD = """import csv
import io
import itertools
import math
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
"""


def _fraction_emission(source: str) -> str:
    return (
        "likelihood = math.prod(\n"
        "    Fraction(99, 100)\n"
        "    if int(row['call']) == int(row['founder'])\n"
        f"    else Fraction(1, 100) for row in {source}\n"
        ")\n"
    )


def _match_count(source: str) -> str:
    return (
        "agreement = sum(\n"
        f"    1 if int(row['call']) == int(row['founder']) else 0 for row in {source}\n"
        ")\n"
    )


_FUSED_TAIL = "report = f'{agreement} {likelihood}'\nPath('results/report.md').write_text(report)\n"


# --- Finding 1: match-count selectors masking the real emission selector ----


@pytest.mark.parametrize(
    ("count_source", "emission_source"),
    [("rows", "panel"), ("panel", "rows")],
)
def test_a_match_count_cannot_answer_for_a_differently_sourced_emission(
    count_source: str, emission_source: str
) -> None:
    """Two report-reaching comparisons over differently oriented panels conflict.

    v2.0.0 read the ``Fraction`` selector as non-numeric, skipped the real
    emission, and let the match count answer in its place -- once for each
    orientation, depending on which panel each read.
    """

    source = (
        _STDLIB_HEAD
        + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + _match_count(count_source)
        + _fraction_emission(emission_source)
        + _FUSED_TAIL
    )
    _unsupported, states = _resolve(source)
    assert states == {"direct", "repaired"}


@pytest.mark.parametrize(
    "selector",
    ["Fraction(99, 100)", "Decimal('0.99')", "Decimal(0.99)", "Fraction(99, 100) * 1"],
)
def test_stdlib_exact_probability_selectors_are_emission_selectors(selector: str) -> None:
    """An ordinary stdlib probability is a recognized emission selector."""

    source = (
        _STDLIB_HEAD
        + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + "likelihood = math.prod(\n"
        + f"    {selector} if int(row['call']) == int(row['founder']) else 0.01\n"
        + "    for row in panel\n"
        + ")\n"
        + "report = f'emission likelihood {likelihood}'\n"
        + "Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"repaired"}


def test_an_unreadable_emission_selector_abstains_for_the_whole_document() -> None:
    """An unreadable selector can no longer be skipped in silence.

    The element still compares two staged columns, so it is an emission
    comparison whatever it selects between; skipping it would leave the match
    count over the other panel as the only answer.
    """

    source = (
        _STDLIB_HEAD
        + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + _match_count("rows")
        + "likelihood = math.prod(\n"
        + "    emit(0.99) if int(row['call']) == int(row['founder']) else emit(0.01)\n"
        + "    for row in panel\n"
        + ")\n"
        + _FUSED_TAIL
    )
    unsupported, _states = _resolve(source)
    assert unsupported


def test_a_column_dictionary_pipeline_abstains() -> None:
    """A dictionary of columns consumed by ``zip`` is not a traceable row set."""

    source = (
        _STDLIB_HEAD
        + _match_count("rows")
        + "columns = {'call': [], 'founder': []}\n"
        + "pairs = list(zip(columns['call'], columns['founder']))\n"
        + "likelihood = math.prod(\n"
        + "    Fraction(99, 100) if pair[0] == pair[1] else Fraction(1, 100) for pair in pairs\n"
        + ")\n"
        + _FUSED_TAIL
    )
    unsupported, _states = _resolve(source)
    assert unsupported


def test_an_itertools_chain_pipeline_abstains() -> None:
    """``itertools.chain`` hides which panel reaches the emission."""

    source = (
        _STDLIB_HEAD
        + _match_count("rows")
        + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + "merged = list(itertools.chain(panel))\n"
        + "likelihood = math.prod(\n"
        + "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in merged\n"
        + ")\n"
        + _FUSED_TAIL
    )
    unsupported, _states = _resolve(source)
    assert unsupported


# --- Finding 2: alias mutation and unhandled assignment forms --------------


def test_mutating_a_row_set_through_an_alias_invalidates_every_name() -> None:
    """``alias = rows`` binds one runtime list to two names.

    Clearing and refilling through the alias makes ``rows`` the repaired
    panel at run time, while v2.0.0 kept ``rows`` tagged as the staged read
    and reported the direct orientation.
    """

    source = _workflow(
        "repaired = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        "alias = rows\n"
        "alias.clear()\n"
        "alias.extend(repaired)\n"
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def test_mutating_a_repaired_panel_through_an_alias_invalidates_it_too() -> None:
    source = _workflow(
        "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        "alias = panel\n"
        "alias.clear()\n"
        "alias.extend(rows)\n",
        source="panel",
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


@pytest.mark.parametrize(
    "assignment",
    [
        "rows[:] = repaired",
        "rows, unused = (repaired, None)",
        "rows = panel = repaired",
        "rows += repaired",
        "rows = (staged := repaired)",
        "rows: list = repaired",
    ],
)
def test_assignment_forms_the_environment_cannot_follow_abstain(assignment: str) -> None:
    """Any binding form the environment model does not handle abstains.

    v2.0.0 ignored these forms outright, so the name kept the provenance of
    whatever it held before, and a repaired workflow read as direct.
    """

    source = _workflow(
        "repaired = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + assignment
        + "\n"
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def test_deleting_from_an_aliased_row_set_invalidates_every_name() -> None:
    source = _workflow("alias = rows\ndel alias[0]\n")
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


# --- Finding 3: dict-spread precedence -------------------------------------


def test_a_spread_after_an_explicit_key_overrides_that_key() -> None:
    """``{'founder': 1 - x, **row}`` is the staged panel, not the repair.

    Python applies dict entries left to right, so the later spread wins.
    v2.0.0 applied every explicit entry after every spread and read this as
    a repair.
    """

    source = _workflow(
        "panel = [{'founder': 1 - int(row['founder']), **row} for row in rows]\n",
        source="panel",
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"direct"}


def test_a_spread_after_an_explicit_key_carries_the_spread_orientation() -> None:
    """The same expression over an already repaired panel stays repaired."""

    source = _workflow(
        "once = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        "panel = [{'founder': 1 - int(row['founder']), **row} for row in once]\n",
        source="panel",
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"repaired"}


def test_a_spread_that_may_not_carry_the_key_leaves_it_opaque() -> None:
    """A later spread whose contents do not settle the key wins nothing.

    ``narrow`` carries no founder column this trace knows about, so whether
    the spread overwrites the explicit entry is a run-time question.
    """

    source = _workflow(
        "narrow = [{'call': int(row['call'])} for row in rows]\n"
        "panel = [{'founder': 1 - int(item['call']), **item} for item in narrow]\n",
        source="panel",
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


# --- Finding 4: static call resolution vs runtime rebinding ----------------


def test_a_local_definition_shadows_the_reader_vocabulary() -> None:
    """A project helper named ``reader`` is read from its body, not its name."""

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "def reader(handle):\n"
        "    raw = csv.DictReader(handle)\n"
        "    return [\n"
        "        {**row, 'founder': 1 - int(row['founder'])}\n"
        "        for row in raw\n"
        "    ]\n\n"
        "rows = list(reader(Path('inputs/markers.csv').open()))\n" + _emission("rows") + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"repaired"}


def test_a_rebound_callable_name_is_opaque_everywhere() -> None:
    """``recode = flip if enabled else recode`` decides at run time."""

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "def recode(x):\n    return x\n\n"
        "def flip(x):\n    return x ^ 1\n\n"
        "enabled = True\n"
        "recode = flip if enabled else recode\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': recode(int(row['founder']))} for row in rows]\n"
        + _emission("panel")
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def test_a_helper_with_a_walrus_binding_abstains() -> None:
    """``(x := x ^ 1); return x`` rebinds through a statement v2.0.0 ignored."""

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "def fix(x):\n    (x := x ^ 1)\n    return x\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': fix(int(row['founder']))} for row in rows]\n"
        + _emission("panel")
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def test_a_helper_with_statements_after_its_return_abstains() -> None:
    """Dead code after the first return no longer contributes a parity."""

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "def fix(x):\n    y = x\n    return y\n    y = x ^ 1\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': fix(int(row['founder']))} for row in rows]\n"
        + _emission("panel")
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def test_a_helper_with_a_side_effecting_statement_abstains() -> None:
    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "def fix(x):\n    log(x)\n    return 1 - x\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': fix(int(row['founder']))} for row in rows]\n"
        + _emission("panel")
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


# --- Finding 7 tail: report reachability -----------------------------------


def test_a_write_into_an_in_memory_buffer_does_not_reach_the_report() -> None:
    """``io.StringIO().write`` answers to the same method name as a file."""

    source = (
        _STDLIB_HEAD
        + _emission("rows")
        + "buffer = io.StringIO()\n"
        + "buffer.write(f'{likelihood}')\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == set()


def test_an_in_memory_diagnostic_cannot_answer_for_the_written_emission() -> None:
    """The real report used an unreadable selector; the buffer got the clean one."""

    source = (
        _STDLIB_HEAD
        + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + "likelihood = math.prod(\n"
        + "    emit(0.99) if int(row['call']) == int(row['founder']) else emit(0.01)\n"
        + "    for row in panel\n"
        + ")\n"
        + "Path('results/report.md').write_text(f'{likelihood}')\n"
        + "diagnostic = math.prod(\n"
        + "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in rows\n"
        + ")\n"
        + "buffer = io.StringIO()\n"
        + "buffer.write(f'{diagnostic}')\n"
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def test_a_return_from_a_function_nobody_calls_does_not_reach_the_report() -> None:
    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n\n"
        "def diagnostic():\n"
        "    likelihood = math.prod(\n"
        "        0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in rows\n"
        "    )\n"
        "    return likelihood\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == set()


def test_a_return_from_a_called_function_still_reaches_the_report() -> None:
    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n\n"
        "def emission():\n"
        "    return math.prod(\n"
        "        0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in rows\n"
        "    )\n\n"
        "likelihood = emission()\n" + _TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"direct"}


# --- Finding 8: crash bounds ------------------------------------------------


def test_a_deeply_composed_recode_abstains_without_recursion_error() -> None:
    """1,100 composed inversions exhausted the interpreter stack in v2.0.0."""

    source = _workflow(
        "panel = [{**row, 'founder': int(row['founder'])" + " ^ 1" * 1100 + "} for row in rows]\n",
        source="panel",
    )
    unsupported, states = _resolve(source)
    assert states == set()
    assert unsupported


def test_a_deeply_composed_selector_abstains_without_recursion_error() -> None:
    source = (
        _HEAD
        + "likelihood = math.prod(\n"
        + "    (0.99"
        + " * 1" * 1100
        + ")\n"
        + "    if int(row['call']) == int(row['founder'])\n"
        + "    else 0.01\n"
        + "    for row in rows\n"
        + ")\n"
        + _TAIL
    )
    unsupported, states = _resolve(source)
    assert states == set() or states == {"direct"}
    assert unsupported or states == {"direct"}


def test_a_report_with_an_astronomically_large_integer_is_scanned_without_crashing() -> None:
    """A 400-digit integer raised ``OverflowError`` inside the v2.0.0 bound."""

    text = (
        "The parental marker panel and the progeny calls were compared marker by marker: "
        "372 of the 480 markers agree. A run identifier of " + "9" * 400 + " was recorded.\n\n"
        "The emission model used a per-marker agreement rate of 0.775.\n"
    )
    assert _report_operands(text) == {DIRECT}


# ---------------------------------------------------------------------------
# Findings 6 and 7: the report plane is demoted.
#
# Three free numbers joined by one ratio reconcile with an orientation by
# coincidence, and no amount of report arithmetic separates a founder
# accounting from a sensitivity, a specificity, or a repeat rate. From v2.0.1
# the report plane can corroborate, contradict, or stay silent -- it can never
# resolve on its own, and it can never reverse an abstaining workflow.

_DIRECT_REPORT = (
    "The parental marker panel and the progeny calls were compared marker by marker: "
    "372 of the 480 markers agree.\n\n"
    "The emission model used a per-marker agreement rate of 0.775.\n"
)
_COMPLEMENT_REPORT = (
    "The parental marker panel and the progeny calls were compared marker by marker: "
    "372 of the 480 markers agree.\n\n"
    "The emission model used a per-marker agreement rate of 0.225.\n"
)
_DIRECT_WORKFLOW = _HEAD + _emission("rows") + _TAIL
_REPAIRED_WORKFLOW = (
    _HEAD
    + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
    + _emission("panel")
    + _TAIL
)


@pytest.mark.parametrize(
    "report_text",
    [
        "Of 100 cases, 90 were true positives; the sensitivity is 0.90.\n",
        "Of 100 cases, 90 were true negatives; the false-positive rate is 0.10.\n",
        "Of 100 cases, 90 informed both a sensitivity of 0.90 and a specificity of 0.90.\n",
        "Of 100 cases, 90 agreed: a rate of 0.90, or 90%.\n",
        "Of 100 cases, 90 agreed at 0.90 while 10% did not.\n",
        "Of 100 cases, 90 agreed and 10 did not.\n",
        "Of 100 cases, 50 agreed; the rate is 0.50.\n",
        "The study used 2 cohorts and 5 batches; the convergence threshold was 0.123.\n",
    ],
)
def test_a_report_alone_never_resolves_the_founder_orientation(report_text: str) -> None:
    """Ordinary non-founder accountings no longer produce an observation."""

    applicability, operand = _fused_observation(report_text)
    assert applicability == "not_applicable"
    assert operand is None


@pytest.mark.parametrize(
    ("report_text", "workflow", "expected_operand"),
    [
        (_DIRECT_REPORT, _DIRECT_WORKFLOW, DIRECT_OPERAND),
        (_COMPLEMENT_REPORT, _REPAIRED_WORKFLOW, REPAIRED_OPERAND),
    ],
)
def test_a_report_corroborating_the_workflow_resolves(
    report_text: str, workflow: str, expected_operand: str
) -> None:
    applicability, operand = _fused_observation(report_text, workflow)
    assert applicability == "applicable"
    assert operand == expected_operand


@pytest.mark.parametrize(
    ("report_text", "workflow"),
    [
        (_DIRECT_REPORT, _REPAIRED_WORKFLOW),
        (_COMPLEMENT_REPORT, _DIRECT_WORKFLOW),
    ],
)
def test_a_report_contradicting_the_workflow_abstains(report_text: str, workflow: str) -> None:
    applicability, operand = _fused_observation(report_text, workflow)
    assert applicability == "ambiguous"
    assert operand is None


def test_a_silent_report_with_a_reconciling_accounting_resolves_on_the_workflow() -> None:
    """Both rates reconcile with one accounting, so only the workflow decides."""

    report_text = (
        "Of the 480 markers, 372 agree; the per-marker agreement rate is 0.775 and its "
        "complement is 0.225.\n"
    )
    assert _fused_observation(report_text, _DIRECT_WORKFLOW) == ("applicable", DIRECT_OPERAND)
    assert _fused_observation(report_text, _REPAIRED_WORKFLOW) == (
        "applicable",
        REPAIRED_OPERAND,
    )


def test_a_resolved_workflow_without_any_reconciling_accounting_is_not_applicable() -> None:
    """Nothing published turns on the orientation, so there is nothing to review."""

    report_text = (
        "The parental marker panel and the progeny calls were compared marker by marker: "
        "372 of the 480 markers agree.\n\n"
        "The selected emission log-likelihood ratio is 0.31.\n"
    )
    assert _fused_observation(report_text, _DIRECT_WORKFLOW) == ("not_applicable", None)


def test_an_unsupported_workflow_is_not_reversed_by_a_reconciling_report() -> None:
    """``return (x + 1) % 2`` is a repair this trace cannot read."""

    workflow = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "def recode(x):\n    return (x + 1) % 2\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': recode(int(row['founder']))} for row in rows]\n"
        + _emission("panel")
        + _TAIL
    )
    assert _fused_observation(_DIRECT_REPORT, workflow) == ("unsupported", None)


def test_an_unreadable_emission_selector_is_not_reversed_by_an_unrelated_report() -> None:
    workflow = (
        _HEAD
        + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + "likelihood = math.prod(\n"
        + "    emit(0.99) if int(row['call']) == int(row['founder']) else emit(0.01)\n"
        + "    for row in panel\n"
        + ")\n"
        + _TAIL
    )
    report_text = "Of 100 cases, 90 were true positives; the sensitivity is 0.90.\n"
    assert _fused_observation(report_text, workflow) == ("unsupported", None)


def test_an_alias_mutated_workflow_is_not_reversed_by_two_stray_integers() -> None:
    workflow = _workflow(
        "repaired = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        "alias = rows\n"
        "alias.clear()\n"
        "alias.extend(repaired)\n"
    )
    report_text = "The study used 2 cohorts and 5 batches; the convergence threshold was 0.123.\n"
    assert _fused_observation(report_text, workflow) == ("unsupported", None)


def test_conflicting_workflow_comparisons_abstain_as_ambiguous() -> None:
    workflow = (
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
    assert _fused_observation(_DIRECT_REPORT, workflow) == ("ambiguous", None)
