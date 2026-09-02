from __future__ import annotations

import runpy
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_4 import (
    MultipleTestingDataflowResult,
    analyze_code_csv_multiple_testing_dataflow,
)

_ROOT = Path("evaluation/development/multitest-code-slice-v3_4/prototype-sweep").resolve()
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


_P3_KEY = "E17:P3:a2e031f79e31c80fd900"
_P6_KEY = "E17:P6:b4e507c4b55954752f14"


def _source(key: str) -> str:
    return _REFERENCE_CASE(key).source_path.read_text(encoding="utf-8")


def test_comprehension_normalization_ignores_prose_display_and_identifier_spelling() -> None:
    """Extension A reads node kinds, spans, and closed identities, never spellings."""

    source = _source(_P3_KEY)
    baseline = _classification(_P3_KEY, source)
    assert baseline == (None, "none", ())
    mutations = (
        "# hierarchical-gatekeeping-present bonferroni correction significant holm\n" + source,
        source.replace(
            "One compact collection of per-outcome results, built in a single pass over",
            "Arbitrary non-scientific commentary of exactly equal structural status here",
        ),
        source.replace("results", "bonferroni_table"),
        source.replace("outcome", "holm_key"),
        source.replace("compare_settings", "apply_bonferroni_correction"),
        source.replace('"p":', '"holm_p":').replace('result["p"]', 'result["holm_p"]'),
        source.replace('"SIGNIFICANT"', '"DISPLAY-ONLY"').replace(
            '"not significant"', '"other display  "'
        ),
        source.replace("  p = {:.6f}", "  q = {:.6f}"),
    )
    assert {_classification(_P3_KEY, item) for item in mutations} == {baseline}


def test_comprehension_structural_mutations_break_the_proof() -> None:
    """The paired positive control: a deleted contract literal or a real callee change moves it."""

    source = _source(_P3_KEY)
    for mutation in (
        source.replace('    "zinc_mg_kg",\n', ""),
        source.replace("stats.ttest_ind", "stats.bonferroni"),
    ):
        reason, classification, _positions = _classification(_P3_KEY, mutation)
        assert reason is not None
        assert classification is None


def test_enumerate_and_cap_admissions_ignore_counter_and_folded_name_spelling() -> None:
    """Extension C matches an unshadowed builtin callee and a binding position, not a name."""

    source = _source(_P6_KEY)
    baseline = _classification(_P6_KEY, source)
    assert baseline == (None, "strict_subset", (0, 1, 2))
    mutations = (
        "# enumerate start counter bonferroni holm sidak capped correction\n" + source,
        source.replace("position", "bonferroni_index"),
        source.replace("corrected_p", "raw_holm_value"),
        source.replace("raw_p", "adjusted_value"),
        source.replace("N_COMPARISONS", "HOLM_FACTOR"),
        source.replace('"SIGNIFICANT"', '"DISPLAY ONLY"').replace(
            '"NOT SIGNIFICANT"', '"OTHER DISPLAY  "'
        ),
        source.replace(
            "Correct by hand: multiply by the number of comparisons, cap at one.",
            "Arbitrary commentary of exactly equal structural status kept at length.",
        ),
    )
    assert {_classification(_P6_KEY, item) for item in mutations} == {baseline}


def test_enumerate_and_cap_structural_mutations_break_the_proof() -> None:
    source = _source(_P6_KEY)
    for mutation in (
        source.replace('    "work_engagement_0_6",\n', ""),
        source.replace("stats.ttest_ind", "stats.bonferroni"),
    ):
        reason, classification, _positions = _classification(_P6_KEY, mutation)
        assert reason is not None
        assert classification is None
