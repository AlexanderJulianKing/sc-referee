from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

from sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_2 import (
    analyze_correction_model,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 import (
    analyze_code_csv_multiple_testing_dataflow as frozen_v3_analyze,
)
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_2 import (
    analyze_code_csv_multiple_testing_dataflow,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v1 import (
    SourceSpan,
    locate_correction_scope_witness,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v1 import (
    existing_complete_coverage_recheck as frozen_guided_recheck,
)
from sc_referee.scientific_checks.multiple_testing_scope_questions_v3_2 import (
    APGuidedRecheckContext,
    existing_complete_coverage_recheck,
)

_SWEEP = Path("evaluation/development/multitest-code-slice-v3_2/prototype-sweep").resolve()
sys.path.insert(0, str(_SWEEP))
try:
    from harness import all_cases, inputs, question_keys, reference_case
finally:
    sys.path.remove(str(_SWEEP))

_RESULTS = json.loads((_SWEEP / "results.json").read_text(encoding="utf-8"))
_EXPECTED_QUESTIONS = set(_RESULTS["question_census"]["removed"])
_CONSUMPTION_ORACLE = Path(
    "evaluation/development/multitest-code-slice-v3_2/audit-fix-r1-oracle"
).resolve()
sys.path.insert(0, str(_CONSUMPTION_ORACLE))
try:
    from fixture_sources import fixture_sources as consumption_fixture_sources
finally:
    sys.path.remove(str(_CONSUMPTION_ORACLE))


def _context(values: dict[str, object]) -> APGuidedRecheckContext:
    return APGuidedRecheckContext(
        authorized_path=str(values["authorized_path"]),
        group_column=str(values["group_column"]),
        outcome_columns=tuple(values["outcome_columns"]),
        csv_header=tuple(values["csv_header"]),
        group_values=tuple(values["group_values"]),
        csv_content=bytes(values["csv_content"]),
    )


def test_no_attestation_question_census_is_exactly_22() -> None:
    before = question_keys()
    assert len(before) == 24
    observed: set[str] = set()
    for case in all_cases():
        values = inputs(case)
        content = values.pop("content")
        result = analyze_code_csv_multiple_testing_dataflow(content, **values)
        witness = locate_correction_scope_witness(
            content,
            qualifying_reason=result.reason or "",
            authorized_count=len(values["outcome_columns"]),
            outcome_columns=values["outcome_columns"],
        )
        if witness is not None:
            observed.add(case.key)
    # spec-30 is deliberately an analyzer-level diagnostic only; the adapter's earlier
    # api-resolution-ambiguous envelope reason prevents question construction.
    assert observed - before == {"corpus:spec-30"}
    observed.remove("corpus:spec-30")
    assert before - observed == _EXPECTED_QUESTIONS
    assert len(observed) == 22
    assert sum(key.startswith("E") for key in observed) == 13
    assert sum(key.startswith("corpus:") for key in observed) == 9


def test_ap_guided_recheck_is_answer_removed_and_temporally_versioned() -> None:
    case = reference_case("corpus:spec-28")
    values = inputs(case)
    content = values.pop("content")
    baseline = frozen_v3_analyze(content, **values)
    model = analyze_correction_model(content, baseline=baseline, **values)
    assert model.changed
    position = model.detail["source_position"]
    assert isinstance(position, list)
    span = SourceSpan(position[0], position[1] + 1, position[2], position[3] + 1)

    before_3_2 = frozen_guided_recheck(
        content,
        source_span=span,
        authorized_count=4,
        outcome_columns=values["outcome_columns"],
    )
    assert before_3_2.status == "unverified"
    answer_removed = existing_complete_coverage_recheck(
        content,
        source_span=span,
        authorized_count=4,
        outcome_columns=values["outcome_columns"],
        ap_context=_context(values),
    )
    guided_pointer = existing_complete_coverage_recheck(
        content,
        source_span=span,
        authorized_count=4,
        outcome_columns=values["outcome_columns"],
        ap_context=_context(values),
    )
    assert guided_pointer.status == "complete"
    assert guided_pointer.corrected_positions == (0, 1, 2, 3)
    assert guided_pointer == answer_removed


def test_ap_guided_recheck_cannot_clear_a_raw_consumer() -> None:
    case_key, source = consumption_fixture_sources()["correct-ap-complete-raw-consumer"]
    case = reference_case(case_key)
    values = inputs(case, source)
    content = values.pop("content")
    baseline = analyze_code_csv_multiple_testing_dataflow(content, **values)
    assert baseline.reason == "unresolved-manual-correction-present"
    correction = next(
        node
        for node in ast.walk(ast.parse(content))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "min"
        and any(isinstance(item, ast.BinOp) for item in ast.walk(node))
    )
    pointer = SourceSpan(
        correction.lineno,
        correction.col_offset + 1,
        correction.end_lineno or correction.lineno,
        (correction.end_col_offset or correction.col_offset + 1) + 1,
    )
    answer_removed = existing_complete_coverage_recheck(
        content,
        source_span=pointer,
        authorized_count=len(values["outcome_columns"]),
        outcome_columns=values["outcome_columns"],
        ap_context=_context(values),
    )
    guided_pointer = existing_complete_coverage_recheck(
        content,
        source_span=pointer,
        authorized_count=len(values["outcome_columns"]),
        outcome_columns=values["outcome_columns"],
        ap_context=_context(values),
    )
    assert guided_pointer.status == "unverified"
    assert guided_pointer.corrected_positions == ()
    assert guided_pointer == answer_removed
