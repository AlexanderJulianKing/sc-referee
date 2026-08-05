from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from scripts.build_first_direct_three_case_pilot_authoring import (
    build_first_direct_three_case_pilot_authoring,
)
from scripts.record_first_direct_three_case_pilot_authors import (
    PilotAuthorRecordError,
    _freeze_case,
    parse_author_response,
    validate_author_response,
)


def _valid_case(case_id: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "input_file": {
            "relative_path": "inputs/stations.csv",
            "content": "scheduled,eligible,events\n96,72,18\n",
        },
        "producer_file": {
            "relative_path": "workflow/analysis.py",
            "content": (
                "from pathlib import Path\n"
                "rows = Path('inputs/stations.csv').read_text().splitlines()\n"
                "report = '[selected-result] target=all; events=18; exposure=72; rate=0.25\\n'\n"
                "Path('results/report.md').write_text(report)\n"
            ),
        },
        "report_file": {
            "relative_path": "results/report.md",
            "content": "[selected-result] target=all; events=18; exposure=72; rate=0.25\n",
        },
        "author_declaration": {
            "declaration_state": "one_selected_result",
            "selected_result_projection": {
                "result_span": {"start_line": 1, "end_line": 1},
                "producer_span": {"start_line": 4, "end_line": 4},
            },
            "candidate_result_spans": [],
            "unsupported_producer_spans": [],
        },
    }


def test_parse_author_response_requires_one_unfenced_object() -> None:
    assert parse_author_response('{"a": 1}') == {"a": 1}
    with pytest.raises(PilotAuthorRecordError, match="unfenced"):
        parse_author_response('```json\n{"a": 1}\n```')


def test_validate_author_response_accepts_exact_assigned_case_set(project_root: Path) -> None:
    assignment = build_first_direct_three_case_pilot_authoring(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]["author_assignments"][1]
    response = {
        "author_participant_id": assignment["participant"]["participant_id"],
        "authored_cases": [_valid_case(assignment["case_ids"][0])],
    }
    assert validate_author_response(response, assignment) == response["authored_cases"]

    wrong = deepcopy(response)
    wrong["authored_cases"][0]["case_id"] = "case:00000000000000000000"
    with pytest.raises(PilotAuthorRecordError, match="schema failed"):
        validate_author_response(wrong, assignment)


def test_validate_author_response_rejects_noncanonical_files_and_spans(
    project_root: Path,
) -> None:
    assignment = build_first_direct_three_case_pilot_authoring(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]["author_assignments"][1]
    response = {
        "author_participant_id": assignment["participant"]["participant_id"],
        "authored_cases": [_valid_case(assignment["case_ids"][0])],
    }
    wrong_path = deepcopy(response)
    wrong_path["authored_cases"][0]["input_file"]["relative_path"] = "../stations.csv"
    with pytest.raises(PilotAuthorRecordError, match="outside"):
        validate_author_response(wrong_path, assignment)

    wrong_span = deepcopy(response)
    wrong_span["authored_cases"][0]["author_declaration"]["selected_result_projection"][
        "producer_span"
    ]["end_line"] = 99
    with pytest.raises(PilotAuthorRecordError, match="outside retained bytes"):
        validate_author_response(wrong_span, assignment)


def test_redundant_selected_candidate_requires_frozen_canonicalization(
    project_root: Path,
) -> None:
    assignment = build_first_direct_three_case_pilot_authoring(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]["author_assignments"][1]
    case = _valid_case(assignment["case_ids"][0])
    selected_span = case["author_declaration"]["selected_result_projection"]["result_span"]
    case["author_declaration"]["candidate_result_spans"] = [deepcopy(selected_span)]
    response = {
        "author_participant_id": assignment["participant"]["participant_id"],
        "authored_cases": [case],
    }
    with pytest.raises(PilotAuthorRecordError, match="inconsistent"):
        validate_author_response(response, assignment)
    assert validate_author_response(
        response, assignment, permit_redundant_selected_candidate=True
    ) == [case]


def test_frozen_canonicalization_rejects_distinct_candidate_span(
    project_root: Path,
) -> None:
    assignment = build_first_direct_three_case_pilot_authoring(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]["author_assignments"][1]
    case = _valid_case(assignment["case_ids"][0])
    case["report_file"]["content"] += "non-result note\n"
    case["author_declaration"]["candidate_result_spans"] = [{"start_line": 2, "end_line": 2}]
    response = {
        "author_participant_id": assignment["participant"]["participant_id"],
        "authored_cases": [case],
    }
    with pytest.raises(PilotAuthorRecordError, match="conflicts"):
        validate_author_response(response, assignment, permit_redundant_selected_candidate=True)


def test_freeze_case_materializes_only_three_files_and_author_metadata(
    project_root: Path, tmp_path: Path
) -> None:
    assignment = build_first_direct_three_case_pilot_authoring(project_root)[
        "PILOT_AUTHORING_PROTOCOL.json"
    ]["author_assignments"][1]
    case = _valid_case(assignment["case_ids"][0])
    frozen = _freeze_case(
        case,
        participant=assignment["participant"],
        authored_at="2026-08-05T02:30:00Z",
        frozen_at="2026-08-05T02:31:00Z",
        cases_root=tmp_path / "cases",
        declarations_root=tmp_path / "declarations",
        manifests_root=tmp_path / "manifests",
    )
    case_root = tmp_path / "cases" / assignment["case_ids"][0].removeprefix("case:")
    assert sorted(
        path.relative_to(case_root).as_posix() for path in case_root.rglob("*") if path.is_file()
    ) == [
        "inputs/stations.csv",
        "results/report.md",
        "workflow/analysis.py",
    ]
    assert frozen["declaration"]["declaration_state"] == "one_selected_result"
    assert frozen["manifest"]["qualification_authority"] == "none_retained_author_case_only"
