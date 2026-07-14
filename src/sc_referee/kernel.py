"""Small proof-rule kernel shared by deterministic checks.

Rules in this module return arithmetic facts, never sc-referee findings or severities.  The caller owns
applicability, scientific interpretation, confirmation gates, citations, and blocker entitlement.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd


class ProofState(str, Enum):
    PROVED_VIOLATION = "proved_violation"
    PROVED_CONFORMANT = "proved_conformant"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class FunctionalDependencySpec:
    """The code-owned proposition: determinant -> at most N dependent identities."""

    determinant_columns: tuple[str, ...]
    dependent_columns: tuple[str, ...]
    max_distinct: int

    def __post_init__(self):
        if not self.determinant_columns:
            raise ValueError("functional dependency needs at least one determinant column")
        if not self.dependent_columns:
            raise ValueError("functional dependency needs at least one dependent column")
        if len(set(self.determinant_columns)) != len(self.determinant_columns):
            raise ValueError("functional dependency determinant columns must be unique")
        if len(set(self.dependent_columns)) != len(self.dependent_columns):
            raise ValueError("functional dependency dependent columns must be unique")
        if self.max_distinct < 0:
            raise ValueError("functional dependency max_distinct must be non-negative")


@dataclass(frozen=True)
class OffendingGroup:
    determinant_values: tuple[object, ...]
    distinct_dependents: int


@dataclass(frozen=True)
class ProofResult:
    state: ProofState
    violation_count: int
    offending_groups: tuple[OffendingGroup, ...]
    coverage_complete: bool
    missing_fields: tuple[str, ...] = ()
    reason: str | None = None

    def __post_init__(self):
        if self.violation_count != len(self.offending_groups):
            raise ValueError("violation_count must equal len(offending_groups)")
        if self.state is ProofState.UNRESOLVED:
            if self.coverage_complete:
                raise ValueError("an unresolved proof cannot have complete coverage")
            if self.violation_count or self.offending_groups:
                raise ValueError("an unresolved proof cannot assert violations")
        else:
            if not self.coverage_complete:
                raise ValueError("a proved result requires complete coverage")
            if self.state is ProofState.PROVED_CONFORMANT and self.violation_count:
                raise ValueError("a conformant proof cannot contain violations")
            if self.state is ProofState.PROVED_VIOLATION and not self.violation_count:
                raise ValueError("a violation proof requires at least one offending group")


class FunctionalDependencyRule:
    """Prove whether each determinant maps to at most ``max_distinct`` dependent tuples."""

    rule_id = "functional_dependency"
    rule_version = "1"

    @staticmethod
    def _unresolved(*, reason: str, missing_fields=()) -> ProofResult:
        return ProofResult(
            state=ProofState.UNRESOLVED,
            violation_count=0,
            offending_groups=(),
            coverage_complete=False,
            missing_fields=tuple(missing_fields),
            reason=reason,
        )

    def evaluate(
        self,
        table: pd.DataFrame,
        spec: FunctionalDependencySpec,
        *,
        coverage_complete: bool = True,
        coverage_reason: str | None = None,
    ) -> ProofResult:
        if not coverage_complete:
            return self._unresolved(reason=coverage_reason or "coverage_incomplete")
        if not isinstance(table, pd.DataFrame):
            return self._unresolved(reason="table_is_not_a_dataframe")

        referenced = tuple(dict.fromkeys((*spec.determinant_columns, *spec.dependent_columns)))
        missing = tuple(c for c in referenced if c not in table.columns)
        if missing:
            return self._unresolved(reason="missing_referenced_columns", missing_fields=missing)

        duplicated_labels = set(table.columns[table.columns.duplicated()])
        ambiguous = tuple(c for c in referenced if c in duplicated_labels)
        if ambiguous:
            return self._unresolved(reason="duplicate_referenced_column_labels", missing_fields=ambiguous)

        try:
            relation = table.loc[:, list(referenced)]
            if bool(relation.isna().to_numpy().any()):
                # Null policy belongs to the caller.  A generic rule must never silently choose whether
                # a null-key row creates a group or is dropped by the producing operation.
                return self._unresolved(reason="null_in_referenced_columns")

            unique_pairs = relation.drop_duplicates()
            if unique_pairs.empty:
                return ProofResult(
                    state=ProofState.PROVED_CONFORMANT,
                    violation_count=0,
                    offending_groups=(),
                    coverage_complete=True,
                )

            determinants = list(spec.determinant_columns)
            grouper = determinants[0] if len(determinants) == 1 else determinants
            counts = unique_pairs.groupby(
                grouper, observed=True, sort=False, dropna=False
            ).size()

            offending = []
            for key, count in counts.items():
                n = int(count)
                if n <= spec.max_distinct:
                    continue
                # pandas returns a scalar key for one grouper and a tuple for multiple groupers.  A
                # scalar value may itself be a tuple, so use the declared arity rather than the value's
                # runtime type or a one-column tuple identity would be flattened.
                values = key if len(determinants) > 1 else (key,)
                offending.append(OffendingGroup(tuple(values), n))
        except Exception as exc:  # pandas cannot safely identify/group one of the supplied values
            return self._unresolved(reason=f"ungroupable_values:{type(exc).__name__}")

        groups = tuple(offending)
        if groups:
            return ProofResult(
                state=ProofState.PROVED_VIOLATION,
                violation_count=len(groups),
                offending_groups=groups,
                coverage_complete=True,
            )
        return ProofResult(
            state=ProofState.PROVED_CONFORMANT,
            violation_count=0,
            offending_groups=(),
            coverage_complete=True,
        )
