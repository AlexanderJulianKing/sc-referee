from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_three_case_stage1_protocol import CASE_IDS, VISIBLE_FILES
from scripts.build_first_direct_three_case_stage1_semantic_recovery_protocol import (
    ACTIVE_REVIEWERS,
    AGGREGATE_CALIBRATION_LEDGER_DIGEST,
    CODEX_RETRY_AMENDMENT_DIGEST,
    RECOVERY_AMENDMENT_DIGEST,
    REPLACEMENT_AMENDMENT_DIGEST,
    REVIEW_RELATIVE,
    SEMANTIC_RECOVERY_INSTRUCTION,
    SOURCE_INELIGIBILITY_LEDGER_DIGEST,
    SOURCE_PANEL_LEDGER_DIGEST,
    SOURCE_PROTOCOL_DIGEST,
    build_first_direct_three_case_stage1_semantic_recovery_protocol,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = PROJECT_ROOT / REVIEW_RELATIVE


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(path: Path, digest_field: str) -> dict[str, Any]:
    record = _load(path)
    supplied = record.pop(digest_field)
    assert supplied == semantic_digest(record)
    record[digest_field] = supplied
    return record


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_semantic_recovery_protocol_binds_recovery_chain_and_exact_v1_workspaces() -> None:
    protocol = _replay(REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json", "protocol_digest")
    assert protocol["source_v1_stage1_protocol_digest"] == SOURCE_PROTOCOL_DIGEST
    assert protocol["source_v1_stage1_panel_ledger_digest"] == SOURCE_PANEL_LEDGER_DIGEST
    assert (
        protocol["source_v1_label_ineligibility_ledger_digest"]
        == SOURCE_INELIGIBILITY_LEDGER_DIGEST
    )
    assert protocol["semantic_recovery_amendment_digest"] == RECOVERY_AMENDMENT_DIGEST
    assert protocol["codex_calibration_retry_amendment_digest"] == CODEX_RETRY_AMENDMENT_DIGEST
    assert protocol["claude_replacement_amendment_digest"] == REPLACEMENT_AMENDMENT_DIGEST
    assert (
        protocol["aggregate_recovery_calibration_ledger_digest"]
        == AGGREGATE_CALIBRATION_LEDGER_DIGEST
    )
    assert _timestamp(protocol["frozen_at"]) > _timestamp("2026-08-05T07:48:30Z")
    assert protocol["execution_state"] == "frozen_not_started"
    assert protocol["stage1_review_count"] == protocol["stage1_freeze_count"] == 0
    assert protocol["stage2_review_count"] == protocol["scientific_label_count"] == 0
    assert protocol["detector_outcome_count"] == 0
    assert protocol["case_ids"] == CASE_IDS
    assert protocol["workspace_reuse"] == {
        "source_visible_bytes_reused_exactly": True,
        "source_workspace_bytes_copied": False,
        "source_workspace_bytes_regenerated": False,
        "source_workspace_manifests_reused_exactly": True,
    }
    assert not (REVIEW_ROOT / "case-preparations").exists()

    expected_paths = sorted(str(item["path"]) for item in VISIBLE_FILES)
    bindings = {str(item["case_id"]): item for item in protocol["source_case_bindings"]}
    assert set(bindings) == set(CASE_IDS)
    for case_id, binding in bindings.items():
        manifest_path = PROJECT_ROOT / binding["source_workspace_manifest_relative_path"]
        workspace_root = PROJECT_ROOT / binding["source_workspace_relative_path"]
        manifest = _replay(manifest_path, "manifest_digest")
        assert manifest["manifest_digest"] == binding["source_workspace_manifest_digest"]
        actual = {
            str(item["path"]): sha256_digest((workspace_root / str(item["path"])).read_bytes())
            for item in manifest["files"]
        }
        assert sorted(actual) == expected_paths
        assert actual == binding["visible_content_digests"]
        assert binding["workspace_bytes_reused_without_copy"] is True
        assert case_id == f"case:{manifest_path.parent.name}"


def test_semantic_recovery_protocol_has_four_calibrated_calls_and_twelve_exact_packets() -> None:
    protocol = _load(REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json")
    assert [str(item["participant_id"]) for item in protocol["calls"]] == ACTIVE_REVIEWERS
    assert {str(item["participant"]["provider"]) for item in protocol["calls"]} == {
        "Anthropic",
        "OpenAI",
    }
    packet_paths: set[str] = set()
    for call in protocol["calls"]:
        assert SEMANTIC_RECOVERY_INSTRUCTION in call["prompt"]
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
        assert len(call["packet_refs"]) == 3
        assert len(call["capture_destinations"]) == 3
        for ref in call["packet_refs"]:
            packet_paths.add(str(ref["relative_path"]))
            packet = _replay(REVIEW_ROOT / str(ref["relative_path"]), "packet_digest")
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
    for item in protocol["controller_implementation"]:
        assert sha256_digest((PROJECT_ROOT / item["path"]).read_bytes()) == item["content_digest"]


def test_semantic_recovery_protocol_builder_is_write_once() -> None:
    protocol_path = REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json"
    before = sha256_digest(protocol_path.read_bytes())
    with pytest.raises(ValueError, match="already exists"):
        build_first_direct_three_case_stage1_semantic_recovery_protocol(PROJECT_ROOT)
    assert sha256_digest(protocol_path.read_bytes()) == before
