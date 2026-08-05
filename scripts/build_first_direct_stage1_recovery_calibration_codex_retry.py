from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage1_recovery_calibration import CALIBRATION_RELATIVE
from scripts.record_first_direct_stage1_recovery_calibration import _protocol

FROZEN_AT = "2026-08-05T07:28:00Z"
AMENDMENT_NAME = "CODEX_CALIBRATION_TRANSPORT_RETRY_AMENDMENT.json"


def build_first_direct_stage1_recovery_calibration_codex_retry(
    project_root: Path,
) -> dict[str, Any]:
    protocol = _protocol(project_root)
    root = project_root / CALIBRATION_RELATIVE
    output = root / AMENDMENT_NAME
    if output.exists() or output.is_symlink():
        raise FileExistsError("The Codex calibration transport retry is already frozen.")
    assignments = [item for item in protocol["assignments"] if item["provider"] == "OpenAI"]
    if len(assignments) != 2:
        raise ValueError("The protocol does not contain exactly two Codex calibrations.")
    by_slug = {str(item["participant_id"]).removeprefix("actor:"): item for item in assignments}
    first_slug = "stage1-recovery-codex-01"
    first_capture_path = root / "process-captures" / first_slug / "capture.json"
    if not first_capture_path.is_file():
        raise ValueError("The retained first transport failure is unavailable.")
    import json

    first_capture = json.loads(first_capture_path.read_text(encoding="utf-8"))
    supplied = first_capture.pop("capture_digest", None)
    if supplied != semantic_digest(first_capture):
        raise ValueError("The retained first transport failure does not replay.")
    first_capture["capture_digest"] = supplied
    if first_capture.get("return_code") == 0 or first_capture.get("final_response_digest") != (
        "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    ):
        raise ValueError("The retained first attempt is not the diagnosed pre-response failure.")
    second_slug = "stage1-recovery-codex-02"
    if (root / "process-captures" / second_slug).exists():
        raise ValueError("The controller-bug diagnosis no longer matches the retained files.")
    if any((root / "incoming" / f"{slug}.json").exists() for slug in by_slug):
        raise ValueError("A Codex calibration response was already admitted.")

    retry_calls = []
    for slug, assignment in sorted(by_slug.items()):
        retry_calls.append(
            {
                "participant_id": assignment["participant_id"],
                "semantic_call_identity_id": assignment["call_identity_id"],
                "transport_attempt_identity_id": str(
                    uuid5(
                        NAMESPACE_URL,
                        f"sc-referee-stage1-recovery-calibration-codex-transport-retry-v1:{slug}",
                    )
                ),
                "prompt_digest": assignment["prompt_digest"],
                "output_schema_digest": assignment["output_schema_digest"],
                "configuration_digest": assignment["configuration_digest"],
                "process_capture_relative_path": f"retry-process-captures/{slug}",
                "incoming_capture_relative_path": f"incoming/{slug}.json",
            }
        )
    amendment: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_recovery_calibration_codex_transport_retry_amendment",
        "amendment_version": "1.0.0",
        "calibration_protocol_digest": protocol["protocol_digest"],
        "retained_failure": {
            "participant_id": by_slug[first_slug]["participant_id"],
            "process_capture_digest": first_capture["capture_digest"],
            "reason": "managed_sandbox_blocked_writable_codex_state_before_response",
        },
        "unretained_parallel_attempt": {
            "participant_id": by_slug[second_slug]["participant_id"],
            "reason": "controller_raised_after_first_failure_before_writing_second_parallel_result",
            "scientific_response_observed": False,
            "admission_permitted": False,
        },
        "controller_fix": {
            "all_parallel_process_evidence_written_before_failure_raise": True,
            "semantic_response_repair_permitted": False,
        },
        "transport_delta": {
            "execute_outside_managed_filesystem_sandbox": True,
            "prompt_bytes_unchanged": True,
            "output_schema_unchanged": True,
            "model_configuration_unchanged": True,
            "calibration_expected_verdicts_unchanged": True,
        },
        "retry_calls": retry_calls,
        "controller_implementation": [
            {
                "path": path_value,
                "content_digest": sha256_digest((project_root / path_value).read_bytes()),
            }
            for path_value in (
                "scripts/run_first_direct_stage1_recovery_calibration_codex_retry.py",
                "scripts/run_first_direct_stage1_recovery_calibration_codex.py",
                "scripts/record_first_direct_stage1_recovery_calibration.py",
                "scripts/run_first_direct_reviewer_calibration.py",
            )
        ],
        "execution_state": "frozen_not_started",
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_transport_retry_only",
    }
    amendment["amendment_digest"] = semantic_digest(amendment)
    write_normalized_json_once(output, amendment)
    return amendment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    amendment = build_first_direct_stage1_recovery_calibration_codex_retry(
        arguments.project_root.resolve()
    )
    print(amendment["amendment_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
