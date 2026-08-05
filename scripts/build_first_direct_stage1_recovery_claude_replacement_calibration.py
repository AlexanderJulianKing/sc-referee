from __future__ import annotations

import argparse
import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage1_recovery_calibration import (
    CALIBRATION_RELATIVE,
    EXPECTED_CALIBRATION_VERDICTS,
    LANE_RELATIVE,
)

REPLACEMENT_RELATIVE = (
    LANE_RELATIVE / "reviewer-calibration-v6-stage1-semantic-recovery-claude-replacement"
)
SOURCE_LEDGER_DIGEST = "sha256:4892d3ee890c19bb98110b8f301bddf225213064ac0acc368c2ae197b67aafc6"
SOURCE_PARTICIPANT_ID = "actor:stage1-recovery-claude-02"
REPLACEMENT_PARTICIPANT_ID = "actor:stage1-recovery-claude-03"
REPLACEMENT_CONTEXT_ID = "context:stage1-recovery-claude-03-v1"
FROZEN_AT = "2026-08-05T07:43:15Z"
PROMPT_CLARIFICATION = (
    "Place each concrete falsification attempt inside that result's required rationale string. "
    "Do not add a falsification_attempt key or any other key; any additional property fails this "
    "strict calibration schema."
)


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def build_first_direct_stage1_recovery_claude_replacement_calibration(
    project_root: Path,
) -> dict[str, Any]:
    source_root = project_root / CALIBRATION_RELATIVE
    output_root = project_root / REPLACEMENT_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError("The Claude replacement calibration is already frozen.")
    source_ledger = _load(source_root / "CALIBRATION_LEDGER.json")
    _replay(
        source_ledger,
        "ledger_digest",
        SOURCE_LEDGER_DIGEST,
        "The source recovery calibration ledger",
    )
    source_entries = {str(item["participant_id"]): item for item in source_ledger["entries"]}
    failed = source_entries[SOURCE_PARTICIPANT_ID]
    if (
        failed["calibration_status"] != "failed"
        or len(failed["calibration_evaluation"]["reason_codes"]) != 6
        or not all(
            "falsification_attempt" in reason
            for reason in failed["calibration_evaluation"]["reason_codes"]
        )
    ):
        raise ValueError("The replacement no longer matches the retained schema failure.")
    source_enrollment = _load(source_root / "PARTICIPANT_ENROLLMENT.json")
    source_participant = next(
        item
        for item in source_enrollment["participants"]
        if item["participant_id"] == SOURCE_PARTICIPANT_ID
    )
    participant = deepcopy(source_participant)
    participant["participant_id"] = REPLACEMENT_PARTICIPANT_ID
    participant["execution_context_id"] = REPLACEMENT_CONTEXT_ID
    participant.pop("configuration_digest", None)
    participant["configuration_digest"] = semantic_digest(participant)
    source_protocol = _load(source_root / "CALIBRATION_PROTOCOL.json")
    source_assignment = next(
        item
        for item in source_protocol["assignments"]
        if item["participant_id"] == SOURCE_PARTICIPANT_ID
    )
    schema = deepcopy(source_assignment["output_schema"])
    schema["properties"]["reviewer_participant_id"]["const"] = REPLACEMENT_PARTICIPANT_ID
    prompt = str(source_assignment["prompt"]).replace(
        f"Reviewer participant identity: {SOURCE_PARTICIPANT_ID}",
        f"Reviewer participant identity: {REPLACEMENT_PARTICIPANT_ID}",
    )
    prompt = prompt.split("Return only one JSON object", 1)[0].rstrip()
    prompt += (
        "\n"
        + PROMPT_CLARIFICATION
        + "\n\nReturn only one JSON object, with no prose or Markdown fence, matching this exact schema:\n"
        + json.dumps(schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    )
    assignment = {
        **{
            key: participant[key]
            for key in (
                "participant_id",
                "role",
                "provider",
                "agent_surface",
                "model_name",
                "model_id",
                "agent_version",
                "reasoning_configuration",
                "execution_context_id",
                "configuration_digest",
                "system_prompt_digest",
                "tool_policy_digest",
                "environment_digest",
                "calibration_suite_digest",
            )
        },
        "call_identity_id": str(
            uuid5(
                NAMESPACE_URL,
                "sc-referee-stage1-semantic-recovery-claude-replacement-calibration-v1",
            )
        ),
        "prompt": prompt,
        "prompt_digest": sha256_digest(prompt),
        "output_schema": schema,
        "output_schema_digest": semantic_digest(schema),
        "interaction_profile": deepcopy(source_assignment["interaction_profile"]),
    }
    output_root.mkdir(parents=True)
    try:
        enrollment: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_recovery_replacement_enrollment",
            "enrollment_version": "1.0.0",
            "source_calibration_ledger_digest": SOURCE_LEDGER_DIGEST,
            "superseded_participant_id": SOURCE_PARTICIPANT_ID,
            "participants": [participant],
            "participant_count": 1,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_participant_enrollment_only",
        }
        enrollment["enrollment_digest"] = semantic_digest(enrollment)
        write_normalized_json_once(output_root / "PARTICIPANT_ENROLLMENT.json", enrollment)

        protocol: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_recovery_replacement_calibration_protocol",
            "protocol_version": "1.0.0",
            "protocol_id": "calibration:stage1-semantic-recovery-claude-replacement-v1",
            "source_calibration_ledger_digest": SOURCE_LEDGER_DIGEST,
            "participant_enrollment_digest": enrollment["enrollment_digest"],
            "calibration_suite_digest": participant["calibration_suite_digest"],
            "expected_verdicts": EXPECTED_CALIBRATION_VERDICTS,
            "prompt_clarification": PROMPT_CLARIFICATION,
            "assignments": [assignment],
            "execution_state": "frozen_not_started",
            "attempt_count": 0,
            "pass_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_calibration_only",
        }
        protocol["protocol_digest"] = semantic_digest(protocol)
        write_normalized_json_once(output_root / "CALIBRATION_PROTOCOL.json", protocol)

        amendment: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_recovery_calibration_replacement_amendment",
            "amendment_version": "1.0.0",
            "source_calibration_ledger_digest": SOURCE_LEDGER_DIGEST,
            "failed_participant_id": SOURCE_PARTICIPANT_ID,
            "failed_response_digest": failed["response_digest"],
            "failure_reason": "schema_forbidden_falsification_attempt_property",
            "replacement_participant_id": REPLACEMENT_PARTICIPANT_ID,
            "replacement_enrollment_digest": enrollment["enrollment_digest"],
            "replacement_calibration_protocol_digest": protocol["protocol_digest"],
            "prompt_delta": PROMPT_CLARIFICATION,
            "scientific_vignettes_unchanged": True,
            "expected_verdicts_unchanged": True,
            "output_schema_unchanged_except_participant_const": True,
            "fresh_participant_identity": True,
            "fresh_execution_context": True,
            "failed_attempt_retained_without_repair": True,
            "frozen_at": FROZEN_AT,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "qualification_authority": "none_calibration_replacement_only",
        }
        amendment["amendment_digest"] = semantic_digest(amendment)
        write_normalized_json_once(output_root / "REPLACEMENT_AMENDMENT.json", amendment)
        return amendment
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    amendment = build_first_direct_stage1_recovery_claude_replacement_calibration(
        arguments.project_root.resolve()
    )
    print(amendment["amendment_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
