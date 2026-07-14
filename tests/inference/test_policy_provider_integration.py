from __future__ import annotations

from fractions import Fraction

from sc_referee.inference.policy.evaluate import PolicySnapshot, evaluate
from sc_referee.inference.proof.discharge import builtin_registry


def _policy(name):
    module = __import__(f"sc_referee.inference.policy.definitions.{name}", fromlist=["POLICY"])
    return module.POLICY


def _snapshot(*relations, facts=None, assumptions=()):
    return PolicySnapshot(
        True, frozenset({"p"}), frozenset({"p"}), frozenset(),
        frozenset({"claim_binding", "producer_flow", "semantic_facts"}),
        {relation: "PROVED" for relation in relations}, facts or {}, frozenset(assumptions),
    )


def test_allele_policy_uses_joint_wald_parity_end_to_end():
    policy = _policy("allele_harmonization")
    common = ("SignedReportClaim", "AllSourceToSinkSignFlowsDefinite")
    clean = evaluate(
        policy, "claim", _snapshot(*common, facts={
            "RatifiedJointReversals": (-1, -1), "AppliedJointMultiplier": 1,
        }), builtin_registry(),
    )
    violation = evaluate(
        policy, "claim", _snapshot(*common, "InconsistentInputMateriallyConsumed",
                                    "SignedSinkFormulaExact", facts={
            "RatifiedJointReversals": (-1, -1), "AppliedJointMultiplier": -1,
        }), builtin_registry(),
    )
    assert clean.outcome == "CLEAN_PROOF"
    assert violation.outcome == "VIOLATION_WITNESS"


def test_enrichment_policy_requires_joint_exact_recomputation():
    policy = _policy("enrichment_universe")
    facts = {
        "CorrectedPopulation": 100, "CorrectedTermSize": 10, "CorrectedDraws": 5,
        "CorrectedOverlap": 2,
        "CompleteRawPValueFamilyQ": (Fraction(1, 1000), Fraction(1, 50), Fraction(1, 20)),
        "TargetFamilyIndex": 0, "ActualCorrectionProcedure": "bh",
        "BoundAlphaQ": Fraction(1, 20), "ReportedAdjustedPValueQ": Fraction(3, 1000),
        "ReportedSignificantDecision": True, "PValueFamilyComplete": True,
    }
    violation = evaluate(
        policy, "claim", _snapshot(
            "OraReportClaim", "ReportConsumedMembershipContradiction",
            "ContradictoryCellMustProducesClaim", "CorrectedTableWellDefined", facts=facts,
        ), builtin_registry(),
    )
    inflated_only = evaluate(
        policy, "claim", _snapshot("OraReportClaim", "InflatedK", facts=facts), builtin_registry(),
    )
    assert violation.outcome == "VIOLATION_WITNESS"
    assert inflated_only.outcome == "ABSTAIN"


def test_coordinate_policy_obeys_exact_consumer_interval_contract():
    policy = _policy("coordinate_consumption")
    base = {
        "ExactContigLength": 101,
        "CoordinateRole": "slice_boundary",
        "CoordinateConsumerContractId": "past_end_sentinel.linear.v1",
    }
    legal = evaluate(
        policy, "claim", _snapshot("CoordinateReportClaim", "CoordinateUnavoidablyConsumed",
                                   facts={**base, "CoordinateValue": 101}), builtin_registry(),
    )
    illegal = evaluate(
        policy, "claim", _snapshot(
            "CoordinateReportClaim", "CoordinateUnavoidablyConsumed",
            "ExactContigIdentityAndLengthBound", "CoordinateMateriallyAffectsClaim",
            facts={**base, "CoordinateValue": 102},
        ), builtin_registry(),
    )
    assert legal.outcome == "CLEAN_PROOF"
    assert illegal.outcome == "VIOLATION_WITNESS"


def _confounding_facts(**updates):
    target = (0, 0, 0, 1, 0, 1, 1, 1)
    run = ((0,), (0,), (0,), (0,), (1,), (1,), (1,), (1,))
    facts = {
        "TargetIndicator": target,
        "IncludedTerms": tuple(() for _ in target),
        "OmittedTerms": run,
        "NuisanceTerms": run,
        "OmittedR2ThresholdQ": Fraction(1, 100),
        "VifThresholdQ": Fraction(10),
    }
    facts.update(updates)
    return facts


def test_confounding_r1_r4_preserve_blocker_major_informational_pass_precedence():
    policy = _policy("confounding")
    registry = builtin_registry()
    r1 = evaluate(policy, "claim", _snapshot(
        "ModeledContrastClaim", "ExactTargetReportBinding", "RequiredFactsRatified",
        facts={"ModeledDesignMatrix": ((1, 1), (2, 2)), "TargetColumn": 1},
    ), registry)
    r2 = evaluate(policy, "claim", _snapshot(
        "ModeledContrastClaim", "OmittedNuisancePresent", "ModeledDesignAndLevelsExact",
        "SetupConfirmed", facts=_confounding_facts(), assumptions=("declared_nuisance_model",),
    ), registry)
    high_vif_facts = _confounding_facts(
        OmittedTerms=tuple(() for _ in range(4)),
        TargetIndicator=(0, 0, 1, 1),
        IncludedTerms=((), (), (), ()),
        NuisanceTerms=((0,), (0,), (1,), (1,)),
    )
    r3 = evaluate(policy, "claim", _snapshot(
        "ModeledContrastClaim", "StructuralAliasRefuted", "OmittedConfoundingRefuted",
        facts=high_vif_facts,
    ), registry)
    r4_metrics = {
        "TargetIndicator": (0, 0, 1, 1), "IncludedTerms": ((), (), (), ()),
        "OmittedTerms": ((), (), (), ()), "NuisanceTerms": ((0,), (1,), (0,), (1,)),
        "OmittedR2ThresholdQ": Fraction(1, 100), "VifThresholdQ": Fraction(10),
    }
    r4 = evaluate(policy, "claim", _snapshot(
        "ModeledContrastClaim", "OmittedConfoundingRefuted", "NearCollinearityRefuted",
        facts={"ModeledDesignMatrix": ((1, 0), (0, 1)), "TargetColumn": 1, **r4_metrics},
    ), registry)
    assert (r1.outcome, r1.max_external_status) == ("VIOLATION_WITNESS", "blocker")
    assert (r2.outcome, r2.max_external_status) == ("VIOLATION_WITNESS", "major")
    assert (r3.outcome, r3.max_external_status) == ("CLEAN_PROOF", "informational")
    assert (r4.outcome, r4.max_external_status) == ("CLEAN_PROOF", "pass")
