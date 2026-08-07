"""ADR-0069 static dataflow resolution of a rate's exposure denominator.

This library works backward from the division that produces a rate. It reads
each Python workflow source statically, tags every variable's provenance
(the full row set read from the staged input, a screened subset produced by a
filtering comprehension, and counts taken over either), and classifies each
division whose numerator and denominator are data-derived counts: a
denominator that resolves to a count of the screened subset is the
retained-subset exposure, and a denominator that resolves to a count of the
full row set is the complete-domain exposure. Variable names never matter;
only the operations do, so a rate printed as a bare integer in the report is
still resolvable on this plane. The quantity-consistency adapter consumes
this resolver and fuses it with the report-plane arithmetic; conflicting
division classifications or untraceable control flow resolve to explicit
non-unique states rather than guesses.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.core import (
    EvidenceSpan,
    FrozenInspectionContext,
    InspectionDocument,
)

QUANTITY_DATAFLOW_IMPLEMENTATION_DIGEST = sha256_digest(Path(__file__).read_bytes())

_ROWS_FULL = "rows_full"
_ROWS_SUBSET = "rows_subset"
_ROWS_ITER_FULL = "rows_iter_full"
_COUNT_FULL = "count_full"
_COUNT_SUBSET = "count_subset"
_INT_OTHER = "int_other"
_OTHER = "other"

_UNSUPPORTED_STATEMENTS = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.If,
    ast.With,
    ast.AsyncWith,
    ast.Try,
)


def quantity_dataflow_grammar(complete_operand: str, retained_operand: str) -> dict[str, Any]:
    return {
        "grammar_id": "quantity-denominator-dataflow",
        "grammar_version": "1.1.0",
        "row_source_operations": ["csv.DictReader", "csv.reader"],
        "subset_operation": "single-generator comprehension with a filter over a row set",
        "count_operations": ["len(rows)", "sum(1 for ... in rows [if ...])"],
        "division_forms": ["a / b", "Fraction(a, b)"],
        "function_support": "straight-line bodies with return-value tagging",
        "division_rule": (
            "a division with a data-derived count numerator classifies by its "
            "denominator's provenance"
        ),
        "operand_by_denominator": {
            "count_of_full_row_set": complete_operand,
            "count_of_screened_subset": retained_operand,
        },
        "control_flow": (
            "straight-line assignments, comprehensions, with-blocks, functions, "
            "and the __main__ guard"
        ),
        "nomenclature_authority": "none",
    }


def quantity_dataflow_grammar_digest(complete_operand: str, retained_operand: str) -> str:
    return semantic_digest(quantity_dataflow_grammar(complete_operand, retained_operand))


@dataclass(frozen=True)
class _Division:
    node: ast.BinOp
    operand_value: str


@dataclass(frozen=True)
class DataflowResolution:
    """The outcome of the bounded source trace across every Python document."""

    state: str  # "unique" | "none" | "ambiguous" | "unsupported"
    operand_value: str | None
    spans: tuple[EvidenceSpan, ...]
    source_path: str | None


def resolve_dataflow_operand(
    context: FrozenInspectionContext,
    *,
    complete_operand: str,
    retained_operand: str,
    parser_id: str,
    parser_version: str,
) -> DataflowResolution:
    divisions: list[tuple[InspectionDocument, _Division]] = []
    triggered = False
    unsupported_flow = False
    parse_failure = False
    for document in context.documents:
        if document.media_type != "text/x-python" or not _python_parser_supported(
            document, parser_id, parser_version
        ):
            continue
        try:
            tree = ast.parse(document.content.decode("utf-8"), filename=document.path)
        except (SyntaxError, UnicodeDecodeError):
            parse_failure = True
            continue
        outcome = _document_divisions(
            tree,
            complete_operand=complete_operand,
            retained_operand=retained_operand,
        )
        triggered = triggered or outcome["triggered"]
        unsupported_flow = unsupported_flow or outcome["unsupported_flow"]
        divisions.extend((document, item) for item in outcome["divisions"])
    operand_values = sorted({item.operand_value for _, item in divisions})
    if len(operand_values) > 1:
        return DataflowResolution("ambiguous", None, (), None)
    if unsupported_flow or parse_failure:
        # A resolved division next to untraceable control flow could be
        # rebound by that flow; report unsupported rather than guess.
        return DataflowResolution("unsupported", None, (), None)
    if not divisions:
        return DataflowResolution("none", None, (), None)
    spans = tuple(
        _ast_node_evidence_span(item_document, item.node) for item_document, item in divisions
    )
    return DataflowResolution("unique", operand_values[0], spans, divisions[0][0].path)


def _python_parser_supported(
    document: InspectionDocument, parser_id: str, parser_version: str
) -> bool:
    if document.parser_result_payload is None:
        return False
    import json as _json

    value = _json.loads(document.parser_result_payload)
    return (
        isinstance(value, dict)
        and value.get("parser_id") == parser_id
        and value.get("parser_version") == parser_version
        and value.get("state") == "parsed"
    )


def _document_divisions(
    tree: ast.Module, *, complete_operand: str, retained_operand: str
) -> dict[str, Any]:
    """Trace divisions across the module scope and straight-line function bodies.

    Ordinary authored workflows wrap their logic in functions, use ``with``
    for file handles, and gate execution behind the ``__main__`` idiom; all
    of those stay traceable. Loops, conditionals beyond the ``__main__``
    guard, try blocks, and classes remain out of bounds and mark the
    document unsupported.
    """

    unsupported_flow = _has_unsupported_flow(tree)
    functions: dict[str, ast.FunctionDef] = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    # Return-value tags for straight-line functions, iterated to a small
    # fixpoint so simple helper chains (load -> list -> filter) resolve.
    returns: dict[str, str] = {}
    for _ in range(3):
        for name, function in functions.items():
            returns[name] = _function_return_tag(function, returns)
    divisions: list[_Division] = []
    read_present = False
    any_division = False

    def _scan_scope(statements: list[ast.stmt], env: dict[str, str]) -> bool:
        nonlocal any_division
        saw_read = False
        for statement in _flatten_statements(statements):
            for node in ast.walk(statement):
                pair = _division_operands(node)
                if pair is None:
                    continue
                any_division = True
                numerator = _numerator_tag(pair[0], env, returns)
                denominator = _tag(pair[1], env, returns)
                if numerator in {_COUNT_FULL, _COUNT_SUBSET} and denominator in {
                    _COUNT_FULL,
                    _COUNT_SUBSET,
                }:
                    divisions.append(
                        _Division(
                            node=node,
                            operand_value=(
                                retained_operand
                                if denominator == _COUNT_SUBSET
                                else complete_operand
                            ),
                        )
                    )
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                tag = _tag(statement.value, env, returns)
                env[statement.targets[0].id] = tag
                if tag in {_ROWS_FULL, _ROWS_ITER_FULL}:
                    saw_read = True
        return saw_read

    module_env: dict[str, str] = {}
    read_present = _scan_scope(
        [s for s in tree.body if not isinstance(s, ast.FunctionDef)], module_env
    )
    for function in functions.values():
        env = dict(module_env)
        if _scan_scope(function.body, env):
            read_present = True
    return {
        "divisions": divisions,
        "triggered": read_present and any_division,
        "unsupported_flow": unsupported_flow,
    }


def _has_unsupported_flow(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.With | ast.AsyncWith):
            continue
        if isinstance(node, ast.If) and _is_main_guard(node):
            continue
        if isinstance(node, _UNSUPPORTED_STATEMENTS):
            if isinstance(node, ast.FunctionDef):
                continue
            return True
    return False


def _is_main_guard(node: ast.If) -> bool:
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def _flatten_statements(statements: list[ast.stmt]) -> list[ast.stmt]:
    flat: list[ast.stmt] = []
    for statement in statements:
        if isinstance(statement, ast.With):
            flat.extend(_flatten_statements(statement.body))
        elif isinstance(statement, ast.If) and _is_main_guard(statement):
            flat.extend(_flatten_statements(statement.body))
        else:
            flat.append(statement)
    return flat


def _function_return_tag(function: ast.FunctionDef, returns: dict[str, str]) -> str:
    env: dict[str, str] = {}
    tag = _OTHER
    for statement in _flatten_statements(function.body):
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            env[statement.targets[0].id] = _tag(statement.value, env, returns)
        elif isinstance(statement, ast.Return) and statement.value is not None:
            tag = _tag(statement.value, env, returns)
    return tag


def _division_operands(node: ast.AST) -> tuple[ast.expr, ast.expr] | None:
    """A division is `a / b` or the exact-arithmetic form `Fraction(a, b)`."""

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return node.left, node.right
    if (
        isinstance(node, ast.Call)
        and _call_name(node) in {"Fraction", "fractions.Fraction"}
        and len(node.args) == 2
        and not node.keywords
    ):
        return node.args[0], node.args[1]
    return None


def _numerator_tag(node: ast.expr, env: dict[str, str], returns: dict[str, str]) -> str:
    """The numerator may carry a constant scale factor (100 * events)."""

    tag = _tag(node, env, returns)
    if tag in {_COUNT_FULL, _COUNT_SUBSET}:
        return tag
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        left = _tag(node.left, env, returns)
        right = _tag(node.right, env, returns)
        counts = {left, right} & {_COUNT_FULL, _COUNT_SUBSET}
        others = {left, right} - counts
        if len(counts) == 1 and others <= {_INT_OTHER}:
            return next(iter(counts))
    return tag


def _tag(node: ast.expr, env: dict[str, str], returns: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return env.get(node.id, _OTHER)
    if isinstance(node, ast.Constant):
        return _INT_OTHER if isinstance(node.value, (int, float)) else _OTHER
    if isinstance(node, ast.Call):
        return _tag_call(node, env, returns)
    if isinstance(node, ast.ListComp | ast.GeneratorExp):
        return _tag_comprehension(node, env, returns)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add | ast.Sub | ast.Mult):
        left = _tag(node.left, env, returns)
        right = _tag(node.right, env, returns)
        numericish = {_COUNT_FULL, _COUNT_SUBSET, _INT_OTHER}
        if left in numericish and right in numericish:
            return _INT_OTHER
        return _OTHER
    return _OTHER


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return f"{node.func.value.id}.{node.func.attr}"
    if isinstance(node.func, ast.Name):
        return node.func.id
    return ""


def _tag_call(node: ast.Call, env: dict[str, str], returns: dict[str, str]) -> str:
    name = _call_name(node)
    if name in {"csv.DictReader", "csv.reader", "DictReader", "reader"}:
        return _ROWS_ITER_FULL
    if name in returns and not node.args and not node.keywords:
        return returns[name]
    if name == "list" and len(node.args) == 1:
        inner = _tag(node.args[0], env, returns)
        if inner in {_ROWS_ITER_FULL, _ROWS_FULL}:
            return _ROWS_FULL
        if inner == _ROWS_SUBSET:
            return _ROWS_SUBSET
        return _OTHER
    if name == "len" and len(node.args) == 1:
        inner = _tag(node.args[0], env, returns)
        if inner == _ROWS_FULL:
            return _COUNT_FULL
        if inner == _ROWS_SUBSET:
            return _COUNT_SUBSET
        return _INT_OTHER if inner in {_ROWS_ITER_FULL} else _OTHER
    if name == "sum" and len(node.args) == 1:
        argument = node.args[0]
        if isinstance(argument, ast.GeneratorExp | ast.ListComp):
            return _tag_counting_comprehension(argument, env, returns)
        return _OTHER
    return _OTHER


def _tag_comprehension(
    node: ast.ListComp | ast.GeneratorExp, env: dict[str, str], returns: dict[str, str]
) -> str:
    if len(node.generators) != 1:
        return _OTHER
    generator = node.generators[0]
    source = _tag(generator.iter, env, returns)
    if source not in {_ROWS_FULL, _ROWS_SUBSET}:
        return _OTHER
    if generator.ifs:
        return _ROWS_SUBSET
    return source


def _tag_counting_comprehension(
    node: ast.ListComp | ast.GeneratorExp, env: dict[str, str], returns: dict[str, str]
) -> str:
    """sum(1 for row in X [if ...]) is a count over X or a conditioned subset."""

    if len(node.generators) != 1:
        return _OTHER
    element = node.elt
    if not (isinstance(element, ast.Constant) and element.value == 1):
        return _OTHER
    generator = node.generators[0]
    source = _tag(generator.iter, env, returns)
    if source not in {_ROWS_FULL, _ROWS_SUBSET}:
        return _OTHER
    if generator.ifs or source == _ROWS_SUBSET:
        return _COUNT_SUBSET
    return _COUNT_FULL


def _ast_node_evidence_span(document: InspectionDocument, node: ast.AST) -> EvidenceSpan:
    assert document.parser_result_ref is not None
    assert document.source_location is not None
    start_line = getattr(node, "lineno", 1)
    end_line = getattr(node, "end_lineno", start_line)
    lines = document.content.decode("utf-8").splitlines()
    start_column = getattr(node, "col_offset", 0) + 1
    end_offset = getattr(node, "end_col_offset", None)
    if end_offset is None:
        end_column = len(lines[end_line - 1]) if 1 <= end_line <= len(lines) else 1
    else:
        end_column = end_offset + 1
    return EvidenceSpan(
        file_ref=document.file_ref,
        path=document.path,
        content_digest=document.source_location.content_digest,
        start_line=start_line + document.line_offset,
        end_line=end_line + document.line_offset,
        start_column=start_column,
        end_column=end_column,
        parser_result_ref=document.parser_result_ref,
    )
