from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee_evaluation.review_protocol import build_stage1_review_packet
from sc_referee_evaluation.review_semantic_payload import build_stage1_batch_output_schema
from sc_referee_evaluation.workspace import build_blind_workspace

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import (
    normalized_json_bytes,
    write_normalized_json,
    write_normalized_json_once,
)
from sc_referee.records.observed import build_file_records
from sc_referee.snapshot.repository import AssetIdentityPolicy, capture_repository
from sc_referee.storage.atomic import atomic_write_bytes

LANE_RELATIVE = Path(
    "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2"
)
AUTHORING_RELATIVE = LANE_RELATIVE / "pilot-authoring-v4-three-case"
CALIBRATION_RELATIVE = LANE_RELATIVE / "reviewer-calibration-v4-app"
REVIEW_RELATIVE = LANE_RELATIVE / "pilot-scientific-review-v1-three-case"

SOURCE_COMMIT = "09ab3c88be0e79480f1207743e70ef0174fcb8a1"
SNAPSHOT_AT = "2026-08-05T05:58:00Z"
WORKSPACE_AT = "2026-08-05T05:59:00Z"
PACKET_AT = "2026-08-05T06:00:00Z"
FROZEN_AT = "2026-08-05T06:01:00Z"
CANONICAL_ISSUE_CLASS = "issue-class:retained-subset-for-complete-domain"
V4_AUTHORING_LEDGER_DIGEST = (
    "sha256:6487d1b7cccfb1fdb90fc080b93ea84233b3f81543d17e7ac3a99f30f3270ebc"
)
ACTIVE_CALIBRATION_LEDGER_DIGEST = (
    "sha256:3c64169c830ff1e963f81fe0e774e367021e3ad4f77892641002e4ff7f13e030"
)
PARTICIPANT_ENROLLMENT_DIGEST = (
    "sha256:95ef5badd874db346279de725a35679da80d00bf8d40c323041b414ce750a5bc"
)
BASE_STAGE1_PROMPT_DIGEST = (
    "sha256:c400be8521c4ef70603e940159c1a049cc5913c5b1eb81918fdf042d409cb778"
)
CASE_IDS = [
    "case:2e26bf5ece15be03717f",
    "case:35069763f06891dba5a3",
    "case:b036fd64c647dfd93e35",
]
STAGE1_REVIEWERS = [
    "actor:stage1-claude-01",
    "actor:stage1-claude-02",
    "actor:stage1-codex-01",
    "actor:stage1-codex-02",
]
CASE_ORDERS = {
    "actor:stage1-claude-01": CASE_IDS,
    "actor:stage1-claude-02": [CASE_IDS[2], CASE_IDS[0], CASE_IDS[1]],
    "actor:stage1-codex-01": [CASE_IDS[1], CASE_IDS[2], CASE_IDS[0]],
    "actor:stage1-codex-02": [CASE_IDS[0], CASE_IDS[2], CASE_IDS[1]],
}
VISIBLE_FILES = [
    {"path": "task.md", "role": "scientific_task"},
    {"path": "inputs/data.csv", "role": "staged_data"},
    {"path": "workflow/analysis.py", "role": "workflow_source"},
    {"path": "results/report.md", "role": "report"},
]


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], digest_field: str, expected: str, label: str) -> None:
    supplied = record.pop(digest_field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[digest_field] = supplied


def _extract_author_visible_briefs(authoring_protocol: dict[str, Any]) -> dict[str, Any]:
    briefs_by_case: dict[str, Any] = {}
    for assignment in authoring_protocol["author_assignments"]:
        prompt = str(assignment["prompt"])
        try:
            encoded = prompt.split("Author-visible briefs:\n", 1)[1].split(
                "\n\nReturn only one", 1
            )[0]
            briefs = json.loads(encoded)
        except (IndexError, json.JSONDecodeError) as error:
            raise ValueError("The frozen author-visible briefs cannot be rederived.") from error
        if [semantic_digest(item) for item in briefs] != assignment["author_visible_brief_digests"]:
            raise ValueError("An author-visible brief digest does not replay.")
        for brief in briefs:
            case_id = str(brief["case_id"])
            if case_id in briefs_by_case:
                raise ValueError(f"Duplicate author-visible brief for {case_id}.")
            briefs_by_case[case_id] = brief
    if set(briefs_by_case) != set(CASE_IDS):
        raise ValueError("The author-visible brief set does not equal the admitted cohort.")
    return briefs_by_case


def _participant_agent(participant: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": participant["provider"],
        "agent_surface": participant["agent_surface"],
        "model_name": participant["model_name"],
        "model_id": participant["model_id"],
        "agent_version": participant["agent_version"],
        "model_snapshot": None,
        "reasoning_configuration": participant["reasoning_configuration"],
        "execution_context_id": participant["execution_context_id"],
        "independent_context": True,
        "system_prompt_digest": participant["system_prompt_digest"],
        "tool_policy_digest": participant["tool_policy_digest"],
        "environment_digest": participant["environment_digest"],
    }


def _answer_side_sources(authoring_root: Path, case_slug: str) -> dict[str, bytes]:
    paths = {
        ".answer-side/case-contract.json": authoring_root / "case-contracts" / f"{case_slug}.json",
        ".answer-side/author-declaration.json": authoring_root
        / "author-declarations"
        / f"{case_slug}.json",
        ".answer-side/case-manifest.json": authoring_root / "case-manifests" / f"{case_slug}.json",
        ".answer-side/selected-result-derivation.json": authoring_root
        / "selected-result-derivations"
        / f"{case_slug}.json",
        ".answer-side/selected-result-validation.json": authoring_root
        / "selected-result-validations"
        / f"{case_slug}.json",
        ".answer-side/authoring-ledger.json": authoring_root / "AUTHORING_LEDGER.json",
        ".answer-side/authoring-protocol.json": authoring_root / "PILOT_AUTHORING_PROTOCOL.json",
        ".answer-side/restart-amendment.json": authoring_root
        / "PILOT_AUTHORING_RESTART_AMENDMENT.json",
        ".answer-side/claude-author-capture.json": authoring_root
        / "incoming"
        / "pilot-author-claude-04.json",
        ".answer-side/codex-author-capture.json": authoring_root
        / "incoming"
        / "pilot-author-codex-04.json",
    }
    payloads: dict[str, bytes] = {}
    for relative, source in paths.items():
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Required answer-side source is unavailable: {source}")
        payloads[relative] = source.read_bytes()
    return payloads


def _prepare_case(
    project_root: Path,
    output_root: Path,
    case_id: str,
    scientific_task: str,
) -> dict[str, Any]:
    case_slug = case_id.removeprefix("case:")
    authoring_root = project_root / AUTHORING_RELATIVE
    admitted_root = authoring_root / "cases" / case_slug
    admitted_manifest = _load(authoring_root / "case-manifests" / f"{case_slug}.json")
    declared_digests = {
        str(item["path"]): str(item["content_digest"]) for item in admitted_manifest["files"]
    }
    if set(declared_digests) != {
        "inputs/data.csv",
        "workflow/analysis.py",
        "results/report.md",
    }:
        raise ValueError(f"Admitted case {case_id} has an unexpected file inventory.")

    preparation_root = output_root / "case-preparations" / case_slug
    runner_source = preparation_root / "runner-source"
    runner_source.mkdir(parents=True)
    task_payload = (scientific_task.rstrip() + "\n").encode("utf-8")
    atomic_write_bytes(runner_source / "task.md", task_payload)
    visible_digests = {"task.md": sha256_digest(task_payload)}
    for path_value in sorted(declared_digests):
        source = admitted_root / path_value
        payload = source.read_bytes()
        if sha256_digest(payload) != declared_digests[path_value]:
            raise ValueError(f"Admitted case bytes drifted for {case_id} {path_value}.")
        atomic_write_bytes(runner_source / path_value, payload)
        visible_digests[path_value] = sha256_digest(payload)

    hidden_payloads = _answer_side_sources(authoring_root, case_slug)
    for path_value, payload in hidden_payloads.items():
        atomic_write_bytes(runner_source / path_value, payload)

    full_digest_budget = sum(
        path.stat().st_size for path in runner_source.rglob("*") if path.is_file()
    )
    captured = capture_repository(
        runner_source,
        preparation_root / "snapshot",
        f"pilot-stage1:{case_id}",
        captured_at=SNAPSHOT_AT,
        identity_policy=AssetIdentityPolicy(
            full_digest_byte_budget=full_digest_budget,
            sampled_fingerprint_byte_budget=0,
        ),
    )
    file_records = build_file_records(
        captured.file_records,
        captured.asset_identity_records,
        str(captured.snapshot_record["snapshot_id"]),
        SNAPSHOT_AT,
    )
    write_normalized_json(preparation_root / "snapshot.json", captured.snapshot_record)
    atomic_write_bytes(
        preparation_root / "file-records.jsonl",
        b"".join(normalized_json_bytes(record) for record in file_records),
    )
    atomic_write_bytes(
        preparation_root / "asset-identities.jsonl",
        b"".join(normalized_json_bytes(record) for record in captured.asset_identity_records),
    )

    contract = _load(authoring_root / "case-contracts" / f"{case_slug}.json")
    answer_markers = {
        str(contract["canonical_issue_class"]),
        str(contract["envelope"]["binding_digest"]),
        str(contract["envelope"]["candidate_id"]),
        str(contract["envelope"]["check_id"]),
        str(contract["envelope"]["envelope_id"]),
        str(contract["contract_digest"]),
        "error-bearing",
        "corrected-twin",
        "valid-alternative",
    }
    workspace_manifest = build_blind_workspace(
        captured.materialized_root,
        preparation_root / "workspace",
        preparation_root / "workspace-manifest.json",
        VISIBLE_FILES,
        snapshot=captured.snapshot_record,
        file_records=file_records,
        asset_identities=captured.asset_identity_records,
        created_at=WORKSPACE_AT,
        forbidden_source_paths=set(hidden_payloads),
        forbidden_digests={sha256_digest(payload) for payload in hidden_payloads.values()},
        forbidden_markers=answer_markers,
    )
    workspace_digests = {
        str(item["path"]): str(item["content_digest"]) for item in workspace_manifest["files"]
    }
    if workspace_digests != visible_digests:
        raise ValueError(f"Blind workspace projection drifted for {case_id}.")
    scanner = workspace_manifest["scanner"]
    if (
        scanner["unresolved_forbidden_source_path_count"] != 0
        or scanner["forbidden_path_count"] != len(hidden_payloads)
        or workspace_manifest["answer_side_content_copied"] is not False
        or workspace_manifest["project_code_executed"] is not False
    ):
        raise ValueError(f"Blind workspace leakage controls are incomplete for {case_id}.")

    preparation: dict[str, Any] = {
        "artifact_kind": "direct_qualification_stage1_case_preparation",
        "preparation_version": "1.0.0",
        "case_id": case_id,
        "source_commit": SOURCE_COMMIT,
        "v4_authoring_ledger_digest": V4_AUTHORING_LEDGER_DIGEST,
        "scientific_task_digest": sha256_digest(scientific_task),
        "source_case_manifest_digest": admitted_manifest["manifest_digest"],
        "snapshot_ref": {
            "record_type": "repository_snapshot",
            "record_id": captured.snapshot_record["snapshot_id"],
        },
        "snapshot_digest": semantic_digest(captured.snapshot_record),
        "workspace_id": workspace_manifest["workspace_id"],
        "workspace_manifest_digest": workspace_manifest["manifest_digest"],
        "visible_paths": sorted(visible_digests),
        "visible_content_digests": dict(sorted(visible_digests.items())),
        "answer_side_path_count": len(hidden_payloads),
        "answer_side_marker_count": len(answer_markers),
        "answer_side_content_copied": False,
        "project_code_executed": False,
        "model_invoked": False,
        "created_at": WORKSPACE_AT,
        "qualification_authority": "none_review_preparation_only",
    }
    preparation["preparation_digest"] = semantic_digest(preparation)
    write_normalized_json_once(preparation_root / "case-preparation.json", preparation)
    return preparation


def _render_file(payload: bytes) -> str:
    text = payload.decode("utf-8")
    lines = text.splitlines()
    return "\n".join(
        f"L{index:04d} | {line}" if line else f"L{index:04d} |"
        for index, line in enumerate(lines, 1)
    )


def _batch_prompt(
    base_prompt: str,
    participant_id: str,
    case_order: list[str],
    workspaces: dict[str, Path],
    output_schema: dict[str, Any],
) -> str:
    blocks = []
    for case_id in case_order:
        workspace = workspaces[case_id]
        files = []
        for path_value in sorted(item["path"] for item in VISIBLE_FILES):
            payload = (workspace / path_value).read_bytes()
            files.append(f"FILE {path_value}\n{_render_file(payload)}\nEND FILE {path_value}")
        blocks.append(f"OPAQUE CASE {case_id}\n" + "\n\n".join(files) + f"\nEND CASE {case_id}")
    return (
        "System instructions for this isolated Stage-1 scientific review:\n"
        + base_prompt.rstrip()
        + "\n\nReviewer participant identity: "
        + participant_id
        + "\nThis frozen transport batch contains three opaque cases. Review every case independently. "
        "Do not compare cases, infer relationships among them, or use one case as evidence for another. "
        "Use no tools, files, external sources, detector output, answer key, prior label, or other review.\n\n"
        "The only scientific issue class in scope is "
        + CANONICAL_ISSUE_CLASS
        + ": a selected rate uses a retained-subset exposure denominator while the stated task and "
        "reported claim require the complete domain. Use demonstrated_issue only when the visible "
        "task, data, workflow, and selected report directly entail that narrow mismatch. A target "
        "explicitly conditional on the retained subset is not this issue. Do not report unrelated concerns.\n\n"
        "For each case, state one concrete falsification attempt, cite at least one exact complete-line "
        "evidence span, and cite at least one exact complete-line counterevidence or falsification span. "
        "Set cross_case_evidence_used to false; if you cannot review a case without another case, the "
        "submission is invalid. quoted_text must omit the displayed "
        "L#### | prefix and equal the underlying complete file line or consecutive lines joined by LF. "
        "For a non-demonstrated verdict, bounded_statement and root_cause must be null. Confidence is "
        "recorded but never used for labeling.\n\n"
        + "\n\n".join(blocks)
        + "\n\nReturn only one unfenced JSON object matching this exact schema:\n"
        + json.dumps(output_schema, sort_keys=True, ensure_ascii=False)
        + "\n"
    ).strip()


def build_first_direct_three_case_stage1_protocol(project_root: Path) -> dict[str, Any]:
    output_root = project_root / REVIEW_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise ValueError(f"Stage-1 protocol output already exists: {output_root}")
    authoring_root = project_root / AUTHORING_RELATIVE
    authoring_ledger = _load(authoring_root / "AUTHORING_LEDGER.json")
    _replay(
        authoring_ledger,
        "ledger_digest",
        V4_AUTHORING_LEDGER_DIGEST,
        "The v4 authoring ledger",
    )
    if (
        authoring_ledger["summary"]["metric_eligible_case_count"] != 3
        or authoring_ledger["summary"]["scientific_label_count"] != 0
        or authoring_ledger["summary"]["detector_outcome_count"] != 0
    ):
        raise ValueError("The admitted cohort is not in the exact pre-review state.")
    authoring_protocol = _load(authoring_root / "PILOT_AUTHORING_PROTOCOL.json")
    briefs = _extract_author_visible_briefs(authoring_protocol)

    calibration_root = project_root / CALIBRATION_RELATIVE
    enrollment = _load(calibration_root / "PARTICIPANT_ENROLLMENT.json")
    _replay(
        enrollment,
        "enrollment_digest",
        PARTICIPANT_ENROLLMENT_DIGEST,
        "The active participant enrollment",
    )
    calibration = _load(calibration_root / "AGGREGATE_CALIBRATION_LEDGER.json")
    _replay(
        calibration,
        "ledger_digest",
        ACTIVE_CALIBRATION_LEDGER_DIGEST,
        "The active reviewer calibration ledger",
    )
    if calibration["summary"]["all_active_reviewer_configurations_passed"] is not True:
        raise ValueError("Not every active reviewer configuration passed calibration.")
    passed_ids = {
        str(item["participant_id"])
        for item in calibration["entries"]
        if item["calibration_status"] == "passed"
    }
    if not set(STAGE1_REVIEWERS).issubset(passed_ids):
        raise ValueError("The exact four Stage-1 reviewers have not all passed calibration.")
    participants = {str(item["participant_id"]): item for item in enrollment["participants"]}

    base_prompt_path = (
        project_root
        / "evaluation/qualification/bounded-analysis-method-conflict-v0.2.0-precase/stage1-prompt.txt"
    )
    base_prompt = base_prompt_path.read_text(encoding="utf-8")
    if sha256_digest(base_prompt) != BASE_STAGE1_PROMPT_DIGEST:
        raise ValueError("The accepted Stage-1 base prompt has drifted.")

    output_root.mkdir(parents=True)
    try:
        preparations: dict[str, dict[str, Any]] = {}
        workspaces: dict[str, Path] = {}
        for case_id in CASE_IDS:
            preparation = _prepare_case(
                project_root,
                output_root,
                case_id,
                str(briefs[case_id]["scientific_task"]),
            )
            preparations[case_id] = preparation
            workspaces[case_id] = (
                output_root / "case-preparations" / case_id.removeprefix("case:") / "workspace"
            )

        calls = []
        for participant_id in STAGE1_REVIEWERS:
            participant = participants[participant_id]
            if participant["role"] != "stage1_reviewer":
                raise ValueError(f"Participant {participant_id} is not a Stage-1 reviewer.")
            case_order = CASE_ORDERS[participant_id]
            schema = build_stage1_batch_output_schema(
                participant_id, case_order, CANONICAL_ISSUE_CLASS
            )
            prompt = _batch_prompt(
                base_prompt,
                participant_id,
                case_order,
                workspaces,
                schema,
            )
            reviewer_agent = _participant_agent(participant)
            packet_refs = []
            for case_id in case_order:
                case_slug = case_id.removeprefix("case:")
                manifest = _load(
                    output_root / "case-preparations" / case_slug / "workspace-manifest.json"
                )
                packet = build_stage1_review_packet(
                    case_id,
                    manifest,
                    reviewer_agent,
                    prompt,
                    created_at=PACKET_AT,
                )
                packet_path = (
                    output_root
                    / "stage1-packets"
                    / case_slug
                    / f"{participant_id.removeprefix('actor:')}.json"
                )
                write_normalized_json_once(packet_path, packet)
                packet_refs.append(
                    {
                        "case_id": case_id,
                        "relative_path": packet_path.relative_to(output_root).as_posix(),
                        "packet_digest": packet["packet_digest"],
                        "workspace_manifest_digest": preparations[case_id][
                            "workspace_manifest_digest"
                        ],
                    }
                )
            calls.append(
                {
                    "call_identity_id": str(
                        uuid5(
                            NAMESPACE_URL,
                            f"sc-referee-first-envelope-stage1-v1:{participant_id}",
                        )
                    ),
                    "participant_id": participant_id,
                    "participant_configuration_digest": participant["configuration_digest"],
                    "participant": {
                        key: participant[key]
                        for key in (
                            "provider",
                            "agent_surface",
                            "agent_version",
                            "model_name",
                            "model_id",
                            "reasoning_configuration",
                            "execution_context_id",
                            "system_prompt_digest",
                            "tool_policy_digest",
                            "environment_digest",
                        )
                    },
                    "reviewer_agent_base": reviewer_agent,
                    "case_order": case_order,
                    "shared_transcript_expected": True,
                    "cross_case_comparison_permitted": False,
                    "prompt": prompt,
                    "prompt_digest": sha256_digest(prompt),
                    "output_schema": schema,
                    "output_schema_digest": semantic_digest(schema),
                    "packet_refs": packet_refs,
                    "capture_destinations": [
                        f"stage1-captures/{case_id.removeprefix('case:')}/{participant_id.removeprefix('actor:')}"
                        for case_id in case_order
                    ],
                    "interaction_profile": (
                        {
                            "surface": "Claude Desktop App Home Chat",
                            "incognito": True,
                            "fresh_chat": True,
                            "model_label": "Opus 5",
                            "effort_label": "Extra",
                            "tools_or_connectors": "none",
                        }
                        if participant["provider"] == "Anthropic"
                        else {
                            "surface": "Codex CLI exec",
                            "ephemeral": True,
                            "fresh_empty_workspace": True,
                            "sandbox": "read-only",
                            "external_network": False,
                            "model_id": participant["model_id"],
                            "reasoning_effort": participant["reasoning_configuration"],
                        }
                    ),
                }
            )

        protocol: dict[str, Any] = {
            "artifact_kind": "direct_qualification_three_case_stage1_review_protocol",
            "protocol_version": "1.0.0",
            "protocol_id": "scientific-review:complete-domain-exposure-denominator-pilot-stage1-v1",
            "source_commit": SOURCE_COMMIT,
            "source_commit_scope": "admitted_cohort_parent; review-controller files are separately content-bound",
            "controller_implementation": [
                {
                    "path": path_value,
                    "content_digest": sha256_digest((project_root / path_value).read_bytes()),
                }
                for path_value in (
                    "evaluation/src/sc_referee_evaluation/review_semantic_payload.py",
                    "evaluation/src/sc_referee_evaluation/review_protocol.py",
                    "evaluation/src/sc_referee_evaluation/capture.py",
                    "evaluation/src/sc_referee_evaluation/workspace.py",
                    "scripts/build_first_direct_three_case_stage1_protocol.py",
                    "reference/schemas-v0.18.0/schemas/v0.18.0/agent-review.schema.json",
                )
            ],
            "v4_authoring_ledger_digest": V4_AUTHORING_LEDGER_DIGEST,
            "participant_enrollment_digest": PARTICIPANT_ENROLLMENT_DIGEST,
            "active_reviewer_calibration_ledger_digest": ACTIVE_CALIBRATION_LEDGER_DIGEST,
            "base_stage1_prompt_digest": BASE_STAGE1_PROMPT_DIGEST,
            "canonical_issue_class_scope": CANONICAL_ISSUE_CLASS,
            "case_ids": CASE_IDS,
            "case_preparations": [
                {
                    "case_id": case_id,
                    "relative_path": (
                        f"case-preparations/{case_id.removeprefix('case:')}/case-preparation.json"
                    ),
                    "preparation_digest": preparations[case_id]["preparation_digest"],
                    "workspace_manifest_digest": preparations[case_id]["workspace_manifest_digest"],
                }
                for case_id in CASE_IDS
            ],
            "review_design": {
                "reviews_per_case": 4,
                "providers_per_case": 2,
                "reviews_per_provider_per_case": 2,
                "external_call_count": 4,
                "cases_per_call": 3,
                "batching_prospectively_declared": True,
                "case_order_frozen_per_reviewer": True,
                "one_agent_review_per_case_per_reviewer": True,
                "one_packet_and_capture_per_agent_review": True,
                "shared_transcript_within_reviewer_batch": True,
                "detector_output_visible": False,
                "answer_side_evidence_visible": False,
                "other_reviews_visible": False,
                "project_code_execution_permitted": False,
            },
            "calls": calls,
            "failure_policy": {
                "attempts_retained_without_replacement": True,
                "invalid_or_incomplete_batch_admits_no_reviews_from_that_call": True,
                "retry_requires_prospective_protocol_amendment_and_fresh_context": True,
                "semantic_content_may_not_be_controller_repaired": True,
            },
            "limitations": [
                "The four enrolled reviewers are independent within each case, but each reviewer sees all three opaque cases in one transport batch.",
                "Cross-case visibility can induce correlated judgments even though comparison and role inference are forbidden.",
                "Capture establishes exact bytes and packet consistency, not cryptographic provider authentication.",
                "The bounded leakage scanner does not detect paraphrases or undisclosed answer-side content.",
                "Agent-only scientific review is not human scientific adjudication.",
            ],
            "execution_state": "frozen_not_started",
            "stage1_review_count": 0,
            "stage1_freeze_count": 0,
            "stage2_review_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_stage1_protocol_only",
        }
        protocol["protocol_digest"] = semantic_digest(protocol)
        write_normalized_json_once(output_root / "STAGE1_REVIEW_PROTOCOL.json", protocol)
        return protocol
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    protocol = build_first_direct_three_case_stage1_protocol(arguments.project_root.resolve())
    print(protocol["protocol_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
