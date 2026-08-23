from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_dependence_conflict_v2_0 import (
    BoundedCodeCsvDependenceConflictV20Detector,
)


class BoundedCodeCsvDependenceConflictV21Detector(BoundedCodeCsvDependenceConflictV20Detector):
    """Versioned code-lane identity for the bounded 2.1 grammar."""

    detector_version = "2.1.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_dependence_conflict_v2_1:"
        "BoundedCodeCsvDependenceConflictV21Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())
