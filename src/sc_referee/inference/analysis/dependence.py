"""Complete typed dependence formulas; every declared read is represented or unknown."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from sc_referee.inference.ids import stable_id


class EdgeKind(Enum):
    VALUE = "VALUE"
    CONTROL = "CONTROL"
    ALIAS = "ALIAS"
    MUTATION = "MUTATION"
    FIELD = "FIELD"
    FITTED_STATE = "FITTED_STATE"
    ARTIFACT = "ARTIFACT"
    SERIALIZE = "SERIALIZE"
    CONFIG = "CONFIG"
    FORMAT = "FORMAT"


@dataclass(frozen=True)
class EdgeEvidence:
    certified: bool = True
    exact_field: bool = True
    singleton_must_alias: bool = True
    no_possible_overwrite: bool = True
    serializer_resolved: bool = True
    artifact_resolved: bool = True
    config_resolved: bool = True
    format_resolved: bool = True
    fitted_state_resolved: bool = True
    widened: bool = False
    unknown_havoc: bool = False

    def sound_for_must(self) -> bool:
        return (self.certified and self.exact_field and self.singleton_must_alias
                and self.no_possible_overwrite and self.serializer_resolved
                and self.artifact_resolved and self.config_resolved and self.format_resolved
                and self.fitted_state_resolved and not self.widened and not self.unknown_havoc)


class DepExpr:
    pass


@dataclass(frozen=True)
class Atom(DepExpr):
    node: str
    edge_kind: EdgeKind = EdgeKind.VALUE
    evidence: EdgeEvidence = EdgeEvidence()


@dataclass(frozen=True)
class Unknown(DepExpr):
    boundary_id: str
    reason: str


@dataclass(frozen=True)
class AllOf(DepExpr):
    items: tuple[DepExpr, ...]
    consumption_complete: bool = False


@dataclass(frozen=True)
class ChoiceOf(DepExpr):
    items: tuple[DepExpr, ...]


@dataclass(frozen=True)
class Guard:
    id: str
    feasible: bool | None
    pinned: bool


@dataclass(frozen=True)
class TransformBinding:
    solver_id: str
    operation: str
    parameters: tuple[tuple[str, object], ...] = ()
    certified: bool = True
    bridge_id: str | None = None

    def parameter(self, name: str, default=None):
        return dict(self.parameters).get(name, default)


@dataclass(frozen=True)
class Alternative:
    id: str
    guard: Guard
    definition: str
    requirements: DepExpr
    transform: TransformBinding
    constraints: tuple[object, ...] = ()


@dataclass(frozen=True)
class Derivation:
    target: str
    alternatives: tuple[Alternative, ...]


@dataclass(frozen=True)
class DependenceProgram:
    derivations: Mapping[str, Derivation] = field(default_factory=dict)
    reads: Mapping[str, DepExpr | None] = field(default_factory=dict)
    producers: frozenset[str] = frozenset()
    max_canonical_nodes: int = 10000

    def validate(self) -> None:
        missing = sorted(read_id for read_id, requirements in self.reads.items()
                         if requirements is None)
        if missing:
            raise ValueError(f"abstract reads lack dependence or unknown boundary: {', '.join(missing)}")
        for target, derivation in self.derivations.items():
            if target != derivation.target:
                raise ValueError(f"derivation key/target mismatch: {target!r}")
            if not derivation.alternatives:
                raise ValueError(f"derivation {target!r} has no alternatives")


class DependenceBuilder:
    def __init__(self, *, max_canonical_nodes: int = 10000):
        self.derivations: dict[str, Derivation] = {}
        self.reads: dict[str, DepExpr | None] = {}
        self.producers: set[str] = set()
        self.max_canonical_nodes = max_canonical_nodes

    def add_derivation(self, derivation: Derivation) -> None:
        if derivation.target in self.derivations:
            raise ValueError(f"duplicate derivation target: {derivation.target}")
        self.derivations[derivation.target] = derivation

    def add_producer(self, producer: str) -> None:
        self.producers.add(producer)

    def declare_read(self, read_id: str) -> None:
        self.reads.setdefault(read_id, None)

    def record_read(self, read_id: str, requirements: DepExpr | None, *,
                    boundary_id: str | None = None, reason: str = "unresolved read") -> None:
        if requirements is None:
            if boundary_id is None:
                raise ValueError("an unresolved read requires an explicit boundary id")
            requirements = Unknown(boundary_id, reason)
        self.reads[read_id] = requirements

    def build(self) -> DependenceProgram:
        return DependenceProgram(dict(self.derivations), dict(self.reads),
                                 frozenset(self.producers), self.max_canonical_nodes)


def _location(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _location(node.value)
        return f"{base}.{node.attr}" if base is not None else None
    if isinstance(node, ast.Subscript):
        base = _location(node.value)
        if base is None:
            return None
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, (str, int)):
            return f"{base}[{node.slice.value!r}]"
    return None


def build_dependence(program) -> DependenceProgram:
    builder = DependenceBuilder()
    environments: dict[str, str] = {}

    def expression(node: ast.AST, source_index: int):
        if isinstance(node, ast.Name):
            bound = environments.get(node.id)
            if bound is not None:
                return Atom(bound)
            producer = f"input:{node.id}"
            builder.add_producer(producer)
            return Atom(producer)
        if isinstance(node, ast.Constant):
            producer = stable_id(
                "literal", source_index, getattr(node, "lineno", 0),
                getattr(node, "col_offset", 0), getattr(node, "end_lineno", 0),
                getattr(node, "end_col_offset", 0),
            )
            builder.add_producer(producer)
            return Atom(producer)
        return Unknown(
            stable_id("expression-boundary", source_index, getattr(node, "lineno", 0),
                      getattr(node, "col_offset", 0), getattr(node, "end_lineno", 0),
                      getattr(node, "end_col_offset", 0)),
            "expression_outside_live_closed_identity_subset",
        )

    for unit in program.sources:
        if unit.parsed.tree is None:
            builder.record_read(f"read:{unit.source_index}:parse", None,
                                boundary_id=f"parse:{unit.source_index}", reason="source did not parse")
            continue
        ordinal = 0
        nodes = sorted(ast.walk(unit.parsed.tree),
                       key=lambda node: (getattr(node, "lineno", 0), getattr(node, "col_offset", 0),
                                         getattr(node, "end_lineno", 0), getattr(node, "end_col_offset", 0),
                                         type(node).__name__))
        for node in nodes:
            requirements = None
            reason = None
            if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load):
                location = _location(node)
                if location is None:
                    reason = "dynamic_or_ambiguous_field_read"
                else:
                    requirements = Atom(location, EdgeKind.FIELD)
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                location = _location(node)
                if location is None:
                    reason = "ambiguous_attribute_read"
                else:
                    requirements = Atom(location, EdgeKind.FIELD)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                requirements = Atom(node.id, EdgeKind.VALUE)
            elif isinstance(node, ast.Call):
                reason = "call_effects_are_opaque_or_summary_unresolved"
            else:
                continue
            read_id = stable_id("read", unit.source_index, getattr(node, "lineno", 0),
                                getattr(node, "col_offset", 0), getattr(node, "end_lineno", 0),
                                getattr(node, "end_col_offset", 0), ordinal)
            ordinal += 1
            if requirements is not None:
                builder.record_read(read_id, requirements)
            else:
                builder.record_read(read_id, None, boundary_id=f"boundary:{read_id}", reason=reason or "unknown")
        # A deliberately tiny live subset: straight-line exact name assignments. This is enough to
        # certify an identity path from a manifest-bound external atom to a report root. Calls,
        # branches, mutation, and every richer expression remain explicit unknown boundaries.
        for statement in unit.parsed.tree.body:
            if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
                continue
            targets = statement.targets if isinstance(statement, ast.Assign) else (statement.target,)
            if len(targets) != 1 or not isinstance(targets[0], ast.Name):
                continue
            target = targets[0].id
            requirement = expression(statement.value, unit.source_index)
            alternative = Alternative(
                stable_id("alternative", unit.source_index, statement.lineno,
                          statement.col_offset, statement.end_lineno, statement.end_col_offset),
                Guard(stable_id("guard", unit.source_index, statement.lineno,
                                statement.col_offset, statement.end_lineno,
                                statement.end_col_offset), True, True),
                stable_id("definition", unit.source_index, statement.lineno,
                          statement.col_offset, statement.end_lineno, statement.end_col_offset),
                requirement,
                TransformBinding("affine_linear_q.v1", "identity"),
            )
            builder.derivations[target] = Derivation(target, (alternative,))
            environments[target] = target
    result = builder.build()
    result.validate()
    return result
