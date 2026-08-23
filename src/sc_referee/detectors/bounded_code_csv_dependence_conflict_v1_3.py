from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_dependence_conflict_v1_2 import (
    BoundedCodeCsvDependenceConflictV12Detector,
)


class BoundedCodeCsvDependenceConflictV13Detector(BoundedCodeCsvDependenceConflictV12Detector):
    """Versioned code-lane identity for the accepted bounded 1.3 grammar."""

    detector_version = "1.3.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_dependence_conflict_v1_3:"
        "BoundedCodeCsvDependenceConflictV13Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())
