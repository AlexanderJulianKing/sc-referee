from __future__ import annotations

import ast
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.static_qualification import (
    StaticQualificationError,
    freeze_bounded_direction_profile,
    freeze_protocol_artifact,
    revalidate_static_proof,
    verify_bounded_direction_case,
)

from sc_referee.records.observed import build_file_records
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.snapshot.repository import capture_repository


def _collection(project_root: Path, name: str) -> list[dict[str, Any]]:
    path = project_root / "src" / "sc_referee" / "resources" / "capability-manifests-v1" / name
    value = json.loads(path.read_text(encoding="utf-8"))
    return value["records"]


def _one(records: list[dict[str, Any]], field: str, identity: str) -> dict[str, Any]:
    return deepcopy(next(record for record in records if record[field] == identity))


def _write_case(
    root: Path,
    *,
    report_direction: str = "increased",
    unsupported_writer: bool = False,
    second_closure: bool = False,
    opposite_sibling: bool = False,
) -> Path:
    root.mkdir()
    report = f"# Results\n\ntreated {report_direction} expression relative to control."
    if opposite_sibling:
        report += "\ntreated decreased expression relative to control."
    report += "\n\nDifference: 2.0\n"
    (root / "report.md").write_text(report, encoding="utf-8")
    (root / "data.csv").write_text(
        "group,expression\ntreated,3\ntreated,5\ncontrol,1\ncontrol,3\n",
        encoding="utf-8",
    )
    rendered_literal = report.replace(
        "Difference: 2.0", "Difference: {difference(Path('data.csv'))}"
    )
    report_expression = (
        "'# Results\\n' + str(difference(Path('data.csv')))"
        if unsupported_writer
        else f"f{rendered_literal!r}"
    )
    source = (
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "Path('PROJECT_CODE_EXECUTED').write_text('unsafe')\n"
        f"Path('report.md').write_text({report_expression}, encoding='utf-8')\n"
    )
    (root / "analysis.py").write_text(source, encoding="utf-8")
    if second_closure:
        (root / "second.csv").write_text(
            "group,expression\ntreated,4\ncontrol,2\n", encoding="utf-8"
        )
        (root / "second.py").write_text(source.replace("data.csv", "second.csv"), encoding="utf-8")
    return root / "PROJECT_CODE_EXECUTED"


def _inputs(
    project_root: Path,
    tmp_path: Path,
    **case_options: bool | str,
) -> dict[str, Any]:
    repository = tmp_path / "repository"
    marker = _write_case(repository, **case_options)
    captured = capture_repository(
        repository,
        tmp_path / "snapshot",
        "audit:static-qualification",
        captured_at="2026-07-30T17:00:00Z",
    )
    files = build_file_records(
        captured.file_records,
        captured.asset_identity_records,
        str(captured.snapshot_record["snapshot_id"]),
        "2026-07-30T17:00:00Z",
    )
    detectors = _collection(project_root, "detector-manifests.json")
    parsers = _collection(project_root, "parser-manifests.json")
    profiles = _collection(project_root, "profile-manifests.json")
    versions = _collection(project_root, "version-manifests.json")
    detector = _one(
        detectors,
        "detector_id",
        "detector:bounded-report-mean-direction",
    )
    selected_parsers = [
        _one(parsers, "parser_id", identity)
        for identity in (
            "parser:markdown-inventory",
            "parser:python-ast-tokenize",
            "parser:tabular-delimited-header-inventory",
        )
    ]
    selected_profiles = [
        _one(profiles, "profile_id", "semantic-profile:bounded-report-mean-direction-v1")
    ]
    selected_versions = [
        _one(
            versions,
            "version_manifest_id",
            "version-manifest:bounded-report-mean-direction-v1",
        )
    ]
    selection = freeze_protocol_artifact(
        "corpus_selection_protocol",
        "selection-protocol:bounded-direction-v1",
        "2026-07-30T17:01:00Z",
        {"selection_rule": "opaque_assignment_before_workspace_inspection"},
    )
    profile = freeze_bounded_direction_profile(
        detector,
        selected_parsers,
        selected_profiles,
        selected_versions,
        selection,
        frozen_at="2026-07-30T17:02:00Z",
    )
    assignment = freeze_protocol_artifact(
        "opaque_case_assignment",
        "case-assignment:bounded-direction-1",
        "2026-07-30T17:03:00Z",
        {
            "selection_protocol_artifact_id": selection["artifact_id"],
            "selection_protocol_artifact_digest": selection["content_digest"],
            "selected_report_path": "report.md",
        },
    )
    label = freeze_protocol_artifact(
        "scientific_label_freeze",
        "label-freeze:bounded-direction-1",
        "2026-07-30T17:04:00Z",
        {
            "case_id": "case:bounded-direction-1",
            "label_status": "verified_good_eligible",
        },
    )
    return {
        "workspace": captured.materialized_root,
        "marker": marker,
        "snapshot": captured.snapshot_record,
        "files": files,
        "identities": captured.asset_identity_records,
        "detector": detector,
        "parsers": selected_parsers,
        "profiles": selected_profiles,
        "versions": selected_versions,
        "selection": selection,
        "profile": profile,
        "assignment": assignment,
        "label": label,
    }


def _verify(inputs: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    values = {**inputs, **overrides}
    return verify_bounded_direction_case(
        values["workspace"],
        values["profile"],
        values["assignment"],
        values["label"],
        values["snapshot"],
        values["files"],
        values["identities"],
        detector_manifest=values["detector"],
        parser_manifests=values["parsers"],
        semantic_profile_manifests=values["profiles"],
        version_manifests=values["versions"],
        proof_frozen_at=values.get("proof_frozen_at", "2026-07-30T17:05:00Z"),
    )


def test_complete_proof_rederives_raw_facts_without_executing_project(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root, tmp_path)
    proof = _verify(inputs)

    assert proof["proof_status"] == "complete"
    assert proof["derived_facts"]["computed_orientation"] == "left_higher"
    relation = next(
        item
        for item in proof["applicability_results"]
        if item["check_id"] == "claim_result_relation"
    )
    assert relation["outcome"] == "conflict_absent"
    assert not inputs["marker"].exists()
    LocalSchemaRegistry(schema_root).validate(inputs["profile"])
    LocalSchemaRegistry(schema_root).validate(proof)

    assert (
        revalidate_static_proof(
            proof,
            inputs["workspace"],
            inputs["profile"],
            inputs["assignment"],
            inputs["label"],
            inputs["snapshot"],
            inputs["files"],
            inputs["identities"],
            inputs["detector"],
            inputs["parsers"],
            inputs["profiles"],
            inputs["versions"],
        )
        == proof
    )


def test_manifest_dependencies_are_typed_and_revalidated(
    project_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root, tmp_path)
    target = inputs["profile"]["target_detector"]
    assert target["semantic_profile_manifests"][0]["manifest_kind"] == ("semantic_profile_manifest")
    assert target["version_manifests"][0]["manifest_kind"] == "version_manifest"

    changed_profiles = deepcopy(inputs["profiles"])
    changed_profiles[0]["known_gaps"].append("mutation")
    with pytest.raises(StaticQualificationError, match="drifted"):
        _verify(inputs, profiles=changed_profiles)


def test_wrong_report_direction_is_recorded_as_conflict_not_hidden(
    project_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root, tmp_path, report_direction="decreased")
    proof = _verify(inputs)
    relation = next(
        item
        for item in proof["applicability_results"]
        if item["check_id"] == "claim_result_relation"
    )
    assert proof["proof_status"] == "complete"
    assert relation["outcome"] == "conflict_present"


@pytest.mark.parametrize(
    ("case_options", "failed_check"),
    [
        ({"unsupported_writer": True}, "supported_python_grammar_complete"),
        ({"second_closure": True}, "unique_dependency_closure"),
    ],
)
def test_unsupported_or_ambiguous_closure_is_unavailable(
    project_root: Path,
    tmp_path: Path,
    case_options: dict[str, bool],
    failed_check: str,
) -> None:
    inputs = _inputs(project_root, tmp_path, **case_options)
    proof = _verify(inputs)
    assert proof["proof_status"] == "unavailable"
    assert any(
        item["check_id"] == failed_check and item["completion_status"] == "unavailable"
        for item in proof["applicability_results"]
    )


def test_snapshot_candidate_removal_cannot_narrow_an_ambiguous_case(
    project_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root, tmp_path, second_closure=True)
    original = _verify(inputs)
    assert original["proof_status"] == "unavailable"

    (inputs["workspace"] / "second.py").unlink()
    (inputs["workspace"] / "second.csv").unlink()
    narrowed = _verify(inputs)

    assert narrowed["proof_status"] == "unavailable"
    enumeration = next(
        item
        for item in narrowed["applicability_results"]
        if item["check_id"] == "candidate_enumeration_complete"
    )
    assert enumeration["completion_status"] == "unavailable"
    assert "complete snapshot candidate inventory" in enumeration["detail_code"]
    with pytest.raises(StaticQualificationError, match="does not replay"):
        revalidate_static_proof(
            original,
            inputs["workspace"],
            inputs["profile"],
            inputs["assignment"],
            inputs["label"],
            inputs["snapshot"],
            inputs["files"],
            inputs["identities"],
            inputs["detector"],
            inputs["parsers"],
            inputs["profiles"],
            inputs["versions"],
        )


def test_snapshot_manifest_omission_cannot_narrow_candidate_inventory(
    project_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root, tmp_path, second_closure=True)
    files = [record for record in inputs["files"] if record["path"] != "second.py"]
    retained_file_ids = {str(record["file_record_id"]) for record in files}
    identities = [
        identity
        for identity in inputs["identities"]
        if identity["asset_ref"]["record_id"] in retained_file_ids
    ]

    proof = _verify(inputs, files=files, identities=identities)

    assert proof["proof_status"] == "unavailable"
    enumeration = next(
        item
        for item in proof["applicability_results"]
        if item["check_id"] == "candidate_enumeration_complete"
    )
    assert enumeration["completion_status"] == "unavailable"
    assert "Snapshot inventory digest" in enumeration["detail_code"]


def test_case_assignment_must_name_the_profile_selection_protocol(
    project_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root, tmp_path)
    assignment = freeze_protocol_artifact(
        "opaque_case_assignment",
        "case-assignment:different-protocol",
        "2026-07-30T17:03:00Z",
        {
            "selection_protocol_artifact_id": "selection-protocol:different",
            "selection_protocol_artifact_digest": inputs["selection"]["content_digest"],
            "selected_report_path": "report.md",
        },
    )

    with pytest.raises(StaticQualificationError, match="profile's frozen selection protocol"):
        _verify(inputs, assignment=assignment)

    digest_drift = freeze_protocol_artifact(
        "opaque_case_assignment",
        "case-assignment:protocol-digest-drift",
        "2026-07-30T17:03:00Z",
        {
            "selection_protocol_artifact_id": inputs["selection"]["artifact_id"],
            "selection_protocol_artifact_digest": "sha256:" + "0" * 64,
            "selected_report_path": "report.md",
        },
    )
    with pytest.raises(StaticQualificationError, match="profile's frozen selection protocol"):
        _verify(inputs, assignment=digest_drift)


def test_weak_identity_and_budget_exhaustion_are_unavailable(
    project_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root, tmp_path)
    identities = deepcopy(inputs["identities"])
    identities[0]["tier"] = "weak_fingerprint"
    weak = _verify(inputs, identities=identities)
    assert weak["proof_status"] == "unavailable"

    small_profile = freeze_bounded_direction_profile(
        inputs["detector"],
        inputs["parsers"],
        inputs["profiles"],
        inputs["versions"],
        inputs["selection"],
        frozen_at="2026-07-30T17:02:00Z",
        max_total_bytes=1,
    )
    over_budget = _verify(inputs, profile=small_profile)
    assert over_budget["proof_status"] == "unavailable"


def test_opposite_sibling_counterevidence_is_explicit(project_root: Path, tmp_path: Path) -> None:
    inputs = _inputs(project_root, tmp_path, opposite_sibling=True)
    proof = _verify(inputs)
    assert proof["proof_status"] == "complete"
    assert proof["counterevidence_results"][0]["outcome"] == "counterevidence_present"


def test_proof_replay_rejects_byte_drift_and_bad_chronology(
    project_root: Path, tmp_path: Path
) -> None:
    inputs = _inputs(project_root, tmp_path)
    proof = _verify(inputs)
    (inputs["workspace"] / "data.csv").write_text(
        "group,expression\ntreated,999\ncontrol,1\n", encoding="utf-8"
    )
    with pytest.raises(StaticQualificationError, match="does not replay"):
        revalidate_static_proof(
            proof,
            inputs["workspace"],
            inputs["profile"],
            inputs["assignment"],
            inputs["label"],
            inputs["snapshot"],
            inputs["files"],
            inputs["identities"],
            inputs["detector"],
            inputs["parsers"],
            inputs["profiles"],
            inputs["versions"],
        )
    with pytest.raises(StaticQualificationError, match="chronology"):
        _verify(inputs, proof_frozen_at="2026-07-30T17:03:30Z")


def test_isolated_verifier_does_not_import_production_fact_derivers(
    project_root: Path,
) -> None:
    source = (
        project_root / "evaluation" / "src" / "sc_referee_evaluation" / "static_qualification.py"
    ).read_text(encoding="utf-8")
    imported = {
        alias.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported.update(
        node.module or ""
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom)
    )
    assert not any(
        name.startswith(
            (
                "sc_referee.parsers",
                "sc_referee.detectors",
                "sc_referee.semantic",
                "sc_referee.records.observed",
            )
        )
        for name in imported
    )


def test_static_profile_and_proof_cli_are_replayable(project_root: Path, tmp_path: Path) -> None:
    inputs = _inputs(project_root, tmp_path)

    def write_object(name: str, value: dict[str, Any]) -> Path:
        path = tmp_path / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    detector = write_object("detector.json", inputs["detector"])
    selection = write_object("selection.json", inputs["selection"])
    parser_paths = [
        write_object(f"parser-{index}.json", value) for index, value in enumerate(inputs["parsers"])
    ]
    semantic_paths = [write_object("semantic-profile.json", inputs["profiles"][0])]
    version_paths = [write_object("version-manifest.json", inputs["versions"][0])]
    profile_path = tmp_path / "profile.json"
    profile_arguments = [
        "freeze-static-profile",
        "--detector-manifest",
        str(detector),
        "--selection-protocol-artifact",
        str(selection),
        "--frozen-at",
        "2026-07-30T17:02:00Z",
        "--output",
        str(profile_path),
    ]
    for path in parser_paths:
        profile_arguments.extend(["--parser-manifest", str(path)])
    for path in semantic_paths:
        profile_arguments.extend(["--semantic-profile-manifest", str(path)])
    for path in version_paths:
        profile_arguments.extend(["--version-manifest", str(path)])
    assert evaluation_main(profile_arguments) == 0
    assert json.loads(profile_path.read_text(encoding="utf-8")) == inputs["profile"]

    assignment = write_object("assignment.json", inputs["assignment"])
    label = write_object("label-artifact.json", inputs["label"])
    snapshot = write_object("snapshot.json", inputs["snapshot"])
    file_records = tmp_path / "files.jsonl"
    file_records.write_text(
        "".join(json.dumps(value) + "\n" for value in inputs["files"]),
        encoding="utf-8",
    )
    identities = tmp_path / "identities.jsonl"
    identities.write_text(
        "".join(json.dumps(value) + "\n" for value in inputs["identities"]),
        encoding="utf-8",
    )
    proof_path = tmp_path / "proof.json"
    proof_arguments = [
        "verify-static-case",
        "--materialized-root",
        str(inputs["workspace"]),
        "--profile",
        str(profile_path),
        "--detector-manifest",
        str(detector),
        "--case-assignment-artifact",
        str(assignment),
        "--label-freeze-artifact",
        str(label),
        "--snapshot",
        str(snapshot),
        "--file-records-jsonl",
        str(file_records),
        "--asset-identities-jsonl",
        str(identities),
        "--proof-frozen-at",
        "2026-07-30T17:05:00Z",
        "--output",
        str(proof_path),
    ]
    for path in parser_paths:
        proof_arguments.extend(["--parser-manifest", str(path)])
    for path in semantic_paths:
        proof_arguments.extend(["--semantic-profile-manifest", str(path)])
    for path in version_paths:
        proof_arguments.extend(["--version-manifest", str(path)])
    assert evaluation_main(proof_arguments) == 0
    assert json.loads(proof_path.read_text(encoding="utf-8")) == _verify(inputs)
