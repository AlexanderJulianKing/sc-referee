from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import pytest

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts import (
    capture_first_direct_three_case_stage1_semantic_recovery_claude_app as claude_module,
)
from scripts import run_first_direct_three_case_stage1_semantic_recovery_codex as codex_module
from scripts.build_first_direct_three_case_stage1_semantic_recovery_protocol import (
    REVIEW_RELATIVE,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PROMPT = "Frozen stage-one reviewer system prompt."
SYSTEM_PROMPT_DIGEST = sha256_digest(SYSTEM_PROMPT)

assert codex_module.REVIEW_RELATIVE == claude_module.REVIEW_RELATIVE == REVIEW_RELATIVE


def _participant(participant_id: str, provider: str) -> dict[str, Any]:
    return {
        "participant_id": participant_id,
        "call_identity_id": f"call:{participant_id}",
        "participant": {
            "provider": provider,
            "system_prompt_digest": SYSTEM_PROMPT_DIGEST,
        },
        "interaction_profile": dict(claude_module.CLAUDE_INTERACTION_PROFILE),
    }


def _protocol() -> dict[str, Any]:
    return {
        "protocol_digest": "sha256:" + "1" * 64,
        "calls": [
            _participant("actor:stage1-semantic-recovery-codex-01", "OpenAI"),
            _participant("actor:stage1-semantic-recovery-codex-02", "OpenAI"),
            _participant("actor:stage1-semantic-recovery-claude-01", "Anthropic"),
        ],
    }


def _configure_system_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
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
    raw_response = b'{"ok":true}' if return_code == 0 else b""
    return {
        "participant_id": participant_id,
        "call": call,
        "started_at": "2026-08-05T08:00:00Z",
        "completed_at": "2026-08-05T08:00:01Z",
        "argv": ["codex", "exec", str(call["participant_id"])],
        "return_code": return_code,
        "stdout": f"stdout:{participant_id}".encode(),
        "stderr": f"stderr:{participant_id}".encode(),
        "raw_response": raw_response,
        "process_error": None if return_code == 0 else "transport_failure",
    }


def test_codex_calls_are_parallel_omit_api_schema_and_retain_both_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = _protocol()
    _configure_system_prompt(monkeypatch)
    monkeypatch.setattr(codex_module, "_protocol", lambda _root: protocol)
    barrier = threading.Barrier(2, timeout=2)
    thread_ids: set[int] = set()

    def fake_run_one(
        _project_root: Path,
        call: dict[str, Any],
        _base_prompt: str,
        *,
        enforce_output_schema: bool,
    ) -> dict[str, Any]:
        assert enforce_output_schema is False
        thread_ids.add(threading.get_ident())
        barrier.wait()
        if str(call["participant_id"]).endswith("-01"):
            raise OSError("synthetic spawn failure")
        return _process_result(call, return_code=1)

    monkeypatch.setattr(codex_module, "_run_one", fake_run_one)
    with pytest.raises(ValueError, match="exact process evidence was retained"):
        codex_module.run_first_direct_three_case_stage1_semantic_recovery_codex(tmp_path)

    assert len(thread_ids) == 2
    root = tmp_path / codex_module.REVIEW_RELATIVE
    for participant_id in (
        "actor:stage1-semantic-recovery-codex-01",
        "actor:stage1-semantic-recovery-codex-02",
    ):
        slug = participant_id.removeprefix("actor:")
        process_root = root / "codex-process-captures" / slug
        record = json.loads((process_root / "capture.json").read_text(encoding="utf-8"))
        supplied = record.pop("capture_digest")
        assert supplied == semantic_digest(record)
        assert record["api_output_schema_argument_present"] is False
        assert record["local_semantic_validation_profile"] == "stage1-semantic-payload-v2"
        if participant_id.endswith("-01"):
            assert record["process_error"] == "transport_exception:OSError"
            assert record["model_invoked"] is False
            assert (process_root / "stdout.bin").read_bytes() == b""
            assert (process_root / "stderr.bin").read_bytes() == b"synthetic spawn failure"
        else:
            assert (process_root / "stdout.bin").read_bytes() == f"stdout:{participant_id}".encode()
            assert (process_root / "stderr.bin").read_bytes() == f"stderr:{participant_id}".encode()
        assert (process_root / "final-response.bin").read_bytes() == b""


def test_codex_incoming_captures_are_write_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = _protocol()
    _configure_system_prompt(monkeypatch)
    monkeypatch.setattr(codex_module, "_protocol", lambda _root: protocol)
    monkeypatch.setattr(
        codex_module,
        "_run_one",
        lambda _project_root, call, _base_prompt, *, enforce_output_schema: (
            _process_result(call, return_code=0)
            if enforce_output_schema is False
            else pytest.fail("Codex API output schema must remain disabled")
        ),
    )

    def fake_capture(
        _project_root: Path,
        participant_id: str,
        raw_response: bytes,
        **kwargs: Any,
    ) -> dict[str, Any]:
        assert raw_response == b'{"ok":true}'
        assert kwargs["transport"]["api_output_schema_argument_present"] is False
        record: dict[str, Any] = {
            "participant_id": participant_id,
            "raw_response_digest": sha256_digest(raw_response),
            "transport": kwargs["transport"],
        }
        record["capture_digest"] = semantic_digest(record)
        return record

    monkeypatch.setattr(codex_module, "build_stage1_call_capture", fake_capture)
    captures = codex_module.run_first_direct_three_case_stage1_semantic_recovery_codex(tmp_path)
    assert len(captures) == 2
    with pytest.raises(ValueError, match="already attempted"):
        codex_module.run_first_direct_three_case_stage1_semantic_recovery_codex(tmp_path)


def test_claude_capture_requires_exact_fresh_incognito_profile_and_is_write_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = _protocol()
    participant_id = "actor:stage1-semantic-recovery-claude-01"
    monkeypatch.setattr(claude_module, "_protocol", lambda _root: protocol)

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
    capture = claude_module.capture_claude_app_stage1_semantic_recovery_submission(
        tmp_path,
        participant_id,
        b"{}",
        started_at="2026-08-05T08:00:00Z",
        completed_at="2026-08-05T08:00:01Z",
        captured_at="2026-08-05T08:00:02Z",
    )
    assert capture["participant_id"] == participant_id
    with pytest.raises(FileExistsError, match="Refusing to replace"):
        claude_module.capture_claude_app_stage1_semantic_recovery_submission(
            tmp_path,
            participant_id,
            b"{}",
            started_at="2026-08-05T08:00:00Z",
            completed_at="2026-08-05T08:00:01Z",
            captured_at="2026-08-05T08:00:02Z",
        )

    protocol["calls"][-1]["interaction_profile"] = {
        **claude_module.CLAUDE_INTERACTION_PROFILE,
        "incognito": False,
    }
    output = (
        tmp_path
        / claude_module.REVIEW_RELATIVE
        / "incoming"
        / f"{participant_id.removeprefix('actor:')}.json"
    )
    output.unlink()
    with pytest.raises(ValueError, match="interaction profile has drifted"):
        claude_module.build_claude_app_stage1_semantic_recovery_capture(
            tmp_path,
            participant_id,
            b"{}",
            started_at="2026-08-05T08:00:00Z",
            completed_at="2026-08-05T08:00:01Z",
            captured_at="2026-08-05T08:00:02Z",
        )
