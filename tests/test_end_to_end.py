import json
import shutil
from copy import deepcopy

import pytest
import yaml

from sc_referee.controller import replay, run_demo
from sc_referee.reporting.html import render_report
from sc_referee.reporting.policy import ReportContractError


def test_demo_and_replay_are_semantically_identical(project_root, schema_root, tmp_path) -> None:
    fixture = project_root / "examples" / "walking-skeleton"
    first = tmp_path / "first"
    second = tmp_path / "second"
    bundle_one = run_demo(fixture, first, schema_root)
    bundle_two = replay(first / "semantic.lock.json", second, schema_root)
    assert bundle_one["detector_results"] == bundle_two["detector_results"]
    assert bundle_one["findings"] == bundle_two["findings"]
    assert bundle_one["conditional_concerns"] == bundle_two["conditional_concerns"]
    assert bundle_one["material_questions"] == bundle_two["material_questions"]
    assert bundle_one["disclosures"] == bundle_two["disclosures"]
    assert bundle_one["coverage_records"] == bundle_two["coverage_records"]
    for field in (
        "agent_reviews",
        "adjudicated_root_causes",
        "detector_evaluation_candidates",
        "stage3_comparison_reviews",
        "detector_case_outcomes",
        "qualification_metric_sets",
        "benchmark_adjudications",
        "benchmark_fixtures",
    ):
        assert bundle_one[field] == bundle_two[field] == []
    for name in ("operation.jsonl", "artifact.jsonl", "observed-result.jsonl"):
        assert (first / "observed" / name).read_bytes() == (second / "observed" / name).read_bytes()
    assert (first / "report.html").read_bytes() == (second / "report.html").read_bytes()
    assert (first / "report.html").exists()
    assert (first / "audit.db").exists()
    serialized = json.loads((first / "audit.bundle.json").read_text())
    assert len(serialized["findings"]) == 1
    assert len(serialized["conditional_concerns"]) == 1
    assert len(serialized["material_questions"]) == 1
    assert len(serialized["disclosures"]) == 1
    assert len(serialized["storage_manifests"]) == 1
    assert serialized["coverage_records"][0]["overall_status"] == "complete_within_plan"


def test_report_escapes_and_disclaims_correctness(project_root, schema_root, tmp_path) -> None:
    output = tmp_path / "audit"
    run_demo(project_root / "examples" / "walking-skeleton", output, schema_root)
    html = (output / "report.html").read_text()
    assert "not a determination that the analysis is correct" in html
    assert "publication-ready" in html
    assert "PROMPT INJECTION" not in html
    lowered = html.lower()
    assert "low risk" not in lowered
    assert "pass badge" not in lowered
    assert "https://" not in lowered
    assert "http://" not in lowered


def test_report_exposes_type_specific_impact_and_exact_source_navigation(
    project_root, schema_root, tmp_path
) -> None:
    output = tmp_path / "audit"
    run_demo(project_root / "examples" / "walking-skeleton", output, schema_root)
    html = (output / "report.html").read_text(encoding="utf-8")
    assert "Detector maturity:" in html
    assert "synthetic fixture simulation; no public qualification" in html
    assert "Direct entailment: satisfied" in html
    assert "Potential impact:" in html
    assert "Review priority:" in html
    assert "Importance:" in html
    assert 'href="#finding-1-evidence-1-source-1"' in html
    assert "Treatment increased expression relative to control." in html
    assert "return sum(treated) / len(treated) - sum(control) / len(control)" in html
    concern_section = html.split("Conditional concerns requiring scientific review", 1)[1].split(
        "Material questions", 1
    )[0]
    assert "Severity:" not in concern_section


def test_report_policy_rejects_strengthening_severity_leak_and_count_drift(
    project_root, schema_root, tmp_path
) -> None:
    bundle = run_demo(
        project_root / "examples" / "walking-skeleton", tmp_path / "audit", schema_root
    )

    strengthened = deepcopy(bundle)
    strengthened["findings"][0]["summary"] = "The biological conclusion is false."
    with pytest.raises(ReportContractError, match="prohibited report strengthening"):
        render_report(strengthened, tmp_path / "strengthened.html")

    severity_leak = deepcopy(bundle)
    severity_leak["conditional_concerns"][0]["severity"] = {"level": "critical"}
    with pytest.raises(ReportContractError, match="must not expose Finding severity"):
        render_report(severity_leak, tmp_path / "severity.html")

    count_drift = deepcopy(bundle)
    count_drift["coverage_records"][0]["assessment_counts"]["findings"] = 99
    with pytest.raises(ReportContractError, match="counts do not match"):
        render_report(count_drift, tmp_path / "counts.html")

    aggregate_drift = deepcopy(bundle)
    aggregate_drift["claims"][0]["lineage"]["status"] = "complete"
    with pytest.raises(ReportContractError, match="aggregate lineage is not derived"):
        render_report(aggregate_drift, tmp_path / "aggregate.html")

    grade_count_drift = deepcopy(bundle)
    grade_count_drift["coverage_records"][0]["claim_coverage"]["lineage_grade_counts"][
        "execution_origin"
    ]["missing"] = 99
    with pytest.raises(ReportContractError, match="grade counts do not match"):
        render_report(grade_count_drift, tmp_path / "grade-counts.html")

    typed_ref_drift = deepcopy(bundle)
    typed_ref_drift["claims"][0]["report_ref"]["record_id"] = "artifact:missing"
    with pytest.raises(ReportContractError, match="typed reference does not resolve"):
        render_report(typed_ref_drift, tmp_path / "typed-ref.html")


def test_demo_rejects_unmarked_repository(project_root, schema_root, tmp_path) -> None:
    source = project_root / "examples" / "walking-skeleton"
    copy = tmp_path / "unmarked"
    shutil.copytree(source, copy)
    lock_path = copy / "fixture.lock.yaml"
    lock = yaml.safe_load(lock_path.read_text())
    lock["fixture_mode"] = False
    lock_path.write_text(yaml.safe_dump(lock, sort_keys=False))
    with pytest.raises(ValueError, match="synthetic fixture"):
        run_demo(copy, tmp_path / "output", schema_root)


def test_demo_refuses_to_overwrite_existing_output(project_root, schema_root, tmp_path) -> None:
    output = tmp_path / "audit"
    output.mkdir()
    sentinel = output / "user-data.txt"
    sentinel.write_text("preserve me", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        run_demo(project_root / "examples" / "walking-skeleton", output, schema_root)

    assert sentinel.read_text(encoding="utf-8") == "preserve me"


def test_demo_replaces_fixture_assembled_claim_and_result_from_snapshot_sources(
    project_root, schema_root, tmp_path
) -> None:
    fixture = tmp_path / "fixture"
    shutil.copytree(project_root / "examples" / "walking-skeleton", fixture)
    lock_path = fixture / "fixture.lock.yaml"
    lock = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
    fixture_claim_id = lock["claim"]["claim_id"]
    lock["claim"]["text"] = "Fixture text that is not present in the report."
    lock["claim"]["proposition"]["direction"] = "negative"
    lock["observed_result"]["scalar_value"] = 999.0
    lock_path.write_text(yaml.safe_dump(lock, sort_keys=False), encoding="utf-8")

    output = tmp_path / "audit"
    bundle = run_demo(fixture, output, schema_root)
    semantic_lock = json.loads((output / "semantic.lock.json").read_text(encoding="utf-8"))

    assert bundle["claims"][0]["claim_id"] != fixture_claim_id
    assert bundle["claims"][0]["text"] == ("Treatment increased expression relative to control.")
    assert bundle["claims"][0]["proposition"]["direction"] == "positive"
    assert bundle["claims"][0]["extraction"]["method"] == "deterministic"
    assert semantic_lock["observed_result"]["scalar_value"] == pytest.approx(-0.42)
    assert semantic_lock["observed_graph"]["operations"]
    assert len(bundle["findings"]) == 1


def test_coverage_denominators_are_derived_and_do_not_overclaim_python_scope(
    project_root, schema_root, tmp_path
) -> None:
    fixture = tmp_path / "fixture"
    shutil.copytree(project_root / "examples" / "walking-skeleton", fixture)
    (fixture / "irrelevant.py").write_text("uninspected = True\n", encoding="utf-8")
    output = tmp_path / "audit"

    bundle = run_demo(fixture, output, schema_root)
    coverage = bundle["coverage_records"][0]
    file_records = [
        json.loads(line)
        for line in (output / "observed" / "files.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    inventory_paths = {record["path"] for record in file_records}
    deeply_inspected = set(coverage["extensions"]["x-deeply-inspected-paths"])

    assert coverage["inventory_summary"] == {
        "files_total": len(file_records),
        "files_classified": len(file_records),
        "files_deeply_inspected": 3,
    }
    assert set(coverage["uninspected_paths"]) == inventory_paths - deeply_inspected
    assert "irrelevant.py" in coverage["uninspected_paths"]
    assert coverage["scope"]["selection_envelope_included"] is False
    assert coverage["claim_coverage"]["claims_total"] == 1
    assert coverage["claim_coverage"]["claims_inspected"] == 1
    assert coverage["claim_coverage"]["claims_with_complete_lineage"] == 0
    assert coverage["claim_coverage"]["lineage_grade_counts"]["execution_origin"]["missing"] == 1
    parser_surfaces = {item["surface"] for item in coverage["parser_coverage"]}
    assert "parser:python-ast-tokenize:analysis.py" in parser_surfaces
    assert all("irrelevant.py" not in surface for surface in parser_surfaces)
    assert coverage["opaque_boundary_refs"]
