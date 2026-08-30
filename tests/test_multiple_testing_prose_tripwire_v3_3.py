from __future__ import annotations

import runpy
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    MultipleTestingDataflowResult,
    analyze_code_csv_multiple_testing_dataflow,
)

_ROOT = Path("evaluation/development/multitest-code-slice-v3_3/prototype-sweep").resolve()
sys.path.insert(0, str(_ROOT))
try:
    _harness = runpy.run_path(str(_ROOT / "harness.py"))
finally:
    sys.path.remove(str(_ROOT))

_REFERENCE_CASE = cast(Callable[[str], Any], _harness["reference_case"])
_INPUTS = cast(Callable[[Any, bytes | None], dict[str, Any]], _harness["inputs"])


def _classification(key: str, source: str) -> tuple[str | None, str | None, tuple[int, ...]]:
    values = _INPUTS(_REFERENCE_CASE(key), source.encode("utf-8"))
    content = cast(bytes, values.pop("content"))
    result: MultipleTestingDataflowResult = analyze_code_csv_multiple_testing_dataflow(
        content, **values
    )
    return (
        result.reason,
        None if result.facts is None else result.facts.correction_classification,
        () if result.facts is None else result.facts.corrected_positions,
    )


def test_terminal_proofs_ignore_prose_display_and_noncallee_renames() -> None:
    keys = (
        "E16:P2:7a43fa7b50f1b99e5034",
        "E16:P4:9ced761b41ef93485acf",
    )
    for key in keys:
        case = _REFERENCE_CASE(key)
        source = case.source_path.read_text(encoding="utf-8")
        baseline = _classification(key, source)
        assert baseline == (None, "none", ())
        mutations = (
            "# hierarchical-gatekeeping-present correction significant\n" + source,
            source.replace("significant", "xxxxxxxxxxx").replace(
                "not xxxxxxxxxxx", "yyy yyyyyyyyyyy"
            ),
            source.replace("p_value", "benjamini_value"),
            source.replace("verdict", "bonferroni"),
        )
        assert {_classification(key, item) for item in mutations} == {baseline}


def test_helper_proof_ignores_docstrings_display_and_record_key_spellings() -> None:
    key = "E16:P3:5a9c5b4377c33916d672"
    case = _REFERENCE_CASE(key)
    source = case.source_path.read_text(encoding="utf-8")
    baseline = _classification(key, source)
    assert baseline == (None, "none", ())
    mutations = (
        source.replace(
            "Two-sample t-test for one outcome, shallow versus deep roofs.",
            "Arbitrary non-scientific helper documentation of equal structural status.",
        ),
        source.replace('"SIGNIFICANT"', '"DISPLAY-ONLY"').replace(
            '"not significant"', '"other display  "'
        ),
        source.replace('"p_value"', '"holm_value"').replace("['p_value']", "['holm_value']"),
        source.replace('"significant"', '"sidak_flag"').replace(
            "['significant']", "['sidak_flag']"
        ),
    )
    assert {_classification(key, item) for item in mutations} == {baseline}


def test_structural_literal_and_callee_mutations_break_the_proof() -> None:
    key = "E16:P3:5a9c5b4377c33916d672"
    source = _REFERENCE_CASE(key).source_path.read_text(encoding="utf-8")
    mutations = (
        source.replace('    "invert_abundance_count",\n', ""),
        source.replace("stats.ttest_ind", "stats.bonferroni"),
    )
    for mutation in mutations:
        reason, classification, _positions = _classification(key, mutation)
        assert reason is not None
        assert classification is None
