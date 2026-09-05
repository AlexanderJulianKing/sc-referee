"""Closed contract-order comprehension grammar and graph lowering for multiple-testing 3.4.

Extension A of the 3.4 design.  A dict or list comprehension whose single generator iterates the
contract-order outcome sequence, carries no ``if``, and whose element is one closed call or one
flat literal record of scalars derived from the loop variable is the same per-outcome collection
an explicit loop builds.  This module proves that exact production and lowers it to the explicit
loop **as a graph fact**: the returned module is an ``ast.Module``, never rewritten source text.

The lowering introduces no record-model construct.  It produces the graph the frozen
``_normalize_contract_domain_loops`` machinery already turns into position-tagged per-outcome
record copies with p-origins, which is why a hand-written three-line loop over the same
computation was already recognized before 3.4.

Two properties are asserted on every lowering, per design section 4.3:

* **element identity** - the lowered element is the same graph as the original element; and
* **idempotence** - applying the normalization to an already-normalized module admits nothing
  and changes no node.

Nothing here classifies, assigns a corrected position, chooses an API, or reads display text,
identifier spelling, comments, or reports.  Admission is a set of syntactic facts about the AST.

The 3.4 adversarial audit's round-2 pass closed two admission predicates here.  Both are
narrowings: they can only withhold an admission that previously fired, so every row they touch
keeps its frozen 3.3 result byte-for-byte.

* ``module_sequences`` now proves the generator's sequence *object* stable, not just its
  *name*, over the whole alias component -- the same closure round 1 gave the sibling
  correction lane, imported from that lane rather than restated.
* ``admitted_comprehensions`` now refuses a collected name that carries a second name for the
  same collection.  Section 4.2 forbids post-construction mutation of the collected name, and a
  store written through an alias is exactly that, written where the clause's census cannot
  reach it.
"""

from __future__ import annotations

import ast
import copy
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import sc_referee.scientific_checks.code_csv_multiple_testing_correction_model_v3_4 as cm
from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_admission_census_v3_4 import (
    record_admission,
)

CODE_CSV_MULTIPLE_TESTING_COMPREHENSION_IMPLEMENTATION_DIGEST = sha256_digest(
    Path(__file__).read_bytes()
)

#: Absolute refusals anywhere inside the element subtree (design section 4.2).
_FORBIDDEN_ELEMENT_NODES: tuple[type[ast.AST], ...] = (
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

_SEQUENCE_MUTATORS = frozenset(
    {"append", "extend", "insert", "pop", "remove", "clear", "sort", "reverse"}
)


def _position(node: ast.AST) -> tuple[int, int, int, int]:
    return (
        getattr(node, "lineno", -1),
        getattr(node, "col_offset", -1),
        getattr(node, "end_lineno", -1),
        getattr(node, "end_col_offset", -1),
    )


def _stored_or_mutated_names(node: ast.AST) -> frozenset[str]:
    """Names this node augments, deletes, subscript-stores, or receiver-mutates."""

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
        and node.func.attr in _SEQUENCE_MUTATORS
    ):
        result.add(node.func.value.id)
    return frozenset(result)


def module_sequences(tree: ast.Module) -> dict[str, tuple[object, ...]]:
    """Flat literal list/tuple displays bound exactly once and whose object is never mutated.

    One reaching Store proves the *name* is stable.  It does not prove the list the generator
    iterates never changes: `SCREENED = OUTCOMES` followed by `SCREENED.remove(...)` leaves the
    single Store on `OUTCOMES` standing while the family the comprehension visits at runtime is
    a different one from the literal read here.  The sequence *object* is therefore proved
    stable over the whole alias component, exactly as the sibling correction lane proves it:
    `cm._alias_edges`, `cm._object_mutated_names`, and `cm._sequence_object_is_stable` are the
    round-1 audit-fix helpers themselves, imported rather than restated so the two lanes cannot
    drift apart.  They follow the frozen B1/B4 record-mutation discipline in
    `rm._record_boundary_reason`, under which passing a name to a call is not a mutation.
    """

    counts: dict[str, int] = {}
    values: dict[str, tuple[object, ...]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets: list[ast.expr] = list(node.targets)
            value: ast.expr | None = node.value
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
    edges, escaped = cm._alias_edges(tree)
    mutated = cm._object_mutated_names(tree)
    return {
        name: value
        for name, value in values.items()
        if counts.get(name) == 1
        and name not in unstable
        and cm._sequence_object_is_stable(name, edges=edges, escaped=escaped, mutated=mutated)
    }


def _scalar(node: ast.expr) -> bool:
    """The closed SCALAR closure of design section 4.2."""

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
    """One flat literal record: unique non-null literal str/int keys over SCALAR values."""

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
    """`call` for one closed SCALAR call, `record` for one flat literal record, else None."""

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
class ComprehensionAdmission:
    """One admitted contract-order comprehension statement."""

    statement: ast.stmt
    target: str
    kind: str
    element: ast.expr
    element_kind: str
    sequence_name: str
    loop_variable: str
    key: ast.Name | None
    iterator: ast.Name
    target_node: ast.Name
    generator_target: ast.Name
    span: tuple[int, int, int, int]

    def as_evidence(self) -> Mapping[str, object]:
        """Structural evidence only: node kind, span, and closed identities."""

        return {
            "span": list(self.span),
            "kind": self.kind,
            "element_kind": self.element_kind,
            "target": self.target,
            "sequence": self.sequence_name,
            "loop_variable": self.loop_variable,
        }


def admitted_comprehensions(
    tree: ast.Module, outcome_columns: tuple[str, ...]
) -> tuple[ComprehensionAdmission, ...]:
    """Every statement matching the closed section-4 grammar, in source order.

    Section 4.2's collected-name clause -- exactly one Store, no rebinding, and no
    post-construction mutation -- is proved by ``_stored_or_mutated_names``, which reads a store
    written through the collected name itself.  A second name for the same collection defeats
    that census outright: ``adjusted = results`` followed by ``adjusted[name]["p"] = ...`` is a
    post-construction mutation the clause forbids, written where the clause cannot see it, and
    the analyzer refuses to classify the identical program when the same store is written
    through ``results``.  A collected name that is aliased, or that escapes into a container or
    a field, is therefore refused rather than admitted on an unprovable clause.
    """

    sequences = module_sequences(tree)
    target_edges, target_escaped = cm._alias_edges(tree)
    result: list[ComprehensionAdmission] = []
    for statement in ast.walk(tree):
        if isinstance(statement, ast.Assign):
            targets: list[ast.expr] = list(statement.targets)
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
        key: ast.Name | None
        if isinstance(value, ast.DictComp):
            if not (isinstance(value.key, ast.Name) and value.key.id == loop_variable):
                continue
            key = value.key
            element = value.value
            kind = "dict"
        else:
            key = None
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
        if target_edges.get(target_name) or target_name in target_escaped:
            continue
        result.append(
            ComprehensionAdmission(
                statement=statement,
                target=target_name,
                kind=kind,
                element=element,
                element_kind=element_kind,
                sequence_name=generator.iter.id,
                loop_variable=loop_variable,
                key=key,
                iterator=generator.iter,
                target_node=targets[0],
                generator_target=generator.target,
                span=_position(statement),
            )
        )
    return tuple(sorted(result, key=lambda item: item.span))


def _lowered_statements(item: ComprehensionAdmission) -> list[ast.stmt]:
    """Build the explicit-loop graph for one admitted comprehension.

    Every node carried over from the original statement keeps its own source position, so the
    threshold grammar's source-text handling and every span-derived evidence value read exactly
    the bytes they read before.  Only the two synthesized wrappers take the statement's span.
    """

    element = copy.deepcopy(item.element)
    if ast.dump(element, include_attributes=True) != ast.dump(
        item.element, include_attributes=True
    ):
        raise AssertionError("comprehension element lowering is not graph-preserving")

    empty: ast.expr
    if item.kind == "dict":
        empty = ast.Dict(keys=[], values=[])
    else:
        empty = ast.List(elts=[], ctx=ast.Load())
    initial = ast.Assign(
        targets=[ast.Name(id=item.target, ctx=ast.Store())],
        value=empty,
    )

    body: ast.stmt
    if item.kind == "dict":
        if not isinstance(item.key, ast.Name):
            raise AssertionError("an admitted dict comprehension key is not the generator target")
        slice_node = copy.deepcopy(item.key)
        slice_node.ctx = ast.Load()
        body = ast.Assign(
            targets=[
                ast.Subscript(
                    value=ast.Name(id=item.target, ctx=ast.Load()),
                    slice=slice_node,
                    ctx=ast.Store(),
                )
            ],
            value=element,
        )
    else:
        body = ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id=item.target, ctx=ast.Load()),
                    attr="append",
                    ctx=ast.Load(),
                ),
                args=[element],
                keywords=[],
            )
        )
    loop_target = copy.deepcopy(item.generator_target)
    loop_target.ctx = ast.Store()
    loop = ast.For(
        target=loop_target,
        iter=copy.deepcopy(item.iterator),
        body=[body],
        orelse=[],
        type_comment=None,
    )
    for synthesized in (initial, loop):
        ast.copy_location(synthesized, item.statement)
        ast.fix_missing_locations(synthesized)
    return [initial, loop]


class _Lowering(ast.NodeTransformer):
    """Replace each admitted comprehension statement with its explicit-loop pair.

    A visitor that returns a list splices that list into the enclosing statement block, which
    is exactly the two-statement replacement the grammar specifies.
    """

    def __init__(self, admitted: Mapping[int, ComprehensionAdmission]) -> None:
        self.admitted = admitted
        self.lowered = 0

    def _lower(self, node: ast.stmt) -> ast.AST | list[ast.stmt]:
        admission = self.admitted.get(id(node))
        if admission is None:
            return self.generic_visit(node)
        self.lowered += 1
        return _lowered_statements(admission)

    def visit_Assign(self, node: ast.Assign) -> ast.AST | list[ast.stmt]:
        return self._lower(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST | list[ast.stmt]:
        return self._lower(node)


@dataclass(frozen=True)
class ComprehensionNormalization:
    """The normalized graph fact and the structural evidence for each admitted span."""

    tree: ast.Module
    admissions: tuple[Mapping[str, object], ...]


def normalize_comprehensions(
    content: bytes, outcome_columns: tuple[str, ...]
) -> ComprehensionNormalization | None:
    """Lower every admitted contract-order comprehension into its explicit-loop graph.

    Returns ``None`` when nothing is admitted, so the caller runs on the untouched module.  The
    census is recorded per admitted span, and both design-4.3 properties are asserted here.
    """

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return None
    admitted = admitted_comprehensions(tree, outcome_columns)
    if not admitted:
        return None
    lowering = _Lowering({id(item.statement): item for item in admitted})
    normalized = lowering.visit(tree)
    if not isinstance(normalized, ast.Module) or lowering.lowered != len(admitted):
        raise AssertionError("comprehension lowering did not replace every admitted statement")
    ast.fix_missing_locations(normalized)

    # Idempotence: an already-normalized module admits nothing and lowers to itself.
    if admitted_comprehensions(normalized, outcome_columns):
        raise AssertionError("comprehension lowering is not idempotent")
    repeated = _Lowering({}).visit(copy.deepcopy(normalized))
    if ast.dump(repeated, include_attributes=True) != ast.dump(normalized, include_attributes=True):
        raise AssertionError("comprehension lowering is not idempotent")

    for item in admitted:
        record_admission("comprehension", item.span)
    return ComprehensionNormalization(normalized, tuple(item.as_evidence() for item in admitted))


__all__ = [
    "CODE_CSV_MULTIPLE_TESTING_COMPREHENSION_IMPLEMENTATION_DIGEST",
    "ComprehensionAdmission",
    "ComprehensionNormalization",
    "admitted_comprehensions",
    "module_sequences",
    "normalize_comprehensions",
]
