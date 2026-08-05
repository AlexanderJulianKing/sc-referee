from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

from sc_referee_evaluation.prospective_qualification_v2 import (
    freeze_case_evidence_contract,
    validate_author_selected_result_declaration,
)
from sc_referee_evaluation.prospective_selected_result_verifier import (
    PYTHON_STATIC_MARKED_REPORT_PROFILE,
    freeze_independent_selected_result_derivation,
    freeze_selected_result_validation,
)

from sc_referee.core.ids import semantic_digest
from scripts.build_first_direct_app_reviewer_calibration import APP_CALIBRATION_RELATIVE
from scripts.build_first_direct_reviewer_calibration_protocol import LANE_RELATIVE
from scripts.build_first_direct_three_case_pilot_authoring import PILOT_AUTHORING_RELATIVE

LANE_FREEZE_DIGEST = "sha256:c58ee57c01d5f7c46855eb9f554d0a476f664e44edbdd7e15679bd53d72fa12b"
ACTIVE_ENROLLMENT_DIGEST = "sha256:95ef5badd874db346279de725a35679da80d00bf8d40c323041b414ce750a5bc"
AUTHORING_LEDGER_DIGEST = "sha256:b1a0bcdaf9aa9a7fc2970bd94c510ac9b8ac5475e0e90d5ce7d4f39a540a58f6"
CANONICAL_ISSUE_CLASS = "issue-class:retained-subset-for-complete-domain"
COORDINATED_AT = "2026-08-05T02:15:30Z"
CONTRACT_FROZEN_AT = "2026-08-05T02:16:00Z"
DERIVED_AT = "2026-08-05T02:16:30Z"
DERIVATION_FROZEN_AT = "2026-08-05T02:17:00Z"
DECLARATION_REVEALED_AT = "2026-08-05T02:17:30Z"
COMPARED_AT = "2026-08-05T02:18:00Z"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _replay(record: dict[str, Any], digest_field: str, expected: str, label: str) -> None:
    supplied = record.pop(digest_field, None)
    if supplied != expected or supplied != semantic_digest(record):
        raise ValueError(f"{label} does not replay.")
    record[digest_field] = supplied


def build_first_direct_three_case_selected_result_intake(
    project_root: Path,
) -> dict[str, Any]:
    lane = _load(project_root / LANE_RELATIVE / "LANE_FREEZE.json")
    _replay(lane, "lane_freeze_digest", LANE_FREEZE_DIGEST, "Direct lane freeze")
    envelopes = lane["prospective_protocol"]["envelopes"]
    if len(envelopes) != 1:
        raise ValueError("First direct lane does not contain one scientific envelope.")
    envelope = envelopes[0]

    authoring_root = project_root / PILOT_AUTHORING_RELATIVE
    authoring_ledger = _load(authoring_root / "AUTHORING_LEDGER.json")
    _replay(
        authoring_ledger,
        "ledger_digest",
        AUTHORING_LEDGER_DIGEST,
        "Three-case authoring ledger",
    )
    if (
        authoring_ledger["summary"]["authored_case_count"] != 3
        or authoring_ledger["summary"]["scientific_label_count"] != 0
        or authoring_ledger["summary"]["detector_outcome_count"] != 0
    ):
        raise ValueError("Authoring ledger is not the exact pre-review three-case state.")

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
        raise ValueError("Active enrollment does not contain one evidence validator.")
    validator = validators[0]
    validator_identity = {
        "validator_id": validator["participant_id"],
        "provider": validator["provider"],
        "execution_context_id": validator["execution_context_id"],
        "identity_evidence_digest": validator["configuration_digest"],
    }

    contracts: dict[str, dict[str, Any]] = {}
    derivations: dict[str, dict[str, Any]] = {}
    validations: dict[str, dict[str, Any]] = {}
    entries = []
    for declaration_path in sorted((authoring_root / "author-declarations").glob("*.json")):
        declaration = validate_author_selected_result_declaration(_load(declaration_path))
        case_id = str(declaration["case_id"])
        suffix = case_id.removeprefix("case:")
        case_root = authoring_root / "cases" / suffix
        contract = freeze_case_evidence_contract(
            {
                "case_id": case_id,
                "envelope": envelope,
                "canonical_issue_class": CANONICAL_ISSUE_CLASS,
                "author_declaration": declaration,
                "coordinated_at": COORDINATED_AT,
            },
            frozen_at=CONTRACT_FROZEN_AT,
        )
        selected = declaration["selected_result_binding"]
        if selected is None:
            raise ValueError("Three-case intake expected one selected report per case.")
        derivation = freeze_independent_selected_result_derivation(
            case_root,
            {
                "case_id": case_id,
                "validator_identity": validator_identity,
                "profile_id": PYTHON_STATIC_MARKED_REPORT_PROFILE,
                "selected_report_path": selected["report_locator"]["path"],
                "derived_at": DERIVED_AT,
            },
            frozen_at=DERIVATION_FROZEN_AT,
        )
        validation = freeze_selected_result_validation(
            case_root,
            contract,
            derivation,
            declaration_revealed_at=DECLARATION_REVEALED_AT,
            compared_at=COMPARED_AT,
        )
        contracts[suffix] = contract
        derivations[suffix] = derivation
        validations[suffix] = validation
        entries.append(
            {
                "case_id": case_id,
                "case_contract_digest": contract["contract_digest"],
                "derivation_digest": derivation["derivation_digest"],
                "derivation_status": derivation["derivation_status"],
                "derivation_reason_codes": derivation["reason_codes"],
                "validation_digest": validation["validation_digest"],
                "validation_status": validation["status"],
                "validation_reason_codes": validation["reason_codes"],
            }
        )
    if len(entries) != 3:
        raise ValueError("Selected-result intake did not enumerate exactly three cases.")
    status_counts = Counter(str(item["validation_status"]) for item in entries)
    reason_counts = Counter(
        str(reason)
        for item in entries
        for reason in cast(list[str], item["validation_reason_codes"])
    )
    ledger: dict[str, Any] = {
        "artifact_kind": "direct_qualification_three_case_selected_result_intake_ledger",
        "ledger_version": "1.0.0",
        "lane_freeze_digest": LANE_FREEZE_DIGEST,
        "authoring_ledger_digest": AUTHORING_LEDGER_DIGEST,
        "active_enrollment_digest": ACTIVE_ENROLLMENT_DIGEST,
        "validator_identity": validator_identity,
        "entries": entries,
        "summary": {
            "case_count": 3,
            "verified_complete_count": status_counts["verified_complete"],
            "ambiguous_count": status_counts["ambiguous_selected_result"],
            "insufficient_count": status_counts["insufficient_evidence"],
            "unsupported_count": status_counts["unsupported_structure"],
            "reason_counts": dict(sorted(reason_counts.items())),
            "project_code_executed_count": 0,
            "scientific_label_count": 0,
            "detector_outcome_count": 0,
            "metric_eligible_case_count": status_counts["verified_complete"],
        },
        "completed_at": COMPARED_AT,
        "qualification_authority": "none_selected_result_intake_ledger_only",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    return {
        "case_contracts": contracts,
        "derivations": derivations,
        "validations": validations,
        "ledger": ledger,
    }


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
    built = build_first_direct_three_case_selected_result_intake(project_root)
    root = project_root / PILOT_AUTHORING_RELATIVE
    outputs = (
        root / "case-contracts",
        root / "selected-result-derivations",
        root / "selected-result-validations",
        root / "SELECTED_RESULT_INTAKE_LEDGER.json",
    )
    if any(path.exists() for path in outputs):
        raise FileExistsError("Refusing to replace selected-result intake evidence.")
    for suffix, value in built["case_contracts"].items():
        _write_json(root / "case-contracts" / f"{suffix}.json", value)
    for suffix, value in built["derivations"].items():
        _write_json(root / "selected-result-derivations" / f"{suffix}.json", value)
    for suffix, value in built["validations"].items():
        _write_json(root / "selected-result-validations" / f"{suffix}.json", value)
    _write_json(root / "SELECTED_RESULT_INTAKE_LEDGER.json", built["ledger"])
    print(json.dumps(built["ledger"]["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
