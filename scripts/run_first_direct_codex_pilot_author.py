from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from scripts.build_first_direct_three_case_pilot_authoring import PILOT_AUTHORING_RELATIVE


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def run_first_direct_codex_pilot_author(project_root: Path) -> dict[str, Any]:
    root = project_root / PILOT_AUTHORING_RELATIVE
    protocol = _load(root / "PILOT_AUTHORING_PROTOCOL.json")
    assignments = [
        item
        for item in protocol["author_assignments"]
        if item["participant"]["provider"] == "OpenAI"
    ]
    if len(assignments) != 1:
        raise ValueError("Expected exactly one frozen Codex author assignment.")
    assignment = assignments[0]
    incoming = root / "incoming"
    incoming.mkdir(parents=True, exist_ok=True)
    participant_id = str(assignment["participant"]["participant_id"])
    retained_path = incoming / f"{participant_id.removeprefix('actor:')}.json"
    if retained_path.exists():
        raise FileExistsError(f"Refusing to replace retained author attempt: {retained_path}")

    with tempfile.TemporaryDirectory(prefix="sc-referee-codex-author-") as directory:
        workspace = Path(directory)
        schema_path = workspace / "output-schema.json"
        response_path = workspace / "final-response.json"
        schema_path.write_text(
            json.dumps(assignment["output_schema"], sort_keys=True) + "\n", encoding="utf-8"
        )
        command = [
            "codex",
            "exec",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--ephemeral",
            "--model",
            "gpt-5.6-sol",
            "--config",
            'model_reasoning_effort="high"',
            "--sandbox",
            "workspace-write",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(response_path),
            "--json",
            "-",
        ]
        started_at = _now()
        completed = subprocess.run(
            command,
            cwd=workspace,
            input=str(assignment["prompt"]),
            text=True,
            capture_output=True,
            check=False,
            timeout=1800,
        )
        completed_at = _now()
        raw_response = response_path.read_text(encoding="utf-8") if response_path.exists() else None
    attempt: dict[str, Any] = {
        "participant_id": participant_id,
        "call_identity_id": assignment["call_identity_id"],
        "protocol_digest": protocol["protocol_digest"],
        "configuration_digest": assignment["participant"]["configuration_digest"],
        "prompt_digest": assignment["prompt_digest"],
        "output_schema_digest": assignment["output_schema_digest"],
        "started_at": started_at,
        "completed_at": completed_at,
        "command": command,
        "exit_code": completed.returncode,
        "stdout_jsonl": completed.stdout,
        "stderr": completed.stderr,
        "raw_response": raw_response,
        "attempt_status": "response_retained"
        if raw_response is not None
        else "failed_before_response",
        "replacement_count": 0,
        "qualification_authority": "none_author_attempt_only",
    }
    retained_path.write_text(
        json.dumps(attempt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return attempt


if __name__ == "__main__":
    result = run_first_direct_codex_pilot_author(Path.cwd())
    print(
        json.dumps(
            {
                "participant_id": result["participant_id"],
                "exit_code": result["exit_code"],
                "attempt_status": result["attempt_status"],
            },
            sort_keys=True,
        )
    )
