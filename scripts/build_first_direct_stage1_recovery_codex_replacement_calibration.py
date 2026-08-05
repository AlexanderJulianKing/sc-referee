from __future__ import annotations

import argparse
import json
import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage1_recovery_calibration import (
    CALIBRATION_RELATIVE as SOURCE_CALIBRATION_RELATIVE,
)
from scripts.build_first_direct_stage1_recovery_calibration import (
    EXPECTED_CALIBRATION_VERDICTS,
)
from scripts.build_first_direct_three_case_stage1_protocol import LANE_RELATIVE
from scripts.build_first_direct_three_case_stage1_semantic_recovery_protocol import (
    REVIEW_RELATIVE as SOURCE_REVIEW_RELATIVE,
)

REPLACEMENT_RELATIVE = (
    LANE_RELATIVE / "reviewer-calibration-v7-stage1-semantic-recovery-codex-replacement"
)
CODEX_REPLACEMENT_RELATIVE = REPLACEMENT_RELATIVE
SOURCE_CALIBRATION_PROTOCOL_DIGEST = (
    "sha256:d8738800d8211cc1a6a4ead04721b09a1eb76e819516fc3dea00eace94538d76"
)
SOURCE_CALIBRATION_ENROLLMENT_DIGEST = (
    "sha256:5b1ecce6b493eadc5184dc359927f19519b0cd8ceeb4124e98220313752bb251"
)
CALIBRATION_SUITE_DIGEST = "sha256:15f3f1636429f624a6fbb649ce6ec9fc8d0bdfd30b6ab673ad47c9ef11cfe671"
SOURCE_DUPLICATE_FAILURE_LEDGER_DIGEST: str | None = (
    "sha256:e47fcf73d71ade4c657ffc796f689457e2b956eafa333ee7583cd05219323267"
)
SOURCE_RECOVERY_AMENDMENT_DIGEST: str | None = (
    "sha256:d5638aa1fee086cf91def672fb5857ac874c0109172c4fea00903c65de21f24e"
)
SOURCE_FAILURE_LEDGER_NAME = "CODEX_DUPLICATE_LAUNCH_FAILURE_LEDGER.json"
SOURCE_RECOVERY_AMENDMENT_NAME = "CODEX_DUPLICATE_LAUNCH_RECOVERY_AMENDMENT.json"
FROZEN_AT = "2026-08-05T08:16:00Z"

SOURCE_PARTICIPANTS = {
    "actor:stage1-recovery-codex-03": "actor:stage1-recovery-codex-01",
    "actor:stage1-recovery-codex-04": "actor:stage1-recovery-codex-02",
}
REPLACEMENT_CONTEXTS = {
    "actor:stage1-recovery-codex-03": "context:stage1-recovery-codex-03-v1",
    "actor:stage1-recovery-codex-04": "context:stage1-recovery-codex-04-v1",
}
CONFIGURATION_FIELDS = (
    "role",
    "provider",
    "agent_surface",
    "model_name",
    "model_id",
    "agent_version",
    "reasoning_configuration",
    "system_prompt_digest",
    "tool_policy_digest",
    "environment_digest",
    "calibration_suite_digest",
)
PROMPT_BOUNDARY = "Return only one JSON object"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _required_digest(value: str | None, label: str) -> str:
    if value is None:
        raise ValueError(f"{label} has not been frozen in the replacement builder.")
    return value


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"Invalid two-Codex replacement timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise ValueError("Two-Codex replacement timestamps must include an offset.")
    return parsed


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def _contains_digest(value: Any, expected: str) -> bool:
    if value == expected:
        return True
    if isinstance(value, dict):
        return any(_contains_digest(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(_contains_digest(item, expected) for item in value)
    return False


def _source_failure_evidence(project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    failure_digest = _required_digest(
        SOURCE_DUPLICATE_FAILURE_LEDGER_DIGEST,
        "The Codex duplicate-launch failure-ledger digest",
    )
    amendment_digest = _required_digest(
        SOURCE_RECOVERY_AMENDMENT_DIGEST,
        "The Codex duplicate-launch recovery-amendment digest",
    )
    source_root = project_root / SOURCE_REVIEW_RELATIVE
    failure = _load(source_root / SOURCE_FAILURE_LEDGER_NAME)
    _replay(failure, "ledger_digest", failure_digest, "The Codex duplicate-launch failure ledger")
    amendment = _load(source_root / SOURCE_RECOVERY_AMENDMENT_NAME)
    _replay(
        amendment,
        "amendment_digest",
        amendment_digest,
        "The Codex duplicate-launch recovery amendment",
    )
    for label, record in (("failure ledger", failure), ("recovery amendment", amendment)):
        if record.get("scientific_label_count") != 0 or record.get("detector_outcome_count") != 0:
            raise ValueError(
                f"The Codex duplicate-launch {label} is not pre-label and pre-outcome."
            )
    if (
        failure.get("artifact_kind")
        != "direct_qualification_stage1_codex_duplicate_launch_failure_ledger"
        or failure.get("failure_class")
        != "overlapping_duplicate_launcher_attempt_identity_collision"
        or failure.get("affected_participant_ids") != sorted(SOURCE_PARTICIPANTS.values())
        or failure.get("retained_review_count") != 6
        or failure.get("stage1_freeze_count") != 0
    ):
        raise ValueError("The retained Codex duplicate-launch failure scope drifted.")
    if (
        amendment.get("artifact_kind")
        != "direct_qualification_stage1_codex_duplicate_launch_recovery_amendment"
        or amendment.get("decision")
        != "abandon_both_affected_codex_configurations_and_recalibrate_fresh_replacements"
        or amendment.get("replacement_calibration_state") != "not_started"
        or amendment.get("replacement_calibration_attempt_count") != 0
        or amendment.get("replacement_review_attempt_count") != 0
        or amendment.get("stage1_freeze_count") != 0
    ):
        raise ValueError("The Codex duplicate-launch recovery authority drifted.")
    abandoned = sorted(
        str(item.get("participant_id"))
        for item in amendment.get("abandoned_codex_configurations", [])
    )
    if abandoned != sorted(SOURCE_PARTICIPANTS.values()):
        raise ValueError("The recovery amendment does not abandon the exact source participants.")
    requirements = amendment.get("replacement_requirements", {})
    if (
        requirements.get("replacement_count") != 2
        or requirements.get("provider") != "OpenAI"
        or requirements.get("both_replacements_must_pass") is not True
        or requirements.get("fresh_calibration_required_before_review") is not True
        or requirements.get("calibration_suite_unchanged") is not True
    ):
        raise ValueError("The two-Codex replacement requirements drifted.")
    if not _contains_digest(amendment, failure_digest):
        raise ValueError("The Codex duplicate-launch recovery amendment does not bind its failure.")
    if not (
        _timestamp(str(failure["recorded_at"]))
        <= _timestamp(str(amendment["frozen_at"]))
        < _timestamp(FROZEN_AT)
    ):
        raise ValueError("The two-Codex replacement calibration was not frozen prospectively.")
    return failure, amendment


def _source_calibration(
    project_root: Path,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source_root = project_root / SOURCE_CALIBRATION_RELATIVE
    enrollment = _load(source_root / "PARTICIPANT_ENROLLMENT.json")
    _replay(
        enrollment,
        "enrollment_digest",
        SOURCE_CALIBRATION_ENROLLMENT_DIGEST,
        "The v5 recovery-calibration enrollment",
    )
    protocol = _load(source_root / "CALIBRATION_PROTOCOL.json")
    _replay(
        protocol,
        "protocol_digest",
        SOURCE_CALIBRATION_PROTOCOL_DIGEST,
        "The v5 recovery-calibration protocol",
    )
    if (
        protocol.get("calibration_suite_digest") != CALIBRATION_SUITE_DIGEST
        or protocol.get("expected_verdicts") != EXPECTED_CALIBRATION_VERDICTS
        or len(protocol.get("expected_verdicts", {})) != 6
        or protocol.get("execution_state") != "frozen_not_started"
        or protocol.get("scientific_label_count") != 0
        or protocol.get("detector_outcome_count") != 0
    ):
        raise ValueError("The v5 recovery-calibration scientific contract drifted.")
    participants = {str(item["participant_id"]): item for item in enrollment["participants"]}
    assignments = {str(item["participant_id"]): item for item in protocol["assignments"]}
    source_ids = set(SOURCE_PARTICIPANTS.values())
    if not source_ids.issubset(participants) or not source_ids.issubset(assignments):
        raise ValueError("The two source Codex calibration configurations are unavailable.")
    for source_id in source_ids:
        participant = participants[source_id]
        assignment = assignments[source_id]
        if (
            participant.get("provider") != "OpenAI"
            or participant.get("model_id") != "gpt-5.6-sol"
            or participant.get("reasoning_configuration") != "high"
            or assignment.get("configuration_digest") != participant.get("configuration_digest")
            or assignment.get("output_schema_digest")
            != semantic_digest(assignment["output_schema"])
            or assignment.get("prompt_digest") != sha256_digest(str(assignment["prompt"]))
        ):
            raise ValueError("A source Codex calibration configuration drifted.")
    return protocol, participants, assignments


def _replacement_participant(source: dict[str, Any], participant_id: str) -> dict[str, Any]:
    participant = deepcopy(source)
    participant["participant_id"] = participant_id
    participant["execution_context_id"] = REPLACEMENT_CONTEXTS[participant_id]
    participant["calibration_status"] = "required_before_participation"
    participant.pop("configuration_digest", None)
    participant["configuration_digest"] = semantic_digest(participant)
    return participant


def _replacement_schema(source: dict[str, Any], participant_id: str) -> dict[str, Any]:
    schema = deepcopy(source)
    schema["properties"]["reviewer_participant_id"]["const"] = participant_id
    return schema


def _replacement_prompt(
    source_prompt: str,
    source_participant_id: str,
    participant_id: str,
    schema: dict[str, Any],
) -> str:
    body = source_prompt.split(PROMPT_BOUNDARY, 1)[0]
    if source_participant_id not in body:
        raise ValueError("A source Codex calibration prompt lacks its participant binding.")
    body = body.replace(source_participant_id, participant_id)
    return (
        body.rstrip()
        + "\n\nReturn only one JSON object, with no prose or Markdown fence, matching this exact schema:\n"
        + json.dumps(schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def build_first_direct_stage1_recovery_codex_replacement_calibration(
    project_root: Path,
) -> dict[str, Any]:
    output_root = project_root / REPLACEMENT_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError("The two-Codex replacement calibration is already frozen.")
    failure_digest = _required_digest(
        SOURCE_DUPLICATE_FAILURE_LEDGER_DIGEST,
        "The Codex duplicate-launch failure-ledger digest",
    )
    recovery_digest = _required_digest(
        SOURCE_RECOVERY_AMENDMENT_DIGEST,
        "The Codex duplicate-launch recovery-amendment digest",
    )
    _failure, _recovery = _source_failure_evidence(project_root)
    source_protocol, source_participants, source_assignments = _source_calibration(project_root)

    participants = []
    assignments = []
    replacement_rows = []
    for participant_id, source_id in SOURCE_PARTICIPANTS.items():
        participant = _replacement_participant(source_participants[source_id], participant_id)
        source_assignment = source_assignments[source_id]
        schema = _replacement_schema(source_assignment["output_schema"], participant_id)
        prompt = _replacement_prompt(
            str(source_assignment["prompt"]),
            source_id,
            participant_id,
            schema,
        )
        assignment = {
            **{
                key: participant[key]
                for key in (
                    "participant_id",
                    *CONFIGURATION_FIELDS,
                    "execution_context_id",
                    "configuration_digest",
                )
            },
            "source_participant_id": source_id,
            "source_configuration_digest": source_participants[source_id]["configuration_digest"],
            "source_assignment_digest": semantic_digest(source_assignment),
            "call_identity_id": str(
                uuid5(
                    NAMESPACE_URL,
                    f"sc-referee-stage1-semantic-recovery-codex-replacement-calibration-v1:{participant_id}",
                )
            ),
            "prompt": prompt,
            "prompt_digest": sha256_digest(prompt),
            "output_schema": schema,
            "output_schema_digest": semantic_digest(schema),
            "interaction_profile": deepcopy(source_assignment["interaction_profile"]),
        }
        participants.append(participant)
        assignments.append(assignment)
        replacement_rows.append(
            {
                "source_participant_id": source_id,
                "source_configuration_digest": source_participants[source_id][
                    "configuration_digest"
                ],
                "replacement_participant_id": participant_id,
                "replacement_configuration_digest": participant["configuration_digest"],
                "replacement_execution_context_id": participant["execution_context_id"],
            }
        )

    output_root.mkdir(parents=True)
    try:
        enrollment: dict[str, Any] = {
            "artifact_kind": "direct_qualification_stage1_recovery_codex_replacement_enrollment",
            "enrollment_version": "1.0.0",
            "source_calibration_enrollment_digest": SOURCE_CALIBRATION_ENROLLMENT_DIGEST,
            "source_duplicate_launch_failure_ledger_digest": failure_digest,
            "source_duplicate_launch_recovery_amendment_digest": recovery_digest,
            "calibration_suite_digest": CALIBRATION_SUITE_DIGEST,
            "superseded_participant_ids": sorted(SOURCE_PARTICIPANTS.values()),
            "participants": participants,
            "participant_count": 2,
            "provider_participation": {"OpenAI": 2},
            "fresh_participant_identities": True,
            "fresh_execution_contexts": True,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_participant_enrollment_only",
        }
        enrollment["enrollment_digest"] = semantic_digest(enrollment)
        write_normalized_json_once(output_root / "PARTICIPANT_ENROLLMENT.json", enrollment)

        protocol: dict[str, Any] = {
            "artifact_kind": (
                "direct_qualification_stage1_recovery_codex_replacement_calibration_protocol"
            ),
            "protocol_version": "1.0.0",
            "protocol_id": "calibration:stage1-semantic-recovery-codex-replacement-v1",
            "source_calibration_protocol_digest": SOURCE_CALIBRATION_PROTOCOL_DIGEST,
            "source_duplicate_launch_failure_ledger_digest": failure_digest,
            "source_duplicate_launch_recovery_amendment_digest": recovery_digest,
            "participant_enrollment_digest": enrollment["enrollment_digest"],
            "calibration_suite_digest": CALIBRATION_SUITE_DIGEST,
            "expected_verdicts": deepcopy(source_protocol["expected_verdicts"]),
            "assignments": assignments,
            "source_vignette_count": 6,
            "scientific_vignettes_unchanged": True,
            "expected_verdicts_unchanged": True,
            "output_schema_unchanged_except_participant_const": True,
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
            "artifact_kind": (
                "direct_qualification_stage1_recovery_codex_replacement_calibration_amendment"
            ),
            "amendment_version": "1.0.0",
            "source_duplicate_launch_failure_ledger_digest": failure_digest,
            "source_duplicate_launch_recovery_amendment_digest": recovery_digest,
            "source_calibration_protocol_digest": SOURCE_CALIBRATION_PROTOCOL_DIGEST,
            "replacement_enrollment_digest": enrollment["enrollment_digest"],
            "replacement_calibration_protocol_digest": protocol["protocol_digest"],
            "replacements": replacement_rows,
            "replacement_count": 2,
            "duplicate_launch_attempts_retained_without_repair": True,
            "source_scientific_responses_not_reused": True,
            "scientific_vignettes_unchanged": True,
            "expected_verdicts_unchanged": True,
            "output_schema_unchanged_except_participant_const": True,
            "model_configuration_unchanged_except_identity_and_context": True,
            "fresh_participant_identities": True,
            "fresh_execution_contexts": True,
            "calibration_required_before_scientific_participation": True,
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
    amendment = build_first_direct_stage1_recovery_codex_replacement_calibration(
        arguments.project_root.resolve()
    )
    print(amendment["amendment_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
