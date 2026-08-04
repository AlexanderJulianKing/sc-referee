"""Isolated answer-side validation for sc-referee qualification evidence."""

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sc_referee_evaluation.analysis_method_qualification import (
        AnalysisMethodQualificationError,
        freeze_bounded_analysis_method_profile,
        revalidate_analysis_method_proof,
        verify_bounded_analysis_method_case,
    )
    from sc_referee_evaluation.candidate import (
        EvaluationCandidateProjectionError,
        project_evaluation_candidate,
    )
    from sc_referee_evaluation.capture import (
        ReviewCaptureError,
        capture_review_submission,
        load_review_capture,
    )
    from sc_referee_evaluation.comparison import (
        DetectorComparisonError,
        compare_detector_output,
    )
    from sc_referee_evaluation.corpus import (
        CorpusPreflightError,
        preflight_genebench_public_package,
    )
    from sc_referee_evaluation.direct_qualification_lane import (
        AUTHORING_BRIEF_MANIFEST_VERSION,
        DIRECT_LANE_FREEZE_VERSION,
        PARTICIPANT_ENROLLMENT_VERSION,
        DirectQualificationLaneError,
        freeze_authoring_brief_manifest,
        freeze_direct_qualification_lane,
        freeze_participant_enrollment,
        validate_authoring_brief_manifest,
        validate_direct_qualification_lane,
        validate_participant_enrollment,
    )
    from sc_referee_evaluation.fixture import (
        FixtureGenerationError,
        FixtureProofInputs,
        generate_ambiguous_fixture,
        generate_control_fixture,
        generate_positive_fixture,
        revalidate_fixture_proof,
    )
    from sc_referee_evaluation.genebench_grader import (
        GeneBenchNumericGradeError,
        grade_genebench_public_answer,
        grade_genebench_public_numeric_answer,
    )
    from sc_referee_evaluation.grader import ExactJsonGraderError, grade_exact_json_output
    from sc_referee_evaluation.method_contract_diagnostic import (
        MethodContractDiagnosticError,
        diagnose_genebench_method_contract_conflict,
    )
    from sc_referee_evaluation.metrics import (
        QualificationMetricError,
        bootstrap_cluster_index,
        bootstrap_problem_sample,
        build_qualification_metric_set,
    )
    from sc_referee_evaluation.prospective_qualification import (
        PROTOCOL_VERSION as PROSPECTIVE_QUALIFICATION_PROTOCOL_VERSION,
    )
    from sc_referee_evaluation.prospective_qualification import (
        REQUIRED_CELL_TYPES,
        ProspectiveQualificationError,
        freeze_pilot_threshold_decision,
        freeze_prospective_qualification_protocol,
        seal_prospective_outcome_ledger,
    )
    from sc_referee_evaluation.prospective_qualification_v2 import (
        AUTHOR_DECLARATION_VERSION,
        CASE_EVIDENCE_CONTRACT_VERSION,
        SCIENTIFIC_LABEL_VERSION,
        ProspectiveQualificationV2Error,
        freeze_author_selected_result_declaration,
        freeze_case_evidence_contract,
        freeze_stage2_scientific_label,
        validate_author_selected_result_declaration,
        validate_case_evidence_contract,
    )
    from sc_referee_evaluation.prospective_selected_result_verifier import (
        DERIVATION_VERSION as SELECTED_RESULT_DERIVATION_VERSION,
    )
    from sc_referee_evaluation.prospective_selected_result_verifier import (
        PYTHON_STATIC_MARKED_REPORT_PROFILE,
        ProspectiveSelectedResultVerifierError,
        freeze_independent_selected_result_derivation,
        freeze_selected_result_validation,
        revalidate_independent_selected_result_derivation,
        validate_independent_selected_result_derivation,
        validate_selected_result_validation,
    )
    from sc_referee_evaluation.prospective_selected_result_verifier import (
        VALIDATION_VERSION as SELECTED_RESULT_VALIDATION_VERSION,
    )
    from sc_referee_evaluation.prospective_selected_result_verifier import (
        VERIFIER_VERSION as SELECTED_RESULT_VERIFIER_VERSION,
    )
    from sc_referee_evaluation.regression_baseline import (
        MODULE_BASELINE_REQUIREMENTS_VERSION,
        RegressionModuleBaselineError,
        regression_module_baseline_gaps,
        regression_module_baseline_projection,
        validate_regression_module_baselines,
    )
    from sc_referee_evaluation.regression_corpus import (
        DEFAULT_REGRESSION_CORPUS_LEDGER,
        REGRESSION_CORPUS_LEDGER_VERSION,
        RegressionCorpusLedgerError,
        regression_tree_digest,
        validate_regression_corpus_ledger,
    )
    from sc_referee_evaluation.regression_runner import (
        DEFAULT_REGRESSION_CORPUS_EXECUTION_PLAN,
        REGRESSION_CORPUS_EXECUTION_PLAN_VERSION,
        REGRESSION_CORPUS_RUNNER_VERSION,
        RegressionCorpusRunnerError,
        compare_corpus_semantic_outcome,
        corpus_semantic_projection,
        run_regression_corpus,
        validate_regression_corpus_execution_plan,
    )
    from sc_referee_evaluation.root_cause import (
        RootCauseReconciliationError,
        build_adjudicated_root_cause,
        validate_adjudicated_root_cause,
    )
    from sc_referee_evaluation.source_method_probe import (
        PROFILE_MANIFEST,
        SourceMethodProbeError,
        probe_python_method_shapes,
    )
    from sc_referee_evaluation.stage3 import (
        Stage3ProtocolError,
        build_stage3_review_packet,
        reconcile_detector_case,
        validate_stage3_review_submission,
    )
    from sc_referee_evaluation.validation import EvaluationValidationError, validate_case_packet

_LAZY_EXPORTS = {
    "AnalysisMethodQualificationError": (
        "sc_referee_evaluation.analysis_method_qualification",
        "AnalysisMethodQualificationError",
    ),
    "freeze_bounded_analysis_method_profile": (
        "sc_referee_evaluation.analysis_method_qualification",
        "freeze_bounded_analysis_method_profile",
    ),
    "revalidate_analysis_method_proof": (
        "sc_referee_evaluation.analysis_method_qualification",
        "revalidate_analysis_method_proof",
    ),
    "verify_bounded_analysis_method_case": (
        "sc_referee_evaluation.analysis_method_qualification",
        "verify_bounded_analysis_method_case",
    ),
    "EvaluationCandidateProjectionError": (
        "sc_referee_evaluation.candidate",
        "EvaluationCandidateProjectionError",
    ),
    "project_evaluation_candidate": (
        "sc_referee_evaluation.candidate",
        "project_evaluation_candidate",
    ),
    "ReviewCaptureError": ("sc_referee_evaluation.capture", "ReviewCaptureError"),
    "capture_review_submission": (
        "sc_referee_evaluation.capture",
        "capture_review_submission",
    ),
    "load_review_capture": ("sc_referee_evaluation.capture", "load_review_capture"),
    "DetectorComparisonError": (
        "sc_referee_evaluation.comparison",
        "DetectorComparisonError",
    ),
    "compare_detector_output": (
        "sc_referee_evaluation.comparison",
        "compare_detector_output",
    ),
    "CorpusPreflightError": ("sc_referee_evaluation.corpus", "CorpusPreflightError"),
    "preflight_genebench_public_package": (
        "sc_referee_evaluation.corpus",
        "preflight_genebench_public_package",
    ),
    "AUTHORING_BRIEF_MANIFEST_VERSION": (
        "sc_referee_evaluation.direct_qualification_lane",
        "AUTHORING_BRIEF_MANIFEST_VERSION",
    ),
    "DIRECT_LANE_FREEZE_VERSION": (
        "sc_referee_evaluation.direct_qualification_lane",
        "DIRECT_LANE_FREEZE_VERSION",
    ),
    "PARTICIPANT_ENROLLMENT_VERSION": (
        "sc_referee_evaluation.direct_qualification_lane",
        "PARTICIPANT_ENROLLMENT_VERSION",
    ),
    "DirectQualificationLaneError": (
        "sc_referee_evaluation.direct_qualification_lane",
        "DirectQualificationLaneError",
    ),
    "freeze_authoring_brief_manifest": (
        "sc_referee_evaluation.direct_qualification_lane",
        "freeze_authoring_brief_manifest",
    ),
    "freeze_direct_qualification_lane": (
        "sc_referee_evaluation.direct_qualification_lane",
        "freeze_direct_qualification_lane",
    ),
    "freeze_participant_enrollment": (
        "sc_referee_evaluation.direct_qualification_lane",
        "freeze_participant_enrollment",
    ),
    "validate_authoring_brief_manifest": (
        "sc_referee_evaluation.direct_qualification_lane",
        "validate_authoring_brief_manifest",
    ),
    "validate_direct_qualification_lane": (
        "sc_referee_evaluation.direct_qualification_lane",
        "validate_direct_qualification_lane",
    ),
    "validate_participant_enrollment": (
        "sc_referee_evaluation.direct_qualification_lane",
        "validate_participant_enrollment",
    ),
    "FixtureGenerationError": (
        "sc_referee_evaluation.fixture",
        "FixtureGenerationError",
    ),
    "FixtureProofInputs": ("sc_referee_evaluation.fixture", "FixtureProofInputs"),
    "generate_ambiguous_fixture": (
        "sc_referee_evaluation.fixture",
        "generate_ambiguous_fixture",
    ),
    "generate_control_fixture": (
        "sc_referee_evaluation.fixture",
        "generate_control_fixture",
    ),
    "generate_positive_fixture": (
        "sc_referee_evaluation.fixture",
        "generate_positive_fixture",
    ),
    "revalidate_fixture_proof": (
        "sc_referee_evaluation.fixture",
        "revalidate_fixture_proof",
    ),
    "GeneBenchNumericGradeError": (
        "sc_referee_evaluation.genebench_grader",
        "GeneBenchNumericGradeError",
    ),
    "grade_genebench_public_answer": (
        "sc_referee_evaluation.genebench_grader",
        "grade_genebench_public_answer",
    ),
    "grade_genebench_public_numeric_answer": (
        "sc_referee_evaluation.genebench_grader",
        "grade_genebench_public_numeric_answer",
    ),
    "ExactJsonGraderError": ("sc_referee_evaluation.grader", "ExactJsonGraderError"),
    "grade_exact_json_output": (
        "sc_referee_evaluation.grader",
        "grade_exact_json_output",
    ),
    "MethodContractDiagnosticError": (
        "sc_referee_evaluation.method_contract_diagnostic",
        "MethodContractDiagnosticError",
    ),
    "diagnose_genebench_method_contract_conflict": (
        "sc_referee_evaluation.method_contract_diagnostic",
        "diagnose_genebench_method_contract_conflict",
    ),
    "QualificationMetricError": (
        "sc_referee_evaluation.metrics",
        "QualificationMetricError",
    ),
    "bootstrap_cluster_index": (
        "sc_referee_evaluation.metrics",
        "bootstrap_cluster_index",
    ),
    "bootstrap_problem_sample": (
        "sc_referee_evaluation.metrics",
        "bootstrap_problem_sample",
    ),
    "build_qualification_metric_set": (
        "sc_referee_evaluation.metrics",
        "build_qualification_metric_set",
    ),
    "PROSPECTIVE_QUALIFICATION_PROTOCOL_VERSION": (
        "sc_referee_evaluation.prospective_qualification",
        "PROTOCOL_VERSION",
    ),
    "REQUIRED_CELL_TYPES": (
        "sc_referee_evaluation.prospective_qualification",
        "REQUIRED_CELL_TYPES",
    ),
    "ProspectiveQualificationError": (
        "sc_referee_evaluation.prospective_qualification",
        "ProspectiveQualificationError",
    ),
    "freeze_pilot_threshold_decision": (
        "sc_referee_evaluation.prospective_qualification",
        "freeze_pilot_threshold_decision",
    ),
    "freeze_prospective_qualification_protocol": (
        "sc_referee_evaluation.prospective_qualification",
        "freeze_prospective_qualification_protocol",
    ),
    "seal_prospective_outcome_ledger": (
        "sc_referee_evaluation.prospective_qualification",
        "seal_prospective_outcome_ledger",
    ),
    "CASE_EVIDENCE_CONTRACT_VERSION": (
        "sc_referee_evaluation.prospective_qualification_v2",
        "CASE_EVIDENCE_CONTRACT_VERSION",
    ),
    "AUTHOR_DECLARATION_VERSION": (
        "sc_referee_evaluation.prospective_qualification_v2",
        "AUTHOR_DECLARATION_VERSION",
    ),
    "SCIENTIFIC_LABEL_VERSION": (
        "sc_referee_evaluation.prospective_qualification_v2",
        "SCIENTIFIC_LABEL_VERSION",
    ),
    "ProspectiveQualificationV2Error": (
        "sc_referee_evaluation.prospective_qualification_v2",
        "ProspectiveQualificationV2Error",
    ),
    "freeze_case_evidence_contract": (
        "sc_referee_evaluation.prospective_qualification_v2",
        "freeze_case_evidence_contract",
    ),
    "freeze_author_selected_result_declaration": (
        "sc_referee_evaluation.prospective_qualification_v2",
        "freeze_author_selected_result_declaration",
    ),
    "freeze_stage2_scientific_label": (
        "sc_referee_evaluation.prospective_qualification_v2",
        "freeze_stage2_scientific_label",
    ),
    "validate_case_evidence_contract": (
        "sc_referee_evaluation.prospective_qualification_v2",
        "validate_case_evidence_contract",
    ),
    "validate_author_selected_result_declaration": (
        "sc_referee_evaluation.prospective_qualification_v2",
        "validate_author_selected_result_declaration",
    ),
    "PYTHON_STATIC_MARKED_REPORT_PROFILE": (
        "sc_referee_evaluation.prospective_selected_result_verifier",
        "PYTHON_STATIC_MARKED_REPORT_PROFILE",
    ),
    "ProspectiveSelectedResultVerifierError": (
        "sc_referee_evaluation.prospective_selected_result_verifier",
        "ProspectiveSelectedResultVerifierError",
    ),
    "SELECTED_RESULT_DERIVATION_VERSION": (
        "sc_referee_evaluation.prospective_selected_result_verifier",
        "DERIVATION_VERSION",
    ),
    "SELECTED_RESULT_VALIDATION_VERSION": (
        "sc_referee_evaluation.prospective_selected_result_verifier",
        "VALIDATION_VERSION",
    ),
    "SELECTED_RESULT_VERIFIER_VERSION": (
        "sc_referee_evaluation.prospective_selected_result_verifier",
        "VERIFIER_VERSION",
    ),
    "freeze_independent_selected_result_derivation": (
        "sc_referee_evaluation.prospective_selected_result_verifier",
        "freeze_independent_selected_result_derivation",
    ),
    "freeze_selected_result_validation": (
        "sc_referee_evaluation.prospective_selected_result_verifier",
        "freeze_selected_result_validation",
    ),
    "revalidate_independent_selected_result_derivation": (
        "sc_referee_evaluation.prospective_selected_result_verifier",
        "revalidate_independent_selected_result_derivation",
    ),
    "validate_independent_selected_result_derivation": (
        "sc_referee_evaluation.prospective_selected_result_verifier",
        "validate_independent_selected_result_derivation",
    ),
    "validate_selected_result_validation": (
        "sc_referee_evaluation.prospective_selected_result_verifier",
        "validate_selected_result_validation",
    ),
    "MODULE_BASELINE_REQUIREMENTS_VERSION": (
        "sc_referee_evaluation.regression_baseline",
        "MODULE_BASELINE_REQUIREMENTS_VERSION",
    ),
    "RegressionModuleBaselineError": (
        "sc_referee_evaluation.regression_baseline",
        "RegressionModuleBaselineError",
    ),
    "regression_module_baseline_gaps": (
        "sc_referee_evaluation.regression_baseline",
        "regression_module_baseline_gaps",
    ),
    "regression_module_baseline_projection": (
        "sc_referee_evaluation.regression_baseline",
        "regression_module_baseline_projection",
    ),
    "validate_regression_module_baselines": (
        "sc_referee_evaluation.regression_baseline",
        "validate_regression_module_baselines",
    ),
    "DEFAULT_REGRESSION_CORPUS_LEDGER": (
        "sc_referee_evaluation.regression_corpus",
        "DEFAULT_REGRESSION_CORPUS_LEDGER",
    ),
    "REGRESSION_CORPUS_LEDGER_VERSION": (
        "sc_referee_evaluation.regression_corpus",
        "REGRESSION_CORPUS_LEDGER_VERSION",
    ),
    "RegressionCorpusLedgerError": (
        "sc_referee_evaluation.regression_corpus",
        "RegressionCorpusLedgerError",
    ),
    "regression_tree_digest": (
        "sc_referee_evaluation.regression_corpus",
        "regression_tree_digest",
    ),
    "validate_regression_corpus_ledger": (
        "sc_referee_evaluation.regression_corpus",
        "validate_regression_corpus_ledger",
    ),
    "DEFAULT_REGRESSION_CORPUS_EXECUTION_PLAN": (
        "sc_referee_evaluation.regression_runner",
        "DEFAULT_REGRESSION_CORPUS_EXECUTION_PLAN",
    ),
    "REGRESSION_CORPUS_EXECUTION_PLAN_VERSION": (
        "sc_referee_evaluation.regression_runner",
        "REGRESSION_CORPUS_EXECUTION_PLAN_VERSION",
    ),
    "REGRESSION_CORPUS_RUNNER_VERSION": (
        "sc_referee_evaluation.regression_runner",
        "REGRESSION_CORPUS_RUNNER_VERSION",
    ),
    "RegressionCorpusRunnerError": (
        "sc_referee_evaluation.regression_runner",
        "RegressionCorpusRunnerError",
    ),
    "compare_corpus_semantic_outcome": (
        "sc_referee_evaluation.regression_runner",
        "compare_corpus_semantic_outcome",
    ),
    "corpus_semantic_projection": (
        "sc_referee_evaluation.regression_runner",
        "corpus_semantic_projection",
    ),
    "run_regression_corpus": (
        "sc_referee_evaluation.regression_runner",
        "run_regression_corpus",
    ),
    "validate_regression_corpus_execution_plan": (
        "sc_referee_evaluation.regression_runner",
        "validate_regression_corpus_execution_plan",
    ),
    "RootCauseReconciliationError": (
        "sc_referee_evaluation.root_cause",
        "RootCauseReconciliationError",
    ),
    "build_adjudicated_root_cause": (
        "sc_referee_evaluation.root_cause",
        "build_adjudicated_root_cause",
    ),
    "validate_adjudicated_root_cause": (
        "sc_referee_evaluation.root_cause",
        "validate_adjudicated_root_cause",
    ),
    "PROFILE_MANIFEST": ("sc_referee_evaluation.source_method_probe", "PROFILE_MANIFEST"),
    "SourceMethodProbeError": (
        "sc_referee_evaluation.source_method_probe",
        "SourceMethodProbeError",
    ),
    "probe_python_method_shapes": (
        "sc_referee_evaluation.source_method_probe",
        "probe_python_method_shapes",
    ),
    "Stage3ProtocolError": ("sc_referee_evaluation.stage3", "Stage3ProtocolError"),
    "build_stage3_review_packet": (
        "sc_referee_evaluation.stage3",
        "build_stage3_review_packet",
    ),
    "reconcile_detector_case": (
        "sc_referee_evaluation.stage3",
        "reconcile_detector_case",
    ),
    "validate_stage3_review_submission": (
        "sc_referee_evaluation.stage3",
        "validate_stage3_review_submission",
    ),
    "EvaluationValidationError": (
        "sc_referee_evaluation.validation",
        "EvaluationValidationError",
    ),
    "validate_case_packet": ("sc_referee_evaluation.validation", "validate_case_packet"),
}


def __getattr__(name: str) -> Any:
    """Load a public export only when callers request it."""

    try:
        module_name, attribute_name = _LAZY_EXPORTS[name]
    except KeyError:
        raise AttributeError(name) from None
    target = import_module(module_name)
    value = getattr(target, attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Include lazily provided public names in module introspection."""

    return sorted(set(globals()) | set(__all__))


__all__ = [
    "AUTHORING_BRIEF_MANIFEST_VERSION",
    "AUTHOR_DECLARATION_VERSION",
    "CASE_EVIDENCE_CONTRACT_VERSION",
    "DEFAULT_REGRESSION_CORPUS_EXECUTION_PLAN",
    "DEFAULT_REGRESSION_CORPUS_LEDGER",
    "DIRECT_LANE_FREEZE_VERSION",
    "MODULE_BASELINE_REQUIREMENTS_VERSION",
    "PARTICIPANT_ENROLLMENT_VERSION",
    "PROFILE_MANIFEST",
    "PROSPECTIVE_QUALIFICATION_PROTOCOL_VERSION",
    "PYTHON_STATIC_MARKED_REPORT_PROFILE",
    "REGRESSION_CORPUS_EXECUTION_PLAN_VERSION",
    "REGRESSION_CORPUS_LEDGER_VERSION",
    "REGRESSION_CORPUS_RUNNER_VERSION",
    "REQUIRED_CELL_TYPES",
    "SCIENTIFIC_LABEL_VERSION",
    "SELECTED_RESULT_DERIVATION_VERSION",
    "SELECTED_RESULT_VALIDATION_VERSION",
    "SELECTED_RESULT_VERIFIER_VERSION",
    "AnalysisMethodQualificationError",
    "CorpusPreflightError",
    "DetectorComparisonError",
    "DirectQualificationLaneError",
    "EvaluationCandidateProjectionError",
    "EvaluationValidationError",
    "ExactJsonGraderError",
    "FixtureGenerationError",
    "FixtureProofInputs",
    "GeneBenchNumericGradeError",
    "MethodContractDiagnosticError",
    "ProspectiveQualificationError",
    "ProspectiveQualificationV2Error",
    "ProspectiveSelectedResultVerifierError",
    "QualificationMetricError",
    "RegressionCorpusLedgerError",
    "RegressionCorpusRunnerError",
    "RegressionModuleBaselineError",
    "ReviewCaptureError",
    "RootCauseReconciliationError",
    "SourceMethodProbeError",
    "Stage3ProtocolError",
    "bootstrap_cluster_index",
    "bootstrap_problem_sample",
    "build_adjudicated_root_cause",
    "build_qualification_metric_set",
    "build_stage3_review_packet",
    "capture_review_submission",
    "compare_corpus_semantic_outcome",
    "compare_detector_output",
    "corpus_semantic_projection",
    "diagnose_genebench_method_contract_conflict",
    "freeze_author_selected_result_declaration",
    "freeze_authoring_brief_manifest",
    "freeze_bounded_analysis_method_profile",
    "freeze_case_evidence_contract",
    "freeze_direct_qualification_lane",
    "freeze_independent_selected_result_derivation",
    "freeze_participant_enrollment",
    "freeze_pilot_threshold_decision",
    "freeze_prospective_qualification_protocol",
    "freeze_selected_result_validation",
    "freeze_stage2_scientific_label",
    "generate_ambiguous_fixture",
    "generate_control_fixture",
    "generate_positive_fixture",
    "grade_exact_json_output",
    "grade_genebench_public_answer",
    "grade_genebench_public_numeric_answer",
    "load_review_capture",
    "preflight_genebench_public_package",
    "probe_python_method_shapes",
    "project_evaluation_candidate",
    "reconcile_detector_case",
    "regression_module_baseline_gaps",
    "regression_module_baseline_projection",
    "regression_tree_digest",
    "revalidate_analysis_method_proof",
    "revalidate_fixture_proof",
    "revalidate_independent_selected_result_derivation",
    "run_regression_corpus",
    "seal_prospective_outcome_ledger",
    "validate_adjudicated_root_cause",
    "validate_author_selected_result_declaration",
    "validate_authoring_brief_manifest",
    "validate_case_evidence_contract",
    "validate_case_packet",
    "validate_direct_qualification_lane",
    "validate_independent_selected_result_derivation",
    "validate_participant_enrollment",
    "validate_regression_corpus_execution_plan",
    "validate_regression_corpus_ledger",
    "validate_regression_module_baselines",
    "validate_selected_result_validation",
    "validate_stage3_review_submission",
    "verify_bounded_analysis_method_case",
]
