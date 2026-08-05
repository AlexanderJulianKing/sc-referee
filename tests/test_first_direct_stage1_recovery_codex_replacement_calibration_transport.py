from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts import (
    record_first_direct_stage1_recovery_codex_replacement_calibration as record_module,
)
from scripts import run_first_direct_stage1_recovery_codex_replacement_calibration as run_module
from scripts.build_first_direct_stage1_recovery_calibration import (
    EXPECTED_CALIBRATION_VERDICTS,
)
from scripts.build_first_direct_stage1_recovery_codex_replacement_calibration import (
    CODEX_REPLACEMENT_RELATIVE,
)

SYSTEM_PROMPT = "Frozen stage-one reviewer system prompt."
SYSTEM_PROMPT_DIGEST = sha256_digest(SYSTEM_PROMPT)
PARTICIPANT_IDS = (
    "actor:stage1-recovery-codex-03",
    "actor:stage1-recovery-codex-04",
)


def _output_schema(participant_id: str) -> dict[str, Any]:
    case_ids = sorted(EXPECTED_CALIBRATION_VERDICTS)
    verdicts = sorted(set(EXPECTED_CALIBRATION_VERDICTS.values()))
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["reviewer_participant_id", "calibration_results"],
        "properties": {
            "reviewer_participant_id": {"const": participant_id},
            "calibration_results": {
                "type": "array",
                "minItems": 6,
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "calibration_case_id",
                        "verdict",
                        "invented_material_premise",
                        "evidence_basis",
                        "rationale",
                    ],
                    "properties": {
                        "calibration_case_id": {"enum": case_ids},
                        "verdict": {"enum": verdicts},
                        "invented_material_premise": {"const": False},
                        "evidence_basis": {"const": "stated_evidence_only"},
                        "rationale": {"type": "string", "minLength": 1},
                    },
                },
            },
        },
    }


def _assignment(participant_id: str) -> dict[str, Any]:
    schema = _output_schema(participant_id)
    prompt = f"Calibrate {participant_id}."
    return {
        "participant_id": participant_id,
        "role": "stage1_reviewer",
        "provider": "OpenAI",
        "model_name": "GPT-5.6",
        "model_id": "gpt-5.6-sol",
        "agent_surface": "Codex CLI exec",
        "agent_version": "test",
        "reasoning_configuration": "high",
        "execution_context_id": f"context:{participant_id.removeprefix('actor:')}-v1",
        "configuration_digest": f"configuration:{participant_id}",
        "call_identity_id": f"call:{participant_id}",
        "system_prompt_digest": SYSTEM_PROMPT_DIGEST,
        "prompt": prompt,
        "prompt_digest": sha256_digest(prompt),
        "output_schema": schema,
        "output_schema_digest": semantic_digest(schema),
    }


def _protocol() -> dict[str, Any]:
    return {
        "protocol_digest": "sha256:" + "1" * 64,
        "participant_enrollment_digest": "sha256:" + "2" * 64,
        "execution_state": "frozen_not_started",
        "expected_verdicts": EXPECTED_CALIBRATION_VERDICTS,
        "assignments": [_assignment(participant_id) for participant_id in PARTICIPANT_IDS],
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
    }


def _valid_response(participant_id: str) -> str:
    return json.dumps(
        {
            "reviewer_participant_id": participant_id,
            "calibration_results": [
                {
                    "calibration_case_id": case_id,
                    "verdict": verdict,
                    "invented_material_premise": False,
                    "evidence_basis": "stated_evidence_only",
                    "rationale": f"The stated evidence supports {verdict}.",
                }
                for case_id, verdict in sorted(EXPECTED_CALIBRATION_VERDICTS.items())
            ],
        },
        sort_keys=True,
    )


def _configure_protocol(monkeypatch: pytest.MonkeyPatch, protocol: dict[str, Any]) -> None:
    monkeypatch.setattr(record_module, "_protocol", lambda _root: protocol)
    monkeypatch.setattr(run_module, "_protocol", lambda _root: protocol)
    monkeypatch.setattr(
        run_module,
        "load_effective_execution_configuration",
        lambda _root: {
            "role_configurations": {"stage1_reviewer": {"system_prompt": SYSTEM_PROMPT}}
        },
    )


def _successful_attempt(assignment: dict[str, Any]) -> dict[str, Any]:
    participant_id = str(assignment["participant_id"])
    return {
        "assignment": assignment,
        "argv": ["codex", "exec", participant_id],
        "started_at": "2026-08-05T08:00:00Z",
        "completed_at": "2026-08-05T08:00:01Z",
        "return_code": 0,
        "stdout": f"stdout:{participant_id}".encode(),
        "stderr": b"",
        "final": _valid_response(participant_id).encode(),
        "process_error": None,
        "model_invoked": True,
    }


def test_recorder_strictly_validates_six_results_and_is_write_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = _protocol()
    _configure_protocol(monkeypatch, protocol)
    incoming_root = tmp_path / CODEX_REPLACEMENT_RELATIVE / "incoming"
    incoming_root.mkdir(parents=True)
    for participant_id in PARTICIPANT_IDS:
        capture = record_module.build_codex_replacement_calibration_capture(
            tmp_path,
            participant_id,
            _valid_response(participant_id),
            started_at="2026-08-05T08:00:00Z",
            completed_at="2026-08-05T08:00:01Z",
            captured_at="2026-08-05T08:00:02Z",
            transport={"surface": "test"},
        )
        write_normalized_json_once(
            incoming_root / f"{participant_id.removeprefix('actor:')}.json", capture
        )

    ledger = record_module.record_first_direct_stage1_recovery_codex_replacement_calibration(
        tmp_path
    )
    assert ledger["summary"]["assigned_reviewer_count"] == 2
    assert ledger["summary"]["passed_count"] == 2
    assert ledger["summary"]["failed_count"] == 0
    assert ledger["summary"]["all_reviewer_configurations_passed"] is True
    assert ledger["scientific_label_count"] == ledger["detector_outcome_count"] == 0
    for entry in ledger["entries"]:
        evaluation = entry["calibration_evaluation"]
        assert evaluation["structured_output_schema_valid"] is True
        assert evaluation["calibration_case_set_complete"] is True
        assert evaluation["exact_expected_verdict_count"] == 6
        assert evaluation["invented_material_premise_count"] == 0
        assert evaluation["pass"] is True
        assert evaluation["reason_codes"] == []

    persisted = json.loads(
        (tmp_path / CODEX_REPLACEMENT_RELATIVE / "CALIBRATION_LEDGER.json").read_text(
            encoding="utf-8"
        )
    )
    supplied = persisted.pop("ledger_digest")
    assert supplied == semantic_digest(persisted)
    with pytest.raises(FileExistsError, match="ledger already exists"):
        record_module.record_first_direct_stage1_recovery_codex_replacement_calibration(tmp_path)


def test_runner_retains_both_process_captures_before_failing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = _protocol()
    _configure_protocol(monkeypatch, protocol)
    barrier = threading.Barrier(2, timeout=2)

    def fake_run(assignment: dict[str, Any], _system_prompt: str) -> dict[str, Any]:
        barrier.wait()
        participant_id = str(assignment["participant_id"])
        if participant_id.endswith("-03"):
            raise OSError("synthetic spawn failure")
        attempt = _successful_attempt(assignment)
        attempt["return_code"] = 1
        attempt["final"] = b""
        attempt["process_error"] = "synthetic_transport_failure"
        return attempt

    monkeypatch.setattr(run_module, "_run_assignment", fake_run)
    with pytest.raises(ValueError, match="all process evidence was retained"):
        run_module.run_first_direct_stage1_recovery_codex_replacement_calibration(tmp_path)

    root = tmp_path / CODEX_REPLACEMENT_RELATIVE
    for participant_id in PARTICIPANT_IDS:
        process_root = root / "process-captures" / participant_id.removeprefix("actor:")
        record = json.loads((process_root / "capture.json").read_text(encoding="utf-8"))
        supplied = record.pop("capture_digest")
        assert supplied == semantic_digest(record)
        assert record["stdout_digest"] == sha256_digest((process_root / "stdout.bin").read_bytes())
        assert record["stderr_digest"] == sha256_digest((process_root / "stderr.bin").read_bytes())
        assert record["final_response_digest"] == sha256_digest(
            (process_root / "final-response.bin").read_bytes()
        )
        if participant_id.endswith("-03"):
            assert record["process_error"] == "transport_exception:OSError"
            assert record["model_invoked"] is False
            assert (process_root / "stderr.bin").read_bytes() == b"synthetic spawn failure"
        else:
            assert record["process_error"] == "synthetic_transport_failure"
            assert record["model_invoked"] is True

    assert not list((root / "incoming").glob("*.json"))


def test_concurrent_and_duplicate_invocations_cannot_reach_model_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = _protocol()
    _configure_protocol(monkeypatch, protocol)
    calls_started = threading.Event()
    release_calls = threading.Event()
    call_lock = threading.Lock()
    call_count = 0

    def blocked_success(assignment: dict[str, Any], _system_prompt: str) -> dict[str, Any]:
        nonlocal call_count
        with call_lock:
            call_count += 1
            if call_count == 2:
                calls_started.set()
        if not release_calls.wait(timeout=3):
            raise TimeoutError("test did not release both fresh calls")
        return _successful_attempt(assignment)

    monkeypatch.setattr(run_module, "_run_assignment", blocked_success)
    with ThreadPoolExecutor(max_workers=1) as executor:
        first = executor.submit(
            run_module.run_first_direct_stage1_recovery_codex_replacement_calibration,
            tmp_path,
        )
        assert calls_started.wait(timeout=2)
        with pytest.raises(FileExistsError, match="attempt already reserved"):
            run_module.run_first_direct_stage1_recovery_codex_replacement_calibration(tmp_path)
        with call_lock:
            assert call_count == 2
        release_calls.set()
        captures = first.result(timeout=4)

    assert [item["participant_id"] for item in captures] == list(PARTICIPANT_IDS)
    with pytest.raises(FileExistsError, match=r"capture already exists|attempt already reserved"):
        run_module.run_first_direct_stage1_recovery_codex_replacement_calibration(tmp_path)
    with call_lock:
        assert call_count == 2
