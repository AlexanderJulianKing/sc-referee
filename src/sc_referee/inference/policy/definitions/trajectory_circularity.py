"""Trajectory circularity declaration, intentionally needs-evidence capped."""
from sc_referee.inference.policy.schema import ProofRule, RelationPremise, ValidityPolicy

POLICY = ValidityPolicy(
    id="trajectory_circularity.v1",
    scope=(RelationPremise("TrajectoryAssociationClaim", ()),),
    rules=(
        ProofRule("trajectory_structure_external", (
            RelationPremise("TrajectoryStructureExternalToTestedData", ()),
        ), (), "CLEAN_PROOF", "pass", ()),
        ProofRule("naive_overlapping_trajectory_reuse", (
            RelationPremise("ClaimMustProducedByNaiveTrajectoryTest", ()),
            RelationPremise("TrajectoryStateMustDependsOnTestedData", ()),
            RelationPremise("TrajectoryAndTestRegionsOverlap", ()),
            RelationPremise("SelectionReuseDependentUnderNull", ()),
            RelationPremise("NoVerifiedTrajectorySafeguard", ()),
        ), (), "VIOLATION_WITNESS", "needs_evidence", ()),
    ),
    required_coverage=frozenset({"claim_binding", "producer_flow", "semantic_facts"}),
)
