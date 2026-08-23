from copy import deepcopy

from test_examples import invalid, load


def test_evaluation_candidate_cannot_grant_production_finding_authority():
    candidate = load("detector-evaluation-candidate.example.json")
    candidate["production_admission_permitted"] = True
    invalid(candidate, "detector_evaluation_candidate")
    candidate = load("detector-evaluation-candidate.example.json")
    candidate["production_finding_ref"] = {"record_type": "finding", "record_id": "finding:bad"}
    invalid(candidate, "detector_evaluation_candidate")


def test_stage3_review_requires_post_freeze_access_and_fresh_context():
    review = load("stage3-comparison-review.example.json")
    review["comparison_access"]["prior_review_context_reused"] = True
    invalid(review, "stage3_comparison_review")
    review = load("stage3-comparison-review.example.json")
    review["confidence_used_for_equivalence"] = True
    invalid(review, "stage3_comparison_review")


def test_reconciled_case_requires_exact_agreement_and_no_exclusion():
    outcome = load("detector-case-outcome.example.json")
    outcome["exact_cross_provider_agreement"] = False
    invalid(outcome, "detector_case_outcome")
    outcome = load("detector-case-outcome.example.json")
    outcome["exclusion_reasons"] = ["material disagreement"]
    invalid(outcome, "detector_case_outcome")


def test_public_development_case_cannot_be_promotion_evidence():
    outcome = load("detector-case-outcome.example.json")
    outcome["promotion_evidence_eligible"] = True
    invalid(outcome, "detector_case_outcome")
    metrics = load("qualification-metric-set.example.json")
    metrics["promotion_evidence_eligible"] = True
    invalid(metrics, "qualification_metric_set")


def test_deferred_threshold_policy_cannot_promote_detector():
    qualification = load("detector-qualification.example.json")
    qualification["outcome"] = "promoted"
    qualification["effective_maturity"] = "validated"
    invalid(qualification, "detector_qualification")


def test_frozen_adjudication_cannot_gain_backward_stage3_refs():
    adjudication = load("benchmark-adjudication.example.json")
    adjudication["stage3_detector_comparison_refs"] = [
        {"record_type": "detector_case_outcome", "record_id": "outcome:late"}
    ]
    invalid(adjudication, "benchmark_adjudication")


def test_bundle_requires_every_stage3_collection():
    for field in (
        "detector_evaluation_candidates",
        "stage3_comparison_reviews",
        "detector_case_outcomes",
        "qualification_metric_sets",
    ):
        bundle = load("audit-bundle.example.json")
        del bundle[field]
        invalid(bundle, "audit_bundle")
