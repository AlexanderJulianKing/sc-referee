from __future__ import annotations

from copy import deepcopy

from sc_referee.core.ids import semantic_digest
from scripts.record_first_direct_three_case_pilot_authors_v2_failure import (
    _invalid_line_entries,
    build_first_direct_three_case_pilot_authors_v2_failure,
)


def test_v2_failure_ledger_replays_exact_retained_attempts(project_root) -> None:
    ledger = build_first_direct_three_case_pilot_authors_v2_failure(project_root)
    assert ledger["summary"] == {
        "assigned_author_context_count": 2,
        "model_attempt_count": 2,
        "response_case_count": 3,
        "transport_invalid_case_count": 2,
        "role_path_invalid_case_count": 1,
        "verified_selected_result_count": 0,
        "admitted_case_count": 0,
        "metric_eligible_case_count": 0,
        "project_code_executed_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
    }
    assert ledger["cohort_status"] == "rejected_before_authoring_admission"
    assert {
        item["provider"]: (item["input_capture_digest"], item["raw_response_digest"])
        for item in ledger["input_captures"]
    } == {
        "Anthropic": (
            "sha256:2617a109e25ab871a14ae1236db8220a18a1ad59b512e00318f406b2cc17f973",
            "sha256:63b9f31ac34e891fbeca5c4ece7bb12bcc607903de7b111ff19213d09a6b7810",
        ),
        "OpenAI": (
            "sha256:5b9a17b658f2ea7485085bc27b5a48899ecc4ea55c5cff619c5ae8626df55e43",
            "sha256:217688e149ed1f28dbf4111e33e7f81e729629a3452aed35da2ee4c2be3a4d36",
        ),
    }
    assert ledger["ledger_digest"] == semantic_digest(
        {key: value for key, value in ledger.items() if key != "ledger_digest"}
    )


def test_v2_failure_localizes_claude_terminators_and_codex_role_path(
    project_root,
) -> None:
    ledger = build_first_direct_three_case_pilot_authors_v2_failure(project_root)
    invalid = [
        item for item in ledger["entries"] if item["transport_status"] == "invalid_content_lines"
    ]
    role_invalid = [
        item
        for item in ledger["entries"]
        if item.get("role_path_status") == "invalid_producer_path"
    ]
    assert len(invalid) == 2
    assert all(item["transport_reason_codes"] == ["embedded_line_terminator"] for item in invalid)
    assert all(item["invalid_line_entries"] for item in invalid)
    assert len(role_invalid) == 1
    assert role_invalid[0]["provider"] == "OpenAI"
    assert role_invalid[0]["producer_relative_path"] == "produce.py"
    assert role_invalid[0]["role_path_reason_codes"] == ["producer_path_outside_workflow_role"]
    assert role_invalid[0]["admitted"] is False
    assert role_invalid[0]["metric_eligible"] is False


def test_invalid_line_entries_is_content_agnostic() -> None:
    response = {
        "authored_cases": [
            {
                "case_id": "case:any",
                "input_file": {"content_lines": ["a", "b\rc"]},
                "producer_file": {"content_lines": ["x\ny"]},
                "report_file": {"content_lines": ["z"]},
            }
        ]
    }
    assert _invalid_line_entries(deepcopy(response)) == [
        {
            "case_id": "case:any",
            "file_role": "input_file",
            "content_line_number": 2,
            "contains_lf": False,
            "contains_cr": True,
        },
        {
            "case_id": "case:any",
            "file_role": "producer_file",
            "content_line_number": 1,
            "contains_lf": True,
            "contains_cr": False,
        },
    ]
