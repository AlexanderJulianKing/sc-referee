"""Development-only multiple-testing 3.1 detector identity."""

from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v3 import (
    BoundedCodeCsvMultipleTestingConflictV3Detector,
)


class BoundedCodeCsvMultipleTestingConflictV3_1Detector(
    BoundedCodeCsvMultipleTestingConflictV3Detector
):
    """Preserve the 3.0 detector evaluation while versioning the development binding."""

    detector_version = "3.1.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v3_1:"
        "BoundedCodeCsvMultipleTestingConflictV3_1Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())


__all__ = ["BoundedCodeCsvMultipleTestingConflictV3_1Detector"]
