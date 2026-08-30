"""Multiple-testing 3.2 AP overlay on the frozen 3.0 source analyzer.

The baseline and surrogate are both selected by the byte-frozen 3.0 analyzer.  This module accepts
only an immutable correction-model delta whose subtraction leaves a frozen candidate/none proof.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_2 import (
    analyze_correction_model,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 import (
    MultipleTestingDataflowFacts,
    MultipleTestingDataflowResult,
    MultipleTestingEvidenceSpan,
    SourceEnvelope,
    _mt30_model_facts,
    select_code_source_envelope,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 import (
    analyze_code_csv_multiple_testing_dataflow as _frozen_v3_analyze,
)

CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)
FROZEN_V3_DATAFLOW_DELEGATE = (
    "sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3:"
    "analyze_code_csv_multiple_testing_dataflow"
)


def analyze_code_csv_multiple_testing_dataflow(
    content: bytes,
    *,
    authorized_path: str,
    group_column: str,
    outcome_columns: tuple[str, ...],
    csv_header: tuple[str, ...] | list[str],
    group_values: tuple[str, str],
    csv_content: bytes,
) -> MultipleTestingDataflowResult:
    """Run the frozen baseline, then apply one AP delta only after independent reproof."""

    arguments: dict[str, Any] = {
        "authorized_path": authorized_path,
        "group_column": group_column,
        "csv_header": csv_header,
        "group_values": group_values,
        "csv_content": csv_content,
    }
    baseline = _frozen_v3_analyze(content, outcome_columns=outcome_columns, **arguments)
    model = analyze_correction_model(
        content,
        baseline=baseline,
        outcome_columns=outcome_columns,
        **arguments,
    )
    if not model.changed:
        return baseline
    facts_result = _mt30_model_facts(
        content,
        outcome_columns=outcome_columns,
        outcome=model.outcome,
        detail=model.detail,
    )
    if facts_result.reason is not None or facts_result.facts is None:
        return baseline
    position = model.detail.get("source_position")
    if (
        not isinstance(position, list)
        or len(position) != 4
        or not all(isinstance(item, int) for item in position)
    ):
        return baseline
    start_line, start_column, end_line, end_column = position
    if min(start_line, end_line) < 1 or min(start_column, end_column) < 0:
        return baseline
    correction_span = MultipleTestingEvidenceSpan(
        "correction",
        None,
        start_line,
        end_line,
        start_column + 1,
        end_column + 1,
    )
    facts = replace(
        facts_result.facts,
        evidence_spans=(*facts_result.facts.evidence_spans, correction_span),
    )
    return MultipleTestingDataflowResult(facts, None)


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
