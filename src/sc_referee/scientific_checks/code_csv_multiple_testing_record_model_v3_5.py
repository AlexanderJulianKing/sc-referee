"""Versioned 3.5 view of the frozen multiple-testing 3.0 record model."""

from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_record_model_v3 import (
    RecordModelResult,
    analyze_record_model,
)

CODE_CSV_MULTIPLE_TESTING_RECORD_MODEL_V3_5_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)
FROZEN_V3_RECORD_MODEL_DELEGATE = (
    "sc_referee.scientific_checks.code_csv_multiple_testing_record_model_v3:analyze_record_model"
)

__all__ = [
    "CODE_CSV_MULTIPLE_TESTING_RECORD_MODEL_V3_5_IMPLEMENTATION_DIGEST",
    "FROZEN_V3_RECORD_MODEL_DELEGATE",
    "RecordModelResult",
    "analyze_record_model",
]
