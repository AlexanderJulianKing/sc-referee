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
    ["Fraction(99, 100)", "Decimal('0.99')", "Decimal(0.99)"],
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


# ---------------------------------------------------------------------------
# v2.1.2 controls: the fourth review round (independent Opus, value-model
# slice). Two families: the selector's own polarity (operator and branch
# order) was never part of the parity model, and rebuilt columns dropped
# their numeric proof so the mixed-runtime-type guard could not fire. Every
# case returned an applicable operand contradicting (or matching neither
# hypothesis of) the runtime; each must now abstain.


ROUND_FOUR_COUNTEREXAMPLES: dict[str, str] = {
    "noteq_operator": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
likelihood = math.prod(
    0.99 if int(row['call']) != int(row['founder']) else 0.01 for row in rows
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.'
)
Path('results/report.md').write_text(report)
""",
    "noteq_against_recode": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
likelihood = math.prod(
    0.99 if int(row['call']) != 1 - int(row['founder']) else 0.01 for row in rows
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.'
)
Path('results/report.md').write_text(report)
""",
    "noteq_container": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
likelihood = math.prod(
    [0.01, 0.99][int(row['call']) != int(row['founder'])] for row in rows
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.'
)
Path('results/report.md').write_text(report)
""",
    "swapped_branches": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
likelihood = math.prod(
    0.01 if int(row['call']) == int(row['founder']) else 0.99 for row in rows
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.'
)
Path('results/report.md').write_text(report)
""",
    "swapped_container": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
likelihood = math.prod(
    [0.99, 0.01][int(row['call']) == int(row['founder'])] for row in rows
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.'
)
Path('results/report.md').write_text(report)
""",
    "named_branch_values": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
MATCH = 0.01
MISMATCH = 0.99
likelihood = math.prod(
    MATCH if int(row['call']) == int(row['founder']) else MISMATCH for row in rows
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.'
)
Path('results/report.md').write_text(report)
""",
    "noteq_in_accumulation_loop": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
likelihood = 1.0
for row in rows:
    likelihood *= 0.99 if int(row['call']) != int(row['founder']) else 0.01
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.'
)
Path('results/report.md').write_text(report)
""",
    "rebuild_without_read_casts": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]
likelihood = math.prod(
    0.99 if item['call'] == item['founder'] else 0.01 for item in panel
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.'
)
Path('results/report.md').write_text(report)
""",
    "identity_rebuild_without_read_casts": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
panel = [{**row, 'founder': int(row['founder'])} for row in rows]
likelihood = math.prod(
    0.99 if item['call'] == item['founder'] else 0.01 for item in panel
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.'
)
Path('results/report.md').write_text(report)
""",
    "explicit_key_rebuild_without_read_casts": r"""import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
panel = [{'call': row['call'], 'founder': 1 - int(row['founder'])} for row in rows]
likelihood = math.prod(
    0.99 if item['call'] == item['founder'] else 0.01 for item in panel
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.'
)
Path('results/report.md').write_text(report)
""",
    "helper_rebuild_without_read_casts": r"""import csv
import math
from pathlib import Path

def load_panel(handle):
    return [{**row, 'founder': 1 - int(row['founder'])} for row in csv.DictReader(handle)]

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
panel = load_panel(Path('inputs/markers.csv').open())
likelihood = math.prod(
    0.99 if item['call'] == item['founder'] else 0.01 for item in panel
)
agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)
n = len(rows)
rate = agreement / n
mismatch = 1 - rate
report = (
    f'Of {n} markers, {agreement} agree. Agreement rate {rate:.6f}; '
    f'mismatch rate {mismatch:.6f}. Likelihood {likelihood:.8g}.'
)
Path('results/report.md').write_text(report)
""",
}

ROUND_FOUR_RULES = {
    "noteq_operator": "an inequality selector is extensionally a complement; non-canonical selectors never classify",
    "noteq_against_recode": "inequality against a recode composes to the opposite reading; non-canonical",
    "noteq_container": "container indexed by an inequality; non-canonical",
    "swapped_branches": "mismatch branch larger than match branch; order is not canonical",
    "swapped_container": "container elements reversed; order is not canonical",
    # v2.2.0 policy change. Through v2.1.5 this case abstained because a name
    # was never a provable constant. Extension two now resolves a name
    # assigned exactly once in the whole module to a literal, so ``MATCH`` and
    # ``MISMATCH`` here do resolve -- to 0.01 and 0.99, which puts the smaller
    # value on the match branch. The case still abstains, now for the same
    # reason ``swapped_branches`` does: the branch order is not canonical. The
    # ruling that the resolution itself is legitimate is proven positively by
    # ``test_single_assignment_named_branch_values_resolve`` and bounded by
    # ``test_a_twice_assigned_branch_name_still_abstains``.
    "named_branch_values": "resolved branch constants in non-canonical order; mismatch branch larger",
    "noteq_in_accumulation_loop": "the loop path recognizes only canonical selectors too",
    "rebuild_without_read_casts": "rebuilt numeric column vs raw string column is constantly unequal at runtime",
    "identity_rebuild_without_read_casts": "identity rebuild with a cast still changes the runtime type",
    "explicit_key_rebuild_without_read_casts": "explicit-key rebuild stores a number beside a raw string",
    "helper_rebuild_without_read_casts": "the numeric proof rides through helper-built panels too",
}


@pytest.mark.parametrize("case", sorted(ROUND_FOUR_COUNTEREXAMPLES))
def test_round_four_counterexample_abstains(case: str) -> None:
    unsupported, states = _resolve(ROUND_FOUR_COUNTEREXAMPLES[case])
    assert unsupported, ROUND_FOUR_RULES[case]
    assert states == set()


@pytest.mark.parametrize("case", sorted(ROUND_FOUR_COUNTEREXAMPLES))
def test_round_four_counterexample_resolver_returns_no_orientation(case: str) -> None:
    resolution = _resolution(ROUND_FOUR_COUNTEREXAMPLES[case])
    assert resolution.state == "unsupported"
    assert resolution.orientation is None
    assert resolution.operand_value is None


@pytest.mark.parametrize("case", sorted(ROUND_FOUR_COUNTEREXAMPLES))
def test_round_four_counterexample_adapter_returns_no_operand(case: str) -> None:
    applicability, operand = _fused_observation(
        _COUNTEREXAMPLE_REPORT, ROUND_FOUR_COUNTEREXAMPLES[case]
    )
    assert applicability == "unsupported"
    assert operand is None


def test_canonical_selectors_still_resolve_after_the_polarity_rule() -> None:
    """The polarity rule must not cost the ordinary canonical positives."""

    head = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
    )
    tail = "report = f'likelihood {likelihood}'\nPath('results/report.md').write_text(report)\n"
    for selector in (
        "0.99 if int(row['call']) == int(row['founder']) else 0.01",
        "[0.01, 0.99][int(row['call']) == int(row['founder'])]",
        "Fraction(99, 100) if int(row['call']) == int(row['founder']) else Fraction(1, 100)",
    ):
        prefix = "from fractions import Fraction\n" if "Fraction" in selector else ""
        source = (
            prefix
            + head
            + "likelihood = math.prod(\n    "
            + selector
            + " for row in panel\n)\n"
            + tail
        )
        unsupported, states = _resolve(source)
        assert not unsupported, selector
        assert states == {"repaired"}, selector


# ---------------------------------------------------------------------------
# v2.1.2 controls, second half: the fourth review round's structure slice
# (independent Opus). Three families: helper-factored emissions invisible to
# classifier and belt, belt blindness to keyword casts and renamed
# accumulators, and package/namespace directories shadowing stdlib imports.


_ROUND_FIVE_TAIL = (
    "agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)\n"
    "n = len(rows)\n"
    "rate = agreement / n\n"
    "report = f'Of {n} markers, {agreement} agree at {rate:.6f}. Likelihood {likelihood:.8g}.'\n"
    "Path('results/report.md').write_text(report)\n"
)
_ROUND_FIVE_HEAD = (
    "import csv\nimport math\nfrom pathlib import Path\n\n"
    "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
    "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
)
_EMIT_HELPER = (
    "\ndef emit(observed, expected):\n    return 0.99 if observed == expected else 0.01\n\n"
)


def test_a_helper_emission_over_a_different_panel_than_the_count_abstains() -> None:
    """Two live disagreeing readings end as ambiguous, never as either answer."""

    source = (
        _ROUND_FIVE_HEAD
        + _EMIT_HELPER
        + "likelihood = math.prod(emit(int(item['call']), int(item['founder'])) for item in panel)\n"
        + _ROUND_FIVE_TAIL
    )
    resolution = _resolution(source)
    assert resolution.state == "ambiguous"
    assert resolution.operand_value is None


def test_a_helper_emission_with_a_matching_count_resolves() -> None:
    """The natural two-parameter helper factoring classifies correctly."""

    source = (
        _ROUND_FIVE_HEAD
        + _EMIT_HELPER
        + "likelihood = math.prod(emit(int(item['call']), int(item['founder'])) for item in panel)\n"
        + "agreement = sum(1 if int(item['call']) == int(item['founder']) else 0 for item in panel)\n"
        + "n = len(rows)\n"
        + "rate = agreement / n\n"
        + "report = f'Of {n} markers, {agreement} agree at {rate:.6f}. Likelihood {likelihood:.8g}.'\n"
        + "Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"repaired"}


def test_a_helper_emission_in_an_accumulation_loop_resolves() -> None:
    source = (
        _ROUND_FIVE_HEAD
        + _EMIT_HELPER
        + "likelihood = 1.0\n"
        + "for item in panel:\n"
        + "    likelihood *= emit(int(item['call']), int(item['founder']))\n"
        + "agreement = sum(1 if int(item['call']) == int(item['founder']) else 0 for item in panel)\n"
        + "n = len(rows)\n"
        + "rate = agreement / n\n"
        + "report = f'Of {n} markers, {agreement} agree at {rate:.6f}. Likelihood {likelihood:.8g}.'\n"
        + "Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"repaired"}


def test_a_boolean_helper_indexing_a_container_abstains() -> None:
    """A helper returning the bare comparison is not the recognized shape."""

    source = (
        _ROUND_FIVE_HEAD
        + "\ndef matches(observed, expected):\n"
        + "    return observed == expected\n\n"
        + "likelihood = math.prod([0.01, 0.99][matches(int(item['call']), int(item['founder']))]"
        + " for item in panel)\n"
        + _ROUND_FIVE_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


def test_a_mirrored_helper_emission_cannot_read_as_the_other_orientation() -> None:
    """Helper emission over raw rows with a panel count disagrees into ambiguity."""

    source = (
        _ROUND_FIVE_HEAD
        + _EMIT_HELPER
        + "likelihood = math.prod(emit(int(row['call']), int(row['founder'])) for row in rows)\n"
        + "agreement = sum(1 if int(item['call']) == int(item['founder']) else 0 for item in panel)\n"
        + "n = len(rows)\n"
        + "rate = agreement / n\n"
        + "report = f'Of {n} markers, {agreement} agree at {rate:.6f}. Likelihood {likelihood:.8g}.'\n"
        + "Path('results/report.md').write_text(report)\n"
    )
    resolution = _resolution(source)
    assert resolution.state == "ambiguous"
    assert resolution.operand_value is None


def test_a_keyword_cast_with_a_renamed_accumulator_abstains() -> None:
    """``int(x, base=10)`` plus ``scores = weights`` blinded the belt in v2.1.1."""

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': str(1 - int(row['founder']))} for row in rows]\n"
        "weights = [\n"
        "    0.99 if int(item['call'], base=10) == int(item['founder'], base=10) else 0.01\n"
        "    for item in panel\n"
        "]\n"
        "scores = weights\n"
        "likelihood = math.prod(scores)\n" + _ROUND_FIVE_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


def test_a_renamed_accumulator_alone_still_classifies() -> None:
    """The rename fix links the comprehension instead of losing it."""

    source = (
        _ROUND_FIVE_HEAD
        + "weights = [\n"
        + "    0.99 if int(item['call']) == int(item['founder']) else 0.01 for item in panel\n"
        + "]\n"
        + "scores = weights\n"
        + "likelihood = math.prod(scores)\n"
        + "agreement = sum(1 if int(item['call']) == int(item['founder']) else 0 for item in panel)\n"
        + "n = len(rows)\n"
        + "rate = agreement / n\n"
        + "report = f'Of {n} markers, {agreement} agree at {rate:.6f}. Likelihood {likelihood:.8g}.'\n"
        + "Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"repaired"}


def test_a_package_directory_shadowing_a_stdlib_import_abstains() -> None:
    """``csv/__init__.py`` in the case shadows stdlib csv; the flat-file rule missed it."""

    workflow = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "likelihood = math.prod(\n"
        "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in rows\n"
        ")\n" + _ROUND_FIVE_TAIL
    )
    shim = (
        '"""Project CSV helpers."""\n\n\n'
        "def DictReader(handle):\n"
        "    return [\n"
        "        {'call': line.strip()[0], 'founder': str(1 - int(line.strip()[2]))}\n"
        "        for line in handle\n"
        "        if line.strip()[0] != 'c'\n"
        "    ]\n"
    )
    for companion_path in ("csv/__init__.py", "csv/README.md"):
        resolution = _resolution(workflow, {companion_path: shim})
        assert resolution.state == "unsupported", companion_path
        assert resolution.operand_value is None


def test_a_star_import_abstains() -> None:
    source = (
        "import csv\nimport math\nfrom math import *\nfrom pathlib import Path\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "likelihood = math.prod(\n"
        "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in rows\n"
        ")\n" + _ROUND_FIVE_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


# ---------------------------------------------------------------------------
# v2.1.3 controls: the fifth review round's whole-system slice (independent
# Opus). Three families against the v2.1.2 machinery itself: a helper body
# rebinding a parameter before its return, an unguarded OverflowError on a
# huge selector constant, and the effective-numeric guard ORing where the
# read-site cast must override.


_ROUND_SIX_TAIL = (
    "agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)\n"
    "n = len(rows)\n"
    "rate = agreement / n\n"
    "report = f'Of {n} markers, {agreement} agree at {rate:.6f}. Likelihood {likelihood:.8g}.'\n"
    "Path('results/report.md').write_text(report)\n"
)
_ROUND_SIX_HEAD = (
    "import csv\nimport math\nfrom pathlib import Path\n\n"
    "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
)


@pytest.mark.parametrize(
    "rebinding",
    [
        "    expected = 1 - expected\n",
        "    observed = 1 - observed\n",
        "    expected = expected ^ 1\n",
        "    expected = abs(expected - 1)\n",
        "    expected = {0: 1, 1: 0}[expected]\n",
    ],
)
def test_a_helper_rebinding_a_parameter_before_its_selector_abstains(rebinding: str) -> None:
    """The recognized helper body is one return and nothing else."""

    source = (
        _ROUND_SIX_HEAD
        + "\ndef emit(observed, expected):\n"
        + rebinding
        + "    return 0.99 if observed == expected else 0.01\n\n"
        + "likelihood = math.prod(emit(int(row['call']), int(row['founder'])) for row in rows)\n"
        + _ROUND_SIX_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()
    applicability, operand = _fused_observation(_COUNTEREXAMPLE_REPORT, source)
    assert applicability == "unsupported"
    assert operand is None


def test_a_docstring_only_helper_body_still_resolves() -> None:
    """The one admitted extra statement is an inert docstring."""

    source = (
        _ROUND_SIX_HEAD
        + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + "\ndef emit(observed, expected):\n"
        + '    """Emission probability for one marker."""\n'
        + "    return 0.99 if observed == expected else 0.01\n\n"
        + "likelihood = math.prod(emit(int(item['call']), int(item['founder'])) for item in panel)\n"
        + "agreement = sum(1 if int(item['call']) == int(item['founder']) else 0 for item in panel)\n"
        + "n = len(rows)\n"
        + "rate = agreement / n\n"
        + "report = f'Of {n} markers, {agreement} agree at {rate:.6f}. Likelihood {likelihood:.8g}.'\n"
        + "Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"repaired"}


@pytest.mark.parametrize(
    "selector",
    [
        "BIG if int(row['call']) == int(row['founder']) else 1",
        "1 if int(row['call']) == int(row['founder']) else BIG",
        "[1, BIG][int(row['call']) == int(row['founder'])]",
        "(BIG + 1) if int(row['call']) == int(row['founder']) else 1",
    ],
)
def test_a_huge_selector_constant_abstains_without_a_crash(selector: str) -> None:
    """``float`` of a 401-digit literal raised OverflowError in v2.1.2."""

    big = "1" + "0" * 400
    source = (
        _ROUND_SIX_HEAD
        + "likelihood = math.prod(\n    "
        + selector.replace("BIG", big)
        + " for row in rows\n)\n"
        + _ROUND_SIX_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()
    applicability, operand = _fused_observation(_COUNTEREXAMPLE_REPORT, source)
    assert applicability == "unsupported"
    assert operand is None


def test_a_str_read_cast_over_a_numeric_rebuild_abstains() -> None:
    """The read-site cast overrides the stored proof; it never ORs with it.

    ``int(item['call']) == str(item['founder'])`` over a numerically rebuilt
    panel is constantly false at runtime, so the emission has no
    orientation; v2.1.2 classified it as the rebuild's parity.
    """

    source = (
        _ROUND_SIX_HEAD
        + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + "likelihood = math.prod(\n"
        + "    0.99 if int(item['call']) == str(item['founder']) else 0.01 for item in panel\n"
        + ")\n"
        + _ROUND_SIX_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


def test_arithmetic_in_a_selector_branch_abstains() -> None:
    """Branch constants must be simple literals; folding arithmetic in
    binary floats mis-ordered Decimal expressions against runtime (a
    demonstrated wrong answer), so no arithmetic is folded at all."""

    source = (
        "from fractions import Fraction\n"
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        "likelihood = math.prod(\n"
        "    Fraction(99, 100) * 1 if int(item['call']) == int(item['founder']) else 0.01\n"
        "    for item in panel\n"
        ")\n"
        "report = f'likelihood {likelihood}'\n"
        "Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


def test_an_extraction_helper_emission_abstains() -> None:
    """``value(item, 'call') == value(item, 'founder')`` reads identical
    names on both sides; the differing constants make it an emission the
    trace did not read, and letting the raw count answer for it was a
    demonstrated wrong answer."""

    source = (
        _ROUND_SIX_HEAD
        + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + "\ndef value(record, key):\n"
        + "    return int(record[key])\n\n"
        + "likelihood = math.prod(\n"
        + "    0.99 if value(item, 'call') == value(item, 'founder') else 0.01 for item in panel\n"
        + ")\n"
        + _ROUND_SIX_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()
    applicability, operand = _fused_observation(_COUNTEREXAMPLE_REPORT, source)
    assert applicability == "unsupported"
    assert operand is None


def test_decimal_arithmetic_in_a_mismatch_branch_abstains() -> None:
    """Binary-float folding read ``1e20 + 1 - 1e20`` as zero; Decimal gives 1."""

    source = (
        "from decimal import Decimal\n"
        + _ROUND_SIX_HEAD
        + "likelihood = math.prod(\n"
        + "    Decimal('0.5') if int(row['call']) == int(row['founder'])\n"
        + "    else Decimal('1e20') + Decimal('1') - Decimal('1e20')\n"
        + "    for row in rows\n"
        + ")\n"
        + _ROUND_SIX_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


def test_negative_branch_constants_abstain() -> None:
    """A negative pair orders differently in linear and log space."""

    source = (
        _ROUND_SIX_HEAD
        + "likelihood = math.prod(\n"
        + "    -0.01 if int(row['call']) == int(row['founder']) else -0.99 for row in rows\n"
        + ")\n"
        + _ROUND_SIX_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


# ---------------------------------------------------------------------------
# v2.1.4 controls: the sixth review round (independent Opus, whole-module).
# One family: a nested comprehension rebinding the enclosing target name has
# its own scope at runtime, and the trace classified its comparison against
# the outer iterable. Plus two degenerate-workflow closures.


_ROUND_SEVEN_HEAD = (
    "import csv\nimport math\nfrom pathlib import Path\n\n"
    "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
    "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
)
_ROUND_SEVEN_TAIL = (
    "report = f'emission likelihood {likelihood}'\nPath('results/report.md').write_text(report)\n"
)


@pytest.mark.parametrize(
    "body",
    [
        "likelihood = math.prod(\n"
        "    sum([0.99 if int(row['call']) == int(row['founder']) else 0.01"
        " for row in panel], 0)\n"
        "    for row in rows\n"
        ")\n",
        "likelihood = math.prod(\n"
        "    sum([0.99 if int(row['call']) == int(row['founder']) else 0.01"
        " for row in panel], 0) / len(panel)\n"
        "    for row in rows\n"
        ")\n",
        "likelihood = math.prod(\n"
        "    sum(sorted([0.99 if int(row['call']) == int(row['founder']) else 0.01"
        " for row in panel]), 0)\n"
        "    for row in rows\n"
        ")\n",
        "likelihood = 1.0\n"
        "for row in rows:\n"
        "    likelihood *= sum([0.99 if int(row['call']) == int(row['founder'])"
        " else 0.01 for row in panel], 0)\n",
    ],
)
def test_a_nested_comprehension_shadowing_the_target_abstains(body: str) -> None:
    """The inner ``for row in panel`` has its own scope; classifying its
    comparison against the outer iterable was a demonstrated wrong answer
    in both directions, including the natural marginalisation form."""

    source = _ROUND_SEVEN_HEAD + body + _ROUND_SEVEN_TAIL
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()
    applicability, operand = _fused_observation(_COUNTEREXAMPLE_REPORT, source)
    assert applicability == "unsupported"
    assert operand is None


def test_a_reader_iterator_consumed_twice_abstains() -> None:
    """The second pass over an unmaterialized DictReader iterates nothing."""

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "reader = csv.DictReader(Path('inputs/markers.csv').open())\n"
        "first = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in reader)\n"
        "likelihood = math.prod(\n"
        "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in reader\n"
        ")\n" + _ROUND_SEVEN_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


def test_a_str_of_not_recode_abstains() -> None:
    """``str(not x)`` is 'True'/'False'; no digit-string column equals it."""

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': str(not int(row['founder']))} for row in rows]\n"
        "likelihood = math.prod(\n"
        "    0.99 if str(int(item['call'])) == item['founder'] else 0.01 for item in panel\n"
        ")\n" + _ROUND_SEVEN_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


# v2.1.5: bypasses of the two round-six degenerate-workflow closures, found
# by the targeted verification. One indirection defeated each syntactic
# form: an alias for the reader, and a helper wrapping ``not``.


@pytest.mark.parametrize(
    "binding",
    [
        "alias = reader\n",
        "first = reader\nalias = first\n",
    ],
)
def test_an_aliased_reader_consumed_twice_abstains(binding: str) -> None:
    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "reader = csv.DictReader(Path('inputs/markers.csv').open())\n"
        + binding
        + "count = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in reader)\n"
        "likelihood = math.prod("
        "0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in alias)\n"
        "report = f'{count} likelihood {likelihood}'\n"
        "Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


def test_two_distinct_readers_each_consumed_once_still_resolve() -> None:
    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "first = csv.DictReader(Path('inputs/markers.csv').open())\n"
        "count = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in first)\n"
        "second = csv.DictReader(Path('inputs/markers.csv').open())\n"
        "likelihood = math.prod("
        "0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in second)\n"
        "report = f'{count} likelihood {likelihood}'\n"
        "Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"direct"}


@pytest.mark.parametrize(
    "body",
    [
        "    return not value\n",
        "    return not not value\n",
    ],
)
def test_a_helper_wrapped_not_inside_str_abstains(body: str) -> None:
    """The boolean taint follows the value, not the syntax."""

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "def flip(value):\n"
        + body
        + "\nrows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': str(flip(int(row['founder'])))} for row in rows]\n"
        "likelihood = math.prod(\n"
        "    0.99 if str(int(item['call'])) == item['founder'] else 0.01 for item in panel\n"
        ")\n"
        "report = f'likelihood {likelihood}'\n"
        "Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


def test_arithmetic_over_a_not_still_resolves() -> None:
    """``str(1 - (not int(x)))`` is a digit again; the taint clears."""

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': str(1 - (not int(row['founder'])))} for row in rows]\n"
        "likelihood = math.prod(\n"
        "    0.99 if str(int(item['call'])) == item['founder'] else 0.01 for item in panel\n"
        ")\n"
        "report = f'likelihood {likelihood}'\n"
        "Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"direct"}


# ---------------------------------------------------------------------------
# v2.2.0 controls: the five coverage extensions, each with its narrow form
# proven to resolve and each of its boundaries proven to abstain. The shapes
# are the ones a blind author wrote in the founder pilot-a lane, where v2.1.5
# abstained on the error-bearing case; every extension is admitted in one
# exact form, so these boundary controls are what keeps the widening from
# becoming a deny-list again.


_V220_HEAD = (
    "import csv\n"
    "import pathlib\n"
    "\n"
    "CALL_COLUMN = 'call'\n"
    "FOUNDER_COLUMN = 'founder'\n"
    "PANEL_BASELINE = 1\n"
    "SELECTOR_MATCH = 1\n"
    "SELECTOR_MISMATCH = 0\n"
    "\n"
    "\n"
    "def agreement_selector(observed_value, reference_value):\n"
    "    match_flag = observed_value == reference_value\n"
    "    return SELECTOR_MISMATCH + (SELECTOR_MATCH - SELECTOR_MISMATCH) * match_flag\n"
    "\n"
    "\n"
    "data_path = pathlib.Path('inputs/markers.csv')\n"
    "csv_lines = data_path.read_text(encoding='ascii').splitlines()\n"
    "rows = [record for record in csv.DictReader(csv_lines)]\n"
)
_V220_TAIL = (
    "n = len(rows)\n"
    "rate = total / n\n"
    "report = f'Of {n} markers, {total} agree at {rate:.6f}.'\n"
    "pathlib.Path('results/report.md').write_text(report)\n"
)
_V220_LOOP = (
    "total = 0\nfor pair in pairs:\n    total = total + agreement_selector(pair[0], pair[1])\n"
)
_V220_REPAIRED_LISTS = (
    "call_values = [int(record[CALL_COLUMN]) for record in rows]\n"
    "founder_values = [PANEL_BASELINE - int(record[FOUNDER_COLUMN]) for record in rows]\n"
)
_V220_DIRECT_LISTS = (
    "call_values = [int(record[CALL_COLUMN]) for record in rows]\n"
    "founder_values = [int(record[FOUNDER_COLUMN]) for record in rows]\n"
)


def _v220_workflow(
    *,
    head: str = _V220_HEAD,
    lists: str = _V220_REPAIRED_LISTS,
    pairing: str = "pairs = zip(call_values, founder_values)\n",
    loop: str = _V220_LOOP,
) -> str:
    return head + lists + pairing + loop + _V220_TAIL


@pytest.mark.parametrize(
    ("pairing", "label"),
    [
        ("pairs = zip(call_values, founder_values)\n", "bare zip"),
        ("pairs = list(zip(call_values, founder_values))\n", "materialized zip"),
        (
            "pairs = [pair for pair in zip(call_values, founder_values)]\n",
            "identity comprehension over zip",
        ),
    ],
)
def test_a_column_value_pairing_resolves(pairing: str, label: str) -> None:
    """Extensions one through five together, in the pilot's own shape.

    One workflow exercises all of them: the reader reads a ``read_text``
    chain through a single-assignment name, the column names and the
    involutive constant are module constants, the two column-values lists
    pair through ``zip``, and the accumulated payload is a helper whose body
    binds its comparison to one local before returning an arithmetic-encoded
    selector.
    """

    unsupported, states = _resolve(_v220_workflow(pairing=pairing))
    assert not unsupported, label
    assert states == {"repaired"}, label


def test_a_column_value_pairing_without_a_recode_reads_as_direct() -> None:
    """The direct reading is proven, not a fallthrough: same shape, no recode."""

    unsupported, states = _resolve(_v220_workflow(lists=_V220_DIRECT_LISTS))
    assert not unsupported
    assert states == {"direct"}


def test_an_inline_read_text_chain_resolves() -> None:
    """Extension one without the intermediate name."""

    head = _V220_HEAD.replace(
        "data_path = pathlib.Path('inputs/markers.csv')\n"
        "csv_lines = data_path.read_text(encoding='ascii').splitlines()\n"
        "rows = [record for record in csv.DictReader(csv_lines)]\n",
        "rows = [record for record in csv.DictReader("
        "pathlib.Path('inputs/markers.csv').read_text(encoding='ascii').splitlines())]\n",
    )
    unsupported, states = _resolve(_v220_workflow(head=head))
    assert not unsupported
    assert states == {"repaired"}


def test_a_non_literal_read_text_keyword_abstains() -> None:
    """A keyword that is not a string literal is an expression, not a policy."""

    head = _V220_HEAD.replace(
        "SELECTOR_MISMATCH = 0\n", "SELECTOR_MISMATCH = 0\nTEXT_ENCODING = 'ascii'\n"
    ).replace("read_text(encoding='ascii')", "read_text(encoding=TEXT_ENCODING)")
    unsupported, states = _resolve(_v220_workflow(head=head))
    assert unsupported
    assert states == set()


def test_a_read_text_chain_on_a_rebound_path_name_abstains() -> None:
    """Last binding wins: a path name rebound to a string opens no chain."""

    head = _V220_HEAD.replace(
        "data_path = pathlib.Path('inputs/markers.csv')\n",
        "data_path = pathlib.Path('inputs/markers.csv')\ndata_path = 'inputs/markers.csv'\n",
    )
    unsupported, states = _resolve(_v220_workflow(head=head))
    assert unsupported
    assert states == set()


_V220_NAMED_CONSTANT_HEAD = (
    "import csv\nimport math\nfrom pathlib import Path\n\n"
    "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
    "MATCH = 0.99\n"
    "MISMATCH = 0.01\n"
    "ONE = 1\n"
    "panel = [{**row, 'founder': ONE - int(row['founder'])} for row in rows]\n"
)
_V220_NAMED_CONSTANT_TAIL = (
    "agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in panel)\n"
    "n = len(rows)\n"
    "rate = agreement / n\n"
    "report = f'Of {n} markers, {agreement} agree at {rate:.6f}. Likelihood {likelihood:.8g}.'\n"
    "Path('results/report.md').write_text(report)\n"
)


@pytest.mark.parametrize(
    "selector",
    [
        "MATCH if int(row['call']) == int(row['founder']) else MISMATCH",
        "[MISMATCH, MATCH][int(row['call']) == int(row['founder'])]",
        "MISMATCH + (MATCH - MISMATCH) * (int(row['call']) == int(row['founder']))",
        "MISMATCH + (MATCH - MISMATCH) * int(int(row['call']) == int(row['founder']))",
        "MISMATCH + (MATCH - MISMATCH) * bool(int(row['call']) == int(row['founder']))",
    ],
)
def test_single_assignment_named_branch_values_resolve(selector: str) -> None:
    """The v2.2.0 ruling on ``named_branch_values``.

    Through v2.1.5 a name in a branch position was an unprovable constant and
    every selector holding one abstained. A name assigned exactly once in the
    whole module to a literal is provable, so it now resolves, and the
    canonicity rule then judges the resolved values exactly as it judges
    literals. The involutive constant ``ONE`` resolves in the same way.
    """

    source = (
        _V220_NAMED_CONSTANT_HEAD
        + "likelihood = math.prod(\n    "
        + selector
        + " for row in panel\n)\n"
        + _V220_NAMED_CONSTANT_TAIL
    )
    unsupported, states = _resolve(source)
    assert not unsupported, selector
    assert states == {"repaired"}, selector


@pytest.mark.parametrize(
    ("rebinding", "label"),
    [
        ("MATCH = 0.99\n", "rebound to the same literal"),
        ("MATCH = 0.98\n", "rebound to another literal"),
        ("for MATCH in rows:\n    pass\n", "rebound as a loop target"),
    ],
)
def test_a_twice_assigned_branch_name_still_abstains(rebinding: str, label: str) -> None:
    """The counter-test to the ruling above: one binding, or nothing.

    A second binding anywhere in the module, under any binding form, makes
    the name's value a question about execution order, and an unprovable
    branch value leaves the selector non-canonical exactly as before.
    """

    source = (
        _V220_NAMED_CONSTANT_HEAD + rebinding + "likelihood = math.prod(\n"
        "    MATCH if int(row['call']) == int(row['founder']) else MISMATCH for row in panel\n"
        ")\n" + _V220_NAMED_CONSTANT_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported, label
    assert states == set(), label


def test_a_twice_assigned_involutive_constant_still_abstains() -> None:
    """``ONE - x`` is a recode only while ``ONE`` provably holds one."""

    source = (
        _V220_NAMED_CONSTANT_HEAD.replace("ONE = 1\n", "ONE = 1\nONE = 1\n")
        + "likelihood = math.prod(\n"
        "    MATCH if int(row['call']) == int(row['founder']) else MISMATCH for row in panel\n"
        ")\n" + _V220_NAMED_CONSTANT_TAIL
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


def test_a_twice_assigned_column_constant_abstains() -> None:
    """A column name behind a rebound name names no column."""

    head = _V220_HEAD.replace(
        "FOUNDER_COLUMN = 'founder'\n", "FOUNDER_COLUMN = 'founder'\nCALL_COLUMN = 'call'\n"
    )
    unsupported, states = _resolve(_v220_workflow(head=head))
    assert unsupported
    assert states == set()


def test_a_zip_across_two_row_sets_abstains() -> None:
    """Two staged reads are two orders; pairing them proves nothing."""

    head = _V220_HEAD + (
        "path_b = pathlib.Path('inputs/panel.csv')\n"
        "lines_b = path_b.read_text(encoding='ascii').splitlines()\n"
        "rows_b = [record for record in csv.DictReader(lines_b)]\n"
    )
    lists = (
        "call_values = [int(record[CALL_COLUMN]) for record in rows]\n"
        "founder_values = [PANEL_BASELINE - int(record[FOUNDER_COLUMN]) for record in rows_b]\n"
    )
    unsupported, states = _resolve(_v220_workflow(head=head, lists=lists))
    assert unsupported
    assert states == set()


def test_a_zip_across_an_alias_of_one_row_set_abstains() -> None:
    """The name is the only identity two lists can be proven to share.

    ``other = rows`` is one runtime list under two names, but proving that
    two differently named iterables walk the same rows in the same order is
    beyond this trace, so the over-strict answer is the sound one.
    """

    head = _V220_HEAD + "other = rows\n"
    lists = (
        "call_values = [int(record[CALL_COLUMN]) for record in rows]\n"
        "founder_values = [PANEL_BASELINE - int(record[FOUNDER_COLUMN]) for record in other]\n"
    )
    unsupported, states = _resolve(_v220_workflow(head=head, lists=lists))
    assert unsupported
    assert states == set()


def test_a_filtered_column_value_list_abstains() -> None:
    """A filtered list is shorter than its sibling; zip would pair strangers."""

    lists = (
        "call_values = [int(record[CALL_COLUMN]) for record in rows if record[CALL_COLUMN]]\n"
        "founder_values = [PANEL_BASELINE - int(record[FOUNDER_COLUMN]) for record in rows]\n"
    )
    unsupported, states = _resolve(_v220_workflow(lists=lists))
    assert unsupported
    assert states == set()


def test_a_rebound_column_value_list_abstains() -> None:
    """Single assignment is what makes the list's column claim durable."""

    lists = _V220_REPAIRED_LISTS + "founder_values = founder_values\n"
    unsupported, states = _resolve(_v220_workflow(lists=lists))
    assert unsupported
    assert states == set()


@pytest.mark.parametrize(
    ("index", "label"),
    [
        ("pair[POSITION]", "a name, even a module constant, is not an integer literal"),
        ("pair[2]", "an index outside the pair"),
        ("pair[-1]", "a negative index"),
    ],
)
def test_a_pair_read_outside_the_two_integer_literals_abstains(index: str, label: str) -> None:
    head = _V220_HEAD.replace("PANEL_BASELINE = 1\n", "PANEL_BASELINE = 1\nPOSITION = 0\n")
    loop = (
        f"total = 0\nfor pair in pairs:\n    total = total + agreement_selector({index}, pair[1])\n"
    )
    unsupported, states = _resolve(_v220_workflow(head=head, loop=loop))
    assert unsupported, label
    assert states == set(), label


def test_a_tuple_unpacked_pair_abstains() -> None:
    """Tuple targets were never a whitelisted assignment form and still are not."""

    loop = (
        "total = 0\n"
        "for pair in pairs:\n"
        "    observed, reference = pair\n"
        "    total = total + agreement_selector(observed, reference)\n"
    )
    unsupported, states = _resolve(_v220_workflow(loop=loop))
    assert unsupported
    assert states == set()


@pytest.mark.parametrize(
    ("body", "label"),
    [
        (
            "    reference_value = PANEL_BASELINE - reference_value\n"
            "    match_flag = observed_value == reference_value\n"
            "    return SELECTOR_MISMATCH + (SELECTOR_MATCH - SELECTOR_MISMATCH) * match_flag\n",
            "a recode before the flag binding",
        ),
        (
            "    observed_value = observed_value == reference_value\n"
            "    return SELECTOR_MISMATCH"
            " + (SELECTOR_MATCH - SELECTOR_MISMATCH) * observed_value\n",
            "the flag bound onto a parameter name",
        ),
        (
            "    match_flag = observed_value == reference_value\n"
            "    scaled = SELECTOR_MATCH - SELECTOR_MISMATCH\n"
            "    return SELECTOR_MISMATCH + scaled * match_flag\n",
            "a second local before the return",
        ),
    ],
)
def test_a_helper_body_beyond_the_one_flag_binding_abstains(body: str, label: str) -> None:
    """One optional docstring, one flag binding, one return. Nothing else."""

    head = _V220_HEAD.replace(
        "    match_flag = observed_value == reference_value\n"
        "    return SELECTOR_MISMATCH + (SELECTOR_MATCH - SELECTOR_MISMATCH) * match_flag\n",
        body,
    )
    unsupported, states = _resolve(_v220_workflow(head=head))
    assert unsupported, label
    assert states == set(), label


def test_a_helper_docstring_before_the_flag_binding_still_resolves() -> None:
    head = _V220_HEAD.replace(
        "    match_flag = observed_value == reference_value\n",
        '    """Two-valued agreement selector."""\n'
        "    match_flag = observed_value == reference_value\n",
    )
    unsupported, states = _resolve(_v220_workflow(head=head))
    assert not unsupported
    assert states == {"repaired"}


@pytest.mark.parametrize(
    "return_statement",
    [
        "    return SELECTOR_MATCH if match_flag else SELECTOR_MISMATCH\n",
        "    return [SELECTOR_MISMATCH, SELECTOR_MATCH][match_flag]\n",
        "    return SELECTOR_MISMATCH + (SELECTOR_MATCH - SELECTOR_MISMATCH) * match_flag\n",
    ],
)
def test_every_canonical_selector_form_reads_the_helper_flag(return_statement: str) -> None:
    head = _V220_HEAD.replace(
        "    return SELECTOR_MISMATCH + (SELECTOR_MATCH - SELECTOR_MISMATCH) * match_flag\n",
        return_statement,
    )
    unsupported, states = _resolve(_v220_workflow(head=head))
    assert not unsupported, return_statement
    assert states == {"repaired"}, return_statement


@pytest.mark.parametrize(
    ("head_edit", "label"),
    [
        (("SELECTOR_MISMATCH = 0\n", "SELECTOR_MISMATCH = int('0')\n"), "unresolved mismatch"),
        (("SELECTOR_MATCH = 1\n", "SELECTOR_MATCH = int('1')\n"), "unresolved match"),
        (
            (
                "SELECTOR_MATCH = 1\nSELECTOR_MISMATCH = 0\n",
                "SELECTOR_MATCH = 0\nSELECTOR_MISMATCH = 1\n",
            ),
            "swapped polarity",
        ),
    ],
)
def test_an_arithmetic_selector_with_unusable_constants_abstains(
    head_edit: tuple[str, str], label: str
) -> None:
    """``A + (B - A) * FLAG`` is a selector only when A and B are provable and ordered."""

    head = _V220_HEAD.replace(*head_edit)
    unsupported, states = _resolve(_v220_workflow(head=head))
    assert unsupported, label
    assert states == set(), label


def test_an_arithmetic_selector_whose_repeated_constant_differs_abstains() -> None:
    """The mismatch constant must stand in both of its positions."""

    head = _V220_HEAD.replace(
        "SELECTOR_MISMATCH = 0\n", "SELECTOR_MISMATCH = 0\nSELECTOR_OTHER = 0.5\n"
    ).replace(
        "(SELECTOR_MATCH - SELECTOR_MISMATCH) * match_flag",
        "(SELECTOR_MATCH - SELECTOR_OTHER) * match_flag",
    )
    unsupported, states = _resolve(_v220_workflow(head=head))
    assert unsupported
    assert states == set()


def test_an_arithmetic_selector_outside_its_exact_shape_abstains() -> None:
    """Only ``A + (B - A) * FLAG`` is modelled; the commuted product is not."""

    head = _V220_HEAD.replace(
        "SELECTOR_MISMATCH + (SELECTOR_MATCH - SELECTOR_MISMATCH) * match_flag",
        "SELECTOR_MISMATCH + match_flag * (SELECTOR_MATCH - SELECTOR_MISMATCH)",
    )
    unsupported, states = _resolve(_v220_workflow(head=head))
    assert unsupported
    assert states == set()


# v2.2.1: the v2.2.0 verification round's two closures.


def test_a_zip_over_a_rebound_row_source_abstains() -> None:
    """Rebinding the row-set name between list constructions pairs columns
    from two different staged reads; the source name must be bound once."""

    source = (
        "import csv\nimport math\nimport pathlib\n\n"
        "CALL_COLUMN = 'call'\n"
        "FOUNDER_COLUMN = 'founder'\n"
        "PANEL_BASELINE = 1\n\n"
        "lines_a = pathlib.Path('inputs/markers.csv').read_text(encoding='ascii').splitlines()\n"
        "lines_b = pathlib.Path('inputs/panel.csv').read_text(encoding='ascii').splitlines()\n"
        "rows = [record for record in csv.DictReader(lines_a)]\n"
        "call_values = [int(record[CALL_COLUMN]) for record in rows]\n"
        "rows = [record for record in csv.DictReader(lines_b)]\n"
        "founder_values = [PANEL_BASELINE - int(record[FOUNDER_COLUMN]) for record in rows]\n"
        "pairs = zip(call_values, founder_values)\n"
        "emission_value = 0\n"
        "for pair in pairs:\n"
        "    emission_value = emission_value + (0 + (1 - 0) * (pair[0] == pair[1]))\n"
        "report_text = f'Of 4 markers, {emission_value} agree.'\n"
        "pathlib.Path('results/report.md').write_text(report_text)\n"
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


def test_a_chained_comparison_emission_abstains() -> None:
    """``a == b == 1`` is outside every classifier; a decoy count answered."""

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        "agreement = sum(1 if int(row['call']) == int(row['founder']) else 0 for row in rows)\n"
        "flags = [int(item['call']) == int(item['founder']) == 1 for item in panel]\n"
        "likelihood = math.prod(0.99 if flag else 0.01 for flag in flags)\n"
        "n = len(rows)\n"
        "report = f'{agreement} of {n}. Likelihood {likelihood:.8g}.'\n"
        "Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert unsupported
    assert states == set()


def test_a_chained_range_check_filter_still_resolves() -> None:
    """``0 <= x <= 1`` reads one name; the belt leaves it alone."""

    source = (
        "import csv\nimport math\nfrom pathlib import Path\n\n"
        "rows = list(csv.DictReader(Path('inputs/markers.csv').open()))\n"
        "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        "likelihood = math.prod(\n"
        "    0.99 if int(item['call']) == int(item['founder']) else 0.01\n"
        "    for item in panel\n"
        "    if 0 <= int(item['call']) <= 1\n"
        ")\n"
        "report = f'Likelihood {likelihood:.8g}.'\n"
        "Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"repaired"}


# v2.2.2: the pilot-b coverage extensions.
#
# The fixture below is the pilot-b error-bearing workflow's shape, reduced to
# what the four new forms need: a loader that opens a handle, reads it through
# a ``dict(row)`` rebuild and closes it; two one-parameter helpers that each
# extract one column, one of them through the involution; and a two-parameter
# selector helper whose return is the multiply-complement encoding. Every
# boundary test below is one edit away from it.

_V222_SOURCE = (
    "import csv\n"
    "import pathlib\n"
    "\n"
    "DATA_PATH = pathlib.Path('inputs/markers.csv')\n"
    "CALL_COLUMN = 'call'\n"
    "FOUNDER_COLUMN = 'founder'\n"
    "PANEL_BASELINE = 1\n"
    "SELECTOR_MATCH = 1\n"
    "SELECTOR_MISMATCH = 0\n"
    "\n"
    "\n"
    "def load_table(source_path):\n"
    "    handle = source_path.open('r', encoding='ascii', newline='')\n"
    "    reader = csv.DictReader(handle)\n"
    "    staged_rows = [dict(entry) for entry in reader]\n"
    "    closed = handle.close()\n"
    "    return staged_rows\n"
    "\n"
    "\n"
    "def observed_state(entry):\n"
    "    return int(entry[CALL_COLUMN])\n"
    "\n"
    "\n"
    "def panel_state(entry):\n"
    "    staged_value = int(entry[FOUNDER_COLUMN])\n"
    "    return PANEL_BASELINE - staged_value\n"
    "\n"
    "\n"
    "def agreement_selector(observed_value, reference_value):\n"
    "    match_flag = observed_value == reference_value\n"
    "    return SELECTOR_MATCH * match_flag + SELECTOR_MISMATCH * (1 - match_flag)\n"
    "\n"
    "\n"
    "rows = load_table(DATA_PATH)\n"
    "total = 0\n"
    "for record in rows:\n"
    "    total = total + agreement_selector(observed_state(record), panel_state(record))\n"
    "n = len(rows)\n"
    "rate = total / n\n"
    "report = f'Of {n} markers, {total} agree at {rate:.6f}.'\n"
    "pathlib.Path('results/report.md').write_text(report)\n"
)


def _v222_workflow(*replacements: tuple[str, str]) -> str:
    source = _V222_SOURCE
    for old, new in replacements:
        assert old in source, old
        source = source.replace(old, new)
    return source


def test_the_v222_extensions_resolve_together() -> None:
    """All four forms in one workflow, in the pilot-b shape."""

    unsupported, states = _resolve(_v222_workflow())
    assert not unsupported
    assert states == {"repaired"}


def test_the_v222_workflow_without_the_involution_reads_direct() -> None:
    """The same workflow comparing both columns as staged."""

    unsupported, states = _resolve(
        _v222_workflow(("    return PANEL_BASELINE - staged_value\n", "    return staged_value\n"))
    )
    assert not unsupported
    assert states == {"direct"}


# Extension one: the identity row copy.


def test_a_dict_row_copy_with_a_second_entry_abstains() -> None:
    """``dict(row)`` is the identity rebuild; ``dict(row, extra=...)`` is not."""

    unsupported, states = _resolve(
        _v222_workflow(
            ("dict(entry) for entry in reader", "dict(entry, call='1') for entry in reader")
        )
    )
    assert unsupported
    assert states == set()


def test_a_dict_copy_of_something_other_than_the_loop_variable_abstains() -> None:
    """The one argument must be the row the comprehension is iterating."""

    unsupported, states = _resolve(
        _v222_workflow(("dict(entry) for entry in reader", "dict(source_path) for entry in reader"))
    )
    assert unsupported
    assert states == set()


# Extension two: the file-handle close.


def test_a_bare_handle_close_statement_resolves() -> None:
    """``close`` is admitted as a statement as well as an assignment source."""

    unsupported, states = _resolve(
        _v222_workflow(("    closed = handle.close()\n", "    handle.close()\n"))
    )
    assert not unsupported
    assert states == {"repaired"}


def test_a_handle_close_inside_a_with_block_resolves() -> None:
    """The ``with``-``as`` target is a modelled handle binding too."""

    loader = (
        "def load_table(source_path):\n"
        "    with source_path.open('r', encoding='ascii', newline='') as handle:\n"
        "        reader = csv.DictReader(handle)\n"
        "        staged_rows = [dict(entry) for entry in reader]\n"
        "        handle.close()\n"
        "    return staged_rows\n"
    )
    original = (
        "def load_table(source_path):\n"
        "    handle = source_path.open('r', encoding='ascii', newline='')\n"
        "    reader = csv.DictReader(handle)\n"
        "    staged_rows = [dict(entry) for entry in reader]\n"
        "    closed = handle.close()\n"
        "    return staged_rows\n"
    )
    unsupported, states = _resolve(_v222_workflow((original, loader)))
    assert not unsupported
    assert states == {"repaired"}


def test_close_on_a_receiver_the_open_pattern_never_bound_abstains() -> None:
    """A handle is a name the modelled ``open()`` bound, and nothing else."""

    unsupported, states = _resolve(
        _v222_workflow(
            (
                "    handle = source_path.open('r', encoding='ascii', newline='')\n",
                "    handle = source_path\n",
            )
        )
    )
    assert unsupported
    assert states == set()


def test_a_handle_method_other_than_close_abstains() -> None:
    """``read`` and ``readlines`` deliver contents; they are not modelled."""

    unsupported, states = _resolve(
        _v222_workflow(("closed = handle.close()", "closed = handle.readlines()"))
    )
    assert unsupported
    assert states == set()


# Extension three: the one-parameter column-extraction helper.


def test_a_column_extraction_helper_with_two_locals_abstains() -> None:
    """The body is one optional local and one return, in that shape only."""

    unsupported, states = _resolve(
        _v222_workflow(
            (
                "    staged_value = int(entry[FOUNDER_COLUMN])\n"
                "    return PANEL_BASELINE - staged_value\n",
                "    staged_value = int(entry[FOUNDER_COLUMN])\n"
                "    flipped_value = PANEL_BASELINE - staged_value\n"
                "    return flipped_value\n",
            )
        )
    )
    assert unsupported
    assert states == set()


def test_a_column_extraction_helper_that_rebinds_its_parameter_abstains() -> None:
    """A rebound parameter makes the return read a value the caller never sent."""

    unsupported, states = _resolve(
        _v222_workflow(
            (
                "    staged_value = int(entry[FOUNDER_COLUMN])\n"
                "    return PANEL_BASELINE - staged_value\n",
                "    entry = dict(entry)\n    return PANEL_BASELINE - int(entry[FOUNDER_COLUMN])\n",
            )
        )
    )
    assert unsupported
    assert states == set()


def test_a_one_parameter_helper_returning_no_column_abstains() -> None:
    """A helper that reads no column of the row it was handed is not an extraction."""

    unsupported, states = _resolve(
        _v222_workflow(
            (
                "    staged_value = int(entry[FOUNDER_COLUMN])\n"
                "    return PANEL_BASELINE - staged_value\n",
                "    return PANEL_BASELINE\n",
            )
        )
    )
    assert unsupported
    assert states == set()


def test_a_second_parameter_leaves_the_extraction_helper_unrecognized() -> None:
    """Exactly one plain parameter, taking exactly the row."""

    unsupported, states = _resolve(
        _v222_workflow(
            (
                "def panel_state(entry):\n"
                "    staged_value = int(entry[FOUNDER_COLUMN])\n"
                "    return PANEL_BASELINE - staged_value\n",
                "def panel_state(entry, baseline):\n"
                "    staged_value = int(entry[FOUNDER_COLUMN])\n"
                "    return baseline - staged_value\n",
            ),
            ("panel_state(record)", "panel_state(record, PANEL_BASELINE)"),
        )
    )
    assert unsupported
    assert states == set()


def test_a_keyword_call_to_an_extraction_helper_abstains() -> None:
    """The call is one positional argument; a keyword is outside the shape."""

    unsupported, states = _resolve(
        _v222_workflow(("panel_state(record)", "panel_state(entry=record)"))
    )
    assert unsupported
    assert states == set()


# Extension four: the multiply-complement selector.


def test_the_multiply_complement_selector_commutes_its_addends() -> None:
    """``B * (1 - FLAG) + A * FLAG`` is the same selector written the other way."""

    unsupported, states = _resolve(
        _v222_workflow(
            (
                "SELECTOR_MATCH * match_flag + SELECTOR_MISMATCH * (1 - match_flag)",
                "SELECTOR_MISMATCH * (1 - match_flag) + SELECTOR_MATCH * match_flag",
            )
        )
    )
    assert not unsupported
    assert states == {"repaired"}


def test_a_multiply_complement_selector_over_an_inline_flag_resolves() -> None:
    """The flag may be written out in both products when the two agree.

    The two comparison nodes are one flag, so the second is recognized with
    the first and the module-wide emission belt is satisfied.
    """

    comparison = "(int(record[CALL_COLUMN]) == PANEL_BASELINE - int(record[FOUNDER_COLUMN]))"
    source = (
        "import csv\n"
        "import pathlib\n"
        "\n"
        "CALL_COLUMN = 'call'\n"
        "FOUNDER_COLUMN = 'founder'\n"
        "PANEL_BASELINE = 1\n"
        "SELECTOR_MATCH = 1\n"
        "SELECTOR_MISMATCH = 0\n"
        "\n"
        "rows = list(csv.DictReader(pathlib.Path('inputs/markers.csv').open()))\n"
        "total = sum(\n"
        f"    SELECTOR_MATCH * {comparison}\n"
        f"    + SELECTOR_MISMATCH * (1 - {comparison})\n"
        "    for record in rows\n"
        ")\n"
        "n = len(rows)\n"
        "rate = total / n\n"
        "report = f'Of {n} markers, {total} agree at {rate:.6f}.'\n"
        "pathlib.Path('results/report.md').write_text(report)\n"
    )
    unsupported, states = _resolve(source)
    assert not unsupported
    assert states == {"repaired"}


def test_a_complement_that_is_not_one_minus_the_flag_abstains() -> None:
    """The complement is exactly one minus the flag; ``2 - FLAG`` is not."""

    unsupported, states = _resolve(
        _v222_workflow(
            (
                "SELECTOR_MISMATCH = 0\n",
                "SELECTOR_MISMATCH = 0\nCOMPLEMENT_BASE = 2\n",
            ),
            (
                "SELECTOR_MISMATCH * (1 - match_flag)",
                "SELECTOR_MISMATCH * (COMPLEMENT_BASE - match_flag)",
            ),
        )
    )
    assert unsupported
    assert states == set()


def test_two_different_flags_in_the_two_products_abstain() -> None:
    """Both products must carry one and the same flag expression."""

    unsupported, states = _resolve(
        _v222_workflow(
            (
                "SELECTOR_MISMATCH * (1 - match_flag)",
                "SELECTOR_MISMATCH * (1 - (reference_value == observed_value))",
            )
        )
    )
    assert unsupported
    assert states == set()


def test_a_flag_left_of_its_multiply_abstains() -> None:
    """The branch constant stands left of the multiply in both products."""

    unsupported, states = _resolve(
        _v222_workflow(
            (
                "SELECTOR_MATCH * match_flag + SELECTOR_MISMATCH * (1 - match_flag)",
                "match_flag * SELECTOR_MATCH + SELECTOR_MISMATCH * (1 - match_flag)",
            )
        )
    )
    assert unsupported
    assert states == set()


def test_a_multiply_complement_selector_with_swapped_branches_abstains() -> None:
    """The canonicity rule is unchanged: the match branch must be the larger."""

    unsupported, states = _resolve(
        _v222_workflow(
            (
                "SELECTOR_MATCH * match_flag + SELECTOR_MISMATCH * (1 - match_flag)",
                "SELECTOR_MISMATCH * match_flag + SELECTOR_MATCH * (1 - match_flag)",
            )
        )
    )
    assert unsupported
    assert states == set()


# v2.2.3: the pilot-c coverage extensions.
#
# The fixture below is the pilot-c error-bearing workflow's shape, reduced to
# what the ten new forms need: exact-numeric module constants in the selector
# branches, a loader and a writer whose path parameters are proven at their
# call sites, a ``read_text`` result read through a name, a bare ``mkdir``, a
# report write routed through a helper, an elementwise recode of a
# column-values list, a ``range``-indexed pairing, two accumulation loops, and
# a ``print`` carrying a keyword argument. Every boundary test below is one
# edit away from it.

_V223_SOURCE = (
    "import csv\n"
    "from decimal import Decimal\n"
    "from fractions import Fraction\n"
    "from pathlib import Path\n"
    "\n"
    "DATA_PATH = Path('inputs/markers.csv')\n"
    "REPORT_PATH = Path('results/report.md')\n"
    "CALL_COLUMN = 'call'\n"
    "FOUNDER_COLUMN = 'founder'\n"
    "PANEL_BASELINE = 1\n"
    "MATCH_WEIGHT = Fraction(1, 1)\n"
    "MISS_WEIGHT = Fraction(1, 4)\n"
    "\n"
    "\n"
    "def read_table(source_path):\n"
    "    raw_text = source_path.read_text(encoding='ascii')\n"
    "    reader = csv.DictReader(raw_text.splitlines())\n"
    "    return [dict(record) for record in reader]\n"
    "\n"
    "\n"
    "def panel_indicator(marker_value):\n"
    "    return PANEL_BASELINE - marker_value\n"
    "\n"
    "\n"
    "def concordance_weight(observed_value, panel_value):\n"
    "    match_flag = observed_value == panel_value\n"
    "    return MISS_WEIGHT + (MATCH_WEIGHT - MISS_WEIGHT) * match_flag\n"
    "\n"
    "\n"
    "def write_report(target_path, payload_text):\n"
    "    target_path.parent.mkdir(parents=True, exist_ok=True)\n"
    "    return target_path.write_text(payload_text, encoding='ascii')\n"
    "\n"
    "\n"
    "table_rows = read_table(DATA_PATH)\n"
    "unit_count = len(table_rows)\n"
    "observed_calls = [int(record[CALL_COLUMN]) for record in table_rows]\n"
    "panel_markers = [int(record[FOUNDER_COLUMN]) for record in table_rows]\n"
    "panel_values = [panel_indicator(marker_value) for marker_value in panel_markers]\n"
    "weight_values = [\n"
    "    concordance_weight(observed_calls[position], panel_values[position])\n"
    "    for position in range(unit_count)\n"
    "]\n"
    "emission_total = 0\n"
    "for weight_value in weight_values:\n"
    "    emission_total = emission_total + weight_value\n"
    "panel_positive_total = 0\n"
    "for panel_entry in panel_values:\n"
    "    panel_positive_total = panel_positive_total + panel_entry\n"
    "rate = emission_total / unit_count\n"
    "report_text = f'Of {unit_count} markers, {panel_positive_total} carry the marker "
    "at {rate:.6f}.'\n"
    "written_length = write_report(REPORT_PATH, report_text)\n"
    "print(report_text, end='')\n"
)

_V223_LOADER = (
    "    raw_text = source_path.read_text(encoding='ascii')\n"
    "    reader = csv.DictReader(raw_text.splitlines())\n"
)
_V223_RECODE = "panel_values = [panel_indicator(marker_value) for marker_value in panel_markers]\n"
_V223_COLUMN_LOOP = (
    "panel_positive_total = 0\n"
    "for panel_entry in panel_values:\n"
    "    panel_positive_total = panel_positive_total + panel_entry\n"
)
_V223_ACCUMULATION = (
    "emission_total = 0\n"
    "for weight_value in weight_values:\n"
    "    emission_total = emission_total + weight_value\n"
)
_V223_WRITE_HELPER = (
    "def write_report(target_path, payload_text):\n"
    "    target_path.parent.mkdir(parents=True, exist_ok=True)\n"
    "    return target_path.write_text(payload_text, encoding='ascii')\n"
    "\n"
    "\n"
)


def _v223_workflow(*replacements: tuple[str, str]) -> str:
    source = _V223_SOURCE
    for old, new in replacements:
        assert old in source, old
        source = source.replace(old, new)
    return source


def test_the_v223_extensions_resolve_together() -> None:
    """All ten forms in one workflow, in the pilot-c shape."""

    unsupported, states = _resolve(_v223_workflow())
    assert not unsupported
    assert states == {"repaired"}


def test_the_v223_workflow_without_the_recode_reads_direct() -> None:
    """The direct reading is proven, not a fallthrough: same shape, no recode."""

    unsupported, states = _resolve(
        _v223_workflow(("    return PANEL_BASELINE - marker_value\n", "    return marker_value\n"))
    )
    assert not unsupported
    assert states == {"direct"}


# Extension one: exact-numeric module constants in selector branches.


def test_decimal_module_constants_resolve_in_selector_branches() -> None:
    """``Decimal('s')`` reads in a branch position exactly as ``Fraction(a, b)`` does."""

    unsupported, states = _resolve(
        _v223_workflow(
            (
                "MATCH_WEIGHT = Fraction(1, 1)\nMISS_WEIGHT = Fraction(1, 4)\n",
                "MATCH_WEIGHT = Decimal('1.00')\nMISS_WEIGHT = Decimal('0.25')\n",
            )
        )
    )
    assert not unsupported
    assert states == {"repaired"}


def test_a_non_literal_exact_numeric_constructor_abstains() -> None:
    """The constructor's arguments are literals; a named denominator is an expression."""

    unsupported, states = _resolve(
        _v223_workflow(
            ("PANEL_BASELINE = 1\n", "PANEL_BASELINE = 1\nMISS_DENOMINATOR = 4\n"),
            ("MISS_WEIGHT = Fraction(1, 4)\n", "MISS_WEIGHT = Fraction(1, MISS_DENOMINATOR)\n"),
        )
    )
    assert unsupported
    assert states == set()


def test_an_exact_numeric_constant_is_not_the_involution_literal() -> None:
    """These constants resolve in selector branches and nowhere else.

    ``Fraction(1, 1) - marker_value`` is not read as the involution the recode
    vocabulary tests for, so the panel column stays unresolved rather than
    being reported as a repair on the strength of a constructor call.
    """

    unsupported, states = _resolve(
        _v223_workflow(("PANEL_BASELINE = 1\n", "PANEL_BASELINE = Fraction(1, 1)\n"))
    )
    assert unsupported
    assert states == set()


# Extension two: a helper parameter proven path-like at its call sites.


def test_a_second_path_like_call_site_still_proves_the_parameter() -> None:
    """Every call site proves it, so two of them prove it as well as one."""

    unsupported, states = _resolve(
        _v223_workflow(
            (
                "table_rows = read_table(DATA_PATH)\n",
                "spare_rows = read_table(DATA_PATH)\ntable_rows = read_table(DATA_PATH)\n",
            )
        )
    )
    assert not unsupported
    assert states == {"repaired"}


def test_one_non_path_call_site_leaves_the_parameter_unproven() -> None:
    """A single call site handing over a string is enough to close the proof."""

    unsupported, states = _resolve(
        _v223_workflow(
            (
                "table_rows = read_table(DATA_PATH)\n",
                "spare_rows = read_table('inputs/markers.csv')\n"
                "table_rows = read_table(DATA_PATH)\n",
            )
        )
    )
    assert unsupported
    assert states == set()


def test_a_helper_name_that_escapes_call_position_proves_nothing() -> None:
    """A helper reachable through an alias has call sites this scan cannot see."""

    unsupported, states = _resolve(
        _v223_workflow(
            (
                "table_rows = read_table(DATA_PATH)\n",
                "loader = read_table\ntable_rows = read_table(DATA_PATH)\n",
            )
        )
    )
    assert unsupported
    assert states == set()


# Extension three: the named read-text chain and the named reader.


def test_a_named_read_text_result_opens_the_splitlines_chain() -> None:
    """``raw_text.splitlines()`` reads what the inline chain reads.

    The reader is inlined here, so the name holding the ``read_text`` result
    is the only form of this extension the workflow uses.
    """

    unsupported, states = _resolve(
        _v223_workflow(
            (
                _V223_LOADER + "    return [dict(record) for record in reader]\n",
                "    raw_text = source_path.read_text(encoding='ascii')\n"
                "    return [dict(record) for record in csv.DictReader(raw_text.splitlines())]\n",
            )
        )
    )
    assert not unsupported
    assert states == {"repaired"}


def test_a_reader_bound_to_a_name_is_iterated_from_there() -> None:
    """The chain is written inline, so the named reader is the only form in play."""

    unsupported, states = _resolve(
        _v223_workflow(
            (
                _V223_LOADER,
                "    reader = csv.DictReader(source_path.read_text(encoding='ascii').splitlines())\n",
            )
        )
    )
    assert not unsupported
    assert states == {"repaired"}


def test_a_rebound_read_text_name_opens_no_chain() -> None:
    """The name holds the read text only when the module binds it exactly once."""

    unsupported, states = _resolve(
        _v223_workflow(
            (
                "    reader = csv.DictReader(raw_text.splitlines())\n",
                "    raw_text = raw_text\n    reader = csv.DictReader(raw_text.splitlines())\n",
            )
        )
    )
    assert unsupported
    assert states == set()


# Extension four: the bare mkdir statement.


def test_a_bare_mkdir_statement_is_admitted() -> None:
    """Creating the results directory answers exactly as leaving it out does."""

    with_mkdir = _resolve(_v223_workflow())
    without_mkdir = _resolve(
        _v223_workflow(("    target_path.parent.mkdir(parents=True, exist_ok=True)\n", ""))
    )
    assert with_mkdir == (False, {"repaired"})
    assert with_mkdir == without_mkdir


def test_an_unknown_bare_method_statement_abstains() -> None:
    """``mkdir`` joins ``close``; every other bare method call stays outside."""

    unsupported, states = _resolve(
        _v223_workflow(
            (
                "    target_path.parent.mkdir(parents=True, exist_ok=True)\n",
                "    target_path.parent.chmod(0o755)\n",
            )
        )
    )
    assert unsupported
    assert states == set()


def test_a_non_literal_mkdir_keyword_abstains() -> None:
    """A keyword whose value is a name is an expression, not a literal setting."""

    unsupported, states = _resolve(
        _v223_workflow(
            ("PANEL_BASELINE = 1\n", "PANEL_BASELINE = 1\nMAKE_PARENTS = True\n"),
            ("mkdir(parents=True, exist_ok=True)", "mkdir(parents=MAKE_PARENTS, exist_ok=True)"),
        )
    )
    assert unsupported
    assert states == set()


# Extension five: the report write routed through a helper.


def test_a_helper_routed_report_write_seeds_reachability() -> None:
    """``write_report(PATH, text)`` publishes what the inline write publishes."""

    routed = _resolve(_v223_workflow())
    inline = _resolve(
        _v223_workflow(
            (_V223_WRITE_HELPER, ""),
            (
                "written_length = write_report(REPORT_PATH, report_text)\n",
                "written_length = REPORT_PATH.write_text(report_text, encoding='ascii')\n",
            ),
        )
    )
    assert routed == (False, {"repaired"})
    assert routed == inline


def test_a_write_helper_handed_a_non_path_argument_abstains() -> None:
    """The call site must prove the path; a string names no proven receiver."""

    unsupported, states = _resolve(
        _v223_workflow(
            (
                "written_length = write_report(REPORT_PATH, report_text)\n",
                "written_length = write_report('results/report.md', report_text)\n",
            )
        )
    )
    assert unsupported
    assert states == set()


# Extension six: the elementwise recode of a column-values list.


def test_a_rebound_recode_source_list_abstains() -> None:
    """A rebound list leaves which list the comprehension walks to execution order."""

    unsupported, states = _resolve(
        _v223_workflow((_V223_RECODE, "panel_markers = panel_markers\n" + _V223_RECODE))
    )
    assert unsupported
    assert states == set()


def test_a_filtered_recode_abstains() -> None:
    """A filter drops rows, so the result is no longer the same column over the same rows."""

    unsupported, states = _resolve(
        _v223_workflow(
            (
                "[panel_indicator(marker_value) for marker_value in panel_markers]",
                "[panel_indicator(marker_value) for marker_value in panel_markers "
                "if marker_value >= 0]",
            )
        )
    )
    assert unsupported
    assert states == set()


# Extension seven: the range-indexed pairing.


@pytest.mark.parametrize(
    "length",
    ["len(observed_calls)", "len(panel_values)", "len(table_rows)"],
)
def test_a_range_indexed_pairing_resolves_on_each_proven_length(length: str) -> None:
    """The three ``len`` forms that prove the walk covers each pair once, in order.

    The fixture itself writes the fourth spelling: a name bound exactly once
    to ``len(table_rows)``.
    """

    unsupported, states = _resolve(
        _v223_workflow(("for position in range(unit_count)", f"for position in range({length})"))
    )
    assert not unsupported, length
    assert states == {"repaired"}, length


def test_a_range_over_a_named_constant_abstains() -> None:
    """A plausible count is not a proof that the walk covers the lists."""

    unsupported, states = _resolve(
        _v223_workflow(
            ("PANEL_BASELINE = 1\n", "PANEL_BASELINE = 1\nUNIT_TOTAL = 4\n"),
            ("for position in range(unit_count)", "for position in range(UNIT_TOTAL)"),
        )
    )
    assert unsupported
    assert states == set()


def test_an_index_used_outside_the_two_subscripts_abstains() -> None:
    """The index may appear nowhere but as the two lists' subscript."""

    unsupported, states = _resolve(
        _v223_workflow(
            (
                "    concordance_weight(observed_calls[position], panel_values[position])\n",
                "    concordance_weight(observed_calls[position], panel_values[position])"
                " + position * 0\n",
            )
        )
    )
    assert unsupported
    assert states == set()


def test_a_shifted_subscript_abstains() -> None:
    """``A[i - 0]`` is an expression under the index, not the index itself."""

    unsupported, states = _resolve(
        _v223_workflow(("panel_values[position])", "panel_values[position - 0])"))
    )
    assert unsupported
    assert states == set()


# Extension eight: the accumulation loop over a list of per-element selectors.


def test_an_accumulation_loop_reads_its_list_as_sum_does() -> None:
    """``for v in vals: total = total + v`` answers as ``sum(vals)`` answers."""

    looped = _resolve(_v223_workflow())
    summed = _resolve(_v223_workflow((_V223_ACCUMULATION, "emission_total = sum(weight_values)\n")))
    assert looped == (False, {"repaired"})
    assert looped == summed


def test_an_augmented_accumulation_loop_resolves() -> None:
    """``total += v`` is the same loop written the shorter way."""

    unsupported, states = _resolve(
        _v223_workflow(
            (
                "    emission_total = emission_total + weight_value\n",
                "    emission_total += weight_value\n",
            )
        )
    )
    assert not unsupported
    assert states == {"repaired"}


def test_an_accumulation_payload_beyond_the_loop_variable_abstains() -> None:
    """The payload is the bare loop variable; anything computed per element is not."""

    unsupported, states = _resolve(
        _v223_workflow(
            (
                "    emission_total = emission_total + weight_value\n",
                "    emission_total = emission_total + weight_value * 2\n",
            )
        )
    )
    assert unsupported
    assert states == set()


def test_an_accumulation_loop_over_a_rebound_list_abstains() -> None:
    """Which list the loop walks must not be a question about execution order."""

    unsupported, states = _resolve(
        _v223_workflow(
            ("emission_total = 0\n", "weight_values = weight_values\nemission_total = 0\n")
        )
    )
    assert unsupported
    assert states == set()


# Extension nine: the accumulation loop over a single column-values list.


def test_a_loop_over_one_column_values_list_introduces_no_abstention() -> None:
    """Counting one column carries no orientation, and no longer costs the answer."""

    with_loop = _resolve(_v223_workflow())
    without_loop = _resolve(
        _v223_workflow(
            (_V223_COLUMN_LOOP, ""),
            ("{panel_positive_total} carry the marker", "{unit_count} carry the marker"),
        )
    )
    assert with_loop == (False, {"repaired"})
    assert with_loop == without_loop


# Extension ten: the print keyword arguments.


@pytest.mark.parametrize("keyword", ["sep=' '", "end='\\n'", "sep='', end=''"])
def test_print_layout_keywords_resolve(keyword: str) -> None:
    """``sep`` and ``end`` change the layout of the same arguments, nothing else."""

    unsupported, states = _resolve(
        _v223_workflow(("print(report_text, end='')", f"print(report_text, {keyword})"))
    )
    assert not unsupported, keyword
    assert states == {"repaired"}, keyword


def test_a_print_file_keyword_abstains() -> None:
    """``file`` redirects the write to a receiver this trace has not proven."""

    unsupported, states = _resolve(
        _v223_workflow(("print(report_text, end='')", "print(report_text, file=None)"))
    )
    assert unsupported
    assert states == set()


def test_a_non_string_print_keyword_value_abstains() -> None:
    """The admitted keyword values are string literals and ``None``."""

    unsupported, states = _resolve(
        _v223_workflow(("print(report_text, end='')", "print(report_text, flush=True)"))
    )
    assert unsupported
    assert states == set()
