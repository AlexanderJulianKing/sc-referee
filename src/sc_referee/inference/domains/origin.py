from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class OriginAtom:
    kind: str
    identity: str
    field: str | None = None


def unknown_origin(boundary_id: str):
    return OriginAtom("unknown", boundary_id)

