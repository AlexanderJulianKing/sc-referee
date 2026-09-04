"""Strict MT 3.5 recall-delta shadow over the shipped 3.4 lane.

Development evidence only; this module is not imported by production code.

The shadow implements four closed productions and installs three of them:

* **D1, installed.**  The three terminal-rendering *arm* positions admit two further display
  forms besides a bare string constant: `"<literal>".format(ARGVAL*)` and an f-string whose
  every interpolated value is an `ARGVAL`.  `ARGVAL` is a scalar literal or a name bound
  exactly once at module level to a scalar literal, and an admitted arm must additionally
  carry no p-origin and no decision position.
* **D2, specified and NOT installed.**  A module-level set literal of unique string
  constants, every load of which is the right operand of an `in` / `not in` comparison, is
  readable by the AP selector's per-row truth evaluation.  It is never readable as an
  ordered sequence.
* **D3, specified and NOT installed.**  `list(csv.DictReader(HANDLE))` /
  `list(csv.reader(HANDLE))` inside `with open(PATH, <text kwargs>) as HANDLE:` is an
  authorized-reader lineage.
* **D4, installed as a pair.**  D4a admits a numeric group-mask comparator that names
  exactly one CSV group token; D4b exempts a presentation loop's own iterator control from
  the hierarchy guard when no registered test, recognised correction, or `.pvalue` read
  occurs at or after the loop, the loop carries no execution-prevention edge, nothing it
  binds escapes it, and it renders through a registered sink.

The ordering rule is inherited from 3.4 and is load-bearing: a row the shipped 3.4 lane
classifies is returned untouched and no 3.5 production is attempted; a row it abstains on is
re-analysed with the installed productions, and that result is adopted only when it is itself
a classification.  Otherwise the frozen 3.4 reason is returned byte-for-byte.

Two prototype techniques are development evidence only and are forbidden in production:

1. the productions are installed by replacing named module-level functions and two bound
   methods for the duration of one re-analysis.  Production must widen those recognisers in
   versioned copies.
2. D4a is installed as a *position-keyed* override of `_Resolver.string`, restricted to the
   comparator positions the D4a grammar admits.  Production must add a numeric-token helper
   consulted at the two group-mask comparator sites in `_bare_group_mask_frame` and
   `_mask_rows`, never by widening `_Resolver.string`.
"""

from __future__ import annotations

import ast
import contextlib
import csv
import io
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterator

from sc_referee.scientific_checks import (
    code_csv_multiple_testing_correction_model_v3_4 as cm34,
)
from sc_referee.scientific_checks import (
    code_csv_multiple_testing_dataflow_v3_3 as df33,
)
from sc_referee.scientific_checks import (
    code_csv_multiple_testing_dataflow_v3_4 as df34,
)
from sc_referee.scientific_checks import (
    code_csv_multiple_testing_terminal_presentation_v3_3 as tp33,
)

ADMISSION_KINDS = (
    "d1-format-arm",
    "d2-set-selector",
    "d3-csv-reader",
    "d4a-numeric-group",
    "d4b-loop-terminal",
    "d5-cardinality-read",
)

#: Which productions this shadow installs.  D2 and D3 are specified and not installed.
INSTALLED = (
    "d1-format-arm",
    "d4a-numeric-group",
    "d4b-loop-terminal",
    "d5-cardinality-read",
)

CENSUS: Counter[str] = Counter({kind: 0 for kind in ADMISSION_KINDS})

_MAX_DISPLAY_BYTES = 256


def reset_census() -> None:
    CENSUS.clear()
    CENSUS.update({kind: 0 for kind in ADMISSION_KINDS})


def census_snapshot() -> dict[str, int]:
    return {kind: int(CENSUS[kind]) for kind in ADMISSION_KINDS}


# ======================================================================================
# Shared closed tables read from the module AST
# ======================================================================================


def _module_bindings(tree: ast.Module) -> Iterator[tuple[str, ast.expr]]:
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
    result: dict[str, str] = {}
    for name, value in _module_bindings(tree):
        resolved = _signed_literal(value)
        if isinstance(resolved, str) and _single_store(tree, name):
            result[name] = resolved
    return result


def module_numeric_constants(tree: ast.Module) -> dict[str, float | int]:
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
# D1: formatted display arms
# ======================================================================================


def bare_display(node: ast.expr) -> bool:
    """The frozen display-string predicate, reproduced for the prototype's own use."""

    return bool(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value
        and "\x00" not in node.value
        and len(node.value.encode("utf-8")) <= _MAX_DISPLAY_BYTES
    )


def _argval(node: ast.expr, constants: frozenset[str]) -> bool:
    """ARGVAL := scalar literal | Name in CONSTANTS.  Everything else refuses."""

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _argval(node.operand, constants)
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (str, int, float)) and not isinstance(node.value, bool)
    return isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in constants


def _constant_format_spec(node: ast.expr | None) -> bool:
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
    """The two new arm forms.  A bare constant is the frozen predicate's business."""

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
        text = "".join(part.value for part in node.values if isinstance(part, ast.Constant))
        if not text or "\x00" in text or len(text.encode("utf-8")) > _MAX_DISPLAY_BYTES:
            return False
        formatted = [part for part in node.values if isinstance(part, ast.FormattedValue)]
        if not formatted:
            return False
        return all(
            _argval(part.value, constants) and _constant_format_spec(part.format_spec)
            for part in formatted
        )
    return False


class _D1:
    enabled = False
    constants: frozenset[str] = frozenset()
    fired: set[tuple[int, int, int, int]] = set()


def _span(node: ast.AST) -> tuple[int, int, int, int]:
    return (
        getattr(node, "lineno", -1),
        getattr(node, "col_offset", -1),
        getattr(node, "end_lineno", -1),
        getattr(node, "end_col_offset", -1),
    )


def _record(kind: str, node: ast.AST) -> None:
    span = _span(node)
    key = (kind, span)
    if key in _RECORDED:
        return
    _RECORDED.add(key)
    CENSUS[kind] += 1


_RECORDED: set[tuple[str, tuple[int, int, int, int]]] = set()


def _engine_arm(engine: Any, node: ast.expr) -> bool:
    if bare_display(node):
        return True
    if not _D1.enabled or not widened_display_arm(node, _D1.constants):
        return False
    if engine._p_origins(node) or engine._decision_positions_in_expr(node, set(), 0):
        return False
    _record("d1-format-arm", node)
    return True


_FROZEN_IFEXP = df33._MtEngine._terminal_rendering_ifexp
_FROZEN_IF = df33._MtEngine._mt_v21_terminal_rendering_if
_FROZEN_DISPLAY = df33._mt_v21_display_string
_FROZEN_TP_DISPLAY = tp33._display_string
_FROZEN_TP_IFEXP = tp33._terminal_ifexp_positions


def _v35_terminal_rendering_ifexp(self: Any, node: ast.IfExp) -> bool:
    """Copy of `_terminal_rendering_ifexp` whose only change is the two arm tests."""

    if not (
        _engine_arm(self, node.body)
        and _engine_arm(self, node.orelse)
        and (
            self._decision_positions_in_expr(node.test, set(), 0)
            or len(self._p_origins(node.test)) == 1
        )
    ):
        return False
    if self._mt23_decision_mapped(node):
        return True
    combined = (*self.original_scope, *self.scope)
    parents = {
        child: parent
        for parent in df33._walk_statements(combined)
        for child in ast.iter_child_nodes(parent)
    }
    cursor: ast.AST = node
    if isinstance((parent := parents.get(cursor)), (ast.Assign, ast.AnnAssign)):
        target = parent.targets[0] if isinstance(parent, ast.Assign) else parent.target
        if isinstance(target, ast.Name):
            loads: list[ast.AST] = [
                item
                for item in df33._walk_statements(combined)
                if isinstance(item, ast.Name)
                and isinstance(item.ctx, ast.Load)
                and item.id == target.id
            ]
        elif (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name)
            and (member := df33._mt_literal_member(target.slice)) is not None
        ):
            loads = [
                item
                for item in df33._walk_statements(combined)
                if isinstance(item, ast.Subscript)
                and isinstance(item.ctx, ast.Load)
                and isinstance(item.value, ast.Name)
                and item.value.id == target.value.id
                and df33._mt_literal_member(item.slice) == member
            ]
        else:
            return False
        return bool(
            loads and all(self._mt_v2_rendering_load_reaches_sink(item, parents) for item in loads)
        )
    return self._mt_v2_rendering_load_reaches_sink(cursor, parents)


def _v35_terminal_rendering_if(self: Any, node: ast.If) -> Any:
    """Sibling 1: only the two *assignment* arms of the `If` lane are widened.

    The matched print-payload arm test in the same frozen function is deliberately left
    unchanged, so a two-branch print of formatted payloads keeps refusing.
    """

    if not (
        _D1.enabled
        and len(node.body) == 1
        and len(node.orelse) == 1
        and isinstance(body := node.body[0], ast.Assign)
        and isinstance(orelse := node.orelse[0], ast.Assign)
    ):
        return _FROZEN_IF(self, node)
    widened: list[ast.expr] = []
    for statement in (body, orelse):
        value = statement.value
        if bare_display(value):
            continue
        if not widened_display_arm(value, _D1.constants):
            return _FROZEN_IF(self, node)
        if self._p_origins(value) or self._decision_positions_in_expr(value, set(), 0):
            return _FROZEN_IF(self, node)
        widened.append(value)
    if not widened:
        return _FROZEN_IF(self, node)
    identities = {id(item) for item in widened}

    def display(candidate: ast.expr) -> bool:
        return id(candidate) in identities or _FROZEN_DISPLAY(candidate)

    df33._mt_v21_display_string = display
    try:
        result = _FROZEN_IF(self, node)
    finally:
        df33._mt_v21_display_string = _FROZEN_DISPLAY
    if result is not None:
        for item in widened:
            _record("d1-format-arm", item)
    return result


def _v35_tp_terminal_ifexp_positions(tree: ast.Module, resolver: Any) -> Any:
    """Sibling 2: the 3.3 terminal-presentation proof's own IfExp arm lane."""

    if not _D1.enabled:
        return _FROZEN_TP_IFEXP(tree, resolver)
    constants = module_constant_names(tree)
    fired: list[ast.expr] = []

    def display(node: ast.expr) -> bool:
        if _FROZEN_TP_DISPLAY(node):
            return True
        if widened_display_arm(node, constants):
            fired.append(node)
            return True
        return False

    tp33._display_string = display
    try:
        result = _FROZEN_TP_IFEXP(tree, resolver)
    finally:
        tp33._display_string = _FROZEN_TP_DISPLAY
    if fired and result:
        for item in fired:
            _record("d1-format-arm", item)
    return result


# ======================================================================================
# D2: set literals in the AP selector, membership only.  Specified, NOT installed.
# ======================================================================================

_FROZEN_STATIC_BOOL = cm34._static_bool


def membership_sets(tree: ast.Module) -> dict[str, tuple[str, ...]]:
    """SETNAME = { STR (, STR)* }, every load of which is an `in` / `not in` right operand."""

    candidates: dict[str, tuple[str, ...]] = {}
    for name, value in _module_bindings(tree):
        if not isinstance(value, ast.Set) or not value.elts:
            continue
        elements: list[str] = []
        for item in value.elts:
            if not (
                isinstance(item, ast.Constant)
                and isinstance(item.value, str)
                and not isinstance(item.value, bool)
            ):
                elements = []
                break
            elements.append(item.value)
        if not elements or len(set(elements)) != len(elements):
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
    for name, elements in candidates.items():
        if not _single_store(tree, name):
            continue
        loads = [
            item
            for item in ast.walk(tree)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id == name
        ]
        if not loads or any(id(load) not in membership_operands for load in loads):
            continue
        result[name] = elements
    return result


class _D2:
    enabled = False
    table: dict[str, tuple[str, ...]] = {}


def _v35_static_bool(
    node: ast.expr,
    row: Any,
    *,
    owner: Any,
    sequences: Any,
    active: Any = frozenset(),
) -> Any:
    if _D2.enabled and (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and len(node.comparators) == 1
        and isinstance(node.left, ast.Name)
        and node.left.id in row
        and isinstance(node.comparators[0], ast.Name)
        and node.comparators[0].id not in sequences
        and isinstance(node.ops[0], (ast.In, ast.NotIn))
    ):
        elements = _D2.table.get(node.comparators[0].id)
        if elements is not None:
            _record("d2-set-selector", node)
            present = row[node.left.id] in elements
            return not present if isinstance(node.ops[0], ast.NotIn) else present
    return _FROZEN_STATIC_BOOL(node, row, owner=owner, sequences=sequences, active=active)


# ======================================================================================
# D3: standard-library csv reader lineage.  Specified, NOT installed.
# ======================================================================================

_FROZEN_READER_CENSUS = df33._mt_full_scope_reader_census


def csv_reader_paths(tree: ast.Module) -> list[ast.expr]:
    """READER := `with open(PATH, <text kwargs>) as H: return list(csv.DictReader(H))`."""

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


class _D3:
    enabled = False


def _v35_reader_census(tree: ast.Module, **kwargs: Any) -> list[str | None]:
    result = _FROZEN_READER_CENSUS(tree, **kwargs)
    if not _D3.enabled:
        return result
    resolver = kwargs["resolver"]
    local_paths = kwargs["local_paths"]
    for path in csv_reader_paths(tree):
        resolved = df33._static_path(path, resolver)
        if resolved is None and isinstance(path, ast.Name):
            resolved = next(
                (value for key, value in local_paths.items() if key[-1] == path.id),
                next(iter(local_paths.values()), None),
            )
        _record("d3-csv-reader", path)
        result.append(resolved)
    return result


# ======================================================================================
# D4a: numeric group-mask comparator tokens
# ======================================================================================

_FROZEN_RESOLVER_STRING = df33._Resolver.string


def normalised_decimal(text: str) -> str | None:
    """`repr`-normalised decimal text of a finite decimal token, or None."""

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
    rows = list(
        csv.reader(
            io.StringIO(csv_content.decode("utf-8"), newline=""), dialect="excel", strict=True
        )
    )
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
    """Comparator spans the D4a grammar admits, each keyed to its one CSV group token."""

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
            span = _span(value_node)
            if -1 in span:
                continue
            result[span] = token
    return result


class _D4A:
    enabled = False
    positions: dict[tuple[int, int, int, int], str] = {}


def _v35_resolver_string(self: Any, node: ast.expr) -> str | None:
    frozen = _FROZEN_RESOLVER_STRING(self, node)
    if frozen is not None or not _D4A.enabled:
        return frozen
    token = _D4A.positions.get(_span(node))
    if token is None:
        return None
    _record("d4a-numeric-group", node)
    return token


# ======================================================================================
# D4b: terminal-position proof for a presentation loop
# ======================================================================================

_FROZEN_TRANSPORT_LOOP = df33._MtEngine._terminal_family_transport_loop

PREVENTION_NODES = (
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


def admitted_loop_iterator(engine: Any, node: ast.expr) -> bool:
    """ITER := NAME | enumerate(NAME) | enumerate(NAME, start=<int literal>)."""

    if isinstance(node, ast.Name):
        return True
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "enumerate"
        and node.func.id not in getattr(engine.resolver, "builtins_shadowed", set())
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


def terminal_presentation_loop(engine: Any, node: ast.For) -> bool:
    """The D4b production, stated as five conjunct proofs."""

    # 1. shape
    if isinstance(node, ast.AsyncFor) or node.orelse or not node.body:
        return False
    if not admitted_loop_iterator(engine, node.iter):
        return False
    # 2. no execution-prevention edge under the loop
    body_nodes = [item for statement in node.body for item in ast.walk(statement)]
    if any(isinstance(item, PREVENTION_NODES) for item in body_nodes):
        return False
    if any(
        isinstance(item, ast.Call) and engine.full_resolver.qualified(item.func) == "sys.exit"
        for item in body_nodes
    ):
        return False
    # 3. terminal position: nothing testable at or after the loop
    start = df33._position(node)
    for candidate in df33._walk_statements(engine.original_scope):
        if df33._position(candidate) < start:
            continue
        if isinstance(candidate, ast.Call):
            api = engine.full_resolver.qualified(candidate.func)
            if api in df33._MT_TEST_APIS or api in df33._MT_CORRECTION_APIS:
                return False
        if isinstance(candidate, ast.Attribute) and candidate.attr == "pvalue":
            return False
    # 4. nothing the loop binds escapes it
    bound = {
        item.id
        for item in body_nodes
        if isinstance(item, ast.Name) and isinstance(item.ctx, (ast.Store, ast.Del))
    }
    bound |= {item.id for item in ast.walk(node.target) if isinstance(item, ast.Name)}
    inside = {id(item) for item in body_nodes} | {id(item) for item in ast.walk(node.target)}
    end = (getattr(node, "end_lineno", 0) or 0, getattr(node, "end_col_offset", 0) or 0)
    outside: list[tuple[tuple[int, int], str, bool]] = []
    for item in df33._walk_statements((*engine.original_scope, *engine.scope)):
        if not (isinstance(item, ast.Name) and item.id in bound and id(item) not in inside):
            continue
        outside.append(
            (
                (getattr(item, "lineno", 0) or 0, getattr(item, "col_offset", 0) or 0),
                item.id,
                isinstance(item.ctx, ast.Load),
            )
        )
    for position, name, is_load in outside:
        if not is_load or position <= end:
            continue
        if not any(
            other_name == name and not other_load and end < other < position
            for other, other_name, other_load in outside
        ):
            return False
    # 5. the loop renders through a registered sink
    combined = (*engine.original_scope, *engine.scope)
    sink_calls = {id(sink.call) for sink in df33._registered_sinks(combined, engine.full_resolver)}
    return any(
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and id(statement.value) in sink_calls
        for statement in node.body
    )


class _D4B:
    enabled = False


def _v35_transport_loop(self: Any, node: Any) -> bool:
    if _FROZEN_TRANSPORT_LOOP(self, node):
        return True
    if not _D4B.enabled or not isinstance(node, ast.For):
        return False
    if terminal_presentation_loop(self, node):
        _record("d4b-loop-terminal", node)
        return True
    return False


# ======================================================================================
# installer and shadow entry point
# ======================================================================================


@contextlib.contextmanager
def installed(
    content: bytes,
    *,
    group_column: str,
    csv_content: bytes,
    group_values: tuple[str, ...],
    kinds: tuple[str, ...] = INSTALLED,
) -> Any:
    try:
        tree: ast.Module | None = ast.parse(content)
    except (SyntaxError, ValueError, RecursionError):
        tree = None
    saved: list[tuple[Any, str, Any]] = []
    try:
        if "d1-format-arm" in kinds and tree is not None:
            _D1.enabled = True
            _D1.constants = module_constant_names(tree)
            saved.append((df33._MtEngine, "_terminal_rendering_ifexp", _FROZEN_IFEXP))
            df33._MtEngine._terminal_rendering_ifexp = _v35_terminal_rendering_ifexp
            saved.append((df33._MtEngine, "_mt_v21_terminal_rendering_if", _FROZEN_IF))
            df33._MtEngine._mt_v21_terminal_rendering_if = _v35_terminal_rendering_if
            saved.append((tp33, "_terminal_ifexp_positions", _FROZEN_TP_IFEXP))
            tp33._terminal_ifexp_positions = _v35_tp_terminal_ifexp_positions
        if "d2-set-selector" in kinds and tree is not None:
            _D2.enabled = True
            _D2.table = membership_sets(tree)
            saved.append((cm34, "_static_bool", _FROZEN_STATIC_BOOL))
            cm34._static_bool = _v35_static_bool
        if "d3-csv-reader" in kinds:
            _D3.enabled = True
            saved.append((df33, "_mt_full_scope_reader_census", _FROZEN_READER_CENSUS))
            df33._mt_full_scope_reader_census = _v35_reader_census
        if "d4a-numeric-group" in kinds and tree is not None:
            _D4A.enabled = True
            _D4A.positions = group_mask_numeric_positions(
                tree,
                group_column=group_column,
                group_values=tuple(group_values),
                column_is_decimal=group_column_is_decimal(csv_content, group_column),
            )
            saved.append((df33._Resolver, "string", _FROZEN_RESOLVER_STRING))
            df33._Resolver.string = _v35_resolver_string
        if "d4b-loop-terminal" in kinds:
            _D4B.enabled = True
            saved.append(
                (df33._MtEngine, "_terminal_family_transport_loop", _FROZEN_TRANSPORT_LOOP)
            )
            df33._MtEngine._terminal_family_transport_loop = _v35_transport_loop
        if "d5-cardinality-read" in kinds:
            _D5.enabled = True
            saved.append(
                (df33._MtEngine, "_off_grammar_transform_guard", _FROZEN_OFF_GRAMMAR)
            )
            df33._MtEngine._off_grammar_transform_guard = _v35_off_grammar_transform_guard
        yield
    finally:
        for owner, name, value in reversed(saved):
            setattr(owner, name, value)
        _D1.enabled = False
        _D1.constants = frozenset()
        _D2.enabled = False
        _D2.table = {}
        _D3.enabled = False
        _D4A.enabled = False
        _D4A.positions = {}
        _D4B.enabled = False
        _D5.enabled = False


@dataclass(frozen=True)
class ShadowResult:
    frozen: Any
    outcome: Any
    changed: bool
    admission_census: dict[str, int]
    reanalysis_reason: str | None


def analyze_v35_shadow(
    content: bytes,
    *,
    authorized_path: str,
    group_column: str,
    outcome_columns: tuple[str, ...],
    csv_header: Any,
    group_values: tuple[str, str],
    csv_content: bytes,
    kinds: tuple[str, ...] = INSTALLED,
) -> ShadowResult:
    """The 3.5 ordering rule over the shipped 3.4 lane."""

    arguments: dict[str, Any] = {
        "authorized_path": authorized_path,
        "group_column": group_column,
        "outcome_columns": outcome_columns,
        "csv_header": csv_header,
        "group_values": group_values,
        "csv_content": csv_content,
    }
    frozen = df34.analyze_code_csv_multiple_testing_dataflow(content, **arguments)
    if frozen.reason is None:
        # step 3: a shipped 3.4 classification is returned untouched
        return ShadowResult(frozen, frozen, False, {kind: 0 for kind in ADMISSION_KINDS}, None)
    _RECORDED.clear()
    before = census_snapshot()
    try:
        with installed(
            content,
            group_column=group_column,
            csv_content=csv_content,
            group_values=tuple(group_values),
            kinds=kinds,
        ):
            attempted = df34._reanalyze_with_v34_admissions(content, **arguments)
    except RecursionError:
        attempted = frozen
    after = census_snapshot()
    census = {kind: after[kind] - before[kind] for kind in ADMISSION_KINDS}
    if attempted.reason is None and not df34._record_collection_alias_unresolved(content):
        # step 5: the re-analysis is adopted only when it is itself a classification
        return ShadowResult(frozen, attempted, True, census, None)
    # steps 5 and 6: an abstaining re-analysis returns the frozen 3.4 reason byte-for-byte
    return ShadowResult(frozen, frozen, False, census, attempted.reason)


def install_into_adapter(kinds: tuple[str, ...] = INSTALLED) -> None:
    """Real-pipeline installation, for a scratch tree only.

    The shipped 3.4 adapter binds the dataflow entry point into its own namespace at import,
    so the shadow replaces that binding.  This is a measurement device: it does not advance
    a detector version and it does not change the implementation digest the adapter reports.
    """

    from sc_referee.scientific_checks import code_csv_multiple_testing_adapter_v3_4 as adapter

    def entry(content: bytes, **arguments: Any) -> Any:
        return analyze_v35_shadow(content, kinds=kinds, **arguments).outcome

    adapter.analyze_code_csv_multiple_testing_dataflow = entry


# ======================================================================================
# D5: cardinality read of the reconstructed p-record collection, display only
# ======================================================================================

_FROZEN_OFF_GRAMMAR = df33._MtEngine._off_grammar_transform_guard
_FROZEN_P_ORIGINS = df33._MtEngine._p_origins

#: An ancestor of an admitted `len()` may only be one of these on the way to its sink.
DISPLAY_ANCESTORS = (ast.JoinedStr, ast.FormattedValue, ast.Expr)

#: Callees an admitted `len()` may appear inside as a display payload.
_DISPLAY_CALLEES = frozenset({"print", "format", "str"})


def _parent_map(statements: Any) -> dict[ast.AST, ast.AST]:
    return {
        child: parent
        for parent in df33._walk_statements(statements)
        for child in ast.iter_child_nodes(parent)
    }


def admitted_cardinality_reads(engine: Any) -> set[int]:
    """`len(COLLECTION)` where COLLECTION is the complete p-record family and the value
    reaches only a display sink.

    The admitted value is a constant the analyzer already holds -- the family size -- so the
    admission adds no value route.  It removes an unaccounted-for consumer of the collection.
    """

    scope = self_scope = engine.scope
    parents = _parent_map(scope)
    sink_calls = {id(sink.call) for sink in engine.sinks}
    expected = tuple(range(len(engine.outcome_columns)))
    admitted: set[int] = set()
    for node in df33._walk_statements(self_scope):
        if not (
            isinstance(node, ast.Call)
            and engine.resolver.qualified(node.func) == "len"
            and "len" not in getattr(engine.resolver, "builtins_shadowed", set())
            and len(node.args) == 1
            and not node.keywords
            and isinstance(node.args[0], ast.Name)
        ):
            continue
        # the argument is the complete, contract-order p-record collection
        sequence = engine._p_sequence(node.args[0])
        if sequence is None or tuple(sequence) != expected:
            continue
        # the collection name is bound exactly once
        name = node.args[0].id
        stores = sum(
            isinstance(item, ast.Name)
            and isinstance(item.ctx, (ast.Store, ast.Del))
            and item.id == name
            for item in df33._walk_statements(scope)
        )
        if stores != 1:
            continue
        # every ancestor up to the enclosing statement is a display node, and the statement
        # is an expression whose call is a registered sink
        cursor: ast.AST = node
        ok = True
        while True:
            parent = parents.get(cursor)
            if parent is None:
                ok = False
                break
            if isinstance(parent, ast.Call):
                if id(parent) in sink_calls:
                    break
                if (
                    isinstance(parent.func, ast.Attribute)
                    and parent.func.attr == "format"
                    and bare_display(parent.func.value)
                ) or engine.resolver.qualified(parent.func) in _DISPLAY_CALLEES:
                    cursor = parent
                    continue
                ok = False
                break
            if not isinstance(parent, DISPLAY_ANCESTORS):
                ok = False
                break
            if isinstance(parent, ast.Expr):
                ok = isinstance(parent.value, ast.Call) and id(parent.value) in sink_calls
                break
            cursor = parent
        if not ok:
            continue
        if not engine._mt_v2_rendering_load_reaches_sink(node, _parent_map(scope)):
            continue
        admitted.add(id(node))
    return admitted


class _D5:
    enabled = False


def _v35_off_grammar_transform_guard(self: Any) -> str | None:
    if not _D5.enabled:
        return _FROZEN_OFF_GRAMMAR(self)
    admitted = admitted_cardinality_reads(self)
    if not admitted:
        return _FROZEN_OFF_GRAMMAR(self)

    def origins(engine_self: Any, node: ast.AST, *args: Any, **kwargs: Any) -> Any:
        if id(node) in admitted:
            return frozenset()
        return _FROZEN_P_ORIGINS(engine_self, node, *args, **kwargs)

    df33._MtEngine._p_origins = origins
    try:
        reason = _FROZEN_OFF_GRAMMAR(self)
    finally:
        df33._MtEngine._p_origins = _FROZEN_P_ORIGINS
    if reason is None:
        for node in df33._walk_statements(self.scope):
            if id(node) in admitted:
                _record("d5-cardinality-read", node)
    return reason
