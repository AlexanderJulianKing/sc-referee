"""Spatial iid-unit specialization; powered collapse is never an identification proof."""
from sc_referee.inference.policy.schema import ProofRule, RelationPremise, ValidityPolicy

POLICY = ValidityPolicy(
    id="spatial_iid.v1",
    scope=(RelationPremise("SpatialPopulationInferenceClaim", ()),),
    rules=(
        ProofRule("spatial_dependence_accounted", (
            RelationPremise("SpatialModelAccountsForSectionOrDonor", ()),
        ), (), "CLEAN_PROOF", "pass", ()),
        ProofRule("exact_spatial_iid_unit_mismatch", (
            RelationPremise("ClaimMustProducedBySpatialIidRowsTest", ()),
            RelationPremise("SpatialRowsStrictlyRefineAssignmentUnit", ()),
            RelationPremise("MultipleSpatialRowsShareAssignmentUnit", ()),
            RelationPremise("NoSpatialModelAccountsForAssignmentUnit", ()),
            RelationPremise("SpatialAssignmentFactsRatifiedExact", ()),
        ), (), "VIOLATION_WITNESS", "blocker", ()),
    ),
    required_coverage=frozenset({"claim_binding", "producer_flow", "semantic_facts"}),
)
