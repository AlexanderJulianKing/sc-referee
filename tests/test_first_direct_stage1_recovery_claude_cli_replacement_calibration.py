from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_stage1_recovery_calibration import (
    CALIBRATION_RELATIVE as V5_CALIBRATION_RELATIVE,
)
from scripts.build_first_direct_stage1_recovery_claude_cli_replacement_calibration import (
    CALIBRATION_SUITE_DIGEST,
    CLEAN_STAGE1_PROTOCOL_DIGEST,
    COMMAND_PROFILE,
    EXPECTED_CALIBRATION_VERDICTS,
    FROZEN_AT,
    OBSOLETE_CLEAN_STAGE1_CLAUDE_CALL_IDS,
    REPLACEMENT_CONTEXTS,
    REPLACEMENT_RELATIVE,
    SUPERSEDED_BY_REPLACEMENT,
    TEMPLATE_BY_REPLACEMENT,
    V5_LEDGER_DIGEST,
    V6_LEDGER_DIGEST,
    build_first_direct_stage1_recovery_claude_cli_replacement_calibration,
)
from scripts.build_first_direct_stage1_recovery_claude_replacement_calibration import (
    REPLACEMENT_RELATIVE as V6_CALIBRATION_RELATIVE,
)
from scripts.build_first_direct_three_case_stage1_protocol import LANE_RELATIVE

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPLACEMENT_ROOT = PROJECT_ROOT / REPLACEMENT_RELATIVE
PROMPT_BOUNDARY = "Return only one JSON object"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(path: Path, field: str) -> dict[str, Any]:
    record = _load(path)
    supplied = record.pop(field)
    assert supplied == semantic_digest(record)
    record[field] = supplied
    return record


def _schema_without_participant_const(schema: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(schema)
    normalized["properties"]["reviewer_participant_id"]["const"] = "actor:normalized"
    return normalized


def test_claude_cli_replacement_calibration_is_frozen_before_calls() -> None:
    enrollment = _replay(REPLACEMENT_ROOT / "PARTICIPANT_ENROLLMENT.json", "enrollment_digest")
    protocol = _replay(REPLACEMENT_ROOT / "CALIBRATION_PROTOCOL.json", "protocol_digest")
    amendment = _replay(REPLACEMENT_ROOT / "REPLACEMENT_AMENDMENT.json", "amendment_digest")

    assert enrollment["participant_count"] == 2
    assert enrollment["provider_participation"] == {"Anthropic": 2}
    assert enrollment["superseded_participant_ids"] == sorted(SUPERSEDED_BY_REPLACEMENT.values())
    assert enrollment["fresh_participant_identities"] is True
    assert enrollment["fresh_execution_contexts"] is True
    assert enrollment["frozen_at"] == FROZEN_AT

    participant_ids = [str(item["participant_id"]) for item in enrollment["participants"]]
    contexts = [str(item["execution_context_id"]) for item in enrollment["participants"]]
    assert participant_ids == sorted(SUPERSEDED_BY_REPLACEMENT)
    assert contexts == [REPLACEMENT_CONTEXTS[item] for item in participant_ids]
    assert len(contexts) == len(set(contexts)) == 2
    for participant in enrollment["participants"]:
        supplied = participant.pop("configuration_digest")
        assert supplied == semantic_digest(participant)
        participant["configuration_digest"] = supplied
        assert participant["provider"] == "Anthropic"
        assert participant["agent_surface"] == "Claude Code CLI"
        assert participant["agent_version"] == "2.1.221"
        assert participant["model_id"] == "claude-opus-5"
        assert participant["reasoning_configuration"] == "high"
        assert participant["role"] == "stage1_reviewer"
        assert participant["calibration_status"] == "required_before_participation"
        assert participant["calibration_suite_digest"] == CALIBRATION_SUITE_DIGEST

    assert protocol["calibration_suite_digest"] == CALIBRATION_SUITE_DIGEST
    assert protocol["expected_verdicts"] == EXPECTED_CALIBRATION_VERDICTS
    assert protocol["source_vignette_count"] == 6
    assert protocol["scientific_vignettes_unchanged"] is True
    assert protocol["expected_verdicts_unchanged"] is True
    assert protocol["output_schema_unchanged_except_participant_const"] is True
    assert protocol["prompt_unchanged_except_participant_identity"] is True
    assert protocol["execution_state"] == "frozen_not_started"
    assert protocol["attempt_count"] == protocol["pass_count"] == 0
    assert protocol["scientific_label_count"] == protocol["detector_outcome_count"] == 0
    call_ids = [str(item["call_identity_id"]) for item in protocol["assignments"]]
    assert len(call_ids) == len(set(call_ids)) == 2
    for assignment in protocol["assignments"]:
        assert assignment["command_profile"] == COMMAND_PROFILE

    assert amendment["source_clean_stage1_protocol_digest"] == CLEAN_STAGE1_PROTOCOL_DIGEST
    assert amendment["obsolete_clean_stage1_claude_call_identity_ids"] == sorted(
        OBSOLETE_CLEAN_STAGE1_CLAUDE_CALL_IDS
    )
    assert amendment["clean_stage1_calls_executed_before_amendment"] == 0
    assert amendment["case_exposure_before_amendment"] is False
    assert amendment["source_v5_calibration_ledger_digest"] == V5_LEDGER_DIGEST
    assert amendment["source_v6_calibration_ledger_digest"] == V6_LEDGER_DIGEST
    assert amendment["replacement_count"] == 2
    assert amendment["superseded_configurations_retained_without_repair"] is True
    assert amendment["superseded_pass_evidence_not_reused"] is True
    assert amendment["reviewer_system_prompt_unchanged"] is True
    assert amendment["provider_and_model_family_unchanged"] is True
    assert amendment["maintainer_directed"] is True
    assert amendment["calibration_required_before_scientific_participation"] is True
    assert amendment["replacement_stage1_protocol_required_before_review"] is True
    assert amendment["scientific_label_count"] == amendment["detector_outcome_count"] == 0


def test_claude_cli_replacements_reuse_the_superseded_scientific_contract() -> None:
    v5_protocol = _load(PROJECT_ROOT / V5_CALIBRATION_RELATIVE / "CALIBRATION_PROTOCOL.json")
    v6_protocol = _load(PROJECT_ROOT / V6_CALIBRATION_RELATIVE / "CALIBRATION_PROTOCOL.json")
    source_assignments = {
        str(item["participant_id"]): item
        for item in [*v5_protocol["assignments"], *v6_protocol["assignments"]]
    }
    lane_enrollment = _load(PROJECT_ROOT / LANE_RELATIVE / "PARTICIPANT_ENROLLMENT.json")
    templates = {str(item["participant_id"]): item for item in lane_enrollment["participants"]}
    enrollment = _load(REPLACEMENT_ROOT / "PARTICIPANT_ENROLLMENT.json")
    participants = {str(item["participant_id"]): item for item in enrollment["participants"]}
    protocol = _load(REPLACEMENT_ROOT / "CALIBRATION_PROTOCOL.json")
    assignments = {str(item["participant_id"]): item for item in protocol["assignments"]}

    assert set(assignments) == set(SUPERSEDED_BY_REPLACEMENT)
    for participant_id, superseded_id in SUPERSEDED_BY_REPLACEMENT.items():
        replacement = assignments[participant_id]
        source = source_assignments[superseded_id]
        participant = participants[participant_id]
        template = templates[TEMPLATE_BY_REPLACEMENT[participant_id]]
        assert replacement["superseded_participant_id"] == superseded_id
        assert replacement["superseded_assignment_digest"] == semantic_digest(source)
        assert replacement["superseded_configuration_digest"] == source["configuration_digest"]
        for field in (
            "agent_surface",
            "agent_version",
            "model_id",
            "model_name",
            "reasoning_configuration",
            "system_prompt_digest",
            "tool_policy_digest",
            "environment_digest",
        ):
            assert participant[field] == template[field]
            assert replacement[field] == participant[field]
        assert participant["system_prompt_digest"] == source["system_prompt_digest"]
        assert participant["execution_context_id"] == REPLACEMENT_CONTEXTS[participant_id]
        assert participant["configuration_digest"] != source["configuration_digest"]
        assert participant["configuration_digest"] != template["configuration_digest"]

        assert _schema_without_participant_const(replacement["output_schema"]) == (
            _schema_without_participant_const(source["output_schema"])
        )
        assert replacement["output_schema_digest"] == semantic_digest(replacement["output_schema"])
        assert replacement["prompt_digest"] == sha256_digest(str(replacement["prompt"]))
        replacement_body = str(replacement["prompt"]).split(PROMPT_BOUNDARY, 1)[0]
        source_body = str(source["prompt"]).split(PROMPT_BOUNDARY, 1)[0]
        assert replacement_body.replace(participant_id, superseded_id) == source_body


def test_claude_cli_replacement_calibration_builder_is_write_once() -> None:
    before = {
        path.name: sha256_digest(path.read_bytes()) for path in REPLACEMENT_ROOT.glob("*.json")
    }
    with pytest.raises(FileExistsError, match="already frozen"):
        build_first_direct_stage1_recovery_claude_cli_replacement_calibration(PROJECT_ROOT)
    assert before == {
        path.name: sha256_digest(path.read_bytes()) for path in REPLACEMENT_ROOT.glob("*.json")
    }
