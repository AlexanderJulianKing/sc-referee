"""Public types for the report-only multiple-testing semantic recognizer."""

from sc_referee.multiple_testing_recognition.adapter import (
    MULTIPLE_TESTING_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST,
    MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST,
    MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_FILES,
    MultipleTestingRecognitionShadowAdapter,
    multiple_testing_recognition_dependency_closure,
)
from sc_referee.multiple_testing_recognition.certificate import (
    family_hypothesis_token,
    family_observation_token,
    family_pvalue_token,
    multiple_testing_case_digest,
    multiple_testing_replay_digest,
    source_construct_token,
    test_result_token,
    verify_multiple_testing_certificate,
)
from sc_referee.multiple_testing_recognition.ir import (
    CorrectionCall,
    EvidenceDeclaration,
    FamilyAuthorization,
    FamilyDomainObligation,
    FamilyScopeCheckObligation,
    FullFamilyProjectionObligation,
    MultipleTestingCaseBinding,
    MultipleTestingCertificate,
    PValueFamilyFact,
    ReportFamilyBinding,
    TestBatteryObligation,
    TestResultPosition,
    VerifiedMultipleTestingCertificate,
)
from sc_referee.multiple_testing_recognition.pvalue_domain import (
    prove_pvalue_family,
    pvalue_family_row_domain,
)
from sc_referee.multiple_testing_recognition.python_analyzer import (
    DischargedMultipleTestingAnalysis,
    PythonMultipleTestingAnalysis,
    analyze_multiple_testing_python,
    discharge_multiple_testing_proposal,
)

__all__ = [
    "MULTIPLE_TESTING_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST",
    "MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST",
    "MULTIPLE_TESTING_RECOGNITION_DEPENDENCY_FILES",
    "CorrectionCall",
    "DischargedMultipleTestingAnalysis",
    "EvidenceDeclaration",
    "FamilyAuthorization",
    "FamilyDomainObligation",
    "FamilyScopeCheckObligation",
    "FullFamilyProjectionObligation",
    "MultipleTestingCaseBinding",
    "MultipleTestingCertificate",
    "MultipleTestingRecognitionShadowAdapter",
    "PValueFamilyFact",
    "PythonMultipleTestingAnalysis",
    "ReportFamilyBinding",
    "TestBatteryObligation",
    "TestResultPosition",
    "VerifiedMultipleTestingCertificate",
    "analyze_multiple_testing_python",
    "discharge_multiple_testing_proposal",
    "family_hypothesis_token",
    "family_observation_token",
    "family_pvalue_token",
    "multiple_testing_case_digest",
    "multiple_testing_recognition_dependency_closure",
    "multiple_testing_replay_digest",
    "prove_pvalue_family",
    "pvalue_family_row_domain",
    "source_construct_token",
    "test_result_token",
    "verify_multiple_testing_certificate",
]
