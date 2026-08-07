from __future__ import annotations

import argparse
import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee_evaluation.review_protocol import build_stage2_review_packet
from sc_referee_evaluation.review_semantic_payload_stage2 import (
    build_stage2_batch_output_schema,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.normalization import write_normalized_json_once
from scripts.build_first_direct_stage2_cross_model_calibration import (
    STAGE2_CROSS_MODEL_RELATIVE as V10_CALIBRATION_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_protocol import (
    CANONICAL_ISSUE_CLASS,
    CASE_IDS,
    LANE_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol import (
    REVIEW_RELATIVE as STAGE1_REVIEW_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_protocol import (
    _participant_agent,
)

STAGE2_REVIEW_RELATIVE = LANE_RELATIVE / "pilot-stage2-cross-model-three-case-v2"
STAGE2_V1_RELATIVE = LANE_RELATIVE / "pilot-stage2-cross-model-three-case"
STAGE2_V1_PROTOCOL_DIGEST = (
    "sha256:21d95e3964326ff211445be2d27324588482e343ddda22dc55f56ce5a5547eb2"
)
STAGE2_V1_CAPTURE_DIGESTS = {
    "actor:stage2-cross-model-fable-01": (
        "sha256:8c3c2dd551d311ab2a94fa0824c603dcc7fa9e8256455cb00c0d369da1a6cd3b"
    ),
    "actor:stage2-cross-model-opus-01": (
        "sha256:a890b2bafdbeddd1af6dc819f6a2c793c853158c36f61805ce8a3242836a8714"
    ),
}
AUTHORING_RELATIVE = LANE_RELATIVE / "pilot-authoring-v4-three-case"
ADR_REFERENCE = "ADR-0066-CROSS-MODEL-SINGLE-PROVIDER-REVIEW-PANEL.md"
PANEL_LEDGER_DIGEST = "sha256:b5a8a566bb8c4430d087e13833cab113639b3418788c65983fb91ad5a8e7d3c9"
V10_ENROLLMENT_DIGEST = "sha256:3db930440af064ba2b774ab3d58d4c63cfb0edcf43fe8a6592d38379096bdb28"
V10_LEDGER_DIGEST = "sha256:2d92ab079af0e5d93964dbced0e7060797b6a5fc6bde018bcb9d22c16188f938"
PACKET_AT = "2026-08-07T19:33:30Z"
FROZEN_AT = "2026-08-07T19:33:31Z"
PROMPT_SCHEMA_MARKER = "\n\nReturn only one unfenced JSON object matching this exact schema:\n"

STAGE2_REVIEWERS = (
    "actor:stage2-cross-model-fable-01",
    "actor:stage2-cross-model-opus-01",
)
CASE_ORDER_BY_REVIEWER = {
    "actor:stage2-cross-model-fable-01": [
        "case:b036fd64c647dfd93e35",
        "case:35069763f06891dba5a3",
        "case:2e26bf5ece15be03717f",
    ],
    "actor:stage2-cross-model-opus-01": [
        "case:35069763f06891dba5a3",
        "case:2e26bf5ece15be03717f",
        "case:b036fd64c647dfd93e35",
    ],
}

_INSTRUCTIONS = """You are one independent Stage-2 scientific adjudicator for exactly three
opaque analysis workflows. A frozen Stage-1 panel of four blind reviewers has already reviewed
each workflow; you now see their frozen conclusions plus the author-side selected-result
declaration for each workflow, which Stage-1 did not see. You have not seen and must not guess
any detector output. Do not compare the workflows to each other or infer their roles; judge each
independently on its own evidence.

For each workflow, decide within this exact scope only: {issue_class}. That scope asks whether
the workflow's selected report claims a complete-domain quantity while its computation
demonstrably uses only a retained subset of the domain. Apply these verdicts exactly:
demonstrated_issue only when the in-scope issue is directly entailed by the visible files;
no_demonstrated_issue_within_scope when the visible files show the in-scope issue is absent;
conditional_or_unknown when an unresolved premise could change the answer;
insufficient_evidence when the visible files cannot support any of the above.

Rules for your output fields. Every evidence and counterevidence atom must quote complete,
exactly transcribed line ranges from the visible files. Attempt to falsify your own verdict and
report it in the structured falsification_attempt object: state the strongest innocent
explanation you could construct, the premises that would reverse your verdict if true, whether
that attempt reversed or survived (outcome), and whether you materially dissent from the frozen
Stage-1 conclusions (material_dissent). unresolved_material_questions has one narrow operational meaning: include
only unanswered questions whose resolution could reverse your in-scope verdict; an eligible
verdict requires this array to be empty; a genuinely reversing open question requires a
conditional or insufficient-evidence verdict instead. For a demonstrated_issue verdict you must
also list, in reconciled_stage1_candidate_ids, the candidate_root_cause_id of every frozen
Stage-1 review whose demonstrated issue is the same underlying issue you found, citing only
candidate ids shown in the frozen Stage-1 material, and supply at least one equivalence atom
quoting the exact file lines that show those candidates and your finding are the same underlying
issue. For any other verdict, both reconciled_stage1_candidate_ids and equivalence_atoms must be
empty."""


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def _panel_inputs(
    project_root: Path,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    root = project_root / STAGE1_REVIEW_RELATIVE
    panel = _load(root / "STAGE1_PANEL_LEDGER.json")
    _replay(panel, "ledger_digest", PANEL_LEDGER_DIGEST, "The Stage-1 panel ledger")
    freezes: dict[str, dict[str, Any]] = {}
    reviews: dict[str, list[dict[str, Any]]] = {case_id: [] for case_id in CASE_IDS}
    for entry in panel["case_panels"]:
        case_id = str(entry["case_id"])
        frozen = _load(root / str(entry["freeze_relative_path"]))
        supplied = dict(frozen)
        digest = supplied.pop("freeze_digest", None)
        if digest != entry["freeze_digest"] or digest != semantic_digest(supplied):
            raise ValueError(f"The Stage-1 freeze for {case_id} does not replay.")
        freezes[case_id] = frozen
    for ledger_ref in panel["call_ledgers"]:
        participant_id = str(ledger_ref["participant_id"])
        call_ledger = _load(
            root / "stage1-call-ledgers" / f"{participant_id.removeprefix('actor:')}.json"
        )
        supplied_ledger = dict(call_ledger)
        ledger_digest = supplied_ledger.pop("ledger_digest", None)
        if ledger_digest != ledger_ref["ledger_digest"] or ledger_digest != semantic_digest(
            supplied_ledger
        ):
            raise ValueError(f"The Stage-1 call ledger for {participant_id} does not replay.")
        for entry in call_ledger["entries"]:
            case_id = str(entry["case_id"])
            review = _load(root / str(entry["relative_capture_path"]) / "review.json")
            if semantic_digest(review) != entry["review_digest"]:
                raise ValueError(f"A Stage-1 review drifted for {participant_id} {case_id}.")
            reviews[case_id].append(review)
    if any(len(items) != 4 for items in reviews.values()):
        raise ValueError("The Stage-1 panel does not supply exactly four reviews per case.")
    return panel, freezes, reviews


def _stage2_participants(project_root: Path) -> dict[str, dict[str, Any]]:
    root = project_root / V10_CALIBRATION_RELATIVE
    enrollment = _load(root / "PARTICIPANT_ENROLLMENT.json")
    supplied = enrollment.pop("enrollment_digest", None)
    if supplied != semantic_digest(enrollment):
        raise ValueError("The v10 Stage-2 enrollment does not replay.")
    enrollment["enrollment_digest"] = supplied
    ledger = _load(root / "CALIBRATION_LEDGER.json")
    _replay(ledger, "ledger_digest", V10_LEDGER_DIGEST, "The v10 calibration ledger")
    if ledger["summary"]["all_reviewer_configurations_passed"] is not True:
        raise ValueError("The Stage-2 reviewer configurations are not all calibrated.")
    participants = {str(item["participant_id"]): item for item in enrollment["participants"]}
    if set(participants) != set(STAGE2_REVIEWERS):
        raise ValueError("The v10 enrollment does not contain the exact Stage-2 pair.")
    for participant in participants.values():
        supplied_config = participant.pop("configuration_digest", None)
        if supplied_config != semantic_digest(participant):
            raise ValueError("A Stage-2 configuration does not replay.")
        participant["configuration_digest"] = supplied_config
    return participants


def _answer_side(project_root: Path, case_id: str) -> tuple[dict[str, Any], list[dict[str, str]]]:
    slug = case_id.removeprefix("case:")
    declaration = _load(project_root / AUTHORING_RELATIVE / "author-declarations" / f"{slug}.json")
    validation = _load(
        project_root / AUTHORING_RELATIVE / "selected-result-validations" / f"{slug}.json"
    )
    refs = [
        {
            "record_type": "author_selected_result_declaration",
            "record_id": str(declaration["declaration_digest"]),
        },
        {
            "record_type": "selected_result_validation",
            "record_id": str(validation["validation_digest"]),
        },
    ]
    summary = {
        "author_declaration_state": declaration["declaration_state"],
        "author_selected_result_binding": deepcopy(declaration["selected_result_binding"]),
        "independent_validation_status": validation["independent_derivation"],
        "independent_validation_digest": validation["validation_digest"],
    }
    return summary, refs


def _case_files(project_root: Path, protocol: dict[str, Any], case_id: str) -> dict[str, str]:
    binding = next(item for item in protocol["source_case_bindings"] if item["case_id"] == case_id)
    workspace_root = project_root / str(binding["source_workspace_relative_path"])
    files: dict[str, str] = {}
    for path_value, digest in sorted(dict(binding["visible_content_digests"]).items()):
        content = (workspace_root / path_value).read_bytes()
        if sha256_digest(content) != digest:
            raise ValueError(f"Workspace bytes drifted for {case_id} {path_value}.")
        files[path_value] = content.decode("utf-8")
    return files


def _stage1_projection_for_prompt(packet: dict[str, Any]) -> list[dict[str, Any]]:
    compact = []
    for item in packet["frozen_stage1_reviews"]:
        identity = item.get("root_cause_identity")
        compact.append(
            {
                "review_id": item["review_ref"]["record_id"],
                "verdict": item["verdict"],
                "bounded_statement": item.get("bounded_statement"),
                "root_cause": item.get("root_cause"),
                "issue_class": item.get("issue_class"),
                "candidate_root_cause_id": (
                    identity.get("candidate_root_cause_id") if isinstance(identity, dict) else None
                ),
                "unresolved_material_questions": item.get("unresolved_material_questions", []),
            }
        )
    return compact


def _retire_v1(project_root: Path) -> None:
    """Retain the executed v1 Stage-2 iteration as a failed attempt before v2 freezes."""

    root = project_root / STAGE2_V1_RELATIVE
    ledger_path = root / "STAGE2_V1_FAILURE_LEDGER.json"
    if ledger_path.exists() or ledger_path.is_symlink():
        return
    if (root / "stage2-call-ledgers").exists():
        raise ValueError("A v1 Stage-2 review was admitted; the iteration cannot be retired.")
    entries = []
    for participant_id, expected in sorted(STAGE2_V1_CAPTURE_DIGESTS.items()):
        slug = participant_id.removeprefix("actor:")
        capture = _load(root / "incoming" / f"{slug}.json")
        supplied = capture.pop("capture_digest", None)
        if supplied != expected or supplied != semantic_digest(capture):
            raise ValueError(f"The v1 Stage-2 capture drifted for {participant_id}.")
        entries.append(
            {
                "participant_id": participant_id,
                "incoming_capture_digest": supplied,
                "raw_response_digest": capture["raw_response_digest"],
                "failure_reason": (
                    "controller_compact_payload_schema_missing_required_stage2_record_fields"
                ),
                "admitted_review_count": 0,
            }
        )
    ledger = {
        "artifact_kind": "direct_qualification_stage2_cross_model_v1_failure_ledger",
        "ledger_version": "1.0.0",
        "v1_protocol_digest": STAGE2_V1_PROTOCOL_DIGEST,
        "root_cause": (
            "The v1 compact Stage-2 payload schema omitted semantic fields the public "
            "AgentReview schema requires for stage2_scientific_adjudication (a structured "
            "falsification attempt with outcome and material dissent, at least two reconciled "
            "Stage-1 candidates, and nonempty equivalence evidence), so no v1 response could "
            "be projected into an admissible review. Both one-shot responses are retained "
            "and permanently ineligible; no review, label, or detector outcome was created."
        ),
        "entries": entries,
        "attempt_count": 2,
        "admitted_review_count": 0,
        "responses_retained_without_repair": True,
        "v1_responses_permanently_ineligible": True,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "recorded_at": FROZEN_AT,
        "qualification_authority": "none_failure_evidence_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    write_normalized_json_once(ledger_path, ledger)


def build_first_direct_stage2_cross_model_protocol(project_root: Path) -> dict[str, Any]:
    output_root = project_root / STAGE2_REVIEW_RELATIVE
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"Stage-2 protocol output already exists: {output_root}")
    _retire_v1(project_root)
    panel, freezes, reviews_by_case = _panel_inputs(project_root)
    participants = _stage2_participants(project_root)
    from scripts.record_first_direct_three_case_stage1_semantic_recovery_clean_cli import (
        _protocol as _stage1_protocol,
    )

    stage1_protocol = _stage1_protocol(project_root)

    output_root.mkdir(parents=True)
    try:
        calls: list[dict[str, Any]] = []
        for participant_id in STAGE2_REVIEWERS:
            participant = participants[participant_id]
            reviewer_agent = _participant_agent(participant)
            case_order = CASE_ORDER_BY_REVIEWER[participant_id]
            output_schema = build_stage2_batch_output_schema(
                participant_id, case_order, CANONICAL_ISSUE_CLASS
            )

            sections: list[str] = []
            answer_refs_by_case: dict[str, list[dict[str, str]]] = {}
            packet_payloads: list[tuple[str, dict[str, Any]]] = []
            for index, case_id in enumerate(case_order, start=1):
                files = _case_files(project_root, stage1_protocol, case_id)
                answer_summary, answer_refs = _answer_side(project_root, case_id)
                answer_refs_by_case[case_id] = answer_refs
                file_sections = "\n".join(
                    f"--- file {path} ---\n{text}" for path, text in files.items()
                )
                sections.append(
                    f"=== workflow {index}: {case_id} ===\n"
                    f"{file_sections}\n"
                    f"--- frozen Stage-1 panel for {case_id} (JSON) ---\n"
                    "STAGE1_PANEL_PLACEHOLDER_" + case_id + "\n"
                    f"--- author-side selected-result declaration for {case_id} (JSON) ---\n"
                    + json.dumps(answer_summary, sort_keys=True, ensure_ascii=False)
                )
            prompt_body = (
                _INSTRUCTIONS.format(issue_class=CANONICAL_ISSUE_CLASS)
                + f"\n\nReviewer participant identity: {participant_id}\n\n"
                + "\n\n".join(sections)
            )

            packet_refs: list[dict[str, Any]] = []
            built_packets: dict[str, dict[str, Any]] = {}
            # Two passes: packets bind the exact final prompt, and the prompt embeds
            # the Stage-1 projection that the packet itself carries. Build the
            # projections first from a provisional packet, splice them into the
            # prompt, then build the exact final packets against that prompt.
            provisional = {
                case_id: build_stage2_review_packet(
                    freezes[case_id],
                    reviews_by_case[case_id],
                    reviewer_agent,
                    "provisional",
                    created_at=PACKET_AT,
                    answer_side_evidence_refs=answer_refs_by_case[case_id],
                    reference_analysis_refs=[],
                    execution_comparison_refs=[],
                )
                for case_id in case_order
            }
            for case_id in case_order:
                projection = _stage1_projection_for_prompt(provisional[case_id])
                prompt_body = prompt_body.replace(
                    "STAGE1_PANEL_PLACEHOLDER_" + case_id,
                    json.dumps(projection, sort_keys=True, ensure_ascii=False),
                )
            prompt = (
                prompt_body
                + PROMPT_SCHEMA_MARKER
                + json.dumps(output_schema, sort_keys=True, ensure_ascii=False)
            ).strip()

            for case_id in case_order:
                packet = build_stage2_review_packet(
                    freezes[case_id],
                    reviews_by_case[case_id],
                    reviewer_agent,
                    prompt,
                    created_at=PACKET_AT,
                    answer_side_evidence_refs=answer_refs_by_case[case_id],
                    reference_analysis_refs=[],
                    execution_comparison_refs=[],
                )
                packet_path = (
                    output_root
                    / "stage2-packets"
                    / case_id.removeprefix("case:")
                    / f"{participant_id.removeprefix('actor:')}.json"
                )
                write_normalized_json_once(packet_path, packet)
                built_packets[case_id] = packet
                packet_refs.append(
                    {
                        "case_id": case_id,
                        "relative_path": packet_path.relative_to(output_root).as_posix(),
                        "packet_digest": packet["packet_digest"],
                        "stage1_freeze_digest": packet["stage1_freeze_digest"],
                    }
                )

            command_profile = {
                "provider_cli": "claude",
                "print_mode": True,
                "safe_mode": True,
                "tool_set": "empty",
                "mcp_set": "empty_mcpServers_record_strict",
                "permission_mode": "dontAsk",
                "session_persistence": False,
                "session_id_binding": "call_identity_id",
                "structured_output": "prompt_embedded_schema_local_fail_closed_validation",
                "json_schema_argument_present": False,
                "model_alias_argument": (
                    "fable" if participant["model_id"] == "claude-fable-5" else "claude-opus-5"
                ),
                "model_usage_post_verification_required": True,
            }
            calls.append(
                {
                    "call_identity_id": str(
                        uuid5(
                            NAMESPACE_URL,
                            "sc-referee-first-envelope-stage2-cross-model-v2:" + participant_id,
                        )
                    ),
                    "participant_id": participant_id,
                    "participant_configuration_digest": participant["configuration_digest"],
                    "calibration_ledger_digest": V10_LEDGER_DIGEST,
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
                    "output_schema": output_schema,
                    "output_schema_digest": semantic_digest(output_schema),
                    "packet_refs": packet_refs,
                    "capture_destinations": [
                        "stage2-captures/"
                        + case_id.removeprefix("case:")
                        + "/"
                        + participant_id.removeprefix("actor:")
                        for case_id in case_order
                    ],
                    "command_profile": command_profile,
                }
            )

        protocol: dict[str, Any] = {
            "artifact_kind": "direct_qualification_three_case_stage2_cross_model_protocol",
            "protocol_version": "2.0.0",
            "protocol_id": (
                "scientific-review:complete-domain-exposure-denominator-pilot-stage2-cross-model-v2"
            ),
            "adr_reference": ADR_REFERENCE,
            "stage1_panel_ledger_digest": PANEL_LEDGER_DIGEST,
            "stage1_protocol_digest": stage1_protocol["protocol_digest"],
            "v10_stage2_enrollment_digest": V10_ENROLLMENT_DIGEST,
            "v10_stage2_calibration_ledger_digest": V10_LEDGER_DIGEST,
            "canonical_issue_class_scope": CANONICAL_ISSUE_CLASS,
            "case_ids": CASE_IDS,
            "review_design": {
                "reviews_per_case": 2,
                "model_families_per_case": 2,
                "provider_families_per_case": 1,
                "single_provider_cross_model_disclosure": True,
                "answer_side_evidence_visible": True,
                "frozen_stage1_reviews_visible": True,
                "detector_output_visible": False,
                "cases_per_call": 3,
                "external_call_count": 2,
                "batching_prospectively_declared": True,
                "identities_disjoint_from_authors_and_stage1_reviewers": True,
                "eligible_verdict_requires_empty_unresolved_material_questions": True,
            },
            "calls": calls,
            "execution_state": "frozen_not_started",
            "stage2_review_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "frozen_at": FROZEN_AT,
            "qualification_authority": "none_stage2_protocol_only",
        }
        protocol["protocol_digest"] = semantic_digest(protocol)
        write_normalized_json_once(output_root / "STAGE2_REVIEW_PROTOCOL.json", protocol)
        return protocol
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    protocol = build_first_direct_stage2_cross_model_protocol(arguments.project_root.resolve())
    print(protocol["protocol_digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
