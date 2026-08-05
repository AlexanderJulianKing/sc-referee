from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_reviewer_calibration_protocol import (
    ALLOWED_VERDICTS,
    CALIBRATION_RELATIVE,
    FAILED_CALIBRATION_RELATIVE,
    PARTIAL_CALIBRATION_RELATIVE,
    build_first_direct_reviewer_calibration_protocol,
    load_effective_execution_configuration,
)
from scripts.run_first_direct_reviewer_calibration import (
    _build_aggregate_ledger,
    validate_calibration_response,
)


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _expected(config: dict[str, Any]) -> dict[str, str]:
    return {
        str(item["calibration_case_id"]): str(item["expected_verdict"])
        for item in config["reviewer_calibration_suite"]["vignettes"]
    }


def _passing_response(participant_id: str, expected: dict[str, str]) -> dict[str, Any]:
    return {
        "reviewer_participant_id": participant_id,
        "calibration_results": [
            {
                "calibration_case_id": case_id,
                "verdict": verdict,
                "invented_material_premise": False,
                "evidence_basis": "stated_evidence_only",
                "rationale": "The verdict follows only from the stated scope and denominator evidence.",
            }
            for case_id, verdict in expected.items()
        ],
    }


def test_frozen_reviewer_calibration_protocol_rebuilds_exactly(project_root: Path) -> None:
    committed = _load(project_root / CALIBRATION_RELATIVE / "CALIBRATION_PROTOCOL.json")
    rebuilt = build_first_direct_reviewer_calibration_protocol(project_root)

    assert rebuilt == committed
    supplied = committed.pop("protocol_digest")
    assert supplied == semantic_digest(committed)
    assert committed["protocol_version"] == "3.0.0"
    assert committed["supersedes_protocol_digest"] == (
        "sha256:b2875a535a1cbf86dffb1fb696c3b05bbc28dd9b5d67a0d82cbb5ed881864aad"
    )
    assert committed["retained_partial_ledger_digest"] == (
        "sha256:253b3fa6283c91e66442a3c9fe42f9f100754bd9aeb4e88e53564c96288e2bf3"
    )
    assert committed["execution_state"] == "frozen_not_started"
    assert committed["qualification_authority"] == "none_calibration_protocol_only"


def test_reviewer_calibration_v3_binds_three_claude_calls_and_three_codex_passes(
    project_root: Path,
) -> None:
    protocol = build_first_direct_reviewer_calibration_protocol(project_root)
    enrollment = _load(
        project_root
        / "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/"
        "PARTICIPANT_ENROLLMENT.json"
    )
    by_id = {item["participant_id"]: item for item in enrollment["participants"]}
    assignments = protocol["assignments"]

    assert len(assignments) == 3
    assert Counter(item["role"] for item in assignments) == {
        "stage1_reviewer": 2,
        "stage2_reviewer": 1,
    }
    assert Counter(item["provider"] for item in assignments) == {"Anthropic": 3}
    assert len({item["call_identity_id"] for item in assignments}) == 3
    assert len(protocol["retained_pass_refs"]) == 3
    assert all(
        item["participant_id"].startswith("actor:stage") for item in protocol["retained_pass_refs"]
    )
    assert protocol["expected_reviewer_count"] == 3
    assert protocol["aggregate_reviewer_count"] == 6
    assert protocol["execution_policy"] == {
        "parallel_execution_permitted": True,
        "one_call_per_assignment": True,
        "replacement_permitted": False,
        "all_attempts_retained": True,
        "fresh_empty_working_directory_per_call": True,
        "tool_access_permitted": False,
        "external_information_access_permitted": False,
    }
    for assignment in assignments:
        participant = by_id[assignment["participant_id"]]
        assert assignment["configuration_digest"] == participant["configuration_digest"]
        assert assignment["system_prompt_digest"] == participant["system_prompt_digest"]
        assert assignment["tool_policy_digest"] == participant["tool_policy_digest"]
        assert assignment["user_prompt_digest"] == sha256_digest(assignment["user_prompt"])
        assert assignment["output_schema_digest"] == semantic_digest(assignment["output_schema"])
        assert assignment["requested_provider_session_id"] == assignment["call_identity_id"]
        assert "$schema" not in assignment["output_schema"]
        assert "expected_verdict" not in assignment["user_prompt"]
        assert set(
            assignment["output_schema"]["properties"]["calibration_results"]["items"]["properties"][
                "verdict"
            ]["enum"]
        ) == set(ALLOWED_VERDICTS)


def test_calibration_response_requires_every_exact_expected_verdict(
    project_root: Path,
) -> None:
    config = load_effective_execution_configuration(project_root)
    expected = _expected(config)
    assignment = build_first_direct_reviewer_calibration_protocol(project_root)["assignments"][0]
    response = _passing_response(assignment["participant_id"], expected)

    assert validate_calibration_response(response, assignment, expected) == {
        "structured_output_schema_valid": True,
        "calibration_case_set_complete": True,
        "exact_expected_verdict_count": 6,
        "invented_material_premise_count": 0,
        "pass": True,
        "reason_codes": [],
    }

    wrong = json.loads(json.dumps(response))
    wrong["calibration_results"][0]["verdict"] = "conditional_or_unknown"
    evaluated = validate_calibration_response(wrong, assignment, expected)
    assert evaluated["pass"] is False
    assert any(reason.startswith("verdict_mismatch:") for reason in evaluated["reason_codes"])

    invented = json.loads(json.dumps(response))
    invented["calibration_results"][0]["invented_material_premise"] = True
    evaluated = validate_calibration_response(invented, assignment, expected)
    assert evaluated["pass"] is False
    assert evaluated["invented_material_premise_count"] == 1


def test_calibration_protocol_contains_no_result_or_qualification_authority(
    project_root: Path,
) -> None:
    protocol = build_first_direct_reviewer_calibration_protocol(project_root)

    assert protocol["execution_state"] == "frozen_not_started"
    assert protocol["qualification_authority"] == "none_calibration_protocol_only"
    assert "calibration_ledger" not in protocol
    assert "scientific_label" not in protocol
    assert "detector_outcome" not in protocol
    assert "finding" not in protocol


def test_first_calibration_transport_failures_are_retained_without_pass(
    project_root: Path,
) -> None:
    root = project_root / FAILED_CALIBRATION_RELATIVE
    ledger = _load(root / "CALIBRATION_LEDGER.json")
    supplied = ledger.pop("ledger_digest")

    assert supplied == semantic_digest(ledger)
    assert supplied == ("sha256:ea070181d537a6c939bf2328ae75d5be1c697cff38a0f3e31e074ac04651c795")
    assert ledger["summary"] == {
        "assigned_reviewer_count": 6,
        "retained_attempt_count": 6,
        "passed_count": 0,
        "failed_count": 6,
        "all_assigned_attempts_retained": True,
        "replacement_count": 0,
        "all_reviewer_configurations_passed": False,
    }
    assert all(entry["provider_cli_exit_code"] == 1 for entry in ledger["entries"])
    assert all(entry["response_digest"] is None for entry in ledger["entries"])
    assert all(entry["calibration_status"] == "failed" for entry in ledger["entries"])
    assert all(
        entry["calibration_evaluation"]["exact_expected_verdict_count"] == 0
        for entry in ledger["entries"]
    )


def test_second_calibration_retains_three_codex_passes_and_three_claude_transport_failures(
    project_root: Path,
) -> None:
    root = project_root / PARTIAL_CALIBRATION_RELATIVE
    ledger = _load(root / "CALIBRATION_LEDGER.json")
    supplied = ledger.pop("ledger_digest")

    assert supplied == semantic_digest(ledger)
    assert supplied == ("sha256:253b3fa6283c91e66442a3c9fe42f9f100754bd9aeb4e88e53564c96288e2bf3")
    assert ledger["summary"] == {
        "assigned_reviewer_count": 6,
        "retained_attempt_count": 6,
        "passed_count": 3,
        "failed_count": 3,
        "all_assigned_attempts_retained": True,
        "replacement_count": 0,
        "all_reviewer_configurations_passed": False,
    }
    by_provider = {
        provider: [entry for entry in ledger["entries"] if entry["provider"] == provider]
        for provider in {"Anthropic", "OpenAI"}
    }
    assert all(entry["calibration_status"] == "passed" for entry in by_provider["OpenAI"])
    assert all(
        entry["calibration_evaluation"]["exact_expected_verdict_count"] == 6
        for entry in by_provider["OpenAI"]
    )
    assert all(entry["reported_session_id"] for entry in by_provider["OpenAI"])
    assert all(entry["calibration_status"] == "failed" for entry in by_provider["Anthropic"])
    assert all(entry["response_digest"] is None for entry in by_provider["Anthropic"])


def test_aggregate_calibration_preserves_retained_and_new_evidence(
    project_root: Path,
) -> None:
    protocol = build_first_direct_reviewer_calibration_protocol(project_root)
    current_entries = []
    for assignment in protocol["assignments"]:
        current_entries.append(
            {
                "participant_id": assignment["participant_id"],
                "role": assignment["role"],
                "provider": assignment["provider"],
                "configuration_digest": assignment["configuration_digest"],
                "execution_context_id": assignment["execution_context_id"],
                "calibration_status": "passed",
                "provider_cli_authenticated_success": True,
                "reported_session_id": assignment["requested_provider_session_id"],
                "calibration_evaluation": {"pass": True},
                "response_digest": "sha256:synthetic-response",
                "transcript_digest": "sha256:synthetic-transcript",
            }
        )
    current_ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_reviewer_calibration_ledger",
        "ledger_version": "1.0.0",
        "protocol_digest": protocol["protocol_digest"],
        "participant_enrollment_digest": protocol["participant_enrollment_digest"],
        "entries": current_entries,
        "summary": {},
        "sealed_at": "2026-08-05T00:12:00Z",
        "qualification_authority": "none_reviewer_calibration_only",
    }
    current_ledger["ledger_digest"] = semantic_digest(current_ledger)

    aggregate = _build_aggregate_ledger(project_root, protocol, current_ledger)
    supplied = aggregate.pop("ledger_digest")

    assert supplied == semantic_digest(aggregate)
    assert aggregate["summary"] == {
        "expected_reviewer_count": 6,
        "active_configuration_evidence_count": 6,
        "retained_v2_pass_count": 3,
        "new_v3_attempt_count": 3,
        "active_passed_count": 6,
        "active_failed_count": 0,
        "historical_attempt_count_across_protocols": 15,
        "historical_failed_attempt_count": 9,
        "current_protocol_replacement_count": 0,
        "all_active_reviewer_configurations_passed": True,
    }
    assert Counter(item["calibration_evidence_source"] for item in aggregate["entries"]) == {
        "retained_protocol_v2_pass": 3,
        "protocol_v3_attempt": 3,
    }
    assert aggregate["qualification_authority"] == "none_reviewer_calibration_only"
    assert "scientific_label" not in aggregate
    assert "detector_outcome" not in aggregate
    assert "finding" not in aggregate


def test_third_calibration_retains_three_claude_authentication_failures(
    project_root: Path,
) -> None:
    root = project_root / CALIBRATION_RELATIVE
    ledger = _load(root / "CALIBRATION_LEDGER.json")
    supplied = ledger.pop("ledger_digest")

    assert supplied == semantic_digest(ledger)
    assert supplied == ("sha256:375265c9dc05186c74c58c4658c20a2877011db476bcebc0a7281658a54f2893")
    assert ledger["summary"] == {
        "assigned_reviewer_count": 3,
        "retained_attempt_count": 3,
        "passed_count": 0,
        "failed_count": 3,
        "all_assigned_attempts_retained": True,
        "replacement_count": 0,
        "all_reviewer_configurations_passed": False,
    }
    assert all(entry["provider"] == "Anthropic" for entry in ledger["entries"])
    assert all(entry["provider_cli_exit_code"] == 1 for entry in ledger["entries"])
    assert all(entry["provider_cli_authenticated_success"] is False for entry in ledger["entries"])
    assert all(entry["calibration_status"] == "failed" for entry in ledger["entries"])
    assert all(entry["response_digest"] is None for entry in ledger["entries"])

    aggregate = _load(root / "AGGREGATE_CALIBRATION_LEDGER.json")
    aggregate_digest = aggregate.pop("ledger_digest")
    assert aggregate_digest == semantic_digest(aggregate)
    assert aggregate_digest == (
        "sha256:3da48f5fead855cd4685448f2f550b71b77ec1e366737381429c3874e00b9fa5"
    )
    assert aggregate["summary"] == {
        "expected_reviewer_count": 6,
        "active_configuration_evidence_count": 6,
        "retained_v2_pass_count": 3,
        "new_v3_attempt_count": 3,
        "active_passed_count": 3,
        "active_failed_count": 3,
        "historical_attempt_count_across_protocols": 15,
        "historical_failed_attempt_count": 12,
        "current_protocol_replacement_count": 0,
        "all_active_reviewer_configurations_passed": False,
    }
    assert aggregate["qualification_authority"] == "none_reviewer_calibration_only"
