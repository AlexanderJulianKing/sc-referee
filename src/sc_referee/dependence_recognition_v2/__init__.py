"""Unregistered dependence semantic growth shadow package."""

from sc_referee.dependence_recognition_v2.adapter import DependenceRecognitionV2ShadowAdapter
from sc_referee.dependence_recognition_v2.certificate import (
    verify_count_dependence_certificate,
    verify_dependence_growth_certificate,
)
from sc_referee.dependence_recognition_v2.count_domain import prove_count_procedure_domain
from sc_referee.dependence_recognition_v2.csv_domain import prove_group_value_sequences
from sc_referee.dependence_recognition_v2.python_analyzer import (
    analyze_dependence_growth_python,
    discharge_dependence_growth_analysis,
)

__all__ = [
    "DependenceRecognitionV2ShadowAdapter",
    "analyze_dependence_growth_python",
    "discharge_dependence_growth_analysis",
    "prove_count_procedure_domain",
    "prove_group_value_sequences",
    "verify_count_dependence_certificate",
    "verify_dependence_growth_certificate",
]
