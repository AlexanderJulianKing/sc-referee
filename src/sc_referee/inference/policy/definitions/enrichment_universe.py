"""Exact joint ORA correction declaration; inflated K alone is non-blocking."""
from sc_referee.inference.policy.schema import FactRef, ProofRule, ProviderInvocation, RelationPremise, ValidityPolicy

POLICY = ValidityPolicy(
    id="enrichment_universe.v1",
    scope=(RelationPremise("OraReportClaim", ()),),
    rules=(
        ProofRule("exact_membership_consistent", (
            RelationPremise("UniverseMembershipInternallyConsistent", ()),
            RelationPremise("OraFamilyInventoryComplete", ()),
        ), (), "CLEAN_PROOF", "pass", ()),
        ProofRule("joint_correction_changes_discovery", (
            RelationPremise("ReportConsumedMembershipContradiction", ()),
            RelationPremise("ContradictoryCellMustProducesClaim", ()),
            RelationPremise("CorrectedTableWellDefined", ()),
        ), (ProviderInvocation(
            "ora_joint_correction.v1", "1",
            "sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4",
            {"population": FactRef("CorrectedPopulation", {}),
             "term_size": FactRef("CorrectedTermSize", {}), "draws": FactRef("CorrectedDraws", {}),
             "overlap": FactRef("CorrectedOverlap", {}),
             "family_raw_pvalues": FactRef("CompleteRawPValueFamilyQ", {}),
             "target_index": FactRef("TargetFamilyIndex", {}),
             "procedure": FactRef("ActualCorrectionProcedure", {}),
             "alpha": FactRef("BoundAlphaQ", {}),
             "reported_adjusted_p": FactRef("ReportedAdjustedPValueQ", {}),
             "reported_significant": FactRef("ReportedSignificantDecision", {}),
             "family_complete": FactRef("PValueFamilyComplete", {})},
            "ReportedMoreSignificantThanCorrected",
        ),), "VIOLATION_WITNESS", "blocker", ()),
    ),
    required_coverage=frozenset({"claim_binding", "producer_flow", "semantic_facts"}),
)
