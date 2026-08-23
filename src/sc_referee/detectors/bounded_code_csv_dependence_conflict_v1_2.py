from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_dependence_conflict_v1_1 import (
    BoundedCodeCsvDependenceConflictV11Detector,
)


class BoundedCodeCsvDependenceConflictV12Detector(BoundedCodeCsvDependenceConflictV11Detector):
    """Versioned code-lane identity for the accepted bounded 1.2 grammar."""

    detector_version = "1.2.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_dependence_conflict_v1_2:"
        "BoundedCodeCsvDependenceConflictV12Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())
