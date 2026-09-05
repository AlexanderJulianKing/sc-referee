"""Closed syntactic grammars for the multiple-testing 3.5 recall deltas.

Every production in this module is a syntactic fact about the AST.  None of them reads
display text, identifier spelling, comments, reports, or Markdown for meaning.  Where a
production reads a string constant it measures the constant's structure only: nonempty, no
NUL, at most 256 UTF-8 bytes.

Five productions are specified.  Three groups are installed by the 3.5 lane:

* **D1** widens the *arm* test at three terminal-rendering positions to admit
  ``"<literal>".format(ARGVAL*)`` and an f-string whose every interpolated value is an
  ``ARGVAL``.  ``ARGVAL`` is a scalar literal or a name bound exactly once at module level to
  a scalar literal.
* **D4a** admits a numeric group-mask comparator that names exactly one of the two CSV group
  tokens under an unambiguous decimal normalisation, consulted only at the two engine
  group-mask comparator positions.
* **D4b** exempts a presentation loop's own iterator control from the hierarchy guard.  Only
  the closed iterator grammar lives here; the four engine-bound proofs live with the engine,
  which is the only place that can see registered sinks, test APIs, and loop scope.
* **D5** admits ``len(COLLECTION)`` over the fully reconstructed contract-order p-record
  family when the value reaches only a display sink.  Only the display-ancestor tables live
  here; the proof itself needs the engine.

Two productions are **specified and deliberately not installed**: `membership_sets` (D2) and
`csv_reader_paths` (D3).  Design section 8.6 requires them to be present and executable so
their refusal lists are proved against the production predicates, and requires that nothing
on the analysis path calls them.  `tests/test_code_csv_multiple_testing_recall_deltas_v3_5.py`
asserts both halves of that.  They may not be installed until the third wall behind D3 is
closed (`helper-free-name-unbound` on a comprehension target inside a helper `return`),
because until then neither production can change a public byte.

Nothing in this module classifies a family, resolves a correction, or writes a reason.  The
unchanged shipped machinery classifies every source.
"""

from __future__ import annotations

import ast
import csv
import io
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from sc_referee.core.ids import sha256_digest

CODE_CSV_MULTIPLE_TESTING_RECALL_DELTAS_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)

#: The frozen display bound every admitted display constant must satisfy.
MAX_DISPLAY_BYTES = 256

#: An ancestor of an admitted `len()` may only be one of these on the way to its sink.
DISPLAY_ANCESTORS: tuple[type[ast.AST], ...] = (ast.JoinedStr, ast.FormattedValue, ast.Expr)

#: Callees an admitted `len()` may appear inside as a display payload.
DISPLAY_CALLEES = frozenset({"print", "format", "str"})

#: Execution-prevention and scope-introducing nodes.  None of them may appear under a loop
#: admitted by D4b, because a loop that can suppress or defer work is not a presentation loop.
PREVENTION_NODES: tuple[type[ast.AST], ...] = (
    ast.Return,
    ast.Break,
    ast.Continue,
    ast.Raise,
    ast.While,
    ast.Try,
    ast.Match,
    ast.Assert,
    ast.With,
    ast.AsyncWith,
    ast.AsyncFor,
    ast.Global,
    ast.Nonlocal,
    ast.Lambda,
    ast.Yield,
    ast.YieldFrom,
    ast.Await,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
)


def span_of(node: ast.AST) -> tuple[int, int, int, int]:
    """The four-tuple source span of a node, or -1s where the node carries no position."""

    return (
        getattr(node, "lineno", -1),
        getattr(node, "col_offset", -1),
        getattr(node, "end_lineno", -1),
        getattr(node, "end_col_offset", -1),
    )


# ======================================================================================
# Shared closed tables read from the module AST
# ======================================================================================


def _module_bindings(tree: ast.Module) -> Iterator[tuple[str, ast.expr]]:
    """Every module-level `NAME = value` and `NAME: T = value` binding, in source order."""

    for node in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets, value = list(node.targets), node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        if len(targets) == 1 and isinstance(targets[0], ast.Name) and value is not None:
            yield targets[0].id, value


def _signed_literal(node: ast.expr) -> object | None:
    """A scalar literal under any number of unary signs, or None.  `bool` is never scalar."""

    sign = 1
    cursor = node
    while isinstance(cursor, ast.UnaryOp) and isinstance(cursor.op, (ast.UAdd, ast.USub)):
        if isinstance(cursor.op, ast.USub):
            sign = -sign
        cursor = cursor.operand
    if not isinstance(cursor, ast.Constant) or isinstance(cursor.value, bool):
        return None
    if isinstance(cursor.value, str):
        return cursor.value if sign == 1 else None
    if isinstance(cursor.value, (int, float)):
        return sign * cursor.value
    return None


def _single_store(tree: ast.Module, name: str) -> bool:
    """The name has exactly one Store or Del in the whole module and no `AugAssign`."""

    stores = sum(
        isinstance(item, ast.Name)
        and isinstance(item.ctx, (ast.Store, ast.Del))
        and item.id == name
        for item in ast.walk(tree)
    )
    augmented = any(
        isinstance(item, ast.AugAssign)
        and isinstance(item.target, ast.Name)
        and item.target.id == name
        for item in ast.walk(tree)
    )
    return stores == 1 and not augmented


def module_constant_names(tree: ast.Module) -> frozenset[str]:
    """CONSTANTS: names bound exactly once, at module level, to a scalar literal."""

    seen: dict[str, int] = {}
    literal: dict[str, bool] = {}
    for name, value in _module_bindings(tree):
        seen[name] = seen.get(name, 0) + 1
        literal[name] = _signed_literal(value) is not None
    return frozenset(
        name
        for name, count in seen.items()
        if count == 1 and literal[name] and _single_store(tree, name)
    )


def module_string_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level names bound once to a string literal, used to resolve column names."""

    result: dict[str, str] = {}
    for name, value in _module_bindings(tree):
        resolved = _signed_literal(value)
        if isinstance(resolved, str) and _single_store(tree, name):
            result[name] = resolved
    return result


def module_numeric_constants(tree: ast.Module) -> dict[str, float | int]:
    """Module-level names bound once to a signed numeric literal.  `bool` never qualifies."""

    result: dict[str, float | int] = {}
    for name, value in _module_bindings(tree):
        resolved = _signed_literal(value)
        if (
            isinstance(resolved, (int, float))
            and not isinstance(resolved, bool)
            and _single_store(tree, name)
        ):
            result[name] = resolved
    return result


# ======================================================================================
# D1: formatted display arms (installed)
# ======================================================================================


def bare_display(node: ast.expr) -> bool:
    """The frozen display-string predicate, restated so this module can compose it.

    It is byte-identical in behaviour to `_mt_v21_display_string` and to the 3.3
    terminal-presentation `_display_string`; those two shared predicates are **not** widened,
    because they have twenty other call sites.
    """

    return bool(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value
        and "\x00" not in node.value
        and len(node.value.encode("utf-8")) <= MAX_DISPLAY_BYTES
    )


def _argval(node: ast.expr, constants: frozenset[str]) -> bool:
    """ARGVAL := scalar literal | signed scalar literal | Name in CONSTANTS.

    Everything else refuses: a `Call`, an `Attribute`, a `Subscript`, a `BinOp`, a `Compare`,
    a comprehension, a `bool`, `bytes`, `Ellipsis`, `None`, and any name that is not a
    module-level constant.
    """

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _argval(node.operand, constants)
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (str, int, float)) and not isinstance(node.value, bool)
    return isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in constants


def _constant_format_spec(node: ast.expr | None) -> bool:
    """A `FormattedValue.format_spec` must be absent or wholly constant string text."""

    if node is None:
        return True
    if isinstance(node, ast.JoinedStr):
        return all(
            isinstance(part, ast.Constant)
            and isinstance(part.value, str)
            and "\x00" not in part.value
            for part in node.values
        )
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def widened_display_arm(node: ast.expr, constants: frozenset[str]) -> bool:
    """The two new arm forms.  A bare constant is the frozen predicate's business.

    ```text
    ARM := Call(func=Attribute(value=Constant(str), attr="format"), args=ARGVAL+, keywords=[])
         | JoinedStr(values=(Constant(str) | FormattedValue)+)
    ```

    The `%` form, keyword arguments, starred arguments, an attribute call other than
    `str.format`, and a `.format` on anything but a bare display constant all refuse.
    """

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "format"
        and bare_display(node.func.value)
        and not node.keywords
        and node.args
        and all(_argval(argument, constants) for argument in node.args)
    ):
        return True
    if isinstance(node, ast.JoinedStr):
        if not all(isinstance(part, (ast.Constant, ast.FormattedValue)) for part in node.values):
            return False
        if any(
            isinstance(part, ast.Constant) and not isinstance(part.value, str)
            for part in node.values
        ):
            return False
        text = "".join(
            part.value
            for part in node.values
            if isinstance(part, ast.Constant) and isinstance(part.value, str)
        )
        if not text or "\x00" in text or len(text.encode("utf-8")) > MAX_DISPLAY_BYTES:
            return False
        formatted = [part for part in node.values if isinstance(part, ast.FormattedValue)]
        if not formatted:
            return False
        return all(
            _argval(part.value, constants) and _constant_format_spec(part.format_spec)
            for part in formatted
        )
    return False


# ======================================================================================
# D2: set literals in the AP selector, membership only.  SPECIFIED, NOT INSTALLED.
# ======================================================================================


def membership_sets(tree: ast.Module) -> dict[str, tuple[str, ...]]:
    """SETNAME = { STR (, STR)* }, every load of which is an `in` / `not in` right operand.

    **Specified and not installed.**  Nothing on the analysis path calls this function.  It
    exists so the section 1.2 refusal list is proved against a production predicate rather
    than against the prototype, and so a later delta can pick the production up with the
    equivalence already proved.  The table is never merged into `sequences`, so a set can
    never become a row-table iterator, an `enumerate` argument, a factor source, or an
    ordered position source; condition 5 below is what makes that structural.
    """

    candidates: dict[str, tuple[str, ...]] = {}
    for name, value in _module_bindings(tree):
        if not isinstance(value, ast.Set) or not value.elts:
            continue
        elements: list[str] = []
        refused = False
        for item in value.elts:
            if not (
                isinstance(item, ast.Constant)
                and isinstance(item.value, str)
                and not isinstance(item.value, bool)
            ):
                refused = True
                break
            elements.append(item.value)
        if refused or not elements or len(set(elements)) != len(elements):
            continue
        candidates[name] = tuple(elements)
    if not candidates:
        return {}
    membership_operands = {
        id(node.comparators[0])
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], (ast.In, ast.NotIn))
        and len(node.comparators) == 1
        and isinstance(node.comparators[0], ast.Name)
    }
    result: dict[str, tuple[str, ...]] = {}
    for name, admitted in candidates.items():
        if not _single_store(tree, name):
            continue
        loads = [
            item
            for item in ast.walk(tree)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id == name
        ]
        if not loads or any(id(load) not in membership_operands for load in loads):
            continue
        result[name] = admitted
    return result


# ======================================================================================
# D3: standard-library csv reader lineage.  SPECIFIED, NOT INSTALLED.
# ======================================================================================


def csv_reader_paths(tree: ast.Module) -> list[ast.expr]:
    """READER := `with open(PATH, <text kwargs>) as H: return list(csv.DictReader(H))`.

    **Specified and not installed.**  Nothing on the analysis path calls this function.  The
    executed measurement in design section 2.4 is why: a deliberately over-generous reader
    stand-in, strictly looser than this grammar, still lands E18 P6 on a third wall
    (`helper-free-name-unbound`), which sits before the AP selector where D2 lives.  Under the
    ordering rule an abstaining re-analysis returns the frozen 3.4 reason byte-for-byte, so
    installing D2 and D3 would change no public byte anywhere in the evidence.
    """

    result: list[ast.expr] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.With) or len(node.items) != 1 or len(node.body) != 1:
            continue
        item = node.items[0]
        call = item.context_expr
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "open"
            and len(call.args) == 1
            and isinstance(item.optional_vars, ast.Name)
        ):
            continue
        keywords = {keyword.arg: keyword.value for keyword in call.keywords}
        if set(keywords) - {"newline", "encoding", "mode"}:
            continue
        if any(
            not isinstance(value, ast.Constant) or not isinstance(value.value, str)
            for value in keywords.values()
        ):
            continue
        mode = keywords.get("mode")
        if isinstance(mode, ast.Constant) and "b" in str(mode.value):
            continue
        statement = node.body[0]
        if not isinstance(statement, ast.Return) or statement.value is None:
            continue
        value = statement.value
        if not (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "list"
            and len(value.args) == 1
            and not value.keywords
        ):
            continue
        inner = value.args[0]
        if not (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr in {"DictReader", "reader"}
            and isinstance(inner.func.value, ast.Name)
            and inner.func.value.id == "csv"
            and len(inner.args) == 1
            and isinstance(inner.args[0], ast.Name)
            and inner.args[0].id == item.optional_vars.id
            and not inner.keywords
        ):
            continue
        result.append(call.args[0])
    return result


# ======================================================================================
# D4a: numeric group-mask comparator tokens (installed)
# ======================================================================================


def normalised_decimal(text: str) -> str | None:
    """`repr`-normalised decimal text of a finite decimal token, or None.

    Surrounding whitespace, a thousands separator, an underscore, an inner space, a
    non-numeric token, and a non-finite value all refuse.
    """

    if text != text.strip() or not text:
        return None
    if any(character in text for character in ",_ "):
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if value != value or value in {float("inf"), float("-inf")}:
        return None
    return repr(value)


def group_column_is_decimal(csv_content: bytes, group_column: str) -> bool:
    """Every non-header cell of the group column parses as a finite decimal."""

    try:
        rows = list(
            csv.reader(
                io.StringIO(csv_content.decode("utf-8"), newline=""), dialect="excel", strict=True
            )
        )
    except (UnicodeError, csv.Error):
        return False
    if not rows or group_column not in rows[0]:
        return False
    index = rows[0].index(group_column)
    return bool(rows[1:]) and all(
        len(row) > index and normalised_decimal(row[index]) is not None for row in rows[1:]
    )


def group_mask_numeric_positions(
    tree: ast.Module,
    *,
    group_column: str,
    group_values: tuple[str, ...],
    column_is_decimal: bool,
) -> dict[tuple[int, int, int, int], str]:
    """Comparator spans the D4a grammar admits, each keyed to its one CSV group token.

    The admitted value is the CSV token itself, so everything downstream sees exactly the
    string the frozen path would have seen for a string-spelled group constant.  `!=` and
    every operator other than `==` refuse; so does a comparator that is a call, an attribute,
    a subscript, or arithmetic; so does a `bool`, a non-finite float, a token column that is
    not wholly decimal, two group tokens that collapse to the same normalised text, a literal
    matching neither token or both, and a mask on a column that is not the group column.
    """

    if not column_is_decimal or len(group_values) != 2:
        return {}
    normalised = {token: normalised_decimal(token) for token in group_values}
    if any(value is None for value in normalised.values()):
        return {}
    if len(set(normalised.values())) != len(group_values):
        return {}
    strings = module_string_constants(tree)
    numbers = module_numeric_constants(tree)
    result: dict[tuple[int, int, int, int], str] = {}

    def column_of(node: ast.expr) -> str | None:
        if not isinstance(node, ast.Subscript):
            return None
        key = node.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            return key.value
        if isinstance(key, ast.Name):
            return strings.get(key.id)
        return None

    def token_of(node: ast.expr) -> str | None:
        sign = 1
        cursor = node
        while isinstance(cursor, ast.UnaryOp) and isinstance(cursor.op, (ast.UAdd, ast.USub)):
            if isinstance(cursor.op, ast.USub):
                sign = -sign
            cursor = cursor.operand
        raw: Any = None
        if (
            isinstance(cursor, ast.Constant)
            and isinstance(cursor.value, (int, float))
            and not isinstance(cursor.value, bool)
        ):
            raw = sign * cursor.value
        elif isinstance(cursor, ast.Name) and cursor.id in numbers:
            raw = sign * numbers[cursor.id]
        if raw is None or isinstance(raw, bool):
            return None
        if isinstance(raw, float) and (raw != raw or raw in {float("inf"), float("-inf")}):
            return None
        text = normalised_decimal(repr(raw))
        if text is None:
            return None
        hits = [token for token, value in normalised.items() if value == text]
        return hits[0] if len(hits) == 1 else None

    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Compare)
            and len(node.ops) == 1
            and isinstance(node.ops[0], ast.Eq)
            and len(node.comparators) == 1
        ):
            continue
        for column_node, value_node in (
            (node.left, node.comparators[0]),
            (node.comparators[0], node.left),
        ):
            if column_of(column_node) != group_column:
                continue
            token = token_of(value_node)
            if token is None:
                continue
            span = span_of(value_node)
            if -1 in span:
                continue
            result[span] = token
    return result


# ======================================================================================
# D4b: the iterator half of the presentation-loop terminal proof (installed)
# ======================================================================================


def admitted_loop_iterator(shadowed_builtins: frozenset[str], node: ast.expr) -> bool:
    """ITER := NAME | enumerate(NAME) | enumerate(NAME, start=<int literal>).

    `sorted(...)`, `reversed(...)`, `.items()`, `enumerate(list(...))`, `enumerate(zip(...))`,
    a non-literal `start`, and a positional second argument all refuse, as does `enumerate`
    when the name is shadowed in the analysed module.
    """

    if isinstance(node, ast.Name):
        return True
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "enumerate"
        and node.func.id not in shadowed_builtins
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
    ):
        return False
    if not node.keywords:
        return True
    return (
        len(node.keywords) == 1
        and node.keywords[0].arg == "start"
        and isinstance(node.keywords[0].value, ast.Constant)
        and isinstance(node.keywords[0].value.value, int)
        and not isinstance(node.keywords[0].value.value, bool)
    )


__all__ = [
    "CODE_CSV_MULTIPLE_TESTING_RECALL_DELTAS_IMPLEMENTATION_DIGEST",
    "DISPLAY_ANCESTORS",
    "DISPLAY_CALLEES",
    "MAX_DISPLAY_BYTES",
    "PREVENTION_NODES",
    "admitted_loop_iterator",
    "bare_display",
    "csv_reader_paths",
    "group_column_is_decimal",
    "group_mask_numeric_positions",
    "membership_sets",
    "module_constant_names",
    "module_numeric_constants",
    "module_string_constants",
    "normalised_decimal",
    "span_of",
    "widened_display_arm",
]
