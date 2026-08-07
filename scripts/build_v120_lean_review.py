from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee_evaluation.review_protocol import build_stage1_review_packet
from sc_referee_evaluation.review_semantic_payload_v2 import (
    build_stage1_batch_output_schema_v2,
)
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
from scripts.build_first_direct_three_case_stage1_protocol import (
    CANONICAL_ISSUE_CLASS,
    VISIBLE_FILES,
    _participant_agent,
)
from scripts.build_v120_lean_pilot_authoring import V120_AUTHORING_RELATIVE
from scripts.build_v120_lean_pilot_authoring import (
    V120_AUTHORING_RELATIVE as AUTHORING_RELATIVE,
)
from scripts.build_v120_lean_reviewer_calibration import (
    V120_REVIEWER_RELATIVE as V12_CALIBRATION_RELATIVE,
)
from scripts.record_v120_lean_pilot_authors import PROTOCOL_DIGEST as AUTHORING_PROTOCOL_DIGEST

V120_REVIEW_RELATIVE = V120_AUTHORING_RELATIVE.parent / "pilot-v120-lean-review-three-case"
ADR_0066 = "ADR-0066-CROSS-MODEL-SINGLE-PROVIDER-REVIEW-PANEL.md"
ADR_0067 = "ADR-0067-LEAN-SINGLE-REVIEW-QUALIFICATION-PROTOCOL.md"
AUTHORING_LEDGER_DIGEST = "sha256:c6c2b109248982bad35efa80492f5e82f75a7bfbc3c937d5675e3bc346366b04"
V12_LEDGER_DIGEST = "sha256:93643034def0ae421c3faafd8419c61e4b087f3039820e30b6f59d97f3e2639e"
PRIMARY_REVIEWER = "actor:v120-reviewer-fable-01"
ESCALATION_REVIEWER = "actor:v120-reviewer-opus-01"
SNAPSHOT_AT = "2026-08-07T21:20:00Z"
WORKSPACE_AT = "2026-08-07T21:20:30Z"
PACKET_AT = "2026-08-07T21:21:00Z"
FROZEN_AT = "2026-08-07T21:21:01Z"
PROMPT_SCHEMA_MARKER = "\n\nReturn only one unfenced JSON object matching this exact schema:\n"

TASK_BY_ROLE = {
    "error_bearing": (
        "Report one occurrence rate whose scientific target is the complete planned set of "
        "observation units, using the planned-unit accounting supplied with this workflow."
    ),
    "corrected_twin": (
        "Report one occurrence rate whose scientific target is the complete planned set of "
        "observation units, using the planned-unit accounting supplied with this workflow."
    ),
    "valid_alternative": (
        "Report one occurrence rate whose scientific target is the prespecified eligible "
        "subset of observation units, with every claim explicitly confined to that subset."
    ),
}

_INSTRUCTIONS = """You are one independent blind scientific reviewer for exactly three opaque
analysis workflows. You have not seen and must not guess any answer key, case role, other
review, or detector output. Do not compare the workflows to each other or infer their roles;
judge each independently on its own visible files, which include the scientist's task statement.

For each workflow, decide within this exact scope only: {issue_class}. That scope asks whether
the workflow's selected report claims a quantity for its complete declared target domain while
its computation demonstrably uses only a retained subset of that domain. Apply these verdicts
exactly: demonstrated_issue only when the in-scope issue is directly entailed by the visible
files; no_demonstrated_issue_within_scope when the visible files show the in-scope issue is
absent; conditional_or_unknown when an unresolved premise could change the answer;
insufficient_evidence when the visible files cannot support any of the above.

Every evidence and counterevidence atom must quote complete, exactly transcribed line ranges
from the visible files. Attempt to falsify your own verdict and report that attempt in the
falsification_attempt string. unresolved_material_questions has one narrow operational meaning:
include only unanswered questions whose resolution could reverse your in-scope verdict; an
eligible verdict requires this array to be empty; a genuinely reversing open question requires a
conditional or insufficient-evidence verdict instead."""


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


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
        ".answer-side/opus-author-capture.json": authoring_root
        / "incoming"
        / "v120-author-opus-01.json",
        ".answer-side/fable-author-capture.json": authoring_root
        / "incoming"
        / "v120-author-fable-01.json",
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
    contract: dict[str, Any],
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
        f"v120-lean-review:{case_id}",
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

    answer_markers = {
        str(contract["canonical_issue_class"]),
        str(contract["envelope"]["binding_digest"]),
        str(contract["envelope"]["candidate_id"]),
        str(contract["envelope"]["check_id"]),
        str(contract["envelope"]["envelope_id"]),
        str(contract["contract_digest"]),
        "error-bearing",
        "error_bearing",
        "corrected-twin",
        "corrected_twin",
        "valid-alternative",
        "valid_alternative",
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
    return {
        "case_id": case_id,
        "workspace_manifest": workspace_manifest,
        "workspace_relative_path": (
            (preparation_root / "workspace").relative_to(project_root).as_posix()
        ),
        "workspace_manifest_relative_path": (
            (preparation_root / "workspace-manifest.json").relative_to(project_root).as_posix()
        ),
        "visible_content_digests": visible_digests,
        "scientific_task_digest": sha256_digest(task_payload),
    }


def build_v120_lean_review(project_root: Path) -> dict[str, Any]:
    output_root = project_root / V120_REVIEW_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"V120 review output already exists: {output_root}")
    authoring_root = project_root / AUTHORING_RELATIVE
    ledger = _load(authoring_root / "AUTHORING_LEDGER.json")
    _replay(ledger, "ledger_digest", AUTHORING_LEDGER_DIGEST, "The v120 authoring ledger")
    protocol = _load(authoring_root / "PILOT_AUTHORING_PROTOCOL.json")
    _replay(protocol, "protocol_digest", AUTHORING_PROTOCOL_DIGEST, "The v120 authoring protocol")
    role_by_case = {
        str(case_id): str(role) for case_id, role in protocol["case_role_assignments"].items()
    }
    case_ids = sorted(role_by_case)

    calibration_root = project_root / V12_CALIBRATION_RELATIVE
    enrollment = _load(calibration_root / "PARTICIPANT_ENROLLMENT.json")
    supplied = enrollment.pop("enrollment_digest", None)
    if supplied != semantic_digest(enrollment):
        raise ValueError("The v12 reviewer enrollment does not replay.")
    enrollment["enrollment_digest"] = supplied
    calibration_ledger = _load(calibration_root / "CALIBRATION_LEDGER.json")
    _replay(calibration_ledger, "ledger_digest", V12_LEDGER_DIGEST, "The v12 calibration ledger")
    if calibration_ledger["summary"]["all_reviewer_configurations_passed"] is not True:
        raise ValueError("The v120 reviewer configurations are not all calibrated.")
    participants = {str(item["participant_id"]): item for item in enrollment["participants"]}
    primary = participants[PRIMARY_REVIEWER]
    entries = {str(item["participant_id"]): item for item in calibration_ledger["entries"]}

    author_ids = {
        str(item["participant"]["participant_id"]) for item in protocol["author_assignments"]
    }
    if {PRIMARY_REVIEWER, ESCALATION_REVIEWER} & author_ids:
        raise ValueError("A v120 reviewer identity overlaps an author identity.")

    output_root.mkdir(parents=True)
    try:
        preparations: dict[str, dict[str, Any]] = {}
        for case_id in case_ids:
            contract = _load(
                authoring_root / "case-contracts" / f"{case_id.removeprefix('case:')}.json"
            )
            preparations[case_id] = _prepare_case(
                project_root,
                output_root,
                case_id,
                TASK_BY_ROLE[role_by_case[case_id]],
                contract,
            )

        reviewer_agent = _participant_agent(primary)
        case_order = case_ids
        output_schema = build_stage1_batch_output_schema_v2(
            PRIMARY_REVIEWER, case_order, CANONICAL_ISSUE_CLASS
        )
        sections: list[str] = []
        for index, case_id in enumerate(case_order, start=1):
            preparation = preparations[case_id]
            workspace_root = project_root / str(preparation["workspace_relative_path"])
            file_sections = "\n".join(
                f"--- file {item['path']} ---\n"
                + (workspace_root / str(item["path"])).read_text(encoding="utf-8")
                for item in VISIBLE_FILES
            )
            sections.append(f"=== workflow {index}: {case_id} ===\n{file_sections}")
        prompt = (
            _INSTRUCTIONS.format(issue_class=CANONICAL_ISSUE_CLASS)
            + f"\n\nReviewer participant identity: {PRIMARY_REVIEWER}\n\n"
            + "\n\n".join(sections)
            + PROMPT_SCHEMA_MARKER
            + json.dumps(output_schema, sort_keys=True, ensure_ascii=False)
        ).strip()

        packet_refs: list[dict[str, Any]] = []
        for case_id in case_order:
            packet = build_stage1_review_packet(
                case_id,
                preparations[case_id]["workspace_manifest"],
                reviewer_agent,
                prompt,
                created_at=PACKET_AT,
            )
            packet_path = (
                output_root
                / "stage1-packets"
                / case_id.removeprefix("case:")
                / f"{PRIMARY_REVIEWER.removeprefix('actor:')}.json"
            )
            write_normalized_json_once(packet_path, packet)
            packet_refs.append(
                {
                    "case_id": case_id,
                    "relative_path": packet_path.relative_to(output_root).as_posix(),
                    "packet_digest": packet["packet_digest"],
                    "source_workspace_manifest_digest": preparations[case_id]["workspace_manifest"][
                        "manifest_digest"
                    ],
                }
            )

        review_protocol: dict[str, Any] = {
            "artifact_kind": "direct_qualification_v120_lean_review_protocol",
            "protocol_version": "1.0.0",
            "adr_references": [ADR_0066, ADR_0067],
            "authoring_protocol_digest": AUTHORING_PROTOCOL_DIGEST,
            "authoring_ledger_digest": AUTHORING_LEDGER_DIGEST,
            "v12_calibration_ledger_digest": V12_LEDGER_DIGEST,
            "canonical_issue_class_scope": CANONICAL_ISSUE_CLASS,
            "case_ids": case_ids,
            "source_case_bindings": [
                {
                    "case_id": case_id,
                    "source_workspace_relative_path": preparations[case_id][
                        "workspace_relative_path"
                    ],
                    "source_workspace_manifest_relative_path": preparations[case_id][
                        "workspace_manifest_relative_path"
                    ],
                    "source_workspace_manifest_digest": preparations[case_id]["workspace_manifest"][
                        "manifest_digest"
                    ],
                    "visible_content_digests": preparations[case_id]["visible_content_digests"],
                    "scientific_task_digest": preparations[case_id]["scientific_task_digest"],
                    "workspace_bytes_reused_without_copy": True,
                }
                for case_id in case_ids
            ],
            "review_design": {
                "reviews_per_case": 1,
                "single_review_with_escalation": True,
                "escalation_reviewer_id": ESCALATION_REVIEWER,
                "escalation_trigger": (
                    "any non-eligible verdict, nonempty unresolved material questions, "
                    "admission failure, or post-unblinding disagreement with the frozen "
                    "case-role expectation"
                ),
                "cases_per_call": 3,
                "external_call_count": 1,
                "batching_prospectively_declared": True,
                "answer_side_evidence_visible": False,
                "detector_output_visible": False,
                "identities_disjoint_from_authors": True,
                "eligible_verdict_requires_empty_unresolved_material_questions": True,
            },
            "calls": [
                {
                    "call_identity_id": str(
                        uuid5(
                            NAMESPACE_URL,
                            "sc-referee:v120-lean-review:" + PRIMARY_REVIEWER,
                        )
                    ),
                    "participant_id": PRIMARY_REVIEWER,
                    "participant_configuration_digest": primary["configuration_digest"],
                    "calibration_ledger_digest": V12_LEDGER_DIGEST,
                    "calibration_entry_digest": semantic_digest(entries[PRIMARY_REVIEWER]),
                    "participant": {
                        key: primary[key]
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
                    "output_schema": output_schema,
                    "output_schema_digest": semantic_digest(output_schema),
                    "packet_refs": packet_refs,
                    "capture_destinations": [
                        "stage1-captures/"
                        + case_id.removeprefix("case:")
                        + "/"
                        + PRIMARY_REVIEWER.removeprefix("actor:")
                        for case_id in case_order
                    ],
                    "command_profile": {
                        "provider_cli": "claude",
                        "print_mode": True,
                        "safe_mode": True,
                        "tool_set": "empty",
                        "mcp_set": "empty_mcpServers_record_strict",
                        "permission_mode": "dontAsk",
                        "session_persistence": False,
                        "session_id_binding": "call_identity_id",
                        "structured_output": (
                            "prompt_embedded_schema_local_fail_closed_validation"
                        ),
                        "json_schema_argument_present": False,
                        "model_alias_argument": "fable",
                        "model_usage_post_verification_required": True,
                    },
                }
            ],
            "execution_state": "frozen_not_started",
            "review_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_lean_review_protocol_only",
        }
        review_protocol["protocol_digest"] = semantic_digest(review_protocol)
        write_normalized_json_once(output_root / "REVIEW_PROTOCOL.json", review_protocol)
        return review_protocol
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    protocol = build_v120_lean_review(arguments.project_root.resolve())
    print(protocol["protocol_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
