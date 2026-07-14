"""Abstention-only assessment of exact, human-ratified random-intercept batch facts."""
from __future__ import annotations

from dataclasses import asdict

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.checks.confounding import (
    OMITTED_R2_MAJOR, PARTIAL_R2_CUT_EPSILON, PARTIAL_R2_NUMERIC_POLICY_VERSION,
    PartialR2Decision, _partial_r2, decide_partial_r2,
)
from sc_referee.citations import CITATIONS
from sc_referee.column_space import CertificationState, certify_column_space
from sc_referee.design_matrix import DesignMatrixError, build_fixed_effect_matrix
from sc_referee.engine import build_pseudobulk_sample_rows
from sc_referee.fitted_design import reconstruct_fixed_component_for_batch
from sc_referee.csp import RatifiedFactSet
from sc_referee.checks.csp_routing import read_batch_premise


CHECK_ID = "confounding_random_intercept"
_RANDOM_MODES = frozenset(("random_intercept", "fixed_and_random_intercept"))


def _finding(status, verdict, metrics, *, applicability, coverage, judgment=None, proof_grade=None):
    return Finding(
        CHECK_ID, status, verdict, metrics=metrics,
        citations=CITATIONS.get(CHECK_ID, CITATIONS["confounding"]),
        applicability=applicability, coverage=coverage, judgment=judgment,
        proof_grade=proof_grade,
    )


def _outcome(batch, category, machine_reason, **metrics):
    return {
        "batch": batch, "category": category, "machine_reason": machine_reason,
        "layer1_check_id": "confounding", "omitted_r2_major": OMITTED_R2_MAJOR,
        **metrics,
    }


def _evaluate_batch(design, fitted_rows, batch):
    declaration = design.fitted_design
    entry = None if declaration is None else declaration.batch_modeling.get(batch)
    if entry is None:
        return _outcome(batch, "abstain", "batch_ledger_unratified", modeled_as=None)
    base = {"modeled_as": entry.modeled_as,
            "computed_row_ledger_identity": fitted_rows.row_ledger_identity}
    if entry.modeled_as in ("fixed", "absent"):
        return _outcome(batch, "defer", "batch_component_not_in_scope", **base)
    if entry.modeled_as == "upstream_handled":
        return _outcome(batch, "abstain", "upstream_certificate_unavailable", **base)
    if entry.modeled_as == "unsupported":
        return _outcome(batch, "abstain", "unsupported_batch_component", **base)
    if entry.modeled_as not in _RANDOM_MODES:
        return _outcome(batch, "abstain", "batch_ledger_unratified", **base)
    if any(value != "high" for value in entry.field_confidence.values()):
        return _outcome(batch, "abstain", "batch_ledger_unratified", **base)
    if not entry.rows_exact or not fitted_rows.exact:
        return _outcome(batch, "abstain", "batch_rows_not_exact", **base)
    if entry.row_ledger_identity != fitted_rows.row_ledger_identity:
        return _outcome(batch, "abstain", "batch_row_identity_mismatch", **base)
    if (entry.component_scope.contrast_name != design.name
            or entry.component_scope.target_coefficient != design.target_coefficient):
        return _outcome(batch, "abstain", "batch_component_scope_mismatch", **base)
    if entry.random_group_column != batch:
        return _outcome(batch, "abstain", "random_group_column_mismatch", **base)
    if entry.unsupported_components:
        return _outcome(batch, "abstain", "unsupported_batch_component", **base)
    if entry.fixed_source_columns is None:
        return _outcome(batch, "abstain", "fixed_sources_unresolved", **base)

    reconstruction = reconstruct_fixed_component_for_batch(
        fitted_rows.rows, design, fitted_rows, batch
    )
    if reconstruction.state is CertificationState.NOT_AUDITED:
        return _outcome(batch, "abstain", reconstruction.machine_reason,
                        fixed_span_state=reconstruction.state.value, **base)
    artifact = reconstruction.artifact
    try:
        kind = declaration.column_kinds[batch]
        levels = ({batch: declaration.categorical_levels[batch]}
                  if kind == "categorical" else {})
        h = build_fixed_effect_matrix(
            fitted_rows.rows, source_columns=(batch,), column_kinds={batch: kind},
            categorical_levels=levels, intercept=False,
        )
    except (KeyError, DesignMatrixError, TypeError, ValueError):
        return _outcome(batch, "abstain", "batch_matrix_unavailable", **base)
    if h.row_identity != artifact.row_identity:
        return _outcome(batch, "abstain", "row_identity_mismatch", **base)
    certificate = certify_column_space(
        artifact.c, h.matrix, c_columns=artifact.c_column_ids,
        excluded_exposure_columns=artifact.excluded_exposure_columns,
        h_mapping=h.column_ids, row_ledger_identity=artifact.row_ledger_identity, exact=True,
    )
    certificate_metrics = {
        "fixed_span_state": certificate.state.value,
        "fixed_span_machine_reason": certificate.machine_reason,
        "fixed_span_witness": (asdict(certificate.witness) if certificate.witness else None),
    }
    if certificate.state is CertificationState.CERTIFIED:
        return _outcome(batch, "defer", "fixed_span_certified", **base, **certificate_metrics)
    if certificate.state is CertificationState.NOT_AUDITED:
        return _outcome(batch, "abstain", certificate.machine_reason,
                        **base, **certificate_metrics)
    if entry.modeled_as == "fixed_and_random_intercept":
        return _outcome(batch, "abstain", "fixed_span_not_certified",
                        **base, **certificate_metrics)

    rows = fitted_rows.rows
    contrast_column, reference, test = design.contrast_column_and_levels()
    if contrast_column not in rows.columns:
        return _outcome(batch, "abstain", "contrast_rows_unavailable", **base)
    sub = rows[rows[contrast_column].isin([reference, test])].reset_index(drop=True)
    t = (sub[contrast_column] == test).to_numpy(dtype=float)
    included = sorted(
        (set(design.analyst_adjusted_for or ()) - {design.target_term}) & set(sub.columns)
    )
    batch_block = sorted(({batch} - set(included)) & set(sub.columns))
    batch_partial_r2 = _partial_r2(sub, t, included, batch_block)
    if batch_partial_r2 is None:
        return _outcome(batch, "abstain", "batch_partial_r2_unavailable",
                        **base, **certificate_metrics)
    decision = decide_partial_r2(batch_partial_r2)
    if decision is PartialR2Decision.INDETERMINATE_NEAR_CUT:
        return _outcome(
            batch, "abstain", "partial_r2_indeterminate_near_cut",
            batch_partial_r2=batch_partial_r2,
            partial_r2_decision=decision.value,
            partial_r2_numeric_policy=PARTIAL_R2_NUMERIC_POLICY_VERSION,
            partial_r2_cut_epsilon=PARTIAL_R2_CUT_EPSILON,
            **base, **certificate_metrics,
        )
    category = "proposal" if decision is PartialR2Decision.MATERIAL else "clear"
    return _outcome(batch, category, "material_association" if category == "proposal"
                    else "below_materiality_threshold", batch_partial_r2=batch_partial_r2,
                    **base, **certificate_metrics)


class ConfoundingRandomInterceptCheck:
    id = CHECK_ID
    analysis_types = ("condition_contrast_DE",)
    audit_dimensions = ("conditioning_set",)
    proof_basis = "exact ratified batch ledger, fixed-span certificate, and partial R-squared"
    contract_fields = ("condition", "batch", "analyst_adjusted_for", "aggregation_key",
                       "fitted_design", "subset")
    max_status = S.NEEDS_EVIDENCE

    def applies_to(self, design, bundle):
        if design.analysis_type not in self.analysis_types or not design.batch:
            return False
        declaration = design.fitted_design
        if declaration is None:
            return False
        owned = [
            batch for batch in design.batch
            if (
            batch in declaration.batch_modeling
            and declaration.batch_modeling[batch].modeled_as in _RANDOM_MODES
            and declaration.batch_modeling[batch].field_confidence.get("modeled_as") == "high"
            )
        ]
        if not owned:
            return False
        try:
            fitted_rows = build_pseudobulk_sample_rows(bundle.observations, design)
        except Exception:
            return True
        return any(not isinstance(read_batch_premise(design, fitted_rows, batch), RatifiedFactSet)
                   for batch in design.batch)

    def cannot_evaluate(self, design, bundle):
        return None

    def run(self, design, bundle, reported=None):
        fitted_rows = build_pseudobulk_sample_rows(bundle.observations, design)
        declaration = design.fitted_design
        owned = [
            batch for batch in design.batch
            if declaration is not None and batch in declaration.batch_modeling
            and declaration.batch_modeling[batch].modeled_as in _RANDOM_MODES
            and declaration.batch_modeling[batch].field_confidence.get("modeled_as") == "high"
        ]
        stage1_owned = [
            batch for batch in design.batch
            if not isinstance(read_batch_premise(design, fitted_rows, batch), RatifiedFactSet)
        ]
        outcomes = [_evaluate_batch(design, fitted_rows, batch) for batch in stage1_owned]
        if not outcomes:
            outcomes = [_outcome(None, "abstain", "batch_ledger_unratified", modeled_as=None)]
        metrics = {"batch_outcomes": outcomes}
        proposals = [row for row in outcomes if row["category"] == "proposal"]
        abstentions = [row for row in outcomes if row["category"] == "abstain"]
        clears = [row for row in outcomes if row["category"] == "clear"]
        if proposals:
            metrics["machine_reason"] = proposals[0]["machine_reason"]
            return _finding(
                S.NEEDS_EVIDENCE,
                "A random intercept partial-pools; it does not project. This does not condition on "
                "the batch the way a fixed effect does. The exact condition–batch partial R² met "
                "the frozen threshold; this structure-only assessment remains not checked.",
                metrics, applicability=S.UNKNOWN, coverage=S.NOT_RUN,
            )
        if abstentions:
            metrics["machine_reason"] = abstentions[0]["machine_reason"]
            return _finding(
                S.NOT_AUDITED,
                "The exact random-intercept batch structure could not be assessed from the "
                "ratified component and fitted-row facts.",
                metrics, applicability=S.UNKNOWN, coverage=S.NOT_RUN,
            )
        if clears:
            metrics["machine_reason"] = clears[0]["machine_reason"]
            return _finding(
                S.PASS,
                "This specific random-intercept-on-a-materially-associated-batch concern was not "
                "triggered; the exact condition–batch partial R² was below the frozen threshold.",
                metrics, applicability=S.APPLIES, coverage=S.COMPLETE,
                judgment=S.CONFORMANT, proof_grade=S.EXACT,
            )
        metrics["machine_reason"] = outcomes[0]["machine_reason"]
        return _finding(
            S.PASS, "This random-intercept-only assessment defers to the certified fixed span.",
            metrics, applicability=S.NOT_APPLICABLE, coverage=S.COMPLETE,
        )
