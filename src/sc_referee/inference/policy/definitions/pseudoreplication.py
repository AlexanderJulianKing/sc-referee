"""Pseudoreplication policy declaration; dormant until Increment 9."""
from sc_referee.inference.policy.schema import ProofRule, RelationPremise, ValidityPolicy

POLICY = ValidityPolicy(
    id="pseudoreplication.v1",
    scope=(RelationPremise("PopulationInferenceClaim", ()),),
    rules=(
        ProofRule("same_replication_unit", (RelationPremise("IndependentUnitEqualsReplicationUnit", ()),),
                  (), "CLEAN_PROOF", "pass", ()),
        ProofRule("modeled_replication_unit", (RelationPremise("DependenceModelAccountsForReplicationUnit", ()),),
                  (), "CLEAN_PROOF", "pass", ()),
        ProofRule("iid_refinement_mismatch", (
            RelationPremise("ClaimMustProducedByIidRowsTest", ()),
            RelationPremise("RowsStrictlyRefineReplicationUnit", ()),
            RelationPremise("MultipleRowsShareReplicationUnit", ()),
            RelationPremise("NoModelAccountsForReplicationUnit", ()),
            RelationPremise("AssignmentFactsRatifiedExact", ()),
        ), (), "VIOLATION_WITNESS", "blocker", ()),
    ),
    required_coverage=frozenset({"claim_binding", "producer_flow", "semantic_facts"}),
)
