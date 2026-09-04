"""Versioned entry point for the closed MT 3.3 helper-record graph proof, unchanged in 3.5.

The graph proof itself is byte-identical to the frozen 3.3 proof; the 3.5 deltas widen four
predicates elsewhere in the engine and none of them is on this route.  The import points at
the versioned 3.5 terminal-presentation copy so the whole 3.5 lane resolves inside its own
version.
"""

from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_terminal_presentation_v3_5 import (
    HelperRecordGraph,
    build_helper_record_graph,
)

CODE_CSV_MULTIPLE_TESTING_HELPER_RECORD_V3_5_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)

__all__ = [
    "CODE_CSV_MULTIPLE_TESTING_HELPER_RECORD_V3_5_IMPLEMENTATION_DIGEST",
    "HelperRecordGraph",
    "build_helper_record_graph",
]
