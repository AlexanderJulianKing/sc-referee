"""Double-dipping policy declaration; dormant until Increment 9."""
from sc_referee.inference.policy.schema import ProofRule, RelationPremise, ValidityPolicy

POLICY = ValidityPolicy(
    id="double_dipping.v1",
    scope=(RelationPremise("ReportClaimPValue", ()),),
    rules=(
        ProofRule("independent_selection", (RelationPremise("SelectionReuseIndependent", ()),), (),
                  "CLEAN_PROOF", "pass", ()),
        ProofRule("disjoint_selection", (RelationPremise("SelectionAndTestRegionsDisjoint", ()),), (),
                  "CLEAN_PROOF", "pass", ()),
        ProofRule("dependent_naive_reuse", (
            RelationPremise("ClaimMustProducedByTest", ()),
            RelationPremise("TestDefinitelyNaive", ()),
            RelationPremise("GroupingMustProducedBySelection", ()),
            RelationPremise("RelevantRegionOverlapDefinite", ()),
            RelationPremise("SelectionReuseDependentUnderNull", ()),
            RelationPremise("PinnedReachable", ()),
        ), (), "VIOLATION_WITNESS", "needs_evidence", ()),
    ),
    required_coverage=frozenset({"claim_binding", "producer_flow", "semantic_facts"}),
)
