from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest
from scripts.build_first_direct_three_case_pilot_authoring import PILOT_AUTHORING_RELATIVE
from scripts.record_first_direct_three_case_selected_result_intake import (
    AUTHORING_LEDGER_DIGEST,
    build_first_direct_three_case_selected_result_intake,
)


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_selected_result_intake_rebuilds_exactly(project_root: Path) -> None:
    built = build_first_direct_three_case_selected_result_intake(project_root)
    root = project_root / PILOT_AUTHORING_RELATIVE
    assert built["ledger"] == _load(root / "SELECTED_RESULT_INTAKE_LEDGER.json")
    for category in ("case_contracts", "derivations", "validations"):
        directory = {
            "case_contracts": "case-contracts",
            "derivations": "selected-result-derivations",
            "validations": "selected-result-validations",
        }[category]
        for suffix, value in built[category].items():
            assert value == _load(root / directory / f"{suffix}.json")


def test_selected_result_intake_retains_all_three_failures(project_root: Path) -> None:
    ledger = build_first_direct_three_case_selected_result_intake(project_root)["ledger"]
    digest = ledger.pop("ledger_digest")
    assert digest == semantic_digest(ledger)
    assert ledger["authoring_ledger_digest"] == AUTHORING_LEDGER_DIGEST
    assert ledger["summary"] == {
        "case_count": 3,
        "verified_complete_count": 0,
        "ambiguous_count": 0,
        "insufficient_count": 0,
        "unsupported_count": 3,
        "reason_counts": {
            "python_source_parse_failed": 2,
            "unsupported_selected_report_writer_signature": 1,
        },
        "project_code_executed_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "metric_eligible_case_count": 0,
    }
    assert {item["validation_status"] for item in ledger["entries"]} == {"unsupported_structure"}


def test_selected_result_intake_is_model_free_and_pre_detector(project_root: Path) -> None:
    built = build_first_direct_three_case_selected_result_intake(project_root)
    for derivation in built["derivations"].values():
        assert derivation["project_code_executed"] is False
        assert derivation["qualification_authority"] == "none_verifier_derivation_only"
    for validation in built["validations"].values():
        assert validation["qualification_authority"] == ("none_selected_result_validation_only")
    assert built["ledger"]["summary"]["detector_outcome_count"] == 0
