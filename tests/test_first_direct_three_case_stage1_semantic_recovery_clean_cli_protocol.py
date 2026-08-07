from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_stage1_recovery_claude_cli_replacement_calibration import (
    REPLACEMENT_RELATIVE as V8_CALIBRATION_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol import (
    ACTIVE_REVIEWERS,
    CASE_IDS,
    CLAUDE_CLI_INTERACTION_PROFILE,
    CLAUDE_REVIEWERS,
    CODEX_REVIEWERS,
    REVIEW_RELATIVE,
    SOURCE_REVIEW_RELATIVE,
    SOURCE_REVIEWERS,
    SOURCE_V3_PROTOCOL_DIGEST,
    V8_LEDGER_DIGEST,
    build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = PROJECT_ROOT / REVIEW_RELATIVE
PROMPT_SCHEMA_MARKER = "\n\nReturn only one unfenced JSON object matching this exact schema:\n"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replayed_protocol() -> dict[str, Any]:
    protocol = _load(REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json")
    supplied = protocol.pop("protocol_digest")
    assert supplied == semantic_digest(protocol)
    protocol["protocol_digest"] = supplied
    return protocol


def test_clean_cli_stage1_protocol_is_frozen_before_calls() -> None:
    protocol = _replayed_protocol()
    assert (
        protocol["artifact_kind"]
        == "direct_qualification_three_case_stage1_semantic_recovery_clean_cli_protocol"
    )
    assert protocol["protocol_version"] == "4.0.0"
    assert protocol["execution_state"] == "frozen_not_started"
    assert protocol["source_v3_stage1_protocol_digest"] == SOURCE_V3_PROTOCOL_DIGEST
    assert protocol["v8_claude_cli_replacement_calibration_ledger_digest"] == V8_LEDGER_DIGEST
    assert protocol["case_ids"] == CASE_IDS
    assert protocol["stage1_review_count"] == 0
    assert protocol["stage1_freeze_count"] == 0
    assert protocol["stage2_review_count"] == 0
    assert protocol["scientific_label_count"] == 0
    assert protocol["detector_outcome_count"] == 0
    assert [item["participant_id"] for item in protocol["calls"]] == ACTIVE_REVIEWERS
    call_ids = [str(item["call_identity_id"]) for item in protocol["calls"]]
    assert len(call_ids) == len(set(call_ids)) == 4
    transition = protocol["participant_transition"]
    assert transition["preserved_unexecuted_v3_codex_participant_ids"] == sorted(CODEX_REVIEWERS)
    assert transition["fresh_v8_participant_ids"] == sorted(CLAUDE_REVIEWERS)
    assert transition["superseded_v3_claude_participant_ids"] == sorted(
        SOURCE_REVIEWERS[item] for item in CLAUDE_REVIEWERS
    )
    for item in protocol["controller_implementation"]:
        path = PROJECT_ROOT / str(item["path"])
        assert sha256_digest(path.read_bytes()) == item["content_digest"]


def test_clean_cli_stage1_calls_bind_exact_configurations_and_prompts() -> None:
    protocol = _replayed_protocol()
    source_protocol = _load(PROJECT_ROOT / SOURCE_REVIEW_RELATIVE / "STAGE1_REVIEW_PROTOCOL.json")
    source_calls = {str(item["participant_id"]): item for item in source_protocol["calls"]}
    source_call_ids = {str(item["call_identity_id"]) for item in source_protocol["calls"]}
    v8_enrollment = _load(PROJECT_ROOT / V8_CALIBRATION_RELATIVE / "PARTICIPANT_ENROLLMENT.json")
    v8_configs = {str(item["participant_id"]): item for item in v8_enrollment["participants"]}

    for call in protocol["calls"]:
        participant_id = str(call["participant_id"])
        source_call = source_calls[SOURCE_REVIEWERS[participant_id]]
        assert call["call_identity_id"] not in source_call_ids
        assert call["prompt_digest"] == sha256_digest(str(call["prompt"]))
        assert call["output_schema_digest"] == semantic_digest(call["output_schema"])
        assert (
            call["output_schema"]["properties"]["reviewer_participant_id"]["const"]
            == participant_id
        )
        assert call["case_order"] == source_call["case_order"]
        for ref in call["packet_refs"]:
            packet = _load(REVIEW_ROOT / str(ref["relative_path"]))
            supplied = packet.pop("packet_digest")
            assert supplied == semantic_digest(packet)
        if participant_id in CLAUDE_REVIEWERS:
            config = v8_configs[participant_id]
            assert call["participant_configuration_digest"] == config["configuration_digest"]
            assert call["participant"]["agent_surface"] == "Claude Code CLI"
            assert call["participant"]["agent_version"] == "2.1.221"
            assert call["participant"]["model_id"] == "claude-opus-5"
            assert call["participant"]["reasoning_configuration"] == "high"
            assert call["calibration_ledger_digest"] == V8_LEDGER_DIGEST
            assert call["interaction_profile"] == CLAUDE_CLI_INTERACTION_PROFILE
            body = str(call["prompt"]).split(PROMPT_SCHEMA_MARKER, 1)[0]
            source_body = str(source_call["prompt"]).split(PROMPT_SCHEMA_MARKER, 1)[0]
            assert body.replace(participant_id, SOURCE_REVIEWERS[participant_id]) == source_body
        else:
            assert (
                call["participant_configuration_digest"]
                == source_call["participant_configuration_digest"]
            )
            assert call["participant"] == source_call["participant"]
            assert call["prompt"] == source_call["prompt"]
            assert call["output_schema"] == source_call["output_schema"]
            assert call["interaction_profile"] == source_call["interaction_profile"]
            assert call["calibration_ledger_digest"] == source_call["calibration_ledger_digest"]
            assert call["calibration_entry_digest"] == source_call["calibration_entry_digest"]


def test_clean_cli_stage1_claude_calls_are_recorded_and_label_eligible_per_review() -> None:
    expected_ledgers = {
        "actor:stage1-recovery-claude-04": (
            "sha256:da5c90dc9cf02ef3418601a3ac539dbfc81912ceabb4a89b54b9495daae65f83"
        ),
        "actor:stage1-recovery-claude-05": (
            "sha256:7cce51f846ccd077a78237c886f10068f16028a296f5769972304b4d231827e5"
        ),
    }
    expected_verdicts = {
        "case:2e26bf5ece15be03717f": "no_demonstrated_issue_within_scope",
        "case:35069763f06891dba5a3": "demonstrated_issue",
        "case:b036fd64c647dfd93e35": "no_demonstrated_issue_within_scope",
    }
    for participant_id, expected_digest in expected_ledgers.items():
        slug = participant_id.removeprefix("actor:")
        ledger = _load(REVIEW_ROOT / "stage1-call-ledgers" / f"{slug}.json")
        supplied = ledger.pop("ledger_digest")
        assert supplied == semantic_digest(ledger) == expected_digest
        ledger["ledger_digest"] = supplied
        assert ledger["participant_id"] == participant_id
        assert ledger["review_count"] == 3
        assert ledger["scientific_label_count"] == 0
        assert ledger["detector_outcome_count"] == 0
        assert {
            str(item["case_id"]): str(item["verdict"]) for item in ledger["entries"]
        } == expected_verdicts
        for entry in ledger["entries"]:
            case_slug = str(entry["case_id"]).removeprefix("case:")
            review = _load(REVIEW_ROOT / "stage1-captures" / case_slug / slug / "review.json")
            assert review["unresolved_material_questions"] == []
            assert semantic_digest(review) == entry["review_digest"]


def test_clean_cli_stage1_protocol_builder_is_write_once() -> None:
    before = sha256_digest((REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json").read_bytes())
    with pytest.raises(FileExistsError, match="already exists"):
        build_first_direct_three_case_stage1_semantic_recovery_clean_cli_protocol(PROJECT_ROOT)
    assert before == sha256_digest((REVIEW_ROOT / "STAGE1_REVIEW_PROTOCOL.json").read_bytes())
