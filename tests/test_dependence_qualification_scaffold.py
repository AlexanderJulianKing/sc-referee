from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation import lean_pipeline as evaluation_pipeline
from sc_referee_evaluation.direct_qualification_lane import (
    validate_authoring_brief_manifest,
    validate_direct_qualification_lane,
    validate_participant_enrollment,
)
from sc_referee_evaluation.lean_pipeline import pipeline_step_order
from sc_referee_evaluation.prospective_qualification import REQUIRED_CELL_TYPES

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition.adapter import DependenceRecognitionShadowAdapter
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenInspectionContext,
    FrozenMaterialInput,
    InspectionDocument,
    RecordRef,
)
from scripts.build_dependence_qualification_lane import (
    ADDITIONAL_HIDDEN_TERMS,
    CANDIDATE_ID,
    CHECK_ID,
    HELDOUT_AUTHOR_1,
    HELDOUT_AUTHOR_2,
    HELDOUT_BLOCK_ID,
    HELDOUT_LEFT_BY_ROLE,
    HELDOUT_PROCEDURE_BY_ROLE,
    HELDOUT_RENAMED_LEFT,
    HELDOUT_RENAMED_RESULT,
    HELDOUT_RENAMED_RIGHT,
    HELDOUT_RENAMED_TRIPLES,
    HELDOUT_RESULT_BY_ROLE,
    HELDOUT_RIGHT_BY_ROLE,
    HELDOUT_TRIPLES_BY_ROLE,
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
    for role in set(ROLES) - {"renamed_implementation"}:
        pilot = _spec_by_block_and_role(assembled, PILOT_BLOCK_ID, role)
        heldout = _spec_by_block_and_role(assembled, HELDOUT_BLOCK_ID, role)
        assert pilot["visible"]["construction_constraints"] == base.role_constraints[role]
        assert heldout["visible"]["construction_constraints"] != base.role_constraints[role]
        assert heldout["design_status"] == "pilot_d_structure_fresh_literals"


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
        assert spec["design_status"] == "hostile_brief_review_cleared_for_freeze"
        text = "\n".join(spec["visible"]["construction_constraints"])
        assert result in text
        assert namespaces in text
        assert "differ from every other supplied construction" in text
        assert "No row has matching numeric suffixes for `k1` and `k2`." in text
    assert HELDOUT_RENAMED_RESULT != PILOT_RENAMED_RESULT
    assert "statistic=np.float64(288.0)" in HELDOUT_RENAMED_RESULT


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


def _heldout_brief_literals(spec: dict[str, Any]) -> dict[str, Any]:
    constraints = list(spec["visible"]["construction_constraints"])
    triples = tuple(
        tuple(value.split(",")) for value in re.findall(r"`([^`]+,[^`]+,[^`]+)`", constraints[0])
    )
    vectors = re.findall(r"`([^`]+)`", constraints[1])
    assert len(vectors) == 2
    left = tuple(float(value) for value in vectors[0].split(", "))
    right = tuple(float(value) for value in vectors[1].split(", "))
    procedure_matches = [
        match
        for constraint in constraints
        if (match := re.search(r"Call `scipy\.stats\.([a-z_]+)`\.", constraint))
    ]
    assert len(procedure_matches) == 1
    result_matches = [
        match
        for constraint in constraints
        if (
            match := re.search(
                r"exact SciPy 1\.14\.0 result text is `(.*?)`; the report",
                constraint,
            )
        )
    ]
    assert len(result_matches) == 1
    return {
        "triples": triples,
        "left": left,
        "right": right,
        "procedure": procedure_matches[0].group(1),
        "result": result_matches[0].group(1),
    }


def _numeric_suffix(value: str) -> str:
    match = re.search(r"(\d+)$", value)
    assert match is not None
    return match.group(1)


def _namespace(value: str) -> str:
    return value.removesuffix(_numeric_suffix(value))


def test_all_heldout_briefs_freeze_disjoint_binary_fraction_literals(
    project_root: Path,
) -> None:
    assembled = assemble_dependence_qualification_inputs(project_root)
    pilot_namespaces: set[str] = set()
    pilot_measurements: set[float] = set()
    for role in ROLES:
        pilot = _spec_by_block_and_role(assembled, PILOT_BLOCK_ID, role)
        constraints = list(pilot["visible"]["construction_constraints"])
        triples = [
            value.split(",")
            for value in re.findall(r"`([^`]+,[^`]+,[^`]+)`", constraints[0])
            if all(re.search(r"\d+$", item) for item in value.split(","))
        ]
        pilot_namespaces.update(_namespace(value) for triple in triples for value in triple)
        vectors = [
            value
            for value in re.findall(r"`([^`]+)`", constraints[1])
            if "," in value
            and all(item.replace(".", "", 1).isdigit() for item in value.split(", "))
        ]
        assert len(vectors) == 2
        pilot_measurements.update(
            float(value) for vector in vectors for value in vector.split(", ")
        )
    all_namespaces: set[str] = set()
    measurement_sets: dict[str, set[float]] = {}
    expected_k1_multiplicity = {
        "error_bearing": 2,
        "corrected_twin": 1,
        "valid_alternative": 1,
        "hard_negative": 1,
        "ambiguous": 2,
        "unsupported": 1,
        "renamed_implementation": 3,
    }
    for role in ROLES:
        spec = _spec_by_block_and_role(assembled, HELDOUT_BLOCK_ID, role)
        parsed = _heldout_brief_literals(spec)
        triples = parsed["triples"]
        left = parsed["left"]
        right = parsed["right"]
        assert triples == HELDOUT_TRIPLES_BY_ROLE[role]
        assert left == HELDOUT_LEFT_BY_ROLE[role]
        assert right == HELDOUT_RIGHT_BY_ROLE[role]
        assert parsed["procedure"] == HELDOUT_PROCEDURE_BY_ROLE[role]
        assert parsed["result"] == HELDOUT_RESULT_BY_ROLE[role]
        assert len(triples) == len(left) == len(right)
        assert all(_numeric_suffix(k1) != _numeric_suffix(k2) for k1, k2, _tag in triples)
        counts = Counter(k1 for k1, _k2, _tag in triples)
        assert set(counts.values()) == {expected_k1_multiplicity[role]}
        assert len({k2 for _k1, k2, _tag in triples}) == len(triples)
        assert len({tag for _k1, _k2, tag in triples}) == len(triples)
        namespaces = {_namespace(value) for triple in triples for value in triple}
        assert len(namespaces) == 3
        assert all_namespaces.isdisjoint(namespaces)
        all_namespaces.update(namespaces)
        values = {*left, *right}
        assert all(value * 8 == int(value * 8) for value in values)
        measurement_sets[role] = values
        constraint_text = "\n".join(spec["visible"]["construction_constraints"])
        assert "No row has matching numeric suffixes for `k1` and `k2`." in constraint_text

    assert pilot_namespaces == {"u", "v", "t", "x", "y", "s"}
    assert all_namespaces.isdisjoint(pilot_namespaces)
    assert len(all_namespaces) == len(ROLES) * 3
    assert all(values.isdisjoint(pilot_measurements) for values in measurement_sets.values())
    for index, role in enumerate(ROLES):
        for other_role in ROLES[index + 1 :]:
            assert measurement_sets[role].isdisjoint(measurement_sets[other_role])


def _honest_author_materials(spec: dict[str, Any]) -> tuple[bytes, str, bytes, str]:
    parsed = _heldout_brief_literals(spec)
    csv_lines = ["k1,k2,tag,a,b"]
    csv_lines.extend(
        f"{k1},{k2},{tag},{a},{b}"
        for (k1, k2, tag), a, b in zip(
            parsed["triples"], parsed["left"], parsed["right"], strict=True
        )
    )
    data = ("\n".join(csv_lines) + "\n").encode("ascii")
    template = default_dependence_config().frozen_workflow_template
    assert template is not None
    source = template.replace("{procedure}", str(parsed["procedure"]))
    report = f"[selected-result] {parsed['result']}\n".encode("ascii")
    return data, source, report, str(parsed["procedure"])


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.skipif(
    not DEPENDENCE_SANDBOX_PYTHON.is_file(),
    reason="dedicated SciPy 1.14.0 qualification interpreter is absent",
)
def test_heldout_brief_honest_author_path_is_byte_exact(
    project_root: Path, tmp_path: Path, role: str
) -> None:
    assembled = assemble_dependence_qualification_inputs(project_root)
    spec = _spec_by_block_and_role(assembled, HELDOUT_BLOCK_ID, role)
    data, source, expected_report, _procedure = _honest_author_materials(spec)
    case_root = tmp_path / role
    (case_root / "inputs").mkdir(parents=True)
    (case_root / "workflow").mkdir()
    (case_root / "results").mkdir()
    (case_root / "inputs/data.csv").write_bytes(data)
    (case_root / "workflow/analysis.py").write_text(source, encoding="utf-8")
    evaluation_pipeline._static_guard(source, default_dependence_config().allowed_import_roots)
    observed = evaluation_pipeline._sandbox_run(case_root, DEPENDENCE_SANDBOX_PYTHON)
    assert observed == expected_report


def _heldout_recognition_context(
    *, data: bytes, source: str, procedure: str, authority_present: bool
) -> FrozenInspectionContext:
    data_path = "inputs/data.csv"
    report_path = "results/report.md"
    requirements = b"numpy==2.2.6\nscipy==1.14.0\n"
    data_digest = sha256_digest(data)
    requirements_digest = sha256_digest(requirements)
    surface_ref = RecordRef("publication_surface", "surface:heldout-preflight")
    artifact_ref = RecordRef("artifact", "artifact:heldout-report")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:heldout-preflight")
    analysis_file_ref = RecordRef("file_record", "file:heldout-analysis")
    parser_ref = RecordRef("parser_result", "parser:heldout-analysis")
    data_file_ref = RecordRef("file_record", "file:heldout-data")
    data_identity_ref = RecordRef("asset_identity", "asset:heldout-data")
    requirements_file_ref = RecordRef("file_record", "file:heldout-requirements")
    requirements_identity_ref = RecordRef("asset_identity", "asset:heldout-requirements")
    analysis_ref = RecordRef("analysis", "analysis:heldout")
    procedure_ref = RecordRef("procedure", "procedure:heldout")
    result_ref = RecordRef("result", "result:heldout")
    parser_payload = canonical_json(
        {"parser_id": "python-ast", "parser_version": "3.11", "state": "parsed"}
    ).encode()
    source_bytes = source.encode()
    records: list[tuple[RecordRef, dict[str, object]]] = [
        (
            surface_ref,
            {
                "publication_surface_id": surface_ref.record_id,
                "status": "resolved",
                "selection": {"selected_surface_refs": [artifact_ref.to_dict()]},
            },
        ),
        (
            artifact_ref,
            {
                "artifact_id": artifact_ref.record_id,
                "kind": "report",
                "path": report_path,
            },
        ),
        (
            snapshot_ref,
            {
                "snapshot_id": snapshot_ref.record_id,
                "extensions": {"x-material-full-digest-paths": [data_path, "requirements.txt"]},
            },
        ),
        (
            data_file_ref,
            {
                "file_record_id": data_file_ref.record_id,
                "path": data_path,
                "entry_kind": "regular_file",
                "asset_identity_ref": data_identity_ref.to_dict(),
            },
        ),
        (
            data_identity_ref,
            {
                "asset_identity_id": data_identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": data_file_ref.to_dict(),
                "identity_evidence": {"kind": "full_digest", "digest": data_digest},
            },
        ),
        (
            requirements_file_ref,
            {
                "file_record_id": requirements_file_ref.record_id,
                "path": "requirements.txt",
                "entry_kind": "regular_file",
                "asset_identity_ref": requirements_identity_ref.to_dict(),
            },
        ),
        (
            requirements_identity_ref,
            {
                "asset_identity_id": requirements_identity_ref.record_id,
                "tier": "full_digest",
                "asset_ref": requirements_file_ref.to_dict(),
                "identity_evidence": {
                    "kind": "full_digest",
                    "digest": requirements_digest,
                },
            },
        ),
        (analysis_file_ref, {"file_record_id": analysis_file_ref.record_id}),
        (parser_ref, {"parser_result_id": parser_ref.record_id}),
        (analysis_ref, {"analysis_id": analysis_ref.record_id}),
        (
            procedure_ref,
            {
                "procedure_id": procedure_ref.record_id,
                "resolved_callable": f"scipy.stats.{procedure}",
            },
        ),
        (result_ref, {"result_id": result_ref.record_id, "path": report_path}),
    ]
    if authority_present:
        authorization_ref = RecordRef("human_method_authorization", "authorization:heldout")
        records.append(
            (
                authorization_ref,
                {
                    "record_type": "human_method_authorization",
                    "record_id": authorization_ref.record_id,
                    "actor_id": "human:heldout-method-owner",
                    "authority_state": "authorized",
                    "analysis_target_ref": analysis_ref.to_dict(),
                    "procedure_ref": procedure_ref.to_dict(),
                    "independent_unit_definition_id": (
                        "unit-definition:k1-first-collection-source-item"
                    ),
                    "authorized_key_columns": ["k1"],
                    "input_path": data_path,
                    "input_content_digest": data_digest,
                },
            )
        )
    return FrozenInspectionContext(
        snapshot_digest=sha256_digest(b"heldout-preflight-snapshot"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(
            InspectionDocument(
                path="workflow/analysis.py",
                file_ref=analysis_file_ref,
                content=source_bytes,
                content_digest=sha256_digest(source_bytes),
                media_type="text/x-python",
                parser_result_ref=parser_ref,
                parser_result_payload=parser_payload,
                parser_result_digest=sha256_digest(parser_payload),
            ),
        ),
        base_records=tuple(FrozenBaseRecord.from_record(ref, value) for ref, value in records),
        material_inputs=(
            FrozenMaterialInput(
                path=data_path,
                file_ref=data_file_ref,
                asset_identity_ref=data_identity_ref,
                content=data,
                content_digest=data_digest,
            ),
            FrozenMaterialInput(
                path="requirements.txt",
                file_ref=requirements_file_ref,
                asset_identity_ref=requirements_identity_ref,
                content=requirements,
                content_digest=requirements_digest,
            ),
        ),
    )


@pytest.mark.parametrize("role", ROLES)
def test_heldout_brief_real_kernel_outcome_matches_cell(project_root: Path, role: str) -> None:
    assembled = assemble_dependence_qualification_inputs(project_root)
    spec = _spec_by_block_and_role(assembled, HELDOUT_BLOCK_ID, role)
    data, source, _report, procedure = _honest_author_materials(spec)
    context = _heldout_recognition_context(
        data=data,
        source=source,
        procedure=procedure,
        authority_present=role != "ambiguous",
    )
    payload = DependenceRecognitionShadowAdapter().inspect(context)
    expected = {
        "error_bearing": ("shadow_candidate", "evaluation_candidate"),
        "corrected_twin": ("coverage_note", "covered_negative"),
        "valid_alternative": ("coverage_note", "covered_negative"),
        "hard_negative": ("coverage_note", "covered_negative"),
        "ambiguous": ("material_question", "question"),
        "unsupported": ("abstention", "unsupported"),
        "renamed_implementation": ("shadow_candidate", "evaluation_candidate"),
    }
    assert (payload["payload_type"], payload["outcome"]) == expected[role]
    body = payload["payload"]
    if role == "unsupported":
        assert "paired-procedure-operand-unverified" in body["coverage_classes"]
    elif role in {"error_bearing", "renamed_implementation"}:
        expected_repeated = 12 if role == "error_bearing" else 8
        assert len(body["repeated_independent_unit_ids"]) == expected_repeated
    elif role == "ambiguous":
        assert body["ranking"] is None
    else:
        assert body["repeated_independent_unit_ids"] == []


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
        "actor:dependence-heldout-reviewer-opus-10"
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
