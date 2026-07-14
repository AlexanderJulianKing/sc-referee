"""Joint sign-parity policy declaration; per-source mismatches never suffice."""
from sc_referee.inference.policy.schema import FactRef, ProofRule, ProviderInvocation, RelationPremise, ValidityPolicy

POLICY = ValidityPolicy(
    id="allele_harmonization.v1",
    scope=(RelationPremise("SignedReportClaim", ()),),
    rules=(
        ProofRule("joint_sign_conformant", (
            RelationPremise("AllSourceToSinkSignFlowsDefinite", ()),
        ), (ProviderInvocation(
            "sign_parity.v1", "1",
            "sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4",
            {"required_factors": FactRef("RatifiedJointReversals", {}),
             "applied_multiplier": FactRef("AppliedJointMultiplier", {})}, "JointSignConsistent",
        ),), "CLEAN_PROOF", "pass", ()),
        ProofRule("joint_sign_inconsistent", (
            RelationPremise("AllSourceToSinkSignFlowsDefinite", ()),
            RelationPremise("InconsistentInputMateriallyConsumed", ()),
            RelationPremise("SignedSinkFormulaExact", ()),
        ), (ProviderInvocation(
            "sign_parity.v1", "1",
            "sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4",
            {"required_factors": FactRef("RatifiedJointReversals", {}),
             "applied_multiplier": FactRef("AppliedJointMultiplier", {})}, "JointSignInconsistent",
        ),), "VIOLATION_WITNESS", "blocker", ()),
    ),
    required_coverage=frozenset({"claim_binding", "producer_flow", "semantic_facts"}),
)
