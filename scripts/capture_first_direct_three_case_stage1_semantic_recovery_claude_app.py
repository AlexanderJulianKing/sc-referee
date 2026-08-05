from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_three_case_stage1_semantic_recovery_protocol import (
    REVIEW_RELATIVE,
)
from scripts.record_first_direct_three_case_stage1_semantic_recovery import (
    _protocol,
    build_stage1_call_capture,
)

CLAUDE_INTERACTION_PROFILE = {
    "surface": "Claude Desktop App Home Chat",
    "incognito": True,
    "fresh_chat": True,
    "model_label": "Opus 5",
    "effort_label": "Extra",
    "tools_or_connectors": "none",
}

CLAUDE_CAPTURE_TRANSPORT = {
    "surface": "Claude Desktop App Home Chat",
    "application_version": "1.25927.0",
    "incognito": True,
    "fresh_chat": True,
    "model_ui_label": "Opus 5",
    "effort_ui_label": "Extra",
    "tools_or_connectors": "none",
    "file_uploads": "none",
    "conversation_url": "claude.ai/new?incognito=",
    "distinct_conversation_identifier_available": False,
    "response_capture_method": "Claude response Copy action followed by exact plain-text paste",
    "interaction_driver": "Codex Computer Use accessibility interface",
    "visible_tool_call_count": 0,
}


def build_claude_app_stage1_semantic_recovery_capture(
    project_root: Path,
    participant_id: str,
    raw_response: bytes,
    *,
    started_at: str,
    completed_at: str,
    captured_at: str,
) -> dict[str, Any]:
    protocol = _protocol(project_root)
    call = next(
        (item for item in protocol["calls"] if item["participant_id"] == participant_id),
        None,
    )
    if call is None or call["participant"]["provider"] != "Anthropic":
        raise ValueError(
            f"Participant {participant_id!r} is not a frozen Claude semantic-recovery call."
        )
    if call["interaction_profile"] != CLAUDE_INTERACTION_PROFILE:
        raise ValueError("The frozen Claude semantic-recovery interaction profile has drifted.")
    return build_stage1_call_capture(
        project_root,
        participant_id,
        raw_response,
        started_at=started_at,
        completed_at=completed_at,
        captured_at=captured_at,
        transport=dict(CLAUDE_CAPTURE_TRANSPORT),
    )


def capture_claude_app_stage1_semantic_recovery_submission(
    project_root: Path,
    participant_id: str,
    raw_response: bytes,
    *,
    started_at: str,
    completed_at: str,
    captured_at: str,
) -> dict[str, Any]:
    participant_slug = participant_id.removeprefix("actor:")
    output = project_root / REVIEW_RELATIVE / "incoming" / f"{participant_slug}.json"
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Refusing to replace Stage-1 semantic-recovery capture: {output}")
    capture = build_claude_app_stage1_semantic_recovery_capture(
        project_root,
        participant_id,
        raw_response,
        started_at=started_at,
        completed_at=completed_at,
        captured_at=captured_at,
    )
    write_normalized_json_once(output, capture)
    return capture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--participant-id", required=True)
    parser.add_argument("--raw-response", type=Path, required=True)
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--completed-at", required=True)
    parser.add_argument("--captured-at", required=True)
    arguments = parser.parse_args()
    capture = capture_claude_app_stage1_semantic_recovery_submission(
        arguments.project_root.resolve(),
        arguments.participant_id,
        arguments.raw_response.read_bytes(),
        started_at=arguments.started_at,
        completed_at=arguments.completed_at,
        captured_at=arguments.captured_at,
    )
    print(capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
