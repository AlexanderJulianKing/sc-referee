from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.prospective_study_scaffold import (
    ProspectiveStudyScaffoldError,
    build_prospective_study_scaffold,
    write_study_scaffold_once,
)

from sc_referee.core.ids import semantic_digest, sha256_digest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = (
    ROOT / "evaluation" / "prospective-qualification-v1" / "ten-envelope-study.template.json"
)
AUTHORING_TEMPLATE_PATH = (
    ROOT
    / "evaluation"
    / "prospective-qualification-v1"
    / "benchmark-blind-authoring-briefs.template.json"
)


def test_standalone_scaffold_cli_bootstraps_checkout_imports() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_prospective_study_scaffold.py"), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "--authoring-template" in completed.stdout


def _digest(value: str) -> str:
    return sha256_digest(value)


def _participant(identifier: str, role: str, provider: str) -> dict[str, str]:
    return {
        "participant_id": identifier,
        "role": role,
        "provider": provider,
        "execution_context_id": f"context:{identifier}",
        "identity_evidence_digest": _digest(f"identity:{identifier}"),
    }


def _template() -> dict[str, Any]:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


def _authoring_template() -> dict[str, Any]:
    return json.loads(AUTHORING_TEMPLATE_PATH.read_text(encoding="utf-8"))


def _setup() -> dict[str, Any]:
    participants = [
        _participant("actor:pilot-primary", "author", "author-provider-a"),
        _participant("actor:pilot-rewrite", "author", "author-provider-b"),
        _participant("actor:heldout-primary", "author", "author-provider-c"),
        _participant("actor:heldout-rewrite", "author", "author-provider-d"),
        _participant("actor:s1-a1", "stage1_reviewer", "review-provider-a"),
        _participant("actor:s1-a2", "stage1_reviewer", "review-provider-a"),
        _participant("actor:s1-b1", "stage1_reviewer", "review-provider-b"),
        _participant("actor:s1-b2", "stage1_reviewer", "review-provider-b"),
        _participant("actor:s2-c", "stage2_reviewer", "review-provider-c"),
        _participant("actor:s2-d", "stage2_reviewer", "review-provider-d"),
        _participant("actor:detector", "detector_implementer", "implementation-provider"),
    ]
    return {
        "study_id": "study:prospective-ten-envelope-v1",
        "protocol_id": "prospective-protocol:ten-envelope-v1",
        "template_digest": _template()["template_digest"],
        "authoring_template_digest": _authoring_template()["template_digest"],
        "detector_lock": {
            "detector_id": "detector:generic-method-conflict",
            "detector_version": "0.3.0",
            "detector_manifest_digest": _digest("detector-manifest"),
            "implementation_digest": _digest("detector-implementation"),
            "frozen_at": "2026-08-04T12:00:00Z",
        },
        "participants": participants,
        "block_assignments": [
            {
                "block_id": "block:pilot",
                "evidence_role": "threshold_pilot",
                "primary_author_ids": ["actor:pilot-primary"],
                "renamed_author_ids": ["actor:pilot-rewrite"],
                "submission_deadline": "2026-08-05T12:00:00Z",
                "submission_channel": "channel:author-submission-a",
            },
            {
                "block_id": "block:heldout",
                "evidence_role": "qualification_heldout",
                "primary_author_ids": ["actor:heldout-primary"],
                "renamed_author_ids": ["actor:heldout-rewrite"],
                "submission_deadline": "2026-08-06T12:00:00Z",
                "submission_channel": "channel:author-submission-b",
            },
        ],
        "stage1_reviewer_ids": [
            "actor:s1-a1",
            "actor:s1-a2",
            "actor:s1-b1",
            "actor:s1-b2",
        ],
        "stage2_reviewer_ids": ["actor:s2-c", "actor:s2-d"],
        "case_id_key": "7a" * 32,
        "assigned_at": "2026-08-04T12:30:00Z",
        "protocol_frozen_at": "2026-08-04T13:00:00Z",
    }


def _json(files: dict[str, bytes], path: str) -> dict[str, Any]:
    return json.loads(files[path])


def _build(setup: dict[str, Any] | None = None) -> dict[str, bytes]:
    return build_prospective_study_scaffold(
        _template(), _authoring_template(), _setup() if setup is None else setup
    )


def test_scaffold_builds_complete_role_separated_assignment_package() -> None:
    files = _build()
    protocol = _json(files, "coordinator/protocol.json")
    manifest = _json(files, "PACKAGE_MANIFEST.json")

    assert protocol["coverage"]["required_case_count"] == 140
    assert protocol["study_state"] == "assignments_frozen_labels_unopened"
    assert protocol["qualification_authority"] == "none_protocol_only"
    assert manifest["case_counts"] == {
        "total": 140,
        "threshold_pilot": 70,
        "qualification_heldout": 70,
    }
    assert manifest["contains_case_material"] is False
    assert manifest["contains_scientific_labels"] is False
    assert manifest["contains_review_decisions"] is False
    assert manifest["contains_detector_observations"] is False
    assert manifest["contains_threshold_decision"] is False

    assignments = protocol["assignments"]
    assert len({assignment["case_id"] for assignment in assignments}) == 140
    for block_id in ("block:pilot", "block:heldout"):
        block = [assignment for assignment in assignments if assignment["block_id"] == block_id]
        assert len(block) == 70
        assert (
            len({(assignment["envelope_id"], assignment["cell_type"]) for assignment in block})
            == 70
        )
        for envelope_id in {assignment["envelope_id"] for assignment in block}:
            family = [
                assignment for assignment in block if assignment["envelope_id"] == envelope_id
            ]
            error = next(item for item in family if item["cell_type"] == "error_bearing")
            corrected = next(item for item in family if item["cell_type"] == "corrected_twin")
            renamed = next(item for item in family if item["cell_type"] == "renamed_implementation")
            assert corrected["reference_case_id"] == error["case_id"]
            assert corrected["author_id"] == error["author_id"]
            assert renamed["reference_case_id"] == error["case_id"]
            assert renamed["author_id"] != error["author_id"]

    assert any(path.startswith("releases/pilot/authors/") for path in files)
    assert not any(path.startswith("releases/heldout/") for path in files)
    assert any(path.startswith("coordinator/staged-heldout/authors/") for path in files)


def test_blind_review_queues_exclude_cell_relation_and_brief_content() -> None:
    files = _build()
    reviewer_paths = [path for path in files if "reviewers/" in path]
    assert reviewer_paths
    for path in reviewer_paths:
        queue = _json(files, path)
        serialized = json.dumps(queue, sort_keys=True)
        assert len(queue["case_ids"]) == 70
        assert "designed_cell" not in serialized
        assert "cell_type" not in serialized
        assert "envelope_id" not in serialized
        assert "required_method" not in serialized
        assert "case_instruction" not in serialized


def test_authoring_briefs_are_descriptive_but_create_no_case_or_outcome_evidence() -> None:
    files = _build()
    brief_paths = [path for path in files if path.startswith("coordinator/authoring-briefs/")]
    assert len(brief_paths) == 140
    cells: set[str] = set()
    for path in brief_paths:
        brief = _json(files, path)
        declared = brief.pop("brief_digest")
        assert semantic_digest(brief) == declared
        cells.add(str(brief["one_cell_brief"]["cell_type"]))
        assert brief["one_cell_brief"]["author_task"]
        assert brief["one_relation_brief"]["governed_premise"]
        assert brief["one_relation_brief"]["contrasting_construction"]
        assert brief["qualification_authority"] == "none_authoring_instruction_only"
        if brief["one_cell_brief"]["cell_type"] == "renamed_implementation":
            assert brief["paired_case_access"] == {
                "reference_case_id": None,
                "access_rule": "none",
            }
        if brief["one_cell_brief"]["cell_type"] == "corrected_twin":
            assert brief["paired_case_access"]["reference_case_id"].startswith("case:")
    assert cells == {
        "error_bearing",
        "corrected_twin",
        "valid_alternative",
        "hard_negative",
        "ambiguous",
        "unsupported",
        "renamed_implementation",
    }
    author_payloads = [
        payload
        for path, payload in files.items()
        if path.startswith("releases/pilot/authors/")
        or path.startswith("coordinator/staged-heldout/authors/")
    ]
    combined = b"".join(author_payloads).lower()
    for forbidden in (
        b'"block_id"',
        b'"evidence_role"',
        b'"blind_envelope_id"',
        b'"check_id"',
        b'"candidate_id"',
        b'"binding_digest"',
        b'"scientific_label"',
        b'"detector_observation"',
        b'"outcomes"',
        b'"promotion_thresholds"',
        b"threshold_pilot",
        b"qualification_heldout",
    ):
        assert forbidden not in combined


def test_scaffold_is_deterministic_and_case_key_changes_opaque_ids() -> None:
    first = _build()
    second = _build()
    assert first == second

    changed_setup = _setup()
    changed_setup["case_id_key"] = "8b" * 32
    changed = _build(changed_setup)
    first_protocol = _json(first, "coordinator/protocol.json")
    changed_protocol = _json(changed, "coordinator/protocol.json")
    assert {item["case_id"] for item in first_protocol["assignments"]}.isdisjoint(
        {item["case_id"] for item in changed_protocol["assignments"]}
    )


def test_scaffold_rejects_reused_heldout_author_and_reviewer_provider_collapse() -> None:
    reused = _setup()
    reused["block_assignments"][1]["primary_author_ids"] = ["actor:pilot-primary"]
    with pytest.raises(ProspectiveStudyScaffoldError, match="disjoint author"):
        _build(reused)

    one_provider = _setup()
    for participant in one_provider["participants"]:
        if participant["role"] == "stage1_reviewer":
            participant["provider"] = "one-review-provider"
    with pytest.raises(ProspectiveStudyScaffoldError, match="Stage-1 must span"):
        _build(one_provider)


def test_write_is_once_only_and_preserves_package_bytes(tmp_path: Path) -> None:
    files = _build()
    output = tmp_path / "study"
    assert write_study_scaffold_once(output, files) == output.resolve()
    for relative, payload in files.items():
        assert (output / relative).read_bytes() == payload
    with pytest.raises(ProspectiveStudyScaffoldError, match="already exists"):
        write_study_scaffold_once(output, files)


def test_setup_does_not_mutate_and_case_key_is_not_copied_into_package() -> None:
    setup = _setup()
    before = deepcopy(setup)
    files = _build(setup)
    assert setup == before
    combined = b"".join(files.values())
    assert setup["case_id_key"].encode("ascii") not in combined
