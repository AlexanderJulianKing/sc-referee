from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.direct_qualification_lane import (
    validate_authoring_brief_manifest,
    validate_direct_qualification_lane,
    validate_participant_enrollment,
)
from sc_referee_evaluation.lean_pipeline import pipeline_step_order
from sc_referee_evaluation.prospective_qualification import REQUIRED_CELL_TYPES

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_dependence_qualification_lane import (
    ADDITIONAL_HIDDEN_TERMS,
    CANDIDATE_ID,
    CHECK_ID,
    HELDOUT_AUTHOR_1,
    HELDOUT_AUTHOR_2,
    HELDOUT_BLOCK_ID,
    HELDOUT_RENAMED_LEFT,
    HELDOUT_RENAMED_RESULT,
    HELDOUT_RENAMED_RIGHT,
    HELDOUT_RENAMED_TRIPLES,
    PILOT_AUTHOR_1,
    PILOT_AUTHOR_2,
    PILOT_BLOCK_ID,
    PILOT_RENAMED_LEFT,
    PILOT_RENAMED_RESULT,
    PILOT_RENAMED_RIGHT,
    PILOT_RENAMED_TRIPLES,
    REGISTRY_RELATIVE,
    ROLES,
    assemble_dependence_qualification_inputs,
    build_dependence_qualification_lane,
)
from scripts.dependence_heldout_run import (
    AUTHOR_OPUS_21,
    AUTHOR_OPUS_22,
    EXPECTED_AUTHOR_ROLES,
    HONORING_PARTICIPANT_BY_SEALED_AUTHOR,
    LANE_RELATIVE,
    OPENING_RELATIVE,
    STEP_CHOICES,
    DependenceHeldoutConfigurationError,
    heldout_config,
)
from scripts.lean_pipeline import DEPENDENCE_SANDBOX_PYTHON, default_dependence_config


def _write_future_seal(project_root: Path, root: Path) -> dict[str, dict[str, Any]]:
    return build_dependence_qualification_lane(project_root, root / LANE_RELATIVE)


def _spec_by_block_and_role(assembled: dict[str, Any], block_id: str, role: str) -> dict[str, Any]:
    return next(
        item
        for item in assembled["case_specs"]
        if item["block_id"] == block_id and item["cell_type"] == role
    )


def test_dependence_precase_reads_complete_live_registry_binding(project_root: Path) -> None:
    assembled = assemble_dependence_qualification_inputs(project_root)
    precase = assembled["FREEZE_MANIFEST.json"]
    supplied = dict(precase)
    assert supplied.pop("freeze_digest") == semantic_digest(supplied)
    assert precase["artifact_kind"] == "direct_envelope_precase_freeze"
    assert precase["metric_case_count"] == 0
    assert precase["scientific_label_count"] == 0
    assert precase["detector_outcome_count"] == 0
    assert precase["envelope"]["check_id"] == CHECK_ID
    assert precase["envelope"]["candidate_id"] == CANDIDATE_ID
    assert precase["binding"]["binding_id"].startswith("method-conflict-binding:")
    binding = dict(precase["binding"])
    digest = binding.pop("binding_digest")
    assert digest == semantic_digest(binding)
    assert precase["envelope"]["binding_digest"] == digest
    assert (
        precase["detector"]["detector_manifest_digest"]
        == precase["binding"]["detector_manifest_digest"]
    )
    assert (
        precase["scientific_check"]["check_manifest_digest"]
        == precase["binding"]["check_manifest_digest"]
    )
    assert precase["registry"]["content_digest"] == sha256_digest(
        (project_root / REGISTRY_RELATIVE).read_bytes()
    )
    adapter_path = project_root / precase["adapter"]["implementation_path"]
    assert precase["adapter"]["implementation_source_digest"] == sha256_digest(
        adapter_path.read_bytes()
    )
    detector_path = project_root / precase["detector"]["implementation_path"]
    assert precase["detector"]["implementation_digest"] == sha256_digest(detector_path.read_bytes())


def test_dependence_fourteen_briefs_replay_and_pass_literal_leakage_screen(
    project_root: Path,
) -> None:
    assembled = assemble_dependence_qualification_inputs(project_root)
    enrollment = assembled["PARTICIPANT_ENROLLMENT.json"]
    manifest = assembled["AUTHORING_BRIEF_MANIFEST.json"]
    assert validate_participant_enrollment(enrollment) == enrollment
    assert validate_authoring_brief_manifest(manifest) == manifest
    assert manifest["expected_case_count"] == 14
    assert len(manifest["briefs"]) == 14
    assert all(item["literal_leakage_screen_passed"] for item in manifest["briefs"])
    assert set(ADDITIONAL_HIDDEN_TERMS).issubset(manifest["literal_hidden_terms"])
    assert "k1" not in manifest["literal_hidden_terms"]
    assert "k2" not in manifest["literal_hidden_terms"]
    serialized = json.dumps(
        [item["author_visible_brief"] for item in manifest["briefs"]],
        sort_keys=True,
    ).casefold()
    for term in ADDITIONAL_HIDDEN_TERMS:
        assert term.casefold() not in serialized

    base = default_dependence_config()
    for block_id in (PILOT_BLOCK_ID, HELDOUT_BLOCK_ID):
        for role in set(ROLES) - {"renamed_implementation"}:
            spec = _spec_by_block_and_role(assembled, block_id, role)
            assert spec["visible"]["construction_constraints"] == base.role_constraints[role]


def _assert_renamed_shape(
    triples: tuple[tuple[str, str, str], ...],
    left: tuple[float, ...],
    *,
    key_prefix: str,
    companion_prefix: str,
    tag_prefix: str,
) -> None:
    assert len(triples) == 24
    assert Counter(k1 for k1, _k2, _tag in triples) == {
        f"{key_prefix}{index:02d}": 3 for index in range(1, 9)
    }
    assert {k2 for _k1, k2, _tag in triples} == {
        f"{companion_prefix}{index:02d}" for index in range(1, 25)
    }
    assert {tag for _k1, _k2, tag in triples} == {
        f"{tag_prefix}{index:02d}" for index in range(1, 25)
    }
    assert all(k1[1:] != k2[1:] for k1, k2, _tag in triples)
    for key in {row[0] for row in triples}:
        values = [left[index] for index, row in enumerate(triples) if row[0] == key]
        assert len(set(values)) == 3


def test_renamed_implementation_drafts_are_distinct_across_blocks(
    project_root: Path,
) -> None:
    assembled = assemble_dependence_qualification_inputs(project_root)
    _assert_renamed_shape(
        PILOT_RENAMED_TRIPLES,
        PILOT_RENAMED_LEFT,
        key_prefix="x",
        companion_prefix="y",
        tag_prefix="s",
    )
    _assert_renamed_shape(
        HELDOUT_RENAMED_TRIPLES,
        HELDOUT_RENAMED_LEFT,
        key_prefix="r",
        companion_prefix="z",
        tag_prefix="q",
    )
    assert set(PILOT_RENAMED_TRIPLES).isdisjoint(HELDOUT_RENAMED_TRIPLES)
    assert set(PILOT_RENAMED_LEFT).isdisjoint(HELDOUT_RENAMED_LEFT)
    assert set(PILOT_RENAMED_RIGHT).isdisjoint(HELDOUT_RENAMED_RIGHT)

    pilot = _spec_by_block_and_role(assembled, PILOT_BLOCK_ID, "renamed_implementation")
    heldout = _spec_by_block_and_role(assembled, HELDOUT_BLOCK_ID, "renamed_implementation")
    for spec, result, namespaces in (
        (pilot, PILOT_RENAMED_RESULT, "x/y/s"),
        (heldout, HELDOUT_RENAMED_RESULT, "r/z/q"),
    ):
        assert spec["design_status"] == "draft_pending_hostile_review"
        text = "\n".join(spec["visible"]["construction_constraints"])
        assert result in text
        assert namespaces in text
        assert "differ from every other supplied construction" in text


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    (
        (PILOT_RENAMED_LEFT, PILOT_RENAMED_RIGHT, PILOT_RENAMED_RESULT),
        (HELDOUT_RENAMED_LEFT, HELDOUT_RENAMED_RIGHT, HELDOUT_RENAMED_RESULT),
    ),
)
@pytest.mark.skipif(
    not DEPENDENCE_SANDBOX_PYTHON.is_file(),
    reason="dedicated SciPy 1.14.0 qualification interpreter is absent",
)
def test_renamed_implementation_results_preflight_in_scipy_114(
    left: tuple[float, ...], right: tuple[float, ...], expected: str
) -> None:
    script = (
        "import scipy, scipy.stats as st\n"
        f"left={list(left)!r}\n"
        f"right={list(right)!r}\n"
        "assert scipy.__version__ == '1.14.0'\n"
        "print(repr(st.mannwhitneyu(left, right)))\n"
    )
    completed = subprocess.run(
        [str(DEPENDENCE_SANDBOX_PYTHON), "-I", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout == expected + "\n"


def test_two_block_allocator_accepts_complete_fourteen_case_matrix(
    project_root: Path, tmp_path: Path
) -> None:
    assert tuple(REQUIRED_CELL_TYPES) == ROLES
    output = tmp_path / "dependence-lane"
    artifacts = build_dependence_qualification_lane(project_root, output)
    lane = artifacts["LANE_FREEZE.json"]
    protocol = lane["prospective_protocol"]
    assignments = protocol["assignments"]
    assert (
        validate_direct_qualification_lane(
            lane,
            precase_freeze=artifacts["FREEZE_MANIFEST.json"],
            participant_enrollment=artifacts["PARTICIPANT_ENROLLMENT.json"],
            brief_manifest=artifacts["AUTHORING_BRIEF_MANIFEST.json"],
        )
        == lane
    )
    assert protocol["coverage"] == {
        "required_cell_types": list(ROLES),
        "matrix_blocks": {
            HELDOUT_BLOCK_ID: "qualification_heldout",
            PILOT_BLOCK_ID: "threshold_pilot",
        },
        "required_case_count": 14,
        "matrix_complete": True,
    }
    assert Counter((item["block_id"], item["cell_type"]) for item in assignments) == {
        (block_id, role): 1 for block_id in (PILOT_BLOCK_ID, HELDOUT_BLOCK_ID) for role in ROLES
    }
    heldout_ids = sorted(
        str(item["case_id"]) for item in assignments if item["block_id"] == HELDOUT_BLOCK_ID
    )
    pilot_ids = {str(item["case_id"]) for item in assignments if item["block_id"] == PILOT_BLOCK_ID}
    assert lane["heldout_seal"] == {
        "block_ids": [HELDOUT_BLOCK_ID],
        "case_ids": heldout_ids,
        "author_access_state": "withheld_until_approved_threshold",
        "scientific_labels_present": False,
        "detector_outcomes_present": False,
    }
    assert pilot_ids.isdisjoint(heldout_ids)
    assert len(pilot_ids) == 7
    assert all(case_id.startswith("case:") and len(case_id) == 25 for case_id in pilot_ids)
    for name, value in artifacts.items():
        path = output / name
        assert json.loads(path.read_text(encoding="utf-8")) == value


def test_freeze_uses_sealed_author_slots_not_future_runtime_actors(
    project_root: Path,
) -> None:
    assembled = assemble_dependence_qualification_inputs(project_root)
    enrollment = assembled["PARTICIPANT_ENROLLMENT.json"]
    author_ids = {
        item["participant_id"] for item in enrollment["participants"] if item["role"] == "author"
    }
    assert author_ids == {
        PILOT_AUTHOR_1,
        PILOT_AUTHOR_2,
        HELDOUT_AUTHOR_1,
        HELDOUT_AUTHOR_2,
    }
    assert AUTHOR_OPUS_21 not in author_ids
    assert AUTHOR_OPUS_22 not in author_ids


def test_dependence_heldout_config_carries_every_envelope_field(
    project_root: Path, tmp_path: Path
) -> None:
    artifacts = _write_future_seal(project_root, tmp_path)
    config, payload = heldout_config(tmp_path)
    base = default_dependence_config()
    assignments = artifacts["LANE_FREEZE.json"]["prospective_protocol"]["assignments"]
    heldout_ids = {item["case_id"] for item in assignments if item["block_id"] == HELDOUT_BLOCK_ID}
    assert set(config.sealed_case_assignments or {}) == heldout_ids
    assert len(config.sealed_case_assignments or {}) == 7
    assert config.author_roles == EXPECTED_AUTHOR_ROLES
    assert set(config.authors) == {AUTHOR_OPUS_21, AUTHOR_OPUS_22}
    assert config.reviewer.participant_id == "actor:dependence-heldout-reviewer-fable-13"
    assert config.escalation_reviewer.participant_id == (
        "actor:dependence-heldout-reviewer-opus-09"
    )
    assert config.allowed_import_roots == base.allowed_import_roots
    assert config.detector_id == base.detector_id
    assert config.sandbox_python == base.sandbox_python
    assert config.required_sandbox_distributions == base.required_sandbox_distributions
    assert config.controller_material_files == base.controller_material_files
    assert config.material_input_paths == base.material_input_paths
    assert config.input_csv_row_bounds == base.input_csv_row_bounds
    assert config.frozen_workflow_template == base.frozen_workflow_template
    assert config.mq_tolerant_roles == base.mq_tolerant_roles
    assert config.contract_free_roles == base.contract_free_roles
    assert config.frozen_workflow_procedure_by_role["renamed_implementation"] == "mannwhitneyu"
    assert config.opening_record_relative == OPENING_RELATIVE
    assert pipeline_step_order(config) == STEP_CHOICES
    assert payload["threshold_authority"] == "pending_separate_maintainer_decision"
    assert len(payload["sealed_assignment_table"]) == 7
    assert {
        (item["sealed_author_id"], item["honoring_participant_id"])
        for item in payload["sealed_assignment_table"]
    } == set(HONORING_PARTICIPANT_BY_SEALED_AUTHOR.items())


def test_dependence_heldout_loader_refuses_six_cases(project_root: Path, tmp_path: Path) -> None:
    _write_future_seal(project_root, tmp_path)
    path = tmp_path / LANE_RELATIVE / "LANE_FREEZE.json"
    lane = json.loads(path.read_text(encoding="utf-8"))
    lane["heldout_seal"]["case_ids"].pop()
    candidate = dict(lane)
    candidate.pop("lane_freeze_digest")
    lane["lane_freeze_digest"] = semantic_digest(candidate)
    path.write_text(json.dumps(lane), encoding="utf-8")
    with pytest.raises(
        DependenceHeldoutConfigurationError,
        match="not exactly seven distinct cases",
    ):
        heldout_config(tmp_path)
