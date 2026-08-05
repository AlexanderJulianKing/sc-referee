from __future__ import annotations

import argparse
import ast
import json
import tempfile
from pathlib import Path
from typing import Any, cast

from sc_referee_evaluation.prospective_qualification_v2 import freeze_case_evidence_contract
from sc_referee_evaluation.prospective_selected_result_verifier import (
    PYTHON_STATIC_MARKED_REPORT_PROFILE,
    freeze_independent_selected_result_derivation,
    freeze_selected_result_validation,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from scripts.build_first_direct_app_reviewer_calibration import APP_CALIBRATION_RELATIVE
from scripts.build_first_direct_reviewer_calibration_protocol import LANE_RELATIVE
from scripts.build_first_direct_three_case_pilot_authoring import ACTIVE_ENROLLMENT_DIGEST
from scripts.build_first_direct_three_case_pilot_authoring_v3 import (
    PILOT_AUTHORING_V3_RELATIVE,
)
from scripts.record_first_direct_three_case_pilot_authors import (
    PilotAuthorRecordError,
    _freeze_case,
)
from scripts.record_first_direct_three_case_pilot_authors_v2 import (
    CANONICAL_ISSUE_CLASS,
    _load,
    _replay,
    _validation_schedule,
)
from scripts.record_first_direct_three_case_pilot_authors_v3 import (
    PROTOCOL_DIGEST,
    RESTART_AMENDMENT_DIGEST,
    validate_v3_author_attempt,
)

CLAUDE_CAPTURE_DIGEST = "sha256:bdb26aa3972225769950c3594578a2b2bdbe424e8529d5f5aa3905c3b838b42e"
CODEX_CAPTURE_DIGEST = "sha256:5009fbb5597a72e664fd2956c8dc96afc98fcfaa78f9c1a4207f95d2a8028dbb"
COMPLETED_AT = "2026-08-05T05:18:00Z"


def _negative_subscript_lines(producer: str) -> list[int]:
    tree = ast.parse(producer)
    return sorted(
        {
            int(node.lineno)
            for node in ast.walk(tree)
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.UnaryOp)
        }
    )


def _inspect_static_case(
    case: dict[str, Any],
    *,
    participant: dict[str, Any],
    authored_at: str,
    schedule: dict[str, str],
    validator_identity: dict[str, Any],
    envelope: dict[str, Any],
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="sc-referee-v3-failure-intake-") as directory:
        temporary = Path(directory)
        frozen = _freeze_case(
            case,
            participant=participant,
            authored_at=authored_at,
            frozen_at=schedule["author_frozen_at"],
            cases_root=temporary / "cases",
            declarations_root=temporary / "author-declarations",
            manifests_root=temporary / "case-manifests",
        )
        case_id = str(case["case_id"])
        case_root = temporary / "cases" / case_id.removeprefix("case:")
        contract = freeze_case_evidence_contract(
            {
                "case_id": case_id,
                "envelope": envelope,
                "canonical_issue_class": CANONICAL_ISSUE_CLASS,
                "author_declaration": frozen["declaration"],
                "coordinated_at": schedule["coordinated_at"],
            },
            frozen_at=schedule["contract_frozen_at"],
        )
        selected = frozen["declaration"]["selected_result_binding"]
        if selected is None:
            raise PilotAuthorRecordError("V3 failure inspection requires one selected result.")
        derivation = freeze_independent_selected_result_derivation(
            case_root,
            {
                "case_id": case_id,
                "validator_identity": validator_identity,
                "profile_id": PYTHON_STATIC_MARKED_REPORT_PROFILE,
                "selected_report_path": selected["report_locator"]["path"],
                "derived_at": schedule["derived_at"],
            },
            frozen_at=schedule["derivation_frozen_at"],
        )
        validation = freeze_selected_result_validation(
            case_root,
            contract,
            derivation,
            declaration_revealed_at=schedule["declaration_revealed_at"],
            compared_at=schedule["compared_at"],
        )
        return {
            "case_manifest_digest": frozen["manifest"]["manifest_digest"],
            "author_declaration_digest": frozen["declaration"]["declaration_digest"],
            "case_contract_digest": contract["contract_digest"],
            "derivation_digest": derivation["derivation_digest"],
            "derivation_status": derivation["derivation_status"],
            "derivation_reason_codes": derivation["reason_codes"],
            "validation_digest": validation["validation_digest"],
            "validation_status": validation["status"],
            "validation_reason_codes": validation["reason_codes"],
        }


def build_first_direct_three_case_pilot_authors_v3_failure(
    project_root: Path,
) -> dict[str, Any]:
    root = project_root / PILOT_AUTHORING_V3_RELATIVE
    restart = _load(root / "PILOT_AUTHORING_RESTART_AMENDMENT.json")
    _replay(
        restart,
        "amendment_digest",
        RESTART_AMENDMENT_DIGEST,
        "V3 authoring restart amendment",
    )
    protocol = _load(root / "PILOT_AUTHORING_PROTOCOL.json")
    _replay(protocol, "protocol_digest", PROTOCOL_DIGEST, "V3 authoring protocol")

    enrollment = _load(project_root / APP_CALIBRATION_RELATIVE / "PARTICIPANT_ENROLLMENT.json")
    _replay(
        enrollment,
        "enrollment_digest",
        ACTIVE_ENROLLMENT_DIGEST,
        "Active participant enrollment",
    )
    validators = [
        item for item in enrollment["participants"] if item["role"] == "evidence_validator"
    ]
    if len(validators) != 1:
        raise PilotAuthorRecordError("Active enrollment lacks one evidence validator.")
    validator = validators[0]
    validator_identity = {
        "validator_id": validator["participant_id"],
        "provider": validator["provider"],
        "execution_context_id": validator["execution_context_id"],
        "identity_evidence_digest": validator["configuration_digest"],
    }
    lane = _load(project_root / LANE_RELATIVE / "LANE_FREEZE.json")
    supplied_lane_digest = str(lane.get("lane_freeze_digest"))
    _replay(lane, "lane_freeze_digest", supplied_lane_digest, "Direct lane freeze")
    envelopes = lane["prospective_protocol"]["envelopes"]
    if len(envelopes) != 1:
        raise PilotAuthorRecordError("Direct lane does not contain one envelope.")
    envelope = envelopes[0]

    expected = {
        "Anthropic": (
            root / "incoming" / "pilot-author-claude-03.json",
            CLAUDE_CAPTURE_DIGEST,
        ),
        "OpenAI": (
            root / "incoming" / "pilot-author-codex-03.json",
            CODEX_CAPTURE_DIGEST,
        ),
    }
    assignments = {
        str(item["participant"]["provider"]): item for item in protocol["author_assignments"]
    }
    if set(assignments) != set(expected):
        raise PilotAuthorRecordError("V3 failure recorder expected one author per provider.")

    schedule = _validation_schedule(COMPLETED_AT)
    captures: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    for provider in ("Anthropic", "OpenAI"):
        assignment = assignments[provider]
        path, expected_digest = expected[provider]
        capture_bytes = path.read_bytes()
        capture_digest = sha256_digest(capture_bytes)
        if capture_digest != expected_digest:
            raise PilotAuthorRecordError(f"Retained v3 {provider} capture has drifted.")
        attempt = cast(dict[str, Any], json.loads(capture_bytes))
        cases = validate_v3_author_attempt(attempt, assignment)
        raw_response = str(attempt["raw_response"])
        response = cast(dict[str, Any], json.loads(raw_response))
        captures.append(
            {
                "participant_id": attempt["participant_id"],
                "provider": provider,
                "input_capture_digest": capture_digest,
                "raw_response_digest": sha256_digest(raw_response.encode("utf-8")),
                "response_digest": semantic_digest(response),
                "attempt_status": attempt["attempt_status"],
                "replacement_count": attempt["replacement_count"],
            }
        )
        for case in cases:
            inspected = _inspect_static_case(
                case,
                participant=assignment["participant"],
                authored_at=str(attempt["completed_at"]),
                schedule=schedule,
                validator_identity=validator_identity,
                envelope=envelope,
            )
            negative_lines = _negative_subscript_lines(case["producer_file"]["content"])
            entries.append(
                {
                    "case_id": case["case_id"],
                    "participant_id": attempt["participant_id"],
                    "provider": provider,
                    "transport_status": "valid_physical_line_transport",
                    "role_path_status": "valid_exact_role_paths",
                    "declaration_status": "valid_one_selected_result_declaration",
                    **inspected,
                    "negative_subscript_lines": negative_lines,
                    "admission_status": (
                        "not_admitted_incomplete_cohort"
                        if inspected["validation_status"] == "verified_complete"
                        else "rejected_static_intake"
                    ),
                    "admitted": False,
                    "metric_eligible": False,
                }
            )

    verified_count = sum(item["validation_status"] == "verified_complete" for item in entries)
    unsupported_count = sum(
        item["validation_status"] == "unsupported_structure" for item in entries
    )
    unsupported = [item for item in entries if item["validation_status"] == "unsupported_structure"]
    if (
        len(entries) != 3
        or verified_count != 2
        or unsupported_count != 1
        or unsupported[0]["provider"] != "OpenAI"
        or unsupported[0]["validation_reason_codes"] != ["unsupported_selected_report_expression"]
        or unsupported[0]["negative_subscript_lines"] != [6, 7, 8]
    ):
        raise PilotAuthorRecordError("V3 failure state no longer matches the retained evidence.")

    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_three_case_authoring_intake_failure_ledger",
        "ledger_version": "2.0.0",
        "protocol_digest": PROTOCOL_DIGEST,
        "authoring_restart_amendment_digest": RESTART_AMENDMENT_DIGEST,
        "lane_freeze_digest": supplied_lane_digest,
        "active_enrollment_digest": ACTIVE_ENROLLMENT_DIGEST,
        "input_captures": captures,
        "entries": sorted(entries, key=lambda item: str(item["case_id"])),
        "validator_identity": validator_identity,
        "summary": {
            "assigned_author_context_count": 2,
            "model_attempt_count": 2,
            "response_case_count": 3,
            "verified_selected_result_count": verified_count,
            "unsupported_selected_result_count": unsupported_count,
            "admitted_case_count": 0,
            "metric_eligible_case_count": 0,
            "project_code_executed_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
        },
        "cohort_status": "rejected_before_authoring_admission",
        "cohort_reason_codes": ["incomplete_admission_valid_causal_triad"],
        "completed_at": COMPLETED_AT,
        "qualification_authority": "none_failed_authoring_intake_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    return ledger


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    root = project_root / PILOT_AUTHORING_V3_RELATIVE
    output = root / "AUTHORING_INTAKE_FAILURE_LEDGER.json"
    if output.exists():
        raise FileExistsError("Refusing to replace retained v3 authoring intake failure.")
    ledger = build_first_direct_three_case_pilot_authors_v3_failure(project_root)
    _write_json(output, ledger)
    print(json.dumps(ledger["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
