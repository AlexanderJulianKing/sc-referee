"""Soundness controls for the founder-orientation dataflow trace.

The invariant under test: the trace either classifies correctly or abstains;
it never answers wrongly and never crashes. The cardinal rule is that
``direct`` is never a fallthrough. The six differently named transform
shapes below are the wrong-answer family the audit of the retired v1.3.0
adapter found: each one moved an orientation repair onto the panel path
under a name the old vocabulary did not carry, and each one was reported as
the direct orientation.

The v2.0.1 blocks in the middle of this module are the counterexamples an
adversarial review of v2.0.0 demonstrated: match-count selectors masking the
real emission, stale provenance surviving alias mutation, reversed
dict-spread precedence, static call resolution ignoring runtime rebinding,
false conditional-repair corroboration, report-plane coincidence, fusion
reversing an abstention, and two crashes. Each block names its finding.

The v2.1.0 block at the end holds the thirteen workflows a second
adversarial review demonstrated against v2.0.1, copied verbatim from that
review's own repro cases, plus the parse-time crash it found. Every one of
them made v2.0.1 answer with the orientation opposite to what the workflow
computes at run time. They are permanent: the default-deny trust model exists
because of them, and no later version may delete them. Each also appears in a
stripped form with the review harness's runtime-witness lines removed, so the
architectural rule that closes it is proven to fire on its own rather than on
the scaffolding.
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
from sc_referee.scientific_checks.founder_orientation_dataflow import (
    FounderDataflowResolution,
    _document_orientations,
    resolve_founder_orientation_dataflow,
)
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
# The accounting every round-two counterexample report states, so a fused
# inspection over one of them has a report plane to work with.
_COUNTEREXAMPLE_REPORT = (
    "Of 4 markers, 3 agree. Agreement rate 0.750000; mismatch rate 0.250000. Likelihood 9.9e-07.\n"
)


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


def _inspection_context(report_text: str, analyses: dict[str, str]) -> FrozenInspectionContext:
    """One report and any number of Python workflow documents."""

    report = report_text.encode("utf-8")
    surface_ref = RecordRef("publication_surface", "publication-surface:soundness")
    artifact_ref = RecordRef("artifact", "artifact:soundness-report")
    identity_ref = RecordRef("asset_identity", "asset-identity:soundness-report")
    report_file_ref = RecordRef("file_record", "file:soundness-report")
    report_parser_ref = RecordRef("parser_result", "parser-result:soundness-report")
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
    records: list[tuple[RecordRef, dict[str, object]]] = [
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
    ]
    documents = [
        InspectionDocument(
            path="report.md",
            file_ref=report_file_ref,
            content=report,
            content_digest=sha256_digest(report),
            media_type="text/markdown",
            parser_result_ref=report_parser_ref,
            parser_result_payload=report_parser,
            parser_result_digest=sha256_digest(report_parser),
        )
    ]
    for index, (path, analysis_text) in enumerate(analyses.items()):
        analysis = analysis_text.encode("utf-8")
        file_ref = RecordRef("file_record", f"file:soundness-analysis-{index}")
        parser_ref = RecordRef("parser_result", f"parser-result:soundness-analysis-{index}")
        records.extend(
            [
                (file_ref, {"file_record_id": file_ref.record_id}),
                (parser_ref, {"parser_result_id": parser_ref.record_id}),
            ]
        )
        documents.append(
            InspectionDocument(
                path=path,
                file_ref=file_ref,
                content=analysis,
                content_digest=sha256_digest(analysis),
                media_type="text/x-python",
                parser_result_ref=parser_ref,
                parser_result_payload=analysis_parser,
                parser_result_digest=sha256_digest(analysis_parser),
            )
        )
    context = FrozenInspectionContext(
        snapshot_digest=sha256_digest("snapshot"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=tuple(documents),
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in records),
    )
    return replace(
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


def _fused_observation(
    report_text: str,
    analysis_text: str = "value = 1\n",
    companions: dict[str, str] | None = None,
) -> tuple[str, str | None]:
    """Run the released founder adapter over one report and one workflow."""

    analyses = {"analysis.py": analysis_text, **(companions or {})}
    context = _inspection_context(report_text, analyses)
    module = next(
        item
        for item in default_scientific_check_registry().modules
        if item.manifest.check_id == FOUNDER_CHECK
    )
    observation = module.adapters[0].inspect(context)
    operand = observation.observed_operand
    return observation.applicability, None if operand is None else str(operand.value)


def _resolution(
    analysis_text: str,
    companions: dict[str, str] | None = None,
    report_text: str = _COUNTEREXAMPLE_REPORT,
) -> FounderDataflowResolution:
    """The public resolver's verdict over one workflow and its companions."""

    analyses = {"analysis.py": analysis_text, **(companions or {})}
    return resolve_founder_orientation_dataflow(
        _inspection_context(report_text, analyses),
        direct_operand=DIRECT_OPERAND,
        repaired_operand=REPAIRED_OPERAND,
        parser_id=PYTHON_PARSER_ID,
        parser_version=PYTHON_PARSER_VERSION,
    )


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


def test_a_diagnostic_flip_that_never_reaches_the_report_conflicts() -> None:
    """v2.1.0 policy: readings are collected module-wide and must agree.

    Expectation flipped from ``{"direct"}``. The banned form was the point of
    the old test: a second recognized reading over the complemented panel,
    running unconditionally at module level, used to be discarded because it
    never reached the written report. The v2.1.0 disagreement rule collects
    every recognized reading, and resolves past a disagreement only when the
    disagreeing reading is provably dead -- inside a function whose name
    occurs nowhere but its own definition. A live module-level diagnostic is
    not dead, so the document is ambiguous.
    """

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
    assert states == {"direct", "repaired"}


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

# The v2.1.1 import allowlist rejects ``io`` and ``itertools``, so positive
# fixtures use this head; _STDLIB_HEAD stays for fixtures that must abstain.
_ALLOWED_HEAD = """import csv
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
        _ALLOWED_HEAD
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
        _ALLOWED_HEAD
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


def test_a_spread_after_an_explicit_key_over_a_raw_read_abstains() -> None:
    """``{'founder': 1 - x, **row}`` over a raw CSV read is a runtime question.

    Python applies dict entries left to right, so the spread wins -- but only
    if the CSV actually carries a ``founder`` column, and the staged file's
    columns are runtime data. The v2.1.0 model assumed presence and read a
    surviving repair as the direct panel (a demonstrated wrong answer), so
    the spread now overwrites an explicit key only when the column's presence
    is proven by an explicit override; over a raw read the key is opaque and
    the document abstains.
    """

    source = _workflow(
        "panel = [{'founder': 1 - int(row['founder']), **row} for row in rows]\n",
        source="panel",
    )
    unsupported, _states = _resolve(source)
    assert unsupported


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


def test_a_write_into_an_in_memory_buffer_abstains() -> None:
    """v2.1.0 policy: the expression-statement whitelist.

    Expectation flipped from ``not unsupported``. ``io.StringIO().write``
    answers to the same method name as a file, so it still never reaches the
    report; but a bare expression statement is now admitted only as a
    docstring, a recognized report write, or the print-read form, and a write
    into a buffer is none of those. The document abstains rather than
    resolving around a statement the trace does not model.
    """

    source = (
        _STDLIB_HEAD
        + _emission("rows")
        + "buffer = io.StringIO()\n"
        + "buffer.write(f'{likelihood}')\n"
    )
    unsupported, states = _resolve(source)
    assert unsupported
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


@pytest.mark.parametrize("called", [False, True])
def test_a_closure_over_a_tagged_row_set_abstains(called: bool) -> None:
    """v2.1.0 policy: closures may not see tagged globals.

    Expectations flipped from ``not unsupported`` with ``set()`` for the
    uncalled body and ``{"direct"}`` for the called one. The banned form was
    the point of both old tests: a function body reading a module-level row
    set by closure. Which panel that name holds when the call runs is decided
    by the module's binding order at run time, and the ``closure_alias``
    counterexample turned exactly that gap into a wrong answer. A helper may
    now read only its own parameters, safe builtins, the import table, and
    other module functions, so both shapes abstain -- and with parameters
    masked there is no surviving positive path for an emission traced inside
    a function.
    """

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n\n"
        "def emission():\n"
        "    return math.prod(\n"
        "        0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in rows\n"
        "    )\n"
    )
    if called:
        source += "\nlikelihood = emission()\n" + _TAIL
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


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


# ---------------------------------------------------------------------------
# v2.1.0 controls: the thirteen workflows a second adversarial review
# demonstrated against v2.0.1, copied verbatim from its repro cases, and the
# parse-time crash it found. Under v2.0.1 every one of these produced an
# applicable observation naming the orientation opposite to what the workflow
# computes at run time. Under the v2.1.0 default-deny trust model each one
# abstains. These tests are permanent; the whitelist exists because of them.

ROUND_TWO_COUNTEREXAMPLES: dict[str, str] = {
    "parameter_alias": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]


def replace(target, replacement):
    target.clear()
    target.extend(replacement)


replace(rows, panel)
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in rows
)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f"Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; "
    f"mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n"
)
Path("results/parameter_alias.md").write_text(report)
current_founders = [int(row["founder"]) for row in rows]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
    "container_alias": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]
holder = [rows]
holder[0].clear()
holder[0].extend(panel)
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in rows
)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f"Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; "
    f"mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n"
)
Path("results/container_alias.md").write_text(report)
current_founders = [int(row["founder"]) for row in rows]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
    "comprehension_alias": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]
[(alias.clear(), alias.extend(panel)) for alias in [rows]]
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in rows
)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f"Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; "
    f"mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n"
)
Path("results/comprehension_alias.md").write_text(report)
current_founders = [int(row["founder"]) for row in rows]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
    "closure_alias": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]


def replace():
    rows.clear()
    rows.extend(panel)


replace()
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in rows
)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f"Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; "
    f"mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n"
)
Path("results/closure_alias.md").write_text(report)
current_founders = [int(row["founder"]) for row in rows]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
    "spread_side_effect": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [
    {
        "side_effect": row.update({"founder": 1 - int(row["founder"])}),
        **row,
    }
    for row in rows
]
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in panel
)
agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in panel
)
n = len(panel)
rate = agreement / n
mismatch = 1 - rate
report = (
    f"Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; "
    f"mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n"
)
Path("results/spread_side_effect.md").write_text(report)
current_founders = [int(row["founder"]) for row in panel]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
    "match_guard": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]
mode = "repair"
selected = rows
match mode:
    case "repair":
        selected = panel

likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in selected
)
agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in selected
)
n = len(selected)
rate = agreement / n
mismatch = 1 - rate
report = (
    f"Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; "
    f"mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n"
)
Path("results/match_guard.md").write_text(report)
current_founders = [int(row["founder"]) for row in selected]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
    "walrus_expr": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]
print(rows := panel)
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in rows
)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f"Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; "
    f"mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n"
)
Path("results/walrus_expr.md").write_text(report)
current_founders = [int(row["founder"]) for row in rows]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
    "higher_order": r"""import csv
import math
from pathlib import Path


def identity(value):
    return value


def flip(value):
    return 1 - value


def apply(identity, value):
    return identity(value)


rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": apply(flip, int(row["founder"]))} for row in rows]
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in panel
)
agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in panel
)
n = len(panel)
rate = agreement / n
mismatch = 1 - rate
report = (
    f"Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; "
    f"mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n"
)
Path("results/higher_order.md").write_text(report)
current_founders = [int(row["founder"]) for row in panel]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
    "duplicate_def": r"""import csv
import math
from pathlib import Path


def recode(value):
    return value


rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": recode(int(row["founder"]))} for row in rows]
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in panel
)
agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in panel
)
n = len(panel)
rate = agreement / n
mismatch = 1 - rate
report = (
    f"Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; "
    f"mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n"
)
Path("results/duplicate_def.md").write_text(report)


def recode(value):
    return 1 - value


current_founders = [int(row["founder"]) for row in panel]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
    "reduce_mask": r"""import csv
import functools
import math
import operator
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]
diagnostic_agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in panel
)
likelihood = functools.reduce(
    operator.mul,
    (0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows),
    1.0,
)
direct_matches = [
    int(row["call"]) == int(row["founder"]) for row in rows
].count(True)
n = len(rows)
match_rate = direct_matches / n
report = (
    f"Of {n} markers, the complemented diagnostic has {diagnostic_agreement} agreements. "
    f"The direct-panel HMM match fraction is {match_rate:.6f}; likelihood {likelihood:.8g}.\n"
)
Path("results/reduce_mask.md").write_text(report)
current_founders = [int(row["founder"]) for row in rows]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
    "uncalled_writer": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]


def diagnostic():
    diagnostic_likelihood = math.prod(
        0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in panel
    )
    Path("results/unused.md").write_text(str(diagnostic_likelihood))


actual_likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
actual_agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in rows
)
n = len(rows)
rate = actual_agreement / n
mismatch = 1 - rate
report = (
    f"Of {n} markers, {actual_agreement} agree. Agreement rate {rate:.6f}; "
    f"mismatch rate {mismatch:.6f}. Likelihood {actual_likelihood:.8g}.\n"
)
with open("results/uncalled_writer.md", "w") as handle:
    handle.write(report)
current_founders = [int(row["founder"]) for row in rows]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
    "rebound_path_sink": r"""import csv
import io
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]
sink = Path("results/unused.md")
sink = io.StringIO()
diagnostic_likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in panel
)
sink.write(str(diagnostic_likelihood))
actual_likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
actual_agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in rows
)
n = len(rows)
rate = actual_agreement / n
mismatch = 1 - rate
report = (
    f"Of {n} markers, {actual_agreement} agree. Agreement rate {rate:.6f}; "
    f"mismatch rate {mismatch:.6f}. Likelihood {actual_likelihood:.8g}.\n"
)
with open("results/rebound_path_sink.md", "w") as handle:
    handle.write(report)
current_founders = [int(row["founder"]) for row in rows]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
    "imported_reader": r"""import csv
import math
from pathlib import Path

from reader_impl import reader

staged_rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in staged_rows]
rows = list(reader(Path("inputs/markers.csv").open()))
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
agreement = sum(
    1 if int(row["call"]) == int(row["founder"]) else 0 for row in rows
)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f"Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; "
    f"mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n"
)
Path("results/imported_reader.md").write_text(report)
current_founders = [int(row["founder"]) for row in rows]
print("RUNTIME_DIRECT=" + str(current_founders == staged_founders))
print("RUNTIME_REPAIRED=" + str(current_founders == [1 - value for value in staged_founders]))
""",
}

ROUND_TWO_COMPANIONS: dict[str, str] = {
    "imported_reader": r"""import csv


def reader(handle):
    return [
        {**row, "founder": 1 - int(row["founder"])}
        for row in csv.DictReader(handle)
    ]
""",
}
# What the default-deny model rejects in each workflow, and the runtime
# orientation the review's witness observed. v2.0.1 answered the opposite.
ROUND_TWO_RULES = {
    "parameter_alias": ("a tagged row set passed as a call argument", "repaired"),
    "container_alias": ("a tagged row set placed inside a container literal", "repaired"),
    "comprehension_alias": ("an expression statement that is not a write or a read", "repaired"),
    "closure_alias": ("a function body reading a tagged module global", "repaired"),
    "spread_side_effect": ("a call inside a container literal outside the recode set", "repaired"),
    "match_guard": ("a statement type outside the whitelist", "repaired"),
    "walrus_expr": ("a walrus anywhere in a statement subtree", "repaired"),
    "higher_order": ("a helper calling one of its own parameters", "repaired"),
    "duplicate_def": ("a name defined by def more than once", "direct"),
    "reduce_mask": ("an unlisted library call over a tagged row set", "direct"),
    "uncalled_writer": ("a function body reading a tagged module global", "direct"),
    "rebound_path_sink": ("a write on a name no longer bound to a path", "direct"),
    "imported_reader": ("an imported callable outside the reader vocabulary", "repaired"),
}

_RUNTIME_WITNESS_PREFIXES = ("staged_founders =", "current_founders =", 'print("RUNTIME_')


def _without_runtime_witness(source: str) -> str:
    """The review case with its runtime-orientation witness lines removed.

    The harness appends two comprehensions and two prints to observe which
    orientation the workflow actually produced. Those lines are themselves
    outside the print-read whitelist, so stripping them proves the rule that
    names each counterexample fires on the workflow itself.
    """

    kept = [line for line in source.splitlines() if not line.startswith(_RUNTIME_WITNESS_PREFIXES)]
    return "\n".join(kept) + "\n"


@pytest.mark.parametrize("case", sorted(ROUND_TWO_COUNTEREXAMPLES))
def test_round_two_counterexample_abstains(case: str) -> None:
    """Each demonstrated wrong answer is now an abstention, verbatim."""

    unsupported, states = _resolve(ROUND_TWO_COUNTEREXAMPLES[case])
    assert unsupported, ROUND_TWO_RULES[case][0]
    assert states == set()


@pytest.mark.parametrize("case", sorted(ROUND_TWO_COUNTEREXAMPLES))
def test_round_two_counterexample_abstains_without_its_witness(case: str) -> None:
    """The rule that closes each case fires on the workflow, not the harness."""

    source = _without_runtime_witness(ROUND_TWO_COUNTEREXAMPLES[case])
    unsupported, states = _resolve(source)
    assert unsupported, ROUND_TWO_RULES[case][0]
    assert states == set()


@pytest.mark.parametrize("case", sorted(ROUND_TWO_COUNTEREXAMPLES))
def test_round_two_counterexample_resolver_returns_no_orientation(case: str) -> None:
    """The public resolver reports unsupported and nothing else."""

    companion = ROUND_TWO_COMPANIONS.get(case)
    resolution = _resolution(
        ROUND_TWO_COUNTEREXAMPLES[case],
        {"companion.py": companion} if companion else None,
    )
    assert resolution.state == "unsupported"
    assert resolution.orientation is None
    assert resolution.operand_value is None
    assert resolution.spans == ()
    assert resolution.source_path is None


@pytest.mark.parametrize("case", sorted(ROUND_TWO_COUNTEREXAMPLES))
def test_round_two_counterexample_adapter_returns_no_operand(case: str) -> None:
    """The released adapter abstains as unsupported over each case's own report."""

    companions = ROUND_TWO_COMPANIONS.get(case)
    applicability, operand = _fused_observation(
        _COUNTEREXAMPLE_REPORT,
        ROUND_TWO_COUNTEREXAMPLES[case],
        {"companion.py": companions} if companions else None,
    )
    assert applicability == "unsupported"
    assert operand is None


def test_a_three_thousand_term_expression_abstains_without_a_parse_crash() -> None:
    """``ast.parse`` itself raised ``RecursionError`` on this shape in v2.0.1.

    The expression bound protected the trace but not the parser, so a valid
    3,000-operation XOR crashed the public resolver before any analysis ran.
    Parsing is now guarded and the document abstains.
    """

    deep = "value = source" + " ^ 1" * 3000 + "\n"
    resolution = _resolution(deep)
    assert resolution.state == "unsupported"
    assert resolution.operand_value is None
    applicability, operand = _fused_observation(_COUNTEREXAMPLE_REPORT, deep)
    assert applicability == "unsupported"
    assert operand is None


# ---------------------------------------------------------------------------
# v2.1.1 controls: every counterexample from the third review round (an
# 11-case Codex slice over the value model and whitelist seams, and a
# 5-case independent Opus sweep). Each demonstrated a wrong non-abstaining
# classification against v2.1.0; each must now abstain.


ROUND_THREE_COUNTEREXAMPLES: dict[str, str] = {
    "comprehension_plain_name": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]
trigger = [0]
ignored = [
    globals().__setitem__("rows", globals()["panel"])
    for unused in trigger
]
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
current_founders = [int(row["founder"]) for row in rows]
repaired_founders = [1 - value for value in staged_founders]
runtime_orientation = (
    "direct"
    if current_founders == staged_founders
    else "repaired"
    if current_founders == repaired_founders
    else "mixed"
)
report = f"runtime_orientation={runtime_orientation}\nlikelihood={likelihood}\n"
Path("results/report.md").write_text(report)
""",
    "comprehension_target_masks_global": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]
trigger = [0]


def emission():
    shadow = [0 for rows in trigger]
    return math.prod(
        0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
    )


used_founders = [int(row["founder"]) for row in rows]
likelihood = emission()
rows = panel
repaired_founders = [1 - value for value in staged_founders]
runtime_orientation = (
    "direct"
    if used_founders == staged_founders
    else "repaired"
    if used_founders == repaired_founders
    else "mixed"
)
report = f"runtime_orientation={runtime_orientation}\nlikelihood={likelihood}\n"
Path("results/report.md").write_text(report)
""",
    "dict_spread_parameter_method": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]


def keep_then_flip_source(value, source_row):
    ignored = source_row.update({"founder": 1 - value})
    return value


panel = [
    {
        "founder": keep_then_flip_source(int(row["founder"]), row),
        **row,
    }
    for row in rows
]
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in panel
)
current_founders = [int(row["founder"]) for row in panel]
repaired_founders = [1 - value for value in staged_founders]
runtime_orientation = (
    "direct"
    if current_founders == staged_founders
    else "repaired"
    if current_founders == repaired_founders
    else "mixed"
)
report = f"runtime_orientation={runtime_orientation}\nlikelihood={likelihood}\n"
Path("results/report.md").write_text(report)
""",
    "expr_bare_call": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]


def swap_rows():
    namespace = globals()
    cleared = namespace["rows"].clear()
    extended = namespace["rows"].extend(namespace["panel"])
    return "swapped"


swap_rows()
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
current_founders = [int(row["founder"]) for row in rows]
repaired_founders = [1 - value for value in staged_founders]
runtime_orientation = (
    "direct"
    if current_founders == staged_founders
    else "repaired"
    if current_founders == repaired_founders
    else "mixed"
)
report = f"runtime_orientation={runtime_orientation}\nlikelihood={likelihood}\n"
Path("results/report.md").write_text(report)
""",
    "expr_print_read": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]


def stringify(self):
    namespace = globals()
    cleared = namespace["rows"].clear()
    extended = namespace["rows"].extend(namespace["panel"])
    return "swapped"


Printer = type("Printer", (), {"__str__": stringify})
printer = Printer()
print(printer)
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
current_founders = [int(row["founder"]) for row in rows]
repaired_founders = [1 - value for value in staged_founders]
runtime_orientation = (
    "direct"
    if current_founders == staged_founders
    else "repaired"
    if current_founders == repaired_founders
    else "mixed"
)
report = f"runtime_orientation={runtime_orientation}\nlikelihood={likelihood}\n"
Path("results/report.md").write_text(report)
""",
    "expr_report_write": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]


def swap_rows():
    namespace = globals()
    cleared = namespace["rows"].clear()
    extended = namespace["rows"].extend(namespace["panel"])
    return "swapped"


Path("results/preflight.txt").write_text(swap_rows())
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
current_founders = [int(row["founder"]) for row in rows]
repaired_founders = [1 - value for value in staged_founders]
runtime_orientation = (
    "direct"
    if current_founders == staged_founders
    else "repaired"
    if current_founders == repaired_founders
    else "mixed"
)
report = f"runtime_orientation={runtime_orientation}\nlikelihood={likelihood}\n"
Path("results/report.md").write_text(report)
""",
    "function_annotation": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": 1 - int(row["founder"])} for row in rows]


def unused(value: globals().__setitem__("rows", globals()["panel"])):
    return value


likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in rows
)
current_founders = [int(row["founder"]) for row in rows]
repaired_founders = [1 - value for value in staged_founders]
runtime_orientation = (
    "direct"
    if current_founders == staged_founders
    else "repaired"
    if current_founders == repaired_founders
    else "mixed"
)
report = f"runtime_orientation={runtime_orientation}\nlikelihood={likelihood}\n"
Path("results/report.md").write_text(report)
""",
    "loop_append_alias": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = []
alias = panel
for row in rows:
    panel.append({**row, "founder": 1 - int(row["founder"])})
    alias.append({**row, "founder": int(row["founder"])})

likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in panel
)
current_founders = [int(row["founder"]) for row in panel]
repaired_founders = [1 - value for value in staged_founders]
runtime_orientation = (
    "direct"
    if current_founders == staged_founders
    else "repaired"
    if current_founders == repaired_founders
    else "mixed"
)
report = f"runtime_orientation={runtime_orientation}\nlikelihood={likelihood}\n"
Path("results/report.md").write_text(report)
""",
    "probability_container_rebound_int": r"""import csv
import math
from pathlib import Path

builtin_int = int


def flip_value(value):
    return 1 - builtin_int(value)


int = flip_value
rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
likelihood = math.prod(
    [0.01, 0.99][int(row["call"]) == float(row["founder"])] for row in rows
)
runtime_orientation = "repaired" if likelihood > 0.5 else "direct"
report = f"runtime_orientation={runtime_orientation}\nlikelihood={likelihood}\n"
Path("results/report.md").write_text(report)
""",
    "raw_not_before_cast": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [int(row["founder"]) for row in rows]
panel = [{**row, "founder": int(not row["founder"])} for row in rows]
likelihood = math.prod(
    0.99 if int(row["call"]) == int(row["founder"]) else 0.01 for row in panel
)
current_founders = [int(row["founder"]) for row in panel]
repaired_founders = [1 - value for value in staged_founders]
runtime_orientation = (
    "direct"
    if current_founders == staged_founders
    else "repaired"
    if current_founders == repaired_founders
    else "mixed"
)
report = f"runtime_orientation={runtime_orientation}\nlikelihood={likelihood}\n"
Path("results/report.md").write_text(report)
""",
    "rebound_identity_cast": r"""import csv
import math
from pathlib import Path

builtin_int = int


def flip(value):
    return 1 - builtin_int(value)


int = flip
rows = list(csv.DictReader(Path("inputs/markers.csv").open()))
staged_founders = [builtin_int(row["founder"]) for row in rows]
panel = [{**row, "founder": int(row["founder"])} for row in rows]
likelihood = math.prod(
    0.99 if float(row["call"]) == float(row["founder"]) else 0.01 for row in panel
)
current_founders = [builtin_int(row["founder"]) for row in panel]
repaired_founders = [1 - value for value in staged_founders]
runtime_orientation = (
    "direct"
    if current_founders == staged_founders
    else "repaired"
    if current_founders == repaired_founders
    else "mixed"
)
report = f"runtime_orientation={runtime_orientation}\nlikelihood={likelihood}\n"
Path("results/report.md").write_text(report)
""",
    "sequenced_row_update": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
likelihood = math.prod(
    (row.update({'founder': str(1 - int(row['founder']))}) or 1.0)
    * (0.99 if int(row['call']) == int(row['founder']) else 0.01)
    for row in rows
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n'
)
Path('results/report.md').write_text(report)
""",
    "filter_row_update": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
likelihood = math.prod(
    0.99 if int(row['call']) == int(row['founder']) else 0.01
    for row in rows
    if not row.update({'founder': str(1 - int(row['founder']))})
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
report = f'Of {n} markers, {agreement} agree at {rate:.6f}. Likelihood {likelihood:.8g}.\n'
Path('results/report.md').write_text(report)
""",
    "loop_body_setitem": r"""import csv
import math
import operator
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
likelihood = 1.0
agreement = 0
for row in rows:
    likelihood *= (operator.setitem(row, 'founder', str(1 - int(row['founder']))) or 1.0) \
        * (0.99 if int(row['call']) == int(row['founder']) else 0.01)
    agreement += 1 if int(row['call']) == int(row['founder']) else 0
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n'
)
Path('results/report.md').write_text(report)
""",
    "spread_over_missing_column": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
panel = [{'founder': 1 - int(row['founder_raw']), **row} for row in rows]
likelihood = math.prod(
    0.99 if int(item['call']) == int(item['founder']) else 0.01 for item in panel
)
agreement = sum(1 if int(item['call']) == int(item['founder']) else 0 for item in panel)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n'
)
Path('results/report.md').write_text(report)
""",
    "dict_get_emission": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]
agreement = sum(1 if int(item['call']) == int(item['founder']) else 0 for item in panel)
likelihood = math.prod(
    0.99 if row.get('call') == row.get('founder') else 0.01 for row in rows
)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n'
)
Path('results/report.md').write_text(report)
""",
    "sibling_csv_module": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
likelihood = math.prod(
    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in rows
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.\n'
)
Path('results/report.md').write_text(report)
""",
}

ROUND_THREE_COMPANIONS: dict[str, dict[str, str]] = {
    "sibling_csv_module": {
        "csv.py": (
            "import csv as _stdlib\n\n\n"
            "def DictReader(handle):\n"
            "    for row in _stdlib.DictReader(handle):\n"
            "        yield {**row, 'founder': str(1 - int(row['founder']))}\n"
        ),
    },
}

# The rule that closes each case.
ROUND_THREE_RULES = {
    "comprehension_plain_name": "a reflection builtin (globals) anywhere in the module",
    "comprehension_target_masks_global": "a tagged name reused as a comprehension target reads as the tagged global",
    "dict_spread_parameter_method": "an unrecognized method call on a helper parameter",
    "expr_bare_call": "a reflection builtin (globals) inside a called body",
    "expr_print_read": "type() constructing an object with a side-effecting __str__",
    "function_annotation": "a parameter annotation, which executes at definition time",
    "loop_append_alias": "two append receivers in one alias group are one runtime list",
    "probability_container_rebound_int": "an assignment shadowing the builtin int",
    "raw_not_before_cast": "not over a raw CSV string is not a numeric inversion",
    "rebound_identity_cast": "an assignment shadowing the builtin int",
    "sequenced_row_update": "an unrecognized method call (row.update) inside an element",
    "filter_row_update": "an unrecognized method call (row.update) in a comprehension filter",
    "loop_body_setitem": "loop bodies pass the same expression whitelist as comprehensions",
    "spread_over_missing_column": "a spread overwrites an explicit key only with proven presence",
    "dict_get_emission": "an unrecognized method call (row.get) reading the emission",
    "sibling_csv_module": "an import resolving to another document in the same case",
}


@pytest.mark.parametrize("case", sorted(ROUND_THREE_COUNTEREXAMPLES))
def test_round_three_counterexample_abstains(case: str) -> None:
    """Each round-three wrong answer is now an abstention, verbatim."""

    unsupported, states = _resolve(ROUND_THREE_COUNTEREXAMPLES[case])
    if case == "sibling_csv_module":
        # The sibling-module rule lives in the public resolver, which sees
        # the whole document set; the per-document trace cannot.
        return
    assert unsupported, ROUND_THREE_RULES[case]
    assert states == set()


@pytest.mark.parametrize("case", sorted(ROUND_THREE_COUNTEREXAMPLES))
def test_round_three_counterexample_abstains_without_its_witness(case: str) -> None:
    """The closing rule fires on the workflow itself, not the harness lines."""

    if case == "sibling_csv_module":
        return
    source = _without_runtime_witness(ROUND_THREE_COUNTEREXAMPLES[case])
    unsupported, states = _resolve(source)
    assert unsupported, ROUND_THREE_RULES[case]
    assert states == set()


@pytest.mark.parametrize("case", sorted(ROUND_THREE_COUNTEREXAMPLES))
def test_round_three_counterexample_resolver_returns_no_orientation(case: str) -> None:
    """The public resolver reports unsupported and nothing else."""

    companions = ROUND_THREE_COMPANIONS.get(case)
    resolution = _resolution(ROUND_THREE_COUNTEREXAMPLES[case], companions)
    assert resolution.state == "unsupported"
    assert resolution.orientation is None
    assert resolution.operand_value is None
    assert resolution.spans == ()
    assert resolution.source_path is None


@pytest.mark.parametrize("case", sorted(ROUND_THREE_COUNTEREXAMPLES))
def test_round_three_counterexample_adapter_returns_no_operand(case: str) -> None:
    """The released adapter abstains as unsupported over each case's own report."""

    companions = ROUND_THREE_COMPANIONS.get(case)
    applicability, operand = _fused_observation(
        _COUNTEREXAMPLE_REPORT,
        ROUND_THREE_COUNTEREXAMPLES[case],
        companions,
    )
    assert applicability == "unsupported"
    assert operand is None
