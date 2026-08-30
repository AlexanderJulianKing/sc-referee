"""Development-only multiple-testing 3.3 detector identity."""

from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v3_2 import (
    BoundedCodeCsvMultipleTestingConflictV3_2Detector,
)


class BoundedCodeCsvMultipleTestingConflictV3_3Detector(
    BoundedCodeCsvMultipleTestingConflictV3_2Detector
):
    """Preserve detector evaluation for the 3.3 graph-proof development binding."""

    detector_version = "3.3.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v3_3:"
        "BoundedCodeCsvMultipleTestingConflictV3_3Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())


__all__ = ["BoundedCodeCsvMultipleTestingConflictV3_3Detector"]
