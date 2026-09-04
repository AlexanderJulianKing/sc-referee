"""Answer-independent 3.5 extension for the frozen correction-scope recheck.

The author Answer never enters this module.  A bound source span may prioritize the already-
shipped AP recognizer, but the source, contract table, CSV snapshot, and frozen 3.0 surrogate
proof are the only values that can establish coverage.  The only 3.5 change is that the guided
recheck runs the 3.5 analyzer, whose ordering rule leaves every frozen 3.4 result untouched.
"""

from __future__ import annotations

from pathlib import Path

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_5 import (
    analyze_code_csv_multiple_testing_dataflow as analyze_v35,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v1 import (
    GuidedCoverageProof,
    SourceSpan,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v3_2 import (
    APGuidedRecheckContext,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v3_4 import (
    existing_complete_coverage_recheck as v34_complete_coverage_recheck,
)

MULTIPLE_TESTING_SCOPE_QUESTIONS_V3_5_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)


def existing_complete_coverage_recheck(
    content: bytes,
    *,
    source_span: SourceSpan,
    authorized_count: int,
    outcome_columns: tuple[str, ...],
    ap_context: APGuidedRecheckContext | None = None,
) -> GuidedCoverageProof:
    """Run the frozen proofs first, then one answer-free 3.5 proof when full inputs are bound."""

    frozen = v34_complete_coverage_recheck(
        content,
        source_span=source_span,
        authorized_count=authorized_count,
        outcome_columns=outcome_columns,
        ap_context=ap_context,
    )
    if frozen.status == "complete" or ap_context is None:
        return frozen
    if ap_context.outcome_columns != outcome_columns or authorized_count != len(outcome_columns):
        return frozen
    result = analyze_v35(
        content,
        authorized_path=ap_context.authorized_path,
        group_column=ap_context.group_column,
        outcome_columns=outcome_columns,
        csv_header=ap_context.csv_header,
        group_values=ap_context.group_values,
        csv_content=ap_context.csv_content,
    )
    if (
        result.reason is not None
        or result.facts is None
        or result.facts.correction_classification != "complete"
        or result.facts.corrected_positions != tuple(range(authorized_count))
    ):
        return frozen
    correction_spans = tuple(
        span
        for span in result.facts.evidence_spans
        if span.role == "correction"
        and span.start_line == source_span.start_line
        and span.start_column == source_span.start_column
        and span.end_line == source_span.end_line
        and span.end_column == source_span.end_column
    )
    if len(correction_spans) != 1:
        return frozen
    proof_digest = semantic_digest(
        {
            "grammar": "multiple-testing-guided-recheck-v3.5",
            "proof_root_span": source_span.to_dict(),
            "corrected_positions": list(result.facts.corrected_positions),
            "analysis_content_digest": sha256_digest(content),
            "answer_inputs": [],
        }
    )
    return GuidedCoverageProof(
        "complete",
        result.facts.corrected_positions,
        source_span,
        proof_digest,
        None,
    )


__all__ = [
    "MULTIPLE_TESTING_SCOPE_QUESTIONS_V3_5_IMPLEMENTATION_DIGEST",
    "APGuidedRecheckContext",
    "existing_complete_coverage_recheck",
]
