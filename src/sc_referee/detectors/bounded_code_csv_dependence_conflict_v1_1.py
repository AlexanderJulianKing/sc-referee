from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_dependence_conflict import (
    BoundedCodeCsvDependenceConflictDetector,
)


class BoundedCodeCsvDependenceConflictV11Detector(BoundedCodeCsvDependenceConflictDetector):
    """Versioned code-lane identity for the accepted bounded 1.1 grammar."""

    detector_version = "1.1.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_dependence_conflict_v1_1:"
        "BoundedCodeCsvDependenceConflictV11Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())
