"""Strict AP(C, POS) correction recognizer for multiple-testing 3.2.

The recognizer never executes project code and never classifies by itself.  It admits only the
closed Bonferroni productions, subtracts one proved correction fold on a structural surrogate,
and requires the frozen 3.0 analyzer to prove the remaining raw family independently.
"""

from __future__ import annotations

import ast
import copy
import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, cast

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 as mt
import sc_referee.scientific_checks.code_csv_multiple_testing_record_model_v3 as rm
from sc_referee.core.ids import sha256_digest

CODE_CSV_MULTIPLE_TESTING_CORRECTION_MODEL_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)

_TARGET_REASONS = frozenset(
    {
        "record-family-lineage-unresolved",
        "record-family-mutation-unresolved",
        "pderived-conclusion-family-incomplete",
        "unresolved-decision-threshold",
        "unresolved-manual-correction-present",
    }
)
_FAMILY_ALPHAS = frozenset({Decimal("0.01"), Decimal("0.05"), Decimal("0.1")})
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
        return _Outcome("abstain", "multiple-testing-code-inspection-exception")
    state = "covered" if result.facts.correction_classification == "complete" else "candidate"
    return _Outcome(
        state,
        result.facts.correction_classification,
        result.facts.corrected_positions,
        result.facts.family_size,
    )


@dataclass(frozen=True)
class CorrectionModelResult:
    outcome: _Outcome
    baseline: _Outcome
    changed: bool
    attempted: bool
    model: str | None
    corrected_positions: tuple[int, ...]
    detail: Mapping[str, object]
    surrogate_sha256: str | None = None


@dataclass(frozen=True)
class _Fold:
    node: ast.expr
    raw: ast.expr
    target: tuple[str, object]
    positions: tuple[int, ...]
    owner: ast.Module | ast.FunctionDef
    form: str
    source_line: int


def _position(node: ast.AST) -> tuple[int, int, int, int]:
    return (
        getattr(node, "lineno", -1),
        getattr(node, "col_offset", -1),
        getattr(node, "end_lineno", -1),
        getattr(node, "end_col_offset", -1),
    )


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}


def _owners(tree: ast.Module) -> dict[ast.AST, ast.Module | ast.FunctionDef]:
    result: dict[ast.AST, ast.Module | ast.FunctionDef] = {}
    for statement in tree.body:
        if isinstance(statement, ast.FunctionDef):
            for node in ast.walk(statement):
                result[node] = statement
        else:
            for node in ast.walk(statement):
                result[node] = tree
    return result


def _literal_key(node: ast.expr) -> str | int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)):
        return node.value
    return None


def _target(node: ast.expr) -> tuple[str, object] | None:
    if isinstance(node, ast.Name):
        return "name", node.id
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        key = _literal_key(node.slice)
        if key is not None:
            return "field", (node.value.id, key)
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return "field", (node.value.id, node.attr)
    return None


def _bindings(owner: ast.Module | ast.FunctionDef, name: str) -> list[ast.expr]:
    values: list[ast.expr] = []
    for node in ast.walk(owner):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            if isinstance(node.targets[0], ast.Name) and node.targets[0].id == name:
                values.append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name and node.value is not None:
                values.append(node.value)
    return values


def _name_stable(tree: ast.Module, name: str) -> bool:
    stores = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Store):
            stores += 1
        if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return False
        if isinstance(node, ast.Delete) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return False
    return stores == 1


def _module_sequences(tree: ast.Module) -> dict[str, tuple[object, ...]]:
    result: dict[str, tuple[object, ...]] = {}
    pending = [node for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))]
    changed = True
    while changed:
        changed = False
        for node in pending:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if value is None or len(targets) != 1 or not isinstance(targets[0], ast.Name):
                continue
            name = targets[0].id
            if name in result or not _name_stable(tree, name):
                continue
            if not isinstance(value, (ast.List, ast.Tuple)):
                continue
            rows: list[object] = []
            valid = True
            for item in value.elts:
                if isinstance(item, ast.Constant) and isinstance(
                    item.value, (str, int, float, bool, type(None))
                ):
                    rows.append(item.value)
                elif isinstance(item, (ast.List, ast.Tuple)):
                    row: list[object] = []
                    for leaf in item.elts:
                        if not isinstance(leaf, ast.Constant) or not isinstance(
                            leaf.value, (str, int, float, bool, type(None))
                        ):
                            valid = False
                            break
                        row.append(leaf.value)
                    rows.append(tuple(row))
                elif isinstance(item, ast.Name) and item.id in result:
                    rows.append(result[item.id])
                else:
                    valid = False
                if not valid:
                    break
            if valid:
                result[name] = tuple(rows)
                changed = True
    return result


def _decimal_literal(node: ast.expr, source: bytes) -> Decimal | None:
    if (
        not isinstance(node, ast.Constant)
        or isinstance(node.value, bool)
        or not isinstance(node.value, (int, float))
    ):
        return None
    segment = ast.get_source_segment(source.decode("utf-8"), node)
    try:
        return Decimal(segment) if segment is not None else Decimal(repr(node.value))
    except InvalidOperation:
        return None


def _resolve_decimal_name(
    node: ast.expr,
    *,
    tree: ast.Module,
    owner: ast.Module | ast.FunctionDef,
    source: bytes,
) -> Decimal | None:
    literal = _decimal_literal(node, source)
    if literal is not None:
        return literal
    if not isinstance(node, ast.Name) or not _name_stable(tree, node.id):
        return None
    local = _bindings(owner, node.id)
    module = _bindings(tree, node.id) if owner is not tree else local
    values = local if len(local) == 1 else module
    if len(values) != 1:
        return None
    return _decimal_literal(values[0], source)


def _resolve_factor(
    node: ast.expr,
    *,
    tree: ast.Module,
    owner: ast.Module | ast.FunctionDef,
    sequences: Mapping[str, tuple[object, ...]],
    outcome_columns: tuple[str, ...],
    active: frozenset[str] = frozenset(),
) -> int | None:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    ):
        return node.value
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "len"
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.args[0], ast.Name)
    ):
        rows = sequences.get(node.args[0].id)
        if rows is None:
            return None
        headers = tuple(row[0] if isinstance(row, tuple) and row else row for row in rows)
        return len(rows) if headers == outcome_columns else None
    if not isinstance(node, ast.Name) or node.id in active or not _name_stable(tree, node.id):
        return None
    local = _bindings(owner, node.id)
    module = _bindings(tree, node.id) if owner is not tree else local
    values = local if len(local) == 1 else module
    if len(values) != 1:
        return None
    value = values[0]
    # A factor alias is deliberately not a family-size proof.  The admitted Name is the one
    # immutable binding itself, whose RHS must be an integer literal or len(CONTRACT_TABLE).
    if isinstance(value, ast.Name):
        return None
    if (
        isinstance(value, ast.Constant)
        and isinstance(value.value, int)
        and not isinstance(value.value, bool)
    ):
        return value.value
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "len"
        and len(value.args) == 1
        and not value.keywords
        and isinstance(value.args[0], ast.Name)
    ):
        rows = sequences.get(value.args[0].id)
        if rows is None:
            return None
        headers = tuple(row[0] if isinstance(row, tuple) and row else row for row in rows)
        return len(rows) if headers == outcome_columns else None
    return None


def _raw_expr(
    node: ast.expr,
    *,
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
) -> ast.expr | None:
    if isinstance(node, ast.Name) and node.id in p_names:
        return node
    if isinstance(node, ast.Subscript) and _literal_key(node.slice) in p_keys:
        return node
    if isinstance(node, ast.Attribute) and node.attr == "pvalue":
        return node
    return None


def _correction_root_names(
    tree: ast.Module,
    p_names: frozenset[str],
) -> frozenset[str]:
    """Exclude Name-to-Name p aliases from the closed AP raw-root grammar."""

    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target = node.target
            value = node.value
        else:
            continue
        if isinstance(target, ast.Name) and isinstance(value, ast.Name) and value.id in p_names:
            aliases.add(target.id)
    return frozenset(p_names - aliases)


def _match_product(
    node: ast.expr,
    *,
    tree: ast.Module,
    owner: ast.Module | ast.FunctionDef,
    sequences: Mapping[str, tuple[object, ...]],
    outcome_columns: tuple[str, ...],
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
) -> tuple[ast.expr, int] | None:
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Mult):
        return None
    left_raw = _raw_expr(node.left, p_names=p_names, p_keys=p_keys)
    right_raw = _raw_expr(node.right, p_names=p_names, p_keys=p_keys)
    if (left_raw is None) == (right_raw is None):
        return None
    raw = left_raw if left_raw is not None else cast(ast.expr, right_raw)
    factor_node = node.right if left_raw is not None else node.left
    factor = _resolve_factor(
        factor_node,
        tree=tree,
        owner=owner,
        sequences=sequences,
        outcome_columns=outcome_columns,
    )
    return (raw, factor) if factor is not None else None


def _match_adjustment(
    node: ast.expr,
    *,
    tree: ast.Module,
    owner: ast.Module | ast.FunctionDef,
    resolver: Any,
    sequences: Mapping[str, tuple[object, ...]],
    outcome_columns: tuple[str, ...],
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
) -> tuple[ast.expr, int, str] | None:
    product = _match_product(
        node,
        tree=tree,
        owner=owner,
        sequences=sequences,
        outcome_columns=outcome_columns,
        p_names=p_names,
        p_keys=p_keys,
    )
    if product is not None:
        return product[0], product[1], "bare-product"
    if not isinstance(node, ast.Call) or len(node.args) != 2 or node.keywords:
        return None
    callee = resolver.qualified(node.func)
    if not (
        (isinstance(node.func, ast.Name) and node.func.id == "min" and callee in {None, "min"})
        or callee == "numpy.minimum"
    ):
        return None
    one = [index for index, item in enumerate(node.args) if _numeric_one(item)]
    if len(one) != 1:
        return None
    product_node = node.args[1 - one[0]]
    product = _match_product(
        product_node,
        tree=tree,
        owner=owner,
        sequences=sequences,
        outcome_columns=outcome_columns,
        p_names=p_names,
        p_keys=p_keys,
    )
    if product is None:
        return None
    return product[0], product[1], "capped-product"


def _numeric_one(node: ast.expr) -> bool:
    return bool(
        isinstance(node, ast.Constant)
        and not isinstance(node.value, bool)
        and isinstance(node.value, (int, float))
        and node.value == 1
    )


def _target_names(target: ast.expr) -> tuple[str, ...] | None:
    if isinstance(target, ast.Name):
        return (target.id,)
    if isinstance(target, (ast.Tuple, ast.List)) and all(
        isinstance(item, ast.Name) for item in target.elts
    ):
        return tuple(cast(ast.Name, item).id for item in target.elts)
    return None


def _complete_rows(
    loop: ast.For,
    *,
    tree: ast.Module,
    owner: ast.Module | ast.FunctionDef,
    sequences: Mapping[str, tuple[object, ...]],
    outcome_columns: tuple[str, ...],
) -> tuple[dict[str, object], ...] | None:
    if not isinstance(loop.iter, ast.Name) or loop.iter.id not in sequences:
        return None
    names = _target_names(loop.target)
    rows = sequences[loop.iter.id]
    if names is None or len(rows) != len(outcome_columns):
        return None
    normalized: list[tuple[object, ...]] = []
    for row in rows:
        values = row if isinstance(row, tuple) else (row,)
        if len(values) != len(names):
            return None
        normalized.append(values)
    mappings = tuple(dict(zip(names, row, strict=True)) for row in normalized)
    if not any(tuple(row[name] for row in mappings) == outcome_columns for name in names):
        return None
    return mappings


def _resolve_bool_name(
    name: str,
    *,
    owner: ast.Module | ast.FunctionDef,
) -> ast.expr | None:
    values = _bindings(owner, name)
    return values[0] if len(values) == 1 else None


def _static_bool(
    node: ast.expr,
    row: Mapping[str, object],
    *,
    owner: ast.Module | ast.FunctionDef,
    sequences: Mapping[str, tuple[object, ...]],
    active: frozenset[str] = frozenset(),
) -> bool | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in row:
            row_value = row[node.id]
            return row_value if isinstance(row_value, bool) else None
        if node.id in active:
            return None
        value = _resolve_bool_name(node.id, owner=owner)
        return (
            None
            if value is None
            else _static_bool(
                value,
                row,
                owner=owner,
                sequences=sequences,
                active=active | {node.id},
            )
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        bool_value = _static_bool(
            node.operand, row, owner=owner, sequences=sequences, active=active
        )
        return None if bool_value is None else not bool_value
    if isinstance(node, ast.BoolOp):
        values = [
            _static_bool(item, row, owner=owner, sequences=sequences, active=active)
            for item in node.values
        ]
        if any(item is None for item in values):
            return None
        if isinstance(node.op, ast.And):
            return all(cast(bool, item) for item in values)
        if isinstance(node.op, ast.Or):
            return any(cast(bool, item) for item in values)
        return None
    if (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and len(node.comparators) == 1
        and isinstance(node.left, ast.Name)
        and node.left.id in row
        and isinstance(node.comparators[0], ast.Name)
        and node.comparators[0].id in sequences
        and isinstance(node.ops[0], (ast.In, ast.NotIn))
    ):
        present = row[node.left.id] in sequences[node.comparators[0].id]
        return not present if isinstance(node.ops[0], ast.NotIn) else present
    return None


def _positions_for(
    node: ast.AST,
    *,
    tree: ast.Module,
    owner: ast.Module | ast.FunctionDef,
    parents: Mapping[ast.AST, ast.AST],
    sequences: Mapping[str, tuple[object, ...]],
    outcome_columns: tuple[str, ...],
) -> tuple[int, ...] | None:
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
    rows = _complete_rows(
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
        if isinstance(parent, ast.If):
            in_body = any(cursor is item or cursor in ast.walk(item) for item in parent.body)
            in_else = any(cursor is item or cursor in ast.walk(item) for item in parent.orelse)
            if in_body == in_else:
                return None
            keep: set[int] = set()
            for index, row in enumerate(rows):
                value = _static_bool(parent.test, row, owner=owner, sequences=sequences)
                if value is None:
                    return None
                if value == in_body:
                    keep.add(index)
            selected &= keep
        elif isinstance(parent, (ast.Try, ast.While, ast.Match, ast.With)):
            return None
        cursor = parent
    return tuple(sorted(selected))


def _has_correction_terminal(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        terminal = (
            node.func.id
            if isinstance(node.func, ast.Name)
            else node.func.attr
            if isinstance(node.func, ast.Attribute)
            else ""
        ).lower()
        if terminal in _CORRECTION_TERMINALS or terminal.startswith("benjamini"):
            return True
    return False


def _record_cross_function(
    fold: _Fold,
    *,
    tree: ast.Module,
    resolver: Any,
    outcome_columns: tuple[str, ...],
) -> bool:
    if fold.target[0] != "field":
        return False
    record_name = cast(tuple[str, str | int], fold.target[1])[0]
    # The record itself must be constructed by one visible literal in the same expanded owner.
    # A helper-return record, even when appended in this owner, is cross-function flow.
    local_constructors = [
        node
        for node in ast.walk(fold.owner)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and node.value is not None
        and isinstance(node.value, (ast.Dict, ast.Tuple))
        and any(
            isinstance(target, ast.Name) and target.id == record_name
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        )
    ]
    if len(local_constructors) == 1:
        return False
    return True


def _boundary_refusal(
    fold: _Fold,
    *,
    tree: ast.Module,
    resolver: Any,
    outcome_columns: tuple[str, ...],
) -> str | None:
    builders = rm._record_builders(tree, resolver, outcome_columns)
    relevant = tuple(builder for builder in builders if builder.owner is fold.owner)
    if not relevant:
        return None
    reason = rm._record_boundary_reason(tree, relevant, resolver, outcome_columns)
    if reason is None:
        return None
    if reason == "record-family-lineage-unresolved" and fold.target[0] == "field":
        if not _record_cross_function(
            fold, tree=tree, resolver=resolver, outcome_columns=outcome_columns
        ):
            return None
    return reason


def _fold_target_is_unique(
    fold: _Fold,
    *,
    tree: ast.Module,
    parents: Mapping[ast.AST, ast.AST],
    owners: Mapping[ast.AST, ast.Module | ast.FunctionDef],
    sequences: Mapping[str, tuple[object, ...]],
    outcome_columns: tuple[str, ...],
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
) -> bool:
    """Prove one reaching fold, allowing only an exact raw/None complementary branch."""

    competing: list[tuple[ast.Assign | ast.AnnAssign, ast.expr]] = []
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
        if len(targets) != 1 or _target(targets[0]) != fold.target or value is fold.node:
            continue
        competing.append((node, value))

    for node in ast.walk(tree):
        if owners.get(node, tree) is not fold.owner:
            continue
        if isinstance(node, ast.AugAssign) and _target(node.target) == fold.target:
            return False
        if isinstance(node, ast.Delete) and any(
            _target(target) == fold.target for target in node.targets
        ):
            return False

    if not competing:
        return True
    if len(competing) != 1:
        return False
    statement, value = competing[0]
    positions = _positions_for(
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
        or _raw_expr(value, p_names=p_names, p_keys=p_keys) is not None
    )


def _folds(
    tree: ast.Module,
    *,
    source: bytes,
    resolver: Any,
    outcome_columns: tuple[str, ...],
) -> tuple[list[_Fold], list[dict[str, object]]]:
    parents = _parents(tree)
    owners = _owners(tree)
    sequences = _module_sequences(tree)
    p_names, p_keys = rm._p_lineage(tree, resolver)
    correction_p_names = _correction_root_names(tree, p_names)
    result: list[_Fold] = []
    rejected: list[dict[str, object]] = []
    for statement in ast.walk(tree):
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)) or statement.value is None:
            continue
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        if len(targets) != 1 or (target := _target(targets[0])) is None:
            continue
        owner = owners.get(statement, tree)
        matched = _match_adjustment(
            statement.value,
            tree=tree,
            owner=owner,
            resolver=resolver,
            sequences=sequences,
            outcome_columns=outcome_columns,
            p_names=correction_p_names,
            p_keys=p_keys,
        )
        if matched is None:
            continue
        raw, factor, form = matched
        positions = _positions_for(
            statement,
            tree=tree,
            owner=owner,
            parents=parents,
            sequences=sequences,
            outcome_columns=outcome_columns,
        )
        item: dict[str, object] = {
            "line": statement.lineno,
            "factor": factor,
            "positions": None if positions is None else list(positions),
            "form": form,
        }
        if factor != len(outcome_columns) or positions is None or not positions:
            rejected.append(item)
            continue
        fold = _Fold(
            statement.value,
            raw,
            target,
            positions,
            owner,
            form,
            statement.lineno,
        )
        if not _fold_target_is_unique(
            fold,
            tree=tree,
            parents=parents,
            owners=owners,
            sequences=sequences,
            outcome_columns=outcome_columns,
            p_names=p_names,
            p_keys=p_keys,
        ):
            item["refusal"] = "single-reaching-fold"
            rejected.append(item)
            continue
        result.append(fold)
    # Constructor fields are admitted only when their literal record is constructed in the same
    # owner occurrence.  Dynamic keys, helper-return records, and nested records remain refused.
    for record in (node for node in ast.walk(tree) if isinstance(node, ast.Dict)):
        owner = owners.get(record, tree)
        positions = _positions_for(
            record,
            tree=tree,
            owner=owner,
            parents=parents,
            sequences=sequences,
            outcome_columns=outcome_columns,
        )
        for key_node, value in zip(record.keys, record.values, strict=True):
            if key_node is None or (key := _literal_key(key_node)) is None:
                continue
            matched = _match_adjustment(
                value,
                tree=tree,
                owner=owner,
                resolver=resolver,
                sequences=sequences,
                outcome_columns=outcome_columns,
                p_names=correction_p_names,
                p_keys=p_keys,
            )
            if matched is None:
                continue
            raw, factor, form = matched
            item = {
                "line": value.lineno,
                "factor": factor,
                "positions": None if positions is None else list(positions),
                "form": f"constructor-{form}",
            }
            if factor != len(outcome_columns) or positions is None or not positions:
                rejected.append(item)
                continue
            result.append(
                _Fold(
                    value,
                    raw,
                    ("constructor-field", (_position(record), key)),
                    positions,
                    owner,
                    f"constructor-{form}",
                    value.lineno,
                )
            )
    return result, rejected


def _threshold_fold(
    tree: ast.Module,
    *,
    source: bytes,
    resolver: Any,
    outcome_columns: tuple[str, ...],
) -> _Fold | None:
    parents = _parents(tree)
    owners = _owners(tree)
    sequences = _module_sequences(tree)
    p_names, p_keys = rm._p_lineage(tree, resolver)
    candidates: list[_Fold] = []
    assignments: list[tuple[ast.Name, ast.expr, ast.Module | ast.FunctionDef]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if len(targets) == 1 and isinstance(targets[0], ast.Name):
                assignments.append((targets[0], node.value, owners.get(node, tree)))
    for compare in (node for node in ast.walk(tree) if isinstance(node, ast.Compare)):
        if (
            len(compare.ops) != 1
            or len(compare.comparators) != 1
            or not isinstance(compare.ops[0], (ast.Lt, ast.LtE, ast.Gt, ast.GtE))
        ):
            continue
        left_raw = _raw_expr(compare.left, p_names=p_names, p_keys=p_keys)
        right_raw = _raw_expr(compare.comparators[0], p_names=p_names, p_keys=p_keys)
        if (left_raw is None) == (right_raw is None):
            continue
        threshold = compare.comparators[0] if left_raw is not None else compare.left
        binding_target: ast.expr | None = None
        if isinstance(threshold, ast.Name):
            matches = [item for item in assignments if item[0].id == threshold.id]
            if len(matches) != 1 or not _name_stable(tree, threshold.id):
                continue
            binding_target, threshold, owner = matches[0]
        else:
            owner = owners.get(compare, tree)
        if not isinstance(threshold, ast.BinOp) or not isinstance(threshold.op, ast.Div):
            continue
        alpha = _resolve_decimal_name(threshold.left, tree=tree, owner=owner, source=source)
        factor = _resolve_factor(
            threshold.right,
            tree=tree,
            owner=owner,
            sequences=sequences,
            outcome_columns=outcome_columns,
        )
        if alpha not in _FAMILY_ALPHAS or factor != len(outcome_columns):
            continue
        positions = _positions_for(
            compare,
            tree=tree,
            owner=owners.get(compare, tree),
            parents=parents,
            sequences=sequences,
            outcome_columns=outcome_columns,
        )
        if positions is None or not positions:
            continue
        replacement = ast.Constant(float(alpha))
        candidates.append(
            _Fold(
                threshold,
                replacement,
                ("threshold-binding", binding_target.id)
                if isinstance(binding_target, ast.Name)
                else ("threshold-direct", _position(compare)),
                positions,
                owner,
                "family-alpha-division",
                compare.lineno,
            )
        )
    unique = {(_position(item.node), item.target): item for item in candidates}
    return next(iter(unique.values())) if len(unique) == 1 else None


def _load_matches(node: ast.expr, target: tuple[str, object]) -> bool:
    if target[0] == "name":
        return (
            isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id == target[1]
        )
    if target[0] == "field" and isinstance(target[1], tuple):
        value = _target(node)
        return value == target
    return False


def _transport_targets(
    tree: ast.Module,
    fold: _Fold,
    *,
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
    outcome_columns: tuple[str, ...],
) -> tuple[tuple[str, object], ...]:
    result: list[tuple[str, object]] = [fold.target]
    parents = _parents(tree)
    owners = _owners(tree)
    sequences = _module_sequences(tree)
    all_positions = set(range(len(outcome_columns)))
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if len(targets) != 1 or (target := _target(targets[0])) is None or target in result:
                continue
            definitions: list[tuple[ast.Assign | ast.AnnAssign, ast.expr]] = []
            for candidate in ast.walk(tree):
                if not isinstance(candidate, (ast.Assign, ast.AnnAssign)):
                    continue
                candidate_targets = (
                    candidate.targets if isinstance(candidate, ast.Assign) else [candidate.target]
                )
                if (
                    candidate.value is not None
                    and len(candidate_targets) == 1
                    and _target(candidate_targets[0]) == target
                ):
                    definitions.append((candidate, candidate.value))
            if not definitions or any(isinstance(value, ast.IfExp) for _, value in definitions):
                continue
            classified: list[tuple[str, tuple[int, ...] | None]] = []
            valid = True
            for statement, value in definitions:
                kind = (
                    "corrected"
                    if any(_load_matches(value, known) for known in result)
                    else "raw"
                    if _raw_expr(value, p_names=p_names, p_keys=p_keys) is not None
                    else "none"
                    if isinstance(value, ast.Constant) and value.value is None
                    else "unknown"
                )
                if kind == "unknown":
                    valid = False
                    break
                owner = owners.get(statement, tree)
                positions = _positions_for(
                    statement,
                    tree=tree,
                    owner=owner,
                    parents=parents,
                    sequences=sequences,
                    outcome_columns=outcome_columns,
                )
                classified.append((kind, positions))
            if not valid:
                continue
            if len(classified) == 1:
                kind, positions = classified[0]
                if kind == "none" or positions is None:
                    continue
            elif len(classified) == 2:
                corrected = [positions for kind, positions in classified if kind == "corrected"]
                raw = [positions for kind, positions in classified if kind == "raw"]
                if (
                    len(corrected) != 1
                    or len(raw) != 1
                    or corrected[0] is None
                    or raw[0] is None
                    or set(corrected[0]) != set(fold.positions)
                    or set(raw[0]) != all_positions - set(fold.positions)
                ):
                    continue
            else:
                continue
            result.append(target)
            changed = True
    return tuple(result)


class _Surrogate(ast.NodeTransformer):
    def __init__(self, fold: _Fold, transports: Sequence[tuple[str, object]]) -> None:
        self.fold = fold
        self.transports = tuple(transports)
        raw_target = _target(fold.raw)
        self.cross_field_fold = (
            fold.target[0] == "field"
            and raw_target is not None
            and raw_target[0] == "field"
            and raw_target != fold.target
        )

    def visit(self, node: ast.AST) -> ast.AST:
        if node is self.fold.node:
            return ast.copy_location(copy.deepcopy(self.fold.raw), node)
        return cast(ast.AST, super().visit(node))

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        if (
            self.cross_field_fold
            and len(node.targets) == 1
            and _target(node.targets[0]) == self.fold.target
        ):
            return ast.copy_location(ast.Pass(), node)
        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
        if self.cross_field_fold and _target(node.target) == self.fold.target:
            return ast.copy_location(ast.Pass(), node)
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if isinstance(node.ctx, ast.Load) and any(
            target[0] == "name" and target[1] == node.id for target in self.transports
        ):
            return ast.copy_location(copy.deepcopy(self.fold.raw), node)
        return node

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        node = cast(ast.Subscript, self.generic_visit(node))
        target = _target(node)
        if isinstance(node.ctx, ast.Load) and target in self.transports:
            return ast.copy_location(copy.deepcopy(self.fold.raw), node)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        node = cast(ast.Attribute, self.generic_visit(node))
        target = _target(node)
        if isinstance(node.ctx, ast.Load) and target in self.transports:
            return ast.copy_location(copy.deepcopy(self.fold.raw), node)
        return node


def _surrogate_bytes(
    tree: ast.Module, fold: _Fold, transports: Sequence[tuple[str, object]]
) -> bytes:
    value = copy.deepcopy(tree)
    # deepcopy changes object identities; recover the corresponding correction node by position.
    copied = next(
        node
        for node in ast.walk(value)
        if isinstance(node, ast.expr)
        and _position(node) == _position(fold.node)
        and ast.dump(node, include_attributes=False)
        == ast.dump(fold.node, include_attributes=False)
    )
    copied_fold = _Fold(
        copied,
        copy.deepcopy(fold.raw),
        fold.target,
        fold.positions,
        value if isinstance(fold.owner, ast.Module) else fold.owner,
        fold.form,
        fold.source_line,
    )
    value = cast(ast.Module, _Surrogate(copied_fold, transports).visit(value))
    ast.fix_missing_locations(value)
    return (ast.unparse(value) + "\n").encode("utf-8")


def _analyze_correction_outcome(
    content: bytes,
    *,
    baseline: _Outcome,
    outcome_columns: tuple[str, ...],
    **kwargs: Any,
) -> CorrectionModelResult:
    if baseline.state != "abstain" or baseline.reason_or_classification not in _TARGET_REASONS:
        return CorrectionModelResult(
            baseline, baseline, False, False, None, (), {"gate": "first-reason"}
        )
    try:
        tree = mt._bounded_parse(content)
        resolver, reason = mt._resolver(
            tuple(item for item in tree.body if not mt._is_docstring(item))
        )
        if resolver is None or reason is not None:
            return CorrectionModelResult(
                baseline, baseline, False, False, None, (), {"gate": reason}
            )
        folds, rejected = _folds(
            tree,
            source=content,
            resolver=resolver,
            outcome_columns=outcome_columns,
        )
        threshold = _threshold_fold(
            tree,
            source=content,
            resolver=resolver,
            outcome_columns=outcome_columns,
        )
        if threshold is not None:
            folds.append(threshold)
        if _has_correction_terminal(tree):
            return CorrectionModelResult(
                baseline,
                baseline,
                False,
                bool(folds or rejected),
                None,
                (),
                {"gate": "correction-terminal-present", "rejected": rejected},
            )
        if len(folds) != 1:
            return CorrectionModelResult(
                baseline,
                baseline,
                False,
                bool(folds or rejected),
                None,
                (),
                {"gate": "single-fold", "fold_count": len(folds), "rejected": rejected},
            )
        fold = folds[0]
        if fold.target[0] == "field" and _record_cross_function(
            fold, tree=tree, resolver=resolver, outcome_columns=outcome_columns
        ):
            return CorrectionModelResult(
                baseline,
                baseline,
                False,
                True,
                None,
                (),
                {"gate": "cross-function-record-flow", "line": fold.source_line},
            )
        merge = rm._record_merge_reason(tree, resolver)
        if merge is not None:
            return CorrectionModelResult(
                baseline,
                baseline,
                False,
                True,
                None,
                (),
                {
                    "gate": "_record_merge_reason",
                    "gate_reason": merge,
                    "line": fold.source_line,
                },
            )
        p_names, p_keys = rm._p_lineage(tree, resolver)
        transports = _transport_targets(
            tree,
            fold,
            p_names=p_names,
            p_keys=p_keys,
            outcome_columns=outcome_columns,
        )
        surrogate = _surrogate_bytes(tree, fold, transports)
        surrogate_result = mt.analyze_code_csv_multiple_testing_dataflow(
            surrogate,
            outcome_columns=outcome_columns,
            **kwargs,
        )
        downstream = _classify(surrogate_result)
        if downstream.state != "candidate" or downstream.reason_or_classification != "none":
            return CorrectionModelResult(
                baseline,
                baseline,
                False,
                True,
                None,
                (),
                {
                    "gate": "surrogate-downstream",
                    "surrogate_outcome": downstream.as_json(),
                    "line": fold.source_line,
                },
            )
        positions = fold.positions
        outcome = (
            _Outcome("covered", "complete", positions, len(outcome_columns))
            if positions == tuple(range(len(outcome_columns)))
            else _Outcome("candidate", "strict_subset", positions, len(outcome_columns))
        )
        return CorrectionModelResult(
            outcome,
            baseline,
            outcome != baseline,
            True,
            fold.form,
            positions,
            {
                "line": fold.source_line,
                "source_position": list(_position(fold.node)),
                "transport_count": len(transports),
                "surrogate_outcome": downstream.as_json(),
            },
            "sha256:" + hashlib.sha256(surrogate).hexdigest(),
        )
    except (ArithmeticError, RecursionError, SyntaxError, UnicodeError, ValueError) as exc:
        return CorrectionModelResult(
            baseline,
            baseline,
            False,
            True,
            None,
            (),
            {"gate": "correction-model-exception", "exception": type(exc).__name__},
        )


def analyze_correction_model(
    content: bytes,
    *,
    baseline: mt.MultipleTestingDataflowResult,
    outcome_columns: tuple[str, ...],
    **kwargs: Any,
) -> CorrectionModelResult:
    """Return an immutable AP delta or preserve the frozen source result."""

    return _analyze_correction_outcome(
        content,
        baseline=_classify(baseline),
        outcome_columns=outcome_columns,
        **kwargs,
    )


__all__ = [
    "CODE_CSV_MULTIPLE_TESTING_CORRECTION_MODEL_IMPLEMENTATION_DIGEST",
    "CorrectionModelResult",
    "analyze_correction_model",
]
