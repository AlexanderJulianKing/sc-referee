"""Refinement inference from interpreter facts and exact summaries only."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from sc_referee.inference.claims.inventory import ReportClaim
from sc_referee.inference.claims.slice import ClaimSlice
from sc_referee.inference.contracts.schema import SummaryBinding, binding_is_exact
from sc_referee.inference.domains.bilattice import MayMust
from sc_referee.inference.domains.calibration import (
    CalibrationValue, UnknownCalibration, Valid, infer_calibration,
)
from sc_referee.inference.domains.origin import OriginAtom
from sc_referee.inference.domains.region import Exact, Region, SetBounds
from sc_referee.inference.domains.selection import UnknownSelection
from sc_referee.inference.domains.unit import UnitRef
from sc_referee.inference.domains.value import AbsValue
from sc_referee.inference.refinement.types import (
    BindingStatus, DependenceModel, GroupingType, NullContract, PValueType, RefinementIndex,
    ReportClaimType, SamplingRegime, Statistic, TestType,
)
from sc_referee.sinks import ValueType


@dataclass(frozen=True)
class TestSummary:
    binding: SummaryBinding
    statistic: Statistic
    null: NullContract
    sampling_regime: SamplingRegime
    dependence_model: DependenceModel
    calibration_handling: str | None


@dataclass(frozen=True)
class VerifiedSafeguard:
    safeguard_id: str
    binding: SummaryBinding
    handling: str
    assumptions: frozenset[str] = frozenset()


@dataclass(frozen=True)
class RefinementFacts:
    grouping_values: Mapping[str, AbsValue] = field(default_factory=dict)
    test_facts: Mapping[str, tuple] = field(default_factory=dict)
    pvalue_facts: Mapping[str, tuple] = field(default_factory=dict)
    report_facts: Mapping[str, tuple[ReportClaim, ClaimSlice]] = field(default_factory=dict)


def _unknown_region(value_id: str) -> Region:
    return Region(
        SetBounds.dynamic("rows", f"grouping:{value_id}:rows"),
        SetBounds.dynamic("patients", f"grouping:{value_id}:patients"),
        SetBounds.dynamic("time", f"grouping:{value_id}:time"),
        SetBounds.dynamic("features", f"grouping:{value_id}:features"),
    )


def infer_grouping_type(value: AbsValue, *, value_id: str,
                        source_name: str | None = None) -> GroupingType:
    # source_name is accepted only to make the invariant testable; it is intentionally never read.
    if value.origins:
        origins = MayMust(value.origins, value.must_origins)
    else:
        unknown = OriginAtom("unknown", f"grouping:{value_id}")
        origins = MayMust(frozenset({unknown}), frozenset())
    if value.selection_events.may:
        selections = value.selection_events
    else:
        unknown_selection = UnknownSelection(f"grouping:{value_id}", "selection_summary_unavailable")
        selections = MayMust(frozenset({unknown_selection}), frozenset())
    if value.units.may:
        units = value.units
    else:
        unknown_unit = UnitRef("<unknown>", (), "unknown", "unknown")
        units = MayMust(frozenset({unknown_unit}), frozenset())
    region = value.region or _unknown_region(value_id)
    return GroupingType(value_id, origins, selections, region.rows, region.patients,
                        region.time, region.features, units)


def infer_test_type(summary: TestSummary | None, *, response: str,
                    grouping_or_design: str | None, block: str | None,
                    selection_events: MayMust | None,
                    candidate_symbol: str | None = None) -> TestType | None:
    # Candidate syntax/name is not evidence. Only a complete exact summary creates TestType.
    if summary is None or not binding_is_exact(summary.binding):
        return None
    selections = selection_events
    if selections is None:
        unknown = UnknownSelection(f"test:{response}", "selection_inputs_unknown")
        selections = MayMust(frozenset({unknown}), frozenset())
    return TestType(summary.statistic, summary.null, summary.sampling_regime,
                    summary.dependence_model, response, grouping_or_design, block,
                    selections, summary.binding)


def infer_pvalue_type(test: TestType | None, summary: TestSummary | None, *,
                      test_event_id: str, safeguards: tuple[VerifiedSafeguard, ...]) -> PValueType:
    exact_safeguards = tuple(item for item in safeguards if binding_is_exact(item.binding))
    if exact_safeguards:
        safeguard = exact_safeguards[0]
        if safeguard.handling == "valid":
            mode = Valid(safeguard.safeguard_id, safeguard.assumptions)
            calibration = CalibrationValue(MayMust(frozenset({mode}), frozenset({mode})))
            return PValueType(calibration, safeguard.assumptions, test_event_id)
    if test is not None and summary is not None and binding_is_exact(summary.binding):
        calibration = infer_calibration(contract_id=summary.binding.symbol,
                                        handling=summary.calibration_handling,
                                        binding=summary.binding)
        return PValueType(calibration, frozenset(), test_event_id)
    unknown = UnknownCalibration(f"pvalue:{test_event_id}")
    return PValueType(CalibrationValue(MayMust(frozenset({unknown}), frozenset())),
                      frozenset(), test_event_id)


def infer_report_claim_type(claim: ReportClaim, claim_slice: ClaimSlice) -> ReportClaimType:
    exact = claim.root_exact
    return ReportClaimType(
        claim.claim_id, claim.role, claim.value, claim_slice.possible_producers,
        claim_slice.unavoidable_producers if exact else frozenset(),
        BindingStatus.EXACT if exact else BindingStatus.UNKNOWN,
    )


_ORIGIN_PROJECTION = {
    "primary_data": "primary_data", "metadata": "metadata", "external": "external",
    "selection": "selected", "artifact_read": "external", "config": "metadata",
    "literal": "metadata", "unknown": "unknown",
}


def _exact_ids(bounds):
    if isinstance(bounds.lower, Exact) and bounds.lower == bounds.upper:
        return frozenset(bounds.lower.ids)
    return None


def project_value_type(grouping: GroupingType) -> ValueType:
    projected_origins = frozenset(_ORIGIN_PROJECTION.get(getattr(origin, "kind", "unknown"), "unknown")
                                  for origin in grouping.origin.may) or frozenset({"unknown"})
    unit = "unknown"
    exact_units = grouping.unit.must or grouping.unit.may
    if len(exact_units) == 1:
        unit = next(iter(exact_units)).kind
    artifact_ids = {getattr(origin, "identity", None) for origin in grouping.origin.must
                    if getattr(origin, "identity", None)}
    return ValueType(
        kind="labels", unit=unit, origins=projected_origins,
        artifact_id=next(iter(artifact_ids)) if len(artifact_ids) == 1 else None,
        feature_set=_exact_ids(grouping.features), observation_set=_exact_ids(grouping.rows),
    )


def infer_refinements(facts: RefinementFacts) -> RefinementIndex:
    groupings = {value_id: infer_grouping_type(value, value_id=value_id)
                 for value_id, value in facts.grouping_values.items()}
    tests = {}
    for event_id, arguments in facts.test_facts.items():
        inferred = infer_test_type(*arguments)
        if inferred is not None:
            tests[event_id] = inferred
    pvalues = {event_id: infer_pvalue_type(*arguments) for event_id, arguments in facts.pvalue_facts.items()}
    report_claims = {claim_id: infer_report_claim_type(*arguments)
                     for claim_id, arguments in facts.report_facts.items()}
    return RefinementIndex(groupings, tests, pvalues, report_claims)
