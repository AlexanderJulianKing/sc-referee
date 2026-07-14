"""Fitted-state identity; must facts require an exact fitted-state summary."""
from __future__ import annotations

from dataclasses import dataclass

from sc_referee.inference.domains.bilattice import MayMust
from sc_referee.inference.contracts.schema import binding_is_exact


@dataclass(frozen=True)
class FittedState:
    id: str
    training_values: tuple[str, ...]
    features: tuple[str, ...]
    parameters: tuple[str, ...]


@dataclass(frozen=True)
class UnknownFittedState:
    fitted_state_id: str


def infer_fitted_state(state: FittedState, *, binding) -> MayMust:
    if binding_is_exact(binding):
        return MayMust(frozenset({state}), frozenset({state}))
    unknown = UnknownFittedState(state.id)
    return MayMust(frozenset({state, unknown}), frozenset())
