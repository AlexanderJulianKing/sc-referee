from dataclasses import replace
from pathlib import Path
import ast
import numpy as np
import pytest

from sc_referee.row_ledger import (
    EvaluationRelation, RowLedgerMachineReason, RowLedgerState, Stage,
    reconstruct_row_ledger,
)
from tests.test_row_ledger_replay import clean_eight_cell_case


def _case(which):
    source,counts,design,declaration=clean_eight_cell_case()
    if which == "absent": declaration=None
    elif which == "identity": source=source.drop(columns=["cell_occurrence_id"])
    elif which == "duplicate": source.loc[1,"cell_occurrence_id"]="c1"
    elif which == "separate": declaration=replace(declaration,evaluation_relation=EvaluationRelation.SEPARATE)
    elif which == "eval-low": declaration=replace(declaration,evaluation_relation_confidence="low")
    elif which == "fit-false": design=replace(design,fitted_design=replace(design.fitted_design,rows_exact=False))
    elif which == "wrong-layer":
        ops=list(declaration.operations); ops[-1]=replace(ops[-1],count_layer_identity="sha256:wrong")
        declaration=replace(declaration,operations=tuple(ops))
    elif which == "length": counts=counts[:-1]
    elif which == "nonfinite": counts=counts.astype(float); counts[0,0]=np.nan
    elif which == "low-field":
        confidence=dict(declaration.field_confidence); confidence["fitted_result_id"]="low"
        declaration=replace(declaration,field_confidence=confidence)
    return source,counts,design,declaration


@pytest.mark.parametrize(("which","reason"),[
    ("absent","row_ledger_not_declared"),("identity","source_occurrence_identity_unavailable"),
    ("duplicate","ambiguous_duplicate_occurrence"),("separate","separate_evaluation_roster_unsupported"),
    ("eval-low","evaluation_relation_not_ratified"),("fit-false","fit_rows_not_attested"),
    ("wrong-layer","zero_count_semantics_unavailable"),("length","source_count_length_mismatch"),
    ("nonfinite","zero_count_semantics_unavailable"),("low-field","row_ledger_not_ratified"),
])
def test_inexact_and_deferred_cases_are_atomic_not_audited(which,reason):
    result=reconstruct_row_ledger(*_case(which),required_stages=(Stage.FIT,Stage.EVALUATION))
    assert result.state is RowLedgerState.NOT_AUDITED and result.machine_reason == reason
    assert result.artifact is None and result.certified_stages == ()


def test_machine_reasons_are_a_closed_inventory():
    expected={
        "row_ledger_not_declared","row_ledger_not_ratified","fit_rows_not_attested",
        "source_binding_unavailable","source_count_length_mismatch","source_occurrence_identity_unavailable",
        "ambiguous_duplicate_occurrence","unexplained_occurrence_loss","unsupported_pipeline_operation",
        "declared_column_unavailable","threshold_semantics_unavailable","operation_order_unavailable",
        "ambiguous_terminal_exclusion","aggregation_key_unavailable","aggregation_not_exact",
        "aggregation_membership_mismatch","zero_count_semantics_unavailable","lineage_not_exact",
        "fitted_row_order_unavailable","evaluation_relation_not_ratified",
        "separate_evaluation_roster_unsupported","evaluation_rows_not_exact","unsupported_library_drop",
        "fitted_object_binding_unsupported","ledger_integrity_failure","certified_rows_ratified",
    }
    assert {reason.value for reason in RowLedgerMachineReason} == expected


def test_primitive_cannot_render_or_import_findings():
    source=Path("src/sc_referee/row_ledger.py").read_text(); tree=ast.parse(source)
    assert "Finding" not in source
    forbidden={"PASS","NEEDS_EVIDENCE","MAJOR","BLOCKER","VIOLATION","CONCERN"}
    assert not forbidden & {node.attr for node in ast.walk(tree) if isinstance(node,ast.Attribute)}
