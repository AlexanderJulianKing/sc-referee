from copy import deepcopy

import pytest
import yaml

from sc_referee.core.ids import semantic_digest
from sc_referee.detectors.admission import AdmissionContext, admit_finding
from sc_referee.detectors.claim_result_agreement import ClaimResultDirectionDetector


def _valid_admission(case, output):
    detector = ClaimResultDirectionDetector()
    assert output.finding_draft is not None
    return AdmissionContext(
        finding_draft=output.finding_draft,
        source_references_resolved=True,
        detector_qualification_applies=True,
        wording_constraints_satisfied=True,
        expected_deterministic_input_digest=semantic_digest(case),
        required_counterevidence_check_ids=detector.counterevidence_check_ids,
        non_inferences=detector.non_inferences,
    )


def test_contradiction_yields_finding(project_root) -> None:
    case = yaml.safe_load(
        (project_root / "examples/walking-skeleton/fixture.lock.yaml").read_text()
    )
    case["source_references_verified"] = True
    output = ClaimResultDirectionDetector().evaluate(case)
    finding = admit_finding(output.detector_result, _valid_admission(case, output))
    assert output.finding_draft is not None
    assert finding is not None
    assert finding["admission"]["direct_entailment"] is True
    assert output.material_question is None


def test_hard_negative_yields_no_finding(project_root) -> None:
    case = yaml.safe_load(
        (project_root / "examples/walking-skeleton/fixture.lock.yaml").read_text()
    )
    case["claim"]["proposition"]["direction"] = "negative"
    output = ClaimResultDirectionDetector().evaluate(case)
    assert output.finding_draft is None
    assert output.detector_result["state"] == "no_issue_detected_within_coverage"


def test_unknown_orientation_yields_question_not_finding(project_root) -> None:
    case = yaml.safe_load(
        (project_root / "examples/walking-skeleton/fixture.lock.yaml").read_text()
    )
    case["observed_result"]["orientation"] = {
        "state": "unknown",
        "rationale": "Test mutation",
        "evidence_refs": [],
    }
    output = ClaimResultDirectionDetector().evaluate(case)
    assert output.finding_draft is None
    assert output.material_question is not None
    assert output.detector_result["state"] == "insufficient_semantics"


def test_unverified_source_references_block_finding(project_root) -> None:
    case = yaml.safe_load(
        (project_root / "examples/walking-skeleton/fixture.lock.yaml").read_text()
    )
    case["source_references_verified"] = False
    output = ClaimResultDirectionDetector().evaluate(case)
    assert output.detector_result["state"] == "finding_candidate"
    context = _valid_admission(case, output)
    context = AdmissionContext(**{**context.__dict__, "source_references_resolved": False})
    assert admit_finding(output.detector_result, context) is None


@pytest.mark.parametrize("premise_index", [0, 1, 2, 3, 4])
@pytest.mark.parametrize("premise_state", ["unknown", "conflicted", "refuted"])
def test_every_material_non_established_premise_blocks_finding(
    project_root, premise_index, premise_state
) -> None:
    case = yaml.safe_load(
        (project_root / "examples/walking-skeleton/fixture.lock.yaml").read_text()
    )
    output = ClaimResultDirectionDetector().evaluate(case)
    result = deepcopy(output.detector_result)
    result["premise_evaluations"][premise_index]["state"] = premise_state
    assert admit_finding(result, _valid_admission(case, output)) is None


@pytest.mark.parametrize(
    ("mutation", "context_change"),
    [
        (lambda result: result.update(state="insufficient_semantics"), {}),
        (lambda result: result.update(detector_maturity="experimental"), {}),
        (lambda result: result["applicability"].update(status="uncertain"), {}),
        (lambda result: result["applicability"]["unsupported_constructs"].append("opaque"), {}),
        (lambda result: result["coverage"].update(status="not_covered"), {}),
        (lambda result: result["coverage"]["gaps"].append("unknown scale"), {}),
        (lambda result: result["unavailable_evidence"].append("required source"), {}),
        (
            lambda result: result["candidate"]["unresolved_material_premise_ids"].append(
                "premise:x"
            ),
            {},
        ),
        (lambda result: result["counterevidence_execution"][0].update(status="unavailable"), {}),
        (
            lambda result: result["counterevidence_execution"][0].update(
                outcome="counterevidence_found"
            ),
            {},
        ),
        (lambda result: result["counterevidence_execution"].pop(), {}),
        (lambda result: result.update(deterministic_input_digest="sha256:" + "0" * 64), {}),
        (lambda result: None, {"detector_qualification_applies": False}),
        (lambda result: None, {"wording_constraints_satisfied": False}),
        (lambda result: None, {"source_references_resolved": False}),
    ],
)
def test_admission_fails_closed_for_each_gate(project_root, mutation, context_change) -> None:
    case = yaml.safe_load(
        (project_root / "examples/walking-skeleton/fixture.lock.yaml").read_text()
    )
    output = ClaimResultDirectionDetector().evaluate(case)
    result = deepcopy(output.detector_result)
    mutation(result)
    context = _valid_admission(case, output)
    context = AdmissionContext(**{**context.__dict__, **context_change})
    assert admit_finding(result, context) is None


def test_candidate_wording_must_equal_finding_wording(project_root) -> None:
    case = yaml.safe_load(
        (project_root / "examples/walking-skeleton/fixture.lock.yaml").read_text()
    )
    output = ClaimResultDirectionDetector().evaluate(case)
    context = _valid_admission(case, output)
    draft = deepcopy(dict(context.finding_draft))
    draft["summary"] = "The entire paper is invalid."
    context = AdmissionContext(**{**context.__dict__, "finding_draft": draft})
    assert admit_finding(output.detector_result, context) is None


def test_scale_mismatch_abstains_without_finding(project_root) -> None:
    case = yaml.safe_load(
        (project_root / "examples/walking-skeleton/fixture.lock.yaml").read_text()
    )
    case["observed_result"]["scale"]["value"] = "log expression units"
    output = ClaimResultDirectionDetector().evaluate(case)
    assert output.detector_result["state"] == "insufficient_semantics"
    assert output.finding_draft is None
    scale_check = next(
        item
        for item in output.detector_result["counterevidence_execution"]
        if item["check_id"] == "check:scale"
    )
    assert scale_check["outcome"] == "counterevidence_found"


def test_comparison_mismatch_abstains_without_finding(project_root) -> None:
    case = yaml.safe_load(
        (project_root / "examples/walking-skeleton/fixture.lock.yaml").read_text()
    )
    case["claim"]["proposition"]["comparison"] = "treated versus placebo"
    output = ClaimResultDirectionDetector().evaluate(case)
    assert output.detector_result["state"] == "insufficient_semantics"
    assert output.finding_draft is None
    comparison_check = next(
        item
        for item in output.detector_result["counterevidence_execution"]
        if item["check_id"] == "check:orientation"
    )
    assert comparison_check["outcome"] == "counterevidence_found"
