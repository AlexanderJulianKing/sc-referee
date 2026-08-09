"""Permanent regression: the founder pilot burned cases.

Four blind pilots have run against this recognizer, and each discovered a
miss. The three cases of the ``...-v2.1.5`` pilot-a lane, the three of the
``...-v2.2.1`` pilot-b lane, the three of the ``...-v2.2.2`` pilot-c lane, and
the three of the ``...-v2.2.4`` pilot-d lane are answer-visible development
evidence: their scientific labels were exposed when each pilot was scored, so
they are permanently qualification-ineligible. They are retained here as the
regression fixtures for the four discovered misses. Under v2.1.5 the detector
abstained on all three pilot-a cases, including the error-bearing one, because
the blind author wrote five ordinary idioms the whitelist did not model;
v2.2.0 models them. Under v2.2.1 it abstained on all three pilot-b cases for
the same kind of reason, across four more idioms; v2.2.2 models those. Under
v2.2.2 it abstained on the pilot-c error-bearing case across ten more; v2.2.3
models those. Under v2.2.4 it abstained on the pilot-d error-bearing case
across four more; v2.2.5 models those.

These assertions are permanent, and they are asymmetric on purpose. Each
error-bearing case must localize: the resolver must read the repaired
orientation and the adapter must return an applicable observation carrying
the repaired operand. Every control must never carry the repaired operand,
whatever else it does. A control is allowed to abstain and allowed to read
the direct orientation; it is never allowed to raise the false alarm.

The case documents are read from the lane directories by their real paths, so
this file tests the released recognizer against the exact bytes the blind
authors wrote.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

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
from sc_referee.scientific_checks.founder_orientation_dataflow import (
    FounderDataflowResolution,
    resolve_founder_orientation_dataflow,
)
from sc_referee.scientific_checks.profiles import default_scientific_check_registry
from sc_referee.scientific_checks.scope_joins import build_static_scope_join_graph

FOUNDER_CHECK = "check:founder-orientation-before-hmm-emission"
DIRECT_OPERAND = "use_supplied_founder_alleles_directly_in_hmm_emission"
REPAIRED_OPERAND = "repair_ril_founder_orientation_before_hmm_emission"

LANE = Path("evaluation/qualification/founder-orientation-before-hmm-emission-v2.1.5-lane/pilot-a")
CASES = LANE / "authoring/cases"
LANE_B = Path(
    "evaluation/qualification/founder-orientation-before-hmm-emission-v2.2.1-lane/pilot-b"
)
CASES_B = LANE_B / "authoring/cases"
LANE_C = Path(
    "evaluation/qualification/founder-orientation-before-hmm-emission-v2.2.2-lane/pilot-c"
)
CASES_C = LANE_C / "authoring/cases"
LANE_D = Path(
    "evaluation/qualification/founder-orientation-before-hmm-emission-v2.2.4-lane/pilot-d"
)
CASES_D = LANE_D / "authoring/cases"
WORKFLOW_PATH = "workflow/analysis.py"
REPORT_PATH = "results/report.md"

ERROR_BEARING = "82083c85adcd805c3dcc"
CORRECTED_TWIN = "34e2f37daaf6bd8bc45c"
HARD_NEGATIVE = "a6f2518e34bfae4a356c"

ERROR_BEARING_B = "a75ef9767fe5d844013c"
CORRECTED_TWIN_B = "a2b7f1909259491efe88"
HARD_NEGATIVE_B = "2d54a3f3add5ee29ce6d"

ERROR_BEARING_C = "8c347d0471b4ab2fcc31"
CORRECTED_TWIN_C = "ba25407cb8c597e00a42"
HARD_NEGATIVE_C = "be698ab19891acbd8e51"

ERROR_BEARING_D = "3a7765ac1f2d5c06b5c6"
CORRECTED_TWIN_D = "afec8de43f6550605f4f"
HARD_NEGATIVE_D = "769d1c65c50fd5c323ac"

CONTROLS = (CORRECTED_TWIN, HARD_NEGATIVE)
CONTROLS_B = (CORRECTED_TWIN_B, HARD_NEGATIVE_B)
CONTROLS_C = (CORRECTED_TWIN_C, HARD_NEGATIVE_C)
CONTROLS_D = (CORRECTED_TWIN_D, HARD_NEGATIVE_D)


def _inspection_context(report: bytes, workflow: bytes) -> FrozenInspectionContext:
    """One selected report and the workflow that writes it."""

    surface_ref = RecordRef("publication_surface", "publication-surface:founder-pilot-a")
    artifact_ref = RecordRef("artifact", "artifact:founder-pilot-a-report")
    identity_ref = RecordRef("asset_identity", "asset-identity:founder-pilot-a-report")
    report_file_ref = RecordRef("file_record", "file:founder-pilot-a-report")
    report_parser_ref = RecordRef("parser_result", "parser-result:founder-pilot-a-report")
    workflow_file_ref = RecordRef("file_record", "file:founder-pilot-a-workflow")
    workflow_parser_ref = RecordRef("parser_result", "parser-result:founder-pilot-a-workflow")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:founder-pilot-a")
    report_parser = canonical_json(
        {
            "parser_id": "parser:markdown-inventory",
            "parser_version": "0.2.0",
            "state": "parsed",
        }
    ).encode("utf-8")
    workflow_parser = canonical_json(
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
                "path": REPORT_PATH,
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
        (workflow_file_ref, {"file_record_id": workflow_file_ref.record_id}),
        (workflow_parser_ref, {"parser_result_id": workflow_parser_ref.record_id}),
    ]
    documents = (
        InspectionDocument(
            path=REPORT_PATH,
            file_ref=report_file_ref,
            content=report,
            content_digest=sha256_digest(report),
            media_type="text/markdown",
            parser_result_ref=report_parser_ref,
            parser_result_payload=report_parser,
            parser_result_digest=sha256_digest(report_parser),
        ),
        InspectionDocument(
            path=WORKFLOW_PATH,
            file_ref=workflow_file_ref,
            content=workflow,
            content_digest=sha256_digest(workflow),
            media_type="text/x-python",
            parser_result_ref=workflow_parser_ref,
            parser_result_payload=workflow_parser,
            parser_result_digest=sha256_digest(workflow_parser),
        ),
    )
    context = FrozenInspectionContext(
        snapshot_digest=sha256_digest("founder-pilot-a"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=documents,
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


def _case_context(project_root: Path, slug: str, cases: Path = CASES) -> FrozenInspectionContext:
    case = project_root / cases / slug
    return _inspection_context(
        (case / REPORT_PATH).read_bytes(), (case / WORKFLOW_PATH).read_bytes()
    )


def _resolution(context: FrozenInspectionContext) -> FounderDataflowResolution:
    return resolve_founder_orientation_dataflow(
        context,
        direct_operand=DIRECT_OPERAND,
        repaired_operand=REPAIRED_OPERAND,
        parser_id=PYTHON_PARSER_ID,
        parser_version=PYTHON_PARSER_VERSION,
    )


def _observation(context: FrozenInspectionContext) -> tuple[str, str | None]:
    """The released registry adapter's applicability and observed operand."""

    module = next(
        item
        for item in default_scientific_check_registry().modules
        if item.manifest.check_id == FOUNDER_CHECK
    )
    observed = module.adapters[0].inspect(context)
    operand = observed.observed_operand
    return observed.applicability, None if operand is None else str(operand.value)


def test_the_lane_labels_still_say_what_these_cases_are(project_root: Path) -> None:
    """The roles asserted below are the lane's own frozen scientific labels."""

    ledger = json.loads(
        (project_root / LANE / "SCIENTIFIC_LABEL_LEDGER.json").read_text(encoding="utf-8")
    )
    roles = {
        entry["case_id"].removeprefix("case:"): entry["case_role"] for entry in ledger["entries"]
    }
    assert roles[ERROR_BEARING] == "error_bearing"
    assert roles[CORRECTED_TWIN] == "corrected_twin"
    assert roles[HARD_NEGATIVE] == "hard_negative"


def test_the_error_bearing_case_localizes_the_repaired_orientation(project_root: Path) -> None:
    """The miss v2.1.5 recorded on this lane, closed.

    The workflow builds its reference column as ``PANEL_BASELINE -
    int(record[REFERENCE_COLUMN])`` and then compares it against the observed
    column, so exactly one operand path carries an involution and the emission
    accumulates over the complemented panel while the report describes the
    panel as staged.
    """

    context = _case_context(project_root, ERROR_BEARING)
    resolution = _resolution(context)
    assert resolution.state == "unique"
    assert resolution.orientation == "repaired"
    assert resolution.operand_value == REPAIRED_OPERAND
    assert resolution.source_path == WORKFLOW_PATH
    applicability, operand = _observation(context)
    assert applicability == "applicable"
    assert operand == REPAIRED_OPERAND


def test_the_corrected_twin_carries_no_repaired_operand(project_root: Path) -> None:
    """The twin compares the two columns as staged; a repair reading is a false alarm.

    Direct and clean abstention are both sound answers here. The twin pairs
    its columns with a tuple comprehension rather than a ``zip`` of two
    column-values lists, which is outside the v2.2.0 pairing form, so the
    current answer is an abstention.
    """

    context = _case_context(project_root, CORRECTED_TWIN)
    resolution = _resolution(context)
    assert resolution.orientation in {None, "direct"}
    assert resolution.operand_value != REPAIRED_OPERAND
    applicability, operand = _observation(context)
    assert operand != REPAIRED_OPERAND
    if applicability == "applicable":
        assert operand == DIRECT_OPERAND


def test_the_hard_negative_stays_clean(project_root: Path) -> None:
    """No false alarm on the hard negative, whichever way it resolves.

    This workflow carries a quality-control complement column beside the
    emission accumulation. The complement never enters the emission, and the
    report says so, but a recognizer that read it as a second orientation
    reading would have two disagreeing readings and would have to abstain as
    ambiguous. Either outcome is clean; a repaired operand is not. The
    assertion is therefore on the absence of the false alarm rather than on a
    particular state.
    """

    context = _case_context(project_root, HARD_NEGATIVE)
    resolution = _resolution(context)
    assert resolution.operand_value != REPAIRED_OPERAND
    applicability, operand = _observation(context)
    assert operand != REPAIRED_OPERAND
    assert applicability != "applicable" or operand == DIRECT_OPERAND


@pytest.mark.parametrize("slug", CONTROLS)
def test_the_controls_never_produce_a_repaired_reading(project_root: Path, slug: str) -> None:
    """One rule over both controls, stated once so no future version loses it."""

    context = _case_context(project_root, slug)
    assert _resolution(context).orientation != "repaired"
    _applicability, operand = _observation(context)
    assert operand != REPAIRED_OPERAND


@pytest.mark.parametrize("slug", [ERROR_BEARING, *CONTROLS])
def test_every_pilot_case_answers_deterministically(project_root: Path, slug: str) -> None:
    context = _case_context(project_root, slug)
    first = _resolution(context)
    second = _resolution(context)
    assert first.state == second.state
    assert first.orientation == second.orientation
    assert first.operand_value == second.operand_value
    assert _observation(context) == _observation(context)


# Pilot b, run blind against v2.2.1 and burned by the same scoring. Its
# error-bearing case wrote four ordinary idioms the v2.2.1 whitelist did not
# model: the row copy ``dict(entry)``, ``handle.close()``, two one-parameter
# column-extraction helpers, and the multiply-complement selector
# ``A * FLAG + B * (1 - FLAG)``. v2.2.2 models all four.


def test_the_pilot_b_lane_labels_still_say_what_these_cases_are(project_root: Path) -> None:
    """The roles asserted below are the lane's own frozen scientific labels."""

    ledger = json.loads(
        (project_root / LANE_B / "SCIENTIFIC_LABEL_LEDGER.json").read_text(encoding="utf-8")
    )
    roles = {
        entry["case_id"].removeprefix("case:"): entry["case_role"] for entry in ledger["entries"]
    }
    assert roles[ERROR_BEARING_B] == "error_bearing"
    assert roles[CORRECTED_TWIN_B] == "corrected_twin"
    assert roles[HARD_NEGATIVE_B] == "hard_negative"


def test_the_pilot_b_error_bearing_case_localizes_the_repaired_orientation(
    project_root: Path,
) -> None:
    """The miss v2.2.1 recorded on this lane, closed.

    The workflow loads its table through a helper that copies each reader row
    with ``dict(entry)`` and closes the handle, reads each column through a
    one-parameter helper, and builds the panel column as ``PANEL_CODE_TOP -
    staged_value``. Exactly one operand path carries that involution, so the
    emission accumulates over the complemented panel while the report
    describes the panel as staged.
    """

    context = _case_context(project_root, ERROR_BEARING_B, CASES_B)
    resolution = _resolution(context)
    assert resolution.state == "unique"
    assert resolution.orientation == "repaired"
    assert resolution.operand_value == REPAIRED_OPERAND
    assert resolution.source_path == WORKFLOW_PATH
    applicability, operand = _observation(context)
    assert applicability == "applicable"
    assert operand == REPAIRED_OPERAND


def test_the_pilot_b_corrected_twin_carries_no_repaired_operand(project_root: Path) -> None:
    """The twin reads both columns as staged, so a repair reading is a false alarm.

    It is the error-bearing workflow with the involution and the two ``int``
    casts removed, so both operand paths are identity reads of raw column
    strings. Direct and clean abstention are both sound answers; under
    v2.2.2 the answer is direct.
    """

    context = _case_context(project_root, CORRECTED_TWIN_B, CASES_B)
    resolution = _resolution(context)
    assert resolution.orientation in {None, "direct"}
    assert resolution.operand_value != REPAIRED_OPERAND
    applicability, operand = _observation(context)
    assert operand != REPAIRED_OPERAND
    if applicability == "applicable":
        assert operand == DIRECT_OPERAND


def test_the_pilot_b_hard_negative_stays_clean(project_root: Path) -> None:
    """No false alarm on the hard negative, whichever way it resolves.

    This workflow carries a complemented reference copy beside the emission
    accumulation as a declared orientation control, and the report says the
    complement never enters the emission. It also reads its columns as
    ``rows[index][COLUMN]``, which is a tagged row set outside its permitted
    positions, so the current answer is an abstention. That is clean, and so
    is a direct reading; a repaired operand is not. The assertion is
    therefore on the absence of the false alarm rather than on a particular
    state.
    """

    context = _case_context(project_root, HARD_NEGATIVE_B, CASES_B)
    resolution = _resolution(context)
    assert resolution.operand_value != REPAIRED_OPERAND
    applicability, operand = _observation(context)
    assert operand != REPAIRED_OPERAND
    assert applicability != "applicable" or operand == DIRECT_OPERAND


@pytest.mark.parametrize("slug", CONTROLS_B)
def test_the_pilot_b_controls_never_produce_a_repaired_reading(
    project_root: Path, slug: str
) -> None:
    """One rule over both controls, stated once so no future version loses it."""

    context = _case_context(project_root, slug, CASES_B)
    assert _resolution(context).orientation != "repaired"
    _applicability, operand = _observation(context)
    assert operand != REPAIRED_OPERAND


@pytest.mark.parametrize("slug", [ERROR_BEARING_B, *CONTROLS_B])
def test_every_pilot_b_case_answers_deterministically(project_root: Path, slug: str) -> None:
    context = _case_context(project_root, slug, CASES_B)
    first = _resolution(context)
    second = _resolution(context)
    assert first.state == second.state
    assert first.orientation == second.orientation
    assert first.operand_value == second.operand_value
    assert _observation(context) == _observation(context)


# Pilot c, run blind against v2.2.2 and burned by the same scoring. Its
# error-bearing case wrote ten ordinary idioms the v2.2.2 whitelist did not
# model: ``Fraction`` module constants in the selector branches, a helper
# parameter used as a filesystem path, ``.splitlines()`` on a name holding a
# ``read_text`` result, a bare ``mkdir()``, a report write routed through a
# two-parameter helper, an elementwise recode of a column-values list, the
# ``range(len(...))`` spelling of a pairing, two accumulation loops, and
# ``print(..., end="")``. v2.2.3 models all ten.


def test_the_pilot_c_lane_labels_still_say_what_these_cases_are(project_root: Path) -> None:
    """The roles asserted below are the lane's own frozen scientific labels."""

    ledger = json.loads(
        (project_root / LANE_C / "SCIENTIFIC_LABEL_LEDGER.json").read_text(encoding="utf-8")
    )
    roles = {
        entry["case_id"].removeprefix("case:"): entry["case_role"] for entry in ledger["entries"]
    }
    assert roles[ERROR_BEARING_C] == "error_bearing"
    assert roles[CORRECTED_TWIN_C] == "corrected_twin"
    assert roles[HARD_NEGATIVE_C] == "hard_negative"


def test_the_pilot_c_error_bearing_case_localizes_the_repaired_orientation(
    project_root: Path,
) -> None:
    """The miss v2.2.2 recorded on this lane, closed.

    The workflow reads its table through a helper whose parameter every call
    site proves is a path, recodes the panel column with ``panel_indicator``,
    which returns ``1 - marker_value``, and then pairs the observed column
    against the recoded one by index. Exactly one operand path carries that
    involution, so the emission accumulates over the complemented panel while
    the report says the panel is used as supplied.
    """

    context = _case_context(project_root, ERROR_BEARING_C, CASES_C)
    resolution = _resolution(context)
    assert resolution.state == "unique"
    assert resolution.orientation == "repaired"
    assert resolution.operand_value == REPAIRED_OPERAND
    assert resolution.source_path == WORKFLOW_PATH
    applicability, operand = _observation(context)
    assert applicability == "applicable"
    assert operand == REPAIRED_OPERAND


def test_the_pilot_c_corrected_twin_carries_no_repaired_operand(project_root: Path) -> None:
    """The twin compares both columns as staged, so a repair reading is a false alarm.

    It is the error-bearing workflow with the recode helper and its
    intermediate column removed, so the panel column reaches the pairing as
    read. Direct and clean abstention are both sound answers; under v2.2.3 the
    answer is direct.
    """

    context = _case_context(project_root, CORRECTED_TWIN_C, CASES_C)
    resolution = _resolution(context)
    assert resolution.orientation in {None, "direct"}
    assert resolution.operand_value != REPAIRED_OPERAND
    applicability, operand = _observation(context)
    assert operand != REPAIRED_OPERAND
    if applicability == "applicable":
        assert operand == DIRECT_OPERAND


def test_the_pilot_c_hard_negative_stays_clean(project_root: Path) -> None:
    """No false alarm on the hard negative, whichever way it resolves.

    This workflow builds a strand-complemented copy of the panel column as a
    declared quality-control comparison, and the report says the complement
    never enters the emission. Its selector helper takes the two branch
    weights as parameters instead of reading module constants, and binds its
    flag through an ``int()`` cast; either one alone puts the helper outside
    the recognized selector shape, so the current answer is an abstention.
    That is clean, and so is a direct reading; a repaired operand is not. The
    assertion is therefore on the absence of the false alarm rather than on a
    particular state.
    """

    context = _case_context(project_root, HARD_NEGATIVE_C, CASES_C)
    resolution = _resolution(context)
    assert resolution.operand_value != REPAIRED_OPERAND
    applicability, operand = _observation(context)
    assert operand != REPAIRED_OPERAND
    assert applicability != "applicable" or operand == DIRECT_OPERAND


@pytest.mark.parametrize("slug", CONTROLS_C)
def test_the_pilot_c_controls_never_produce_a_repaired_reading(
    project_root: Path, slug: str
) -> None:
    """One rule over both controls, stated once so no future version loses it."""

    context = _case_context(project_root, slug, CASES_C)
    assert _resolution(context).orientation != "repaired"
    _applicability, operand = _observation(context)
    assert operand != REPAIRED_OPERAND


@pytest.mark.parametrize("slug", [ERROR_BEARING_C, *CONTROLS_C])
def test_every_pilot_c_case_answers_deterministically(project_root: Path, slug: str) -> None:
    context = _case_context(project_root, slug, CASES_C)
    first = _resolution(context)
    second = _resolution(context)
    assert first.state == second.state
    assert first.orientation == second.orientation
    assert first.operand_value == second.operand_value
    assert _observation(context) == _observation(context)


# Pilot d, run blind against v2.2.4 and burned by the same scoring. Its
# error-bearing case wrote four ordinary idioms the v2.2.4 whitelist did not
# model: a loader local named ``text`` beside a writer parameter of the same
# name, a selector helper that casts its flag and then names the weight it
# returns, a writer that makes the directory, writes, echoes and returns the
# length, and the selector-weighted product ``[A[i] * S[i] for i in
# range(N)]``. v2.2.5 models all four.


def test_the_pilot_d_lane_labels_still_say_what_these_cases_are(project_root: Path) -> None:
    """The roles asserted below are the lane's own frozen scientific labels."""

    ledger = json.loads(
        (project_root / LANE_D / "SCIENTIFIC_LABEL_LEDGER.json").read_text(encoding="utf-8")
    )
    roles = {
        entry["case_id"].removeprefix("case:"): entry["case_role"] for entry in ledger["entries"]
    }
    assert roles[ERROR_BEARING_D] == "error_bearing"
    assert roles[CORRECTED_TWIN_D] == "corrected_twin"
    assert roles[HARD_NEGATIVE_D] == "hard_negative"


def test_the_pilot_d_error_bearing_case_localizes_the_repaired_orientation(
    project_root: Path,
) -> None:
    """The miss v2.2.4 recorded on this lane, closed.

    The workflow builds ``panel_reference_values`` as ``PANEL_BASELINE -
    value`` over the staged panel column, compares the observed column against
    that recoded one through a two-parameter selector helper, and then weights
    each unit's measured rate by the selector before summing. Exactly one
    operand path carries the involution, so the emission accumulates over the
    complemented panel while the report says the panel is read as supplied.
    """

    context = _case_context(project_root, ERROR_BEARING_D, CASES_D)
    resolution = _resolution(context)
    assert resolution.state == "unique"
    assert resolution.orientation == "repaired"
    assert resolution.operand_value == REPAIRED_OPERAND
    assert resolution.source_path == WORKFLOW_PATH
    applicability, operand = _observation(context)
    assert applicability == "applicable"
    assert operand == REPAIRED_OPERAND


def test_the_pilot_d_corrected_twin_carries_no_repaired_operand(project_root: Path) -> None:
    """The twin compares both columns as staged, so a repair reading is a false alarm.

    It is the error-bearing workflow with ``PANEL_BASELINE`` and the recoded
    reference column removed, so the panel column reaches the selector as
    read. Direct and clean abstention are both sound answers; under v2.2.5 the
    answer is direct.
    """

    context = _case_context(project_root, CORRECTED_TWIN_D, CASES_D)
    resolution = _resolution(context)
    assert resolution.orientation in {None, "direct"}
    assert resolution.operand_value != REPAIRED_OPERAND
    applicability, operand = _observation(context)
    assert operand != REPAIRED_OPERAND
    if applicability == "applicable":
        assert operand == DIRECT_OPERAND


def test_the_pilot_d_hard_negative_stays_clean(project_root: Path) -> None:
    """No false alarm on the hard negative, whichever way it resolves.

    This workflow carries a complemented reference column that feeds a
    declared strand-flip quality-control count and never the emission, and the
    report says so. Its emission factor helper returns ``MISMATCH_WEIGHT +
    WEIGHT_GAP * (observed == reference)``, whose match branch is a name bound
    to a subtraction rather than a resolvable constant, so the selector is
    outside the canonical shape and the comparison inside it goes
    unrecognized; the current answer is an abstention. That is clean, and so
    is a direct reading; a repaired operand is not. The assertion is therefore
    on the absence of the false alarm rather than on a particular state.
    """

    context = _case_context(project_root, HARD_NEGATIVE_D, CASES_D)
    resolution = _resolution(context)
    assert resolution.operand_value != REPAIRED_OPERAND
    applicability, operand = _observation(context)
    assert operand != REPAIRED_OPERAND
    assert applicability != "applicable" or operand == DIRECT_OPERAND


@pytest.mark.parametrize("slug", CONTROLS_D)
def test_the_pilot_d_controls_never_produce_a_repaired_reading(
    project_root: Path, slug: str
) -> None:
    """One rule over both controls, stated once so no future version loses it."""

    context = _case_context(project_root, slug, CASES_D)
    assert _resolution(context).orientation != "repaired"
    _applicability, operand = _observation(context)
    assert operand != REPAIRED_OPERAND


@pytest.mark.parametrize("slug", [ERROR_BEARING_D, *CONTROLS_D])
def test_every_pilot_d_case_answers_deterministically(project_root: Path, slug: str) -> None:
    context = _case_context(project_root, slug, CASES_D)
    first = _resolution(context)
    second = _resolution(context)
    assert first.state == second.state
    assert first.orientation == second.orientation
    assert first.operand_value == second.operand_value
    assert _observation(context) == _observation(context)
