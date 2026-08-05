from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_three_case_stage1_protocol import REVIEW_RELATIVE
from scripts.record_first_direct_three_case_stage1_reviews import PROTOCOL_DIGEST

FAILURE_LEDGER_DIGEST = "sha256:8ab75e78a52d476d395f11f8dfa46d54cd2371309c17db3d7210e7a984039787"
SOURCE_COMMIT = "307bd6c6852bc511948ac24e41a3f936d0f6abd1"
FROZEN_AT = "2026-08-05T06:45:00Z"
AMENDMENT_NAME = "STAGE1_CODEX_TRANSPORT_RECOVERY_AMENDMENT.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected one JSON object at {path}.")
    return cast(dict[str, Any], value)


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def build_stage1_codex_transport_recovery_amendment(project_root: Path) -> dict[str, Any]:
    root = project_root / REVIEW_RELATIVE
    protocol = _load(root / "STAGE1_REVIEW_PROTOCOL.json")
    _replay(protocol, "protocol_digest", PROTOCOL_DIGEST, "The Stage-1 protocol")
    failure = _load(root / "CODEX_TRANSPORT_FAILURE_LEDGER.json")
    _replay(
        failure,
        "ledger_digest",
        FAILURE_LEDGER_DIGEST,
        "The Codex transport failure ledger",
    )
    if (
        failure["protocol_digest"] != PROTOCOL_DIGEST
        or failure["summary"]["pre_inference_failure_count"] != 2
        or failure["summary"]["reviewer_response_count"] != 0
        or failure["summary"]["stage1_review_count"] != 0
    ):
        raise ValueError("The retained failure does not authorize transport-only recovery.")

    failures = {str(item["participant_id"]): item for item in failure["attempts"]}
    calls = [item for item in protocol["calls"] if item["participant"]["provider"] == "OpenAI"]
    if len(calls) != 2 or {str(item["participant_id"]) for item in calls} != set(failures):
        raise ValueError("The exact two failed Codex assignments are unavailable.")

    recovery_calls = []
    for call in calls:
        participant_id = str(call["participant_id"])
        failed = failures[participant_id]
        schema_text = json.dumps(call["output_schema"], sort_keys=True, ensure_ascii=False)
        if (
            failed["superseded_call_identity_id"] != call["call_identity_id"]
            or failed["prompt_digest"] != call["prompt_digest"]
            or failed["semantic_output_schema_digest"] != call["output_schema_digest"]
            or sha256_digest(call["prompt"]) != call["prompt_digest"]
            or semantic_digest(call["output_schema"]) != call["output_schema_digest"]
            or schema_text not in str(call["prompt"])
        ):
            raise ValueError(f"Frozen semantic assignment drifted for {participant_id}.")
        slug = participant_id.removeprefix("actor:")
        recovery_calls.append(
            {
                "participant_id": participant_id,
                "semantic_call_identity_id": call["call_identity_id"],
                "superseded_transport_attempt_identity_id": call["call_identity_id"],
                "transport_attempt_identity_id": str(
                    uuid5(
                        NAMESPACE_URL,
                        f"sc-referee-first-envelope-stage1-codex-transport-recovery-v1:{participant_id}",
                    )
                ),
                "fresh_transport_context_id": str(
                    uuid5(
                        NAMESPACE_URL,
                        f"sc-referee-first-envelope-stage1-codex-ephemeral-context-v1:{participant_id}",
                    )
                ),
                "participant_configuration_digest": call["participant_configuration_digest"],
                "prompt_digest": call["prompt_digest"],
                "semantic_output_schema_digest": call["output_schema_digest"],
                "case_order": call["case_order"],
                "packet_digests": [
                    item["packet_digest"]
                    for item in cast(list[dict[str, Any]], call["packet_refs"])
                ],
                "failed_process_capture_digest": failed["process_capture_digest"],
                "recovery_process_capture_relative_path": (
                    f"codex-recovery-process-captures/{slug}"
                ),
                "incoming_capture_relative_path": f"incoming/{slug}.json",
            }
        )

    implementation_paths = (
        "evaluation/src/sc_referee_evaluation/review_semantic_payload.py",
        "scripts/record_first_direct_three_case_stage1_reviews.py",
        "scripts/run_first_direct_three_case_stage1_codex.py",
        "scripts/run_first_direct_three_case_stage1_codex_recovery.py",
        "scripts/build_first_direct_three_case_stage1_codex_recovery.py",
    )
    amendment: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_codex_transport_recovery_amendment",
        "amendment_version": "1.0.0",
        "amendment_id": "stage1-transport-recovery:complete-domain-codex-v1",
        "source_commit": SOURCE_COMMIT,
        "source_commit_scope": "retained-failure parent; recovery-controller files are separately content-bound",
        "protocol_digest": PROTOCOL_DIGEST,
        "retained_failure_ledger_digest": FAILURE_LEDGER_DIGEST,
        "controller_implementation": [
            {
                "path": path_value,
                "content_digest": sha256_digest((project_root / path_value).read_bytes()),
            }
            for path_value in implementation_paths
        ],
        "eligibility_basis": {
            "failed_attempt_count": 2,
            "model_inference_started_count": 0,
            "reviewer_response_count": 0,
            "review_admitted_count": 0,
            "failure_reason_code": "api_rejected_unsupported_allof_keyword",
        },
        "semantic_invariants": {
            "prompt_bytes_unchanged": True,
            "case_order_unchanged": True,
            "packet_bytes_unchanged": True,
            "participant_configuration_unchanged": True,
            "semantic_output_schema_unchanged": True,
            "local_semantic_validation_unchanged": True,
            "controller_semantic_repair_permitted": False,
            "scientific_content_changed": False,
        },
        "transport_delta": {
            "removed": ["codex_cli_api_enforced_output_schema"],
            "added": [
                "prompt_embedded_exact_semantic_schema",
                "post_response_exact_local_semantic_schema_validation",
            ],
            "api_output_schema_argument_present": False,
            "raw_response_capture_before_validation": True,
            "fresh_ephemeral_context_per_call": True,
            "parallel_submission": True,
        },
        "recovery_calls": recovery_calls,
        "failure_policy": {
            "one_recovery_attempt_per_participant": True,
            "all_process_evidence_retained_before_assessment": True,
            "invalid_or_incomplete_batch_admits_no_reviews_from_that_call": True,
            "semantic_content_may_not_be_controller_repaired": True,
        },
        "execution_state": "frozen_not_started",
        "reviewer_response_count": 0,
        "stage1_review_count": 0,
        "stage1_freeze_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_transport_recovery_amendment_only",
    }
    amendment["amendment_digest"] = semantic_digest(amendment)
    return amendment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    project_root = arguments.project_root.resolve()
    output = project_root / REVIEW_RELATIVE / AMENDMENT_NAME
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Refusing to replace frozen recovery amendment: {output}")
    amendment = build_stage1_codex_transport_recovery_amendment(project_root)
    write_normalized_json_once(output, amendment)
    print(amendment["amendment_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
