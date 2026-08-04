from __future__ import annotations

import json
from pathlib import Path

import pytest

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_selected_result_verifier_runner_freeze import (
    CONTROLLER_DIGEST,
    build_selected_result_verifier_runner_freeze,
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_runner_freeze_binds_controller_assignments_and_blind_target_input(
    project_root: Path,
) -> None:
    study = project_root / "evaluation" / "qualification" / "selected-result-verifier-v1.0.0-study"
    value = _load(study / "runner-freeze.json")
    basis = dict(value)
    supplied = basis.pop("runner_freeze_digest")
    assert supplied == semantic_digest(basis)
    controller = value["controller_module"]
    assert isinstance(controller, dict)
    assert controller["content_digest"] == CONTROLLER_DIGEST
    assert sha256_digest((project_root / str(controller["path"])).read_bytes()) == CONTROLLER_DIGEST
    assert value["target_outputs_present"] is False
    assert value["qualification_authority"] == "none_runner_freeze_only"
    forbidden = value["target_input_forbidden"]
    assert isinstance(forbidden, list)
    assert {
        "construction_certificate",
        "oracle_state",
        "reason_codes",
        "positive_binding",
        "cell_label",
    }.issubset(forbidden)


def test_runner_freeze_rebuilds_and_never_overwrites(project_root: Path, tmp_path: Path) -> None:
    qualification = project_root / "evaluation" / "qualification"
    pre_case = qualification / "selected-result-verifier-v1.0.0-precase"
    study = qualification / "selected-result-verifier-v1.0.0-study"
    rebuilt = tmp_path / "runner-freeze.json"
    build_selected_result_verifier_runner_freeze(
        project_root,
        pre_case,
        study / "opaque-assignments.json",
        rebuilt,
    )
    assert rebuilt.read_bytes() == (study / "runner-freeze.json").read_bytes()
    with pytest.raises(FileExistsError):
        build_selected_result_verifier_runner_freeze(
            project_root,
            pre_case,
            study / "opaque-assignments.json",
            rebuilt,
        )
