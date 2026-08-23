from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sc_referee.capability_matrix import (  # noqa: E402
    default_capability_manifest_root,
    generate_capability_matrix,
)
from sc_referee.controller import replay, run_demo  # noqa: E402
from sc_referee.detectors.method_conflict_grant_pins import (  # noqa: E402
    GRANT_PINS,
    installed_pin_matches_live_identity,
)
from sc_referee.qualification_grants import load_installed_qualification_grants  # noqa: E402
from sc_referee.records.schema_registry import LocalSchemaRegistry  # noqa: E402
from sc_referee.storage.integrity import (  # noqa: E402
    verify_sqlite_index,
    verify_storage_manifest,
)
from sc_referee.storage.layout import AuditLayout  # noqa: E402


def main() -> int:
    schema_root = ROOT / "reference" / "schemas-v0.20.0"
    count = LocalSchemaRegistry(schema_root).validate_example_directory()
    capability_matrix = generate_capability_matrix(default_capability_manifest_root(), schema_root)
    assert len(capability_matrix["entries"]) == 17
    assert capability_matrix["domain_wide_support_claim_allowed"] is False
    detector_entries = [
        detector for entry in capability_matrix["entries"] for detector in entry["detectors"]
    ]
    assert {item["detector_id"] for item in detector_entries} == {
        "detector:bounded-analysis-method-conflict",
        "detector:bounded-code-csv-dependence-conflict",
        "detector:bounded-feature-identifier-identity",
        "detector:bounded-report-mean-direction",
        "detector:bounded-reported-method-contract-conflict",
    }
    expected_binding_grants = [
        {
            "binding_id": "method-conflict-binding:complete-domain-exposure-denominator-v1",
            "check_id": "check:complete-domain-exposure-denominator",
            "qualification_ref": ("qualification:complete-domain-exposure-denominator-v207-round2"),
            "strongest_output_type": "finding",
        },
    ]
    retained_grants = load_installed_qualification_grants()
    dependence_binding_id = (
        "method-conflict-binding:"
        "authorized-independent-unit-entry-into-row-independent-procedure-v1"
    )
    dependence_grant = retained_grants[dependence_binding_id]
    assert {
        "binding_id": dependence_binding_id,
        "check_id": dependence_grant.grant["check_id"],
        "qualification_ref": dependence_grant.grant["qualification_id"],
        "strongest_output_type": "finding",
    } == {
        "binding_id": dependence_binding_id,
        "check_id": "check:authorized-independent-unit-entry-into-row-independent-procedure",
        "qualification_ref": "qualification:authorized-independent-unit-entry-v210-code-csv-envelope5",
        "strongest_output_type": "finding",
    }
    assert installed_pin_matches_live_identity(GRANT_PINS[dependence_binding_id]) is False
    method_detector = next(
        item
        for item in detector_entries
        if item["detector_id"] == "detector:bounded-analysis-method-conflict"
    )
    assert method_detector == {
        "detector_id": "detector:bounded-analysis-method-conflict",
        "maturity": "experimental",
        "qualification_ref": None,
        "strongest_output_type": "disclosure",
        "review_basis": "not_qualified",
        "binding_grants": expected_binding_grants,
    }
    code_detector = next(
        item
        for item in detector_entries
        if item["detector_id"] == "detector:bounded-code-csv-dependence-conflict"
    )
    assert code_detector == {
        "detector_id": "detector:bounded-code-csv-dependence-conflict",
        "maturity": "experimental",
        "qualification_ref": None,
        "strongest_output_type": "disclosure",
        "review_basis": "not_qualified",
    }
    assert all(
        item
        == {
            "detector_id": item["detector_id"],
            "maturity": "experimental",
            "qualification_ref": None,
            "strongest_output_type": "disclosure",
            "review_basis": "not_qualified",
        }
        for item in detector_entries
        if item is not method_detector and item is not code_detector
    )
    assert all(not entry["tested_versions"] for entry in capability_matrix["entries"])
    assert all(not entry["inferred_compatibility"] for entry in capability_matrix["entries"])
    obligation_entry = next(
        entry
        for entry in capability_matrix["entries"]
        if entry["entry_id"] == "capability:bounded-expected-count-unresolved-obligation-v1"
    )
    assert obligation_entry["detectors"] == []
    assert obligation_entry["operation_scope"] == [
        "bounded_expected_count_unresolved_obligation_v1"
    ]
    r_entries = [entry for entry in capability_matrix["entries"] if entry["language"] == "r"]
    assert {entry["package"] for entry in r_entries} == {"DESeq2", "edgeR", "limma"}
    assert all(entry["detectors"] == [] for entry in r_entries)
    bridge_entry = next(
        entry for entry in capability_matrix["entries"] if entry["language"] == "container_cell"
    )
    assert bridge_entry["operation_extraction"] == "partial"
    assert bridge_entry["semantic_modeling"] == "not_started"
    assert bridge_entry["detectors"] == []
    notebook_entry = next(
        entry for entry in capability_matrix["entries"] if entry["language"] == "jupyter_notebook"
    )
    assert notebook_entry["detectors"] == []
    assert notebook_entry["operation_extraction"] == "not_started"
    quarto_entry = next(
        entry for entry in capability_matrix["entries"] if entry["language"] == "quarto"
    )
    assert quarto_entry["detectors"] == []
    assert quarto_entry["operation_extraction"] == "not_started"
    assert quarto_entry["semantic_modeling"] == "not_started"
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        first = temp_root / "first"
        second = temp_root / "second"
        one = run_demo(ROOT / "examples" / "walking-skeleton", first, schema_root)
        two = replay(first / "semantic.lock.json", second, schema_root)
        assert one["detector_results"] == two["detector_results"]
        assert one["findings"] == two["findings"]
        assert one["conditional_concerns"] == two["conditional_concerns"]
        assert one["material_questions"] == two["material_questions"]
        assert one["disclosures"] == two["disclosures"]
        assert one["coverage_records"] == two["coverage_records"]
        assert one["claims"] == two["claims"]
        assert one["asset_identities"] == two["asset_identities"]
        assert one["file_records"] == two["file_records"]
        assert one["operations"] == two["operations"]
        assert one["artifacts"] == two["artifacts"]
        assert one["observed_results"] == two["observed_results"]
        for field in (
            "data_assets",
            "variables",
            "analysis_decisions",
            "selection_envelopes",
            "executions",
            "project_execution_authorizations",
            "environments",
            "agent_reviews",
            "adjudicated_root_causes",
            "detector_evaluation_candidates",
            "stage3_comparison_reviews",
            "detector_case_outcomes",
            "qualification_metric_sets",
            "benchmark_adjudications",
            "benchmark_fixtures",
        ):
            assert one[field] == two[field]
        assert len(one["findings"]) == 1
        assert len(one["conditional_concerns"]) == 1
        assert len(one["material_questions"]) == 1
        assert len(one["disclosures"]) == 1
        assert len(one["coverage_records"]) == 1
        assert len(one["storage_manifests"]) == 1
        assert len(one["parser_results"]) == 2
        assert len(one["audit_runs"]) == 8
        assert len(one["stage_results"]) == 7
        assert len(one["file_records"]) == 10
        assert len(one["operations"]) == 17
        assert len(one["artifacts"]) == 4
        assert len(one["observed_results"]) == 1
        assert len(one["reproduction_requests"]) == 0
        assert len(one["performance_records"]) == 0
        assert len(one["cache_entries"]) == 0
        assert len(one["cache_policies"]) == 0
        assert all(
            one[field] == []
            for field in (
                "data_assets",
                "variables",
                "analysis_decisions",
                "selection_envelopes",
                "executions",
                "project_execution_authorizations",
                "environments",
                "agent_reviews",
                "adjudicated_root_causes",
                "detector_evaluation_candidates",
                "stage3_comparison_reviews",
                "detector_case_outcomes",
                "qualification_metric_sets",
                "benchmark_adjudications",
                "benchmark_fixtures",
            )
        )
        verify_storage_manifest(AuditLayout(first), one["storage_manifests"][0])
        records = [record for value in one.values() if isinstance(value, list) for record in value]
        verify_sqlite_index(first / "audit.db", records)
        digest_one = hashlib.sha256(
            (first / "derived" / "detector-result.jsonl").read_bytes()
        ).hexdigest()
        digest_two = hashlib.sha256(
            (second / "derived" / "detector-result.jsonl").read_bytes()
        ).hexdigest()
        assert digest_one == digest_two
    summary = {
        "public_examples_validated": count,
        "public_schema_version": "0.20.0",
        "observed_plane_records": "public",
        "multidimensional_lineage_plane": "public",
        "walking_skeleton": "passed",
        "synthetic_findings": 1,
        "conditional_concerns": 1,
        "material_questions": 1,
        "disclosures": 1,
        "deterministic_replay": "passed",
        "storage_integrity": "passed",
        "generated_capability_matrix": "passed_fail_closed_manifest_profile",
        "capability_matrix_entries": len(capability_matrix["entries"]),
        "capability_matrix_detector_qualification": "one_live_exact_binding_grant",
        "capability_matrix_tested_versions": "none_declared",
        "public_detector_qualification": "binding_scoped_only",
    }
    (ROOT / "VALIDATION.txt").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
