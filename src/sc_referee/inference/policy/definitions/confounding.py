"""Confounding R1-R4 declaration with exact provider-bound thresholds."""
from sc_referee.inference.policy.schema import FactRef, ProofRule, ProviderInvocation, RelationPremise, ValidityPolicy

POLICY = ValidityPolicy(
    id="confounding.v2",
    scope=(RelationPremise("ModeledContrastClaim", ()),),
    rules=(
        ProofRule("R1_STRUCTURAL_ALIAS", (
            RelationPremise("ExactTargetReportBinding", ()),
            RelationPremise("RequiredFactsRatified", ()),
        ), (ProviderInvocation(
            "exact_rational_rank.v1", "1",
            "sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4",
            {"matrix": FactRef("ModeledDesignMatrix", {}),
             "target_column": FactRef("TargetColumn", {})}, "TargetAliased",
        ),), "VIOLATION_WITNESS", "blocker", ()),
        ProofRule("R2_GRADED_OMITTED_CONFOUNDING", (
            RelationPremise("OmittedNuisancePresent", ()),
            RelationPremise("ModeledDesignAndLevelsExact", ()),
            RelationPremise("SetupConfirmed", ()),
        ), (ProviderInvocation(
            "confounding_metrics_q.v1", "1",
            "sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4",
            {"target": FactRef("TargetIndicator", {}), "included": FactRef("IncludedTerms", {}),
             "omitted": FactRef("OmittedTerms", {}), "nuisance": FactRef("NuisanceTerms", {}),
             "omitted_r2_threshold": (1, 100), "vif_threshold": 10}, "OmittedNuisancePresent",
        ), ProviderInvocation(
            "confounding_metrics_q.v1", "1",
            "sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4",
            {"target": FactRef("TargetIndicator", {}), "included": FactRef("IncludedTerms", {}),
             "omitted": FactRef("OmittedTerms", {}), "nuisance": FactRef("NuisanceTerms", {}),
             "omitted_r2_threshold": (1, 100), "vif_threshold": 10}, "OmittedPartialR2AtLeast",
        ),), "VIOLATION_WITNESS", "major", ("declared_nuisance_model",)),
        ProofRule("R3_NEAR_COLLINEAR", (
            RelationPremise("StructuralAliasRefuted", ()),
            RelationPremise("OmittedConfoundingRefuted", ()),
        ), (ProviderInvocation(
            "confounding_metrics_q.v1", "1",
            "sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4",
            {"target": FactRef("TargetIndicator", {}), "included": FactRef("IncludedTerms", {}),
             "omitted": FactRef("OmittedTerms", {}), "nuisance": FactRef("NuisanceTerms", {}),
             "omitted_r2_threshold": (1, 100), "vif_threshold": 10}, "VifAtLeast",
        ),), "CLEAN_PROOF", "informational", ()),
        ProofRule("R4_ESTIMABLE", (
            RelationPremise("OmittedConfoundingRefuted", ()),
            RelationPremise("NearCollinearityRefuted", ()),
        ), (ProviderInvocation(
            "exact_rational_rank.v1", "1",
            "sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4",
            {"matrix": FactRef("ModeledDesignMatrix", {}),
             "target_column": FactRef("TargetColumn", {})}, "TargetEstimable",
        ), ProviderInvocation(
            "confounding_metrics_q.v1", "1",
            "sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4",
            {"target": FactRef("TargetIndicator", {}), "included": FactRef("IncludedTerms", {}),
             "omitted": FactRef("OmittedTerms", {}), "nuisance": FactRef("NuisanceTerms", {}),
             "omitted_r2_threshold": (1, 100), "vif_threshold": 10}, "OmittedPartialR2Below",
        ), ProviderInvocation(
            "confounding_metrics_q.v1", "1",
            "sha256:13d26eddc19def337b6a34c8c09f3552f829fdf9fbae1358745505188614eef4",
            {"target": FactRef("TargetIndicator", {}), "included": FactRef("IncludedTerms", {}),
             "omitted": FactRef("OmittedTerms", {}), "nuisance": FactRef("NuisanceTerms", {}),
             "omitted_r2_threshold": (1, 100), "vif_threshold": 10}, "VifBelow",
        )), "CLEAN_PROOF", "pass", ()),
    ),
    required_coverage=frozenset({"claim_binding", "producer_flow", "semantic_facts"}),
)
