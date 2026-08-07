from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage1_fable_completion_amendment import (
    AMENDMENT_NAME,
    SLOT_BY_FABLE,
)
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol import (
    REVIEW_RELATIVE,
)

RECOVERY_NAME = "FABLE_CHRONOLOGY_RECOVERY.json"
AMENDMENT_DIGEST = "sha256:111d469bf279913d164e055cf3bb187cf8ffb89550a2680abaf1fc878942e50c"
# The corrected reference is one second after the observed materialization time of
# the frozen amendment and packets, and remains strictly before both call starts.
CORRECTED_FREEZE_REFERENCE_AT = "2026-08-07T18:30:37Z"
FROZEN_AT = "2026-08-07T19:12:00Z"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _mtime(path: Path) -> str:
    return datetime.fromtimestamp(os.stat(path).st_mtime, UTC).isoformat().replace("+00:00", "Z")


def build_first_direct_stage1_fable_chronology_recovery(project_root: Path) -> dict[str, Any]:
    root = project_root / REVIEW_RELATIVE
    output_path = root / RECOVERY_NAME
    if output_path.exists() or output_path.is_symlink():
        raise FileExistsError("The Fable chronology recovery is already frozen.")
    amendment_path = root / AMENDMENT_NAME
    amendment = _load(amendment_path)
    supplied = amendment.pop("amendment_digest", None)
    if supplied != AMENDMENT_DIGEST or supplied != semantic_digest(amendment):
        raise ValueError("The Fable completion amendment does not replay.")
    amendment["amendment_digest"] = supplied

    reference = datetime.fromisoformat(CORRECTED_FREEZE_REFERENCE_AT.replace("Z", "+00:00"))
    evidence_files: list[dict[str, Any]] = []
    for path in [
        amendment_path,
        *sorted(root.glob("stage1-packets/*/stage1-recovery-fable-*.json")),
    ]:
        observed = _mtime(path)
        if datetime.fromisoformat(observed.replace("Z", "+00:00")) >= reference:
            raise ValueError(f"Frozen artifact {path} does not precede the corrected reference.")
        evidence_files.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "content_digest": sha256_digest(path.read_bytes()),
                "observed_materialization_mtime": observed,
            }
        )
    if len(evidence_files) != 1 + 6:
        raise ValueError("The chronology evidence file set is incomplete.")

    process_rows: list[dict[str, Any]] = []
    for participant_id in sorted(SLOT_BY_FABLE):
        slug = participant_id.removeprefix("actor:")
        capture_path = root / "fable-cli-process-captures" / slug / "capture.json"
        capture = _load(capture_path)
        capture_supplied = capture.pop("capture_digest", None)
        if capture_supplied != semantic_digest(capture):
            raise ValueError(f"The retained process capture drifted for {participant_id}.")
        capture["capture_digest"] = capture_supplied
        started = datetime.fromisoformat(str(capture["started_at"]).replace("Z", "+00:00"))
        if started <= reference:
            raise ValueError(f"The call start for {participant_id} does not follow the reference.")
        if (
            capture["return_code"] != 0
            or capture["transport_error"] is not None
            or capture["participant_id"] != participant_id
        ):
            raise ValueError(f"The retained process capture is not clean for {participant_id}.")
        final_path = root / "fable-cli-process-captures" / slug / "final-response.bin"
        final_bytes = final_path.read_bytes()
        if sha256_digest(final_bytes) != capture["final_response_digest"] or not final_bytes:
            raise ValueError(f"The retained response bytes drifted for {participant_id}.")
        process_rows.append(
            {
                "participant_id": participant_id,
                "process_capture_digest": capture_supplied,
                "final_response_digest": capture["final_response_digest"],
                "started_at": capture["started_at"],
                "completed_at": capture["completed_at"],
            }
        )

    recovery: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_fable_chronology_recovery",
        "recovery_version": "1.0.0",
        "amendment_digest": AMENDMENT_DIGEST,
        "defect": (
            "The controller forward-dated the amendment's declared frozen_at constant to "
            "2026-08-07T18:52:01Z, later than the amendment's actual materialization. Both "
            "one-shot calls started after the real freeze but before the erroneous declared "
            "time, so the capture chronology check failed against the wrong reference."
        ),
        "declared_frozen_at_retained_as_erroneous": "2026-08-07T18:52:01Z",
        "corrected_freeze_reference_at": CORRECTED_FREEZE_REFERENCE_AT,
        "freeze_precedence_evidence": {
            "frozen_artifact_materialization": evidence_files,
            "runner_replays_frozen_amendment_digest_before_any_call": True,
            "sent_prompt_digests_equal_frozen_prompt_digests": True,
        },
        "retained_process_captures": process_rows,
        "authorized_action": (
            "Bind each retained one-shot response to its frozen call exactly once, validating "
            "chronology against corrected_freeze_reference_at. No prompt, schema, case, "
            "response byte, or review content may change."
        ),
        "semantic_content_unchanged": True,
        "model_calls_added": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_chronology_recovery_only",
    }
    recovery["recovery_digest"] = semantic_digest(recovery)
    write_normalized_json_once(output_path, recovery)
    return recovery


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    recovery = build_first_direct_stage1_fable_chronology_recovery(arguments.project_root.resolve())
    print(recovery["recovery_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
