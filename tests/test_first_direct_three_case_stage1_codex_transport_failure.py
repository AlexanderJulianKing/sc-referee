from __future__ import annotations

from pathlib import Path

import pytest

from sc_referee.core.ids import semantic_digest
from scripts import record_first_direct_three_case_stage1_codex_transport_failure as module
from scripts.build_first_direct_three_case_stage1_protocol import REVIEW_RELATIVE
from scripts.record_first_direct_three_case_stage1_codex_transport_failure import (
    build_stage1_codex_transport_failure_ledger,
)


def test_codex_transport_failure_ledger_replays_exact_pre_inference_failures(
    project_root: Path,
) -> None:
    ledger = build_stage1_codex_transport_failure_ledger(project_root)
    assert ledger["summary"] == {
        "attempt_count": 2,
        "pre_inference_failure_count": 2,
        "reviewer_response_count": 0,
        "stage1_review_count": 0,
        "stage1_freeze_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "project_code_executed_count": 0,
    }
    assert ledger["ledger_digest"] == semantic_digest(
        {key: value for key, value in ledger.items() if key != "ledger_digest"}
    )
    assert all(item["model_inference_started"] is False for item in ledger["attempts"])
    assert all(item["review_admitted"] is False for item in ledger["attempts"])


def test_codex_transport_failure_replay_rejects_capture_drift(
    project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(
        module.EXPECTED_CAPTURE_DIGESTS,
        "actor:stage1-codex-01",
        "sha256:" + "0" * 64,
    )
    with pytest.raises(module.Stage1CodexTransportFailureError, match="does not replay"):
        build_stage1_codex_transport_failure_ledger(project_root)


def test_no_codex_review_was_admitted_after_transport_failure(project_root: Path) -> None:
    root = project_root / REVIEW_RELATIVE
    assert not (root / "incoming" / "stage1-codex-01.json").exists()
    assert not (root / "incoming" / "stage1-codex-02.json").exists()
    assert not (root / "stage1-captures").exists()
    assert not (root / "stage1-freezes").exists()
