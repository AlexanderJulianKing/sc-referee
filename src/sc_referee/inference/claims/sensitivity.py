"""The closed, non-extensible sensitivity solver set used by the must slicer."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from math import isfinite

from sc_referee.inference.domains.scalar import ScalarInterval
from sc_referee.inference.domains.unit import RelationSource, UnitRelationFact, UnitRelationKind


class SensitivitySolverKind(Enum):
    AFFINE_LINEAR_Q = "affine_linear_q.v1"
    SIGN_MONOTONE = "sign_monotone.v1"
    EXACT_SET_MEMBERSHIP = "exact_set_membership.v1"
    UNIT_PARTITION = "unit_partition.v1"
    EXACT_RATIONAL_RANK = "exact_rational_rank.v1"


CLOSED_SOLVER_IDS = frozenset(kind.value for kind in SensitivitySolverKind)


class SensitivitySolverSet:
    """Intentionally has no registration API; extending it is an architecture change."""

    @staticmethod
    def supports(solver_id: str) -> bool:
        return solver_id in CLOSED_SOLVER_IDS


def sign_monotone_sensitive(operations: tuple[str, ...], *, factor_signs: tuple[int, ...]) -> bool | None:
    sign_index = 0
    for operation in operations:
        if operation in ("identity", "negate", "strictly_increasing", "strictly_decreasing"):
            continue
        if operation in ("multiply", "divide"):
            if sign_index >= len(factor_signs) or factor_signs[sign_index] not in (-1, 1):
                return None
            sign_index += 1
            continue
        return None
    return True


def exact_set_membership_sensitive(initial_present: bool,
                                   operations: tuple[tuple[str, bool], ...]) -> bool | None:
    present = initial_present
    for operation, predicate in operations:
        if operation in ("select", "intersection"):
            present = present and predicate
        elif operation in ("remove", "difference"):
            present = present and not predicate
        elif operation == "union":
            present = present or predicate
        else:
            return None
    return present


def unit_partition_sensitive(relation: UnitRelationFact) -> bool | None:
    if not isinstance(relation, UnitRelationFact):
        return None
    if relation.source not in set(RelationSource):
        return None
    if relation.kind is UnitRelationKind.UNKNOWN:
        return None
    return True


def _fraction(value) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    raise TypeError("exact rational solver accepts integers/Fractions only")


def exact_rational_rank(matrix) -> int:
    rows = [list(map(_fraction, row)) for row in matrix]
    if not rows:
        return 0
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("matrix is not rectangular")
    rank = 0
    for column in range(width):
        pivot = next((index for index in range(rank, len(rows)) if rows[index][column] != 0), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        divisor = rows[rank][column]
        rows[rank] = [value / divisor for value in rows[rank]]
        for index, row in enumerate(rows):
            if index == rank or row[column] == 0:
                continue
            factor = row[column]
            rows[index] = [value - factor * pivot_value
                           for value, pivot_value in zip(row, rows[rank])]
        rank += 1
        if rank == len(rows):
            break
    return rank


def exact_rational_rank_sensitive(matrix, *, target_column: int) -> bool | None:
    try:
        rows = tuple(tuple(row) for row in matrix)
    except TypeError:
        return None
    if not rows or target_column < 0 or target_column >= len(rows[0]):
        return None
    without = tuple(tuple(value for index, value in enumerate(row) if index != target_column)
                    for row in rows)
    try:
        return exact_rational_rank(rows) > exact_rational_rank(without)
    except (TypeError, ValueError, IndexError):
        return None


@dataclass(frozen=True)
class LeafForm:
    producers: frozenset[str]


@dataclass(frozen=True)
class AffineForm:
    coefficients: tuple[tuple[str, Fraction], ...]
    constant: Fraction = Fraction(0)

    @classmethod
    def from_leaf(cls, leaf: LeafForm):
        return cls(tuple(sorted((producer, Fraction(1)) for producer in leaf.producers)))

    def as_dict(self):
        return dict(self.coefficients)


@dataclass(frozen=True)
class SignForm:
    producers: frozenset[str]
    parity: int = 1


@dataclass(frozen=True)
class SetMembershipForm:
    present: frozenset[str]


@dataclass(frozen=True)
class RelationForm:
    producers: frozenset[str]


@dataclass(frozen=True)
class CanonicalForm:
    solver_id: str
    payload: object


@dataclass(frozen=True)
class SolverApplication:
    status: str  # PROVED form construction | UNKNOWN
    form: CanonicalForm | None
    reason: str | None = None


def _coerce_affine(child) -> AffineForm | None:
    if isinstance(child, LeafForm):
        return AffineForm.from_leaf(child)
    if isinstance(child, CanonicalForm) and child.solver_id == SensitivitySolverKind.AFFINE_LINEAR_Q.value:
        return child.payload
    return None


def _sum_affine(forms, signs=None):
    coefficients = {}
    constant = Fraction(0)
    signs = signs or [1] * len(forms)
    for form, sign in zip(forms, signs):
        constant += sign * form.constant
        for producer, coefficient in form.coefficients:
            coefficients[producer] = coefficients.get(producer, Fraction(0)) + sign * coefficient
    return AffineForm(tuple(sorted((producer, coefficient) for producer, coefficient in coefficients.items()
                                   if coefficient != 0)), constant)


def _exact_factor(value):
    if isinstance(value, (int, Fraction)):
        return _fraction(value)
    if isinstance(value, ScalarInterval) and value.lower == value.upper and isfinite(value.lower):
        if isinstance(value.lower, int):
            return Fraction(value.lower, 1)
    return None


def apply_transform(transform, children: tuple[LeafForm | CanonicalForm, ...]) -> SolverApplication:
    solver_id = transform.solver_id
    if solver_id not in CLOSED_SOLVER_IDS or not transform.certified:
        return SolverApplication("UNKNOWN", None, "non_closed_or_uncertified_transform")
    child_solvers = {child.solver_id for child in children if isinstance(child, CanonicalForm)}
    if any(child_solver != solver_id for child_solver in child_solvers):
        return SolverApplication("UNKNOWN", None, "mixed_solver_algebras_without_verified_bridge")

    operation = transform.operation
    if solver_id == SensitivitySolverKind.AFFINE_LINEAR_Q.value:
        forms = tuple(_coerce_affine(child) for child in children)
        if any(form is None for form in forms):
            return SolverApplication("UNKNOWN", None, "affine_input_outside_solver")
        if operation == "identity" and len(forms) == 1:
            result = forms[0]
        elif operation == "negate" and len(forms) == 1:
            result = _sum_affine(forms, [-1])
        elif operation == "add":
            result = _sum_affine(forms)
        elif operation == "subtract" and len(forms) == 2:
            result = _sum_affine(forms, [1, -1])
        elif operation in ("scale", "multiply") and len(forms) == 1:
            factor = _exact_factor(transform.parameter("factor"))
            if factor is None:
                return SolverApplication("UNKNOWN", None, "multiplier_not_exact_nonzero_rational")
            result = AffineForm(tuple((producer, coefficient * factor)
                                      for producer, coefficient in forms[0].coefficients
                                      if coefficient * factor != 0),
                                forms[0].constant * factor)
        else:
            return SolverApplication("UNKNOWN", None, "unsupported_affine_operation")
        return SolverApplication("PROVED", CanonicalForm(solver_id, result))

    if solver_id == SensitivitySolverKind.SIGN_MONOTONE.value:
        forms = []
        for child in children:
            if isinstance(child, LeafForm):
                forms.append(SignForm(child.producers))
            elif isinstance(child, CanonicalForm) and child.solver_id == solver_id:
                forms.append(child.payload)
            else:
                return SolverApplication("UNKNOWN", None, "sign_input_outside_solver")
        if len(forms) != 1:
            return SolverApplication("UNKNOWN", None, "sign_solver_requires_unary_path")
        parity = forms[0].parity
        if operation in ("negate", "strictly_decreasing"):
            parity *= -1
        elif operation in ("identity", "strictly_increasing"):
            pass
        elif operation in ("multiply", "divide"):
            factor_sign = transform.parameter("factor_sign")
            if factor_sign not in (-1, 1):
                return SolverApplication("UNKNOWN", None, "factor_sign_not_fixed_nonzero")
            parity *= factor_sign
        else:
            return SolverApplication("UNKNOWN", None, "unsupported_sign_operation")
        return SolverApplication("PROVED", CanonicalForm(solver_id,
                                                          SignForm(forms[0].producers, parity)))

    if solver_id == SensitivitySolverKind.EXACT_SET_MEMBERSHIP.value:
        if len(children) != 1:
            return SolverApplication("UNKNOWN", None, "set_solver_requires_unary_path")
        child = children[0]
        if isinstance(child, LeafForm):
            present = child.producers
        elif isinstance(child, CanonicalForm) and child.solver_id == solver_id:
            present = child.payload.present
        else:
            return SolverApplication("UNKNOWN", None, "set_input_outside_solver")
        members = transform.parameter("members", frozenset())
        if operation in ("select", "intersection"):
            present = present & frozenset(members)
        elif operation in ("remove", "difference"):
            present = present - frozenset(members)
        elif operation == "union":
            present = present | frozenset(members)
        elif operation == "identity":
            pass
        else:
            return SolverApplication("UNKNOWN", None, "unknown_or_unsupported_set_predicate")
        return SolverApplication("PROVED", CanonicalForm(solver_id, SetMembershipForm(present)))

    if solver_id == SensitivitySolverKind.UNIT_PARTITION.value:
        relation = transform.parameter("relation")
        if unit_partition_sensitive(relation) is not True:
            return SolverApplication("UNKNOWN", None, "unit_relation_unproved")
        producers = frozenset().union(*(
            child.producers if isinstance(child, LeafForm) else child.payload.producers
            for child in children))
        return SolverApplication("PROVED", CanonicalForm(solver_id, RelationForm(producers)))

    if solver_id == SensitivitySolverKind.EXACT_RATIONAL_RANK.value:
        sensitive = exact_rational_rank_sensitive(transform.parameter("matrix"),
                                                   target_column=transform.parameter("target_column"))
        if sensitive is None:
            return SolverApplication("UNKNOWN", None, "rank_input_unsupported")
        producers = frozenset().union(*(
            child.producers if isinstance(child, LeafForm) else child.payload.producers
            for child in children)) if sensitive else frozenset()
        return SolverApplication("PROVED", CanonicalForm(solver_id, RelationForm(producers)))

    return SolverApplication("UNKNOWN", None, "solver_not_closed")


def form_sensitive(form: CanonicalForm, producer: str) -> bool | None:
    payload = form.payload
    if isinstance(payload, AffineForm):
        return payload.as_dict().get(producer, Fraction(0)) != 0
    if isinstance(payload, (SignForm, RelationForm)):
        return producer in payload.producers
    if isinstance(payload, SetMembershipForm):
        return producer in payload.present
    return None
