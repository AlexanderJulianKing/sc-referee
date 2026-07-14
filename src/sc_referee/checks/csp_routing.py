"""Exact, shared CSP request construction for the two random-intercept routes."""
from __future__ import annotations

from sc_referee.csp import (
    CspAbstention, CspReadRequest, CspScope, assignment_identity, read_ratified_contract,
)
from sc_referee.csp_contracts.between_group_adjustment_obligation_v1 import (
    CONTRACT_TYPE,
    REQUIRED_FIELDS,
)


CONSUMER_ID = "confounding_random_intercept_conditional"


def read_batch_premise(design, fitted_rows, batch):
    declaration = design.fitted_design
    entry = None if declaration is None else declaration.batch_modeling.get(batch)
    exposure, _, _ = design.contrast_column_and_levels()
    if (entry is None or not design.estimand_id or not exposure
            or not design.target_coefficient or not fitted_rows.row_ledger_identity):
        return CspAbstention("scope_unavailable", None)
    try:
        scope = CspScope(
            fitted_result_id=entry.component_scope.fitted_result_id,
            contrast_name=design.name,
            target_coefficient=design.target_coefficient,
            exposure_column=exposure,
            row_ledger_identity=fitted_rows.row_ledger_identity,
            estimand_id=design.estimand_id,
            group_source_column=batch,
            assignment_identity=assignment_identity(fitted_rows.rows, exposure, batch),
        )
    except (TypeError, ValueError):
        return CspAbstention("scope_unavailable", None)
    return read_ratified_contract(
        design.csp_contracts,
        CspReadRequest(CONTRACT_TYPE, scope, REQUIRED_FIELDS, CONSUMER_ID),
    )
