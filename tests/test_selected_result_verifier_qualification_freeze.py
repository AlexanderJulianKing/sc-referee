from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_selected_result_verifier_qualification_freeze import (
    TARGET_PROFILE_DIGEST,
    TARGET_SOURCE_DIGEST,
    build_selected_result_verifier_qualification_freeze,
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


def test_committed_pre_case_freeze_is_exact_answer_blind_and_non_authoritative(
    project_root: Path,
) -> None:
    frozen = (
        project_root / "evaluation" / "qualification" / "selected-result-verifier-v1.0.0-precase"
    )
    expected_files = {
        "FREEZE_MANIFEST.json",
        "case-author-prompt.txt",
        "oracle-validator-prompt.txt",
        "qualification-profile.json",
        "selection-protocol.json",
        "target-runner-prompt.txt",
    }
    assert {path.name for path in frozen.iterdir()} == expected_files

    manifest = _load(frozen / "FREEZE_MANIFEST.json")
    profile = _load(frozen / "qualification-profile.json")
    protocol = _load(frozen / "selection-protocol.json")
    assert manifest["target_implementation_digest"] == TARGET_SOURCE_DIGEST
    target = profile["target_verifier"]
    assert isinstance(target, dict)
    assert target["selected_result_profile_digest"] == TARGET_PROFILE_DIGEST
    assert target["module"]["content_digest"] == TARGET_SOURCE_DIGEST  # type: ignore[index]
    assert profile["qualification_authority"] == "none_precase_profile_only"
    oracle = profile["independent_oracle"]
    assert isinstance(oracle, dict)
    assert oracle["qualification_authority"] == "none_tooling_only"

    payload = protocol["payload"]
    assert isinstance(payload, dict)
    assert payload["assignment_status"] == "not_started"
    assert payload["case_replacement"] is False
    assert payload["finding_permission"] is False
    assert payload["scientific_detector_qualification"] is False
    assert payload["cases_per_block"] == 48
    assert sum(item["count"] for item in payload["block_matrix"]) == 48  # type: ignore[union-attr]
    assert not {
        "case_id",
        "assignment_id",
        "target_output",
        "oracle_proof",
        "comparison",
        "qualification_decision",
    } & _keys(protocol)

    inventory = manifest["inventory"]
    assert isinstance(inventory, list)
    assert [entry["path"] for entry in inventory] == sorted(
        expected_files - {"FREEZE_MANIFEST.json"}
    )
    assert manifest["inventory_digest"] == semantic_digest(inventory)
    for entry in inventory:
        assert isinstance(entry, dict)
        path = frozen / str(entry["path"])
        assert entry["content_digest"] == sha256_digest(path.read_bytes())
        assert entry["size_bytes"] == path.stat().st_size


def test_invalidated_v1_freeze_cannot_be_rebuilt_from_changed_target(
    project_root: Path, tmp_path: Path
) -> None:
    rebuilt = tmp_path / "freeze"
    with pytest.raises(ValueError, match="implementation has drifted"):
        build_selected_result_verifier_qualification_freeze(project_root, rebuilt)
    assert not rebuilt.exists()


def test_v1_target_lock_is_historical_and_oracle_import_firewall_is_live(
    project_root: Path,
) -> None:
    target = (
        project_root
        / "evaluation"
        / "src"
        / "sc_referee_evaluation"
        / "prospective_selected_result_verifier.py"
    )
    oracle = (
        project_root
        / "evaluation"
        / "src"
        / "sc_referee_evaluation"
        / "selected_result_qualification_oracle.py"
    )
    assert sha256_digest(target.read_bytes()) != TARGET_SOURCE_DIGEST
    source = oracle.read_text(encoding="utf-8")
    assert "prospective_selected_result_verifier" not in source
    assert "prospective_qualification_v2" not in source
    imported_modules = {
        node.module
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module is not None
    } | {
        alias.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not {
        module
        for module in imported_modules
        if module == "sc_referee" or module.startswith("sc_referee.")
    }
    assert "import ast" not in source


def test_builder_rejects_target_implementation_drift(project_root: Path, tmp_path: Path) -> None:
    copied = tmp_path / "project"
    target_relative = Path(
        "evaluation/src/sc_referee_evaluation/prospective_selected_result_verifier.py"
    )
    oracle_relative = Path(
        "evaluation/src/sc_referee_evaluation/selected_result_qualification_oracle.py"
    )
    (copied / target_relative).parent.mkdir(parents=True)
    (copied / target_relative).write_bytes(
        (project_root / target_relative).read_bytes() + b"\n# drift\n"
    )
    (copied / oracle_relative).write_bytes((project_root / oracle_relative).read_bytes())

    with pytest.raises(ValueError, match="implementation has drifted"):
        build_selected_result_verifier_qualification_freeze(copied, tmp_path / "freeze")
