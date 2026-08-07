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
        "grammar_version": "1.0.0",
        "row_source_operations": ["csv.DictReader", "csv.reader"],
        "subset_operation": "single-generator comprehension with a filter over a row set",
        "count_operations": ["len(rows)", "sum(1 for ... in rows [if ...])"],
        "division_rule": (
            "a division with a data-derived count numerator classifies by its "
            "denominator's provenance"
        ),
        "operand_by_denominator": {
            "count_of_full_row_set": complete_operand,
            "count_of_screened_subset": retained_operand,
        },
        "control_flow": "straight-line assignments and comprehensions only",
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
    unsupported_flow = any(isinstance(node, _UNSUPPORTED_STATEMENTS) for node in ast.walk(tree))
    env: dict[str, str] = {}
    divisions: list[_Division] = []
    read_present = False
    for statement in tree.body:
        for node in ast.walk(statement):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                numerator = _numerator_tag(node.left, env)
                denominator = _tag(node.right, env)
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
            tag = _tag(statement.value, env)
            env[statement.targets[0].id] = tag
            if tag in {_ROWS_FULL, _ROWS_ITER_FULL}:
                read_present = True
    return {
        "divisions": divisions,
        "triggered": read_present
        and any(
            isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) for node in ast.walk(tree)
        ),
        "unsupported_flow": unsupported_flow,
    }


def _numerator_tag(node: ast.expr, env: dict[str, str]) -> str:
    """The numerator may carry a constant scale factor (100 * events)."""

    tag = _tag(node, env)
    if tag in {_COUNT_FULL, _COUNT_SUBSET}:
        return tag
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        left = _tag(node.left, env)
        right = _tag(node.right, env)
        counts = {left, right} & {_COUNT_FULL, _COUNT_SUBSET}
        others = {left, right} - counts
        if len(counts) == 1 and others <= {_INT_OTHER}:
            return next(iter(counts))
    return tag


def _tag(node: ast.expr, env: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return env.get(node.id, _OTHER)
    if isinstance(node, ast.Constant):
        return _INT_OTHER if isinstance(node.value, (int, float)) else _OTHER
    if isinstance(node, ast.Call):
        return _tag_call(node, env)
    if isinstance(node, ast.ListComp | ast.GeneratorExp):
        return _tag_comprehension(node, env)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add | ast.Sub | ast.Mult):
        left = _tag(node.left, env)
        right = _tag(node.right, env)
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


def _tag_call(node: ast.Call, env: dict[str, str]) -> str:
    name = _call_name(node)
    if name in {"csv.DictReader", "csv.reader", "DictReader", "reader"}:
        return _ROWS_ITER_FULL
    if name == "list" and len(node.args) == 1:
        inner = _tag(node.args[0], env)
        if inner in {_ROWS_ITER_FULL, _ROWS_FULL}:
            return _ROWS_FULL
        if inner == _ROWS_SUBSET:
            return _ROWS_SUBSET
        return _OTHER
    if name == "len" and len(node.args) == 1:
        inner = _tag(node.args[0], env)
        if inner == _ROWS_FULL:
            return _COUNT_FULL
        if inner == _ROWS_SUBSET:
            return _COUNT_SUBSET
        return _INT_OTHER if inner in {_ROWS_ITER_FULL} else _OTHER
    if name == "sum" and len(node.args) == 1:
        argument = node.args[0]
        if isinstance(argument, ast.GeneratorExp | ast.ListComp):
            return _tag_counting_comprehension(argument, env)
        return _OTHER
    return _OTHER


def _tag_comprehension(node: ast.ListComp | ast.GeneratorExp, env: dict[str, str]) -> str:
    if len(node.generators) != 1:
        return _OTHER
    generator = node.generators[0]
    source = _tag(generator.iter, env)
    if source not in {_ROWS_FULL, _ROWS_SUBSET}:
        return _OTHER
    if generator.ifs:
        return _ROWS_SUBSET
    return source


def _tag_counting_comprehension(node: ast.ListComp | ast.GeneratorExp, env: dict[str, str]) -> str:
    """sum(1 for row in X [if ...]) is a count over X or a conditioned subset."""

    if len(node.generators) != 1:
        return _OTHER
    element = node.elt
    if not (isinstance(element, ast.Constant) and element.value == 1):
        return _OTHER
    generator = node.generators[0]
    source = _tag(generator.iter, env)
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
