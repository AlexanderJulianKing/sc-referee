from copy import deepcopy

from test_examples import errors, invalid, load


def test_experimental_evaluation_candidate_state_is_closed():
    result = load("detector-result.evaluation-candidate.example.json")
    assert not errors(result, "detector_result")
    result["detector_maturity"] = "validated"
    invalid(result, "detector_result")


def test_finding_candidate_still_rejects_experimental_maturity():
    result = load("detector-result.example.json")
    result["detector_maturity"] = "experimental"
    invalid(result, "detector_result")


def test_evaluation_state_requires_exact_resolved_material_premises():
    result = load("detector-result.evaluation-candidate.example.json")
    result["candidate"]["material_premise_ids"] = []
    invalid(result, "detector_result")
    result = load("detector-result.evaluation-candidate.example.json")
    result["candidate"]["unresolved_material_premise_ids"] = ["premise:unknown"]
    invalid(result, "detector_result")


def test_complete_case_requires_a_result_projection():
    outcome = load("detector-case-outcome.example.json")
    outcome["detector_result_outcomes"] = []
    invalid(outcome, "detector_case_outcome")


def test_result_projection_execution_class_is_derived_from_state():
    outcome = load("detector-case-outcome.example.json")
    outcome["detector_result_outcomes"][0]["execution_class"] = "detector_error"
    invalid(outcome, "detector_case_outcome")
    outcome["detector_result_outcomes"][0]["state"] = "detector_error"
    assert not errors(outcome, "detector_case_outcome")


def test_legacy_incomplete_case_is_fail_closed():
    outcome = load("detector-case-outcome.example.json")
    outcome["metric_input_status"] = "legacy_source_projection_unavailable"
    outcome["detector_result_outcomes"] = []
    outcome["metric_eligible"] = False
    assert not errors(outcome, "detector_case_outcome")
    outcome["metric_eligible"] = True
    invalid(outcome, "detector_case_outcome")


def test_metric_set_requires_each_declared_metric_exactly_once():
    metric_set = load("qualification-metric-set.example.json")
    metric_set["metrics"][1]["metric_name"] = metric_set["metrics"][0]["metric_name"]
    invalid(metric_set, "qualification_metric_set")


def test_zero_denominator_requires_null_estimate():
    metric_set = load("qualification-metric-set.example.json")
    metric_set["metrics"][0]["denominator"] = 0
    metric_set["metrics"][0]["estimate"] = 0
    invalid(metric_set, "qualification_metric_set")
    metric_set["metrics"][0]["estimate"] = None
    assert not errors(metric_set, "qualification_metric_set")


def test_not_estimable_interval_requires_null_bounds():
    metric_set = load("qualification-metric-set.example.json")
    metric_set["metrics"][0]["interval"]["lower"] = 0
    invalid(metric_set, "qualification_metric_set")
