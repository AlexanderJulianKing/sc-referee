from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_protocol import (
    REVIEW_RELATIVE,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts import (
    capture_first_direct_three_case_stage1_semantic_recovery_clean_claude_app as claude_module,
)
from scripts import (
    run_first_direct_three_case_stage1_semantic_recovery_clean_codex as codex_module,
)

SYSTEM_PROMPT = "Frozen calibrated stage-one reviewer system prompt."
SYSTEM_PROMPT_DIGEST = sha256_digest(SYSTEM_PROMPT)


def _call(participant_id: str, provider: str) -> dict[str, Any]:
    return {
        "participant_id": participant_id,
        "call_identity_id": f"call:{participant_id}",
        "participant": {
            "provider": provider,
            "model_id": "test-model",
            "reasoning_configuration": "high",
            "system_prompt_digest": SYSTEM_PROMPT_DIGEST,
        },
        "interaction_profile": (
            dict(claude_module.CLAUDE_INTERACTION_PROFILE)
            if provider == "Anthropic"
            else {"surface": "Codex CLI exec"}
        ),
    }


def _protocol() -> dict[str, Any]:
    return {
        "protocol_digest": "sha256:" + "1" * 64,
        "calls": [
            _call("actor:stage1-recovery-claude-01", "Anthropic"),
            _call("actor:stage1-recovery-claude-03", "Anthropic"),
            _call("actor:stage1-recovery-codex-03", "OpenAI"),
            _call("actor:stage1-recovery-codex-04", "OpenAI"),
        ],
    }


def _configure_codex(monkeypatch: pytest.MonkeyPatch, protocol: dict[str, Any]) -> None:
    monkeypatch.setattr(codex_module, "_protocol", lambda _root: protocol)
    monkeypatch.setattr(
        codex_module,
        "load_effective_execution_configuration",
        lambda _root: {
            "role_configurations": {
                "stage1_reviewer": {"system_prompt": SYSTEM_PROMPT},
            }
        },
    )


def _process_result(call: dict[str, Any], *, return_code: int) -> dict[str, Any]:
    participant_id = str(call["participant_id"])
    raw_response = b'{"reviews":[]}' if return_code == 0 else b""
    return {
        "participant_id": participant_id,
        "call": call,
        "started_at": "2026-08-05T09:00:00Z",
        "completed_at": "2026-08-05T09:00:01Z",
        "argv": ["codex", "exec", participant_id],
        "return_code": return_code,
        "stdout": f"stdout:{participant_id}".encode(),
        "stderr": f"stderr:{participant_id}".encode(),
        "raw_response": raw_response,
        "process_error": None if return_code == 0 else "synthetic_transport_failure",
        "model_invoked": True,
    }


def test_codex_calls_are_parallel_without_api_schema_and_retain_both_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = _protocol()
    _configure_codex(monkeypatch, protocol)
    barrier = threading.Barrier(2, timeout=2)
    thread_ids: set[int] = set()

    def fake_run(
        _project_root: Path,
        call: dict[str, Any],
        base_prompt: str,
        *,
        enforce_output_schema: bool,
    ) -> dict[str, Any]:
        assert base_prompt == SYSTEM_PROMPT
        assert enforce_output_schema is False
        thread_ids.add(threading.get_ident())
        barrier.wait()
        if str(call["participant_id"]).endswith("-03"):
            raise OSError("synthetic spawn failure")
        return _process_result(call, return_code=1)

    monkeypatch.setattr(codex_module, "_run_one", fake_run)
    with pytest.raises(ValueError, match="both exact process records were retained"):
        codex_module.run_first_direct_three_case_stage1_semantic_recovery_clean_codex(tmp_path)

    assert len(thread_ids) == 2
    root = tmp_path / REVIEW_RELATIVE
    for participant_id in codex_module.CODEX_PARTICIPANT_IDS:
        process_root = root / "codex-process-captures" / participant_id.removeprefix("actor:")
        record = json.loads((process_root / "capture.json").read_text(encoding="utf-8"))
        supplied = record.pop("capture_digest")
        assert supplied == semantic_digest(record)
        assert record["api_output_schema_argument_present"] is False
        assert record["local_semantic_validation_profile"] == ("stage1-semantic-payload-v2")
        assert record["local_semantic_validation_required"] is True
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


def test_concurrent_and_duplicate_codex_invocations_cannot_reach_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = _protocol()
    _configure_codex(monkeypatch, protocol)
    both_started = threading.Event()
    release = threading.Event()
    lock = threading.Lock()
    call_count = 0

    def blocked_run(
        _project_root: Path,
        call: dict[str, Any],
        _base_prompt: str,
        *,
        enforce_output_schema: bool,
    ) -> dict[str, Any]:
        nonlocal call_count
        assert enforce_output_schema is False
        with lock:
            call_count += 1
            if call_count == 2:
                both_started.set()
        if not release.wait(timeout=3):
            raise TimeoutError("test did not release the two calls")
        return _process_result(call, return_code=0)

    def fake_capture(
        _project_root: Path,
        participant_id: str,
        raw_response: bytes,
        **kwargs: Any,
    ) -> dict[str, Any]:
        assert raw_response == b'{"reviews":[]}'
        assert kwargs["transport"]["api_output_schema_argument_present"] is False
        record: dict[str, Any] = {
            "participant_id": participant_id,
            "raw_response_digest": sha256_digest(raw_response),
            "transport": kwargs["transport"],
        }
        record["capture_digest"] = semantic_digest(record)
        return record

    monkeypatch.setattr(codex_module, "_run_one", blocked_run)
    monkeypatch.setattr(codex_module, "build_stage1_call_capture", fake_capture)
    with ThreadPoolExecutor(max_workers=1) as executor:
        first = executor.submit(
            codex_module.run_first_direct_three_case_stage1_semantic_recovery_clean_codex,
            tmp_path,
        )
        assert both_started.wait(timeout=2)
        with pytest.raises(FileExistsError, match="attempt already reserved"):
            codex_module.run_first_direct_three_case_stage1_semantic_recovery_clean_codex(tmp_path)
        with lock:
            assert call_count == 2
        release.set()
        captures = first.result(timeout=4)

    assert [item["participant_id"] for item in captures] == list(codex_module.CODEX_PARTICIPANT_IDS)
    with pytest.raises(FileExistsError, match=r"capture already exists|attempt already reserved"):
        codex_module.run_first_direct_three_case_stage1_semantic_recovery_clean_codex(tmp_path)
    with lock:
        assert call_count == 2


def test_claude_capture_requires_exact_fresh_incognito_profile_and_is_write_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = _protocol()
    monkeypatch.setattr(claude_module, "_protocol", lambda _root: protocol)
    participant_id = "actor:stage1-recovery-claude-01"

    def fake_capture(
        _project_root: Path,
        supplied_participant_id: str,
        raw_response: bytes,
        **kwargs: Any,
    ) -> dict[str, Any]:
        assert supplied_participant_id == participant_id
        assert raw_response == b"{}"
        assert kwargs["transport"] == claude_module.CLAUDE_CAPTURE_TRANSPORT
        record: dict[str, Any] = {
            "participant_id": supplied_participant_id,
            "transport": kwargs["transport"],
        }
        record["capture_digest"] = semantic_digest(record)
        return record

    monkeypatch.setattr(claude_module, "build_stage1_call_capture", fake_capture)
    capture = claude_module.capture_claude_app_stage1_semantic_recovery_clean_submission(
        tmp_path,
        participant_id,
        b"{}",
        started_at="2026-08-05T09:00:00Z",
        completed_at="2026-08-05T09:00:01Z",
        captured_at="2026-08-05T09:00:02Z",
    )
    assert capture["participant_id"] == participant_id
    assert capture["transport"]["incognito"] is True
    assert capture["transport"]["fresh_chat"] is True
    assert capture["transport"]["model_ui_label"] == "Opus 5"
    assert capture["transport"]["effort_ui_label"] == "Extra"
    assert capture["transport"]["tools_or_connectors"] == "none"
    with pytest.raises(FileExistsError, match="Refusing to replace"):
        claude_module.capture_claude_app_stage1_semantic_recovery_clean_submission(
            tmp_path,
            participant_id,
            b"{}",
            started_at="2026-08-05T09:00:00Z",
            completed_at="2026-08-05T09:00:01Z",
            captured_at="2026-08-05T09:00:02Z",
        )

    output = (
        tmp_path / REVIEW_RELATIVE / "incoming" / f"{participant_id.removeprefix('actor:')}.json"
    )
    output.unlink()
    protocol["calls"][0]["interaction_profile"] = {
        **claude_module.CLAUDE_INTERACTION_PROFILE,
        "incognito": False,
    }
    with pytest.raises(ValueError, match="interaction profile has drifted"):
        claude_module.build_claude_app_stage1_semantic_recovery_clean_capture(
            tmp_path,
            participant_id,
            b"{}",
            started_at="2026-08-05T09:00:00Z",
            completed_at="2026-08-05T09:00:01Z",
            captured_at="2026-08-05T09:00:02Z",
        )
