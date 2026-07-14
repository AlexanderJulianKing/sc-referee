"""Effect-allele orientation: report-bound donor-level sign conformance for a narrow eQTL contract."""
from __future__ import annotations

import numpy as np

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.citations import CITATIONS
from sc_referee.design import confidence_high
from sc_referee.engines.eqtl_sign import recompute_eqtl_sign, resolve_orientation

CHECK_ID = "allele_orientation"


def _f(status, verdict, *, coverage=None, judgment=None, **metrics):
    if coverage is None:
        coverage = S.NOT_RUN if status == S.NOT_AUDITED else S.COMPLETE
    if judgment is None:
        judgment = {S.BLOCKER: S.VIOLATION, S.PASS: S.CONFORMANT}.get(status)
    return Finding(CHECK_ID, status, verdict, metrics=metrics, citations=CITATIONS[CHECK_ID],
                   coverage=coverage, judgment=judgment)


def _missing_contract_facts(design):
    required = (
        "variant_id", "genotype_column", "target_feature", "effect_allele", "variant_alleles",
        "dosage_ploidy", "eqtl_estimator", "eqtl_outcome_scale",
    )
    missing = [name for name in required if getattr(design, name, None) is None]
    has_direct = design.dosage_counts_allele is not None
    has_frequency = (design.effect_allele_frequency_interval is not None
                     and design.effect_allele_frequency_scope == "audited_donors")
    if not has_direct and not has_frequency:
        missing.append("orientation_footprint")
    return missing


def _missing_contract_labels(missing):
    labels = {
        "variant_id": "variant ID",
        "genotype_column": "genotype column",
        "target_feature": "target feature",
        "effect_allele": "effect allele",
        "variant_alleles": "variant alleles",
        "dosage_ploidy": "ploidy",
        "eqtl_estimator": "estimator",
        "eqtl_outcome_scale": "outcome scale",
        "orientation_footprint": "allele-orientation metadata",
    }
    return ", ".join(labels.get(name, name.replace("_", " ")) for name in missing)


def _supported_model_contract(design):
    """The MVP is an unadjusted OLS-with-intercept slope. None means that exact declared default;
    when a formula is supplied, accept only the literal one-predictor equivalent. Over-abstention is
    safer than silently ignoring a covariate, weight, offset, interaction, or no-intercept term."""
    if design.eqtl_estimator != "ols" or design.eqtl_outcome_scale != "log2_cpm_plus_1":
        return False
    if design.model is None:
        return True
    compact = "".join(str(design.model).split())
    return compact == f"~{design.genotype_column}"


def _orientation_diagnostics(bundle, design) -> dict:
    """The one orientation-agnostic fact worth surfacing even when the referee abstains: the empirical
    effect-allele frequency mean(g)/2. When it sits at ~0.5 the dosage cannot be oriented from frequency
    either — which is precisely why the sign is unresolvable without a ratified allele. Deliberately does
    NOT surface a raw OLS slope: it is not estimator-equivalent to a reported NB/adjusted coefficient and
    would invite a false apples-to-apples comparison. Empty when the recompute cannot be formed."""
    raw = recompute_eqtl_sign(bundle, design, transform="identity")
    if raw.raw_frequency is None:
        return {}
    diagnostics = {"effect_allele_frequency": raw.raw_frequency}
    supported = (design.eqtl_estimator in (None, "ols")
                 and design.eqtl_outcome_scale in (None, "log2_cpm_plus_1"))
    if not supported and design.eqtl_estimator is not None:
        diagnostics["independent_recompute"] = (
            f"unavailable — reported model is {design.eqtl_estimator}, not the supported OLS")
    return diagnostics


def _reported_effect_value(design, reported, bundle):
    """Best-effort read of the reported effect for the target gene, for display in the verdict only."""
    report = reported if reported is not None else getattr(bundle, "reported_results", None)
    if (report is None or not hasattr(report, "columns") or report.columns.duplicated().any()
            or "feature_id" not in report.columns or "effect" not in report.columns):
        return None
    rows = report[report["feature_id"].astype(str) == str(design.target_feature)]
    if len(rows) != 1:
        return None
    try:
        value = rows.iloc[0]["effect"]
        return None if isinstance(value, (bool, np.bool_)) else float(value)
    except (TypeError, ValueError):
        return None


def _effect_phrase(design, reported, bundle) -> str:
    """Name the SPECIFIC effect the gate is talking about — the target gene, the variant, and the
    reported value when readable — so a verdict is never a generic 'the effect'."""
    gene, variant = design.target_feature, design.variant_id
    if gene is not None and variant is not None:
        who = f"the reported effect for {gene} (variant {variant})"
    elif gene is not None:
        who = f"the reported effect for {gene}"
    else:
        who = "the reported effect"
    value = _reported_effect_value(design, reported, bundle)
    if value is not None and np.isfinite(value) and value != 0:
        who += f" — reported as {value:+.3g} per allele-copy"
    return who


def evaluate_allele_orientation(design, bundle, reported=None):
    missing = _missing_contract_facts(design)
    if missing:
        return _f(
            S.NEEDS_EVIDENCE,
            f"Referee cannot certify whether {_effect_phrase(design, reported, bundle)} points up or "
            "down because the folder does not establish which allele the genotype dosage counts. "
            f"Add the missing {_missing_contract_labels(missing)}, then run the review again.",
            coverage=S.NOT_RUN, unresolved_contract=missing, **_orientation_diagnostics(bundle, design),
        )

    raw = recompute_eqtl_sign(bundle, design, transform="identity")
    if raw.raw_frequency is None:
        return _f(
            S.NOT_AUDITED,
            f"I couldn't rebuild the variant-versus-expression check from the donor-level data "
            f"({raw.reason}), so the reported direction was NOT audited.", recompute_reason=raw.reason,
        )
    orientation = resolve_orientation(design, raw.raw_frequency)
    if not orientation.resolved:
        return _f(
            S.NEEDS_EVIDENCE,
            f"I couldn't work out which allele the genotype dosage counts ({orientation.reason}) — "
            "and without that there's no way to know whether the reported direction should be read "
            "as-is or flipped, so I'm not judging the sign.", orientation_reason=orientation.reason,
            raw_dosage_frequency=raw.raw_frequency, coverage=S.NOT_RUN,
        )
    if not _supported_model_contract(design):
        return _f(
            S.NOT_AUDITED,
            f"your reported effect for {design.target_feature} (variant {design.variant_id}) was fit "
            f"with {design.eqtl_estimator!r} on {design.eqtl_outcome_scale!r}, but the only method I "
            "can independently reproduce here is a plain unadjusted straight-line fit (OLS) on "
            "log2(CPM+1). Different methods can legitimately disagree on the effect-allele "
            "orientation, so I did NOT re-derive the sign for this one.",
            estimator=design.eqtl_estimator, outcome_scale=design.eqtl_outcome_scale,
        )

    report = reported if reported is not None else getattr(bundle, "reported_results", None)
    if (report is None or not hasattr(report, "columns") or report.columns.duplicated().any()
            or "feature_id" not in report.columns):
        return _f(S.NOT_AUDITED, f"I couldn't find a results row for your target gene "
                  f"({design.target_feature}) to read a direction from, so the sign was NOT audited")
    target_rows = report[report["feature_id"].astype(str) == str(design.target_feature)]
    if len(target_rows) != 1 or "effect" not in target_rows.columns:
        return _f(
            S.NOT_AUDITED,
            f"I need exactly one results row for your target gene ({design.target_feature!r}) to "
            f"read its direction, but found {len(target_rows)}; the sign was NOT audited.",
            target_feature=design.target_feature, matching_report_rows=len(target_rows),
        )
    effect_value = target_rows.iloc[0]["effect"]
    try:
        reported_effect = (np.nan if isinstance(effect_value, (bool, np.bool_))
                           else float(effect_value))
    except (TypeError, ValueError):
        reported_effect = np.nan
    if not np.isfinite(reported_effect) or reported_effect == 0:
        return _f(
            S.NOT_AUDITED,
            f"the reported effect for your target gene ({design.target_feature}) is missing, not a "
            "finite number, or exactly zero — so it has no up-or-down direction to check.",
            target_feature=design.target_feature,
        )

    result = (raw if orientation.transform == "identity"
              else recompute_eqtl_sign(bundle, design, transform="complement"))
    if not result.identified:
        return _f(
            S.NOT_AUDITED,
            f"my independent donor-level fit couldn't settle on a direction ({result.reason}); the "
            "sign was NOT audited.", recompute_reason=result.reason, n_donors=result.n_donors,
            genotype_class_counts=result.class_counts,
        )

    reported_sign = 1 if reported_effect > 0 else -1
    metrics = {
        "variant_id": design.variant_id,
        "target_feature": design.target_feature,
        "reported_sign": reported_sign,
        "recomputed_sign": result.sign,
        "transform": orientation.transform,
        "orientation_source": orientation.source,
        "n_donors": result.n_donors,
        "genotype_class_counts": result.class_counts,
        "raw_dosage_frequency": result.raw_frequency,
        "slope": result.slope,
        "slope_se": result.se,
        "slope_ci95": [result.ci_low, result.ci_high],
        "magnitude_reproduced": False,
    }
    entitled = (design.confirmed_by_human
                and confidence_high(design, "allele_orientation")
                and confidence_high(design, "replicate_unit"))
    if reported_sign == result.sign:
        if not entitled:
            return _f(
                S.NEEDS_EVIDENCE,
                "good sign: the reported up-or-down direction matches what my independent "
                "donor-level check finds — but the allele bookkeeping (or the replicate setup) "
                "isn't confirmed yet, so I can't call it a clean pass. Confirm the design to "
                "upgrade this to a pass.",
                coverage=S.NOT_RUN, **metrics,
            )
        return _f(
            S.PASS,
            f"the reported direction (per copy of the {design.effect_allele} allele) agrees with my "
            "independent donor-level recomputation, using the confirmed rule for which allele the "
            "dosage counts. This checks the up-or-down direction only — I did not try to reproduce "
            "the effect's size.",
            **metrics,
        )

    if not entitled:
        return _f(
            S.NEEDS_EVIDENCE,
            "the reported up-or-down direction disagrees with my independent donor-level check — "
            "but the allele bookkeeping (or the replicate setup) isn't confirmed yet, so I won't "
            "hard-block. Confirm the design (sc-referee confirm) to turn a genuine disagreement "
            "into a blocking verdict.",
            coverage=S.NOT_RUN, **metrics,
        )
    return _f(
        S.BLOCKER,
        f"effect-allele orientation error for {design.target_feature} (variant {design.variant_id}): "
        f"your report says {design.target_feature} expression goes "
        f"{'UP' if reported_sign > 0 else 'DOWN'} with each extra copy of the {design.effect_allele} "
        f"allele, but my independent donor-level recomputation — using the confirmed rule for which "
        f"allele the dosage counts — says it goes the other way "
        f"({'UP' if result.sign > 0 else 'DOWN'}). The reported direction is flipped, most often "
        f"from mixing up which allele the genotype number counts. Re-check the allele the effect is "
        f"reported 'per' and flip the sign if needed. (This is about direction only; I did not "
        f"check the effect's size.)",
        **metrics,
    )


class AlleleOrientationCheck:
    id = CHECK_ID
    analysis_types = ("eqtl",)
    audit_dimensions = ("orientation",)
    proof_basis = "independent recompute"
    contract_fields = (
        "variant_id", "genotype_column", "target_feature", "effect_allele",
        "dosage_counts_allele", "variant_alleles", "dosage_ploidy",
        "effect_allele_frequency_interval", "effect_allele_frequency_scope",
        "eqtl_estimator", "eqtl_outcome_scale", "replicate_unit", "model", "subset",
    )
    claim_template = "reported eQTL effect sign for {variant_id} on {target_feature}"
    max_status = S.BLOCKER

    def applies_to(self, design, bundle):
        return design.analysis_type == "eqtl" and bundle is not None

    def run(self, design, bundle, reported=None):
        return evaluate_allele_orientation(design, bundle, reported)
