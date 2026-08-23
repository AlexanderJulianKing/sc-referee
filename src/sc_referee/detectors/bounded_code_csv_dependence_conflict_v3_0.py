from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_dependence_conflict_v2_2 import (
    BoundedCodeCsvDependenceConflictV22Detector,
)


class BoundedCodeCsvDependenceConflictV30Detector(BoundedCodeCsvDependenceConflictV22Detector):
    """Versioned development identity for the operand-first 3.0 grammar."""

    detector_version = "3.0.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_dependence_conflict_v3_0:"
        "BoundedCodeCsvDependenceConflictV30Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())
