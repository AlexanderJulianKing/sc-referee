from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_three_case_stage1_protocol import REVIEW_RELATIVE
from scripts.record_first_direct_three_case_stage1_reviews import PROTOCOL_DIGEST

COMPLETED_AT = "2026-08-05T06:35:00Z"
EXPECTED_CAPTURE_DIGESTS = {
    "actor:stage1-codex-01": (
        "sha256:beb689d9a797953864145ba126a5d877dfd2e79d705d6ec0649fc2873f5dd5fe"
    ),
    "actor:stage1-codex-02": (
        "sha256:ca445a569f59cda7500fe482d9a4cb94b0a264211b9f2261e039059b9bd1fff6"
    ),
}


class Stage1CodexTransportFailureError(ValueError):
    """Retained Codex transport evidence is incomplete or has drifted."""


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Stage1CodexTransportFailureError(f"Expected one JSON object at {path}.")
    return cast(dict[str, Any], value)


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise Stage1CodexTransportFailureError(f"{label} does not replay.")
    record[field] = supplied


def _stdout_events(payload: bytes) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in payload.decode("utf-8").splitlines():
        value = json.loads(line)
        if not isinstance(value, dict):
            raise Stage1CodexTransportFailureError("Codex stdout contains a non-object event.")
        events.append(cast(dict[str, Any], value))
    return events


def _api_error(events: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [item for item in events if item.get("type") == "error"]
    if len(errors) != 1:
        raise Stage1CodexTransportFailureError("Expected exactly one Codex API error event.")
    nested = json.loads(str(errors[0].get("message")))
    if not isinstance(nested, dict) or not isinstance(nested.get("error"), dict):
        raise Stage1CodexTransportFailureError("Codex API error event is malformed.")
    return cast(dict[str, Any], nested)


def build_stage1_codex_transport_failure_ledger(project_root: Path) -> dict[str, Any]:
    root = project_root / REVIEW_RELATIVE
    protocol = _load(root / "STAGE1_REVIEW_PROTOCOL.json")
    _replay(protocol, "protocol_digest", PROTOCOL_DIGEST, "The Stage-1 protocol")
    calls = {
        str(item["participant_id"]): item
        for item in protocol["calls"]
        if item["participant"]["provider"] == "OpenAI"
    }
    if set(calls) != set(EXPECTED_CAPTURE_DIGESTS):
        raise Stage1CodexTransportFailureError(
            "The Stage-1 protocol no longer contains the exact two Codex calls."
        )

    attempts: list[dict[str, Any]] = []
    for participant_id in sorted(calls):
        call = calls[participant_id]
        slug = participant_id.removeprefix("actor:")
        capture_root = root / "codex-process-captures" / slug
        capture = _load(capture_root / "capture.json")
        _replay(
            capture,
            "capture_digest",
            EXPECTED_CAPTURE_DIGESTS[participant_id],
            f"The retained {participant_id} process capture",
        )
        if (
            capture["protocol_digest"] != PROTOCOL_DIGEST
            or capture["participant_id"] != participant_id
            or capture["call_identity_id"] != call["call_identity_id"]
        ):
            raise Stage1CodexTransportFailureError(
                f"The retained {participant_id} process capture is bound incorrectly."
            )

        payloads = {
            name: (capture_root / name).read_bytes()
            for name in ("stdout.bin", "stderr.bin", "final-response.bin")
        }
        for name, field in (
            ("stdout.bin", "stdout"),
            ("stderr.bin", "stderr"),
            ("final-response.bin", "final_response"),
        ):
            payload = payloads[name]
            if (
                sha256_digest(payload) != capture[f"{field}_digest"]
                or len(payload) != capture[f"{field}_byte_size"]
            ):
                raise Stage1CodexTransportFailureError(
                    f"The retained {participant_id} {name} has drifted."
                )

        events = _stdout_events(payloads["stdout.bin"])
        event_types = [str(item.get("type")) for item in events]
        api_error = _api_error(events)
        error = cast(dict[str, Any], api_error["error"])
        message = str(error.get("message"))
        if (
            capture["return_code"] != 1
            or payloads["final-response.bin"] != b""
            or event_types != ["thread.started", "turn.started", "error", "turn.failed"]
            or api_error.get("status") != 400
            or error.get("type") != "invalid_request_error"
            or error.get("code") != "invalid_json_schema"
            or error.get("param") != "text.format.schema"
            or "'allOf' is not permitted" not in message
        ):
            raise Stage1CodexTransportFailureError(
                f"The retained {participant_id} evidence is not the expected pre-inference schema rejection."
            )

        attempts.append(
            {
                "participant_id": participant_id,
                "provider": "OpenAI",
                "superseded_call_identity_id": call["call_identity_id"],
                "prompt_digest": call["prompt_digest"],
                "semantic_output_schema_digest": call["output_schema_digest"],
                "process_capture_relative_path": capture_root.relative_to(root).as_posix(),
                "process_capture_digest": capture["capture_digest"],
                "return_code": capture["return_code"],
                "failure_stage": "pre_inference_response_schema_validation",
                "failure_reason_code": "api_rejected_unsupported_allof_keyword",
                "api_status": api_error["status"],
                "api_error_code": error["code"],
                "model_request_submitted": True,
                "model_inference_started": False,
                "reviewer_response_observed": False,
                "review_admitted": False,
                "replacement_attempted": False,
                "started_at": capture["started_at"],
                "completed_at": capture["completed_at"],
            }
        )

    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_codex_transport_failure_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": PROTOCOL_DIGEST,
        "attempts": attempts,
        "failure_interpretation": {
            "classification": "pre_inference_transport_failure",
            "basis": "Both API requests returned HTTP 400 invalid_json_schema before any model output event or final-response byte existed.",
            "legacy_capture_model_invoked_field_interpretation": "CLI invocation attempted; it does not establish that model inference started.",
            "scientific_verdict_permitted": False,
            "semantic_response_repair_permitted": False,
        },
        "summary": {
            "attempt_count": 2,
            "pre_inference_failure_count": 2,
            "reviewer_response_count": 0,
            "stage1_review_count": 0,
            "stage1_freeze_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "project_code_executed_count": 0,
        },
        "completed_at": COMPLETED_AT,
        "qualification_authority": "none_transport_failure_evidence_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    output = project_root / REVIEW_RELATIVE / "CODEX_TRANSPORT_FAILURE_LEDGER.json"
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Refusing to replace retained failure ledger: {output}")
    ledger = build_stage1_codex_transport_failure_ledger(project_root)
    write_normalized_json_once(output, ledger)
    print(ledger["ledger_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
