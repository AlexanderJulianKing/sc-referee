"""Pure, sound-over-complete matrix-version and shared-ancestry algebra.

This module deliberately knows nothing about Python syntax, engine state, policy, or
witnesses.  Callers must supply exact abstract versions, feasibility inventories,
derivation edges, and joint-coordinate influence bounds.  Every affirmative result
is guarded by the full MV-0 proof conjunction; all other cases abstain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from itertools import product
import json
from typing import FrozenSet, Iterable

from sc_referee.inference.domains.region import Exact, SetBounds, overlap_relation


_VERSION_SCHEMA = "sc-referee.statistical-matrix-version.v1"
_TRANSITION_SCHEMA = "sc-referee.derivation-transition.v1"
_EDGE_SCHEMA = "sc-referee.derivation-edge.v1"
_JOINT_AXIS = "joint-row-feature-coordinate"


def _domain_hash(schema: str, payload: dict[str, object]) -> str:
    canonical = json.dumps(
        {"schema": schema, **payload}, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return sha256((schema + "\0" + canonical).encode("utf-8")).hexdigest()


def _require_nonempty_string(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a nonempty string")


class ComponentKind(str, Enum):
    X = "X"
    RAW_X = "RAW_X"
    LAYER = "LAYER"
    OBSM = "OBSM"
    OBSP = "OBSP"
    VAR_SELECTOR = "VAR_SELECTOR"
    OBS_LABEL = "OBS_LABEL"
    UNS_RESULT = "UNS_RESULT"
    EPHEMERAL_MATRIX = "EPHEMERAL_MATRIX"


@dataclass(frozen=True, order=True)
class ComponentRef:
    heap_location: str
    kind: ComponentKind
    key: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty_string(self.heap_location, "heap_location")
        if not isinstance(self.kind, ComponentKind):
            raise TypeError("kind must be a ComponentKind")
        if self.key is not None:
            _require_nonempty_string(self.key, "key")


class MeasurementDigestKind(str, Enum):
    CONTENT = "CONTENT"
    RECIPE = "RECIPE"


class EvidenceKind(str, Enum):
    CANONICAL_ARTIFACT = "CANONICAL_ARTIFACT"
    INSTRUMENTED_SNAPSHOT = "INSTRUMENTED_SNAPSHOT"


@dataclass(frozen=True)
class StatisticalMatrixVersion:
    root_artifact_digest: str
    row_identity_digest: str
    feature_identity_digest: str
    measurement_value_digest: str
    noise_unit_digest: str
    transform_lineage_digest: str
    measurement_digest_kind: MeasurementDigestKind
    evidence_kind: EvidenceKind
    version_id: str = field(init=False)

    def __post_init__(self) -> None:
        digest_fields = (
            "root_artifact_digest",
            "row_identity_digest",
            "feature_identity_digest",
            "measurement_value_digest",
            "noise_unit_digest",
            "transform_lineage_digest",
        )
        for field_name in digest_fields:
            _require_nonempty_string(getattr(self, field_name), field_name)
        if not isinstance(self.measurement_digest_kind, MeasurementDigestKind):
            raise TypeError("measurement_digest_kind must be a MeasurementDigestKind")
        if not isinstance(self.evidence_kind, EvidenceKind):
            raise TypeError("evidence_kind must be an EvidenceKind")
        payload = {field_name: getattr(self, field_name) for field_name in digest_fields}
        payload.update(
            measurement_digest_kind=self.measurement_digest_kind.value,
            evidence_kind=self.evidence_kind.value,
        )
        object.__setattr__(self, "version_id", _domain_hash(_VERSION_SCHEMA, payload))


@dataclass(frozen=True, order=True)
class VersionBoundary:
    boundary_id: str

    def __post_init__(self) -> None:
        _require_nonempty_string(self.boundary_id, "boundary_id")


@dataclass(frozen=True)
class GuardedVersion:
    guard_id: str
    version: StatisticalMatrixVersion

    def __post_init__(self) -> None:
        _require_nonempty_string(self.guard_id, "guard_id")
        if not isinstance(self.version, StatisticalMatrixVersion):
            raise TypeError("version must be a StatisticalMatrixVersion")


@dataclass(frozen=True)
class VersionValue:
    alternatives: FrozenSet[GuardedVersion] = frozenset()
    unknown_boundaries: FrozenSet[VersionBoundary] = frozenset()

    def __post_init__(self) -> None:
        if any(not isinstance(item, GuardedVersion) for item in self.alternatives):
            raise TypeError("alternatives must contain GuardedVersion values")
        if any(not isinstance(item, VersionBoundary) for item in self.unknown_boundaries):
            raise TypeError("unknown_boundaries must contain VersionBoundary values")

    def join(self, other: "VersionValue") -> "VersionValue":
        return VersionValue(
            self.alternatives | other.alternatives,
            self.unknown_boundaries | other.unknown_boundaries,
        )


class ImmediateVersionRelation(str, Enum):
    SAME_VERSION = "SAME_VERSION"
    DIFFERENT_VERSION = "DIFFERENT_VERSION"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class VersionPairInventory:
    pairs: FrozenSet[tuple[GuardedVersion, GuardedVersion]]
    complete: bool = True
    unknown_boundaries: FrozenSet[VersionBoundary] = frozenset()

    def __post_init__(self) -> None:
        for pair in self.pairs:
            if (
                not isinstance(pair, tuple)
                or len(pair) != 2
                or not all(isinstance(item, GuardedVersion) for item in pair)
            ):
                raise TypeError("pairs must contain two-GuardedVersion tuples")
        if not isinstance(self.complete, bool):
            raise TypeError("complete must be bool")
        if any(not isinstance(item, VersionBoundary) for item in self.unknown_boundaries):
            raise TypeError("unknown_boundaries must contain VersionBoundary values")

    @classmethod
    def cartesian(cls, left: VersionValue, right: VersionValue) -> "VersionPairInventory":
        return cls(
            frozenset(product(left.alternatives, right.alternatives)),
            complete=True,
            unknown_boundaries=left.unknown_boundaries | right.unknown_boundaries,
        )

    @classmethod
    def from_feasibility(
        cls,
        left: VersionValue,
        right: VersionValue,
        *,
        feasible_pairs: Iterable[tuple[GuardedVersion, GuardedVersion]],
        feasibility_complete: bool,
        boundary_id: str = "incomplete-feasibility",
    ) -> "VersionPairInventory":
        cartesian_pairs = frozenset(product(left.alternatives, right.alternatives))
        boundaries = left.unknown_boundaries | right.unknown_boundaries
        if not feasibility_complete:
            # A partial solver result is not negative evidence.  Retain every pair.
            return cls(
                cartesian_pairs,
                complete=False,
                unknown_boundaries=boundaries | {VersionBoundary(boundary_id)},
            )
        pairs = frozenset(feasible_pairs)
        if not pairs <= cartesian_pairs:
            raise ValueError("feasible pairs must come from the alternatives' Cartesian product")
        return cls(pairs, complete=True, unknown_boundaries=boundaries)


def compare_immediate_versions(inventory: VersionPairInventory) -> ImmediateVersionRelation:
    if not inventory.complete or inventory.unknown_boundaries or not inventory.pairs:
        return ImmediateVersionRelation.UNKNOWN
    equalities = {
        left.version.version_id == right.version.version_id for left, right in inventory.pairs
    }
    if equalities == {True}:
        return ImmediateVersionRelation.SAME_VERSION
    if equalities == {False}:
        return ImmediateVersionRelation.DIFFERENT_VERSION
    return ImmediateVersionRelation.UNKNOWN


class JointOverlap(str, Enum):
    DEFINITE_OVERLAP = "DEFINITE_OVERLAP"
    DISJOINT = "DISJOINT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class JointCoordinateBounds:
    """Lower/upper bounds over full ``(row, feature)`` ancestor tuples."""

    bounds: SetBounds
    proved_rectangular: bool = False

    def __post_init__(self) -> None:
        if self.bounds.lower.axis != _JOINT_AXIS:
            raise ValueError(f"joint bounds must use axis {_JOINT_AXIS!r}")
        if not isinstance(self.proved_rectangular, bool):
            raise TypeError("proved_rectangular must be bool")
        for expression in (self.bounds.lower, self.bounds.upper):
            if isinstance(expression, Exact):
                for coordinate in expression.ids:
                    if not isinstance(coordinate, tuple) or len(coordinate) != 2:
                        raise ValueError("joint coordinates must be (row, feature) tuples")

    @property
    def unknown_boundaries(self) -> FrozenSet[VersionBoundary]:
        return frozenset(VersionBoundary(item) for item in self.bounds.boundaries)

    @classmethod
    def exact(
        cls, coordinates: Iterable[tuple[object, object]], *, proved_rectangular: bool = False
    ) -> "JointCoordinateBounds":
        values = frozenset(coordinates)
        for coordinate in values:
            if not isinstance(coordinate, tuple) or len(coordinate) != 2:
                raise ValueError("joint coordinates must be (row, feature) tuples")
        return cls(SetBounds.exact(_JOINT_AXIS, values), proved_rectangular)

    @classmethod
    def dynamic(cls, boundary_id: str) -> "JointCoordinateBounds":
        return cls(SetBounds.dynamic(_JOINT_AXIS, boundary_id))

    @classmethod
    def from_rectangular_marginals(
        cls,
        rows: SetBounds,
        features: SetBounds,
        *,
        proved_rectangular: bool,
        boundary_id: str = "unproved-rectangular-joint-region",
    ) -> "JointCoordinateBounds":
        if not proved_rectangular:
            return cls.dynamic(boundary_id)
        exact_inputs = (
            isinstance(rows.lower, Exact)
            and rows.lower == rows.upper
            and not rows.boundaries
            and isinstance(features.lower, Exact)
            and features.lower == features.upper
            and not features.boundaries
        )
        if not exact_inputs:
            # MV-0 has no symbolic product term in the closed joint grammar.
            return cls.dynamic(f"{boundary_id}:non-exact-marginals")
        return cls.exact(product(rows.lower.ids, features.lower.ids), proved_rectangular=True)

    def overlap(self, other: "JointCoordinateBounds") -> JointOverlap:
        if self.unknown_boundaries or other.unknown_boundaries:
            return JointOverlap.UNKNOWN
        relation = overlap_relation(self.bounds, other.bounds)
        if relation == "definite_overlap":
            return JointOverlap.DEFINITE_OVERLAP
        if relation == "disjoint":
            return JointOverlap.DISJOINT
        return JointOverlap.UNKNOWN


@dataclass(frozen=True)
class AncestorInfluence:
    ancestor_version_id: str
    region: JointCoordinateBounds

    def __post_init__(self) -> None:
        _require_nonempty_string(self.ancestor_version_id, "ancestor_version_id")
        if not isinstance(self.region, JointCoordinateBounds):
            raise TypeError("region must be JointCoordinateBounds")


@dataclass(frozen=True)
class JointInfluenceMap:
    influences: FrozenSet[AncestorInfluence] = frozenset()
    unknown_boundaries: FrozenSet[VersionBoundary] = frozenset()

    def __post_init__(self) -> None:
        if any(not isinstance(item, AncestorInfluence) for item in self.influences):
            raise TypeError("influences must contain AncestorInfluence values")
        ancestor_ids = [item.ancestor_version_id for item in self.influences]
        if len(set(ancestor_ids)) != len(ancestor_ids):
            raise ValueError("an influence map has at most one region per ancestor version")
        if any(not isinstance(item, VersionBoundary) for item in self.unknown_boundaries):
            raise TypeError("unknown_boundaries must contain VersionBoundary values")

    def region_for(self, ancestor_version_id: str) -> JointCoordinateBounds | None:
        return next(
            (
                item.region
                for item in self.influences
                if item.ancestor_version_id == ancestor_version_id
            ),
            None,
        )

    def project(
        self,
        projected_influences: FrozenSet[AncestorInfluence],
        *,
        relation_representable: bool,
        boundary_id: str = "unrepresentable-joint-composition",
    ) -> "JointInfluenceMap":
        boundaries = self.unknown_boundaries
        if not relation_representable:
            boundaries = boundaries | {VersionBoundary(boundary_id)}
            projected_influences = frozenset()
        # Prior uncertainty is sticky: a later shape cannot recover an ancestor image.
        return JointInfluenceMap(projected_influences, boundaries)


@dataclass(frozen=True)
class MatrixRead:
    component: ComponentRef
    versions: VersionValue
    row_region: SetBounds
    feature_region: SetBounds
    influence_map: JointInfluenceMap
    lineage_complete: bool = True
    unknown_boundaries: FrozenSet[VersionBoundary] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.component, ComponentRef):
            raise TypeError("component must be ComponentRef")
        if not isinstance(self.versions, VersionValue):
            raise TypeError("versions must be VersionValue")
        if not isinstance(self.row_region, SetBounds) or not isinstance(self.feature_region, SetBounds):
            raise TypeError("row_region and feature_region must be SetBounds")
        if not isinstance(self.influence_map, JointInfluenceMap):
            raise TypeError("influence_map must be JointInfluenceMap")
        if not isinstance(self.lineage_complete, bool):
            raise TypeError("lineage_complete must be bool")
        if any(not isinstance(item, VersionBoundary) for item in self.unknown_boundaries):
            raise TypeError("unknown_boundaries must contain VersionBoundary values")

    @property
    def all_unknown_boundaries(self) -> FrozenSet[VersionBoundary]:
        region_boundaries = frozenset(
            VersionBoundary(boundary)
            for boundary in self.row_region.boundaries | self.feature_region.boundaries
        )
        influence_region_boundaries = frozenset(
            boundary
            for influence in self.influence_map.influences
            for boundary in influence.region.unknown_boundaries
        )
        return (
            self.unknown_boundaries
            | self.versions.unknown_boundaries
            | self.influence_map.unknown_boundaries
            | region_boundaries
            | influence_region_boundaries
        )


class DerivationKind(str, Enum):
    ROOT = "root"
    INPLACE_TRANSFORM = "inplace_transform"
    DERIVED_COMPONENT = "derived_component"
    PROJECTION = "projection"
    COPY = "copy"
    SPLIT_CHILD = "split_child"


@dataclass(frozen=True)
class DerivationEdge:
    parent: StatisticalMatrixVersion
    child: StatisticalMatrixVersion
    kind: DerivationKind
    summary_digest: str
    occurrence_id: str
    influence_map_digest: str
    split_event_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.parent, StatisticalMatrixVersion) or not isinstance(
            self.child, StatisticalMatrixVersion
        ):
            raise TypeError("parent and child must be StatisticalMatrixVersion values")
        if not isinstance(self.kind, DerivationKind):
            raise TypeError("kind must be DerivationKind")
        for field_name in ("summary_digest", "occurrence_id", "influence_map_digest"):
            _require_nonempty_string(getattr(self, field_name), field_name)
        if self.split_event_id is not None:
            _require_nonempty_string(self.split_event_id, "split_event_id")
        child = self.child
        object.__setattr__(
            self,
            "child",
            StatisticalMatrixVersion(
                root_artifact_digest=child.root_artifact_digest,
                row_identity_digest=child.row_identity_digest,
                feature_identity_digest=child.feature_identity_digest,
                measurement_value_digest=child.measurement_value_digest,
                noise_unit_digest=child.noise_unit_digest,
                transform_lineage_digest=self.transition_commitment_digest,
                measurement_digest_kind=child.measurement_digest_kind,
                evidence_kind=child.evidence_kind,
            ),
        )

    @property
    def transition_commitment_digest(self) -> str:
        """Hash transition identity without the child ID it will help determine."""
        return _domain_hash(
            _TRANSITION_SCHEMA,
            {
                "parent_version_ids": [self.parent.version_id],
                "kind": self.kind.value,
                "summary_digest": self.summary_digest,
                "occurrence_id": self.occurrence_id,
                "influence_map_digest": self.influence_map_digest,
                "split_event_id": self.split_event_id,
            },
        )

    @property
    def transform_lineage_digest(self) -> str:
        return _domain_hash(
            _EDGE_SCHEMA,
            {
                "parent_version_id": self.parent.version_id,
                "child_version_id": self.child.version_id,
                "kind": self.kind.value,
                "summary_digest": self.summary_digest,
                "occurrence_id": self.occurrence_id,
                "influence_map_digest": self.influence_map_digest,
                "split_event_id": self.split_event_id,
            },
        )

    @property
    def committed_transform_lineage_digest(self) -> str:
        """Return the non-self-referential commitment carried by the child version."""
        return self.child.transform_lineage_digest


def ancestor_version_ids(
    version: StatisticalMatrixVersion, edges: Iterable[DerivationEdge]
) -> FrozenSet[str]:
    """Return the reflexive-transitive ancestor closure of ``version``."""

    parents_by_child: dict[str, set[str]] = {}
    for edge in edges:
        parents_by_child.setdefault(edge.child.version_id, set()).add(edge.parent.version_id)
    seen: set[str] = set()
    frontier = [version.version_id]
    while frontier:
        current = frontier.pop()
        if current in seen:
            continue
        seen.add(current)
        frontier.extend(parents_by_child.get(current, ()))
    return frozenset(seen)


class NoiseUnitKind(str, Enum):
    FULL = "full"
    ROW_HOLDOUT = "row_holdout"
    FEATURE_HOLDOUT = "feature_holdout"
    COUNT_SPLIT = "count_split"
    SAMPLE_SPLIT = "sample_split"
    INDEPENDENT_ASSAY = "independent_assay"


class NoiseEngineStatus(str, Enum):
    RECOGNIZED = "RECOGNIZED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class NoiseUnit:
    kind: NoiseUnitKind
    root_measurement_digest: str
    partition_digest: str
    engine_status: NoiseEngineStatus
    complement_digest: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, NoiseUnitKind):
            raise TypeError("kind must be NoiseUnitKind")
        if not isinstance(self.engine_status, NoiseEngineStatus):
            raise TypeError("engine_status must be NoiseEngineStatus")
        _require_nonempty_string(self.root_measurement_digest, "root_measurement_digest")
        _require_nonempty_string(self.partition_digest, "partition_digest")
        if self.complement_digest is not None:
            _require_nonempty_string(self.complement_digest, "complement_digest")


class MeasurementRelation(str, Enum):
    PROVED_SHARED = "PROVED_SHARED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class MeasurementPair:
    selection_read: MatrixRead
    selection_version: GuardedVersion
    test_read: MatrixRead
    test_version: GuardedVersion

    def __post_init__(self) -> None:
        if self.selection_version not in self.selection_read.versions.alternatives:
            raise ValueError("selection_version must be an alternative of selection_read")
        if self.test_version not in self.test_read.versions.alternatives:
            raise ValueError("test_version must be an alternative of test_read")


@dataclass(frozen=True)
class MeasurementPairInventory:
    pairs: FrozenSet[MeasurementPair]
    complete: bool
    unknown_boundaries: FrozenSet[VersionBoundary] = frozenset()

    def __post_init__(self) -> None:
        if any(not isinstance(item, MeasurementPair) for item in self.pairs):
            raise TypeError("pairs must contain MeasurementPair values")
        if not isinstance(self.complete, bool):
            raise TypeError("complete must be bool")
        if any(not isinstance(item, VersionBoundary) for item in self.unknown_boundaries):
            raise TypeError("unknown_boundaries must contain VersionBoundary values")

    @classmethod
    def from_reads(
        cls,
        selection_read: MatrixRead,
        test_read: MatrixRead,
        *,
        feasible_pairs: Iterable[tuple[GuardedVersion, GuardedVersion]],
        inventory_complete: bool,
        boundary_id: str = "incomplete-pair-inventory",
    ) -> "MeasurementPairInventory":
        version_inventory = VersionPairInventory.from_feasibility(
            selection_read.versions,
            test_read.versions,
            feasible_pairs=feasible_pairs,
            feasibility_complete=inventory_complete,
            boundary_id=boundary_id,
        )
        pairs = frozenset(
            MeasurementPair(selection_read, left, test_read, right)
            for left, right in version_inventory.pairs
        )
        return cls(pairs, version_inventory.complete, version_inventory.unknown_boundaries)


def judge_measurement_pair(
    pair: MeasurementPair, edges: Iterable[DerivationEdge]
) -> MeasurementRelation:
    selection = pair.selection_read
    test = pair.test_read
    if (
        not selection.lineage_complete
        or not test.lineage_complete
        or selection.all_unknown_boundaries
        or test.all_unknown_boundaries
    ):
        return MeasurementRelation.UNKNOWN

    edge_values = tuple(edges)
    selection_ancestors = ancestor_version_ids(pair.selection_version.version, edge_values)
    test_ancestors = ancestor_version_ids(pair.test_version.version, edge_values)
    common_ancestors = selection_ancestors & test_ancestors
    for ancestor_id in common_ancestors:
        selection_region = selection.influence_map.region_for(ancestor_id)
        test_region = test.influence_map.region_for(ancestor_id)
        if selection_region is None or test_region is None:
            continue
        if selection_region.overlap(test_region) is JointOverlap.DEFINITE_OVERLAP:
            return MeasurementRelation.PROVED_SHARED
    return MeasurementRelation.UNKNOWN


def aggregate_judgments(
    judgments: Iterable[MeasurementRelation],
    *,
    pair_inventory_complete: bool,
    unknown_boundaries: FrozenSet[VersionBoundary] = frozenset(),
) -> MeasurementRelation:
    values = tuple(judgments)
    if (
        not pair_inventory_complete
        or unknown_boundaries
        or not values
        or any(value is not MeasurementRelation.PROVED_SHARED for value in values)
    ):
        return MeasurementRelation.UNKNOWN
    return MeasurementRelation.PROVED_SHARED


def aggregate_measurement_relation(
    inventory: MeasurementPairInventory, edges: Iterable[DerivationEdge]
) -> MeasurementRelation:
    return aggregate_judgments(
        (judge_measurement_pair(pair, edges) for pair in inventory.pairs),
        pair_inventory_complete=inventory.complete,
        unknown_boundaries=inventory.unknown_boundaries,
    )


__all__ = [
    "AncestorInfluence",
    "ComponentKind",
    "ComponentRef",
    "DerivationEdge",
    "DerivationKind",
    "EvidenceKind",
    "GuardedVersion",
    "ImmediateVersionRelation",
    "JointCoordinateBounds",
    "JointInfluenceMap",
    "JointOverlap",
    "MatrixRead",
    "MeasurementDigestKind",
    "MeasurementPair",
    "MeasurementPairInventory",
    "MeasurementRelation",
    "NoiseEngineStatus",
    "NoiseUnit",
    "NoiseUnitKind",
    "StatisticalMatrixVersion",
    "VersionBoundary",
    "VersionPairInventory",
    "VersionValue",
    "aggregate_judgments",
    "aggregate_measurement_relation",
    "ancestor_version_ids",
    "compare_immediate_versions",
    "judge_measurement_pair",
]
