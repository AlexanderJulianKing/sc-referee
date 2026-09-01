"""Development-only multiple-testing 3.4 detector identity."""

from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v3_3 import (
    BoundedCodeCsvMultipleTestingConflictV3_3Detector,
)


class BoundedCodeCsvMultipleTestingConflictV3_4Detector(
    BoundedCodeCsvMultipleTestingConflictV3_3Detector
):
    """Preserve detector evaluation for the 3.4 comprehension/iterator development binding."""

    detector_version = "3.4.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v3_4:"
        "BoundedCodeCsvMultipleTestingConflictV3_4Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())


__all__ = ["BoundedCodeCsvMultipleTestingConflictV3_4Detector"]
