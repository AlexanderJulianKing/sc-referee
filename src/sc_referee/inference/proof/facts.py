from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RatifiedFact:
    fact_id: str
    predicate: str
    fact_digest: str

