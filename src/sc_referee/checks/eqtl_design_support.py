"""Donor/genotype support for a donor-level eQTL coefficient."""
from __future__ import annotations

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.citations import CITATIONS
from sc_referee.engines.eqtl_sign import recompute_eqtl_sign


CHECK_ID = "eqtl_design_support"


class EqtlDesignSupportCheck:
    """Verify that a supplied eQTL has donor-level support across genotype classes.

    This deliberately says nothing about the reported effect's direction or magnitude. It certifies
    only the data structure that makes a donor-level genotype coefficient estimable.
    """

    id = CHECK_ID
    analysis_types = ("eqtl",)
    audit_dimensions = ("unit_of_independence",)
    proof_basis = "donor-level aggregation and genotype-class recount"
    contract_fields = (
        "analysis_type", "replicate_unit", "sample_unit", "genotype_column", "target_feature",
    )
    max_status = S.NOT_AUDITED

    def applies_to(self, design, bundle):
        measure = getattr(bundle, "measure", None) if bundle is not None else None
        observations = getattr(bundle, "observations", None) if bundle is not None else None
        return (
            design.analysis_type == "eqtl"
            and measure is not None
            and getattr(measure, "kind", None) == "counts"
            and observations is not None
            and getattr(design, "genotype_column", None) in observations.columns
            and bool(getattr(design, "replicate_unit", None))
            and bool(getattr(design, "target_feature", None))
        )

    def run(self, design, bundle, reported=None):
        result = recompute_eqtl_sign(bundle, design, transform="identity")
        supported_classes = sum(count >= 3 for count in result.class_counts.values())
        metrics = {
            "n_donors": result.n_donors,
            "genotype_class_counts": result.class_counts,
            "effect_allele_frequency": result.raw_frequency,
            "support_reason": result.reason,
        }
        if result.n_donors and supported_classes >= 2:
            classes = ", ".join(
                f"{dosage}: {count}" for dosage, count in sorted(result.class_counts.items())
            )
            return Finding(
                CHECK_ID,
                S.PASS,
                f"Referee verified a donor-level design with {result.n_donors} distinct donors. "
                f"Genotype dosage counts are {classes}, so the genotype coefficient has support "
                "across the supplied classes. This checks donor/genotype structure only; it does "
                "not validate the reported effect.",
                metrics=metrics,
                citations=CITATIONS[CHECK_ID],
                applicability=S.APPLIES,
                judgment=S.CONFORMANT,
                coverage=S.COMPLETE,
                proof_grade=S.RECOMPUTED,
            )
        return Finding(
            CHECK_ID,
            S.NOT_AUDITED,
            "Referee could not verify enough donor-level genotype support to evaluate the eQTL "
            "coefficient. Supply donor identifiers and genotype dosages, then run the review again.",
            metrics=metrics,
            citations=CITATIONS[CHECK_ID],
            applicability=S.APPLIES,
            judgment=S.UNRESOLVED,
            coverage=S.NOT_RUN,
        )
