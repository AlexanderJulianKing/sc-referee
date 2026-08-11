from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import sc_referee_evaluation.complete_domain_replay_at_head as replay_at_head
from sc_referee_evaluation.complete_domain_replay_at_head import (
    CHECK_ID,
    REPLAY_ARTIFACT_NAME,
    REPLAY_OUTPUT_RELATIVE,
    REPLAY_PURPOSE,
    CompleteDomainHeadReplayError,
    build_complete_domain_replay_at_head,
    load_complete_domain_replay_at_head,
)

from sc_referee.core.ids import canonical_json


def test_retained_head_replay_is_digest_bound_nonblind_and_seven_of_seven(
    project_root: Path,
) -> None:
    artifact = load_complete_domain_replay_at_head(
        project_root / REPLAY_OUTPUT_RELATIVE / REPLAY_ARTIFACT_NAME
    )

    assert artifact["purpose"] == REPLAY_PURPOSE
    assert artifact["non_blind"] is True
    assert artifact["fresh_examination_claimed"] is False
    assert artifact["qualification_authority"] == "none_drift_ruling_evidence_only"
    assert artifact["project_authored_code_executed"] is False
    assert artifact["case_count"] == 7
    assert artifact["agreement_count"] == 7
    assert artifact["all_cases_agree"] is True
    assert artifact["current_production_finding_count"] == 0
    assert artifact["current_project_code_execution_count"] == 0
    assert artifact["head_identity"]["check_id"] == CHECK_ID
    assert artifact["head_identity"]["drift_from_sealed_adapter"] == {
        "implementation_digest_changed": True,
        "manifest_digest_changed": True,
        "recognition_grammar_digest_changed": False,
    }
    assert all(entry["agreement"] is True for entry in artifact["entries"])
    assert all(entry["mismatch_fields"] == [] for entry in artifact["entries"])


def test_retained_head_replay_preserves_all_case_outcomes_across_v019_identity_drift(
    project_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact_path = project_root / REPLAY_OUTPUT_RELATIVE / REPLAY_ARTIFACT_NAME
    expected = load_complete_domain_replay_at_head(artifact_path)

    # The retained artifact's writer remains strict about a clean HEAD. This
    # regression deliberately replays proposed controller bytes before the
    # orchestrator commit, then compares every substantive field while
    # excluding only the expected commit-id change.
    monkeypatch.setattr(replay_at_head, "_require_audit_paths_at_head", lambda _root: None)
    replayed = build_complete_domain_replay_at_head(
        project_root,
        tmp_path / "runs",
        recorded_at=str(expected["recorded_at"]),
    )

    replay_payload = deepcopy(replayed)
    expected_payload = deepcopy(expected)
    replay_payload.pop("semantic_digest")
    expected_payload.pop("semantic_digest")
    replay_payload.pop("replay_harness_implementation_digest")
    expected_payload.pop("replay_harness_implementation_digest")
    replay_payload["head_identity"].pop("git_head_commit")
    expected_payload["head_identity"].pop("git_head_commit")
    current_registry_digest = replay_payload["head_identity"].pop("registry_content_digest")
    retained_registry_digest = expected_payload["head_identity"].pop("registry_content_digest")
    assert current_registry_digest != retained_registry_digest
    assert replay_payload == expected_payload


def test_replay_loader_refuses_digest_drift(project_root: Path, tmp_path: Path) -> None:
    artifact_path = project_root / REPLAY_OUTPUT_RELATIVE / REPLAY_ARTIFACT_NAME
    value = json.loads(artifact_path.read_text(encoding="utf-8"))
    value["all_cases_agree"] = False
    drifted = tmp_path / REPLAY_ARTIFACT_NAME
    drifted.write_text(canonical_json(value) + "\n", encoding="utf-8")

    with pytest.raises(CompleteDomainHeadReplayError, match="digest"):
        load_complete_domain_replay_at_head(drifted)
