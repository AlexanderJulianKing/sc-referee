from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from sc_referee_evaluation.direct_qualification_lane import (
    validate_authoring_brief_manifest,
    validate_direct_qualification_lane,
    validate_participant_enrollment,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_qualification_lane import (
    BASE_LANE_RELATIVE,
    HELDOUT_BLOCK_ID,
    LANE_RELATIVE,
    PILOT_BLOCK_ID,
    build_first_direct_qualification_lane,
    load_effective_execution_configuration,
)

PRECASE_RELATIVE = Path(
    "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-v3-precase/"
    "FREEZE_MANIFEST.json"
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifacts(project_root: Path) -> dict[str, dict[str, Any]]:
    root = project_root / LANE_RELATIVE
    artifacts = {
        name: _load(root / name)
        for name in (
            "PARTICIPANT_ENROLLMENT.json",
            "AUTHORING_BRIEF_MANIFEST.json",
            "LANE_FREEZE.json",
        )
    }
    artifacts["EXECUTION_CONFIGURATION.json"] = load_effective_execution_configuration(project_root)
    return artifacts


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in _keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in _keys(item)}
    return set()


def test_first_direct_lane_artifacts_replay_and_rebuild_exactly(
    project_root: Path, tmp_path: Path
) -> None:
    artifacts = _artifacts(project_root)
    precase = _load(project_root / PRECASE_RELATIVE)
    enrollment = artifacts["PARTICIPANT_ENROLLMENT.json"]
    briefs = artifacts["AUTHORING_BRIEF_MANIFEST.json"]
    lane = artifacts["LANE_FREEZE.json"]

    assert validate_participant_enrollment(enrollment) == enrollment
    assert validate_authoring_brief_manifest(briefs) == briefs
    assert (
        validate_direct_qualification_lane(
            lane,
            precase_freeze=precase,
            participant_enrollment=enrollment,
            brief_manifest=briefs,
        )
        == lane
    )

    rebuilt = build_first_direct_qualification_lane(project_root, tmp_path)
    assert rebuilt == {
        name: artifacts[name]
        for name in (
            "PARTICIPANT_ENROLLMENT.json",
            "AUTHORING_BRIEF_MANIFEST.json",
            "LANE_FREEZE.json",
        )
    }


def test_unexposed_v1_lane_is_preserved_and_explicitly_superseded(
    project_root: Path,
) -> None:
    root = project_root / BASE_LANE_RELATIVE
    replacement_root = project_root / LANE_RELATIVE
    precase = _load(project_root / PRECASE_RELATIVE)
    enrollment = _load(root / "PARTICIPANT_ENROLLMENT.json")
    briefs = _load(root / "AUTHORING_BRIEF_MANIFEST.json")
    lane = _load(root / "LANE_FREEZE.json")
    supersession = _load(root / "SUPERSESSION.json")
    amendment = _load(replacement_root / "EXECUTION_CONFIGURATION_AMENDMENT.json")

    assert validate_participant_enrollment(enrollment) == enrollment
    assert validate_authoring_brief_manifest(briefs) == briefs
    assert (
        validate_direct_qualification_lane(
            lane,
            precase_freeze=precase,
            participant_enrollment=enrollment,
            brief_manifest=briefs,
        )
        == lane
    )
    assert supersession["superseded_lane_freeze_digest"] == lane["lane_freeze_digest"]
    assert supersession["reason_code"] == ("author_prompt_conflicts_with_frozen_case_tree_grammar")
    assert supersession["participant_authentication_count"] == 0
    assert supersession["author_brief_exposure_count"] == 0
    assert supersession["authored_case_count"] == 0
    assert supersession["scientific_label_count"] == 0
    assert supersession["detector_outcome_count"] == 0
    supersession_digest = supersession.pop("supersession_digest")
    assert supersession_digest == semantic_digest(supersession)
    amendment_digest = amendment.pop("amendment_digest")
    assert amendment_digest == semantic_digest(amendment)
    assert amendment["superseded_configuration_content_digest"] == sha256_digest(
        (root / "EXECUTION_CONFIGURATION.json").read_bytes()
    )
    assert amendment["participant_or_case_exposure_before_amendment"] is False


def test_first_direct_lane_enrolls_exact_isolated_panel(project_root: Path) -> None:
    artifacts = _artifacts(project_root)
    config = artifacts["EXECUTION_CONFIGURATION.json"]
    enrollment = artifacts["PARTICIPANT_ENROLLMENT.json"]
    participants = enrollment["participants"]

    assert Counter(item["role"] for item in participants) == {
        "author": 12,
        "stage1_reviewer": 4,
        "stage2_reviewer": 2,
        "detector_implementer": 1,
        "evidence_validator": 1,
    }
    assert Counter(
        item["provider"] for item in participants if item["role"] == "stage1_reviewer"
    ) == {"Anthropic": 2, "OpenAI": 2}
    assert Counter(
        item["provider"] for item in participants if item["role"] == "stage2_reviewer"
    ) == {"Anthropic": 1, "OpenAI": 1}
    assert len({item["execution_context_id"] for item in participants}) == 20

    environment_digest = semantic_digest(config["environment"])
    calibration_digest = semantic_digest(config["reviewer_calibration_suite"])
    for participant in participants:
        role_config = config["role_configurations"][participant["role"]]
        assert participant["system_prompt_digest"] == sha256_digest(role_config["system_prompt"])
        assert participant["tool_policy_digest"] == semantic_digest(role_config["tool_policy"])
        assert participant["environment_digest"] == environment_digest
        assert participant["calibration_suite_digest"] == calibration_digest
        expected_status = (
            "required_before_participation"
            if participant["role"] in {"stage1_reviewer", "stage2_reviewer"}
            else "not_applicable"
        )
        assert participant["calibration_status"] == expected_status


def test_first_direct_lane_freezes_matrix_and_keeps_sealed_cases_closed(
    project_root: Path,
) -> None:
    artifacts = _artifacts(project_root)
    lane = artifacts["LANE_FREEZE.json"]
    briefs = artifacts["AUTHORING_BRIEF_MANIFEST.json"]
    protocol = lane["prospective_protocol"]
    assignments = protocol["assignments"]

    assert len(briefs["briefs"]) == 14
    assert len(assignments) == 14
    assert protocol["coverage"]["matrix_complete"] is True
    assert Counter((item["block_id"], item["cell_type"]) for item in assignments) == {
        (block_id, cell_type): 1
        for block_id in (PILOT_BLOCK_ID, HELDOUT_BLOCK_ID)
        for cell_type in (
            "error_bearing",
            "corrected_twin",
            "valid_alternative",
            "hard_negative",
            "ambiguous",
            "unsupported",
            "renamed_implementation",
        )
    }
    expected_sealed = sorted(
        item["case_id"] for item in assignments if item["block_id"] == HELDOUT_BLOCK_ID
    )
    assert lane["heldout_seal"] == {
        "block_ids": [HELDOUT_BLOCK_ID],
        "case_ids": expected_sealed,
        "author_access_state": "withheld_until_approved_threshold",
        "scientific_labels_present": False,
        "detector_outcomes_present": False,
    }

    by_case = {item["case_id"]: item for item in assignments}
    for assignment in assignments:
        reference_id = assignment["reference_case_id"]
        if assignment["cell_type"] == "corrected_twin":
            assert assignment["author_id"] == by_case[reference_id]["author_id"]
        elif assignment["cell_type"] == "renamed_implementation":
            assert assignment["author_id"] != by_case[reference_id]["author_id"]


def test_first_direct_lane_exposes_no_controller_labels_to_authors(
    project_root: Path,
) -> None:
    artifacts = _artifacts(project_root)
    briefs = artifacts["AUTHORING_BRIEF_MANIFEST.json"]

    for item in briefs["briefs"]:
        visible = item["author_visible_brief"]
        assert set(visible) == {
            "brief_version",
            "case_id",
            "scientific_task",
            "available_inputs",
            "required_artifacts",
            "construction_constraints",
        }
        serialized = json.dumps(visible, sort_keys=True).casefold()
        assert "cell_type" not in _keys(visible)
        assert "detector:" not in serialized
        assert "relation-envelope:" not in serialized
        assert "check:" not in serialized
        assert item["literal_leakage_screen_passed"] is True


def test_first_direct_lane_still_has_zero_qualification_or_finding_authority(
    project_root: Path,
) -> None:
    artifacts = _artifacts(project_root)
    enrollment = artifacts["PARTICIPANT_ENROLLMENT.json"]
    briefs = artifacts["AUTHORING_BRIEF_MANIFEST.json"]
    lane = artifacts["LANE_FREEZE.json"]

    assert enrollment["qualification_authority"] == "none_enrollment_only"
    assert enrollment["authentication_status"] == "declared_not_authenticated"
    assert briefs["qualification_authority"] == "none_brief_manifest_only"
    assert lane["qualification_authority"] == "none_lane_freeze_only"
    assert lane["study_state"] == "assignments_frozen_labels_unopened"
    forbidden = {"scientific_label", "detector_observation", "finding"}
    assert not forbidden & _keys(enrollment)
    assert not forbidden & _keys(briefs)
    heldout = deepcopy(lane["heldout_seal"])
    assert heldout.pop("scientific_labels_present") is False
    assert heldout.pop("detector_outcomes_present") is False
