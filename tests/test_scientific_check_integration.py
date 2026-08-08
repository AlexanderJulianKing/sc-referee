from __future__ import annotations

import json
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from sc_referee.agent_protocol import load_open_questions
from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.parsers.python_ast import PARSER_ID as PYTHON_PARSER_ID
from sc_referee.parsers.python_ast import PARSER_VERSION as PYTHON_PARSER_VERSION
from sc_referee.scientific_checks import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    InspectionDocument,
    RecordRef,
    RegistryValidationError,
    ScientificCheckContractError,
    ScientificCheckRegistry,
)
from sc_referee.scientific_checks.profiles import (
    default_scientific_check_registry,
    scientific_check_release_projection,
    verify_scientific_check_release_manifest,
)
from sc_referee.scientific_checks.scope_joins import build_static_scope_join_graph

FOUNDER_CHECK = "check:founder-orientation-before-hmm-emission"
DIRECTIONAL_MEASUREMENT_ERROR_CHECK = "check:directional-measurement-error-interpretation"
TRANSITION_PATH_CHECK = "check:within-sequence-transition-path-continuity"
PULSE_CHECK = "check:full-map-ancestry-exposure"
MVMR_CHECK = "check:ld-covariance-whitening-before-robust-fit"
MVMR_INSTRUMENT_CHECK = "check:phase-split-mvmr-instrument-construction"
MVMR_ESTIMATOR_CHECK = "check:mvmr-residual-heterogeneity-estimator"
MVMR_COVARIANCE_CHECK = "check:mvmr-cross-exposure-covariance"
POSTSTRATIFIED_CALIBRATION_CHECK = "check:poststratified-misclassification-estimator"
POSTTREATMENT_MISSINGNESS_CHECK = "check:posttreatment-missingness-strategy"
SOMATIC_CLONALITY_CHECK = "check:somatic-clonality-representation"
DIRECT_STANDARDIZATION_CHECK = "check:direct-standardization-conditioning-set"
CLASSIFIER_COPY_DOSAGE_CHECK = "check:classifier-derived-copy-dosage-representation"
TECHNICAL_GROUP_CHECK = "check:recoverable-technical-group-adjustment"
CASRX_AXIS_CHECK = "check:casrx-isoform-axis-model"
PAIRED_BRIDGE_CHECK = "check:paired-bridge-location-alignment"
LOCAL_PERTURBATION_ROW_SCOPE_CHECK = "check:local-perturbation-primary-row-scope"
LOCAL_PERTURBATION_REGRESSION_CHECK = "check:local-perturbation-regression-specification"
EXPECTED_COUNT_CONSTRUCTION_CHECK = "check:expected-count-background-construction"
EXPECTED_COUNT_TARGET_HANDLING_CHECK = "check:expected-count-focal-target-handling"
CONFORMANCE_CHECK = "check:registry-conformance-token"

# ADR-0069 founder-orientation fixtures. The reviewable operand is whether an
# orientation repair sits on the dataflow path into the emission comparison,
# so every founder fixture states an arithmetic accounting or an operation,
# never a sentence claiming a repair. With 480 markers and 372 agreements the
# direct reading is 372 / 480 = 0.775 and the complement reading is
# 108 / 480 = 0.225; the accounting-only report states neither.
#
# From v2.0.1 the report plane never resolves alone, so every founder fixture
# that expects an applicable observation also carries the workflow source
# whose emission comparison the report corroborates.
FOUNDER_DIRECT_REPORT = (
    "The parental marker panel and the progeny calls were compared marker by marker: "
    "372 of the 480 markers agree.\n\n"
    "The emission model used a per-marker agreement rate of 0.775.\n"
)
FOUNDER_COMPLEMENT_REPORT = (
    "The parental marker panel as supplied and the progeny calls were compared marker "
    "by marker: 372 of the 480 markers agree.\n\n"
    "The emission model used a per-marker agreement rate of 0.225.\n"
)
FOUNDER_DEGENERATE_REPORT = (
    "The parental marker panel and the progeny calls were compared marker by marker: "
    "240 of the 480 markers agree.\n\n"
    "The emission model used a per-marker agreement rate of 0.5.\n"
)
FOUNDER_ACCOUNTING_ONLY_REPORT = (
    "The parental marker panel and the progeny calls were compared marker by marker: "
    "372 of the 480 markers agree.\n\n"
    "The selected emission log-likelihood ratio is 0.31.\n"
)
# Both stated rates reconcile with the same 480-and-372 accounting, so the
# report states an accounting without identifying an orientation. Only the
# workflow source can say which reading the emission used.
FOUNDER_TIED_REPORT = (
    "The parental marker panel and the progeny calls were compared marker by marker: "
    "372 of the 480 markers agree.\n\n"
    "The per-marker agreement rate is 0.775 and its complement is 0.225.\n"
)

_FOUNDER_WORKFLOW_HEAD = """import csv
import math
from pathlib import Path

rows = list(csv.DictReader(Path('inputs/markers.csv').open()))
"""
_FOUNDER_WORKFLOW_TAIL = """report = f'emission likelihood {likelihood}'
Path('results/report.md').write_text(report)
"""
_FOUNDER_EMISSION = (
    "likelihood = math.prod(\n"
    "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in {source}\n"
    ")\n"
)
FOUNDER_DIRECT_SOURCE = (
    _FOUNDER_WORKFLOW_HEAD + _FOUNDER_EMISSION.format(source="rows") + _FOUNDER_WORKFLOW_TAIL
)
FOUNDER_REPAIRED_SOURCE = (
    _FOUNDER_WORKFLOW_HEAD
    + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
    + _FOUNDER_EMISSION.format(source="panel")
    + _FOUNDER_WORKFLOW_TAIL
)
FOUNDER_UNREADABLE_SOURCE = (
    _FOUNDER_WORKFLOW_HEAD
    + "panel = [{**row, 'founder': recode(row['founder'])} for row in rows]\n"
    + _FOUNDER_EMISSION.format(source="panel")
    + _FOUNDER_WORKFLOW_TAIL
)
FOUNDER_CONFLICTING_SOURCE = (
    _FOUNDER_WORKFLOW_HEAD
    + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
    + "supplied = math.prod(\n"
    + "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in rows\n"
    + ")\n"
    + "repaired = math.prod(\n"
    + "    0.99 if int(row['call']) == int(row['founder']) else 0.01 for row in panel\n"
    + ")\n"
    + "report = f'{supplied} {repaired}'\n"
    + "Path('results/report.md').write_text(report)\n"
)
_COPY_WORKFLOW_HEAD = """import numpy as np
import pandas as pd
import statsmodels.api as sm
from pathlib import Path
from sklearn.linear_model import LogisticRegression, RidgeCV

frame = pd.read_csv(Path('inputs/assay.csv'))
features = frame[['marker_a', 'marker_b']]
outcome = frame['phenotype']
"""
_COPY_POSTERIOR = (
    "classifier = LogisticRegression().fit(features, frame['copy_state'])\n"
    "expected = classifier.predict_proba(features) @ np.array([0, 1, 2])\n"
)
_COPY_WORKFLOW_TAIL = (
    "fit = sm.OLS(outcome, sm.add_constant(dosage)).fit()\n"
    "Path('results/report.md').write_text(f'coefficient {fit.params[1]}')\n"
)
COPY_HARD_STATE_SOURCE = (
    _COPY_WORKFLOW_HEAD + _COPY_POSTERIOR + "dosage = expected.astype(int)\n" + _COPY_WORKFLOW_TAIL
)
COPY_POSTERIOR_SOURCE = (
    _COPY_WORKFLOW_HEAD + _COPY_POSTERIOR + "dosage = expected\n" + _COPY_WORKFLOW_TAIL
)
COPY_CALIBRATION_SOURCE = (
    _COPY_WORKFLOW_HEAD
    + "calibrator = RidgeCV().fit(features, frame['copy_index'])\n"
    + "dosage = calibrator.predict(features)\n"
    + _COPY_WORKFLOW_TAIL
)
COPY_UNREADABLE_SOURCE = (
    _COPY_WORKFLOW_HEAD
    + _COPY_POSTERIOR
    + "dosage = expected.apply(lambda value: int(value))\n"
    + _COPY_WORKFLOW_TAIL
)
COPY_CONFLICTING_SOURCE = (
    _COPY_WORKFLOW_HEAD
    + _COPY_POSTERIOR
    + "hard = expected.astype(int)\n"
    + "quantized_fit = sm.OLS(outcome, sm.add_constant(hard)).fit()\n"
    + "continuous_fit = sm.OLS(outcome, sm.add_constant(expected)).fit()\n"
    + "Path('results/report.md').write_text(\n"
    + "    f'{quantized_fit.params[1]} {continuous_fit.params[1]}'\n"
    + ")\n"
)
_SOURCE_BY_OPERAND = {
    "use_supplied_founder_alleles_directly_in_hmm_emission": FOUNDER_DIRECT_SOURCE,
    "repair_ril_founder_orientation_before_hmm_emission": FOUNDER_REPAIRED_SOURCE,
    "integer_hard_copy_state_as_numeric_dosage": COPY_HARD_STATE_SOURCE,
    "continuous_posterior_expected_copy_dosage": COPY_POSTERIOR_SOURCE,
    "direct_continuous_calibrated_copy_dosage": COPY_CALIBRATION_SOURCE,
}


def _audit(
    root: Path,
    schema_root: Path,
    *,
    report_text: str,
    analysis_text: str = "value = 1\n",
    report_path: str = "report.md",
    include_conformance: bool = False,
    registry: ScientificCheckRegistry | None = None,
) -> dict[str, Any]:
    repository = root / "repository"
    repository.mkdir(parents=True)
    report = repository / report_path
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(report_text, encoding="utf-8")
    (repository / "analysis.py").write_text(analysis_text, encoding="utf-8")
    bundle = run_audit(
        repository,
        root / "audit",
        schema_root,
        report=report_path,
        scientific_check_registry=(
            registry
            if registry is not None
            else default_scientific_check_registry(include_conformance=include_conformance)
        ),
    )
    lock = json.loads((root / "audit" / "semantic.lock.json").read_text(encoding="utf-8"))
    bundle["_scientific_check_registry"] = lock["scientific_check_registry"]
    return bundle


def _check_questions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in bundle["material_questions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
    ]


def _check_assertions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in bundle["semantic_assertions"]
        if item.get("extensions", {}).get("x-scientific-check-id")
    ]


def _module(bundle: dict[str, Any], check_id: str) -> dict[str, Any]:
    return next(
        item
        for item in bundle["_scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == check_id
    )


def _inspection_context(*, report_parser_version: str = "0.2.0") -> FrozenInspectionContext:
    report = FOUNDER_DIRECT_REPORT.encode("utf-8")
    # The founder observation is dataflow-led from v2.0.1, so the context
    # carries the workflow whose emission comparison the report corroborates.
    analysis = FOUNDER_DIRECT_SOURCE.encode("utf-8")
    surface_ref = RecordRef("publication_surface", "publication-surface:test")
    artifact_ref = RecordRef("artifact", "artifact:test-report")
    identity_ref = RecordRef("asset_identity", "asset-identity:test-report")
    file_ref = RecordRef("file_record", "file:test-report")
    parser_ref = RecordRef("parser_result", "parser-result:test-report")
    analysis_file_ref = RecordRef("file_record", "file:test-analysis")
    analysis_parser_ref = RecordRef("parser_result", "parser-result:test-analysis")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:test")
    parser = canonical_json(
        {
            "parser_id": "parser:markdown-inventory",
            "parser_version": report_parser_version,
            "state": "parsed",
        }
    ).encode("utf-8")
    analysis_parser = canonical_json(
        {
            "parser_id": PYTHON_PARSER_ID,
            "parser_version": PYTHON_PARSER_VERSION,
            "state": "parsed",
        }
    ).encode("utf-8")
    records = (
        (
            surface_ref,
            {
                "publication_surface_id": surface_ref.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact_ref.to_dict()]},
            },
        ),
        (
            artifact_ref,
            {
                "artifact_id": artifact_ref.record_id,
                "kind": "report",
                "path": "report.md",
                "asset_identity_ref": identity_ref.to_dict(),
            },
        ),
        (
            identity_ref,
            {
                "asset_identity_id": identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": artifact_ref.to_dict(),
                "identity_evidence": {
                    "kind": "full_digest",
                    "digest": sha256_digest(report),
                },
            },
        ),
        (snapshot_ref, {"snapshot_id": snapshot_ref.record_id}),
        (file_ref, {"file_record_id": file_ref.record_id}),
        (parser_ref, {"parser_result_id": parser_ref.record_id}),
        (analysis_file_ref, {"file_record_id": analysis_file_ref.record_id}),
        (analysis_parser_ref, {"parser_result_id": analysis_parser_ref.record_id}),
    )
    context = FrozenInspectionContext(
        snapshot_digest=sha256_digest("snapshot"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(
            InspectionDocument(
                path="report.md",
                file_ref=file_ref,
                content=report,
                content_digest=sha256_digest(report),
                media_type="text/markdown",
                parser_result_ref=parser_ref,
                parser_result_payload=parser,
                parser_result_digest=sha256_digest(parser),
            ),
            InspectionDocument(
                path="analysis.py",
                file_ref=analysis_file_ref,
                content=analysis,
                content_digest=sha256_digest(analysis),
                media_type="text/x-python",
                parser_result_ref=analysis_parser_ref,
                parser_result_payload=analysis_parser,
                parser_result_digest=sha256_digest(analysis_parser),
            ),
        ),
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in records),
    )
    return replace(
        context,
        scope_join_graph=build_static_scope_join_graph(
            snapshot_digest=context.snapshot_digest,
            snapshot_ref=snapshot_ref,
            selected_surface_ref=surface_ref,
            selected_artifact_ref=artifact_ref,
            documents=context.documents,
            base_records=context.base_records,
        ),
    )


@pytest.mark.parametrize(
    ("report_text", "check_id", "operand"),
    [
        (
            FOUNDER_DIRECT_REPORT,
            FOUNDER_CHECK,
            "use_supplied_founder_alleles_directly_in_hmm_emission",
        ),
        (
            FOUNDER_COMPLEMENT_REPORT,
            FOUNDER_CHECK,
            "repair_ril_founder_orientation_before_hmm_emission",
        ),
        (
            "For each replicate separately, the expected value was the arithmetic mean of "
            "counts on the same diagonal.\n",
            EXPECTED_COUNT_CONSTRUCTION_CHECK,
            "same_stratum_arithmetic_mean_expected_count",
        ),
        (
            "The focal pixel was left out of its own expected-count background.\n",
            EXPECTED_COUNT_TARGET_HANDLING_CHECK,
            "exclude_focal_target_from_expected_count_training",
        ),
        (
            "The focal observation was left out of its expected background.\n",
            EXPECTED_COUNT_TARGET_HANDLING_CHECK,
            "exclude_focal_target_from_expected_count_training",
        ),
        (
            "The supplied average of the two directional measurement-error rates cannot identify "
            "the rates separately. The primary observation model uses the symmetric "
            "interpretation: both directions equal the supplied average.\n",
            DIRECTIONAL_MEASUREMENT_ERROR_CHECK,
            "reported_average_as_symmetric_bidirectional_error_rate",
        ),
        (
            "Only the average of the two directional allele-miscall rates is available. The read "
            "likelihood therefore requires the identifying assumption of symmetric errors.\n",
            DIRECTIONAL_MEASUREMENT_ERROR_CHECK,
            "reported_average_as_symmetric_bidirectional_error_rate",
        ),
        (
            "The reported average of the two directional measurement-error rates was decomposed "
            "into direction-specific error rates using the independently supplied error floor "
            "before constructing the observation model.\n",
            DIRECTIONAL_MEASUREMENT_ERROR_CHECK,
            "direction_specific_error_rates_from_average_and_directional_constraint",
        ),
        (
            "The reported read error is an average of directional miscall rates, not a "
            "symmetric rate. Given the stated low instrument-error direction, I computed the "
            "complementary direction and evaluated both possible assignments.\n",
            DIRECTIONAL_MEASUREMENT_ERROR_CHECK,
            "direction_specific_error_rates_from_average_and_directional_constraint",
        ),
        (
            "Under a single-pulse, two-state ancestry process, the timing estimate was "
            "t = N_switch / ((1-m)L_A + mL_B).\n",
            PULSE_CHECK,
            "high_confidence_called_tract_exposure_only",
        ),
        (
            "Transition exposure used the complete chromosome-map length, so pulse timing used "
            "t = N_switch / (2 m (1-m) L_map).\n",
            PULSE_CHECK,
            "full_chromosome_map_exposure",
        ),
        (
            "The map file is used to validate chromosome membership and bounds; unrepresented "
            "map length is not silently treated as either ancestry and is not time-model "
            "exposure.\n",
            PULSE_CHECK,
            "high_confidence_called_tract_exposure_only",
        ),
        (
            "A transition is counted only at an exactly touching callable A/B boundary. "
            "Masked or uncalled intervals terminate the path.\n",
            TRANSITION_PATH_CHECK,
            "terminate_path_at_unobserved_or_filtered_intervals",
        ),
        (
            "A transition is counted only at an exactly touching callable A/B boundary. Gaps and "
            "chromosome boundaries terminate a callable block; they contribute neither a "
            "transition nor exposure connecting their two sides.\n",
            TRANSITION_PATH_CHECK,
            "terminate_path_at_unobserved_or_filtered_intervals",
        ),
        (
            "A transition is counted between successive retained callable tracts within a "
            "chromosome, including across intervening masked or uncalled intervals; chromosome "
            "ends remain path boundaries.\n",
            TRANSITION_PATH_CHECK,
            "preserve_within_sequence_path_across_unobserved_intervals",
        ),
        (
            "We used a Tukey biweight M-estimator on Cholesky-whitened residual "
            "innovations; this preserves the LD covariance.\n",
            MVMR_CHECK,
            "ld_covariance_cholesky_whitening_before_robust_fit",
        ),
        (
            "The robust M-estimator used unwhitened residual innovations; LD covariance "
            "was ignored.\n",
            MVMR_CHECK,
            "diagonal_or_unwhitened_robust_fit",
        ),
        (
            "# Phase-split MVMR\n\nUnion of phase-1 LD-conditional joint-effect signals at "
            "two-sided p<5e-8; phase-2 joint exposure coefficients and matching joint disease "
            "coefficients.\n",
            MVMR_INSTRUMENT_CHECK,
            "phase1_ld_conditional_signal_union_with_phase2_joint_coefficients",
        ),
        (
            "# Phase-split MVMR\n\nUnion of phase-1 marginal-association signals at p<5e-8; "
            "phase-2 marginal exposure coefficients and marginal disease coefficients.\n",
            MVMR_INSTRUMENT_CHECK,
            "phase1_marginal_signal_union_with_phase2_marginal_coefficients",
        ),
        (
            "# MVMR analysis\n\n## Primary estimator\n\nZero-intercept generalized least "
            "squares with the full supplied LD-derived disease covariance.\n",
            MVMR_ESTIMATOR_CHECK,
            "zero_intercept_generalized_ivw_or_gls",
        ),
        (
            "We directly standardized completed-test call distributions over the target-population "
            "cells. We then jointly deconvolved the standardized distributions with the matched "
            "control matrices.\n",
            POSTSTRATIFIED_CALIBRATION_CHECK,
            "aggregate_observed_distribution_then_joint_calibration",
        ),
        (
            "Within each target-population post-stratum, we used nonnegative-constrained joint "
            "calibration of the mutually exclusive class probabilities, then standardized the "
            "calibrated cell estimates with the roster weights.\n",
            POSTSTRATIFIED_CALIBRATION_CHECK,
            "constrained_joint_calibration_within_each_poststratum_then_standardize",
        ),
        (
            "The assessed-case outcome model used treatment and observed week-8 toxicity. Missing "
            "week-16 outcomes were imputed. Toxicity was integrated over its treatment-specific "
            "distribution.\n",
            POSTTREATMENT_MISSINGNESS_CHECK,
            "sequential_outcome_imputation_conditioning_on_posttreatment_endpoint",
        ),
        (
            "The longitudinal procedure modeled visit assessment from exposure, adverse event, "
            "and baseline variables; modeled the later outcome among assessed participants from "
            "exposure, adverse event, and baseline variables; and integrated the adverse event "
            "under each exposure before standardizing over the cohort.\n",
            POSTTREATMENT_MISSINGNESS_CHECK,
            "sequential_outcome_imputation_conditioning_on_posttreatment_endpoint",
        ),
        (
            "The normalized IPCW assessment model excludes observed week-8 toxicity because it "
            "occurs after treatment.\n",
            POSTTREATMENT_MISSINGNESS_CHECK,
            "assessment_weighting_excluding_posttreatment_endpoint_from_missingness_model",
        ),
        (
            "For the primary missing-outcome strategy, observed week-4 adverse event was "
            "deliberately excluded from every assessment-model predictor set because it is "
            "post-treatment. The inverse-assessment residual correction transported observed "
            "outcomes to the full target population.\n",
            POSTTREATMENT_MISSINGNESS_CHECK,
            "assessment_weighting_excluding_posttreatment_endpoint_from_missingness_model",
        ),
        (
            "Target membership for the somatic structural variant used local total copy number "
            "below 4 as the eligibility ceiling.\n",
            SOMATIC_CLONALITY_CHECK,
            "direct_local_copy_number_ceiling_for_target_eligibility",
        ),
        (
            "Target eligibility used all of the following molecular gate criteria: variant-"
            "molecule fraction at least 0.12 and local total copy below 4, together with mapping "
            "and phase support.\n",
            SOMATIC_CLONALITY_CHECK,
            "direct_local_copy_number_ceiling_for_target_eligibility",
        ),
        (
            "Target membership for the somatic structural variant used a purity/copy-adjusted "
            "single-copy CCF window from 0.68 through 1.25.\n",
            SOMATIC_CLONALITY_CHECK,
            "purity_copy_adjusted_clonal_fraction_window_for_target_eligibility",
        ),
        (
            "The prespecified primary-target eligibility rule requires a purity-and-copy-adjusted "
            "cancer-cell fraction between 0.70 and 1.20.\n",
            SOMATIC_CLONALITY_CHECK,
            "purity_copy_adjusted_clonal_fraction_window_for_target_eligibility",
        ),
        (
            "The primary target is restricted to baseline records. The evaluator-frozen "
            "`reference_target` then requires a purity/copy-adjusted single-copy CCF from 0.68 "
            "through 1.25.\n",
            SOMATIC_CLONALITY_CHECK,
            "purity_copy_adjusted_clonal_fraction_window_for_target_eligibility",
        ),
        (
            "We directly standardized completed-test call distributions over family-history tier "
            "x intake site x collection wave within each ancestry, using the full-roster cell "
            "proportions.\n",
            DIRECT_STANDARDIZATION_CHECK,
            "include_named_availability_variables_in_direct_standardization_cells",
        ),
        (
            "Completed-test call distributions were directly standardized over family-history "
            "tier x intake site x collection wave within each ancestry, using full-roster cell "
            "counts.\n",
            DIRECT_STANDARDIZATION_CHECK,
            "include_named_availability_variables_in_direct_standardization_cells",
        ),
        (
            "Completed partners were analyzed within ancestry by family-history tier and "
            "standardized to the corresponding counts in all 500 roster rows. Site and wave were "
            "treated as testing-selection variables, not biological prevalence predictors.\n",
            DIRECT_STANDARDIZATION_CHECK,
            "substantive_risk_strata_only_with_availability_variables_diagnostic",
        ),
        (
            "The association model used the copy dosage as its quantitative exposure; the "
            "estimated coefficient was 0.42.\n",
            CLASSIFIER_COPY_DOSAGE_CHECK,
            "integer_hard_copy_state_as_numeric_dosage",
        ),
        (
            "The association model reported a copy-dosage coefficient of 0.31 for the full "
            "cohort.\n",
            CLASSIFIER_COPY_DOSAGE_CHECK,
            "continuous_posterior_expected_copy_dosage",
        ),
        (
            "The calibrated copy dosage entered the association model, whose coefficient was "
            "0.27.\n",
            CLASSIFIER_COPY_DOSAGE_CHECK,
            "direct_continuous_calibrated_copy_dosage",
        ),
        (
            "The primary association reconstructed a donor-level technical group from mean "
            "contamination estimates and included the recovered technical group as a categorical "
            "covariate.\n",
            TECHNICAL_GROUP_CHECK,
            "include_recovered_technical_group_covariate",
        ),
        (
            "Sample-level contamination fractions separated into two non-overlapping ranges. "
            "We reconstructed that sample-level technical group and included it as a categorical "
            "covariate in the primary association model.\n",
            TECHNICAL_GROUP_CHECK,
            "include_recovered_technical_group_covariate",
        ),
        (
            "Donor HBB-derived soup fractions separated into non-overlapping low and high ranges "
            "around 0.18. In this evaluator-owned one-change ablation, I reconstructed that "
            "donor-level technical group and included it as a categorical covariate in the "
            "primary model. This is an observed-data contamination proxy, not authenticated "
            "batch metadata.\n",
            TECHNICAL_GROUP_CHECK,
            "include_recovered_technical_group_covariate",
        ),
        (
            "No donor-specific ambient group or technical group is directly observed. None is "
            "reconstructed. Consequently, no ambient-group or technical-group covariate is "
            "included.\n",
            TECHNICAL_GROUP_CHECK,
            "omit_unobserved_or_unlinked_technical_group_covariate",
        ),
        (
            "An assay-control feature was treated as an ambient-only negative-control proxy. "
            "The cell estimator allows technical contamination to vary by observation.\n\n"
            "By subject, the retained measurements were aggregated for the outcome. The primary "
            "association model was mean = exposure * exp(intercept + treatment + age).\n",
            TECHNICAL_GROUP_CHECK,
            "omit_unobserved_or_unlinked_technical_group_covariate",
        ),
        (
            "For every CasRx guide, the effective dominant-transcript axis was overlap times "
            "knockdown efficiency. The non-dominant axis was one minus overlap times knockdown "
            "efficiency. A simultaneous two-axis fit used the dominant-axis coefficient as the "
            "transcript-specific effect.\n",
            CASRX_AXIS_CHECK,
            "simultaneous_dominant_and_nondominant_effective_knockdown_axes",
        ),
        (
            "The CasRx follow-up supplied transcript-specific measurements.\n\n"
            "I retained four guides with at least 0.90 dominant-isoform overlap. A "
            "through-origin regression fit growth effect on knockdown efficiency as one axis.\n",
            CASRX_AXIS_CHECK,
            "high_dominant_overlap_subset_single_efficiency_axis",
        ),
        (
            "Paired bridge measurements estimated plate-specific location offsets. Each "
            "follow-up-minus-primary offset was subtracted from the follow-up effects before the "
            "effect model. A global multiplicative scale was also fitted.\n",
            PAIRED_BRIDGE_CHECK,
            "group_specific_paired_bridge_location_offsets_before_followup_fit",
        ),
        (
            "The independent single-guide follow-up was not substituted for the pooled endpoint. "
            "Its correlation with the pooled guide effects was 0.986, supporting the guide "
            "ranking.\n",
            PAIRED_BRIDGE_CHECK,
            "no_group_specific_paired_bridge_location_offsets_before_followup_fit",
        ),
        (
            "The single-guide follow-up contained one NTC on each plate. Those controls were "
            "-0.0338 on one plate and were subtracted from the follow-up measurements. A "
            "through-origin pooled/follow-up scale was then applied.\n",
            PAIRED_BRIDGE_CHECK,
            "no_group_specific_paired_bridge_location_offsets_before_followup_fit",
        ),
    ],
)
def test_exact_method_profiles_route_through_one_general_audit_interface(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    check_id: str,
    operand: object,
) -> None:
    # The founder and copy-dosage rows carry their workflow source: both
    # checks resolve from operations, and their report planes only corroborate.
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=report_text,
        analysis_text=_SOURCE_BY_OPERAND.get(str(operand), "value = 1\n"),
    )

    questions = _check_questions(bundle)
    assertions = _check_assertions(bundle)

    assert bundle["findings"] == []
    assert len(questions) == 1
    assert questions[0]["affected_claim_ids"] == []
    assert questions[0]["extensions"]["x-scientific-check-id"] == check_id
    assert len(assertions) == 1
    assert assertions[0]["object"] == operand
    assert assertions[0]["finding_eligibility"] == "ineligible"
    assert _module(bundle, check_id)["state"] == "applicable"


def test_expected_count_construction_and_target_handling_are_independent_questions(
    tmp_path: Path,
    schema_root: Path,
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "# Method\n\nExpected is the per-replicate arithmetic mean of all 15 "
            "intrachromosomal 20 kb pixels at `dist_bin = 9`, including the focal pixel.\n"
        ),
    )

    questions = _check_questions(bundle)
    assertions = _check_assertions(bundle)
    expected_checks = {
        EXPECTED_COUNT_CONSTRUCTION_CHECK,
        EXPECTED_COUNT_TARGET_HANDLING_CHECK,
    }
    assert bundle["findings"] == []
    assert {item["extensions"]["x-scientific-check-id"] for item in questions} == (expected_checks)
    assert {item["extensions"]["x-scientific-check-id"] for item in assertions} == (expected_checks)
    assert {item["object"] for item in assertions} == {
        "same_stratum_arithmetic_mean_expected_count",
        "include_focal_target_in_expected_count_background",
    }


def test_expected_count_model_prediction_and_target_holdout_are_independent_questions(
    tmp_path: Path,
    schema_root: Path,
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "The target pair was excluded from expected-count training in every replicate. "
            "We fitted a negative-binomial GLM and predicted the held-out target expectation "
            "separately for every replicate.\n"
        ),
    )

    questions = _check_questions(bundle)
    assertions = _check_assertions(bundle)
    expected_checks = {
        EXPECTED_COUNT_CONSTRUCTION_CHECK,
        EXPECTED_COUNT_TARGET_HANDLING_CHECK,
    }
    assert bundle["findings"] == []
    assert {item["extensions"]["x-scientific-check-id"] for item in questions} == (expected_checks)
    assert {item["extensions"]["x-scientific-check-id"] for item in assertions} == (expected_checks)
    assert {item["object"] for item in assertions} == {
        "negative_binomial_glm_predicted_expected_count",
        "exclude_focal_target_from_expected_count_training",
    }


@pytest.mark.parametrize(
    ("report_text", "check_id", "expected_state"),
    [
        (
            "A same-distance expected count was considered, but the primary background was not "
            "stated.\n",
            EXPECTED_COUNT_CONSTRUCTION_CHECK,
            "unsupported",
        ),
        (
            "The focal pixel was plotted next to the expected count for quality control.\n",
            EXPECTED_COUNT_TARGET_HANDLING_CHECK,
            "unsupported",
        ),
        (
            "Expected is the per-replicate arithmetic mean of all 15 intrachromosomal 20 kb "
            "pixels at dist_bin = 9, including the focal pixel.\n\nWe fitted a "
            "negative-binomial GLM, and the masked count model predicted the held-out target "
            "expectation separately for every replicate.\n",
            EXPECTED_COUNT_CONSTRUCTION_CHECK,
            "ambiguous",
        ),
    ],
)
def test_expected_count_checks_fail_closed_on_partial_or_conflicting_wording(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    check_id: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert all(
        item["extensions"]["x-scientific-check-id"] != check_id for item in _check_questions(bundle)
    )
    assert all(
        item["extensions"]["x-scientific-check-id"] != check_id
        for item in _check_assertions(bundle)
    )
    assert _module(bundle, check_id)["state"] == expected_state


def test_mvmr_robust_estimator_and_ld_treatment_remain_atomic_questions(
    tmp_path: Path,
    schema_root: Path,
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "# MVMR analysis\n\n## Primary estimator\n\nZero-intercept Tukey-biweight "
            "M-regression (c=4.685) on lower-Cholesky-whitened disease residual innovations.\n"
        ),
    )

    questions = _check_questions(bundle)
    assertions = _check_assertions(bundle)
    expected_checks = {MVMR_ESTIMATOR_CHECK, MVMR_CHECK}
    assert bundle["findings"] == []
    assert {item["extensions"]["x-scientific-check-id"] for item in questions} == expected_checks
    assert {item["extensions"]["x-scientific-check-id"] for item in assertions} == expected_checks
    assert {item["object"] for item in assertions} == {
        "redescending_robust_m_estimator_on_ld_whitened_innovations",
        "ld_covariance_cholesky_whitening_before_robust_fit",
    }


@pytest.mark.parametrize(
    ("instrument", "estimator", "expected_question_count"),
    [
        ("conditional", "gls", 2),
        ("marginal", "gls", 2),
        ("conditional", "robust", 3),
        ("marginal", "robust", 3),
    ],
)
def test_mvmr_instrument_and_heterogeneity_four_cell_independence(
    tmp_path: Path,
    schema_root: Path,
    instrument: str,
    estimator: str,
    expected_question_count: int,
) -> None:
    instrument_paragraph = (
        "Union of phase-1 LD-conditional joint-effect signals at two-sided p<5e-8; phase-2 "
        "joint exposure coefficients and matching joint disease coefficients.\n"
        if instrument == "conditional"
        else (
            "Union of phase-1 marginal-association signals at p<5e-8; phase-2 marginal "
            "exposure coefficients and marginal disease coefficients.\n"
        )
    )
    estimator_paragraph = (
        "Zero-intercept generalized least squares with the full supplied LD-derived disease "
        "covariance.\n"
        if estimator == "gls"
        else (
            "Zero-intercept Tukey-biweight M-regression (c=4.685) on lower-Cholesky-whitened "
            "disease residual innovations.\n"
        )
    )
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            f"# Phase-split MVMR\n\n{instrument_paragraph}\n"
            f"## Primary estimator\n\n{estimator_paragraph}"
        ),
    )

    questions = _check_questions(bundle)
    assertions = _check_assertions(bundle)
    expected_checks = {MVMR_INSTRUMENT_CHECK, MVMR_ESTIMATOR_CHECK}
    if estimator == "robust":
        expected_checks.add(MVMR_CHECK)
    assert bundle["findings"] == []
    assert len(questions) == expected_question_count
    assert {item["extensions"]["x-scientific-check-id"] for item in questions} == expected_checks
    assert {item["extensions"]["x-scientific-check-id"] for item in assertions} == expected_checks


@pytest.mark.parametrize(
    ("report_text", "check_id", "expected_state"),
    [
        (
            "# Phase-split MVMR\n\nUnion of phase-1 LD-conditional joint-effect signals; "
            "phase-2 joint exposure coefficients and matching joint disease coefficients.\n\n"
            "Union of phase-1 marginal-association signals; phase-2 marginal exposure "
            "coefficients and marginal disease coefficients.\n",
            MVMR_INSTRUMENT_CHECK,
            "ambiguous",
        ),
        (
            "# MVMR analysis\n\n## Sensitivity analysis\n\nA zero-intercept Tukey-biweight "
            "M-regression on lower-Cholesky-whitened disease residual innovations was a "
            "sensitivity; the primary estimator was not stated.\n",
            MVMR_ESTIMATOR_CHECK,
            "unsupported",
        ),
        (
            "Phase-1 marginal associations were plotted for one exposure; no multivariable "
            "instrument set or phase-2 estimator was defined.\n",
            MVMR_INSTRUMENT_CHECK,
            "not_applicable",
        ),
    ],
)
def test_mvmr_new_profiles_preserve_ambiguity_and_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    check_id: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert all(
        item["extensions"]["x-scientific-check-id"] != check_id for item in _check_questions(bundle)
    )
    assert all(
        item["extensions"]["x-scientific-check-id"] != check_id
        for item in _check_assertions(bundle)
    )
    assert _module(bundle, check_id)["state"] == expected_state


def test_copy_dosage_evidence_cites_the_quantizing_operation_and_the_report_accounting(
    tmp_path: Path,
    schema_root: Path,
) -> None:
    """v2.0.0 evidence is the operation and the accounting it corroborates.

    The retired v1.2.0 rule cited a linked span of report prose. The rebuilt
    check cites the workflow step that put the exposure on the integers, and,
    when the report tabulates the per-state counts, those tokens too.
    """

    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "# Results\n\nAn unrelated descriptive result was reported first.\n\n"
            "Copy state was 0 in 120 participants, 1 in 260, and 2 in 120 of the 500 "
            "genotyped participants; the mean dosage was 1.00.\n\n"
            "# Limitations\n\nAn unrelated limitation followed the method.\n"
        ),
        analysis_text=COPY_HARD_STATE_SOURCE,
    )

    assertion = next(
        item
        for item in _check_assertions(bundle)
        if item["extensions"]["x-scientific-check-id"] == CLASSIFIER_COPY_DOSAGE_CHECK
    )
    assert assertion["object"] == "integer_hard_copy_state_as_numeric_dosage"
    quoted = [item["quoted_text"] for item in assertion["source_refs"]]
    assert any("astype(int)" in item for item in quoted)
    assert not any("unrelated descriptive result" in item for item in quoted)
    assert not any("unrelated limitation" in item for item in quoted)


@pytest.mark.parametrize(
    ("report_text", "operand"),
    [
        (
            "# Analysis\n\n"
            "```{r diagnostics}\n"
            "strength_mvmr(r_input = formatted, gencov = 0)\n"
            "```\n",
            "zero_cross_exposure_covariance",
        ),
        (
            "---\ntitle: Analysis\n---\n\n"
            "```{r covariance}\n"
            "study_covariance <- MVMR::phenocov_mvmr(correlation, standard_errors)\n"
            "MVMR::pleiotropy_mvmr(r_input = formatted, gencov = study_covariance)\n"
            "```\n",
            "provided_cross_exposure_covariance",
        ),
    ],
)
def test_rmarkdown_connector_routes_mvmr_calls_through_shared_question_lifecycle(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    operand: str,
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=report_text,
        report_path="reports/scientist-selected.Rmd",
    )

    questions = _check_questions(bundle)
    assertions = _check_assertions(bundle)

    assert bundle["findings"] == []
    assert len(questions) == 1
    assert questions[0]["extensions"]["x-scientific-check-id"] == MVMR_COVARIANCE_CHECK
    assert [item["object"] for item in assertions] == [operand]
    assert assertions[0]["semantic_role"] == "observed"
    assert assertions[0]["authority_scope"] == "none"
    module = _module(bundle, MVMR_COVARIANCE_CHECK)
    assert module["state"] == "applicable"
    assert module["observations"][0]["scope_join_path"][0]["relation"] == (
        "selected_source_artifact_of_publication_surface"
    )


@pytest.mark.parametrize(
    ("report_path", "chunk"),
    [
        (
            "analysis.Rmd",
            "```{r}\nstrength_mvmr(r_input = formatted, gencov = 0)\n```\n",
        ),
        (
            "nested/methods.rmd",
            "```{R empty}\n```\n"
            "```{R diagnostics, echo = TRUE}\n"
            "MVMR::strength_mvmr ( r_input=formatted , gencov=0.0 )\n"
            "```\n",
        ),
    ],
)
def test_rmarkdown_mvmr_profile_is_invariant_to_path_chunk_label_formatting_and_namespace(
    tmp_path: Path,
    schema_root: Path,
    report_path: str,
    chunk: str,
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=chunk,
        report_path=report_path,
    )

    module = _module(bundle, MVMR_COVARIANCE_CHECK)
    assert module["state"] == "applicable"
    assert module["observations"][0]["observed_operand"] == {
        "kind": "canonical_scalar",
        "value": "zero_cross_exposure_covariance",
    }
    assert len(_check_questions(bundle)) == 1


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "```{r}\n# strength_mvmr(r_input = formatted, gencov = 0)\n```\n",
            "not_applicable",
        ),
        (
            "```{r hidden, eval=FALSE}\nstrength_mvmr(r_input = formatted, gencov = 0)\n```\n",
            "not_applicable",
        ),
        (
            "```{r}\nstrength_mvmr(r_input = formatted, gencov = choose_covariance())\n```\n",
            "unsupported",
        ),
        (
            "```{r}\nstrength_mvmr(r_input = formatted)\n```\n",
            "unsupported",
        ),
        (
            "```{r}\n"
            "diagnostic <- function() strength_mvmr(r_input = formatted, gencov = 0)\n"
            "```\n",
            "unsupported",
        ),
        (
            "```{r}\n"
            "covariance_input <- phenocov_mvmr(correlation, standard_errors)\n"
            "covariance_input <- transform(covariance_input)\n"
            "strength_mvmr(r_input = formatted, gencov = covariance_input)\n"
            "```\n",
            "unsupported",
        ),
        (
            "```{r}\n"
            "covariance_input <- snpcov_mvmr(genotypes, exposures)\n"
            "strength_mvmr(r_input = formatted, gencov = 0)\n"
            "pleiotropy_mvmr(r_input = formatted, gencov = covariance_input)\n"
            "```\n",
            "ambiguous",
        ),
    ],
)
def test_rmarkdown_mvmr_connector_fails_closed_on_inactive_dynamic_or_conflicting_calls(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=report_text,
        report_path="analysis.Rmd",
    )

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, MVMR_COVARIANCE_CHECK)["state"] == expected_state


@pytest.mark.parametrize(
    "report_text",
    [
        "Robust MVMR covariance and gencov assumptions were reviewed.\n",
        "```{r}\nother_mvmr(r_input = formatted, gencov = 0)\n```\n",
        "```r\nstrength_mvmr(r_input = formatted, gencov = 0)\n```\n",
        '```{r}\nmessage("strength_mvmr(r_input = formatted, gencov = 0)")\n```\n',
    ],
)
def test_rmarkdown_mvmr_lexical_hard_negatives_do_not_create_questions(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=report_text,
        report_path="analysis.Rmd",
    )

    assert _module(bundle, MVMR_COVARIANCE_CHECK)["state"] == "not_applicable"
    assert _check_questions(bundle) == []
    assert bundle["findings"] == []


@pytest.mark.parametrize(
    "report_text",
    [
        "A standard regression was fitted and summarized.\n",
        "Founder alleles were plotted beside a founder-origin HMM diagram.\n",
        "Founder 0/1 alleles were quality-control plotted before HMM emissions.\n",
        (
            "Eligible called A and B tract lengths were reported in a QC table; no ancestry "
            "fraction or pulse-exposure denominator was defined.\n"
        ),
        (
            "The founder-origin HMM was fitted using the supplied founder alleles. Founder "
            "alleles were reoriented before the HMM emission.\n"
        ),
        FOUNDER_DEGENERATE_REPORT,
    ],
)
def test_unrelated_lookalike_and_ambiguous_reports_do_not_create_questions(
    tmp_path: Path, schema_root: Path, report_text: str
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []


@pytest.mark.parametrize(
    ("report_text", "analysis_text", "expected_state"),
    [
        # The report reads the panel directly while the workflow complements it
        # before the comparison: the two planes disagree.
        (FOUNDER_DIRECT_REPORT, FOUNDER_REPAIRED_SOURCE, "ambiguous"),
        # The workflow's own comparisons disagree with each other.
        (FOUNDER_ACCOUNTING_ONLY_REPORT, FOUNDER_CONFLICTING_SOURCE, "ambiguous"),
        # A transform on the panel path that the bounded trace cannot read is
        # never the direct orientation by default.
        (
            "Founder alleles were plotted beside a founder-origin HMM diagram for quality "
            "control; no emission coding choice was declared.\n",
            FOUNDER_UNREADABLE_SOURCE,
            "unsupported",
        ),
        # The degenerate accounting reconciles with both orientations at once.
        (FOUNDER_DEGENERATE_REPORT, "value = 1\n", "not_applicable"),
        ("A standard regression was fitted and summarized.\n", "value = 1\n", "not_applicable"),
    ],
)
def test_founder_orientation_profile_preserves_ambiguity_and_hard_negative(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    analysis_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text, analysis_text=analysis_text)

    assert bundle["findings"] == []
    assert not [
        item
        for item in _check_questions(bundle)
        if item["extensions"].get("x-scientific-check-id") == FOUNDER_CHECK
    ]
    assert _module(bundle, FOUNDER_CHECK)["state"] == expected_state


def test_expected_count_unrelated_report_is_a_hard_negative(
    tmp_path: Path, schema_root: Path
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "Observed and expected counts were plotted for descriptive quality control; no "
            "expected-count background or focal-target handling rule was declared.\n"
        ),
    )

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, EXPECTED_COUNT_CONSTRUCTION_CHECK)["state"] == "not_applicable"
    assert _module(bundle, EXPECTED_COUNT_TARGET_HANDLING_CHECK)["state"] == "not_applicable"


@pytest.mark.parametrize(
    ("report_text", "check_id", "expected_state"),
    [
        (
            "We used a Tukey biweight M-estimator on Cholesky-whitened residual innovations.\n\n"
            "The robust M-estimator also used unwhitened residual innovations and ignored LD.\n",
            MVMR_CHECK,
            "unsupported",
        ),
        (
            "A standard regression was fitted and summarized.\n",
            MVMR_CHECK,
            "not_applicable",
        ),
        (
            "A standard regression was fitted and summarized.\n",
            MVMR_ESTIMATOR_CHECK,
            "not_applicable",
        ),
    ],
)
def test_remaining_mvmr_profiles_preserve_ambiguity_and_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    check_id: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, check_id)["state"] == expected_state


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "The supplied average of the two directional measurement-error rates cannot identify "
            "the rates separately. The primary observation model uses the symmetric "
            "interpretation: both directions equal the supplied average.\n\n"
            "The reported average of the two directional measurement-error rates was decomposed "
            "into direction-specific error rates using the independently supplied error floor "
            "before constructing the observation model.\n",
            "ambiguous",
        ),
        (
            "The two directional measurement-error rates were plotted for quality control, but "
            "the primary observation model was not stated.\n",
            "not_applicable",
        ),
        (
            "The HMM used a symmetric distance-dependent transition matrix. Measurement error "
            "was not discussed.\n",
            "not_applicable",
        ),
    ],
)
def test_directional_measurement_error_profile_preserves_ambiguity_and_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, DIRECTIONAL_MEASUREMENT_ERROR_CHECK)["state"] == expected_state


def test_directional_error_and_founder_orientation_remain_independent_questions(
    tmp_path: Path, schema_root: Path
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "The supplied average of the two directional measurement-error rates cannot identify "
            "the rates separately. The primary observation model uses the symmetric "
            "interpretation: both directions equal the supplied average.\n\n"
            + FOUNDER_COMPLEMENT_REPORT
        ),
        analysis_text=FOUNDER_REPAIRED_SOURCE,
    )

    assert bundle["findings"] == []
    assert {item["extensions"]["x-scientific-check-id"] for item in _check_questions(bundle)} == {
        DIRECTIONAL_MEASUREMENT_ERROR_CHECK,
        FOUNDER_CHECK,
    }
    assert {item["object"] for item in _check_assertions(bundle)} == {
        "reported_average_as_symmetric_bidirectional_error_rate",
        "repair_ril_founder_orientation_before_hmm_emission",
    }


def test_pulse_timing_exposure_does_not_conflate_the_ancestry_fraction_denominator(
    tmp_path: Path, schema_root: Path
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "The ancestry-fraction denominator is eligible called A length plus eligible called "
            "B length; gaps remain outside that fraction.\n\n"
            "Under a single-pulse, two-state ancestry process, transition exposure used the "
            "complete chromosome-map length, so pulse timing used "
            "t = N_switch / (2 m (1-m) L_map).\n"
        ),
    )

    questions = _check_questions(bundle)
    assertions = _check_assertions(bundle)
    assert len(questions) == 1
    assert questions[0]["extensions"]["x-scientific-check-id"] == PULSE_CHECK
    assert questions[0]["extensions"]["x-unresolved-dimensions"] == ["time_definition"]
    assert [item["object"] for item in assertions] == ["full_chromosome_map_exposure"]
    assert _module(bundle, PULSE_CHECK)["state"] == "applicable"


def test_pulse_timing_recognizes_explicit_called_path_instead_of_full_map(
    tmp_path: Path, schema_root: Path
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "Under a single-pulse model, the ancestry path was a two-state continuous-time "
            "process. I used retained called tract length only for its exposure and did not use "
            "the full genetic-map length as the denominator.\n"
        ),
    )

    assert bundle["findings"] == []
    assert [item["object"] for item in _check_assertions(bundle)] == [
        "high_confidence_called_tract_exposure_only"
    ]
    assert _module(bundle, PULSE_CHECK)["state"] == "applicable"


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "The ancestry-fraction denominator is eligible called A length plus eligible called "
            "B length. Uncalled gaps remain outside that denominator.\n",
            "not_applicable",
        ),
        (
            "Under a single-pulse, two-state ancestry process, gaps and filtered tracts did not "
            "terminate the transition path. The timing exposure was not stated.\n",
            "unsupported",
        ),
        (
            "Under a single-pulse, two-state ancestry process, timing used "
            "t = N_switch / ((1-m)L_A + mL_B).\n\n"
            "Transition exposure used the complete chromosome-map length, so pulse timing used "
            "t = N_switch / (2 m (1-m) L_map).\n",
            "ambiguous",
        ),
    ],
)
def test_pulse_timing_profile_keeps_fraction_path_and_conflicts_bounded(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, PULSE_CHECK)["state"] == expected_state


def test_transition_continuity_and_pulse_exposure_are_independent_questions(
    tmp_path: Path, schema_root: Path
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "A transition is counted only at an exactly touching callable A/B boundary. "
            "Masked or uncalled intervals terminate the path.\n\n"
            "Pulse-time transition exposure uses only retained callable A-plus-B length.\n"
        ),
    )

    assert bundle["findings"] == []
    assert {item["extensions"]["x-scientific-check-id"] for item in _check_questions(bundle)} == {
        TRANSITION_PATH_CHECK,
        PULSE_CHECK,
    }
    assert {item["object"] for item in _check_assertions(bundle)} == {
        "terminate_path_at_unobserved_or_filtered_intervals",
        "high_confidence_called_tract_exposure_only",
    }


def test_transition_path_recognizes_exact_hidden_gap_integration(
    tmp_path: Path, schema_root: Path
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "For each positive-length uncalled gap, the exact two-state transition matrix "
            "integrated over zero or more hidden switches in the path.\n"
        ),
    )

    assert bundle["findings"] == []
    assert [item["object"] for item in _check_assertions(bundle)] == [
        "preserve_within_sequence_path_across_unobserved_intervals"
    ]
    assert _module(bundle, TRANSITION_PATH_CHECK)["state"] == "applicable"


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "Transitions are counted between successive retained states within each sequence, "
            "including across intervening missing or filtered intervals; sequence ends remain "
            "path boundaries.\n\n"
            "A transition is counted only at an exactly touching retained-state boundary. "
            "Missing or filtered intervals terminate the path.\n",
            "ambiguous",
        ),
        (
            "Successive retained values were connected across missing intervals for plotting; "
            "no transition process was fitted.\n",
            "not_applicable",
        ),
        (
            "Transitions among successive retained states were summarized, and missing intervals "
            "were present, but their treatment in the transition path was not declared.\n",
            "unsupported",
        ),
    ],
)
def test_transition_path_profile_preserves_ambiguity_and_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, TRANSITION_PATH_CHECK)["state"] == expected_state


def test_fixed_linear_calibration_and_weighting_order_is_not_a_scientific_question(
    tmp_path: Path, schema_root: Path
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "Within each ancestry, we standardized observed call distributions over full-roster "
            "cells and then deconvolved the result with one fixed ancestry-specific calibration "
            "matrix. The same matrix governed every cell in that ancestry.\n"
        ),
    )

    # A fixed linear inverse commutes with weighted averaging. Step order alone therefore cannot
    # define a material incompatibility without a varying or nonlinear calibration mapping.
    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert all(
        item["check_id"] != "check:calibration-before-target-population-weighting"
        for item in bundle["_scientific_check_registry"]["evaluation"]["modules"]
    )


def test_nonnegative_cell_projection_is_the_material_noncommuting_operation() -> None:
    false_positive_rate = Fraction(1, 20)
    sensitivity = Fraction(1, 2)
    cell_rates = (Fraction(0), Fraction(1, 5))
    weights = (Fraction(1, 2), Fraction(1, 2))

    def linear_inverse(observed_rate: Fraction) -> Fraction:
        return (observed_rate - false_positive_rate) / (sensitivity - false_positive_rate)

    weighted_observed = sum(
        (weight * rate for weight, rate in zip(weights, cell_rates, strict=True)),
        start=Fraction(0),
    )
    aggregate_linear = linear_inverse(weighted_observed)
    weighted_linear = sum(
        (weight * linear_inverse(rate) for weight, rate in zip(weights, cell_rates, strict=True)),
        start=Fraction(0),
    )
    weighted_cellwise_projection = sum(
        (
            weight * max(Fraction(0), linear_inverse(rate))
            for weight, rate in zip(weights, cell_rates, strict=True)
        ),
        start=Fraction(0),
    )

    assert aggregate_linear == weighted_linear
    assert weighted_cellwise_projection != aggregate_linear


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "We directly standardized completed-test call distributions over the target-population "
            "cells. We then jointly deconvolved the standardized distributions with matched "
            "control matrices.\n\n"
            "Within each target-population post-stratum, we used nonnegative-constrained joint "
            "calibration of the mutually exclusive class probabilities, then standardized the "
            "calibrated cell estimates.\n",
            "ambiguous",
        ),
        (
            "We standardized classifier scores before plotting a multiclass calibration curve and "
            "reported a confusion matrix. No target-population prevalence was estimated.\n",
            "not_applicable",
        ),
        (
            "Observed call distributions were standardized over cells and a calibration matrix "
            "was discussed, but the estimator and constraint scope were not stated.\n",
            "not_applicable",
        ),
    ],
)
def test_poststratified_calibration_profile_preserves_ambiguity_and_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, POSTSTRATIFIED_CALIBRATION_CHECK)["state"] == expected_state


@pytest.mark.parametrize(
    ("report_text", "expected_operand"),
    [
        (
            "I directly standardized completed-test outcome rates to the full sampling frame "
            "across region, intake channel, and collection-period cells. Within each region and "
            "period group I then applied the matched control correction.\n",
            "aggregate_observed_distribution_then_joint_calibration",
        ),
        (
            "For each sampling-frame cell, I used simplex-constrained joint deconvolution of "
            "the mutually exclusive class probabilities, then standardized the calibrated "
            "cell estimates using the target weights.\n",
            "constrained_joint_calibration_within_each_poststratum_then_standardize",
        ),
    ],
)
def test_poststratified_calibration_recognizes_order_across_renamed_strata(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_operand: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    module = _module(bundle, POSTSTRATIFIED_CALIBRATION_CHECK)
    observation = next(
        item for item in module["observations"] if item["applicability"] == "applicable"
    )

    assert module["state"] == "applicable"
    assert observation["observed_operand"]["value"] == expected_operand
    assert len(_check_questions(bundle)) == 1
    assert bundle["findings"] == []


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "The assessed-case outcome model used treatment and observed week-8 toxicity. Missing "
            "week-16 outcomes were imputed. Toxicity was integrated over its treatment-specific "
            "distribution.\n\n"
            "The normalized IPCW assessment model excludes observed week-8 toxicity because it "
            "occurs after treatment.\n",
            "ambiguous",
        ),
        (
            "Week-8 toxicity and week-16 assessment rates were summarized descriptively. The "
            "analysis did not define a missing-outcome transport model.\n",
            "not_applicable",
        ),
        (
            "A baseline history of prior toxicity was included in the treatment model; outcomes "
            "were complete and no censoring weights were needed.\n",
            "not_applicable",
        ),
        (
            "In a sensitivity analysis, observed week-8 toxicity was deliberately excluded from "
            "every assessment-model predictor set because it is post-treatment. The inverse-"
            "assessment residual correction transported observed outcomes. The primary "
            "missing-outcome strategy was not stated.\n",
            "unsupported",
        ),
    ],
)
def test_posttreatment_missingness_profile_preserves_ambiguity_and_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, POSTTREATMENT_MISSINGNESS_CHECK)["state"] == expected_state


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "Target membership for the somatic structural variant used local total copy number "
            "below 4 as the eligibility ceiling.\n\n"
            "Target membership for the somatic structural variant used a purity/copy-adjusted "
            "single-copy CCF window from 0.68 through 1.25.\n",
            "ambiguous",
        ),
        (
            "Local total copy number and somatic structural-variant calls were plotted for quality "
            "control, but no target population was defined.\n",
            "unsupported",
        ),
        (
            "A purity/copy-adjusted CCF was reported descriptively for each variant; it did not "
            "define target eligibility or membership.\n",
            "unsupported",
        ),
        (
            "The primary target used promoter-facing breakpoints. A sensitivity eligibility rule "
            "required a purity/copy-adjusted single-copy CCF range, but the primary eligibility "
            "rule did not.\n",
            "not_applicable",
        ),
    ],
)
def test_somatic_clonality_profile_preserves_ambiguity_and_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, SOMATIC_CLONALITY_CHECK)["state"] == expected_state


@pytest.mark.parametrize(
    ("target_paragraph", "missingness_paragraph", "expected_operands"),
    [
        (
            "Target membership for the somatic structural variant was determined using local "
            "total copy number below 4 as the eligibility ceiling.\n",
            "The assessed-case outcome model used treatment and observed week-8 toxicity. Missing "
            "week-16 outcomes were imputed. Toxicity was integrated over its treatment-specific "
            "distribution.\n",
            {
                "direct_local_copy_number_ceiling_for_target_eligibility",
                "sequential_outcome_imputation_conditioning_on_posttreatment_endpoint",
            },
        ),
        (
            "Target membership for the somatic structural variant was determined using a "
            "purity/copy-adjusted single-copy CCF window from 0.68 through 1.25.\n",
            "The assessed-case outcome model used treatment and observed week-8 toxicity. Missing "
            "week-16 outcomes were imputed. Toxicity was integrated over its treatment-specific "
            "distribution.\n",
            {
                "purity_copy_adjusted_clonal_fraction_window_for_target_eligibility",
                "sequential_outcome_imputation_conditioning_on_posttreatment_endpoint",
            },
        ),
        (
            "Target membership for the somatic structural variant was determined using local "
            "total copy number below 4 as the eligibility ceiling.\n",
            "The normalized IPCW assessment model excludes observed week-8 toxicity because it "
            "occurs after treatment.\n",
            {
                "direct_local_copy_number_ceiling_for_target_eligibility",
                "assessment_weighting_excluding_posttreatment_endpoint_from_missingness_model",
            },
        ),
        (
            "Target membership for the somatic structural variant was determined using a "
            "purity/copy-adjusted single-copy CCF window from 0.68 through 1.25.\n",
            "The normalized IPCW assessment model excludes observed week-8 toxicity because it "
            "occurs after treatment.\n",
            {
                "purity_copy_adjusted_clonal_fraction_window_for_target_eligibility",
                "assessment_weighting_excluding_posttreatment_endpoint_from_missingness_model",
            },
        ),
    ],
)
def test_compound_target_and_missingness_choices_remain_independent(
    tmp_path: Path,
    schema_root: Path,
    target_paragraph: str,
    missingness_paragraph: str,
    expected_operands: set[str],
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=f"{target_paragraph}\n{missingness_paragraph}",
    )

    questions = _check_questions(bundle)
    assertions = _check_assertions(bundle)
    assert bundle["findings"] == []
    assert len(questions) == 2
    assert {item["object"] for item in assertions} == expected_operands


@pytest.mark.parametrize(
    ("use_frozen_target", "exclude_posttreatment_endpoint", "expected_checks"),
    [
        (False, False, set()),
        (True, False, {SOMATIC_CLONALITY_CHECK}),
        (False, True, {POSTTREATMENT_MISSINGNESS_CHECK}),
        (True, True, {SOMATIC_CLONALITY_CHECK, POSTTREATMENT_MISSINGNESS_CHECK}),
    ],
)
def test_fresh_txr1_four_cell_recurrence_preserves_independent_connectivity(
    tmp_path: Path,
    schema_root: Path,
    use_frozen_target: bool,
    exclude_posttreatment_endpoint: bool,
    expected_checks: set[str],
) -> None:
    target_paragraph = (
        "The evaluator-frozen `reference_target` then requires a purity/copy-adjusted "
        "single-copy CCF from 0.68 through 1.25.\n"
        if use_frozen_target
        else (
            "The primary target requires a promoter-facing P2T breakpoint, high mapping "
            "quality, TXR1 expression, and linked ASE; no adjusted CCF gate was stated.\n"
        )
    )
    missingness_paragraph = (
        "This evaluator-owned ablation uses baseline covariates within therapy. Observed week-8 "
        "toxicity is deliberately excluded from every assessment-model predictor set because "
        "it is post-treatment. The inverse-assessment residual correction transports observed "
        "benefit to all target patients.\n"
        if exclude_posttreatment_endpoint
        else (
            "Observed week-8 toxicity is used in the assessment model because it occurs after "
            "treatment and before week 16. The inverse-assessment residual correction transports "
            "observed benefit to all target patients.\n"
        )
    )

    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=f"{target_paragraph}\n{missingness_paragraph}",
    )

    questions = _check_questions(bundle)
    assertions = _check_assertions(bundle)
    assert bundle["findings"] == []
    assert {item["extensions"]["x-scientific-check-id"] for item in questions} == expected_checks
    assert {item["extensions"]["x-scientific-check-id"] for item in assertions} == expected_checks


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "We directly standardized completed-test call distributions over family-history tier "
            "x intake site x collection wave within each ancestry, using the full-roster cell "
            "proportions.\n\n"
            "Completed partners were analyzed within ancestry by family-history tier and "
            "standardized to the corresponding counts in all roster rows. Site and wave were "
            "treated as testing-selection variables, not biological prevalence predictors.\n",
            "ambiguous",
        ),
        (
            "All target-roster rows were measured, so no completed-row standardization was "
            "needed. Site and collection wave were summarized descriptively.\n",
            "not_applicable",
        ),
        (
            "Site and collection wave defined assay-calibration groups and were shown in QC "
            "plots. No completed-row target standardization was reported.\n",
            "not_applicable",
        ),
        (
            "Site and wave were ordinary covariates in the outcome regression. The analysis did "
            "not standardize completed rows to a full roster.\n",
            "not_applicable",
        ),
        (
            "Testing was nonrandom, and completed rows were standardized to the full roster. The "
            "conditioning variables were not stated.\n",
            "not_applicable",
        ),
        (
            "An inverse-probability model used site and collection wave to weight completed rows "
            "to the target population; no direct standardization cells were defined.\n",
            "unsupported",
        ),
        (
            "Completed partners were analyzed within ancestry by family-history tier and "
            "standardized to full-roster rows. Site was included in some cells, while wave was "
            "diagnostic-only.\n",
            "unsupported",
        ),
    ],
)
def test_direct_standardization_profile_preserves_ambiguity_and_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, DIRECT_STANDARDIZATION_CHECK)["state"] == expected_state


@pytest.mark.parametrize(
    ("analysis_text", "report_text", "expected_state"),
    [
        (
            COPY_CONFLICTING_SOURCE,
            "The association model reported a copy-dosage coefficient of 0.42.\n",
            "ambiguous",
        ),
        (
            COPY_POSTERIOR_SOURCE,
            "Copy state was 0 in 120 participants, 1 in 260, and 2 in 120 of the 500 genotyped "
            "participants; the mean dosage was 1.00.\n",
            "ambiguous",
        ),
        (
            COPY_UNREADABLE_SOURCE,
            "The association model reported a copy-dosage coefficient of 0.42.\n",
            "unsupported",
        ),
        (
            "value = 1\n",
            "The full-cohort representation is continuous posterior expected copy dosage, "
            "P(copy=1) + 2*P(copy=2), not an integer hard call.\n",
            "not_applicable",
        ),
        (
            "value = 1\n",
            "A directly measured continuous copy dosage from digital PCR entered the association "
            "model; no copy-state calibration model was used.\n",
            "not_applicable",
        ),
        (
            "value = 1\n",
            "Medication dosage was rounded to an integer before a classifier was evaluated.\n",
            "not_applicable",
        ),
    ],
)
def test_classifier_copy_dosage_profile_preserves_ambiguity_and_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    analysis_text: str,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text, analysis_text=analysis_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, CLASSIFIER_COPY_DOSAGE_CHECK)["state"] == expected_state


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "The primary association reconstructed a donor-level technical group from mean "
            "contamination estimates and included the recovered technical group as a categorical "
            "covariate.\n\n"
            "No donor-specific ambient group or technical group is directly observed. None is "
            "reconstructed. Consequently, no ambient-group or technical-group covariate is "
            "included.\n",
            "ambiguous",
        ),
        (
            "A technical group reconstructed from mean contamination was shown only in a QC plot; "
            "the primary association adjustment set was not stated.\n",
            "unsupported",
        ),
        (
            "Sample-level contamination fractions separated into two ranges. We reconstructed "
            "that sample-level technical group and included it as a categorical covariate in a "
            "sensitivity model. The primary association model used only age and sex.\n",
            "unsupported",
        ),
        (
            "The primary association included the directly recorded sequencing batch; no "
            "data-derived grouping was used.\n",
            "not_applicable",
        ),
        (
            "An assay-control feature was treated as an ambient-only negative-control proxy. "
            "The cell estimator allows technical contamination to vary by observation. By "
            "subject, measurements were aggregated. The primary association model was mean = "
            "exposure * exp(intercept + treatment + batch).\n",
            "unsupported",
        ),
        (
            "Biological treatment groups were included as covariates in the association model.\n",
            "not_applicable",
        ),
    ],
)
def test_recoverable_technical_group_profile_preserves_ambiguity_and_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, TECHNICAL_GROUP_CHECK)["state"] == expected_state


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "Paired bridge measurements estimated plate-specific location offsets. Each "
            "follow-up-minus-primary offset was subtracted from the follow-up effects before the "
            "effect model.\n\n"
            "The independent single-guide follow-up was not substituted for the pooled endpoint. "
            "Its correlation with the pooled guide effects supported the guide ranking.\n",
            "ambiguous",
        ),
        (
            "Within each follow-up plate, non-targeting controls were subtracted before a QC plot. "
            "No primary assay was compared.\n",
            "not_applicable",
        ),
        (
            "Paired bridge measurements were plotted with plate-specific offsets annotated for "
            "QC. No follow-up effect model was specified.\n",
            "unsupported",
        ),
        (
            "Batch-specific location offsets were subtracted from follow-up effects before "
            "regression, but no paired bridge measurements existed.\n",
            "unsupported",
        ),
    ],
)
def test_paired_bridge_location_profile_preserves_ambiguity_and_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, PAIRED_BRIDGE_CHECK)["state"] == expected_state


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "For every CasRx guide, the effective dominant-transcript axis was overlap times "
            "knockdown efficiency. The non-dominant axis was one minus overlap times knockdown "
            "efficiency. A simultaneous two-axis fit used the dominant-axis coefficient.\n\n"
            "I retained four CasRx guides with at least 0.90 dominant-isoform overlap. A "
            "through-origin regression fit growth effect on knockdown efficiency.\n",
            "ambiguous",
        ),
        (
            "CasRx dominant-isoform overlap and knockdown efficiency were displayed in a QC "
            "plot. The transcript-effect regression was not specified.\n",
            "unsupported",
        ),
        (
            "An effective dominant-transcript axis and non-dominant axis were calculated for a "
            "design-balance plot only; no effect model was fitted.\n",
            "unsupported",
        ),
        (
            "Two treatment axes were included in an ordinary clinical regression unrelated to "
            "CasRx or transcript overlap.\n",
            "not_applicable",
        ),
    ],
)
def test_casrx_isoform_axis_profile_preserves_ambiguity_and_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    assert _check_questions(bundle) == []
    assert _check_assertions(bundle) == []
    assert _module(bundle, CASRX_AXIS_CHECK)["state"] == expected_state


def test_casrx_axis_and_paired_bridge_are_independent_questions(
    tmp_path: Path, schema_root: Path
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "Paired bridge measurements estimated plate-specific location offsets. Each "
            "follow-up-minus-primary offset was subtracted from the follow-up effects before the "
            "effect model.\n\n"
            "For every CasRx guide, the effective dominant-transcript axis was overlap times "
            "knockdown efficiency. The non-dominant axis was one minus overlap times knockdown "
            "efficiency. A simultaneous two-axis fit used the dominant-axis coefficient.\n"
        ),
    )

    assert {
        question["extensions"]["x-scientific-check-id"] for question in _check_questions(bundle)
    } == {CASRX_AXIS_CHECK, PAIRED_BRIDGE_CHECK}
    assert bundle["findings"] == []


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "An initial local model compared count outcomes with expression-predicted effects. "
            "Cross-modal count-expression contradictions were flagged by robust residuals, those "
            "guide rows were excluded, and we refit the local model on the retained full-assay "
            "rows.\n",
            "applicable",
        ),
        (
            "For the neighbor-mediated local-locus model, I used the 36 guides nominally aimed "
            "at the focal locus and fit the effect model on that subset.\n",
            "applicable",
        ),
        (
            "The primary local perturbation model used nominally targeted guide rows, but its "
            "exact row filter was not stated.\n",
            "unsupported",
        ),
        (
            "The clinical model used 36 patients nominally assigned to treatment. No perturbation "
            "analysis was fitted.\n",
            "not_applicable",
        ),
    ],
)
def test_local_perturbation_row_scope_profile_preserves_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    module = _module(bundle, LOCAL_PERTURBATION_ROW_SCOPE_CHECK)
    assert module["state"] == expected_state
    assert len(_check_questions(bundle)) == (1 if expected_state == "applicable" else 0)


@pytest.mark.parametrize(
    ("report_text", "expected_state"),
    [
        (
            "The same linear local perturbation model jointly used both measured knockdown axes. "
            "Guide-level GC excess was included as a nuisance covariate, together with a "
            "promoter-core indicator.\n",
            "applicable",
        ),
        (
            "In the neighbor-mediated local-locus model, I first removed the externally estimated "
            "transcript contribution, then fit an intercept plus the remaining knockdown axis "
            "with Huber regression.\n",
            "applicable",
        ),
        (
            "The primary local perturbation regression displayed guide GC and promoter distance "
            "in QC plots, but the exact adjustment set was not stated.\n",
            "unsupported",
        ),
        (
            "A clinical regression included patient GC status and distance to hospital. No guide "
            "or local perturbation model was used.\n",
            "not_applicable",
        ),
    ],
)
def test_local_perturbation_regression_profile_preserves_hard_negatives(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    expected_state: str,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text)

    assert bundle["findings"] == []
    module = _module(bundle, LOCAL_PERTURBATION_REGRESSION_CHECK)
    assert module["state"] == expected_state
    assert len(_check_questions(bundle)) == (1 if expected_state == "applicable" else 0)


def test_report_path_and_markdown_formatting_do_not_define_profile_identity(
    tmp_path: Path, schema_root: Path
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=(
            "# METHOD\n\n| markers | agreeing |\n| --- | --- |\n| 480 | 372 |\n\n"
            "*Per-marker agreement rate:*   `0.775`\n"
        ),
        analysis_text=FOUNDER_DIRECT_SOURCE,
        report_path="nested/review-summary.markdown",
    )

    questions = _check_questions(bundle)
    assert len(questions) == 1
    assert questions[0]["extensions"]["x-scientific-check-id"] == FOUNDER_CHECK


def _founder_source_with_marker(marker: Path) -> str:
    """The repaired workflow, plus a side effect that must never happen."""

    return (
        _FOUNDER_WORKFLOW_HEAD
        + f"Path({str(marker)!r}).write_text('executed')\n"
        + "panel = [{**row, 'founder': 1 - int(row['founder'])} for row in rows]\n"
        + _FOUNDER_EMISSION.format(source="panel")
        + _FOUNDER_WORKFLOW_TAIL
    )


@pytest.mark.parametrize(
    ("analysis_text", "expected_operand"),
    [
        (FOUNDER_DIRECT_SOURCE, "use_supplied_founder_alleles_directly_in_hmm_emission"),
        (FOUNDER_REPAIRED_SOURCE, "repair_ril_founder_orientation_before_hmm_emission"),
    ],
)
def test_founder_dataflow_plane_resolves_the_orientation_operand(
    tmp_path: Path,
    schema_root: Path,
    analysis_text: str,
    expected_operand: str,
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=FOUNDER_TIED_REPORT,
        analysis_text=analysis_text,
    )

    module = _module(bundle, FOUNDER_CHECK)
    observation = module["observations"][0]

    assert module["state"] == "applicable"
    assert observation["applicability"] == "applicable"
    assert observation["evidence_plane"] == "reported_text"
    assert observation["observed_operand"]["value"] == expected_operand
    assert observation["evidence_spans"]
    assert all(item["end_line"] - item["start_line"] <= 4 for item in observation["evidence_spans"])
    assert len(_check_questions(bundle)) == 1
    assert _check_questions(bundle)[0]["extensions"]["x-scientific-check-id"] == FOUNDER_CHECK
    assert bundle["findings"] == []


@pytest.mark.parametrize("analysis_text", [FOUNDER_DIRECT_SOURCE, FOUNDER_REPAIRED_SOURCE])
def test_founder_dataflow_alone_cannot_classify_without_a_stated_accounting(
    tmp_path: Path, schema_root: Path, analysis_text: str
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text="A hidden-state reconstruction and mixed-model scan were completed.\n",
        analysis_text=analysis_text,
    )

    assert _module(bundle, FOUNDER_CHECK)["state"] == "not_applicable"
    assert _check_questions(bundle) == []
    assert bundle["findings"] == []


@pytest.mark.parametrize(
    ("report_text", "analysis_text", "expected_state", "expected_operand"),
    [
        (
            FOUNDER_DIRECT_REPORT,
            FOUNDER_DIRECT_SOURCE,
            "applicable",
            "use_supplied_founder_alleles_directly_in_hmm_emission",
        ),
        (
            FOUNDER_COMPLEMENT_REPORT,
            FOUNDER_REPAIRED_SOURCE,
            "applicable",
            "repair_ril_founder_orientation_before_hmm_emission",
        ),
        (FOUNDER_COMPLEMENT_REPORT, FOUNDER_DIRECT_SOURCE, "ambiguous", None),
        # A transform the trace cannot read leaves the workflow unsupported,
        # and from v2.0.1 a reconciling report cannot reverse that.
        (FOUNDER_DIRECT_REPORT, FOUNDER_UNREADABLE_SOURCE, "unsupported", None),
    ],
)
def test_founder_report_and_source_planes_fuse_or_abstain(
    tmp_path: Path,
    schema_root: Path,
    report_text: str,
    analysis_text: str,
    expected_state: str,
    expected_operand: str | None,
) -> None:
    bundle = _audit(tmp_path, schema_root, report_text=report_text, analysis_text=analysis_text)

    module = _module(bundle, FOUNDER_CHECK)
    observation = module["observations"][0]

    assert module["state"] == expected_state
    assert bundle["findings"] == []
    if expected_operand is None:
        assert observation["observed_operand"] is None
        assert not [
            item
            for item in _check_questions(bundle)
            if item["extensions"].get("x-scientific-check-id") == FOUNDER_CHECK
        ]
    else:
        assert observation["observed_operand"]["value"] == expected_operand
        assert len(_check_questions(bundle)) == 1


def test_founder_question_is_publication_scoped_and_replays_without_execution(
    tmp_path: Path, schema_root: Path
) -> None:
    marker = tmp_path / "must-not-exist"
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=FOUNDER_COMPLEMENT_REPORT,
        analysis_text=_founder_source_with_marker(marker),
    )

    module = _module(bundle, FOUNDER_CHECK)
    observation = module["observations"][0]
    relations = [
        item["relation"]
        for item in _check_questions(bundle)[0]["extensions"]["x-scientific-check-scope-join-path"]
    ]

    assert module["state"] == "applicable"
    assert observation["applicability"] == "applicable"
    assert [item["relation"] for item in observation["scope_join_path"]] == [
        "selected_by_publication_surface"
    ]
    assert relations == [item["relation"] for item in observation["scope_join_path"]]
    assert len(_check_questions(bundle)) == 1
    assert {item["semantic_role"] for item in _check_assertions(bundle)} == {"reported"}
    assert bundle["findings"] == []
    assert bundle["executions"] == []
    assert not marker.exists()

    replayed = replay(tmp_path / "audit" / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["material_questions"] == bundle["material_questions"]
    assert replayed["semantic_assertions"] == bundle["semantic_assertions"]


def test_conformance_module_is_removable_without_changing_substantive_evaluation(
    tmp_path: Path, schema_root: Path
) -> None:
    report = FOUNDER_DIRECT_REPORT + "\nSC-REFEREE-CONFORMANCE: bounded\n"
    full_registry = default_scientific_check_registry(include_conformance=True)
    conformance = next(
        module for module in full_registry.modules if module.manifest.check_id == CONFORMANCE_CHECK
    )
    reduced_registry = ScientificCheckRegistry(
        tuple(
            module
            for module in full_registry.modules
            if module.manifest.check_id != CONFORMANCE_CHECK
        ),
        unavailable_manifests=(conformance.manifest,),
    )
    default = _audit(
        tmp_path / "default",
        schema_root,
        report_text=report,
        analysis_text=FOUNDER_DIRECT_SOURCE,
        registry=reduced_registry,
    )
    augmented = _audit(
        tmp_path / "augmented",
        schema_root,
        report_text=report,
        analysis_text=FOUNDER_DIRECT_SOURCE,
        registry=full_registry,
    )

    default_founder = _module(default, FOUNDER_CHECK)
    augmented_founder = _module(augmented, FOUNDER_CHECK)
    assert {
        "check_id": default_founder["check_id"],
        "manifest_digest": default_founder["manifest_digest"],
        "state": default_founder["state"],
        "basis": default_founder["basis"],
        "observations": [
            (item["adapter_id"], item["applicability"], item["observed_operand"])
            for item in default_founder["observations"]
        ],
    } == {
        "check_id": augmented_founder["check_id"],
        "manifest_digest": augmented_founder["manifest_digest"],
        "state": augmented_founder["state"],
        "basis": augmented_founder["basis"],
        "observations": [
            (item["adapter_id"], item["applicability"], item["observed_operand"])
            for item in augmented_founder["observations"]
        ],
    }
    assert {item["extensions"]["x-scientific-check-id"] for item in _check_questions(default)} == {
        FOUNDER_CHECK
    }
    assert {
        item["extensions"]["x-scientific-check-id"] for item in _check_questions(augmented)
    } == {FOUNDER_CHECK, CONFORMANCE_CHECK}
    unavailable = next(
        item
        for item in default["disclosures"]
        if item.get("extensions", {}).get("x-scientific-check-id") == CONFORMANCE_CHECK
    )
    assert unavailable["title"] == "Scientific check is not installed"
    assert unavailable["extensions"]["x-scientific-check-state"] == "not_installed"


def test_rmarkdown_mvmr_module_does_not_change_existing_sibling_module_bytes() -> None:
    full_registry = default_scientific_check_registry()
    mvmr_covariance = next(
        module
        for module in full_registry.modules
        if module.manifest.check_id == MVMR_COVARIANCE_CHECK
    )
    reduced_registry = ScientificCheckRegistry(
        tuple(
            module
            for module in full_registry.modules
            if module.manifest.check_id != MVMR_COVARIANCE_CHECK
        ),
        unavailable_manifests=(mvmr_covariance.manifest,),
    )
    context = _inspection_context()
    reduced = next(
        item
        for item in reduced_registry.evaluate(context).modules
        if item.check_id == FOUNDER_CHECK
    )
    full = next(
        item for item in full_registry.evaluate(context).modules if item.check_id == FOUNDER_CHECK
    )

    assert canonical_json(reduced.to_dict()) == canonical_json(full.to_dict())


@pytest.mark.parametrize("removed_check_id", [MVMR_INSTRUMENT_CHECK, MVMR_ESTIMATOR_CHECK])
def test_new_mvmr_modules_are_removable_and_sibling_isolated(removed_check_id: str) -> None:
    full_registry = default_scientific_check_registry()
    removed = next(
        module for module in full_registry.modules if module.manifest.check_id == removed_check_id
    )
    reduced_registry = ScientificCheckRegistry(
        tuple(
            module
            for module in full_registry.modules
            if module.manifest.check_id != removed_check_id
        ),
        unavailable_manifests=(removed.manifest,),
    )
    context = _inspection_context()
    reduced = next(
        item
        for item in reduced_registry.evaluate(context).modules
        if item.check_id == FOUNDER_CHECK
    )
    full = next(
        item for item in full_registry.evaluate(context).modules if item.check_id == FOUNDER_CHECK
    )

    assert canonical_json(reduced.to_dict()) == canonical_json(full.to_dict())


def test_poststratified_calibration_module_is_removable_and_sibling_isolated() -> None:
    full_registry = default_scientific_check_registry()
    calibration = next(
        module
        for module in full_registry.modules
        if module.manifest.check_id == POSTSTRATIFIED_CALIBRATION_CHECK
    )
    reduced_registry = ScientificCheckRegistry(
        tuple(
            module
            for module in full_registry.modules
            if module.manifest.check_id != POSTSTRATIFIED_CALIBRATION_CHECK
        ),
        unavailable_manifests=(calibration.manifest,),
    )
    context = _inspection_context()
    reduced = next(
        item
        for item in reduced_registry.evaluate(context).modules
        if item.check_id == FOUNDER_CHECK
    )
    full = next(
        item for item in full_registry.evaluate(context).modules if item.check_id == FOUNDER_CHECK
    )

    assert canonical_json(reduced.to_dict()) == canonical_json(full.to_dict())


def test_directional_measurement_error_module_is_removable_and_sibling_isolated() -> None:
    full_registry = default_scientific_check_registry()
    directional_error = next(
        module
        for module in full_registry.modules
        if module.manifest.check_id == DIRECTIONAL_MEASUREMENT_ERROR_CHECK
    )
    reduced_registry = ScientificCheckRegistry(
        tuple(
            module
            for module in full_registry.modules
            if module.manifest.check_id != DIRECTIONAL_MEASUREMENT_ERROR_CHECK
        ),
        unavailable_manifests=(directional_error.manifest,),
    )
    context = _inspection_context()
    reduced = next(
        item
        for item in reduced_registry.evaluate(context).modules
        if item.check_id == FOUNDER_CHECK
    )
    full = next(
        item for item in full_registry.evaluate(context).modules if item.check_id == FOUNDER_CHECK
    )

    assert canonical_json(reduced.to_dict()) == canonical_json(full.to_dict())


def test_transition_path_module_is_removable_and_sibling_isolated() -> None:
    full_registry = default_scientific_check_registry()
    transition_path = next(
        module
        for module in full_registry.modules
        if module.manifest.check_id == TRANSITION_PATH_CHECK
    )
    reduced_registry = ScientificCheckRegistry(
        tuple(
            module
            for module in full_registry.modules
            if module.manifest.check_id != TRANSITION_PATH_CHECK
        ),
        unavailable_manifests=(transition_path.manifest,),
    )
    context = _inspection_context()
    reduced = next(
        item
        for item in reduced_registry.evaluate(context).modules
        if item.check_id == FOUNDER_CHECK
    )
    full = next(
        item for item in full_registry.evaluate(context).modules if item.check_id == FOUNDER_CHECK
    )

    assert canonical_json(reduced.to_dict()) == canonical_json(full.to_dict())


def test_direct_standardization_module_is_removable_and_sibling_isolated() -> None:
    full_registry = default_scientific_check_registry()
    standardization = next(
        module
        for module in full_registry.modules
        if module.manifest.check_id == DIRECT_STANDARDIZATION_CHECK
    )
    reduced_registry = ScientificCheckRegistry(
        tuple(
            module
            for module in full_registry.modules
            if module.manifest.check_id != DIRECT_STANDARDIZATION_CHECK
        ),
        unavailable_manifests=(standardization.manifest,),
    )
    context = _inspection_context()
    reduced = next(
        item
        for item in reduced_registry.evaluate(context).modules
        if item.check_id == FOUNDER_CHECK
    )
    full = next(
        item for item in full_registry.evaluate(context).modules if item.check_id == FOUNDER_CHECK
    )

    assert canonical_json(reduced.to_dict()) == canonical_json(full.to_dict())


def test_classifier_copy_dosage_module_is_removable_and_sibling_isolated() -> None:
    full_registry = default_scientific_check_registry()
    dosage = next(
        module
        for module in full_registry.modules
        if module.manifest.check_id == CLASSIFIER_COPY_DOSAGE_CHECK
    )
    reduced_registry = ScientificCheckRegistry(
        tuple(
            module
            for module in full_registry.modules
            if module.manifest.check_id != CLASSIFIER_COPY_DOSAGE_CHECK
        ),
        unavailable_manifests=(dosage.manifest,),
    )
    context = _inspection_context()
    reduced = next(
        item
        for item in reduced_registry.evaluate(context).modules
        if item.check_id == FOUNDER_CHECK
    )
    full = next(
        item for item in full_registry.evaluate(context).modules if item.check_id == FOUNDER_CHECK
    )

    assert canonical_json(reduced.to_dict()) == canonical_json(full.to_dict())


def test_recoverable_technical_group_module_is_removable_and_sibling_isolated() -> None:
    full_registry = default_scientific_check_registry()
    technical_group = next(
        module
        for module in full_registry.modules
        if module.manifest.check_id == TECHNICAL_GROUP_CHECK
    )
    reduced_registry = ScientificCheckRegistry(
        tuple(
            module
            for module in full_registry.modules
            if module.manifest.check_id != TECHNICAL_GROUP_CHECK
        ),
        unavailable_manifests=(technical_group.manifest,),
    )
    context = _inspection_context()
    reduced = next(
        item
        for item in reduced_registry.evaluate(context).modules
        if item.check_id == FOUNDER_CHECK
    )
    full = next(
        item for item in full_registry.evaluate(context).modules if item.check_id == FOUNDER_CHECK
    )

    assert canonical_json(reduced.to_dict()) == canonical_json(full.to_dict())


def test_paired_bridge_location_module_is_removable_and_sibling_isolated() -> None:
    full_registry = default_scientific_check_registry()
    paired_bridge = next(
        module
        for module in full_registry.modules
        if module.manifest.check_id == PAIRED_BRIDGE_CHECK
    )
    reduced_registry = ScientificCheckRegistry(
        tuple(
            module
            for module in full_registry.modules
            if module.manifest.check_id != PAIRED_BRIDGE_CHECK
        ),
        unavailable_manifests=(paired_bridge.manifest,),
    )
    context = _inspection_context()
    reduced = next(
        item
        for item in reduced_registry.evaluate(context).modules
        if item.check_id == FOUNDER_CHECK
    )
    full = next(
        item for item in full_registry.evaluate(context).modules if item.check_id == FOUNDER_CHECK
    )

    assert canonical_json(reduced.to_dict()) == canonical_json(full.to_dict())


def test_casrx_isoform_axis_module_is_removable_and_sibling_isolated() -> None:
    full_registry = default_scientific_check_registry()
    casrx_axis = next(
        module for module in full_registry.modules if module.manifest.check_id == CASRX_AXIS_CHECK
    )
    reduced_registry = ScientificCheckRegistry(
        tuple(
            module
            for module in full_registry.modules
            if module.manifest.check_id != CASRX_AXIS_CHECK
        ),
        unavailable_manifests=(casrx_axis.manifest,),
    )
    context = _inspection_context()
    reduced = next(
        item
        for item in reduced_registry.evaluate(context).modules
        if item.check_id == FOUNDER_CHECK
    )
    full = next(
        item for item in full_registry.evaluate(context).modules if item.check_id == FOUNDER_CHECK
    )

    assert canonical_json(reduced.to_dict()) == canonical_json(full.to_dict())


@pytest.mark.parametrize(
    "removed_check_id",
    [module.manifest.check_id for module in default_scientific_check_registry().canonical_modules],
)
def test_each_scientific_module_is_removable_and_sibling_isolated(
    removed_check_id: str,
) -> None:
    full_registry = default_scientific_check_registry()
    removed = next(
        module for module in full_registry.modules if module.manifest.check_id == removed_check_id
    )
    reduced_registry = ScientificCheckRegistry(
        tuple(
            module
            for module in full_registry.modules
            if module.manifest.check_id != removed_check_id
        ),
        unavailable_manifests=(removed.manifest,),
    )
    context = _inspection_context()
    full = {
        item.check_id: canonical_json(item.to_dict())
        for item in full_registry.evaluate(context).modules
        if item.check_id != removed_check_id
    }
    reduced = {
        item.check_id: canonical_json(item.to_dict())
        for item in reduced_registry.evaluate(context).modules
        if item.check_id != removed_check_id
    }

    assert reduced == full


def test_scientific_check_inventory_and_evaluation_are_locked_for_replay(
    tmp_path: Path, schema_root: Path
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=FOUNDER_DIRECT_REPORT,
    )
    lock = json.loads((tmp_path / "audit" / "semantic.lock.json").read_text(encoding="utf-8"))

    assert lock["scientific_check_registry"] == bundle["_scientific_check_registry"]
    assert lock["scientific_check_registry"]["registry_digest"].startswith("sha256:")
    assert lock["model_access_after_lock"] is False
    replayed = replay(tmp_path / "audit" / "semantic.lock.json", tmp_path / "replay", schema_root)
    for field in (
        "semantic_assertions",
        "material_questions",
        "disclosures",
        "findings",
        "coverage_records",
    ):
        assert replayed[field] == bundle[field]


def test_agent_and_html_surfaces_show_exact_scientist_choices_and_observation(
    tmp_path: Path, schema_root: Path
) -> None:
    bundle = _audit(
        tmp_path,
        schema_root,
        report_text=FOUNDER_DIRECT_REPORT,
        analysis_text=FOUNDER_DIRECT_SOURCE,
    )

    batch = load_open_questions(tmp_path / "audit", schema_root)
    assert len(batch.questions) == 1
    question = batch.questions[0]
    assert question.comparison_forms == {"scale_and_orientation": "value_equals"}
    assert [item.operand["value"] for item in question.requirement_candidates] == [
        "repair_ril_founder_orientation_before_hmm_emission",
        "use_supplied_founder_alleles_directly_in_hmm_emission",
    ]
    assert len(question.observed_operands) == 1
    assert (
        question.observed_operands[0].value
        == "use_supplied_founder_alleles_directly_in_hmm_emission"
    )
    # The observation now cites both planes: the report accounting it
    # corroborates and the workflow comparison that resolved it.
    assert {item["path"] for item in question.observed_operands[0].source_refs} == {
        "report.md",
        "analysis.py",
    }
    assert question.output_ceiling == "question_only"
    assert question.review_scope is not None
    assert question.review_scope.level == "analysis"

    html = (tmp_path / "audit" / "report.html").read_text(encoding="utf-8")
    assert "What the audit observed" in html
    assert "What the scientist can decide for this review" in html
    assert "repair_ril_founder_orientation_before_hmm_emission" in html
    assert "use_supplied_founder_alleles_directly_in_hmm_emission" in html
    assert "Blocked detectors:</strong> </p>" not in html
    assert "Ask the scientist to select one listed review-scoped method requirement" in html
    routine_count = sum(
        item["coverage_status"] == "not_applicable" for item in bundle["disclosures"]
    )
    assert f">{routine_count}</div><div>Routine not-applicable checks</div>" in html
    assert "coverage bookkeeping, not concerns about the workflow" in html
    coverage = bundle["coverage_records"][0]
    assert all(
        "after the publication surface is resolved" not in item
        for item in coverage["extensions"]["x-pending-work"]
    )


def test_packaged_release_manifest_rejects_declared_manifest_drift(tmp_path: Path) -> None:
    registry = default_scientific_check_registry(include_conformance=True)
    projection = scientific_check_release_projection(registry)
    projection["modules"][0]["manifest_digest"] = sha256_digest("mutated-manifest")
    manifest = tmp_path / "registry.json"
    manifest.write_text(canonical_json(projection) + "\n", encoding="utf-8")

    with pytest.raises(RegistryValidationError, match="manifest or implementation drift"):
        verify_scientific_check_release_manifest(registry, manifest_path=manifest)


def test_parser_identity_and_document_digest_mutations_fail_closed() -> None:
    registry = default_scientific_check_registry()
    applicable = registry.evaluate(_inspection_context())
    module = next(item for item in applicable.modules if item.check_id == FOUNDER_CHECK)
    assert module.state == "applicable"

    parser_mismatch = registry.evaluate(_inspection_context(report_parser_version="9.9.9"))
    founder = next(item for item in parser_mismatch.modules if item.check_id == FOUNDER_CHECK)
    assert founder.state == "unsupported"

    document = _inspection_context().documents[0]
    with pytest.raises(ScientificCheckContractError, match="content digest mismatch"):
        replace(document, content=document.content + b"mutated")
