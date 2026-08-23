"""Independent, non-executing verifier for the one closed world-1 source flow."""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from typing import Final, NoReturn, cast

from sc_referee_evaluation.audit_ladder.slice_c.core import sha256

_SOURCE_SIZE: Final = 1_015
_SOURCE_DIGEST: Final = "sha256:c5f3bb51457ace3e4b979b69739f212b9d0c7a12baba62033859d31f5b2ade18"
_AST_DUMP_SHA256: Final = "fbf46d76762d0580584caca2883dfa3497b1d0bf4a4f2bb7fadad5cb48e5f299"
_ALLOWED_NODE_TYPES: Final = frozenset(
    {
        ast.Module,
        ast.Import,
        ast.ImportFrom,
        ast.alias,
        ast.Assign,
        ast.Expr,
        ast.Name,
        ast.Load,
        ast.Store,
        ast.Tuple,
        ast.Call,
        ast.Attribute,
        ast.Constant,
        ast.Subscript,
        ast.Compare,
        ast.Eq,
        ast.Slice,
        ast.JoinedStr,
        ast.FormattedValue,
    }
)


class SourceVerificationError(RuntimeError):
    """The digest-bound source does not prove the closed world-1 flow."""


def _fail(message: str) -> NoReturn:
    raise SourceVerificationError(message)


@dataclass(frozen=True, slots=True)
class SourceSpansV1:
    read: tuple[int, int]
    subsets: tuple[tuple[int, int], tuple[int, int]]
    vectors: tuple[tuple[int, int], tuple[int, int]]
    call: tuple[int, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "call": list(self.call),
            "read": list(self.read),
            "subsets": [list(item) for item in self.subsets],
            "vectors": [list(item) for item in self.vectors],
        }


@dataclass(frozen=True, slots=True)
class SourceFlowFactV1:
    source_sha256: str
    h5ad_read_literal: str
    obs_column: str
    selection_literals: tuple[str, str]
    subset_bindings: tuple[str, str]
    vector_bindings: tuple[str, str]
    procedure: str
    call_argument_order: tuple[str, str]
    spans: SourceSpansV1

    def to_dict(self) -> dict[str, object]:
        return {
            "call_argument_order": list(self.call_argument_order),
            "h5ad_read_literal": self.h5ad_read_literal,
            "obs_column": self.obs_column,
            "procedure": self.procedure,
            "selection_literals": list(self.selection_literals),
            "source_sha256": self.source_sha256,
            "spans": self.spans.to_dict(),
            "subset_bindings": list(self.subset_bindings),
            "vector_bindings": list(self.vector_bindings),
        }


def _single_name_target(node: ast.Assign) -> str:
    if len(node.targets) != 1 or type(node.targets[0]) is not ast.Name:
        _fail("tracked assignment target is not one direct name")
    return node.targets[0].id


def _node_span(raw: bytes, node: ast.stmt) -> tuple[int, int]:
    if not all(
        hasattr(node, name) for name in ("lineno", "col_offset", "end_lineno", "end_col_offset")
    ):
        _fail("tracked node has no complete source span")
    lines = raw.splitlines(keepends=True)
    start_line = node.lineno
    end_line = node.end_lineno
    if end_line is None:
        _fail("tracked node has no end line")
    if not 1 <= start_line <= end_line <= len(lines):
        _fail("tracked source span is outside the source")
    end_col_offset = node.end_col_offset
    if end_col_offset is None:
        _fail("tracked node has no end column")
    start = sum(len(line) for line in lines[: start_line - 1]) + node.col_offset
    end = sum(len(line) for line in lines[: end_line - 1]) + end_col_offset
    if not 0 <= start < end <= len(raw):
        _fail("tracked source span is invalid")
    return start, end


def _expect_call(
    value: ast.expr,
    *,
    function: tuple[str, ...],
    arguments: tuple[str, ...] | None = None,
) -> ast.Call:
    if type(value) is not ast.Call or value.keywords:
        _fail("tracked call shape differs")
    call = value
    components: list[str] = []
    cursor: ast.expr = call.func
    while type(cursor) is ast.Attribute:
        attribute = cursor
        components.append(attribute.attr)
        cursor = attribute.value
    if type(cursor) is not ast.Name:
        _fail("tracked call is not direct")
    components.append(cursor.id)
    if tuple(reversed(components)) != function:
        _fail("tracked callable differs")
    if (
        arguments is not None
        and tuple(argument.id if type(argument) is ast.Name else "" for argument in call.args)
        != arguments
    ):
        _fail("tracked call arguments differ")
    return call


def _subset_parts(value: ast.expr) -> tuple[str, str, str]:
    if type(value) is not ast.Subscript:
        _fail("tracked subset is not one direct subscript")
    outer = value
    if type(outer.value) is not ast.Name or outer.value.id != "adata":
        _fail("tracked subset base differs")
    comparison = outer.slice
    if (
        type(comparison) is not ast.Compare
        or len(comparison.ops) != 1
        or type(comparison.ops[0]) is not ast.Eq
        or len(comparison.comparators) != 1
        or type(comparison.comparators[0]) is not ast.Constant
        or type(comparison.comparators[0].value) is not str
    ):
        _fail("tracked subset predicate differs")
    left = comparison.left
    if (
        type(left) is not ast.Subscript
        or type(left.value) is not ast.Attribute
        or left.value.attr != "obs"
        or type(left.value.value) is not ast.Name
        or left.value.value.id != "adata"
        or type(left.slice) is not ast.Constant
        or type(left.slice.value) is not str
    ):
        _fail("tracked observation-column selection differs")
    return (
        outer.value.id,
        left.slice.value,
        comparison.comparators[0].value,
    )


def _vector_subset_name(value: ast.expr) -> str:
    if type(value) is not ast.Call or value.args or value.keywords:
        _fail("tracked vector flatten call differs")
    flatten_call = value
    if type(flatten_call.func) is not ast.Attribute or flatten_call.func.attr != "flatten":
        _fail("tracked vector flatten callable differs")
    toarray = flatten_call.func.value
    if type(toarray) is not ast.Call or toarray.args or toarray.keywords:
        _fail("tracked vector conversion differs")
    toarray_call = toarray
    if type(toarray_call.func) is not ast.Attribute or toarray_call.func.attr != "toarray":
        _fail("tracked vector conversion callable differs")
    x_value = toarray_call.func.value
    if type(x_value) is not ast.Attribute or x_value.attr != "X":
        _fail("tracked vector matrix access differs")
    subset = x_value.value
    if type(subset) is not ast.Subscript or type(subset.value) is not ast.Name:
        _fail("tracked vector subset access differs")
    slice_value = subset.slice
    if (
        type(slice_value) is not ast.Tuple
        or len(slice_value.elts) != 2
        or type(slice_value.elts[0]) is not ast.Slice
        or any(
            getattr(slice_value.elts[0], name) is not None for name in ("lower", "upper", "step")
        )
        or type(slice_value.elts[1]) is not ast.Name
        or slice_value.elts[1].id != "gene"
    ):
        _fail("tracked vector slice differs")
    return subset.value.id


def verify_world1_source_v1(raw: bytes) -> SourceFlowFactV1:
    """Parse, compile, recursively close, and reconstruct the sole source fact."""

    if type(raw) is not bytes or len(raw) != _SOURCE_SIZE or sha256(raw) != _SOURCE_DIGEST:
        _fail("source byte identity differs")
    try:
        text = raw.decode("utf-8", "strict")
        tree = ast.parse(text, filename="<slice-c-world1>", mode="exec", type_comments=True)
        compile(tree, "<slice-c-world1>", "exec", dont_inherit=True, optimize=0)
    except (UnicodeDecodeError, SyntaxError, ValueError, TypeError) as error:
        raise SourceVerificationError("source parse or compile failed") from error
    for node in ast.walk(tree):
        if type(node) not in _ALLOWED_NODE_TYPES:
            _fail("source AST contains an unrecognized node")
    recursive_dump = ast.dump(tree, annotate_fields=True, include_attributes=False)
    if hashlib.sha256(recursive_dump.encode("utf-8")).hexdigest() != _AST_DUMP_SHA256:
        _fail("source AST is outside the exact closed flow")
    if len(tree.body) != 12 or [type(item) for item in tree.body] != [
        ast.Import,
        ast.ImportFrom,
        ast.Assign,
        ast.Assign,
        ast.Assign,
        ast.Assign,
        ast.Assign,
        ast.Assign,
        ast.Assign,
        ast.Expr,
        ast.Expr,
        ast.Expr,
    ]:
        _fail("source statement inventory differs")
    scanpy_import = cast(ast.Import, tree.body[0])
    scipy_import = cast(ast.ImportFrom, tree.body[1])
    if (
        len(scanpy_import.names) != 1
        or scanpy_import.names[0].name != "scanpy"
        or scanpy_import.names[0].asname != "sc"
        or scipy_import.module != "scipy.stats"
        or scipy_import.level != 0
        or len(scipy_import.names) != 1
        or scipy_import.names[0].name != "ttest_ind"
        or scipy_import.names[0].asname is not None
    ):
        _fail("source import authority differs")

    assignments = [cast(ast.Assign, item) for item in tree.body[2:9]]
    read, subset_one, subset_two, gene, vector_one, vector_two, call_assignment = assignments
    if _single_name_target(read) != "adata":
        _fail("source read binding differs")
    read_call = _expect_call(read.value, function=("sc", "read_h5ad"))
    if (
        len(read_call.args) != 1
        or type(read_call.args[0]) is not ast.Constant
        or read_call.args[0].value != "sc_reads.h5ad"
    ):
        _fail("source read literal differs")
    subset_bindings = (_single_name_target(subset_one), _single_name_target(subset_two))
    subset_parts = (_subset_parts(subset_one.value), _subset_parts(subset_two.value))
    if subset_bindings != ("cells_animal1", "cells_animal2"):
        _fail("source subset bindings differ")
    obs_columns = (subset_parts[0][1], subset_parts[1][1])
    selections = (subset_parts[0][2], subset_parts[1][2])
    if obs_columns != ("animal_id", "animal_id") or selections != ("Animal_1", "Animal_2"):
        _fail("source subset literals differ")
    if _single_name_target(gene) != "gene":
        _fail("source feature binding differs")
    vector_bindings = (_single_name_target(vector_one), _single_name_target(vector_two))
    if (
        vector_bindings != ("expr_1", "expr_2")
        or (
            _vector_subset_name(vector_one.value),
            _vector_subset_name(vector_two.value),
        )
        != subset_bindings
    ):
        _fail("source vector flow differs")
    if (
        len(call_assignment.targets) != 1
        or type(call_assignment.targets[0]) is not ast.Tuple
        or tuple(
            item.id if type(item) is ast.Name else "" for item in call_assignment.targets[0].elts
        )
        != ("stat", "inflated_pvalue")
    ):
        _fail("source procedure result binding differs")
    _expect_call(
        call_assignment.value,
        function=("ttest_ind",),
        arguments=vector_bindings,
    )
    spans = SourceSpansV1(
        read=_node_span(raw, read),
        subsets=(_node_span(raw, subset_one), _node_span(raw, subset_two)),
        vectors=(_node_span(raw, vector_one), _node_span(raw, vector_two)),
        call=_node_span(raw, call_assignment),
    )
    if spans != SourceSpansV1(
        read=(347, 384),
        subsets=((431, 490), (491, 550)),
        vectors=((703, 756), (757, 810)),
        call=(812, 861),
    ):
        _fail("source byte spans differ")
    return SourceFlowFactV1(
        source_sha256=_SOURCE_DIGEST,
        h5ad_read_literal="sc_reads.h5ad",
        obs_column="animal_id",
        selection_literals=selections,
        subset_bindings=subset_bindings,
        vector_bindings=vector_bindings,
        procedure="scipy.stats.ttest_ind",
        call_argument_order=vector_bindings,
        spans=spans,
    )


__all__ = [
    "SourceFlowFactV1",
    "SourceSpansV1",
    "SourceVerificationError",
    "verify_world1_source_v1",
]
