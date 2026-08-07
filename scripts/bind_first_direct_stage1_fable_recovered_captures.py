from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage1_fable_completion_amendment import SLOT_BY_FABLE
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol import (
    REVIEW_RELATIVE,
)
from scripts.record_first_direct_stage1_fable_completion import (
    RECOVERY_DIGEST,
    _amendment_call,
    build_fable_stage1_call_capture,
)
from scripts.run_first_direct_stage1_recovery_claude_cli_replacement_calibration import (
    CLAUDE_PINNED,
)


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def bind_first_direct_stage1_fable_recovered_captures(
    project_root: Path,
) -> list[dict[str, Any]]:
    """Bind the retained one-shot responses under the frozen chronology recovery."""

    if RECOVERY_DIGEST is None:
        raise ValueError("The chronology recovery digest is not frozen in the recorder.")
    root = project_root / REVIEW_RELATIVE
    captures: list[dict[str, Any]] = []
    for participant_id in sorted(SLOT_BY_FABLE):
        slug = participant_id.removeprefix("actor:")
        incoming = root / "incoming" / f"{slug}.json"
        if incoming.exists() or incoming.is_symlink():
            raise FileExistsError(f"Recovered capture already bound: {participant_id}")
        process_root = root / "fable-cli-process-captures" / slug
        process = _load(process_root / "capture.json")
        supplied = process.pop("capture_digest", None)
        if supplied != semantic_digest(process):
            raise ValueError(f"The retained process capture drifted for {participant_id}.")
        process["capture_digest"] = supplied
        raw_response = (process_root / "final-response.bin").read_bytes()
        call = _amendment_call(project_root, participant_id)
        capture = build_fable_stage1_call_capture(
            project_root,
            participant_id,
            raw_response,
            started_at=str(process["started_at"]),
            completed_at=str(process["completed_at"]),
            captured_at=_now(),
            transport={
                "surface": "Claude Code CLI print mode",
                "binary_path": str(CLAUDE_PINNED),
                "safe_mode": True,
                "tools_disabled": True,
                "mcp_servers": "empty_strict",
                "permission_mode": "dontAsk",
                "session_persistence": False,
                "output_format": "json",
                "model_alias_argument": str(call["interaction_profile"]["model_alias_argument"]),
                "served_model_verified": str(call["participant"]["model_id"]),
                "api_output_schema_argument_present": False,
                "local_semantic_validation_profile": "stage1-semantic-payload-v2",
                "local_semantic_validation_required": True,
                "reported_session_id": process["reported_session_id"],
                "process_capture_relative_path": process_root.relative_to(root).as_posix(),
                "process_capture_digest": process["capture_digest"],
                "chronology_recovery_digest": RECOVERY_DIGEST,
            },
        )
        write_normalized_json_once(incoming, capture)
        captures.append(capture)
    return captures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    captures = bind_first_direct_stage1_fable_recovered_captures(arguments.project_root.resolve())
    for capture in captures:
        print(capture["participant_id"], capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
