from dataclasses import FrozenInstanceError
import numpy as np
import pytest

from sc_referee.engine import build_pseudobulk_sample_rows
from sc_referee.row_ledger import (
    EvaluationRelation, RowLedgerState, Stage, aggregate_positions, build_aggregation_ledger,
    reconstruct_row_ledger, replay_source_operations,
)
from tests.test_row_ledger_replay import clean_eight_cell_case


def test_ledger_and_count_aggregation_consume_identical_group_positions():
    source,counts,design,declaration=clean_eight_cell_case()
    replay=replay_source_operations(source,counts,design,declaration)
    grouped=build_pseudobulk_sample_rows(replay.survivor_rows,design)
    aggregated=aggregate_positions(counts[list(replay.survivor_source_positions)],grouped.group_positions)
    artifact=build_aggregation_ledger(replay,grouped,aggregated,declaration)
    assert [[x.value for x in row.canonical_row_key] for row in artifact.fitted_occurrences] == [["d1","A"],["d1","B"],["d2","B"]]
    np.testing.assert_array_equal(aggregated,np.vstack([[11,3],[4,2],[15,1]]))


def test_clean_declared_pipeline_is_ratified_for_fit_and_evaluation():
    source,counts,design,declaration=clean_eight_cell_case()
    result=reconstruct_row_ledger(source,counts,design,declaration,required_stages=(Stage.FIT,Stage.EVALUATION))
    assert result.state is RowLedgerState.CERTIFIED_ROWS_RATIFIED
    assert result.certified_stages == (Stage.FIT,Stage.EVALUATION)
    assert result.artifact.evaluation.relation is EvaluationRelation.VERIFIED_SAME_AS_FITTED
    assert result.artifact.row_ledger_identity != result.artifact.core_pseudobulk_row_identity


def test_published_artifact_is_deeply_immutable():
    source,counts,design,declaration=clean_eight_cell_case()
    artifact=reconstruct_row_ledger(source,counts,design,declaration).artifact
    with pytest.raises(FrozenInstanceError): artifact.row_ledger_identity="sha256:forged"
    with pytest.raises(TypeError): artifact.fitted_occurrences[0].carried_values[0] = ("condition","forged")


def test_zero_count_derived_row_has_one_terminal_exclusion_and_no_fitted_position():
    source,counts,design,declaration=clean_eight_cell_case(); counts=counts.copy(); counts[3]=0
    result=reconstruct_row_ledger(source,counts,design,declaration)
    zero=[x for x in result.artifact.exclusions if x.reason.value == "zero_count_row"]
    assert len(zero) == 1
    assert [x.value for x in zero[0].affected_occurrence_id] == ["d1","B",0]
    assert all([x.value for x in row.canonical_row_key] != ["d1","B"]
               for row in result.artifact.fitted_occurrences)
