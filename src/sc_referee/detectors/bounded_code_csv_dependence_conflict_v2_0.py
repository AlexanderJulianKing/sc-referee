from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.detectors.bounded_code_csv_dependence_conflict_v1_3 import (
    BoundedCodeCsvDependenceConflictV13Detector,
)


class BoundedCodeCsvDependenceConflictV20Detector(BoundedCodeCsvDependenceConflictV13Detector):
    """Versioned code-lane identity for the bounded reachability grammar."""

    detector_version = "2.0.0"
    entry_point = (
        "sc_referee.detectors.bounded_code_csv_dependence_conflict_v2_0:"
        "BoundedCodeCsvDependenceConflictV20Detector"
    )

    @staticmethod
    def implementation_digest() -> str:
        return sha256_digest(Path(__file__).read_bytes())
