"""Executed, recon-only prototypes for the two narrow E13 delta ideas."""

from __future__ import annotations

import ast
from collections import Counter, defaultdict
from collections.abc import Callable
from typing import Any

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_2 as mt

Analyzer = Callable[..., mt.MultipleTestingDataflowResult]


def admit_static_local_reader_path(content: bytes) -> bytes:
    """Normalize an exact single-binding static path Name at a recognized reader call."""

    tree = mt._bounded_parse(content)
    full_scope = tuple(item for item in tree.body if not mt._is_docstring(item))
    resolver, reason = mt._resolver(full_scope)
    if reason is not None or resolver is None:
        return content
    definitions: dict[str, list[ast.expr]] = defaultdict(list)
    stores: Counter[str] = Counter()
    unsafe: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                for name in mt._store_names(target):
                    stores[name] += 1
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                definitions[node.targets[0].id].append(node.value)
        elif isinstance(node, ast.AnnAssign):
            for name in mt._store_names(node.target):
                stores[name] += 1
            if isinstance(node.target, ast.Name) and node.value is not None:
                definitions[node.target.id].append(node.value)
        elif isinstance(node, (ast.AugAssign, ast.Delete, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Delete) else (node.target,)
            unsafe.update(name for target in targets for name in mt._store_names(target))

    replacements: list[tuple[int, int, str]] = []
    text = content.decode("utf-8", errors="strict")
    line_starts = [0]
    for line in text.splitlines(keepends=True):
        line_starts.append(line_starts[-1] + len(line))

    class Normalize(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            if not (
                resolver.qualified(node.func) in {"pandas.read_csv", "numpy.genfromtxt"}
                and len(node.args) == 1
                and isinstance(node.args[0], ast.Name)
            ):
                self.generic_visit(node)
                return
            if mt._static_path(node.args[0], resolver) is not None:
                self.generic_visit(node)
                return
            name = node.args[0].id
            expressions = definitions.get(name, ())
            if stores[name] != 1 or name in unsafe or len(expressions) != 1:
                self.generic_visit(node)
                return
            expression = expressions[0]
            if mt._static_path(expression, resolver) is None:
                self.generic_visit(node)
                return
            replacement = ast.get_source_segment(text, expression)
            argument = node.args[0]
            if (
                replacement is None
                or argument.end_lineno is None
                or argument.end_col_offset is None
            ):
                return
            start = line_starts[argument.lineno - 1] + argument.col_offset
            end = line_starts[argument.end_lineno - 1] + argument.end_col_offset
            replacements.append((start, end, replacement))

    normalizer = Normalize()
    normalizer.visit(tree)
    if not replacements:
        return content
    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text.encode("utf-8")


def reader_path_analyzer(content: bytes, **kwargs: Any) -> mt.MultipleTestingDataflowResult:
    return mt.analyze_code_csv_multiple_testing_dataflow(
        admit_static_local_reader_path(content), **kwargs
    )


def terminal_clone_position_analyzer(
    content: bytes, **kwargs: Any
) -> mt.MultipleTestingDataflowResult:
    """Close cloned-node provenance by position without changing the R1/terminal grammar."""

    tree = mt._bounded_parse(content)
    shaped_helpers = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and len(body := [item for item in node.body if not mt._is_docstring(item)]) == 1
        and isinstance(body[0], ast.Return)
        and isinstance(body[0].value, ast.IfExp)
        and isinstance(body[0].value.body, ast.Constant)
        and isinstance(body[0].value.body.value, str)
        and isinstance(body[0].value.orelse, ast.Constant)
        and isinstance(body[0].value.orelse.value, str)
    }
    if not shaped_helpers or not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in shaped_helpers
        for node in ast.walk(tree)
    ):
        return mt.analyze_code_csv_multiple_testing_dataflow(content, **kwargs)

    original_percent = mt._MtEngine._literal_percent_presentation
    original_ifexp = mt._MtEngine._terminal_rendering_ifexp

    def position_reaches_sink(engine: Any, node: ast.AST) -> bool:
        position = mt._position(node)
        sinks = (
            *engine.sinks,
            *mt._registered_sinks(engine.original_scope, engine.full_resolver),
        )
        return any(
            sink.p_result_eligible
            and any(
                mt._position(descendant) == position
                for payload in sink.payloads
                for descendant in ast.walk(payload)
            )
            for sink in sinks
        )

    def percent(engine: Any, node: ast.BinOp) -> bool:
        if original_percent(engine, node):
            return True
        return bool(
            isinstance(node.op, ast.Mod)
            and mt._mt_v21_display_string(node.left)
            and engine._p_origins(node.right)
            and position_reaches_sink(engine, node)
        )

    def ifexp(engine: Any, node: ast.IfExp) -> bool:
        if original_ifexp(engine, node):
            return True
        return bool(
            getattr(node, "_sc_mt_terminal_rendering", False)
            and len(engine._decision_positions_in_expr(node.test, set(), 0)) == 1
            and position_reaches_sink(engine, node)
        )

    mt._MtEngine._literal_percent_presentation = percent
    mt._MtEngine._terminal_rendering_ifexp = ifexp
    try:
        return mt.analyze_code_csv_multiple_testing_dataflow(content, **kwargs)
    finally:
        mt._MtEngine._literal_percent_presentation = original_percent
        mt._MtEngine._terminal_rendering_ifexp = original_ifexp


def combined_analyzer(content: bytes, **kwargs: Any) -> mt.MultipleTestingDataflowResult:
    return terminal_clone_position_analyzer(admit_static_local_reader_path(content), **kwargs)


PROTOTYPES: dict[str, Analyzer] = {
    "baseline-2.2": mt.analyze_code_csv_multiple_testing_dataflow,
    "D-reader-static-local-binding": reader_path_analyzer,
    "D-terminal-clone-position-closure": terminal_clone_position_analyzer,
    "D-combined": combined_analyzer,
}
