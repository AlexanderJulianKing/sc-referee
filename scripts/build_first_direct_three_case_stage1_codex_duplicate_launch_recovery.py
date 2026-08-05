from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_three_case_stage1_semantic_recovery_protocol import (
    REVIEW_RELATIVE,
)

PROTOCOL_DIGEST = "sha256:c7645bc5b5921f90505ce9f757cfbcff211f7386c14a1b778a8aeef595b93da6"
FROZEN_AT = "2026-08-05T08:10:00Z"
FAILURE_LEDGER_NAME = "CODEX_DUPLICATE_LAUNCH_FAILURE_LEDGER.json"
RECOVERY_AMENDMENT_NAME = "CODEX_DUPLICATE_LAUNCH_RECOVERY_AMENDMENT.json"
CODEX_ARTIFACT_DIGESTS = {
    "actor:stage1-recovery-codex-01": {
        "process_capture": (
            "sha256:1d9943e6450466142010146aa46e7a9614ce3b9de2f5bb6af1a2c741ce896acc"
        ),
        "incoming_capture": (
            "sha256:82024aa62c2ca6f6213e22aa3f995e5f9509264b770780d8199259f3f17cec65"
        ),
        "call_ledger": ("sha256:aeb5efcd3e87c053c34f76372c1d5347bcd19ea4afc6e1149e1673bc8847c3fd"),
    },
    "actor:stage1-recovery-codex-02": {
        "process_capture": (
            "sha256:37548d7a80ed4067b6f5e2c577d13c594a97c14c9467de6ab75747630c36ba4c"
        ),
        "incoming_capture": (
            "sha256:20484231e9a4a78c8a9b303dc7a66b5128354bd013de1dd46cf48e0fdbc59567"
        ),
        "call_ledger": ("sha256:7dc9c8cfb075e42d20393e9bafdcaefdbe580d6be718d67af2f6742d4a5e43ad"),
    },
}


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Duplicate-launch recovery timestamps require an offset.")
    return parsed


def _protocol(project_root: Path) -> dict[str, Any]:
    protocol = _load(project_root / REVIEW_RELATIVE / "STAGE1_REVIEW_PROTOCOL.json")
    _replay(protocol, "protocol_digest", PROTOCOL_DIGEST, "The frozen v2 Stage-1 protocol")
    if (
        protocol["execution_state"] != "frozen_not_started"
        or protocol["stage1_review_count"] != 0
        or protocol["stage1_freeze_count"] != 0
        or protocol["scientific_label_count"] != 0
        or protocol["detector_outcome_count"] != 0
    ):
        raise ValueError("The frozen v2 protocol declaration has drifted.")
    return protocol


def _binary_binding(root: Path, process: dict[str, Any], name: str, field: str) -> None:
    payload = (root / name).read_bytes()
    byte_size_field = field.replace("_digest", "_byte_size")
    if sha256_digest(payload) != process[field] or len(payload) != process[byte_size_field]:
        raise ValueError(f"The retained {name} bytes do not match their process capture.")


def _retained_codex_attempts(project_root: Path, protocol: dict[str, Any]) -> list[dict[str, Any]]:
    review_root = project_root / REVIEW_RELATIVE
    calls = {str(item["participant_id"]): item for item in protocol["calls"]}
    retained: list[dict[str, Any]] = []
    for participant_id, digests in CODEX_ARTIFACT_DIGESTS.items():
        call = calls[participant_id]
        slug = participant_id.removeprefix("actor:")
        process_path = review_root / "codex-process-captures" / slug / "capture.json"
        incoming_path = review_root / "incoming" / f"{slug}.json"
        ledger_path = review_root / "stage1-call-ledgers" / f"{slug}.json"
        process = _load(process_path)
        _replay(
            process,
            "capture_digest",
            digests["process_capture"],
            f"The retained process capture for {participant_id}",
        )
        process_root = process_path.parent
        _binary_binding(process_root, process, "stdout.bin", "stdout_digest")
        _binary_binding(process_root, process, "stderr.bin", "stderr_digest")
        _binary_binding(
            process_root,
            process,
            "final-response.bin",
            "final_response_digest",
        )
        incoming = _load(incoming_path)
        _replay(
            incoming,
            "capture_digest",
            digests["incoming_capture"],
            f"The retained incoming capture for {participant_id}",
        )
        ledger = _load(ledger_path)
        _replay(
            ledger,
            "ledger_digest",
            digests["call_ledger"],
            f"The retained call ledger for {participant_id}",
        )
        if (
            process["protocol_digest"] != PROTOCOL_DIGEST
            or incoming["protocol_digest"] != PROTOCOL_DIGEST
            or ledger["protocol_digest"] != PROTOCOL_DIGEST
            or process["participant_id"] != participant_id
            or incoming["participant_id"] != participant_id
            or ledger["participant_id"] != participant_id
            or process["call_identity_id"] != call["call_identity_id"]
            or incoming["call_identity_id"] != call["call_identity_id"]
            or ledger["call_identity_id"] != call["call_identity_id"]
            or incoming["transport"]["process_capture_digest"] != process["capture_digest"]
            or ledger["incoming_capture_digest"] != incoming["capture_digest"]
            or process["return_code"] != 0
            or process["final_response_digest"] != incoming["raw_response_digest"]
            or ledger["review_count"] != 3
            or ledger["admission_status"] != "three_reviews_captured"
            or ledger["scientific_label_count"] != 0
            or ledger["detector_outcome_count"] != 0
        ):
            raise ValueError(f"The retained artifact chain drifted for {participant_id}.")
        if _timestamp(str(ledger["recorded_at"])) >= _timestamp(FROZEN_AT):
            raise ValueError("The duplicate-launch failure freeze predates retained evidence.")
        retained.append(
            {
                "participant_id": participant_id,
                "participant_configuration_digest": call["participant_configuration_digest"],
                "execution_context_id": call["participant"]["execution_context_id"],
                "call_identity_id": call["call_identity_id"],
                "case_order": call["case_order"],
                "process_capture": {
                    "relative_path": process_path.relative_to(review_root).as_posix(),
                    "capture_digest": process["capture_digest"],
                    "final_response_digest": process["final_response_digest"],
                },
                "incoming_capture": {
                    "relative_path": incoming_path.relative_to(review_root).as_posix(),
                    "capture_digest": incoming["capture_digest"],
                    "raw_response_digest": incoming["raw_response_digest"],
                },
                "call_ledger": {
                    "relative_path": ledger_path.relative_to(review_root).as_posix(),
                    "ledger_digest": ledger["ledger_digest"],
                    "review_count": ledger["review_count"],
                    "review_capture_digests": sorted(
                        str(item["capture_digest"]) for item in ledger["entries"]
                    ),
                },
                "retention_status": "retained_exact_but_label_ineligible",
            }
        )
    return retained


def _unexposed_claude_calls(project_root: Path, protocol: dict[str, Any]) -> list[dict[str, Any]]:
    review_root = project_root / REVIEW_RELATIVE
    calls = [item for item in protocol["calls"] if item["participant"]["provider"] == "Anthropic"]
    if len(calls) != 2:
        raise ValueError("The frozen v2 protocol no longer contains two Claude calls.")
    preserved: list[dict[str, Any]] = []
    for call in calls:
        slug = str(call["participant_id"]).removeprefix("actor:")
        forbidden = [
            review_root / "incoming" / f"{slug}.json",
            review_root / "stage1-call-ledgers" / f"{slug}.json",
            *list((review_root / "stage1-captures").glob(f"*/{slug}")),
        ]
        if any(path.exists() or path.is_symlink() for path in forbidden):
            raise ValueError("A Claude recovery call is no longer unexposed and unattempted.")
        preserved.append(
            {
                "participant_id": call["participant_id"],
                "participant_configuration_digest": call["participant_configuration_digest"],
                "execution_context_id": call["participant"]["execution_context_id"],
                "call_identity_id": call["call_identity_id"],
                "prompt_digest": call["prompt_digest"],
                "output_schema_digest": call["output_schema_digest"],
                "case_order": call["case_order"],
                "preservation_status": "authorized_unattempted_unchanged",
            }
        )
    return preserved


def build_first_direct_three_case_stage1_codex_duplicate_launch_recovery(
    project_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    review_root = project_root / REVIEW_RELATIVE
    failure_path = review_root / FAILURE_LEDGER_NAME
    amendment_path = review_root / RECOVERY_AMENDMENT_NAME
    if any(path.exists() or path.is_symlink() for path in (failure_path, amendment_path)):
        raise FileExistsError("The Codex duplicate-launch recovery is already frozen.")
    protocol = _protocol(project_root)
    retained = _retained_codex_attempts(project_root, protocol)
    preserved_claude = _unexposed_claude_calls(project_root, protocol)

    failure: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_codex_duplicate_launch_failure_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": PROTOCOL_DIGEST,
        "controller_implementation": {
            "path": "scripts/run_first_direct_three_case_stage1_semantic_recovery_codex.py",
            "content_digest": sha256_digest(
                (
                    project_root
                    / "scripts/run_first_direct_three_case_stage1_semantic_recovery_codex.py"
                ).read_bytes()
            ),
        },
        "failure_class": "overlapping_duplicate_launcher_attempt_identity_collision",
        "observed_failure": {
            "duplicate_launcher_model_calls_completed_before_persistence": True,
            "persistence_exception": "FileExistsError",
            "exception_site": "process_root.mkdir(parents=True)",
            "first_colliding_participant_id": "actor:stage1-recovery-codex-01",
            "duplicate_response_bytes_retained": False,
            "duplicate_response_digests_known": False,
            "unique_attempt_identity_established": False,
        },
        "affected_participant_ids": sorted(CODEX_ARTIFACT_DIGESTS),
        "retained_artifacts": retained,
        "retained_review_count": 6,
        "retained_artifact_admission": "ineligible_duplicate_attempt_identity",
        "stage1_freeze_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "recorded_at": FROZEN_AT,
        "qualification_authority": "none_failure_evidence_only",
    }
    failure["ledger_digest"] = semantic_digest(failure)

    protocol_calls = {str(item["participant_id"]): item for item in protocol["calls"]}
    abandoned = [
        {
            "participant_id": participant_id,
            "participant_configuration_digest": protocol_calls[participant_id][
                "participant_configuration_digest"
            ],
            "execution_context_id": protocol_calls[participant_id]["participant"][
                "execution_context_id"
            ],
            "call_identity_id": protocol_calls[participant_id]["call_identity_id"],
            "case_order": protocol_calls[participant_id]["case_order"],
            "panel_status": "abandoned_permanently_for_this_panel",
        }
        for participant_id in sorted(CODEX_ARTIFACT_DIGESTS)
    ]
    amendment: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_codex_duplicate_launch_recovery_amendment",
        "amendment_version": "1.0.0",
        "protocol_digest": PROTOCOL_DIGEST,
        "source_failure_ledger_digest": failure["ledger_digest"],
        "decision": "abandon_both_affected_codex_configurations_and_recalibrate_fresh_replacements",
        "abandoned_codex_configurations": abandoned,
        "replacement_requirements": {
            "replacement_count": 2,
            "provider": "OpenAI",
            "fresh_participant_ids_required": True,
            "fresh_execution_contexts_required": True,
            "fresh_call_identity_ids_required": True,
            "fresh_calibration_required_before_review": True,
            "calibration_schema_profile": "stage1-semantic-payload-v2",
            "calibration_suite_unchanged": True,
            "both_replacements_must_pass": True,
            "replacement_review_calls_may_start_before_calibration_freeze": False,
            "preserved_case_orders": [item["case_order"] for item in abandoned],
        },
        "preserved_unexposed_claude_configurations": preserved_claude,
        "preserved_scientific_material": {
            "canonical_issue_class_scope": protocol["canonical_issue_class_scope"],
            "semantic_recovery_contract_digest": semantic_digest(
                protocol["semantic_recovery_contract"]
            ),
            "source_case_bindings_digest": semantic_digest(protocol["source_case_bindings"]),
            "workflow_bytes_unchanged": True,
            "workspace_manifests_unchanged": True,
            "scientific_contract_unchanged": True,
            "case_orders_unchanged": True,
        },
        "prohibitions": [
            "admitting_any_retained_codex_review_to_a_stage1_freeze_or_scientific_label",
            "reusing_either_abandoned_codex_participant_id_or_execution_context",
            "repairing_or_relabeling_retained_response_content",
            "modifying_or_replacing_the_two_unexposed_claude_configurations",
            "changing_workflow_bytes_workspace_manifests_case_orders_or_scientific_contract",
            "starting_replacement_review_before_fresh_calibration_is_frozen_and_passed",
        ],
        "replacement_calibration_state": "not_started",
        "replacement_calibration_attempt_count": 0,
        "replacement_review_attempt_count": 0,
        "stage1_freeze_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_prospective_recovery_only",
    }
    amendment["amendment_digest"] = semantic_digest(amendment)
    write_normalized_json_once(failure_path, failure)
    write_normalized_json_once(amendment_path, amendment)
    return failure, amendment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    failure, amendment = build_first_direct_three_case_stage1_codex_duplicate_launch_recovery(
        arguments.project_root.resolve()
    )
    print(failure["ledger_digest"])
    print(amendment["amendment_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
