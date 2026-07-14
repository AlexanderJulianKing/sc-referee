from __future__ import annotations

from dataclasses import dataclass

from sc_referee.inference.domains.bilattice import MayMust


@dataclass(frozen=True)
class AbsValue:
    points_to: frozenset[str] = frozenset()
    origins: frozenset[object] = frozenset()
    literals: frozenset[object] = frozenset()
    unknown: bool = False
    must_points_to: frozenset[str] = frozenset()
    must_origins: frozenset[object] = frozenset()
    region: object | None = None
    units: MayMust = MayMust(frozenset(), frozenset())
    calibration: object | None = None
    selection_events: MayMust = MayMust(frozenset(), frozenset())
    fitted_states: MayMust = MayMust(frozenset(), frozenset())
    scalar: object | None = None
    effects: tuple[object, ...] = ()
    widened_facets: frozenset[str] = frozenset()

    def __post_init__(self):
        if not self.must_points_to <= self.points_to:
            raise ValueError("must points-to locations must be possible")
        if not self.must_origins <= self.origins:
            raise ValueError("must origins must be possible")

    def join(self, other: "AbsValue") -> "AbsValue":
        region = self.region.join(other.region) if self.region is not None and other.region is not None else None
        scalar = self.scalar.join(other.scalar) if self.scalar is not None and other.scalar is not None else None
        return AbsValue(
            points_to=self.points_to | other.points_to,
            origins=self.origins | other.origins,
            literals=self.literals | other.literals,
            unknown=self.unknown or other.unknown,
            must_points_to=self.must_points_to & other.must_points_to,
            must_origins=self.must_origins & other.must_origins,
            region=region,
            units=self.units.join(other.units),
            calibration=self.calibration if self.calibration == other.calibration else None,
            selection_events=self.selection_events.join(other.selection_events),
            fitted_states=self.fitted_states.join(other.fitted_states),
            scalar=scalar,
            effects=self.effects + other.effects,
            widened_facets=self.widened_facets | other.widened_facets,
        )

    def widen(self, other: "AbsValue") -> "AbsValue":
        joined = self.join(other)
        points_grew = not other.points_to <= self.points_to
        region = (self.region.widen(other.region)
                  if self.region is not None and other.region is not None else None)
        scalar = (self.scalar.widen(other.scalar)
                  if self.scalar is not None and other.scalar is not None else None)
        facets = set(joined.widened_facets)
        points_to = joined.points_to
        if points_grew:
            points_to = points_to | {"<unknown-heap>"}
            facets.add("points_to")
        if region is not None and getattr(region, "widened", False):
            facets.add("region")
        if scalar is not None and getattr(scalar, "widened", False):
            facets.add("scalar")
        return AbsValue(
            points_to=frozenset(points_to), origins=joined.origins, literals=joined.literals,
            unknown=joined.unknown or points_grew, must_points_to=joined.must_points_to,
            must_origins=joined.must_origins, region=region, units=joined.units,
            calibration=joined.calibration, selection_events=joined.selection_events,
            fitted_states=joined.fitted_states, scalar=scalar, effects=joined.effects,
            widened_facets=frozenset(facets),
        )
