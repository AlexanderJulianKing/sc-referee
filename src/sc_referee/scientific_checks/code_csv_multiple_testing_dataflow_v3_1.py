"""Versioned 3.1 view of the frozen multiple-testing 3.0 source analyzer.

The 3.1 correction-scope question layer runs only after the 3.0 result has been selected.  This
module deliberately delegates every source-analysis operation to the frozen implementation and
adds no recognition grammar.
"""

from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 import (
    MultipleTestingDataflowFacts,
    MultipleTestingDataflowResult,
    MultipleTestingEvidenceSpan,
    SourceEnvelope,
    analyze_code_csv_multiple_testing_dataflow,
    select_code_source_envelope,
)

CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)
FROZEN_V3_DATAFLOW_DELEGATE = (
    "sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3:"
    "analyze_code_csv_multiple_testing_dataflow"
)

__all__ = [
    "CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST",
    "FROZEN_V3_DATAFLOW_DELEGATE",
    "MultipleTestingDataflowFacts",
    "MultipleTestingDataflowResult",
    "MultipleTestingEvidenceSpan",
    "SourceEnvelope",
    "analyze_code_csv_multiple_testing_dataflow",
    "select_code_source_envelope",
]
