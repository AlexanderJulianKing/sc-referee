from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from sc_referee.records.schema_registry import LocalSchemaRegistry
from scripts.build_root_cause_schema_release import RELEASE_VERSION, build_release
from scripts.migrate_v0_8_to_v0_9 import (
    PublicMigrationError,
    migrate_public_bundle,
    root_cause_candidate_id,
)


def _load(root: Path, name: str) -> dict[str, object]:
    return json.loads((root / "examples" / name).read_text(encoding="utf-8"))


def _v080_positive_bundle(root: Path) -> dict[str, object]:
    bundle = _load(root, "audit-bundle.example.json")
    stage1_template = _load(root, "agent-review.example.json")
    stage2_template = _load(root, "agent-review.stage2.example.json")
    stage1: list[dict[str, object]] = []
    stage2: list[dict[str, object]] = []
    for provider, suffix in (("Anthropic", "anthropic"), ("OpenAI", "openai")):
        for index in (1, 2):
            review = deepcopy(stage1_template)
            review["review_id"] = f"review:{suffix}:stage1:{index}"
            review["case_id"] = "case:migration-positive"
            reviewer = review["reviewer_agent"]
            assert isinstance(reviewer, dict)
            reviewer["provider"] = provider
            reviewer["execution_context_id"] = f"context:{suffix}:stage1:{index}"
            stage1.append(review)
        review = deepcopy(stage2_template)
        review["review_id"] = f"review:{suffix}:stage2:1"
        review["case_id"] = "case:migration-positive"
        reviewer = review["reviewer_agent"]
        assert isinstance(reviewer, dict)
        reviewer["provider"] = provider
        reviewer["execution_context_id"] = f"context:{suffix}:stage2:1"
        stage2.append(review)

    adjudication = _load(root, "benchmark-adjudication.example.json")
    adjudication["case_id"] = "case:migration-positive"
    adjudication["adjudication_id"] = "benchmark-adjudication:migration-positive"
    adjudication["stage1_review_refs"] = [
        {"record_type": "agent_review", "record_id": review["review_id"]} for review in stage1
    ]
    adjudication["stage2_review_refs"] = [
        {"record_type": "agent_review", "record_id": review["review_id"]} for review in stage2
    ]

    fixture = _load(root, "benchmark-fixture.example.json")
    fixture["fixture_id"] = "fixture:migration-positive"
    fixture["fixture_kind"] = "positive_issue_fixture"
    fixture["expected_issue_labels"] = ["claim_result_agreement"]
    proof = fixture["proof_obligations"]
    assert isinstance(proof, dict)
    proof["positive_root_cause_documented"] = True
    fixture["adjudication_ref"] = {
        "record_type": "benchmark_adjudication",
        "record_id": adjudication["adjudication_id"],
    }

    bundle["agent_reviews"] = [*stage1, *stage2]
    bundle["benchmark_adjudications"] = [adjudication]
    bundle["benchmark_fixtures"] = [fixture]
    return bundle


def test_committed_root_cause_release_is_accepted_exact_v090(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.9.0"
    status = json.loads((release / "RELEASE_STATUS.json").read_text(encoding="utf-8"))
    assert status == {
        "accepted": True,
        "baseline_version": "0.8.0",
        "public_release": True,
        "release_version": "0.9.0",
        "source_adr": ("docs/implementation/ADR-0008-CANONICAL-ROOT-CAUSE-RECONCILIATION.md"),
    }
    assert RELEASE_VERSION == "0.9.0"
    assert LocalSchemaRegistry(release).validate_example_directory() == 63


def test_root_cause_release_manifest_binds_every_file(project_root: Path) -> None:
    release = project_root / "reference" / "schemas-v0.9.0"
    manifest = {}
    for line in (release / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", maxsplit=1)
        manifest[relative] = digest
    actual = {
        path.relative_to(release).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in release.rglob("*")
        if path.is_file()
        and path.name != "MANIFEST.sha256"
        and not any(part.startswith(".") or part == "__pycache__" for part in path.parts)
    }
    assert manifest == actual


def test_root_cause_release_builder_is_reproducible_and_preserves_v080(
    project_root: Path, tmp_path: Path
) -> None:
    baseline_manifest = project_root / "reference" / "schemas-v0.8.0" / "MANIFEST.sha256"
    before = baseline_manifest.read_bytes()
    output = tmp_path / "schemas-v0.9.0"
    assert build_release(output) == 63
    committed = project_root / "reference" / "schemas-v0.9.0"
    generated_files = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    committed_files = {
        path.relative_to(committed).as_posix(): path.read_bytes()
        for path in committed.rglob("*")
        if path.is_file()
        and not any(part.startswith(".") or part == "__pycache__" for part in path.parts)
    }
    assert generated_files == committed_files
    assert baseline_manifest.read_bytes() == before


def test_public_v080_positive_migration_invents_no_root_cause_equivalence(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.8.0"
    target_root = project_root / "reference" / "schemas-v0.9.0"
    source = _v080_positive_bundle(source_root)
    source_path = tmp_path / "source-v080.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    bundle = migrate_public_bundle(source_path, source_root, target_root, tmp_path / "migration")

    LocalSchemaRegistry(target_root).validate(bundle)
    assert bundle["schema_version"] == "0.9.0"
    assert bundle["adjudicated_root_causes"] == []
    stage1 = [review for review in bundle["agent_reviews"] if review["stage"] == "stage1_blind"]
    stage2 = [
        review
        for review in bundle["agent_reviews"]
        if review["stage"] == "stage2_scientific_adjudication"
    ]
    assert all(
        review["root_cause_identity"]["candidate_root_cause_id"] == root_cause_candidate_id(review)
        for review in stage1
    )
    assert all(review["verdict"] == "insufficient_evidence" for review in stage2)
    assert all(review["root_cause_identity"] is None for review in stage2)
    adjudication = bundle["benchmark_adjudications"][0]
    assert adjudication["label_status"] == "insufficient_evidence"
    assert adjudication["adjudicated_root_cause_refs"] == []
    assert adjudication["root_cause_reconciliation_status"] == "unresolved"
    assert "bounded_root_cause_statement" not in adjudication
    fixture = bundle["benchmark_fixtures"][0]
    assert fixture["fixture_kind"] == "ambiguous_fixture"
    assert fixture["expected_issue_labels"] == []
    assert fixture["expected_root_cause_refs"] == []
    report = json.loads(
        (tmp_path / "migration" / "MIGRATION_REPORT.json").read_text(encoding="utf-8")
    )
    assert report["stage2_reconciliation_invented"] is False
    assert report["root_cause_equivalence_invented"] is False
    assert report["legacy_positive_labels_admitted"] is False


def test_public_v080_migration_rejects_mixed_schema_versions(
    project_root: Path, tmp_path: Path
) -> None:
    source_root = project_root / "reference" / "schemas-v0.8.0"
    target_root = project_root / "reference" / "schemas-v0.9.0"
    source = _load(source_root, "audit-bundle.example.json")
    claims = source["claims"]
    assert isinstance(claims, list)
    claims[0]["schema_version"] = "0.7.0"
    source_path = tmp_path / "mixed.json"
    source_path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(PublicMigrationError, match="Mixed or unsupported"):
        migrate_public_bundle(source_path, source_root, target_root, tmp_path / "rejected")
