from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Generic, TypeVar

A = TypeVar("A")


@dataclass(frozen=True)
class MayMust(Generic[A]):
    may: FrozenSet[A]
    must: FrozenSet[A]

    def __post_init__(self):
        if not self.must <= self.may:
            raise ValueError("must facts must be a subset of may facts")

    def join(self, other: "MayMust[A]") -> "MayMust[A]":
        return MayMust(self.may | other.may, self.must & other.must)

    def refine(self, other: "MayMust[A]") -> "MayMust[A]":
        return MayMust(self.may & other.may, self.must | other.must)

    def meet(self, other: "MayMust[A]") -> "MayMust[A]":
        """Evidence meet. Contradictory evidence raises via the invariant."""
        return self.refine(other)

    def leq(self, other: "MayMust[A]") -> bool:
        """Precision order: ``self`` is at least as precise as ``other``."""
        return self.may <= other.may and self.must >= other.must

    def add_possible(self, atom: A) -> "MayMust[A]":
        return MayMust(self.may | {atom}, self.must)

    def widen(self, other: "MayMust[A]", unknown_atom: A) -> "MayMust[A]":
        """Lose may precision and must certainty; never create a must fact."""
        return MayMust(self.may | other.may | {unknown_atom}, self.must & other.must)


def unknown(atom):
    return MayMust(frozenset({atom}), frozenset())
