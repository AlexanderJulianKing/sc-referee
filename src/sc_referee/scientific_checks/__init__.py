"""Deterministic, capability-limited scientific-check extension seam."""

from sc_referee.scientific_checks.core import (
    AdapterManifest,
    CanonicalOperand,
    CheckManifest,
    EvidenceSpan,
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenSourceLocation,
    InspectionDocument,
    InspectionReceipt,
    MethodConflictBinding,
    NormalizedMethodObservation,
    RecordRef,
    RequirementCandidate,
    RoleBinding,
    ScientificCheckContractError,
    ScientificCheckModule,
    ScopeJoinEdge,
)
from sc_referee.scientific_checks.registry import (
    RegistryEvaluation,
    RegistryValidationError,
    ScientificCheckRegistry,
)

__all__ = [
    "AdapterManifest",
    "CanonicalOperand",
    "CheckManifest",
    "EvidenceSpan",
    "FrozenBaseRecord",
    "FrozenInspectionContext",
    "FrozenSourceLocation",
    "InspectionDocument",
    "InspectionReceipt",
    "MethodConflictBinding",
    "NormalizedMethodObservation",
    "RecordRef",
    "RegistryEvaluation",
    "RegistryValidationError",
    "RequirementCandidate",
    "RoleBinding",
    "ScientificCheckContractError",
    "ScientificCheckModule",
    "ScientificCheckRegistry",
    "ScopeJoinEdge",
]
