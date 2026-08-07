"""Permanent regression: the first-envelope burned pilot cases.

The three v4 pilot cases are answer-visible development evidence after the
failed v1.1.0 pilot (their labels were exposed when the pilot was scored), so
they are permanently qualification-ineligible. They are retained here as the
regression fixtures the delivery plan requires for the discovered missed
error: detector v1.2.0 must localize the planted retained-subset conflict in
the error-bearing case and stay clean on both controls, deterministically.
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
RUNS_RELATIVE = Path(
    "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-lane-v2/"
    "pilot-detector-run-three-case/runs"
)
CASES = (
    ("35069763f06891dba5a3", "complete-declared-domain-exposure", "error"),
    ("2e26bf5ece15be03717f", "complete-declared-domain-exposure", "corrected"),
    ("b036fd64c647dfd93e35", "retained-observed-subset-exposure", "valid_alternative"),
)


def _audit_case(
    project_root: Path, tmp_path: Path, slug: str, candidate_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    repository = tmp_path / "project"
    shutil.copytree(project_root / RUNS_RELATIVE / slug / "project", repository)
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


@pytest.mark.parametrize(("slug", "candidate_id", "role"), CASES, ids=lambda value: str(value))
def test_burned_pilot_cases_have_exact_v120_outcomes(
    project_root: Path, tmp_path: Path, slug: str, candidate_id: str, role: str
) -> None:
    bundle, module = _audit_case(project_root, tmp_path, slug, candidate_id)
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
        assert module["state"] == "not_applicable"
        assert conflicts == []
