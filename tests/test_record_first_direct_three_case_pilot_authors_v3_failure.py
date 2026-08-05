from __future__ import annotations

from pathlib import Path

import pytest

from sc_referee.core.ids import semantic_digest
from scripts import record_first_direct_three_case_pilot_authors_v3_failure as failure_module
from scripts.build_first_direct_three_case_pilot_authoring_v3 import PILOT_AUTHORING_V3_RELATIVE
from scripts.record_first_direct_three_case_pilot_authors import PilotAuthorRecordError
from scripts.record_first_direct_three_case_pilot_authors_v3 import (
    record_first_direct_three_case_pilot_authors_v3,
)
from scripts.record_first_direct_three_case_pilot_authors_v3_failure import (
    _negative_subscript_lines,
    build_first_direct_three_case_pilot_authors_v3_failure,
)


def test_v3_failure_ledger_replays_exact_retained_attempts(project_root: Path) -> None:
    ledger = build_first_direct_three_case_pilot_authors_v3_failure(project_root)
    assert ledger["summary"] == {
        "assigned_author_context_count": 2,
        "model_attempt_count": 2,
        "response_case_count": 3,
        "verified_selected_result_count": 2,
        "unsupported_selected_result_count": 1,
        "admitted_case_count": 0,
        "metric_eligible_case_count": 0,
        "project_code_executed_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
    }
    assert ledger["ledger_digest"] == semantic_digest(
        {key: value for key, value in ledger.items() if key != "ledger_digest"}
    )


def test_v3_failure_retains_two_verified_but_admits_none(project_root: Path) -> None:
    ledger = build_first_direct_three_case_pilot_authors_v3_failure(project_root)
    verified = [
        item for item in ledger["entries"] if item["validation_status"] == "verified_complete"
    ]
    unsupported = [
        item for item in ledger["entries"] if item["validation_status"] == "unsupported_structure"
    ]
    assert len(verified) == 2
    assert all(item["provider"] == "Anthropic" for item in verified)
    assert all(item["admitted"] is False and item["metric_eligible"] is False for item in verified)
    assert all(item["admission_status"] == "not_admitted_incomplete_cohort" for item in verified)
    assert len(unsupported) == 1
    assert unsupported[0]["provider"] == "OpenAI"
    assert unsupported[0]["validation_reason_codes"] == ["unsupported_selected_report_expression"]
    assert unsupported[0]["negative_subscript_lines"] == [6, 7, 8]
    assert unsupported[0]["admission_status"] == "rejected_static_intake"
    assert all(
        item["transport_status"] == "valid_physical_line_transport" for item in ledger["entries"]
    )
    assert all(item["role_path_status"] == "valid_exact_role_paths" for item in ledger["entries"])
    assert all(
        item["declaration_status"] == "valid_one_selected_result_declaration"
        for item in ledger["entries"]
    )


def test_negative_subscript_diagnostic_is_syntax_generic() -> None:
    source = "items = ['a', 'b']\nlast = items[-1]\nfirst = items[0]\n"
    assert _negative_subscript_lines(source) == [2]


def test_v3_admission_fails_atomically_on_localized_codex_case(project_root: Path) -> None:
    root = project_root / PILOT_AUTHORING_V3_RELATIVE
    materialized = (
        root / "AUTHORING_LEDGER.json",
        root / "cases",
        root / "author-declarations",
        root / "case-manifests",
        root / "case-contracts",
        root / "selected-result-derivations",
        root / "selected-result-validations",
    )
    assert not any(path.exists() for path in materialized)
    with pytest.raises(
        PilotAuthorRecordError,
        match=(
            r"case:7e2d0d333ffa5e630352.*"
            r"unsupported_selected_report_expression"
        ),
    ):
        record_first_direct_three_case_pilot_authors_v3(
            project_root, frozen_at="2026-08-05T05:18:00Z"
        )
    assert not any(path.exists() for path in materialized)


def test_v3_failure_replay_rejects_capture_drift(
    project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(failure_module, "CLAUDE_CAPTURE_DIGEST", "sha256:" + "0" * 64)
    with pytest.raises(PilotAuthorRecordError, match="Anthropic capture has drifted"):
        build_first_direct_three_case_pilot_authors_v3_failure(project_root)
