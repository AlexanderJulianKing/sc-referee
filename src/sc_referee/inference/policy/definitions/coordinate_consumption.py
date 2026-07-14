"""Consumer-contract-specific coordinate-consumption declaration."""
from sc_referee.inference.policy.schema import FactRef, ProofRule, ProviderInvocation, RelationPremise, ValidityPolicy

POLICY = ValidityPolicy(
    id="coordinate_consumption.v1",
    scope=(RelationPremise("CoordinateReportClaim", ()),),
    rules=(
        ProofRule("coordinate_legal_for_consumer", (
            RelationPremise("CoordinateUnavoidablyConsumed", ()),
        ), (ProviderInvocation(
            "interval_bounds.v1", "1",
            "sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4",
            {"value": FactRef("CoordinateValue", {}),
             "contig_length": FactRef("ExactContigLength", {}),
             "coordinate_role": FactRef("CoordinateRole", {}),
             "consumer_contract_id": FactRef("CoordinateConsumerContractId", {})},
            "CoordinateLegal",
        ),), "CLEAN_PROOF", "pass", ()),
        ProofRule("coordinate_illegal_and_consumed", (
            RelationPremise("ExactContigIdentityAndLengthBound", ()),
            RelationPremise("CoordinateUnavoidablyConsumed", ()),
            RelationPremise("CoordinateMateriallyAffectsClaim", ()),
        ), (ProviderInvocation(
            "interval_bounds.v1", "1",
            "sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4",
            {"value": FactRef("CoordinateValue", {}),
             "contig_length": FactRef("ExactContigLength", {}),
             "coordinate_role": FactRef("CoordinateRole", {}),
             "consumer_contract_id": FactRef("CoordinateConsumerContractId", {})},
            "CoordinateIllegal",
        ),), "VIOLATION_WITNESS", "blocker", ()),
    ),
    required_coverage=frozenset({"claim_binding", "producer_flow", "semantic_facts"}),
)
