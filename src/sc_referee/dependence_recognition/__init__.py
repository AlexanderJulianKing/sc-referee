"""Development-only dependence semantic v1 certificate surface."""

from sc_referee.dependence_recognition.certificate import verify_dependence_certificate
from sc_referee.dependence_recognition.ir import (
    DependenceCertificate,
    UnitKeyMultiplicityFact,
    VerifiedDependenceCertificate,
)

__all__ = [
    "DependenceCertificate",
    "UnitKeyMultiplicityFact",
    "VerifiedDependenceCertificate",
    "verify_dependence_certificate",
]
