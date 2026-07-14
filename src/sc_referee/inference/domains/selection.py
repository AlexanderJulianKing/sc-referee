"""Evidence-gated selection events."""
from __future__ import annotations

from dataclasses import dataclass

from sc_referee.inference.domains.bilattice import MayMust
from sc_referee.inference.contracts.schema import binding_is_exact


@dataclass(frozen=True)
class SelectionEvent:
    id: str
    kind: str
    inputs: tuple[str, ...]
    output: str
    rows: object | None = None
    patients: object | None = None
    time: object | None = None
    features: object | None = None
    handling: object | None = None
    summary_binding: object | None = None


@dataclass(frozen=True)
class UnknownSelection:
    event_id: str
    reason: str


def infer_selection_event(event: SelectionEvent, *, method_name: str,
                          binding, ratified: bool) -> MayMust:
    if binding_is_exact(binding) or ratified:
        return MayMust(frozenset({event}), frozenset({event}))
    unknown = UnknownSelection(event.id, f"method_name_{method_name}_is_not_a_summary")
    return MayMust(frozenset({unknown}), frozenset())
