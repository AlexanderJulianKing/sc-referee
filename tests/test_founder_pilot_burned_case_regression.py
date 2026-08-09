"""Permanent regression: the founder pilot-a burned cases.

The three cases in the ``founder-orientation-before-hmm-emission-v2.1.5``
pilot-a lane are answer-visible development evidence: their scientific labels
were exposed when the pilot was scored, so they are permanently
qualification-ineligible. They are retained here as the regression fixtures
for the discovered miss. Under v2.1.5 the detector abstained on all three,
including the error-bearing case, because the blind author wrote five
ordinary idioms the whitelist did not model. v2.2.0 models them.

These assertions are permanent, and they are asymmetric on purpose. The
error-bearing case must localize: the resolver must read the repaired
orientation and the adapter must return an applicable observation carrying
the repaired operand. The two controls must never carry the repaired operand,
whatever else they do. A control is allowed to abstain and allowed to read
the direct orientation; it is never allowed to raise the false alarm.

The case documents are read from the lane directory by their real paths, so
this file tests the released recognizer against the exact bytes the blind
author wrote.
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
WORKFLOW_PATH = "workflow/analysis.py"
REPORT_PATH = "results/report.md"

ERROR_BEARING = "82083c85adcd805c3dcc"
CORRECTED_TWIN = "34e2f37daaf6bd8bc45c"
HARD_NEGATIVE = "a6f2518e34bfae4a356c"

CONTROLS = (CORRECTED_TWIN, HARD_NEGATIVE)


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


def _case_context(project_root: Path, slug: str) -> FrozenInspectionContext:
    case = project_root / CASES / slug
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
