"""ADR-0069 static dataflow resolution of a rate's exposure denominator.

This library works backward from the division that produces the reported
rate. It reads each Python workflow source statically, tags variable
provenance (the full row set read from the staged input, a conditioned
subset produced by a filtering comprehension, and counts taken over either),
and classifies divisions whose numerator and denominator are data-derived
counts: a denominator counting the conditioned subset is the retained-subset
exposure, and a denominator counting the full row set is the complete-domain
exposure. Variable names never matter; only the operations do.

Soundness rules (each backed by a demonstrated counterexample in
``tests/test_quantity_dataflow_soundness.py``):

- Only divisions whose value can reach the written report classify;
  incidental or diagnostic divisions never become the operand.
- A helper's return tag is the join over every return statement: any
  disagreement is opaque, so a conditional early return cannot mislabel.
- Call-site binding covers positional and keyword arguments; any unbindable
  call is opaque, and module globals are masked from parameter names.
- Iterator row sources are invalidated on any consuming use before ``list``.
- A collection is invalidated when later code deletes from it, mutates it,
  or passes it to a local helper that mutates its parameter.
- Lambda bodies never classify.
- Helper tracing is depth-bounded with cycle detection; recursion abstains
  instead of crashing.

Conflicting classifications and untraceable interactions resolve to explicit
non-unique states, never to a guess.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
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

_ROW_TAGS = {_ROWS_FULL, _ROWS_SUBSET, _ROWS_ITER_FULL}
_COUNT_TAGS = {_COUNT_FULL, _COUNT_SUBSET}
_MAX_CALL_DEPTH = 2
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

_WRITE_METHODS = {"write", "writelines", "write_text"}


def quantity_dataflow_grammar(complete_operand: str, retained_operand: str) -> dict[str, Any]:
    return {
        "grammar_id": "quantity-denominator-dataflow",
        "grammar_version": "1.2.0",
        "row_source_operations": ["csv.DictReader", "csv.reader"],
        "subset_operation": "single-generator comprehension with a filter over a row set",
        "count_operations": ["len(rows)", "sum(1 for ... in rows [if ...])"],
        "division_forms": ["a / b", "Fraction(a, b)"],
        "function_support": (
            "straight-line bodies; positional and keyword call binding; return "
            "tags joined over every return; depth-bounded with cycle detection"
        ),
        "division_rule": (
            "a division with a data-derived count numerator classifies by its "
            "denominator's provenance, and only when its value can reach the "
            "written report"
        ),
        "operand_by_denominator": {
            "count_of_full_row_set": complete_operand,
            "count_of_screened_subset": retained_operand,
        },
        "control_flow": (
            "straight-line assignments, comprehensions, with-blocks, functions, "
            "the __main__ guard, and provenance-disjoint loops or conditionals"
        ),
        "soundness": [
            "report-reaching value linkage",
            "return-tag join over all returns",
            "keyword-aware call binding with masked globals",
            "iterator consumption invalidation",
            "collection mutation and deletion invalidation, including through "
            "local-helper aliasing",
            "lambda bodies never classify",
            "bounded call depth with cycle abstention",
        ],
        "nomenclature_authority": "none",
    }


def quantity_dataflow_grammar_digest(complete_operand: str, retained_operand: str) -> str:
    return semantic_digest(quantity_dataflow_grammar(complete_operand, retained_operand))


@dataclass(frozen=True)
class _Division:
    node: ast.AST
    operand_value: str


@dataclass(frozen=True)
class DataflowResolution:
    """The outcome of the bounded source trace across every Python document."""

    state: str  # "unique" | "none" | "ambiguous" | "unsupported"
    operand_value: str | None
    spans: tuple[EvidenceSpan, ...]
    source_path: str | None


@dataclass
class _TraceContext:
    functions: dict[str, ast.FunctionDef]
    returns: dict[str, str] = field(default_factory=dict)
    depth: int = 0
    visiting: set[str] = field(default_factory=set)


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
        # A resolved division next to untraceable interacting control flow
        # could be rebound by that flow; report unsupported rather than guess.
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


# ---------------------------------------------------------------------------
# The per-document trace engine.


def _document_divisions(
    tree: ast.Module, *, complete_operand: str, retained_operand: str
) -> dict[str, Any]:
    """Trace report-reaching divisions across the module and function scopes."""

    unsupported_flow = _has_unsupported_flow(tree)
    functions: dict[str, ast.FunctionDef] = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    ctx = _TraceContext(functions=functions)
    for _ in range(3):
        for name, function in functions.items():
            ctx.returns[name] = _function_return_tag(function, ctx)
    mutated_params = _mutating_parameter_names(functions)
    reaching = _report_reaching_names(tree, functions)

    divisions: list[_Division] = []
    any_division = False

    def _classify(node: ast.AST, env: dict[str, str]) -> None:
        nonlocal any_division
        pair = _division_operands(node)
        if pair is None:
            return
        any_division = True
        numerator = _numerator_tag(pair[0], env, ctx)
        denominator = _tag(pair[1], env, ctx)
        if numerator in _COUNT_TAGS and denominator in _COUNT_TAGS:
            divisions.append(
                _Division(
                    node=node,
                    operand_value=(
                        retained_operand if denominator == _COUNT_SUBSET else complete_operand
                    ),
                )
            )

    def _statement_reaches(statement: ast.stmt) -> bool:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            return statement.targets[0].id in reaching
        if isinstance(statement, ast.Expr) and _write_payloads(statement.value):
            return True
        if isinstance(statement, ast.Return):
            return True
        return False

    def _scan_callee(call: ast.Call, env: dict[str, str]) -> None:
        function = ctx.functions.get(_call_name(call))
        if function is None or ctx.depth >= _MAX_CALL_DEPTH:
            return
        if function.name in ctx.visiting:
            return
        callee_env = _bind_call(function, call, env, ctx)
        if callee_env is None:
            return
        ctx.depth += 1
        ctx.visiting.add(function.name)
        try:
            for statement in _flatten_statements(function.body):
                for node in _walk_skipping_lambdas(statement):
                    _classify(node, callee_env)
                    if isinstance(node, ast.Call) and node is not call:
                        _scan_callee(node, callee_env)
                if (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                ):
                    callee_env[statement.targets[0].id] = _tag(statement.value, callee_env, ctx)
        finally:
            ctx.depth -= 1
            ctx.visiting.discard(function.name)

    def _scan_scope(statements: list[ast.stmt], env: dict[str, str]) -> bool:
        saw_read = False
        for statement in _flatten_statements(statements):
            reaches = _statement_reaches(statement)
            for node in _walk_skipping_lambdas(statement):
                if reaches:
                    _classify(node, env)
                    if isinstance(node, ast.Call):
                        _scan_callee(node, env)
                _invalidate_consumed(node, env)
            _invalidate_mutations(statement, env, mutated_params)
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                tag = _tag(statement.value, env, ctx)
                env[statement.targets[0].id] = tag
                if tag in {_ROWS_FULL, _ROWS_ITER_FULL}:
                    saw_read = True
        return saw_read

    module_env: dict[str, str] = {}
    read_present = _scan_scope(
        [s for s in tree.body if not isinstance(s, ast.FunctionDef)], module_env
    )
    for function in functions.values():
        # Function bodies are scanned with parameters masked, so a module
        # global can never stand in for an unbound parameter.
        env = dict(module_env)
        for parameter in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        ):
            env[parameter.arg] = _OTHER
        if _scan_scope(function.body, env):
            read_present = True
    if unsupported_flow and divisions:
        # Control flow that never rebinds or mutates any quantity-tagged name
        # (or any name a division reads) cannot change the divisions'
        # provenance; table-building and formatting loops are the common
        # case. Any overlap keeps the document unsupported.
        touched = _names_touched_in_flow(tree)
        provenance = {name for name, tag in module_env.items() if tag != _OTHER}
        for function in functions.values():
            env = dict(module_env)
            for statement in _flatten_statements(function.body):
                if (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                ):
                    tag = _tag(statement.value, env, ctx)
                    env[statement.targets[0].id] = tag
                    if tag != _OTHER:
                        provenance.add(statement.targets[0].id)
        for item in divisions:
            pair = _division_operands(item.node)
            if pair is not None:
                for operand in pair:
                    for name in ast.walk(operand):
                        if isinstance(name, ast.Name):
                            provenance.add(name.id)
        if not (touched & provenance):
            unsupported_flow = False
    return {
        "divisions": divisions,
        "triggered": read_present and any_division,
        "unsupported_flow": unsupported_flow,
    }


def _walk_skipping_lambdas(statement: ast.AST) -> list[ast.AST]:
    """Walk a statement's tree without descending into lambda bodies."""

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
    """Arguments of report-writing calls within one expression."""

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

    Seeds are the free names of every write-call payload and of every return
    value (a returned value may be written by the caller); the closure
    follows straight-line assignments backward, so a division assigned to a
    diagnostic that is never written can never classify.
    """

    dependencies: dict[str, set[str]] = {}
    seeds: set[str] = set()

    def _collect(statements: list[ast.stmt]) -> None:
        for statement in _flatten_statements(statements):
            for payload in _write_payloads(statement):
                for name in ast.walk(payload):
                    if isinstance(name, ast.Name):
                        seeds.add(name.id)
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                free = {name.id for name in ast.walk(statement.value) if isinstance(name, ast.Name)}
                dependencies.setdefault(statement.targets[0].id, set()).update(free)
            if isinstance(statement, ast.Return) and statement.value is not None:
                for name in ast.walk(statement.value):
                    if isinstance(name, ast.Name):
                        seeds.add(name.id)

    _collect([s for s in tree.body if not isinstance(s, ast.FunctionDef)])
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


def _bind_call(
    function: ast.FunctionDef,
    call: ast.Call,
    env: dict[str, str],
    ctx: _TraceContext,
) -> dict[str, str] | None:
    """Parameter environment for a call, or None when unbindable."""

    if (
        function.args.posonlyargs
        or function.args.kwonlyargs
        or function.args.vararg
        or function.args.kwarg
    ):
        return None
    parameters = [parameter.arg for parameter in function.args.args]
    if len(call.args) > len(parameters):
        return None
    bound: dict[str, str] = {}
    for parameter, argument in zip(parameters, call.args, strict=False):
        bound[parameter] = _tag(argument, env, ctx)
    for keyword in call.keywords:
        if keyword.arg is None or keyword.arg not in parameters or keyword.arg in bound:
            return None
        bound[keyword.arg] = _tag(keyword.value, env, ctx)
    defaults = function.args.defaults
    if defaults:
        for parameter in parameters[len(parameters) - len(defaults) :]:
            bound.setdefault(parameter, _OTHER)
    if set(bound) != set(parameters):
        return None
    return bound


def _mutating_parameter_names(
    functions: dict[str, ast.FunctionDef],
) -> dict[str, set[int]]:
    """For each local function, the positional indices of parameters it mutates."""

    result: dict[str, set[int]] = {}
    for name, function in functions.items():
        parameters = [parameter.arg for parameter in function.args.args]
        mutated: set[int] = set()
        for node in ast.walk(function):
            receiver: str | None = None
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.attr in _MUTATING_METHODS
            ):
                receiver = node.func.value.id
            elif isinstance(node, ast.Delete):
                for target in node.targets:
                    inner: ast.expr = target
                    while isinstance(inner, ast.Subscript):
                        inner = inner.value
                    if isinstance(inner, ast.Name):
                        receiver = inner.id
            elif isinstance(node, ast.AugAssign):
                inner = node.target
                while isinstance(inner, ast.Subscript):
                    inner = inner.value
                if isinstance(inner, ast.Name):
                    receiver = inner.id
            if receiver is not None and receiver in parameters:
                mutated.add(parameters.index(receiver))
        if mutated:
            result[name] = mutated
    return result


def _invalidate_consumed(node: ast.AST, env: dict[str, str]) -> None:
    """A row iterator passed to anything but list() is consumed; drop its tag."""

    if not isinstance(node, ast.Call):
        return
    if _call_name(node) == "list":
        return
    for argument in node.args:
        if isinstance(argument, ast.Name) and env.get(argument.id) == _ROWS_ITER_FULL:
            env[argument.id] = _OTHER


def _invalidate_mutations(
    statement: ast.stmt, env: dict[str, str], mutated_params: dict[str, set[int]]
) -> None:
    """Drop provenance for collections a statement mutates, deletes from, or
    passes to a local helper that mutates its parameter."""

    for node in ast.walk(statement):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.attr in _MUTATING_METHODS
            and env.get(node.func.value.id, _OTHER) != _OTHER
        ):
            env[node.func.value.id] = _OTHER
        elif isinstance(node, ast.Delete):
            for target in node.targets:
                inner: ast.expr = target
                while isinstance(inner, ast.Subscript):
                    inner = inner.value
                if isinstance(inner, ast.Name) and env.get(inner.id, _OTHER) != _OTHER:
                    env[inner.id] = _OTHER
        elif isinstance(node, ast.Call):
            callee = _call_name(node)
            for index in mutated_params.get(callee, ()):
                if index < len(node.args):
                    argument = node.args[index]
                    if isinstance(argument, ast.Name) and env.get(argument.id, _OTHER) != _OTHER:
                        env[argument.id] = _OTHER


def _names_touched_in_flow(tree: ast.Module) -> set[str]:
    """Names a loop, conditional, or try block could rebind, mutate, or delete."""

    touched: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and _is_main_guard(node):
            continue
        if not isinstance(node, ast.For | ast.AsyncFor | ast.While | ast.If | ast.Try):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Assign):
                for target in inner.targets:
                    for name in ast.walk(target):
                        if isinstance(name, ast.Name):
                            touched.add(name.id)
            elif isinstance(inner, ast.AugAssign):
                target = inner.target
                while isinstance(target, ast.Subscript):
                    target = target.value
                if isinstance(target, ast.Name):
                    touched.add(target.id)
            elif isinstance(inner, ast.For | ast.AsyncFor):
                for name in ast.walk(inner.target):
                    if isinstance(name, ast.Name):
                        touched.add(name.id)
            elif isinstance(inner, ast.Delete):
                for target in inner.targets:
                    resolved: ast.expr = target
                    while isinstance(resolved, ast.Subscript):
                        resolved = resolved.value
                    if isinstance(resolved, ast.Name):
                        touched.add(resolved.id)
            elif (
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Attribute)
                and isinstance(inner.func.value, ast.Name)
                and inner.func.attr in _MUTATING_METHODS
            ):
                touched.add(inner.func.value.id)
    return touched


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


def _function_return_tag(function: ast.FunctionDef, ctx: _TraceContext) -> str:
    """The join of every return's tag; disagreement or recursion is opaque."""

    if function.name in ctx.visiting:
        return _OTHER
    ctx.visiting.add(function.name)
    try:
        env: dict[str, str] = {
            parameter.arg: _OTHER
            for parameter in (
                *function.args.posonlyargs,
                *function.args.args,
                *function.args.kwonlyargs,
            )
        }
        for statement in _flatten_statements(function.body):
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                env[statement.targets[0].id] = _tag(statement.value, env, ctx)
        tags: set[str] = set()
        for node in ast.walk(function):
            if isinstance(node, ast.Return) and node.value is not None:
                tags.add(_tag(node.value, env, ctx))
        if len(tags) == 1:
            return next(iter(tags))
        return _OTHER
    finally:
        ctx.visiting.discard(function.name)


def _bound_return_tag(
    function: ast.FunctionDef,
    call: ast.Call,
    env: dict[str, str],
    ctx: _TraceContext,
) -> str:
    """Return tag of a callee with parameters bound to the caller's argument
    tags; the join over every return, depth-bounded and cycle-safe."""

    if ctx.depth >= _MAX_CALL_DEPTH or function.name in ctx.visiting:
        return _OTHER
    callee_env = _bind_call(function, call, env, ctx)
    if callee_env is None:
        return _OTHER
    ctx.depth += 1
    ctx.visiting.add(function.name)
    try:
        for statement in _flatten_statements(function.body):
            if (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                callee_env[statement.targets[0].id] = _tag(statement.value, callee_env, ctx)
        tags: set[str] = set()
        for node in ast.walk(function):
            if isinstance(node, ast.Return) and node.value is not None:
                tags.add(_tag(node.value, callee_env, ctx))
        if len(tags) == 1:
            return next(iter(tags))
        return _OTHER
    finally:
        ctx.depth -= 1
        ctx.visiting.discard(function.name)


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


def _numerator_tag(node: ast.expr, env: dict[str, str], ctx: _TraceContext) -> str:
    """The numerator may carry a constant scale factor (100 * events)."""

    tag = _tag(node, env, ctx)
    if tag in _COUNT_TAGS:
        return tag
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        left = _tag(node.left, env, ctx)
        right = _tag(node.right, env, ctx)
        counts = {left, right} & _COUNT_TAGS
        others = {left, right} - counts
        if len(counts) == 1 and others <= {_INT_OTHER}:
            return next(iter(counts))
    return tag


def _tag(node: ast.expr, env: dict[str, str], ctx: _TraceContext) -> str:
    if isinstance(node, ast.Name):
        return env.get(node.id, _OTHER)
    if isinstance(node, ast.Constant):
        return _INT_OTHER if isinstance(node.value, (int, float)) else _OTHER
    if isinstance(node, ast.Call):
        return _tag_call(node, env, ctx)
    if isinstance(node, ast.ListComp | ast.GeneratorExp):
        return _tag_comprehension(node, env, ctx)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add | ast.Sub | ast.Mult):
        left = _tag(node.left, env, ctx)
        right = _tag(node.right, env, ctx)
        numericish = _COUNT_TAGS | {_INT_OTHER}
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


def _tag_call(node: ast.Call, env: dict[str, str], ctx: _TraceContext) -> str:
    name = _call_name(node)
    if name in {"csv.DictReader", "csv.reader", "DictReader", "reader"}:
        return _ROWS_ITER_FULL
    if name in ctx.functions:
        if not node.args and not node.keywords:
            return ctx.returns.get(name, _OTHER)
        return _bound_return_tag(ctx.functions[name], node, env, ctx)
    if name == "list" and len(node.args) == 1:
        inner = _tag(node.args[0], env, ctx)
        if inner in {_ROWS_ITER_FULL, _ROWS_FULL}:
            return _ROWS_FULL
        if inner == _ROWS_SUBSET:
            return _ROWS_SUBSET
        return _OTHER
    if name == "len" and len(node.args) == 1:
        inner = _tag(node.args[0], env, ctx)
        if inner == _ROWS_FULL:
            return _COUNT_FULL
        if inner == _ROWS_SUBSET:
            return _COUNT_SUBSET
        return _OTHER
    if name == "sum" and len(node.args) == 1:
        argument = node.args[0]
        if isinstance(argument, ast.GeneratorExp | ast.ListComp):
            return _tag_counting_comprehension(argument, env, ctx)
        return _OTHER
    return _OTHER


def _tag_comprehension(
    node: ast.ListComp | ast.GeneratorExp, env: dict[str, str], ctx: _TraceContext
) -> str:
    if len(node.generators) != 1:
        return _OTHER
    generator = node.generators[0]
    source = _tag(generator.iter, env, ctx)
    if source not in {_ROWS_FULL, _ROWS_SUBSET}:
        return _OTHER
    if generator.ifs:
        return _ROWS_SUBSET
    return source


def _tag_counting_comprehension(
    node: ast.ListComp | ast.GeneratorExp, env: dict[str, str], ctx: _TraceContext
) -> str:
    """sum(1 for row in X [if ...]) is a count over X or a conditioned subset."""

    if len(node.generators) != 1:
        return _OTHER
    element = node.elt
    if not (isinstance(element, ast.Constant) and element.value == 1):
        return _OTHER
    generator = node.generators[0]
    source = _tag(generator.iter, env, ctx)
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
