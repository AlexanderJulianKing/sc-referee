from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_stage1_recovery_fable_addition_calibration import (
    ADDITION_CONTEXTS,
    ADDITION_RELATIVE,
    CALIBRATION_SUITE_DIGEST,
    EXPECTED_CALIBRATION_VERDICTS,
    FABLE_MODEL_ID,
    FROZEN_AT,
    TEMPLATE_BY_ADDITION,
    build_first_direct_stage1_recovery_fable_addition_calibration,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADDITION_ROOT = PROJECT_ROOT / ADDITION_RELATIVE


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(path: Path, field: str) -> dict[str, Any]:
    record = _load(path)
    supplied = record.pop(field)
    assert supplied == semantic_digest(record)
    record[field] = supplied
    return record


def test_fable_addition_calibration_is_frozen_and_additive_only() -> None:
    enrollment = _replay(ADDITION_ROOT / "PARTICIPANT_ENROLLMENT.json", "enrollment_digest")
    protocol = _replay(ADDITION_ROOT / "CALIBRATION_PROTOCOL.json", "protocol_digest")
    amendment = _replay(ADDITION_ROOT / "ADDITION_AMENDMENT.json", "amendment_digest")

    assert enrollment["participant_count"] == 2
    assert enrollment["provider_participation"] == {"Anthropic": 2}
    assert enrollment["superseded_participant_ids"] == []
    assert enrollment["frozen_at"] == FROZEN_AT
    for participant in enrollment["participants"]:
        supplied = participant.pop("configuration_digest")
        assert supplied == semantic_digest(participant)
        participant["configuration_digest"] = supplied
        assert participant["provider"] == "Anthropic"
        assert participant["model_id"] == FABLE_MODEL_ID
        assert participant["model_name"] == "Claude Fable 5"
        assert participant["agent_surface"] == "Claude Code CLI"
        assert participant["agent_version"] == "2.1.221"
        assert participant["calibration_suite_digest"] == CALIBRATION_SUITE_DIGEST
        assert (
            participant["execution_context_id"] == ADDITION_CONTEXTS[participant["participant_id"]]
        )

    assert protocol["expected_verdicts"] == EXPECTED_CALIBRATION_VERDICTS
    assert protocol["execution_state"] == "frozen_not_started"
    assert protocol["scientific_label_count"] == protocol["detector_outcome_count"] == 0
    for assignment in protocol["assignments"]:
        profile = assignment["command_profile"]
        assert profile["model_alias_argument"] == "fable"
        assert profile["model_usage_post_verification_required"] is True
        assert (
            assignment["template_participant_id"]
            == (TEMPLATE_BY_ADDITION[assignment["participant_id"]])
        )

    assert amendment["codex_configurations_superseded"] is False
    assert amendment["codex_configurations_remain_enrolled_and_calibrated"] is True
    assert amendment["maintainer_directed"] is True
    assert amendment["adr_reference"] == "ADR-0066-CROSS-MODEL-SINGLE-PROVIDER-REVIEW-PANEL.md"
    assert amendment["calibration_required_before_scientific_participation"] is True
    assert amendment["scientific_label_count"] == amendment["detector_outcome_count"] == 0


def test_fable_addition_calibration_attempts_are_retained_pass_and_model_verified() -> None:
    ledger = _replay(ADDITION_ROOT / "CALIBRATION_LEDGER.json", "ledger_digest")
    assert (
        ledger["ledger_digest"]
        == "sha256:6ae6507fa76c9444386f3c12dda0b141a496cfb57e0f3fefc3539d15a8dda542"
    )
    assert ledger["summary"]["passed_count"] == 2
    assert ledger["summary"]["failed_count"] == 0
    assert ledger["summary"]["all_reviewer_configurations_passed"] is True
    for entry in ledger["entries"]:
        assert entry["calibration_status"] == "passed"
        assert entry["calibration_evaluation"]["exact_expected_verdict_count"] == 6
        assert entry["calibration_evaluation"]["invented_material_premise_count"] == 0
        assert entry["model_id"] == FABLE_MODEL_ID
        capture = _replay(
            ADDITION_ROOT
            / "incoming"
            / f"{str(entry['participant_id']).removeprefix('actor:')}.json",
            "capture_digest",
        )
        process = _replay(
            ADDITION_ROOT
            / str(capture["transport"]["process_capture_relative_path"])
            / "capture.json",
            "capture_digest",
        )
        assert FABLE_MODEL_ID in process["provider_model_usage_ids"]
        assert process["return_code"] == 0
        assert process["reported_session_id"] == capture["call_identity_id"]
        final_bytes = (
            ADDITION_ROOT
            / str(capture["transport"]["process_capture_relative_path"])
            / "final-response.bin"
        ).read_bytes()
        assert sha256_digest(final_bytes) == process["final_response_digest"]


def test_fable_addition_calibration_builder_is_write_once() -> None:
    before = {path.name: sha256_digest(path.read_bytes()) for path in ADDITION_ROOT.glob("*.json")}
    with pytest.raises(FileExistsError, match="already frozen"):
        build_first_direct_stage1_recovery_fable_addition_calibration(PROJECT_ROOT)
    assert before == {
        path.name: sha256_digest(path.read_bytes()) for path in ADDITION_ROOT.glob("*.json")
    }
