"""Development-only dependence semantic v1 shadow surface."""

from sc_referee.dependence_recognition.adapter import (
    DEPENDENCE_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST,
    DEPENDENCE_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST,
    DEPENDENCE_RECOGNITION_DEPENDENCY_FILES,
    DependenceRecognitionShadowAdapter,
    dependence_recognition_dependency_closure,
)
from sc_referee.dependence_recognition.certificate import verify_dependence_certificate
from sc_referee.dependence_recognition.ir import (
    DependenceCertificate,
    UnitKeyMultiplicityFact,
    VerifiedDependenceCertificate,
)

__all__ = [
    "DEPENDENCE_RECOGNITION_ADAPTER_IMPLEMENTATION_DIGEST",
    "DEPENDENCE_RECOGNITION_DEPENDENCY_CLOSURE_DIGEST",
    "DEPENDENCE_RECOGNITION_DEPENDENCY_FILES",
    "DependenceCertificate",
    "DependenceRecognitionShadowAdapter",
    "UnitKeyMultiplicityFact",
    "VerifiedDependenceCertificate",
    "dependence_recognition_dependency_closure",
    "verify_dependence_certificate",
]
