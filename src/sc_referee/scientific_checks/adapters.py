"""Compatibility exports for the isolated scientific-check adapter modules."""

from sc_referee.scientific_checks.python_founder_adapter import (
    PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST,
    PythonFounderOrientationAdapter,
    python_founder_recognition_grammar_digest,
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

__all__ = [
    "PYTHON_FOUNDER_ADAPTER_IMPLEMENTATION_DIGEST",
    "RMARKDOWN_MVMR_ADAPTER_IMPLEMENTATION_DIGEST",
    "SELECTED_REPORT_ADAPTER_IMPLEMENTATION_DIGEST",
    "PythonFounderOrientationAdapter",
    "RMarkdownMVMRCovarianceAdapter",
    "ReportOperandRule",
    "SelectedReportMethodAdapter",
    "python_founder_recognition_grammar_digest",
    "report_recognition_grammar_digest",
    "rmarkdown_mvmr_recognition_grammar_digest",
]
