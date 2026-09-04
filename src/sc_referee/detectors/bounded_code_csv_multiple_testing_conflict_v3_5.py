"""Development-only multiple-testing 3.5 detector identity."""

from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v3_4 import (
    BoundedCodeCsvMultipleTestingConflictV3_4Detector,
)


class BoundedCodeCsvMultipleTestingConflictV3_5Detector(
    BoundedCodeCsvMultipleTestingConflictV3_4Detector
):
    """Preserve detector evaluation for the 3.5 recall-delta development binding."""

    detector_version = "3.5.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_multiple_testing_conflict_v3_5:"
        "BoundedCodeCsvMultipleTestingConflictV3_5Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())


__all__ = ["BoundedCodeCsvMultipleTestingConflictV3_5Detector"]
