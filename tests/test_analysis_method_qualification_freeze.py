from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from sc_referee_evaluation.analysis_method_qualification import (
    AnalysisMethodQualificationError,
)
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.founder_orientation_adapter import (
    FounderOrientationQualificationAdapter,
    founder_orientation_dependency_closure,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_analysis_method_qualification_freeze import build_qualification_freeze
from scripts.build_typed_method_qualification_freeze import (
    FROZEN_BINDING_SOURCE_DIGEST,
    build_typed_method_qualification_freeze,
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in _keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in _keys(item)}
    return set()


def test_typed_pre_case_freeze_is_current_exact_and_answer_blind(
    project_root: Path,
) -> None:
    frozen = (
        project_root
        / "evaluation"
        / "qualification"
        / "bounded-analysis-method-conflict-v0.2.0-precase"
    )
    manifest = _load(frozen / "FREEZE_MANIFEST.json")
    expected_files = {
        "FREEZE_MANIFEST.json",
        "detector-manifest.json",
        "method-conflict-binding.json",
        "parser-manifest.markdown.json",
        "parser-manifest.python.json",
        "selection-protocol.json",
        "semantic-profile-manifest.json",
        "stage1-prompt-semantic-consistency-v2.txt",
        "stage1-prompt.txt",
        "stage2-prompt.txt",
        "stage3-prompt.txt",
        "static-qualification-profile.json",
        "version-manifest.json",
    }
    assert {path.name for path in frozen.iterdir()} == expected_files

    profile = _load(frozen / "static-qualification-profile.json")
    detector = _load(frozen / "detector-manifest.json")
    binding = _load(frozen / "method-conflict-binding.json")
    protocol = _load(frozen / "selection-protocol.json")
    LocalSchemaRegistry(project_root / "reference" / "schemas-v0.17.0").validate(profile)
    assert profile["schema_version"] == "0.17.0"
    assert profile["profile_kind"] == "typed_static_method_conflict_v1"
    assert detector["detector_version"] == "0.2.0"
    assert profile["target_detector"]["detector_version"] == "0.2.0"  # type: ignore[index]
    assert profile["method_binding"] == binding

    digest_basis = deepcopy(binding)
    supplied_binding_digest = digest_basis.pop("binding_digest")
    assert supplied_binding_digest == semantic_digest(digest_basis)
    adapter = FounderOrientationQualificationAdapter()
    qualification_adapter = binding["qualification_adapter"]
    assert isinstance(qualification_adapter, dict)
    assert qualification_adapter["adapter_id"] == adapter.adapter_id
    assert qualification_adapter["implementation_digest"] == adapter.implementation_digest
    assert qualification_adapter["dependency_closure"] == list(
        founder_orientation_dependency_closure()
    )

    payload = protocol["payload"]
    assert isinstance(payload, dict)
    assert payload["case_assignment_status"] == "not_started"
    assert payload["promotion_eligible"] is False
    assert payload["finding_permission"] is False
    assert payload["project_code_execution"] is False
    assert payload["post_assignment_case_replacement"] is False
    assert not {
        "case_id",
        "reviewer_agent",
        "reviewer_identity",
        "scientific_label",
        "detector_output",
        "transcript",
    } & _keys(protocol)

    inventory = manifest["inventory"]
    assert isinstance(inventory, list)
    # The manifest inventory is immutable freeze-time evidence; the later retained
    # Stage-1 semantic-consistency v2 prompt lives in the directory but is not part
    # of the original frozen tuple.
    assert [entry["path"] for entry in inventory] == sorted(
        expected_files - {"FREEZE_MANIFEST.json", "stage1-prompt-semantic-consistency-v2.txt"}
    )
    assert manifest["inventory_digest"] == semantic_digest(inventory)
    binding_source = manifest["binding_source"]
    assert isinstance(binding_source, dict)
    assert binding_source["content_digest"] == FROZEN_BINDING_SOURCE_DIGEST
    current_registry = (
        project_root
        / "src"
        / "sc_referee"
        / "resources"
        / "scientific-check-manifests-v1"
        / "registry.json"
    )
    assert sha256_digest(current_registry.read_bytes()) != FROZEN_BINDING_SOURCE_DIGEST
    for entry in inventory:
        assert isinstance(entry, dict)
        path = frozen / str(entry["path"])
        assert entry["content_digest"] == sha256_digest(path.read_bytes())
        assert entry["size_bytes"] == path.stat().st_size


def test_typed_pre_case_builder_fails_closed_after_active_registry_migration(
    project_root: Path, tmp_path: Path
) -> None:
    output = tmp_path / "bounded-analysis-method-conflict-v0.2.0-precase"
    with pytest.raises(ValueError, match="frozen qualification binding has drifted"):
        build_typed_method_qualification_freeze(project_root, output)
    assert not output.exists()


def test_typed_pre_case_cli_rebuilds_profile_and_assigns_without_label(
    project_root: Path, tmp_path: Path
) -> None:
    frozen = (
        project_root
        / "evaluation"
        / "qualification"
        / "bounded-analysis-method-conflict-v0.2.0-precase"
    )
    profile_output = tmp_path / "typed-profile.json"
    assert (
        evaluation_main(
            [
                "freeze-typed-method-static-profile",
                "--method-binding",
                str(frozen / "method-conflict-binding.json"),
                "--detector-manifest",
                str(frozen / "detector-manifest.json"),
                "--parser-manifest",
                str(frozen / "parser-manifest.markdown.json"),
                "--parser-manifest",
                str(frozen / "parser-manifest.python.json"),
                "--semantic-profile-manifest",
                str(frozen / "semantic-profile-manifest.json"),
                "--version-manifest",
                str(frozen / "version-manifest.json"),
                "--selection-protocol-artifact",
                str(frozen / "selection-protocol.json"),
                "--candidate-suffix",
                ".md",
                "--candidate-suffix",
                ".py",
                "--frozen-at",
                "2026-07-31T18:35:00Z",
                "--output",
                str(profile_output),
            ]
        )
        == 0
    )
    profile = _load(profile_output)
    assert profile["schema_version"] == "0.19.0"
    assert (
        profile_output.read_bytes() != (frozen / "static-qualification-profile.json").read_bytes()
    )
    LocalSchemaRegistry(project_root / "reference" / "schemas-v0.19.0").validate(profile)

    assignment_output = tmp_path / "typed-assignment.json"
    assert (
        evaluation_main(
            [
                "assign-typed-method-static-case",
                "--profile",
                str(profile_output),
                "--case-id",
                "case:typed-readiness:1",
                "--selected-report",
                "report.md",
                "--assigned-at",
                "2026-07-31T18:36:00Z",
                "--output",
                str(assignment_output),
            ]
        )
        == 0
    )
    assignment = _load(assignment_output)
    protocol = _load(frozen / "selection-protocol.json")
    assert assignment["artifact_kind"] == "opaque_case_assignment"
    assert assignment["payload"] == {
        "case_id": "case:typed-readiness:1",
        "selected_report_path": "report.md",
        "selection_protocol_artifact_digest": protocol["content_digest"],
        "selection_protocol_artifact_id": protocol["artifact_id"],
    }
    assert "label" not in json.dumps(assignment).casefold()


def test_pre_case_qualification_freeze_is_exact_and_nonpromoting(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    del schema_root, tmp_path
    frozen = (
        project_root
        / "evaluation"
        / "qualification"
        / "bounded-analysis-method-conflict-v0.1.0-readiness-pilot"
    )
    first_manifest = _load(frozen / "FREEZE_MANIFEST.json")

    expected_files = {
        "FREEZE_MANIFEST.json",
        "detector-manifest.json",
        "parser-manifest.markdown.json",
        "parser-manifest.python.json",
        "selection-protocol.json",
        "semantic-profile-manifest.json",
        "stage1-prompt.txt",
        "stage2-prompt.txt",
        "stage3-prompt.txt",
        "static-qualification-profile.json",
        "version-manifest.json",
    }
    assert {path.name for path in frozen.iterdir()} == expected_files

    profile = _load(frozen / "static-qualification-profile.json")
    protocol = _load(frozen / "selection-protocol.json")
    LocalSchemaRegistry(project_root / "reference" / "schemas-v0.16.0").validate(profile)
    assert profile["profile_kind"] == "bounded_analysis_method_conflict_v1"
    assert protocol["artifact_kind"] == "corpus_selection_protocol"
    payload = protocol["payload"]
    assert isinstance(payload, dict)
    assert payload["promotion_eligible"] is False
    assert payload["post_assignment_case_replacement"] is False
    assert payload["project_code_execution"] is False
    assert "case_id" not in json.dumps(protocol)

    inventory = first_manifest["inventory"]
    assert isinstance(inventory, list)
    assert [entry["path"] for entry in inventory] == sorted(
        expected_files - {"FREEZE_MANIFEST.json"}
    )
    assert first_manifest["inventory_digest"] == semantic_digest(inventory)
    for entry in inventory:
        assert isinstance(entry, dict)
        path = frozen / str(entry["path"])
        assert entry["content_digest"] == sha256_digest(path.read_bytes())
        assert entry["size_bytes"] == path.stat().st_size


def test_superseded_readiness_builder_rejects_current_detector(
    project_root: Path, tmp_path: Path
) -> None:
    rebuilt = tmp_path / "rebuilt"
    with pytest.raises(AnalysisMethodQualificationError):
        build_qualification_freeze(project_root, rebuilt)
    assert not rebuilt.exists()


def test_case_assignment_cli_binds_frozen_protocol_before_any_label(
    project_root: Path, tmp_path: Path
) -> None:
    frozen = (
        project_root
        / "evaluation"
        / "qualification"
        / "bounded-analysis-method-conflict-v0.1.0-readiness-pilot"
    )
    output = tmp_path / "assignment.json"
    assert (
        evaluation_main(
            [
                "assign-analysis-method-static-case",
                "--profile",
                str(frozen / "static-qualification-profile.json"),
                "--case-id",
                "case:readiness:1",
                "--selected-report",
                "report.md",
                "--assigned-at",
                "2026-07-31T08:01:00Z",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assignment = _load(output)
    protocol = _load(frozen / "selection-protocol.json")
    assert assignment["artifact_kind"] == "opaque_case_assignment"
    payload = assignment["payload"]
    assert isinstance(payload, dict)
    assert payload == {
        "case_id": "case:readiness:1",
        "selected_report_path": "report.md",
        "selection_protocol_artifact_digest": protocol["content_digest"],
        "selection_protocol_artifact_id": protocol["artifact_id"],
    }
    assert "label" not in json.dumps(assignment).casefold()

    assert (
        evaluation_main(
            [
                "assign-analysis-method-static-case",
                "--profile",
                str(frozen / "static-qualification-profile.json"),
                "--case-id",
                "case:too-early",
                "--selected-report",
                "report.md",
                "--assigned-at",
                "2026-07-31T08:00:00Z",
                "--output",
                str(tmp_path / "too-early.json"),
            ]
        )
        == 2
    )
