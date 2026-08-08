"""Permanent regression: the first-envelope burned pilot cases.

The six burned pilot cases are answer-visible development evidence after the
failed v1.1.0 and v1.2.0 pilots (their labels were exposed when the pilots were scored), so
they are permanently qualification-ineligible. They are retained here as the
regression fixtures the delivery plan requires for the discovered missed
errors: the current detector must localize the planted retained-subset conflict in
each error-bearing case and stay clean on every control, deterministically.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.method_contract_run import run_method_contract
from sc_referee.scientific_requirement_contract import (
    SCIENTIFIC_REQUIREMENT_PROFILE_ID,
    SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
)

CHECK_ID = "check:complete-domain-exposure-denominator"
DETECTOR_ID = "detector:bounded-analysis-method-conflict"
LANE_RELATIVE = Path(
    "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2"
)
V1_RUNS = LANE_RELATIVE / "pilot-detector-run-three-case/runs"
V120_RUNS = LANE_RELATIVE / "pilot-v120-lean-detector-run-three-case/runs"
V200B_RUNS = LANE_RELATIVE / "pilot-v200b-lean-pipeline-three-case/detector-run/runs"
V201C_RUNS = LANE_RELATIVE / "pilot-v201c-lean-pipeline-three-case/detector-run/runs"
V202F_RUNS = LANE_RELATIVE / "pilot-v202f-lean-pipeline-three-case/detector-run/runs"
# Both burned error cases must be caught by quantity arithmetic alone
# (ADR-0069). Both valid alternatives state a full accounting and a
# percent-marked or decimal rate, so the arithmetic recognizes their
# retained-subset exposure as an applicable covered match for their
# contracts.
CASES = (
    (V1_RUNS, "35069763f06891dba5a3", "complete-declared-domain-exposure", "error", "applicable"),
    (
        V1_RUNS,
        "2e26bf5ece15be03717f",
        "complete-declared-domain-exposure",
        "corrected",
        "applicable",
    ),
    (
        V1_RUNS,
        "b036fd64c647dfd93e35",
        "retained-observed-subset-exposure",
        "valid_alternative",
        "applicable",
    ),
    (V120_RUNS, "ce8220b59efdff3392a3", "complete-declared-domain-exposure", "error", "applicable"),
    (
        V120_RUNS,
        "58cd55a6683253e967dd",
        "complete-declared-domain-exposure",
        "corrected",
        "applicable",
    ),
    (
        V120_RUNS,
        "5b1bce664dbff4b6f405",
        "retained-observed-subset-exposure",
        "valid_alternative",
        "applicable",
    ),
    (
        V200B_RUNS,
        "533703c9e99aabc44ace",
        "complete-declared-domain-exposure",
        "error",
        "applicable",
    ),
    (
        V200B_RUNS,
        "a9568ea9854998c55e90",
        "complete-declared-domain-exposure",
        "corrected",
        "applicable",
    ),
    (
        V200B_RUNS,
        "575a0b1399c85e4cf4d7",
        "retained-observed-subset-exposure",
        "valid_alternative",
        "applicable",
    ),
    (
        V201C_RUNS,
        "ce0feda26ed1612a2efd",
        "complete-declared-domain-exposure",
        "error",
        "applicable",
    ),
    (
        V201C_RUNS,
        "8875fc42723bf9f35470",
        "complete-declared-domain-exposure",
        "corrected",
        "applicable",
    ),
    (
        V201C_RUNS,
        "9e3b88f3fcd2545eaa30",
        "retained-observed-subset-exposure",
        "valid_alternative",
        "applicable",
    ),
    (
        V202F_RUNS,
        "f96cb930a43f48491c3c",
        "complete-declared-domain-exposure",
        "error",
        "applicable",
    ),
    (
        V202F_RUNS,
        "a143e5f92a980a92ede5",
        "complete-declared-domain-exposure",
        "corrected",
        "applicable",
    ),
    (
        V202F_RUNS,
        "4b3a3ca7b912052270cf",
        "retained-observed-subset-exposure",
        "valid_alternative",
        "applicable",
    ),
)


def _audit_case(
    project_root: Path, tmp_path: Path, runs: Path, slug: str, candidate_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    repository = tmp_path / "project"
    shutil.copytree(project_root / runs / slug / "project", repository)
    schema_root = project_root / "reference/schemas-v0.18.0"
    contract = run_method_contract(
        repository,
        "task.md",
        tmp_path / "contract",
        schema_root,
        profile={
            "profile_id": SCIENTIFIC_REQUIREMENT_PROFILE_ID,
            "profile_version": SCIENTIFIC_REQUIREMENT_PROFILE_VERSION,
            "check_id": CHECK_ID,
            "candidate_id": candidate_id,
        },
        actor_id="scientist:burned-pilot-regression",
    )
    assert contract["findings"] == []
    bundle = run_audit(
        repository,
        tmp_path / "audit",
        schema_root,
        report="results/report.md",
        method_contract_lock=tmp_path / "contract" / "semantic.lock.json",
    )
    replayed = replay(tmp_path / "audit" / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["detector_results"] == bundle["detector_results"]
    lock = json.loads((tmp_path / "audit" / "semantic.lock.json").read_text(encoding="utf-8"))
    module = next(
        item
        for item in lock["scientific_check_registry"]["evaluation"]["modules"]
        if item["check_id"] == CHECK_ID
    )
    return bundle, module


def _conflict_candidates(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        result
        for result in bundle["detector_results"]
        if result.get("detector_id") == DETECTOR_ID
        and result.get("state") == "evaluation_finding_candidate"
        and any(
            item.get("evidence_id") == "evidence:analysis-method-ledger"
            for item in result.get("evidence", [])
        )
    ]


@pytest.mark.parametrize(
    ("runs", "slug", "candidate_id", "role", "expected_state"),
    CASES,
    ids=lambda value: str(value),
)
def test_burned_pilot_cases_have_exact_v2_outcomes(
    project_root: Path,
    tmp_path: Path,
    runs: Path,
    slug: str,
    candidate_id: str,
    role: str,
    expected_state: str,
) -> None:
    bundle, module = _audit_case(project_root, tmp_path, runs, slug, candidate_id)
    conflicts = _conflict_candidates(bundle)
    assert bundle["findings"] == []
    assert bundle["executions"] == []
    if role == "error":
        assert module["state"] == "applicable"
        assert len(conflicts) == 1
        ledger = next(
            item
            for item in conflicts[0]["evidence"]
            if item["evidence_id"] == "evidence:analysis-method-ledger"
        )
        assert ledger["observed_value"]["observed"] == "retained_observed_subset_exposure_only"
        assert ledger["observed_value"]["requirement"] == "complete_declared_domain_exposure"
        assert conflicts[0]["extensions"]["x-production-finding-permitted"] is False
        cited_paths = {
            ref.get("path")
            for item in conflicts[0]["evidence"]
            for ref in item.get("source_refs", [])
        }
        assert "results/report.md" in cited_paths
    elif role == "corrected":
        assert module["state"] == "applicable"
        assert conflicts == []
        observation = module["observations"][0]
        assert observation["observed_operand"]["value"] == "complete_declared_domain_exposure"
    else:
        assert module["state"] == expected_state
        assert conflicts == []
        if expected_state == "applicable":
            observation = module["observations"][0]
            assert (
                observation["observed_operand"]["value"] == "retained_observed_subset_exposure_only"
            )
