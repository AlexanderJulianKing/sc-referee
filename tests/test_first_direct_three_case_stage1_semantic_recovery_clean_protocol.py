from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pytest
from sc_referee_evaluation.review_semantic_payload_v2 import (
    build_stage1_batch_output_schema_v2,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_protocol import (
    ACTIVE_REVIEWERS,
    CALIBRATION_RELATIVE,
    CANONICAL_ISSUE_CLASS,
    CASE_IDS,
    CLAUDE_REVIEWERS,
    CODEX_REVIEWERS,
    DUPLICATE_FAILURE_LEDGER_DIGEST,
    DUPLICATE_RECOVERY_AMENDMENT_DIGEST,
    PROMPT_SCHEMA_MARKER,
    REVIEW_RELATIVE,
    SOURCE_REVIEW_RELATIVE,
    SOURCE_REVIEWERS,
    SOURCE_V2_PROTOCOL_DIGEST,
    V7_AMENDMENT_DIGEST,
    V7_ENROLLMENT_DIGEST,
    V7_LEDGER_DIGEST,
    V7_PROTOCOL_DIGEST,
    VISIBLE_FILES,
    build_first_direct_three_case_stage1_semantic_recovery_clean_protocol,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = PROJECT_ROOT / REVIEW_RELATIVE
SOURCE_REVIEW_ROOT = PROJECT_ROOT / SOURCE_REVIEW_RELATIVE
CALIBRATION_ROOT = PROJECT_ROOT / CALIBRATION_RELATIVE


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(path: Path, field: str) -> dict[str, Any]:
    record = _load(path)
    supplied = record.pop(field)
    assert supplied == semantic_digest(record)
    record[field] = supplied
    return record


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _schema_without_participant_const(schema: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(schema)
    normalized["properties"]["reviewer_participant_id"]["const"] = "actor:normalized"
    return normalized


def test_clean_protocol_binds_complete_recovery_chain_and_exact_v1_workspaces() -> None:
    protocol = _replay(REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json", "protocol_digest")
    assert protocol["source_v2_stage1_protocol_digest"] == SOURCE_V2_PROTOCOL_DIGEST
    assert protocol["duplicate_launch_failure_ledger_digest"] == (DUPLICATE_FAILURE_LEDGER_DIGEST)
    assert protocol["duplicate_launch_recovery_amendment_digest"] == (
        DUPLICATE_RECOVERY_AMENDMENT_DIGEST
    )
    assert protocol["v7_codex_replacement_enrollment_digest"] == V7_ENROLLMENT_DIGEST
    assert protocol["v7_codex_replacement_calibration_protocol_digest"] == V7_PROTOCOL_DIGEST
    assert protocol["v7_codex_replacement_amendment_digest"] == V7_AMENDMENT_DIGEST
    assert protocol["v7_codex_replacement_calibration_ledger_digest"] == V7_LEDGER_DIGEST
    v7_ledger = _load(CALIBRATION_ROOT / "CALIBRATION_LEDGER.json")
    assert _timestamp(protocol["frozen_at"]) > _timestamp(v7_ledger["sealed_at"])
    assert protocol["execution_state"] == "frozen_not_started"
    assert protocol["stage1_review_count"] == protocol["stage1_freeze_count"] == 0
    assert protocol["stage2_review_count"] == protocol["scientific_label_count"] == 0
    assert protocol["detector_outcome_count"] == 0
    assert protocol["case_ids"] == CASE_IDS
    assert protocol["canonical_issue_class_scope"] == CANONICAL_ISSUE_CLASS
    assert protocol["workspace_reuse"] == {
        "source_v1_visible_bytes_reused_exactly": True,
        "source_v1_workspace_bytes_copied": False,
        "source_v1_workspace_bytes_regenerated": False,
        "source_v1_workspace_manifests_reused_exactly": True,
    }
    assert not (REVIEW_ROOT / "case-preparations").exists()

    expected_paths = sorted(str(item["path"]) for item in VISIBLE_FILES)
    bindings = {str(item["case_id"]): item for item in protocol["source_case_bindings"]}
    assert set(bindings) == set(CASE_IDS)
    for binding in bindings.values():
        manifest_path = PROJECT_ROOT / binding["source_workspace_manifest_relative_path"]
        workspace_root = PROJECT_ROOT / binding["source_workspace_relative_path"]
        assert "pilot-scientific-review-v1-three-case" in manifest_path.parts
        manifest = _replay(manifest_path, "manifest_digest")
        actual = {
            str(item["path"]): sha256_digest((workspace_root / str(item["path"])).read_bytes())
            for item in manifest["files"]
        }
        assert sorted(actual) == expected_paths
        assert actual == binding["visible_content_digests"]
        assert manifest["manifest_digest"] == binding["source_workspace_manifest_digest"]


def test_clean_protocol_preserves_claude_and_maps_calibrated_codex_to_old_orders() -> None:
    protocol = _load(REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json")
    source = _load(SOURCE_REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json")
    source_calls = {str(item["participant_id"]): item for item in source["calls"]}
    calls = {str(item["participant_id"]): item for item in protocol["calls"]}
    assert list(calls) == ACTIVE_REVIEWERS
    assert set(calls) == CLAUDE_REVIEWERS | CODEX_REVIEWERS

    enrollment = _load(CALIBRATION_ROOT / "PARTICIPANT_ENROLLMENT.json")
    participants = {str(item["participant_id"]): item for item in enrollment["participants"]}
    calibration = _load(CALIBRATION_ROOT / "CALIBRATION_LEDGER.json")
    entries = {str(item["participant_id"]): item for item in calibration["entries"]}
    for participant_id, call in calls.items():
        source_call = source_calls[SOURCE_REVIEWERS[participant_id]]
        assert call["case_order"] == source_call["case_order"]
        assert call["interaction_profile"] == source_call["interaction_profile"]
        assert call["call_identity_id"] != source_call["call_identity_id"]
        if participant_id in CLAUDE_REVIEWERS:
            assert (
                call["participant_configuration_digest"]
                == source_call["participant_configuration_digest"]
            )
            assert call["participant"] == source_call["participant"]
            assert call["reviewer_agent_base"] == source_call["reviewer_agent_base"]
            assert call["prompt"] == source_call["prompt"]
            assert call["prompt_digest"] == source_call["prompt_digest"]
            assert call["output_schema"] == source_call["output_schema"]
            assert call["output_schema_digest"] == source_call["output_schema_digest"]
        else:
            enrolled = participants[participant_id]
            assert call["participant_configuration_digest"] == enrolled["configuration_digest"]
            assert call["participant"]["execution_context_id"] == enrolled["execution_context_id"]
            assert call["calibration_ledger_digest"] == V7_LEDGER_DIGEST
            assert call["calibration_entry_digest"] == semantic_digest(entries[participant_id])
            expected_schema = build_stage1_batch_output_schema_v2(
                participant_id,
                call["case_order"],
                CANONICAL_ISSUE_CLASS,
            )
            assert call["output_schema"] == expected_schema
            assert _schema_without_participant_const(call["output_schema"]) == (
                _schema_without_participant_const(source_call["output_schema"])
            )
            new_body = str(call["prompt"]).split(PROMPT_SCHEMA_MARKER, 1)[0]
            old_body = str(source_call["prompt"]).split(PROMPT_SCHEMA_MARKER, 1)[0]
            assert new_body.replace(participant_id, SOURCE_REVIEWERS[participant_id]) == old_body


def test_clean_protocol_uses_v2_eligible_schema_and_has_only_twelve_exact_packets() -> None:
    protocol = _load(REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json")
    packet_paths: set[str] = set()
    for call in protocol["calls"]:
        assert sha256_digest(call["prompt"]) == call["prompt_digest"]
        assert semantic_digest(call["output_schema"]) == call["output_schema_digest"]
        review_schema = call["output_schema"]["properties"]["reviews"]["items"]
        assert any(
            branch.get("then", {})
            .get("properties", {})
            .get("unresolved_material_questions", {})
            .get("maxItems")
            == 0
            for branch in review_schema["allOf"]
        )
        assert len(call["packet_refs"]) == len(CASE_IDS)
        assert len(call["capture_destinations"]) == len(CASE_IDS)
        for ref in call["packet_refs"]:
            relative_path = str(ref["relative_path"])
            packet_paths.add(relative_path)
            packet = _replay(REVIEW_ROOT / relative_path, "packet_digest")
            assert packet["packet_digest"] == ref["packet_digest"]
            assert packet["case_id"] == ref["case_id"]
            assert packet["prompt"]["prompt_digest"] == call["prompt_digest"]
            assert packet["expected_reviewer_agent"] == {
                **call["reviewer_agent_base"],
                "task_prompt_digest": call["prompt_digest"],
            }
            assert packet["workspace"]["manifest_digest"] == ref["source_workspace_manifest_digest"]
    assert len(packet_paths) == 12
    assert {
        path.relative_to(REVIEW_ROOT).as_posix()
        for path in (REVIEW_ROOT / "stage1-packets").glob("*/*.json")
    } == packet_paths
    assert {
        path.relative_to(REVIEW_ROOT).as_posix()
        for path in REVIEW_ROOT.rglob("*")
        if path.is_file()
    } == {"STAGE1_REVIEW_PROTOCOL.json", *packet_paths}
    for item in protocol["controller_implementation"]:
        assert sha256_digest((PROJECT_ROOT / item["path"]).read_bytes()) == item["content_digest"]


def test_clean_protocol_builder_is_write_once() -> None:
    protocol_path = REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json"
    before = sha256_digest(protocol_path.read_bytes())
    with pytest.raises(FileExistsError, match="already exists"):
        build_first_direct_three_case_stage1_semantic_recovery_clean_protocol(PROJECT_ROOT)
    assert sha256_digest(protocol_path.read_bytes()) == before
