"""Rich refinement/effect types inferred from abstract facts, never names."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from sc_referee.inference.domains.bilattice import MayMust


class Statistic(Enum):
    MEAN_DIFFERENCE = "MeanDifference"
    RANK_STATISTIC = "RankStatistic"
    WALD = "Wald"
    SCORE = "Score"
    LIKELIHOOD_RATIO = "LikelihoodRatio"
    HYPERGEOMETRIC_TAIL = "HypergeometricTail"
    CORRELATION = "Correlation"
    PERMUTATION = "Permutation"
    CUSTOM = "Custom"


class SamplingRegime(Enum):
    IID_ROWS = "IIDRows"
    PAIRED = "Paired"
    CLUSTERED = "Clustered"
    BLOCKED = "Blocked"
    RESTRICTED_PERMUTATION = "RestrictedPermutation"
    POPULATION_AGGREGATE = "PopulationAggregate"
    UNKNOWN = "Unknown"


@dataclass(frozen=True)
class DependenceModel:
    kind: str
    unit: object | None = None
    region: object | None = None


@dataclass(frozen=True)
class NullContract:
    family: str
    assumptions: frozenset[str] = frozenset()


class BindingStatus(Enum):
    EXACT = "exact"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class GroupingType:
    value_id: str
    origin: MayMust
    selection_events: MayMust
    rows: object
    patients: object
    time: object
    features: object
    unit: MayMust


@dataclass(frozen=True)
class TestType:
    statistic: Statistic
    null: NullContract
    sampling_regime: SamplingRegime
    dependence_model: DependenceModel
    response: str
    grouping_or_design: str | None
    block: str | None
    selection_events: MayMust
    summary_binding: object


@dataclass(frozen=True)
class PValueType:
    calibration: object
    assumptions: frozenset[str]
    test: str


@dataclass(frozen=True)
class ReportClaimType:
    claim_id: str
    role: str
    value: str
    possible_producers: frozenset[object]
    unavoidable_producers: frozenset[str]
    report_binding: BindingStatus


@dataclass(frozen=True)
class RefinementIndex:
    groupings: Mapping[str, GroupingType] = field(default_factory=dict)
    tests: Mapping[str, TestType] = field(default_factory=dict)
    pvalues: Mapping[str, PValueType] = field(default_factory=dict)
    report_claims: Mapping[str, ReportClaimType] = field(default_factory=dict)

