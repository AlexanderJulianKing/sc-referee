"""Parse-only, sound-over-complete inference engine (shadow mode)."""

from sc_referee.inference.api import AnalysisRequest, AnalysisSnapshot, analyze
from sc_referee.inference.compatibility import (
    project_legacy_marker_tests,
    project_legacy_sink_uses,
)

__all__ = [
    "AnalysisRequest", "AnalysisSnapshot", "analyze",
    "project_legacy_marker_tests", "project_legacy_sink_uses",
]
