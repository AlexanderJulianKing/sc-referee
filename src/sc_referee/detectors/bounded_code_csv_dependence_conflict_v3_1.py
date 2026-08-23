from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_dependence_conflict_v2_2 import (
    BoundedCodeCsvDependenceConflictV22Detector,
)


class BoundedCodeCsvDependenceConflictV31Detector(BoundedCodeCsvDependenceConflictV22Detector):
    """Versioned development identity for the operand-first 3.1 grammar."""

    detector_version = "3.1.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_dependence_conflict_v3_1:"
        "BoundedCodeCsvDependenceConflictV31Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())
