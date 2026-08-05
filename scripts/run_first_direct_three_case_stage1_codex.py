from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.storage.atomic import atomic_write_bytes
from scripts.build_first_direct_three_case_stage1_protocol import (
    BASE_STAGE1_PROMPT_DIGEST,
    REVIEW_RELATIVE,
)
from scripts.record_first_direct_three_case_stage1_reviews import (
    build_stage1_call_capture,
)

CODEX = Path("/Users/alexanderking/.local/bin/codex")


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected one JSON object at {path}.")
    return value


def _codex_argv(
    call: dict[str, Any],
    base_prompt: str,
    working: Path,
    schema_path: Path,
    final_path: Path,
    *,
    enforce_output_schema: bool,
) -> list[str]:
    argv = [
        str(CODEX),
        "--model",
        str(call["participant"]["model_id"]),
        "--sandbox",
        "read-only",
        "--ask-for-approval",
        "never",
        "--config",
        f'model_reasoning_effort="{call["participant"]["reasoning_configuration"]}"',
        "--config",
        f"developer_instructions={json.dumps(base_prompt)}",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
    ]
    if enforce_output_schema:
        argv.extend(["--output-schema", str(schema_path)])
    argv.extend(
        [
            "--json",
            "--output-last-message",
            str(final_path),
            "--cd",
            str(working),
            str(call["prompt"]),
        ]
    )
    return argv


def _run_one(
    project_root: Path,
    call: dict[str, Any],
    base_prompt: str,
    *,
    enforce_output_schema: bool = True,
) -> dict[str, Any]:
    participant_id = str(call["participant_id"])
    started_at = _now()
    environment = dict(os.environ)
    environment["NO_COLOR"] = "1"
    with tempfile.TemporaryDirectory(prefix="sc-referee-stage1-codex-") as temporary:
        working = Path(temporary)
        schema_path = working / "output-schema.json"
        schema_path.write_text(json.dumps(call["output_schema"], sort_keys=True), encoding="utf-8")
        final_path = working / "final-response.json"
        argv = _codex_argv(
            call,
            base_prompt,
            working,
            schema_path,
            final_path,
            enforce_output_schema=enforce_output_schema,
        )
        try:
            completed = subprocess.run(
                argv,
                cwd=working,
                env=environment,
                capture_output=True,
                check=False,
                timeout=900,
            )
            return_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
            raw_response = final_path.read_bytes() if final_path.exists() else b""
            process_error = None
        except subprocess.TimeoutExpired as error:
            return_code = 124
            stdout = error.stdout or b""
            stderr = error.stderr or b""
            raw_response = b""
            process_error = "timeout_900_seconds"
    completed_at = _now()
    return {
        "participant_id": participant_id,
        "call": call,
        "started_at": started_at,
        "completed_at": completed_at,
        "argv": argv,
        "return_code": return_code,
        "stdout": stdout,
        "stderr": stderr,
        "raw_response": raw_response,
        "process_error": process_error,
    }


def run_first_direct_three_case_stage1_codex(project_root: Path) -> list[dict[str, Any]]:
    protocol = _load(project_root / REVIEW_RELATIVE / "STAGE1_REVIEW_PROTOCOL.json")
    supplied = protocol.pop("protocol_digest", None)
    if supplied != semantic_digest(protocol):
        raise ValueError("The Stage-1 protocol digest is invalid.")
    protocol["protocol_digest"] = supplied
    base_prompt_path = (
        project_root
        / "evaluation/qualification/bounded-analysis-method-conflict-v0.2.0-precase/stage1-prompt.txt"
    )
    base_prompt = base_prompt_path.read_text(encoding="utf-8")
    if sha256_digest(base_prompt) != BASE_STAGE1_PROMPT_DIGEST:
        raise ValueError("The accepted Stage-1 system prompt has drifted.")
    calls = [item for item in protocol["calls"] if item["participant"]["provider"] == "OpenAI"]
    if len(calls) != 2:
        raise ValueError("The frozen protocol does not contain two Codex Stage-1 calls.")
    root = project_root / REVIEW_RELATIVE
    for call in calls:
        participant_slug = str(call["participant_id"]).removeprefix("actor:")
        if (root / "incoming" / f"{participant_slug}.json").exists() or (
            root / "codex-process-captures" / participant_slug
        ).exists():
            raise ValueError(f"Codex Stage-1 call {participant_slug} was already attempted.")
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda call: _run_one(project_root, call, base_prompt), calls))

    process_evidence: list[tuple[dict[str, Any], Path, dict[str, Any]]] = []
    for result in results:
        participant_id = str(result["participant_id"])
        participant_slug = participant_id.removeprefix("actor:")
        process_root = root / "codex-process-captures" / participant_slug
        process_root.mkdir(parents=True)
        atomic_write_bytes(process_root / "stdout.bin", result["stdout"])
        atomic_write_bytes(process_root / "stderr.bin", result["stderr"])
        atomic_write_bytes(process_root / "final-response.bin", result["raw_response"])
        process_record: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_codex_process_capture",
            "capture_version": "1.0.0",
            "protocol_digest": protocol["protocol_digest"],
            "participant_id": participant_id,
            "call_identity_id": result["call"]["call_identity_id"],
            "argv_digest": semantic_digest(result["argv"]),
            "return_code": result["return_code"],
            "process_error": result["process_error"],
            "stdout_digest": sha256_digest(result["stdout"]),
            "stdout_byte_size": len(result["stdout"]),
            "stderr_digest": sha256_digest(result["stderr"]),
            "stderr_byte_size": len(result["stderr"]),
            "final_response_digest": sha256_digest(result["raw_response"]),
            "final_response_byte_size": len(result["raw_response"]),
            "started_at": result["started_at"],
            "completed_at": result["completed_at"],
            "model_invoked": True,
            "project_code_executed": False,
            "qualification_authority": "none_process_capture_only",
        }
        process_record["capture_digest"] = semantic_digest(process_record)
        write_normalized_json_once(process_root / "capture.json", process_record)
        process_evidence.append((result, process_root, process_record))
    failures = [
        str(result["participant_id"])
        for result, _process_root, _process_record in process_evidence
        if result["return_code"] != 0 or not result["raw_response"]
    ]
    if failures:
        raise ValueError(
            "Codex Stage-1 calls failed and exact process evidence was retained: "
            + ", ".join(sorted(failures))
        )

    retained = []
    for result, process_root, process_record in process_evidence:
        participant_id = str(result["participant_id"])
        participant_slug = participant_id.removeprefix("actor:")
        captured_at = _now()
        call_capture = build_stage1_call_capture(
            project_root,
            participant_id,
            result["raw_response"],
            started_at=result["started_at"],
            completed_at=result["completed_at"],
            captured_at=captured_at,
            transport={
                "surface": "Codex CLI exec",
                "ephemeral": True,
                "sandbox": "read-only",
                "external_network": False,
                "process_capture_relative_path": process_root.relative_to(root).as_posix(),
                "process_capture_digest": process_record["capture_digest"],
            },
        )
        write_normalized_json_once(root / "incoming" / f"{participant_slug}.json", call_capture)
        retained.append(call_capture)
    return retained


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    captures = run_first_direct_three_case_stage1_codex(arguments.project_root.resolve())
    for capture in captures:
        print(capture["participant_id"], capture["capture_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
