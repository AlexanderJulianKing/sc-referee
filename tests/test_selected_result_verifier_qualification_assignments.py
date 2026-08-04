from __future__ import annotations

import json
from pathlib import Path

import pytest

from sc_referee.core.ids import semantic_digest
from scripts.build_selected_result_verifier_qualification_assignments import (
    build_selected_result_verifier_qualification_assignments,
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_assignments_are_complete_unique_label_free_and_no_replacement(
    project_root: Path,
) -> None:
    value = _load(
        project_root
        / "evaluation"
        / "qualification"
        / "selected-result-verifier-v1.0.0-study"
        / "opaque-assignments.json"
    )
    digest_basis = dict(value)
    supplied_digest = digest_basis.pop("assignment_digest")
    assert supplied_digest == semantic_digest(digest_basis)
    assert value["case_count"] == 96
    assert value["case_replacement_permitted"] is False
    assert value["case_bytes_present"] is False
    assert value["oracle_states_present"] is False
    assert value["cell_labels_present"] is False
    assert value["oracle_proofs_present"] is False
    assert value["target_outputs_present"] is False
    assert value["qualification_authority"] == "none_assignment_only"

    blocks = value["blocks"]
    assert isinstance(blocks, list)
    assert [item["block"] for item in blocks] == ["pilot", "held_out"]
    identities: set[str] = set()
    for block in blocks:
        assignments = block["assignments"]
        assert len(assignments) == 48
        assert [item["assignment_position"] for item in assignments] == list(range(1, 49))
        providers = [item["provider_slot"] for item in assignments]
        assert providers.count("provider-family-1") == 24
        assert providers.count("provider-family-2") == 24
        for assignment in assignments:
            assert assignment["case_replacement_permitted"] is False
            case_id = assignment["case_id"]
            assert isinstance(case_id, str) and len(case_id) == 25 and case_id.startswith("case:")
            assert case_id not in identities
            identities.add(case_id)
            target_packet = assignment["target_packet"]
            assert set(target_packet) == {"case_id", "profile_id", "selected_report_path"}
            assert target_packet["case_id"] == case_id
    assert len(identities) == 96
    serialized = json.dumps(value).casefold()
    for forbidden in (
        "author_cell",
        "expected_state",
        'oracle_state"',
        "reason_code",
        "positive_binding",
        'target_output"',
    ):
        assert forbidden not in serialized


def test_assignment_builder_replays_and_refuses_overwrite(
    project_root: Path, tmp_path: Path
) -> None:
    freeze_root = (
        project_root / "evaluation" / "qualification" / "selected-result-verifier-v1.0.0-precase"
    )
    committed = (
        project_root
        / "evaluation"
        / "qualification"
        / "selected-result-verifier-v1.0.0-study"
        / "opaque-assignments.json"
    )
    rebuilt = tmp_path / "opaque-assignments.json"
    build_selected_result_verifier_qualification_assignments(freeze_root, rebuilt)
    assert rebuilt.read_bytes() == committed.read_bytes()
    with pytest.raises(FileExistsError):
        build_selected_result_verifier_qualification_assignments(freeze_root, rebuilt)
