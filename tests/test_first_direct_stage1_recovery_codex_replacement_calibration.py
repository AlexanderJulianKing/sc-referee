from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_stage1_recovery_calibration import (
    CALIBRATION_RELATIVE as SOURCE_CALIBRATION_RELATIVE,
)
from scripts.build_first_direct_stage1_recovery_codex_replacement_calibration import (
    CALIBRATION_SUITE_DIGEST,
    CONFIGURATION_FIELDS,
    EXPECTED_CALIBRATION_VERDICTS,
    FROZEN_AT,
    REPLACEMENT_CONTEXTS,
    REPLACEMENT_RELATIVE,
    SOURCE_CALIBRATION_PROTOCOL_DIGEST,
    SOURCE_DUPLICATE_FAILURE_LEDGER_DIGEST,
    SOURCE_PARTICIPANTS,
    SOURCE_RECOVERY_AMENDMENT_DIGEST,
    build_first_direct_stage1_recovery_codex_replacement_calibration,
)

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


def test_two_codex_replacement_calibration_is_frozen_before_calls() -> None:
    assert SOURCE_DUPLICATE_FAILURE_LEDGER_DIGEST is not None
    assert SOURCE_RECOVERY_AMENDMENT_DIGEST is not None
    enrollment = _replay(REPLACEMENT_ROOT / "PARTICIPANT_ENROLLMENT.json", "enrollment_digest")
    protocol = _replay(REPLACEMENT_ROOT / "CALIBRATION_PROTOCOL.json", "protocol_digest")
    amendment = _replay(REPLACEMENT_ROOT / "REPLACEMENT_AMENDMENT.json", "amendment_digest")

    assert enrollment["source_duplicate_launch_failure_ledger_digest"] == (
        SOURCE_DUPLICATE_FAILURE_LEDGER_DIGEST
    )
    assert enrollment["source_duplicate_launch_recovery_amendment_digest"] == (
        SOURCE_RECOVERY_AMENDMENT_DIGEST
    )
    assert enrollment["participant_count"] == 2
    assert enrollment["provider_participation"] == {"OpenAI": 2}
    assert enrollment["fresh_participant_identities"] is True
    assert enrollment["fresh_execution_contexts"] is True
    assert enrollment["frozen_at"] == FROZEN_AT

    participant_ids = [str(item["participant_id"]) for item in enrollment["participants"]]
    contexts = [str(item["execution_context_id"]) for item in enrollment["participants"]]
    assert participant_ids == list(SOURCE_PARTICIPANTS)
    assert contexts == [REPLACEMENT_CONTEXTS[item] for item in participant_ids]
    assert len(contexts) == len(set(contexts)) == 2
    for participant in enrollment["participants"]:
        supplied = participant.pop("configuration_digest")
        assert supplied == semantic_digest(participant)
        participant["configuration_digest"] = supplied

    assert protocol["source_calibration_protocol_digest"] == SOURCE_CALIBRATION_PROTOCOL_DIGEST
    assert protocol["calibration_suite_digest"] == CALIBRATION_SUITE_DIGEST
    assert protocol["expected_verdicts"] == EXPECTED_CALIBRATION_VERDICTS
    assert protocol["source_vignette_count"] == 6
    assert protocol["scientific_vignettes_unchanged"] is True
    assert protocol["expected_verdicts_unchanged"] is True
    assert protocol["output_schema_unchanged_except_participant_const"] is True
    assert protocol["execution_state"] == "frozen_not_started"
    assert protocol["attempt_count"] == protocol["pass_count"] == 0
    assert protocol["scientific_label_count"] == protocol["detector_outcome_count"] == 0
    assert amendment["source_duplicate_launch_failure_ledger_digest"] == (
        SOURCE_DUPLICATE_FAILURE_LEDGER_DIGEST
    )
    assert amendment["source_duplicate_launch_recovery_amendment_digest"] == (
        SOURCE_RECOVERY_AMENDMENT_DIGEST
    )
    assert amendment["replacement_count"] == 2
    assert amendment["duplicate_launch_attempts_retained_without_repair"] is True
    assert amendment["source_scientific_responses_not_reused"] is True
    assert amendment["calibration_required_before_scientific_participation"] is True
    assert amendment["scientific_label_count"] == amendment["detector_outcome_count"] == 0


def test_two_codex_replacement_calibration_attempts_are_retained_and_pass() -> None:
    ledger = _replay(REPLACEMENT_ROOT / "CALIBRATION_LEDGER.json", "ledger_digest")
    assert (
        ledger["ledger_digest"]
        == "sha256:a4b68cbe07aaba3237a805d5ce0df2aa4554b859f9efee371e382960fcc4de90"
    )
    assert ledger["summary"] == {
        "all_assigned_attempts_retained": True,
        "all_reviewer_configurations_passed": True,
        "assigned_reviewer_count": 2,
        "failed_count": 0,
        "passed_count": 2,
        "replacement_count": 0,
        "retained_attempt_count": 2,
    }
    assert [item["participant_id"] for item in ledger["entries"]] == list(SOURCE_PARTICIPANTS)
    for entry in ledger["entries"]:
        assert entry["calibration_status"] == "passed"
        assert entry["calibration_evaluation"]["pass"] is True
        assert entry["calibration_evaluation"]["structured_output_schema_valid"] is True
        assert entry["calibration_evaluation"]["exact_expected_verdict_count"] == 6
    assert ledger["scientific_label_count"] == 0
    assert ledger["detector_outcome_count"] == 0


def test_two_codex_replacements_reuse_only_the_v5_scientific_calibration_contract() -> None:
    source_protocol = _replay(
        PROJECT_ROOT / SOURCE_CALIBRATION_RELATIVE / "CALIBRATION_PROTOCOL.json",
        "protocol_digest",
    )
    assert source_protocol["protocol_digest"] == SOURCE_CALIBRATION_PROTOCOL_DIGEST
    source_assignments = {
        str(item["participant_id"]): item for item in source_protocol["assignments"]
    }
    enrollment = _load(REPLACEMENT_ROOT / "PARTICIPANT_ENROLLMENT.json")
    participants = {str(item["participant_id"]): item for item in enrollment["participants"]}
    protocol = _load(REPLACEMENT_ROOT / "CALIBRATION_PROTOCOL.json")
    assignments = {str(item["participant_id"]): item for item in protocol["assignments"]}

    assert set(assignments) == set(SOURCE_PARTICIPANTS)
    for participant_id, source_id in SOURCE_PARTICIPANTS.items():
        replacement = assignments[participant_id]
        source = source_assignments[source_id]
        participant = participants[participant_id]
        assert replacement["source_participant_id"] == source_id
        assert replacement["source_assignment_digest"] == semantic_digest(source)
        assert replacement["source_configuration_digest"] == source["configuration_digest"]
        for field in CONFIGURATION_FIELDS:
            assert participant[field] == source[field]
            assert replacement[field] == participant[field]
        assert participant["participant_id"] == participant_id
        assert participant["execution_context_id"] == REPLACEMENT_CONTEXTS[participant_id]
        assert participant["configuration_digest"] != source["configuration_digest"]

        assert _schema_without_participant_const(replacement["output_schema"]) == (
            _schema_without_participant_const(source["output_schema"])
        )
        assert replacement["output_schema_digest"] == semantic_digest(replacement["output_schema"])
        assert replacement["prompt_digest"] == sha256_digest(str(replacement["prompt"]))
        replacement_body = str(replacement["prompt"]).split(PROMPT_BOUNDARY, 1)[0]
        source_body = str(source["prompt"]).split(PROMPT_BOUNDARY, 1)[0]
        assert replacement_body.replace(participant_id, source_id) == source_body
        assert replacement["interaction_profile"] == source["interaction_profile"]


def test_two_codex_replacement_calibration_builder_is_write_once() -> None:
    before = {
        path.name: sha256_digest(path.read_bytes()) for path in REPLACEMENT_ROOT.glob("*.json")
    }
    with pytest.raises(FileExistsError, match="already frozen"):
        build_first_direct_stage1_recovery_codex_replacement_calibration(PROJECT_ROOT)
    assert before == {
        path.name: sha256_digest(path.read_bytes()) for path in REPLACEMENT_ROOT.glob("*.json")
    }
