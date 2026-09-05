"""Versioned entry point for the closed MT 3.3 helper-record graph proof, unchanged in 3.4."""

from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_terminal_presentation_v3_3 import (
    HelperRecordGraph,
    build_helper_record_graph,
)

CODE_CSV_MULTIPLE_TESTING_HELPER_RECORD_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)

__all__ = [
    "CODE_CSV_MULTIPLE_TESTING_HELPER_RECORD_IMPLEMENTATION_DIGEST",
    "HelperRecordGraph",
    "build_helper_record_graph",
]
