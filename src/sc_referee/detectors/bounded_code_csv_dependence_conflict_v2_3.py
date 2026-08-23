from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_dependence_conflict_v2_2 import (
    BoundedCodeCsvDependenceConflictV22Detector,
)


class BoundedCodeCsvDependenceConflictV23Detector(BoundedCodeCsvDependenceConflictV22Detector):
    """Versioned code-lane identity for the bounded 2.3 grammar."""

    detector_version = "2.3.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_dependence_conflict_v2_3:"
        "BoundedCodeCsvDependenceConflictV23Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())
