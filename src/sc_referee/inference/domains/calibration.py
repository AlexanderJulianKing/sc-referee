"""Calibration modes that never infer naivety from absence of a safeguard."""
from __future__ import annotations

from dataclasses import dataclass

from sc_referee.inference.domains.bilattice import MayMust
from sc_referee.inference.contracts.schema import binding_is_exact


@dataclass(frozen=True)
class Naive:
    contract_id: str


@dataclass(frozen=True)
class Valid:
    contract_id: str
    assumptions: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Descriptive:
    contract_id: str


@dataclass(frozen=True)
class UnknownCalibration:
    boundary_id: str


@dataclass(frozen=True)
class CalibrationValue:
    modes: MayMust
    nulls: MayMust = MayMust(frozenset(), frozenset())
    regimes: MayMust = MayMust(frozenset(), frozenset())
    dependence_models: MayMust = MayMust(frozenset(), frozenset())


def infer_calibration(*, contract_id: str, handling: str | None, binding) -> CalibrationValue:
    if not binding_is_exact(binding):
        unknown = UnknownCalibration(f"calibration:{contract_id}")
        return CalibrationValue(MayMust(frozenset({unknown}), frozenset()))
    if handling == "naive":
        mode = Naive(contract_id)
    elif handling == "valid":
        mode = Valid(contract_id)
    elif handling == "descriptive":
        mode = Descriptive(contract_id)
    else:
        unknown = UnknownCalibration(f"calibration:{contract_id}:summary_incomplete")
        return CalibrationValue(MayMust(frozenset({unknown}), frozenset()))
    return CalibrationValue(MayMust(frozenset({mode}), frozenset({mode})))
