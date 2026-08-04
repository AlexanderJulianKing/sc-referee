from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from sc_referee_evaluation.direct_qualification_lane import (
    freeze_authoring_brief_manifest,
    freeze_direct_qualification_lane,
    freeze_participant_enrollment,
)

from sc_referee.core.ids import semantic_digest, sha256_digest

PRECASE_RELATIVE = Path(
    "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-v3-precase/"
    "FREEZE_MANIFEST.json"
)
BASE_LANE_RELATIVE = Path(
    "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane"
)
LANE_RELATIVE = Path(
    "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2"
)
CONFIGURATION_NAME = "EXECUTION_CONFIGURATION.json"
CONFIGURATION_AMENDMENT_NAME = "EXECUTION_CONFIGURATION_AMENDMENT.json"
ASSIGNED_AT = "2026-08-04T23:49:00Z"
FROZEN_AT = "2026-08-04T23:50:00Z"

ENVELOPE_ID = "relation-envelope:complete-domain-exposure-denominator"
CHECK_ID = "check:complete-domain-exposure-denominator"
CANDIDATE_ID = "complete-declared-domain-exposure"
CANONICAL_ISSUE_CLASS = "issue-class:retained-subset-for-complete-domain"
DETECTOR_ID = "detector:bounded-analysis-method-conflict"

PILOT_BLOCK_ID = "block:61b869e41dea194d"
HELDOUT_BLOCK_ID = "block:88d0fdb420461a3f"
STAGE1_IDS = (
    "actor:stage1-claude-01",
    "actor:stage1-claude-02",
    "actor:stage1-codex-01",
    "actor:stage1-codex-02",
)
STAGE2_IDS = ("actor:stage2-claude-01", "actor:stage2-codex-01")

COMMON_SUPPORTED_ARTIFACTS = [
    "One ASCII CSV or TSV input containing the complete planned-unit accounting.",
    "One UTF-8 Python source file with an unconditional module-level literal-path write_text call.",
    "One ASCII-LF Markdown or text report whose bytes equal the statically constructed Python output and contain exactly one [selected-result] line.",
    "A truthful author-only selected-result declaration stored outside the three-file case tree.",
]


def _visible_brief(
    case_id: str,
    task: str,
    inputs: list[str],
    constraints: list[str],
    *,
    artifacts: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "brief_version": "1.0.0",
        "case_id": case_id,
        "scientific_task": task,
        "available_inputs": inputs,
        "required_artifacts": list(artifacts or COMMON_SUPPORTED_ARTIFACTS),
        "construction_constraints": constraints,
    }


def _case_specs() -> list[dict[str, Any]]:
    pilot_error = "case:c5e5a75d42962d2e95a3"
    heldout_error = "case:670f4b5b1a48188a8973"
    return [
        {
            "case_id": pilot_error,
            "brief_id": "brief:cebb3b28354c376a",
            "block_id": PILOT_BLOCK_ID,
            "cell_type": "error_bearing",
            "reference_case_id": None,
            "author_id": "actor:pilot-author-claude-01",
            "visible": _visible_brief(
                pilot_error,
                "Build a compact coastal-station workflow that reports one occurrence rate for the entire scheduled survey network.",
                [
                    "Create a table representing 96 scheduled stations, of which 72 pass the signal screen; record 18 occurrences among the retained stations and account explicitly for every omitted station."
                ],
                [
                    "Declare the scientific target as all 96 scheduled stations.",
                    "Use the 72 post-screening stations as the exposure denominator for the selected occurrence rate.",
                    "Describe the selected rate as applying to the entire scheduled network.",
                    "State that no protocol amendment or approved method deviation exists.",
                ],
            ),
        },
        {
            "case_id": "case:345133226e9fc72a32b0",
            "brief_id": "brief:d8b91cf3b5c7353a",
            "block_id": PILOT_BLOCK_ID,
            "cell_type": "corrected_twin",
            "reference_case_id": pilot_error,
            "author_id": "actor:pilot-author-claude-01",
            "visible": _visible_brief(
                "case:345133226e9fc72a32b0",
                "Using the supplied coastal-station base workflow, produce a revised selected occurrence rate for the entire scheduled survey network.",
                [
                    "The base workflow represents 96 scheduled stations, 72 signal-screen passes, 18 observed occurrences, and complete omitted-station accounting."
                ],
                [
                    "Keep the scientific target as all 96 scheduled stations.",
                    "Use all 96 scheduled stations as the exposure denominator for the selected rate and retain the unavailable-station accounting.",
                    "Limit the report to claims supported by that complete-network denominator.",
                ],
            ),
        },
        {
            "case_id": "case:72678038fd451aac236a",
            "brief_id": "brief:092df31cef604ef8",
            "block_id": PILOT_BLOCK_ID,
            "cell_type": "valid_alternative",
            "reference_case_id": None,
            "author_id": "actor:pilot-author-codex-01",
            "visible": _visible_brief(
                "case:72678038fd451aac236a",
                "Build a coastal-station workflow whose scientific question is the occurrence rate conditional on passing a prespecified signal screen.",
                [
                    "Create a table with 96 scheduled stations, 72 signal-screen passes, 18 occurrences among those passes, and complete accounting for stations outside the eligible set."
                ],
                [
                    "Define the target population explicitly as the 72 signal-eligible stations.",
                    "Use those 72 stations as the selected rate denominator.",
                    "Confine every scientific claim to signal-eligible stations and distinguish that target from the scheduled network.",
                ],
            ),
        },
        {
            "case_id": "case:a5409f5f081836abc336",
            "brief_id": "brief:bca58d5eb0ce1de7",
            "block_id": PILOT_BLOCK_ID,
            "cell_type": "hard_negative",
            "reference_case_id": None,
            "author_id": "actor:pilot-author-claude-02",
            "visible": _visible_brief(
                "case:a5409f5f081836abc336",
                "Build a coastal survey with a full-network scientific occurrence endpoint and a separate screening-completion quality-control endpoint.",
                [
                    "Create a table with 96 scheduled stations, complete network exposure accounting, 18 occurrences, and 72 records that complete signal screening."
                ],
                [
                    "Make the selected scientific result the occurrence rate over all 96 scheduled stations.",
                    "Also report screening completion among inspected records as a clearly secondary quality-control value.",
                    "State explicitly that the quality-control denominator does not define or enter the selected scientific endpoint.",
                ],
            ),
        },
        {
            "case_id": "case:a35ee5ac7a59333fdcc1",
            "brief_id": "brief:ee70355885c122dd",
            "block_id": PILOT_BLOCK_ID,
            "cell_type": "ambiguous",
            "reference_case_id": None,
            "author_id": "actor:pilot-author-codex-02",
            "visible": _visible_brief(
                "case:a35ee5ac7a59333fdcc1",
                "Build a coastal-station workflow governed by two equally authoritative scope records and report one rate from the signal-screened stations.",
                [
                    "Create 96 scheduled stations, 72 signal-screen passes, and 18 occurrences among the passes; include one signed scope record for all scheduled stations and another for signal-eligible stations."
                ],
                [
                    "Give the two scope records equal authority and provide no date, amendment, or precedence rule that resolves them.",
                    "Use 72 signal-screened stations as the selected rate denominator.",
                    "Describe both governing scope records faithfully without selecting one as controlling.",
                ],
            ),
        },
        {
            "case_id": "case:54e6452ec78d35dc72ac",
            "brief_id": "brief:fddc498845b1ca12",
            "block_id": PILOT_BLOCK_ID,
            "cell_type": "unsupported",
            "reference_case_id": None,
            "author_id": "actor:pilot-author-claude-03",
            "visible": _visible_brief(
                "case:54e6452ec78d35dc72ac",
                "Build a coastal-station report producer whose retained report destination is selected from a runtime command-line value.",
                [
                    "Create a station table with full planned and screened counts and one retained report example."
                ],
                [
                    "Compute the output path from a runtime argument rather than a source-code path literal.",
                    "Preserve enough source and report material to show why static inspection cannot establish the selected producer-to-report binding.",
                    "Make a truthful author declaration that identifies the runtime-selected producer surface instead of asserting a single statically bound result.",
                ],
                artifacts=[
                    "One ASCII CSV or TSV input with planned and screened station accounting.",
                    "One UTF-8 Python producer whose output path depends on a runtime command-line value.",
                    "One ASCII-LF retained Markdown or text report example with a [selected-result] line.",
                    "A truthful author-only producer-surface declaration stored outside the three-file case tree.",
                ],
            ),
        },
        {
            "case_id": "case:00e38ff58c6d50621e1c",
            "brief_id": "brief:81bd3ad82ef45933",
            "block_id": PILOT_BLOCK_ID,
            "cell_type": "renamed_implementation",
            "reference_case_id": pilot_error,
            "author_id": "actor:pilot-author-codex-03",
            "visible": _visible_brief(
                "case:00e38ff58c6d50621e1c",
                "Independently build a traffic-sensor workflow that reports one event frequency for the complete scheduled monitoring route.",
                [
                    "Create a TSV representing 120 scheduled time windows, 90 windows retained after device checks, and 30 events in retained windows, with all excluded windows accounted for."
                ],
                [
                    "Declare the target as the complete 120-window route schedule.",
                    "Use the 90 device-check passes as the exposure denominator for the selected frequency and describe it as route-wide.",
                    "Use different filenames, variable names, report layout, and domain vocabulary from any supplied coastal-station material.",
                    "State that no governing amendment or approved deviation exists.",
                ],
            ),
        },
        {
            "case_id": heldout_error,
            "brief_id": "brief:c25c1e5ef38f0142",
            "block_id": HELDOUT_BLOCK_ID,
            "cell_type": "error_bearing",
            "reference_case_id": None,
            "author_id": "actor:sealed-author-codex-04",
            "visible": _visible_brief(
                heldout_error,
                "Build a compact instrument-uptime workflow that reports one failure intensity for the complete commissioned observation calendar.",
                [
                    "Create a table representing 168 commissioned hourly slots, 126 retained after telemetry screening, and 21 failures among retained slots, with every omitted slot accounted for."
                ],
                [
                    "Declare the scientific target as all 168 commissioned slots.",
                    "Use the 126 telemetry-screened slots as the exposure denominator for the selected failure intensity.",
                    "Describe the selected intensity as applying to the complete commissioned calendar.",
                    "State that no protocol amendment or approved method deviation exists.",
                ],
            ),
        },
        {
            "case_id": "case:6d9579fa1e8f9f50db4c",
            "brief_id": "brief:e705a9f6655d0f93",
            "block_id": HELDOUT_BLOCK_ID,
            "cell_type": "corrected_twin",
            "reference_case_id": heldout_error,
            "author_id": "actor:sealed-author-codex-04",
            "visible": _visible_brief(
                "case:6d9579fa1e8f9f50db4c",
                "Using the supplied instrument-uptime base workflow, produce a revised failure intensity for the complete commissioned observation calendar.",
                [
                    "The base workflow represents 168 commissioned slots, 126 telemetry-screen passes, 21 observed failures, and complete omitted-slot accounting."
                ],
                [
                    "Keep the target as all 168 commissioned slots.",
                    "Use all 168 commissioned slots as the exposure denominator and retain unavailable-slot accounting.",
                    "Limit the report to claims supported by that complete-calendar denominator.",
                ],
            ),
        },
        {
            "case_id": "case:87f491b5c0fa3ae7be4a",
            "brief_id": "brief:d312c99bddc6e0e2",
            "block_id": HELDOUT_BLOCK_ID,
            "cell_type": "valid_alternative",
            "reference_case_id": None,
            "author_id": "actor:sealed-author-claude-04",
            "visible": _visible_brief(
                "case:87f491b5c0fa3ae7be4a",
                "Build an instrument workflow whose scientific question is failure intensity conditional on slots with valid telemetry.",
                [
                    "Create 168 commissioned hourly slots, 126 valid-telemetry slots, 21 failures among valid slots, and complete accounting outside that eligible set."
                ],
                [
                    "Define the target explicitly as the 126 valid-telemetry slots.",
                    "Use those 126 slots as the selected intensity denominator.",
                    "Confine every scientific claim to valid-telemetry slots and distinguish that target from the commissioned calendar.",
                ],
            ),
        },
        {
            "case_id": "case:cdc9e2ae44b02c1a85d2",
            "brief_id": "brief:a808bf014045de09",
            "block_id": HELDOUT_BLOCK_ID,
            "cell_type": "hard_negative",
            "reference_case_id": None,
            "author_id": "actor:sealed-author-codex-05",
            "visible": _visible_brief(
                "case:cdc9e2ae44b02c1a85d2",
                "Build an instrument study with a complete-calendar scientific failure endpoint and a separate telemetry-completion quality endpoint.",
                [
                    "Create 168 commissioned slots, complete calendar exposure accounting, 21 failures, and 126 slots that complete telemetry screening."
                ],
                [
                    "Make the selected scientific result the failure intensity over all 168 commissioned slots.",
                    "Also report telemetry completion among inspected slots as a clearly secondary quality value.",
                    "State explicitly that the quality denominator does not define or enter the selected scientific endpoint.",
                ],
            ),
        },
        {
            "case_id": "case:79bba09d589444884c44",
            "brief_id": "brief:e4450b7d81d5ff73",
            "block_id": HELDOUT_BLOCK_ID,
            "cell_type": "ambiguous",
            "reference_case_id": None,
            "author_id": "actor:sealed-author-claude-05",
            "visible": _visible_brief(
                "case:79bba09d589444884c44",
                "Build an instrument workflow governed by two equally authoritative scope records and report one failure intensity from valid-telemetry slots.",
                [
                    "Create 168 commissioned slots, 126 valid-telemetry slots, and 21 failures among valid slots; include one signed scope record for all commissioned slots and another for valid-telemetry slots."
                ],
                [
                    "Give the two scope records equal authority and provide no date, amendment, or precedence rule that resolves them.",
                    "Use 126 valid-telemetry slots as the selected intensity denominator.",
                    "Describe both governing scope records faithfully without selecting one as controlling.",
                ],
            ),
        },
        {
            "case_id": "case:0e8a84e424013c876694",
            "brief_id": "brief:4d3aea8545788d76",
            "block_id": HELDOUT_BLOCK_ID,
            "cell_type": "unsupported",
            "reference_case_id": None,
            "author_id": "actor:sealed-author-codex-06",
            "visible": _visible_brief(
                "case:0e8a84e424013c876694",
                "Build an instrument report producer whose retained report destination is selected from a runtime environment value.",
                [
                    "Create an observation-slot table with complete commissioned and telemetry-screened counts and one retained report example."
                ],
                [
                    "Compute the output path from a runtime environment value rather than a source-code path literal.",
                    "Preserve enough source and report material to show why static inspection cannot establish the selected producer-to-report binding.",
                    "Make a truthful author declaration that identifies the runtime-selected producer surface instead of asserting a single statically bound result.",
                ],
                artifacts=[
                    "One ASCII CSV or TSV input with commissioned and telemetry-screened slot accounting.",
                    "One UTF-8 Python producer whose output path depends on a runtime environment value.",
                    "One ASCII-LF retained Markdown or text report example with a [selected-result] line.",
                    "A truthful author-only producer-surface declaration stored outside the three-file case tree.",
                ],
            ),
        },
        {
            "case_id": "case:6a3c7be6adbfa11a7168",
            "brief_id": "brief:ea59bff4915df9bc",
            "block_id": HELDOUT_BLOCK_ID,
            "cell_type": "renamed_implementation",
            "reference_case_id": heldout_error,
            "author_id": "actor:sealed-author-claude-06",
            "visible": _visible_brief(
                "case:6a3c7be6adbfa11a7168",
                "Independently build a greenhouse-light workflow that reports one outage burden for the complete programmed illumination cycle.",
                [
                    "Create a CSV representing 144 programmed light periods, 108 periods retained after sensor plausibility checks, and 27 outages in retained periods, with all excluded periods accounted for."
                ],
                [
                    "Declare the target as the complete 144-period illumination cycle.",
                    "Use the 108 sensor-check passes as the exposure denominator for the selected burden and describe it as cycle-wide.",
                    "Use different filenames, variable names, report layout, and domain vocabulary from any supplied instrument material.",
                    "State that no governing amendment or approved deviation exists.",
                ],
            ),
        },
    ]


def _agent_configuration(provider: str) -> dict[str, str]:
    if provider == "Anthropic":
        return {
            "agent_surface": "Claude Code CLI",
            "agent_version": "2.1.221",
            "model_name": "Claude Opus 5",
            "model_id": "claude-opus-5",
            "reasoning_configuration": "high",
        }
    if provider == "OpenAI":
        return {
            "agent_surface": "Codex CLI",
            "agent_version": "0.144.0",
            "model_name": "GPT-5.6 Sol",
            "model_id": "gpt-5.6-sol",
            "reasoning_configuration": "high",
        }
    return {
        "agent_surface": "Local deterministic validator",
        "agent_version": "1.0.0",
        "model_name": "No model",
        "model_id": "software:prospective-selected-result-verifier-v1.0.0",
        "reasoning_configuration": "deterministic_no_model",
    }


def _participant(
    config: dict[str, Any],
    participant_id: str,
    role: str,
    provider: str,
    context_id: str,
) -> dict[str, Any]:
    role_config = config["role_configurations"][role]
    return {
        "participant_id": participant_id,
        "role": role,
        "provider": provider,
        **_agent_configuration(provider),
        "execution_context_id": context_id,
        "system_prompt_digest": sha256_digest(role_config["system_prompt"]),
        "tool_policy_digest": semantic_digest(role_config["tool_policy"]),
        "environment_digest": semantic_digest(config["environment"]),
        "calibration_suite_digest": semantic_digest(config["reviewer_calibration_suite"]),
        "calibration_status": (
            "required_before_participation"
            if role in {"stage1_reviewer", "stage2_reviewer"}
            else "not_applicable"
        ),
    }


def _participants(config: dict[str, Any]) -> list[dict[str, Any]]:
    author_specs = [
        ("actor:pilot-author-claude-01", "Anthropic"),
        ("actor:pilot-author-codex-01", "OpenAI"),
        ("actor:pilot-author-claude-02", "Anthropic"),
        ("actor:pilot-author-codex-02", "OpenAI"),
        ("actor:pilot-author-claude-03", "Anthropic"),
        ("actor:pilot-author-codex-03", "OpenAI"),
        ("actor:sealed-author-codex-04", "OpenAI"),
        ("actor:sealed-author-claude-04", "Anthropic"),
        ("actor:sealed-author-codex-05", "OpenAI"),
        ("actor:sealed-author-claude-05", "Anthropic"),
        ("actor:sealed-author-codex-06", "OpenAI"),
        ("actor:sealed-author-claude-06", "Anthropic"),
    ]
    participants = [
        _participant(config, identifier, "author", provider, f"context:{identifier[6:]}-v2")
        for identifier, provider in author_specs
    ]
    for identifier, provider in (
        ("actor:stage1-claude-01", "Anthropic"),
        ("actor:stage1-claude-02", "Anthropic"),
        ("actor:stage1-codex-01", "OpenAI"),
        ("actor:stage1-codex-02", "OpenAI"),
    ):
        participants.append(
            _participant(
                config,
                identifier,
                "stage1_reviewer",
                provider,
                f"context:{identifier[6:]}-calibrated-v2",
            )
        )
    for identifier, provider in (
        ("actor:stage2-claude-01", "Anthropic"),
        ("actor:stage2-codex-01", "OpenAI"),
    ):
        participants.append(
            _participant(
                config,
                identifier,
                "stage2_reviewer",
                provider,
                f"context:{identifier[6:]}-calibrated-v2",
            )
        )
    participants.extend(
        [
            _participant(
                config,
                "actor:selected-result-validator-01",
                "evidence_validator",
                "Local deterministic software",
                "context:selected-result-validator-v2",
            ),
            _participant(
                config,
                "actor:detector-implementer-codex-01",
                "detector_implementer",
                "OpenAI",
                "context:detector-implementer-blind-v2",
            ),
        ]
    )
    return participants


def _protocol_participants(enrollment: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "participant_id": item["participant_id"],
                "role": item["role"],
                "provider": item["provider"],
                "execution_context_id": item["execution_context_id"],
                "identity_evidence_digest": item["configuration_digest"],
            }
            for item in enrollment["participants"]
            if item["role"] != "evidence_validator"
        ),
        key=lambda item: str(item["participant_id"]),
    )


def build_first_direct_qualification_lane(
    project_root: Path, output_dir: Path
) -> dict[str, dict[str, Any]]:
    config = load_effective_execution_configuration(project_root)
    precase = json.loads((project_root / PRECASE_RELATIVE).read_text(encoding="utf-8"))
    enrollment = freeze_participant_enrollment(
        {
            "enrollment_id": "enrollment:complete-domain-exposure-denominator-v2",
            "precase_freeze_digest": precase["freeze_digest"],
            "participants": _participants(config),
        },
        frozen_at=FROZEN_AT,
    )
    cases = _case_specs()
    brief_manifest = freeze_authoring_brief_manifest(
        {
            "manifest_id": "brief-manifest:complete-domain-exposure-denominator-v2",
            "lane_id": "lane:complete-domain-exposure-denominator-v2",
            "precase_freeze_digest": precase["freeze_digest"],
            "expected_case_count": 14,
            "additional_hidden_terms": [
                ENVELOPE_ID,
                CHECK_ID,
                CANDIDATE_ID,
                CANONICAL_ISSUE_CLASS,
                DETECTOR_ID,
                precase["binding"]["binding_id"],
            ],
            "briefs": [
                {
                    "brief_id": item["brief_id"],
                    "case_id": item["case_id"],
                    "author_visible_brief": item["visible"],
                }
                for item in cases
            ],
        },
        frozen_at=FROZEN_AT,
    )
    brief_by_case = {str(item["case_id"]): item for item in brief_manifest["briefs"]}
    assignments = [
        {
            "case_id": item["case_id"],
            "envelope_id": ENVELOPE_ID,
            "block_id": item["block_id"],
            "cell_type": item["cell_type"],
            "source_kind": "independent_prospective",
            "reference_case_id": item["reference_case_id"],
            "author_id": item["author_id"],
            "stage1_reviewer_ids": list(STAGE1_IDS),
            "stage2_reviewer_ids": list(STAGE2_IDS),
            "authoring_brief_digest": brief_by_case[item["case_id"]]["brief_digest"],
            "assigned_at": ASSIGNED_AT,
        }
        for item in cases
    ]
    lane = freeze_direct_qualification_lane(
        {
            "lane_id": "lane:complete-domain-exposure-denominator-v2",
            "heldout_access_policy": "withhold_author_access_until_approved_threshold",
            "prospective_protocol": {
                "protocol_id": "prospective-protocol:complete-domain-exposure-denominator-v2",
                "expected_envelope_count": 1,
                "detector_lock": {
                    "detector_id": precase["detector"]["detector_id"],
                    "detector_version": precase["detector"]["detector_version"],
                    "detector_manifest_digest": precase["detector"]["detector_manifest_digest"],
                    "implementation_digest": precase["detector"]["implementation_digest"],
                    "frozen_at": precase["frozen_at"],
                },
                "participants": _protocol_participants(enrollment),
                "envelopes": [
                    {
                        "envelope_id": ENVELOPE_ID,
                        "check_id": CHECK_ID,
                        "candidate_id": CANDIDATE_ID,
                        "binding_digest": precase["binding"]["binding_digest"],
                    }
                ],
                "blocks": [
                    {"block_id": PILOT_BLOCK_ID, "evidence_role": "threshold_pilot"},
                    {
                        "block_id": HELDOUT_BLOCK_ID,
                        "evidence_role": "qualification_heldout",
                    },
                ],
                "assignments": assignments,
                "governance": {
                    "all_outcomes_retained": True,
                    "no_replacement": True,
                    "public_benchmark_qualification_excluded": True,
                    "development_case_qualification_excluded": True,
                    "detector_implementers_label_blind": True,
                    "review_detector_output_hidden": True,
                    "independent_review_contexts_required": True,
                },
            },
        },
        precase_freeze=precase,
        participant_enrollment=enrollment,
        brief_manifest=brief_manifest,
        frozen_at=FROZEN_AT,
    )
    artifacts = {
        "PARTICIPANT_ENROLLMENT.json": enrollment,
        "AUTHORING_BRIEF_MANIFEST.json": brief_manifest,
        "LANE_FREEZE.json": lane,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in artifacts.items():
        path = output_dir / name
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"Refusing to overwrite frozen lane artifact: {path}")
        path.write_text(
            json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return artifacts


def load_effective_execution_configuration(project_root: Path) -> dict[str, Any]:
    base_path = project_root / BASE_LANE_RELATIVE / CONFIGURATION_NAME
    amendment_path = project_root / LANE_RELATIVE / CONFIGURATION_AMENDMENT_NAME
    config = json.loads(base_path.read_text(encoding="utf-8"))
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    if amendment["superseded_configuration_content_digest"] != sha256_digest(
        base_path.read_bytes()
    ):
        raise ValueError("The superseded execution configuration bytes have drifted.")
    effective = deepcopy(config)
    effective["role_configurations"]["author"]["system_prompt"] = amendment[
        "replacement_author_system_prompt"
    ]
    return effective


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    output = args.output.resolve() if args.output else project_root / LANE_RELATIVE
    build_first_direct_qualification_lane(project_root, output)


if __name__ == "__main__":
    main()
