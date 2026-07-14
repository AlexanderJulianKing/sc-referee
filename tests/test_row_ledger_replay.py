from dataclasses import replace
import numpy as np
import pandas as pd

from sc_referee.row_ledger import (
    AggregationOperation, CompleteCaseOperation, EvaluationRelation, QcThresholdOperation,
    RowLedgerDeclaration, RowLedgerState, Stage, SubsetOperation, TypedScalar,
    ZeroCountOperation, reconstruct_row_ledger, replay_source_operations,
)
from tests.factories import fitted_design_declaration, make_design


def scalar(value): return TypedScalar.from_value(value)
def oid(value): return (scalar(value),)
def ids(*values): return tuple(oid(value) for value in values)


def clean_eight_cell_case():
    source = pd.DataFrame({
        "cell_occurrence_id": [f"c{i}" for i in range(1, 9)],
        "barcode": ["bc1", "bc1", "bc3", "bc4", "bc5", "bc6", "bc7", "bc8"],
        "donor": ["d1", "d1", "d2", "d1", "d2", "d2", "d3", None],
        "condition": ["A", "A", "A", "B", "B", "B", "A", "A"],
        "cell_type": ["T", "T", "T", "T", "T", "T", "B", "T"],
        "n_genes": [300, 250, 100, 220, 210, 230, 300, 250],
    })
    counts = np.asarray([[5,1],[6,2],[9,9],[4,2],[7,0],[8,1],[3,3],[2,2]], dtype=np.int64)
    design = make_design(condition="condition", reference="A", test="B", batch=(),
        sample_unit=("donor","condition"), aggregation_key=("donor","condition"),
        analyst_adjusted_for=["condition"], fitted_design=fitted_design_declaration(
            column_kinds={"condition":"categorical"}, categorical_levels={"condition":("A","B")},
            transforms={"condition":"identity"}, rows_exact=True),
        confidence={"condition":"high","aggregation_key":"high","analyst_adjusted_for":"high","fitted_design":"high"})
    operations = (
        SubsetOperation("subset-t","cell_type",(scalar("T"),),"high"),
        QcThresholdOperation("qc-n-genes","n_genes","ge",scalar(200),"drop","high"),
        CompleteCaseOperation("cc-fit",("donor","condition"),"high"),
        AggregationOperation("aggregate",("donor","condition"),"stable_first_occurrence","high"),
        ZeroCountOperation("zero-library","total_library_equals_zero","sha256:raw-counts-v1","high"),
    )
    declaration=RowLedgerDeclaration("row-ledger-schema-v1","sha256:observations-v1","sha256:raw-counts-v1",
        ("cell_occurrence_id",),ids("c1","c2","c4","c5","c6"),operations,
        EvaluationRelation.VERIFIED_SAME_AS_FITTED,"high","results.csv#condition-B-vs-A","condition[T.B]",
        {"source_snapshot_identity":"high","count_layer_identity":"high","source_occurrence_id_columns":"high",
         "fitted_source_occurrence_ids":"high","evaluation_relation":"high","fitted_result_id":"high","target_coefficient":"high"})
    return source,counts,design,declaration


def test_subset_qc_and_complete_case_own_exact_terminal_occurrences():
    source,counts,design,declaration=clean_eight_cell_case()
    replay=replay_source_operations(source,counts,design,declaration)
    assert replay.survivor_ids == ids("c1","c2","c4","c5","c6")
    assert [(x.affected_occurrence_id,x.reason.value,x.operation_id) for x in replay.exclusions] == [
        (oid("c7"),"declared_subset","subset-t"),(oid("c3"),"declared_qc_threshold","qc-n-genes"),
        (oid("c8"),"complete_case_missing_covariate","cc-fit")]
    assert replay.exclusions[2].operands == (("missing_columns",("donor",)),)


def test_low_confidence_operation_abstains_atomically():
    source,counts,design,declaration=clean_eight_cell_case(); ops=list(declaration.operations)
    ops[1]=replace(ops[1],confidence="low")
    result=reconstruct_row_ledger(source,counts,design,replace(declaration,operations=tuple(ops)))
    assert result.state is RowLedgerState.NOT_AUDITED and result.machine_reason == "row_ledger_not_ratified"
    assert result.artifact is None


def test_undeclared_irreproducible_filter_is_not_audited():
    source,counts,design,declaration=clean_eight_cell_case()
    declaration=replace(declaration,fitted_source_occurrence_ids=ids("c1","c2","c4","c5"))
    result=reconstruct_row_ledger(source,counts,design,declaration)
    assert result.state is RowLedgerState.NOT_AUDITED
    assert result.machine_reason == "unexplained_occurrence_loss" and result.artifact is None
    assert result.diagnostic.last_reconciled_operation_id == "qc-n-genes"
    assert result.diagnostic.expected_occurrence_ids == ids("c1","c2","c4","c5","c6")


def test_roster_comparison_is_ordered_and_multiplicity_preserving():
    source,counts,design,declaration=clean_eight_cell_case()
    declaration=replace(declaration,fitted_source_occurrence_ids=ids("c2","c1","c4","c5","c6"))
    assert reconstruct_row_ledger(source,counts,design,declaration).machine_reason == "unexplained_occurrence_loss"


def test_matching_removed_counts_with_different_occurrences_never_reconciles():
    source=pd.DataFrame({"cell_occurrence_id":["c1","c2","c3","c4","c5","c6"],
        "donor":["d1","d1","d2","d2","d3","d3"],"condition":["A","A","A","A","B","B"],
        "n_genes":[300,100,150,300,300,300]})
    counts=np.ones((6,2),dtype=np.int64); _,_,design,base=clean_eight_cell_case()
    declaration=replace(base,source_snapshot_identity="sha256:adversary",
        fitted_source_occurrence_ids=ids("c1","c2","c3","c4"),operations=(
            QcThresholdOperation("qc-n-genes","n_genes","ge",scalar(200),"drop","high"),
            AggregationOperation("aggregate",("donor","condition"),"stable_first_occurrence","high")))
    result=reconstruct_row_ledger(source,counts,design,declaration)
    assert result.machine_reason == "unexplained_occurrence_loss" and result.artifact is None
    assert set(result.diagnostic.expected_occurrence_ids) != set(result.diagnostic.observed_occurrence_ids)
