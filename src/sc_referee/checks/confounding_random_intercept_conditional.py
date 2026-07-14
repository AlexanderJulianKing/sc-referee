"""Premise-gated Stage-2 assessment of exact random-intercept batch geometry."""
from __future__ import annotations

from sc_referee import statuses as S
from sc_referee.checks.base import ConditionalPremise, Finding
from sc_referee.checks.confounding_random_intercept import _RANDOM_MODES, _evaluate_batch
from sc_referee.checks.csp_routing import read_batch_premise
from sc_referee.citations import CITATIONS
from sc_referee.csp import RatifiedFactSet
from sc_referee.csp_contracts.between_group_adjustment_obligation_v1 import PREMISE_TEMPLATE
from sc_referee.engine import build_pseudobulk_sample_rows


CHECK_ID = "confounding_random_intercept_conditional"


def _finding(status, verdict, metrics, *, applicability, coverage, judgment=None,
             proof_grade=None, conditional_on=None):
    if status == S.MAJOR and conditional_on is None:
        raise ValueError("conditional MAJOR requires a first-class premise marker")
    return Finding(
        CHECK_ID, status, verdict, metrics=metrics, citations=CITATIONS[CHECK_ID],
        applicability=applicability, coverage=coverage, judgment=judgment,
        proof_grade=proof_grade, conditional_on=conditional_on,
    )


class ConfoundingRandomInterceptConditionalCheck:
    id = CHECK_ID
    analysis_types = ("condition_contrast_DE",)
    audit_dimensions = ("conditioning_set",)
    proof_basis = "exact batch witness conditioned on an exact ratified scientific premise"
    contract_fields = ("condition", "batch", "analyst_adjusted_for", "aggregation_key",
                       "fitted_design", "subset", "estimand_id", "csp_contracts")
    max_status = S.MAJOR

    def _reads(self, design, bundle):
        try:
            fitted_rows = build_pseudobulk_sample_rows(bundle.observations, design)
        except Exception:
            return None, []
        return fitted_rows, [
            (batch, read_batch_premise(design, fitted_rows, batch))
            for batch in design.batch
        ]

    def applies_to(self, design, bundle):
        if design.analysis_type not in self.analysis_types or not design.batch:
            return False
        declaration = design.fitted_design
        if declaration is None:
            return False
        owned = [batch for batch in design.batch
                 if batch in declaration.batch_modeling
                 and declaration.batch_modeling[batch].modeled_as in _RANDOM_MODES
                 and declaration.batch_modeling[batch].field_confidence.get("modeled_as") == "high"]
        if not owned:
            return False
        _, reads = self._reads(design, bundle)
        return any(batch in owned and isinstance(read, RatifiedFactSet)
                   for batch, read in reads)

    def cannot_evaluate(self, design, bundle):
        return None

    def run(self, design, bundle, reported=None):
        fitted_rows, reads = self._reads(design, bundle)
        if fitted_rows is None:
            return _finding(
                S.NOT_AUDITED, "The exact fitted rows needed for this premise-dependent check "
                "were unavailable.", {"machine_reason": "fitted_rows_unavailable"},
                applicability=S.UNKNOWN, coverage=S.NOT_RUN,
            )
        ratified = [(batch, read) for batch, read in reads if isinstance(read, RatifiedFactSet)]
        if not ratified:
            return _finding(
                S.NOT_AUDITED, "No exact ratified premise was available for this direct Stage-2 "
                "evaluation.", {"machine_reason": "csp_read_abstained"},
                applicability=S.UNKNOWN, coverage=S.NOT_RUN,
            )
        evaluated = [(batch, facts, _evaluate_batch(design, fitted_rows, batch))
                     for batch, facts in ratified]

        # G-fixed-span: a certified fixed span satisfies the obligation.  Ownership remains
        # Stage 2 after ratification, but the result explicitly defers to the autonomous clear.
        deferred = [item for item in evaluated if item[2]["category"] == "defer"]
        adverse = [item for item in evaluated if item[2]["category"] == "proposal"]
        abstained = [item for item in evaluated if item[2]["category"] == "abstain"]
        clears = [item for item in evaluated if item[2]["category"] == "clear"]
        if adverse:
            batch, facts, outcome = adverse[0]
            values = dict(facts.values)
            premise = PREMISE_TEMPLATE.format(group=batch)
            marker = ConditionalPremise(
                contract_id=facts.contract_id,
                contract_type=facts.contract_type,
                decisive_fields=values,
                plain_language_premise=premise,
                scope={
                    "fitted_result_id": facts.scope.fitted_result_id,
                    "contrast_name": facts.scope.contrast_name,
                    "target_coefficient": facts.scope.target_coefficient,
                    "exposure_column": facts.scope.exposure_column,
                    "row_ledger_identity": facts.scope.row_ledger_identity,
                    "estimand_id": facts.scope.estimand_id,
                    "group_source_column": facts.scope.group_source_column,
                    "assignment_identity": facts.scope.assignment_identity,
                },
            )
            metrics = {
                "machine_reason": "conditional_material_association",
                "batch_outcome": outcome,
                "contract_id": facts.contract_id,
                "contract_type": facts.contract_type,
                "decisive_fields": values,
            }
            return _finding(
                S.MAJOR,
                f"Conditional on your confirmation that arbitrary differences among {batch} "
                "groups must be removed and this result may not rely on unrelated group baselines, "
                f"the captured fit models {batch} only through a random intercept and does not "
                "provide fixed-effect-equivalent conditioning for that premise.",
                metrics, applicability=S.APPLIES, coverage=S.COMPLETE,
                judgment=S.VIOLATION, proof_grade=S.EXACT, conditional_on=marker,
            )
        if abstained:
            _, _, outcome = abstained[0]
            return _finding(
                S.NOT_AUDITED, "The exact Stage-2 arithmetic or structure was unavailable.",
                {"machine_reason": outcome["machine_reason"], "batch_outcome": outcome},
                applicability=S.UNKNOWN, coverage=S.NOT_RUN,
            )
        if clears:
            _, facts, outcome = clears[0]
            return _finding(
                S.PASS, "The exact condition–batch partial R² was below the frozen threshold.",
                {"machine_reason": outcome["machine_reason"], "batch_outcome": outcome,
                 "contract_id": facts.contract_id, "contract_type": facts.contract_type,
                 "decisive_fields": dict(facts.values)},
                applicability=S.APPLIES, coverage=S.COMPLETE,
                judgment=S.CONFORMANT, proof_grade=S.EXACT,
            )
        _, _, outcome = deferred[0]
        return _finding(
            S.PASS, "This premise-dependent assessment defers to the certified fixed span.",
            {"machine_reason": outcome["machine_reason"], "batch_outcome": outcome},
            applicability=S.NOT_APPLICABLE, coverage=S.COMPLETE,
        )
