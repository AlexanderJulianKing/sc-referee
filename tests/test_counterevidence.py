from copy import deepcopy

import yaml

from sc_referee.detectors.counterevidence import (
    check_lineage_target,
    check_orientation,
    check_report_qualification,
    check_scale,
    execute_counterevidence_protocol,
)


def _case(project_root):
    return yaml.safe_load(
        (project_root / "examples/walking-skeleton/fixture.lock.yaml").read_text()
    )


def test_each_counterevidence_check_executes_independently(project_root) -> None:
    case = _case(project_root)
    outcomes = [
        check_orientation(case),
        check_scale(case),
        check_report_qualification(case),
        check_lineage_target(case),
    ]
    assert [item.check_id for item in outcomes] == [
        "check:orientation",
        "check:scale",
        "check:report-qualification",
        "check:lineage-target",
    ]
    assert all(item.status == "completed" for item in outcomes)
    assert all(item.outcome == "no_counterevidence" for item in outcomes)
    assert all(item.evidence_ids for item in outcomes)


def test_each_decisive_unavailable_or_counterevidence_path_is_recorded(project_root) -> None:
    base = _case(project_root)

    orientation_case = deepcopy(base)
    orientation_case["observed_result"]["orientation"] = {
        "state": "unknown",
        "rationale": "Test mutation",
        "evidence_refs": [],
    }
    assert check_orientation(orientation_case).status == "unavailable"

    scale_case = deepcopy(base)
    scale_case["observed_result"]["scale"]["value"] = "different units"
    assert check_scale(scale_case).outcome == "counterevidence_found"

    report_case = deepcopy(base)
    report_case["claim"]["extraction"]["independently_verified"] = False
    assert check_report_qualification(report_case).status == "unavailable"

    lineage_case = deepcopy(base)
    lineage_case["observed_result"]["lineage_status"] = "partial"
    assert check_lineage_target(lineage_case).status == "unavailable"

    records = execute_counterevidence_protocol(lineage_case)
    assert len(records) == 4
    assert records[-1]["outcome"] == "inconclusive"
