from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Mapping

from sc_referee.inference.coverage import CoverageIndex, coverage_from_barriers
from sc_referee.inference.diagnostics import Diagnostic
from sc_referee.inference.frontend.common import SourceUnit, adapt_sources
from sc_referee.inference.frontend.python import lower_python
from sc_referee.inference.frontend.r import lower_r
from sc_referee.inference.analysis.interpret import interpret
from sc_referee.inference.analysis.dependence import DependenceProgram, build_dependence
from sc_referee.inference.claims.inventory import StructuredClaimManifest, inventory_claims
from sc_referee.inference.claims.slice import slice_claim
from sc_referee.inference.ir.lower import lower
from sc_referee.inference.ir.nodes import ProgramIR
from sc_referee.inference.ir.validate import validate_program
from sc_referee.inference.refinement.infer import RefinementFacts, infer_refinements
from sc_referee.inference.refinement.types import RefinementIndex


@dataclass(frozen=True)
class ArtifactManifest:
    artifacts: tuple[object, ...] = ()


@dataclass(frozen=True)
class ClaimManifest:
    claims: tuple[object, ...] = ()


@dataclass(frozen=True)
class PinnedConfig:
    values: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class DependencyBindings:
    bindings: tuple[object, ...] = ()


@dataclass(frozen=True)
class AnalysisRequest:
    sources: tuple[str | SourceUnit, ...]
    artifacts: ArtifactManifest = field(default_factory=ArtifactManifest)
    claims: ClaimManifest | None = None
    config: PinnedConfig = field(default_factory=PinnedConfig)
    dependency_bindings: DependencyBindings = field(default_factory=DependencyBindings)
    ratified_facts: tuple[object, ...] = ()
    compatibility_profile: str | None = None


@dataclass(frozen=True)
class EvidenceBindings:
    bindings: tuple[object, ...] = ()


@dataclass(frozen=True)
class AnalysisSnapshot:
    program: ProgramIR
    states: Mapping[str, object]
    dependence: DependenceProgram
    claims: tuple[object, ...]
    refinements: RefinementIndex
    coverage: CoverageIndex
    diagnostics: tuple[Diagnostic, ...]
    bindings: EvidenceBindings
    analyzer_digest: str
    judgment: str = "ABSTAIN"
    claim_slices: Mapping[str, object] = field(default_factory=dict)

    @property
    def outcome(self) -> str:
        return self.judgment


ANALYZER_VERSION = "sc-referee.inference.increment-9.live.advisory-v4"
ANALYZER_DIGEST = "sha256:" + sha256(ANALYZER_VERSION.encode()).hexdigest()


def analyze(request: AnalysisRequest | tuple[str, ...] | list[str]) -> AnalysisSnapshot:
    """Build a static snapshot; Increment 9 policy routing evaluates this snapshot separately."""
    if not isinstance(request, AnalysisRequest):
        request = AnalysisRequest(tuple(request))
    sources = adapt_sources(request.sources)
    program = lower(tuple(lower_python(unit) if unit.language == "python" else lower_r(unit)
                          for unit in sources))
    validate_program(program)
    states = interpret(program)
    dependence = build_dependence(program)
    claim_inventory = (inventory_claims(request.claims, (), egress_complete=False)
                       if isinstance(request.claims, StructuredClaimManifest)
                       else inventory_claims(None, (), egress_complete=False))
    claim_slices = {claim.claim_id: slice_claim(dependence, claim)
                    for claim in claim_inventory.claims}
    call_effects_complete = not any(effect.unknown_effects for state in states.values()
                                    for effect in state.effects)
    artifact_resolution_complete = bool(request.artifacts.artifacts) and all(
        getattr(artifact, "exact", False) for artifact in request.artifacts.artifacts
    )
    diagnostics = tuple(Diagnostic(barrier.kind, barrier.reason, barrier.span,
                                   {"barrier_id": barrier.id, "ast_kind": barrier.ast_kind})
                        for barrier in program.barriers)
    return AnalysisSnapshot(
        program=program,
        states=states,
        dependence=dependence,
        claims=claim_inventory.claims,
        refinements=infer_refinements(RefinementFacts(
            report_facts={claim.claim_id: (claim, claim_slices[claim.claim_id])
                          for claim in claim_inventory.claims},
        )),
        coverage=coverage_from_barriers(program.barriers,
                                        call_effects_complete=call_effects_complete,
                                        artifact_resolution_complete=artifact_resolution_complete,
                                        claim_inventory_complete=claim_inventory.complete),
        diagnostics=diagnostics,
        bindings=EvidenceBindings(),
        analyzer_digest=ANALYZER_DIGEST,
        judgment="ABSTAIN",
        claim_slices=claim_slices,
    )
