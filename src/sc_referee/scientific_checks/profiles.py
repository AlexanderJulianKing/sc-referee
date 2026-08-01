from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest
from sc_referee.parsers.python_ast import PARSER_ID as PYTHON_PARSER_ID
from sc_referee.parsers.python_ast import PARSER_VERSION as PYTHON_PARSER_VERSION
from sc_referee.scientific_checks.core import (
    AdapterManifest,
    CanonicalOperand,
    CheckManifest,
    MethodConflictBinding,
    RequirementCandidate,
    RoleBinding,
    ScientificCheckAdapter,
    ScientificCheckModule,
)
from sc_referee.scientific_checks.python_founder_adapter import (
    PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST,
    PythonFounderOrientationAdapter,
    python_founder_recognition_grammar_digest,
)
from sc_referee.scientific_checks.registry import (
    SCIENTIFIC_CHECK_REDUCER_IMPLEMENTATION_DIGEST,
    RegistryValidationError,
    ScientificCheckRegistry,
)
from sc_referee.scientific_checks.rmarkdown_mvmr_adapter import (
    RMARKDOWN_MVMR_ADAPTER_IMPLEMENTATION_DIGEST,
    RMarkdownMVMRCovarianceAdapter,
    rmarkdown_mvmr_recognition_grammar_digest,
)
from sc_referee.scientific_checks.selected_report_adapter import (
    SELECTED_REPORT_ADAPTER_IMPLEMENTATION_DIGEST,
    ReportOperandRule,
    SelectedReportMethodAdapter,
    report_recognition_grammar_digest,
)

NON_INFERENCES = (
    "execution",
    "historical_intent",
    "numerical_causality",
    "scientific_correctness",
)
REPORT_COUNTEREVIDENCE = (
    "exactly-one-supported-declaration",
    "contradictory-declaration-absent",
    "selected-surface-identity-complete",
    "finite-paragraph-scan-complete",
)
_RELEASE_MANIFEST_PATH = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "scientific-check-manifests-v1"
    / "registry.json"
)


@dataclass(frozen=True)
class _ReportProfile:
    check_id: str
    dimension: str
    candidates: tuple[RequirementCandidate, ...]
    semantic_roles: tuple[str, ...]
    role_bindings: tuple[RoleBinding, ...]
    rules: tuple[ReportOperandRule, ...]
    triggers: tuple[str, ...]
    question_wording: str
    extra_record_types: tuple[str, ...] = ()
    check_version: str = "1.0.0"
    adapter_version: str = "1.0.0"


def default_scientific_check_registry(
    *, include_conformance: bool = False
) -> ScientificCheckRegistry:
    """Build the explicit auditor-controlled ADR-0020 question-only registry."""

    release = scientific_check_release_registry()
    verify_scientific_check_release_manifest(release)
    if include_conformance:
        return release
    selected = release.modules[:-1]
    selected_ids = {module.manifest.check_id for module in selected}
    return ScientificCheckRegistry(
        selected,
        method_conflict_bindings=tuple(
            binding
            for binding in release.method_conflict_bindings
            if binding.check_id in selected_ids
        ),
    )


def scientific_check_release_registry() -> ScientificCheckRegistry:
    """Construct the complete content-addressed registry before release-manifest verification."""

    modules = _scientific_check_release_modules()
    founder = next(
        module
        for module in modules
        if module.manifest.check_id == "check:founder-orientation-before-hmm-emission"
    )
    detector_manifest = _method_conflict_detector_manifest()
    binding = MethodConflictBinding(
        binding_id="method-conflict-binding:founder-orientation-before-hmm-emission-v1",
        check_id=founder.manifest.check_id,
        check_version=founder.manifest.check_version,
        check_manifest_digest=founder.manifest.manifest_digest,
        detector_id=str(detector_manifest["detector_id"]),
        detector_version=str(detector_manifest["detector_version"]),
        detector_manifest_digest=semantic_digest(detector_manifest),
        dimension=founder.manifest.dimension,
        comparison_form=founder.manifest.comparison_form,
        operand_kind="canonical_scalar",
        required_evidence_planes=("reported_text", "static_source"),
        required_semantic_roles=founder.manifest.semantic_roles,
        required_assertion_roles=("reported", "observed"),
        counterevidence_predicates=(
            "approved_method_deviation",
            "governing_protocol_amendment",
            "method_obligation_applicability",
        ),
    )
    return ScientificCheckRegistry(modules, method_conflict_bindings=(binding,))


def _scientific_check_release_modules() -> tuple[ScientificCheckModule, ...]:
    """Construct the complete manifest set, including the removable conformance module."""

    report_profiles = (
        _expected_count_background_construction_profile(),
        _expected_count_focal_target_handling_profile(),
        _founder_orientation_profile(),
        _directional_measurement_error_profile(),
        _transition_path_continuity_profile(),
        _ancestry_exposure_profile(),
        _phase_split_mvmr_instrument_profile(),
        _mvmr_heterogeneity_estimator_profile(),
        _ld_whitening_profile(),
        _poststratified_misclassification_profile(),
        _posttreatment_missingness_strategy_profile(),
        _somatic_clonality_representation_profile(),
        _direct_standardization_conditioning_set_profile(),
        _classifier_copy_dosage_profile(),
        _recoverable_technical_group_profile(),
        _casrx_isoform_axis_profile(),
        _paired_bridge_location_alignment_profile(),
    )
    modules = (
        *(tuple(_module(profile) for profile in report_profiles)),
        _mvmr_covariance_module(),
        _module(_conformance_profile()),
    )
    return modules


def verify_scientific_check_release_manifest(
    registry: ScientificCheckRegistry,
    *,
    manifest_path: Path = _RELEASE_MANIFEST_PATH,
) -> None:
    """Reject source or manifest drift against the packaged ADR-0020 release inventory."""

    try:
        payload = manifest_path.read_bytes()
        expected = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise RegistryValidationError(
            "scientific-check release manifest is unavailable or invalid"
        ) from error
    if not isinstance(expected, dict) or canonical_json(expected).encode("utf-8") != payload.rstrip(
        b"\n"
    ):
        raise RegistryValidationError("scientific-check release manifest is not canonical JSON")
    actual = scientific_check_release_projection(registry)
    if expected != actual:
        raise RegistryValidationError("scientific-check release manifest or implementation drift")


def scientific_check_release_projection(
    registry: ScientificCheckRegistry,
) -> dict[str, Any]:
    return {
        "manifest_set_id": "scientific-check-manifest-set:v1",
        "profile_id": "scientific_check_registry_v1",
        "implementation_files": {
            "scientific_checks/python_founder_adapter.py": (
                PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/rmarkdown_mvmr_adapter.py": (
                RMARKDOWN_MVMR_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/registry.py": SCIENTIFIC_CHECK_REDUCER_IMPLEMENTATION_DIGEST,
            "scientific_checks/selected_report_adapter.py": (
                SELECTED_REPORT_ADAPTER_IMPLEMENTATION_DIGEST
            ),
        },
        "modules": [
            {
                "check_id": module.manifest.check_id,
                "check_version": module.manifest.check_version,
                "manifest_digest": module.manifest.manifest_digest,
                "implementation_digest": module.manifest.implementation_digest,
                "adapters": [
                    {
                        "adapter_id": adapter.adapter_id,
                        "adapter_version": adapter.adapter_version,
                        "manifest_digest": adapter.manifest_digest,
                        "implementation_digest": adapter.implementation_digest,
                        "recognition_grammar_digest": adapter.recognition_grammar_digest,
                    }
                    for adapter in sorted(
                        module.adapter_manifests, key=lambda item: item.adapter_id
                    )
                ],
            }
            for module in sorted(registry.modules, key=lambda item: item.manifest.check_id)
        ],
        "method_conflict_bindings": [
            binding.to_dict()
            for binding in sorted(
                registry.method_conflict_bindings, key=lambda item: item.binding_id
            )
        ],
    }


def _method_conflict_detector_manifest() -> Mapping[str, Any]:
    path = (
        Path(__file__).resolve().parents[1]
        / "resources"
        / "capability-manifests-v1"
        / "detector-manifests.json"
    )
    payload = path.read_bytes()
    try:
        collection = json.loads(payload)
    except json.JSONDecodeError as error:
        raise RegistryValidationError("detector manifest collection is invalid") from error
    if canonical_json(collection).encode("utf-8") != payload.rstrip(b"\n"):
        raise RegistryValidationError("detector manifest collection is not canonical JSON")
    records = collection.get("records") if isinstance(collection, Mapping) else None
    if not isinstance(records, list):
        raise RegistryValidationError("detector manifest collection has no record list")
    matches = [
        item
        for item in records
        if isinstance(item, Mapping)
        and item.get("detector_id") == "detector:bounded-analysis-method-conflict"
    ]
    if len(matches) != 1:
        raise RegistryValidationError("method-conflict detector manifest is unavailable")
    manifest = matches[0]
    if (
        manifest.get("record_type") != "detector_manifest"
        or manifest.get("detector_version") != "0.2.0"
        or manifest.get("maturity") != "experimental"
        or "finding" in manifest.get("permitted_output_types", [])
    ):
        raise RegistryValidationError("method-conflict detector manifest is ineligible")
    return manifest


def _module(profile: _ReportProfile) -> ScientificCheckModule:
    check = CheckManifest(
        check_id=profile.check_id,
        check_version=profile.check_version,
        implementation_digest=SCIENTIFIC_CHECK_REDUCER_IMPLEMENTATION_DIGEST,
        maturity_tier="question_only",
        dimension=profile.dimension,
        comparison_form="value_equals",
        requirement_candidates=profile.candidates,
        semantic_roles=profile.semantic_roles,
        required_record_types=(
            "artifact",
            "asset_identity",
            "parser_result",
            "publication_surface",
            *profile.extra_record_types,
        ),
        permitted_wording=profile.question_wording,
        prohibited_inferences=NON_INFERENCES,
    )
    adapter_id = f"adapter:{profile.check_id.removeprefix('check:')}:selected-report-v1"
    adapter_manifest = AdapterManifest(
        adapter_id=adapter_id,
        adapter_version=profile.adapter_version,
        implementation_digest=SELECTED_REPORT_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=report_recognition_grammar_digest(
            profile.rules, profile.role_bindings, profile.triggers
        ),
        parser_id="parser:markdown-inventory",
        parser_version="0.2.0",
        source_language="markdown",
        evidence_plane="reported_text",
        semantic_roles=profile.semantic_roles,
        applicability_profile="exact-selected-report-method-declaration-v1",
        counterevidence_profiles=REPORT_COUNTEREVIDENCE,
        known_gaps=(
            "paraphrases outside the enumerated grammar",
            "non-Markdown publication surfaces",
            "reported wording does not establish execution",
        ),
    )
    report_adapter = SelectedReportMethodAdapter(
        check_manifest=check,
        adapter_manifest=adapter_manifest,
        rules=profile.rules,
        role_bindings=profile.role_bindings,
        trigger_patterns=profile.triggers,
    )
    adapter_manifests = [adapter_manifest]
    adapters: list[ScientificCheckAdapter] = [report_adapter]
    if profile.check_id == "check:founder-orientation-before-hmm-emission":
        direct_operand = CanonicalOperand.scalar(
            "use_supplied_founder_alleles_directly_in_hmm_emission"
        )
        repaired_operand = CanonicalOperand.scalar(
            "repair_ril_founder_orientation_before_hmm_emission"
        )
        source_manifest = AdapterManifest(
            adapter_id="adapter:founder-orientation-before-hmm-emission:python-ast-v1",
            adapter_version="1.2.0",
            implementation_digest=PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST,
            recognition_grammar_digest=python_founder_recognition_grammar_digest(
                direct_operand, repaired_operand, profile.role_bindings
            ),
            parser_id=PYTHON_PARSER_ID,
            parser_version=PYTHON_PARSER_VERSION,
            source_language="python",
            evidence_plane="static_source",
            semantic_roles=profile.semantic_roles,
            applicability_profile="exact-founder-input-to-emission-ast-flow-and-scope-v2",
            counterevidence_profiles=(
                "exact-founder-emission-role-binding",
                "alternative-orientation-targets-absent",
                "source-to-analysis-scope-join",
            ),
            known_gaps=(
                "dynamic dispatch",
                "multiple founder-emission targets",
                "separate source files without exact selected-output writer lineage",
                "writer or selected-container scope does not establish execution or primary-analysis status",
            ),
        )
        adapter_manifests.append(source_manifest)
        adapters.append(
            PythonFounderOrientationAdapter(
                check_manifest=check,
                adapter_manifest=source_manifest,
                direct_operand=direct_operand,
                repaired_operand=repaired_operand,
                role_bindings=profile.role_bindings,
            )
        )
    return ScientificCheckModule(
        manifest=check,
        declared_manifest_digest=check.manifest_digest,
        adapter_manifests=tuple(adapter_manifests),
        adapters=tuple(adapters),
    )


def _candidate(candidate_id: str, label: str, value: str, basis: str) -> RequirementCandidate:
    return RequirementCandidate(
        candidate_id=candidate_id,
        label=label,
        operand=CanonicalOperand.scalar(value),
        authority_basis=basis,
    )


def _expected_count_background_construction_profile() -> _ReportProfile:
    same_stratum = "same_stratum_arithmetic_mean_expected_count"
    count_model = "negative_binomial_glm_predicted_expected_count"
    authority_basis = (
        "Scientist-supplied expected-count definition for this review; the check does not infer "
        "a preferred estimator from count data, available annotations, or numeric agreement."
    )
    return _ReportProfile(
        check_id="check:expected-count-background-construction",
        dimension="measurement_model",
        candidates=(
            _candidate(
                "negative-binomial-model-prediction",
                "Use a negative-binomial GLM prediction as expected count",
                count_model,
                authority_basis,
            ),
            _candidate(
                "same-stratum-arithmetic-mean",
                "Use a same-stratum arithmetic mean as expected count",
                same_stratum,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "observed_count",
            "expected_count_background",
            "background_estimator",
        ),
        role_bindings=(
            RoleBinding("observed_count", "focal_observed_count"),
            RoleBinding("expected_count_background", "declared_primary_expected_count"),
            RoleBinding("background_estimator", "declared_primary_background_estimator"),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(same_stratum),
                (
                    r"(?is)\bexpected\s+(?:count\s+)?is\s+the\s+per[- ]replicate\s+arithmetic\s+mean\b",
                    r"(?is)\b(?:same[- ]distance|same\s+(?:genomic\s+)?(?:distance|separation)|pixels?\s+at\s+`?dist_bin\s*=\s*[1-9][0-9]*)\b",
                ),
                match_scope="document",
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(count_model),
                (
                    r"(?is)\b(?:fit|fitted|fits|fitting)\s+(?:a|the)\s+(?:negative[- ]binomial|NB2?)\s+(?:GLM|generalized\s+linear\s+model)\b",
                    r"(?is)\b(?:predict|predicted|predicting)\b[^.]{0,200}\bheld[- ]out\s+(?:focal\s+)?target\b[^.]{0,120}\bexpect(?:ation|ed\s+count)\b",
                ),
                match_scope="document",
            ),
        ),
        triggers=(
            r"(?is)\b(?:same[- ]distance|same[- ]stratum)\b[^.]{0,160}\bexpected\s+count\b",
            r"(?is)\bexpected\s+(?:count\s+)?is\b[^.]{0,200}\barithmetic\s+mean\b",
            r"(?is)\b(?:negative[- ]binomial|NB2?)\b[^.]{0,160}\b(?:expected|background)\b",
        ),
        question_wording=(
            "Which expected-count background construction governs the requested values for "
            "this review?"
        ),
    )


def _expected_count_focal_target_handling_profile() -> _ReportProfile:
    exclude = "exclude_focal_target_from_expected_count_training"
    include = "include_focal_target_in_expected_count_background"
    authority_basis = (
        "Scientist-supplied information-boundary rule for this review; the check does not infer "
        "target handling from a sensitivity result or choose it as a universal convention."
    )
    return _ReportProfile(
        check_id="check:expected-count-focal-target-handling",
        dimension="selection_process",
        candidates=(
            _candidate(
                "exclude-focal-target",
                "Exclude the focal target from expected-count training",
                exclude,
                authority_basis,
            ),
            _candidate(
                "include-focal-target",
                "Include the focal target in its expected-count background",
                include,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "focal_target",
            "expected_count_training_set",
            "target_handling_rule",
        ),
        role_bindings=(
            RoleBinding("focal_target", "selected_focal_observation"),
            RoleBinding("expected_count_training_set", "declared_background_observations"),
            RoleBinding("target_handling_rule", "declared_primary_target_handling"),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(include),
                (
                    r"(?is)(?:\bexpected\s+(?:count\s+)?is\b[^.]{0,320}\bincluding\s+the\s+(?:focal\s+pixel|focal\s+observation|target(?:\s+pair|\s+observation)?)\b|\b(?:focal\s+pixel|focal\s+observation|focal\s+target|target\s+pair)\b[^.]{0,100}\b(?:was\s+|is\s+)?included\s+in\s+(?:its\s+own\s+)?(?:expected[- ]count\s+)?background\b)",
                ),
                match_scope="document",
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(exclude),
                (
                    r"(?is)\b(?:target\s+pair|focal\s+pixel|focal\s+observation|focal\s+target)\b[^.]{0,100}\b(?:was\s+|is\s+)?excluded\s+from\s+(?:expected[- ]count\s+)?(?:training|background)\b",
                    r"(?is)\b(?:predict|predicted|predicting)\b[^.]{0,200}\bheld[- ]out\s+(?:focal\s+)?target\b[^.]{0,120}\bexpect(?:ation|ed\s+count)\b",
                ),
                match_scope="document",
            ),
        ),
        triggers=(
            r"(?is)\b(?:focal\s+pixel|focal\s+observation|focal\s+target|target\s+pair)\b[^.]{0,220}\b(?:expected|background|training)\b",
            r"(?is)\b(?:expected|background|training)\b[^.]{0,220}\b(?:focal\s+pixel|focal\s+observation|focal\s+target|target\s+pair)\b",
        ),
        question_wording=(
            "Which focal-target handling rule governs expected-count construction for this review?"
        ),
    )


def _mvmr_covariance_module() -> ScientificCheckModule:
    zero = CanonicalOperand.scalar("zero_cross_exposure_covariance")
    provided = CanonicalOperand.scalar("provided_cross_exposure_covariance")
    roles = (
        "cross_exposure_covariance",
        "mvmr_diagnostic",
        "sample_overlap_condition",
    )
    bindings = (
        RoleBinding("cross_exposure_covariance", "named_gencov_argument"),
        RoleBinding("mvmr_diagnostic", "strength_or_pleiotropy_diagnostic"),
        RoleBinding("sample_overlap_condition", "scientist_governed"),
    )
    check = CheckManifest(
        check_id="check:mvmr-cross-exposure-covariance",
        check_version="1.0.0",
        implementation_digest=SCIENTIFIC_CHECK_REDUCER_IMPLEMENTATION_DIGEST,
        maturity_tier="question_only",
        dimension="measurement_model",
        comparison_form="value_equals",
        requirement_candidates=(
            RequirementCandidate(
                candidate_id="nonoverlapping-samples-zero-covariance",
                label=("Exposure GWAS samples do not overlap; use zero cross-exposure covariance"),
                operand=zero,
                authority_basis=(
                    "Scientist-supplied sample provenance; the check does not infer overlap."
                ),
            ),
            RequirementCandidate(
                candidate_id="overlapping-samples-estimated-covariance",
                label=(
                    "Exposure GWAS samples overlap; provide estimated cross-exposure covariance"
                ),
                operand=provided,
                authority_basis=(
                    "Scientist-supplied sample provenance; the check does not infer overlap."
                ),
            ),
        ),
        semantic_roles=roles,
        required_record_types=(
            "artifact",
            "asset_identity",
            "parser_result",
            "publication_surface",
        ),
        permitted_wording=(
            "Which exposure-sample condition governs the covariance used by these MVMR diagnostics?"
        ),
        prohibited_inferences=NON_INFERENCES,
    )
    adapter_manifest = AdapterManifest(
        adapter_id="adapter:mvmr-cross-exposure-covariance:selected-rmarkdown-v1",
        adapter_version="1.0.0",
        implementation_digest=RMARKDOWN_MVMR_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=rmarkdown_mvmr_recognition_grammar_digest(
            zero, provided, bindings
        ),
        parser_id="parser:rmarkdown-selected-report-inventory",
        parser_version="0.1.0",
        source_language="r_markdown",
        evidence_plane="static_source",
        semantic_roles=roles,
        applicability_profile="selected-rmarkdown-mvmr-gencov-call-v1",
        counterevidence_profiles=(
            "selected-surface-identity-complete",
            "active-r-chunk-scan-complete",
            "explicit-named-gencov-argument",
            "contradictory-diagnostic-operands-absent",
            "same-artifact-scope-join-complete",
        ),
        known_gaps=(
            "general R syntax and dataflow",
            "rendered R Markdown and chunk execution",
            "MVMR functions other than strength_mvmr and pleiotropy_mvmr",
            "sample overlap is not inferred",
        ),
    )
    adapter = RMarkdownMVMRCovarianceAdapter(
        check_manifest=check,
        adapter_manifest=adapter_manifest,
        zero_operand=zero,
        provided_operand=provided,
        role_bindings=bindings,
    )
    return ScientificCheckModule(
        manifest=check,
        declared_manifest_digest=check.manifest_digest,
        adapter_manifests=(adapter_manifest,),
        adapters=(adapter,),
    )


def _founder_orientation_profile() -> _ReportProfile:
    direct = "use_supplied_founder_alleles_directly_in_hmm_emission"
    repaired = "repair_ril_founder_orientation_before_hmm_emission"
    return _ReportProfile(
        check_id="check:founder-orientation-before-hmm-emission",
        dimension="scale_and_orientation",
        candidates=(
            _candidate(
                "repair-before-emission",
                "Repair founder orientation before emission",
                repaired,
                "Closed review choice; the check does not select it for the scientist.",
            ),
            _candidate(
                "use-supplied-orientation",
                "Use supplied founder orientation",
                direct,
                "Closed review choice; the check does not select it for the scientist.",
            ),
        ),
        semantic_roles=("founder_allele_input", "hmm_emission", "orientation_step"),
        role_bindings=(
            RoleBinding("founder_allele_input", "supplied_founder_alleles"),
            RoleBinding("hmm_emission", "founder_origin_emission"),
            RoleBinding("orientation_step", "before_emission"),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(direct),
                (
                    r"(?i)founder-origin\s+HMM\s+was\s+fitted[^.]*using\s+the\s+supplied\s+founder\s+alleles",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(repaired),
                (
                    r"(?i)founder(?:\s+(?:0/1|binary))?(?:\s+marker)?\s+alleles\s+were\s+(?:orientation-repaired|reoriented|oriented)[^.]*before\s+(?:the\s+)?(?:HMM\s+)?emissions?",
                ),
            ),
        ),
        triggers=(
            r"(?i)founder[- ]origin\s+HMM",
            r"(?i)founder(?:\s+(?:0/1|binary))?(?:\s+marker)?\s+alleles",
        ),
        question_wording=(
            "Which founder-allele orientation rule governs the HMM emission for this review?"
        ),
        extra_record_types=("file_record", "operation"),
    )


def _directional_measurement_error_profile() -> _ReportProfile:
    symmetric_average = "reported_average_as_symmetric_bidirectional_error_rate"
    directional_split = "direction_specific_error_rates_from_average_and_directional_constraint"
    authority_basis = (
        "Scientist-supplied observation-error model and identifying assumptions; the check does "
        "not infer an error direction, choose a decomposition, or treat numeric agreement as "
        "scientific authority."
    )
    return _ReportProfile(
        check_id="check:directional-measurement-error-interpretation",
        dimension="measurement_model",
        candidates=(
            _candidate(
                "symmetric-reported-average",
                "Use the reported average as the error rate in both directions",
                symmetric_average,
                authority_basis,
            ),
            _candidate(
                "direction-specific-decomposition",
                (
                    "Decompose the reported average into direction-specific error rates using "
                    "an independently supplied directional constraint"
                ),
                directional_split,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "reported_average_error_summary",
            "forward_measurement_error_rate",
            "reverse_measurement_error_rate",
            "observation_model",
        ),
        role_bindings=(
            RoleBinding(
                "reported_average_error_summary",
                "reported_average_of_two_directional_error_rates",
            ),
            RoleBinding(
                "forward_measurement_error_rate",
                "scientist_governed_direction_specific_rate",
            ),
            RoleBinding(
                "reverse_measurement_error_rate",
                "scientist_governed_direction_specific_rate",
            ),
            RoleBinding(
                "observation_model",
                "reported_primary_likelihood_or_emission_model",
            ),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(symmetric_average),
                (
                    r"(?is)\b(?:reported|supplied)\b[^.]*\baverage\s+of\s+(?:the\s+)?two\s+directional\s+(?:(?:allele[- ])?miscall|measurement[- ]error|error)\s+rates?\b",
                    r"(?is)\b(?:primary|observation|emission|likelihood|analysis|result)\b[^.]*\b(?:symmetric|exchangeable)\b[^.]*\b(?:both\s+directions|bidirectional|two[- ]way)\b[^.]*\b(?:reported|supplied)\s+(?:mean|average)\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(symmetric_average),
                (
                    r"(?is)\b(?:only\s+)?(?:the\s+)?average\s+of\s+(?:the\s+)?two\s+directional\s+(?:(?:allele[- ])?miscall|measurement[- ]error|error)\s+rates?\s+is\s+(?:available|reported|supplied)\b",
                    r"(?is)\b(?:observation|read|emission)\s+(?:model|likelihood)\b[^.]*\b(?:assum(?:e|es|ed|ing|ption)|treat(?:s|ed|ing)?)\b[^.]*\bsymmetric\s+(?:measurement[- ]errors?|miscalls?|errors?)\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(directional_split),
                (
                    r"(?is)\b(?:reported|supplied)\b[^.]*\baverage\s+of\s+(?:the\s+)?two\s+directional\s+(?:(?:allele[- ])?miscall|measurement[- ]error|error)\s+rates?\b",
                    r"(?is)\b(?:decompos(?:e|ed|ing|ition)|split)\b[^.]*\bdirection[- ]specific\s+(?:measurement[- ]error|miscall|error)\s+rates?\b",
                    r"(?is)\b(?:independent(?:ly)?\s+supplied|externally\s+supplied|stated)\b[^.]*\b(?:directional\s+constraint|baseline|error\s+floor|low[- ]direction\s+rate|high[- ]error\s+direction)\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)(?=.*\baverage\s+of\s+(?:the\s+)?two\s+directional\b)(?=.*\b(?:(?:allele[- ])?miscall|measurement[- ]error|error)\s+rates?\b)",
            r"(?is)(?=.*\bdirection[- ]specific\s+(?:measurement[- ]error|miscall|error)\s+rates?\b)(?=.*\b(?:symmetric|decompos|error\s+floor|directional\s+constraint)\b)",
        ),
        question_wording=(
            "Which interpretation of the reported average directional measurement error "
            "governs the observation model for this review?"
        ),
    )


def _ancestry_exposure_profile() -> _ReportProfile:
    full = "full_chromosome_map_exposure"
    called = "high_confidence_called_tract_exposure_only"
    return _ReportProfile(
        check_id="check:full-map-ancestry-exposure",
        dimension="time_definition",
        candidates=(
            _candidate(
                "full-map-exposure",
                "Use full chromosome-map exposure for pulse timing",
                full,
                "Closed review choice; the check does not establish the governing time definition.",
            ),
            _candidate(
                "called-tract-exposure",
                "Use retained called-tract exposure for pulse timing",
                called,
                "Closed review choice; the check does not establish the governing time definition.",
            ),
        ),
        semantic_roles=("pulse_likelihood", "pulse_time_exposure", "transition_count"),
        role_bindings=(
            RoleBinding("pulse_likelihood", "two_state_switch_process"),
            RoleBinding("pulse_time_exposure", "pulse_time_denominator"),
            RoleBinding("transition_count", "N_switch"),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(called),
                (
                    r"(?i)pulse[- ]time\s+transition\s+exposure\s+uses\s+only\s+(?:the\s+)?retained\s+callable\s+A[- ]plus[- ]B\s+length",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(called),
                (
                    r"(?is)\bmap\s+file\b[^.]*\bused\s+to\s+validate\b[^.]*\b(?:chromosome\s+membership|bounds)\b",
                    r"(?is)\bunrepresented\s+map\s+length\b[^.]*\bnot\b[^.]*\btime[- ]model\s+exposure\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(called),
                (
                    r"(?i)single[- ]pulse[^.]*two[- ]state\s+ancestry\s+process",
                    r"(?i)t\s*=\s*N[_ ]?switch\s*/\s*\(\s*\(\s*1\s*-\s*m\s*\)\s*L_A\s*\+\s*m\s*L_B\s*\)",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(full),
                (
                    r"(?i)(?:transition|pulse[- ]time)\s+exposure\s+used\s+(?:the\s+)?(?:complete|full)\s+(?:chromosome|genetic)[- ]map\s+length",
                    r"(?i)t\s*=\s*N[_ ]?switch\s*/\s*\(\s*2\s*m\s*\(\s*1\s*-\s*m\s*\)\s*L[_ ]?map\s*\)",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(full),
                (
                    r"(?i)pulse[- ]time\s+transition\s+exposure\s+uses\s+(?:the\s+)?(?:complete|full)\s+(?:chromosome|genetic)[- ]map\s+length",
                ),
            ),
        ),
        triggers=(
            r"(?i)single[- ]pulse[^.]*two[- ]state\s+ancestry\s+process",
            r"(?i)(?:transition|pulse[- ]time)\s+exposure",
            r"(?i)pulse[- ]time\s+transition\s+exposure",
            r"(?i)time[- ]model\s+exposure",
            r"(?i)t\s*=\s*N[_ ]?switch\s*/",
        ),
        question_wording=(
            "Which chromosome-length exposure definition governs pulse timing for this review?"
        ),
        check_version="1.1.0",
        adapter_version="1.1.0",
    )


def _transition_path_continuity_profile() -> _ReportProfile:
    preserve = "preserve_within_sequence_path_across_unobserved_intervals"
    terminate = "terminate_path_at_unobserved_or_filtered_intervals"
    authority_basis = (
        "Scientist-supplied dependence model for missing or filtered intervals; the check does "
        "not infer hidden states, choose a path treatment, or treat numeric agreement as "
        "scientific authority."
    )
    return _ReportProfile(
        check_id="check:within-sequence-transition-path-continuity",
        dimension="dependence_structure",
        candidates=(
            _candidate(
                "preserve-path-across-unobserved-intervals",
                "Preserve the within-sequence path across retained-data gaps",
                preserve,
                authority_basis,
            ),
            _candidate(
                "terminate-path-at-unobserved-intervals",
                "Terminate the within-sequence path at retained-data gaps",
                terminate,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "transition_process",
            "retained_state_sequence",
            "unobserved_interval",
            "path_boundary",
        ),
        role_bindings=(
            RoleBinding("transition_process", "finite_state_transition_or_switch_process"),
            RoleBinding("retained_state_sequence", "ordered_retained_state_observations"),
            RoleBinding("unobserved_interval", "missing_masked_filtered_or_uncalled_interval"),
            RoleBinding("path_boundary", "within_sequence_continuity_rule"),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(preserve),
                (
                    r"(?is)\b(?:transitions?|switch(?:es)?)\b[^.]*\b(?:successive|adjacent)\b[^.]*\b(?:callable|eligible|retained)\b[^.]*\b(?:chromosome|sequence|trajectory)\b",
                    r"(?is)(?:\bincluding\s+across\b[^.]*\b(?:masked|uncalled|missing|filtered|unobserved)\b|\b(?:masked|uncalled|missing|filtered|unobserved)\b[^.]*\b(?:did\s+not|do\s+not|does\s+not)\b[^.]*\b(?:terminate|break)\b[^.]*\b(?:path|sequence|trajectory)\b)",
                    r"(?is)\b(?:chromosome|sequence|trajectory)\s+(?:ends?|boundaries)\b[^.]*\bremain(?:ed)?\b[^.]*\bboundar",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(terminate),
                (
                    r"(?is)\b(?:transitions?|switch(?:es)?)\b[^.]*\bonly\b[^.]*\b(?:touching|contiguous)\b[^.]*\b(?:callable|eligible|retained)\b[^.]*\bboundar",
                    r"(?is)\b(?:masked|uncalled|missing|filtered|unobserved|gaps?)\b[^.]*\b(?:terminate|break)\b[^.]*\b(?:path|observation|sequence|trajectory)\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(terminate),
                (
                    r"(?is)\b(?:transitions?|switch(?:es)?)\b[^.]*\bonly\b[^.]*\b(?:callable|eligible|retained)\b[^.]*\b(?:touching|contiguous)\b[^.]*\bboundar",
                    r"(?is)\b(?:masked|uncalled|missing|filtered|unobserved|gaps?)\b[^.]*\b(?:terminate|break)\b[^.]*\b(?:path|observation|sequence|trajectory)\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(terminate),
                (
                    r"(?is)\b(?:transitions?|switch(?:es)?)\b[^.]*\bonly\b[^.]*\b(?:touching|contiguous)\b[^.]*\b(?:callable|eligible|retained)\b[^.]*\bboundar",
                    r"(?is)\bgaps?\b[^.]*\bterminate\b[^.]*\b(?:callable|retained|observation)\s+block\b",
                    r"(?is)\bcontribute\s+neither\b[^.]*\btransition\b[^.]*\bexposure\b[^.]*\bconnecting\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)\b(?:transitions?|switch(?:es)?)\b[^.]*\b(?:successive|adjacent|touching|contiguous)\b[^.]*\b(?:callable|eligible|retained)\b",
            r"(?is)\b(?:masked|uncalled|missing|filtered|unobserved|gaps?)\b[^.]*\b(?:terminate|break)\b[^.]*\b(?:path|observation|sequence|trajectory)\b",
        ),
        question_wording=(
            "Should the within-sequence transition path continue across retained-data gaps for "
            "this review?"
        ),
    )


def _phase_split_mvmr_instrument_profile() -> _ReportProfile:
    conditional = "phase1_ld_conditional_signal_union_with_phase2_joint_coefficients"
    marginal = "phase1_marginal_signal_union_with_phase2_marginal_coefficients"
    authority_basis = (
        "Scientist-supplied instrument-construction and LD-identification policy; the check does "
        "not choose a signal representation, validate instruments, infer winner's-curse control, "
        "or use numeric agreement as scientific authority."
    )
    return _ReportProfile(
        check_id="check:phase-split-mvmr-instrument-construction",
        dimension="measurement_model",
        candidates=(
            _candidate(
                "phase1-ld-conditional-signals-phase2-joint-coefficients",
                (
                    "Select the phase-1 union of LD-conditional signals and use matching "
                    "phase-2 joint coefficients"
                ),
                conditional,
                authority_basis,
            ),
            _candidate(
                "phase1-marginal-signal-union-phase2-marginal-coefficients",
                (
                    "Select the phase-1 marginal-association union and use matching phase-2 "
                    "marginal coefficients"
                ),
                marginal,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "phase1_exposure_screen",
            "ld_signal_representation",
            "selected_instrument_union",
            "phase2_exposure_design",
        ),
        role_bindings=(
            RoleBinding("phase1_exposure_screen", "reported_screening_associations"),
            RoleBinding(
                "ld_signal_representation",
                "reported_marginal_or_ld_conditional_signal_definition",
            ),
            RoleBinding("selected_instrument_union", "reported_union_across_exposures"),
            RoleBinding(
                "phase2_exposure_design",
                "scientist_governed_holdout_coefficient_representation",
            ),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(conditional),
                (
                    r"(?i)\bunion\s+of\s+phase[- ]1\s+LD[- ]conditional\s+joint[- ]effect\s+signals\b",
                    r"(?i)\bphase[- ]2\s+joint\s+exposure\s+coefficients\b[^.]*\b(?:matching\s+)?joint\s+disease\s+coefficients\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(conditional),
                (
                    r"(?i)\bphase[- ]1\s+conditional\s+p\b.{0,180}\btook\s+the\s+union\s+across\s+(?:proteins?|exposures?)\b",
                    r"(?i)\bexposure\s+matrix\s+used\s+the\s+matching\s+phase[- ]2\s+joint\s+coefficients\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(marginal),
                (
                    r"(?i)\bunion\s+of\s+phase[- ]1\s+marginal[- ]association\s+signals\b",
                    r"(?i)\bphase[- ]2\s+marginal\s+exposure\s+coefficients\b[^.]*\bmarginal\s+disease\s+coefficients\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)(?=.*\b(?:MVMR|multivariable\s+Mendelian[- ]randomization)\b)(?=.*\bphase[- ]1\b)(?=.*\bphase[- ]2\b)(?=.*\b(?:marginal|LD[- ]conditional|joint[- ]effect)\b)",
        ),
        question_wording=(
            "Which phase-split instrument construction governs the multivariable MR effect for "
            "this review?"
        ),
    )


def _mvmr_heterogeneity_estimator_profile() -> _ReportProfile:
    generalized_gls = "zero_intercept_generalized_ivw_or_gls"
    robust_whitened = "redescending_robust_m_estimator_on_ld_whitened_innovations"
    authority_basis = (
        "Scientist-supplied residual-heterogeneity and invalid-instrument policy; the check does "
        "not choose an estimator, establish instrument validity, diagnose pleiotropy, or use "
        "numeric agreement as scientific authority."
    )
    return _ReportProfile(
        check_id="check:mvmr-residual-heterogeneity-estimator",
        dimension="dependence_structure",
        candidates=(
            _candidate(
                "zero-intercept-generalized-ivw-or-gls",
                "Use a zero-intercept generalized IVW or full-covariance GLS estimator",
                generalized_gls,
                authority_basis,
            ),
            _candidate(
                "redescending-robust-estimator-on-ld-whitened-innovations",
                (
                    "Use a redescending robust M-estimator on LD-covariance-whitened residual "
                    "innovations"
                ),
                robust_whitened,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "multivariable_exposure_design",
            "outcome_association_covariance",
            "residual_heterogeneity",
            "primary_effect_estimator",
        ),
        role_bindings=(
            RoleBinding(
                "multivariable_exposure_design",
                "reported_multivariable_mr_exposure_coefficients",
            ),
            RoleBinding(
                "outcome_association_covariance",
                "reported_full_ld_or_whitened_covariance",
            ),
            RoleBinding("residual_heterogeneity", "reported_instrument_residual_behavior"),
            RoleBinding(
                "primary_effect_estimator",
                "scientist_governed_heterogeneity_response",
            ),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(generalized_gls),
                (
                    r"(?is)##[ \t]+(?:primary[ \t]+)?estimator[ \t]*\r?\n(?:[ \t]*\r?\n)?[^#]{0,1200}?\bzero[- ]intercept\s+(?:generalized\s+IVW\s+estimator|generalized\s+least\s+squares|GLS)\b",
                ),
                match_scope="document",
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(robust_whitened),
                (
                    r"(?is)##[ \t]+(?:primary[ \t]+)?estimator[ \t]*\r?\n(?:[ \t]*\r?\n)?[^#]{0,1200}?\b(?:redescending\s+)?Tukey[- ]biweight\s+M-(?:estimator|regression)\b.{0,180}\bon\s+(?:lower[- ])?Cholesky[- ]whitened\s+(?:disease\s+)?residual\s+innovations\b",
                ),
                match_scope="document",
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(robust_whitened),
                (
                    r"(?is)\bprimary\s+LD[- ]aware\s+robust\s+multivariable\s+estimate\b.{0,2400}\b(?:redescending\s+)?Tukey[- ]biweight\s+M-(?:estimator|regression)\b.{0,180}\bon\s+(?:lower[- ])?Cholesky[- ]whitened\s+(?:disease\s+)?residual\s+innovations\b",
                ),
                match_scope="document",
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(robust_whitened),
                (
                    r"(?i)\bordinary\s+correlated\s+GLS\s+fit\s+showed\s+overwhelming\s+lack\s+of\s+fit\b",
                    r"(?i)\bI\s+used\s+a\s+redescending\s+Tukey(?:-|\s+)biweight\s+M-estimator\s+on\s+Cholesky[- ]whitened\s+residual\s+innovations\b",
                    r"(?i)\bpreserves\s+the\s+LD\s+covariance\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)(?=.*\b(?:MVMR|multivariable\s+Mendelian[- ]randomization|multivariable\s+MR)\b)(?=.*\b(?:zero[- ]intercept|Tukey[- ]biweight)\b)(?=.*\b(?:LD|covariance|Cholesky[- ]whitened)\b)",
        ),
        question_wording=(
            "Which residual-heterogeneity estimator governs the multivariable MR effect for this "
            "review?"
        ),
    )


def _ld_whitening_profile() -> _ReportProfile:
    whitened = "ld_covariance_cholesky_whitening_before_robust_fit"
    unwhitened = "diagonal_or_unwhitened_robust_fit"
    return _ReportProfile(
        check_id="check:ld-covariance-whitening-before-robust-fit",
        dimension="measurement_model",
        candidates=(
            _candidate(
                "ld-whiten-before-robust-fit",
                "Whiten by LD covariance before robust fitting",
                whitened,
                "Closed review choice; it does not certify this as universally correct.",
            ),
            _candidate(
                "unwhitened-robust-fit",
                "Use an unwhitened or diagonal robust fit",
                unwhitened,
                "Closed review choice; it does not certify this as universally correct.",
            ),
        ),
        semantic_roles=("ld_covariance", "residual_innovations", "robust_fit"),
        role_bindings=(
            RoleBinding("ld_covariance", "supplied_variant_correlation"),
            RoleBinding("residual_innovations", "cholesky_whitened"),
            RoleBinding("robust_fit", "redescending_m_estimator"),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(whitened),
                (
                    r"(?i)Tukey\s+biweight\s+M-estimator\s+on\s+Cholesky-whitened\s+residual\s+innovations",
                    r"(?i)preserves\s+the\s+LD\s+covariance",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(whitened),
                (
                    r"(?i)\b(?:zero[- ]intercept\s+)?Tukey[- ]biweight\s+M-regression\b.{0,160}\bon\s+(?:lower[- ])?Cholesky[- ]whitened\s+(?:disease\s+)?residual\s+innovations\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(unwhitened),
                (
                    r"(?i)(?:robust|M-estimator)[^.]*\b(?:unwhitened|diagonal-weighted)\b[^.]*residual",
                    r"(?i)LD\s+covariance[^.]*\b(?:omitted|ignored|not\s+used)\b",
                ),
            ),
        ),
        triggers=(r"(?i)robust", r"(?i)Cholesky-whitened", r"(?i)LD\s+covariance"),
        question_wording=(
            "Which LD-covariance treatment governs the robust multivariable fit for this review?"
        ),
        check_version="1.1.0",
        adapter_version="1.1.0",
    )


def _poststratified_misclassification_profile() -> _ReportProfile:
    aggregate_first = "aggregate_observed_distribution_then_joint_calibration"
    constrained_cellwise = "constrained_joint_calibration_within_each_poststratum_then_standardize"
    return _ReportProfile(
        check_id="check:poststratified-misclassification-estimator",
        dimension="measurement_model",
        candidates=(
            _candidate(
                "aggregate-then-joint-calibration",
                "Standardize observed class distributions, then jointly calibrate the aggregate",
                aggregate_first,
                (
                    "Scientist-supplied estimand and constraint policy; the check does not select "
                    "an estimator or treat an answer key as scientific authority."
                ),
            ),
            _candidate(
                "constrained-cellwise-calibration-then-standardize",
                (
                    "Jointly estimate feasible class probabilities within each post-stratum, "
                    "then standardize"
                ),
                constrained_cellwise,
                (
                    "Scientist-supplied estimand and constraint policy; the check does not select "
                    "an estimator or treat an answer key as scientific authority."
                ),
            ),
        ),
        semantic_roles=(
            "mutually_exclusive_class_distribution",
            "misclassification_mapping",
            "target_population_poststrata",
            "probability_constraint_scope",
        ),
        role_bindings=(
            RoleBinding(
                "mutually_exclusive_class_distribution",
                "observed_class_or_call_distribution",
            ),
            RoleBinding(
                "misclassification_mapping",
                "control_derived_joint_calibration_matrix",
            ),
            RoleBinding(
                "target_population_poststrata",
                "standardization_cells_and_weights",
            ),
            RoleBinding(
                "probability_constraint_scope",
                "scientist_governed_estimator_choice",
            ),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(aggregate_first),
                (
                    r"(?i)\b(?:directly\s+)?standardized[^.]*\b(?:observed|completed-test)\b[^.]*\b(?:assay[- ]?)?(?:call|class)\s+distributions?\b",
                    r"(?i)\bthen\s+(?:jointly\s+)?(?:deconvolved|inverted)[^.]*\bstandardized\s+(?:(?:call|class)\s+)?distributions?\b[^.]*\b(?:calibration|confusion|control)\s+(?:matrix|matrices)\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(constrained_cellwise),
                (
                    r"(?i)\b(?:nonnegative|simplex|probability)[- ]constrained\s+(?:joint\s+)?(?:calibration|deconvolution|class(?:-prevalence)?\s+estimation)\b",
                    r"(?i)\b(?:within|inside|for)\s+each\s+(?:target-population\s+)?(?:post-?strat(?:ification\s+)?cell|post-?stratum|cell)\b",
                    r"(?i)\b(?:then|before)\s+(?:standardiz(?:ed|ing)|post-?stratif(?:ied|ying)|weight(?:ed|ing)|aggregat(?:ed|ing))\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)(?=.*\bstandardized[^.]*\b(?:observed|completed-test)\b[^.]*\b(?:call|class)\s+distributions?\b)(?=.*\b(?:deconvol|invert)[^.]*\b(?:matrix|matrices)\b)",
            r"(?is)(?=.*\b(?:nonnegative|simplex|probability)[- ]constrained\b)(?=.*\b(?:post-?strat|standardiz)\b)(?=.*\b(?:calibrat|deconvol)\b)",
        ),
        question_wording=(
            "Which joint misclassification-calibration estimator governs the target-population "
            "class frequencies for this review?"
        ),
    )


def _posttreatment_missingness_strategy_profile() -> _ReportProfile:
    sequential_imputation = "sequential_outcome_imputation_conditioning_on_posttreatment_endpoint"
    baseline_ipcw = "assessment_weighting_excluding_posttreatment_endpoint_from_missingness_model"
    authority_basis = (
        "Scientist-supplied estimand, temporal ordering, and missingness assumptions; the check "
        "does not decide whether conditioning on a post-treatment endpoint is appropriate, infer "
        "causal identification, or use numeric agreement as scientific authority."
    )
    return _ReportProfile(
        check_id="check:posttreatment-missingness-strategy",
        dimension="missingness_and_transport",
        candidates=(
            _candidate(
                "sequential-imputation-with-posttreatment-endpoint",
                (
                    "Use sequential outcome imputation that conditions on an observed "
                    "post-treatment endpoint and integrates its treatment-specific distribution"
                ),
                sequential_imputation,
                authority_basis,
            ),
            _candidate(
                "assessment-weighting-without-posttreatment-endpoint",
                (
                    "Use assessment or censoring weights that exclude the observed "
                    "post-treatment endpoint from the missingness model"
                ),
                baseline_ipcw,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "treatment_assignment",
            "posttreatment_endpoint",
            "later_outcome_observation",
            "missing_outcome_transport_model",
        ),
        role_bindings=(
            RoleBinding("treatment_assignment", "reported_treatment_indicator"),
            RoleBinding(
                "posttreatment_endpoint",
                "reported_intermediate_endpoint_or_mediator",
            ),
            RoleBinding(
                "later_outcome_observation",
                "reported_assessment_or_censoring_indicator",
            ),
            RoleBinding(
                "missing_outcome_transport_model",
                "scientist_governed_missingness_strategy",
            ),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(sequential_imputation),
                (
                    r"(?i)\b(?:assessed[- ]case\s+)?outcome\s+model\b[^.]*\b(?:observed\s+)?(?:week[- ]?\d+\s+)?(?:toxicity|adverse\s+event|intermediate\s+endpoint|mediator)\b",
                    r"(?i)\bmissing\s+(?:week[- ]?\d+\s+)?outcomes?\b[^.]*\bimput(?:ed|ation)\b",
                    r"(?is)(?=.*\b(?:toxicity|adverse\s+event|intermediate\s+endpoint|mediator)\b)(?=.*\bintegrat(?:ed|ing)\b)(?=.*\btreatment[- ]specific\s+distribution\b)",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(baseline_ipcw),
                (
                    r"(?i)\b(?:assessment|censoring|missingness)\s+model\b[^.]*\bexclud(?:e|es|ed|ing)\b[^.]*\b(?:observed\s+)?(?:week[- ]?\d+\s+)?(?:toxicity|adverse\s+event|intermediate\s+endpoint|mediator)\b",
                    r"(?i)\b(?:after\s+|post[- ]?)treatment\b",
                    r"(?i)\b(?:IPCW|inverse\s+probability\s+(?:of\s+)?(?:censoring|assessment)\s+weight(?:ing|s)?)\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(baseline_ipcw),
                (
                    r"(?is)\b(?:primary(?:\s+missing[- ]outcome)?\s+(?:strategy|estimator|analysis)|evaluator[- ]owned\s+ablation)\b.{0,360}\b(?:observed\s+)?(?:week[- ]?\d+\s+)?(?:toxicity|adverse\s+event|intermediate\s+endpoint|mediator)\b[^.]{0,240}\b(?:deliberately\s+)?exclud(?:e|es|ed|ing)\b[^.]{0,180}\b(?:every\s+)?assessment[- ]model\s+predictor\s+set\b",
                    r"(?i)\b(?:after\s+|post[- ]?)treatment\b",
                    r"(?i)\binverse[- ]assessment\s+(?:residual\s+correction|weight(?:ing|s)?)\b[^.]{0,240}\btransport(?:s|ed|ing)?\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)(?=.*\bmissing\s+(?:week[- ]?\d+\s+)?outcomes?\b)(?=.*\b(?:toxicity|adverse\s+event|intermediate\s+endpoint|mediator)\b)(?=.*\b(?:imput|assessment|censor|IPCW)\b)",
            r"(?is)(?=.*\b(?:assessment|censoring|missingness)\s+model\b)(?=.*\b(?:after\s+|post[- ]?)treatment\b)(?=.*\b(?:toxicity|adverse\s+event|intermediate\s+endpoint|mediator)\b)",
            r"(?is)(?=.*\bsensitivity\s+analysis\b)(?=.*\b(?:after\s+|post[- ]?)treatment\b)(?=.*\binverse[- ]assessment\b)(?=.*\bprimary\s+missing[- ]outcome\s+strategy\b)",
        ),
        question_wording=(
            "Which missing-outcome transport strategy governs the treatment-effect estimate for "
            "this review?"
        ),
        check_version="1.1.0",
        adapter_version="1.1.0",
    )


def _somatic_clonality_representation_profile() -> _ReportProfile:
    copy_ceiling = "direct_local_copy_number_ceiling_for_target_eligibility"
    adjusted_clonality = "purity_copy_adjusted_clonal_fraction_window_for_target_eligibility"
    authority_basis = (
        "Scientist-supplied somatic target definition, alteration-multiplicity assumptions, and "
        "clonality policy; the check does not choose thresholds, infer target status, or treat an "
        "answer key as scientific authority."
    )
    return _ReportProfile(
        check_id="check:somatic-clonality-representation",
        dimension="target_population",
        candidates=(
            _candidate(
                "direct-local-copy-number-ceiling",
                "Use a direct local copy-number ceiling as the target-eligibility gate",
                copy_ceiling,
                authority_basis,
            ),
            _candidate(
                "purity-copy-adjusted-clonal-fraction-window",
                (
                    "Use a purity/copy-adjusted clonal-fraction window as the "
                    "target-eligibility gate"
                ),
                adjusted_clonality,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "somatic_variant_signal",
            "tumor_purity",
            "local_copy_number",
            "target_clonality_gate",
        ),
        role_bindings=(
            RoleBinding("somatic_variant_signal", "reported_variant_molecule_fraction"),
            RoleBinding("tumor_purity", "reported_tumor_fraction"),
            RoleBinding("local_copy_number", "reported_locus_copy_state"),
            RoleBinding(
                "target_clonality_gate",
                "scientist_governed_target_eligibility_representation",
            ),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(copy_ceiling),
                (
                    r"(?is)\btarget\s+(?:membership|eligibility|population)\b[^.]*\b(?:determined|defined|used|uses|retains|required)\b(?=.*\b(?:local\s+)?(?:total\s+)?copy(?:\s+number)?\b[^.]*\b(?:below|less\s+than|ceiling|<)\b)",
                    r"(?i)\b(?:somatic|structural|SV|variant|breakpoint)\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(adjusted_clonality),
                (
                    r"(?is)\btarget\s+(?:membership|eligibility|population)\b[^.]*\b(?:determined|defined|used|uses|retains|required)\b(?=.*\b(?:purity[/-]copy[- ]adjusted|purity[- ]and[- ]copy[- ]adjusted)\b)",
                    r"(?i)\b(?:single[- ]copy\s+)?(?:CCF|cancer[- ]cell\s+fraction|clonal[- ]fraction)\b[^.]*\b(?:window|range|from|between|in\s*\[)\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(adjusted_clonality),
                (
                    r"(?is)\b(?:evaluator[- ]frozen\s+`?reference[-_ ]target`?|(?:prespecified|predefined)\s+primary[- ]target\s+eligibility\s+rule)\b[^.]{0,120}\b(?:then\s+)?requires?\b[^.]{0,240}\b(?:purity[/-]copy[- ]adjusted|purity[- ]and[- ]copy[- ]adjusted)\b",
                    r"(?i)\b(?:single[- ]copy\s+)?(?:CCF|cancer[- ]cell\s+fraction|clonal[- ]fraction)\b[^.]*\b(?:window|range|from|between|in\s*\[)\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)(?=.*\btarget\s+(?:membership|eligibility|population)\b)(?=.*\b(?:local\s+)?(?:total\s+)?copy(?:\s+number)?\b)(?=.*\b(?:somatic|structural|SV|variant|breakpoint)\b)",
            r"(?is)(?=.*\btarget\s+(?:membership|eligibility|population)\b)(?=.*\b(?:purity[/-]copy[- ]adjusted|purity[- ]and[- ]copy[- ]adjusted)\b)(?=.*\b(?:CCF|cancer[- ]cell\s+fraction|clonal[- ]fraction)\b)",
        ),
        question_wording=(
            "Which clonality representation governs somatic target eligibility for this review?"
        ),
        check_version="1.1.0",
        adapter_version="1.1.0",
    )


def _direct_standardization_conditioning_set_profile() -> _ReportProfile:
    include_availability = "include_named_availability_variables_in_direct_standardization_cells"
    substantive_only = "substantive_risk_strata_only_with_availability_variables_diagnostic"
    authority_basis = (
        "Scientist-supplied target-population exchangeability, outcome-relationship, and "
        "positivity assumptions; predicting measurement availability alone neither mandates nor "
        "forbids including a variable in direct-standardization cells."
    )
    return _ReportProfile(
        check_id="check:direct-standardization-conditioning-set",
        dimension="target_population",
        candidates=(
            _candidate(
                "include-named-availability-variables",
                (
                    "Include the specifically named testing-availability variables in the "
                    "standardization cells together with the declared substantive risk strata"
                ),
                include_availability,
                authority_basis,
            ),
            _candidate(
                "substantive-risk-strata-only",
                (
                    "Standardize only over the declared substantive risk strata and keep the "
                    "named availability variables diagnostic-only"
                ),
                substantive_only,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "completed_or_measured_rows",
            "full_target_roster",
            "substantive_risk_strata",
            "testing_availability_variables",
            "direct_standardization_cells",
        ),
        role_bindings=(
            RoleBinding("completed_or_measured_rows", "reported_measured_subset"),
            RoleBinding("full_target_roster", "reported_target_population"),
            RoleBinding("substantive_risk_strata", "reported_risk_conditioning_set"),
            RoleBinding(
                "testing_availability_variables",
                "reported_included_or_diagnostic_only_variables",
            ),
            RoleBinding(
                "direct_standardization_cells",
                "scientist_governed_conditioning_set",
            ),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(include_availability),
                (
                    r"(?i)\b(?:(?:directly\s+)?standardized\b[^.]*\bcompleted[- ]test\s+(?:call\s+)?distributions?|completed[- ]test\s+(?:call\s+)?distributions?\s+(?:were\s+)?(?:directly\s+)?standardized)\b",
                    r"(?i)\b(?:family[- ]history(?:\s+tier)?|substantive\s+risk\s+strata?)\b[^.]*\b(?:intake\s+)?site\b[^.]*\b(?:collection\s+)?wave\b",
                    r"(?i)\b(?:full[- ]roster|target[- ]population)\s+(?:cell\s+)?(?:proportions|counts|weights)\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(substantive_only),
                (
                    r"(?i)\bcompleted\s+(?:partners?|rows?|participants?)\b[^.]*\b(?:analy[sz]ed|standardized)\b[^.]*\b(?:ancestry|substantive\s+risk)\b[^.]*\bfamily[- ]history(?:\s+tier)?\b[^.]*\bstandardized\b[^.]*\b(?:full\s+roster|roster\s+rows?|target\s+population)\b",
                    r"(?i)\b(?:site|center)\b[^.]*\b(?:wave|period)\b[^.]*\b(?:testing|measurement)[- ]selection\s+variables?\b[^.]*\bnot\s+(?:biological\s+)?(?:prevalence|outcome|risk)\s+predictors?\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)(?=.*\b(?:standardized|direct\s+standardization)\b)(?=.*\bcompleted(?:[- ]test|\s+(?:rows?|partners?|participants?))\b)(?=.*\b(?:full[- ]roster|target[- ]population)\b)(?=.*\b(?:site|center)\b)(?=.*\b(?:wave|period)\b)",
        ),
        question_wording=(
            "Which conditioning set governs direct standardization from completed rows to the "
            "full target roster for this review?"
        ),
    )


def _classifier_copy_dosage_profile() -> _ReportProfile:
    hard_call = "integer_hard_copy_state_as_numeric_dosage"
    expected_dosage = "continuous_posterior_expected_copy_dosage"
    direct_dosage = "direct_continuous_calibrated_copy_dosage"
    authority_basis = (
        "Scientist-supplied exposure estimand and measurement-uncertainty policy; the check does "
        "not choose a representation or treat an answer key as scientific authority."
    )
    return _ReportProfile(
        check_id="check:classifier-derived-copy-dosage-representation",
        dimension="measurement_model",
        candidates=(
            _candidate(
                "integer-hard-copy-state",
                "Use the predicted integer copy state as numeric dosage",
                hard_call,
                authority_basis,
            ),
            _candidate(
                "continuous-posterior-expected-copy-dosage",
                "Use posterior expected copy count as continuous dosage",
                expected_dosage,
                authority_basis,
            ),
            _candidate(
                "direct-continuous-calibrated-copy-dosage",
                "Use direct continuous copy-calibration predictions as dosage",
                direct_dosage,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "copy_state_calibration_labels",
            "calibration_model_output",
            "quantitative_copy_dosage",
            "downstream_model_exposure",
        ),
        role_bindings=(
            RoleBinding("copy_state_calibration_labels", "ordered_integer_copy_states"),
            RoleBinding(
                "calibration_model_output",
                "hard_state_posterior_expectation_or_direct_continuous_prediction",
            ),
            RoleBinding("quantitative_copy_dosage", "reported_full_cohort_representation"),
            RoleBinding("downstream_model_exposure", "scientist_governed_representation"),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(hard_call),
                (
                    r"(?i)\b(?:primary|full-cohort|downstream)[^.]*\b(?:used|entered|treated)\b[^.]*\b(?:integer|discrete)\s+hard[- ]call(?:ed)?\b[^.]*\b(?:copy\s+)?(?:state|count|dosage)\b",
                    r"(?i)\bhard[- ]call(?:ed)?\s+(?:copy\s+)?(?:state|count)\b[^.]*\b(?:used|entered|treated)\b[^.]*\b(?:numeric|quantitative)?\s*(?:copy\s+)?dosage\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(expected_dosage),
                (
                    r"(?i)\b(?:continuous\s+)?posterior\s+expected\s+(?:copy\s+)?(?:count|dosage)\b",
                    r"(?i)P\s*\(\s*copy\s*=\s*1\s*\)\s*\+\s*2\s*\*\s*P\s*\(\s*copy\s*=\s*2\s*\)",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(direct_dosage),
                (
                    r"(?i)\b(?:primary|full[- ]cohort|downstream)[^.]*\bcontinuous\s+calibrated\s+(?:copy\s+)?dosage\b",
                    r"(?i)\b(?:linear|ridge(?:cv)?|regression)\b[^.]*\b(?:models?|calibrat(?:ion|ors?))\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(direct_dosage),
                (
                    r"(?is)\bretained\s+the\s+continuous\s+copy\s+index\s+for\s+dosage\s+calibration\b[^.]{0,400}\brather\s+than\s+round(?:ing)?\b(?=.{0,2400}(?<![A-Za-z0-9_-])(?P<copy_target>[A-Za-z][A-Za-z0-9_-]{0,63})\s+copy\s+index\s+was\s+learned\b)(?=.{0,3200}\bridge\s+regression\b).{0,5000}?\b(?:model|association|regression)\b[^.]{0,800}\b(?:included|used|entered)\b[^.]{0,800}\bcalibrated\s+(?P=copy_target)\s+(?:copy\s+)?dosage\b",
                ),
                match_scope="document",
            ),
        ),
        triggers=(
            r"(?i)\bposterior\s+expected\s+(?:copy\s+)?(?:count|dosage)\b",
            r"(?is)(?=.*\bhard[- ]call)(?=.*\bcopy\b)(?=.*\bdosage\b)",
            r"(?is)(?=.*\bclassifier\b[^.]*\bpredicted\b[^.]*\bcopy\s+(?:count|state)\b)(?=.*\b(?:copy\s+)?dosage\b)",
            r"(?is)(?=.*\bcontinuous\s+calibrated\s+(?:copy\s+)?dosage\b)(?=.*\b(?:linear|ridge(?:cv)?|regression)\b)",
            r"(?is)(?=.*\bretained\s+the\s+continuous\s+copy\s+index\s+for\s+dosage\s+calibration\b)(?=.*\bridge\s+regression\b)",
        ),
        question_wording=(
            "Which calibrated copy-number representation governs the quantitative "
            "exposure for this review?"
        ),
        check_version="1.2.0",
        adapter_version="1.2.0",
    )


def _recoverable_technical_group_profile() -> _ReportProfile:
    include_group = "include_recovered_technical_group_covariate"
    omit_group = "omit_unobserved_or_unlinked_technical_group_covariate"
    authority_basis = (
        "Scientist-supplied adjustment set and acceptance of the data-derived grouping rule; the "
        "check does not select a covariate or treat an answer key as scientific authority."
    )
    return _ReportProfile(
        check_id="check:recoverable-technical-group-adjustment",
        dimension="adjustment_set",
        candidates=(
            _candidate(
                "include-recovered-technical-group",
                "Include the recovered technical group as an association covariate",
                include_group,
                authority_basis,
            ),
            _candidate(
                "omit-unobserved-or-unlinked-technical-group",
                "Do not reconstruct or include an unobserved technical group",
                omit_group,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "negative_control_or_contamination_signal",
            "unit_level_technical_summary",
            "recovered_technical_group",
            "primary_association_adjustment_set",
        ),
        role_bindings=(
            RoleBinding(
                "negative_control_or_contamination_signal",
                "reported_technical_proxy_source",
            ),
            RoleBinding(
                "unit_level_technical_summary",
                "reported_grouping_input",
            ),
            RoleBinding(
                "recovered_technical_group",
                "included_or_explicitly_not_reconstructed",
            ),
            RoleBinding(
                "primary_association_adjustment_set",
                "scientist_governed_covariate_choice",
            ),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(include_group),
                (
                    r"(?i)\b(?:reconstruct(?:ed)?|recover(?:ed)?)\b[^.]*\b(?:donor-level\s+)?technical[- ]group\b[^.]*\b(?:mean|average)\b[^.]*\b(?:ambient|contamination|negative-control)\b",
                    r"(?i)\b(?:included|entered|adjusted)\b[^.]*\b(?:technical[- ]group|recovered\s+group)\b[^.]*\b(?:categorical\s+)?covariate\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(include_group),
                (
                    r"(?is)\b(?:ambient|contamination|soup|negative[- ]control|technical[- ]proxy)\b[^.]{0,240}\b(?:estimates?|fractions?|rates?|summar(?:y|ies))\b[^.]{0,240}\b(?:separat(?:ed|ion)|split|cluster(?:ed|ing)|gap|threshold)\b.{0,400}\breconstruct(?:ed)?\s+that\b[^.]{0,160}\btechnical[- ]group\b[^.]{0,200}\bincluded\s+it\s+as\s+(?:a\s+)?(?:categorical\s+)?covariate\s+in\s+the\s+primary(?:\s+association)?\s+model\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(omit_group),
                (
                    r"(?is)\bno\b[^.]*\b(?:ambient[- ]group|technical[- ]group)\b[^.]*\bdirectly\s+observed\b.*?\bnone\s+is\s+reconstructed\b",
                    r"(?i)\bno\b[^.]*\b(?:ambient[- ]group|technical[- ]group)\s+covariate\b[^.]*\bincluded\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)(?=.*\b(?:reconstruct|recover)[^.]*\btechnical[- ]group\b)(?=.*\b(?:covariate|adjustment)\b)",
            r"(?is)(?=.*\b(?:ambient[- ]group|technical[- ]group)\b)(?=.*\b(?:covariate|adjustment)\b)",
        ),
        question_wording=(
            "Which treatment of a recoverable technical grouping governs the primary association "
            "adjustment set for this review?"
        ),
        check_version="1.1.0",
        adapter_version="1.1.0",
    )


def _casrx_isoform_axis_profile() -> _ReportProfile:
    two_axis = "simultaneous_dominant_and_nondominant_effective_knockdown_axes"
    one_axis = "high_dominant_overlap_subset_single_efficiency_axis"
    authority_basis = (
        "Scientist-supplied transcript-effect measurement model; the check does not infer that a "
        "non-dominant component exists, select an overlap threshold, or use numeric agreement as "
        "scientific authority."
    )
    return _ReportProfile(
        check_id="check:casrx-isoform-axis-model",
        dimension="measurement_model",
        candidates=(
            _candidate(
                "simultaneous-dominant-and-nondominant-axes",
                "Fit simultaneous effective dominant- and non-dominant-isoform knockdown axes",
                two_axis,
                authority_basis,
            ),
            _candidate(
                "high-overlap-single-axis",
                "Restrict to high dominant-isoform overlap and fit one efficiency axis",
                one_axis,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "casrx_effect_model",
            "dominant_isoform_overlap",
            "guide_knockdown_efficiency",
            "transcript_specific_effect",
        ),
        role_bindings=(
            RoleBinding("casrx_effect_model", "reported_transcript_effect_regression"),
            RoleBinding("dominant_isoform_overlap", "reported_per_guide_overlap"),
            RoleBinding("guide_knockdown_efficiency", "reported_per_guide_efficiency"),
            RoleBinding("transcript_specific_effect", "dominant_axis_coefficient"),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(two_axis),
                (
                    r"(?is)\beffective\s+dominant(?:[- ]transcript)?\s+axis\b[^.]*\boverlap\b[^.]*\bknockdown\s+efficiency\b",
                    r"(?is)\bnon[- ]dominant\s+axis\b[^.]*\bone\s+minus\s+overlap\b[^.]*\bknockdown\s+efficiency\b",
                    r"(?is)\bsimultaneous\s+two[- ]axis\s+(?:fit|model|regression)\b",
                    r"(?is)\bdominant[- ]axis\s+coefficient\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(one_axis),
                (
                    r"(?is)(?=.*\b(?:retained|used|restricted)\b[^.]*\b(?:guides?|subset)\b)(?=.*\b(?:dominant|major)[- ]isoform\s+overlap\b)",
                    r"(?is)\b(?:one[- ]axis|through[- ]origin|least[- ]squares)\b[^.]*\b(?:slope|regression|fit)\b[^.]*\bknockdown(?:\s+efficiency)?\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)(?=.*\bCasRx\b)(?=.*\b(?:dominant|major)[- ]isoform\s+overlap\b)(?=.*\bknockdown\s+efficiency\b)",
            r"(?is)(?=.*\beffective\s+dominant(?:[- ]transcript)?\s+axis\b)(?=.*\bnon[- ]dominant\s+axis\b)",
        ),
        question_wording=(
            "Which CasRx isoform-axis model governs the dominant-transcript effect for this review?"
        ),
    )


def _paired_bridge_location_alignment_profile() -> _ReportProfile:
    require_offsets = "group_specific_paired_bridge_location_offsets_before_followup_fit"
    no_offsets = "no_group_specific_paired_bridge_location_offsets_before_followup_fit"
    authority_basis = (
        "Scientist-supplied cross-assay location-alignment requirement; the check does not infer "
        "that an offset is needed, treat negative-control centering as paired-bridge evidence, or "
        "use an answer key as scientific authority."
    )
    return _ReportProfile(
        check_id="check:paired-bridge-location-alignment",
        dimension="scale_and_orientation",
        candidates=(
            _candidate(
                "require-group-specific-paired-bridge-offsets",
                (
                    "Subtract follow-up-minus-primary group offsets estimated from paired bridge "
                    "measurements before the follow-up effect fit"
                ),
                require_offsets,
                authority_basis,
            ),
            _candidate(
                "do-not-require-group-specific-paired-bridge-offsets",
                "Do not require group-specific paired-bridge location offsets",
                no_offsets,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "primary_assay_effect_scale",
            "followup_assay_effect_scale",
            "paired_bridge_measurements",
            "group_specific_location_offset",
            "followup_effect_model",
        ),
        role_bindings=(
            RoleBinding("primary_assay_effect_scale", "reported_primary_assay_effects"),
            RoleBinding("followup_assay_effect_scale", "reported_followup_assay_effects"),
            RoleBinding(
                "paired_bridge_measurements",
                "same_units_measured_on_primary_and_followup_assays",
            ),
            RoleBinding(
                "group_specific_location_offset",
                "followup_minus_primary_if_required",
            ),
            RoleBinding(
                "followup_effect_model",
                "scientist_governed_location_alignment",
            ),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(require_offsets),
                (
                    r"(?is)(?=.*\bpaired\s+bridge\s+measurements?\b)(?=.*\b(?:(?:group|plate|batch)[- ]specific|per[- ](?:group|plate|batch))\s+(?:location\s+|bridge\s+)?offsets?\b)",
                    r"(?is)\bfollow-up[- ]minus[- ]primary\b[^.]*\boffsets?\b[^.]*\bsubtracted\b[^.]*\bfollow-up\s+(?:effects?|measurements?|outcomes?)\b[^.]*\bbefore\b[^.]*\b(?:effect\s+)?(?:model|fit|regression)\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(no_offsets),
                (
                    r"(?is)\b(?:independent|paired)\s+single[- ]guide\s+follow-up\b[^.]*\bnot\s+substituted\b[^.]*\b(?:pooled|primary)\s+endpoint\b",
                    r"(?is)\b(?:correlation|concordance)\b.*?\b(?:pooled|primary)\s+guide\s+effects?\b.*?\b(?:guide\s+)?ranking\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(no_offsets),
                (
                    r"(?is)\bsingle[- ]guide\s+follow-up\b[^.]*\b(?:NTC|negative[- ]control|non[- ]targeting\s+control)\b[^.]*\beach\s+(?:plate|batch|group)\b",
                    r"(?is)\b(?:controls?|NTCs?)\b.*?\bsubtracted\b.*?\b(?:follow-up|secondary)\s+measurements?\b",
                    r"(?i)\bthrough-origin\s+(?:pooled|primary)[-/ ](?:follow-up|secondary)\s+scale\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)(?=.*\bpaired\s+bridge\s+measurements?\b)(?=.*\b(?:(?:group|plate|batch)[- ]specific|per[- ](?:group|plate|batch))\b)(?=.*\boffsets?\b)",
            r"(?is)(?=.*\bsingle[- ]guide\s+follow-up\b)(?=.*\b(?:pooled|primary)\s+(?:endpoint|guide\s+effects?)\b)(?=.*\b(?:ranking|concordance|correlation)\b)",
            r"(?is)(?=.*\bsingle[- ]guide\s+follow-up\b)(?=.*\b(?:NTC|negative[- ]control|non[- ]targeting\s+control)\b)(?=.*\bthrough-origin\s+(?:pooled|primary)[-/ ](?:follow-up|secondary)\s+scale\b)",
        ),
        question_wording=(
            "Does this review require group-specific location alignment estimated from paired "
            "bridge measurements before follow-up effect estimation?"
        ),
    )


def _conformance_profile() -> _ReportProfile:
    return _ReportProfile(
        check_id="check:registry-conformance-token",
        dimension="measurement_model",
        candidates=(
            _candidate(
                "bounded-conformance",
                "Use bounded conformance mode",
                "bounded_conformance_mode",
                "Synthetic conformance choice; it has no scientific authority.",
            ),
        ),
        semantic_roles=("conformance_token",),
        role_bindings=(RoleBinding("conformance_token", "bounded"),),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar("bounded_conformance_mode"),
                (r"SC-REFEREE-CONFORMANCE:\s*bounded",),
            ),
        ),
        triggers=(r"SC-REFEREE-CONFORMANCE:",),
        question_wording="Which synthetic conformance token governs this test review?",
    )
