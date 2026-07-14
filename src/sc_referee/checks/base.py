"""The Finding a check returns, and the Check protocol checks implement."""
from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from types import MappingProxyType
from typing import Mapping, Optional, Protocol, runtime_checkable

from sc_referee import statuses as S


@dataclass(frozen=True)
class ConditionalPremise:
    contract_id: str
    contract_type: str
    decisive_fields: Mapping[str, object]
    plain_language_premise: str
    scope: Mapping[str, str]
    component_identities: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "decisive_fields", MappingProxyType(dict(self.decisive_fields)))
        object.__setattr__(self, "scope", MappingProxyType(dict(self.scope)))
        object.__setattr__(self, "component_identities",
                           MappingProxyType(dict(self.component_identities)))


@dataclass
class Finding:
    check_id: str
    status: str  # one of sc_referee.statuses.STATUSES
    verdict: str  # plain-language, derived FROM the metrics
    metrics: dict = field(default_factory=dict)
    citations: list = field(default_factory=list)
    fix: Optional[str] = None  # path to a generated fix template, if any
    # InitVar preserves the frozen legacy dataclass projection while retaining first-class
    # instance metadata for premise-dependent findings.
    conditional_on: InitVar[Optional[ConditionalPremise]] = None
    # Orthogonal report-ledger axes. InitVar keeps the legacy dataclass field projection, equality,
    # and repr byte-stable; __post_init__ retains the canonical values as ordinary instance metadata
    # for report classification. Judgment/proof remain optional for the safe shipped-status fallback.
    applicability: InitVar[str] = S.APPLIES
    judgment: InitVar[Optional[str]] = None
    coverage: InitVar[str] = S.COMPLETE
    proof_grade: InitVar[Optional[str]] = None

    def __post_init__(self, conditional_on, applicability, judgment, coverage, proof_grade):
        self.conditional_on = conditional_on
        self.applicability = applicability
        self.judgment = judgment
        self.coverage = coverage
        self.proof_grade = (S.ADVISORY
                            if proof_grade is None and self.status == S.INFORMATIONAL
                            else proof_grade)


@runtime_checkable
class Check(Protocol):
    id: str
    analysis_types: tuple
    audit_dimensions: tuple[str, ...]
    proof_basis: str
    contract_fields: tuple[str, ...]
    # The worst status this verifier is ENTITLED to emit. `blocker` only for structural verifiers
    # and recompute verifiers on an engine that can earn it; `major` caps advisory/`simple`-engine
    # verifiers. `audit._safe_run` clamps anything above this — a blocker a verifier isn't entitled
    # to is the worst failure. (design doc §9.3, the safety invariant.)
    max_status: str

    def applies_to(self, design, bundle) -> bool: ...

    def run(self, design, bundle, reported) -> Finding: ...

    def cannot_evaluate(self, design, bundle):
        """Return a reason string when this check SHOULD have run but a prerequisite is missing.

        `applies_to == False` means "not applicable — there is nothing here to check".
        `cannot_evaluate` means "this is exactly our business, and we could not look."
        The two are not the same, and conflating them is how a silent green happens: a
        pseudoreplicated analysis whose replicate column we failed to detect must not be
        reported as clean. `run_audit` turns this into a `not_audited` finding.
        """
        return None
