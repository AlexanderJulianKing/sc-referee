"""Closed symbolic record models for the multiple-testing 3.0 dataflow.

The models are structural transports layered over the versioned 3.0 baseline proof. They do not
execute project code, read prose, or inspect case identity. Every unresolved record, subset,
dispatch, or DataFrame edge returns a closed abstention reason.
"""

from __future__ import annotations

import ast
import copy
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 as mt

_REGISTERED_APIS = frozenset(
    {
        "scipy.stats.ttest_ind",
        "scipy.stats.mannwhitneyu",
    }
)
_CORRECTION_APIS = frozenset(
    {
        "statsmodels.stats.multitest.multipletests",
        "statsmodels.stats.multitest.fdrcorrection",
        "scipy.stats.false_discovery_control",
        "sc_referee.calculation_checks.bh.benjamini_hochberg",
    }
)
_DATAFRAME_APIS = frozenset({"pandas.DataFrame"})
_ALLOWED_FRAME_METHODS = frozenset(
    {
        "copy",
        "drop",
        "to_string",
        "itertuples",
        "iterrows",
    }
)
_ALLOWED_SERIES_METHODS = frozenset(
    {
        "tolist",
        "to_numpy",
        "isin",
        "where",
        "astype",
        "map",
    }
)
_REFUSED_FRAME_METHODS = frozenset(
    {
        "sort_values",
        "sort_index",
        "query",
        "merge",
        "join",
        "groupby",
        "pivot",
        "pivot_table",
        "reset_index",
        "set_index",
        "explode",
        "sample",
        "head",
        "tail",
        "drop_duplicates",
        "transpose",
        "apply",
        "applymap",
    }
)
_RECORD_MUTATORS = frozenset(
    {
        "append",
        "remove",
        "pop",
        "insert",
        "extend",
        "clear",
        "sort",
        "reverse",
        "__setitem__",
    }
)
_TARGET_REASONS = frozenset(
    {
        "authorized-family-test-census-incomplete",
        "mixed-test-api-family",
        "pvalue-family-collection-unresolved",
        "unresolved-pvalue-consumer",
        "correction-family-lineage-unresolved",
        "test-battery-cardinality-unresolved",
    }
)


@dataclass(frozen=True)
class _Outcome:
    state: str
    reason_or_classification: str
    corrected_positions: tuple[int, ...] = ()
    authorized_count: int | None = None

    def as_json(self) -> list[object]:
        value: list[object] = [self.state, self.reason_or_classification]
        if self.state in {"candidate", "covered"}:
            value.append(
                {
                    "authorized_count": self.authorized_count,
                    "corrected_positions": list(self.corrected_positions),
                }
            )
        return value


def _classify(result: mt.MultipleTestingDataflowResult) -> _Outcome:
    if result.reason is not None:
        return _Outcome("abstain", result.reason)
    if result.facts is None:
        raise ValueError("multiple-testing result contains neither facts nor reason")
    facts = result.facts
    return _Outcome(
        "covered" if facts.correction_classification == "complete" else "candidate",
        facts.correction_classification,
        facts.corrected_positions,
        facts.family_size,
    )


@dataclass(frozen=True)
class RecordModelResult:
    outcome: _Outcome
    baseline: _Outcome
    changed: bool
    models: tuple[str, ...]
    trigger_shapes: tuple[str, ...]
    detail: Mapping[str, object]


@dataclass(frozen=True)
class _DispatchPlan:
    api_by_position: tuple[str, ...]
    dispatch_if: ast.If
    selected_body: tuple[ast.stmt, ...]
    attempt: bool
    refusal: str | None = None


@dataclass(frozen=True)
class _RecordBuilder:
    collection: str
    owner: ast.Module | ast.FunctionDef
    loop: ast.For | ast.ListComp
    append: ast.Call | None
    record: ast.expr
    wrapper_depth: int
    schema: tuple[str | int, ...]


@dataclass(frozen=True)
class _ModelDecision:
    outcome: _Outcome
    models: tuple[str, ...]
    detail: Mapping[str, object]


def _position(node: ast.AST) -> tuple[int, int, int, int]:
    return (
        getattr(node, "lineno", -1),
        getattr(node, "col_offset", -1),
        getattr(node, "end_lineno", -1),
        getattr(node, "end_col_offset", -1),
    )


def _literal(node: ast.expr, resolver: Any) -> object | None:
    if isinstance(node, ast.Constant) and isinstance(
        node.value, (str, int, float, bool, type(None))
    ):
        return node.value
    if isinstance(node, ast.Name):
        value = resolver.constants.get(node.id, resolver.literals.get(node.id))
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
    return None


def _literal_int(node: ast.expr | None, resolver: Any) -> int | None:
    value = _literal(node, resolver) if node is not None else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _literal_key(node: ast.expr) -> str | int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)):
        return node.value
    return None


def _resolver(tree: ast.Module) -> Any:
    scope = tuple(item for item in tree.body if not mt._is_docstring(item))
    value, reason = mt._resolver(scope)
    if value is None or reason is not None:
        raise ValueError(reason or "api-resolution-ambiguous")
    return value


def _functions(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    result: dict[str, ast.FunctionDef] = {}
    duplicate: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name in result:
            duplicate.add(node.name)
        result[node.name] = node
    for name in duplicate:
        result.pop(name, None)
    return result


def _owners(tree: ast.Module) -> dict[ast.AST, ast.Module | ast.FunctionDef]:
    result: dict[ast.AST, ast.Module | ast.FunctionDef] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                result[child] = node
        else:
            for child in ast.walk(node):
                result[child] = tree
    return result


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}


def _calls_of(
    functions: Mapping[str, ast.FunctionDef], tree: ast.Module
) -> dict[str, list[ast.Call]]:
    result: dict[str, list[ast.Call]] = {name: [] for name in functions}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in result
        ):
            result[node.func.id].append(node)
    return result


def _assignments(owner: ast.Module | ast.FunctionDef) -> dict[str, list[ast.expr]]:
    result: dict[str, list[ast.expr]] = defaultdict(list)
    body = owner.body
    for statement in body:
        for node in ast.walk(statement):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    result[target.id].append(node.value)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.value is not None:
                    result[node.target.id].append(node.value)
    return result


def _static_tables(
    tree: ast.Module, resolver: Any, outcome_columns: tuple[str, ...]
) -> dict[str, tuple[tuple[object, ...], ...]]:
    result: dict[str, tuple[tuple[object, ...], ...]] = {}
    for statement in tree.body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)) or statement.value is None:
            continue
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        if len(targets) != 1 or not isinstance(targets[0], ast.Name):
            continue
        table = resolver.tables.get(targets[0].id)
        if table is None or len(table) != len(outcome_columns):
            continue
        rows = tuple(tuple(row) for row in table)
        if not rows or any(len(row) != len(rows[0]) for row in rows):
            continue
        if not any(
            tuple(row[index] for row in rows) == outcome_columns for index in range(len(rows[0]))
        ):
            continue
        result[targets[0].id] = rows
    return result


def _table_binding(
    owner: ast.Module | ast.FunctionDef,
    iterable: ast.expr,
    *,
    tables: Mapping[str, tuple[tuple[object, ...], ...]],
    calls: Mapping[str, Sequence[ast.Call]],
) -> tuple[str, tuple[tuple[object, ...], ...]] | None:
    if isinstance(iterable, ast.Name) and iterable.id in tables:
        return iterable.id, tables[iterable.id]
    if not isinstance(owner, ast.FunctionDef) or not isinstance(iterable, ast.Name):
        return None
    parameters = [*owner.args.posonlyargs, *owner.args.args]
    parameter_names = [item.arg for item in parameters]
    if iterable.id not in parameter_names or len(calls.get(owner.name, ())) != 1:
        return None
    call = calls[owner.name][0]
    index = parameter_names.index(iterable.id)
    argument: ast.expr | None = call.args[index] if index < len(call.args) else None
    if argument is None:
        matches = [item.value for item in call.keywords if item.arg == iterable.id]
        argument = matches[0] if len(matches) == 1 else None
    if isinstance(argument, ast.Name) and argument.id in tables:
        return argument.id, tables[argument.id]
    return None


def _target_names(target: ast.expr) -> tuple[str, ...] | None:
    if isinstance(target, ast.Name):
        return (target.id,)
    if isinstance(target, (ast.Tuple, ast.List)) and all(
        isinstance(item, ast.Name) for item in target.elts
    ):
        return tuple(cast(ast.Name, item).id for item in target.elts)
    return None


def _complete_loop_rows(
    loop: ast.For | ast.ListComp,
    owner: ast.Module | ast.FunctionDef,
    *,
    tables: Mapping[str, tuple[tuple[object, ...], ...]],
    calls: Mapping[str, Sequence[ast.Call]],
    outcome_columns: tuple[str, ...],
) -> tuple[dict[str, object], ...] | None:
    if isinstance(loop, ast.ListComp):
        if len(loop.generators) != 1:
            return None
        generator = loop.generators[0]
        if generator.is_async or generator.ifs:
            return None
        iterable = generator.iter
        target = generator.target
    else:
        iterable = loop.iter
        target = loop.target
    bound = _table_binding(owner, iterable, tables=tables, calls=calls)
    names = _target_names(target)
    if bound is None or names is None:
        return None
    _name, rows = bound
    if any(len(row) != len(names) for row in rows):
        return None
    mappings = tuple(dict(zip(names, row, strict=True)) for row in rows)
    if not any(tuple(row.get(name) for row in mappings) == outcome_columns for name in names):
        return None
    return mappings


def _registered_calls(node: ast.AST, resolver: Any) -> tuple[ast.Call, ...]:
    return tuple(
        sorted(
            (
                item
                for item in ast.walk(node)
                if isinstance(item, ast.Call) and resolver.qualified(item.func) in _REGISTERED_APIS
            ),
            key=_position,
        )
    )


def _record_return(function: ast.FunctionDef) -> ast.expr | None:
    returns = [item for item in ast.walk(function) if isinstance(item, ast.Return)]
    if len(returns) != 1 or returns[0].value is None:
        return None
    return returns[0].value


def _recordish(
    node: ast.expr,
    *,
    owner: ast.Module | ast.FunctionDef,
    functions: Mapping[str, ast.FunctionDef],
    active: frozenset[str] = frozenset(),
) -> bool:
    if isinstance(node, (ast.Dict, ast.Tuple, ast.List)):
        return True
    if isinstance(node, ast.Name):
        if node.id in active:
            return False
        values = _assignments(owner).get(node.id, ())
        return len(values) == 1 and _recordish(
            values[0], owner=owner, functions=functions, active=active | {node.id}
        )
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        function = functions.get(node.func.id)
        if function is None:
            return False
        value = _record_return(function)
        return value is not None and _recordish(value, owner=function, functions=functions)
    return False


def trigger_shapes(content: bytes, outcome_columns: tuple[str, ...]) -> tuple[str, ...]:
    """Return the design's broad trigger census, never an admission decision."""

    tree = mt._bounded_parse(content)
    resolver = _resolver(tree)
    functions = _functions(tree)
    owner_for = _owners(tree)
    result: set[str] = set()
    if any(
        isinstance(node, ast.Call) and resolver.qualified(node.func) in _DATAFRAME_APIS
        for node in ast.walk(tree)
    ):
        result.add("dataframe-table")
    if any(
        len({resolver.qualified(call.func) for call in _registered_calls(node, resolver)}) > 1
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
    ):
        result.add("mixed-dispatch")
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "append"
            and len(node.args) == 1
            and not node.keywords
        ):
            continue
        owner = owner_for.get(node, tree)
        if _recordish(node.args[0], owner=owner, functions=functions):
            result.add("record-accumulation")
            break
    return tuple(sorted(result))


def _pure_projection(node: ast.expr, outcome_name: str) -> bool:
    return bool(
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and isinstance(node.slice, ast.Name)
        and node.slice.id == outcome_name
    )


def _d14_rewrite(content: bytes, outcome_columns: tuple[str, ...]) -> bytes:
    tree = mt._bounded_parse(content)
    scope = tuple(item for item in tree.body if not mt._is_docstring(item))
    resolver, reason = mt._resolver(scope)
    if reason is not None or resolver is None:
        return content
    closed_resolver = resolver
    changed = False

    class Rewrite(ast.NodeTransformer):
        def visit_DictComp(self, node: ast.DictComp) -> ast.AST:
            nonlocal changed
            if len(node.generators) != 2:
                return self.generic_visit(node)
            first, second = node.generators
            rows = mt._mt_outcome_iteration_bindings(
                first.iter, first.target, closed_resolver, outcome_columns
            )
            if (
                rows is None
                or len(rows) != len(outcome_columns)
                or first.is_async
                or first.ifs
                or second.is_async
                or second.ifs
                or not isinstance(second.iter, (ast.List, ast.Tuple))
                or len(second.iter.elts) != 1
                or not isinstance(second.target, (ast.List, ast.Tuple))
                or not isinstance(second.iter.elts[0], type(second.target))
            ):
                return self.generic_visit(node)
            row = second.iter.elts[0]
            if (
                len(row.elts) != 2
                or len(second.target.elts) != 2
                or not all(isinstance(item, ast.Name) for item in second.target.elts)
            ):
                return self.generic_visit(node)
            names = tuple(cast(ast.Name, item).id for item in second.target.elts)
            if len(set(names)) != 2:
                return self.generic_visit(node)
            outcome_names = [
                name
                for name in rows[0]
                if tuple(values[name] for values in rows) == outcome_columns
            ]
            if len(outcome_names) != 1 or not all(
                _pure_projection(item, outcome_names[0]) for item in row.elts
            ):
                return self.generic_visit(node)
            bindings = dict(zip(names, row.elts, strict=True))
            loads = Counter(
                item.id
                for item in ast.walk(ast.Tuple(elts=[node.key, node.value]))
                if isinstance(item, ast.Name)
                and isinstance(item.ctx, ast.Load)
                and item.id in bindings
            )
            if set(loads) - set(bindings):
                return self.generic_visit(node)

            class Substitute(ast.NodeTransformer):
                def visit_Name(self, item: ast.Name) -> ast.AST:
                    if isinstance(item.ctx, ast.Load) and item.id in bindings:
                        return ast.copy_location(copy.deepcopy(bindings[item.id]), item)
                    return item

            substitute = Substitute()
            node = copy.deepcopy(node)
            node.key = cast(ast.expr, substitute.visit(node.key))
            node.value = cast(ast.expr, substitute.visit(node.value))
            node.generators = [first]
            changed = True
            return self.generic_visit(node)

    rewritten = Rewrite().visit(copy.deepcopy(tree))
    if not changed:
        return content
    ast.fix_missing_locations(rewritten)
    return (ast.unparse(rewritten) + "\n").encode("utf-8")


def _compare_token(node: ast.expr, selector: str, resolver: Any) -> object | None:
    if not (isinstance(node, ast.Compare) and len(node.ops) == 1 and len(node.comparators) == 1):
        return None
    if not isinstance(node.ops[0], ast.Eq):
        return None
    left, right = node.left, node.comparators[0]
    if isinstance(left, ast.Name) and left.id == selector:
        return _literal(right, resolver)
    if isinstance(right, ast.Name) and right.id == selector:
        return _literal(left, resolver)
    return None


def _dispatch_chain(
    node: ast.If,
) -> tuple[list[tuple[ast.expr, tuple[ast.stmt, ...]]], tuple[ast.stmt, ...]]:
    branches: list[tuple[ast.expr, tuple[ast.stmt, ...]]] = []
    cursor = node
    while True:
        branches.append((cursor.test, tuple(cursor.body)))
        if len(cursor.orelse) == 1 and isinstance(cursor.orelse[0], ast.If):
            cursor = cursor.orelse[0]
            continue
        return branches, tuple(cursor.orelse)


def _call_result_target(statement: ast.stmt, resolver: Any) -> tuple[str, ast.Call] | None:
    if not isinstance(statement, (ast.Assign, ast.AnnAssign)) or statement.value is None:
        return None
    targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
    if len(targets) != 1:
        return None
    target = targets[0]
    call: ast.Call | None = None
    value = statement.value
    if isinstance(value, ast.Call) and resolver.qualified(value.func) in _REGISTERED_APIS:
        call = value
    elif (
        isinstance(value, ast.Attribute)
        and value.attr == "pvalue"
        and isinstance(value.value, ast.Call)
        and resolver.qualified(value.value.func) in _REGISTERED_APIS
    ):
        call = value.value
    if call is None:
        return None
    if isinstance(target, ast.Name):
        return f"name:{target.id}", call
    if isinstance(target, (ast.Tuple, ast.List)) and all(
        isinstance(item, ast.Name) for item in target.elts
    ):
        return f"{type(target).__name__}:" + ",".join(
            cast(ast.Name, item).id for item in target.elts
        ), call
    return None


def _branch_call(branch: Sequence[ast.stmt], resolver: Any) -> tuple[str, ast.Call] | None:
    matches = [
        value
        for statement in branch
        if (value := _call_result_target(statement, resolver)) is not None
    ]
    if len(matches) != 1:
        return None
    if any(
        isinstance(item, (ast.Return, ast.Break, ast.Continue, ast.Raise))
        or (
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr in _RECORD_MUTATORS
        )
        for statement in branch
        for item in ast.walk(statement)
    ):
        return None
    return matches[0]


def _dispatch_attempts(tree: ast.Module, resolver: Any) -> tuple[ast.If, ...]:
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and len(_dispatch_chain(node)[0]) >= 2
        and len(_registered_calls(node, resolver)) >= 1
    )


def _dispatch_plan(
    tree: ast.Module, resolver: Any, outcome_columns: tuple[str, ...]
) -> _DispatchPlan | None:
    functions = _functions(tree)
    calls = _calls_of(functions, tree)
    tables = _static_tables(tree, resolver, outcome_columns)
    owner_for = _owners(tree)
    attempts = _dispatch_attempts(tree, resolver)
    if not attempts:
        return None
    parents = _parents(tree)
    for candidate in attempts:
        # Only the outer chain owns the attempt.
        if (
            isinstance(parents.get(candidate), ast.If)
            and candidate in cast(ast.If, parents[candidate]).orelse
        ):
            continue
        branches, fallback = _dispatch_chain(candidate)
        if len(fallback) != 1 or not isinstance(fallback[0], ast.Raise):
            return _DispatchPlan((), candidate, (), True, "family-test-api-dispatch-unresolved")
        owner = owner_for.get(candidate, tree)
        loop: ast.For | None = None
        cursor: ast.AST | None = candidate
        while cursor is not None:
            cursor = parents.get(cursor)
            if isinstance(cursor, ast.For):
                loop = cursor
                break
        selector: str | None = None
        rows: tuple[dict[str, object], ...] | None = None
        if loop is not None:
            rows = _complete_loop_rows(
                loop,
                owner,
                tables=tables,
                calls=calls,
                outcome_columns=outcome_columns,
            )
            names = _target_names(loop.target)
            if rows is not None and names is not None:
                for name in names:
                    if all(
                        _compare_token(test, name, resolver) is not None for test, _ in branches
                    ):
                        selector = name
                        break
        if selector is None:
            # R4/P5 shape: the dispatch lives in a sole-call helper invoked by a complete loop.
            if not isinstance(owner, ast.FunctionDef) or len(calls.get(owner.name, ())) != 1:
                continue
            helper_call = calls[owner.name][0]
            call_owner = owner_for.get(helper_call, tree)
            loop_cursor: ast.AST | None = helper_call
            while loop_cursor is not None:
                loop_cursor = parents.get(loop_cursor)
                if isinstance(loop_cursor, ast.For):
                    loop = loop_cursor
                    break
            if loop is None:
                continue
            rows = _complete_loop_rows(
                loop,
                call_owner,
                tables=tables,
                calls=calls,
                outcome_columns=outcome_columns,
            )
            loop_names = _target_names(loop.target)
            parameters = [*owner.args.posonlyargs, *owner.args.args]
            if rows is None or loop_names is None:
                continue
            for parameter_index, parameter in enumerate(parameters):
                if not all(
                    _compare_token(test, parameter.arg, resolver) is not None
                    for test, _ in branches
                ):
                    continue
                argument = (
                    helper_call.args[parameter_index]
                    if parameter_index < len(helper_call.args)
                    else None
                )
                if isinstance(argument, ast.Name) and argument.id in loop_names:
                    selector = parameter.arg
                    values = tuple(row[argument.id] for row in rows)
                    rows = tuple(
                        {selector: value, **row} for value, row in zip(values, rows, strict=True)
                    )
                    break
        if selector is None and rows is not None:
            return _DispatchPlan(
                (), candidate, branches[0][1], True, "family-test-api-dispatch-unresolved"
            )
        if selector is None or rows is None:
            continue
        static_marker = branches[0][1]
        tokens: list[object] = []
        calls_by_token: dict[object, tuple[str, ast.Call, tuple[ast.stmt, ...]]] = {}
        target_key: str | None = None
        for test, body in branches:
            token = _compare_token(test, selector, resolver)
            registered_in_branch = tuple(
                item
                for statement in body
                for item in ast.walk(statement)
                if isinstance(item, ast.Call) and resolver.qualified(item.func) in _REGISTERED_APIS
            )
            if len(registered_in_branch) > 1:
                return _DispatchPlan(
                    (),
                    candidate,
                    static_marker,
                    True,
                    "multiple-registered-tests-for-family-member",
                )
            branch_call = _branch_call(body, resolver)
            if token is None or branch_call is None or token in calls_by_token:
                return _DispatchPlan(
                    (), candidate, static_marker, True, "family-test-api-dispatch-unresolved"
                )
            branch_target, call = branch_call
            if target_key is None:
                target_key = branch_target
            elif target_key != branch_target:
                return _DispatchPlan(
                    (), candidate, static_marker, True, "family-test-api-dispatch-unresolved"
                )
            api = resolver.qualified(call.func)
            if api not in _REGISTERED_APIS:
                return _DispatchPlan(
                    (), candidate, static_marker, True, "family-test-api-dispatch-unresolved"
                )
            if len(call.args) < 2 or ast.dump(call.args[0]) == ast.dump(call.args[1]):
                return _DispatchPlan(
                    (), candidate, static_marker, True, "test-operand-lineage-unresolved"
                )
            tokens.append(token)
            calls_by_token[token] = (api, call, body)
        selected: list[str] = []
        for row in rows:
            value = row.get(selector)
            if value not in calls_by_token:
                return _DispatchPlan(
                    (), candidate, static_marker, True, "family-test-api-dispatch-unresolved"
                )
            selected.append(calls_by_token[value][0])
        if set(tokens) != {row.get(selector) for row in rows}:
            return _DispatchPlan(
                (), candidate, static_marker, True, "family-test-api-dispatch-unresolved"
            )
        if any(selected.count(api) < 1 for api in {item[0] for item in calls_by_token.values()}):
            return _DispatchPlan(
                (), candidate, static_marker, True, "family-test-api-dispatch-unresolved"
            )
        first = calls_by_token[tokens[0]][2]
        return _DispatchPlan(tuple(selected), candidate, first, True)
    if attempts:
        branches, _fallback = _dispatch_chain(attempts[0])
        if any(any(isinstance(item, ast.Call) for item in ast.walk(test)) for test, _ in branches):
            return _DispatchPlan(
                (), attempts[0], branches[0][1], True, "family-test-api-dispatch-unresolved"
            )
        return _DispatchPlan((), attempts[0], (), True, "family-test-api-dispatch-unresolved")
    return None


def _lower_dispatch(content: bytes, plan: _DispatchPlan) -> bytes:
    tree = mt._bounded_parse(content)
    target_position = _position(plan.dispatch_if)
    changed = False

    class Lower(ast.NodeTransformer):
        def visit_If(self, node: ast.If) -> ast.AST | list[ast.stmt]:
            nonlocal changed
            if _position(node) == target_position:
                changed = True
                return [copy.deepcopy(item) for item in plan.selected_body]
            return self.generic_visit(node)

    rewritten = Lower().visit(copy.deepcopy(tree))
    if not changed:
        raise ValueError("dispatch surrogate did not replace its proved chain")
    ast.fix_missing_locations(rewritten)
    return (ast.unparse(rewritten) + "\n").encode("utf-8")


def _record_schema(node: ast.expr) -> tuple[tuple[str | int, ...], int] | None:
    if isinstance(node, ast.Dict):
        if any(key is None for key in node.keys):
            return None
        keys = tuple(_literal_key(cast(ast.expr, key)) for key in node.keys)
        if (
            any(key is None for key in keys)
            or len(keys) != len(set(keys))
            or not 1 <= len(keys) <= 16
        ):
            return None
        return cast(tuple[str | int, ...], keys), 1
    if isinstance(node, ast.Tuple):
        if not 1 <= len(node.elts) <= 16 or any(
            isinstance(item, ast.Starred) for item in node.elts
        ):
            return None
        nested = [item for item in node.elts if isinstance(item, (ast.Dict, ast.Tuple))]
        if len(nested) == 1:
            inner = _record_schema(cast(ast.expr, nested[0]))
            if inner is None or inner[1] != 1:
                return None
            nested_index = node.elts.index(nested[0])
            outer = tuple(f"outer:{index}" for index in range(len(node.elts)))
            inner_keys = tuple(f"nested:{nested_index}:{key}" for key in inner[0])
            return (*outer, *inner_keys), 2
        if nested:
            return None
        return tuple(range(len(node.elts))), 1
    return None


def _resolve_record_expr(
    node: ast.expr,
    *,
    owner: ast.Module | ast.FunctionDef,
    functions: Mapping[str, ast.FunctionDef],
    active: frozenset[str] = frozenset(),
) -> ast.expr | None:
    if isinstance(node, (ast.Dict, ast.Tuple)):
        return node
    if isinstance(node, ast.Name):
        if node.id in active:
            return None
        values = _assignments(owner).get(node.id, ())
        if len(values) != 1:
            return None
        return _resolve_record_expr(
            values[0], owner=owner, functions=functions, active=active | {node.id}
        )
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        function = functions.get(node.func.id)
        if function is None:
            return None
        value = _record_return(function)
        return (
            _resolve_record_expr(value, owner=function, functions=functions)
            if value is not None
            else None
        )
    return None


def _record_builders(
    tree: ast.Module, resolver: Any, outcome_columns: tuple[str, ...]
) -> tuple[_RecordBuilder, ...]:
    functions = _functions(tree)
    calls = _calls_of(functions, tree)
    tables = _static_tables(tree, resolver, outcome_columns)
    owner_for = _owners(tree)
    parents = _parents(tree)
    result: list[_RecordBuilder] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.attr == "append"
            and len(node.args) == 1
            and not node.keywords
        ):
            continue
        owner = owner_for.get(node, tree)
        loop: ast.For | None = None
        cursor: ast.AST | None = node
        while cursor is not None:
            cursor = parents.get(cursor)
            if isinstance(cursor, ast.For):
                loop = cursor
                break
        if loop is None:
            continue
        rows = _complete_loop_rows(
            loop,
            owner,
            tables=tables,
            calls=calls,
            outcome_columns=outcome_columns,
        )
        if rows is None:
            # The complete loop may be the caller of a sole-call builder helper.
            if not isinstance(owner, ast.FunctionDef) or len(calls.get(owner.name, ())) != 1:
                continue
            call = calls[owner.name][0]
            call_owner = owner_for.get(call, tree)
            outer: ast.AST | None = call
            while outer is not None:
                outer = parents.get(outer)
                if isinstance(outer, ast.For):
                    loop = outer
                    break
            if loop is None:
                continue
            rows = _complete_loop_rows(
                loop,
                call_owner,
                tables=tables,
                calls=calls,
                outcome_columns=outcome_columns,
            )
        if rows is None:
            continue
        record = _resolve_record_expr(node.args[0], owner=owner, functions=functions)
        if record is None:
            continue
        schema = _record_schema(record)
        if schema is None:
            continue
        keys, depth = schema
        result.append(_RecordBuilder(node.func.value.id, owner, loop, node, record, depth, keys))
    # Exact comprehension builder.
    for node in ast.walk(tree):
        if not isinstance(node, ast.ListComp):
            continue
        owner = owner_for.get(node, tree)
        rows = _complete_loop_rows(
            node,
            owner,
            tables=tables,
            calls=calls,
            outcome_columns=outcome_columns,
        )
        schema = _record_schema(node.elt)
        if rows is None or schema is None:
            continue
        parent = parents.get(node)
        if not isinstance(parent, (ast.Assign, ast.AnnAssign)):
            continue
        targets = parent.targets if isinstance(parent, ast.Assign) else [parent.target]
        if len(targets) != 1 or not isinstance(targets[0], ast.Name):
            continue
        result.append(
            _RecordBuilder(
                targets[0].id,
                owner,
                node,
                None,
                node.elt,
                schema[1],
                schema[0],
            )
        )
    return tuple(result)


def strict_trigger_shapes(content: bytes, outcome_columns: tuple[str, ...]) -> tuple[str, ...]:
    """Return the review census after excluding record noise with no family-test origin."""

    result = list(trigger_shapes(content, outcome_columns))
    if "record-accumulation" not in result:
        return tuple(result)
    tree = mt._bounded_parse(content)
    resolver = _resolver(tree)
    functions = _functions(tree)
    registered_anywhere = any(
        isinstance(node, ast.Call) and resolver.qualified(node.func) in _REGISTERED_APIS
        for node in ast.walk(tree)
    )
    append_collections = {
        node.func.value.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.attr == "append"
        and len(node.args) == 1
    }
    append_has_decision = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in append_collections
        and any(isinstance(item, ast.Compare) for item in ast.walk(node.args[0]))
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and node.args
    )
    decision_names = {
        target.id
        for assignment in ast.walk(tree)
        if isinstance(assignment, (ast.Assign, ast.AnnAssign))
        and assignment.value is not None
        and isinstance(assignment.value, ast.Compare)
        for target in (
            assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
        )
        if isinstance(target, ast.Name)
    }
    append_has_decision = append_has_decision or any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in append_collections
        and any(
            isinstance(item, ast.Name)
            and isinstance(item.ctx, ast.Load)
            and item.id in decision_names
            for item in ast.walk(node.args[0])
        )
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and node.args
    )
    if not append_has_decision:
        for loop in (node for node in ast.walk(tree) if isinstance(node, ast.For)):
            iter_names = {
                item.id
                for item in ast.walk(loop.iter)
                if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
            }
            if not iter_names & append_collections:
                continue
            target_names = {item.id for item in ast.walk(loop.target) if isinstance(item, ast.Name)}
            if any(
                isinstance(compare, ast.Compare)
                and any(
                    isinstance(item, ast.Name)
                    and isinstance(item.ctx, ast.Load)
                    and item.id in target_names
                    for item in ast.walk(compare)
                )
                for compare in ast.walk(loop)
            ):
                append_has_decision = True
                break
    joint_record_gate = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test_names = {
            item.id
            for item in ast.walk(node.test)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
        }
        controlled = {
            call.func.id
            for statement in (*node.body, *node.orelse)
            for call in ast.walk(statement)
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
        }
        if not any(
            name in functions
            and any(
                isinstance(item, ast.Call) and resolver.qualified(item.func) in _REGISTERED_APIS
                for item in ast.walk(functions[name])
            )
            for name in controlled
        ):
            continue
        joint_record_gate = False
        for assignment in ast.walk(tree):
            if not isinstance(assignment, (ast.Assign, ast.AnnAssign)):
                continue
            value = assignment.value
            if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Name):
                continue
            targets = (
                assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
            )
            bound = {
                item.id
                for target in targets
                for item in ast.walk(target)
                if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store)
            }
            function = functions.get(value.func.id)
            if not bound & test_names or function is None:
                continue
            joint_record_gate = any(
                isinstance(item, ast.Call)
                and isinstance(item.func, ast.Attribute)
                and item.func.attr == "append"
                for item in ast.walk(function)
            ) and not any(
                isinstance(item, ast.Call) and resolver.qualified(item.func) in _REGISTERED_APIS
                for item in ast.walk(function)
            )
            if joint_record_gate:
                break
        if joint_record_gate:
            break
    if (not registered_anywhere and not append_has_decision) or joint_record_gate:
        result.remove("record-accumulation")
    return tuple(result)


def _static_bool_position_sets(
    tree: ast.Module, resolver: Any, outcome_columns: tuple[str, ...]
) -> tuple[frozenset[int], ...]:
    result: list[frozenset[int]] = []
    for rows in _static_tables(tree, resolver, outcome_columns).values():
        for index in range(len(rows[0])):
            values = tuple(row[index] for row in rows)
            if all(isinstance(value, bool) for value in values):
                result.append(frozenset(position for position, value in enumerate(values) if value))
    return tuple(result)


def _subset_positions(
    node: ast.expr,
    *,
    collection: str,
    assignments: Mapping[str, ast.expr],
    resolver: Any,
    outcome_columns: tuple[str, ...],
    bool_positions: tuple[frozenset[int], ...],
    active: frozenset[str] = frozenset(),
) -> frozenset[int] | None:
    if isinstance(node, ast.Name):
        if node.id == collection:
            return frozenset(range(len(outcome_columns)))
        if node.id in active or node.id not in assignments:
            return None
        return _subset_positions(
            assignments[node.id],
            collection=collection,
            assignments=assignments,
            resolver=resolver,
            outcome_columns=outcome_columns,
            bool_positions=bool_positions,
            active=active | {node.id},
        )
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
        base = _subset_positions(
            node.value,
            collection=collection,
            assignments=assignments,
            resolver=resolver,
            outcome_columns=outcome_columns,
            bool_positions=bool_positions,
            active=active,
        )
        if base is None:
            return None
        ordered = tuple(sorted(base))
        start = _literal_int(node.slice.lower, resolver) if node.slice.lower else 0
        stop = _literal_int(node.slice.upper, resolver) if node.slice.upper else len(ordered)
        step = _literal_int(node.slice.step, resolver) if node.slice.step else 1
        if start is None or stop is None or step != 1 or not 0 <= start <= stop <= len(ordered):
            return None
        return frozenset(ordered[start:stop])
    if isinstance(node, (ast.ListComp, ast.GeneratorExp)):
        if len(node.generators) != 1:
            return None
        generator = node.generators[0]
        base = _subset_positions(
            generator.iter,
            collection=collection,
            assignments=assignments,
            resolver=resolver,
            outcome_columns=outcome_columns,
            bool_positions=bool_positions,
            active=active,
        )
        if base is None:
            return None
        if not generator.ifs:
            return base
        if len(generator.ifs) != 1 or len(bool_positions) != 1:
            return None
        flag = generator.ifs[0]
        inverted = isinstance(flag, ast.UnaryOp) and isinstance(flag.op, ast.Not)
        flag_value = flag.operand if isinstance(flag, ast.UnaryOp) and inverted else flag
        if not isinstance(flag_value, ast.Subscript) or _literal_key(flag_value.slice) is None:
            return None
        selected = bool_positions[0]
        if inverted:
            selected = frozenset(range(len(outcome_columns))) - selected
        return base & selected
    return None


def _store_positions(
    node: ast.Assign | ast.AnnAssign,
    *,
    builder: _RecordBuilder,
    tree: ast.Module,
    resolver: Any,
    outcome_columns: tuple[str, ...],
) -> frozenset[int] | None:
    parents = _parents(tree)
    assignments = {
        item.targets[0].id: item.value
        for item in ast.walk(builder.owner)
        if isinstance(item, ast.Assign)
        and len(item.targets) == 1
        and isinstance(item.targets[0], ast.Name)
    }
    boolean_sets = _static_bool_position_sets(tree, resolver, outcome_columns)
    positions: frozenset[int] | None = None
    cursor: ast.AST = node
    while (parent := parents.get(cursor)) is not None and parent is not builder.owner:
        if isinstance(parent, ast.For):
            iterable = parent.iter
            if isinstance(iterable, ast.Call) and resolver.qualified(iterable.func) == "zip":
                if not iterable.args:
                    return None
                iterable = iterable.args[0]
            loop_positions = _subset_positions(
                iterable,
                collection=builder.collection,
                assignments=assignments,
                resolver=resolver,
                outcome_columns=outcome_columns,
                bool_positions=boolean_sets,
            )
            positions = (
                loop_positions
                if positions is None
                else None
                if loop_positions is None
                else positions & loop_positions
            )
        if isinstance(parent, ast.If):
            test = parent.test
            inverted = isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)
            test_value = test.operand if isinstance(test, ast.UnaryOp) and inverted else test
            if (
                not isinstance(test_value, ast.Subscript)
                or _literal_key(test_value.slice) is None
                or len(boolean_sets) != 1
            ):
                return None
            selected = boolean_sets[0]
            in_body = any(node is item or node in ast.walk(item) for item in parent.body)
            if not in_body:
                selected = frozenset(range(len(outcome_columns))) - selected
            if inverted:
                selected = frozenset(range(len(outcome_columns))) - selected
            positions = selected if positions is None else positions & selected
        cursor = parent
    return positions


def _root_name(node: ast.expr) -> str | None:
    cursor = node
    while isinstance(cursor, (ast.Attribute, ast.Subscript)):
        cursor = cursor.value
    return cursor.id if isinstance(cursor, ast.Name) else None


def _enclosing_statement(
    node: ast.AST,
    parents: Mapping[ast.AST, ast.AST],
) -> ast.stmt | None:
    cursor: ast.AST | None = node
    while cursor is not None and not isinstance(cursor, ast.stmt):
        cursor = parents.get(cursor)
    return cursor


def _enclosing_iteration(
    node: ast.AST,
    parents: Mapping[ast.AST, ast.AST],
    owner: ast.Module | ast.FunctionDef,
) -> ast.For | ast.ListComp | None:
    cursor: ast.AST | None = node
    while cursor is not None and cursor is not owner:
        cursor = parents.get(cursor)
        if isinstance(cursor, (ast.For, ast.ListComp)):
            return cursor
    return None


def _builder_record_names(
    builder: _RecordBuilder,
    functions: Mapping[str, ast.FunctionDef],
) -> frozenset[str]:
    """Return only names whose value is the builder's proved record expression."""

    if builder.append is None or not builder.append.args:
        return frozenset()
    names: set[str] = set()
    for node in ast.walk(builder.append.args[0]):
        if not isinstance(node, ast.Name) or not isinstance(node.ctx, ast.Load):
            continue
        resolved = _resolve_record_expr(node, owner=builder.owner, functions=functions)
        if resolved is not None and _record_schema(resolved) is not None:
            names.add(node.id)
    return frozenset(names)


def _record_boundary_reason(
    tree: ast.Module,
    builders: Sequence[_RecordBuilder],
    resolver: Any,
    outcome_columns: tuple[str, ...],
) -> str | None:
    parents = _parents(tree)
    functions = _functions(tree)
    calls = _calls_of(functions, tree)
    for builder in builders:
        record_names = _builder_record_names(builder, functions)
        tracked_names = record_names | {builder.collection}
        if builder.append is not None:
            cursor: ast.AST | None = builder.append
            while cursor is not None and cursor is not builder.loop:
                cursor = parents.get(cursor)
                if isinstance(cursor, (ast.If, ast.IfExp, ast.Try, ast.While, ast.Match)):
                    return "record-family-mutation-unresolved"
        # One empty-list binding plus the loop target/ordinary local row names; the collection
        # itself may not be rebound, deleted, augmented, or aliased.
        collection_bindings = [
            node
            for statement in builder.owner.body
            for node in ast.walk(statement)
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            and any(
                isinstance(target, ast.Name) and target.id == builder.collection
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            )
        ]
        if len(collection_bindings) != 1:
            return "record-family-mutation-unresolved"
        initial = collection_bindings[0].value
        if not isinstance(initial, ast.List) or initial.elts:
            return "record-family-mutation-unresolved"
        direct_record_bindings: dict[str, list[ast.Assign | ast.AnnAssign]] = defaultdict(list)
        for node in ast.walk(builder.owner):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and target.id in record_names:
                        direct_record_bindings[target.id].append(node)
            if isinstance(node, ast.AugAssign) and _root_name(node.target) in tracked_names:
                return "record-family-mutation-unresolved"
            if isinstance(node, ast.Delete) and any(
                _root_name(target) in tracked_names for target in node.targets
            ):
                return "record-family-mutation-unresolved"
            if (
                isinstance(node, (ast.Assign, ast.AnnAssign))
                and node not in collection_bindings
                and node.value is not None
                and isinstance(node.value, ast.Name)
                and node.value.id in tracked_names
            ):
                return "record-family-mutation-unresolved"
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in tracked_names
                and node is not builder.append
            ):
                return "record-family-mutation-unresolved"
        if any(len(bindings) != 1 for bindings in direct_record_bindings.values()):
            return "record-family-mutation-unresolved"
        # Every crossing of a helper boundary is one exact X4 call site.
        if (
            isinstance(builder.owner, ast.FunctionDef)
            and len(calls.get(builder.owner.name, ())) != 1
        ):
            return "helper-call-site-reentry-unsupported"
        # Dynamic/unconditional stores and duplicate reaching stores are refused.
        stores: dict[tuple[str, str | int], list[ast.Assign | ast.AnnAssign]] = defaultdict(list)
        for node in ast.walk(builder.owner):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if not isinstance(target, ast.Subscript) or not isinstance(target.value, ast.Name):
                    continue
                key = _literal_key(target.slice)
                if key is None:
                    return "record-family-mutation-unresolved"
                stores[(target.value.id, key)].append(node)
                store_cursor: ast.AST = node
                while (
                    parent := parents.get(store_cursor)
                ) is not None and parent is not builder.owner:
                    if isinstance(parent, (ast.While, ast.Try, ast.Match)):
                        return "record-family-mutation-unresolved"
                    if isinstance(parent, ast.If):
                        # Exact record-flag and outcome-table branches are checked later; an
                        # unknown call/data-derived test is never folded here.
                        if any(isinstance(item, ast.Call) for item in ast.walk(parent.test)):
                            return "record-family-mutation-unresolved"
                    store_cursor = parent
        for store_nodes in stores.values():
            if len(store_nodes) <= 1:
                continue
            position_sets = [
                _store_positions(
                    item,
                    builder=builder,
                    tree=tree,
                    resolver=resolver,
                    outcome_columns=outcome_columns,
                )
                for item in store_nodes
            ]
            if any(value is None for value in position_sets):
                if builder.append is not None and all(
                    item.lineno < builder.append.lineno for item in store_nodes
                ):
                    return "record-family-mutation-unresolved"
                return "record-subset-position-unresolved"
            proved = cast(list[frozenset[int]], position_sets)
            if any(
                left & right for index, left in enumerate(proved) for right in proved[index + 1 :]
            ):
                return "correction-family-lineage-unresolved"
        # Section 6.4 is intentionally stricter than the executed shadow: within one proved
        # record-binding phase, any p/flag/table consumer closes the record to every later store.
        # The statement boundary matters: a p load on the RHS of the admitted store is evaluated
        # as part of that store, not as a preceding consumer.
        closed_fold_nodes: set[ast.AST] = set()
        for conditional in (node for node in ast.walk(builder.owner) if isinstance(node, ast.If)):
            test = conditional.test
            admitted_selector = (
                isinstance(test, ast.Subscript) and _literal_key(test.slice) is not None
            ) or (
                isinstance(test, ast.UnaryOp)
                and isinstance(test.op, ast.Not)
                and isinstance(test.operand, ast.Subscript)
                and _literal_key(test.operand.slice) is not None
            )
            if admitted_selector:
                closed_fold_nodes.update(ast.walk(conditional))
        consumers: list[tuple[tuple[int, int, int, int], ast.For | ast.ListComp | None]] = []
        for node in ast.walk(builder.owner):
            is_record_field = (
                isinstance(node, (ast.Subscript, ast.Attribute))
                and isinstance(node.ctx, ast.Load)
                and _root_name(node) in record_names
            )
            is_collection_load = (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id == builder.collection
            )
            if not (is_record_field or is_collection_load):
                continue
            if node in closed_fold_nodes:
                # Section 6.5 checks the exact static raw/adjusted or flag fold. Its selector is
                # not a terminal consumer of the record it selects.
                continue
            statement = _enclosing_statement(node, parents)
            if statement is None:
                continue
            if isinstance(statement, (ast.Assign, ast.AnnAssign)) and any(
                _root_name(target) in record_names
                for target in (
                    statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                )
            ):
                # A closed record-to-record field fold remains one construction operation; its
                # value lattice is checked below. Only a consumer outside that store closes it.
                continue
            consumers.append(
                (
                    _position(statement),
                    _enclosing_iteration(statement, parents, builder.owner),
                )
            )
        if builder.append is not None:
            statement = _enclosing_statement(builder.append, parents)
            if statement is not None:
                consumers.append(
                    (
                        _position(statement),
                        _enclosing_iteration(statement, parents, builder.owner),
                    )
                )
        for node in ast.walk(builder.owner):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            store_roots = {
                root for target in targets if (root := _root_name(target)) in tracked_names
            }
            if not store_roots:
                continue
            statement = _enclosing_statement(node, parents)
            if statement is None:
                continue
            store_position = _position(statement)
            store_iteration = _enclosing_iteration(statement, parents, builder.owner)
            iteration_targets = (
                frozenset(_target_names(store_iteration.target) or ())
                if isinstance(store_iteration, ast.For)
                else frozenset()
            )
            record_rebound = bool(store_roots & record_names & iteration_targets)
            if any(
                consumer_position < store_position
                and (
                    builder.collection in store_roots
                    or not record_rebound
                    or consumer_iteration is store_iteration
                )
                for consumer_position, consumer_iteration in consumers
            ):
                return "record-family-mutation-unresolved"
        if builder.wrapper_depth > 2:
            return "record-family-lineage-unresolved"
        if len(builder.schema) != len(set(builder.schema)):
            return "record-family-lineage-unresolved"
        # A record/collection passed to an unresolved external call is an escape. Calls to one
        # closed local helper are left to unchanged X4; known sinks/corrections/transports are okay.
        for node in ast.walk(builder.owner):
            if not isinstance(node, ast.Call) or node is builder.append:
                continue
            arguments = [*node.args, *(keyword.value for keyword in node.keywords)]
            if not any(
                isinstance(argument, ast.Name) and argument.id in tracked_names
                for argument in arguments
            ):
                continue
            api = resolver.qualified(node.func)
            local = node.func.id if isinstance(node.func, ast.Name) else None
            if (
                api
                in _CORRECTION_APIS
                | _REGISTERED_APIS
                | {"len", "enumerate", "list", "tuple", "zip", "print"}
                or local in functions
            ):
                continue
            return "record-family-mutation-unresolved"
    return None


def _correction_calls(tree: ast.Module, resolver: Any) -> tuple[ast.Call, ...]:
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and resolver.qualified(node.func) in _CORRECTION_APIS
    )


def _static_sequence_values(node: ast.expr, resolver: Any) -> tuple[object, ...] | None:
    values = resolver.sequence(node)
    if values is not None:
        return tuple(values)

    def value(item: ast.expr) -> object | None:
        literal = _literal(item, resolver)
        if literal is not None:
            return literal
        if not isinstance(item, ast.Subscript):
            return None
        member = _literal_key(item.slice)
        if not isinstance(member, int):
            return None
        if isinstance(item.value, ast.Name):
            sequence = resolver.tuples.get(item.value.id)
            table = resolver.tables.get(item.value.id)
            values_inner: Sequence[object] | None = sequence if sequence is not None else table
            if values_inner is None:
                return None
            index = member if member >= 0 else len(values_inner) + member
            return values_inner[index] if 0 <= index < len(values_inner) else None
        outer = value(item.value)
        if not isinstance(outer, tuple):
            return None
        index = member if member >= 0 else len(outer) + member
        return outer[index] if 0 <= index < len(outer) else None

    if not isinstance(node, (ast.List, ast.Tuple)):
        return None
    resolved = tuple(value(item) for item in node.elts)
    return None if any(item is None for item in resolved) else resolved


def _correction_positions(
    tree: ast.Module,
    resolver: Any,
    outcome_columns: tuple[str, ...],
    builders: Sequence[_RecordBuilder],
) -> tuple[tuple[int, ...], str | None]:
    calls = _correction_calls(tree, resolver)
    if not calls:
        return (), None
    if len(calls) != 1:
        return (), "correction-family-lineage-unresolved"
    call = calls[0]
    if not call.args:
        return (), "correction-family-lineage-unresolved"
    source = call.args[0]
    parents = _parents(tree)
    assignments: dict[str, ast.expr] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            if node.targets[0].id in assignments:
                assignments.pop(node.targets[0].id, None)
            else:
                assignments[node.targets[0].id] = node.value

    builders_by_name = {builder.collection for builder in builders}

    def boolean_positions() -> tuple[tuple[int, ...], ...]:
        candidates: list[tuple[int, ...]] = []
        for rows in _static_tables(tree, resolver, outcome_columns).values():
            for index in range(len(rows[0])):
                values = tuple(row[index] for row in rows)
                if all(isinstance(value, bool) for value in values):
                    candidates.append(tuple(i for i, value in enumerate(values) if value))
        return tuple(candidates)

    def resolve(node: ast.expr, active: frozenset[str] = frozenset()) -> tuple[int, ...] | None:
        if isinstance(node, ast.Name):
            if node.id in builders_by_name:
                return tuple(range(len(outcome_columns)))
            if node.id in active:
                return None
            value = assignments.get(node.id)
            return resolve(value, active | {node.id}) if value is not None else None
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            base = resolve(node.value, active)
            if base is None:
                return None
            start = _literal_int(node.slice.lower, resolver) if node.slice.lower else 0
            stop = _literal_int(node.slice.upper, resolver) if node.slice.upper else len(base)
            step = _literal_int(node.slice.step, resolver) if node.slice.step else 1
            if start is None or stop is None or step != 1 or not 0 <= start <= stop <= len(base):
                return None
            return base[start:stop]
        if isinstance(node, (ast.ListComp, ast.GeneratorExp)):
            if len(node.generators) != 1 or node.generators[0].is_async:
                return None
            generator = node.generators[0]
            base = resolve(generator.iter, active)
            if base is None:
                return None
            if not generator.ifs:
                return base
            if len(generator.ifs) != 1:
                return None
            flag = generator.ifs[0]
            inverted = isinstance(flag, ast.UnaryOp) and isinstance(flag.op, ast.Not)
            flag_value = flag.operand if isinstance(flag, ast.UnaryOp) and inverted else flag
            if not isinstance(flag_value, ast.Subscript) or _literal_key(flag_value.slice) is None:
                return None
            # Recover an immutable Boolean table column by value, never by key spelling.
            candidates = boolean_positions()
            if len(candidates) != 1:
                return None
            selected = set(candidates[0])
            if inverted:
                selected = set(range(len(outcome_columns))) - selected
            return tuple(position for position in base if position in selected)
        if isinstance(node, (ast.List, ast.Tuple)):
            if len(node.elts) == len(outcome_columns):
                return tuple(range(len(outcome_columns)))
            return None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                node.func.attr in {"tolist", "to_numpy"}
                and len(node.args) == 0
                and not node.keywords
            ):
                return resolve(node.func.value, active)
        if isinstance(node, ast.Subscript):
            return resolve(node.value, active)
        return None

    positions = resolve(source)
    if positions is None:
        # DataFrame loc/static-mask inputs are resolved separately.
        positions = _dataframe_correction_positions(tree, resolver, outcome_columns, source)
    if positions is None or len(set(positions)) != len(positions):
        return (), "correction-family-lineage-unresolved"
    if any(position < 0 or position >= len(outcome_columns) for position in positions):
        return (), "record-subset-position-unresolved"
    # Slice-of-slice is explicitly refused.
    if isinstance(source, ast.Subscript) and isinstance(source.value, ast.Subscript):
        return (), "record-subset-position-unresolved"
    _ = parents
    return positions, None


def _p_lineage(tree: ast.Module, resolver: Any) -> tuple[frozenset[str], frozenset[str | int]]:
    p_names: set[str] = set()
    result_names: set[str] = set()
    p_keys: set[str | int] = set()
    correction_names: set[str] = set()
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for key, member in zip(node.keys, node.values, strict=True):
                    if key is None:
                        continue
                    literal_key = _literal_key(key)
                    if literal_key is None:
                        continue
                    if any(
                        isinstance(item, ast.Name)
                        and isinstance(item.ctx, ast.Load)
                        and item.id in p_names | correction_names | result_names
                        for item in ast.walk(member)
                    ) or any(
                        isinstance(item, ast.Attribute) and item.attr == "pvalue"
                        for item in ast.walk(member)
                    ):
                        if literal_key not in p_keys:
                            p_keys.add(literal_key)
                            changed = True
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if isinstance(value, ast.Call) and resolver.qualified(value.func) in _REGISTERED_APIS:
                for target in targets:
                    if isinstance(target, ast.Name) and target.id not in result_names:
                        result_names.add(target.id)
                        changed = True
                    elif isinstance(target, (ast.Tuple, ast.List)) and len(target.elts) >= 2:
                        second = target.elts[1]
                        if isinstance(second, ast.Name) and second.id not in p_names:
                            p_names.add(second.id)
                            changed = True
            if (
                isinstance(value, ast.Attribute)
                and value.attr == "pvalue"
                and (
                    (
                        isinstance(value.value, ast.Call)
                        and resolver.qualified(value.value.func) in _REGISTERED_APIS
                    )
                    or (isinstance(value.value, ast.Name) and value.value.id in result_names)
                )
            ):
                for target in targets:
                    if isinstance(target, ast.Name) and target.id not in p_names:
                        p_names.add(target.id)
                        changed = True
            if isinstance(value, ast.Call) and resolver.qualified(value.func) in _CORRECTION_APIS:
                for target in targets:
                    if isinstance(target, ast.Name):
                        correction_names.add(target.id)
                    elif isinstance(target, (ast.Tuple, ast.List)):
                        for item in target.elts:
                            if isinstance(item, ast.Name):
                                correction_names.add(item.id)
            dependencies = (
                any(
                    isinstance(item, ast.Name)
                    and isinstance(item.ctx, ast.Load)
                    and item.id in p_names | correction_names | result_names
                    for item in ast.walk(value)
                )
                or any(
                    isinstance(item, ast.Attribute) and item.attr == "pvalue"
                    for item in ast.walk(value)
                )
                or any(
                    isinstance(item, ast.Subscript) and _literal_key(item.slice) in p_keys
                    for item in ast.walk(value)
                )
            )
            if dependencies:
                for target in targets:
                    if isinstance(target, ast.Name) and target.id not in p_names:
                        p_names.add(target.id)
                        changed = True
            if isinstance(value, ast.Dict):
                for key, member in zip(value.keys, value.values, strict=True):
                    if key is None:
                        continue
                    literal_key = _literal_key(key)
                    if literal_key is None:
                        continue
                    if (
                        any(
                            isinstance(item, ast.Name)
                            and isinstance(item.ctx, ast.Load)
                            and item.id in p_names | correction_names | result_names
                            for item in ast.walk(member)
                        )
                        or any(
                            isinstance(item, ast.Attribute) and item.attr == "pvalue"
                            for item in ast.walk(member)
                        )
                        or any(
                            isinstance(item, ast.Subscript) and _literal_key(item.slice) in p_keys
                            for item in ast.walk(member)
                        )
                    ):
                        if literal_key not in p_keys:
                            p_keys.add(literal_key)
                            changed = True
            for target in targets:
                if not isinstance(target, ast.Subscript):
                    continue
                target_key = _literal_key(target.slice)
                if target_key is None:
                    continue
                if dependencies and target_key not in p_keys:
                    p_keys.add(target_key)
                    changed = True
    return frozenset(p_names | correction_names), frozenset(p_keys)


def _p_derived(node: ast.expr, p_names: frozenset[str], p_keys: frozenset[str | int]) -> bool:
    return any(
        (isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id in p_names)
        or (isinstance(item, ast.Subscript) and _literal_key(item.slice) in p_keys)
        or (isinstance(item, ast.Attribute) and item.attr == "pvalue")
        for item in ast.walk(node)
    )


def _p_origin_tokens(
    node: ast.expr,
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
) -> frozenset[str]:
    tokens: set[str] = set()
    for item in ast.walk(node):
        if isinstance(item, ast.Subscript) and _literal_key(item.slice) in p_keys:
            tokens.add(ast.dump(item, annotate_fields=True, include_attributes=False))
        elif isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id in p_names:
            tokens.add(f"name:{item.id}")
        elif isinstance(item, ast.Attribute) and item.attr == "pvalue":
            tokens.add(ast.dump(item, annotate_fields=True, include_attributes=False))
    return frozenset(tokens)


def _manual_p_transform(
    node: ast.expr,
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
) -> bool:
    return any(
        (isinstance(item, ast.BinOp) and _p_derived(item, p_names, p_keys))
        or (
            isinstance(item, ast.Call)
            and _p_derived(item, p_names, p_keys)
            and (
                (isinstance(item.func, ast.Name) and item.func.id in {"min", "max"})
                or (
                    isinstance(item.func, ast.Attribute)
                    and item.func.attr in {"minimum", "maximum"}
                )
            )
        )
        for item in ast.walk(node)
    )


def _decision_signature(
    node: ast.expr,
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
) -> tuple[str, ast.expr, ast.expr] | None:
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
        return None
    left, right = node.left, node.comparators[0]
    left_p = _p_derived(left, p_names, p_keys)
    right_p = _p_derived(right, p_names, p_keys)
    if left_p == right_p:
        return None
    op = node.ops[0]
    if left_p:
        polarity = type(op).__name__
        return polarity, left, right
    reversed_polarity = {
        ast.Lt: "Gt",
        ast.LtE: "GtE",
        ast.Gt: "Lt",
        ast.GtE: "LtE",
    }
    reversed_operator = reversed_polarity.get(type(op))
    return (reversed_operator, right, left) if reversed_operator is not None else None


def _record_merge_reason(
    tree: ast.Module,
    resolver: Any,
) -> str | None:
    """Enforce the section-4.1 component merge lattice before coverage."""

    p_names, p_keys = _p_lineage(tree, resolver)
    for node in ast.walk(tree):
        if not isinstance(node, ast.IfExp):
            continue
        body_p = _p_derived(node.body, p_names, p_keys)
        else_p = _p_derived(node.orelse, p_names, p_keys)
        if not (body_p and else_p):
            continue
        body_signature = _decision_signature(node.body, p_names, p_keys)
        else_signature = _decision_signature(node.orelse, p_names, p_keys)
        if body_signature is not None and else_signature is not None:
            body_polarity, body_value, body_threshold = body_signature
            else_polarity, else_value, else_threshold = else_signature
            if body_polarity != else_polarity:
                return "record-decision-polarity-unresolved"
            if ast.dump(body_threshold, include_attributes=False) != ast.dump(
                else_threshold, include_attributes=False
            ):
                return "unresolved-decision-threshold"
        else:
            body_value, else_value = node.body, node.orelse
        body_origins = _p_origin_tokens(body_value, p_names, p_keys)
        else_origins = _p_origin_tokens(else_value, p_names, p_keys)
        if (
            not body_origins
            or not else_origins
            or len(body_origins) != 1
            or len(else_origins) != 1
            or body_origins != else_origins
            or _manual_p_transform(body_value, p_names, p_keys)
            != _manual_p_transform(else_value, p_names, p_keys)
        ):
            return "record-family-lineage-unresolved"
    return None


def _p_hierarchy_gate(tree: ast.Module, resolver: Any) -> int | None:
    p_names, p_keys = _p_lineage(tree, resolver)
    owners = _owners(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not _p_derived(node.test, p_names, p_keys):
            continue
        owner = owners.get(node)
        if isinstance(owner, ast.FunctionDef) and _presentation_function(owner):
            continue
        if any(
            isinstance(item, (ast.Return, ast.Break, ast.Continue, ast.Raise))
            or (
                isinstance(item, ast.Call)
                and resolver.qualified(item.func) in _REGISTERED_APIS | _CORRECTION_APIS
            )
            for statement in node.body
            for item in ast.walk(statement)
        ):
            return node.lineno
    return None


def _presentation_function(owner: ast.FunctionDef) -> bool:
    returns = [item.value for item in ast.walk(owner) if isinstance(item, ast.Return)]
    if not returns or any(value is None for value in returns):
        return False
    return all(
        isinstance(value, (ast.Constant, ast.JoinedStr))
        or (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Attribute)
            and value.func.attr == "format"
        )
        for value in returns
    )


def _dynamic_threshold_present(tree: ast.Module, resolver: Any) -> bool:
    assignments: dict[str, ast.expr] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            assignments[node.targets[0].id] = node.value
    p_names, p_keys = _p_lineage(tree, resolver)
    owners = _owners(tree)

    def presentation_helper(node: ast.Compare) -> bool:
        owner = owners.get(node)
        return isinstance(owner, ast.FunctionDef) and _presentation_function(owner)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or len(node.comparators) != 1:
            continue
        if presentation_helper(node):
            continue
        left, right = node.left, node.comparators[0]
        if _p_derived(left, p_names, p_keys) == _p_derived(right, p_names, p_keys):
            continue
        candidate = right if _p_derived(left, p_names, p_keys) else left
        if isinstance(candidate, ast.Constant) and isinstance(candidate.value, (int, float)):
            if float(candidate.value) != 0.05:
                return True
        elif isinstance(candidate, ast.Name):
            value = assignments.get(candidate.id)
            literal = _literal(candidate, resolver) if value is None else _literal(value, resolver)
            if not (isinstance(literal, (int, float)) and float(literal) == 0.05):
                return True
        else:
            return True
    return False


def _decision_from_coverage(
    *,
    positions: tuple[int, ...],
    outcome_columns: tuple[str, ...],
    dynamic_threshold: bool,
    models: tuple[str, ...],
    detail: Mapping[str, object],
) -> _ModelDecision:
    if len(positions) == len(outcome_columns):
        return _ModelDecision(
            _Outcome("covered", "complete", positions, len(outcome_columns)), models, detail
        )
    if dynamic_threshold:
        return _ModelDecision(_Outcome("abstain", "unresolved-decision-threshold"), models, detail)
    if positions:
        return _ModelDecision(
            _Outcome("candidate", "strict_subset", positions, len(outcome_columns)),
            models,
            detail,
        )
    return _ModelDecision(_Outcome("candidate", "none", (), len(outcome_columns)), models, detail)


def _record_decision(
    tree: ast.Module,
    resolver: Any,
    outcome_columns: tuple[str, ...],
    *,
    dispatch: _DispatchPlan | None,
) -> _ModelDecision | None:
    builders = _record_builders(tree, resolver, outcome_columns)
    functions_all = _functions(tree)

    def builder_has_registered_test(builder: _RecordBuilder) -> bool:
        for node in ast.walk(builder.loop):
            if not isinstance(node, ast.Call):
                continue
            if resolver.qualified(node.func) in _REGISTERED_APIS:
                return True
            if isinstance(node.func, ast.Name):
                function = functions_all.get(node.func.id)
                if function is not None and any(
                    isinstance(item, ast.Call) and resolver.qualified(item.func) in _REGISTERED_APIS
                    for item in ast.walk(function)
                ):
                    return True
        return False

    builders = tuple(builder for builder in builders if builder_has_registered_test(builder))
    if not builders:
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "append"
                and len(node.args) == 1
                and isinstance(node.args[0], ast.Tuple)
            ):
                continue
            nested = sum(isinstance(item, (ast.Dict, ast.Tuple)) for item in node.args[0].elts)
            if nested > 1 or (nested == 1 and len(node.args[0].elts) >= 3):
                return _ModelDecision(
                    _Outcome("abstain", "record-family-lineage-unresolved"),
                    ("record",),
                    {"competing_nested_line": node.lineno},
                )
        return None
    functions = _functions(tree)
    for builder in builders:
        if builder.append is None or not builder.append.args:
            continue
        argument = builder.append.args[0]
        if not isinstance(argument, ast.Tuple):
            continue
        record_members = 0
        for item in argument.elts:
            resolved = _resolve_record_expr(item, owner=builder.owner, functions=functions)
            if resolved is not None and _record_schema(resolved) is not None:
                record_members += 1
        if record_members > 1:
            return _ModelDecision(
                _Outcome("abstain", "record-family-lineage-unresolved"),
                ("record",),
                {"competing_nested_line": builder.append.lineno},
            )
    p_names, p_keys = _p_lineage(tree, resolver)
    parents = _parents(tree)
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.ListComp, ast.GeneratorExp))
            and any(
                _p_derived(condition, p_names, p_keys)
                for generator in node.generators
                for condition in generator.ifs
            )
            and not (
                isinstance(parents.get(node), ast.Call)
                and isinstance(cast(ast.Call, parents[node]).func, ast.Name)
                and cast(ast.Name, cast(ast.Call, parents[node]).func).id == "sum"
            )
        ):
            return _ModelDecision(
                _Outcome("abstain", "hierarchical-gatekeeping-present"),
                ("record", "positional-subset"),
                {"filter_line": node.lineno},
            )
    # Record schemas must be homogeneous within a collection. Two builders for one collection are
    # conditional/heterogeneous construction and never merge.
    schemas: dict[str, set[tuple[str | int, ...]]] = defaultdict(set)
    for builder in builders:
        schemas[builder.collection].add(builder.schema)
    if any(len(values) != 1 for values in schemas.values()):
        return _ModelDecision(
            _Outcome("abstain", "record-family-lineage-unresolved"),
            ("record",),
            {"schemas": {name: len(values) for name, values in schemas.items()}},
        )
    reason = _record_boundary_reason(tree, builders, resolver, outcome_columns)
    if reason is not None:
        return _ModelDecision(_Outcome("abstain", reason), ("record",), {"builders": len(builders)})
    merge_reason = _record_merge_reason(tree, resolver)
    if merge_reason is not None:
        return _ModelDecision(
            _Outcome("abstain", merge_reason),
            ("record",),
            {"builders": len(builders)},
        )
    # Exact competing p origins and unresolved post-construction p fields do not merge merely
    # because the enclosing record has a recognized schema.
    p_names, p_keys = _p_lineage(tree, resolver)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Subscript) or _literal_key(target.slice) is None:
            continue
        unresolved_call = any(
            isinstance(item, ast.Call)
            and resolver.qualified(item.func) not in _CORRECTION_APIS | _REGISTERED_APIS
            and not (
                isinstance(item.func, ast.Name)
                and item.func.id in {"float", "bool", "min", "max", "len"}
            )
            for item in ast.walk(node.value)
        )
        record_row_store = isinstance(target.value, ast.Name) and any(
            isinstance(builder.record, ast.Tuple) for builder in builders
        )
        if (_p_derived(node.value, p_names, p_keys) or record_row_store) and unresolved_call:
            return _ModelDecision(
                _Outcome("abstain", "record-family-lineage-unresolved"),
                ("record",),
                {"competing_field_line": node.lineno},
            )
    # Polarity and duplicate-emission attacks are structural and fail before coverage.
    for node in ast.walk(tree):
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            parent = _parents(tree).get(node)
            if isinstance(parent, (ast.If, ast.IfExp)) and any(
                isinstance(item, ast.Constant) and isinstance(item.value, str)
                for item in ast.walk(parent)
            ):
                # An explicit inverted display is accepted only if both arms are structurally
                # swapped. The closed grammar cannot prove that from a single-arm statement.
                if isinstance(parent, (ast.If, ast.IfExp)):
                    return _ModelDecision(
                        _Outcome("abstain", "record-decision-polarity-unresolved"),
                        ("record",),
                        {"polarity_line": node.lineno},
                    )
    positions, correction_reason = _correction_positions(tree, resolver, outcome_columns, builders)
    if correction_reason is not None:
        return _ModelDecision(
            _Outcome("abstain", correction_reason),
            ("record", "positional-subset") if _correction_calls(tree, resolver) else ("record",),
            {"builders": len(builders)},
        )
    if positions:
        assignments = {
            node.targets[0].id: node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        }
        bool_positions = _static_bool_position_sets(tree, resolver, outcome_columns)
        correction_names = _p_lineage(tree, resolver)[0]
        for loop in (node for node in ast.walk(tree) if isinstance(node, ast.For)):
            if not (
                isinstance(loop.iter, ast.Call)
                and resolver.qualified(loop.iter.func) == "zip"
                and len(loop.iter.args) >= 2
                and any(
                    isinstance(argument, ast.Name) and argument.id in correction_names
                    for argument in loop.iter.args[1:]
                )
            ):
                continue
            store_positions = _subset_positions(
                loop.iter.args[0],
                collection=builders[0].collection,
                assignments=assignments,
                resolver=resolver,
                outcome_columns=outcome_columns,
                bool_positions=bool_positions,
            )
            if store_positions is not None and tuple(sorted(store_positions)) != positions:
                return _ModelDecision(
                    _Outcome("abstain", "correction-family-lineage-unresolved"),
                    ("record", "positional-subset"),
                    {
                        "correction_positions": list(positions),
                        "store_positions": sorted(store_positions),
                    },
                )
    # More than two scientific decision emissions per collection are not admitted. Count only
    # comparisons/Boolean flag loads under accepted print payloads, not raw p formatting.
    p_names, p_keys = _p_lineage(tree, resolver)
    decision_names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        if not isinstance(node.value, (ast.Compare, ast.IfExp)) or not _p_derived(
            node.value, p_names, p_keys
        ):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        decision_names.update(target.id for target in targets if isinstance(target, ast.Name))
    decision_sinks = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not (
            isinstance(node.func, ast.Name) and node.func.id == "print"
        ):
            continue
        if any(
            any(
                isinstance(item, (ast.Compare, ast.IfExp)) and _p_derived(item, p_names, p_keys)
                for item in ast.walk(argument)
            )
            or any(
                isinstance(item, ast.Name)
                and isinstance(item.ctx, ast.Load)
                and item.id in decision_names
                for item in ast.walk(argument)
            )
            for argument in node.args
        ):
            decision_sinks += 1
    if decision_sinks > 2:
        return _ModelDecision(
            _Outcome("abstain", "record-duplicate-conclusion-ambiguous"),
            ("record",),
            {"decision_sink_sites": decision_sinks},
        )
    # A p-derived flag used to control a correction/test/store is not presentation.
    dispatch_nodes = (
        {_position(item) for item in ast.walk(dispatch.dispatch_if) if isinstance(item, ast.If)}
        if dispatch is not None
        else set()
    )
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        if _position(node) in dispatch_nodes:
            continue
        if any(
            isinstance(item, ast.Call)
            and resolver.qualified(item.func) in _CORRECTION_APIS | _REGISTERED_APIS
            for statement in node.body
            for item in ast.walk(statement)
        ):
            return _ModelDecision(
                _Outcome("abstain", "hierarchical-gatekeeping-present"),
                ("record",),
                {"guard_line": node.lineno},
            )
    models = ["record"]
    if positions and len(positions) < len(outcome_columns):
        models.append("positional-subset")
    if dispatch is not None:
        models.insert(0, "mixed-dispatch")
    detail: dict[str, object] = {
        "builders": len(builders),
        "schemas": {name: [list(next(iter(values)))] for name, values in schemas.items()},
        "corrected_positions": list(positions),
    }
    if dispatch is not None:
        detail["api_by_position"] = list(dispatch.api_by_position)
    return _decision_from_coverage(
        positions=positions,
        outcome_columns=outcome_columns,
        dynamic_threshold=_dynamic_threshold_present(tree, resolver),
        models=tuple(models),
        detail=detail,
    )


def _dataframe_names(tree: ast.Module, resolver: Any) -> set[str]:
    names: set[str] = set()
    functions = _functions(tree)

    def frame_call(call: ast.Call, active: frozenset[str] = frozenset()) -> bool:
        if resolver.qualified(call.func) in _DATAFRAME_APIS:
            return True
        if not isinstance(call.func, ast.Name) or call.func.id in active:
            return False
        function = functions.get(call.func.id)
        if function is None:
            return False
        returns = [item.value for item in ast.walk(function) if isinstance(item, ast.Return)]
        if len(returns) != 1 or returns[0] is None:
            return False
        returned = returns[0]
        if isinstance(returned, ast.Call):
            return frame_call(returned, active | {call.func.id})
        if isinstance(returned, ast.Name):
            parameters = [*function.args.posonlyargs, *function.args.args]
            for index, parameter in enumerate(parameters):
                if parameter.arg == returned.id and index < len(call.args):
                    argument = call.args[index]
                    return isinstance(argument, ast.Call) and frame_call(
                        argument, active | {call.func.id}
                    )
        return False

    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if (
                not isinstance(node, ast.Assign)
                or len(node.targets) != 1
                or not isinstance(node.targets[0], ast.Name)
            ):
                continue
            target = node.targets[0].id
            value = node.value
            source = False
            if isinstance(value, ast.Call) and frame_call(value):
                source = True
            elif isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
                root = value.func.value
                source = (
                    isinstance(root, ast.Name)
                    and root.id in names
                    and value.func.attr in {"copy", "drop"}
                )
            elif isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name):
                source = value.value.id in names and isinstance(
                    value.slice, (ast.List, ast.Tuple, ast.Name)
                )
            if source and target not in names:
                names.add(target)
                changed = True
    return names


def _dataframe_constructor_reason(tree: ast.Module, resolver: Any) -> str | None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or resolver.qualified(node.func) not in _DATAFRAME_APIS:
            continue
        if not 1 <= len(node.args) <= 2:
            return "dataframe-pvalue-table-unresolved"
        keyword_names = [item.arg for item in node.keywords]
        if (
            any(name not in {"columns"} for name in keyword_names)
            or keyword_names.count("columns") > 1
        ):
            return "dataframe-pvalue-table-unresolved"
        if len(node.args) == 2 and keyword_names:
            return "dataframe-pvalue-table-unresolved"
        if len(node.args) == 1 and keyword_names:
            columns = node.keywords[0].value
            values = _static_sequence_values(columns, resolver)
            if values is None or len(values) != len(set(values)) or len(values) > 32:
                return "dataframe-pvalue-table-unresolved"
        if len(node.args) == 2:
            values = _static_sequence_values(node.args[1], resolver)
            if values is None or len(values) != len(set(values)) or len(values) > 32:
                return "dataframe-pvalue-table-unresolved"
    return None


def _dataframe_boundary_reason(tree: ast.Module, resolver: Any) -> str | None:
    reason = _dataframe_constructor_reason(tree, resolver)
    if reason is not None:
        return reason
    names = _dataframe_names(tree, resolver)
    if not names:
        return None
    _p_names, p_keys = _p_lineage(tree, resolver)
    p_table_names = {
        node.value.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id in names
        and _literal_key(node.slice) in p_keys
    }
    if p_table_names:
        names = p_table_names
    parents = _parents(tree)
    functions = _functions(tree)
    calls = _calls_of(functions, tree)
    assignments = {
        node.targets[0].id: node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda) and any(
            isinstance(item, (ast.BinOp, ast.Compare)) for item in ast.walk(node.body)
        ):
            parent = parents.get(node)
            if isinstance(parent, ast.keyword) and parent.arg == "float_format":
                return "dataframe-pvalue-table-unresolved"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Delete, ast.AugAssign)) and any(
            isinstance(item, ast.Name) and item.id in names for item in ast.walk(node)
        ):
            return "dataframe-pvalue-table-unresolved"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr
            root_names = {
                item.id
                for item in ast.walk(node.func.value)
                if isinstance(item, ast.Name) and item.id in names
            }
            if not root_names:
                continue
            if method in _REFUSED_FRAME_METHODS:
                return "dataframe-pvalue-table-unresolved"
            if (
                method == "append"
                and len(node.args) == 1
                and isinstance(node.args[0], (ast.Dict, ast.Tuple))
            ):
                continue
            if method not in _ALLOWED_FRAME_METHODS | _ALLOWED_SERIES_METHODS:
                return "dataframe-pvalue-table-unresolved"
            if method == "copy" and (node.args or node.keywords):
                return "dataframe-pvalue-table-unresolved"
            if method == "drop" and (
                node.args
                or len(node.keywords) != 1
                or node.keywords[0].arg != "columns"
                or _static_sequence_values(node.keywords[0].value, resolver) is None
            ):
                return "dataframe-pvalue-table-unresolved"
            if method in {"tolist", "to_numpy", "itertuples", "iterrows"} and (
                node.args or node.keywords
            ):
                return "dataframe-pvalue-table-unresolved"
            if method == "where" and node.args and isinstance(node.args[0], ast.Compare):
                return "dataframe-pvalue-table-unresolved"
        if (
            not isinstance(node, ast.Name)
            or not isinstance(node.ctx, ast.Load)
            or node.id not in names
        ):
            continue
        parent = parents.get(node)
        if isinstance(parent, (ast.Subscript, ast.Attribute, ast.Return)):
            continue
        if isinstance(parent, ast.Call):
            if resolver.qualified(parent.func) in _DATAFRAME_APIS:
                continue
            if isinstance(parent.func, ast.Name) and parent.func.id in functions:
                if len(calls.get(parent.func.id, ())) != 1:
                    return "dataframe-pvalue-table-unresolved"
                continue
            return "dataframe-pvalue-table-unresolved"
        if isinstance(parent, (ast.Assign, ast.AnnAssign)) and parent.value is node:
            return "dataframe-pvalue-table-unresolved"
        if isinstance(parent, ast.For):
            continue
    # Boolean row subscripts and dynamic loc/iloc stores are outside the model.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript):
            continue
        roots = [
            item.id
            for item in ast.walk(node.value)
            if isinstance(item, ast.Name) and item.id in names
        ]
        if not roots:
            continue
        if isinstance(node.value, ast.Attribute) and node.value.attr == "iloc":
            if _literal_key(node.slice) is None:
                return "dataframe-pvalue-table-unresolved"
            continue
        if isinstance(node.slice, ast.Slice):
            return "dataframe-pvalue-table-unresolved"
        if isinstance(node.slice, (ast.Compare, ast.BoolOp, ast.UnaryOp)):
            return "dataframe-pvalue-table-unresolved"
        parent = parents.get(node)
        if isinstance(parent, (ast.Assign, ast.AnnAssign)) and node in (
            parent.targets if isinstance(parent, ast.Assign) else [parent.target]
        ):
            if isinstance(node.value, ast.Attribute) and node.value.attr in {"loc", "iloc"}:
                selection = node.slice
                if not isinstance(selection, ast.Tuple) or len(selection.elts) != 2:
                    return "dataframe-pvalue-table-unresolved"
                mask = selection.elts[0]
                if isinstance(mask, ast.Name):
                    mask = assignments.get(mask.id, mask)
                if not (
                    isinstance(mask, ast.Call)
                    and isinstance(mask.func, ast.Attribute)
                    and mask.func.attr == "isin"
                    and len(mask.args) == 1
                    and not mask.keywords
                    and _static_sequence_values(
                        assignments.get(mask.args[0].id, mask.args[0])
                        if isinstance(mask.args[0], ast.Name)
                        else mask.args[0],
                        resolver,
                    )
                    is not None
                ):
                    return "dataframe-pvalue-table-unresolved"
    return None


def _dataframe_correction_positions(
    tree: ast.Module,
    resolver: Any,
    outcome_columns: tuple[str, ...],
    source: ast.expr,
) -> tuple[int, ...] | None:
    assignments = {
        node.targets[0].id: node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }

    def dereference(node: ast.expr, active: frozenset[str] = frozenset()) -> ast.expr | None:
        if isinstance(node, ast.Name) and node.id in assignments:
            if node.id in active:
                return None
            return dereference(assignments[node.id], active | {node.id})
        return node

    # Full static p column, optionally transported by to_numpy/tolist.
    resolved = dereference(source)
    if resolved is None:
        return None
    cursor = resolved
    if (
        isinstance(cursor, ast.Call)
        and isinstance(cursor.func, ast.Attribute)
        and cursor.func.attr in {"tolist", "to_numpy"}
    ):
        if cursor.args or cursor.keywords:
            return None
        cursor = cursor.func.value
    if isinstance(cursor, ast.Subscript):
        if isinstance(cursor.value, ast.Name) and _literal_key(cursor.slice) is not None:
            return tuple(range(len(outcome_columns)))
        if isinstance(cursor.value, ast.Attribute) and cursor.value.attr == "loc":
            selection = cursor.slice
            if not isinstance(selection, ast.Tuple) or len(selection.elts) != 2:
                return None
            mask = selection.elts[0]
            if isinstance(mask, ast.Name):
                mask = assignments.get(mask.id, mask)
            if (
                isinstance(mask, ast.Call)
                and isinstance(mask.func, ast.Attribute)
                and mask.func.attr == "isin"
                and len(mask.args) == 1
                and not mask.keywords
            ):
                values_expr = dereference(mask.args[0])
                values = (
                    _static_sequence_values(values_expr, resolver)
                    if values_expr is not None
                    else None
                )
                if values is None or len(values) != len(set(values)):
                    return None
                if not set(values).issubset(outcome_columns):
                    return None
                return tuple(
                    index for index, value in enumerate(outcome_columns) if value in values
                )
    return None


def _dataframe_decision(
    tree: ast.Module,
    resolver: Any,
    outcome_columns: tuple[str, ...],
) -> _ModelDecision | None:
    if not any(
        isinstance(node, ast.Call) and resolver.qualified(node.func) in _DATAFRAME_APIS
        for node in ast.walk(tree)
    ):
        return None
    names = _dataframe_names(tree, resolver)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"to_csv", "savetxt", "dump"}
            and any(
                isinstance(item, ast.Name) and item.id in names
                for item in ast.walk(node.func.value)
            )
        ):
            return _ModelDecision(
                _Outcome("abstain", "unresolved-pvalue-consumer"),
                ("dataframe",),
                {"export_line": node.lineno},
            )
    p_names, p_keys = _p_lineage(tree, resolver)
    for function in _functions(tree).values():
        parameters = {item.arg for item in (*function.args.posonlyargs, *function.args.args)}
        if not parameters:
            continue
        p_call_site = any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == function.name
            and any(_p_derived(argument, p_names, p_keys) for argument in call.args)
            for call in ast.walk(tree)
        )
        direct_formal_transform = any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id not in {"float", "bool", "int", "str", "min", "max", "len"}
            and any(
                isinstance(argument, ast.Name) and argument.id in parameters
                for argument in call.args
            )
            for call in ast.walk(function)
        ) and any(
            isinstance(compare, ast.Compare)
            and any(
                isinstance(item, ast.Name) and item.id in parameters for item in ast.walk(compare)
            )
            for compare in ast.walk(function)
        )
        if (p_call_site or direct_formal_transform) and any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id not in {"float", "bool", "int", "str", "min", "max", "len", "print"}
            and call.func.id not in _functions(tree)
            and any(
                isinstance(item, ast.Name) and item.id in parameters
                for argument in call.args
                for item in ast.walk(argument)
            )
            for call in ast.walk(function)
        ):
            return _ModelDecision(
                _Outcome("abstain", "unresolved-pvalue-consumer"),
                ("dataframe",),
                {"unresolved_helper": function.name},
            )
    reason = _dataframe_boundary_reason(tree, resolver)
    if reason is not None:
        return _ModelDecision(_Outcome("abstain", reason), ("dataframe",), {})
    positions, correction_reason = _correction_positions(tree, resolver, outcome_columns, ())
    if correction_reason is not None:
        return _ModelDecision(_Outcome("abstain", correction_reason), ("dataframe",), {})
    return _decision_from_coverage(
        positions=positions,
        outcome_columns=outcome_columns,
        dynamic_threshold=_dynamic_threshold_present(tree, resolver),
        models=("dataframe",),
        detail={"corrected_positions": list(positions)},
    )


def analyze_record_model(content: bytes, **kwargs: Any) -> RecordModelResult:
    outcome_columns = tuple(cast(tuple[str, ...], kwargs["outcome_columns"]))
    baseline_result = mt._analyze_code_csv_multiple_testing_baseline(content, **kwargs)
    baseline = _classify(baseline_result)
    try:
        triggers = strict_trigger_shapes(content, outcome_columns)
    except ValueError:
        triggers = ()
    if baseline.reason_or_classification == "api-resolution-ambiguous":
        return RecordModelResult(baseline, baseline, False, (), triggers, {})
    detail: dict[str, object] = {}

    d14_content = _d14_rewrite(content, outcome_columns)
    d14_changed = d14_content != content
    effective_content = d14_content
    effective_tree = mt._bounded_parse(effective_content)
    try:
        effective_resolver = _resolver(effective_tree)
    except ValueError as error:
        outcome = _Outcome("abstain", str(error))
        return RecordModelResult(outcome, baseline, outcome != baseline, (), triggers, {})
    effective_result = (
        mt._analyze_code_csv_multiple_testing_baseline(effective_content, **kwargs)
        if d14_changed
        else baseline_result
    )
    effective = _classify(effective_result)
    if d14_changed:
        detail["d14_surrogate"] = "singleton projection generator substituted exactly once"

    dispatch = _dispatch_plan(effective_tree, effective_resolver, outcome_columns)
    if baseline.reason_or_classification == "mixed-test-api-family" and dispatch is None:
        outcome = _Outcome("abstain", "family-test-api-dispatch-unresolved")
        return RecordModelResult(
            outcome,
            baseline,
            True,
            ("mixed-dispatch",),
            triggers,
            {**detail, "dispatch_refusal": "family-test-api-dispatch-unresolved"},
        )
    if baseline.reason_or_classification == "authorized-family-test-census-incomplete" and (
        dispatch is None or (dispatch.refusal is not None and not dispatch.selected_body)
    ):
        return RecordModelResult(baseline, baseline, False, (), triggers, detail)
    if dispatch is not None and dispatch.refusal is not None:
        decision = _ModelDecision(
            _Outcome("abstain", dispatch.refusal),
            ("mixed-dispatch",),
            {"dispatch_refusal": dispatch.refusal},
        )
        return RecordModelResult(
            decision.outcome,
            baseline,
            decision.outcome != baseline,
            decision.models,
            triggers,
            decision.detail,
        )
    if dispatch is not None:
        lowered = _lower_dispatch(effective_content, dispatch)
        downstream_result = mt._analyze_code_csv_multiple_testing_baseline(lowered, **kwargs)
        downstream = _classify(downstream_result)
        detail["dispatch_api_by_position"] = list(dispatch.api_by_position)
        detail["dispatch_surrogate_outcome"] = downstream.as_json()
        effective = downstream

    hierarchy_line = _p_hierarchy_gate(effective_tree, effective_resolver)
    if hierarchy_line is not None:
        outcome = _Outcome("abstain", "hierarchical-gatekeeping-present")
        return RecordModelResult(
            outcome,
            baseline,
            outcome != baseline,
            tuple(("d14-a",) if d14_changed else ())
            + tuple(("mixed-dispatch",) if dispatch is not None else ()),
            triggers,
            {**detail, "hierarchy_line": hierarchy_line},
        )

    # A pre-record/pre-table guard remains first unless it is precisely one of the walls the
    # commissioned models own. This preserves every global census and earlier slice decision.
    if effective.state == "abstain" and effective.reason_or_classification not in _TARGET_REASONS:
        models = ("d14-a",) if d14_changed and effective != baseline else ()
        return RecordModelResult(
            effective,
            baseline,
            effective != baseline,
            models,
            triggers,
            detail,
        )

    dataframe = _dataframe_decision(effective_tree, effective_resolver, outcome_columns)
    if dataframe is not None and effective.reason_or_classification == "unresolved-pvalue-consumer":
        return RecordModelResult(
            dataframe.outcome,
            baseline,
            dataframe.outcome != baseline,
            tuple(("d14-a",) if d14_changed else ()) + dataframe.models,
            triggers,
            {**detail, **dataframe.detail},
        )

    record = _record_decision(
        effective_tree,
        effective_resolver,
        outcome_columns,
        dispatch=dispatch,
    )
    if record is not None and effective.reason_or_classification in {
        "pvalue-family-collection-unresolved",
        "unresolved-pvalue-consumer",
        "correction-family-lineage-unresolved",
        "authorized-family-test-census-incomplete",
        "mixed-test-api-family",
    }:
        return RecordModelResult(
            record.outcome,
            baseline,
            record.outcome != baseline,
            tuple(("d14-a",) if d14_changed else ()) + record.models,
            triggers,
            {**detail, **record.detail},
        )

    if dispatch is not None and effective != baseline:
        return RecordModelResult(
            effective,
            baseline,
            True,
            (*(("d14-a",) if d14_changed else ()), "mixed-dispatch"),
            triggers,
            detail,
        )
    if d14_changed and effective != baseline:
        return RecordModelResult(effective, baseline, True, ("d14-a",), triggers, detail)
    return RecordModelResult(baseline, baseline, False, (), triggers, detail)
