from __future__ import annotations

from copy import deepcopy

import pytest
from sc_referee_evaluation.authoring_render_grammar import (
    RenderGrammarError,
    validate_render_only_producer,
)


def _valid_lines() -> list[str]:
    return [
        "from pathlib import Path",
        "SOURCE_TEXT = Path('inputs/data.csv').read_text()",
        "SOURCE_LINES = SOURCE_TEXT.splitlines()",
        "SOURCE_LINE_COUNT = len(SOURCE_LINES)",
        "LF = SOURCE_TEXT[len(SOURCE_LINES[0])]",
        "EVENTS = 18",
        "RESULT_LINE = f'[selected-result] lines={SOURCE_LINE_COUNT}; events={EVENTS}' + LF",
        "REPORT_TEXT = RESULT_LINE",
        "Path('results/report.md').write_text(REPORT_TEXT)",
    ]


def test_render_only_grammar_accepts_literal_name_add_and_plain_fstring() -> None:
    result = validate_render_only_producer(_valid_lines())
    assert result["status"] == "valid_render_only_producer"
    assert result["assignment_names"] == ["EVENTS", "RESULT_LINE", "REPORT_TEXT"]
    assert result["report_dependencies"] == ["LF", "SOURCE_LINE_COUNT"]


@pytest.mark.parametrize(
    ("replacement", "reason"),
    [
        ("EVENTS = SOURCE_LINES[1][-1]", "outside_frozen_grammar"),
        ("EVENTS = int('18')", "outside_frozen_grammar"),
        ("EVENTS = SOURCE_TEXT.strip()", "outside_frozen_grammar"),
        ("EVENTS = -18", "outside_frozen_grammar"),
        ("EVENTS = SOURCE_TEXT", "unavailable_name"),
    ],
)
def test_render_only_grammar_rejects_post_prefix_parsing_surfaces(
    replacement: str, reason: str
) -> None:
    lines = _valid_lines()
    lines[5] = replacement
    with pytest.raises(RenderGrammarError, match=reason):
        validate_render_only_producer(lines)


def test_render_only_grammar_rejects_complex_fstring_field() -> None:
    lines = _valid_lines()
    lines[6] = (
        "RESULT_LINE = f'[selected-result] lines={SOURCE_LINE_COUNT:03d}; events={EVENTS}' + LF"
    )
    with pytest.raises(RenderGrammarError, match="conversion_or_format_spec"):
        validate_render_only_producer(lines)


def test_render_only_grammar_rejects_duplicate_or_late_report_text() -> None:
    duplicate = _valid_lines()
    duplicate.insert(-1, "EVENTS = 19")
    with pytest.raises(RenderGrammarError, match="render_name_is_reassigned"):
        validate_render_only_producer(duplicate)

    late = _valid_lines()
    late.insert(-1, "AFTER_REPORT = 'x'")
    with pytest.raises(RenderGrammarError, match="report_text_must_be_last"):
        validate_render_only_producer(late)


def test_render_only_grammar_requires_input_and_lf_dependencies() -> None:
    no_input = deepcopy(_valid_lines())
    no_input[6] = "RESULT_LINE = f'[selected-result] events={EVENTS}' + LF"
    with pytest.raises(RenderGrammarError, match="lacks_source_line_count"):
        validate_render_only_producer(no_input)

    no_lf = deepcopy(_valid_lines())
    no_lf[6] = "RESULT_LINE = f'[selected-result] lines={SOURCE_LINE_COUNT}; events={EVENTS}'"
    with pytest.raises(RenderGrammarError, match="lacks_lf_dependency"):
        validate_render_only_producer(no_lf)
