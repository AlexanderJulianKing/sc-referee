from __future__ import annotations

import json
from pathlib import Path

import pytest

from sc_referee.core.ids import semantic_digest
from scripts.build_selected_result_verifier_v1_1_assignments import (
    build_selected_result_verifier_v1_1_assignments,
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_v1_1_assignments_are_new_label_free_and_self_digested(
    project_root: Path,
) -> None:
    qualification = project_root / "evaluation" / "qualification"
    current = _load(
        qualification / "selected-result-verifier-v1.1.0-study" / "opaque-assignments.json"
    )
    prior = _load(
        qualification / "selected-result-verifier-v1.0.0-study" / "opaque-assignments.json"
    )
    supplied = current.pop("assignment_digest")
    assert supplied == semantic_digest(current)
    current["assignment_digest"] = supplied
    assert current["assignment_version"] == "1.1.0"
    assert current["case_count"] == 96
    assert current["case_bytes_present"] is False
    assert current["oracle_states_present"] is False
    assert current["cell_labels_present"] is False
    assert current["semantic_attestations_present"] is False
    assert current["target_outputs_present"] is False

    def case_ids(value: dict[str, object]) -> set[str]:
        blocks = value["blocks"]
        assert isinstance(blocks, list)
        return {
            str(assignment["case_id"]) for block in blocks for assignment in block["assignments"]
        }

    assert len(case_ids(current)) == 96
    assert case_ids(current).isdisjoint(case_ids(prior))


def test_v1_1_assignments_rebuild_and_never_overwrite(project_root: Path, tmp_path: Path) -> None:
    qualification = project_root / "evaluation" / "qualification"
    contract = (
        qualification / "selected-result-verifier-v1.1.0-precase" / "semantic-review-contract.json"
    )
    frozen = qualification / "selected-result-verifier-v1.1.0-study" / "opaque-assignments.json"
    rebuilt = tmp_path / "opaque-assignments.json"
    build_selected_result_verifier_v1_1_assignments(contract, rebuilt)
    assert rebuilt.read_bytes() == frozen.read_bytes()
    with pytest.raises(FileExistsError):
        build_selected_result_verifier_v1_1_assignments(contract, rebuilt)
