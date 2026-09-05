"""Development-only multiple-testing 3.2 detector identity."""

from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v3 import (
    BoundedCodeCsvMultipleTestingConflictV3Detector,
)


class BoundedCodeCsvMultipleTestingConflictV3_2Detector(
    BoundedCodeCsvMultipleTestingConflictV3Detector
):
    """Preserve detector evaluation while versioning the AP-enabled development binding."""

    detector_version = "3.2.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v3_2:"
        "BoundedCodeCsvMultipleTestingConflictV3_2Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())


__all__ = ["BoundedCodeCsvMultipleTestingConflictV3_2Detector"]
