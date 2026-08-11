from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from sc_referee_evaluation.production_finding_demonstration import (
    ProductionFindingDemonstrationError,
    verify_production_finding_demonstration,
)

from sc_referee.controller import replay
from sc_referee.reporting.policy import validate_report_contract

DEMONSTRATION_RELATIVE = Path("evaluation/production-finding-demonstration-v1")


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_committed_first_findings_are_policy_valid_exactly_one_per_error(
    project_root: Path, schema_root: Path
) -> None:
    root = project_root / DEMONSTRATION_RELATIVE
    record = verify_production_finding_demonstration(root, schema_root=schema_root)

    assert record["execution_policy"] == {
        "project_authored_code_executed": False,
        "production_run_audit_path_used": True,
        "timestamp_override_available": False,
    }
    assert [item["key"] for item in record["demonstrations"]] == [
        "complete-domain",
        "dependence",
    ]
    for item in record["demonstrations"]:
        assert item["error_run"]["finding_count"] == 1
        assert item["control_twin"]["finding_count"] == 0
        assert item["error_run"]["project_execution_count"] == 0
        assert item["control_twin"]["project_execution_count"] == 0


def test_committed_error_and_control_locks_replay_through_current_controller(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    root = project_root / DEMONSTRATION_RELATIVE
    for detector in ("complete-domain", "dependence"):
        for role, expected in (("error", 1), ("control", 0)):
            committed = _load(root / detector / role / "audit/audit.bundle.json")
            replayed = replay(
                root / detector / role / "audit/semantic.lock.json",
                tmp_path / detector / role,
                schema_root,
            )
            validate_report_contract(replayed)
            assert replayed["detector_results"] == committed["detector_results"]
            assert replayed["findings"] == committed["findings"]
            assert replayed["coverage_records"] == committed["coverage_records"]
            assert len(replayed["findings"]) == expected


def test_demonstration_manifest_tamper_fails_closed(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    source = project_root / DEMONSTRATION_RELATIVE
    copied = tmp_path / "demonstration"
    shutil.copytree(source, copied)
    report = copied / "dependence/control/project/results/report.md"
    report.write_text(report.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")

    with pytest.raises(ProductionFindingDemonstrationError, match="manifest"):
        verify_production_finding_demonstration(copied, schema_root=schema_root)


def test_demonstration_readme_quotes_exact_published_finding_text(project_root: Path) -> None:
    root = project_root / DEMONSTRATION_RELATIVE
    record = _load(root / "DEMONSTRATION_RECORD.json")
    readme = (root / "README.md").read_text(encoding="utf-8")
    for item in record["demonstrations"]:
        text = item["error_run"]["finding_text"]
        assert text["title"] in readme
        assert text["summary"] in readme
        assert text["next_action"] in readme
