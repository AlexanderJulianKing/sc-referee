"""Multiple-testing 3.4 ordered integration over the byte-frozen 3.3 pipeline.

The ordering rule in design section 3.3 is the load-bearing safety property of this delta, and
it was chosen against executed evidence rather than on principle:

1. run every unchanged adapter precondition and global census on original bytes;
2. run the **complete unchanged 3.3 pipeline** and record its result;
3. if that result is a classification, return it untouched.  No 3.4 admission is attempted;
4. otherwise re-analyze with the section-4 comprehension normalization supplied as a graph fact
   and the section-6 and section-7 admissions inside the 3.4 correction recognizer;
5. adopt the re-analysis only if it is itself a classification.  If it abstains, return the
   step-2 abstention reason byte-for-byte.

An earlier revision normalized unconditionally and lost two pinned 3.3 candidates: on E16 P3 the
normalization resolved the p-lineage, the first reason stopped being `unresolved-pvalue-consumer`
and the frozen helper-record route was never attempted.  Under steps 3 and 5 every frozen 3.3
classification and every frozen 3.3 abstention reason survives by construction, so the only rows
3.4 can move are abstentions it converts into classifications.

Section 8's outcome-headers reason routing is measured in the design and **not applied** here:
3.4 emits the frozen reason unchanged.  Extension B, the terminal `IfExp` print-only production,
is specified in the design and is **not** part of this recognizer set.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import Any

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_comprehension_v3_4 import (
    normalize_comprehensions,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    MultipleTestingDataflowFacts,
    MultipleTestingDataflowResult,
    MultipleTestingEvidenceSpan,
    SourceEnvelope,
    _analyze_v3_core,
    _mt30_model_facts,
    select_code_source_envelope,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    analyze_code_csv_multiple_testing_dataflow as _frozen_v33_analyze,
)

CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)
FROZEN_V33_DATAFLOW_DELEGATE = (
    "sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3:"
    "analyze_code_csv_multiple_testing_dataflow"
)

#: Reasons whose 3.3 graph proof is re-attempted inside the 3.4 re-analysis.
_TERMINAL_PRESENTATION_REASON = "hierarchical-gatekeeping-present"
_HELPER_RECORD_REASON = "unresolved-pvalue-consumer"


def _apply_v34_ap(
    content: bytes,
    *,
    baseline: MultipleTestingDataflowResult,
    authorized_path: str,
    group_column: str,
    outcome_columns: tuple[str, ...],
    csv_header: Any,
    group_values: tuple[str, str],
    csv_content: bytes,
) -> MultipleTestingDataflowResult:
    """Apply the 3.4 AP proof, whose only delta is the section-6 and section-7 admissions."""

    from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 import (
        analyze_correction_model,
    )

    arguments: dict[str, Any] = {
        "authorized_path": authorized_path,
        "group_column": group_column,
        "csv_header": csv_header,
        "group_values": group_values,
        "csv_content": csv_content,
    }
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
    return MultipleTestingDataflowResult(
        replace(
            facts_result.facts,
            evidence_spans=(*facts_result.facts.evidence_spans, correction_span),
        ),
        None,
    )


def _reanalyze_with_v34_admissions(
    content: bytes,
    *,
    authorized_path: str,
    group_column: str,
    outcome_columns: tuple[str, ...],
    csv_header: Any,
    group_values: tuple[str, str],
    csv_content: bytes,
) -> MultipleTestingDataflowResult:
    """Step 4: the 3.3 pipeline shape with the three shipped 3.4 admissions installed.

    The comprehension normalization enters as an `ast.Module` graph fact, exactly as the frozen
    3.3 helper-record graph does.  Global censuses continue to run on the original bytes inside
    the copied core, so a normalized family can never hide a census fact.
    """

    arguments: dict[str, Any] = {
        "authorized_path": authorized_path,
        "group_column": group_column,
        "outcome_columns": outcome_columns,
        "csv_header": csv_header,
        "group_values": group_values,
        "csv_content": csv_content,
    }
    normalization = normalize_comprehensions(content, outcome_columns)
    analysis_tree: ast.Module | None = None if normalization is None else normalization.tree
    terminal_exclusions: frozenset[tuple[tuple[int, int, int, int], str, str]] = frozenset()

    external = _apply_v34_ap(
        content,
        baseline=_analyze_v3_core(content, analysis_tree=analysis_tree, **arguments),
        **arguments,
    )
    if external.reason is None:
        return external

    from sc_referee.scientific_checks.code_csv_multiple_testing_helper_record_v3_4 import (
        build_helper_record_graph,
    )
    from sc_referee.scientific_checks.code_csv_multiple_testing_terminal_presentation_v3_3 import (
        prove_terminal_presentation,
    )

    if external.reason == _TERMINAL_PRESENTATION_REASON:
        proof = prove_terminal_presentation(content)
        if proof is None:
            return external
        terminal_exclusions = proof.occurrences
    elif external.reason == _HELPER_RECORD_REASON and analysis_tree is None:
        graph = build_helper_record_graph(content, outcome_columns)
        if graph is None:
            return external
        repeated = build_helper_record_graph(content, outcome_columns)
        if repeated is None or ast.dump(repeated.tree, include_attributes=True) != ast.dump(
            graph.tree, include_attributes=True
        ):
            return MultipleTestingDataflowResult(None, "multiple-testing-code-inspection-exception")
        analysis_tree = graph.tree
    else:
        return external

    downstream = _analyze_v3_core(
        content,
        analysis_tree=analysis_tree,
        terminal_exclusions=terminal_exclusions,
        **arguments,
    )
    return _apply_v34_ap(content, baseline=downstream, **arguments)


def analyze_code_csv_multiple_testing_dataflow(
    content: bytes,
    *,
    authorized_path: str,
    group_column: str,
    outcome_columns: tuple[str, ...],
    csv_header: Any,
    group_values: tuple[str, str],
    csv_content: bytes,
) -> MultipleTestingDataflowResult:
    """Run the complete unchanged 3.3 pipeline first, then the 3.4 admissions only if it abstained."""

    arguments: dict[str, Any] = {
        "authorized_path": authorized_path,
        "group_column": group_column,
        "outcome_columns": outcome_columns,
        "csv_header": csv_header,
        "group_values": group_values,
        "csv_content": csv_content,
    }
    frozen = _frozen_v33_analyze(content, **arguments)
    if frozen.reason is None:
        # Step 3: a frozen 3.3 classification is returned untouched and no admission is tried.
        return frozen
    attempted = _reanalyze_with_v34_admissions(content, **arguments)
    if attempted.reason is None:
        # Step 5: the re-analysis is adopted only when it is itself a classification.
        return attempted
    # Steps 5 and 6: an abstaining re-analysis returns the frozen 3.3 reason byte-for-byte.
    return frozen


__all__ = [
    "CODE_CSV_MULTIPLE_TESTING_DATAFLOW_IMPLEMENTATION_DIGEST",
    "FROZEN_V33_DATAFLOW_DELEGATE",
    "MultipleTestingDataflowFacts",
    "MultipleTestingDataflowResult",
    "MultipleTestingEvidenceSpan",
    "SourceEnvelope",
    "analyze_code_csv_multiple_testing_dataflow",
    "select_code_source_envelope",
]
