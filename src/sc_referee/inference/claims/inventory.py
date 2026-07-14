"""Structured claim roots and closed egress inventory, without policy judgments."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClaimRootGrade(Enum):
    ACCUSATION_GRADE = "accusation_grade"
    CLEAN_ONLY = "clean_only"
    DIAGNOSTIC_ONLY = "diagnostic_only"


@dataclass(frozen=True)
class StructuredClaimRoot:
    claim_id: str
    report_artifact_digest: str
    report_span_or_field: str
    producing_value: str
    producer_binding_digest: str
    claim_role: str
    ratification_fact_id: str

    @property
    def exact(self) -> bool:
        return all((self.claim_id, self.report_artifact_digest, self.report_span_or_field,
                    self.producing_value, self.producer_binding_digest, self.claim_role,
                    self.ratification_fact_id))


@dataclass(frozen=True)
class StructuredClaimManifest:
    roots: tuple[StructuredClaimRoot, ...]


@dataclass(frozen=True)
class Egress:
    id: str
    value: str
    report_locator: str
    role: str
    digest: str


@dataclass(frozen=True)
class ClaimBoundary:
    id: str
    reason: str


@dataclass(frozen=True)
class ReportClaim:
    claim_id: str
    value: str
    role: str
    root_grade: ClaimRootGrade
    root_exact: bool
    report_locator: str | None = None
    root_digest: str | None = None


@dataclass(frozen=True)
class ClaimInventory:
    claims: tuple[ReportClaim, ...] = ()
    complete: bool = False
    unknown_boundaries: tuple[ClaimBoundary, ...] = ()


def inventory_claims(manifest: StructuredClaimManifest | None, egresses: tuple[Egress, ...],
                     *, egress_complete: bool) -> ClaimInventory:
    if manifest is not None:
        claims = []
        boundaries = []
        if not manifest.roots:
            boundaries.append(ClaimBoundary("claim-manifest", "structured_claim_manifest_empty"))
        for root in manifest.roots:
            exact = root.exact
            claims.append(ReportClaim(root.claim_id, root.producing_value, root.claim_role,
                                      ClaimRootGrade.ACCUSATION_GRADE if exact
                                      else ClaimRootGrade.DIAGNOSTIC_ONLY,
                                      exact, root.report_span_or_field, root.report_artifact_digest))
            if not exact:
                boundaries.append(ClaimBoundary(f"claim:{root.claim_id}",
                                                "structured_claim_root_incomplete"))
        return ClaimInventory(tuple(claims), bool(claims) and not boundaries, tuple(boundaries))

    claims = tuple(ReportClaim(
        f"claim:{egress.id}", egress.value, egress.role,
        ClaimRootGrade.CLEAN_ONLY if egress_complete else ClaimRootGrade.DIAGNOSTIC_ONLY,
        egress_complete, egress.report_locator, egress.digest,
    ) for egress in egresses)
    boundaries = (() if egress_complete else
                  (ClaimBoundary("claim-inventory", "egress_enumeration_incomplete"),))
    return ClaimInventory(claims, egress_complete, boundaries)
