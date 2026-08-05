from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_reviewer_calibration_protocol import (
    ALLOWED_VERDICTS,
    CALIBRATION_RELATIVE,
    build_first_direct_reviewer_calibration_protocol,
    load_effective_execution_configuration,
)
from scripts.run_first_direct_reviewer_calibration import validate_calibration_response


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    assert committed["execution_state"] == "frozen_not_started"
    assert committed["qualification_authority"] == "none_calibration_protocol_only"


def test_reviewer_calibration_protocol_binds_exact_six_tool_free_contexts(
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

    assert len(assignments) == 6
    assert Counter(item["role"] for item in assignments) == {
        "stage1_reviewer": 4,
        "stage2_reviewer": 2,
    }
    assert Counter(item["provider"] for item in assignments) == {
        "Anthropic": 3,
        "OpenAI": 3,
    }
    assert len({item["requested_session_id"] for item in assignments}) == 6
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
