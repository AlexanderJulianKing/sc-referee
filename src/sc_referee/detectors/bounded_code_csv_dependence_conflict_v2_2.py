from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_dependence_conflict_v2_1 import (
    BoundedCodeCsvDependenceConflictV21Detector,
)


class BoundedCodeCsvDependenceConflictV22Detector(BoundedCodeCsvDependenceConflictV21Detector):
    """Versioned code-lane identity for the bounded 2.2 grammar."""

    detector_version = "2.2.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_dependence_conflict_v2_2:"
        "BoundedCodeCsvDependenceConflictV22Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())
