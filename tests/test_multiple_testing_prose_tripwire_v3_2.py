from __future__ import annotations

import sys
from pathlib import Path

from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_2 import (
    analyze_code_csv_multiple_testing_dataflow,
)

_SWEEP = Path("evaluation/development/multitest-code-slice-v3_2/prototype-sweep").resolve()
sys.path.insert(0, str(_SWEEP))
try:
    from harness import inputs, reference_case
finally:
    sys.path.remove(str(_SWEEP))


def _classification(content: bytes) -> tuple[str | None, str | None, tuple[int, ...]]:
    case = reference_case("E15:P6:81980e878c1bc8cc216b")
    values = inputs(case, content)
    source = values.pop("content")
    result = analyze_code_csv_multiple_testing_dataflow(source, **values)
    return (
        result.reason,
        None if result.facts is None else result.facts.correction_classification,
        () if result.facts is None else result.facts.corrected_positions,
    )


def test_comments_docstrings_display_strings_and_noncallee_names_are_not_evidence() -> None:
    case = reference_case("E15:P6:81980e878c1bc8cc216b")
    source = case.source_path.read_text(encoding="utf-8")
    baseline = _classification(source.encode("utf-8"))
    assert baseline == (None, "strict_subset", (0, 1, 3))
    mutations = (
        source.replace(
            "# By-hand correction: multiply by the family size, then cap at one.",
            "# alpha prose removed; this comment carries no detector evidence.",
        ),
        source.replace(
            "Run one two-sample test per declared outcome and report the verdicts.",
            "Arbitrary documentation mutation with no structural authority.",
        ),
        source.replace('"SIGNIFICANT"', '"DISPLAY-A"').replace('"not significant"', '"DISPLAY-B"'),
        source.replace("basis", "benjamini_hochberg"),
    )
    assert {_classification(item.encode("utf-8")) for item in mutations} == {baseline}


def test_structural_factor_and_callee_controls_do_change_recognition() -> None:
    case = reference_case("E15:P6:81980e878c1bc8cc216b")
    source = case.source_path.read_text(encoding="utf-8")
    wrong_factor = source.replace("FAMILY_SIZE = len(OUTCOMES)", "FAMILY_SIZE = 7")
    wrong_callee = source.replace(
        "p_corrected = min(p_raw * FAMILY_SIZE, 1.0)",
        "p_corrected = max(p_raw * FAMILY_SIZE, 1.0)",
    )
    for mutation in (wrong_factor, wrong_callee):
        reason, classification, _positions = _classification(mutation.encode("utf-8"))
        assert reason is not None
        assert classification is None
