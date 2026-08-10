from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path

import pytest
from sc_referee_evaluation.direct_qualification_lane import (
    validate_authoring_brief_manifest,
    validate_participant_enrollment,
)
from sc_referee_evaluation.lean_pipeline import pipeline_step_order
from sc_referee_evaluation.prospective_qualification import (
    REQUIRED_CELL_TYPES,
    ProspectiveQualificationError,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_dependence_qualification_lane import (
    ADDITIONAL_HIDDEN_TERMS,
    BLOCK_ID,
    CANDIDATE_ID,
    CHECK_ID,
    REGISTRY_RELATIVE,
    RENAMED_LEFT,
    RENAMED_RESULT,
    RENAMED_RIGHT,
    RENAMED_TRIPLES,
    ROLES,
    assemble_dependence_qualification_inputs,
    build_dependence_qualification_lane,
)
from scripts.dependence_heldout_run import (
    AUTHOR_OPUS_21,
    AUTHOR_OPUS_22,
    EXPECTED_AUTHOR_ROLES,
    LANE_RELATIVE,
    OPENING_RELATIVE,
    STEP_CHOICES,
    DependenceHeldoutConfigurationError,
    heldout_config,
)
from scripts.lean_pipeline import DEPENDENCE_SANDBOX_PYTHON, default_dependence_config


def _write_future_seal(project_root: Path, root: Path) -> dict[str, object]:
    assembled = assemble_dependence_qualification_inputs(project_root)
    briefs = assembled["AUTHORING_BRIEF_MANIFEST.json"]
    protocol = assembled["lane_spec"]["prospective_protocol"]
    case_ids = sorted(str(item["case_id"]) for item in protocol["assignments"])
    lane: dict[str, object] = {
        "artifact_kind": "direct_qualification_lane_freeze",
        "authoring_brief_manifest_digest": briefs["manifest_digest"],
        "prospective_protocol": protocol,
        "heldout_seal": {
            "block_ids": [BLOCK_ID],
            "case_ids": case_ids,
            "author_access_state": "withheld_until_approved_threshold",
            "scientific_labels_present": False,
            "detector_outcomes_present": False,
        },
        "study_state": "assignments_frozen_labels_unopened",
        "qualification_authority": "none_lane_freeze_only",
    }
    lane["lane_freeze_digest"] = semantic_digest(lane)
    lane_root = root / LANE_RELATIVE
    lane_root.mkdir(parents=True)
    (lane_root / "AUTHORING_BRIEF_MANIFEST.json").write_text(json.dumps(briefs), encoding="utf-8")
    (lane_root / "LANE_FREEZE.json").write_text(json.dumps(lane), encoding="utf-8")
    return assembled


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


def test_dependence_seven_briefs_replay_and_pass_literal_leakage_screen(
    project_root: Path, tmp_path: Path
) -> None:
    assembled = assemble_dependence_qualification_inputs(project_root)
    enrollment = assembled["PARTICIPANT_ENROLLMENT.json"]
    manifest = assembled["AUTHORING_BRIEF_MANIFEST.json"]
    assert validate_participant_enrollment(enrollment) == enrollment
    assert validate_authoring_brief_manifest(manifest) == manifest
    assert manifest["expected_case_count"] == 7
    assert len(manifest["briefs"]) == 7
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
    by_role = {item["cell_type"]: item for item in assembled["case_specs"]}
    for role in set(ROLES) - {"renamed_implementation"}:
        assert by_role[role]["visible"]["construction_constraints"] == (base.role_constraints[role])
    for name in (
        "FREEZE_MANIFEST.json",
        "PARTICIPANT_ENROLLMENT.json",
        "AUTHORING_BRIEF_MANIFEST.json",
    ):
        path = tmp_path / name
        path.write_text(json.dumps(assembled[name]), encoding="utf-8")
        assert json.loads(path.read_text("utf-8")) == assembled[name]


def test_renamed_implementation_draft_has_fresh_three_row_literals(
    project_root: Path,
) -> None:
    assembled = assemble_dependence_qualification_inputs(project_root)
    spec = next(
        item for item in assembled["case_specs"] if item["cell_type"] == "renamed_implementation"
    )
    assert spec["design_status"] == "draft_pending_hostile_review"
    assert len(RENAMED_TRIPLES) == 24
    assert Counter(k1 for k1, _k2, _tag in RENAMED_TRIPLES) == {
        f"x{index:02d}": 3 for index in range(1, 9)
    }
    assert {k2 for _k1, k2, _tag in RENAMED_TRIPLES} == {f"y{index:02d}" for index in range(1, 25)}
    assert {tag for _k1, _k2, tag in RENAMED_TRIPLES} == {f"s{index:02d}" for index in range(1, 25)}
    assert all(k1[1:] != k2[1:] for k1, k2, _tag in RENAMED_TRIPLES)
    for key in {row[0] for row in RENAMED_TRIPLES}:
        values = [RENAMED_LEFT[index] for index, row in enumerate(RENAMED_TRIPLES) if row[0] == key]
        assert len(set(values)) == 3
    visible = spec["visible"]
    text = "\n".join(visible["construction_constraints"])
    assert RENAMED_RESULT in text
    assert "differ from every other supplied construction" in text


@pytest.mark.skipif(
    not DEPENDENCE_SANDBOX_PYTHON.is_file(),
    reason="dedicated SciPy 1.14.0 qualification interpreter is absent",
)
def test_renamed_implementation_result_preflights_in_scipy_114() -> None:
    script = (
        "import scipy, scipy.stats as st\n"
        f"left={list(RENAMED_LEFT)!r}\n"
        f"right={list(RENAMED_RIGHT)!r}\n"
        "assert scipy.__version__ == '1.14.0'\n"
        "print(repr(st.mannwhitneyu(left, right)))\n"
    )
    completed = subprocess.run(
        [str(DEPENDENCE_SANDBOX_PYTHON), "-I", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout == RENAMED_RESULT + "\n"


def test_seven_cell_vocabulary_matches_but_single_block_allocator_refuses(
    project_root: Path, tmp_path: Path
) -> None:
    assembled = assemble_dependence_qualification_inputs(project_root)
    assert tuple(REQUIRED_CELL_TYPES) == ROLES
    assert {item["cell_type"] for item in assembled["case_specs"]} == set(ROLES)
    output = tmp_path / "dependence-lane"
    with pytest.raises(
        ProspectiveQualificationError,
        match="requires exactly one threshold-pilot and one qualification-heldout block",
    ):
        build_dependence_qualification_lane(project_root, output)
    assert not output.exists()


def test_dependence_heldout_config_carries_every_envelope_field(
    project_root: Path, tmp_path: Path
) -> None:
    assembled = _write_future_seal(project_root, tmp_path)
    config, payload = heldout_config(tmp_path)
    base = default_dependence_config()
    assert set(config.sealed_case_assignments or {}) == {
        item["case_id"] for item in assembled["case_specs"]
    }
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
    assert config.frozen_workflow_procedure_by_role["renamed_implementation"] == ("mannwhitneyu")
    assert config.opening_record_relative == OPENING_RELATIVE
    assert pipeline_step_order(config) == STEP_CHOICES
    assert payload["threshold_authority"] == "pending_separate_maintainer_decision"
    assert len(payload["sealed_assignment_table"]) == 7


def test_dependence_heldout_loader_refuses_six_cases(project_root: Path, tmp_path: Path) -> None:
    _write_future_seal(project_root, tmp_path)
    path = tmp_path / LANE_RELATIVE / "LANE_FREEZE.json"
    lane = json.loads(path.read_text("utf-8"))
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
