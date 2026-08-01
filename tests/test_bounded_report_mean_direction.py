from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from sc_referee.controller import replay, run_audit
from sc_referee.detectors.admission import AdmissionContext, admit_finding
from sc_referee.detectors.bounded_report_mean_direction import (
    BoundedDirectionDetectorError,
    BoundedReportMeanDirectionDetector,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.reporting.html import render_report_bytes
from sc_referee.reporting.policy import ReportContractError


def _write_project(
    root: Path,
    *,
    result_direction: str,
    reported_direction: str = "increased",
    reported_outcome: str = "expression",
    opposite_sibling: bool = False,
    second_result: bool = False,
) -> Path:
    if result_direction == "positive":
        rows = "treated,3\ntreated,5\ncontrol,1\ncontrol,3\n"
        value = 2.0
    elif result_direction == "negative":
        rows = "treated,1\ntreated,3\ncontrol,3\ncontrol,5\n"
        value = -2.0
    else:
        rows = "treated,1\ntreated,3\ncontrol,1\ncontrol,3\n"
        value = 0.0
    claim_line = f"treated {reported_direction} {reported_outcome} relative to control."
    sibling_line = (
        "\ntreated decreased expression relative to control."
        if opposite_sibling and reported_direction == "increased"
        else "\ntreated increased expression relative to control."
        if opposite_sibling
        else ""
    )
    report_text = f"# Results\n\n{claim_line}{sibling_line}\n\nDifference: {value}\n"
    (root / "report.md").write_text(report_text, encoding="utf-8")
    (root / "data.csv").write_text("group,expression\n" + rows, encoding="utf-8")
    analysis = (
        "from pathlib import Path\n"
        "import csv\n"
        "def difference(path):\n"
        "    rows = list(csv.DictReader(path.open()))\n"
        "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
        "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
        "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
        "Path('SHOULD_NOT_EXIST').write_text('project code ran')\n"
        "Path('report.md').write_text(\n"
        f"    {report_text!r}.replace({value!r}, str(difference(Path('data.csv')))),\n"
        "    encoding='utf-8',\n"
        ")\n"
    )
    # Use the already-supported direct f-string form rather than the deliberately opaque replace
    # expression above; the marker remains present to prove the module was not executed.
    rendered_literal = report_text.replace(
        f"Difference: {value}", "Difference: {difference(Path('data.csv'))}"
    )
    analysis = analysis.split("Path('report.md').write_text(\n", 1)[0] + (
        f"Path('report.md').write_text(\n    f{rendered_literal!r},\n    encoding='utf-8',\n)\n"
    )
    (root / "analysis.py").write_text(analysis, encoding="utf-8")
    if second_result:
        (root / "second.csv").write_text("group,expression\n" + rows, encoding="utf-8")
        (root / "second.py").write_text(
            "from pathlib import Path\n"
            "import csv\n"
            "def other_difference(path):\n"
            "    rows = list(csv.DictReader(path.open()))\n"
            "    treated = [float(row['expression']) for row in rows if row['group'] == 'treated']\n"
            "    control = [float(row['expression']) for row in rows if row['group'] == 'control']\n"
            "    return sum(treated) / len(treated) - sum(control) / len(control)\n"
            "value = other_difference(Path('second.csv'))\n",
            encoding="utf-8",
        )
    return root / "SHOULD_NOT_EXIST"


def _audit(
    tmp_path: Path,
    schema_root: Path,
    **fixture: object,
) -> tuple[dict[str, object], Path, Path]:
    repository = tmp_path / "project"
    repository.mkdir()
    marker = _write_project(repository, **fixture)  # type: ignore[arg-type]
    output = tmp_path / "audit"
    bundle = run_audit(repository, output, schema_root, report="report.md")
    return bundle, output, marker


def test_opposite_sign_emits_evaluation_candidate_only(schema_root: Path, tmp_path: Path) -> None:
    bundle, output, marker = _audit(
        tmp_path,
        schema_root,
        result_direction="negative",
    )

    assert not marker.exists()
    assert bundle["findings"] == []
    assert {item["detector_id"] for item in bundle["detector_manifests"]} == {
        "detector:bounded-analysis-method-conflict",
        "detector:bounded-report-mean-direction",
        "detector:bounded-reported-method-contract-conflict",
    }
    assert len(bundle["detector_results"]) == 1
    result = bundle["detector_results"][0]
    assert result["state"] == "evaluation_finding_candidate"
    assert result["detector_maturity"] == "experimental"
    assert result["candidate"]["assessment_type"] == "finding"
    assert result["candidate"]["unresolved_material_premise_ids"] == []
    assert "-2.0 (negative)" in result["candidate"]["bounded_statement"]
    assert {item["status"] for item in result["counterevidence_execution"]} == {"completed"}
    assert {item["outcome"] for item in result["counterevidence_execution"]} == {
        "no_counterevidence"
    }
    assert result["coverage"]["status"] == "covered"
    assert (
        admit_finding(
            result,
            AdmissionContext(
                finding_draft={},
                source_references_resolved=True,
                detector_qualification_applies=True,
                wording_constraints_satisfied=True,
                expected_deterministic_input_digest=result["deterministic_input_digest"],
                required_counterevidence_check_ids=tuple(
                    item["check_id"] for item in result["counterevidence_execution"]
                ),
                non_inferences=("No broader scientific conclusion is established.",),
            ),
        )
        is None
    )
    assert all(
        execution["sandbox"]["project_code_executed"] is False
        for execution in bundle["executions"]
        if execution["execution_kind"] == "auditor_verification"
    )
    html = (output / "report.html").read_text(encoding="utf-8")
    assert "Experimental detector outputs" in html
    assert "production Finding permission:</strong> none" in html
    assert "Evaluation-only bounded statement" in html

    replayed = replay(output / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert replayed["detector_manifests"] == bundle["detector_manifests"]
    assert replayed["detector_results"] == bundle["detector_results"]
    assert replayed["findings"] == []


def test_matching_sign_is_covered_negative(schema_root: Path, tmp_path: Path) -> None:
    bundle, _, marker = _audit(
        tmp_path,
        schema_root,
        result_direction="positive",
    )

    assert not marker.exists()
    result = bundle["detector_results"][0]
    assert result["state"] == "no_issue_detected_within_coverage"
    assert result["coverage"] == {
        "status": "covered",
        "basis": result["applicability"]["basis"],
        "gaps": [],
    }
    assert "candidate" not in result
    assert bundle["findings"] == []


def test_hard_negative_unlinked_outcome_abstains(schema_root: Path, tmp_path: Path) -> None:
    bundle, _, _ = _audit(
        tmp_path,
        schema_root,
        result_direction="negative",
        reported_outcome="yield",
    )

    result = bundle["detector_results"][0]
    assert result["state"] == "insufficient_semantics"
    assert result["coverage"]["status"] == "not_covered"
    assert "one unique exact ObservedResult" in result["applicability"]["basis"]
    assert bundle["findings"] == []


def test_ambiguous_multiple_results_abstain(schema_root: Path, tmp_path: Path) -> None:
    bundle, _, _ = _audit(
        tmp_path,
        schema_root,
        result_direction="negative",
        second_result=True,
    )

    assert len(bundle["observed_results"]) == 2
    result = bundle["detector_results"][0]
    assert result["state"] == "insufficient_semantics"
    assert result["applicability"]["status"] == "uncertain"
    assert "one unique exact ObservedResult" in result["applicability"]["basis"]
    assert bundle["findings"] == []


def test_opposite_sibling_claim_suppresses_candidate(schema_root: Path, tmp_path: Path) -> None:
    bundle, _, _ = _audit(
        tmp_path,
        schema_root,
        result_direction="negative",
        opposite_sibling=True,
    )

    assert len(bundle["claims"]) == 2
    assert len(bundle["detector_results"]) == 2
    assert {item["state"] for item in bundle["detector_results"]} == {"insufficient_semantics"}
    for result in bundle["detector_results"]:
        check = result["counterevidence_execution"][0]
        assert check["check_id"] == "check:literal-report-conflict"
        assert check["status"] == "completed"
        assert check["outcome"] == "counterevidence_found"
        assert result["coverage"]["status"] == "not_covered"
    assert bundle["findings"] == []


def test_non_scalar_result_is_unsupported(schema_root: Path, tmp_path: Path) -> None:
    bundle, output, _ = _audit(
        tmp_path,
        schema_root,
        result_direction="positive",
    )
    locked = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))
    manifest = next(
        item
        for item in locked["detector_manifests"]
        if item["detector_id"] == BoundedReportMeanDirectionDetector.detector_id
    )
    detector = BoundedReportMeanDirectionDetector(manifest)
    changed = deepcopy(locked)
    changed["observed_results"][0]["value_kind"] = "table"
    changed["observed_results"][0].pop("scalar_value")

    result = detector.evaluate(changed, changed["claims"][0])

    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "unsupported_path"
    assert result["applicability"]["status"] == "not_applicable"
    assert result["applicability"]["unsupported_constructs"]
    assert bundle["findings"] == []


def test_manifest_and_input_mutations_change_or_fail_identity(
    schema_root: Path, tmp_path: Path
) -> None:
    bundle, output, _ = _audit(
        tmp_path,
        schema_root,
        result_direction="positive",
    )
    locked = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))
    manifest = next(
        item
        for item in locked["detector_manifests"]
        if item["detector_id"] == BoundedReportMeanDirectionDetector.detector_id
    )
    detector = BoundedReportMeanDirectionDetector(manifest)
    baseline = detector.evaluate(locked, locked["claims"][0])

    changed = deepcopy(locked)
    changed["observed_results"][0]["scalar_value"] = -2.0
    mutated = detector.evaluate(changed, changed["claims"][0])
    assert mutated["state"] == "evaluation_finding_candidate"
    assert mutated["deterministic_input_digest"] != baseline["deterministic_input_digest"]
    assert mutated["result_id"] != baseline["result_id"]

    drifted_manifest = deepcopy(manifest)
    drifted_manifest["implementation"]["implementation_digest"] = "sha256:" + "0" * 64
    with pytest.raises(BoundedDirectionDetectorError, match="implementation digest mismatch"):
        BoundedReportMeanDirectionDetector(drifted_manifest)

    drifted_bundle = deepcopy(bundle)
    drifted_bundle["detector_results"][0]["detector_manifest_digest"] = "sha256:" + "0" * 64
    with pytest.raises(ReportContractError, match="bundled DetectorManifest"):
        render_report_bytes(drifted_bundle)
