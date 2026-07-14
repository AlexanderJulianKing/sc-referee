"""Exact fitted-design geometry audit for human-declared categorical batches."""
from __future__ import annotations

from dataclasses import asdict

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.checks.confounding import (
    OMITTED_R2_MAJOR, PARTIAL_R2_CUT_EPSILON, PARTIAL_R2_NUMERIC_POLICY_VERSION,
    PartialR2Decision, _partial_r2, decide_partial_r2,
)
from sc_referee.column_space import CertificationState, ColumnSpaceCertificate, certify_column_space
from sc_referee.design import confidence_high
from sc_referee.design_matrix import DesignMatrixError, build_fixed_effect_matrix
from sc_referee.engine import build_pseudobulk_sample_rows
from sc_referee.fitted_design import (
    certificate_abstention_finding, reconstruct_nuisance_design, request_from_confirmed_design,
)


def _abstain(machine_reason: str, reason: str) -> Finding:
    return certificate_abstention_finding(
        "confounding_strong",
        ColumnSpaceCertificate(CertificationState.NOT_AUDITED, reason, machine_reason),
    )


def evaluate_confounding_strong(observations, design, fitted_rows) -> Finding:
    required = ("condition", "batch", "analyst_adjusted_for", "aggregation_key", "fitted_design")
    if not design.confirmed_by_human or any(not confidence_high(design, field) for field in required):
        return _abstain("strong_declaration_not_ratified", "Required fitted-design facts were not ratified at high confidence.")
    declaration = design.fitted_design
    upstream = [] if declaration is None else [
        batch for batch in design.batch
        if batch in declaration.batch_modeling
        and declaration.batch_modeling[batch].modeled_as == "upstream_handled"
        and declaration.batch_modeling[batch].field_confidence.get("modeled_as") == "high"
    ]
    if upstream:
        return _abstain(
            "upstream_handling_not_independently_certified",
            "batch corrected upstream — a design-matrix check cannot verify it",
        )
    if declaration is not None and not declaration.intercept:
        return _abstain("no_verified_intercept", "No verified intercept-bearing conditioning operator was declared.")
    if not fitted_rows.exact:
        return _abstain(fitted_rows.machine_reason, fitted_rows.reason)

    request = request_from_confirmed_design(design, fitted_rows)
    reconstruction = reconstruct_nuisance_design(fitted_rows.rows, design, request)
    if reconstruction.state is CertificationState.NOT_AUDITED:
        return certificate_abstention_finding("confounding_strong", reconstruction)
    artifact = reconstruction.artifact
    try:
        batch_kinds = {source: request.column_kinds[source] for source in design.batch}
        batch_levels = {
            source: request.categorical_levels[source]
            for source in design.batch if batch_kinds[source] == "categorical"
        }
        h = build_fixed_effect_matrix(
            fitted_rows.rows, source_columns=tuple(design.batch), column_kinds=batch_kinds,
            categorical_levels=batch_levels, intercept=False,
        )
    except (KeyError, DesignMatrixError, TypeError, ValueError) as error:
        return _abstain("batch_matrix_unavailable", f"The declared batch block could not be reconstructed: {error}.")
    if h.row_identity != artifact.row_identity:
        return _abstain("row_identity_mismatch", "The batch and fitted nuisance rows or order do not match.")

    certificate = certify_column_space(
        artifact.c, h.matrix, c_columns=artifact.c_column_ids,
        excluded_exposure_columns=artifact.excluded_exposure_columns,
        h_mapping=h.column_ids, row_ledger_identity=artifact.row_ledger_identity, exact=True,
    )
    if certificate.state is CertificationState.NOT_AUDITED:
        return certificate_abstention_finding("confounding_strong", certificate)

    rows = fitted_rows.rows
    contrast_column, reference, test = design.contrast_column_and_levels()
    sub = rows[rows[contrast_column].isin([reference, test])].reset_index(drop=True)
    t = (sub[contrast_column] == test).to_numpy(dtype=float)
    included = sorted(
        (set(design.analyst_adjusted_for or []) - {design.target_term}) & set(sub.columns)
    )
    batch_block = sorted((set(design.batch) & set(sub.columns)) - set(included))
    batch_partial_r2 = _partial_r2(sub, t, included, batch_block)
    partial_r2_decision = decide_partial_r2(batch_partial_r2)
    metrics = {
        "column_space_state": certificate.state.value,
        "certificate_reason": certificate.reason,
        "batch_columns": list(design.batch),
        "batch_partial_r2": batch_partial_r2,
        "omitted_r2_major": OMITTED_R2_MAJOR,
        "layer1_check_id": "confounding",
        "witness": asdict(certificate.witness),
    }
    if certificate.state is CertificationState.CERTIFIED:
        return Finding(
            "confounding_strong", S.PASS,
            "The exact fitted design conditions on the declared batch column space.", metrics,
            judgment=S.CONFORMANT, proof_grade=S.EXACT,
        )
    if partial_r2_decision is PartialR2Decision.INDETERMINATE_NEAR_CUT:
        metrics.update(
            partial_r2_decision=partial_r2_decision.value,
            partial_r2_numeric_policy=PARTIAL_R2_NUMERIC_POLICY_VERSION,
            partial_r2_cut_epsilon=PARTIAL_R2_CUT_EPSILON,
        )
        return Finding(
            "confounding_strong", S.NOT_AUDITED,
            "The exposure-batch partial R-squared is at the materiality threshold within "
            "float64 least-squares numerical error, so the span failure was not adjudicated.",
            metrics, coverage=S.NOT_RUN,
        )
    if partial_r2_decision is PartialR2Decision.IMMATERIAL:
        return Finding(
            "confounding_strong", S.PASS,
            "The fitted design does not span the batch, but the measured conditional "
            f"exposure–batch association is below {OMITTED_R2_MAJOR:.2f}. This check did not "
            "measure batch effects on outcomes or rule out omitted-variable bias.",
            metrics, judgment=S.CONFORMANT, proof_grade=S.EXACT,
        )
    # This asserts only a property of the fitted design. Upstream count-level correction is not
    # visible here, so this verdict intentionally makes no claim about an effect-size bias magnitude.
    names = ", ".join(map(str, design.batch))
    witness = certificate.witness
    return Finding(
        "confounding_strong", S.MAJOR,
        f"Your fitted design does not condition on the declared batch ({names}); "
        f"batch partial R²={batch_partial_r2:.3f}, rho={witness.rho:.3g} exceeds tau={witness.tau:.3g}. "
        "Add a supported batch term or supply the exact supported fitted operator.",
        metrics, judgment=S.VIOLATION, proof_grade=S.EXACT,
    )


class ConfoundingStrongCheck:
    id = "confounding_strong"
    analysis_types = ("condition_contrast_DE",)
    audit_dimensions = ("conditioning_set",)
    proof_basis = "exact fitted-design column-space certificate"
    contract_fields = ("condition", "batch", "analyst_adjusted_for", "aggregation_key", "fitted_design", "subset")
    max_status = S.MAJOR

    def applies_to(self, design, bundle):
        return design.analysis_type in self.analysis_types and bool(design.batch)

    def cannot_evaluate(self, design, bundle):
        return None

    def run(self, design, bundle, reported=None):
        rows = build_pseudobulk_sample_rows(bundle.observations, design)
        return evaluate_confounding_strong(bundle.observations, design, rows)
