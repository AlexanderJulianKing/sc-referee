"""Exact scalar intervals with widening markers."""
from __future__ import annotations

from dataclasses import dataclass
from math import inf


@dataclass(frozen=True)
class ScalarInterval:
    lower: float
    upper: float
    widened: bool = False

    def __post_init__(self):
        if self.lower > self.upper:
            raise ValueError("scalar lower bound exceeds upper bound")

    def join(self, other: "ScalarInterval") -> "ScalarInterval":
        return ScalarInterval(min(self.lower, other.lower), max(self.upper, other.upper),
                              self.widened or other.widened)

    def meet(self, other: "ScalarInterval") -> "ScalarInterval":
        return ScalarInterval(max(self.lower, other.lower), min(self.upper, other.upper),
                              self.widened or other.widened)

    def widen(self, other: "ScalarInterval") -> "ScalarInterval":
        if other.lower < self.lower or other.upper > self.upper:
            return ScalarInterval(-inf if other.lower < self.lower else self.lower,
                                  inf if other.upper > self.upper else self.upper, True)
        return ScalarInterval(self.lower, self.upper, self.widened or other.widened)

    def contains(self, other: "ScalarInterval") -> bool:
        return self.lower <= other.lower and self.upper >= other.upper
