from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

from sc_referee_evaluation.authoring_render_grammar import RENDER_ONLY_PROFILE_ID
from sc_referee_evaluation.prospective_selected_result_verifier import VERIFIER_VERSION

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from scripts.build_first_direct_reviewer_calibration_protocol import LANE_RELATIVE
from scripts.build_first_direct_three_case_pilot_authoring import LANE_FREEZE_DIGEST
from scripts.build_first_direct_three_case_pilot_authoring_v3 import _output_schema
from scripts.build_first_direct_three_case_pilot_authoring_v4 import _prompt

V120_AUTHORING_RELATIVE = LANE_RELATIVE / "pilot-v120-lean-authoring-three-case"
ADR_0066 = "ADR-0066-CROSS-MODEL-SINGLE-PROVIDER-REVIEW-PANEL.md"
ADR_0067 = "ADR-0067-LEAN-SINGLE-REVIEW-QUALIFICATION-PROTOCOL.md"
LANE_ENROLLMENT_DIGEST = "sha256:c29bdc3c277b840c2bf9b4369f69181190663530467926ccfdfb24407eff0016"
CHECK_MANIFEST_DIGEST_V120 = (
    "sha256:408a5e9c97788473138aa3edcb88480f846a66f930971b451a4e49013e64cca5"
)
FROZEN_AT = "2026-08-07T21:09:00Z"

AUTHOR_TEMPLATE_ID = "actor:pilot-author-claude-01"
AUTHORS = {
    "actor:v120-author-opus-01": {
        "model_id": "claude-opus-5",
        "model_name": "Claude Opus 5",
        "roles": ("error_bearing", "corrected_twin"),
    },
    "actor:v120-author-fable-01": {
        "model_id": "claude-fable-5",
        "model_name": "Claude Fable 5",
        "roles": ("valid_alternative",),
    },
}
MODEL_ALIAS_BY_MODEL_ID = {"claude-opus-5": "claude-opus-5", "claude-fable-5": "fable"}

_COMMON_TASK = (
    "Choose one concrete scientific subject area yourself, from any field you like, and invent a "
    "small truthful observational accounting for it: a planned set of observation units (choose "
    "the unit noun and the planned count yourself), a prespecified screening or eligibility step "
    "that retains only a strict subset of the planned units, and a count of occurrences of some "
    "clearly named event among the retained units. Keep every number internally consistent. The "
    "input CSV must contain the complete planned-unit accounting, including the units the "
    "screening step removed."
)
_ROLE_CONSTRAINTS = {
    "error_bearing": [
        "Declare the scientific target as the complete planned set of units.",
        "Use only the retained post-screening subset as the exposure denominator for the "
        "selected rate.",
        "Describe the selected rate as applying to the complete planned set.",
        "State that no protocol amendment or approved method deviation exists.",
    ],
    "corrected_twin": [
        "Use the same subject area, unit noun, planned count, screening step, retained count, "
        "and occurrence count as your other assigned case.",
        "Declare the scientific target as the complete planned set of units.",
        "Use the complete planned set as the exposure denominator for the selected rate and "
        "retain the removed-unit accounting.",
        "Limit the report to claims supported by that complete-set denominator.",
    ],
    "valid_alternative": [
        "Define the scientific target explicitly and only as the retained post-screening subset.",
        "Use that retained subset as the selected rate denominator.",
        "Confine every scientific claim to the retained subset and distinguish that target "
        "from the complete planned set.",
    ],
}
_REQUIRED_ARTIFACTS = [
    "One ASCII CSV input containing the complete planned-unit accounting.",
    "One Python producer in the exact frozen straight-line render-only grammar described by "
    "the author prompt.",
    "One ASCII-LF Markdown or text report whose lines exactly equal the producer output and "
    "contain exactly one [selected-result] line.",
    "One truthful author selected-result declaration for the marked report line.",
]


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], field: str, expected: str, label: str) -> None:
    supplied = record.pop(field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[field] = supplied


def _tuple_binding(project_root: Path) -> dict[str, Any]:
    registry_path = (
        project_root / "src/sc_referee/resources/scientific-check-manifests-v1/registry.json"
    )
    registry = _load(registry_path)
    module = next(
        item
        for item in registry["modules"]
        if item["check_id"] == "check:complete-domain-exposure-denominator"
    )
    if (
        module["check_version"] != "1.2.0"
        or module["manifest_digest"] != CHECK_MANIFEST_DIGEST_V120
    ):
        raise ValueError("The current registry does not carry the exact v1.2.0 module.")
    binding = next(
        item
        for item in registry["method_conflict_bindings"]
        if item["check_id"] == "check:complete-domain-exposure-denominator"
    )
    profiles_path = project_root / "src/sc_referee/scientific_checks/profiles.py"
    return {
        "check_id": module["check_id"],
        "check_version": "1.2.0",
        "adapter_version": "1.2.0",
        "check_manifest_digest": module["manifest_digest"],
        "method_conflict_binding_digest": semantic_digest(binding),
        "detector_id": binding["detector_id"],
        "detector_version": binding["detector_version"],
        "detector_manifest_digest": binding["detector_manifest_digest"],
        "profile_source_path": "src/sc_referee/scientific_checks/profiles.py",
        "profile_source_digest": sha256_digest(profiles_path.read_bytes()),
        "registry_content_digest": sha256_digest(registry_path.read_bytes()),
        "selected_result_verifier_version": VERIFIER_VERSION,
        "render_grammar_profile_id": RENDER_ONLY_PROFILE_ID,
        "production_finding_permitted": False,
    }


def _fresh_author(template: dict[str, Any], participant_id: str) -> dict[str, Any]:
    participant = deepcopy(template)
    spec = AUTHORS[participant_id]
    participant["participant_id"] = participant_id
    participant["execution_context_id"] = f"context:{participant_id.removeprefix('actor:')}-v1"
    participant["model_id"] = spec["model_id"]
    participant["model_name"] = spec["model_name"]
    participant.pop("configuration_digest", None)
    participant["configuration_digest"] = semantic_digest(participant)
    return participant


def build_v120_lean_pilot_authoring(project_root: Path) -> dict[str, dict[str, Any]]:
    lane = _load(project_root / LANE_RELATIVE / "LANE_FREEZE.json")
    _replay(lane, "lane_freeze_digest", LANE_FREEZE_DIGEST, "Direct lane freeze")
    enrollment = _load(project_root / LANE_RELATIVE / "PARTICIPANT_ENROLLMENT.json")
    _replay(
        enrollment,
        "enrollment_digest",
        LANE_ENROLLMENT_DIGEST,
        "The frozen lane participant enrollment",
    )
    template = next(
        item for item in enrollment["participants"] if item["participant_id"] == AUTHOR_TEMPLATE_ID
    )
    tuple_binding = _tuple_binding(project_root)
    tuple_digest = semantic_digest(tuple_binding)

    case_ids = {
        role: stable_id("case", "v120-lean-pilot", role, tuple_digest)
        for spec in AUTHORS.values()
        for role in spec["roles"]
    }
    briefs: dict[str, dict[str, Any]] = {}
    role_by_case: dict[str, str] = {}
    for role, case_id in case_ids.items():
        brief = {
            "brief_version": "5.0.0",
            "case_id": case_id,
            "scientific_task": _COMMON_TASK,
            "construction_constraints": list(_ROLE_CONSTRAINTS[role]),
            "required_artifacts": list(_REQUIRED_ARTIFACTS),
        }
        briefs[case_id] = brief
        role_by_case[case_id] = role

    author_assignments: list[dict[str, Any]] = []
    for participant_id in sorted(AUTHORS):
        participant = _fresh_author(template, participant_id)
        assigned_cases = sorted(case_ids[role] for role in AUTHORS[participant_id]["roles"])
        visible = [briefs[case_id] for case_id in assigned_cases]
        schema = _output_schema(participant_id, assigned_cases)
        prompt = _prompt(participant, visible, schema)
        author_assignments.append(
            {
                "participant": participant,
                "case_ids": assigned_cases,
                "author_visible_brief_digests": [
                    semantic_digest(briefs[case_id]) for case_id in assigned_cases
                ],
                "call_identity_id": str(
                    uuid5(
                        NAMESPACE_URL,
                        f"sc-referee:v120-lean-pilot-authoring:{participant_id}:{tuple_digest}",
                    )
                ),
                "prompt": prompt,
                "prompt_digest": sha256_digest(prompt),
                "output_schema": schema,
                "output_schema_digest": semantic_digest(schema),
                "command_profile": {
                    "provider_cli": "claude",
                    "print_mode": True,
                    "safe_mode": True,
                    "tool_set": "empty",
                    "mcp_set": "empty_mcpServers_record_strict",
                    "permission_mode": "dontAsk",
                    "session_persistence": False,
                    "session_id_binding": "call_identity_id",
                    "structured_output": ("prompt_embedded_schema_local_fail_closed_validation"),
                    "json_schema_argument_present": False,
                    "model_alias_argument": MODEL_ALIAS_BY_MODEL_ID[str(participant["model_id"])],
                    "model_usage_post_verification_required": True,
                },
            }
        )

    protocol: dict[str, Any] = {
        "artifact_kind": "direct_qualification_v120_lean_pilot_authoring_protocol",
        "protocol_version": "1.0.0",
        "adr_references": [ADR_0066, ADR_0067],
        "lane_freeze_digest": LANE_FREEZE_DIGEST,
        "detector_tuple": tuple_binding,
        "detector_tuple_digest": tuple_digest,
        "case_role_assignments": {
            case_id: role_by_case[case_id] for case_id in sorted(role_by_case)
        },
        "case_ids": sorted(role_by_case),
        "author_domain_choice": (
            "Each author chooses the scientific subject area, unit noun, and counts freely; "
            "no domain, vocabulary, case identity, or recognizer detail is supplied, so the "
            "authored phrasing is a blind generalization test of the v1.2.0 recognition "
            "grammar."
        ),
        "render_grammar_profile_id": RENDER_ONLY_PROFILE_ID,
        "author_assignments": author_assignments,
        "execution_policy": {
            "exact_author_context_count": 2,
            "exact_case_count": 3,
            "one_attempt_per_author_context": True,
            "repair_retry_or_replacement_permitted": False,
            "all_attempts_retained": True,
            "heldout_brief_access_permitted": False,
            "pre_admission_render_grammar_validation_required": True,
            "unchanged_static_selected_result_validation_required": True,
            "atomic_complete_causal_triad_admission_required": True,
        },
        "burned_pilot_cases_excluded": True,
        "execution_state": "frozen_not_started",
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "frozen_at": FROZEN_AT,
        "qualification_authority": "none_authoring_protocol_only",
    }
    protocol["protocol_digest"] = semantic_digest(protocol)
    return {"PILOT_AUTHORING_PROTOCOL.json": protocol}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    artifacts = build_v120_lean_pilot_authoring(project_root)
    root = project_root / V120_AUTHORING_RELATIVE
    if root.exists():
        raise FileExistsError(f"Refusing to replace frozen v120 authoring root: {root}")
    root.mkdir(parents=True)
    for name, value in artifacts.items():
        (root / name).write_text(
            json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(artifacts["PILOT_AUTHORING_PROTOCOL.json"]["protocol_digest"])


if __name__ == "__main__":
    main()
