from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.multiple_testing_scope_attestations_v3_2 import (
    MULTIPLE_TESTING_SCOPE_ATTESTATIONS_V3_2_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_0 import (
    CODE_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST as CODE_CSV_DEPENDENCE_ADAPTER_V3_0_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    CODE_CSV_DEPENDENCE_ADAPTER_ID,
    CODE_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST,
    CODE_CSV_DEPENDENCE_ADAPTER_VERSION,
    CODE_CSV_DEPENDENCE_COUNTEREVIDENCE,
    CODE_CSV_DEPENDENCE_ROLE_BINDINGS,
    CODE_CSV_DEPENDENCE_SEMANTIC_ROLES,
    DEPENDENCE_RECOGNITION_CHECK_VERSION,
    CodeCsvDependenceAdapter,
    code_csv_dependence_grammar_digest,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    CODE_CSV_DEPENDENCE_ADAPTER_ID as QUALIFIED_CODE_CSV_DEPENDENCE_ADAPTER_ID,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    CODE_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST as QUALIFIED_CODE_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    CODE_CSV_DEPENDENCE_ADAPTER_VERSION as QUALIFIED_CODE_CSV_DEPENDENCE_ADAPTER_VERSION,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    CODE_CSV_DEPENDENCE_COUNTEREVIDENCE as QUALIFIED_CODE_CSV_DEPENDENCE_COUNTEREVIDENCE,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    CODE_CSV_DEPENDENCE_ROLE_BINDINGS as QUALIFIED_CODE_CSV_DEPENDENCE_ROLE_BINDINGS,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    CODE_CSV_DEPENDENCE_SEMANTIC_ROLES as QUALIFIED_CODE_CSV_DEPENDENCE_SEMANTIC_ROLES,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    DEPENDENCE_RECOGNITION_CHECK_VERSION as QUALIFIED_DEPENDENCE_RECOGNITION_CHECK_VERSION,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    CodeCsvDependenceAdapter as QualifiedCodeCsvDependenceAdapter,
)
from sc_referee.scientific_checks.code_csv_dependence_adapter_v3_1 import (
    code_csv_dependence_grammar_digest as qualified_code_csv_dependence_grammar_digest,
)
from sc_referee.scientific_checks.code_csv_dependence_dataflow_v3_0 import (
    CODE_CSV_DEPENDENCE_DATAFLOW_IMPLEMENTATION_DIGEST as CODE_CSV_DEPENDENCE_DATAFLOW_V3_0_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_dependence_dataflow_v3_1 import (
    CODE_CSV_DEPENDENCE_DATAFLOW_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_dependence_dataflow_v3_1 import (
    CODE_CSV_DEPENDENCE_DATAFLOW_IMPLEMENTATION_DIGEST as QUALIFIED_CODE_CSV_DEPENDENCE_DATAFLOW_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v2 import (
    CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_ADAPTER_V2_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v2_1 import (
    CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_ADAPTER_V2_1_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v2_2 import (
    CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_ADAPTER_V2_2_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v2_3 import (
    CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_ADAPTER_V2_3_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3 import (
    CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_ADAPTER_V3_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_1 import (
    CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_ADAPTER_V3_1_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_adapter_v3_2 import (
    CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST,
    COMPLETE_FAMILY_CORRECTION_OPERAND,
    MULTIPLE_TESTING_CODE_ADAPTER_ID,
    MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
    MULTIPLE_TESTING_CODE_CANDIDATE_ID,
    MULTIPLE_TESTING_CODE_CHECK_ID,
    MULTIPLE_TESTING_CODE_CHECK_VERSION,
    MULTIPLE_TESTING_CODE_COUNTEREVIDENCE,
    MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    MULTIPLE_TESTING_CODE_SEMANTIC_ROLES,
    NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND,
    STRICT_SUBSET_FAMILY_CORRECTION_OPERAND,
    CodeCsvMultipleTestingAdapter,
    code_csv_multiple_testing_grammar_digest,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_2 import (
    CODE_CSV_MULTIPLE_TESTING_CORRECTION_MODEL_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2 import (
    CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V2_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_1 import (
    CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V2_1_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_2 import (
    CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V2_2_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_3 import (
    CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V2_3_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 import (
    CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V3_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_1 import (
    CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V3_1_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_2 import (
    CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_record_model_v3_1 import (
    CODE_CSV_MULTIPLE_TESTING_RECORD_MODEL_IMPLEMENTATION_DIGEST as CODE_CSV_MULTIPLE_TESTING_RECORD_MODEL_V3_1_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_record_model_v3_2 import (
    CODE_CSV_MULTIPLE_TESTING_RECORD_MODEL_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.copy_dosage_adapter import (
    COPY_DOSAGE_ADAPTER_IMPLEMENTATION_DIGEST,
    COPY_DOSAGE_COUNTEREVIDENCE,
    CopyDosageReportAdapter,
    copy_dosage_recognition_grammar_digest,
)
from sc_referee.scientific_checks.copy_dosage_dataflow import (
    COPY_DOSAGE_DATAFLOW_IMPLEMENTATION_DIGEST,
)
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
from sc_referee.scientific_checks.dependence_recognition_adapter import (
    DEPENDENCE_RECOGNITION_CANDIDATE_ID,
    DEPENDENCE_RECOGNITION_CHECK_ID,
    MULTIPLE_ROWS_PER_AUTHORIZED_UNIT,
    ONE_ROW_PER_AUTHORIZED_UNIT,
)
from sc_referee.scientific_checks.founder_orientation_adapter import (
    FOUNDER_ORIENTATION_ADAPTER_IMPLEMENTATION_DIGEST,
    FOUNDER_ORIENTATION_COUNTEREVIDENCE,
    FounderOrientationReportAdapter,
    founder_orientation_recognition_grammar_digest,
)
from sc_referee.scientific_checks.founder_orientation_dataflow import (
    FOUNDER_ORIENTATION_DATAFLOW_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.founder_orientation_semantic import (
    FOUNDER_ORIENTATION_SEMANTIC_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.founder_orientation_semantic_adapter import (
    FOUNDER_ORIENTATION_SEMANTIC_ADAPTER_IMPLEMENTATION_DIGEST,
    FOUNDER_ORIENTATION_SEMANTIC_COUNTEREVIDENCE,
    FounderOrientationSemanticReportAdapter,
    founder_orientation_semantic_recognition_grammar_digest,
)
from sc_referee.scientific_checks.integration_multiple_testing_v2 import (
    MULTIPLE_TESTING_INTEGRATION_IMPLEMENTATION_DIGEST as MULTIPLE_TESTING_INTEGRATION_V2_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.integration_multiple_testing_v2_1 import (
    MULTIPLE_TESTING_INTEGRATION_IMPLEMENTATION_DIGEST as MULTIPLE_TESTING_INTEGRATION_V2_1_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.integration_multiple_testing_v2_2 import (
    MULTIPLE_TESTING_INTEGRATION_IMPLEMENTATION_DIGEST as MULTIPLE_TESTING_INTEGRATION_V2_2_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.integration_multiple_testing_v2_3 import (
    MULTIPLE_TESTING_INTEGRATION_IMPLEMENTATION_DIGEST as MULTIPLE_TESTING_INTEGRATION_V2_3_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.integration_multiple_testing_v3 import (
    MULTIPLE_TESTING_INTEGRATION_IMPLEMENTATION_DIGEST as MULTIPLE_TESTING_INTEGRATION_V3_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.integration_multiple_testing_v3_1 import (
    MULTIPLE_TESTING_INTEGRATION_IMPLEMENTATION_DIGEST as MULTIPLE_TESTING_INTEGRATION_V3_1_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.integration_multiple_testing_v3_2 import (
    MULTIPLE_TESTING_INTEGRATION_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.multiple_testing_recognition_adapter import (
    COMPLETE_FAMILY_CORRECTION,
    MULTIPLE_TESTING_RECOGNITION_ADAPTER_ID,
    MULTIPLE_TESTING_RECOGNITION_ADAPTER_VERSION,
    MULTIPLE_TESTING_RECOGNITION_CANDIDATE_ID,
    MULTIPLE_TESTING_RECOGNITION_CHECK_ID,
    MULTIPLE_TESTING_RECOGNITION_CHECK_VERSION,
    MULTIPLE_TESTING_RECOGNITION_COUNTEREVIDENCE,
    MULTIPLE_TESTING_RECOGNITION_ROLE_BINDINGS,
    MULTIPLE_TESTING_RECOGNITION_SCIENTIFIC_ADAPTER_IMPLEMENTATION_DIGEST,
    MULTIPLE_TESTING_RECOGNITION_SEMANTIC_ROLES,
    STRICT_SUBSET_CORRECTION,
    MultipleTestingRecognitionScientificAdapter,
    multiple_testing_recognition_grammar_digest,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v3_2 import (
    MULTIPLE_TESTING_SCOPE_QUESTIONS_V3_2_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.python_founder_adapter import (
    PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.quantity_consistency_adapter import (
    QUANTITY_CONSISTENCY_ADAPTER_IMPLEMENTATION_DIGEST,
    QUANTITY_COUNTEREVIDENCE,
    QuantityConsistencyReportAdapter,
    quantity_recognition_grammar_digest,
)
from sc_referee.scientific_checks.quantity_dataflow_adapter import (
    QUANTITY_DATAFLOW_IMPLEMENTATION_DIGEST,
)
from sc_referee.scientific_checks.registry import (
    SCIENTIFIC_CHECK_REDUCER_IMPLEMENTATION_DIGEST,
    RegistryValidationError,
    ScientificCheckRegistry,
)
from sc_referee.scientific_checks.report_csv_dependence_adapter import (
    REPORT_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST,
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
from sc_referee.scientific_checks.static_source_adapter import (
    STATIC_SOURCE_ADAPTER_IMPLEMENTATION_DIGEST,
    make_static_source_adapter,
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
_QUALIFIED_DEPENDENCE_CHECK_IMPLEMENTATION_DIGEST = (
    "sha256:784ed2db607630e1939f82dd6649b152e8c3913cc1ec12668283d6ecb624de36"
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
    selected_development = release.development_modules[:-1]
    selected_ids = {module.manifest.check_id for module in selected}
    selected_development_ids = {module.manifest.check_id for module in selected_development}
    return ScientificCheckRegistry(
        selected,
        method_conflict_bindings=tuple(
            binding
            for binding in release.method_conflict_bindings
            if binding.check_id in selected_ids
        ),
        development_modules=selected_development,
        development_method_conflict_bindings=tuple(
            binding
            for binding in release.development_method_conflict_bindings
            if binding.check_id in selected_development_ids
        ),
    )


def scientific_check_release_registry() -> ScientificCheckRegistry:
    """Construct the complete content-addressed registry before release-manifest verification."""

    modules = _scientific_check_release_modules(dependence_lane="qualified")
    development_modules = _scientific_check_release_modules(dependence_lane="development")
    detector_manifests = _method_conflict_detector_manifests()
    substantive_modules = modules[:-1]
    substantive_development_modules = development_modules[:-1]
    bindings = tuple(
        _method_conflict_binding(
            module,
            detector_manifests[
                (
                    "detector:bounded-code-csv-dependence-conflict",
                    "3.1.0",
                )
                if module.manifest.check_id
                == "check:authorized-independent-unit-entry-into-row-independent-procedure"
                else (
                    "detector:bounded-code-csv-multiple-testing-conflict",
                    "3.0.0",
                )
                if module.manifest.check_id == MULTIPLE_TESTING_CODE_CHECK_ID
                else ("detector:bounded-analysis-method-conflict", "0.3.0")
            ],
        )
        for module in substantive_modules
    )
    development_bindings = tuple(
        _method_conflict_binding(
            module,
            detector_manifests[
                (
                    "detector:bounded-code-csv-dependence-conflict",
                    "3.1.0",
                )
                if module.manifest.check_id
                == "check:authorized-independent-unit-entry-into-row-independent-procedure"
                else (
                    "detector:bounded-code-csv-multiple-testing-conflict",
                    "3.2.0",
                )
                if module.manifest.check_id == MULTIPLE_TESTING_CODE_CHECK_ID
                else ("detector:bounded-analysis-method-conflict", "0.3.0")
            ],
            binding_id=(
                "method-conflict-binding:authorized-independent-unit-entry-into-row-"
                "independent-procedure-v1:development"
                if module.manifest.check_id
                == "check:authorized-independent-unit-entry-into-row-independent-procedure"
                else (
                    "method-conflict-binding:authorized-complete-family-correction-over-code-"
                    "test-battery-v1:development"
                )
                if module.manifest.check_id == MULTIPLE_TESTING_CODE_CHECK_ID
                else None
            ),
        )
        for module in substantive_development_modules
    )
    return ScientificCheckRegistry(
        modules,
        method_conflict_bindings=bindings,
        development_modules=development_modules,
        development_method_conflict_bindings=development_bindings,
    )


def _method_conflict_binding(
    module: ScientificCheckModule,
    detector_manifest: Mapping[str, Any],
    *,
    binding_id: str | None = None,
) -> MethodConflictBinding:
    manifest = module.manifest
    operand_kinds = {candidate.operand.kind for candidate in manifest.requirement_candidates}
    if len(operand_kinds) != 1:
        raise RegistryValidationError(
            f"scientific check has mixed requirement operand kinds: {manifest.check_id}"
        )
    evidence_planes = tuple(
        sorted({adapter.evidence_plane for adapter in module.adapter_manifests})
    )
    assertion_roles = tuple(
        sorted(
            {"reported" if plane == "reported_text" else "observed" for plane in evidence_planes}
        )
    )
    return MethodConflictBinding(
        binding_id=(
            binding_id or f"method-conflict-binding:{manifest.check_id.removeprefix('check:')}-v1"
        ),
        check_id=manifest.check_id,
        check_version=manifest.check_version,
        check_manifest_digest=manifest.manifest_digest,
        detector_id=str(detector_manifest["detector_id"]),
        detector_version=str(detector_manifest["detector_version"]),
        detector_manifest_digest=semantic_digest(detector_manifest),
        dimension=manifest.dimension,
        comparison_form=manifest.comparison_form,
        operand_kind=next(iter(operand_kinds)),
        required_evidence_planes=evidence_planes,
        required_semantic_roles=manifest.semantic_roles,
        required_assertion_roles=assertion_roles,
        counterevidence_predicates=(
            "approved_method_deviation",
            "governing_protocol_amendment",
            "method_obligation_applicability",
        ),
    )


def _scientific_check_release_modules(*, dependence_lane: str) -> tuple[ScientificCheckModule, ...]:
    """Construct the complete manifest set, including the removable conformance module."""

    report_profiles = (
        _expected_count_background_construction_profile(),
        _expected_count_focal_target_handling_profile(),
        _founder_orientation_profile(),
        _directional_measurement_error_profile(),
        _transition_path_continuity_profile(),
        _ancestry_exposure_profile(),
        _complete_domain_exposure_profile(),
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
        _local_perturbation_row_scope_profile(),
        _local_perturbation_regression_profile(),
    )
    qualified_lane = dependence_lane == "qualified"
    modules = (
        *(tuple(_module(profile, qualified_lane=qualified_lane) for profile in report_profiles)),
        _mvmr_covariance_module(qualified_lane=qualified_lane),
        _module(
            _dependence_recognition_profile(qualified=qualified_lane),
            qualified_lane=qualified_lane,
        ),
        _module(_multiple_testing_recognition_profile(), qualified_lane=qualified_lane),
        *((_multiple_testing_code_module(),) if not qualified_lane else ()),
        _module(_conformance_profile(), qualified_lane=qualified_lane),
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
            "scientific_checks/core.py": sha256_digest(
                (Path(__file__).resolve().parent / "core.py").read_bytes()
            ),
            "scientific_checks/copy_dosage_adapter.py": (COPY_DOSAGE_ADAPTER_IMPLEMENTATION_DIGEST),
            "scientific_checks/copy_dosage_dataflow.py": (
                COPY_DOSAGE_DATAFLOW_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/report_csv_dependence_adapter.py": (
                REPORT_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_dependence_adapter.py": (
                sha256_digest(
                    (
                        Path(__file__).resolve().parent / "code_csv_dependence_adapter.py"
                    ).read_bytes()
                )
            ),
            "scientific_checks/code_csv_dependence_dataflow.py": (
                sha256_digest(
                    (
                        Path(__file__).resolve().parent / "code_csv_dependence_dataflow.py"
                    ).read_bytes()
                )
            ),
            "scientific_checks/code_csv_dependence_adapter_v3_1.py": (
                CODE_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_dependence_dataflow_v3_1.py": (
                CODE_CSV_DEPENDENCE_DATAFLOW_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_adapter_v1.py": sha256_digest(
                (
                    Path(__file__).resolve().parent / "code_csv_multiple_testing_adapter_v1.py"
                ).read_bytes()
            ),
            "scientific_checks/code_csv_multiple_testing_dataflow_v1.py": sha256_digest(
                (
                    Path(__file__).resolve().parent / "code_csv_multiple_testing_dataflow_v1.py"
                ).read_bytes()
            ),
            "scientific_checks/integration_multiple_testing_v1.py": sha256_digest(
                (
                    Path(__file__).resolve().parent / "integration_multiple_testing_v1.py"
                ).read_bytes()
            ),
            "scientific_checks/code_csv_multiple_testing_adapter_v1_1.py": (
                sha256_digest(
                    (
                        Path(__file__).resolve().parent
                        / "code_csv_multiple_testing_adapter_v1_1.py"
                    ).read_bytes()
                )
            ),
            "scientific_checks/code_csv_multiple_testing_dataflow_v1_1.py": (
                sha256_digest(
                    (
                        Path(__file__).resolve().parent
                        / "code_csv_multiple_testing_dataflow_v1_1.py"
                    ).read_bytes()
                )
            ),
            "scientific_checks/code_csv_multiple_testing_adapter_v2.py": (
                CODE_CSV_MULTIPLE_TESTING_ADAPTER_V2_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_dataflow_v2.py": (
                CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V2_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/integration_multiple_testing_v2.py": (
                MULTIPLE_TESTING_INTEGRATION_V2_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_adapter_v2_1.py": (
                CODE_CSV_MULTIPLE_TESTING_ADAPTER_V2_1_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_dataflow_v2_1.py": (
                CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V2_1_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/integration_multiple_testing_v2_1.py": (
                MULTIPLE_TESTING_INTEGRATION_V2_1_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_adapter_v2_2.py": (
                CODE_CSV_MULTIPLE_TESTING_ADAPTER_V2_2_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_dataflow_v2_2.py": (
                CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V2_2_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/integration_multiple_testing_v2_2.py": (
                MULTIPLE_TESTING_INTEGRATION_V2_2_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_adapter_v2_3.py": (
                CODE_CSV_MULTIPLE_TESTING_ADAPTER_V2_3_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_dataflow_v2_3.py": (
                CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V2_3_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/integration_multiple_testing_v2_3.py": (
                MULTIPLE_TESTING_INTEGRATION_V2_3_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_adapter_v3.py": (
                CODE_CSV_MULTIPLE_TESTING_ADAPTER_V3_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_dataflow_v3.py": (
                CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V3_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_record_model_v3.py": sha256_digest(
                (
                    Path(__file__).resolve().parent / "code_csv_multiple_testing_record_model_v3.py"
                ).read_bytes()
            ),
            "scientific_checks/integration_multiple_testing_v3.py": (
                MULTIPLE_TESTING_INTEGRATION_V3_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_adapter_v3_1.py": (
                CODE_CSV_MULTIPLE_TESTING_ADAPTER_V3_1_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_dataflow_v3_1.py": (
                CODE_CSV_MULTIPLE_TESTING_DATAFLOW_V3_1_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_record_model_v3_1.py": (
                CODE_CSV_MULTIPLE_TESTING_RECORD_MODEL_V3_1_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/integration_multiple_testing_v3_1.py": (
                MULTIPLE_TESTING_INTEGRATION_V3_1_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_adapter_v3_2.py": (
                CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_dataflow_v3_2.py": (
                CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_record_model_v3_2.py": (
                CODE_CSV_MULTIPLE_TESTING_RECORD_MODEL_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_multiple_testing_correction_model_v3_2.py": (
                CODE_CSV_MULTIPLE_TESTING_CORRECTION_MODEL_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/integration_multiple_testing_v3_2.py": (
                MULTIPLE_TESTING_INTEGRATION_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/multiple_testing_scope_questions_v3_2.py": (
                MULTIPLE_TESTING_SCOPE_QUESTIONS_V3_2_IMPLEMENTATION_DIGEST
            ),
            "multiple_testing_scope_attestations_v3_2.py": (
                MULTIPLE_TESTING_SCOPE_ATTESTATIONS_V3_2_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/multiple_testing_scope_questions_v1.py": sha256_digest(
                (
                    Path(__file__).resolve().parent / "multiple_testing_scope_questions_v1.py"
                ).read_bytes()
            ),
            "multiple_testing_scope_attestations_v1.py": sha256_digest(
                (
                    Path(__file__).resolve().parents[1]
                    / "multiple_testing_scope_attestations_v1.py"
                ).read_bytes()
            ),
            "resources/input-schemas-v1/multiple-testing-correction-scope-attestations-v1.schema.json": sha256_digest(
                (
                    Path(__file__).resolve().parents[1]
                    / "resources"
                    / "input-schemas-v1"
                    / "multiple-testing-correction-scope-attestations-v1.schema.json"
                ).read_bytes()
            ),
            "resources/multiple-testing-question-profiles-v1/correction-scope-v1.json": sha256_digest(
                (
                    Path(__file__).resolve().parents[1]
                    / "resources"
                    / "multiple-testing-question-profiles-v1"
                    / "correction-scope-v1.json"
                ).read_bytes()
            ),
            "scientific_checks/code_csv_dependence_adapter_v3_0.py": (
                CODE_CSV_DEPENDENCE_ADAPTER_V3_0_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_dependence_dataflow_v3_0.py": (
                CODE_CSV_DEPENDENCE_DATAFLOW_V3_0_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/code_csv_dependence_adapter_v2_1.py": sha256_digest(
                (
                    Path(__file__).resolve().parent / "code_csv_dependence_adapter_v2_1.py"
                ).read_bytes()
            ),
            "scientific_checks/code_csv_dependence_dataflow_v2_1.py": (
                QUALIFIED_CODE_CSV_DEPENDENCE_DATAFLOW_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/report_csv_dependence_adapter_v2_1.py": sha256_digest(
                (
                    Path(__file__).resolve().parent / "report_csv_dependence_adapter_v2_1.py"
                ).read_bytes()
            ),
            "resources/frozen-code-csv-dependence-v2.1.0/code_csv_dependence_adapter.py": (
                sha256_digest(
                    (
                        Path(__file__).resolve().parents[1]
                        / "resources"
                        / "frozen-code-csv-dependence-v2.1.0"
                        / "code_csv_dependence_adapter.py"
                    ).read_bytes()
                )
            ),
            "resources/frozen-code-csv-dependence-v2.1.0/code_csv_dependence_dataflow.py": (
                sha256_digest(
                    (
                        Path(__file__).resolve().parents[1]
                        / "resources"
                        / "frozen-code-csv-dependence-v2.1.0"
                        / "code_csv_dependence_dataflow.py"
                    ).read_bytes()
                )
            ),
            "resources/frozen-code-csv-dependence-v2.1.0/report_csv_dependence_adapter.py": (
                sha256_digest(
                    (
                        Path(__file__).resolve().parents[1]
                        / "resources"
                        / "frozen-code-csv-dependence-v2.1.0"
                        / "report_csv_dependence_adapter.py"
                    ).read_bytes()
                )
            ),
            "resources/frozen-code-csv-dependence-v2.1.0/FROZEN_SOURCES.json": (
                sha256_digest(
                    (
                        Path(__file__).resolve().parents[1]
                        / "resources"
                        / "frozen-code-csv-dependence-v2.1.0"
                        / "FROZEN_SOURCES.json"
                    ).read_bytes()
                )
            ),
            "scientific_checks/multiple_testing_recognition_adapter.py": (
                MULTIPLE_TESTING_RECOGNITION_SCIENTIFIC_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/founder_orientation_adapter.py": (
                FOUNDER_ORIENTATION_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/founder_orientation_dataflow.py": (
                FOUNDER_ORIENTATION_DATAFLOW_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/founder_orientation_semantic.py": (
                FOUNDER_ORIENTATION_SEMANTIC_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/founder_orientation_semantic_adapter.py": (
                FOUNDER_ORIENTATION_SEMANTIC_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/founder_orientation_certificate.py": sha256_digest(
                (
                    Path(__file__).resolve().parent / "founder_orientation_certificate.py"
                ).read_bytes()
            ),
            "scientific_checks/founder_orientation_csv_domain.py": sha256_digest(
                (Path(__file__).resolve().parent / "founder_orientation_csv_domain.py").read_bytes()
            ),
            "scientific_checks/founder_orientation_semantic_ir.py": sha256_digest(
                (
                    Path(__file__).resolve().parent / "founder_orientation_semantic_ir.py"
                ).read_bytes()
            ),
            "scientific_checks/integration.py": sha256_digest(
                (Path(__file__).resolve().parent / "integration.py").read_bytes()
            ),
            "scientific_checks/integration_multiple_testing_v1_1.py": (
                sha256_digest(
                    (
                        Path(__file__).resolve().parent / "integration_multiple_testing_v1_1.py"
                    ).read_bytes()
                )
            ),
            "scientific_checks/python_founder_adapter.py": (
                PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/rmarkdown_mvmr_adapter.py": (
                RMARKDOWN_MVMR_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/quantity_consistency_adapter.py": (
                QUANTITY_CONSISTENCY_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/quantity_dataflow_adapter.py": (
                QUANTITY_DATAFLOW_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/registry.py": SCIENTIFIC_CHECK_REDUCER_IMPLEMENTATION_DIGEST,
            "scientific_checks/selected_report_adapter.py": (
                SELECTED_REPORT_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/static_source_adapter.py": (
                STATIC_SOURCE_ADAPTER_IMPLEMENTATION_DIGEST
            ),
            "scientific_checks/scope_joins.py": sha256_digest(
                (Path(__file__).resolve().parent / "scope_joins.py").read_bytes()
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
        "development_modules": [
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
            for module in sorted(
                registry.development_modules, key=lambda item: item.manifest.check_id
            )
        ],
        "method_conflict_bindings": [
            binding.to_dict()
            for binding in sorted(
                registry.method_conflict_bindings, key=lambda item: item.binding_id
            )
        ],
        "development_method_conflict_bindings": [
            binding.to_dict()
            for binding in sorted(
                registry.development_method_conflict_bindings,
                key=lambda item: item.binding_id,
            )
        ],
    }


def _method_conflict_detector_manifests() -> Mapping[tuple[str, str], Mapping[str, Any]]:
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
    expected = {
        ("detector:bounded-analysis-method-conflict", "0.3.0"),
        ("detector:bounded-code-csv-dependence-conflict", "2.1.0"),
        ("detector:bounded-code-csv-dependence-conflict", "2.3.0"),
        ("detector:bounded-code-csv-dependence-conflict", "3.0.0"),
        ("detector:bounded-code-csv-dependence-conflict", "3.1.0"),
        ("detector:bounded-code-csv-multiple-testing-conflict", "1.0.0"),
        ("detector:bounded-code-csv-multiple-testing-conflict", "1.1.0"),
        ("detector:bounded-code-csv-multiple-testing-conflict", "2.0.0"),
        ("detector:bounded-code-csv-multiple-testing-conflict", "2.1.0"),
        ("detector:bounded-code-csv-multiple-testing-conflict", "2.2.0"),
        ("detector:bounded-code-csv-multiple-testing-conflict", "2.3.0"),
        ("detector:bounded-code-csv-multiple-testing-conflict", "3.0.0"),
        ("detector:bounded-code-csv-multiple-testing-conflict", "3.1.0"),
        ("detector:bounded-code-csv-multiple-testing-conflict", "3.2.0"),
    }
    matches = [
        item
        for item in records
        if isinstance(item, Mapping)
        and (str(item.get("detector_id")), str(item.get("detector_version"))) in expected
    ]
    by_identity = {
        (str(item["detector_id"]), str(item["detector_version"])): item for item in matches
    }
    if set(by_identity) != expected:
        raise RegistryValidationError("method-conflict detector manifests are unavailable")
    for detector_id, detector_version in expected:
        manifest = by_identity[(detector_id, detector_version)]
        if (
            manifest.get("record_type") != "detector_manifest"
            or manifest.get("detector_version") != detector_version
            or manifest.get("maturity") != "experimental"
            or "finding" in manifest.get("permitted_output_types", [])
        ):
            raise RegistryValidationError("method-conflict detector manifest is ineligible")
    return by_identity


def _module(profile: _ReportProfile, *, qualified_lane: bool = False) -> ScientificCheckModule:
    check = CheckManifest(
        check_id=profile.check_id,
        check_version=profile.check_version,
        implementation_digest=_QUALIFIED_DEPENDENCE_CHECK_IMPLEMENTATION_DIGEST,
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
    if profile.check_id == "check:complete-domain-exposure-denominator":
        return _quantity_consistency_module(check, profile)
    if profile.check_id == "check:founder-orientation-before-hmm-emission":
        return _founder_orientation_module(check, profile)
    if profile.check_id == "check:classifier-derived-copy-dosage-representation":
        return _copy_dosage_module(check, profile)
    if profile.check_id == DEPENDENCE_RECOGNITION_CHECK_ID:
        if qualified_lane:
            return _qualified_dependence_recognition_module(check, profile)
        return _dependence_recognition_module(check, profile)
    if profile.check_id == MULTIPLE_TESTING_RECOGNITION_CHECK_ID:
        return _multiple_testing_recognition_module(check, profile)
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
    source_profile = {
        "check:directional-measurement-error-interpretation": (
            "directional_measurement_error",
            ("python",),
        ),
        "check:ld-covariance-whitening-before-robust-fit": (
            "ld_whitening",
            ("python", "r"),
        ),
    }.get(profile.check_id)
    if source_profile is not None:
        source_recognizer, source_languages = source_profile
        for language in source_languages:
            source_manifest, source_adapter = make_static_source_adapter(
                check_manifest=check,
                language=language,  # type: ignore[arg-type]
                recognizer=source_recognizer,  # type: ignore[arg-type]
                role_bindings=profile.role_bindings,
            )
            adapter_manifests.append(source_manifest)
            adapters.append(source_adapter)
    return ScientificCheckModule(
        manifest=check,
        declared_manifest_digest=check.manifest_digest,
        adapter_manifests=tuple(adapter_manifests),
        adapters=tuple(adapters),
    )


def _quantity_consistency_module(
    check: CheckManifest, profile: _ReportProfile
) -> ScientificCheckModule:
    """Build the ADR-0069 quantity-arithmetic module for the denominator-domain check."""

    operands = {candidate.candidate_id: candidate.operand for candidate in profile.candidates}
    complete_operand = operands["complete-declared-domain-exposure"]
    retained_operand = operands["retained-observed-subset-exposure"]
    adapter_manifest = AdapterManifest(
        adapter_id=(f"adapter:{profile.check_id.removeprefix('check:')}:quantity-consistency-v1"),
        adapter_version=profile.adapter_version,
        implementation_digest=QUANTITY_CONSISTENCY_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=quantity_recognition_grammar_digest(
            str(complete_operand.value), str(retained_operand.value)
        ),
        parser_id="parser:markdown-inventory",
        parser_version="0.2.0",
        source_language="markdown",
        evidence_plane="reported_text",
        semantic_roles=profile.semantic_roles,
        applicability_profile="bounded-quantity-accounting-reconciliation-v1",
        counterevidence_profiles=QUANTITY_COUNTEREVIDENCE,
        known_gaps=(
            "rates stated as bare integers without a percent marker",
            "word-form numbers",
            "accountings whose removed count is never stated",
            "non-Markdown publication surfaces",
            "reported quantities do not establish execution",
        ),
    )
    adapter = QuantityConsistencyReportAdapter(
        check_manifest=check,
        adapter_manifest=adapter_manifest,
        complete_operand=complete_operand,
        retained_operand=retained_operand,
    )
    return ScientificCheckModule(
        manifest=check,
        declared_manifest_digest=check.manifest_digest,
        adapter_manifests=(adapter_manifest,),
        adapters=(adapter,),
    )


def _founder_orientation_module(
    check: CheckManifest, profile: _ReportProfile
) -> ScientificCheckModule:
    """Build the ADR-0069 operations-based module for the founder-orientation check."""

    operands = {candidate.candidate_id: candidate.operand for candidate in profile.candidates}
    direct_operand = operands["use-supplied-orientation"]
    repaired_operand = operands["repair-before-emission"]
    adapter_manifest = AdapterManifest(
        adapter_id=(f"adapter:{profile.check_id.removeprefix('check:')}:orientation-dataflow-v1"),
        adapter_version=profile.adapter_version,
        implementation_digest=FOUNDER_ORIENTATION_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=founder_orientation_recognition_grammar_digest(
            str(direct_operand.value), str(repaired_operand.value)
        ),
        parser_id="parser:markdown-inventory",
        parser_version="0.2.0",
        source_language="markdown",
        evidence_plane="reported_text",
        semantic_roles=profile.semantic_roles,
        applicability_profile="bounded-founder-orientation-reconciliation-v1",
        counterevidence_profiles=FOUNDER_ORIENTATION_COUNTEREVIDENCE,
        known_gaps=(
            "emission comparisons over parallel sequences other than a recognized "
            "zip pairing of two single-assignment column-values lists of one named "
            "staged row set",
            "emission comparisons inside a helper that receives the row set as a "
            "parameter, where the staged read is out of the traced scope",
            "orientation repairs expressed by arithmetic this trace does not recognize",
            "reports that state no marker-total and agreement-count accounting",
            "reports whose incidental integers reconcile as a second accounting",
            "non-Markdown publication surfaces",
            "reported quantities and source operations do not establish execution",
        ),
    )
    adapter = FounderOrientationReportAdapter(
        check_manifest=check,
        adapter_manifest=adapter_manifest,
        direct_operand=direct_operand,
        repaired_operand=repaired_operand,
        role_bindings=profile.role_bindings,
    )
    semantic_manifest = AdapterManifest(
        adapter_id=(f"adapter:{profile.check_id.removeprefix('check:')}:orientation-semantic-v3"),
        adapter_version="3.1.1",
        implementation_digest=FOUNDER_ORIENTATION_SEMANTIC_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=founder_orientation_semantic_recognition_grammar_digest(
            str(direct_operand.value), str(repaired_operand.value)
        ),
        parser_id="parser:markdown-inventory",
        parser_version="0.2.0",
        source_language="markdown",
        evidence_plane="reported_text",
        semantic_roles=profile.semantic_roles,
        applicability_profile="bounded-founder-orientation-semantic-certificate-v3",
        counterevidence_profiles=FOUNDER_ORIENTATION_SEMANTIC_COUNTEREVIDENCE,
        known_gaps=(
            "opaque operations whose effects intersect the report-reaching projection, "
            "selector, fold, accumulator, or sink slice",
            "binary-only recodes other than one-minus remain outside the accepted transform "
            "grammar even when a staged-column binary domain is proved",
            "control-flow joins that do not reduce to one exact abstract value",
            "helpers with variadic or higher-order dynamic dispatch",
            "orientation-from-report-numbers CSV refinement remains intentionally disabled",
            "reports that state no marker-total and agreement-count accounting",
            "non-Markdown publication surfaces",
            "static operations do not establish execution or scientific intent",
        ),
    )
    semantic_adapter = FounderOrientationSemanticReportAdapter(
        check_manifest=check,
        adapter_manifest=semantic_manifest,
        direct_operand=direct_operand,
        repaired_operand=repaired_operand,
        role_bindings=profile.role_bindings,
    )
    return ScientificCheckModule(
        manifest=check,
        declared_manifest_digest=check.manifest_digest,
        adapter_manifests=(adapter_manifest, semantic_manifest),
        adapters=(adapter, semantic_adapter),
    )


def _copy_dosage_module(check: CheckManifest, profile: _ReportProfile) -> ScientificCheckModule:
    """Build the ADR-0069 operations-based module for the copy-dosage check."""

    operands = {candidate.candidate_id: candidate.operand for candidate in profile.candidates}
    hard_operand = operands["integer-hard-copy-state"]
    expectation_operand = operands["continuous-posterior-expected-copy-dosage"]
    calibration_operand = operands["direct-continuous-calibrated-copy-dosage"]
    adapter_manifest = AdapterManifest(
        adapter_id=(f"adapter:{profile.check_id.removeprefix('check:')}:dosage-dataflow-v1"),
        adapter_version=profile.adapter_version,
        implementation_digest=COPY_DOSAGE_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=copy_dosage_recognition_grammar_digest(
            str(hard_operand.value),
            str(expectation_operand.value),
            str(calibration_operand.value),
        ),
        parser_id="parser:markdown-inventory",
        parser_version="0.2.0",
        source_language="markdown",
        evidence_plane="reported_text",
        semantic_roles=profile.semantic_roles,
        applicability_profile="bounded-copy-dosage-representation-dataflow-v1",
        counterevidence_profiles=COPY_DOSAGE_COUNTEREVIDENCE,
        known_gaps=(
            "formula-interface model specifications, whose regressors are named in a "
            "string rather than built as a design matrix",
            "estimator wrappers such as pipelines and search objects, whose fitted "
            "terminal stage this trace cannot read",
            "staged table columns whose numeric type no operation in the workflow "
            "establishes, which are neither continuous nor integer-coded here",
            "a report-reaching fit whose design this trace cannot read at all, which "
            "contributes no classification",
            "workflows in languages other than Python",
            "reports that state no per-state dosage accounting",
            "reported quantities and source operations do not establish execution",
        ),
    )
    adapter = CopyDosageReportAdapter(
        check_manifest=check,
        adapter_manifest=adapter_manifest,
        hard_operand=hard_operand,
        expectation_operand=expectation_operand,
        calibration_operand=calibration_operand,
        role_bindings=profile.role_bindings,
    )
    return ScientificCheckModule(
        manifest=check,
        declared_manifest_digest=check.manifest_digest,
        adapter_manifests=(adapter_manifest,),
        adapters=(adapter,),
    )


def _dependence_recognition_module(
    check: CheckManifest, profile: _ReportProfile
) -> ScientificCheckModule:
    """Build the single prose-free code/CSV dependence evaluation module."""

    operands = {candidate.candidate_id: candidate.operand for candidate in profile.candidates}
    one_row_operand = operands[DEPENDENCE_RECOGNITION_CANDIDATE_ID]
    multiple_rows_operand = CanonicalOperand.scalar(MULTIPLE_ROWS_PER_AUTHORIZED_UNIT)
    adapter_manifest = AdapterManifest(
        adapter_id=CODE_CSV_DEPENDENCE_ADAPTER_ID,
        adapter_version=CODE_CSV_DEPENDENCE_ADAPTER_VERSION,
        implementation_digest=CODE_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=code_csv_dependence_grammar_digest(),
        parser_id="parser:python-ast-tokenize",
        parser_version="0.15.1",
        source_language="python",
        evidence_plane="static_source",
        semantic_roles=profile.semantic_roles,
        applicability_profile="bounded-code-csv-rowwise-two-sample-dependence-v1",
        counterevidence_profiles=CODE_CSV_DEPENDENCE_COUNTEREVIDENCE,
        known_gaps=(
            "analysis paths outside one root analysis.py",
            "helper dataflow beyond the exact depth-two inlining grammar and unsupported control flow",
            "procedures outside registered scipy two-sample APIs",
            "readers, selections, transforms, and sinks outside the closed AST grammar",
            "alternate analysis files and off-scope statistics imports",
            "D1-prime irregular composite labels outside the closed candidate rule",
            "static source and CSV structure do not establish execution or scientific correctness",
        ),
    )
    adapter = CodeCsvDependenceAdapter(
        check_manifest=check,
        adapter_manifest=adapter_manifest,
        one_row_operand=one_row_operand,
        multiple_rows_operand=multiple_rows_operand,
        role_bindings=CODE_CSV_DEPENDENCE_ROLE_BINDINGS,
    )
    return ScientificCheckModule(
        manifest=check,
        declared_manifest_digest=check.manifest_digest,
        adapter_manifests=(adapter_manifest,),
        adapters=(adapter,),
    )


def _qualified_dependence_recognition_module(
    check: CheckManifest, profile: _ReportProfile
) -> ScientificCheckModule:
    """Build the byte-frozen Envelope-9 production dependence module."""

    operands = {candidate.candidate_id: candidate.operand for candidate in profile.candidates}
    one_row_operand = operands[DEPENDENCE_RECOGNITION_CANDIDATE_ID]
    multiple_rows_operand = CanonicalOperand.scalar(MULTIPLE_ROWS_PER_AUTHORIZED_UNIT)
    adapter_manifest = AdapterManifest(
        adapter_id=QUALIFIED_CODE_CSV_DEPENDENCE_ADAPTER_ID,
        adapter_version=QUALIFIED_CODE_CSV_DEPENDENCE_ADAPTER_VERSION,
        implementation_digest=QUALIFIED_CODE_CSV_DEPENDENCE_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=qualified_code_csv_dependence_grammar_digest(),
        parser_id="parser:python-ast-tokenize",
        parser_version="0.15.1",
        source_language="python",
        evidence_plane="static_source",
        semantic_roles=profile.semantic_roles,
        applicability_profile="bounded-code-csv-rowwise-two-sample-dependence-v1",
        counterevidence_profiles=QUALIFIED_CODE_CSV_DEPENDENCE_COUNTEREVIDENCE,
        known_gaps=(
            "analysis paths outside one root analysis.py",
            "helper dataflow beyond the exact depth-two inlining grammar and unsupported control flow",
            "procedures outside registered scipy two-sample APIs",
            "readers, selections, transforms, and sinks outside the closed AST grammar",
            "alternate analysis files and off-scope statistics imports",
            "D1-prime irregular composite labels outside the closed candidate rule",
            "static source and CSV structure do not establish execution or scientific correctness",
        ),
    )
    adapter = QualifiedCodeCsvDependenceAdapter(
        check_manifest=check,
        adapter_manifest=adapter_manifest,
        one_row_operand=one_row_operand,
        multiple_rows_operand=multiple_rows_operand,
        role_bindings=QUALIFIED_CODE_CSV_DEPENDENCE_ROLE_BINDINGS,
    )
    return ScientificCheckModule(
        manifest=check,
        declared_manifest_digest=check.manifest_digest,
        adapter_manifests=(adapter_manifest,),
        adapters=(adapter,),
    )


def _multiple_testing_recognition_module(
    check: CheckManifest, profile: _ReportProfile
) -> ScientificCheckModule:
    """Build the single-adapter Stage 5 multiple-testing evaluation module."""

    operands = {candidate.candidate_id: candidate.operand for candidate in profile.candidates}
    complete_family_operand = operands[MULTIPLE_TESTING_RECOGNITION_CANDIDATE_ID]
    strict_subset_operand = CanonicalOperand.scalar(STRICT_SUBSET_CORRECTION)
    adapter_manifest = AdapterManifest(
        adapter_id=MULTIPLE_TESTING_RECOGNITION_ADAPTER_ID,
        adapter_version=MULTIPLE_TESTING_RECOGNITION_ADAPTER_VERSION,
        implementation_digest=MULTIPLE_TESTING_RECOGNITION_SCIENTIFIC_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=multiple_testing_recognition_grammar_digest(),
        parser_id="parser:python-ast-tokenize",
        parser_version="0.15.1",
        source_language="python",
        evidence_plane="static_source",
        semantic_roles=profile.semantic_roles,
        applicability_profile="bounded-multiple-testing-semantic-certificate-v1",
        counterevidence_profiles=MULTIPLE_TESTING_RECOGNITION_COUNTEREVIDENCE,
        known_gaps=(
            "loop-built-test-battery-unrecognized",
            "cross-module-correction-unverified",
            "hand-typed-correction-family-unbound",
            "family-definition-unauthorized",
            "per-group-correction-unrecognized",
            "value-predicate-correction-unsupported",
            "repository-bh-runtime-type-binding-unverified",
            "single-column-key-tuple-form-unsupported",
            "static source relationships do not establish execution or scientific correctness",
        ),
    )
    adapter = MultipleTestingRecognitionScientificAdapter(
        check_manifest=check,
        adapter_manifest=adapter_manifest,
        complete_family_operand=complete_family_operand,
        strict_subset_operand=strict_subset_operand,
        role_bindings=MULTIPLE_TESTING_RECOGNITION_ROLE_BINDINGS,
    )
    return ScientificCheckModule(
        manifest=check,
        declared_manifest_digest=check.manifest_digest,
        adapter_manifests=(adapter_manifest,),
        adapters=(adapter,),
    )


def _multiple_testing_code_module() -> ScientificCheckModule:
    """Build the independent development-only contract/code multiple-testing module."""

    candidate = RequirementCandidate(
        candidate_id=MULTIPLE_TESTING_CODE_CANDIDATE_ID,
        label="Correct the complete authorized outcome family",
        operand=CanonicalOperand.scalar(COMPLETE_FAMILY_CORRECTION_OPERAND),
        authority_basis=(
            "Scientist-supplied ordered outcome-family authority for one full-digest CSV; the "
            "check does not infer the family, correction need, or correction method."
        ),
    )
    check = CheckManifest(
        check_id=MULTIPLE_TESTING_CODE_CHECK_ID,
        check_version=MULTIPLE_TESTING_CODE_CHECK_VERSION,
        implementation_digest=semantic_digest(
            {
                "check_id": MULTIPLE_TESTING_CODE_CHECK_ID,
                "check_version": MULTIPLE_TESTING_CODE_CHECK_VERSION,
                "candidate": candidate.to_dict(),
                "adapter_grammar_digest": code_csv_multiple_testing_grammar_digest(),
            }
        ),
        maturity_tier="question_only",
        dimension="selection_process",
        comparison_form="value_equals",
        requirement_candidates=(candidate,),
        semantic_roles=MULTIPLE_TESTING_CODE_SEMANTIC_ROLES,
        required_record_types=(
            "answer",
            "artifact",
            "asset_identity",
            "file_record",
            "parser_result",
            "publication_surface",
            "repository_snapshot",
            "semantic_assertion",
        ),
        permitted_wording=(
            "Which complete-family correction rule governs the ordered authorized outcome "
            "family for this review?"
        ),
        prohibited_inferences=(
            "execution",
            "historical_intent",
            "numerical_causality",
            "scientific_correctness",
            "correction_was_not_applied_outside_the_analyzed_source",
            "authorized_outcomes_should_scientifically_form_one_family",
        ),
    )
    adapter_manifest = AdapterManifest(
        adapter_id=MULTIPLE_TESTING_CODE_ADAPTER_ID,
        adapter_version=MULTIPLE_TESTING_CODE_ADAPTER_VERSION,
        implementation_digest=CODE_CSV_MULTIPLE_TESTING_ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=code_csv_multiple_testing_grammar_digest(),
        parser_id="parser:python-ast-tokenize",
        parser_version="0.15.1",
        source_language="python",
        evidence_plane="static_source",
        semantic_roles=MULTIPLE_TESTING_CODE_SEMANTIC_ROLES,
        applicability_profile="bounded-code-csv-multiple-testing-conflict-v1",
        counterevidence_profiles=MULTIPLE_TESTING_CODE_COUNTEREVIDENCE,
        known_gaps=(
            "analysis paths outside one root analysis.py",
            "test and correction APIs outside the exact registries",
            "helper, container, selection, threshold, and sink shapes outside the closed grammar",
            "unsupported inferential siblings and resampling structures",
            "upstream, downstream, imported, file-loaded, and externally applied corrections",
            "static source and CSV structure do not establish execution or scientific correctness",
        ),
    )
    adapter = CodeCsvMultipleTestingAdapter(
        check_manifest=check,
        adapter_manifest=adapter_manifest,
        complete_operand=candidate.operand,
        none_operand=CanonicalOperand.scalar(NO_RECOGNIZED_FAMILY_CORRECTION_OPERAND),
        strict_subset_operand=CanonicalOperand.scalar(STRICT_SUBSET_FAMILY_CORRECTION_OPERAND),
        role_bindings=MULTIPLE_TESTING_CODE_ROLE_BINDINGS,
    )
    return ScientificCheckModule(
        manifest=check,
        declared_manifest_digest=check.manifest_digest,
        adapter_manifests=(adapter_manifest,),
        adapters=(adapter,),
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
                CanonicalOperand.scalar(same_stratum),
                (
                    r"(?is)\b(?:for\s+each\s+replicate|replicate[- ]specific(?:ally)?)\b[^.]{0,220}\bexpected\s+(?:value|count)\b[^.]{0,160}\barithmetic\s+mean\b",
                    r"(?is)\b(?:same\s+diagonal|on\s+(?:that|the)\s+diagonal|same[- ]distance|same\s+(?:genomic\s+)?(?:distance|separation))\b",
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
            ReportOperandRule(
                CanonicalOperand.scalar(exclude),
                (
                    r"(?is)\b(?:target\s+pair|focal\s+pixel|focal\s+observation|focal\s+target)\b[^.]{0,120}\b(?:left\s+out|omitted|removed)\s+(?:from|of)\s+(?:its(?:\s+own)?\s+)?(?:expected(?:[- ]count)?\s+)?(?:training|background)\b",
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


def _mvmr_covariance_module(*, qualified_lane: bool = False) -> ScientificCheckModule:
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
        implementation_digest=_QUALIFIED_DEPENDENCE_CHECK_IMPLEMENTATION_DIGEST,
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
        parser_version="0.2.0",
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
    """Recognize the founder orientation an emission uses from operations alone.

    v2.0.0 (ADR-0069): recognition is delegated to the fused
    founder-orientation adapter, which reconciles the report's stated marker
    total, agreement count, and rate arithmetically and resolves the workflow
    source's emission comparison by bounded static dataflow. Nomenclature
    never gates recognition, so this profile carries no report grammar rules
    or lexical triggers; the retired two-sentence grammar answered whether the
    report claimed a repair, while the reviewable operand is whether an
    orientation repair sits on the dataflow path.

    v2.0.1 closes an adversarial review of that recognizer. The report plane
    no longer resolves on its own, conditional repair is no longer recognized
    at all, and the dataflow trace abstains for aliased mutation, unhandled
    assignment forms, rebound callables, unreadable emission selectors,
    reversed dict-spread precedence, in-memory report writes, and expressions
    deeper than its bound.

    v2.1.0 inverts the trust model that a second adversarial review broke.
    v2.0.1 enumerated dangerous forms and treated unlisted Python as safe;
    thirteen ordinary workflows exploited that to produce an answer opposite
    to run time. The dataflow trace now holds an explicit whitelist of the
    statement and expression forms it models completely, and any form outside
    that whitelist anywhere in the workflow leaves the document unsupported.

    Semantic v3 is an independent shadow adapter beside the frozen v2 tuple.
    It proposes typed dataflow certificates to a smaller verifier kernel;
    adapter disagreement remains an abstention under the registry reducer.
    """

    direct = "use_supplied_founder_alleles_directly_in_hmm_emission"
    repaired = "repair_ril_founder_orientation_before_hmm_emission"
    authority_basis = (
        "Closed review choice; the check does not select it for the scientist, does not infer "
        "the intended allele coding, and does not treat file, column, or function names as "
        "scientific authority."
    )
    return _ReportProfile(
        check_id="check:founder-orientation-before-hmm-emission",
        dimension="scale_and_orientation",
        candidates=(
            _candidate(
                "repair-before-emission",
                "Repair founder orientation before emission",
                repaired,
                authority_basis,
            ),
            _candidate(
                "use-supplied-orientation",
                "Use supplied founder orientation",
                direct,
                authority_basis,
            ),
        ),
        semantic_roles=("founder_allele_input", "hmm_emission", "orientation_step"),
        role_bindings=(
            RoleBinding("founder_allele_input", "supplied_founder_alleles"),
            RoleBinding("hmm_emission", "founder_origin_emission"),
            RoleBinding("orientation_step", "before_emission"),
        ),
        rules=(),
        triggers=(),
        question_wording=(
            "Which founder-allele orientation rule governs the HMM emission for this review?"
        ),
        check_version="2.2.6",
        adapter_version="2.2.6",
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
            ReportOperandRule(
                CanonicalOperand.scalar(directional_split),
                (
                    r"(?is)\b(?:reported|supplied)\b.{0,300}?\baverage\s+of\s+(?:the\s+)?(?:two\s+)?directional\s+(?:(?:allele[- ])?miscall|measurement[- ]error|error)\s+rates?\b",
                    r"(?is)\b(?:given|using|with)\b[^.]*\b(?:stated|supplied|instrument|baseline|low)\b[^.]*\b(?:error|miscall)\b[^.]*\bdirection\b",
                    r"(?is)\b(?:complementary|other)\s+direction\b[^.]*\b(?:evaluat(?:e|ed|ing)|assign(?:ment|ed)|comput(?:e|ed|ing)|deriv(?:e|ed|ing))\b|\b(?:evaluat(?:e|ed|ing)|assign(?:ment|ed))\b[^.]*\bboth\s+(?:possible\s+)?assignments?\b",
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
                CanonicalOperand.scalar(called),
                (
                    r"(?is)\b(?:uncalled|masked)\s+gaps?\b[^.]{0,120}\b(?:rejected|filtered|low[- ]confidence)\s+intervals?\b[^.]{0,120}\b(?:were\s+)?(?:omitted|excluded)\s+from\s+(?:the\s+)?ancestry\s+exposure\b",
                    r"(?i)t\s*=\s*N[_ ]?switch\s*/\s*\(\s*\(\s*1\s*-\s*p[_ ]?A\s*\)\s*L[_ ]?A\s*\+\s*p[_ ]?A\s*L[_ ]?B\s*\)",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(called),
                (
                    r"(?is)\b(?:single[- ]pulse|pulse\s+time)\b.{0,700}\b(?:two[- ]state|ancestry[- ]switch|transition)\b",
                    r"(?is)\b(?:retained\s+)?called\s+(?:tract\s+)?length\s+only\b",
                    r"(?is)\bdid\s+not\s+use\s+(?:the\s+)?full\s+(?:chromosome|genetic)[- ]map\s+length\s+as\s+(?:the\s+)?denominator\b",
                ),
                match_scope="document",
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
            r"(?is)(?=.*\b(?:single[- ]pulse|pulse\s+time)\b)(?=.*\bdid\s+not\s+use\s+(?:the\s+)?full\s+(?:chromosome|genetic)[- ]map\s+length\s+as\s+(?:the\s+)?denominator\b)",
        ),
        question_wording=(
            "Which chromosome-length exposure definition governs pulse timing for this review?"
        ),
        check_version="1.2.0",
        adapter_version="1.2.0",
    )


def _complete_domain_exposure_profile() -> _ReportProfile:
    """Recognize a selected denominator's domain from quantity arithmetic alone.

    v2.0.0 (ADR-0069): recognition is delegated to the quantity-consistency
    adapter, which reconciles the report's stated counts and rate
    arithmetically. Nomenclature never gates recognition, so this profile
    carries no report grammar rules or lexical triggers; two blind pilots
    demonstrated that closed word lists over free prose do not generalize.
    """

    complete = "complete_declared_domain_exposure"
    retained = "retained_observed_subset_exposure_only"
    authority_basis = (
        "Scientist-supplied denominator-domain requirement for one selected rate or spacing "
        "estimate; the check does not infer the governing domain, impute unobserved states, "
        "choose a missing-data treatment, or treat file and variable names as scientific "
        "authority."
    )
    return _ReportProfile(
        check_id="check:complete-domain-exposure-denominator",
        dimension="denominator_or_universe",
        candidates=(
            _candidate(
                "complete-declared-domain-exposure",
                "Use the complete declared domain as exposure",
                complete,
                authority_basis,
            ),
            _candidate(
                "retained-observed-subset-exposure",
                "Use only the retained observed subset as exposure",
                retained,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "selected_rate_or_spacing_estimate",
            "exposure_denominator",
            "declared_domain",
            "retained_observed_subset",
        ),
        role_bindings=(
            RoleBinding(
                "selected_rate_or_spacing_estimate",
                "reported_primary_rate_spacing_or_recurrence_target",
            ),
            RoleBinding("exposure_denominator", "reported_selected_target_denominator"),
            RoleBinding("declared_domain", "complete_scientist_governed_exposure_domain"),
            RoleBinding(
                "retained_observed_subset",
                "reported_observed_or_high_confidence_subset_of_declared_domain",
            ),
        ),
        rules=(),
        triggers=(),
        question_wording=(
            "Which declared-domain exposure governs the selected rate or spacing denominator "
            "for this review?"
        ),
        check_version="2.0.7",
        adapter_version="2.0.7",
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
                CanonicalOperand.scalar(preserve),
                (
                    r"(?is)\b(?:positive[- ]length\s+)?(?:uncalled|missing|masked|unobserved)\s+gaps?\b[^.]{0,180}\b(?:exact\s+)?(?:two[- ]state\s+)?transition\s+(?:matrix|probabilit\w*)\b[^.]{0,180}\bintegrat(?:e|ed|ing)\b[^.]{0,180}\b(?:hidden\s+)?(?:switches|transitions|paths?)\b",
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
            r"(?is)(?=.*\b(?:uncalled|missing|masked|unobserved)\s+gaps?\b)(?=.*\btransition\s+(?:matrix|probabilit\w*)\b)(?=.*\bintegrat(?:e|ed|ing)\b[^.]{0,180}\b(?:hidden\s+)?(?:switches|transitions|paths?)\b)",
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
        check_version="1.2.0",
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
                CanonicalOperand.scalar(aggregate_first),
                (
                    r"(?i)\b(?:directly\s+)?standardiz(?:ed|ing)[^.]*\b(?:observed|completed[- ]test)\b[^.]*\b(?:assay[- ]?)?(?:outcome|call|class)\s+(?:rates?|distributions?)\b",
                    r"(?i)\bthen\s+(?:applied|used|performed)[^.]*\b(?:control|calibration|confusion|misclassification)\b[^.]*\b(?:correction|calibrat(?:ed|ion)|deconvol(?:ved|ution)|invert(?:ed|ing))\b",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(constrained_cellwise),
                (
                    r"(?i)\b(?:nonnegative|simplex|probability)[- ]constrained\s+(?:joint\s+)?(?:calibration|deconvolution|class(?:-prevalence)?\s+estimation)\b",
                    r"(?i)\b(?:within|inside|for)\s+each\s+(?:(?:target[- ]population|sampling[- ]frame)\s+)?(?:post-?strat(?:ification\s+)?cell|post-?stratum|cell)\b",
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
                CanonicalOperand.scalar(sequential_imputation),
                (
                    r"(?is)\bmodel(?:ed|ing)?\b[^.;]{0,100}\b(?:assessment|assessability|observation)\b[^.;]{0,180}\b(?:treatment|exposure)\b[^.;]{0,160}\b(?:toxicity|adverse\s+event|intermediate\s+endpoint|mediator)\b",
                    r"(?is)\bmodel(?:ed|ing)?\b[^.;]{0,100}\b(?:benefit|later\s+outcome|outcome)\b[^.;]{0,100}\bamong\s+assessed\b[^.;]{0,180}\b(?:toxicity|adverse\s+event|intermediate\s+endpoint|mediator)\b",
                    r"(?is)\bintegrat(?:e|ed|ing)\b[^.;]{0,120}\b(?:toxicity|adverse\s+event|intermediate\s+endpoint|mediator)\b[^.;]{0,160}\bunder\s+each\s+(?:treatment|exposure)\b[^.;]{0,160}\bbefore\s+standardiz(?:e|ed|ing)\b",
                ),
                match_scope="document",
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
            r"(?is)(?=.*\bmodel(?:ed|ing)?\b[^.;]{0,100}\b(?:assessment|assessability|observation)\b)(?=.*\bmodel(?:ed|ing)?\b[^.;]{0,100}\b(?:benefit|later\s+outcome|outcome)\b[^.;]{0,100}\bamong\s+assessed\b)(?=.*\bintegrat(?:e|ed|ing)\b[^.;]{0,160}\bunder\s+each\s+(?:treatment|exposure)\b)",
        ),
        question_wording=(
            "Which missing-outcome transport strategy governs the treatment-effect estimate for "
            "this review?"
        ),
        check_version="1.2.0",
        adapter_version="1.2.0",
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
                CanonicalOperand.scalar(copy_ceiling),
                (
                    r"(?is)\btarget\s+(?:membership|eligibility|population|gate)\b.{0,500}\b(?:case|record|sample|unit)\b[^.]{0,120}\bhad\s+to\s+meet\s+all\s+of\s+the\s+following\b",
                    r"(?is)\b(?:alternate|variant)[- ]+(?:molecule|allele|read)[- ]fraction\b[^.;]{0,100}(?:>=|≥|at\s+least|above)",
                    r"(?is)\b(?:local\s+)?(?:total\s+)?copy(?:\s+number)?\b[^.;]{0,100}(?:<|≤|below|less\s+than|ceiling)",
                ),
                match_scope="document",
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
        check_version="1.2.0",
        adapter_version="1.2.0",
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
                CanonicalOperand.scalar(include_availability),
                (
                    r"(?is)\b(?:formed|constructed|defined)\s+(?:exact\s+)?(?:poststrata|standardization\s+cells)\s+from\b(?=[^.]*\b(?:ancestry|substantive\s+risk)\b)(?=[^.]*\bfamily[- ]history(?:\s+tier)?\b)(?=[^.]*\b(?:intake\s+)?site\b)(?=[^.]*\b(?:collection\s+)?wave\b)[^.]*",
                    r"(?is)\bcompleted[- ](?:partner|participant|row|test)\s+(?:positive\s+)?(?:rate|distribution)\s+in\s+each\s+cell\s+(?:is|was)\s+weighted\s+by\s+(?:that|the)\s+cell(?:'s)?\s+share\s+of\s+all\s+(?:[0-9][0-9,]*\s+)?(?:ancestry[- ]specific\s+)?(?:roster|target[- ]population)\s+rows\b",
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
            r"(?is)(?=.*\b(?:poststrata|standardization\s+cells)\b)(?=.*\bcompleted[- ](?:partner|participant|row|test)\b)(?=.*\b(?:roster|target[- ]population)\s+rows\b)(?=.*\b(?:site|center)\b)(?=.*\b(?:wave|period)\b)",
        ),
        question_wording=(
            "Which conditioning set governs direct standardization from completed rows to the "
            "full target roster for this review?"
        ),
        check_version="1.1.0",
        adapter_version="1.1.0",
    )


def _classifier_copy_dosage_profile() -> _ReportProfile:
    """Recognize the copy-dosage exposure representation from operations alone.

    v2.0.0 (ADR-0069): recognition is delegated to the fused copy-dosage
    adapter, which resolves the workflow source's exposure operand by bounded
    static dataflow and reads the report's per-state dosage accounting only as
    corroboration. Nomenclature never gates recognition, so this profile
    carries no report grammar rules or lexical triggers; the retired v1.x
    grammar answered whether the report claimed a representation, while the
    reviewable operand is which representation the value entering the fitted
    model actually carries. The three ADR-0024 operands are unchanged.

    v2.0.1 closes the first adversarial review of that recognizer: per-value
    provenance identity, default-deny mutation, literal lookup tables read as
    binnings, and hermetic imports.

    v2.0.2 closes a second review, shape-level throughout. A ``**`` unpacking
    makes a call unreadable and mutating; every recognized call and method
    states the positional arity it reads, so anything past that arity is a
    destination; aliasing follows shared runtime buffers rather than
    assignment syntax; one estimator evaluation owns one provenance identity;
    ``numpy.where`` is a selection rather than arithmetic unless both branches
    are literals; and a subscript indexed by a traced value is a gather. The
    adapter also abstains when the frozen contract's three operand values are
    not pairwise distinct.

    v2.0.3 closes the fourth adversarial review: conversion aliasing follows
    whether a call necessarily creates a new buffer, starred positional calls
    abstain, estimator evaluation identities ignore argument spelling, fitted
    estimators merge by constructor path and fit signature, ``numpy.where`` is
    treated as selection, and only closed row-index forms retain selection
    semantics.

    v2.0.4 closes the final pre-pilot review: arithmetic cannot regain a
    continuous classification through an operand annihilated by an exact
    zero, zero exponent, or constant clip; bare-statement estimator ``fit``
    calls merge their fitted identity back into the receiver; and arithmetic
    origins are derived from semantic operand roles so operand order cannot
    change the representation conclusion.
    """

    hard_call = "integer_hard_copy_state_as_numeric_dosage"
    expected_dosage = "continuous_posterior_expected_copy_dosage"
    direct_dosage = "direct_continuous_calibrated_copy_dosage"
    authority_basis = (
        "Scientist-supplied exposure estimand and measurement-uncertainty policy; the check does "
        "not choose a representation, and does not treat variable, column, or file names as "
        "scientific authority."
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
        rules=(),
        triggers=(),
        question_wording=(
            "Which calibrated copy-number representation governs the quantitative "
            "exposure for this review?"
        ),
        check_version="2.0.4",
        adapter_version="2.0.4",
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
            ReportOperandRule(
                CanonicalOperand.scalar(omit_group),
                (
                    r"(?is)\b(?:ambient[- ]only|negative[- ]control)\b[^.]{0,120}\b(?:marker|proxy)\b",
                    r"(?is)\b(?:allows?|estimat(?:e|ed|ing))\b[^.]{0,180}\b(?:contamination|technical[- ]signal)\b[^.]{0,120}\b(?:differ|vary)\b[^.]{0,80}\b(?:cell|observation|sample)\b",
                    r"(?is)\b(?:for\s+each|by)\s+(?:donor|subject|sample|participant|cluster)\b[^.]{0,180}\b(?:pseudobulk(?:ed|ing)?|aggregat(?:e|ed|ing)|summ(?:ed|ing))\b",
                    r"(?is)\bprimary\s+(?:association\s+)?model\s+was\b[^.]{0,300}\bexp\((?:(?!\b(?:batch|plate|wave|technical|contamination|proxy|group)\b)[^()]){1,320}\)",
                ),
                match_scope="document",
            ),
        ),
        triggers=(
            r"(?is)(?=.*\b(?:reconstruct|recover)[^.]*\btechnical[- ]group\b)(?=.*\b(?:covariate|adjustment)\b)",
            r"(?is)(?=.*\b(?:ambient[- ]group|technical[- ]group)\b)(?=.*\b(?:covariate|adjustment)\b)",
            r"(?is)(?=.*\b(?:ambient[- ]only|negative[- ]control)\b[^.]{0,120}\b(?:marker|proxy)\b)(?=.*\b(?:donor|subject|sample|participant|cluster)\b[^.]{0,180}\b(?:pseudobulk|aggregat|summ))(?=.*\bprimary\s+(?:association\s+)?model\b)",
        ),
        question_wording=(
            "Which treatment of a recoverable technical grouping governs the primary association "
            "adjustment set for this review?"
        ),
        check_version="1.2.0",
        adapter_version="1.2.0",
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


def _local_perturbation_row_scope_profile() -> _ReportProfile:
    full_assay = "full_assay_rows_after_cross_modal_residual_screening"
    nominal_subset = "nominal_focal_target_rows_only"
    authority_basis = (
        "Scientist-supplied primary-model row-scope and cross-modal QC requirement; the check "
        "does not infer that residual screening is valid, choose a residual cutoff, or treat a "
        "benchmark answer as scientific authority."
    )
    return _ReportProfile(
        check_id="check:local-perturbation-primary-row-scope",
        dimension="analysis_population",
        candidates=(
            _candidate(
                "full-assay-after-cross-modal-screening",
                "Fit the local perturbation model on full-assay rows after cross-modal residual screening",
                full_assay,
                authority_basis,
            ),
            _candidate(
                "nominal-focal-target-subset",
                "Fit the local perturbation model only on rows nominally assigned to the focal target",
                nominal_subset,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "primary_local_model",
            "assay_row_population",
            "cross_modal_residual_screen",
            "nominal_target_assignment",
        ),
        role_bindings=(
            RoleBinding("primary_local_model", "reported_local_perturbation_model"),
            RoleBinding("assay_row_population", "reported_model_fitting_rows"),
            RoleBinding("cross_modal_residual_screen", "reported_pre_fit_row_screen"),
            RoleBinding("nominal_target_assignment", "reported_focal_row_filter"),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(full_assay),
                (
                    r"(?is)(?=.*\b(?:first[- ]pass|initial)\s+(?:local\s+)?(?:model|fit)\b)(?=.*\b(?:cross[- ]modal|count[- ]expression|measurement[- ]outcome)\b[^.]{0,220}\b(?:contradiction\w*|residual\w*|discordan\w*)\b)(?=.*\b(?:rows?|guides?|features?|observations?)\b[^.]{0,160}\b(?:exclude|remove|retain|screen|flag)\w*\b)(?=.*\brefit\b)",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(nominal_subset),
                (
                    r"(?is)\b(?:used|fit|restricted\s+to)\b[^.]{0,100}\b(?:the\s+)?\d+\s+(?:rows?|guides?|features?|observations?)\b[^.]{0,160}\bnominally\s+(?:aimed|assigned|targeted|annotated)\b[^.]{0,160}\b(?:locus|target|region|feature)\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)(?=.*\b(?:rows?|guides?|features?|observations?)\b)(?=.*\bnominal(?:ly)?\s+(?:aimed|assigned|targeted|annotated)\b)(?=.*\b(?:local[- ]locus|local\s+perturbation|neighbor[- ]mediated|adjacent[- ]target)\s+(?:model|effect|component)\b)",
            r"(?is)(?=.*\b(?:first[- ]pass|initial)\s+(?:local\s+)?(?:model|fit)\b)(?=.*\b(?:cross[- ]modal|count[- ]expression|measurement[- ]outcome)\b)(?=.*\brefit\b)",
        ),
        question_wording=(
            "Which assay-row scope and cross-modal screening rule governs the primary local "
            "perturbation model for this review?"
        ),
    )


def _local_perturbation_regression_profile() -> _ReportProfile:
    joint_adjusted = "joint_target_axes_with_observed_guide_nuisance_terms"
    residualized_single_axis = "external_target_subtraction_then_single_remaining_axis"
    authority_basis = (
        "Scientist-supplied local perturbation estimand and adjustment set; the check does not "
        "infer which measured guide features are causal nuisances or use numeric agreement as "
        "scientific authority."
    )
    return _ReportProfile(
        check_id="check:local-perturbation-regression-specification",
        dimension="adjustment_set",
        candidates=(
            _candidate(
                "joint-target-axes-with-guide-nuisance-terms",
                "Jointly fit measured target axes with observed guide-level nuisance terms",
                joint_adjusted,
                authority_basis,
            ),
            _candidate(
                "external-subtraction-then-single-axis",
                "Subtract an externally estimated target contribution, then fit one remaining target axis",
                residualized_single_axis,
                authority_basis,
            ),
        ),
        semantic_roles=(
            "local_perturbation_outcome",
            "measured_target_axes",
            "guide_level_nuisance_terms",
            "external_target_contribution",
        ),
        role_bindings=(
            RoleBinding("local_perturbation_outcome", "reported_primary_local_effect"),
            RoleBinding("measured_target_axes", "reported_local_knockdown_predictors"),
            RoleBinding("guide_level_nuisance_terms", "reported_primary_adjustment_set"),
            RoleBinding("external_target_contribution", "reported_pre_fit_subtraction"),
        ),
        rules=(
            ReportOperandRule(
                CanonicalOperand.scalar(joint_adjusted),
                (
                    r"(?is)(?=.*\b(?:joint|same|single)\s+(?:linear\s+)?(?:local\s+)?(?:perturbation\s+)?(?:model|regression|fit)\b)(?=.*\b(?:measured|observed)\b[^.]{0,180}\b(?:knockdown|repression|target)\b)(?=.*\b(?:guide[- ]level|sequence|composition|GC)\b[^.]{0,160}\b(?:nuisance|covariate|excess|adjust)\w*\b)(?=.*\b(?:promoter|position|distance|core)[- ]\w*\b[^.]{0,160}\b(?:indicator|term|covariate|adjust)\w*\b)",
                ),
            ),
            ReportOperandRule(
                CanonicalOperand.scalar(residualized_single_axis),
                (
                    r"(?is)\b(?:first\s+)?(?:removed|subtracted)\b[^.]{0,240}\b(?:external(?:ly)?\s+(?:identified|estimated)\s+)?(?:transcript|target|component)\s+contribution\b[^.]{0,240}\bthen\s+fit\s+an?\s+intercept\s+plus\s+[^.]{1,80}\b(?:Huber|robust|ordinary|linear)\s+(?:regression|fit|model)\b",
                ),
            ),
        ),
        triggers=(
            r"(?is)(?=.*\b(?:local[- ]locus|local\s+perturbation|neighbor[- ]mediated|adjacent[- ]target)\s+(?:model|effect|component)\b)(?=.*\b(?:removed|subtracted)\b[^.]{0,240}\b(?:transcript|target|component)\s+contribution\b)(?=.*\b(?:regression|fit|model)\b)",
            r"(?is)(?=.*\b(?:same|joint|primary)\s+(?:linear\s+)?(?:local\s+)?(?:perturbation\s+)?(?:model|regression|fit)\b)(?=.*\b(?:guide[- ]level|sequence|composition|GC)\b)(?=.*\b(?:promoter|position|distance|core)\b)",
        ),
        question_wording=(
            "Which target-axis and guide-nuisance specification governs the primary local "
            "perturbation effect for this review?"
        ),
    )


def _dependence_recognition_profile(*, qualified: bool = False) -> _ReportProfile:
    authority_basis = (
        "Scientist-supplied independent-unit authority for this exact analysis, procedure, "
        "ordered key, and frozen input; the check does not infer the unit from column names "
        "or repetition."
    )
    return _ReportProfile(
        check_id=DEPENDENCE_RECOGNITION_CHECK_ID,
        check_version=(
            QUALIFIED_DEPENDENCE_RECOGNITION_CHECK_VERSION
            if qualified
            else DEPENDENCE_RECOGNITION_CHECK_VERSION
        ),
        adapter_version=(
            QUALIFIED_CODE_CSV_DEPENDENCE_ADAPTER_VERSION
            if qualified
            else CODE_CSV_DEPENDENCE_ADAPTER_VERSION
        ),
        dimension="dependence_structure",
        candidates=(
            _candidate(
                DEPENDENCE_RECOGNITION_CANDIDATE_ID,
                "Use one analyzed row per authorized independent unit",
                ONE_ROW_PER_AUTHORIZED_UNIT,
                authority_basis,
            ),
        ),
        semantic_roles=(
            QUALIFIED_CODE_CSV_DEPENDENCE_SEMANTIC_ROLES
            if qualified
            else CODE_CSV_DEPENDENCE_SEMANTIC_ROLES
        ),
        role_bindings=(
            QUALIFIED_CODE_CSV_DEPENDENCE_ROLE_BINDINGS
            if qualified
            else CODE_CSV_DEPENDENCE_ROLE_BINDINGS
        ),
        rules=(),
        triggers=(),
        question_wording=(
            "Which analyzed-row entry rule relative to the authorized independent-unit key "
            "governs this review?"
        ),
        extra_record_types=(
            "answer",
            "file_record",
            "repository_snapshot",
            "semantic_assertion",
        ),
    )


def _multiple_testing_recognition_profile() -> _ReportProfile:
    authority_basis = (
        "Scientist-supplied family authority for this exact battery construct, ordered row "
        "domain, key columns, frozen family input, analysis, and correction procedure; the "
        "check does not infer the test family from values or column names."
    )
    return _ReportProfile(
        check_id=MULTIPLE_TESTING_RECOGNITION_CHECK_ID,
        check_version=MULTIPLE_TESTING_RECOGNITION_CHECK_VERSION,
        adapter_version=MULTIPLE_TESTING_RECOGNITION_ADAPTER_VERSION,
        dimension="selection_process",
        candidates=(
            _candidate(
                MULTIPLE_TESTING_RECOGNITION_CANDIDATE_ID,
                "Correct the complete performed test battery",
                COMPLETE_FAMILY_CORRECTION,
                authority_basis,
            ),
        ),
        semantic_roles=MULTIPLE_TESTING_RECOGNITION_SEMANTIC_ROLES,
        role_bindings=MULTIPLE_TESTING_RECOGNITION_ROLE_BINDINGS,
        rules=(),
        triggers=(),
        question_wording=(
            "Which correction-family entry rule relative to the authorized performed test "
            "battery governs this review?"
        ),
        extra_record_types=(
            "analysis",
            "family_authorization",
            "file_record",
            "procedure",
            "repository_snapshot",
            "result",
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
