from __future__ import annotations

import ast
from collections.abc import Sequence
from typing import Any

from sc_referee.core.ids import semantic_digest

RENDER_ONLY_PROFILE_ID = "authoring-render-only-v1"
REQUIRED_PREFIX = (
    "from pathlib import Path",
    "SOURCE_TEXT = Path('inputs/data.csv').read_text()",
    "SOURCE_LINES = SOURCE_TEXT.splitlines()",
    "SOURCE_LINE_COUNT = len(SOURCE_LINES)",
    "LF = SOURCE_TEXT[len(SOURCE_LINES[0])]",
)
REQUIRED_FINAL_WRITER = "Path('results/report.md').write_text(REPORT_TEXT)"


class RenderGrammarError(ValueError):
    pass


def _expression_dependencies(
    node: ast.expr,
    *,
    dependencies_by_name: dict[str, frozenset[str]],
) -> frozenset[str]:
    if isinstance(node, ast.Constant):
        if type(node.value) not in {str, int, float}:
            raise RenderGrammarError("render_expression_has_unsupported_constant")
        if isinstance(node.value, str) and not node.value.isascii():
            raise RenderGrammarError("render_expression_has_non_ascii_string")
        return frozenset()
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
        if node.id not in dependencies_by_name:
            raise RenderGrammarError("render_expression_uses_unavailable_name")
        return dependencies_by_name[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _expression_dependencies(
            node.left, dependencies_by_name=dependencies_by_name
        ) | _expression_dependencies(node.right, dependencies_by_name=dependencies_by_name)
    if isinstance(node, ast.JoinedStr):
        dependencies: frozenset[str] = frozenset()
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                if not value.value.isascii():
                    raise RenderGrammarError("render_fstring_has_non_ascii_text")
                continue
            if not isinstance(value, ast.FormattedValue):
                raise RenderGrammarError("render_fstring_has_unsupported_part")
            if value.conversion != -1 or value.format_spec is not None:
                raise RenderGrammarError("render_fstring_has_conversion_or_format_spec")
            if not isinstance(value.value, ast.Name) or not isinstance(value.value.ctx, ast.Load):
                raise RenderGrammarError("render_fstring_field_is_not_plain_name")
            dependencies |= _expression_dependencies(
                value.value, dependencies_by_name=dependencies_by_name
            )
        return dependencies
    raise RenderGrammarError("render_expression_outside_frozen_grammar")


def validate_render_only_producer(content_lines: Sequence[str]) -> dict[str, Any]:
    lines = list(content_lines)
    if len(lines) < 8:
        raise RenderGrammarError("producer_too_short_for_render_only_grammar")
    if any(not isinstance(line, str) or not line or not line.isascii() for line in lines):
        raise RenderGrammarError("producer_lines_must_be_nonempty_ascii")
    if tuple(lines[:5]) != REQUIRED_PREFIX:
        raise RenderGrammarError("producer_prefix_does_not_match_frozen_grammar")
    if lines[-1] != REQUIRED_FINAL_WRITER:
        raise RenderGrammarError("producer_final_writer_does_not_match_frozen_grammar")

    source = "\n".join(lines) + "\n"
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise RenderGrammarError("producer_is_not_valid_python") from error
    if len(tree.body) != len(lines):
        raise RenderGrammarError("producer_requires_one_statement_per_physical_line")
    for line_number, statement in enumerate(tree.body, start=1):
        if statement.lineno != line_number or statement.end_lineno != line_number:
            raise RenderGrammarError("producer_statement_crosses_physical_lines")

    dependencies_by_name = {
        "SOURCE_LINE_COUNT": frozenset({"SOURCE_LINE_COUNT"}),
        "LF": frozenset({"LF"}),
    }
    assigned_names = {"SOURCE_TEXT", "SOURCE_LINES", "SOURCE_LINE_COUNT", "LF"}
    rendered_names: list[str] = []
    for statement in tree.body[5:-1]:
        if (
            not isinstance(statement, ast.Assign)
            or len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
        ):
            raise RenderGrammarError("render_statement_is_not_simple_assignment")
        name = statement.targets[0].id
        if name in assigned_names:
            raise RenderGrammarError("render_name_is_reassigned")
        dependencies = _expression_dependencies(
            statement.value, dependencies_by_name=dependencies_by_name
        )
        assigned_names.add(name)
        dependencies_by_name[name] = dependencies
        rendered_names.append(name)

    if rendered_names.count("REPORT_TEXT") != 1:
        raise RenderGrammarError("report_text_must_be_assigned_once")
    if rendered_names[-1] != "REPORT_TEXT":
        raise RenderGrammarError("report_text_must_be_last_render_assignment")
    report_dependencies = dependencies_by_name["REPORT_TEXT"]
    if "SOURCE_LINE_COUNT" not in report_dependencies:
        raise RenderGrammarError("report_text_lacks_source_line_count_dependency")
    if "LF" not in report_dependencies:
        raise RenderGrammarError("report_text_lacks_lf_dependency")

    result: dict[str, Any] = {
        "grammar_profile_id": RENDER_ONLY_PROFILE_ID,
        "status": "valid_render_only_producer",
        "assignment_names": rendered_names,
        "report_dependencies": sorted(report_dependencies),
    }
    result["validation_digest"] = semantic_digest(result)
    return result
