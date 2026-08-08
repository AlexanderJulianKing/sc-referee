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
- Any guarded rebinding of a row set leaves the document unsupported. A
  branch decides at run time which panel the emission reads, and no static
  reading of the guard can settle that, so v2.0.1 recognizes no conditional
  repair at all.
- A report-reaching accumulation whose element compares two staged columns
  but whose selector this library cannot read leaves the document
  unsupported. Skipping it would let an unrelated recognized comparison
  elsewhere answer for it.
- Names that alias one runtime row set share an invalidation group: mutating
  any member drops the provenance of every member. Any assignment form the
  environment model does not fully handle, touching any tagged name, leaves
  the document unsupported.
- A local function definition shadows the built-in reader vocabulary, and a
  callable name that is rebound anywhere is opaque everywhere.
- Only equalities whose selected probability can reach the written report
  classify. A report write counts only when its receiver is a filesystem
  path, and a return statement seeds the report only from a function some
  reachable caller actually calls.
- Equalities reaching the report with conflicting classifications abstain.
- Helper tracing is depth-bounded with cycle detection, and expression
  tracing carries its own depth bound; recursion abstains instead of
  crashing.
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
_MAX_EXPRESSION_DEPTH = 100
_READER_CALLS = {"csv.DictReader", "csv.reader", "DictReader", "reader"}
_PATH_CALLS = {"Path", "pathlib.Path", "PurePath", "pathlib.PurePath"}
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
        "grammar_version": "2.0.0",
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
            (
                "dict literals and dict-spread literals rebuilding a row, read "
                "strictly left to right so a later entry overrides an earlier one"
            ),
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
            "not recognized; any guarded rebinding of a row set, whether by an "
            "if statement or by a conditional expression choosing between row "
            "sets, leaves the document unsupported"
        ),
        "control_flow": (
            "straight-line assignments, comprehensions, with-blocks, functions, "
            "the __main__ guard, and recognized accumulation and row-building "
            "loops; every other branch or loop leaves the document unsupported"
        ),
        "function_support": (
            "straight-line bodies whose first top-level return is the last "
            "statement; positional and keyword call binding; local definitions "
            "shadow the reader vocabulary and a rebound callable name is opaque "
            "everywhere; depth-bounded with cycle detection"
        ),
        "assignment_support": (
            "single-name assignment only; names bound to one another share an "
            "invalidation group, and any other assignment form touching a "
            "tagged name leaves the document unsupported"
        ),
        "report_reachability": (
            "a write whose receiver resolves to a filesystem path, or a return "
            "from a function some reachable caller calls"
        ),
        "soundness": [
            "direct is never a fallthrough",
            "unrecognized operand-path transforms abstain",
            "joint operand inversions compose to the direct reading only when proven",
            "off-path inversions never classify",
            "unrecognized report-reaching emission selectors abstain",
            "aliased row sets share mutation invalidation",
            "unhandled assignment forms touching tagged names abstain",
            "guarded row-set rebinding abstains",
            "report-reaching value linkage",
            "conflicting classifications abstain",
            "bounded call depth with cycle abstention",
            "bounded expression-tracing depth",
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
    pass


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
    opaque_callables: frozenset[str] = frozenset()
    path_names: frozenset[str] = frozenset()
    accumulated: set[int] = field(default_factory=set)
    reaching: set[str] = field(default_factory=set)
    depth: int = 0
    expression_depth: int = 0
    visiting: set[str] = field(default_factory=set)
    recognized_ids: set[int] = field(default_factory=set)
    unresolved: bool = False


class _Aliases:
    """Names that are known to reference one runtime row-set object.

    A plain ``alias = rows`` binds two names to the same list, so mutating
    either one invalidates the provenance of both. Groups are per scope and
    are broken as soon as a member is rebound to something else.
    """

    def __init__(self, groups: dict[str, set[str]] | None = None) -> None:
        self._groups: dict[str, set[str]] = groups or {}

    def copy(self) -> _Aliases:
        copied: dict[str, set[str]] = {}
        for group in self._groups.values():
            shared = set(group)
            for name in shared:
                copied[name] = shared
        return _Aliases(copied)

    def group(self, name: str) -> set[str]:
        return set(self._groups.get(name, {name}))

    def detach(self, name: str) -> None:
        group = self._groups.pop(name, None)
        if group is not None:
            group.discard(name)

    def link(self, name: str, other: str) -> None:
        merged = self._groups.get(name, {name}) | self._groups.get(other, {other})
        merged = set(merged)
        for member in merged:
            self._groups[member] = merged


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
    called = _called_function_names(tree, functions)
    path_names = _path_like_names(tree)
    ctx = _TraceContext(
        functions=functions,
        opaque_callables=frozenset(_rebound_names(tree) & set(functions)),
        path_names=path_names,
        accumulated=_accumulated_comprehension_ids(tree),
        reaching=_report_reaching_names(tree, functions, path_names, called),
    )
    classifications: list[_Classification] = []

    module_env: dict[str, _Value] = {}
    module_aliases = _Aliases()
    _scan_scope(
        [item for item in tree.body if not isinstance(item, ast.FunctionDef)],
        module_env,
        module_aliases,
        ctx,
        classifications,
        returns_reach=False,
    )
    for function in functions.values():
        # Function bodies are scanned with parameters masked, so a module
        # global can never stand in for an unbound parameter.
        env: dict[str, _Value] = dict(module_env)
        aliases = module_aliases.copy()
        for parameter in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        ):
            aliases.detach(parameter.arg)
            env[parameter.arg] = _OPAQUE
        _scan_scope(
            function.body,
            env,
            aliases,
            ctx,
            classifications,
            returns_reach=function.name in called,
        )

    return {
        "classifications": classifications,
        "unsupported": ctx.unresolved or _has_unsupported_flow(tree, ctx.recognized_ids),
    }


def _scan_scope(
    statements: list[ast.stmt],
    env: dict[str, _Value],
    aliases: _Aliases,
    ctx: _TraceContext,
    classifications: list[_Classification],
    *,
    returns_reach: bool,
) -> None:
    for statement in _flatten_statements(statements):
        if _apply_recognized_loop(statement, env, ctx, classifications):
            continue
        if _statement_reaches(statement, ctx, returns_reach=returns_reach):
            for node in _walk_skipping_lambdas(statement):
                if (
                    isinstance(node, ast.ListComp | ast.GeneratorExp)
                    and id(node) in ctx.accumulated
                ):
                    _classify_comprehension(node, env, ctx, classifications)
        _invalidate_mutations(statement, env, aliases)
        _apply_assign(statement, env, aliases, ctx)


def _statement_reaches(statement: ast.stmt, ctx: _TraceContext, *, returns_reach: bool) -> bool:
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    ):
        return statement.targets[0].id in ctx.reaching
    if isinstance(statement, ast.Expr) and _write_payloads(statement.value, ctx.path_names):
        return True
    return returns_reach and isinstance(statement, ast.Return)


def _bind(name: str, value: _Value, env: dict[str, _Value], aliases: _Aliases) -> None:
    aliases.detach(name)
    env[name] = value


def _invalidate_group(name: str, env: dict[str, _Value], aliases: _Aliases) -> None:
    for member in aliases.group(name):
        env[member] = _OPAQUE


def _tagged(name: str, env: dict[str, _Value], aliases: _Aliases) -> bool:
    return any(isinstance(env.get(member), _Rows) for member in aliases.group(name))


def _statement_touches_tagged(
    statement: ast.stmt, env: dict[str, _Value], aliases: _Aliases
) -> bool:
    return any(
        isinstance(node, ast.Name) and _tagged(node.id, env, aliases)
        for node in ast.walk(statement)
    )


def _target_names(target: ast.expr) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names


def _apply_assign(
    statement: ast.stmt, env: dict[str, _Value], aliases: _Aliases, ctx: _TraceContext
) -> None:
    """Update the environment for one assignment, or abstain for the document.

    Only a single ``Name`` target is modelled exactly. Every other assignment
    form -- tuple or starred targets, chained targets, subscript and slice
    targets, annotated targets, augmented assignment, and the walrus operator
    -- leaves the document unsupported as soon as it touches a name whose row
    provenance is tagged, because the environment cannot follow it.
    """

    if not isinstance(statement, ast.Assign | ast.AugAssign | ast.AnnAssign):
        return
    walrus = any(isinstance(node, ast.NamedExpr) for node in ast.walk(statement))
    simple = (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and not walrus
    )
    if not simple:
        if _statement_touches_tagged(statement, env, aliases):
            ctx.unresolved = True
        targets: list[ast.expr] = (
            list(statement.targets) if isinstance(statement, ast.Assign) else [statement.target]
        )
        for target in targets:
            for name in _target_names(target):
                _invalidate_group(name, env, aliases)
                _bind(name, _OPAQUE, env, aliases)
        return
    assert isinstance(statement, ast.Assign)
    target = statement.targets[0]
    assert isinstance(target, ast.Name)
    if _is_row_set_conditional(statement.value, env, ctx):
        # A branch decides at run time which panel the name holds; no static
        # reading of the guard settles it.
        ctx.unresolved = True
        _bind(target.id, _OPAQUE, env, aliases)
        return
    value = _tag(statement.value, env, ctx)
    _bind(target.id, value, env, aliases)
    if isinstance(statement.value, ast.Name) and isinstance(value, _Rows):
        aliases.link(target.id, statement.value.id)


def _is_row_set_conditional(value: ast.expr, env: dict[str, _Value], ctx: _TraceContext) -> bool:
    """A conditional expression choosing between row sets."""

    if not isinstance(value, ast.IfExp):
        return False
    return isinstance(_tag(value.body, env, ctx), _Rows) or isinstance(
        _tag(value.orelse, env, ctx), _Rows
    )


def _invalidate_mutations(statement: ast.stmt, env: dict[str, _Value], aliases: _Aliases) -> None:
    """Drop provenance for row sets a statement mutates or deletes from.

    Every name that aliases the mutated object loses its provenance too: the
    runtime list is one object, and the syntactic receiver is only one of its
    names.
    """

    for node in ast.walk(statement):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.attr in _MUTATING_METHODS
        ):
            _invalidate_group(node.func.value.id, env, aliases)
        elif isinstance(node, ast.Delete):
            for item in node.targets:
                inner: ast.expr = item
                while isinstance(inner, ast.Subscript):
                    inner = inner.value
                if isinstance(inner, ast.Name):
                    _invalidate_group(inner.id, env, aliases)


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
    source = _tag(generator.iter, env, ctx)
    _flag_unrecognized_selectors(node.elt, selectors, generator.target.id, env, ctx)
    if not selectors:
        return
    for compare in selectors:
        _classify_compare(compare, generator.target.id, source, env, ctx, classifications)


def _flag_unrecognized_selectors(
    element: ast.expr,
    selectors: list[ast.Compare],
    loop_var: str,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> None:
    """Abstain for the document when an emission-like selector is unreadable.

    A report-reaching accumulation whose element compares two staged columns
    is an emission selector whatever it selects between. If this library
    cannot read the selected values, skipping the accumulation would let a
    recognized comparison elsewhere -- a match count over a different panel,
    say -- answer in its place.
    """

    recognized = {id(item) for item in selectors}
    for node in ast.walk(element):
        if not isinstance(node, ast.Compare) or id(node) in recognized:
            continue
        if _is_emission_like_comparison(node, loop_var, env, ctx):
            ctx.unresolved = True
            return


def _is_emission_like_comparison(
    compare: ast.Compare,
    loop_var: str,
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> bool:
    if len(compare.ops) != 1 or not isinstance(compare.ops[0], ast.Eq | ast.NotEq):
        return False
    left = _column_parity(compare.left, loop_var=loop_var, carriers={}, env=env, ctx=ctx)
    right = _column_parity(compare.comparators[0], loop_var=loop_var, carriers={}, env=env, ctx=ctx)
    if left is None or right is None:
        return False
    return not (left.resolved and right.resolved and left.column == right.column)


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


_EXACT_NUMERIC_CALLS = {
    "Fraction",
    "fractions.Fraction",
    "Decimal",
    "decimal.Decimal",
}


def _numeric_like(node: ast.expr, depth: int = 0) -> bool:
    """A numeric emission probability: a literal, a name, or arithmetic over them.

    ``Fraction(99, 100)`` and ``Decimal("0.99")`` are ordinary stdlib ways of
    writing an emission probability, so they read as numeric here; leaving
    them out made a legitimate emission selector invisible.
    """

    if depth >= _MAX_EXPRESSION_DEPTH:
        return False
    if isinstance(node, ast.Constant):
        return isinstance(node.value, int | float) and not isinstance(node.value, bool)
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.UnaryOp):
        return _numeric_like(node.operand, depth + 1)
    if isinstance(node, ast.BinOp):
        return _numeric_like(node.left, depth + 1) and _numeric_like(node.right, depth + 1)
    if isinstance(node, ast.Call) and not node.keywords:
        name = _call_name(node)
        if name in _EXACT_NUMERIC_CALLS:
            return (
                bool(node.args)
                and len(node.args) <= 2
                and all(_numeric_argument(item, depth + 1) for item in node.args)
            )
        if name in {"float", "int"}:
            return len(node.args) == 1 and _numeric_like(node.args[0], depth + 1)
    return False


def _numeric_argument(node: ast.expr, depth: int) -> bool:
    """A numeric constructor argument, including the decimal string form."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        try:
            float(node.value)
        except ValueError:
            return False
        return True
    return _numeric_like(node, depth)


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

    The recursion carries an explicit depth bound: a long enough composed
    expression would otherwise exhaust the interpreter stack, and abstaining
    beyond the bound is the only sound answer.
    """

    if ctx.expression_depth >= _MAX_EXPRESSION_DEPTH:
        return _UNRESOLVED
    ctx.expression_depth += 1
    try:
        return _column_parity_inner(
            expression, loop_var=loop_var, carriers=carriers, env=env, ctx=ctx
        )
    finally:
        ctx.expression_depth -= 1


def _column_parity_inner(
    expression: ast.expr,
    *,
    loop_var: str | None,
    carriers: dict[str, _Path],
    env: dict[str, _Value],
    ctx: _TraceContext,
) -> _Path | None:
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
    if name in ctx.opaque_callables:
        # The name is rebound somewhere in the module, so which body runs here
        # is a runtime question.
        return None
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
    if not _straight_line_helper(function):
        return _UNRESOLVED
    ctx.depth += 1
    ctx.visiting.add(function.name)
    try:
        local = dict(carried)
        statements = _flatten_statements(function.body)
        for index, statement in enumerate(statements):
            if isinstance(statement, ast.Return):
                # Statements after the first return are dead code the value
                # never sees, and a body that keeps going is not the
                # straight line this analysis assumes.
                if statement.value is None or index != len(statements) - 1:
                    return _UNRESOLVED
                path = _column_parity(
                    statement.value, loop_var=None, carriers=local, env=env, ctx=ctx
                )
                if path is None or not path.resolved:
                    return _UNRESOLVED
                return _Path(str(path.column), path.parity % 2)
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
                continue
            if isinstance(statement, ast.Pass):
                continue
            return _UNRESOLVED
        return _UNRESOLVED
    finally:
        ctx.depth -= 1
        ctx.visiting.discard(function.name)


def _straight_line_helper(function: ast.FunctionDef) -> bool:
    """A helper body free of walrus bindings and side-effecting statements."""

    for node in ast.walk(function):
        if isinstance(node, ast.NamedExpr):
            return False
    for statement in _flatten_statements(function.body):
        if isinstance(statement, ast.Expr) and not isinstance(statement.value, ast.Constant):
            # A bare expression statement exists for its side effect; only a
            # docstring is inert.
            return False
    return True


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
    if ctx.expression_depth >= _MAX_EXPRESSION_DEPTH:
        return _OPAQUE
    ctx.expression_depth += 1
    try:
        return _tag_inner(node, env, ctx)
    finally:
        ctx.expression_depth -= 1


def _tag_inner(node: ast.expr, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
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
        return _Scalar()
    return _OPAQUE


def _tag_call(node: ast.Call, env: dict[str, _Value], ctx: _TraceContext) -> _Value:
    name = _call_name(node)
    if name in ctx.opaque_callables:
        return _OPAQUE
    if isinstance(node.func, ast.Name) and node.func.id in env:
        # The callable name is bound to a value this trace is following, so
        # the built-in vocabulary below does not describe it.
        return _OPAQUE
    if name in ctx.functions:
        # A project definition shadows the reader vocabulary; its body, not
        # its name, says what it returns.
        return _bound_return_value(ctx.functions[name], node, env, ctx)
    if name in _READER_CALLS:
        return _Rows(iterator=True)
    if name == "list" and len(node.args) == 1 and not node.keywords:
        inner = _tag(node.args[0], env, ctx)
        if isinstance(inner, _Rows):
            return _Rows(inner.overrides, inner.default_identity, iterator=False)
        return _OPAQUE
    if name in _ACCUMULATOR_CALLS or name in {"len"}:
        return _Scalar()
    if name in _IDENTITY_CASTS and len(node.args) == 1 and not node.keywords:
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
    """The row set a per-row element expression builds, or opaque.

    Dict construction is order-sensitive: ``{"founder": ..., **row}`` keeps
    the spread's value for ``founder`` and ``{**row, "founder": ...}`` keeps
    the explicit one. Entries are therefore applied strictly left to right,
    and a later spread overwrites an earlier explicit key with whatever that
    spread carries -- opaque when the spread's own contents do not say.
    """

    if isinstance(element, ast.Name) and element.id == loop_var:
        return _Rows(source.overrides, source.default_identity, iterator=False)
    if not isinstance(element, ast.Dict):
        return _OPAQUE
    built: dict[str, tuple[str, int] | None] = {}
    default_identity = False
    for key, value in zip(element.keys, element.values, strict=True):
        if key is None:
            if not (isinstance(value, ast.Name) and value.id == loop_var):
                return _OPAQUE
            for existing in list(built):
                built[existing] = _rows_column(source, existing)
            built.update(dict(source.overrides))
            default_identity = source.default_identity
            continue
        if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
            return _OPAQUE
        path = _column_parity(value, loop_var=loop_var, carriers={}, env=env, ctx=ctx)
        if path is None or not path.resolved:
            built[key.value] = None
            continue
        resolved = _rows_column(source, str(path.column))
        if resolved is None:
            built[key.value] = None
            continue
        built[key.value] = (resolved[0], (resolved[1] + path.parity) % 2)
    return _Rows(
        tuple(sorted(built.items())),
        default_identity=default_identity,
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
    """The return value of a callee with its parameters bound.

    Statements are processed in order and the first top-level return decides;
    a body that continues past its return is not the straight line this
    analysis assumes and reads as opaque.
    """

    if ctx.depth >= _MAX_CALL_DEPTH or function.name in ctx.visiting:
        return _OPAQUE
    if not _straight_line_helper(function):
        return _OPAQUE
    callee_env = _bind_call(function, call, env, ctx)
    if callee_env is None:
        return _OPAQUE
    ctx.depth += 1
    ctx.visiting.add(function.name)
    try:
        callee_aliases = _Aliases()
        statements = _flatten_statements(function.body)
        for index, statement in enumerate(statements):
            if isinstance(statement, ast.Return):
                if statement.value is None or index != len(statements) - 1:
                    return _OPAQUE
                return _tag(statement.value, callee_env, ctx)
            if _apply_recognized_loop(statement, callee_env, ctx, []):
                continue
            _invalidate_mutations(statement, callee_env, callee_aliases)
            _apply_assign(statement, callee_env, callee_aliases, ctx)
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
            selectors = _selector_comparisons(payload)
            _flag_unrecognized_selectors(payload, selectors, loop.target.id, env, ctx)
            for compare in selectors:
                _classify_compare(compare, loop.target.id, source, env, ctx, classifications)
    for name in targets:
        env[name] = _Scalar()
    return True


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


def _is_path_like(node: ast.expr, path_names: set[str], depth: int = 0) -> bool:
    """Whether an expression resolves to a filesystem path or a handle on one.

    A ``StringIO`` buffer also answers to ``write``, so a diagnostic string
    written into memory would otherwise look exactly like the published
    report. Only a ``Path`` call chain, a name assigned from one, or an
    ``open`` on one counts.
    """

    if depth >= _MAX_EXPRESSION_DEPTH:
        return False
    if isinstance(node, ast.Name):
        return node.id in path_names
    if isinstance(node, ast.Call):
        name = _call_name(node)
        if name in _PATH_CALLS:
            return True
        if name == "open" and node.args:
            return _is_path_like(node.args[0], path_names, depth + 1)
        if isinstance(node.func, ast.Attribute):
            return _is_path_like(node.func.value, path_names, depth + 1)
        return False
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _is_path_like(node.left, path_names, depth + 1) or _is_path_like(
            node.right, path_names, depth + 1
        )
    if isinstance(node, ast.Attribute):
        return _is_path_like(node.value, path_names, depth + 1)
    return False


def _path_like_names(tree: ast.Module) -> frozenset[str]:
    """Names bound, directly or transitively, to a filesystem path."""

    names: set[str] = set()
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            targets: list[ast.expr] = []
            value: ast.expr | None = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                targets = [node.targets[0]]
                value = node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets = [node.target]
                value = node.value
            elif isinstance(node, ast.withitem) and node.optional_vars is not None:
                targets = [node.optional_vars]
                value = node.context_expr
            if value is None:
                continue
            for target in targets:
                if not isinstance(target, ast.Name) or target.id in names:
                    continue
                if _is_path_like(value, names):
                    names.add(target.id)
                    changed = True
    return frozenset(names)


def _rebound_names(tree: ast.Module) -> set[str]:
    """Every name any binding form in the module can rebind."""

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                names.update(_target_names(target))
        elif isinstance(node, ast.AugAssign | ast.AnnAssign):
            names.update(_target_names(node.target))
        elif isinstance(node, ast.For | ast.AsyncFor):
            names.update(_target_names(node.target))
        elif isinstance(node, ast.NamedExpr):
            names.update(_target_names(node.target))
        elif isinstance(node, ast.withitem) and node.optional_vars is not None:
            names.update(_target_names(node.optional_vars))
    return names


def _called_function_names(
    tree: ast.Module, functions: dict[str, ast.FunctionDef]
) -> frozenset[str]:
    """Module-level functions some reachable caller actually calls.

    A return statement inside a function nobody calls never delivers a value
    anywhere, so it cannot seed the report-reaching set.
    """

    frontier: set[str] = set()
    for statement in (item for item in tree.body if not isinstance(item, ast.FunctionDef)):
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and _call_name(node) in functions:
                frontier.add(_call_name(node))
    reached: set[str] = set()
    while frontier:
        name = frontier.pop()
        if name in reached:
            continue
        reached.add(name)
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Call):
                callee = _call_name(node)
                if callee in functions and callee not in reached:
                    frontier.add(callee)
    return frozenset(reached)


def _write_payloads(node: ast.AST, path_names: frozenset[str] | set[str]) -> list[ast.expr]:
    payloads: list[ast.expr] = []
    for inner in ast.walk(node):
        if (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr in _WRITE_METHODS
            and inner.args
            and _is_path_like(inner.func.value, set(path_names))
        ):
            payloads.append(inner.args[0])
    return payloads


def _report_reaching_names(
    tree: ast.Module,
    functions: dict[str, ast.FunctionDef],
    path_names: frozenset[str],
    called: frozenset[str],
) -> set[str]:
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

    def _collect(statements: list[ast.stmt], *, seed_returns: bool) -> None:
        for statement in _flatten_statements(statements):
            for payload in _write_payloads(statement, path_names):
                for name in ast.walk(payload):
                    if isinstance(name, ast.Name):
                        seeds.add(name.id)
            if seed_returns and isinstance(statement, ast.Return) and statement.value is not None:
                for name in ast.walk(statement.value):
                    if isinstance(name, ast.Name):
                        seeds.add(name.id)
        for statement in statements:
            for node in ast.walk(statement):
                _collect_edge(node)

    _collect(
        [item for item in tree.body if not isinstance(item, ast.FunctionDef)],
        seed_returns=False,
    )
    for function in functions.values():
        _collect(function.body, seed_returns=function.name in called)

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
