"""Identity-bearing units and evidence-gated partition relations."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from sc_referee.inference.domains.bilattice import MayMust


@dataclass(frozen=True)
class UnitRef:
    artifact_id: str
    fields: tuple[str, ...]
    kind: str
    role: str


class UnitRelationKind(Enum):
    SAME_PARTITION = "same_partition"
    STRICTLY_REFINES = "strictly_refines"
    COARSER_THAN = "coarser_than"
    ACCOUNTS_FOR = "accounts_for"
    INCOMPARABLE = "incomparable"
    UNKNOWN = "unknown"


class RelationSource(Enum):
    ARTIFACT_RELATION = "artifact_relation"
    EXACT_CONSTRUCTION = "exact_construction"
    RATIFIED_FACT = "ratified_fact"


@dataclass(frozen=True)
class UnitRelationFact:
    left: UnitRef
    right: UnitRef
    kind: UnitRelationKind
    source: RelationSource | None
    evidence_id: str


class UnitRelationIndex:
    def __init__(self):
        self._facts: list[UnitRelationFact] = []

    def add(self, left: UnitRef, right: UnitRef, kind: UnitRelationKind, *,
            source: RelationSource, evidence_id: str) -> UnitRelationFact:
        if not isinstance(source, RelationSource):
            raise ValueError("unit relations require artifact, exact-construction, or ratified evidence")
        fact = UnitRelationFact(left, right, kind, source, evidence_id)
        self._facts.append(fact)
        return fact

    def relate(self, left: UnitRef, right: UnitRef) -> MayMust[UnitRelationFact]:
        facts = frozenset(fact for fact in self._facts if fact.left == left and fact.right == right)
        if facts:
            return MayMust(facts, facts)
        unknown = UnitRelationFact(left, right, UnitRelationKind.UNKNOWN, None, "unproved")
        return MayMust(frozenset({unknown}), frozenset())

    def relate_from_names(self, left: UnitRef, right: UnitRef) -> MayMust[UnitRelationFact]:
        unknown = UnitRelationFact(left, right, UnitRelationKind.UNKNOWN, None,
                                   "names_are_not_partition_evidence")
        return MayMust(frozenset({unknown}), frozenset())

