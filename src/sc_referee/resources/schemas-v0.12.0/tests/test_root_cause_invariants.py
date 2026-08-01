from copy import deepcopy

from test_examples import invalid, load


def test_stage1_root_cause_identity_cannot_reconcile_other_reviews():
    review = load("agent-review.example.json")
    review["root_cause_identity"]["reconciled_stage1_candidates"] = [
        {"review_ref": {"record_type": "agent_review", "record_id": "review:other"},
         "candidate_root_cause_id": "root-cause-candidate:other"}
    ]
    invalid(review, "agent_review")


def test_stage2_demonstrated_issue_requires_candidate_set_and_equivalence_evidence():
    review = load("agent-review.stage2.example.json")
    review["root_cause_identity"]["reconciled_stage1_candidates"] = []
    invalid(review, "agent_review")
    review = load("agent-review.stage2.example.json")
    review["root_cause_identity"]["equivalence_evidence"] = []
    invalid(review, "agent_review")


def test_positive_adjudication_requires_typed_verified_root_cause():
    adjudication = load("benchmark-adjudication.example.json")
    adjudication["adjudicated_root_cause_refs"] = []
    invalid(adjudication, "benchmark_adjudication")
    adjudication = load("benchmark-adjudication.example.json")
    adjudication["root_cause_reconciliation_status"] = "unresolved"
    invalid(adjudication, "benchmark_adjudication")


def test_nonpositive_fixture_cannot_claim_a_positive_root_cause():
    fixture = load("benchmark-fixture.example.json")
    fixture["expected_root_cause_refs"] = [
        {"record_type": "adjudicated_root_cause", "record_id": "root-cause:forbidden"}
    ]
    invalid(fixture, "benchmark_fixture")


def test_adjudicated_root_cause_requires_bounded_exclusion():
    root_cause = load("adjudicated-root-cause.example.json")
    root_cause["stronger_claims_excluded"] = []
    invalid(root_cause, "adjudicated_root_cause")


def test_bundle_requires_root_cause_collection():
    bundle = load("audit-bundle.example.json")
    del bundle["adjudicated_root_causes"]
    invalid(bundle, "audit_bundle")
