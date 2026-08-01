from copy import deepcopy

import yaml

from sc_referee.detectors.sample_unit_dependence import SampleUnitDependenceQuestionDetector


def test_repeated_unknown_units_yield_linked_conditional_concern(project_root) -> None:
    case = yaml.safe_load(
        (project_root / "examples/walking-skeleton/fixture.lock.yaml").read_text()
    )
    case["repeated_identifier_observation"] = {
        "state": "observed",
        "repeated_values": ["d1", "d2"],
        "source_refs": case["observed_result"]["source_refs"],
    }
    result, concern = SampleUnitDependenceQuestionDetector().evaluate(case)
    assert result["state"] == "conditional_concern_candidate"
    assert concern is not None
    assert concern["material_question_id"] == case["material_question"]["question_id"]
    assert concern["record_type"] == "conditional_concern"


def test_unique_identifiers_yield_no_conditional_concern(project_root) -> None:
    case = yaml.safe_load(
        (project_root / "examples/walking-skeleton/fixture.lock.yaml").read_text()
    )
    case = deepcopy(case)
    case["repeated_identifier_observation"] = {
        "state": "observed",
        "repeated_values": [],
        "source_refs": case["observed_result"]["source_refs"],
    }
    result, concern = SampleUnitDependenceQuestionDetector().evaluate(case)
    assert result["state"] == "no_issue_detected_within_coverage"
    assert concern is None
