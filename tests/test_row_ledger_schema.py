from dataclasses import FrozenInstanceError
import pytest

from sc_referee.row_ledger import QcThresholdOperation, RowLedgerDeclaration, RowLedgerState, TypedScalar


def test_mvp_state_space_has_no_bound_or_not_certified_state():
    assert {state.value for state in RowLedgerState} == {"certified_rows_ratified", "not_audited"}


def test_operations_are_closed_structured_facts_and_frozen():
    operation = QcThresholdOperation("qc", "n_genes", "ge", TypedScalar.from_value(200), "drop", "high")
    with pytest.raises(FrozenInstanceError):
        operation.column_id = "formula:n_genes > 200"
    with pytest.raises(ValueError, match="comparison"):
        QcThresholdOperation("x", "n_genes", "eval", TypedScalar.from_value(200), "drop", "high")


def test_declaration_rejects_formula_or_callback_payloads():
    with pytest.raises((TypeError, ValueError)):
        RowLedgerDeclaration(operations=({"predicate": "df.query(expr)"},), **{
            "schema_version": "row-ledger-schema-v1", "source_snapshot_identity": "sha256:s",
            "count_layer_identity": "sha256:c", "source_occurrence_id_columns": ("id",),
            "fitted_source_occurrence_ids": (), "evaluation_relation": "not_applicable",
            "evaluation_relation_confidence": "high", "fitted_result_id": "r",
            "target_coefficient": "condition[T.B]", "field_confidence": {
                "source_snapshot_identity": "high", "count_layer_identity": "high",
                "source_occurrence_id_columns": "high", "fitted_source_occurrence_ids": "high",
                "evaluation_relation": "high", "fitted_result_id": "high", "target_coefficient": "high",
            }})
