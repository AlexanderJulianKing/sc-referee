from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_three_case_stage1_codex_duplicate_launch_recovery import (
    CODEX_ARTIFACT_DIGESTS,
    FAILURE_LEDGER_NAME,
    PROTOCOL_DIGEST,
    RECOVERY_AMENDMENT_NAME,
    build_first_direct_three_case_stage1_codex_duplicate_launch_recovery,
)
from scripts.build_first_direct_three_case_stage1_semantic_recovery_protocol import (
    REVIEW_RELATIVE,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = PROJECT_ROOT / REVIEW_RELATIVE


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(path: Path, field: str) -> dict[str, Any]:
    record = _load(path)
    supplied = record.pop(field)
    assert supplied == semantic_digest(record)
    record[field] = supplied
    return record


def test_duplicate_launch_failure_ledger_retains_exact_but_ineligible_codex_chains() -> None:
    ledger = _replay(REVIEW_ROOT / FAILURE_LEDGER_NAME, "ledger_digest")
    assert ledger["protocol_digest"] == PROTOCOL_DIGEST
    assert ledger["failure_class"] == "overlapping_duplicate_launcher_attempt_identity_collision"
    assert ledger["observed_failure"] == {
        "duplicate_launcher_model_calls_completed_before_persistence": True,
        "duplicate_response_bytes_retained": False,
        "duplicate_response_digests_known": False,
        "exception_site": "process_root.mkdir(parents=True)",
        "first_colliding_participant_id": "actor:stage1-recovery-codex-01",
        "persistence_exception": "FileExistsError",
        "unique_attempt_identity_established": False,
    }
    assert ledger["affected_participant_ids"] == sorted(CODEX_ARTIFACT_DIGESTS)
    assert ledger["retained_review_count"] == 6
    assert ledger["retained_artifact_admission"] == "ineligible_duplicate_attempt_identity"
    assert ledger["stage1_freeze_count"] == 0
    assert ledger["scientific_label_count"] == ledger["detector_outcome_count"] == 0

    retained = {str(item["participant_id"]): item for item in ledger["retained_artifacts"]}
    assert set(retained) == set(CODEX_ARTIFACT_DIGESTS)
    for participant_id, expected in CODEX_ARTIFACT_DIGESTS.items():
        item = retained[participant_id]
        assert item["retention_status"] == "retained_exact_but_label_ineligible"
        assert item["process_capture"]["capture_digest"] == expected["process_capture"]
        assert item["incoming_capture"]["capture_digest"] == expected["incoming_capture"]
        assert item["call_ledger"]["ledger_digest"] == expected["call_ledger"]
        assert item["call_ledger"]["review_count"] == 3
        assert len(item["call_ledger"]["review_capture_digests"]) == 3
        process = _replay(REVIEW_ROOT / item["process_capture"]["relative_path"], "capture_digest")
        incoming = _replay(
            REVIEW_ROOT / item["incoming_capture"]["relative_path"], "capture_digest"
        )
        call_ledger = _replay(REVIEW_ROOT / item["call_ledger"]["relative_path"], "ledger_digest")
        assert process["final_response_digest"] == incoming["raw_response_digest"]
        assert call_ledger["incoming_capture_digest"] == incoming["capture_digest"]

    implementation = ledger["controller_implementation"]
    assert (
        sha256_digest((PROJECT_ROOT / implementation["path"]).read_bytes())
        == implementation["content_digest"]
    )


def test_duplicate_launch_amendment_requires_fresh_calibrated_codex_and_preserves_claude() -> None:
    ledger = _load(REVIEW_ROOT / FAILURE_LEDGER_NAME)
    amendment = _replay(REVIEW_ROOT / RECOVERY_AMENDMENT_NAME, "amendment_digest")
    assert amendment["protocol_digest"] == PROTOCOL_DIGEST
    assert amendment["source_failure_ledger_digest"] == ledger["ledger_digest"]
    assert (
        amendment["decision"]
        == "abandon_both_affected_codex_configurations_and_recalibrate_fresh_replacements"
    )
    abandoned = amendment["abandoned_codex_configurations"]
    assert [str(item["participant_id"]) for item in abandoned] == sorted(CODEX_ARTIFACT_DIGESTS)
    assert all(item["panel_status"] == "abandoned_permanently_for_this_panel" for item in abandoned)
    requirements = amendment["replacement_requirements"]
    assert requirements["replacement_count"] == 2
    assert requirements["provider"] == "OpenAI"
    assert requirements["fresh_participant_ids_required"] is True
    assert requirements["fresh_execution_contexts_required"] is True
    assert requirements["fresh_call_identity_ids_required"] is True
    assert requirements["fresh_calibration_required_before_review"] is True
    assert requirements["both_replacements_must_pass"] is True
    assert requirements["replacement_review_calls_may_start_before_calibration_freeze"] is False
    assert requirements["preserved_case_orders"] == [item["case_order"] for item in abandoned]

    claude = amendment["preserved_unexposed_claude_configurations"]
    assert len(claude) == 2
    assert all(item["preservation_status"] == "authorized_unattempted_unchanged" for item in claude)
    assert not list((REVIEW_ROOT / "incoming").glob("stage1-recovery-claude-*.json"))
    assert not list((REVIEW_ROOT / "stage1-call-ledgers").glob("stage1-recovery-claude-*.json"))
    assert amendment["preserved_scientific_material"] == {
        "canonical_issue_class_scope": "issue-class:retained-subset-for-complete-domain",
        "case_orders_unchanged": True,
        "scientific_contract_unchanged": True,
        "semantic_recovery_contract_digest": amendment["preserved_scientific_material"][
            "semantic_recovery_contract_digest"
        ],
        "source_case_bindings_digest": amendment["preserved_scientific_material"][
            "source_case_bindings_digest"
        ],
        "workflow_bytes_unchanged": True,
        "workspace_manifests_unchanged": True,
    }
    assert amendment["replacement_calibration_state"] == "not_started"
    assert amendment["replacement_calibration_attempt_count"] == 0
    assert amendment["replacement_review_attempt_count"] == 0
    assert amendment["stage1_freeze_count"] == 0
    assert amendment["scientific_label_count"] == amendment["detector_outcome_count"] == 0


def test_duplicate_launch_recovery_builder_is_write_once() -> None:
    failure_path = REVIEW_ROOT / FAILURE_LEDGER_NAME
    amendment_path = REVIEW_ROOT / RECOVERY_AMENDMENT_NAME
    before = (sha256_digest(failure_path.read_bytes()), sha256_digest(amendment_path.read_bytes()))
    with pytest.raises(FileExistsError, match="already frozen"):
        build_first_direct_three_case_stage1_codex_duplicate_launch_recovery(PROJECT_ROOT)
    assert before == (
        sha256_digest(failure_path.read_bytes()),
        sha256_digest(amendment_path.read_bytes()),
    )
