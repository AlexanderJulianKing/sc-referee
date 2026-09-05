"""Strict shadow proofs for the MT 3.3 design commission.

The shadow never classifies a family.  It proves one terminal-presentation or
single-call helper-record production, lowers only that proved production, and
asks the shipped 3.2 analyzer to classify the resulting structural surrogate.
"""

from __future__ import annotations

import ast
import copy
import hashlib
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, cast

from harness import Outcome, classify

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 as frozen
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_2 import (
    analyze_code_csv_multiple_testing_dataflow,
)

_CORRECTION_TERMINALS = frozenset(
    {
        "multipletests",
        "fdrcorrection",
        "false_discovery_control",
        "multicomp",
        "fdr_correction",
        "p_adjust",
        "padjust",
        "bonferroni",
        "holm",
        "sidak",
    }
)
_OUTPUT_NAMES = frozenset({"print"})
_IDENTITY_WRAPPERS = frozenset({"bool", "float"})


@dataclass(frozen=True)
class ShadowResult:
    outcome: Outcome
    baseline: Outcome
    changed: bool
    attempted: bool
    models: tuple[str, ...]
    detail: Mapping[str, object]
    surrogate_sha256: str | None


def _position(node: ast.AST) -> tuple[int, int, int, int]:
    return (
        getattr(node, "lineno", -1),
        getattr(node, "col_offset", -1),
        getattr(node, "end_lineno", -1),
        getattr(node, "end_col_offset", -1),
    )


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _owner(node: ast.AST, parents: Mapping[ast.AST, ast.AST]) -> ast.AST:
    cursor = node
    while cursor in parents:
        cursor = parents[cursor]
        if isinstance(cursor, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            return cursor
    return cursor


def _enclosing(
    node: ast.AST, parents: Mapping[ast.AST, ast.AST], kinds: tuple[type[ast.AST], ...]
) -> ast.AST | None:
    cursor = node
    while cursor in parents:
        cursor = parents[cursor]
        if isinstance(cursor, kinds):
            return cursor
    return None


def _literal_key(node: ast.expr) -> str | int | None:
    return (
        node.value
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, int))
        else None
    )


def _display_string(node: ast.expr) -> bool:
    return bool(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value
        and "\x00" not in node.value
        and len(node.value.encode("utf-8")) <= 256
    )


def _functions(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def _resolver(tree: ast.Module) -> Any:
    scope = tuple(item for item in tree.body if not frozen._is_docstring(item))
    resolver, reason = frozen._resolver(scope)
    if reason is not None or resolver is None:
        raise ValueError(reason or "api-resolution-ambiguous")
    return resolver


def _registered_call(node: ast.AST, resolver: Any) -> bool:
    return bool(
        isinstance(node, ast.Call) and resolver.qualified(node.func) in frozen._MT_TEST_APIS
    )


def _contains_registered_call(
    node: ast.AST, resolver: Any, functions: Mapping[str, ast.FunctionDef]
) -> bool:
    for item in ast.walk(node):
        if _registered_call(item, resolver):
            return True
        if isinstance(item, ast.Call) and isinstance(item.func, ast.Name):
            helper = functions.get(item.func.id)
            if helper is not None and any(
                _registered_call(child, resolver) for child in ast.walk(helper)
            ):
                return True
    return False


def _correction_terminal_present(tree: ast.Module, resolver: Any) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        terminal: str | None = None
        if isinstance(node.func, ast.Name):
            terminal = node.func.id
        elif isinstance(node.func, ast.Attribute):
            terminal = node.func.attr
        qualified = resolver.qualified(node.func)
        if terminal in _CORRECTION_TERMINALS or (
            isinstance(terminal, str) and terminal.startswith("benjamini")
        ):
            return True
        if qualified in frozen._MT_CORRECTION_APIS:
            return True
    return False


def _reaches_print(node: ast.AST, parents: Mapping[ast.AST, ast.AST]) -> bool:
    cursor = node
    for _ in range(16):
        parent = parents.get(cursor)
        if parent is None:
            return False
        if isinstance(parent, ast.Call):
            if isinstance(parent.func, ast.Name) and parent.func.id in _OUTPUT_NAMES:
                return True
            if isinstance(parent.func, ast.Attribute) and parent.func.attr in {"format", "join"}:
                cursor = parent
                continue
            return False
        if isinstance(parent, (ast.FormattedValue, ast.JoinedStr, ast.BinOp, ast.Tuple, ast.List)):
            cursor = parent
            continue
        return False
    return False


def _statement_for(node: ast.AST, parents: Mapping[ast.AST, ast.AST]) -> ast.stmt | None:
    cursor: ast.AST | None = node
    while cursor is not None and not isinstance(cursor, ast.stmt):
        cursor = parents.get(cursor)
    return cast(ast.stmt | None, cursor)


def _stores(node: ast.AST) -> frozenset[str]:
    return frozenset(
        item.id
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, (ast.Store, ast.Del))
    )


def _loads(tree: ast.AST, name: str) -> tuple[ast.Name, ...]:
    return tuple(
        item
        for item in ast.walk(tree)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load) and item.id == name
    )


def _call_sites(tree: ast.Module, name: str) -> tuple[ast.Call, ...]:
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name
    )


def _later_test_or_helper(
    owner: ast.FunctionDef,
    control: ast.AST,
    resolver: Any,
    functions: Mapping[str, ast.FunctionDef],
) -> bool:
    control_position = _position(control)
    return any(
        _position(node) > control_position
        and (
            _registered_call(node, resolver)
            or (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in functions
                and _contains_registered_call(functions[node.func.id], resolver, functions)
            )
        )
        for node in ast.walk(owner)
    )


def _contains_early_exit(node: ast.AST, resolver: Any) -> bool:
    return any(
        isinstance(item, (ast.Return, ast.Raise, ast.Break, ast.Continue, ast.Yield, ast.YieldFrom))
        or (isinstance(item, ast.Call) and resolver.qualified(item.func) == "sys.exit")
        for item in ast.walk(node)
    )


def _later_controlled_exit(
    owner: ast.FunctionDef,
    control: ast.AST,
    parents: Mapping[ast.AST, ast.AST],
    resolver: Any,
) -> bool:
    """Refuse every later exit nested under a control edge; a final bare return is harmless."""

    for item in ast.walk(owner):
        if _position(item) <= _position(control):
            continue
        is_exit = isinstance(item, (ast.Return, ast.Raise, ast.Break, ast.Continue)) or (
            isinstance(item, ast.Call) and resolver.qualified(item.func) == "sys.exit"
        )
        if not is_exit:
            continue
        cursor: ast.AST = item
        while cursor in parents and parents[cursor] is not owner:
            cursor = parents[cursor]
            if isinstance(
                cursor,
                (
                    ast.If,
                    ast.IfExp,
                    ast.For,
                    ast.AsyncFor,
                    ast.While,
                    ast.Match,
                    ast.match_case,
                    ast.comprehension,
                    ast.Try,
                    ast.With,
                    ast.AsyncWith,
                ),
            ):
                return True
    return False


def _simple_presentation_body(
    statements: Sequence[ast.stmt],
    *,
    owner: ast.FunctionDef,
    tree: ast.Module,
    parents: Mapping[ast.AST, ast.AST],
    resolver: Any,
    functions: Mapping[str, ast.FunctionDef],
) -> bool:
    local_stores: set[str] = set()
    output_count = 0
    for statement in statements:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            if len(targets) != 1 or not isinstance(targets[0], ast.Name):
                return False
            value = statement.value
            if value is None or any(
                isinstance(item, (ast.Await, ast.Yield, ast.YieldFrom, ast.NamedExpr))
                for item in ast.walk(value)
            ):
                return False
            if not (
                _display_string(value)
                or (
                    isinstance(value, ast.IfExp)
                    and _display_string(value.body)
                    and _display_string(value.orelse)
                    and isinstance(value.test, ast.Compare)
                    and not any(isinstance(item, ast.Call) for item in ast.walk(value.test))
                )
            ):
                return False
            local_stores.add(targets[0].id)
            continue
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id in _OUTPUT_NAMES
            and not statement.value.keywords
        ):
            return False
        if [item for item in ast.walk(statement) if isinstance(item, ast.Call)] != [
            statement.value
        ]:
            return False
        output_count += 1
        if _contains_registered_call(statement, resolver, functions):
            return False
    for name in local_stores:
        bindings = [
            item
            for item in ast.walk(owner)
            if isinstance(item, ast.Name)
            and isinstance(item.ctx, (ast.Store, ast.Del))
            and item.id == name
        ]
        if len(bindings) != 1:
            return False
        for load in _loads(owner, name):
            statement = _statement_for(load, parents)
            if statement not in statements or not _reaches_print(load, parents):
                return False
    return bool(
        output_count == 1
        and not _contains_early_exit(ast.Module(body=list(statements), type_ignores=[]), resolver)
    )


def _terminal_if_positions(
    tree: ast.Module, resolver: Any
) -> tuple[tuple[int, int, int, int], ...]:
    parents = _parents(tree)
    functions = _functions(tree)
    p_names, p_keys = _structural_p_roots(tree, resolver)
    result: list[tuple[int, int, int, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        loop = _enclosing(node, parents, (ast.For,))
        if not (
            isinstance(loop, ast.For)
            and node in loop.body
            and isinstance(loop.target, ast.Name)
            and isinstance(loop.iter, ast.Name)
            and not loop.orelse
        ):
            continue
        compare_operands = (
            (node.test.left, node.test.comparators[0])
            if isinstance(node.test, ast.Compare) and len(node.test.comparators) == 1
            else ()
        )
        record_p_operands = [
            operand
            for operand in compare_operands
            if isinstance(operand, ast.Subscript)
            and isinstance(operand.value, ast.Name)
            and operand.value.id == loop.target.id
            and _literal_key(operand.slice) in p_keys
        ]
        if len(record_p_operands) != 1:
            continue
        owner = _owner(node, parents)
        if not isinstance(owner, ast.FunctionDef) or owner.name != "main":
            continue
        if not _single_p_compare(node.test, p_names, p_keys):
            continue
        if (
            _contains_early_exit(node, resolver)
            or _later_test_or_helper(owner, node, resolver, functions)
            or _later_controlled_exit(owner, node, parents, resolver)
        ):
            continue
        if not _simple_presentation_body(
            node.body,
            owner=owner,
            tree=tree,
            parents=parents,
            resolver=resolver,
            functions=functions,
        ) or not _simple_presentation_body(
            node.orelse,
            owner=owner,
            tree=tree,
            parents=parents,
            resolver=resolver,
            functions=functions,
        ):
            continue
        result.append(_position(node.test))
    return tuple(result)


def _dict_field_for_name(
    node: ast.IfExp,
    name: str,
    parents: Mapping[ast.AST, ast.AST],
) -> tuple[str, str | int] | None:
    owner_loop = _enclosing(node, parents, (ast.For,))
    if not isinstance(owner_loop, ast.For):
        return None
    for call in ast.walk(owner_loop):
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.attr == "append"
            and len(call.args) == 1
            and not call.keywords
            and isinstance(call.args[0], ast.Dict)
        ):
            continue
        for key, value in zip(call.args[0].keys, call.args[0].values, strict=True):
            if key is None or not isinstance(value, ast.Name) or value.id != name:
                continue
            literal = _literal_key(key)
            if literal is not None:
                return call.func.value.id, literal
    return None


def _structural_p_roots(
    tree: ast.Module, resolver: Any
) -> tuple[frozenset[str], frozenset[str | int]]:
    """Derive p names and record keys from registered calls, never from spelling."""

    p_names: set[str] = set()
    result_names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if len(targets) != 1 or not _registered_call(node.value, resolver):
            continue
        target = targets[0]
        if isinstance(target, ast.Name):
            result_names.add(target.id)
        elif (
            isinstance(target, (ast.Tuple, ast.List))
            and len(target.elts) == 2
            and isinstance(target.elts[1], ast.Name)
        ):
            p_names.add(target.elts[1].id)
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if len(targets) != 1 or not isinstance(targets[0], ast.Name):
                continue
            value = node.value
            derived = isinstance(value, ast.Name) and value.id in p_names
            derived = derived or bool(
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id in _IDENTITY_WRAPPERS
                and len(value.args) == 1
                and not value.keywords
                and isinstance(value.args[0], ast.Name)
                and value.args[0].id in p_names
            )
            if derived and targets[0].id not in p_names:
                p_names.add(targets[0].id)
                changed = True

    def p_value(value: ast.expr) -> bool:
        if isinstance(value, ast.Name):
            return value.id in p_names
        if (
            isinstance(value, ast.Attribute)
            and value.attr == "pvalue"
            and isinstance(value.value, ast.Name)
        ):
            return value.value.id in result_names
        return bool(
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id in _IDENTITY_WRAPPERS
            and len(value.args) == 1
            and not value.keywords
            and p_value(value.args[0])
        )

    keys: set[str | int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values, strict=True):
            if key is None:
                continue
            literal = _literal_key(key)
            if literal is not None and p_value(value):
                keys.add(literal)
    return frozenset(p_names), frozenset(keys)


def _single_p_compare(
    node: ast.expr,
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
) -> bool:
    if not (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], (ast.Lt, ast.LtE, ast.Gt, ast.GtE))
        and len(node.comparators) == 1
    ):
        return False

    def is_p(value: ast.expr) -> bool:
        if isinstance(value, ast.Name):
            return value.id in p_names
        if isinstance(value, ast.Subscript):
            return _literal_key(value.slice) in p_keys
        return bool(
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id in _IDENTITY_WRAPPERS
            and len(value.args) == 1
            and not value.keywords
            and is_p(value.args[0])
        )

    return sum(is_p(value) for value in (node.left, node.comparators[0])) == 1


def _collection_terminal_safe(
    tree: ast.Module,
    owner: ast.FunctionDef,
    collection: str,
    parents: Mapping[ast.AST, ast.AST],
) -> bool:
    bindings = [
        node
        for node in ast.walk(owner)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(target, ast.Name) and target.id == collection
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        )
    ]
    if not (
        len(bindings) == 1
        and isinstance(bindings[0].value, ast.List)
        and not bindings[0].value.elts
    ):
        return False
    calls = _call_sites(tree, owner.name)
    return_values_ignored = bool(calls) and all(
        isinstance(parents.get(call), ast.Expr) for call in calls
    )
    for load in _loads(owner, collection):
        parent = parents.get(load)
        grandparent = parents.get(parent) if parent is not None else None
        if (
            isinstance(parent, ast.Attribute)
            and parent.value is load
            and parent.attr == "append"
            and isinstance(grandparent, ast.Call)
            and grandparent.func is parent
        ):
            continue
        if isinstance(parent, ast.comprehension) and parent.iter is load:
            continue
        if (
            isinstance(parent, ast.Call)
            and isinstance(parent.func, ast.Name)
            and parent.func.id == "len"
            and len(parent.args) == 1
            and not parent.keywords
            and _reaches_print(parent, parents)
        ):
            continue
        if isinstance(parent, ast.Return) and parent.value is load and return_values_ignored:
            continue
        return False
    return True


def _terminal_count_for_field(
    tree: ast.Module,
    *,
    collection: str,
    field: str | int,
    parents: Mapping[ast.AST, ast.AST],
) -> bool:
    matching_loads = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript) or _literal_key(node.slice) != field:
            continue
        loop = _enclosing(node, parents, (ast.GeneratorExp,))
        if not isinstance(loop, ast.GeneratorExp) or len(loop.generators) != 1:
            return False
        generator = loop.generators[0]
        condition = generator.ifs[0] if len(generator.ifs) == 1 else None
        field_is_left = bool(
            isinstance(condition, ast.Compare)
            and condition.left is node
            and len(condition.comparators) == 1
            and _display_string(condition.comparators[0])
        )
        field_is_right = bool(
            isinstance(condition, ast.Compare)
            and len(condition.comparators) == 1
            and condition.comparators[0] is node
            and _display_string(condition.left)
        )
        if not (
            not generator.is_async
            and len(generator.ifs) == 1
            and node in ast.walk(generator.ifs[0])
            and isinstance(generator.target, ast.Name)
            and isinstance(node.value, ast.Name)
            and node.value.id == generator.target.id
            and isinstance(generator.iter, ast.Name)
            and generator.iter.id == collection
            and isinstance(condition, ast.Compare)
            and len(condition.ops) == 1
            and isinstance(condition.ops[0], (ast.Eq, ast.NotEq))
            and (field_is_left or field_is_right)
            and isinstance(loop.elt, ast.Constant)
            and type(loop.elt.value) is int
            and loop.elt.value == 1
        ):
            return False
        call = parents.get(loop)
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "sum"
            and call.args == [loop]
            and not call.keywords
        ):
            return False
        assignment = parents.get(call)
        if not (isinstance(assignment, (ast.Assign, ast.AnnAssign)) and assignment.value is call):
            return False
        targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
        if len(targets) != 1 or not isinstance(targets[0], ast.Name):
            return False
        count_name = targets[0].id
        count_loads = _loads(tree, count_name)
        if not count_loads or not all(_reaches_print(load, parents) for load in count_loads):
            return False
        matching_loads += 1
    return matching_loads == 1


def _terminal_ifexp_positions(
    tree: ast.Module, resolver: Any
) -> tuple[tuple[int, int, int, int], ...]:
    parents = _parents(tree)
    functions = _functions(tree)
    p_names, p_keys = _structural_p_roots(tree, resolver)
    result: list[tuple[int, int, int, int]] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.IfExp)
            and _display_string(node.body)
            and _display_string(node.orelse)
        ):
            continue
        assignment = parents.get(node)
        if not (isinstance(assignment, (ast.Assign, ast.AnnAssign)) and assignment.value is node):
            continue
        targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
        if len(targets) != 1 or not isinstance(targets[0], ast.Name):
            continue
        verdict_name = targets[0].id
        owner = _owner(node, parents)
        if not isinstance(owner, ast.FunctionDef) or owner.name != "main":
            continue
        if _later_test_or_helper(owner, node, resolver, functions):
            continue
        if _later_controlled_exit(owner, node, parents, resolver):
            continue
        if isinstance(node.test, ast.Name):
            stores = [
                item
                for item in ast.walk(owner)
                if isinstance(item, (ast.Assign, ast.AnnAssign))
                and any(
                    isinstance(target, ast.Name) and target.id == node.test.id
                    for target in (item.targets if isinstance(item, ast.Assign) else [item.target])
                )
            ]
            if len(stores) != 1 or not _single_p_compare(
                cast(ast.expr, stores[0].value), p_names, p_keys
            ):
                continue
        elif not _single_p_compare(node.test, p_names, p_keys):
            continue
        field = _dict_field_for_name(node, verdict_name, parents)
        loads = _loads(owner, verdict_name)
        if field is None or not loads:
            continue
        verdict_stores = [
            item
            for item in ast.walk(owner)
            if isinstance(item, ast.Name)
            and isinstance(item.ctx, (ast.Store, ast.Del))
            and item.id == verdict_name
        ]
        if len(verdict_stores) != 1:
            continue
        append_loads = 0
        safe = True
        for load in loads:
            if _reaches_print(load, parents):
                continue
            enclosing_dict = _enclosing(load, parents, (ast.Dict,))
            enclosing_call = (
                parents.get(enclosing_dict) if isinstance(enclosing_dict, ast.Dict) else None
            )
            if (
                isinstance(enclosing_dict, ast.Dict)
                and load in ast.walk(enclosing_dict)
                and isinstance(enclosing_call, ast.Call)
                and isinstance(enclosing_call.func, ast.Attribute)
                and isinstance(enclosing_call.func.value, ast.Name)
                and enclosing_call.func.value.id == field[0]
                and enclosing_call.func.attr == "append"
                and enclosing_call.args == [enclosing_dict]
                and not enclosing_call.keywords
            ):
                append_loads += 1
                continue
            safe = False
            break
        if not safe or append_loads != 1:
            continue
        if not _terminal_count_for_field(
            tree, collection=field[0], field=field[1], parents=parents
        ):
            continue
        if not _collection_terminal_safe(tree, owner, field[0], parents):
            continue
        result.append(_position(node.test))
    return tuple(result)


def _terminal_count_positions(
    tree: ast.Module,
) -> tuple[tuple[int, int, int, int], ...]:
    """Census the already-admitted exact direct-p terminal count production."""

    result: list[tuple[int, int, int, int]] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "sum"
            and len(node.args) == 1
            and not node.keywords
            and isinstance(node.args[0], ast.GeneratorExp)
        ):
            continue
        generator = node.args[0]
        if (
            len(generator.generators) == 1
            and not generator.generators[0].is_async
            and len(generator.generators[0].ifs) == 1
            and isinstance(generator.elt, ast.Constant)
            and type(generator.elt.value) is int
            and generator.elt.value == 1
        ):
            result.append(_position(generator.generators[0].ifs[0]))
    return tuple(result)


@contextmanager
def _skip_proved_controls(
    positions: frozenset[tuple[int, int, int, int]],
) -> Iterator[None]:
    original = frozen._MtEngine._control_tracked

    def wrapped(self: Any, node: ast.expr) -> bool:
        tracked = original(self, node)
        return False if tracked and _position(node) in positions else tracked

    frozen._MtEngine._control_tracked = wrapped
    try:
        yield
    finally:
        frozen._MtEngine._control_tracked = original


def _terminal_presentation(
    content: bytes,
    *,
    baseline: Outcome,
    arguments: Mapping[str, Any],
) -> ShadowResult | None:
    if baseline != Outcome("abstain", "hierarchical-gatekeeping-present"):
        return None
    tree = frozen._bounded_parse(content)
    resolver = _resolver(tree)
    if _correction_terminal_present(tree, resolver):
        return None
    if_positions = _terminal_if_positions(tree, resolver)
    ifexp_positions = _terminal_ifexp_positions(tree, resolver)
    positions = frozenset((*if_positions, *ifexp_positions))
    if len(positions) != 1:
        return None
    with _skip_proved_controls(positions):
        downstream = classify(analyze_code_csv_multiple_testing_dataflow(content, **arguments))
    if downstream.state not in {"candidate", "covered"}:
        return ShadowResult(
            downstream,
            baseline,
            downstream != baseline,
            True,
            ("terminal-presentation",),
            {
                "admitted_if_tests": [list(item) for item in if_positions],
                "admitted_ifexp_tests": [list(item) for item in ifexp_positions],
                "terminal_count_tests": [list(item) for item in _terminal_count_positions(tree)],
                "downstream_gate": "frozen-3.2-classifier",
            },
            None,
        )
    return ShadowResult(
        downstream,
        baseline,
        True,
        True,
        ("terminal-presentation",),
        {
            "admitted_if_tests": [list(item) for item in if_positions],
            "admitted_ifexp_tests": [list(item) for item in ifexp_positions],
            "terminal_count_tests": [list(item) for item in _terminal_count_positions(tree)],
            "downstream_gate": "frozen-3.2-classifier",
        },
        None,
    )


def _sequence(node: ast.expr, assignments: Mapping[str, ast.expr]) -> tuple[object, ...] | None:
    if isinstance(node, ast.Name):
        value = assignments.get(node.id)
        return None if value is None else _sequence(value, assignments)
    if not isinstance(node, (ast.List, ast.Tuple)):
        return None
    values: list[object] = []
    for item in node.elts:
        if isinstance(item, ast.Constant) and isinstance(item.value, (str, int, float, bool)):
            values.append(item.value)
        else:
            return None
    return tuple(values)


class _Bind(ast.NodeTransformer):
    def __init__(self, names: Mapping[str, ast.expr], suffix: str) -> None:
        self.names = names
        self.suffix = suffix
        self.locals: set[str] = set()

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if isinstance(node.ctx, ast.Load) and node.id in self.names:
            return ast.copy_location(copy.deepcopy(self.names[node.id]), node)
        if node.id in self.locals:
            return ast.copy_location(ast.Name(id=node.id + self.suffix, ctx=node.ctx), node)
        return node


def _helper_record_surrogate(
    content: bytes, outcome_columns: tuple[str, ...]
) -> tuple[bytes, Mapping[str, object]] | None:
    tree = frozen._bounded_parse(content)
    resolver = _resolver(tree)
    if _correction_terminal_present(tree, resolver):
        return None
    functions = _functions(tree)
    assignments = {
        target.id: statement.value
        for statement in tree.body
        if isinstance(statement, (ast.Assign, ast.AnnAssign)) and statement.value is not None
        for target in (
            statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        )
        if isinstance(target, ast.Name)
    }
    matches: list[tuple[ast.FunctionDef, ast.Assign, ast.DictComp, ast.Call]] = []
    for statement in ast.walk(tree):
        if not (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.DictComp)
        ):
            continue
        comp = statement.value
        if not isinstance(comp.value, ast.Call) or not isinstance(comp.value.func, ast.Name):
            continue
        helper = functions.get(comp.value.func.id)
        if helper is not None:
            matches.append((helper, statement, comp, comp.value))
    if len(matches) != 1:
        return None
    helper, assignment, comp, call = matches[0]
    if len(_call_sites(tree, helper.name)) != 1:
        return None
    if (
        helper.decorator_list
        or helper.returns is not None
        or helper.type_comment is not None
        or helper.args.vararg is not None
        or helper.args.kwarg is not None
        or helper.args.kwonlyargs
        or helper.args.defaults
        or helper.args.kw_defaults
        or helper.args.posonlyargs
        or len(helper.args.args) != 2
        or len(call.args) != 2
        or call.keywords
    ):
        return None
    body = [item for item in helper.body if not frozen._is_docstring(item)]
    if not body or not isinstance(body[-1], ast.Return) or not isinstance(body[-1].value, ast.Dict):
        return None
    if any(not isinstance(item, (ast.Assign, ast.AnnAssign, ast.Return)) for item in body) or any(
        isinstance(
            item,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.Try,
                ast.With,
                ast.AsyncWith,
                ast.Match,
                ast.Global,
                ast.Nonlocal,
                ast.Delete,
                ast.AugAssign,
                ast.NamedExpr,
                ast.Lambda,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Yield,
                ast.YieldFrom,
                ast.Await,
            ),
        )
        for statement in body
        for item in ast.walk(statement)
    ):
        return None
    test_calls = [node for node in ast.walk(helper) if _registered_call(node, resolver)]
    if len(test_calls) != 1:
        return None
    generator = comp.generators
    if (
        len(generator) != 1
        or generator[0].is_async
        or generator[0].ifs
        or not isinstance(generator[0].target, ast.Name)
        or not isinstance(comp.key, ast.Name)
        or comp.key.id != generator[0].target.id
        or not isinstance(call.args[1], ast.Name)
        or call.args[1].id != generator[0].target.id
    ):
        return None
    rows = _sequence(generator[0].iter, assignments)
    if rows != outcome_columns:
        return None
    returned = cast(ast.Dict, body[-1].value)
    if any(key is None for key in returned.keys):
        return None
    keys = tuple(_literal_key(cast(ast.expr, key)) for key in returned.keys)
    if any(key is None for key in keys) or len(keys) != len(set(keys)):
        return None
    if any(
        isinstance(value, (ast.Dict, ast.List, ast.Set, ast.Tuple)) for value in returned.values
    ):
        return None
    p_names: set[str] = set()
    for statement in body[:-1]:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)) or statement.value is None:
            return None
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        if len(targets) != 1:
            return None
        target = targets[0]
        if isinstance(target, (ast.Tuple, ast.List)) and statement.value is test_calls[0]:
            if len(target.elts) != 2 or not isinstance(target.elts[1], ast.Name):
                return None
            p_names.add(target.elts[1].id)
        elif not isinstance(target, ast.Name):
            return None
    if len(p_names) != 1:
        return None
    p_name = next(iter(p_names))

    def direct_p(value: ast.expr) -> bool:
        if isinstance(value, ast.Name):
            return value.id == p_name
        return bool(
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id in _IDENTITY_WRAPPERS
            and len(value.args) == 1
            and not value.keywords
            and isinstance(value.args[0], ast.Name)
            and value.args[0].id == p_name
        )

    p_fields = [key for key, value in zip(keys, returned.values, strict=True) if direct_p(value)]

    def direct_decision(value: ast.expr) -> bool:
        comparison = value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "bool"
            and len(value.args) == 1
            and not value.keywords
        ):
            comparison = value.args[0]
        return bool(
            isinstance(comparison, ast.Compare)
            and len(comparison.ops) == 1
            and isinstance(comparison.ops[0], (ast.Lt, ast.LtE, ast.Gt, ast.GtE))
            and len(comparison.comparators) == 1
            and sum(
                isinstance(item, ast.Name) and item.id == p_name
                for item in (comparison.left, comparison.comparators[0])
            )
            == 1
        )

    decision_fields = [
        key for key, value in zip(keys, returned.values, strict=True) if direct_decision(value)
    ]
    if len(p_fields) != 1 or len(decision_fields) != 1:
        return None
    parents = _parents(tree)
    helper_nodes = frozenset(ast.walk(helper))
    for node in ast.walk(tree):
        if node in helper_nodes or not isinstance(node, ast.Subscript):
            continue
        if _literal_key(node.slice) != p_fields[0]:
            continue
        if not _reaches_print(node, parents):
            return None

    decision_uses = 0
    for node in ast.walk(tree):
        if node in helper_nodes or not isinstance(node, ast.Subscript):
            continue
        if _literal_key(node.slice) != decision_fields[0]:
            continue
        ifexp = _enclosing(node, parents, (ast.IfExp,))
        if not (
            isinstance(ifexp, ast.IfExp)
            and ifexp.test is node
            and _display_string(ifexp.body)
            and _display_string(ifexp.orelse)
        ):
            return None
        decision_assignment = parents.get(ifexp)
        if not (
            isinstance(decision_assignment, (ast.Assign, ast.AnnAssign))
            and decision_assignment.value is ifexp
        ):
            return None
        decision_targets = (
            decision_assignment.targets
            if isinstance(decision_assignment, ast.Assign)
            else [decision_assignment.target]
        )
        if len(decision_targets) != 1 or not isinstance(decision_targets[0], ast.Name):
            return None
        decision_name = decision_targets[0].id
        decision_bindings = [
            item
            for item in ast.walk(tree)
            if isinstance(item, ast.Name)
            and isinstance(item.ctx, (ast.Store, ast.Del))
            and item.id == decision_name
        ]
        if len(decision_bindings) != 1 or not all(
            _reaches_print(load, parents) for load in _loads(tree, decision_name)
        ):
            return None
        decision_uses += 1
    if decision_uses != 1:
        return None
    collection = cast(ast.Name, assignment.targets[0]).id
    stores = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, (ast.Store, ast.Del))
        and node.id == collection
    ]
    if len(stores) != 1:
        return None
    presentation_loops = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.For)
        and isinstance(node.iter, ast.Call)
        and isinstance(node.iter.func, ast.Attribute)
        and isinstance(node.iter.func.value, ast.Name)
        and node.iter.func.value.id == collection
        and node.iter.func.attr == "items"
        and not node.iter.args
        and not node.iter.keywords
        and isinstance(node.target, (ast.Tuple, ast.List))
        and len(node.target.elts) == 2
        and all(isinstance(item, ast.Name) for item in node.target.elts)
    ]
    if len(presentation_loops) != 1:
        return None
    presentation = presentation_loops[0]
    items_call = cast(ast.Call, presentation.iter)
    items_attribute = cast(ast.Attribute, items_call.func)
    for load in _loads(tree, collection):
        if load is items_attribute.value:
            continue
        return None
    outer_owner = _owner(assignment, parents)
    if not isinstance(outer_owner, ast.FunctionDef) or outer_owner.name != "main":
        return None

    suffix = "__mt33"
    formal_bindings = {
        helper.args.args[0].arg: call.args[0],
        helper.args.args[1].arg: ast.Name(id=generator[0].target.id, ctx=ast.Load()),
    }
    binder = _Bind(formal_bindings, suffix)
    binder.locals = {
        node.id
        for statement in body[:-1]
        for node in ast.walk(statement)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    lowered_body: list[ast.stmt] = []
    for statement in body[:-1]:
        transformed = binder.visit(copy.deepcopy(statement))
        if not isinstance(transformed, ast.stmt):
            return None
        lowered_body.append(transformed)
    lowered_record = binder.visit(copy.deepcopy(returned))
    if not isinstance(lowered_record, ast.Dict):
        return None
    synthetic_key = "__mt33_contract_position_key"
    if synthetic_key in keys:
        return None
    lowered_record.keys.insert(0, ast.Constant(value=synthetic_key))
    lowered_record.values.insert(0, ast.Name(id=generator[0].target.id, ctx=ast.Load()))
    append = ast.Expr(
        value=ast.Call(
            func=ast.Attribute(
                value=ast.Name(id=collection, ctx=ast.Load()), attr="append", ctx=ast.Load()
            ),
            args=[lowered_record],
            keywords=[],
        )
    )
    lowered_loop = ast.For(
        target=copy.deepcopy(generator[0].target),
        iter=copy.deepcopy(generator[0].iter),
        body=[*lowered_body, append],
        orelse=[],
        type_comment=None,
    )
    empty = ast.Assign(
        targets=[ast.Name(id=collection, ctx=ast.Store())], value=ast.List(elts=[], ctx=ast.Load())
    )
    result_name = cast(ast.Name, presentation.target.elts[1]).id
    key_name = cast(ast.Name, presentation.target.elts[0]).id
    new_presentation = copy.deepcopy(presentation)
    new_presentation.target = ast.Name(id=result_name, ctx=ast.Store())
    new_presentation.iter = ast.Name(id=collection, ctx=ast.Load())
    new_presentation.body.insert(
        0,
        ast.Assign(
            targets=[ast.Name(id=key_name, ctx=ast.Store())],
            value=ast.Subscript(
                value=ast.Name(id=result_name, ctx=ast.Load()),
                slice=ast.Constant(value=synthetic_key),
                ctx=ast.Load(),
            ),
        ),
    )

    class Lower(ast.NodeTransformer):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST | None:
            if node is helper:
                return None
            return self.generic_visit(node)

        def visit_Assign(self, node: ast.Assign) -> ast.AST | list[ast.stmt]:
            if node is assignment:
                return [ast.copy_location(empty, node), ast.copy_location(lowered_loop, node)]
            return self.generic_visit(node)

        def visit_For(self, node: ast.For) -> ast.AST:
            if node is presentation:
                return ast.copy_location(new_presentation, node)
            return self.generic_visit(node)

    surrogate = Lower().visit(tree)
    if not isinstance(surrogate, ast.Module):
        return None
    ast.fix_missing_locations(surrogate)
    payload = (ast.unparse(surrogate) + "\n").encode("utf-8")
    return payload, {
        "helper": helper.name,
        "call_position": list(_position(call)),
        "collection": collection,
        "p_field_structural_key": p_fields[0],
        "decision_field_structural_key": decision_fields[0],
        "family_size": len(outcome_columns),
    }


def _helper_record(
    content: bytes,
    *,
    baseline: Outcome,
    arguments: Mapping[str, Any],
) -> ShadowResult | None:
    if baseline != Outcome("abstain", "unresolved-pvalue-consumer"):
        return None
    transformed = _helper_record_surrogate(content, tuple(arguments["outcome_columns"]))
    if transformed is None:
        return None
    surrogate, detail = transformed
    downstream = classify(analyze_code_csv_multiple_testing_dataflow(surrogate, **arguments))
    return ShadowResult(
        downstream,
        baseline,
        downstream != baseline,
        True,
        ("single-call-helper-record-consumer",),
        {**detail, "downstream_gate": "frozen-3.2-classifier"},
        "sha256:" + hashlib.sha256(surrogate).hexdigest(),
    )


def analyze_v33_shadow(content: bytes, **arguments: Any) -> ShadowResult:
    baseline = classify(analyze_code_csv_multiple_testing_dataflow(content, **arguments))
    helper = _helper_record(content, baseline=baseline, arguments=arguments)
    if helper is not None:
        return helper
    presentation = _terminal_presentation(content, baseline=baseline, arguments=arguments)
    if presentation is not None:
        return presentation
    tree = frozen._bounded_parse(content)
    count_positions = _terminal_count_positions(tree)
    return ShadowResult(
        baseline,
        baseline,
        False,
        bool(count_positions),
        tuple(("existing-terminal-count",) if count_positions else ()),
        {"terminal_count_tests": [list(item) for item in count_positions]},
        None,
    )
