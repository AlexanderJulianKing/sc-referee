"""Strict shadow proofs for the MT 3.4 design commission.

The shadow never classifies a family.  It proves one of four exact syntactic admissions,
lowers or admits only that proved production, and asks the shipped 3.3 analyzer to classify
the result.

  A  contract-order comprehension normalization  (source-span lowering to the equivalent
     explicit loop, which the frozen loop normalizer already turns into position-tagged
     record copies with p-origins)
  B  terminal IfExp compute-verdict-then-emit    (widened 3.3 terminal-presentation proof)
  C  AP row-table `enumerate` iterator           (widened `_complete_rows`)
  D  AP two-statement if-cap as one fold         (widened `_fold_target_is_unique`)
  E  outcome-headers-only reason routing         (post-hoc abstention relabel)

Extensions A-D are measured as `core`.  Extension E changes no classification; it is measured
separately as `relabel` so the reviewer can price the public-record byte change on its own.
"""

from __future__ import annotations

import ast
import copy
import hashlib
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, cast

from harness import Outcome, classify

import sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_2 as cm2
import sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_3 as cm
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 as frozen
import sc_referee.scientific_checks.code_csv_multiple_testing_terminal_presentation_v3_3 as tp
from sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3_3 import (
    analyze_code_csv_multiple_testing_dataflow,
)

_MISLABEL_SOURCE_REASON = "hierarchical-gatekeeping-present"
_MISLABEL_TARGET_REASON = "pvalue-control-dependence-unresolved"


class _Counter:
    """Opaque row binding for an `enumerate` counter.

    Every structural predicate that can consume a row value tests for `bool` or for equality
    with a contract outcome string.  This object is neither, so any use of the counter in a
    correction or decision path resolves to `None` and refuses.
    """

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return "<enumerate-counter>"


_COUNTER = _Counter()

# Executed admission census for one analyzer call.  Each entry is a source span, so a design
# claim about which extension fired on which row is measured, never asserted.
_ADMISSIONS: dict[str, set[tuple[int, int, int, int]]] = {
    "comprehension": set(),
    "terminal-ifexp": set(),
    "enumerate": set(),
    "cap": set(),
}


def _record(kind: str, span: tuple[int, int, int, int]) -> None:
    _ADMISSIONS[kind].add(span)


def _admission_census() -> dict[str, int]:
    return {kind: len(spans) for kind, spans in sorted(_ADMISSIONS.items())}


@dataclass(frozen=True)
class ShadowResult:
    outcome: Outcome
    core_outcome: Outcome
    baseline: Outcome
    changed: bool
    relabeled: bool
    attempted: bool
    models: tuple[str, ...]
    detail: Mapping[str, object]
    surrogate_sha256: str | None


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _position(node: ast.AST) -> tuple[int, int, int, int]:
    return (
        getattr(node, "lineno", -1),
        getattr(node, "col_offset", -1),
        getattr(node, "end_lineno", -1),
        getattr(node, "end_col_offset", -1),
    )


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


# ---------------------------------------------------------------------------
# A.  Contract-order comprehension normalization
# ---------------------------------------------------------------------------

_FORBIDDEN_ELEMENT_NODES = (
    ast.Lambda,
    ast.NamedExpr,
    ast.Await,
    ast.Yield,
    ast.YieldFrom,
    ast.IfExp,
    ast.Starred,
    ast.GeneratorExp,
    ast.DictComp,
    ast.ListComp,
    ast.SetComp,
    ast.JoinedStr,
    ast.Slice,
)


def _module_sequences(tree: ast.Module) -> dict[str, tuple[object, ...]]:
    """Flat literal list/tuple displays bound exactly once at module level."""

    counts: dict[str, int] = {}
    values: dict[str, tuple[object, ...]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
            value = node.value
        else:
            continue
        if len(targets) != 1 or not isinstance(targets[0], ast.Name):
            continue
        name = targets[0].id
        counts[name] = counts.get(name, 0) + 1
        if not isinstance(value, (ast.List, ast.Tuple)):
            continue
        items: list[object] = []
        for item in value.elts:
            if not isinstance(item, ast.Constant) or isinstance(item.value, bool):
                items = []
                break
            items.append(item.value)
        if items:
            values[name] = tuple(items)
    unstable = {
        name for node in ast.walk(tree) for name in _stored_or_mutated_names(node) if name in values
    }
    return {
        name: value
        for name, value in values.items()
        if counts.get(name) == 1 and name not in unstable
    }


def _stored_or_mutated_names(node: ast.AST) -> frozenset[str]:
    result: set[str] = set()
    if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
        result.add(node.target.id)
    if isinstance(node, ast.Delete):
        result.update(item.id for item in node.targets if isinstance(item, ast.Name))
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                result.add(target.value.id)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.attr
        in {"append", "extend", "insert", "pop", "remove", "clear", "sort", "reverse"}
    ):
        result.add(node.func.value.id)
    return frozenset(result)


def _scalar(node: ast.expr) -> bool:
    if isinstance(node, _FORBIDDEN_ELEMENT_NODES):
        return False
    if isinstance(node, ast.Constant):
        return not isinstance(node.value, (bytes, type(...)))
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.Attribute):
        return _scalar(node.value)
    if isinstance(node, ast.Subscript):
        return _scalar(node.value) and isinstance(node.slice, (ast.Constant, ast.Name))
    if isinstance(node, ast.BinOp):
        return _scalar(node.left) and _scalar(node.right)
    if isinstance(node, ast.UnaryOp):
        return _scalar(node.operand)
    if isinstance(node, (ast.Tuple, ast.List)):
        return all(_scalar(item) for item in node.elts)
    if isinstance(node, ast.Call):
        callee = isinstance(node.func, ast.Name) or (
            isinstance(node.func, ast.Attribute) and _scalar(node.func.value)
        )
        return callee and not node.keywords and all(_scalar(item) for item in node.args)
    return False


def _flat_record(node: ast.Dict) -> bool:
    keys: list[object] = []
    for key, value in zip(node.keys, node.values, strict=True):
        if key is None or not isinstance(key, ast.Constant):
            return False
        if not isinstance(key.value, (str, int)) or isinstance(key.value, bool):
            return False
        keys.append(key.value)
        if not _scalar(value):
            return False
    return bool(keys) and len(keys) == len(set(keys))


def _admitted_element(node: ast.expr) -> str | None:
    for child in ast.walk(node):
        if isinstance(child, _FORBIDDEN_ELEMENT_NODES) and child is not node:
            return None
        if isinstance(child, ast.Call) and child.keywords:
            return None
    if isinstance(node, ast.Call):
        return "call" if _scalar(node) else None
    if isinstance(node, ast.Dict):
        return "record" if _flat_record(node) else None
    return None


def _name_store_count(tree: ast.Module, name: str) -> int:
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, (ast.Store, ast.Del))
        and node.id == name
    )


@dataclass(frozen=True)
class _ComprehensionAdmission:
    statement: ast.stmt
    target: str
    kind: str
    element: ast.expr
    element_kind: str
    sequence_name: str
    loop_variable: str
    span: tuple[int, int, int, int]


def _admitted_comprehensions(
    tree: ast.Module, outcome_columns: tuple[str, ...]
) -> tuple[_ComprehensionAdmission, ...]:
    """Every comprehension matching the closed section-4 grammar, in source order."""

    sequences = _module_sequences(tree)
    result: list[_ComprehensionAdmission] = []
    for statement in ast.walk(tree):
        if isinstance(statement, ast.Assign):
            targets = statement.targets
            value: ast.expr | None = statement.value
        elif isinstance(statement, ast.AnnAssign):
            targets = [statement.target]
            value = statement.value
        else:
            continue
        if len(targets) != 1 or not isinstance(targets[0], ast.Name) or value is None:
            continue
        if not isinstance(value, (ast.DictComp, ast.ListComp)):
            continue
        if len(value.generators) != 1:
            continue
        generator = value.generators[0]
        if generator.is_async or generator.ifs or not isinstance(generator.target, ast.Name):
            continue
        if not isinstance(generator.iter, ast.Name):
            continue
        sequence = sequences.get(generator.iter.id)
        if sequence is None or tuple(sequence) != outcome_columns:
            continue
        loop_variable = generator.target.id
        if isinstance(value, ast.DictComp):
            if not (isinstance(value.key, ast.Name) and value.key.id == loop_variable):
                continue
            element = value.value
            kind = "dict"
        else:
            element = value.elt
            kind = "list"
        element_kind = _admitted_element(element)
        if element_kind is None:
            continue
        loads = {
            node.id
            for node in ast.walk(element)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }
        if loop_variable not in loads:
            continue
        target_name = targets[0].id
        if target_name == loop_variable or _name_store_count(tree, target_name) != 1:
            continue
        if any(
            target_name in _stored_or_mutated_names(node)
            for node in ast.walk(tree)
            if node is not statement
        ):
            continue
        result.append(
            _ComprehensionAdmission(
                statement=statement,
                target=target_name,
                kind=kind,
                element=element,
                element_kind=element_kind,
                sequence_name=generator.iter.id,
                loop_variable=loop_variable,
                span=_position(statement),
            )
        )
    return tuple(sorted(result, key=lambda item: item.span))


def _line_offsets(text: str) -> list[int]:
    offsets = [0]
    for index, character in enumerate(text):
        if character == "\n":
            offsets.append(index + 1)
    return offsets


def _splice(text: str, span: tuple[int, int, int, int], replacement: str) -> str:
    offsets = _line_offsets(text)
    start = offsets[span[0] - 1] + span[1]
    end = offsets[span[2] - 1] + span[3]
    return text[:start] + replacement + text[end:]


def _lowered_statements(item: _ComprehensionAdmission, indent: str) -> str:
    element = ast.unparse(item.element)
    reparsed = ast.parse(element, mode="eval").body
    if ast.dump(reparsed) != ast.dump(item.element):
        raise AssertionError("comprehension element lowering is not graph-preserving")
    empty = "{}" if item.kind == "dict" else "[]"
    body = (
        f"{item.target}[{item.loop_variable}] = {element}"
        if item.kind == "dict"
        else f"{item.target}.append({element})"
    )
    lines = [
        f"{item.target} = {empty}",
        f"{indent}for {item.loop_variable} in {item.sequence_name}:",
        f"{indent}    {body}",
    ]
    original_lines = item.span[2] - item.span[0] + 1
    while len(lines) < original_lines:
        lines.append("")
    return "\n".join(lines)


def normalize_comprehensions(
    content: bytes, outcome_columns: tuple[str, ...]
) -> tuple[bytes, tuple[Mapping[str, object], ...]]:
    """Lower every admitted comprehension to its equivalent explicit loop."""

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return content, ()
    admissions = _admitted_comprehensions(tree, outcome_columns)
    if not admissions:
        return content, ()
    text = content.decode("utf-8")
    detail: list[Mapping[str, object]] = []
    for item in reversed(admissions):
        indent = " " * item.span[1]
        text = _splice(text, item.span, _lowered_statements(item, indent))
    for item in admissions:
        _record("comprehension", item.span)
        detail.append(
            {
                "span": list(item.span),
                "kind": item.kind,
                "element_kind": item.element_kind,
                "target": item.target,
                "sequence": item.sequence_name,
                "loop_variable": item.loop_variable,
            }
        )
    result = text.encode("utf-8")
    ast.parse(result)
    return result, tuple(detail)


# ---------------------------------------------------------------------------
# B.  Terminal IfExp: compute verdict, emit immediately
# ---------------------------------------------------------------------------


def _stored_into_any_collection(load: ast.Name, parents: Mapping[ast.AST, ast.AST]) -> bool:
    cursor: ast.AST = load
    while cursor in parents:
        parent = parents[cursor]
        if isinstance(parent, (ast.Dict, ast.List, ast.Tuple, ast.Set)):
            return True
        if isinstance(parent, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Return)):
            return True
        if isinstance(parent, ast.Call):
            if isinstance(parent.func, ast.Attribute):
                return True
            if not (isinstance(parent.func, ast.Name) and parent.func.id == "print"):
                return True
        if isinstance(parent, ast.Expr):
            return False
        cursor = parent
    return True


def _terminal_ifexp_positions_v34(
    tree: ast.Module, resolver: Any
) -> tuple[tuple[int, int, int, int], ...]:
    """3.3 `_terminal_ifexp_positions` plus the compute-verdict-then-emit production."""

    parents = tp._parents(tree)
    functions = tp._functions(tree)
    p_names, p_keys = tp._structural_p_roots(tree, resolver)
    result: list[tuple[int, int, int, int]] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.IfExp)
            and tp._display_string(node.body)
            and tp._display_string(node.orelse)
        ):
            continue
        assignment = parents.get(node)
        if not (isinstance(assignment, (ast.Assign, ast.AnnAssign)) and assignment.value is node):
            continue
        targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
        if len(targets) != 1 or not isinstance(targets[0], ast.Name):
            continue
        verdict_name = targets[0].id
        owner = tp._owner(node, parents)
        if not isinstance(owner, ast.FunctionDef) or owner.name != "main":
            continue
        if tp._later_test_or_helper(owner, node, resolver, functions):
            continue
        if tp._later_controlled_exit(owner, node, parents, resolver):
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
            if len(stores) != 1 or not tp._single_p_compare(
                cast(ast.expr, stores[0].value), p_names, p_keys
            ):
                continue
        elif not tp._single_p_compare(node.test, p_names, p_keys):
            continue
        loads = tp._loads(owner, verdict_name)
        if not loads:
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
        field = tp._dict_field_for_name(node, verdict_name, parents)
        if field is not None:
            append_loads = 0
            safe = True
            for load in loads:
                if tp._reaches_print(load, parents):
                    continue
                enclosing_dict = tp._enclosing(load, parents, (ast.Dict,))
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
            if not tp._terminal_count_for_field(
                tree, collection=field[0], field=field[1], parents=parents
            ):
                continue
            if not tp._collection_terminal_safe(tree, owner, field[0], parents):
                continue
            result.append(_position(node.test))
            continue
        # 3.4 addition: no record collection at all.  Every load must be a closed print
        # payload and nothing may store the verdict anywhere.
        if not all(tp._reaches_print(load, parents) for load in loads):
            continue
        if any(_stored_into_any_collection(load, parents) for load in loads):
            continue
        _record("terminal-ifexp", _position(node.test))
        result.append(_position(node.test))
    return tuple(result)


# ---------------------------------------------------------------------------
# C.  `enumerate` row-table iterator
# ---------------------------------------------------------------------------


def _enumerate_sequence_name(
    node: ast.expr, sequences: Mapping[str, tuple[object, ...]]
) -> str | None:
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "enumerate"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
    ):
        return None
    if node.keywords:
        if len(node.keywords) != 1:
            return None
        keyword = node.keywords[0]
        if keyword.arg != "start" or not isinstance(keyword.value, ast.Constant):
            return None
        if not isinstance(keyword.value.value, int) or isinstance(keyword.value.value, bool):
            return None
    name = cast(ast.Name, node.args[0]).id
    return name if name in sequences else None


def _complete_rows_v34(
    loop: ast.For,
    *,
    tree: ast.Module,
    owner: Any,
    sequences: Mapping[str, tuple[object, ...]],
    outcome_columns: tuple[str, ...],
) -> tuple[dict[str, object], ...] | None:
    if isinstance(loop.iter, ast.Name):
        return _COMPLETE_ROWS_V33(
            loop,
            tree=tree,
            owner=owner,
            sequences=sequences,
            outcome_columns=outcome_columns,
        )
    sequence_name = _enumerate_sequence_name(loop.iter, sequences)
    if sequence_name is None:
        return None
    names = cm._target_names(loop.target)
    if names is None or len(names) != 2 or names[0] == names[1]:
        return None
    rows = sequences[sequence_name]
    if len(rows) != len(outcome_columns):
        return None
    mappings: list[dict[str, object]] = []
    for row in rows:
        if isinstance(row, tuple):
            return None
        mappings.append({names[0]: _COUNTER, names[1]: row})
    if tuple(row[names[1]] for row in mappings) != outcome_columns:
        return None
    _record("enumerate", _position(loop.iter))
    return tuple(mappings)


# ---------------------------------------------------------------------------
# D.  Two-statement if-cap as one fold
# ---------------------------------------------------------------------------


def _blocks(node: ast.AST) -> Iterator[list[ast.stmt]]:
    for parent in ast.walk(node):
        for slot in ("body", "orelse", "finalbody"):
            block = getattr(parent, slot, None)
            if isinstance(block, list) and all(isinstance(item, ast.stmt) for item in block):
                yield cast("list[ast.stmt]", block)


def _guard_on_name(test: ast.expr, name: str) -> bool:
    if not (isinstance(test, ast.Compare) and len(test.ops) == 1 and len(test.comparators) == 1):
        return False
    left, right, operator = test.left, test.comparators[0], test.ops[0]
    if isinstance(operator, (ast.Gt, ast.GtE)):
        return isinstance(left, ast.Name) and left.id == name and cm._numeric_one(right)
    if isinstance(operator, (ast.Lt, ast.LtE)):
        return cm._numeric_one(left) and isinstance(right, ast.Name) and right.id == name
    return False


@dataclass(frozen=True)
class _AdmittedCap:
    product: ast.Assign
    guard: ast.If
    reassignment: ast.Assign
    name: str


def admitted_caps(tree: ast.Module) -> tuple[_AdmittedCap, ...]:
    """Every exact adjacent `X = A * B` / `if X > 1.0: X = 1.0` pair in the module.

    The pair is absorbed into one fold equivalent to `min(A * B, 1.0)`.  Nothing else is
    absorbed: a non-adjacent cap, a guard on a different Name, a guard against a value other
    than the literal one, an `else` arm, or an if-body with any other statement stays a
    second reaching fold and refuses exactly as it does under 3.3.
    """

    result: list[_AdmittedCap] = []
    for block in _blocks(tree):
        for index, statement in enumerate(block[:-1]):
            if not (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and isinstance(statement.value, ast.BinOp)
                and isinstance(statement.value.op, ast.Mult)
            ):
                continue
            name = statement.targets[0].id
            following = block[index + 1]
            if not isinstance(following, ast.If) or following.orelse:
                continue
            if not _guard_on_name(following.test, name) or len(following.body) != 1:
                continue
            inner = following.body[0]
            if not (
                isinstance(inner, ast.Assign)
                and len(inner.targets) == 1
                and isinstance(inner.targets[0], ast.Name)
                and inner.targets[0].id == name
                and cm._numeric_one(inner.value)
            ):
                continue
            result.append(_AdmittedCap(statement, following, inner, name))
    return tuple(result)


# Keyed by object identity, with a strong reference to the tree so an id is never reused
# while the entry is live.  Cleared on every recognizer activation.
_CAP_CACHE: dict[int, tuple[ast.Module, tuple[_AdmittedCap, ...]]] = {}


def _caps_for(tree: ast.Module) -> tuple[_AdmittedCap, ...]:
    key = id(tree)
    if key not in _CAP_CACHE:
        _CAP_CACHE[key] = (tree, admitted_caps(tree))
    return _CAP_CACHE[key][1]


def admitted_cap_statement(
    fold_statement: ast.stmt, name: str, tree: ast.Module
) -> ast.Assign | None:
    for cap in _caps_for(tree):
        if cap.product is fold_statement and cap.name == name:
            return cap.reassignment
    return None


def _surrogate_bytes_v34(
    tree: ast.Module, fold: Any, transports: Sequence[tuple[str, object]]
) -> bytes:
    """3.3 surrogate lowering, with the absorbed cap statement dropped with its fold.

    `X = p * F` / `if X > 1.0: X = 1.0` lowers to raw exactly as `X = min(p * F, 1.0)` does:
    the surrogate keeps the raw p and drops the whole cap, so the raw family the unchanged
    analyzer classifies is byte-equivalent between the two spellings.
    """

    caps = [cap for cap in _caps_for(tree) if cap.product.value is fold.node]
    if not caps:
        return _SURROGATE_BYTES_V33(tree, fold, transports)
    stripped = copy.deepcopy(tree)
    guards = {_position(cap.guard) for cap in caps}
    for block in _blocks(stripped):
        keep = [
            statement
            for statement in block
            if not (isinstance(statement, ast.If) and _position(statement) in guards)
        ]
        if block and not keep:
            return _SURROGATE_BYTES_V33(tree, fold, transports)
        block[:] = keep
    return _SURROGATE_BYTES_V33(stripped, fold, transports)


def _positions_for_v34(
    node: ast.AST,
    *,
    tree: ast.Module,
    owner: Any,
    parents: Mapping[ast.AST, ast.AST],
    sequences: Mapping[str, tuple[object, ...]],
    outcome_columns: tuple[str, ...],
) -> tuple[int, ...] | None:
    """3.3 `_positions_for`, with the admitted cap `If` absorbed into its fold.

    An admitted cap guard is not a family-position selector: it chooses between `p * F` and
    `1.0` for the same position, exactly as `min` does.  It is therefore transparent here.
    Every other `If`, and every `Try`/`While`/`Match`/`With`, behaves as it does under 3.3.
    """

    cap_guards = {id(cap.guard) for cap in _caps_for(tree)}
    cursor: ast.AST = node
    loop: ast.For | None = None
    while cursor is not owner:
        parent = parents.get(cursor)
        if parent is None:
            return None
        if isinstance(parent, ast.For):
            loop = parent
            break
        cursor = parent
    if loop is None:
        return None
    rows = _complete_rows_v34(
        loop,
        tree=tree,
        owner=owner,
        sequences=sequences,
        outcome_columns=outcome_columns,
    )
    if rows is None:
        return None
    selected = set(range(len(rows)))
    cursor = node
    while cursor is not loop:
        parent = parents.get(cursor)
        if parent is None:
            return None
        if isinstance(parent, ast.If) and id(parent) not in cap_guards:
            in_body = any(cursor is item or cursor in ast.walk(item) for item in parent.body)
            in_else = any(cursor is item or cursor in ast.walk(item) for item in parent.orelse)
            if in_body == in_else:
                return None
            keep: set[int] = set()
            for index, row in enumerate(rows):
                value = cm._static_bool(parent.test, row, owner=owner, sequences=sequences)
                if value is None:
                    return None
                if value == in_body:
                    keep.add(index)
            selected &= keep
        elif isinstance(parent, (ast.Try, ast.While, ast.Match, ast.With)):
            return None
        cursor = parent
    return tuple(sorted(selected))


def _fold_target_is_unique_v34(
    fold: Any,
    *,
    tree: ast.Module,
    parents: Mapping[ast.AST, ast.AST],
    owners: Mapping[ast.AST, Any],
    sequences: Mapping[str, tuple[object, ...]],
    outcome_columns: tuple[str, ...],
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
) -> bool:
    """3.3 single-reaching-fold proof, with one admitted adjacent if-cap folded in."""

    kind, name = fold.target
    cap: ast.Assign | None = None
    if kind == "name" and isinstance(name, str):
        statement = parents.get(fold.node)
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            cap = admitted_cap_statement(cast(ast.stmt, statement), name, tree)
    if cap is not None:
        _record("cap", _position(cap))
    if cap is None:
        return _FOLD_TARGET_IS_UNIQUE_V33(
            fold,
            tree=tree,
            parents=parents,
            owners=owners,
            sequences=sequences,
            outcome_columns=outcome_columns,
            p_names=p_names,
            p_keys=p_keys,
        )

    competing: list[tuple[ast.stmt, ast.expr]] = []
    for node in ast.walk(tree):
        if owners.get(node, tree) is not fold.owner:
            continue
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
            value = node.value
        else:
            continue
        if len(targets) != 1 or cm._target(targets[0]) != fold.target or value is fold.node:
            continue
        if node is cap:
            continue
        competing.append((node, value))

    for node in ast.walk(tree):
        if owners.get(node, tree) is not fold.owner:
            continue
        if isinstance(node, ast.AugAssign) and cm._target(node.target) == fold.target:
            return False
        if isinstance(node, ast.Delete) and any(
            cm._target(target) == fold.target for target in node.targets
        ):
            return False

    if not competing:
        return True
    if len(competing) != 1:
        return False
    statement, value = competing[0]
    positions = _positions_for_v34(
        statement,
        tree=tree,
        owner=fold.owner,
        parents=parents,
        sequences=sequences,
        outcome_columns=outcome_columns,
    )
    complement = set(range(len(outcome_columns))) - set(fold.positions)
    if positions is None or set(positions) != complement:
        return False
    return bool(
        (isinstance(value, ast.Constant) and value.value is None)
        or cm._raw_expr(value, p_names=p_names, p_keys=p_keys) is not None
    )


# ---------------------------------------------------------------------------
# E.  Outcome-headers-only reason routing
# ---------------------------------------------------------------------------


def _registry_control_expressions(scope: Sequence[ast.AST]) -> set[int]:
    result: set[int] = set()
    for node in frozen._walk_statements(tuple(scope)):
        if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.Assert)):
            result.add(id(node.test))
        elif isinstance(node, ast.Match):
            result.add(id(node.subject))
            result.update(id(case.guard) for case in node.cases if case.guard is not None)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            result.add(id(node.iter))
        elif isinstance(node, ast.comprehension):
            result.add(id(node.iter))
            result.update(id(item) for item in node.ifs)
    return result


@dataclass
class _RelabelProbe:
    active: bool = False
    controls: list[dict[str, object]] = field(default_factory=list)


def _outcome_headers_only_control(
    content: bytes, values: Mapping[str, Any]
) -> dict[str, object] | None:
    """Observe whether every tracked hierarchy control matched only on outcome headers.

    One analyzer call can run the hierarchy guard several times (the frozen 3.2 pass, then a
    3.3 re-analysis under a proved exclusion).  Attributing the emitted reason to the first
    tracked control of the first pass would be a guess.  Instead every tracked control from
    every pass is recorded, and the routing applies only when all of them are control-registry
    expressions with zero p-origins, no correction control, and at least two outcome headers.
    That can only under-route, never over-route.
    """

    probe = _RelabelProbe()
    original_control = frozen._MtEngine._control_tracked
    original_guard = frozen._MtEngine._hierarchy_guard
    registry_cache: dict[int, set[int]] = {}

    def control(self: Any, node: ast.expr) -> bool:
        tracked = original_control(self, node)
        if probe.active and tracked:
            if id(self) not in registry_cache:
                registry_cache[id(self)] = _registry_control_expressions(
                    (*self.original_scope, *self.scope)
                )
            probe.controls.append(
                {
                    "position": list(_position(node)),
                    "node_type": type(node).__name__,
                    "p_origins": len(self._p_origins(node)),
                    "correction_control": bool(self._correction_control_present(node)),
                    "outcome_headers": len(self._outcome_headers(node, set(), 0)),
                    "registry_control": id(node) in registry_cache[id(self)],
                }
            )
        return tracked

    def guard(self: Any) -> str | None:
        probe.active = True
        try:
            return original_guard(self)
        finally:
            probe.active = False

    frozen._MtEngine._control_tracked = control
    frozen._MtEngine._hierarchy_guard = guard
    try:
        arguments = dict(values)
        arguments.pop("content", None)
        analyze_code_csv_multiple_testing_dataflow(content, **arguments)
    finally:
        frozen._MtEngine._control_tracked = original_control
        frozen._MtEngine._hierarchy_guard = original_guard
    if not probe.controls:
        return None
    for item in probe.controls:
        if not (
            item["registry_control"]
            and item["p_origins"] == 0
            and not item["correction_control"]
            and cast(int, item["outcome_headers"]) >= 2
        ):
            return None
    return {"tracked_control_count": len(probe.controls), "controls": probe.controls}


# ---------------------------------------------------------------------------
# Patch harness
# ---------------------------------------------------------------------------

# The 3.2 and 3.3 correction models are byte-identical apart from one type annotation, and
# the 3.3 wrapper still routes an `unresolved-manual-correction-present` first reason through
# the 3.2 module.  Both are patched so an AP admission cannot depend on which lane ran.
_CORRECTION_MODULES = (cm2, cm)
_COMPLETE_ROWS_V33 = cm._complete_rows
_FOLD_TARGET_IS_UNIQUE_V33 = cm._fold_target_is_unique
_POSITIONS_FOR_V33 = cm._positions_for
_SURROGATE_BYTES_V33 = cm._surrogate_bytes
_TERMINAL_IFEXP_V33 = tp._terminal_ifexp_positions
for _module in _CORRECTION_MODULES:
    for _name, _frozen in (
        ("_complete_rows", _COMPLETE_ROWS_V33),
        ("_fold_target_is_unique", _FOLD_TARGET_IS_UNIQUE_V33),
        ("_positions_for", _POSITIONS_FOR_V33),
        ("_surrogate_bytes", _SURROGATE_BYTES_V33),
    ):
        if getattr(_module, _name).__code__.co_code != _frozen.__code__.co_code:
            raise RuntimeError(f"correction model {_name} diverges between the 3.2 and 3.3 lanes")


@contextmanager
def _v34_recognizers(*, extension_b: bool = False) -> Iterator[None]:
    """Activate the shipped 3.4 recognizer admissions for one analyzer call.

    Extension B is NOT shipped.  It is installed only by the instrumentation probe that
    measures why: on E16 P4 its single extra admitted position collides with the 3.3
    single-occurrence requirement in `prove_terminal_presentation` and loses a pinned
    candidate.  See section 5 of the design.
    """

    _CAP_CACHE.clear()
    for spans in _ADMISSIONS.values():
        spans.clear()
    for module in _CORRECTION_MODULES:
        module._complete_rows = _complete_rows_v34
        module._fold_target_is_unique = _fold_target_is_unique_v34
        module._positions_for = _positions_for_v34
        module._surrogate_bytes = _surrogate_bytes_v34
    if extension_b:
        tp._terminal_ifexp_positions = _terminal_ifexp_positions_v34
    try:
        yield
    finally:
        for module in _CORRECTION_MODULES:
            module._complete_rows = _COMPLETE_ROWS_V33
            module._fold_target_is_unique = _FOLD_TARGET_IS_UNIQUE_V33
            module._positions_for = _POSITIONS_FOR_V33
            module._surrogate_bytes = _SURROGATE_BYTES_V33
        tp._terminal_ifexp_positions = _TERMINAL_IFEXP_V33
        _CAP_CACHE.clear()


_MODEL_NAMES = {
    "comprehension": "A-comprehension-normalization",
    "terminal-ifexp": "B-terminal-ifexp-print-only",
    "enumerate": "C-enumerate-row-table",
    "cap": "D-adjacent-if-cap",
}


_CLASSIFIED = frozenset({"candidate", "covered"})


def analyze_v34_shadow(
    content: bytes, *, baseline: Outcome | None = None, **values: Any
) -> ShadowResult:
    """Run the shipped 3.3 pipeline, then the 3.4 admissions only where it abstained.

    The ordering rule is load-bearing and was chosen against evidence, not on principle.  An
    unconditional normalization loses E16 P3: extension A resolves that source's p-lineage,
    the first reason stops being `unresolved-pvalue-consumer`, and the frozen 3.3
    helper-record route that produced its pinned candidate is never attempted.  So:

      * a row the unchanged 3.3 pipeline classifies is returned untouched and no 3.4
        admission is even attempted; and
      * a row it abstains on is re-analyzed with the 3.4 admissions, and the 3.4 result is
        adopted only if it is itself a classification.  Otherwise the original 3.3 abstention
        reason is returned byte-for-byte.

    Every frozen 3.3 classification and every frozen 3.3 abstention reason therefore survives
    by construction, and the only rows 3.4 can move are abstentions it converts.
    """

    outcome_columns = cast("tuple[str, ...]", values["outcome_columns"])
    if baseline is None:
        baseline = classify(analyze_code_csv_multiple_testing_dataflow(content, **values))

    normalized = content
    comprehension_detail: tuple[Mapping[str, object], ...] = ()
    census = {kind: 0 for kind in sorted(_ADMISSIONS)}
    attempted_outcome: Outcome | None = None
    if baseline.state not in _CLASSIFIED:
        with _v34_recognizers():
            normalized, comprehension_detail = normalize_comprehensions(content, outcome_columns)
            attempted_outcome = classify(
                analyze_code_csv_multiple_testing_dataflow(normalized, **values)
            )
            census = _admission_census()
            # A second application is only informative where an admission actually fired: with
            # an empty census the second call is the frozen analyzer on identical bytes.
            if any(census.values()):
                repeat = classify(analyze_code_csv_multiple_testing_dataflow(normalized, **values))
                if repeat != attempted_outcome or _admission_census() != census:
                    raise AssertionError("the 3.4 shadow is not idempotent on repeated use")
        again, repeat_detail = normalize_comprehensions(normalized, outcome_columns)
        if again != normalized or (comprehension_detail and repeat_detail):
            raise AssertionError("comprehension lowering is not idempotent")

    core = (
        attempted_outcome
        if attempted_outcome is not None and attempted_outcome.state in _CLASSIFIED
        else baseline
    )
    models = [_MODEL_NAMES[kind] for kind in sorted(census) if census[kind]]
    relabel_witness: dict[str, object] | None = None
    outcome = core
    if core.state == "abstain" and core.reason_or_classification == _MISLABEL_SOURCE_REASON:
        relabel_witness = _outcome_headers_only_control(content, values)
        if relabel_witness is not None:
            models.append("E-outcome-headers-reason-routing")
            outcome = Outcome("abstain", _MISLABEL_TARGET_REASON)

    detail: dict[str, object] = {
        "admission_census": census,
        "attempted_outcome": None if attempted_outcome is None else attempted_outcome.as_json(),
        "comprehensions": list(comprehension_detail),
        "relabel_witness": relabel_witness,
    }
    return ShadowResult(
        outcome=outcome,
        core_outcome=core,
        baseline=baseline,
        changed=core != baseline,
        relabeled=outcome != core,
        attempted=attempted_outcome is not None,
        models=tuple(models),
        detail=detail,
        surrogate_sha256=_sha256(normalized) if normalized != content else None,
    )


__all__ = [
    "ShadowResult",
    "admitted_cap_statement",
    "admitted_caps",
    "analyze_v34_shadow",
    "normalize_comprehensions",
]
