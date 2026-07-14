from dataclasses import replace

import pytest

from sc_referee.column_space import CertificationState, certify_column_space
from sc_referee.design_matrix import build_fixed_effect_matrix
from sc_referee.engine import build_pseudobulk_sample_rows
from sc_referee.fitted_design import reconstruct_fixed_component_for_batch
from tests.factories import (
    fitted_design_declaration,
    make_design,
    pseudobulk_confounding_bundle,
    random_intercept_batch_declaration,
)


def _fixture(*, adjusted=("run", "condition"), entry_mutation=None,
             fixed_source_columns=("run",)):
    bundle = pseudobulk_confounding_bundle()
    entry = random_intercept_batch_declaration(
        modeled_as="fixed_and_random_intercept",
        fixed_source_columns=fixed_source_columns,
    )
    declaration = fitted_design_declaration(batch_modeling={"run": entry})
    design = make_design(
        batch=("run",), aggregation_key=("donor_id",), analyst_adjusted_for=list(adjusted),
        fitted_design=declaration,
        confidence={"condition": "high", "batch": "high", "analyst_adjusted_for": "high",
                    "aggregation_key": "high", "fitted_design": "high"},
    )
    rows = build_pseudobulk_sample_rows(bundle.observations, design)
    entry = replace(entry, row_ledger_identity=rows.row_ledger_identity)
    if entry_mutation:
        entry = entry_mutation(entry)
    design = replace(design, fitted_design=replace(declaration, batch_modeling={"run": entry}))
    return design, bundle, rows


def test_fixed_and_random_batch_uses_certificate_not_fixed_source_names():
    design, _, rows = _fixture()
    reconstruction = reconstruct_fixed_component_for_batch(rows.rows, design, rows, "run")
    h = build_fixed_effect_matrix(
        rows.rows, source_columns=("run",), column_kinds={"run": "categorical"},
        categorical_levels={"run": ("R1", "R2")}, intercept=False,
    )
    certificate = certify_column_space(
        reconstruction.artifact.c, h.matrix,
        c_columns=reconstruction.artifact.c_column_ids,
        excluded_exposure_columns=reconstruction.artifact.excluded_exposure_columns,
        h_mapping=h.column_ids,
        row_ledger_identity=reconstruction.artifact.row_ledger_identity, exact=True,
    )
    assert certificate.state is CertificationState.CERTIFIED


def test_fixed_source_claim_does_not_substitute_for_a_span_certificate():
    design, _, rows = _fixture(adjusted=("condition",))
    reconstruction = reconstruct_fixed_component_for_batch(rows.rows, design, rows, "run")
    assert reconstruction.state is CertificationState.CERTIFIED
    assert "run" not in reconstruction.artifact.c_source_columns


@pytest.mark.parametrize("mutation,machine_reason", [
    (lambda entry: replace(entry, rows_exact=False), "batch_rows_not_exact"),
    (lambda entry: replace(entry, row_ledger_identity="stale"), "batch_row_identity_mismatch"),
    (lambda entry: replace(entry, unsupported_components=("random_slope",)), "unsupported_batch_component"),
    (lambda entry: replace(entry, fixed_source_columns=None), "fixed_sources_unresolved"),
])
def test_fixed_component_reconstruction_is_atomic(mutation, machine_reason):
    design, _, rows = _fixture(entry_mutation=mutation)
    result = reconstruct_fixed_component_for_batch(rows.rows, design, rows, "run")
    assert result.state is CertificationState.NOT_AUDITED
    assert result.machine_reason == machine_reason
