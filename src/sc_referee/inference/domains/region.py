"""Closed symbolic set algebra and lower/upper region bounds."""
from __future__ import annotations

from dataclasses import dataclass


class SetExpr:
    axis: str

    def is_empty(self) -> bool:
        value = normalize(self)
        return isinstance(value, Empty) or (isinstance(value, Exact) and not value.ids)


@dataclass(frozen=True)
class Empty(SetExpr):
    axis: str


@dataclass(frozen=True)
class All(SetExpr):
    axis: str


@dataclass(frozen=True)
class Exact(SetExpr):
    axis: str
    ids: frozenset[object]


@dataclass(frozen=True)
class FieldEquals(SetExpr):
    axis: str
    field: str
    value: object


@dataclass(frozen=True)
class Union(SetExpr):
    left: SetExpr
    right: SetExpr

    @property
    def axis(self):
        return self.left.axis


@dataclass(frozen=True)
class Intersection(SetExpr):
    left: SetExpr
    right: SetExpr

    @property
    def axis(self):
        return self.left.axis


@dataclass(frozen=True)
class Difference(SetExpr):
    left: SetExpr
    right: SetExpr

    @property
    def axis(self):
        return self.left.axis


@dataclass(frozen=True)
class Image(SetExpr):
    relation: str
    expression: SetExpr
    axis: str


@dataclass(frozen=True)
class Preimage(SetExpr):
    relation: str
    expression: SetExpr
    axis: str


@dataclass(frozen=True)
class Unknown(SetExpr):
    axis: str
    boundary_id: str


def _same_axis(left: SetExpr, right: SetExpr) -> None:
    if left.axis != right.axis:
        raise ValueError(f"set axes differ: {left.axis!r} vs {right.axis!r}")


def _ordered(left: SetExpr, right: SetExpr):
    return (left, right) if repr(left) <= repr(right) else (right, left)


def normalize(expression: SetExpr) -> SetExpr:
    if isinstance(expression, Union):
        left, right = normalize(expression.left), normalize(expression.right)
        _same_axis(left, right)
        if left == right:
            return left
        if isinstance(left, Empty):
            return right
        if isinstance(right, Empty):
            return left
        if isinstance(left, All) or isinstance(right, All):
            return All(left.axis)
        if isinstance(left, Exact) and isinstance(right, Exact):
            return Exact(left.axis, left.ids | right.ids)
        return Union(*_ordered(left, right))
    if isinstance(expression, Intersection):
        left, right = normalize(expression.left), normalize(expression.right)
        _same_axis(left, right)
        if left == right:
            return left
        if isinstance(left, Empty) or isinstance(right, Empty):
            return Empty(left.axis)
        if isinstance(left, All):
            return right
        if isinstance(right, All):
            return left
        if isinstance(left, Exact) and isinstance(right, Exact):
            return Exact(left.axis, left.ids & right.ids)
        return Intersection(*_ordered(left, right))
    if isinstance(expression, Difference):
        left, right = normalize(expression.left), normalize(expression.right)
        _same_axis(left, right)
        if isinstance(left, Empty) or left == right:
            return Empty(left.axis)
        if isinstance(right, Empty):
            return left
        if isinstance(left, Exact) and isinstance(right, Exact):
            return Exact(left.axis, left.ids - right.ids)
        return Difference(left, right)
    return expression


def _proved_subset(left: SetExpr, right: SetExpr) -> bool | None:
    left, right = normalize(left), normalize(right)
    _same_axis(left, right)
    if isinstance(left, Empty) or isinstance(right, All) or left == right:
        return True
    if isinstance(left, Exact) and isinstance(right, Exact):
        return left.ids <= right.ids
    if isinstance(right, Empty):
        return left.is_empty()
    return None


@dataclass(frozen=True)
class SetBounds:
    lower: SetExpr
    upper: SetExpr
    boundaries: frozenset[str] = frozenset()

    def __post_init__(self):
        _same_axis(self.lower, self.upper)
        subset = _proved_subset(self.lower, self.upper)
        if subset is False:
            raise ValueError("region lower bound is not contained in upper bound")

    @classmethod
    def exact(cls, axis: str, ids) -> "SetBounds":
        expression = Exact(axis, frozenset(ids))
        return cls(expression, expression)

    @classmethod
    def dynamic(cls, axis: str, boundary_id: str) -> "SetBounds":
        # Unknown is retained in the boundary/proof frontier; [Empty, All] is its set meaning.
        return cls(Empty(axis), All(axis), frozenset({boundary_id}))

    def join(self, other: "SetBounds") -> "SetBounds":
        return SetBounds(normalize(Intersection(self.lower, other.lower)),
                         normalize(Union(self.upper, other.upper)),
                         self.boundaries | other.boundaries)

    def refine(self, other: "SetBounds") -> "SetBounds":
        return SetBounds(normalize(Union(self.lower, other.lower)),
                         normalize(Intersection(self.upper, other.upper)),
                         self.boundaries | other.boundaries)

    meet = refine

    def widen(self, other: "SetBounds") -> "SetBounds":
        if self == other:
            return self
        return SetBounds(Empty(self.lower.axis), All(self.upper.axis),
                         self.boundaries | other.boundaries | {f"widened:{self.lower.axis}"})


def overlap_relation(left: SetBounds, right: SetBounds) -> str:
    if normalize(Intersection(left.upper, right.upper)).is_empty():
        return "disjoint"
    lower_overlap = normalize(Intersection(left.lower, right.lower))
    if not lower_overlap.is_empty() and isinstance(lower_overlap, Exact):
        return "definite_overlap"
    return "unknown"


def patient_bounds_from_rows(rows: SetBounds, relation_id: str, *,
                             exact: bool, ratified: bool) -> SetBounds:
    if not (exact or ratified):
        return SetBounds.dynamic("patients", f"unproved-patient-map:{relation_id}")
    return SetBounds(Image(relation_id, rows.lower, "patients"),
                     Image(relation_id, rows.upper, "patients"), rows.boundaries)


@dataclass(frozen=True)
class Region:
    rows: SetBounds
    patients: SetBounds
    time: SetBounds
    features: SetBounds
    widened: bool = False

    def join(self, other: "Region") -> "Region":
        return Region(self.rows.join(other.rows), self.patients.join(other.patients),
                      self.time.join(other.time), self.features.join(other.features),
                      self.widened or other.widened)

    def refine(self, other: "Region") -> "Region":
        return Region(self.rows.refine(other.rows), self.patients.refine(other.patients),
                      self.time.refine(other.time), self.features.refine(other.features),
                      self.widened or other.widened)

    meet = refine

    def widen(self, other: "Region") -> "Region":
        if self == other:
            return self
        return Region(self.rows.widen(other.rows), self.patients.widen(other.patients),
                      self.time.widen(other.time), self.features.widen(other.features), True)
