from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EffectValue:
    reads: frozenset[str] = frozenset()
    writes: frozenset[str] = frozenset()
    allocations: frozenset[str] = frozenset()
    return_dependencies: frozenset[str] = frozenset()
    egresses: frozenset[str] = frozenset()
    unknown_effects: frozenset[str] = frozenset()
    must_reads: frozenset[str] = frozenset()
    must_writes: frozenset[str] = frozenset()
    must_allocations: frozenset[str] = frozenset()
    control_dependencies: frozenset[str] = frozenset()
    artifact_reads: frozenset[str] = frozenset()
    must_artifact_reads: frozenset[str] = frozenset()
    artifact_writes: frozenset[str] = frozenset()
    must_artifact_writes: frozenset[str] = frozenset()
    must_egresses: frozenset[str] = frozenset()

    def __post_init__(self):
        pairs = (
            (self.must_reads, self.reads), (self.must_writes, self.writes),
            (self.must_allocations, self.allocations),
            (self.must_artifact_reads, self.artifact_reads),
            (self.must_artifact_writes, self.artifact_writes),
            (self.must_egresses, self.egresses),
        )
        if any(not must <= may for must, may in pairs):
            raise ValueError("effect must facts must be possible")
