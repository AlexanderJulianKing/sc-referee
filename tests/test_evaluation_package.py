from __future__ import annotations

import ast
import json
import os
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation import EvaluationValidationError, validate_case_packet
from sc_referee_evaluation.capture import capture_review_submission
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.fixture import FixtureGenerationError, generate_positive_fixture
from sc_referee_evaluation.review_protocol import (
    build_stage1_review_packet,
    build_stage2_review_packet,
    freeze_stage1_panel,
)
from sc_referee_evaluation.root_cause import build_adjudicated_root_cause
from sc_referee_evaluation.workspace import build_blind_workspace

from sc_referee.controller import run_demo
from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.records.observed import build_file_records
from sc_referee.records.root_cause import root_cause_candidate_id, root_cause_candidate_ref
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.reporting.html import render_report
from sc_referee.reporting.policy import ReportContractError
from sc_referee.snapshot.repository import capture_repository


def _load_example(project_root: Path, name: str) -> dict[str, Any]:
    path = project_root / "reference" / "schemas-v0.18.0" / "examples" / name
    return json.loads(path.read_text(encoding="utf-8"))


def _positive_case_packet(
    project_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    stage1_template = _load_example(project_root, "agent-review.example.json")
    stage2_template = _load_example(project_root, "agent-review.stage2.example.json")
    reviews: list[dict[str, Any]] = []
    for provider, model, surface in (
        ("Anthropic", "claude-opus-5", "Claude Code"),
        ("OpenAI", "gpt-5.6-sol", "Codex"),
    ):
        for index in (1, 2):
            review = deepcopy(stage1_template)
            review["review_id"] = f"review:{provider.lower()}:stage1:{index}"
            review["case_id"] = "case:bounded-positive"
            review["reviewer_agent"].update(
                {
                    "provider": provider,
                    "model_id": model,
                    "agent_surface": surface,
                    "execution_context_id": f"context:{provider.lower()}:stage1:{index}",
                }
            )
            review["completed_at"] = f"2026-07-27T18:0{index}:00Z"
            review["root_cause_identity"]["candidate_root_cause_id"] = root_cause_candidate_id(
                review
            )
            reviews.append(review)
        review = deepcopy(stage2_template)
        review["review_id"] = f"review:{provider.lower()}:stage2:1"
        review["case_id"] = "case:bounded-positive"
        review["reviewer_agent"].update(
            {
                "provider": provider,
                "model_id": model,
                "agent_surface": surface,
                "execution_context_id": f"context:{provider.lower()}:stage2:1",
            }
        )
        review["completed_at"] = "2026-07-27T18:30:00Z"
        reviews.append(review)

    adjudication = _load_example(project_root, "benchmark-adjudication.example.json")
    adjudication["adjudication_id"] = "benchmark-adjudication:bounded-positive"
    adjudication["case_id"] = "case:bounded-positive"
    adjudication["stage1_review_refs"] = [
        {"record_type": "agent_review", "record_id": review["review_id"]}
        for review in reviews
        if review["stage"] == "stage1_blind"
    ]
    adjudication["stage2_review_refs"] = [
        {"record_type": "agent_review", "record_id": review["review_id"]}
        for review in reviews
        if review["stage"] == "stage2_scientific_adjudication"
    ]

    fixture = _load_example(project_root, "benchmark-fixture.example.json")
    fixture.update(
        {
            "fixture_id": "fixture:bounded-positive",
            "fixture_kind": "positive_issue_fixture",
            "qualification_proof_status": "legacy_proof_projection_unavailable",
            "proof_evidence": None,
            "execution_evidence": "not_executed",
            "expected_issue_labels": ["claim_result_agreement"],
            "scientific_contract_refs": [],
            "adjudication_ref": {
                "record_type": "benchmark_adjudication",
                "record_id": adjudication["adjudication_id"],
            },
        }
    )
    fixture["proof_obligations"]["positive_root_cause_documented"] = True
    root_cause = _refresh_root_cause(project_root, fixture, adjudication, reviews)
    return fixture, adjudication, reviews, root_cause


def _refresh_root_cause(
    project_root: Path,
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    reviews: list[dict[str, Any]],
) -> dict[str, Any]:
    stage1 = [review for review in reviews if review["stage"] == "stage1_blind"]
    stage2 = [review for review in reviews if review["stage"] == "stage2_scientific_adjudication"]
    for review in stage1:
        review["root_cause_identity"]["candidate_root_cause_id"] = root_cause_candidate_id(review)
    selected: dict[str, dict[str, Any]] = {}
    for review in stage1:
        selected.setdefault(
            str(review["reviewer_agent"]["provider"]), root_cause_candidate_ref(review)
        )
    candidate_refs = sorted(
        selected.values(), key=lambda item: str(item["review_ref"]["record_id"])
    )
    for review in stage2:
        review["root_cause_identity"]["reconciled_stage1_candidates"] = deepcopy(candidate_refs)
        review["root_cause_identity"]["candidate_root_cause_id"] = root_cause_candidate_id(review)
    root_cause = build_adjudicated_root_cause(
        stage1,
        stage2,
        project_root / "reference" / "schemas-v0.18.0",
        adjudicated_at=str(adjudication["adjudicated_at"]),
        statement_source_review_id=str(stage2[0]["review_id"]),
        required_scientific_premises=["The report and result use the same contrast orientation."],
        stronger_claims_excluded=["No global workflow correctness claim is established."],
    )
    root_ref = {
        "record_type": "adjudicated_root_cause",
        "record_id": root_cause["adjudicated_root_cause_id"],
    }
    adjudication["adjudicated_root_cause_refs"] = [deepcopy(root_ref)]
    fixture["expected_root_cause_refs"] = [deepcopy(root_ref)]
    proof = fixture.get("proof_evidence")
    if isinstance(proof, dict):
        proof["public_inputs"]["adjudicated_root_causes"] = [
            {
                "record_ref": deepcopy(root_ref),
                "semantic_digest": semantic_digest(root_cause),
            }
        ]
    return root_cause


def _replace_typed_record_id(value: Any, record_type: str, record_id: str) -> None:
    if isinstance(value, dict):
        if value.get("record_type") == record_type and "record_id" in value:
            value["record_id"] = record_id
            return
        for item in value.values():
            _replace_typed_record_id(item, record_type, record_id)
    elif isinstance(value, list):
        for item in value:
            _replace_typed_record_id(item, record_type, record_id)


def test_answer_side_packet_reconciles_without_admitting_an_unverified_label(
    project_root: Path, schema_root: Path
) -> None:
    fixture, adjudication, reviews, root_cause = _positive_case_packet(project_root)

    report = validate_case_packet(
        fixture,
        adjudication,
        reviews,
        schema_root,
        adjudicated_root_causes=[root_cause],
    )

    assert report["panel_consistency"] == "consistent"
    assert report["label_status"] == "positive_demonstrated"
    assert report["label_admission"] == "withheld_pending_independent_evidence_checks"
    assert report["provider_participation"] == {
        "Anthropic": {"stage1": 2, "stage2": 1, "distinct_contexts": 3},
        "OpenAI": {"stage1": 2, "stage2": 1, "distinct_contexts": 3},
    }
    assert set(report["unverified_checks"]) == {
        "source_references_resolve_against_fixture_snapshot",
    }


def test_answer_side_cli_persists_a_deterministic_validation_report(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    fixture, adjudication, reviews, root_cause = _positive_case_packet(project_root)
    fixture_path = tmp_path / "fixture.json"
    adjudication_path = tmp_path / "adjudication.json"
    reviews_path = tmp_path / "reviews.jsonl"
    fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
    adjudication_path.write_text(json.dumps(adjudication), encoding="utf-8")
    reviews_path.write_text(
        "".join(json.dumps(review) + "\n" for review in reviews), encoding="utf-8"
    )
    roots_path = tmp_path / "adjudicated-root-causes.jsonl"
    roots_path.write_text(json.dumps(root_cause) + "\n", encoding="utf-8")
    output = tmp_path / "validation.json"

    exit_code = evaluation_main(
        [
            "validate-case",
            "--fixture",
            str(fixture_path),
            "--adjudication",
            str(adjudication_path),
            "--reviews-jsonl",
            str(reviews_path),
            "--adjudicated-root-causes-jsonl",
            str(roots_path),
            "--schema-root",
            str(schema_root),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["evaluation_protocol_version"] == "0.2.0"
    assert persisted["label_admission"] == "withheld_pending_independent_evidence_checks"
    digest = persisted.pop("validation_report_digest")
    assert digest == semantic_digest(persisted)
    assert output.read_bytes().endswith(b"\n")
    original = output.read_bytes()
    assert (
        evaluation_main(
            [
                "validate-case",
                "--fixture",
                str(fixture_path),
                "--adjudication",
                str(adjudication_path),
                "--reviews-jsonl",
                str(reviews_path),
                "--adjudicated-root-causes-jsonl",
                str(roots_path),
                "--schema-root",
                str(schema_root),
                "--output",
                str(output),
            ]
        )
        == 2
    )
    assert output.read_bytes() == original


def test_answer_side_packet_rejects_reused_execution_context(
    project_root: Path, schema_root: Path
) -> None:
    fixture, adjudication, reviews, root_cause = _positive_case_packet(project_root)
    reviews[-1]["reviewer_agent"]["execution_context_id"] = reviews[0]["reviewer_agent"][
        "execution_context_id"
    ]

    with pytest.raises(EvaluationValidationError, match="execution context"):
        validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            adjudicated_root_causes=[root_cause],
        )


def test_answer_side_packet_rejects_material_dissent_hidden_by_adjudication(
    project_root: Path, schema_root: Path
) -> None:
    fixture, adjudication, reviews, root_cause = _positive_case_packet(project_root)
    stage2 = next(
        review for review in reviews if review["stage"] == "stage2_scientific_adjudication"
    )
    stage2["falsification_attempt"]["material_dissent"] = True
    stage2["falsification_attempt"]["outcome"] = "unresolved"

    with pytest.raises(EvaluationValidationError, match="material dissent"):
        validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            adjudicated_root_causes=[root_cause],
        )


def test_answer_side_packet_rejects_fixture_label_mismatch(
    project_root: Path, schema_root: Path
) -> None:
    fixture, adjudication, reviews, root_cause = _positive_case_packet(project_root)
    fixture["fixture_kind"] = "ambiguous_fixture"
    fixture["qualification_proof_status"] = "excluded_label"
    fixture["proof_evidence"] = None

    with pytest.raises(EvaluationValidationError, match="expected_root_cause_refs"):
        validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            adjudicated_root_causes=[root_cause],
        )


def test_positive_packet_rejects_missing_or_mutated_canonical_root_cause(
    project_root: Path, schema_root: Path
) -> None:
    fixture, adjudication, reviews, root_cause = _positive_case_packet(project_root)

    with pytest.raises(EvaluationValidationError, match="exactly one canonical root cause"):
        validate_case_packet(fixture, adjudication, reviews, schema_root)

    mutated = deepcopy(root_cause)
    mutated["adjudicated_root_cause_id"] = "adjudicated-root-cause:mutated"
    mutated_ref = {
        "record_type": "adjudicated_root_cause",
        "record_id": mutated["adjudicated_root_cause_id"],
    }
    fixture["expected_root_cause_refs"] = [deepcopy(mutated_ref)]
    adjudication["adjudicated_root_cause_refs"] = [deepcopy(mutated_ref)]
    with pytest.raises(EvaluationValidationError, match="deterministic reconciliation"):
        validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            adjudicated_root_causes=[mutated],
        )


def test_candidate_content_mutation_or_stage2_set_disagreement_abstains(
    project_root: Path, schema_root: Path
) -> None:
    fixture, adjudication, reviews, root_cause = _positive_case_packet(project_root)
    content_mutation = deepcopy(reviews)
    content_mutation[0]["bounded_statement"] += " Mutated after identity creation."
    with pytest.raises(EvaluationValidationError, match="candidate ID"):
        validate_case_packet(
            fixture,
            adjudication,
            content_mutation,
            schema_root,
            adjudicated_root_causes=[root_cause],
        )

    stage1 = [review for review in reviews if review["stage"] == "stage1_blind"]
    stage2 = [review for review in reviews if review["stage"] == "stage2_scientific_adjudication"]
    replacement = next(
        review
        for review in stage1
        if review["reviewer_agent"]["provider"] == "Anthropic"
        and review["review_id"]
        != stage2[1]["root_cause_identity"]["reconciled_stage1_candidates"][0]["review_ref"][
            "record_id"
        ]
    )
    stage2[1]["root_cause_identity"]["reconciled_stage1_candidates"][0] = root_cause_candidate_ref(
        replacement
    )
    with pytest.raises(EvaluationValidationError, match="identical Stage-1 candidate set"):
        validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            adjudicated_root_causes=[root_cause],
        )


def test_canonical_root_cause_is_bundle_valid_and_reported_without_becoming_a_finding(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    fixture, adjudication, reviews, _root_cause = _positive_case_packet(project_root)
    bundle = run_demo(
        project_root / "examples" / "walking-skeleton", tmp_path / "audit", schema_root
    )
    claim_id = str(bundle["claims"][0]["claim_id"])
    for record in [fixture, *reviews]:
        _replace_typed_record_id(record, "claim", claim_id)
    fixture["snapshot_ref"] = {
        "record_type": "repository_snapshot",
        "record_id": bundle["repository_snapshots"][0]["snapshot_id"],
    }
    fixture["declared_scope"]["operation_refs"] = []
    root_cause = _refresh_root_cause(project_root, fixture, adjudication, reviews)
    bundle["agent_reviews"] = reviews
    bundle["adjudicated_root_causes"] = [root_cause]
    bundle["benchmark_adjudications"] = [adjudication]
    bundle["benchmark_fixtures"] = [fixture]

    LocalSchemaRegistry(schema_root).validate(bundle)
    report_path = tmp_path / "root-cause-report.html"
    render_report(bundle, report_path)
    html = report_path.read_text(encoding="utf-8")
    assert "Answer-side adjudicated root causes" in html
    assert root_cause["bounded_statement"] in html
    assert root_cause["adjudicated_root_cause_id"] in html
    assert "They are not Findings in this audit" in html
    assert "Anthropic, OpenAI" in html
    assert "not represented as human expert review" in html
    assert len(bundle["findings"]) == 1

    disclosure_drift = deepcopy(bundle)
    disclosure_drift["benchmark_adjudications"][0]["agent_only_disclosure"] = "Reviewed by experts."
    with pytest.raises(ReportContractError, match="non-human-expert disclosure"):
        render_report(disclosure_drift, tmp_path / "disclosure-drift.html")


def test_answer_side_source_refs_resolve_against_immutable_fixture_snapshot(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    fixture, adjudication, reviews, _root_cause = _positive_case_packet(project_root)
    repository = tmp_path / "fixture"
    repository.mkdir()
    source_text = "effect = -0.42\n"
    (repository / "analysis.py").write_text(source_text, encoding="utf-8")
    snapshot = capture_repository(
        repository,
        tmp_path / "captured",
        "audit:evaluation-fixture",
        captured_at="2026-07-27T17:00:00Z",
    )
    public_files = build_file_records(
        snapshot.file_records,
        snapshot.asset_identity_records,
        str(snapshot.snapshot_record["snapshot_id"]),
        "2026-07-27T17:00:00Z",
    )
    fixture["snapshot_ref"] = {
        "record_type": "repository_snapshot",
        "record_id": snapshot.snapshot_record["snapshot_id"],
    }
    source_ref = {
        "source_kind": "file_span",
        "locator": "analysis.py:1",
        "path": "analysis.py",
        "content_digest": sha256_digest(source_text.encode("utf-8")),
        "start_line": 1,
        "end_line": 1,
        "start_column": 1,
        "end_column": 15,
        "quoted_text": "effect = -0.42",
    }
    for review in reviews:
        for evidence in review["evidence"]:
            evidence["source_refs"] = [deepcopy(source_ref)]
        falsification = review.get("falsification_attempt")
        if falsification is not None:
            for evidence in falsification["evidence_tested"]:
                evidence["source_refs"] = [deepcopy(source_ref)]
        identity = review.get("root_cause_identity")
        if isinstance(identity, dict):
            for evidence in identity["equivalence_evidence"]:
                evidence["source_refs"] = [deepcopy(source_ref)]
    root_cause = _refresh_root_cause(project_root, fixture, adjudication, reviews)

    report = validate_case_packet(
        fixture,
        adjudication,
        reviews,
        schema_root,
        adjudicated_root_causes=[root_cause],
        snapshot=snapshot.snapshot_record,
        file_records=public_files,
        asset_identities=snapshot.asset_identity_records,
        materialized_root=snapshot.materialized_root,
    )

    assert report["resolved_source_ref_count"] == 10
    assert report["unverified_checks"] == []
    assert report["label_admission"] == "admitted_for_declared_fixture_scope"
    assert "source_references_resolve_against_fixture_snapshot" in report["independently_checked"]


def test_positive_fixture_is_compiled_only_from_admitted_exact_panel_evidence(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed_fixture, adjudication, reviews, _root_cause = _positive_case_packet(project_root)
    repository = tmp_path / "positive-source"
    repository.mkdir()
    source_text = "effect = -0.42\n"
    (repository / "analysis.py").write_text(source_text, encoding="utf-8")
    snapshot = capture_repository(
        repository,
        tmp_path / "positive-captured",
        "audit:positive-fixture",
        captured_at="2026-07-27T17:00:00Z",
    )
    public_files = build_file_records(
        snapshot.file_records,
        snapshot.asset_identity_records,
        str(snapshot.snapshot_record["snapshot_id"]),
        "2026-07-27T17:00:00Z",
    )
    source_ref = {
        "source_kind": "file_span",
        "locator": "analysis.py:1",
        "path": "analysis.py",
        "content_digest": sha256_digest(source_text.encode("utf-8")),
        "start_line": 1,
        "end_line": 1,
        "start_column": 1,
        "end_column": 15,
        "quoted_text": "effect = -0.42",
    }
    for review in reviews:
        for evidence in review["evidence"]:
            evidence["source_refs"] = [deepcopy(source_ref)]
        falsification = review.get("falsification_attempt")
        if isinstance(falsification, dict):
            for evidence in falsification["evidence_tested"]:
                evidence["source_refs"] = [deepcopy(source_ref)]
        identity = review.get("root_cause_identity")
        if isinstance(identity, dict):
            for evidence in identity["equivalence_evidence"]:
                evidence["source_refs"] = [deepcopy(source_ref)]
    root_cause = _refresh_root_cause(project_root, seed_fixture, adjudication, reviews)
    fixture_spec = {
        "problem_id": "problem:positive-compiler",
        "declared_scope": {
            "claim_refs": [],
            "detector_ids": ["detector:claim-sign"],
            "issue_classes": [root_cause["issue_class"]],
            "operation_refs": [],
        },
        "scientific_contract_refs": [],
        "limitations": ["The fixture is limited to the declared detector and issue class."],
    }
    workspace_manifest_path = tmp_path / "positive-workspace.manifest.json"
    workspace_manifest = build_blind_workspace(
        snapshot.materialized_root,
        tmp_path / "positive-workspace",
        workspace_manifest_path,
        [{"path": "analysis.py", "role": "workflow_source"}],
        snapshot=snapshot.snapshot_record,
        file_records=public_files,
        asset_identities=snapshot.asset_identity_records,
        created_at="2026-07-27T17:05:00Z",
    )
    stage1_reviews = [review for review in reviews if review["stage"] == "stage1_blind"]
    stage2_reviews = [
        review for review in reviews if review["stage"] == "stage2_scientific_adjudication"
    ]
    stage1_packets: list[dict[str, Any]] = []
    stage1_manifests: list[dict[str, Any]] = []
    stage1_capture_paths: list[Path] = []
    for index, review in enumerate(stage1_reviews, start=1):
        packet = build_stage1_review_packet(
            str(review["case_id"]),
            workspace_manifest,
            review["reviewer_agent"],
            "Review only the supplied scientific workflow.",
            created_at="2026-07-27T17:10:00Z",
        )
        review["reviewer_agent"] = deepcopy(packet["expected_reviewer_agent"])
        review["extensions"] = {"x-review-packet-digest": packet["packet_digest"]}
        transcript = tmp_path / f"positive-stage1-{index}.transcript.txt"
        transcript.write_text(f"Synthetic positive Stage-1 transcript {index}.\n", encoding="utf-8")
        review["transcript_digest"] = sha256_digest(transcript.read_bytes())
        capture_path = tmp_path / f"positive-stage1-{index}.capture"
        manifest = capture_review_submission(
            review,
            packet,
            transcript,
            schema_root,
            captured_at="2026-07-27T18:05:00Z",
            destination=capture_path,
        )
        stage1_packets.append(packet)
        stage1_manifests.append(manifest)
        stage1_capture_paths.append(capture_path)
    stage1_freeze_path = tmp_path / "positive-stage1.freeze.json"
    stage1_freeze = freeze_stage1_panel(
        stage1_reviews,
        stage1_packets,
        stage1_manifests,
        schema_root,
        frozen_at="2026-07-27T18:10:00Z",
        output=stage1_freeze_path,
    )
    stage2_capture_paths: list[Path] = []
    for index, review in enumerate(stage2_reviews, start=1):
        packet = build_stage2_review_packet(
            stage1_freeze,
            stage1_reviews,
            review["reviewer_agent"],
            "Adjudicate the frozen scientific panel.",
            created_at="2026-07-27T18:11:00Z",
            answer_side_evidence_refs=[],
            reference_analysis_refs=[],
            execution_comparison_refs=[],
        )
        review["reviewer_agent"] = deepcopy(packet["expected_reviewer_agent"])
        review["extensions"] = {
            "x-review-packet-digest": packet["packet_digest"],
            "x-stage1-freeze-digest": stage1_freeze["freeze_digest"],
        }
        transcript = tmp_path / f"positive-stage2-{index}.transcript.txt"
        transcript.write_text(f"Synthetic positive Stage-2 transcript {index}.\n", encoding="utf-8")
        review["transcript_digest"] = sha256_digest(transcript.read_bytes())
        capture_path = tmp_path / f"positive-stage2-{index}.capture"
        capture_review_submission(
            review,
            packet,
            transcript,
            schema_root,
            captured_at="2026-07-27T18:40:00Z",
            destination=capture_path,
        )
        stage2_capture_paths.append(capture_path)

    fixture = generate_positive_fixture(
        adjudication,
        stage1_capture_paths,
        stage2_capture_paths,
        stage1_freeze,
        [workspace_manifest],
        [root_cause],
        snapshot.snapshot_record,
        public_files,
        snapshot.asset_identity_records,
        snapshot.materialized_root,
        fixture_spec,
        schema_root,
        created_at="2026-07-27T20:00:00Z",
        output=tmp_path / "positive-fixture.json",
    )

    assert fixture["fixture_kind"] == "positive_issue_fixture"
    assert fixture["corpus_partition"] == "public_development"
    assert fixture["execution_evidence"] == "not_executed"
    assert fixture["expected_issue_labels"] == [root_cause["issue_class"]]
    assert fixture["expected_root_cause_refs"] == adjudication["adjudicated_root_cause_refs"]
    assert fixture["proof_obligations"]["positive_root_cause_documented"] is True
    assert fixture["qualification_proof_status"] == "complete"
    assert len(fixture["proof_evidence"]["protocol_artifacts"]["review_captures"]) == 6
    assert fixture["global_correctness_claim_allowed"] is False

    input_records = {
        "adjudication": adjudication,
        "snapshot": snapshot.snapshot_record,
        "fixture-spec": fixture_spec,
        "root": root_cause,
    }
    input_paths: dict[str, Path] = {}
    for label, record in input_records.items():
        path = tmp_path / f"positive-{label}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        input_paths[label] = path
    file_records_path = tmp_path / "positive-file-records.jsonl"
    file_records_path.write_text(
        "".join(json.dumps(record) + "\n" for record in public_files), encoding="utf-8"
    )
    identities_path = tmp_path / "positive-asset-identities.jsonl"
    identities_path.write_text(
        "".join(json.dumps(record) + "\n" for record in snapshot.asset_identity_records),
        encoding="utf-8",
    )
    stage_arguments: list[str] = []
    for capture_path in stage1_capture_paths:
        stage_arguments.extend(["--stage1-capture", str(capture_path)])
    for capture_path in stage2_capture_paths:
        option = "--stage2-capture"
        stage_arguments.extend([option, str(capture_path)])
    cli_output = tmp_path / "positive-fixture-cli.json"
    assert (
        evaluation_main(
            [
                "generate-positive-fixture",
                "--adjudication",
                str(input_paths["adjudication"]),
                *stage_arguments,
                "--stage1-freeze",
                str(stage1_freeze_path),
                "--workspace-manifest",
                str(workspace_manifest_path),
                "--adjudicated-root-cause",
                str(input_paths["root"]),
                "--snapshot",
                str(input_paths["snapshot"]),
                "--file-records-jsonl",
                str(file_records_path),
                "--asset-identities-jsonl",
                str(identities_path),
                "--materialized-root",
                str(snapshot.materialized_root),
                "--fixture-spec",
                str(input_paths["fixture-spec"]),
                "--schema-root",
                str(schema_root),
                "--created-at",
                "2026-07-27T20:00:00Z",
                "--output",
                str(cli_output),
            ]
        )
        == 0
    )
    assert cli_output.read_bytes() == (tmp_path / "positive-fixture.json").read_bytes()

    drifted_capture = tmp_path / "drifted-positive-stage1.capture"
    shutil.copytree(stage1_capture_paths[0], drifted_capture)
    drifted_review_path = drifted_capture / "review.json"
    drifted_review = json.loads(drifted_review_path.read_text(encoding="utf-8"))
    drifted_review["evidence"][0]["source_refs"][0]["content_digest"] = "sha256:" + "00" * 32
    drifted_review_path.write_text(json.dumps(drifted_review), encoding="utf-8")
    drifted_stage1_paths = [drifted_capture, *stage1_capture_paths[1:]]
    with pytest.raises(FixtureGenerationError, match=r"candidate ID|digest|manifest"):
        generate_positive_fixture(
            adjudication,
            drifted_stage1_paths,
            stage2_capture_paths,
            stage1_freeze,
            [workspace_manifest],
            [root_cause],
            snapshot.snapshot_record,
            public_files,
            snapshot.asset_identity_records,
            snapshot.materialized_root,
            fixture_spec,
            schema_root,
            created_at="2026-07-27T20:00:00Z",
            output=tmp_path / "drifted-positive-fixture.json",
        )

    race_output = tmp_path / "raced-positive-fixture.json"
    real_link = os.link

    def competing_link(source: str, destination: str, *, follow_symlinks: bool = True) -> None:
        Path(destination).write_bytes(b"incumbent\n")
        real_link(source, destination, follow_symlinks=follow_symlinks)

    monkeypatch.setattr("sc_referee.storage.atomic.os.link", competing_link)
    with pytest.raises(FileExistsError):
        generate_positive_fixture(
            adjudication,
            stage1_capture_paths,
            stage2_capture_paths,
            stage1_freeze,
            [workspace_manifest],
            [root_cause],
            snapshot.snapshot_record,
            public_files,
            snapshot.asset_identity_records,
            snapshot.materialized_root,
            fixture_spec,
            schema_root,
            created_at="2026-07-27T20:00:00Z",
            output=race_output,
        )
    assert race_output.read_bytes() == b"incumbent\n"


def test_answer_side_source_resolution_rejects_digest_or_snapshot_drift(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    fixture, adjudication, reviews, _root_cause = _positive_case_packet(project_root)
    repository = tmp_path / "fixture"
    repository.mkdir()
    (repository / "analysis.py").write_text("effect = -0.42\n", encoding="utf-8")
    snapshot = capture_repository(
        repository,
        tmp_path / "captured",
        "audit:evaluation-fixture",
        captured_at="2026-07-27T17:00:00Z",
    )
    public_files = build_file_records(
        snapshot.file_records,
        snapshot.asset_identity_records,
        str(snapshot.snapshot_record["snapshot_id"]),
        "2026-07-27T17:00:00Z",
    )
    fixture["snapshot_ref"] = {
        "record_type": "repository_snapshot",
        "record_id": snapshot.snapshot_record["snapshot_id"],
    }
    reviews[0]["evidence"][0]["source_refs"] = [
        {
            "source_kind": "file_span",
            "locator": "analysis.py:1",
            "path": "analysis.py",
            "content_digest": "sha256:" + "0" * 64,
            "start_line": 1,
            "end_line": 1,
        }
    ]
    root_cause = _refresh_root_cause(project_root, fixture, adjudication, reviews)

    with pytest.raises(EvaluationValidationError, match="digest"):
        validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            adjudicated_root_causes=[root_cause],
            snapshot=snapshot.snapshot_record,
            file_records=public_files,
            asset_identities=snapshot.asset_identity_records,
            materialized_root=snapshot.materialized_root,
        )


def test_answer_side_source_resolution_rejects_coordinated_manifest_rewrite(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    fixture, adjudication, reviews, root_cause = _positive_case_packet(project_root)
    repository = tmp_path / "fixture"
    repository.mkdir()
    (repository / "analysis.py").write_text("effect = -0.42\n", encoding="utf-8")
    snapshot = capture_repository(
        repository,
        tmp_path / "captured",
        "audit:evaluation-fixture",
        captured_at="2026-07-27T17:00:00Z",
    )
    public_files = build_file_records(
        snapshot.file_records,
        snapshot.asset_identity_records,
        str(snapshot.snapshot_record["snapshot_id"]),
        "2026-07-27T17:00:00Z",
    )
    fixture["snapshot_ref"] = {
        "record_type": "repository_snapshot",
        "record_id": snapshot.snapshot_record["snapshot_id"],
    }
    rewritten_bytes = b"effect = 0.42\n"
    (snapshot.materialized_root / "analysis.py").write_bytes(rewritten_bytes)
    rewritten_digest = sha256_digest(rewritten_bytes)
    evidence = {"kind": "full_digest", "digest": rewritten_digest}
    rewritten_file_id = stable_id("file", "analysis.py", "full_digest", semantic_digest(evidence))
    rewritten_identity_id = stable_id(
        "asset-identity",
        str(snapshot.snapshot_record["audit_run_id"]),
        "file_record",
        rewritten_file_id,
        "full_digest",
        semantic_digest(evidence),
    )
    public_files[0]["file_record_id"] = rewritten_file_id
    public_files[0]["byte_size"] = len(rewritten_bytes)
    public_files[0]["asset_identity_ref"]["record_id"] = rewritten_identity_id
    identities = deepcopy(snapshot.asset_identity_records)
    identities[0]["asset_identity_id"] = rewritten_identity_id
    identities[0]["asset_ref"]["record_id"] = rewritten_file_id
    identities[0]["identity_evidence"] = evidence

    with pytest.raises(EvaluationValidationError, match="RepositorySnapshot digest"):
        validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            adjudicated_root_causes=[root_cause],
            snapshot=snapshot.snapshot_record,
            file_records=public_files,
            asset_identities=identities,
            materialized_root=snapshot.materialized_root,
        )


def test_ambiguous_packet_remains_excluded(project_root: Path, schema_root: Path) -> None:
    fixture, adjudication, reviews, _root_cause = _positive_case_packet(project_root)
    fixture["fixture_kind"] = "ambiguous_fixture"
    fixture["qualification_proof_status"] = "excluded_label"
    fixture["proof_evidence"] = None
    fixture["expected_issue_labels"] = []
    fixture["expected_root_cause_refs"] = []
    adjudication["label_status"] = "ambiguous_excluded"
    adjudication["adjudicated_root_cause_refs"] = []
    adjudication["root_cause_reconciliation_status"] = "unresolved"
    adjudication["exclusion_reason"] = "The panel retained a material interpretation conflict."
    adjudication["agreement"].update(
        {"cross_provider_support": False, "material_disagreement": True}
    )
    for check in adjudication["deterministic_checks"]:
        adjudication["deterministic_checks"][check] = False
    stage2 = next(
        review for review in reviews if review["stage"] == "stage2_scientific_adjudication"
    )
    stage2["falsification_attempt"]["material_dissent"] = True
    stage2["falsification_attempt"]["outcome"] = "unresolved"
    stage2["verdict"] = "conditional_or_unknown"
    stage2["root_cause_identity"] = None

    report = validate_case_packet(fixture, adjudication, reviews, schema_root)

    assert report["panel_consistency"] == "consistent_exclusion"
    assert report["label_admission"] == "excluded_by_adjudication"


def test_production_package_never_imports_answer_side_code(project_root: Path) -> None:
    forbidden = "sc_referee_evaluation"
    for path in (project_root / "src" / "sc_referee").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported.update(
            node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
        )
        assert all(not name.startswith(forbidden) for name in imported), path
