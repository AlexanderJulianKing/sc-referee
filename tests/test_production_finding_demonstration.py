from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from sc_referee_evaluation.production_finding_demonstration import (
    ProductionFindingDemonstrationError,
    _verify_case,
    verify_production_finding_demonstration,
)

DEMONSTRATION_RELATIVE = Path("evaluation/production-finding-demonstration-v1")


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_committed_v019_demonstration_is_retained_but_stale_authority_refuses_validation(
    project_root: Path, schema_root: Path
) -> None:
    root = project_root / DEMONSTRATION_RELATIVE
    with pytest.raises(ProductionFindingDemonstrationError, match="authority chain drifted"):
        verify_production_finding_demonstration(root, schema_root=schema_root)


def test_committed_v019_audit_and_replay_projections_remain_identical(
    project_root: Path,
) -> None:
    root = project_root / DEMONSTRATION_RELATIVE
    for lane in ("complete-domain", "dependence"):
        for role, expected in (("error", 1), ("control", 0)):
            committed = _load(root / lane / role / "audit/audit.bundle.json")
            replayed = _load(root / lane / role / "replay/audit.bundle.json")
            assert committed["schema_version"] == "0.19.0"
            assert replayed["schema_version"] == "0.19.0"
            assert replayed["detector_results"] == committed["detector_results"]
            assert replayed["findings"] == committed["findings"]
            assert replayed["coverage_records"] == committed["coverage_records"]
            assert len(replayed["findings"]) == expected


def test_complete_domain_cases_reach_case_verification_and_prove_no_execution(
    project_root: Path,
) -> None:
    root = project_root / DEMONSTRATION_RELATIVE
    record = _load(root / "DEMONSTRATION_RECORD.json")
    demonstrations = record["demonstrations"]
    assert isinstance(demonstrations, list)
    entry = next(
        item
        for item in demonstrations
        if isinstance(item, dict) and item.get("key") == "complete-domain"
    )
    binding_id = entry["binding_id"]

    for role, key, expected in (
        ("error", "error_run", 1),
        ("control", "control_twin", 0),
    ):
        case = entry[key]
        assert isinstance(case, dict)
        case_root = root / "complete-domain" / role
        _verify_case(
            case_root,
            case,
            binding_id,
            expected=expected,
            validate_live_report_policy=False,
        )
        bundle = _load(case_root / str(case["audit_bundle"]))
        assert case["project_execution_count"] == 0
        assert bundle["executions"] == []


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
