from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProofObligation:
    kind: str
    subject: str


def minimize_frontier(obligations):
    return tuple(dict.fromkeys(obligations))

