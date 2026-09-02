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
from collections import Counter
from collections.abc import Callable, Iterator, Mapping, Sequence
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

    def __init__(
        self,
        mappings: frozenset[str],
        *,
        shadowed: frozenset[str] = frozenset(),
        passthrough: Callable[[ast.Call], bool] | None = None,
    ) -> None:
        self.mappings: set[str] = set(mappings)
        self.sequences: dict[str, object] = {}
        self.records: set[str] = set()
        #: Round 6, soundness fix 5: the wrapper names this module binds itself.  A project-local
        #: `def sorted(values)` is not the builtin row wrapper, so recognizing it by spelling read
        #: a new unrelated dictionary as one of the collection's records and lost a true
        #: accusation.  A shadowed spelling falls through to the round-6 return-flow hook, which
        #: resolves the definition and asks whether it actually hands the argument back.
        self.shadowed = shadowed
        #: Round 6, rule B: a call whose callee resolves to a project-local definition that hands
        #: one of its arguments back.  `target = identity(record)` binds the record itself.
        self._passthrough = passthrough
        #: Round 7, rule A(1): the names that hold records ONLY because a record was inserted into
        #: them.  `held = []` followed by `held.append(record)` is a container of the collection's
        #: records, so a later store through one of its elements is a store into the family.  The
        #: set is kept apart from the ordinary bindings because the frozen mutation census reads
        #: every receiver method call as an in-place mutation, and the insertion call *is* one:
        #: counting it against the container would refuse `seen.append(record); seen.index(record)`,
        #: which only reads a family that really was left uncorrected.
        self.inserted: set[str] = set()
        #: The names some ordinary binding form also reached, so a name that is both is never
        #: treated as insertion-only and round 6's disposition for it stands unchanged.
        self.bound: set[str] = set()
        self._from_insertion = False

    # -- expression classifiers ---------------------------------------------------------

    def _hands_back(self, node: ast.Call) -> bool:
        return self._passthrough is not None and self._passthrough(node)

    def _arguments(self, node: ast.Call) -> tuple[ast.expr, ...]:
        return (*node.args, *(keyword.value for keyword in node.keywords))

    def maps_records(self, node: ast.expr) -> bool:
        """True when the expression is a container still keyed or indexed by family member."""

        if isinstance(node, ast.NamedExpr):
            return self.maps_records(node.value)
        if isinstance(node, ast.Name):
            return node.id in self.mappings
        if isinstance(node, ast.Dict):
            # Round 7, rule A(1): a dictionary display written around a record is a container
            # keyed by whatever key stands beside it, so `.values()` and `[k]` reach the record.
            return any(item is not None and self.is_record(item) for item in node.values)
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in _SHALLOW_COPY_METHODS
                and not node.args
            ):
                return self.maps_records(node.func.value)
            if (
                isinstance(node.func, ast.Name)
                and node.func.id in _MAPPING_WRAPPERS
                and node.func.id not in self.shadowed
            ):
                return any(self.maps_records(argument) for argument in node.args)
            if self._hands_back(node):
                return any(self.maps_records(argument) for argument in self._arguments(node))
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
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            # Round 6: a display written around a record hands that record on.  The bare-Name
            # spelling is already a display escape; `[results[name]]` is the same container one
            # subscript away, and the round-6 probe hands exactly that to a storing helper.
            return _RECORD if any(self.is_record(item) for item in node.elts) else _OPAQUE
        return _OPAQUE

    def _call_element_shape(self, node: ast.Call) -> object:
        function = node.func
        if isinstance(function, ast.Attribute):
            if not self.maps_records(function.value):
                return (
                    _RECORD if self._hands_back(node) and self._argument_record(node) else _OPAQUE
                )
            if function.attr in _KEY_VIEW_METHODS:
                return _OPAQUE
            if function.attr in _RECORD_VIEW_METHODS:
                return (_OPAQUE, _RECORD) if function.attr == "items" else _RECORD
            return _OPAQUE
        if not isinstance(function, ast.Name):
            return _OPAQUE
        if function.id not in self.shadowed:
            if function.id == "enumerate" and node.args:
                return (_OPAQUE, self.element_shape(node.args[0]))
            if function.id == "zip":
                return tuple(self.element_shape(argument) for argument in node.args)
            if function.id in _ITERABLE_WRAPPERS and node.args:
                return self.element_shape(node.args[0])
        if self._hands_back(node):
            for argument in self._arguments(node):
                shape = self.element_shape(argument)
                if self._carries_record(shape):
                    return shape
            if self._argument_record(node):
                return _RECORD
        # `dict(X)` is a mapping, so iterating it yields keys.  Its records are reached through
        # `.items()`, `.values()`, or a subscript, each of which reads `maps_records` instead.
        return _OPAQUE

    def _argument_record(self, node: ast.Call) -> bool:
        return any(self.is_record(argument) for argument in self._arguments(node))

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
                and function.id not in self.shadowed
                and node.args
                and self.element_shape(node.args[0]) is _RECORD
            ):
                return True
            if self._hands_back(node) and self._argument_record(node):
                return True
            if isinstance(function, ast.Call) and self.is_record(function):
                # Round 7, rule A(2): `getter(record)()` calls a closure the helper returned over
                # the record, and what it hands back is the record.  Calling a callable that
                # already carries the record yields the record, so the store the caller then
                # writes is a store into the family.
                return True
        return False

    # -- binding ------------------------------------------------------------------------

    def _carries_record(self, shape: object) -> bool:
        if shape is _RECORD:
            return True
        return isinstance(shape, tuple) and any(self._carries_record(item) for item in shape)

    def _note(self, name: str) -> None:
        """Record which half of the enumeration reached a name, for the round-7 insertion set."""

        (self.inserted if self._from_insertion else self.bound).add(name)

    def _add(self, group: set[str], name: str) -> bool:
        self._note(name)
        if name in group:
            return False
        group.add(name)
        return True

    def _set_sequence(self, name: str, shape: object) -> bool:
        self._note(name)
        if self.sequences.get(name) == shape:
            return False
        self.sequences[name] = shape
        return True

    def _bind_target(self, target: ast.expr, shape: object) -> bool:
        """Distribute an element shape over a loop target or an unpacking assignment target."""

        if isinstance(target, ast.Name):
            if shape is _RECORD:
                return self._add(self.records, target.id)
            if isinstance(shape, tuple) and self._carries_record(shape):
                return self._set_sequence(target.id, shape)
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
            if self._carries_record(shape):
                changed = self._set_sequence(target.id, shape) or changed
            # A bare `A = B` binds one object to two names, so the record role is undirected
            # exactly as the round-3 alias edge is.
            if isinstance(value, ast.Name) and target.id in self.records:
                changed = self._add(self.records, value.id) or changed
        elif isinstance(value, ast.Name) and value.id in self.sequences:
            changed = self._bind_target(target, self.sequences[value.id]) or changed
        return changed

    def _bind_insertion(self, node: ast.AST) -> bool:
        """Rule A(1): a record inserted into a container makes that container hold records.

        `held = []` followed by `held.append(record)` is a list of the collection's own record
        objects, because `append` and `extend` preserve identity; the audit reproduced a complete
        Bonferroni pass written as `for target in held: operator.setitem(target, "p", ...)` that
        round 6 published as an accusation because the insertion dropped the record's role.  A
        dictionary filled by `registry[name] = record` is the same container written by subscript.
        """

        changed = False
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            function = node.func
            if not isinstance(function.value, ast.Name):
                return False
            container = function.value.id
            if function.attr not in _ROLE_PROPAGATING_INSERTIONS:
                return False
            for argument in node.args:
                if function.attr in {"extend", "update"}:
                    shape = self.element_shape(argument)
                    if self._carries_record(shape):
                        changed = self._set_sequence(container, shape) or changed
                    if function.attr == "update" and self.maps_records(argument):
                        changed = self._add(self.mappings, container) or changed
                elif self.is_record(argument):
                    changed = self._set_sequence(container, _RECORD) or changed
            return changed
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if value is None or not self.is_record(value):
                return False
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                    changed = self._add(self.mappings, target.value.id) or changed
        return changed

    def resolve(self, tree: ast.Module) -> None:
        """Grow the three role sets to a fixpoint over the whole module."""

        changed = True
        while changed:
            changed = False
            for node in ast.walk(tree):
                self._from_insertion = False
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
                self._from_insertion = True
                changed = self._bind_insertion(node) or changed
                self._from_insertion = False

    def names(self) -> frozenset[str]:
        return frozenset(self.mappings | set(self.sequences) | self.records)

    def insertion_only(self) -> frozenset[str]:
        """The names rule A(1) reached and no other binding form did."""

        return frozenset(self.inserted - self.bound)


def record_derived_roles(
    tree: ast.Module,
    collection_aliases: frozenset[str],
    census: _HelperStores | None = None,
) -> tuple[frozenset[str], frozenset[str]]:
    """The record-derived names, and the subset rule A(1) reached only by an insertion."""

    census = _HelperStores(tree) if census is None else census
    derivation = _RecordDerivation(
        collection_aliases,
        shadowed=census.shadowed_wrappers,
        passthrough=census.hands_back_an_argument,
    )
    derivation.resolve(tree)
    return derivation.names(), derivation.insertion_only()


def record_derived_names(
    tree: ast.Module,
    collection_aliases: frozenset[str],
    census: _HelperStores | None = None,
) -> frozenset[str]:
    """Every name that reaches a record of the given collection, or a container of them.

    `collection_aliases` is the round-3 alias component of one record collection: the collection
    name and every other bare name for the same object.  The result is that component closed
    under the enumerated record-derived binding forms, including their chains -- an alias of an
    alias, a loop over a list built from a view of a copy, a record rebound to a third name.

    Round 7, rule A(1), adds the insertion forms: `held.append(record)`, `held.extend(view)`, and
    `registry[name] = record` all put the collection's own record objects into another container,
    and a store written through an element of that container is a store into the family.
    """

    return record_derived_roles(tree, collection_aliases, census)[0]


def _insertion_container_is_only_filled_and_read(tree: ast.Module, name: str) -> bool:
    """True when every in-place form reaching an insertion container is a fill or a read.

    The frozen mutation census reads any receiver method call as an in-place mutation, so the very
    `held.append(record)` that puts the records there would refuse the container that holds them.
    That is not a refusal round 6 made, and making it would lose the accusation
    `seen.append(record); seen.index(record)` earns over an uncorrected family.  A fill is an
    allowlisted insertion or query method call on the name, or a one-level subscript store into
    it; anything else -- an augmented assignment, a `del`, a nested subscript store such as
    `held[0]["p"] = ...`, or any other method call -- is a mutation and refuses as before.
    """

    for node in ast.walk(tree):
        if isinstance(node, ast.AugAssign):
            if rm._root_name(node.target) == name:
                return False
        elif isinstance(node, ast.Delete):
            if any(rm._root_name(target) == name for target in node.targets):
                return False
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if not isinstance(target, ast.Subscript) or rm._root_name(target) != name:
                    continue
                if not isinstance(target.value, ast.Name):
                    return False
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == name
            and node.func.attr not in (_ROLE_PROPAGATING_INSERTIONS | _READ_ONLY_CONTAINER_QUERIES)
        ):
            return False
    return True


#: Round 5: the builtins that hand each element of the iterables beside them to a callable.
#: `map(f, X)` and `filter(f, X)` apply `f` to the elements of `X`, so an `f` that stores through
#: its first parameter is a store into the records `X` yields.
_ELEMENT_CALLBACK_BUILTINS = frozenset({"map", "filter"})
#: The builtins that apply a `key=` callable to each element of their first argument.
_KEY_CALLBACK_BUILTINS = frozenset({"sorted", "min", "max"})

#: Round 7, rule B: how many times the role enumeration and the call census are allowed to feed
#: each other before the answer is taken as final.  Roles only grow, so the loop converges on its
#: own; the bound is here so a pathological module cannot make it run long.
_RETURN_FLOW_PASSES = 4

#: The edge parameter that means "any parameter of the callee".  A starred argument forwards an
#: unknown position, so it is bound to every parameter at once and is captured when any of them
#: stores.
_ANY_PARAMETER = "*"

#: Round 6: the three roles a tracked argument can carry into a callee parameter.  Round 5 seeded
#: every parameter as a mapping *and* a sequence of records at once, which made a bare
#: `for key in table` inside a helper yield records where the identical module-level loop yields
#: keys, and lost the true accusation the module-level boundary preserves.  A parameter is seeded
#: with the role of the argument that binds it and with nothing else.
_ROLE_MAPPING = "mapping"
_ROLE_SEQUENCE = "sequence"
_ROLE_RECORD = "record"

#: Round 6, rule A: the read-only builtins a tracked argument may reach.  Every entry is measured:
#: the census over the 245 prototype fixtures, the E10-E17 envelope cases, the open-corpus rows,
#: and the round-1..round-5 oracle sources reports exactly these builtin callees receiving a
#: tracked root -- `len` (45 rows, E10:N3, E10:N4, E10:P1), `zip` (22, E10:N3, E10:P5, E12:N4,
#: E12:P5), `list` (6, r4 list/reversed/subscript rows), `sorted` (6, E12:N7, E13:N7, E14:N7),
#: `enumerate` (5, E12:N4, r4 enumerate rows), `set` (5, E13:N7, E14:N7, E17:N7), `min` (4,
#: E14:N7, E15:N7, E17:N7), `max` (3, the same three), `iter` (2, r4 iter rows), `dict` (1, r4
#: dict-copy row), `float` (1, E13:N7), `next` (1, r4 next/iter row), `print` (1, r5 builtin
#: control), `reversed` (1, r4 reversed row), `sum` (1, E13:N7), `tuple` (1, r4 tuple row) --
#: plus their obvious read-only siblings.  Refusing on any of them loses those rows' accusations,
#: which is what mutation kill (c) records.
_READ_ONLY_BUILTIN_CALLEES = frozenset(
    {
        "abs",
        "all",
        "any",
        "bool",
        "dict",
        "enumerate",
        "float",
        "format",
        "frozenset",
        "hash",
        "id",
        "int",
        "isinstance",
        "iter",
        "len",
        "list",
        "next",
        "print",
        "repr",
        "reversed",
        "round",
        "set",
        "str",
        "sum",
        "tuple",
        "type",
        "zip",
    }
)

#: The builtins that are read-only on their iterable only while the callable beside them is.
#: `sorted(results.values(), key=lambda row: row["p"])` is a measured read-only control; the same
#: call with a storing callable is a store into every record it visits, which rule C decides.
_CALLBACK_BEARING_BUILTINS = _ELEMENT_CALLBACK_BUILTINS | _KEY_CALLBACK_BUILTINS

#: Never allowlisted, whatever else is: each one either hands out a bound mutator, evaluates
#: project text this recognizer cannot read, or writes through an attribute path.
_NEVER_READ_ONLY_CALLEES = frozenset(
    {
        "apply",
        "delattr",
        "eval",
        "exec",
        "getattr",
        "globals",
        "locals",
        "setattr",
        "vars",
    }
)

#: The bare imported library names a tracked argument may reach.  `multipletests` is measured on
#: 14 rows (E10:N4, E11:N4, E13:P5, E14:N1); `mean` and `stdev` are measured on 8 rows each
#: (E10:P1).  The remaining entries are this module's own closed `_CORRECTION_TERMINALS` plus the
#: statistics reducers, all of which return a new sequence or a scalar and none of which can
#: write into the family it is handed.
_READ_ONLY_IMPORTED_CALLEES = frozenset(
    {
        "fdrcorrection",
        "fmean",
        "mean",
        "median",
        "pstdev",
        "pvariance",
        "stdev",
        "variance",
        *_CORRECTION_TERMINALS,
    }
)

#: Round 7, rule C: the import identities the allowlist is keyed on, as
#: `dotted module path -> the canonical receiver token used below`.  Round 6 keyed the qualified
#: allowlist on the *spelling* of the receiver, so a project that wrote `json = Mutator` beside a
#: storing `Mutator.dumps` staticmethod had its complete Bonferroni pass published as an
#: accusation, and a project that wrote `import json as payload` lost the accusation its
#: uncorrected family had earned.  A base name is a library name only when the scope chain binds
#: it exclusively by `import` statements, and the identity is what those statements say it is:
#: `import pandas as pd` and `import pandas` are both `pandas`, `from scipy import stats` and
#: `import scipy.stats as stats` are both `scipy.stats`.  A dotted path with no entry here is not
#: allowlisted, so widening the recognizer to a new library is an explicit edit of this table.
_READ_ONLY_MODULE_IDENTITIES: Mapping[str, str] = {
    "copy": "copy",
    "csv": "csv",
    "functools": "functools",
    "json": "json",
    "logging": "logging",
    "math": "math",
    "pandas": "pandas",
    "pingouin": "pg",
    "pprint": "pprint",
    "scipy.stats": "stats",
    "statistics": "statistics",
    "warnings": "warnings",
}

#: The module-qualified library APIs a tracked argument may reach, as
#: `(canonical receiver, attribute)` after the import resolution above.
#: `statistics.mean` and `statistics.stdev` are measured on E17:N7, `stats.ttest_ind` on E10:P1
#: (4 rows), `pg.multicomp` on E10:N3 and E14:N3, and `pandas.DataFrame` on E14:N3.  The siblings
#: are the read-only reporting and hypothesis-test APIs of the same four modules.
#:
#: Round 7 adds five measured Direction-2 targets, each justified by one named round-7 oracle row
#: that loses a true accusation without it: `copy.copy`/`copy.deepcopy`
#: (`positive-copy-deepcopy-of-the-collection`), `pprint.pprint`/`pprint.pformat`
#: (`positive-pprint-of-the-collection`), `json.load`/`json.loads` as the read siblings of the
#: already-measured `json.dump`/`json.dumps`, and the `csv` writer constructors
#: (`positive-csv-dictwriter-writerow`).  The `math` reducers are the scalar-returning siblings of
#: the already-measured `statistics` reducers and are admitted on the same ground: each returns a
#: new number and none of them can write into the family it reads.
_READ_ONLY_MODULE_APIS = frozenset(
    {
        ("copy", "copy"),
        ("copy", "deepcopy"),
        ("csv", "DictWriter"),
        ("csv", "writer"),
        ("json", "dump"),
        ("json", "dumps"),
        ("json", "load"),
        ("json", "loads"),
        ("logging", "critical"),
        ("logging", "debug"),
        ("logging", "error"),
        ("logging", "exception"),
        ("logging", "info"),
        ("logging", "log"),
        ("logging", "warning"),
        ("math", "ceil"),
        ("math", "exp"),
        ("math", "fabs"),
        ("math", "floor"),
        ("math", "fsum"),
        ("math", "isclose"),
        ("math", "isinf"),
        ("math", "isnan"),
        ("math", "log"),
        ("math", "log10"),
        ("math", "log2"),
        ("math", "prod"),
        ("math", "sqrt"),
        ("pandas", "DataFrame"),
        ("pandas", "Series"),
        ("pg", "multicomp"),
        ("pprint", "pformat"),
        ("pprint", "pprint"),
        ("statistics", "fmean"),
        ("statistics", "mean"),
        ("statistics", "median"),
        ("statistics", "pstdev"),
        ("statistics", "pvariance"),
        ("statistics", "stdev"),
        ("statistics", "variance"),
        ("stats", "chi2_contingency"),
        ("stats", "f_oneway"),
        ("stats", "false_discovery_control"),
        ("stats", "kruskal"),
        ("stats", "mannwhitneyu"),
        ("stats", "pearsonr"),
        ("stats", "spearmanr"),
        ("stats", "ttest_ind"),
        ("stats", "ttest_rel"),
        ("stats", "wilcoxon"),
        ("warnings", "warn"),
    }
)

#: The `csv` writer constructors, and the writer methods that consume one record per call without
#: writing into it.  Measured: `positive-csv-dictwriter-writerow`, where a family that really was
#: left uncorrected is only serialized.  The receiver has to be a name bound exactly once to one
#: of these constructors, so a writer name rebound to a project-local class is not one of these.
_CSV_WRITER_CONSTRUCTORS = frozenset({("csv", "DictWriter"), ("csv", "writer")})
_CSV_WRITER_METHODS = frozenset({"writeheader", "writerow", "writerows"})

#: The library constructors that re-wrap what they are handed without copying the objects inside,
#: so an argument's roots reach through them.  `pd.Series(list(results.values())).apply(rescale)`
#: is the measured route: the receiver of `.apply` is the collection's records.  This set is read
#: by spelling and deliberately stays that way: it only ever *widens* the roots an argument hands
#: over, so reading an unrelated `pd` as pandas errs toward refusal, which is the safe direction.
_READ_ONLY_CONTAINER_CONSTRUCTORS = frozenset(
    {("pd", "DataFrame"), ("pd", "Series"), ("pandas", "DataFrame"), ("pandas", "Series")}
)

#: The container-insertion methods that store their argument somewhere else without writing into
#: it.  Measured: `secondary_results.append(result)` on E13:P5, whose `candidate`/`strict_subset`
#: accusation over positions (0, 1) of 7 is lost if the call is read as a write into `result`.
#: Round 7 keeps them read-only *and* propagates the inserted object's role into the container,
#: because `held.append(record)` followed by a store through an element of `held` is a store into
#: the family: rule A(1).  `update` is deliberately absent: `dict.update(record, p=...)` is the
#: measured round-6 unbound-mutation route, and admitting the spelling would readmit it.  Rule
#: A(1) still propagates a role through `update`, because propagation only adds refusals.
_READ_ONLY_CONTAINER_INSERTIONS = frozenset({"add", "append", "extend", "insert"})

#: The insertion forms rule A(1) propagates a role through.  `update` is here and not above for
#: the reason stated above: propagating a role is a narrowing, admitting the callee is not.
_ROLE_PROPAGATING_INSERTIONS = _READ_ONLY_CONTAINER_INSERTIONS | {"update"}

#: Round 7, rule C: the container query methods that read a container without writing into it or
#: into what they are handed.  Measured: `positive-seen-index-and-count`, where the record is
#: appended to a scratch list and then located in it, and the family is never corrected.  They are
#: admitted only on a receiver the role enumeration already tracks, so an unrelated object with a
#: storing method of the same spelling is not one of these.
_READ_ONLY_CONTAINER_QUERIES = frozenset({"count", "get", "index"})

#: The methods that apply a callable to each element of their receiver.  Read-only exactly while
#: the callable is, which is rule C.
_ELEMENT_CALLBACK_METHODS = frozenset({"apply", "applymap", "map", "transform"})

#: Round 7, rule B: the bound methods that may stand in a callable position.  `sorted(results,
#: key=results.get)` is a measured read-only control, so a bound method of a tracked container is
#: admitted there; `pop` and `setdefault` are absent because they write into their receiver.
_READ_ONLY_BOUND_CALLABLES = (
    _RECORD_VIEW_METHODS | _KEY_VIEW_METHODS | _SHALLOW_COPY_METHODS | _READ_ONLY_CONTAINER_QUERIES
)

#: Decorators that describe how a method binds rather than wrapping what it does.
_STRUCTURAL_DECORATORS = frozenset({"abstractmethod", "classmethod", "property", "staticmethod"})

#: Round 7, rule D(3): the decorator that copies a wrapped function's metadata onto a wrapper and
#: changes nothing about what the wrapper does with its arguments.  It is admitted on the nested
#: wrapper of a forwarding decorator and nowhere else.
_METADATA_DECORATORS = frozenset({("functools", "wraps")})


def _module_api(function: ast.Attribute) -> tuple[str, str] | None:
    """`(receiver name, attribute)` for `pd.DataFrame(...)`-shaped callees, else `None`."""

    if isinstance(function.value, ast.Name):
        return (function.value.id, function.attr)
    return None


def _import_identity(statement: ast.AST, name: str) -> str | None:
    """What one import statement binds `name` to, as a dotted path.

    `import json` and `import json as payload` both bind `json`.  `import os.path` binds the
    package `os` under the bare name `os`.  `from scipy import stats` binds `scipy.stats`, and
    `from json import dumps as serialize` binds `json.dumps`.  A relative import has no absolute
    identity this module can read, so it resolves to nothing and rule A fails closed on it.
    """

    if isinstance(statement, ast.Import):
        for alias in statement.names:
            if (alias.asname or alias.name).split(".")[0] != name:
                continue
            return alias.name if alias.asname else alias.name.split(".")[0]
        return None
    if isinstance(statement, ast.ImportFrom):
        if statement.level or statement.module is None:
            return None
        for alias in statement.names:
            if (alias.asname or alias.name).split(".")[0] != name:
                continue
            return f"{statement.module}.{alias.name}"
    return None


def _string_receiver(node: ast.expr) -> bool:
    """True for `"...".format(...)`-shaped receivers, the measured 470-row str-method route."""

    if isinstance(node, ast.JoinedStr):
        return True
    return isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes))


def _module_bound_names(tree: ast.Module) -> frozenset[str]:
    """Every name this module binds anywhere, in any scope and by any binding form."""

    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.arg):
            bound.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            bound.add(node.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            bound.update(node.names)
    return frozenset(bound)


#: Round 7, rule A(3): of the wrappers `_capture_roots` already reads through, the ones that hand
#: back what iterating their argument yields.  Over a MAPPING-role name they yield its keys, and a
#: key is not a record -- the same boundary the module-level bare-iteration rule draws.  `dict` and
#: `next` are absent: `dict(X)` is a shallow copy that still holds the records, and `next(X)` is
#: not an iteration of a mapping.  The set the roots propagate through is unchanged from round 6,
#: so this constant can only ever narrow a root away, never add one.
_KEY_YIELDING_WRAPPERS = _ITERABLE_WRAPPERS | {"enumerate", "zip"}


def _comprehension_targets(generators: Sequence[ast.comprehension]) -> frozenset[str]:
    """The names a comprehension's own generators bind."""

    bound: set[str] = set()
    for generator in generators:
        for node in ast.walk(generator.target):
            if isinstance(node, ast.Name):
                bound.add(node.id)
    return frozenset(bound)


def _capture_roots(
    node: ast.expr,
    records: frozenset[str] = frozenset(),
    mappings: frozenset[str] = frozenset(),
) -> frozenset[str]:
    """The names an argument expression hands the callee an object *of*.

    `rescale(record, len(OUTCOMES))` hands `rescale` the object `record` names, so a store
    through the parameter it binds is a store through `record`.  `rescale(results.values(), n)`
    and `rescale(results[name], n)` hand it the collection's records, so the root is `results`.
    `rescale(record["p"] * len(OUTCOMES), n)` hands it a float, so it has no root at all: the
    enumeration is the round-4 record-derived forms read backwards, not every name that appears
    in the argument.  The keys view is excluded for the reason round 4 excludes it -- a key is
    not a record -- and every other call form is a value the callee cannot store into.

    Round 6, soundness fix 3, supplies `records`: the names the round-4 enumeration says hold one
    record object rather than a container of them.  A subscript of a *record* is a scalar and a
    lookup method on one returns a scalar, so `inspect_float(record["p"])` hands over a float and
    has no root, while `rescale(results[name], n)` still hands over a record of `results`.
    Reading every subscript back to its container root regardless of role is what made a
    read-only float helper look like a handover of the record and lost a true accusation.

    Round 6 also reads a list, tuple, set, or dict display back to the objects it holds.  A bare
    Name inside a display is already a display escape; `rescale_all([results[name]], n)` is the
    same container one subscript away, and it is a measured false-accusation route.

    Round 7, rule A(2), adds the two lazy displays round 6 missed.  A generator expression, a
    comprehension, and a `lambda` are objects that hand out whatever their body names, so
    `def stream(entry): return (entry for _ in range(1))` and `def getter(entry): return lambda:
    entry` both hand the record straight back, and reading them as fresh published two complete
    Bonferroni passes as accusations.  A comprehension target that appears in the element
    expression carries the roots of the iterable it was drawn from, so `(e for e in entry)` is not
    fresh either, while `[row["p"] for row in results.values()]` still is: its element is a scalar.

    Round 7, rule A(3), supplies `mappings`: the names that hold a container still keyed by family
    member.  Iterating one of those yields its KEYS, exactly as the module-level bare-iteration
    boundary says, so `{"names": list(table)}` over a mapping parameter is a fresh dictionary of
    strings and storing into it cannot touch the family.  The same wrapper over a SEQUENCE-role
    name yields the records and keeps its root.
    """

    if isinstance(node, ast.Starred):
        return _capture_roots(node.value, records, mappings)
    if isinstance(node, ast.NamedExpr):
        target = node.target
        walrus = frozenset({target.id}) if isinstance(target, ast.Name) else frozenset[str]()
        return _capture_roots(node.value, records, mappings) | walrus
    if isinstance(node, ast.Name):
        return frozenset({node.id})
    if isinstance(node, ast.Subscript):
        if isinstance(node.value, ast.Name) and node.value.id in records:
            return frozenset()
        return _capture_roots(node.value, records, mappings)
    if isinstance(node, ast.Attribute):
        return _capture_roots(node.value, records, mappings)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        held: set[str] = set()
        for item in node.elts:
            held |= _capture_roots(item, records, mappings)
        return frozenset(held)
    if isinstance(node, ast.Dict):
        held = set()
        for item in node.values:
            if item is not None:
                held |= _capture_roots(item, records, mappings)
        return frozenset(held)
    if isinstance(node, ast.Lambda):
        return _capture_roots(node.body, records, mappings) - _all_parameters(node)
    if isinstance(node, (ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)):
        if isinstance(node, ast.DictComp):
            produced = _capture_roots(node.key, records, mappings) | _capture_roots(
                node.value, records, mappings
            )
        else:
            produced = _capture_roots(node.elt, records, mappings)
        bound = _comprehension_targets(node.generators)
        drawn: set[str] = set()
        for generator in node.generators:
            if _comprehension_targets([generator]) & produced:
                drawn |= _capture_roots(generator.iter, records, mappings)
        return (produced - bound) | frozenset(drawn)
    if isinstance(node, ast.Call):
        function = node.func
        if isinstance(function, ast.Attribute):
            if function.attr in _RECORD_VIEW_METHODS | _SHALLOW_COPY_METHODS:
                return _capture_roots(function.value, records, mappings)
            if function.attr in _RECORD_LOOKUP_METHODS:
                if isinstance(function.value, ast.Name) and function.value.id in records:
                    return frozenset()
                return _capture_roots(function.value, records, mappings)
            if _module_api(function) in _READ_ONLY_CONTAINER_CONSTRUCTORS:
                roots: set[str] = set()
                for argument in node.args:
                    roots |= _capture_roots(argument, records, mappings)
                return frozenset(roots)
            return frozenset()
        if isinstance(function, ast.Name) and function.id in (
            _ITERABLE_WRAPPERS | _MAPPING_WRAPPERS | {"enumerate", "zip", "next"}
        ):
            keys_only = function.id in _KEY_YIELDING_WRAPPERS
            roots = set()
            for argument in node.args:
                if (
                    keys_only
                    and isinstance(argument, ast.Name)
                    and argument.id in mappings
                    and argument.id not in records
                ):
                    continue
                roots |= _capture_roots(argument, records, mappings)
            return frozenset(roots)
    return frozenset()


def _parameter_slots(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda,
) -> tuple[tuple[str, ...], str | None, frozenset[str], str | None]:
    """The positional slots, the `*args` bucket, the keyword-bindable names, and `**kwargs`."""

    arguments = node.args
    positional = tuple(argument.arg for argument in (*arguments.posonlyargs, *arguments.args))
    keyword_bindable = frozenset(
        argument.arg for argument in (*arguments.args, *arguments.kwonlyargs)
    )
    vararg = arguments.vararg.arg if arguments.vararg is not None else None
    kwarg = arguments.kwarg.arg if arguments.kwarg is not None else None
    return positional, vararg, keyword_bindable, kwarg


def _all_parameters(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda) -> frozenset[str]:
    positional, vararg, keyword_bindable, kwarg = _parameter_slots(node)
    names = set(positional) | set(keyword_bindable)
    if vararg is not None:
        names.add(vararg)
    if kwarg is not None:
        names.add(kwarg)
    return frozenset(names)


def _nested_definitions(body: Sequence[ast.stmt]) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """The `def`s written directly inside one body, at any statement depth below it."""

    found: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for statement in body:
        for node in ast.walk(statement):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found.append(node)
    return found


def _own_scope_nodes(body: Sequence[ast.stmt]) -> Iterator[ast.AST]:
    """Every node of one body that belongs to that body's own scope.

    A nested `def`, `async def`, or `lambda` opens its own scope, so its `return` belongs to it and
    not to the body around it.  Round 7's forwarding-decorator proof needs exactly that split: the
    decorator's own returns say what the decorator hands back, and the wrapper's returns do not.
    """

    frontier: list[ast.AST] = list(body)
    while frontier:
        node = frontier.pop()
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        frontier.extend(ast.iter_child_nodes(node))


def _name_is_read(body: Sequence[ast.stmt], name: str) -> bool:
    """True when the body reads `name` anywhere: calls it, returns it, passes it, stores it."""

    for statement in body:
        for node in ast.walk(statement):
            if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Load):
                return True
    return False


class _DeadDefinitionPruner(ast.NodeTransformer):
    """Replace the listed definition subtrees with `pass`, at any depth of one callee body."""

    def __init__(self, dead: frozenset[int]) -> None:
        self._dead = dead

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        if id(node) in self._dead:
            return ast.copy_location(ast.Pass(), node)
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        if id(node) in self._dead:
            return ast.copy_location(ast.Pass(), node)
        return self.generic_visit(node)


def _callee_body(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda) -> ast.Module:
    """The callee's body as a module, so the round-3 and round-4 closures read it unchanged.

    Round 6, rule D: a `def` written inside the body and never read there is dead code and its
    stores are not stores the call performs.  `def inspect_record(entry): def never_called():
    entry["p"] = 1.0; return entry["p"]` only reads the record, and reading the nested body as
    part of the helper lost that true accusation.  A nested definition whose name is read
    anywhere in the body -- called, returned, passed, stored -- is kept, because any of those
    hands the store to the caller.  A `lambda` is an expression and is always kept.
    """

    if isinstance(node, ast.Lambda):
        return ast.Module(body=[ast.Expr(value=node.body)], type_ignores=[])
    body = copy.deepcopy(list(node.body))
    dead = frozenset(
        id(nested) for nested in _nested_definitions(body) if not _name_is_read(body, nested.name)
    )
    if dead:
        pruner = _DeadDefinitionPruner(dead)
        body = [cast("ast.stmt", pruner.visit(statement)) for statement in body]
    return ast.Module(body=body, type_ignores=[])


@dataclass(frozen=True)
class _CaptureEdge:
    """One call argument, the parameter it binds, the names it hands over, and its role.

    A `callee` of `None` is round 6's fail-closed edge: the call site hands a tracked object to a
    callee this module cannot resolve and that is not on the read-only allowlist, so it is a
    mutation with no body to read.
    """

    owner: int
    callee: int | None
    parameter: str
    roots: frozenset[str]
    role: str | None = None


class _ScopeCensus:
    """Which definition a callee name resolves to, decided per scope chain.

    Round 5 gathered every parameter name and every `Name` store in the module and refused to
    resolve any function sharing a spelling with one of them.  That is not what Python does, and
    it was a measured false-accusation route: `def unrelated(rescale): return rescale` beside a
    module-level `def rescale` left the correcting definition unresolvable, so the complete
    Bonferroni pass it performed stayed invisible and the row was published as an accusation.
    An unrelated parameter in another function does not shadow a module-level definition, and
    neither does a class attribute of the same name.

    The census is therefore per scope: each function and lambda owns the names its own body
    binds, a class body owns its own attributes and is never on a function's scope chain, and the
    module owns the rest.  A callee resolves when the innermost scope on the chain that binds the
    name binds it exactly once and binds it as a definition -- a `def`, an `async def`, a `class`,
    or one `lambda` assignment.  Anything else is unresolvable and, under rule A, fails closed:
    two conditional definitions, an import followed by a definition, a name bound to
    `functools.partial(...)` or to a bound method or to a dictionary entry, and a subscript or
    attribute callee.
    """

    _DEFINITION_KINDS = frozenset({"def", "class", "lambda"})

    def __init__(self, tree: ast.Module) -> None:
        self.parents = _parents(tree)
        #: scope id (0 for the module) -> name -> the binding kinds that scope carries
        self.bindings: dict[int, dict[str, list[tuple[str, ast.AST]]]] = {}
        self.scope_of: dict[int, int] = {}
        #: Round 7, semantics fix D(1): the class bodies.  A class namespace is not an enclosing
        #: lexical scope in Python, so it is collected as its own scope and then kept off every
        #: other scope's chain.
        self.class_scopes: set[int] = set()
        self._collect_scope(tree, 0)

    # -- scope collection ---------------------------------------------------------------

    def _collect_scope(self, scope: ast.AST, scope_id: int) -> None:
        table: dict[str, list[tuple[str, ast.AST]]] = {}
        self.bindings[scope_id] = table
        children: list[tuple[ast.AST, int]] = []

        def bind(name: str, kind: str, node: ast.AST) -> None:
            table.setdefault(name, []).append((kind, node))

        if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            for argument in ast.walk(scope.args):
                if isinstance(argument, ast.arg):
                    bind(argument.arg, "param", argument)
            body: list[ast.AST] = (
                [scope.body] if isinstance(scope, ast.Lambda) else list(scope.body)
            )
        else:
            body = list(cast("ast.Module", scope).body)

        def walk(node: ast.AST) -> None:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                bind(node.name, "def", node)
                children.append((node, id(node)))
                return
            if isinstance(node, ast.ClassDef):
                bind(node.name, "class", node)
                children.append((node, id(node)))
                self.class_scopes.add(id(node))
                return
            if isinstance(node, ast.Lambda):
                children.append((node, id(node)))
                return
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    bind((alias.asname or alias.name).split(".")[0], "import", node)
                return
            if isinstance(node, ast.Global):
                for name in node.names:
                    bind(name, "global", node)
                return
            if isinstance(node, ast.Nonlocal):
                for name in node.names:
                    bind(name, "nonlocal", node)
                return
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target, value = node.targets[0], node.value
                if isinstance(target, ast.Name) and isinstance(value, ast.Lambda):
                    bind(target.id, "lambda", value)
                    children.append((value, id(value)))
                    for child in ast.iter_child_nodes(node):
                        if child is not target and child is not value:
                            walk(child)
                    return
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                bind(node.id, "store", node)
            for child in ast.iter_child_nodes(node):
                walk(child)

        for statement in body:
            walk(statement)
        for child_scope, child_id in children:
            self.scope_of[child_id] = scope_id
            self._collect_scope(child_scope, child_id)

    # -- resolution ---------------------------------------------------------------------

    def scope_chain(self, scope_id: int) -> Iterator[int]:
        """The lexical chain a bare name is looked up through, starting at `scope_id`.

        Round 7, semantics fix D(1): a class body is not an enclosing scope.  A bare `inspect`
        written inside `Report.show` is the module-level `inspect`, never `Report.inspect`, which
        is reached only through `self.`, `cls.`, or `Report.`.  Round 6 walked method -> class ->
        module and resolved the bare name to the storing class method, so a read-only helper
        standing beside a same-named method lost the accusation its uncorrected family had earned.
        The starting scope is always yielded: a name written directly in a class body really does
        resolve in that class namespace.
        """

        current: int | None = scope_id
        first = True
        while current is not None:
            if first or current not in self.class_scopes:
                yield current
            first = False
            if current == 0:
                return
            current = self.scope_of.get(current)
        return

    def resolve(self, name: str, scope_id: int) -> tuple[str, ast.AST] | None:
        """The definition `name` denotes at a call site in `scope_id`, or `None`.

        Round 7, semantics fix D(2): a `global name` or `nonlocal name` declaration rebinds the
        lookup to the declared scope, so the declaring function's own table is not the answer.  A
        declaration that is accompanied anywhere by a store of the same name leaves the target
        scope's binding ambiguous, and rule A fails closed on it.
        """

        for scope in self.scope_chain(scope_id):
            entries = self.bindings.get(scope, {}).get(name)
            if entries is None:
                continue
            kinds = {kind for kind, _node in entries}
            if kinds & {"global", "nonlocal"}:
                return self._resolve_declared(name, scope, entries)
            if len(entries) != 1:
                return None
            kind, node = entries[0]
            return (kind, node) if kind in self._DEFINITION_KINDS else None
        return None

    def _resolve_declared(
        self, name: str, scope: int, entries: Sequence[tuple[str, ast.AST]]
    ) -> tuple[str, ast.AST] | None:
        """Continue a `global`/`nonlocal` lookup in the scope the declaration names."""

        if any(kind not in {"global", "nonlocal"} for kind, _node in entries):
            # The declaring scope also writes the name, so what the target scope holds at the
            # call site is not decidable here.
            return None
        if any(kind == "global" for kind, _node in entries):
            return self.resolve(name, 0) if scope != 0 else None
        parent = self.scope_of.get(scope)
        return None if parent is None else self.resolve(name, parent)

    def bound_in(self, scope_id: int) -> frozenset[str]:
        return frozenset(self.bindings.get(scope_id, {}))


class _HelperStores:
    """Rounds 5 and 6: what a call does to the tracked object it is handed.

    Rounds 3 and 4 close the bindings a correction store can travel through *inside one scope*.
    Round 5 followed the store into a project-local helper: a call whose callee resolves to a
    definition in this module is a mutation of every argument whose bound parameter is stored
    through in the callee body.  Round 6 decides the calls round 5 left as non-captures, in both
    directions, because the audit demonstrated a false accusation and a lost accusation on each
    side of that boundary.

    **Rule A, fail closed on an unresolvable callee.**  Round 5 read every callee it could not
    resolve as a non-capture, and fourteen correct, complete Bonferroni programs were published
    as accusations because of it: `dict.update(record, p=...)`, `operator.setitem(record, ...)`,
    `functools.partial(rescale, family_size=6)`, a static method stored in a name,
    `ADJUSTERS["bonferroni"](record, 6)`, a decorator-supplied wrapper, and the rest.  A call
    that is handed a tracked object is now a mutation of it unless the callee is a project-local
    definition whose body only reads what it binds, or a read-only builtin or library API on the
    closed allowlist above.  Calls with no tracked argument are untouched, so the frozen
    `len(OUTCOMES)` and `", ".join(MUSCULOSKELETAL)` non-capture discipline every earlier round
    preserves is exactly as it was.

    **Rule B, return flow.**  The result of a call that is handed a tracked object carries that
    object's role, unless the callee provably hands back nothing it was given.  `target =
    identity(record)` then `target["p"] = ...` is a complete correction round 5 could not see.

    **Rule C, storing callables as values.**  A project-local callable that stores through a
    parameter is a storing callable, and so is any name, container entry, `functools.partial`,
    bound or static method, or decorated definition that carries one.  Invoking one with a
    tracked argument is a mutation, and so is *passing* one to a call that also carries a tracked
    argument or receiver: `pd.Series(list(results.values())).apply(rescale)` writes into every
    record of `results`.

    **Rule D, closures and nested definitions.**  A `def` or `lambda` whose body stores through a
    free variable is a mutation at its definition site, called or not, because a definition is an
    escape: `def rescale_all(): results[name]["p"] = ...` corrects the whole family through the
    collection's own name in a scope the frozen engine does not follow.  A default argument bound
    to a tracked name is the same escape one binding earlier.  Inside a resolved helper the rule
    runs the other way: a nested definition that is never read there is dead code, and reading it
    as part of the helper lost a true accusation.

    **Four soundness fixes to round 5.**  A parameter is seeded with the role of the argument it
    binds and not with both roles at once; a starred argument binds only what it really forwards;
    a subscript of a record is a scalar and not the record; and a parameter rebound to a fresh
    value in straight-line code before any store through it is detached from the argument.  Each
    one is a true accusation the round-5 closure lost, and each is recorded in the round-6 oracle
    against the row that measured it.

    **Recursion resolves to a fixpoint.**  The storing set and the storing-callable set only
    grow, so a cyclic or mutually recursive callee graph converges rather than needing a
    conservative refusal, and a helper that only calls itself never becomes storing.

    **Round 7 makes the three sides of that decision uniform.**  Round 6 fails closed on a callee
    it cannot resolve; it did not fail closed on a value it cannot follow or on a callable it
    cannot resolve, and it keyed its library allowlist on the spelling of a name rather than on
    what the imports say the name is.  A record inserted into a container by `append`, `extend`,
    `insert`, `add`, or a subscript store now carries its role into that container, so a store
    written through one of the container's elements is a store into the family; the insertion call
    itself stays read-only, and a container reached only by an insertion is judged on what is done
    to it afterwards rather than on the insertion, so appending a record to a scratch list and then
    locating it there is still a read.  A generator expression, a comprehension, and a `lambda` are
    objects that hand out whatever their body names, so a helper returning one hands the record
    back.  Iterating a mapping yields its keys, so the freshness test draws the module-level
    bare-iteration boundary one scope in.  A callable standing in a callable position is admitted
    only when it provably reads, decided after the interprocedural storing fixpoint has run, and a
    callback-bearing call reaches its receiver's roots whether or not the callable is readable.
    The allowlist is keyed on the identity the imports give a base name, so `import json as
    payload` is `json` and `json = Mutator` is not a library name at all.  Three resolution
    defects are fixed with it: a class body is not an enclosing lexical scope, a `global` or
    `nonlocal` declaration continues the lookup in the scope it names, and a `functools.wraps`-
    style forwarding decorator is transparent when its structure proves it forwards and nothing
    more.

    Names are matched module-wide, as they are in rounds 1 to 5.  A name reused in two scopes can
    only add captures, so the error is toward refusal.
    """

    def __init__(self, tree: ast.Module) -> None:
        self._tree = tree
        self._definitions: dict[int, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda] = {}
        self._edges: list[_CaptureEdge] = []
        self._storing: set[tuple[int, str, str | None]] = set()
        self._census: dict[int, tuple[frozenset[str], frozenset[str]]] = {}
        self._reached: dict[tuple[int, str, str | None], frozenset[str]] = {}
        self._hands_back_cache: dict[tuple[int, str, str | None], bool] = {}
        self._bodies: dict[int, ast.Module] = {}
        self._call_callee: dict[int, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda] = {}
        self._call_offset: dict[int, int] = {}
        self._storing_callables: set[str] = set()
        #: Round 7, rule B: the callback-bearing calls the first pass admitted, re-asked once the
        #: interprocedural storing fixpoint has run.
        self._deferred_callbacks: list[tuple[ast.Call, int, frozenset[str]]] = []
        self._scopes = _ScopeCensus(tree)
        self.shadowed_wrappers = _module_bound_names(tree) & (
            _ITERABLE_WRAPPERS
            | _MAPPING_WRAPPERS
            | _CALLBACK_BEARING_BUILTINS
            | {"enumerate", "zip", "next"}
        )
        self._roles = self._seed_roles(tree)
        self._record_names = frozenset(self._roles.records)
        self._parameters = frozenset(
            node.arg for node in ast.walk(tree) if isinstance(node, ast.arg)
        )
        self._tracked = self._roles.names()
        self._collect(tree)
        self._resolve()
        if self._finish_deferred_callbacks():
            self._resolve()
        self._close_return_flow_roles(tree)

    def _body_of(
        self, definition: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    ) -> ast.Module:
        """The callee body, memoized per census: pruning it is pure and it is read many times."""

        body = self._bodies.get(id(definition))
        if body is None:
            body = _callee_body(definition)
            self._bodies[id(definition)] = body
        return body

    # -- roles --------------------------------------------------------------------------

    def _seed_roles(self, tree: ast.Module) -> _RecordDerivation:
        """The round-4 role enumeration over every record collection, without return flow.

        This is stage one: rule B's return flow needs callee resolution, and callee resolution
        needs the roles that decide which arguments are tracked, so the roles are computed once
        without it and the return-flow pass is run afterwards by `record_derived_names`.
        """

        edges, _escaped = _alias_edges(tree)
        component: set[str] = set()
        for collection in record_collection_names(tree):
            frontier = [collection]
            component.add(collection)
            while frontier:
                current = frontier.pop()
                for neighbour in edges.get(current, ()):
                    if neighbour not in component:
                        component.add(neighbour)
                        frontier.append(neighbour)
        self._collection_component = frozenset(component)
        derivation = _RecordDerivation(frozenset(component), shadowed=self.shadowed_wrappers)
        derivation.resolve(tree)
        return derivation

    def _close_return_flow_roles(self, tree: ast.Module) -> None:
        """Re-seed the roles with rule B's return flow and rebuild the census if they grew.

        Stage one computes the roles without return flow, because deciding whether a call hands an
        argument back needs callee resolution and callee resolution needs the roles.  Once the
        first census exists the roles can be recomputed with it, and if that reaches names the
        first pass did not -- `for target in stream(record)` over a helper returning a generator
        over its parameter -- the census is rebuilt over the larger tracked set.  Roles only ever
        grow, so the loop converges; it is bounded anyway, and it does no work at all on a module
        with no passthrough helper, which is every module in the frozen evidence base.
        """

        for _pass in range(_RETURN_FLOW_PASSES):
            derivation = _RecordDerivation(
                self._collection_component,
                shadowed=self.shadowed_wrappers,
                passthrough=self.hands_back_an_argument,
            )
            derivation.resolve(tree)
            if derivation.names() <= self._tracked:
                return
            self._roles = derivation
            self._record_names = frozenset(derivation.records)
            self._tracked = derivation.names()
            self._edges = []
            self._deferred_callbacks = []
            self._collect(tree)
            self._resolve()
            if self._finish_deferred_callbacks():
                self._resolve()

    def _argument_role(self, node: ast.expr) -> str | None:
        inner = node.value if isinstance(node, ast.Starred) else node
        if self._roles.is_record(inner):
            return _ROLE_RECORD
        if self._roles.maps_records(inner):
            return _ROLE_MAPPING
        if self._roles._carries_record(self._roles.element_shape(inner)):
            return _ROLE_SEQUENCE
        return None

    def _roots(self, node: ast.expr) -> frozenset[str]:
        return _capture_roots(node, self._record_names)

    def _interesting(self, roots: frozenset[str]) -> bool:
        """Round 6 fails closed only on a call that is handed a tracked object.

        The tracked set is the round-3 alias component of every record collection closed under
        the round-4 enumeration, plus every parameter name, because a name bound as a parameter
        in one scope is the name a helper body's own tracked object carries.
        """

        return bool(roots & (self._tracked | self._parameters))

    # -- callee classification ----------------------------------------------------------

    def _enclosing_scope(self, node: ast.AST) -> int:
        current: ast.AST | None = self._scopes.parents.get(node)
        while current is not None:
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                return id(current)
            if isinstance(current, ast.ClassDef):
                return id(current)
            current = self._scopes.parents.get(current)
        return 0

    def _enclosing_function(self, node: ast.AST) -> tuple[int, str | None]:
        current: ast.AST | None = self._scopes.parents.get(node)
        class_name: str | None = None
        while current is not None:
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                owner = id(current)
                parent = self._scopes.parents.get(current)
                if isinstance(parent, ast.ClassDef):
                    class_name = parent.name
                return owner, class_name
            current = self._scopes.parents.get(current)
        return 0, None

    def _read_only_callee(self, node: ast.Call) -> bool:
        """True when the callee is on the closed read-only allowlist for tracked arguments."""

        function = node.func
        if isinstance(function, ast.Name):
            name = function.id
            if name in _NEVER_READ_ONLY_CALLEES:
                return False
            kind, target = self._bare_callee_target(name, node)
            if kind == "builtin":
                if name in _CALLBACK_BEARING_BUILTINS:
                    return self._callable_arguments_are_read_only(node)
                return name in _READ_ONLY_BUILTIN_CALLEES
            if kind == "import":
                return self._imported_target_is_read_only(target)
            return False
        if isinstance(function, ast.Attribute):
            attribute = function.attr
            if attribute in _NEVER_READ_ONLY_CALLEES:
                return False
            if _string_receiver(function.value):
                return True
            if attribute in _ELEMENT_CALLBACK_METHODS:
                return self._callable_arguments_are_read_only(node)
            if attribute in _READ_ONLY_CONTAINER_INSERTIONS:
                return True
            if attribute in _READ_ONLY_CONTAINER_QUERIES and self._tracked_receiver(function):
                return True
            if attribute in _CSV_WRITER_METHODS and self._csv_writer_receiver(function, node):
                return True
            return self._qualified_target(function, node) in _READ_ONLY_MODULE_APIS
        return False

    # -- rule C, the allowlist keyed on import-resolved targets --------------------------

    def _bare_callee_target(self, name: str, at: ast.AST) -> tuple[str | None, str | None]:
        """What a bare name denotes: a builtin, an import identity, or nothing this can read.

        Round 6 asked only whether the spelling was bound by anything other than an import, which
        left two demonstrated defects standing.  A project that wrote `json = Mutator` kept the
        qualified `json.dumps` allowlist entry, because the entry was matched on the receiver's
        spelling; and a project that wrote `import json as payload` lost it, because the alias is
        not the spelling.  The identity is what the import statements say: `import pandas as pd`
        and `import pandas` are both `pandas`, `from scipy import stats` is `scipy.stats`, and
        `from json import dumps as serialize` is `json.dumps`.  A name bound by anything else, or
        by imports that disagree, is not a library name and rule A fails closed on it.
        """

        for scope in self._scopes.scope_chain(self._enclosing_scope(at)):
            entries = self._scopes.bindings.get(scope, {}).get(name)
            if entries is None:
                continue
            if any(kind != "import" for kind, _node in entries):
                return None, None
            identities = {
                identity
                for _kind, statement in entries
                if (identity := _import_identity(statement, name)) is not None
            }
            if len(identities) != 1:
                return None, None
            return "import", identities.pop()
        return "builtin", name

    def _qualified_target(self, function: ast.Attribute, at: ast.AST) -> tuple[str, str] | None:
        """`(canonical receiver, attribute)` for a receiver that really is an imported module."""

        if not isinstance(function.value, ast.Name):
            return None
        kind, identity = self._bare_callee_target(function.value.id, at)
        if kind != "import" or identity is None:
            return None
        canonical = _READ_ONLY_MODULE_IDENTITIES.get(identity)
        return None if canonical is None else (canonical, function.attr)

    def _imported_target_is_read_only(self, identity: str | None) -> bool:
        """True when a bare imported name resolves to an allowlisted library target.

        The identity is `module path` plus `attribute`, so the *imported* spelling decides and the
        local alias never does: `from operator import setitem as put` resolves to
        `operator.setitem` and fails closed, while `from json import dumps as serialize` resolves
        to `json.dumps` and is admitted.  The `_READ_ONLY_IMPORTED_CALLEES` fallback keeps the
        measured reducers and correction terminals, whose owning modules vary across the evidence
        base; it is keyed on the imported attribute and never on the local alias, so it is a
        strict narrowing of the round-6 spelling test.
        """

        if identity is None or "." not in identity:
            return False
        module_path, _dot, attribute = identity.rpartition(".")
        canonical = _READ_ONLY_MODULE_IDENTITIES.get(module_path)
        if canonical is not None and (canonical, attribute) in _READ_ONLY_MODULE_APIS:
            return True
        return attribute in _READ_ONLY_IMPORTED_CALLEES

    def _tracked_receiver(self, function: ast.Attribute) -> bool:
        """True when the method's receiver is a name the role enumeration already tracks."""

        return isinstance(function.value, ast.Name) and function.value.id in self._tracked

    def _csv_writer_receiver(self, function: ast.Attribute, at: ast.AST) -> bool:
        """True when the receiver is a name bound exactly once to a `csv` writer constructor."""

        if not isinstance(function.value, ast.Name):
            return False
        for scope in self._scopes.scope_chain(self._enclosing_scope(at)):
            entries = self._scopes.bindings.get(scope, {}).get(function.value.id)
            if entries is None:
                continue
            if len(entries) != 1 or entries[0][0] != "store":
                return False
            parent = self._scopes.parents.get(entries[0][1])
            if not isinstance(parent, ast.Assign) or not isinstance(parent.value, ast.Call):
                return False
            constructor = parent.value.func
            if not isinstance(constructor, ast.Attribute):
                return False
            return self._qualified_target(constructor, parent.value) in _CSV_WRITER_CONSTRUCTORS
        return False

    # -- collection ---------------------------------------------------------------------

    def _collect(self, tree: ast.Module) -> None:
        methods: dict[str, dict[str, ast.FunctionDef | ast.AsyncFunctionDef]] = {}
        owner_class: dict[int, str] = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            table = methods.setdefault(node.name, {})
            bindings: Counter[str] = Counter()
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    bindings[item.name] += 1
                    table[item.name] = item
                    owner_class[id(item)] = node.name
                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            bindings[target.id] += 1
            # A class body that binds one method name twice does not say which definition runs
            # at the call site, so the name is unresolvable and rule A fails closed on it.
            for bound, count in bindings.items():
                if count > 1:
                    table.pop(bound, None)

        for table in methods.values():
            for definition in table.values():
                self._definitions[id(definition)] = definition
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                self._definitions.setdefault(id(node), node)

        self._collect_storing_callables(tree, methods)
        self._scan_calls(tree, methods=methods, owner_class=owner_class)
        self._scan_closures(tree)

    def _resolve_call(
        self,
        node: ast.Call,
        methods: Mapping[str, Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef]],
    ) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda | None, int]:
        """The definition this call runs and the argument offset its receiver consumes."""

        scope = self._enclosing_scope(node)
        function = node.func
        if isinstance(function, ast.Name):
            resolved = self._scopes.resolve(function.id, scope)
            if resolved is None:
                return None, 0
            kind, definition = resolved
            if kind == "class":
                table = methods.get(cast("ast.ClassDef", definition).name, {})
                initializer = table.get("__init__")
                return (initializer, 1) if initializer is not None else (None, 0)
            callee = cast("ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda", definition)
            return (callee, 0) if self._decorators_are_transparent(callee) else (None, 0)
        if isinstance(function, ast.Attribute) and isinstance(function.value, ast.Name):
            receiver = function.value.id
            resolved = self._scopes.resolve(receiver, scope)
            class_name: str | None = None
            offset = 1
            if resolved is not None and resolved[0] == "class":
                class_name = cast("ast.ClassDef", resolved[1]).name
                offset = 0
            elif resolved is not None and resolved[0] == "store":
                class_name = None
            else:
                alias = self._class_alias(receiver, node, methods)
                if alias is not None:
                    class_name, offset = alias, 0
                else:
                    class_name = self._instance_class(receiver, node, methods)
            if class_name is None:
                _owner, enclosing_class = self._enclosing_function(node)
                if enclosing_class is not None and receiver == self._self_name(node):
                    class_name = enclosing_class
            if class_name is None:
                return None, 0
            method = methods.get(class_name, {}).get(function.attr)
            if method is None:
                return None, 0
            if not self._decorators_are_transparent(method):
                return None, 0
            decorators = frozenset(
                item.id for item in method.decorator_list if isinstance(item, ast.Name)
            )
            if "staticmethod" in decorators:
                offset = 0
            elif "classmethod" in decorators:
                offset = 1
            return method, offset
        return None, 0

    def _class_alias(
        self,
        receiver: str,
        node: ast.Call,
        methods: Mapping[str, Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef]],
    ) -> str | None:
        """The class a name bound exactly once to a bare class name denotes.

        `json = Mutator` beside a storing `Mutator.dumps` staticmethod is a local namespace wearing
        a library module's spelling.  Rule C already refuses to read it as the library, and this
        reads it as what it is, so `json.dumps(record, 6)` resolves to the staticmethod and its
        store is seen rather than merely feared.
        """

        scope = self._enclosing_scope(node)
        for scope_id in self._scopes.scope_chain(scope):
            entries = self._scopes.bindings.get(scope_id, {}).get(receiver)
            if entries is None:
                continue
            if len(entries) != 1 or entries[0][0] != "store":
                return None
            parent = self._scopes.parents.get(entries[0][1])
            if not isinstance(parent, ast.Assign) or not isinstance(parent.value, ast.Name):
                return None
            resolved = self._scopes.resolve(parent.value.id, scope_id)
            if resolved is None or resolved[0] != "class":
                return None
            name = cast("ast.ClassDef", resolved[1]).name
            return name if name in methods else None
        return None

    def _instance_class(
        self,
        receiver: str,
        node: ast.Call,
        methods: Mapping[str, Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef]],
    ) -> str | None:
        """The class of a name bound exactly once to a constructor call on a resolved class."""

        scope = self._enclosing_scope(node)
        for scope_id in self._scopes.scope_chain(scope):
            entries = self._scopes.bindings.get(scope_id, {}).get(receiver)
            if entries is None:
                continue
            if len(entries) != 1 or entries[0][0] != "store":
                return None
            target = entries[0][1]
            parent = self._scopes.parents.get(target)
            if not isinstance(parent, ast.Assign) or not isinstance(parent.value, ast.Call):
                return None
            constructor = parent.value.func
            if not isinstance(constructor, ast.Name):
                return None
            resolved = self._scopes.resolve(constructor.id, scope_id)
            if resolved is None or resolved[0] != "class":
                return None
            name = cast("ast.ClassDef", resolved[1]).name
            return name if name in methods else None
        return None

    def _self_name(self, node: ast.AST) -> str | None:
        owner, _class_name = self._enclosing_function(node)
        definition = self._definitions.get(owner)
        if definition is None:
            return None
        positional, _vararg, _keyword, _kwarg = _parameter_slots(definition)
        return positional[0] if positional else None

    def _decorators_are_transparent(
        self, callee: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    ) -> bool:
        """True when no decorator can replace what the definition does.

        A decorator that returns a different callable is what the definition really runs, so a
        decorated name whose decorator this module cannot read is unresolvable and rule A fails
        closed on it -- that is the measured `@bonferroni`-supplied wrapper.  A decorator that
        provably returns its own parameter changes nothing and is transparent, which keeps a
        read-only helper behind a tracing decorator a true accusation.
        """

        if isinstance(callee, ast.Lambda):
            return True
        for decorator in callee.decorator_list:
            node = decorator.func if isinstance(decorator, ast.Call) else decorator
            if isinstance(node, ast.Name) and node.id in _STRUCTURAL_DECORATORS:
                continue
            if isinstance(node, ast.Name) and self._is_identity_definition(node.id, callee):
                continue
            if isinstance(node, ast.Name) and self._is_forwarding_decorator(node.id, callee):
                continue
            return False
        return True

    def _is_forwarding_decorator(self, name: str, at: ast.AST) -> bool:
        """Round 7, semantics fix D(3): a `functools.wraps`-style decorator changes nothing.

        The proof is structural and complete, not a guess from the decorator's spelling.  The
        decorator must be a project-local `def` of exactly one plain parameter; every one of its
        returns must be the same bare name; that name must be bound in its body by exactly one
        nested `def`; the nested wrapper must neither store through its own parameters nor write
        through a free variable; and every call the wrapper makes must be a call of the
        decorator's own parameter, so the arguments it is handed go to the wrapped function and
        nowhere else.  A wrapper carrying `@functools.wraps(func)` is admitted, because that
        decorator copies metadata and does not change what the wrapper does.  Under those
        conditions the decorated name behaves, argument for argument, like the definition it
        decorates, and reading it as unresolvable lost the accusation an uncorrected family under
        a genuine `functools.wraps` logging decorator had earned.
        """

        resolved = self._scopes.resolve(name, self._enclosing_scope(at))
        if resolved is None or resolved[0] != "def":
            return False
        decorator = cast("ast.FunctionDef", resolved[1])
        if decorator.decorator_list:
            return False
        positional, vararg, _keyword, kwarg = _parameter_slots(decorator)
        if len(positional) != 1 or vararg is not None or kwarg is not None:
            return False
        parameter = positional[0]
        own = list(_own_scope_nodes(decorator.body))
        returns = [statement for statement in own if isinstance(statement, ast.Return)]
        if not returns or any(not isinstance(statement.value, ast.Name) for statement in returns):
            return False
        if any(isinstance(statement, (ast.Yield, ast.YieldFrom)) for statement in own):
            return False
        returned = {cast("ast.Name", statement.value).id for statement in returns}
        if len(returned) != 1:
            return False
        wrapper_name = returned.pop()
        wrappers = [
            item
            for item in own
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            and item.name == wrapper_name
        ]
        if len(wrappers) != 1:
            return False
        wrapper = wrappers[0]
        for item in wrapper.decorator_list:
            head = item.func if isinstance(item, ast.Call) else item
            if isinstance(head, ast.Attribute):
                if self._qualified_target(head, wrapper) in _METADATA_DECORATORS:
                    continue
            return False
        if self._definition_stores(wrapper):
            return False
        body = self._body_of(wrapper)
        _edges, escaped = _alias_edges(body)
        written = escaped | _object_mutated_names(body)
        if written - self._scopes.bound_in(id(wrapper)):
            return False
        for call in _own_scope_nodes(wrapper.body):
            if isinstance(call, ast.Call) and not (
                isinstance(call.func, ast.Name) and call.func.id == parameter
            ):
                return False
        return True

    # -- rule B, callables standing in a callable position ------------------------------

    def _callable_positions(self, node: ast.Call) -> list[ast.expr] | None:
        """The arguments of a callback-bearing call that are themselves callables."""

        function = node.func
        if isinstance(function, ast.Name):
            if function.id not in _CALLBACK_BEARING_BUILTINS:
                return None
            if function.id in _ELEMENT_CALLBACK_BUILTINS:
                return list(node.args[:1])
            return [item.value for item in node.keywords if item.arg == "key"]
        if isinstance(function, ast.Attribute) and function.attr in _ELEMENT_CALLBACK_METHODS:
            if node.args:
                return list(node.args[:1])
            return [item.value for item in node.keywords if item.arg == "func"]
        return None

    def _is_callback_bearing(self, node: ast.Call) -> bool:
        return self._callable_positions(node) is not None

    def _callable_arguments_are_read_only(self, node: ast.Call) -> bool:
        """Rule B: a callable beside a tracked argument is admitted only when it provably reads.

        Round 6 asked the opposite question -- whether the callable was *known* to store -- and
        four complete Bonferroni passes reached `Series.apply` through routes the question could
        not see: a wrapper that stores only by calling a storing helper, a callable held in an
        attribute, one taken out of a dictionary with `.get`, and one returned by a chain of
        identity functions.  A callable position now has to resolve: a `lambda` or a project-local
        definition that does not store, a read-only builtin, an allowlisted library target, or a
        bound method of a tracked container.  Everything else is storing by default.
        """

        positions = self._callable_positions(node)
        if not positions:
            return positions is not None
        return all(self._callable_is_read_only(item, node) for item in positions)

    def _callable_is_read_only(self, node: ast.expr, at: ast.Call) -> bool:
        if isinstance(node, ast.Lambda):
            return not self._definition_is_storing(node)
        if isinstance(node, ast.Name):
            kind, identity = self._bare_callee_target(node.id, at)
            if kind == "builtin":
                return (
                    node.id in _READ_ONLY_BUILTIN_CALLEES
                    and node.id not in _NEVER_READ_ONLY_CALLEES
                )
            if kind == "import":
                return self._imported_target_is_read_only(identity)
            resolved = self._scopes.resolve(node.id, self._enclosing_scope(at))
            if resolved is None or resolved[0] not in {"def", "lambda"}:
                return False
            definition = cast("ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda", resolved[1])
            if not self._decorators_are_transparent(definition):
                return False
            return not self._definition_is_storing(definition)
        if isinstance(node, ast.Attribute):
            if node.attr in _NEVER_READ_ONLY_CALLEES:
                return False
            if self._qualified_target(node, at) in _READ_ONLY_MODULE_APIS:
                return True
            return node.attr in _READ_ONLY_BOUND_CALLABLES and self._tracked_receiver(node)
        return False

    def _definition_is_storing(
        self, definition: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    ) -> bool:
        """True when the definition writes through anything it is handed or closes over.

        The interprocedural storing fixpoint is consulted first, so `def wrapper(entry):
        direct(entry)` is storing even though its own body writes nothing.  During the first
        collection pass the fixpoint is still empty and only the direct census answers; the
        deferred pass below re-asks every callable position once the fixpoint has run, which is
        what closes the wrapper route.
        """

        identifier = id(definition)
        if any(
            (identifier, parameter, None) in self._storing
            for parameter in _all_parameters(definition)
        ):
            return True
        if self._definition_stores(definition):
            return True
        body = self._body_of(definition)
        _edges, escaped = _alias_edges(body)
        written = (escaped | _object_mutated_names(body)) - self._scopes.bound_in(identifier)
        return any(self._interesting(frozenset({name})) for name in written)

    def _is_identity_definition(self, name: str, at: ast.AST) -> bool:
        resolved = self._scopes.resolve(name, self._enclosing_scope(at))
        if resolved is None or resolved[0] != "def":
            return False
        definition = cast("ast.FunctionDef", resolved[1])
        positional, _vararg, _keyword, _kwarg = _parameter_slots(definition)
        if not positional:
            return False
        parameter = positional[0]
        returns = [node for node in ast.walk(definition) if isinstance(node, ast.Return)]
        if not returns:
            return False
        for statement in returns:
            value = statement.value
            if not isinstance(value, ast.Name) or value.id != parameter:
                return False
        body = self._body_of(definition)
        _edges, escaped = _alias_edges(body)
        return not ({parameter} & (escaped | _object_mutated_names(body)))

    # -- storing callables (rule C) -----------------------------------------------------

    def _collect_storing_callables(
        self,
        tree: ast.Module,
        methods: Mapping[str, Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef]],
    ) -> None:
        """Every name that carries a callable which stores through what it is handed."""

        storing_definitions: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._definition_stores(node):
                    storing_definitions.add(node.name)
            elif isinstance(node, ast.Assign) and len(node.targets) == 1:
                target, value = node.targets[0], node.value
                if (
                    isinstance(target, ast.Name)
                    and isinstance(value, ast.Lambda)
                    and self._definition_stores(value)
                ):
                    storing_definitions.add(target.id)
        for name, table in methods.items():
            for method, definition in table.items():
                if self._definition_stores(definition):
                    storing_definitions.add(method)
                    storing_definitions.add(name)
        self._storing_callables = set(storing_definitions)
        changed = True
        while changed:
            changed = False
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                    continue
                target, value = node.targets[0], node.value
                if not isinstance(target, ast.Name) or target.id in self._storing_callables:
                    continue
                if self._carries_storing_callable(value):
                    self._storing_callables.add(target.id)
                    changed = True

    def _definition_stores(
        self, definition: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    ) -> bool:
        """True when the body stores through any name that reaches one of its parameters."""

        body = self._body_of(definition)
        _edges, escaped = _alias_edges(body)
        mutated = _object_mutated_names(body)
        parameters = _all_parameters(definition)
        for parameter in parameters:
            component = self._alias_component(body, parameter)
            if component & (escaped | mutated):
                return True
        return False

    def _carries_storing_callable(self, node: ast.expr) -> bool:
        """True when the expression evaluates to, or holds, a storing callable."""

        if isinstance(node, ast.Name):
            return node.id in self._storing_callables
        if isinstance(node, ast.Lambda):
            return self._definition_stores(node)
        if isinstance(node, ast.Attribute):
            return node.attr in self._storing_callables or self._carries_storing_callable(
                node.value
            )
        if isinstance(node, ast.Subscript):
            return self._carries_storing_callable(node.value)
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return any(self._carries_storing_callable(item) for item in node.elts)
        if isinstance(node, ast.Dict):
            return any(
                item is not None and self._carries_storing_callable(item) for item in node.values
            )
        if isinstance(node, ast.Call):
            function = node.func
            partial = (isinstance(function, ast.Name) and function.id == "partial") or (
                isinstance(function, ast.Attribute) and function.attr == "partial"
            )
            if partial:
                return any(
                    self._carries_storing_callable(argument)
                    for argument in (*node.args, *(item.value for item in node.keywords))
                )
        return False

    def _carries_a_storing_callable(self, node: ast.Call) -> bool:
        return any(
            self._carries_storing_callable(argument)
            for argument in (*node.args, *(item.value for item in node.keywords))
        )

    def _alias_component(self, body: ast.Module, parameter: str) -> set[str]:
        edges, _escaped = _alias_edges(body)
        component = {parameter}
        frontier = [parameter]
        while frontier:
            current = frontier.pop()
            for neighbour in edges.get(current, ()):
                if neighbour not in component:
                    component.add(neighbour)
                    frontier.append(neighbour)
        return component

    # -- call scanning ------------------------------------------------------------------

    def _scan_calls(
        self,
        tree: ast.Module,
        *,
        methods: Mapping[str, Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef]],
        owner_class: Mapping[int, str],
    ) -> None:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            owner, _class_name = self._enclosing_function(node)
            self._record_callback_edges(node, owner)
            callee, offset = self._resolve_call(node, methods)
            if callee is not None:
                self._call_callee[id(node)] = callee
                self._call_offset[id(node)] = offset
                self._record_edges(node, owner=owner, callee=callee, offset=offset)
                continue
            self._record_unresolvable(node, owner)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                self._record_default_edges(node)

    def _tracked_arguments(self, node: ast.Call) -> frozenset[str]:
        roots: set[str] = set()
        for argument in (*node.args, *(item.value for item in node.keywords)):
            roots |= self._roots(argument)
        return frozenset(roots)

    def _receiver_roots(self, node: ast.Call) -> frozenset[str]:
        function = node.func
        if isinstance(function, ast.Attribute):
            return self._roots(function.value)
        return frozenset()

    def _record_unresolvable(self, node: ast.Call, owner: int) -> None:
        """Rule A: a call handed a tracked object with no readable body is a mutation of it."""

        roots = self._tracked_arguments(node)
        storing_callable = self._carries_a_storing_callable(node)
        callback = self._is_callback_bearing(node)
        if storing_callable or callback:
            # A callback-bearing call writes through its receiver, not through its arguments:
            # `pd.Series(list(results.values())).apply(rescale)` corrects every record of
            # `results`, and the receiver is the only place those records appear.
            roots = roots | self._receiver_roots(node)
        if not self._interesting(roots):
            return
        if not storing_callable and self._read_only_callee(node):
            if callback:
                self._deferred_callbacks.append((node, owner, roots))
            return
        if self._carries_storing_callable(node.func):
            roots = roots | self._receiver_roots(node)
        self._edges.append(_CaptureEdge(owner, None, _ANY_PARAMETER, roots))

    def _finish_deferred_callbacks(self) -> bool:
        """Rule B, second pass: re-ask every admitted callable position after the fixpoint.

        Callable classification has to run *after* the interprocedural storing fixpoint, because a
        wrapper that stores only by calling a storing helper writes nothing in its own body.  The
        first pass answers with the direct census alone, this pass re-asks with the fixpoint in
        hand, and the storing sets only grow, so re-running the fixpoint afterwards converges.
        """

        deferred, self._deferred_callbacks = self._deferred_callbacks, []
        added = False
        for node, owner, roots in deferred:
            if self._callable_arguments_are_read_only(node):
                continue
            self._edges.append(_CaptureEdge(owner, None, _ANY_PARAMETER, roots))
            added = True
        return added

    def _record_callback_edges(self, node: ast.Call, owner: int) -> None:
        """`map`, `filter`, and the `key=` builtins apply a callable to the elements beside it."""

        function = node.func
        if not isinstance(function, ast.Name) or function.id in self.shadowed_wrappers:
            return
        if function.id in _ELEMENT_CALLBACK_BUILTINS and node.args:
            callable_node, iterables = node.args[0], node.args[1:]
        elif function.id in _KEY_CALLBACK_BUILTINS and node.args:
            keyword = next((item for item in node.keywords if item.arg == "key"), None)
            if keyword is None:
                return
            callable_node, iterables = keyword.value, node.args[:1]
        else:
            return
        callee = self._callback_definition(callable_node, node)
        if callee is None:
            return
        positional, vararg, _keyword_bindable, _kwarg = _parameter_slots(callee)
        parameter = positional[0] if positional else vararg
        if parameter is None:
            return
        roots: set[str] = set()
        role: str | None = None
        for iterable in iterables:
            roots |= self._roots(iterable)
            shape = self._roles.element_shape(iterable)
            if role is None and self._roles._carries_record(shape):
                role = _ROLE_RECORD
        if roots:
            self._edges.append(_CaptureEdge(owner, id(callee), parameter, frozenset(roots), role))

    def _callback_definition(
        self, node: ast.expr, at: ast.Call
    ) -> ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda | None:
        if isinstance(node, ast.Lambda):
            self._definitions.setdefault(id(node), node)
            return node
        if isinstance(node, ast.Name):
            resolved = self._scopes.resolve(node.id, self._enclosing_scope(at))
            if resolved is not None and resolved[0] in {"def", "lambda"}:
                return cast("ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda", resolved[1])
        return None

    def _record_edges(
        self,
        node: ast.Call,
        *,
        owner: int,
        callee: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda,
        offset: int,
    ) -> None:
        positional, vararg, keyword_bindable, kwarg = _parameter_slots(callee)
        index = offset
        for argument in node.args:
            roots = self._roots(argument)
            if isinstance(argument, ast.Starred):
                # Round 6, soundness fix 2: `*X` forwards the ELEMENTS of `X`.  A mapping and a
                # record both pass their KEYS, so `*record` hands over strings and binds nothing.
                # A sequence forwards what it holds, and an argument with no role at all is
                # forwarded conservatively, which is what keeps `forward(*args)` closed.
                if roots and self._argument_role(argument) not in (_ROLE_RECORD, _ROLE_MAPPING):
                    self._edges.append(
                        _CaptureEdge(owner, id(callee), _ANY_PARAMETER, roots, _ROLE_RECORD)
                    )
                index = len(positional) + 1
                continue
            parameter = (
                positional[index]
                if index < len(positional)
                else (vararg if vararg is not None else None)
            )
            bucket = index >= len(positional)
            index += 1
            if parameter is not None and roots:
                role = self._argument_role(argument)
                if bucket and role is not None:
                    role = _ROLE_SEQUENCE
                self._edges.append(_CaptureEdge(owner, id(callee), parameter, roots, role))
        for keyword in node.keywords:
            roots = self._roots(keyword.value)
            if not roots:
                continue
            role = self._argument_role(keyword.value)
            if keyword.arg is None:
                # `**X` forwards the VALUES of `X`.  A record's values are the collected scalars
                # and bind nothing; a mapping of records forwards records, and a bucket with no
                # role is forwarded conservatively so `rescale(**fields)` stays closed.
                if role != _ROLE_RECORD:
                    self._edges.append(
                        _CaptureEdge(owner, id(callee), _ANY_PARAMETER, roots, _ROLE_RECORD)
                    )
                continue
            if keyword.arg in keyword_bindable:
                parameter = keyword.arg
            elif kwarg is not None:
                parameter = kwarg
                if role is not None:
                    role = _ROLE_MAPPING
            else:
                continue
            self._edges.append(_CaptureEdge(owner, id(callee), parameter, roots, role))

    def _record_default_edges(
        self, definition: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
    ) -> None:
        """Rule D: a default argument bound to a tracked name is an escape at the def site."""

        arguments = definition.args
        slots = [*arguments.posonlyargs, *arguments.args]
        pairs: list[tuple[str, ast.expr]] = []
        if arguments.defaults:
            for slot, default in zip(
                slots[-len(arguments.defaults) :], arguments.defaults, strict=True
            ):
                pairs.append((slot.arg, default))
        for slot, keyword_default in zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True):
            if keyword_default is not None:
                pairs.append((slot.arg, keyword_default))
        owner, _class_name = self._enclosing_function(definition)
        for parameter, default in pairs:
            roots = self._roots(default)
            if not roots:
                continue
            self._edges.append(
                _CaptureEdge(owner, id(definition), parameter, roots, self._argument_role(default))
            )

    def _scan_closures(self, tree: ast.Module) -> None:
        """Rule D: a definition whose body stores through a free variable is an escape.

        A definition is an escape whether or not it is called, because the caller decides.  The
        one exception is the other half of the same rule: a definition written *inside* a helper
        and never read there is dead code that the call cannot reach, and counting it lost the
        true accusation the never-called nested store row pins.
        """

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and self._is_dead_nested(
                node
            ):
                continue
            body = self._body_of(node)
            _edges, escaped = _alias_edges(body)
            written = escaped | _object_mutated_names(body)
            free = written - self._scopes.bound_in(id(node))
            free = frozenset(name for name in free if self._interesting(frozenset({name})))
            if free:
                owner, _class_name = self._enclosing_function(node)
                self._edges.append(_CaptureEdge(owner, None, _ANY_PARAMETER, frozenset(free)))

    def _is_dead_nested(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """True for a definition written inside a function body and never read there."""

        parent = self._scopes.parents.get(node)
        while parent is not None and not isinstance(
            parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.Module, ast.ClassDef)
        ):
            parent = self._scopes.parents.get(parent)
        if not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        if node.decorator_list:
            return False
        return not _name_is_read(list(parent.body), node.name)

    # -- the storing fixpoint -----------------------------------------------------------

    def _body_census(self, callee: int) -> tuple[frozenset[str], frozenset[str]]:
        if callee not in self._census:
            body = self._body_of(self._definitions[callee])
            _edges, escaped = _alias_edges(body)
            self._census[callee] = (escaped, _object_mutated_names(body))
        return self._census[callee]

    def _reached_names(self, callee: int, parameter: str, role: str | None) -> frozenset[str]:
        """The parameter's alias component, closed under the round-4 record-derived forms.

        Round 6, soundness fix 1: the component is seeded with the role the argument carries and
        with nothing else.  Round 5 seeded a parameter as a mapping *and* a sequence of records at
        once, so `for key in table` inside a helper bound `key` as a record where the identical
        module-level loop leaves it opaque, and the read-only key loop lost its accusation.  An
        argument with no role is untracked, and seeding it both ways keeps the round-5 capture set
        for those names byte-for-byte.
        """

        key = (callee, parameter, role)
        if key not in self._reached:
            body = self._body_of(self._definitions[callee])
            component = self._alias_component(body, parameter)
            mappings = frozenset(component) if role in (None, _ROLE_MAPPING) else frozenset()
            derivation = _RecordDerivation(mappings, shadowed=self.shadowed_wrappers)
            if role in (None, _ROLE_SEQUENCE):
                for name in component:
                    derivation.sequences[name] = _RECORD
            if role in (None, _ROLE_RECORD):
                derivation.records.update(component)
            derivation.resolve(body)
            self._reached[key] = frozenset(component) | derivation.names()
        return self._reached[key]

    def _edge_is_storing(self, edge: _CaptureEdge) -> bool:
        if edge.callee is None:
            return True
        if edge.parameter != _ANY_PARAMETER:
            return (edge.callee, edge.parameter, edge.role) in self._storing
        return any(callee == edge.callee for callee, _parameter, _role in self._storing)

    def _detached(self, callee: int, parameter: str, role: str | None) -> bool:
        """Round 6, soundness fix 4: the parameter is rebound to a fresh value before any store.

        `def inspect_record(entry): entry = {}; entry["scratch"] = 1` never touches the record it
        was handed, and reading the later store as a store through the argument lost a true
        accusation.  The rebinding has to be straight-line -- a rebinding inside a branch or a
        loop leaves the alias standing -- and the parameter may not be read before it, so no
        alias of the argument can outlive the rebinding.  `dict(entry)` is a fresh copy of one
        record, so it detaches a record-role parameter; a shallow copy of a *mapping* of records
        still holds the same records and detaches nothing.
        """

        definition = self._definitions[callee]
        if isinstance(definition, ast.Lambda):
            return False
        for statement in definition.body:
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
                target = statement.targets[0]
                if isinstance(target, ast.Name) and target.id == parameter:
                    if self._fresh_value(statement.value, parameter, role):
                        return True
                    return False
            if _name_is_read([statement], parameter):
                return False
            if any(
                isinstance(node, ast.Name)
                and node.id == parameter
                and isinstance(node.ctx, (ast.Store, ast.Del))
                for node in ast.walk(statement)
            ):
                return False
        return False

    def _fresh_value(self, value: ast.expr, parameter: str, role: str | None) -> bool:
        if isinstance(value, (ast.Dict, ast.List, ast.Set, ast.Tuple)):
            return not self._roots(value)
        if isinstance(value, ast.Constant):
            return True
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
            if value.func.id in self.shadowed_wrappers:
                return False
            if value.func.id not in (_COLLECTION_SEED_CALLS | {"set", "tuple", "frozenset"}):
                return False
            if not value.args:
                return True
            # A shallow copy of one record is a new record; a shallow copy of a mapping of
            # records is a different container holding the same records.
            return role == _ROLE_RECORD and self._roots(value) == frozenset({parameter})
        return False

    def _reaches_a_store(self, callee: int, parameter: str, role: str | None = None) -> bool:
        if self._detached(callee, parameter, role):
            return False
        names = self._reached_names(callee, parameter, role)
        escaped, mutated = self._body_census(callee)
        if names & (escaped | mutated):
            return True
        return any(
            edge.roots & names and self._edge_is_storing(edge)
            for edge in self._edges
            if edge.owner == callee
        )

    def _resolve(self) -> None:
        wanted: set[tuple[int, str, str | None]] = set()
        for edge in self._edges:
            if edge.callee is None:
                continue
            definition = self._definitions.get(edge.callee)
            if definition is None:
                continue
            if edge.parameter == _ANY_PARAMETER:
                wanted.update(
                    (edge.callee, name, edge.role) for name in _all_parameters(definition)
                )
            else:
                wanted.add((edge.callee, edge.parameter, edge.role))
        # Every parameter of every reachable definition is asked about with no role too, so a
        # body-internal edge whose role differs from the call site's is still answered.
        for callee, definition in self._definitions.items():
            for parameter in _all_parameters(definition):
                wanted.add((callee, parameter, None))
        changed = True
        while changed:
            changed = False
            for callee, parameter, role in sorted(
                wanted, key=lambda item: (item[0], item[1], str(item[2]))
            ):
                if (callee, parameter, role) in self._storing:
                    continue
                if self._reaches_a_store(callee, parameter, role):
                    self._storing.add((callee, parameter, role))
                    changed = True

    # -- results ------------------------------------------------------------------------

    def captured_names(self) -> frozenset[str]:
        """Every name handed to a call that writes into what it is handed."""

        captured: set[str] = set()
        for edge in self._edges:
            if self._edge_is_storing(edge):
                captured |= edge.roots
        return frozenset(captured)

    def hands_back_an_argument(self, node: ast.Call) -> bool:
        """Rule B: the call's result carries the object one of its arguments handed over.

        A resolved project-local callee that returns a name reaching one of its parameters hands
        that object back, so `target = identity(record)` binds the record itself and a later
        `target["p"] = ...` is the same store as `record["p"] = ...`.  A callee whose every
        return is a display, a literal, or a scalar expression hands back nothing it was given,
        which is what keeps a read-only helper returning a NEW dictionary a true accusation when
        the caller stores into it.
        """

        callee = self._call_callee.get(id(node))
        if callee is None:
            return False
        offset = self._call_offset.get(id(node), 0)
        positional, vararg, keyword_bindable, kwarg = _parameter_slots(callee)
        bound: set[tuple[str, str | None]] = set()
        index = offset
        for argument in node.args:
            role = self._argument_role(argument)
            if isinstance(argument, ast.Starred):
                bound |= {(name, role) for name in _all_parameters(callee)}
                break
            if index < len(positional):
                bound.add((positional[index], role))
            elif vararg is not None:
                bound.add((vararg, _ROLE_SEQUENCE if role is not None else None))
            index += 1
        for keyword in node.keywords:
            role = self._argument_role(keyword.value)
            if keyword.arg is None:
                bound |= {(name, role) for name in _all_parameters(callee)}
            elif keyword.arg in keyword_bindable:
                bound.add((keyword.arg, role))
            elif kwarg is not None:
                bound.add((kwarg, _ROLE_MAPPING if role is not None else None))
        return any(self._returns_parameter(id(callee), name, role) for name, role in bound)

    def _returns_parameter(self, callee: int, parameter: str, role: str | None) -> bool:
        """True when some return of the callee hands back the object this parameter binds.

        The freshness test is role-aware for the reason soundness fix 3 is: a helper that returns
        `{"p": entry["p"]}` builds a NEW dictionary out of one scalar, so a caller that stores
        into the result never touches the family, and reading the subscript back to the record
        would have refused a genuinely uncorrected family.
        """

        key = (callee, parameter, role)
        if key in self._hands_back_cache:
            return self._hands_back_cache[key]
        definition = self._definitions[callee]
        body = self._body_of(definition)
        if isinstance(definition, ast.Lambda):
            values: list[ast.expr] = [definition.body]
        else:
            values = [
                statement.value
                for statement in ast.walk(body)
                if isinstance(statement, ast.Return) and statement.value is not None
            ]
        names = self._reached_names(callee, parameter, role)
        records, mappings = self._body_roles(callee, parameter, role)
        result = any(bool(_capture_roots(value, records, mappings) & names) for value in values)
        self._hands_back_cache[key] = result
        return result

    def _body_roles(
        self, callee: int, parameter: str, role: str | None
    ) -> tuple[frozenset[str], frozenset[str]]:
        """The record-role and mapping-role names inside the callee body, given the argument role.

        Round 7, rule A(3): the mapping half is what draws the key boundary in the freshness test.
        `def summarize(table): return {"names": list(table)}` iterates a mapping of records, and
        iterating a mapping yields its keys, so the dictionary it returns holds strings and the
        caller's `summary["scratch"] = 1` cannot reach the family.  Round 6 read the wrapper as a
        handover of the mapping's root and refused a family that really was left uncorrected.
        """

        body = self._body_of(self._definitions[callee])
        component = self._alias_component(body, parameter)
        seeded = frozenset(component) if role in (None, _ROLE_MAPPING) else frozenset()
        derivation = _RecordDerivation(seeded, shadowed=self.shadowed_wrappers)
        if role in (None, _ROLE_SEQUENCE):
            for name in component:
                derivation.sequences[name] = _RECORD
        if role in (None, _ROLE_RECORD):
            derivation.records.update(component)
        derivation.resolve(body)
        # A name that is also a sequence of records, or a record itself, is not key-yielding: a
        # role the argument does not carry may never make the freshness test more permissive.
        keyed = set(derivation.mappings) - set(derivation.sequences) - derivation.records
        return frozenset(derivation.records), frozenset(keyed)


def helper_captured_names(tree: ast.Module) -> frozenset[str]:
    """Rounds 5 and 6: the names a call writes into, or hands to something that writes."""

    return _HelperStores(tree).captured_names()


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

    Round 5 adds one more census against the same names.  `helper_captured_names` returns every
    name handed to a project-local callee that stores through the parameter the argument binds,
    so `bonferroni_adjust(record, len(OUTCOMES))` into a helper writing `entry["p"] = ...`
    refuses exactly as a direct store through `record` does.  Unlike the mutation census, the
    capture census is checked for the collection's own name too: the collection's own stores are
    excluded because the frozen engine judges them, and a store written inside a helper through a
    differently named parameter is not one the frozen engine sees.

    Names are matched module-wide rather than per scope, as they are in rounds 1 to 3.  A name
    reused in two scopes can only add edges, so the error is toward refusal.
    """

    edges, escaped = _alias_edges(tree)
    mutated = _object_mutated_names(tree)
    census = _HelperStores(tree)
    captured = census.captured_names()
    for collection in record_collection_names(tree):
        component = {collection}
        frontier = [collection]
        while frontier:
            current = frontier.pop()
            for neighbour in edges.get(current, ()):
                if neighbour not in component:
                    component.add(neighbour)
                    frontier.append(neighbour)
        derived, inserted_only = record_derived_roles(tree, frozenset(component), census)
        for name in component | set(derived):
            if name in escaped:
                return True
            if name != collection and name in mutated:
                # Round 7, rule A(1): a container that holds records only because records were
                # put into it is refused by the same census as any other derived name, except
                # for the insertion and query calls that put them there and read them back.
                if name not in inserted_only or not _insertion_container_is_only_filled_and_read(
                    tree, name
                ):
                    return True
            if name in captured:
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
    "helper_captured_names",
    "record_collection_alias_unresolved",
    "record_collection_names",
    "record_derived_names",
]
