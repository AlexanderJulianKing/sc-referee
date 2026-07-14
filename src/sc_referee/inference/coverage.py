from __future__ import annotations

from dataclasses import dataclass

from sc_referee.inference.ir.nodes import Barrier


@dataclass(frozen=True)
class CoverageIndex:
    source_complete: bool
    frontend_complete: bool
    call_effects_complete: bool
    artifact_resolution_complete: bool
    claim_inventory_complete: bool
    barriers: tuple[Barrier, ...] = ()

    @property
    def complete(self) -> bool:
        return (self.source_complete and self.frontend_complete and self.call_effects_complete
                and self.artifact_resolution_complete and self.claim_inventory_complete)


def coverage_from_barriers(barriers: tuple[Barrier, ...], *, call_effects_complete: bool = True,
                           artifact_resolution_complete: bool = False,
                           claim_inventory_complete: bool = False):
    kinds = {barrier.kind for barrier in barriers}
    return CoverageIndex(
        source_complete="parse_error" not in kinds,
        frontend_complete=not bool(barriers),
        call_effects_complete=call_effects_complete,
        artifact_resolution_complete=artifact_resolution_complete,
        claim_inventory_complete=claim_inventory_complete,
        barriers=barriers,
    )
