from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.method_contract_run import run_method_contract
from sc_referee.scientific_requirement_contract import (
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
)

CORPUS_PATH = Path(__file__).resolve().parent / "data" / "generic_method_contract_e2e_v1.json"
GENERIC_WRITER = (
    "from pathlib import Path\nPath('report.md').write_text('generated\\n', encoding='utf-8')\n"
)


def _corpus() -> dict[str, Any]:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


CASES = _corpus()["cases"]


def _write_state(repository: Path, case: dict[str, Any], state: str) -> None:
    (repository / "report.md").write_text(case[f"{state}_report"], encoding="utf-8")
    source = case.get(f"{state}_source")
    if source is None:
        source = case.get("corrected_source", GENERIC_WRITER)
    (repository / "analysis.py").write_text(source, encoding="utf-8")


def _method_results(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in bundle["detector_results"]
        if item["detector_id"] == "detector:bounded-analysis-method-conflict"
    ]


def _result_for_requirement(bundle: dict[str, Any], required_operand: str) -> dict[str, Any] | None:
    for result in _method_results(bundle):
        ledger = next(
            (
                evidence
                for evidence in result["evidence"]
                if evidence["evidence_id"] == "evidence:analysis-method-ledger"
            ),
            None,
        )
        if ledger is not None and ledger["observed_value"]["requirement"] == required_operand:
            return result
    return None


def _module(lock_path: Path, check_id: str) -> dict[str, Any]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    return next(
        item
        for item in lock["scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == check_id
    )


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
def test_generic_contract_bound_conflict_control_and_abstention_matrix(
    schema_root: Path,
    tmp_path: Path,
    case: dict[str, Any],
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    (repository / "task.md").write_text(
        "Apply the scientist-authorized atomic analysis requirement.\n", encoding="utf-8"
    )
    contract_root = tmp_path / "contract"
    contract = run_method_contract(
        repository,
        "task.md",
        contract_root,
        schema_root,
        profile={
            "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            "semantic_role_authority": {},
            "check_id": case["check_id"],
            "candidate_id": case["required_candidate_id"],
        },
        actor_id="scientist:development-fixture-author",
    )
    assert contract["findings"] == []

    _write_state(repository, case, "conflict")
    conflict_root = tmp_path / "conflict"
    conflict = run_audit(
        repository,
        conflict_root,
        schema_root,
        report="report.md",
        method_contract_lock=contract_root / "semantic.lock.json",
    )
    conflict_result = _result_for_requirement(conflict, case["required_operand"])
    assert conflict_result is not None
    assert conflict_result["state"] == "evaluation_finding_candidate"
    assert conflict_result["extensions"]["x-production-finding-permitted"] is False
    assert conflict["findings"] == []
    assert conflict["executions"] == []
    ledger_source_paths = {
        source_ref["path"] for source_ref in conflict_result["evidence"][-1]["source_refs"]
    }
    assert set(case["expected_source_paths"]) <= ledger_source_paths

    conflict_replay = replay(
        conflict_root / "semantic.lock.json",
        tmp_path / "conflict-replay",
        schema_root,
    )
    for field in ("answers", "semantic_assertions", "detector_results", "findings"):
        assert conflict_replay[field] == conflict[field]

    _write_state(repository, case, "corrected")
    corrected_root = tmp_path / "corrected"
    corrected = run_audit(
        repository,
        corrected_root,
        schema_root,
        report="report.md",
        method_contract_lock=contract_root / "semantic.lock.json",
    )
    corrected_result = _result_for_requirement(corrected, case["required_operand"])
    assert corrected_result is not None
    assert corrected_result["state"] == "no_issue_detected_within_coverage"
    assert "evaluation_candidate" not in corrected_result
    assert corrected["findings"] == []
    assert corrected["executions"] == []

    corrected_replay = replay(
        corrected_root / "semantic.lock.json",
        tmp_path / "corrected-replay",
        schema_root,
    )
    assert corrected_replay["detector_results"] == corrected["detector_results"]

    _write_state(repository, case, "ambiguous")
    ambiguous_root = tmp_path / "ambiguous"
    ambiguous = run_audit(
        repository,
        ambiguous_root,
        schema_root,
        report="report.md",
        method_contract_lock=contract_root / "semantic.lock.json",
    )
    assert _module(ambiguous_root / "semantic.lock.json", case["check_id"])["state"] in {
        "ambiguous",
        "unsupported",
    }
    assert not [
        question
        for question in ambiguous["material_questions"]
        if question.get("extensions", {}).get("x-scientific-check-id") == case["check_id"]
    ]
    assert _result_for_requirement(ambiguous, case["required_operand"]) is None
    assert ambiguous["findings"] == []
    assert ambiguous["executions"] == []


def test_generic_e2e_matrix_is_explicitly_development_only() -> None:
    corpus = _corpus()
    template = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "evaluation"
            / "prospective-qualification-v1"
            / "ten-envelope-study.template.json"
        ).read_text(encoding="utf-8")
    )

    assert corpus["qualification_use_permitted"] is False
    assert corpus["qualification_status"] == "ineligible_development_fixture"
    assert corpus["benchmark_identity_used"] is False
    assert len(corpus["limitations"]) == 3
    assert len(corpus["cases"]) == 10
    assert len({case["check_id"] for case in corpus["cases"]}) == 10
    assert {(case["check_id"], case["required_candidate_id"]) for case in corpus["cases"]} == {
        (envelope["check_id"], envelope["candidate_id"]) for envelope in template["envelopes"]
    }
