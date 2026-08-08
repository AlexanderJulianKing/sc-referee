"""ADR-0069 static dataflow resolution of founder-panel orientation before emission.

This library works backward from the per-marker equality that selects an
emission probability. It reads each Python workflow source statically, tags
the provenance of every row set read from a staged CSV input, and tracks, per
column, whether the value reaching that equality is the staged value or its
involution (0 <-> 1). Both operands of the equality must be columns of the
same row set; the parity of the recognized value-inverting steps on the two
operand paths, taken together, is the answer. An odd total parity means one
panel was complement-repaired before the comparison; an even total parity
means the comparison reads the two panels in the same coding. Variable
names, function names, and column names never matter; only the operations do.

The cardinal rule: ``direct`` is never a fallthrough. An equality classifies
as the direct reading only when every step on both operand paths is a
recognized identity-preserving or recognized inverting operation. Anything
unrecognized on a path that touches the staged rows abstains, because a
transform this library cannot read may be exactly the repair whose absence
would invert every ancestry assignment.

Soundness rules (each backed by a demonstrated counterexample in
``tests/test_founder_orientation_soundness.py``):

- An unrecognized transform on an operand path abstains; it never reads as
  the direct orientation.
- Inversions on both operands compose to no net change, and classify as the
  direct reading only when both paths are otherwise identity-proven.
- Two inversions composed on one path have even parity and classify as the
  direct reading only when both inversions are recognized.
- A transform that is not on either operand's path (a diagnostic or mask
  flip) has no effect on the classification.
- A conditional repair classifies only when its guard is itself a
  cross-panel comparison; any other guard abstains.
- Only equalities whose selected probability can reach the written report
  classify.
- Equalities reaching the report with conflicting classifications abstain.
- Helper tracing is depth-bounded with cycle detection; recursion abstains
  instead of crashing.
- A function body is traced with its parameters masked, so an emission
  comparison that reads a row set arriving as a parameter abstains rather
  than letting a module global stand in for it.

The report-reaching closure, the statement flattening, the ``__main__``
guard recognition, the call-binding shape, and the evidence-span projection
are modelled on ``quantity_dataflow_adapter``; they are copied rather than
imported so the two recognizers stay independently versionable and neither
module's identity moves when the other changes.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.scientific_checks.core import (
    EvidenceSpan,
    FrozenInspectionContext,
    InspectionDocument,
)

FOUNDER_ORIENTATION_DATAFLOW_IMPLEMENTATION_DIGEST = sha256_digest(Path(__file__).read_bytes())

_MAX_CALL_DEPTH = 2
_READER_CALLS = {"csv.DictReader", "csv.reader", "DictReader", "reader"}
_ACCUMULATOR_CALLS = {"sum", "prod", "math.prod", "fsum", "math.fsum"}
_IDENTITY_CASTS = {"int", "float", "str"}
_STRIP_METHODS = {"strip", "lstrip", "rstrip"}
_WRITE_METHODS = {"write", "writelines", "write_text"}
_MUTATING_METHODS = {
    "append",
    "extend",
    "insert",
    "pop",
    "remove",
    "clear",
    "update",
    "setdefault",
    "sort",
    "reverse",
    "popitem",
}
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

_REPAIRED = "repaired"
_DIRECT = "direct"


def founder_orientation_dataflow_grammar(
    direct_operand: str, repaired_operand: str
) -> dict[str, Any]:
    return {
        "grammar_id": "founder-orientation-emission-dataflow",
        "grammar_version": "1.0.0",
        "row_source_operations": ["csv.DictReader", "csv.reader"],
        "emission_comparison": (
            "an equality or inequality between two distinct columns of one "
            "staged row set, selecting between two numeric values inside a "
            "product or sum accumulation whose value reaches the written report"
        ),
        "selector_forms": [
            "conditional expression whose test is the comparison",
            "two-element list, tuple, or dict literal indexed by the comparison",
        ],
        "accumulation_forms": [
            "sum, prod, math.prod, or math.fsum over a comprehension",
            "a comprehension bound to a name that one of those consumes",
            "an elementwise multiply or add accumulation loop over the row set",
        ],
        "involutive_recode_forms": [
            "1 - x",
            "x ^ 1",
            "abs(x - 1)",
            "not x and int(not x)",
            "1 if x == 0 else 0 and its mirrored forms",
            "{0: 1, 1: 0}[x]",
            "a two-element list or tuple literal indexed by x with a reversed domain",
            "a row-column comprehension applying any of the above",
            "a straight-line local helper applying any of the above",
            "a recognized elementwise accumulation loop applying any of the above",
        ],
        "identity_preserving_steps": [
            "int, float, and str casts",
            "strip, lstrip, and rstrip on a column value",
            "assignment and list materialization of a row set",
            "constant-string column subscripts",
            "dict literals and dict-spread literals rebuilding a row",
        ],
        "classification_rule": (
            "odd total parity over both operand paths is the repaired "
            "orientation; even total parity is the direct orientation, and only "
            "when every step on both paths is recognized; anything unrecognized, "
            "unresolved, or conflicting abstains"
        ),
        "operand_by_parity": {
            "odd_total_parity": repaired_operand,
            "even_total_parity_with_proven_paths": direct_operand,
        },
        "conditional_repair": (
            "a guarded rebinding of a row set to an involuted row set is the "
            "repaired orientation only when the guard is itself a cross-panel "
            "comparison; any other guard leaves the document unsupported"
        ),
        "control_flow": (
            "straight-line assignments, comprehensions, with-blocks, functions, "
            "the __main__ guard, recognized accumulation and row-building loops, "
            "and recognized guarded repairs"
        ),
        "function_support": (
            "straight-line bodies; positional and keyword call binding; return "
            "values joined over every return; depth-bounded with cycle detection"
        ),
        "soundness": [
            "direct is never a fallthrough",
            "unrecognized operand-path transforms abstain",
            "joint operand inversions compose to the direct reading only when proven",
            "off-path inversions never classify",
            "report-reaching value linkage",
            "conflicting classifications abstain",
            "bounded call depth with cycle abstention",
        ],
        "nomenclature_authority": "none",
    }


def founder_orientation_dataflow_grammar_digest(direct_operand: str, repaired_operand: str) -> str:
    return semantic_digest(founder_orientation_dataflow_grammar(direct_operand, repaired_operand))


# ---------------------------------------------------------------------------
# Value model.


@dataclass(frozen=True)
class _Rows:
    """A row set, with per-column provenance relative to the staged read.

    ``overrides`` maps an output column to the staged column it came from and
    the parity of the recognized inverting steps on the way, or to ``None``
    when the column passed through something this library cannot read.
    ``default_identity`` says whether a column absent from ``overrides``
    passes through unchanged.
    """

    overrides: tuple[tuple[str, tuple[str, int] | None], ...] = ()
    default_identity: bool = True
    iterator: bool = False


@dataclass(frozen=True)
class _Scalar:
    cross_panel: bool = False


@dataclass(frozen=True)
class _EmptyList:
    pass


@dataclass(frozen=True)
class _Opaque:
    pass


_OPAQUE = _Opaque()
_EMPTY_LIST = _EmptyList()

_Value = _Rows | _Scalar | _EmptyList | _Opaque


@dataclass(frozen=True)
class _Path:
    """A resolved column origin, or the unresolved marker when ``column`` is None."""

    column: str | None
    parity: int = 0

    @property
    def resolved(self) -> bool:
        return self.column is not None


_UNRESOLVED = _Path(None)


@dataclass(frozen=True)
class _Classification:
    node: ast.AST
    state: str


@dataclass(frozen=True)
class FounderDataflowResolution:
    """The outcome of the bounded source trace across every Python document."""

    state: str  # "unique" | "none" | "ambiguous" | "unsupported"
    orientation: str | None  # "repaired" | "direct" | None
    operand_value: str | None
    spans: tuple[EvidenceSpan, ...]
    source_path: str | None


@dataclass
class _TraceContext:
    functions: dict[str, ast.FunctionDef]
    accumulated: set[int] = field(default_factory=set)
    reaching: set[str] = field(default_factory=set)
    depth: int = 0
    visiting: set[str] = field(default_factory=set)
    recognized_ids: set[int] = field(default_factory=set)
    unresolved: bool = False


# ---------------------------------------------------------------------------
# The public resolver.


def resolve_founder_orientation_dataflow(
    context: FrozenInspectionContext,
    *,
    direct_operand: str,
    repaired_operand: str,
    parser_id: str,
    parser_version: str,
) -> FounderDataflowResolution:
    classifications: list[tuple[InspectionDocument, _Classification]] = []
    unsupported = False
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
        outcome = _document_orientations(tree)
        unsupported = unsupported or outcome["unsupported"]
        classifications.extend((document, item) for item in outcome["classifications"])
    states = sorted({item.state for _, item in classifications})
    if len(states) > 1:
        return FounderDataflowResolution("ambiguous", None, None, (), None)
    if unsupported or parse_failure:
        # A resolved comparison next to an unreadable transform or untraceable
        # control flow could be rebound by it; abstain rather than guess.
        return FounderDataflowResolution("unsupported", None, None, (), None)
    if not classifications:
        return FounderDataflowResolution("none", None, None, (), None)
    orientation = states[0]
    spans = tuple(
        _ast_node_evidence_span(item_document, item.node) for item_document, item in classifications
    )
    return FounderDataflowResolution(
        "unique",
        orientation,
        repaired_operand if orientation == _REPAIRED else direct_operand,
        spans,
        classifications[0][0].path,
    )


def _python_parser_supported(
    document: InspectionDocument, parser_id: str, parser_version: str
) -> bool:
    if document.parser_result_payload is None:
        return False
    value = json.loads(document.parser_result_payload)
    return (
        isinstance(value, dict)
        and value.get("parser_id") == parser_id
        and value.get("parser_version") == parser_version
        and value.get("state") == "parsed"
    )


# ---------------------------------------------------------------------------
# The per-document trace engine.


def _document_orientations(tree: ast.Module) -> dict[str, Any]:
    """Trace report-reaching emission comparisons across module and function scopes."""

    functions: dict[str, ast.FunctionDef] = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    ctx = _TraceContext(
        functions=functions,
        accumulated=_accumulated_comprehension_ids(tree),
        reaching=_report_reaching_names(tree, functions),
    )
    classifications: list[_Classification] = []

    module_env: dict[str, _Value] = {}
    _scan_scope(
        [item for item in tree.body if not isinstance(item, ast.FunctionDef)],
        module_env,
        ctx,
        classifications,
    )
    for function in functions.values():
        # Function bodies are scanned with parameters masked, so a module
        # global can never stand in for an unbound parameter.
        env: dict[str, _Value] = dict(module_env)
        for parameter in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        ):
            env[parameter.arg] = _OPAQUE
        _scan_scope(function.body, env, ctx, classifications)

    return {
        "classifications": classifications,
        "unsupported": ctx.unresolved or _has_unsupported_flow(tree, ctx.recognized_ids),
    }


def _scan_scope(
    statements: list[ast.stmt],
    env: dict[str, _Value],
    ctx: _TraceContext,
    classifications: list[_Classification],
) -> None:
    for statement in _flatten_statements(statements):
        if _apply_recognized_repair_if(statement, env, ctx):
            continue
        if _apply_recognized_loop(statement, env, ctx, classifications):
            continue
        if _statement_reaches(statement, ctx):
            for node in _walk_skipping_lambdas(statement):
                if (
                    isinstance(node, ast.ListComp | ast.GeneratorExp)
                    and id(node) in ctx.accumulated
                ):
                    _classify_comprehension(node, env, ctx, classifications)
        _invalidate_mutations(statement, env)
        _apply_assign(statement, env, ctx)


def _statement_reaches(statement: ast.stmt, ctx: _TraceContext) -> bool:
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    ):
        return statement.targets[0].id in ctx.reaching
    if isinstance(statement, ast.Expr) and _write_payloads(statement.value):
        return True
    return isinstance(statement, ast.Return)


def _apply_assign(statement: ast.stmt, env: dict[str, _Value], ctx: _TraceContext) -> None:
    if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
        return
    target = statement.targets[0]
    if not isinstance(target, ast.Name):
        return
    env[target.id] = _tag(statement.value, env, ctx)


def _invalidate_mutations(statement: ast.stmt, env: dict[str, _Value]) -> None:
    """Drop provenance for row sets a statement mutates or deletes from."""

    for node in ast.walk(statement):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.attr in _MUTATING_METHODS
            and isinstance(env.get(node.func.value.id), _Rows)
        ):
            env[node.func.value.id] = _OPAQUE
        elif isinstance(node, ast.Delete):
            for item in node.targets:
                inner: ast.expr = item
                while isinstance(inner, ast.Subscript):
                    inner = inner.value
                if isinstance(inner, ast.Name) and inner.id in env:
                    env[inner.id] = _OPAQUE


# ---------------------------------------------------------------------------
# Emission comparison recognition.


def _classify_comprehension(
    node: ast.ListComp | ast.GeneratorExp,
    env: dict[str, _Value],
    ctx: _TraceContext,
    classifications: list[_Classification],
) -> None:
    if len(node.generators) != 1:
        return
    generator = node.generators[0]
    if not isinstance(generator.target, ast.Name):
        return
    selectors = _selector_comparisons(node.elt)
    if not selectors:
        return
    source = _tag(generator.iter, env, ctx)
    for compare in selectors:
        _classify_compare(compare, generator.target.id, source, env, ctx, classifications)


def _classify_compare(
    compare: ast.Compare,
    loop_var: str,
    source: _Value,
    env: dict[str, _Value],
    ctx: _TraceContext,
    classifications: list[_Classification],
) -> None:
    if len(compare.ops) != 1 or not isinstance(compare.ops[0], ast.Eq | ast.NotEq):
        return
    left = _column_parity(compare.left, loop_var=loop_var, carriers={}, env=env, ctx=ctx)
    right = _column_parity(compare.comparators[0], loop_var=loop_var, carriers={}, env=env, ctx=ctx)
    if left is None or right is None:
        # At least one side is not a column of the iterated rows at all, so
        # this is a filter or a literal test, not an emission comparison.
        return
    if not left.resolved or not right.resolved:
        ctx.unresolved = True
        return
    if not isinstance(source, _Rows):
        # The comparison reads columns, but the row set they came from is not
        # a traceable staged read; the orientation is unknowable here.
        ctx.unresolved = True
        return
    left_source = _rows_column(source, str(left.column))
    right_source = _rows_column(source, str(right.column))
    if left_source is None or right_source is None:
        ctx.unresolved = True
        return
    if left_source[0] == right_source[0]:
        # A column compared with itself carries no cross-panel orientation.
        return
    parity = (left.parity + left_source[1] + right.parity + right_source[1]) % 2
    classifications.append(_Classification(node=compare, state=_REPAIRED if parity else _DIRECT))


def _selector_comparisons(element: ast.expr) -> list[ast.Compare]:
    """Comparisons that select between two numeric values inside one element."""

    found: list[ast.Compare] = []
    for node in ast.walk(element):
        if isinstance(node, ast.IfExp) and isinstance(node.test, ast.Compare):
            if _numeric_like(node.body) and _numeric_like(node.orelse):
                found.append(node.test)
        elif isinstance(node, ast.Subscript):
            if not _two_element_numeric_container(node.value):
                continue
            index = node.slice
            if (
                isinstance(index, ast.Call)
                and _call_name(index) == "int"
                and len(index.args) == 1
                and not index.keywords
            ):
                index = index.args[0]
            if isinstance(index, ast.Compare):
                found.append(index)
    return found


def _two_element_numeric_container(node: ast.expr) -> bool:
    """A two-element literal of emission probabilities indexed by a boolean."""

    return (
        isinstance(node, ast.List | ast.Tuple)
        and len(node.elts) == 2
        and all(_numeric_like(item) for item in node.elts)
    )


def _numeric_like(node: ast.expr) -> bool:
    """A numeric emission probability: a literal, a name, or arithmetic over them."""

    if isinstance(node, ast.Constant):
        return isinstance(node.value, int | float) and not isinstance(node.value, bool)
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.UnaryOp):
        return _numeric_like(node.operand)
    if isinstance(node, ast.BinOp):
        return _numeric_like(node.left) and _numeric_like(node.right)
    if isinstance(node, ast.Call) and _call_name(node) in {"float", "int", "Decimal"}:
        return len(node.args) == 1 and _numeric_like(node.args[0])
    return False


def _rows_column(rows: _Rows, column: str) -> tuple[str, int] | None:
    for key, value in rows.overrides:
        if key == column:
            return value
    return (column, 0) if rows.default_identity else None


# ---------------------------------------------------------------------------
# Per-column parity of one expression.


def _column_parity(
    expression: ast.expr,
    *,
    loop_var: str | None,
    carriers: dict[str, _Path],
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Path | None:
    """The staged column an expression reads and the parity of its recoding.

    Returns ``None`` when the expression has no row-column origin at all,
    the unresolved marker when it touches one through an operation this
    library does not recognize, and a resolved path otherwise.
    """

    def _unknown() -> _Path | None:
        return _UNRESOLVED if _touches_rows(expression, loop_var, carriers) else None

    if isinstance(expression, ast.Name):
        return carriers.get(expression.id)

    if isinstance(expression, ast.Subscript):
        if (
            loop_var is not None
            and isinstance(expression.value, ast.Name)
            and expression.value.id == loop_var
            and isinstance(expression.slice, ast.Constant)
            and isinstance(expression.slice.value, str)
        ):
            return _Path(expression.slice.value, 0)
        table = _two_element_table(expression.value)
        if table is not None:
            base = _column_parity(
                expression.slice, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
            )
            return _table_shift(table, base)
        return _unknown()

    if isinstance(expression, ast.Call):
        return _call_parity(expression, loop_var, carriers, env, ctx) or _unknown()

    if isinstance(expression, ast.BinOp):
        if isinstance(expression.op, ast.Sub) and _is_one(expression.left):
            return _shift(
                _column_parity(
                    expression.right, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
                ),
                1,
            )
        if isinstance(expression.op, ast.BitXor):
            for one, other in (
                (expression.right, expression.left),
                (expression.left, expression.right),
            ):
                if _is_one(one):
                    return _shift(
                        _column_parity(
                            other, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
                        ),
                        1,
                    )
        return _unknown()

    if isinstance(expression, ast.UnaryOp) and isinstance(expression.op, ast.Not):
        return _shift(
            _column_parity(
                expression.operand, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
            ),
            1,
        )

    if isinstance(expression, ast.IfExp):
        return _ifexp_parity(expression, loop_var, carriers, env, ctx) or _unknown()

    return _unknown()


def _call_parity(
    call: ast.Call,
    loop_var: str | None,
    carriers: dict[str, _Path],
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Path | None:
    name = _call_name(call)
    if (
        isinstance(call.func, ast.Attribute)
        and call.func.attr in _STRIP_METHODS
        and not call.args
        and not call.keywords
    ):
        return _column_parity(
            call.func.value, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
        )
    if (
        name in _IDENTITY_CASTS
        and len(call.args) == 1
        and not call.keywords
        and name not in env
        and name not in ctx.functions
    ):
        return _column_parity(call.args[0], loop_var=loop_var, carriers=carriers, env=env, ctx=ctx)
    if name == "abs" and len(call.args) == 1 and not call.keywords and "abs" not in ctx.functions:
        inner = call.args[0]
        if isinstance(inner, ast.BinOp) and isinstance(inner.op, ast.Sub):
            for one, other in ((inner.right, inner.left), (inner.left, inner.right)):
                if _is_one(one):
                    return _shift(
                        _column_parity(
                            other, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
                        ),
                        1,
                    )
        return None
    if name in ctx.functions:
        return _helper_parity(ctx.functions[name], call, loop_var, carriers, env, ctx)
    return None


def _helper_parity(
    function: ast.FunctionDef,
    call: ast.Call,
    loop_var: str | None,
    carriers: dict[str, _Path],
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Path | None:
    """Parity of a straight-line helper applied to exactly one column value."""

    if ctx.depth >= _MAX_CALL_DEPTH or function.name in ctx.visiting:
        return _UNRESOLVED
    if (
        function.args.posonlyargs
        or function.args.kwonlyargs
        or function.args.vararg
        or function.args.kwarg
    ):
        return _UNRESOLVED
    parameters = [item.arg for item in function.args.args]
    bound: dict[str, ast.expr] = {}
    if len(call.args) > len(parameters):
        return _UNRESOLVED
    for parameter, argument in zip(parameters, call.args, strict=False):
        bound[parameter] = argument
    for keyword in call.keywords:
        if keyword.arg is None or keyword.arg not in parameters or keyword.arg in bound:
            return _UNRESOLVED
        bound[keyword.arg] = keyword.value
    if set(bound) != set(parameters):
        return _UNRESOLVED
    carried: dict[str, _Path] = {}
    for parameter, argument in bound.items():
        path = _column_parity(argument, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx)
        if path is None:
            continue
        if not path.resolved:
            return _UNRESOLVED
        carried[parameter] = path
    if len(carried) != 1:
        # A helper carrying no column, or two of them, is not a recode of one
        # panel value; abstain rather than pick a side.
        return None if not carried else _UNRESOLVED
    ctx.depth += 1
    ctx.visiting.add(function.name)
    try:
        local = dict(carried)
        for statement in _flatten_statements(function.body):
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                path = _column_parity(
                    statement.value, loop_var=None, carriers=local, env=env, ctx=ctx
                )
                if path is not None:
                    local[statement.targets[0].id] = path
                else:
                    local.pop(statement.targets[0].id, None)
            elif not isinstance(statement, ast.Return | ast.Pass | ast.Expr):
                return _UNRESOLVED
        results: set[tuple[str, int]] = set()
        for node in ast.walk(function):
            if isinstance(node, ast.Return) and node.value is not None:
                path = _column_parity(node.value, loop_var=None, carriers=local, env=env, ctx=ctx)
                if path is None or not path.resolved:
                    return _UNRESOLVED
                results.add((str(path.column), path.parity % 2))
        if len(results) != 1:
            return _UNRESOLVED
        column, parity = next(iter(results))
        return _Path(column, parity)
    finally:
        ctx.depth -= 1
        ctx.visiting.discard(function.name)


def _ifexp_parity(
    expression: ast.IfExp,
    loop_var: str | None,
    carriers: dict[str, _Path],
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Path | None:
    """``1 if x == 0 else 0`` and its three mirrored forms."""

    test = expression.test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return None
    if not isinstance(test.ops[0], ast.Eq | ast.NotEq):
        return None
    body = _binary_constant(expression.body)
    orelse = _binary_constant(expression.orelse)
    if body is None or orelse is None or body == orelse:
        return None
    for constant_side, value_side in (
        (test.left, test.comparators[0]),
        (test.comparators[0], test.left),
    ):
        constant = _binary_constant(constant_side)
        if constant is None:
            continue
        base = _column_parity(value_side, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx)
        if base is None:
            return None
        matched, unmatched = (body, orelse) if isinstance(test.ops[0], ast.Eq) else (orelse, body)
        table = [0, 0]
        table[constant] = matched
        table[1 - constant] = unmatched
        return _table_shift((table[0], table[1]), base)
    return None


def _two_element_table(node: ast.expr) -> tuple[int, int] | None:
    """A literal mapping of the domain {0, 1} onto {0, 1}."""

    if isinstance(node, ast.List | ast.Tuple) and len(node.elts) == 2:
        values = [_binary_constant(item) for item in node.elts]
        if values[0] is not None and values[1] is not None:
            return (values[0], values[1])
        return None
    if isinstance(node, ast.Dict) and len(node.keys) == 2:
        entries: dict[int, int] = {}
        for key, value in zip(node.keys, node.values, strict=True):
            if key is None:
                return None
            index = _binary_constant(key)
            mapped = _binary_constant(value)
            if index is None or mapped is None:
                return None
            entries[index] = mapped
        if set(entries) == {0, 1}:
            return (entries[0], entries[1])
    return None


def _table_shift(table: tuple[int, int], base: _Path | None) -> _Path | None:
    if base is None:
        return None
    if not base.resolved:
        return base
    if table == (0, 1):
        return base
    if table == (1, 0):
        return _Path(base.column, base.parity + 1)
    return _UNRESOLVED


def _binary_constant(node: ast.expr) -> int | None:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and node.value in {0, 1}
    ):
        return int(node.value)
    return None


def _is_one(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int | float)
        and not isinstance(node.value, bool)
        and node.value == 1
    )


def _shift(base: _Path | None, amount: int) -> _Path | None:
    if base is None or not base.resolved:
        return base
    return _Path(base.column, base.parity + amount)


def _touches_rows(expression: ast.expr, loop_var: str | None, carriers: dict[str, _Path]) -> bool:
    for node in ast.walk(expression):
        if (
            loop_var is not None
            and isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == loop_var
        ):
            return True
        if isinstance(node, ast.Name) and node.id in carriers:
            return True
    return False


# ---------------------------------------------------------------------------
# Row-set tagging.


def _tag(node: ast.expr, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    if isinstance(node, ast.Name):
        return env.get(node.id, _OPAQUE)
    if isinstance(node, ast.Constant):
        return _Scalar() if isinstance(node.value, int | float) else _OPAQUE
    if isinstance(node, ast.List | ast.Tuple) and not node.elts:
        return _EMPTY_LIST
    if isinstance(node, ast.Call):
        return _tag_call(node, env, ctx)
    if isinstance(node, ast.ListComp | ast.GeneratorExp):
        return _tag_comprehension(node, env, ctx)
    if isinstance(node, ast.BinOp | ast.UnaryOp | ast.Compare):
        return _Scalar(cross_panel=_expression_has_cross_panel(node, env, ctx))
    return _OPAQUE


def _tag_call(node: ast.Call, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    name = _call_name(node)
    if name in _READER_CALLS:
        return _Rows(iterator=True)
    if name == "list" and len(node.args) == 1 and not node.keywords:
        inner = _tag(node.args[0], env, ctx)
        if isinstance(inner, _Rows):
            return _Rows(inner.overrides, inner.default_identity, iterator=False)
        return _OPAQUE
    if name in _ACCUMULATOR_CALLS or name in {"len"}:
        return _Scalar(cross_panel=_expression_has_cross_panel(node, env, ctx))
    if name in ctx.functions:
        return _bound_return_value(ctx.functions[name], node, env, ctx)
    if (
        name in _IDENTITY_CASTS
        and len(node.args) == 1
        and not node.keywords
        and name not in ctx.functions
    ):
        inner = _tag(node.args[0], env, ctx)
        return inner if isinstance(inner, _Scalar) else _OPAQUE
    return _OPAQUE


def _tag_comprehension(
    node: ast.ListComp | ast.GeneratorExp, env: dict[str, _Value], ctx: _TraceContext
) -> _Value:
    if len(node.generators) != 1:
        return _OPAQUE
    generator = node.generators[0]
    if not isinstance(generator.target, ast.Name):
        return _OPAQUE
    source = _tag(generator.iter, env, ctx)
    if not isinstance(source, _Rows):
        return _OPAQUE
    return _row_element_value(node.elt, generator.target.id, source, env, ctx)


def _row_element_value(
    element: ast.expr,
    loop_var: str,
    source: _Rows,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Value:
    """The row set a per-row element expression builds, or opaque."""

    if isinstance(element, ast.Name) and element.id == loop_var:
        return _Rows(source.overrides, source.default_identity, iterator=False)
    if not isinstance(element, ast.Dict):
        return _OPAQUE
    spread = False
    explicit: list[tuple[str, tuple[str, int] | None]] = []
    for key, value in zip(element.keys, element.values, strict=True):
        if key is None:
            if not (isinstance(value, ast.Name) and value.id == loop_var):
                return _OPAQUE
            spread = True
            continue
        if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
            return _OPAQUE
        path = _column_parity(value, loop_var=loop_var, carriers={}, env=env, ctx=ctx)
        if path is None or not path.resolved:
            explicit.append((key.value, None))
            continue
        resolved = _rows_column(source, str(path.column))
        if resolved is None:
            explicit.append((key.value, None))
            continue
        explicit.append((key.value, (resolved[0], (resolved[1] + path.parity) % 2)))
    overrides: dict[str, tuple[str, int] | None] = {}
    if spread:
        overrides.update(dict(source.overrides))
    overrides.update(dict(explicit))
    return _Rows(
        tuple(sorted(overrides.items())),
        default_identity=source.default_identity if spread else False,
        iterator=False,
    )


def _bind_call(
    function: ast.FunctionDef,
    call: ast.Call,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> dict[str, _Value] | None:
    if (
        function.args.posonlyargs
        or function.args.kwonlyargs
        or function.args.vararg
        or function.args.kwarg
    ):
        return None
    parameters = [item.arg for item in function.args.args]
    if len(call.args) > len(parameters):
        return None
    bound: dict[str, _Value] = {}
    for parameter, argument in zip(parameters, call.args, strict=False):
        bound[parameter] = _tag(argument, env, ctx)
    for keyword in call.keywords:
        if keyword.arg is None or keyword.arg not in parameters or keyword.arg in bound:
            return None
        bound[keyword.arg] = _tag(keyword.value, env, ctx)
    for parameter in parameters[len(parameters) - len(function.args.defaults) :]:
        bound.setdefault(parameter, _OPAQUE)
    if set(bound) != set(parameters):
        return None
    return bound


def _bound_return_value(
    function: ast.FunctionDef,
    call: ast.Call,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Value:
    """The joined return value of a callee with its parameters bound."""

    if ctx.depth >= _MAX_CALL_DEPTH or function.name in ctx.visiting:
        return _OPAQUE
    callee_env = _bind_call(function, call, env, ctx)
    if callee_env is None:
        return _OPAQUE
    ctx.depth += 1
    ctx.visiting.add(function.name)
    try:
        for statement in _flatten_statements(function.body):
            _apply_recognized_loop(statement, callee_env, ctx, [])
            _apply_assign(statement, callee_env, ctx)
        values: set[_Value] = set()
        for node in ast.walk(function):
            if isinstance(node, ast.Return) and node.value is not None:
                values.add(_tag(node.value, callee_env, ctx))
        if len(values) == 1:
            return next(iter(values))
        return _OPAQUE
    finally:
        ctx.depth -= 1
        ctx.visiting.discard(function.name)


# ---------------------------------------------------------------------------
# Recognized loops and guarded repairs.


def _apply_recognized_loop(
    statement: ast.stmt,
    env: dict[str, _Value],
    ctx: _TraceContext,
    classifications: list[_Classification],
) -> bool:
    if not isinstance(statement, ast.For) or statement.orelse:
        return False
    if not isinstance(statement.target, ast.Name):
        return False
    source = _tag(statement.iter, env, ctx)
    if not isinstance(source, _Rows):
        return False
    if _apply_row_building_loop(statement, source, env, ctx):
        _mark_recognized(statement, ctx)
        return True
    if _apply_accumulation_loop(statement, source, env, ctx, classifications):
        _mark_recognized(statement, ctx)
        return True
    return False


def _apply_row_building_loop(
    loop: ast.For, source: _Rows, env: dict[str, _Value], ctx: _TraceContext
) -> bool:
    """``out = []`` then ``for row in rows: out.append(<row expression>)``."""

    assert isinstance(loop.target, ast.Name)
    built: dict[str, set[_Value]] = {}
    for statement in loop.body:
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Attribute)
            and statement.value.func.attr == "append"
            and isinstance(statement.value.func.value, ast.Name)
            and len(statement.value.args) == 1
            and not statement.value.keywords
        ):
            return False
        name = statement.value.func.value.id
        if not isinstance(env.get(name), _EmptyList):
            return False
        built.setdefault(name, set()).add(
            _row_element_value(statement.value.args[0], loop.target.id, source, env, ctx)
        )
    if not built:
        return False
    for name, values in built.items():
        if len(values) != 1:
            return False
        value = next(iter(values))
        if not isinstance(value, _Rows):
            return False
        env[name] = value
    return True


def _apply_accumulation_loop(
    loop: ast.For,
    source: _Rows,
    env: dict[str, _Value],
    ctx: _TraceContext,
    classifications: list[_Classification],
) -> bool:
    """``for row in rows: total = total * <selector>`` and its augmented form."""

    assert isinstance(loop.target, ast.Name)
    targets: set[str] = set()
    payloads: list[ast.expr] = []
    for statement in loop.body:
        if (
            isinstance(statement, ast.AugAssign)
            and isinstance(statement.target, ast.Name)
            and isinstance(statement.op, ast.Mult | ast.Add)
        ):
            targets.add(statement.target.id)
            payloads.append(statement.value)
            continue
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.BinOp)
            and isinstance(statement.value.op, ast.Mult | ast.Add)
        ):
            name = statement.targets[0].id
            operands = (statement.value.left, statement.value.right)
            if any(isinstance(item, ast.Name) and item.id == name for item in operands):
                targets.add(name)
                payloads.extend(
                    item
                    for item in operands
                    if not (isinstance(item, ast.Name) and item.id == name)
                )
                continue
        return False
    if not targets or any(not isinstance(env.get(name), _Scalar) for name in targets):
        return False
    if targets & ctx.reaching:
        for payload in payloads:
            for compare in _selector_comparisons(payload):
                _classify_compare(compare, loop.target.id, source, env, ctx, classifications)
    for name in targets:
        env[name] = _Scalar()
    return True


def _apply_recognized_repair_if(
    statement: ast.stmt, env: dict[str, _Value], ctx: _TraceContext
) -> bool:
    """``if <cross-panel comparison>: rows = <involuted rows>``."""

    if not isinstance(statement, ast.If) or statement.orelse or _is_main_guard(statement):
        return False
    body = statement.body
    if len(body) != 1:
        return False
    assign = body[0]
    if not (
        isinstance(assign, ast.Assign)
        and len(assign.targets) == 1
        and isinstance(assign.targets[0], ast.Name)
    ):
        return False
    value = _tag(assign.value, env, ctx)
    if not isinstance(value, _Rows):
        return False
    if not _guard_is_cross_panel(statement.test, env, ctx):
        # A repair conditioned on anything but a measured cross-panel
        # comparison is a branch this library cannot resolve statically.
        return False
    env[assign.targets[0].id] = value
    _mark_recognized(statement, ctx)
    return True


def _guard_is_cross_panel(test: ast.expr, env: dict[str, _Value], ctx: _TraceContext) -> bool:
    if _expression_has_cross_panel(test, env, ctx):
        return True
    for node in ast.walk(test):
        value = env.get(node.id) if isinstance(node, ast.Name) else None
        if isinstance(value, _Scalar) and value.cross_panel:
            return True
    return False


def _expression_has_cross_panel(
    expression: ast.expr, env: dict[str, _Value], ctx: _TraceContext
) -> bool:
    """Whether an expression measures agreement between two panel columns."""

    for node in ast.walk(expression):
        if not isinstance(node, ast.ListComp | ast.GeneratorExp):
            continue
        if len(node.generators) != 1:
            continue
        generator = node.generators[0]
        if not isinstance(generator.target, ast.Name):
            continue
        source = _tag(generator.iter, env, ctx)
        if not isinstance(source, _Rows):
            continue
        loop_var = generator.target.id
        for candidate in (node.elt, *generator.ifs):
            for inner in ast.walk(candidate):
                if not isinstance(inner, ast.Compare) or len(inner.ops) != 1:
                    continue
                if not isinstance(inner.ops[0], ast.Eq | ast.NotEq):
                    continue
                left = _column_parity(inner.left, loop_var=loop_var, carriers={}, env=env, ctx=ctx)
                right = _column_parity(
                    inner.comparators[0], loop_var=loop_var, carriers={}, env=env, ctx=ctx
                )
                if left is None or right is None or not left.resolved or not right.resolved:
                    continue
                if left.column != right.column:
                    return True
    return False


def _mark_recognized(statement: ast.stmt, ctx: _TraceContext) -> None:
    for node in ast.walk(statement):
        ctx.recognized_ids.add(id(node))


# ---------------------------------------------------------------------------
# Report reachability and control-flow bounds.
#
# Copied from ``quantity_dataflow_adapter`` so the two recognizers stay
# independently versionable; see this module's docstring.


def _accumulated_comprehension_ids(tree: ast.Module) -> set[int]:
    """Comprehensions whose elements a product or sum accumulates."""

    ids: set[int] = set()
    assigned: dict[str, list[ast.expr]] = {}
    consumed: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and _call_name(node) in _ACCUMULATOR_CALLS
            and len(node.args) == 1
        ):
            argument = node.args[0]
            if isinstance(argument, ast.GeneratorExp | ast.ListComp):
                ids.add(id(argument))
            elif isinstance(argument, ast.Name):
                consumed.add(argument.id)
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.GeneratorExp | ast.ListComp)
        ):
            assigned.setdefault(node.targets[0].id, []).append(node.value)
    for name in consumed:
        for comprehension in assigned.get(name, []):
            ids.add(id(comprehension))
    return ids


def _walk_skipping_lambdas(statement: ast.AST) -> list[ast.AST]:
    found: list[ast.AST] = []
    stack: list[ast.AST] = [statement]
    while stack:
        node = stack.pop()
        found.append(node)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Lambda):
                continue
            stack.append(child)
    return found


def _write_payloads(node: ast.AST) -> list[ast.expr]:
    payloads: list[ast.expr] = []
    for inner in ast.walk(node):
        if (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr in _WRITE_METHODS
            and inner.args
        ):
            payloads.append(inner.args[0])
    return payloads


def _report_reaching_names(tree: ast.Module, functions: dict[str, ast.FunctionDef]) -> set[str]:
    """Names whose values can flow into a written report payload.

    This is a permit gate only. Widening it can admit a comparison that never
    reaches the report, which costs an abstention, and can never change which
    orientation a classified comparison reports.
    """

    dependencies: dict[str, set[str]] = {}
    seeds: set[str] = set()

    def _depend(target: str, values: list[ast.expr]) -> None:
        free: set[str] = set()
        for value in values:
            free.update(name.id for name in ast.walk(value) if isinstance(name, ast.Name))
        dependencies.setdefault(target, set()).update(free)

    def _collect_edge(node: ast.AST) -> None:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            _depend(node.targets[0].id, [node.value])
            return
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        ):
            if node.func.attr in {"append", "extend"}:
                _depend(node.func.value.id, list(node.args))
            elif node.func.attr == "insert":
                _depend(node.func.value.id, list(node.args[1:]))
            return
        if (
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and isinstance(node.op, ast.Add | ast.Mult)
        ):
            _depend(node.target.id, [node.value])

    def _collect(statements: list[ast.stmt]) -> None:
        for statement in _flatten_statements(statements):
            for payload in _write_payloads(statement):
                for name in ast.walk(payload):
                    if isinstance(name, ast.Name):
                        seeds.add(name.id)
            if isinstance(statement, ast.Return) and statement.value is not None:
                for name in ast.walk(statement.value):
                    if isinstance(name, ast.Name):
                        seeds.add(name.id)
        for statement in statements:
            for node in ast.walk(statement):
                _collect_edge(node)

    _collect([item for item in tree.body if not isinstance(item, ast.FunctionDef)])
    for function in functions.values():
        _collect(function.body)

    reaching = set(seeds)
    changed = True
    while changed:
        changed = False
        for target, free in dependencies.items():
            if target in reaching and not free <= reaching:
                reaching.update(free)
                changed = True
    return reaching


def _has_unsupported_flow(tree: ast.Module, recognized_ids: set[int]) -> bool:
    for node in ast.walk(tree):
        if id(node) in recognized_ids:
            continue
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


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return f"{node.func.value.id}.{node.func.attr}"
    if isinstance(node.func, ast.Name):
        return node.func.id
    return ""


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
