"""Strict AP(C, POS) correction recognizer for multiple-testing 3.4.

Versioned copy of the byte-frozen 3.3 recognizer.  It never executes project code and never
classifies by itself.  It admits only the closed Bonferroni productions, subtracts one proved
correction fold on a structural surrogate, and requires the frozen 3.0 analyzer to prove the
remaining raw family independently.

Exactly two 3.4 admissions are added, and nothing else in this module moves:

* **extension C**, the `enumerate` row-table iterator (design section 6).  `_complete_rows`
  admits `enumerate(NAME)` and `enumerate(NAME, start=K)` alongside the bare contract-sequence
  Name.  Positions still come from the index of each element in the sequence, so `K` never
  enters position derivation.  The counter is bound to an opaque object that is neither a
  `bool` nor any contract outcome string, so `_static_bool` returns `None` for it and any use
  of the counter in a correction or decision path refuses.
* **extension D**, the adjacent if-cap fold (design section 7).  The exact two-statement pair
  `X = A * B` followed immediately by `if X > 1.0: X = 1.0` is one fold equivalent to
  `min(A * B, 1.0)`.  Its three consequences are the competing-assignment exclusion in
  `_fold_target_is_unique`, the position-transparent cap `If` in `_positions_for`, and the
  surrogate dropping the whole cap statement together with its fold.

Factor resolution, name-set selection, transport proofs, conclusion consumption, wording, and
classification are untouched.

The 3.4 adversarial audit closed two admission predicates.  Both are narrowings: they can only
withhold an admission that previously fired, so every row they touch keeps its frozen 3.3
result byte-for-byte.

* `_module_sequences` now proves the sequence *object* stable, not just the sequence *name*.
  A single reaching Store says nothing about `NAME.extend(...)`, an augmented assignment, a
  slice store, or the same three written through an alias, each of which grows the family a
  membership guard selects at runtime while the literal the recognizer reads stays put.  The
  closure runs over the whole alias component and follows the frozen B1/B4 record-mutation
  discipline in `rm._record_boundary_reason`.  Round 2 extended its escape half to container
  displays, because `PLAN = {"family": SEQ}` followed by `PLAN["family"].extend(...)` grows the
  same list with nothing the mutation census can see, and gave the sibling comprehension lane
  the identical closure by importing these three helpers rather than restating them.
* `_enumerate_sequence_name` now requires `enumerate` to be the unshadowed builtin, proved
  module-wide by the frozen `mt._definition_shadows_builtin` census.  A project-local
  definition of the name is never read as the builtin row-table iterator.
"""

from __future__ import annotations

import ast
import copy
import hashlib
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, cast

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v3 as mt
import sc_referee.scientific_checks.code_csv_multiple_testing_record_model_v3 as rm
from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.code_csv_multiple_testing_admission_census_v3_4 import (
    record_admission,
)

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


@dataclass(frozen=True)
class _TransportProof:
    target: tuple[str, object]
    corrected_positions: tuple[int, ...]
    raw_positions: tuple[int, ...]


@dataclass(frozen=True)
class _ConclusionConsumption:
    corrected_positions: tuple[int, ...]
    raw_positions: tuple[int, ...]
    comparison_positions: tuple[tuple[int, int, int, int], ...]


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


def _alias_edges(tree: ast.Module) -> tuple[dict[str, set[str]], frozenset[str]]:
    """Bare Name-to-Name bindings, and every name bound somewhere this module cannot follow.

    `A = B` binds one object to two names, so the edge is undirected: a mutation reached
    through either name changes what the other one reads.  A bare Name bound anywhere other
    than a single Name target -- a tuple unpack, a record field, a subscript -- escapes into a
    location whose later mutations are not enumerable here, and is refused outright.

    A container display escapes the same way and for the same reason.  `PLAN = {"family": SEQ}`
    stores the list object behind a subscript path, and `PLAN["family"].extend(...)` then grows
    it with no Store, no augmented assignment, and no method call whose receiver is a Name, so
    nothing the mutation census can see moves.  Every bare Name read into a list, tuple, set, or
    dict display is therefore refused, however deeply the displays are nested, because walking
    the module reaches each display in turn.  Reading a name into a call argument is not a
    capture and stays admissible -- that is the frozen `len(OUTCOMES)` and
    `", ".join(MUSCULOSKELETAL)` discipline, which the pinned 3.3 evidence rows depend on.
    """

    edges: dict[str, set[str]] = {}
    escaped: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            escaped.update(
                item.id
                for item in node.elts
                if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
            )
            continue
        if isinstance(node, ast.Dict):
            escaped.update(
                item.id
                for item in (*node.keys, *node.values)
                if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
            )
            continue
        if isinstance(node, ast.Assign):
            targets: list[ast.expr] = list(node.targets)
            value: ast.expr | None = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        elif isinstance(node, ast.NamedExpr):
            # A walrus is a binding like any other, so it aliases like any other.
            targets = [node.target]
            value = node.value
        else:
            continue
        if not isinstance(value, ast.Name):
            continue
        if len(targets) == 1 and isinstance(targets[0], ast.Name):
            left, right = targets[0].id, value.id
            edges.setdefault(left, set()).add(right)
            edges.setdefault(right, set()).add(left)
        else:
            escaped.add(value.id)
    return edges, frozenset(escaped)


def _object_mutated_names(tree: ast.Module) -> frozenset[str]:
    """Every name whose bound object is mutated in place anywhere in the module.

    These are the exact forms the frozen B1/B4 record-mutation closure in
    `rm._record_boundary_reason` refuses on its tracked names: an augmented assignment, a
    `del`, a subscript or slice store, and a receiver method call.  Passing a name to a call
    is not a mutation there and is not one here either -- the frozen 3.3 evidence rows read
    `len(OUTCOMES)` and `", ".join(MUSCULOSKELETAL)`.
    """

    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AugAssign):
            root = rm._root_name(node.target)
            if root is not None:
                result.add(root)
        elif isinstance(node, ast.Delete):
            result.update(
                root for target in node.targets if (root := rm._root_name(target)) is not None
            )
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Subscript):
                    root = rm._root_name(target)
                    if root is not None:
                        result.add(root)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        ):
            result.add(node.func.value.id)
    return frozenset(result)


def _sequence_object_is_stable(
    name: str,
    *,
    edges: Mapping[str, set[str]],
    escaped: frozenset[str],
    mutated: frozenset[str],
) -> bool:
    """No name that reaches this sequence object is ever mutated in place.

    A single reaching Store proves the *name* is stable; it does not prove the list it reads
    never changes.  `MUSCULOSKELETAL.extend(OUTCOMES[3:])`, and the same call, `+=`, or slice
    assignment written through an alias, all leave one Store standing while the family the
    membership guard selects grows at runtime.  The closure is therefore over the whole alias
    component, and an alias this module cannot follow refuses the sequence outright.
    """

    seen = {name}
    frontier = [name]
    while frontier:
        current = frontier.pop()
        if current in mutated or current in escaped:
            return False
        for neighbour in edges.get(current, ()):
            if neighbour not in seen:
                seen.add(neighbour)
                frontier.append(neighbour)
    return True


#: The seed calls that open an empty record collection, alongside the mapping and list displays.
_COLLECTION_SEED_CALLS = frozenset({"dict", "list"})


def _collection_seed(value: ast.expr) -> bool:
    """The value forms that open a collection the module then fills member by member.

    The display need not be empty.  `results = {"_notes": "..."}` filled per outcome is the same
    collection as `results = {}` filled per outcome, and the alias asymmetry survives the extra
    key intact, so restricting the seed to an empty display would leave the whole route open one
    character away from the reported one.  A display that is never subscript-stored -- the
    declared outcome list, a label table -- is excluded by the store requirement below rather
    than by the shape of its seed.
    """

    if isinstance(value, (ast.DictComp, ast.ListComp, ast.Dict, ast.List)):
        return True
    return bool(
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in _COLLECTION_SEED_CALLS
        and not value.args
        and not value.keywords
    )


def record_collection_names(tree: ast.Module) -> frozenset[str]:
    """Every name bound once to a collection this module then fills by subscript store.

    This is the family container the frozen engine reconstructs member identity from: a name
    opened as a mapping or list and filled at `NAME[member] = record`, or bound to one
    comprehension, which is the same container written in one statement and is how the frozen
    3.3 evidence rows build it.  The store requirement is what separates a collection the module
    fills from a literal table it only reads, so the declared outcome list and the label table
    are never tracked however they are aliased.

    List builders filled by `append` are deliberately absent.  The frozen B1/B4 closure in
    `rm._record_boundary_reason` already refuses a second name for a tracked builder collection,
    so nothing here would add to it, and every name this predicate returns widens the closure
    below.
    """

    subscript_stored: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
            if isinstance(target, ast.Subscript):
                root = rm._root_name(target)
                if root is not None:
                    subscript_stored.add(root)
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target, value = node.target, node.value
        else:
            continue
        if not isinstance(target, ast.Name) or not _collection_seed(value):
            continue
        if (
            not isinstance(value, (ast.DictComp, ast.ListComp))
            and target.id not in subscript_stored
        ):
            continue
        if _name_stable(tree, target.id):
            result.add(target.id)
    return frozenset(result)


#: Round 4: the element shapes a record-derived binding can carry.  `_RECORD` is one of the
#: tracked record objects, reached through a view or a lookup that can only hand out records.
#: `_OPAQUE` is anything else.  A fixed-length unpack carries a tuple of shapes.
_RECORD = "record"
_OPAQUE = "opaque"

#: The mapping views that hand out the collection's own record objects, and the one that does not.
#: `X.keys()` yields keys, and a key is not a record: the store a key reaches is `X[k][...]`,
#: which is written through the collection's own name and is already what the frozen engine sees.
_RECORD_VIEW_METHODS = frozenset({"items", "values"})
_KEY_VIEW_METHODS = frozenset({"keys"})

#: A shallow copy is a different container holding the *same* record objects, so a store through
#: one of its records changes what the original collection reads.
_SHALLOW_COPY_METHODS = frozenset({"copy"})

#: The mapping methods that hand out one record by key.
_RECORD_LOOKUP_METHODS = frozenset({"get", "pop", "setdefault"})

#: The builtins that re-wrap an iterable without copying the objects it yields.
_ITERABLE_WRAPPERS = frozenset({"iter", "list", "reversed", "sorted", "tuple"})
#: The builtin that copies a mapping.  `dict(X)` is a shallow copy: a different mapping holding
#: the same record objects, so its records are the collection's records.
_MAPPING_WRAPPERS = frozenset({"dict"})


class _RecordDerivation:
    """The closed enumeration of names bound to a tracked record collection's records.

    Round 3 followed bare `A = B` alias edges, which is the only way a *name for the collection*
    can be made.  It is not the only way a *store into the collection* can be made.  A loop
    target bound from `results.items()` is not an alias edge, so

    ```python
    for name, record in results.items():
        record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
    ```

    wrote a complete Bonferroni correction that round 3 could not see, and the row was published
    as an accusation that a corrected analysis was never corrected.  The binding form is
    incidental: `.values()`, `enumerate`, `zip`, `sorted`, `list`, `reversed`, `dict(X).items()`,
    `X[k]`, `X.get(k)`, `X.setdefault(k, ...)`, `X.pop(k)`, `next(iter(X.values()))`,
    `list(X.values())[i]`, and the walrus and comprehension spellings of each all hand out the
    same record objects.  This class enumerates that whole class of bindings at once so the
    closure stops being one spelling behind the next audit.

    Three roles are tracked, because the forms compose:

    * **mappings** -- names for a container still keyed or indexed by family member whose values
      are the tracked records: the collection, its round-3 aliases, `dict(X)`, and `X.copy()`.
      A mapping is what `.items()`, `.values()`, and `X[k]` are read from.
    * **sequences** -- names bound to an iterable, or to a fixed-length unpack, that yields the
      records: `list(X.values())`, `X.items()`, `enumerate(X.values())`, `zip(X.values(), ...)`,
      a generator expression over any of them.  The recorded shape is what one element looks
      like, so a `(key, record)` pair binds only its second element as a record.
    * **records** -- names for one record object.

    Two element positions are deliberately `_OPAQUE`, and both boundaries were measured rather
    than argued.  The key half of an `items()` unpack is not a record: a key is not a record, the
    store a key reaches is `X[k][...]`, which is written through the collection's own name and is
    already what the frozen engine refuses, and treating the key as a record would refuse the
    ordinary presentation loop
    `for name, record in results.items(): print(name.title(), record["p"])` over a family that
    really was left uncorrected.  The target of a bare `for x in X` is not a record either:
    iterating a mapping yields keys and iterating a list yields whatever it holds, which for a
    collected p-value table is a float, and the collection's seed does not say which.  Four
    pinned rows are true accusations that survive only because of the second boundary -- two
    envelope positives whose partial Holm adjustment is written `for row, adjusted in
    zip(primary, p_adjusted): row["p_adjusted"] = ...` with the correction terminal itself
    plainly visible, and two open-corpus missteps that read a loop variable of a tracked list
    into a display.  In every measured row where a bare iteration really does hand out records,
    the store it reaches is either written through the collection's own name, which the frozen
    engine refuses on its own, or accompanied by a correction terminal the engine already reads.

    Argument passing is not a binding form here.  A name read into a call argument stays a
    non-capture, which is the frozen `len(OUTCOMES)` discipline the pinned 3.3 evidence rows
    depend on and which rounds 1 to 3 all preserve.

    Names are matched module-wide, as they are in rounds 1 to 3.  A name reused in two scopes can
    only add bindings, so the error is toward refusal.
    """

    def __init__(self, mappings: frozenset[str]) -> None:
        self.mappings: set[str] = set(mappings)
        self.sequences: dict[str, object] = {}
        self.records: set[str] = set()

    # -- expression classifiers ---------------------------------------------------------

    def maps_records(self, node: ast.expr) -> bool:
        """True when the expression is a container still keyed or indexed by family member."""

        if isinstance(node, ast.NamedExpr):
            return self.maps_records(node.value)
        if isinstance(node, ast.Name):
            return node.id in self.mappings
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in _SHALLOW_COPY_METHODS
                and not node.args
            ):
                return self.maps_records(node.func.value)
            if isinstance(node.func, ast.Name) and node.func.id in _MAPPING_WRAPPERS:
                return any(self.maps_records(argument) for argument in node.args)
        return False

    def element_shape(self, node: ast.expr) -> object:
        """The shape of one element produced by iterating the expression."""

        if isinstance(node, ast.NamedExpr):
            return self.element_shape(node.value)
        if isinstance(node, ast.Name):
            # A bare name for the collection is iterated ambiguously -- keys for a mapping,
            # elements for a list -- so its target is not enumerated as a record.
            return self.sequences.get(node.id, _OPAQUE)
        if isinstance(node, ast.Call):
            return self._call_element_shape(node)
        if isinstance(node, (ast.GeneratorExp, ast.ListComp, ast.SetComp)):
            return _RECORD if self.is_record(node.elt) else _OPAQUE
        return _OPAQUE

    def _call_element_shape(self, node: ast.Call) -> object:
        function = node.func
        if isinstance(function, ast.Attribute):
            if not self.maps_records(function.value):
                return _OPAQUE
            if function.attr in _KEY_VIEW_METHODS:
                return _OPAQUE
            if function.attr in _RECORD_VIEW_METHODS:
                return (_OPAQUE, _RECORD) if function.attr == "items" else _RECORD
            return _OPAQUE
        if not isinstance(function, ast.Name):
            return _OPAQUE
        if function.id == "enumerate" and node.args:
            return (_OPAQUE, self.element_shape(node.args[0]))
        if function.id == "zip":
            return tuple(self.element_shape(argument) for argument in node.args)
        if function.id in _ITERABLE_WRAPPERS and node.args:
            return self.element_shape(node.args[0])
        # `dict(X)` is a mapping, so iterating it yields keys.  Its records are reached through
        # `.items()`, `.values()`, or a subscript, each of which reads `maps_records` instead.
        return _OPAQUE

    def is_record(self, node: ast.expr) -> bool:
        """True when the expression evaluates to one of the tracked record objects."""

        if isinstance(node, ast.NamedExpr):
            return self.is_record(node.value)
        if isinstance(node, ast.Name):
            return node.id in self.records
        if isinstance(node, ast.Subscript) and not isinstance(node.slice, ast.Slice):
            return self.maps_records(node.value) or self.element_shape(node.value) is _RECORD
        if isinstance(node, ast.Call):
            function = node.func
            if (
                isinstance(function, ast.Attribute)
                and function.attr in _RECORD_LOOKUP_METHODS
                and self.maps_records(function.value)
            ):
                return True
            if (
                isinstance(function, ast.Name)
                and function.id == "next"
                and node.args
                and self.element_shape(node.args[0]) is _RECORD
            ):
                return True
        return False

    # -- binding ------------------------------------------------------------------------

    def _carries_record(self, shape: object) -> bool:
        if shape is _RECORD:
            return True
        return isinstance(shape, tuple) and any(self._carries_record(item) for item in shape)

    def _add(self, group: set[str], name: str) -> bool:
        if name in group:
            return False
        group.add(name)
        return True

    def _bind_target(self, target: ast.expr, shape: object) -> bool:
        """Distribute an element shape over a loop target or an unpacking assignment target."""

        if isinstance(target, ast.Name):
            if shape is _RECORD:
                return self._add(self.records, target.id)
            if isinstance(shape, tuple) and self._carries_record(shape):
                if self.sequences.get(target.id) == shape:
                    return False
                self.sequences[target.id] = shape
                return True
            return False
        if isinstance(target, (ast.Tuple, ast.List)) and isinstance(shape, tuple):
            if len(target.elts) != len(shape):
                # A starred or mismatched unpack is not enumerable here.  Every element is
                # treated as a record so the error stays toward refusal.
                pairs: list[tuple[ast.expr, object]] = [
                    (element, _RECORD) for element in target.elts
                ]
            else:
                pairs = list(zip(target.elts, shape, strict=True))
            changed = False
            for element, item in pairs:
                # Every element is bound: `any` over a generator would stop at the first one
                # that moved and leave the rest to a later pass of the fixpoint.
                changed = self._bind_target(element, item) or changed
            return changed
        return False

    def _bind_value(self, target: ast.expr, value: ast.expr) -> bool:
        """Bind an assignment target.  The value is the object itself, not one of its elements.

        `family = list(results.values())` binds a *sequence of* records, so the shape belongs in
        `sequences`, where a later `for record in family` reads it back as its element shape.
        Filing it as a record instead would end the chain one binding early, which is the whole
        failure mode this round exists to close.
        """

        changed = False
        if isinstance(target, ast.Name):
            if self.is_record(value):
                changed = self._add(self.records, target.id) or changed
            if self.maps_records(value):
                changed = self._add(self.mappings, target.id) or changed
            shape = self.element_shape(value)
            if self._carries_record(shape) and self.sequences.get(target.id) != shape:
                self.sequences[target.id] = shape
                changed = True
            # A bare `A = B` binds one object to two names, so the record role is undirected
            # exactly as the round-3 alias edge is.
            if isinstance(value, ast.Name) and target.id in self.records:
                changed = self._add(self.records, value.id) or changed
        elif isinstance(value, ast.Name) and value.id in self.sequences:
            changed = self._bind_target(target, self.sequences[value.id]) or changed
        return changed

    def resolve(self, tree: ast.Module) -> None:
        """Grow the three role sets to a fixpoint over the whole module."""

        changed = True
        while changed:
            changed = False
            for node in ast.walk(tree):
                if isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
                    shape = self.element_shape(node.iter)
                    changed = self._bind_target(node.target, shape) or changed
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        changed = self._bind_value(target, node.value) or changed
                elif isinstance(node, ast.AnnAssign) and node.value is not None:
                    changed = self._bind_value(node.target, node.value) or changed
                elif isinstance(node, ast.NamedExpr):
                    changed = self._bind_value(node.target, node.value) or changed
                elif isinstance(node, ast.withitem) and node.optional_vars is not None:
                    changed = self._bind_value(node.optional_vars, node.context_expr) or changed

    def names(self) -> frozenset[str]:
        return frozenset(self.mappings | set(self.sequences) | self.records)


def record_derived_names(tree: ast.Module, collection_aliases: frozenset[str]) -> frozenset[str]:
    """Every name that reaches a record of the given collection, or a container of them.

    `collection_aliases` is the round-3 alias component of one record collection: the collection
    name and every other bare name for the same object.  The result is that component closed
    under the enumerated record-derived binding forms, including their chains -- an alias of an
    alias, a loop over a list built from a view of a copy, a record rebound to a third name.
    """

    derivation = _RecordDerivation(collection_aliases)
    derivation.resolve(tree)
    return derivation.names()


def record_collection_alias_unresolved(tree: ast.Module) -> bool:
    """True when a store or mutation of a record collection hides behind a second name for it.

    The frozen engine reconstructs the p-value family from the stores written *through the
    collection name*.  A store written through any other name for the same object is invisible
    to it, so `adjusted = results` followed by `adjusted[name]["p"] = ...` is read as a family
    that was never corrected, while the identical program written through `results` refuses at
    `pvalue-family-collection-unresolved` because the member the store names cannot be resolved.
    The alias does not make the family reconstructable; it only makes the store unreachable.

    The closure is the round-1/round-2 one, over the collection name's whole alias component:
    `_alias_edges` supplies the undirected Name-to-Name edges and the container/field/tuple
    display escapes, and `_object_mutated_names` supplies the in-place mutation census.  The
    collection's *own* stores are excluded, because those are exactly what the frozen engine
    already sees and judges.  Reads through an alias move nothing and are not refused here:
    `verdict = adjusted[name]["p"] < ALPHA` with no store anywhere leaves the component clean.

    Round 4 widens *which names* the walk covers and changes nothing else.  A second name for the
    collection is not the only binding a store can travel through: a loop target bound from
    `results.items()` holds the record itself, and `record["p"] = ...` was invisible to the
    round-3 component for the same reason `adjusted[name]["p"] = ...` was invisible to the frozen
    engine.  `record_derived_names` supplies the closed enumeration of those bindings -- the
    iteration targets, the subscript and lookup bindings, their walrus and comprehension
    spellings, and every chain of them -- and each one is checked against the same escape set and
    the same mutation census the alias component is checked against.  Reads through them stay
    admissible, which is what keeps the ordinary presentation loop a true accusation.

    Names are matched module-wide rather than per scope, as they are in rounds 1 to 3.  A name
    reused in two scopes can only add edges, so the error is toward refusal.
    """

    edges, escaped = _alias_edges(tree)
    mutated = _object_mutated_names(tree)
    for collection in record_collection_names(tree):
        component = {collection}
        frontier = [collection]
        while frontier:
            current = frontier.pop()
            for neighbour in edges.get(current, ()):
                if neighbour not in component:
                    component.add(neighbour)
                    frontier.append(neighbour)
        for name in component | set(record_derived_names(tree, frozenset(component))):
            if name in escaped:
                return True
            if name != collection and name in mutated:
                return True
    return False


def _module_sequences(tree: ast.Module) -> dict[str, tuple[object, ...]]:
    result: dict[str, tuple[object, ...]] = {}
    edges, escaped = _alias_edges(tree)
    mutated = _object_mutated_names(tree)
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
            if not _sequence_object_is_stable(name, edges=edges, escaped=escaped, mutated=mutated):
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


class _EnumerateCounter:
    """Opaque row binding for an admitted `enumerate` counter (design section 6.2).

    Every structural predicate that can consume a row value tests for a `bool` or for equality
    with a contract outcome string.  This object is neither, so `_static_bool` returns `None`
    for it, `_positions_for` then refuses the fold, and the contract-order check never matches
    it.  The counter therefore cannot select positions, supply a factor, or gate a fold.  That
    is a property of what the counter is bound to, not a judgement about its spelling.
    """

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return "<enumerate-counter>"


_ENUMERATE_COUNTER = _EnumerateCounter()


def _enumerate_is_the_unshadowed_builtin(tree: ast.Module) -> bool:
    """`enumerate` in this module is the builtin and nothing else.

    `mt._definition_shadows_builtin` is the census the frozen lanes already use to prove a name
    in `_UNSHADOWED_BUILTINS` is not rebound anywhere in the module by a function or class
    definition, an import, a parameter, or any Store or Del of the name -- which covers an
    assignment, a comprehension target, and a loop target.  `global` and `nonlocal` are the one
    binding form that census does not carry, so they are refused here as well.  A project-local
    `def enumerate` is then never read as the builtin row-table iterator.
    """

    if mt._definition_shadows_builtin(tree):
        return False
    return not any(
        isinstance(node, (ast.Global, ast.Nonlocal)) and "enumerate" in node.names
        for node in ast.walk(tree)
    )


def _enumerate_sequence_name(
    node: ast.expr, sequences: Mapping[str, tuple[object, ...]], *, tree: ast.Module
) -> str | None:
    """The stable sequence Name of an admitted `enumerate` iterator, else None."""

    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "enumerate"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
    ):
        return None
    if not _enumerate_is_the_unshadowed_builtin(tree):
        return None
    if node.keywords:
        if len(node.keywords) != 1:
            return None
        keyword = node.keywords[0]
        if keyword.arg != "start" or not isinstance(keyword.value, ast.Constant):
            return None
        if not isinstance(keyword.value.value, int) or isinstance(keyword.value.value, bool):
            return None
    name = node.args[0].id
    return name if name in sequences else None


def _enumerate_rows(
    loop: ast.For,
    *,
    tree: ast.Module,
    sequences: Mapping[str, tuple[object, ...]],
    outcome_columns: tuple[str, ...],
) -> tuple[dict[str, object], ...] | None:
    """The 3.4 `enumerate` row table.  Positions come from sequence order, never from K."""

    sequence_name = _enumerate_sequence_name(loop.iter, sequences, tree=tree)
    if sequence_name is None:
        return None
    names = _target_names(loop.target)
    if names is None or len(names) != 2 or names[0] == names[1]:
        return None
    rows = sequences[sequence_name]
    if len(rows) != len(outcome_columns):
        return None
    mappings: list[dict[str, object]] = []
    for row in rows:
        if isinstance(row, tuple):
            return None
        mappings.append({names[0]: _ENUMERATE_COUNTER, names[1]: row})
    if tuple(row[names[1]] for row in mappings) != outcome_columns:
        return None
    record_admission("enumerate", _position(loop.iter))
    return tuple(mappings)


def _complete_rows(
    loop: ast.For,
    *,
    tree: ast.Module,
    owner: ast.Module | ast.FunctionDef,
    sequences: Mapping[str, tuple[object, ...]],
    outcome_columns: tuple[str, ...],
) -> tuple[dict[str, object], ...] | None:
    if not isinstance(loop.iter, ast.Name) or loop.iter.id not in sequences:
        return _enumerate_rows(
            loop, tree=tree, sequences=sequences, outcome_columns=outcome_columns
        )
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


def _statement_blocks(node: ast.AST) -> Iterator[list[ast.stmt]]:
    """Every statement block in the module, so adjacency is proved inside one block."""

    for parent in ast.walk(node):
        for slot in ("body", "orelse", "finalbody"):
            block = getattr(parent, slot, None)
            if isinstance(block, list) and all(isinstance(item, ast.stmt) for item in block):
                yield cast("list[ast.stmt]", block)


def _cap_guard_on_name(test: ast.expr, name: str) -> bool:
    """One of exactly four forms: `X > 1`, `X >= 1`, `1 < X`, `1 <= X` (design section 7.2)."""

    if not (isinstance(test, ast.Compare) and len(test.ops) == 1 and len(test.comparators) == 1):
        return False
    left, right, operator = test.left, test.comparators[0], test.ops[0]
    if isinstance(operator, (ast.Gt, ast.GtE)):
        return isinstance(left, ast.Name) and left.id == name and _numeric_one(right)
    if isinstance(operator, (ast.Lt, ast.LtE)):
        return _numeric_one(left) and isinstance(right, ast.Name) and right.id == name
    return False


@dataclass(frozen=True)
class _AdmittedCap:
    """One exact adjacent `X = A * B` / `if X > 1.0: X = 1.0` pair."""

    product: ast.Assign
    guard: ast.If
    reassignment: ast.Assign
    name: str


def admitted_caps(tree: ast.Module) -> tuple[_AdmittedCap, ...]:
    """Every admitted adjacent if-cap pair, which is one fold equal to `min(A * B, 1.0)`.

    Nothing else is absorbed: a non-adjacent cap, a guard on a different Name, a guard against
    a value other than the literal one, an `else` arm, or an if-body holding any other
    statement stays a second reaching fold and refuses exactly as it does under 3.3.
    """

    result: list[_AdmittedCap] = []
    for block in _statement_blocks(tree):
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
            if not _cap_guard_on_name(following.test, name) or len(following.body) != 1:
                continue
            inner = following.body[0]
            if not (
                isinstance(inner, ast.Assign)
                and len(inner.targets) == 1
                and isinstance(inner.targets[0], ast.Name)
                and inner.targets[0].id == name
                and _numeric_one(inner.value)
            ):
                continue
            result.append(_AdmittedCap(statement, following, inner, name))
    return tuple(result)


def admitted_cap_statement(
    fold_statement: ast.stmt, name: str, tree: ast.Module
) -> ast.Assign | None:
    """The cap reassignment absorbed into the fold whose product is `fold_statement`."""

    for cap in admitted_caps(tree):
        if cap.product is fold_statement and cap.name == name:
            return cap.reassignment
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
    # An admitted cap guard is not a family-position selector: it chooses between `A * B` and
    # `1.0` for the *same* position, which is what `min` does.  It is therefore transparent
    # here.  Every other `If`, and every `Try`, `While`, `Match`, and `With`, is unchanged.
    cap_guards = {id(cap.guard) for cap in admitted_caps(tree)}
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
        if isinstance(parent, ast.If) and id(parent) not in cap_guards:
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
    """Prove one reaching fold, allowing only an exact raw/None complementary branch.

    One 3.4 change: an admitted adjacent cap reassignment is excluded from the competing set,
    because the product and its cap are one fold equal to `min(A * B, 1.0)` rather than two.
    """

    cap: ast.Assign | None = None
    kind, cap_name = fold.target
    if kind == "name" and isinstance(cap_name, str):
        fold_statement = parents.get(fold.node)
        if isinstance(fold_statement, (ast.Assign, ast.AnnAssign)):
            cap = admitted_cap_statement(cast(ast.stmt, fold_statement), cap_name, tree)
    if cap is not None:
        record_admission("cap", _position(cap))

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
        if node is cap:
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


def _transport_proofs(
    tree: ast.Module,
    fold: _Fold,
    *,
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
    outcome_columns: tuple[str, ...],
) -> tuple[_TransportProof, ...]:
    parents = _parents(tree)
    owners = _owners(tree)
    sequences = _module_sequences(tree)
    all_positions = set(range(len(outcome_columns)))
    initial_raw: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if (
            len(targets) == 1
            and _target(targets[0]) == fold.target
            and node.value is not fold.node
            and _raw_expr(node.value, p_names=p_names, p_keys=p_keys) is not None
        ):
            positions = _positions_for(
                node,
                tree=tree,
                owner=owners.get(node, tree),
                parents=parents,
                sequences=sequences,
                outcome_columns=outcome_columns,
            )
            if positions is not None:
                initial_raw.update(positions)
    result = [_TransportProof(fold.target, fold.positions, tuple(sorted(initial_raw)))]
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if (
                len(targets) != 1
                or (target := _target(targets[0])) is None
                or any(item.target == target for item in result)
            ):
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
            classified: list[tuple[str, tuple[int, ...] | None, _TransportProof | None]] = []
            valid = True
            for statement, value in definitions:
                known = [item for item in result if _load_matches(value, item.target)]
                if len(known) == 1:
                    kind = "transport"
                    origin = known[0]
                elif not known and _raw_expr(value, p_names=p_names, p_keys=p_keys) is not None:
                    kind = "raw"
                    origin = None
                elif not known and isinstance(value, ast.Constant) and value.value is None:
                    kind = "none"
                    origin = None
                else:
                    kind = "unknown"
                    origin = None
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
                classified.append((kind, positions, origin))
            if not valid:
                continue
            corrected_positions: set[int] = set()
            raw_positions: set[int] = set()
            for kind, positions, origin in classified:
                if positions is None:
                    valid = False
                    break
                selected = set(positions)
                if kind == "transport" and origin is not None:
                    available = set(origin.corrected_positions) | set(origin.raw_positions)
                    if not selected <= available:
                        valid = False
                        break
                    corrected_positions.update(selected & set(origin.corrected_positions))
                    raw_positions.update(selected & set(origin.raw_positions))
                elif kind == "raw":
                    raw_positions.update(selected)
                elif kind != "none":
                    valid = False
                    break
            if not valid or corrected_positions & raw_positions:
                continue
            if len(classified) == 1:
                kind, positions, _ = classified[0]
                if (
                    kind != "transport"
                    or positions is None
                    or set(positions) != corrected_positions | raw_positions
                    or not corrected_positions
                ):
                    continue
            elif len(classified) == 2:
                if corrected_positions != set(
                    fold.positions
                ) or raw_positions != all_positions - set(fold.positions):
                    continue
            else:
                continue
            result.append(
                _TransportProof(
                    target,
                    tuple(sorted(corrected_positions)),
                    tuple(sorted(raw_positions)),
                )
            )
            changed = True
    return tuple(result)


def _transport_targets(
    tree: ast.Module,
    fold: _Fold,
    *,
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
    outcome_columns: tuple[str, ...],
) -> tuple[tuple[str, object], ...]:
    return tuple(
        item.target
        for item in _transport_proofs(
            tree,
            fold,
            p_names=p_names,
            p_keys=p_keys,
            outcome_columns=outcome_columns,
        )
    )


def _same_expression(left: ast.expr, right: ast.expr) -> bool:
    return ast.dump(left, include_attributes=False) == ast.dump(right, include_attributes=False)


def _threshold_compare_uses_fold(compare: ast.Compare, fold: _Fold) -> bool:
    if fold.target[0] == "threshold-direct":
        return _position(compare) == fold.target[1]
    if fold.target[0] != "threshold-binding" or not isinstance(fold.target[1], str):
        return False
    operands = (compare.left, *compare.comparators)
    return any(
        isinstance(operand, ast.Name)
        and isinstance(operand.ctx, ast.Load)
        and operand.id == fold.target[1]
        for operand in operands
    )


def _conclusion_consumption(
    tree: ast.Module,
    fold: _Fold,
    transports: Sequence[_TransportProof],
    *,
    p_names: frozenset[str],
    p_keys: frozenset[str | int],
    outcome_columns: tuple[str, ...],
) -> _ConclusionConsumption | None:
    """Prove each conclusion's corrected/raw origin before AP classification."""

    parents = _parents(tree)
    owners = _owners(tree)
    sequences = _module_sequences(tree)
    origins: dict[int, set[str]] = {position: set() for position in range(len(outcome_columns))}
    comparison_positions: list[tuple[int, int, int, int]] = []
    for compare in (node for node in ast.walk(tree) if isinstance(node, ast.Compare)):
        left_p = rm._p_derived(compare.left, p_names, p_keys)
        right_p = any(rm._p_derived(item, p_names, p_keys) for item in compare.comparators)
        if not left_p and not right_p:
            continue
        if left_p == right_p or len(compare.ops) != 1 or len(compare.comparators) != 1:
            return None
        positions = _positions_for(
            compare,
            tree=tree,
            owner=owners.get(compare, tree),
            parents=parents,
            sequences=sequences,
            outcome_columns=outcome_columns,
        )
        if positions is None or not positions:
            return None
        p_operand = compare.left if left_p else compare.comparators[0]
        if fold.form == "family-alpha-division":
            kind = "corrected" if _threshold_compare_uses_fold(compare, fold) else "raw"
            for position in positions:
                origins[position].add(kind)
            comparison_positions.append(_position(compare))
            continue

        matching = [item for item in transports if _load_matches(p_operand, item.target)]
        if len(matching) == 1:
            proof = matching[0]
            available = set(proof.corrected_positions) | set(proof.raw_positions)
            if not set(positions) <= available:
                return None
            for position in positions:
                if position in proof.corrected_positions:
                    origins[position].add("corrected")
                if position in proof.raw_positions:
                    origins[position].add("raw")
        elif not matching and _same_expression(p_operand, fold.raw):
            for position in positions:
                origins[position].add("raw")
        else:
            return None
        comparison_positions.append(_position(compare))

    corrected = set(fold.positions)
    family = set(range(len(outcome_columns)))
    if any(
        origins[position] != ({"corrected"} if position in corrected else {"raw"})
        for position in family
    ):
        return None
    return _ConclusionConsumption(
        tuple(sorted(corrected)),
        tuple(sorted(family - corrected)),
        tuple(sorted(comparison_positions)),
    )


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
    """Lower the proved fold to its raw expression, dropping any absorbed cap with it.

    `X = p * F` / `if X > 1.0: X = 1.0` lowers to raw exactly as `X = min(p * F, 1.0)` does.
    Without the drop the surrogate would retain `if X > 1.0: X = 1.0`, whose `1.0` reads as a
    second decision threshold and abstains at `unresolved-decision-threshold`.
    """

    caps = [cap for cap in admitted_caps(tree) if cap.product.value is fold.node]
    if caps:
        stripped = copy.deepcopy(tree)
        guards = {_position(cap.guard) for cap in caps}
        emptied = False
        for block in _statement_blocks(stripped):
            keep = [
                statement
                for statement in block
                if not (isinstance(statement, ast.If) and _position(statement) in guards)
            ]
            if block and not keep:
                emptied = True
                break
            block[:] = keep
        if not emptied:
            tree = stripped
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
        transport_proofs = _transport_proofs(
            tree,
            fold,
            p_names=p_names,
            p_keys=p_keys,
            outcome_columns=outcome_columns,
        )
        transports = tuple(item.target for item in transport_proofs)
        consumption = _conclusion_consumption(
            tree,
            fold,
            transport_proofs,
            p_names=p_names,
            p_keys=p_keys,
            outcome_columns=outcome_columns,
        )
        if consumption is None:
            return CorrectionModelResult(
                baseline,
                baseline,
                False,
                True,
                None,
                (),
                {"gate": "conclusion-consumption", "line": fold.source_line},
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
                "consumption_comparisons": [
                    list(position) for position in consumption.comparison_positions
                ],
                "consumption_corrected_positions": list(consumption.corrected_positions),
                "consumption_raw_positions": list(consumption.raw_positions),
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
    baseline: Any,
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
    "record_collection_alias_unresolved",
    "record_collection_names",
    "record_derived_names",
]
