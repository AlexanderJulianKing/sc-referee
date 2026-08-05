from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage1_recovery_calibration import CALIBRATION_RELATIVE
from scripts.record_first_direct_stage1_recovery_calibration import (
    build_claude_app_recovery_calibration_capture,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--participant-id", required=True)
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--completed-at", required=True)
    parser.add_argument("--captured-at", required=True)
    parser.add_argument("--raw-response-base64")
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    raw_response = (
        base64.b64decode(str(arguments.raw_response_base64), validate=True).decode("utf-8")
        if arguments.raw_response_base64 is not None
        else sys.stdin.read()
    )
    capture = build_claude_app_recovery_calibration_capture(
        project_root,
        str(arguments.participant_id),
        raw_response,
        started_at=str(arguments.started_at),
        completed_at=str(arguments.completed_at),
        captured_at=str(arguments.captured_at),
    )
    slug = str(arguments.participant_id).removeprefix("actor:")
    output = project_root / CALIBRATION_RELATIVE / "incoming" / f"{slug}.json"
    write_normalized_json_once(output, capture)
    print(capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
