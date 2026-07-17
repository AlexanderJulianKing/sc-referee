from dataclasses import replace

import pytest
from scipy import sparse

# Load the existing check package before fitted_design, matching the application import spine.
from sc_referee.checks.confounding_strong import ConfoundingStrongCheck  # noqa: F401
from sc_referee.checks.confounding_random_intercept import ConfoundingRandomInterceptCheck  # noqa: F401
from sc_referee.engine import apply_row_ledger_evidence, build_pseudobulk_sample_rows
from sc_referee.fitted_design import request_from_confirmed_design
from sc_referee.row_ledger import RowLedgerState, RowsExactBasis, reconstruct_row_ledger, replay_source_operations
from tests.test_row_ledger_replay import clean_eight_cell_case, ids


def _fitted_rows(source, counts, design, declaration):
    replay=replay_source_operations(source,counts,design,declaration)
    return build_pseudobulk_sample_rows(replay.survivor_rows,design)


def test_absent_ledger_is_an_identity_operation_for_legacy_fitted_rows():
    source,counts,design,declaration=clean_eight_cell_case()
    legacy=_fitted_rows(source,counts,design,declaration)
    composed=apply_row_ledger_evidence(legacy,None,design)
    assert composed is legacy and composed.rows_exact_basis is RowsExactBasis.HUMAN_DECLARED


def test_certified_ledger_strengthens_only_an_already_true_legacy_gate():
    source,counts,design,declaration=clean_eight_cell_case()
    rows=_fitted_rows(source,counts,design,declaration)
    ledger=reconstruct_row_ledger(source,counts,design,declaration)
    composed=apply_row_ledger_evidence(rows,ledger,design)
    request=request_from_confirmed_design(design,composed)
    assert request.rows_exact is True
    assert request.rows_exact_basis is RowsExactBasis.RECONSTRUCTED_CERTIFIED
    assert request.row_ledger_identity == ledger.artifact.row_ledger_identity


def test_certification_never_upgrades_false_human_rows_exact():
    source,counts,design,declaration=clean_eight_cell_case()
    rows=_fitted_rows(source,counts,design,declaration)
    ledger=reconstruct_row_ledger(source,counts,design,declaration)
    false_design=replace(design,fitted_design=replace(design.fitted_design,rows_exact=False))
    composed=apply_row_ledger_evidence(rows,ledger,false_design)
    request=request_from_confirmed_design(false_design,composed)
    assert request.rows_exact is False and request.rows_exact_basis is RowsExactBasis.UNAVAILABLE


def test_not_audited_ledger_uses_existing_rows_inexact_abstention():
    source,counts,design,declaration=clean_eight_cell_case()
    rows=_fitted_rows(source,counts,design,declaration)
    ledger=reconstruct_row_ledger(source,counts,design,
        replace(declaration,fitted_source_occurrence_ids=ids("c1","c2","c4","c5")))
    assert ledger.state is RowLedgerState.NOT_AUDITED
    composed=apply_row_ledger_evidence(rows,ledger,design)
    assert not composed.exact and composed.machine_reason == "rows_not_exact"


def test_core_identity_mismatch_demotes_instead_of_rebinding_rows():
    source,counts,design,declaration=clean_eight_cell_case()
    replay=replay_source_operations(source,counts,design,declaration)
    reordered=build_pseudobulk_sample_rows(replay.survivor_rows.iloc[::-1],design)
    ledger=reconstruct_row_ledger(source,counts,design,declaration)
    composed=apply_row_ledger_evidence(reordered,ledger,design)
    assert not composed.exact and composed.rows_exact_basis is RowsExactBasis.UNAVAILABLE


def test_row_ledger_result_has_no_finding_surface():
    source,counts,design,declaration=clean_eight_cell_case()
    result=reconstruct_row_ledger(source,counts,design,declaration)
    assert set(result.__dataclass_fields__) == {"state","reason","machine_reason","certified_stages","artifact","diagnostic"}
    assert not hasattr(result,"status") and not hasattr(result,"judgment") and not hasattr(result,"proof_grade")


@pytest.mark.parametrize("matrix_type", [sparse.csr_matrix, sparse.csc_matrix])
def test_sparse_counts_reconstruct_the_same_certified_ledger(matrix_type):
    source,counts,design,declaration=clean_eight_cell_case()
    dense=reconstruct_row_ledger(source,counts,design,declaration)
    observed=reconstruct_row_ledger(source,matrix_type(counts),design,declaration)
    assert observed.state is RowLedgerState.CERTIFIED_ROWS_RATIFIED
    assert observed.artifact.row_ledger_identity == dense.artifact.row_ledger_identity
