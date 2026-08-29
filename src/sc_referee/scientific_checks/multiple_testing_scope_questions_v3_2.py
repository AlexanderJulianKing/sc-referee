"""Answer-independent 3.2 AP extension for the frozen correction-scope recheck.

The author Answer never enters this module. A bound source span may prioritize the already-shipped
AP recognizer, but the source, contract table, CSV snapshot, and frozen 3.0 surrogate proof are the
only values that can establish coverage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_2 import (
    analyze_correction_model,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 import (
    analyze_code_csv_multiple_testing_dataflow as frozen_v3_analyze,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v1 import (
    GuidedCoverageProof,
    SourceSpan,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v1 import (
    existing_complete_coverage_recheck as frozen_complete_coverage_recheck,
)

MULTIPLE_TESTING_SCOPE_QUESTIONS_V3_2_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)


@dataclass(frozen=True)
class APGuidedRecheckContext:
    authorized_path: str
    group_column: str
    outcome_columns: tuple[str, ...]
    csv_header: tuple[str, ...]
    group_values: tuple[str, str]
    csv_content: bytes


def existing_complete_coverage_recheck(
    content: bytes,
    *,
    source_span: SourceSpan,
    authorized_count: int,
    outcome_columns: tuple[str, ...],
    ap_context: APGuidedRecheckContext | None = None,
) -> GuidedCoverageProof:
    """Run frozen proof first, then one answer-free AP proof when full inputs are bound."""

    frozen = frozen_complete_coverage_recheck(
        content,
        source_span=source_span,
        authorized_count=authorized_count,
        outcome_columns=outcome_columns,
    )
    if frozen.status == "complete" or ap_context is None:
        return frozen
    if ap_context.outcome_columns != outcome_columns or authorized_count != len(outcome_columns):
        return frozen
    baseline = frozen_v3_analyze(
        content,
        authorized_path=ap_context.authorized_path,
        group_column=ap_context.group_column,
        outcome_columns=outcome_columns,
        csv_header=ap_context.csv_header,
        group_values=ap_context.group_values,
        csv_content=ap_context.csv_content,
    )
    model = analyze_correction_model(
        content,
        baseline=baseline,
        authorized_path=ap_context.authorized_path,
        group_column=ap_context.group_column,
        outcome_columns=outcome_columns,
        csv_header=ap_context.csv_header,
        group_values=ap_context.group_values,
        csv_content=ap_context.csv_content,
    )
    if (
        not model.changed
        or model.outcome.state != "covered"
        or model.outcome.reason_or_classification != "complete"
        or model.corrected_positions != tuple(range(authorized_count))
    ):
        return frozen
    position = model.detail.get("source_position")
    if not isinstance(position, list) or len(position) != 4:
        return frozen
    expected_position = [
        source_span.start_line,
        source_span.start_column - 1,
        source_span.end_line,
        source_span.end_column - 1,
    ]
    if position != expected_position:
        return frozen
    proof_digest = semantic_digest(
        {
            "grammar": "multiple-testing-ap-c-pos-v3.2",
            "proof_root_span": source_span.to_dict(),
            "corrected_positions": list(model.corrected_positions),
            "surrogate_sha256": model.surrogate_sha256,
            "answer_inputs": [],
        }
    )
    return GuidedCoverageProof(
        "complete",
        model.corrected_positions,
        source_span,
        proof_digest,
        None,
    )


__all__ = [
    "MULTIPLE_TESTING_SCOPE_QUESTIONS_V3_2_IMPLEMENTATION_DIGEST",
    "APGuidedRecheckContext",
    "existing_complete_coverage_recheck",
]
