"""Report-bound conformance to one narrow, ratified Hi-C loop-strength estimator."""
from __future__ import annotations

import numpy as np
import pandas as pd

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.citations import CITATIONS
from sc_referee.design import confidence_high
from sc_referee.engines.hic_loop_strength import recompute_hic_loop_strength

CHECK_ID = "hic_loop_strength"

SUPPORTED = {
    "hic_contact_scale": "raw_unbalanced_integer_counts",
    "hic_expected_model": "cis_exact_distance_arithmetic_mean_target_excluded_v1",
    "hic_mask_policy": "exclude_if_either_bin_masked_v1",
    "hic_zero_policy": "dense_including_zeros",
    "hic_pseudocount": 0.0,
    "hic_target_statistic": "single_pixel",
    "hic_replicate_functional": "equal_weight_mean_log2_oe_v1",
}


def _f(status, verdict, *, coverage=None, judgment=None, **metrics):
    if coverage is None:
        coverage = S.NOT_RUN if status == S.NOT_AUDITED else S.COMPLETE
    if judgment is None:
        judgment = {S.BLOCKER: S.VIOLATION, S.PASS: S.CONFORMANT}.get(status)
    return Finding(CHECK_ID, status, verdict, metrics=metrics, citations=CITATIONS[CHECK_ID],
                   coverage=coverage, judgment=judgment)


def _missing_contract_facts(design):
    required = (
        "condition", "reference", "test", "replicate_unit", "hic_genome_assembly",
        "hic_resolution_bp", "hic_target_bin_i", "hic_target_bin_j",
        "hic_background_view_start", "hic_background_view_end", "hic_contact_scale",
        "hic_expected_model", "hic_mask_policy", "hic_zero_policy", "hic_pseudocount",
        "hic_target_statistic", "hic_replicate_functional", "hic_report_delta_tolerance",
        "hic_report_delta_tolerance_authority",
    )
    missing = [name for name in required if getattr(design, name, None) is None]
    if not list(getattr(design, "replicate_unit", None) or []) and "replicate_unit" not in missing:
        missing.append("replicate_unit")
    return missing


def _unsupported_contract(design):
    return {name: {"declared": getattr(design, name, None), "supported": supported}
            for name, supported in SUPPORTED.items() if getattr(design, name, None) != supported}


def _unsupported_analysis_structure(design):
    """Generic Design facts that imply a functional outside the narrow unadjusted recompute."""
    unsupported = {}
    simple_model = f"~ {design.condition}"
    if design.model not in (None, simple_model):
        unsupported["model"] = {"declared": design.model, "supported": simple_model}
    if list(design.pairing_unit or []):
        unsupported["pairing_unit"] = {
            "declared": list(design.pairing_unit), "supported": [],
        }
    if design.subset:
        unsupported["subset"] = {"declared": design.subset, "supported": None}
    return unsupported


def _canonical_pair(left, right):
    if not isinstance(left, str) or not isinstance(right, str) or left == right:
        return None
    return (left, right) if left < right else (right, left)


def _bind_reported_delta(report, design):
    required = ["genome_assembly", "resolution_bp", "bin_i", "bin_j", "reference", "test", "delta"]
    if (not isinstance(report, pd.DataFrame) or report.columns.duplicated().any()
            or any(c not in report.columns for c in required)):
        return None, "report_table_missing_or_malformed", 0
    target = _canonical_pair(design.hic_target_bin_i, design.hic_target_bin_j)
    pairs = [_canonical_pair(a, b) for a, b in zip(report["bin_i"], report["bin_j"])]
    mask = ((report["genome_assembly"] == design.hic_genome_assembly)
            & (report["resolution_bp"] == design.hic_resolution_bp)
            & pd.Series([pair == target for pair in pairs], index=report.index)
            & (report["reference"] == design.reference)
            & (report["test"] == design.test))
    rows = report[mask]
    if len(rows) != 1:
        return None, "report_binding_not_unique", len(rows)
    value = rows.iloc[0]["delta"]
    try:
        delta = np.nan if isinstance(value, (bool, np.bool_)) else float(value)
    except (TypeError, ValueError):
        delta = np.nan
    if not np.isfinite(delta):
        return None, "reported_delta_missing_or_nonfinite", 1
    return delta, None, 1


def evaluate_hic_loop_strength(design, bundle, reported=None):
    missing = _missing_contract_facts(design)
    if missing:
        return _f(
            S.NEEDS_EVIDENCE,
            f"I can only re-check the reported loop-strength change once the recipe for computing it "
            f"is fully specified, and some of it is still blank (missing: {', '.join(missing)}). "
            f"Until then I can't certify the reported change. Fill in those fields in the design and "
            f"re-run.", coverage=S.NOT_RUN, unresolved_contract=missing,
        )
    tolerance = design.hic_report_delta_tolerance
    if (isinstance(tolerance, bool) or not isinstance(tolerance, (int, float))
            or not np.isfinite(float(tolerance)) or float(tolerance) < 0):
        return _f(S.NEEDS_EVIDENCE, "the allowed wiggle-room for matching the reported change (its "
                  "tolerance) is missing or not a valid non-negative number, so I can't judge "
                  "whether the reported value matches. Set a valid tolerance and re-run.",
                  coverage=S.NOT_RUN, report_delta_tolerance=tolerance)
    if design.hic_report_delta_tolerance_authority != "rounding_absolute_log2_ratio_delta":
        return _f(
            S.NEEDS_EVIDENCE,
            "the reported tolerance is not bound as an absolute rounding/numerical tolerance on "
            "the log2-ratio delta, so it cannot certify agreement.",
            coverage=S.NOT_RUN,
            report_delta_tolerance=tolerance,
            tolerance_authority=design.hic_report_delta_tolerance_authority,
        )
    unsupported = _unsupported_contract(design)
    unsupported_structure = _unsupported_analysis_structure(design)
    if unsupported or unsupported_structure:
        return _f(
            S.NOT_AUDITED,
            "the loop-strength recipe you declared is a valid one, but it is not the supported "
            "recipe I know how to reproduce exactly (raw counts; a distance-matched background with "
            "the target bin excluded; zeros kept; no covariates; a single pixel; averaging the "
            "per-replicate log ratios). A different-but-correct recipe was NOT forced through my "
            "recompute, so I did not audit it.",
            unsupported_contract=unsupported,
            unsupported_analysis_structure=unsupported_structure,
        )
    result = recompute_hic_loop_strength(bundle, design)
    if not result.identified:
        return _f(
            S.NOT_AUDITED,
            f"I couldn't rebuild the loop-strength calculation from the contact data "
            f"({result.reason}), so the reported change was NOT audited.",
            recompute_reason=result.reason, background_pairs=result.background_pairs,
            distance_bp=result.distance_bp, sample_strengths=list(result.sample_strengths),
        )
    report = reported if reported is not None else getattr(bundle, "reported_results", None)
    reported_delta, report_reason, matching_rows = _bind_reported_delta(report, design)
    if report_reason:
        return _f(
            S.NOT_AUDITED,
            f"I couldn't find a single clean reported loop-strength change matching this exact "
            f"genome/resolution/target/comparison ({report_reason}), so there was nothing to audit.",
            report_binding_reason=report_reason, matching_report_rows=matching_rows,
            recomputed_delta=result.recomputed_delta,
        )
    numerical_tolerance = 1e-9 * max(1.0, abs(reported_delta), abs(result.recomputed_delta))
    absolute_error = abs(reported_delta - result.recomputed_delta)
    allowed_error = float(tolerance) + numerical_tolerance
    agrees = bool(absolute_error <= allowed_error)
    metrics = {
        "reported_delta": reported_delta,
        "recomputed_delta": result.recomputed_delta,
        "absolute_error": absolute_error,
        "report_delta_tolerance": float(tolerance),
        "numerical_tolerance": numerical_tolerance,
        "within_tolerance": agrees,
        "sign_relation": "same" if np.sign(reported_delta) == np.sign(result.recomputed_delta)
        else "opposite",
        "background_pairs": result.background_pairs,
        "distance_bp": result.distance_bp,
        "condition_means": result.condition_means,
        "samples_per_condition": result.samples_per_condition,
        "sample_strengths": list(result.sample_strengths),
        "contacts_digest": result.contacts_digest,
        "bins_digest": result.bins_digest,
    }
    entitled = (design.confirmed_by_human
                and confidence_high(design, "hic_loop_strength")
                and confidence_high(design, "replicate_unit"))
    if agrees:
        if not entitled:
            return _f(S.NEEDS_EVIDENCE, "good sign: my independent recomputation of the loop-strength "
                      "change matches your reported value — but the recipe or the replicate setup "
                      "isn't confirmed yet, so I can't call it a clean pass. Confirm the design to "
                      "upgrade this to a pass.", coverage=S.NOT_RUN, **metrics)
        return _f(S.PASS, "your reported loop-strength change matches my independent recomputation of "
                  "it (using the confirmed recipe), within the allowed tolerance.", **metrics)
    if not entitled:
        return _f(S.NEEDS_EVIDENCE, "your reported loop-strength change and my independent "
                  "recomputation disagree — but the recipe or the replicate setup isn't confirmed "
                  "yet, so I won't hard-block. Confirm the design (sc-referee confirm) to turn a "
                  "genuine mismatch into a blocking verdict.", coverage=S.NOT_RUN, **metrics)
    return _f(S.BLOCKER, "your reported loop-strength change does not conform to the confirmed "
              "recipe: my independent recomputation of the exact same recipe gives a different "
              "number, beyond the allowed tolerance. The mismatch is real, but a single disagreeing "
              "number can't tell you which step caused it — re-check the calculation against the "
              "declared recipe.", **metrics)


class HiCLoopStrengthCheck:
    id = CHECK_ID
    analysis_types = ("hic_loop_strength",)
    audit_dimensions = ("inclusion_set", "scale", "weighting")
    proof_basis = "independent recompute"
    contract_fields = (
        "condition", "reference", "test", "replicate_unit", "hic_genome_assembly",
        "hic_resolution_bp", "hic_target_bin_i", "hic_target_bin_j",
        "hic_background_view_start", "hic_background_view_end", "hic_contact_scale",
        "hic_expected_model", "hic_mask_policy", "hic_zero_policy", "hic_pseudocount",
        "hic_target_statistic", "hic_replicate_functional", "hic_report_delta_tolerance",
        "hic_report_delta_tolerance_authority",
        "model", "pairing_unit", "subset",
    )
    claim_template = (
        "reported loop-strength delta for {hic_target_bin_i}–{hic_target_bin_j} "
        "({test} − {reference})"
    )
    max_status = S.BLOCKER

    def applies_to(self, design, bundle):
        return design.analysis_type == "hic_loop_strength" and bundle is not None

    def run(self, design, bundle, reported=None):
        return evaluate_hic_loop_strength(design, bundle, reported)
