from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.capture import capture_review_submission, load_review_capture
from sc_referee_evaluation.cli import main as evaluation_main
from sc_referee_evaluation.metrics import build_qualification_metric_set
from sc_referee_evaluation.stage3 import (
    Stage3ProtocolError,
    build_stage3_review_packet,
    reconcile_detector_case,
    validate_stage3_review_submission,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.evaluation_candidate import evaluation_candidate_id
from sc_referee.records.root_cause import adjudicated_root_cause_id
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.reporting.html import render_report
from sc_referee.reporting.policy import ReportContractError


def _example(project_root: Path, name: str) -> dict[str, Any]:
    return json.loads(
        (project_root / "reference" / "schemas-v0.18.0" / "examples" / name).read_text(
            encoding="utf-8"
        )
    )


def _stage3_inputs(project_root: Path) -> dict[str, Any]:
    fixture = _example(project_root, "benchmark-fixture.example.json")
    adjudication = _example(project_root, "benchmark-adjudication.example.json")
    root = _example(project_root, "adjudicated-root-cause.example.json")
    audit_bundle = _example(project_root, "audit-bundle.example.json")
    root["issue_class"] = "claim_result_disagreement"
    root["adjudicated_root_cause_id"] = adjudicated_root_cause_id(
        str(root["case_id"]), str(root["issue_class"]), root["stage1_candidate_refs"]
    )
    adjudication["adjudicated_root_cause_refs"] = [
        {
            "record_type": "adjudicated_root_cause",
            "record_id": root["adjudicated_root_cause_id"],
        }
    ]
    fixture.update(
        {
            "fixture_id": "fixture:stage3-positive",
            "fixture_kind": "positive_issue_fixture",
            "qualification_proof_status": "legacy_proof_projection_unavailable",
            "proof_evidence": None,
            "execution_evidence": "not_executed",
            "expected_issue_labels": ["claim_result_disagreement"],
            "expected_root_cause_refs": deepcopy(adjudication["adjudicated_root_cause_refs"]),
            "scientific_contract_refs": [],
            "adjudication_ref": {
                "record_type": "benchmark_adjudication",
                "record_id": adjudication["adjudication_id"],
            },
        }
    )
    fixture["declared_scope"] = {
        "claim_refs": [{"record_type": "claim", "record_id": "claim:1"}],
        "detector_ids": ["detector:claim-direction"],
        "issue_classes": ["claim_result_disagreement"],
        "operation_refs": [],
    }
    fixture["proof_obligations"]["positive_root_cause_documented"] = True

    stage1_freeze: dict[str, Any] = {
        "evaluation_protocol_version": "0.1.0",
        "record_type": "evaluation_stage1_freeze",
        "case_id": adjudication["case_id"],
        "frozen_at": "2026-07-27T18:00:00Z",
        "reviews": [
            {
                "provider": provider,
                "execution_context_id": f"context:stage1:{provider.lower()}:{index}",
            }
            for provider in ("Anthropic", "OpenAI")
            for index in (1, 2)
        ],
        "provider_participation": {"Anthropic": 2, "OpenAI": 2},
        "detector_output_observed": False,
        "answer_side_evidence_observed": False,
    }
    stage1_freeze["freeze_digest"] = semantic_digest(stage1_freeze)
    label_freeze: dict[str, Any] = {
        "evaluation_protocol_version": "0.1.0",
        "record_type": "evaluation_scientific_label_freeze",
        "case_id": adjudication["case_id"],
        "stage1_freeze_digest": stage1_freeze["freeze_digest"],
        "stage2_reviews": [
            {
                "review_ref": deepcopy(review_ref),
                "review_digest": "sha256:" + "1" * 64,
                "packet_digest": "sha256:" + "2" * 64,
                "provider": provider,
                "execution_context_id": f"context:stage2:{provider.lower()}",
                "completed_at": "2026-07-27T18:30:00Z",
            }
            for review_ref, provider in zip(
                adjudication["stage2_review_refs"], ("Anthropic", "OpenAI"), strict=True
            )
        ],
        "adjudication_ref": {
            "record_type": "benchmark_adjudication",
            "record_id": adjudication["adjudication_id"],
        },
        "adjudication_digest": semantic_digest(adjudication),
        "adjudicated_root_causes": [
            {
                "root_cause_ref": deepcopy(adjudication["adjudicated_root_cause_refs"][0]),
                "root_cause_digest": semantic_digest(root),
            }
        ],
        "label_status": adjudication["label_status"],
        "frozen_at": "2026-07-27T19:00:00Z",
        "detector_output_observed": False,
    }
    label_freeze["freeze_digest"] = semantic_digest(label_freeze)

    result = _example(project_root, "detector-result.evaluation-candidate.example.json")
    audit_bundle["detector_results"] = [deepcopy(result)]
    candidate = _example(project_root, "detector-evaluation-candidate.example.json")
    candidate.update(
        {
            "case_id": adjudication["case_id"],
            "fixture_ref": {
                "record_type": "benchmark_fixture",
                "record_id": fixture["fixture_id"],
            },
            "scientific_label_freeze_digest": label_freeze["freeze_digest"],
            "audit_bundle_ref": {
                "record_type": "audit_bundle",
                "record_id": audit_bundle["bundle_id"],
            },
            "audit_bundle_digest": semantic_digest(audit_bundle),
            "semantic_lock_digest": audit_bundle["semantic_lock_digest"],
            "detector_id": result["detector_id"],
            "detector_version": result["detector_version"],
            "detector_manifest_digest": result["detector_manifest_digest"],
            "source_detector_result_ref": {
                "record_type": "detector_result",
                "record_id": result["result_id"],
            },
            "source_detector_result_digest": semantic_digest(result),
            "title": result["candidate"]["title"],
            "bounded_statement": result["candidate"]["bounded_statement"],
            "issue_class": root["issue_class"],
            "root_locator": deepcopy(audit_bundle["findings"][0]["root_cause"]),
            "subject_refs": deepcopy(result["target_refs"]),
            "affected_record_refs": deepcopy(root["affected_record_refs"]),
            "evidence": deepcopy(result["evidence"]),
            "candidate_created_at": "2026-07-27T20:10:00Z",
        }
    )
    candidate["admission_checks"] = {
        "direct_entailment": True,
        "no_reversing_unknown": True,
        "exact_detector_applicability": True,
        "counterevidence_protocol_complete": True,
        "bounded_wording": True,
        "deterministic_replay": True,
        "source_references_resolved": True,
        "material_premise_ids": deepcopy(result["candidate"]["material_premise_ids"]),
        "unresolved_material_premise_ids": [],
        "non_inferences": ["No global workflow correctness claim is established."],
    }
    candidate["evaluation_candidate_id"] = evaluation_candidate_id(candidate)
    return {
        "fixture": fixture,
        "adjudication": adjudication,
        "stage1_freeze": stage1_freeze,
        "label_freeze": label_freeze,
        "audit_bundle": audit_bundle,
        "candidates": [candidate],
        "roots": [root],
        "detector_id": result["detector_id"],
    }


def _reviewer(project_root: Path, provider: str, index: int) -> dict[str, Any]:
    reviewer = deepcopy(
        _example(project_root, "stage3-comparison-review.example.json")["reviewer_agent"]
    )
    reviewer.update(
        {
            "provider": provider,
            "model_id": f"model:{provider.lower()}",
            "model_name": f"Synthetic {provider} model",
            "execution_context_id": f"context:stage3:{provider.lower()}:{index}",
        }
    )
    return reviewer


def _packet_and_review(
    project_root: Path,
    schema_root: Path,
    inputs: dict[str, Any],
    provider: str,
    index: int,
) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    packet = build_stage3_review_packet(
        inputs["fixture"],
        inputs["adjudication"],
        inputs["stage1_freeze"],
        inputs["label_freeze"],
        inputs["audit_bundle"],
        inputs["candidates"],
        inputs["roots"],
        inputs["detector_id"],
        _reviewer(project_root, provider, index),
        "Compare every detector candidate with every frozen adjudicated root.",
        schema_root,
        created_at=f"2026-07-27T20:2{index}:00Z",
    )
    review = deepcopy(_example(project_root, "stage3-comparison-review.example.json"))
    transcript = f"Synthetic {provider} Stage-3 transcript.\n".encode()
    review.update(
        {
            "comparison_review_id": f"stage3-review:{provider.lower()}:{index}",
            "case_id": inputs["adjudication"]["case_id"],
            "reviewer_agent": deepcopy(packet["expected_reviewer_agent"]),
            "fixture_ref": deepcopy(packet["fixture"]["fixture_ref"]),
            "adjudication_ref": deepcopy(packet["adjudication"]["adjudication_ref"]),
            "adjudication_digest": packet["adjudication"]["adjudication_digest"],
            "scientific_label_freeze_digest": inputs["label_freeze"]["freeze_digest"],
            "audit_bundle_ref": deepcopy(packet["detector_output"]["audit_bundle_ref"]),
            "audit_bundle_digest": packet["detector_output"]["audit_bundle_digest"],
            "detector_id": packet["detector_output"]["detector_id"],
            "detector_version": packet["detector_output"]["detector_version"],
            "detector_manifest_digest": packet["detector_output"]["detector_manifest_digest"],
            "root_cause_refs": deepcopy(packet["root_cause_refs"]),
            "candidate_refs": deepcopy(packet["candidate_refs"]),
            "unmatched_root_cause_refs": [],
            "packet_digest": packet["packet_digest"],
            "transcript_digest": sha256_digest(transcript),
            "completed_at": f"2026-07-27T20:3{index}:00Z",
        }
    )
    if packet["candidate_refs"] and packet["root_cause_refs"]:
        review["candidate_mappings"] = [
            {
                "candidate_ref": deepcopy(packet["candidate_refs"][0]),
                "root_cause_ref": deepcopy(packet["root_cause_refs"][0]),
                "scientific_relation": "same_first_material_divergence",
                "statement_boundedness": "within_adjudicated_bounds",
                "affected_scope": "within_adjudicated_scope",
                "issue_class_relationship": "exact",
                "evidence": [deepcopy(inputs["candidates"][0]["evidence"][0])],
                "material_ambiguity": False,
                "rationale": "Exact frozen evidence supports the same bounded first divergence.",
            }
        ]
        review["unmatched_root_cause_refs"] = []
    elif packet["candidate_refs"]:
        review["candidate_mappings"] = [
            {
                "candidate_ref": deepcopy(packet["candidate_refs"][0]),
                "root_cause_ref": None,
                "scientific_relation": "no_adjudicated_root",
                "statement_boundedness": "not_applicable",
                "affected_scope": "not_applicable",
                "issue_class_relationship": "not_applicable",
                "evidence": [deepcopy(inputs["candidates"][0]["evidence"][0])],
                "material_ambiguity": False,
                "rationale": "The frozen negative fixture has no admitted positive root.",
            }
        ]
        review["unmatched_root_cause_refs"] = []
    else:
        review["candidate_mappings"] = []
        review["unmatched_root_cause_refs"] = deepcopy(packet["root_cause_refs"])
    review["provenance"]["created_at"] = review["completed_at"]
    return packet, review, transcript


def test_stage3_packets_capture_fresh_reviews_and_reconcile_exactly(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _stage3_inputs(project_root)
    LocalSchemaRegistry(schema_root).validate(inputs["candidates"][0])
    captures: list[Path] = []
    reviews: list[dict[str, Any]] = []
    packets: list[dict[str, Any]] = []
    for index, provider in enumerate(("Anthropic", "OpenAI"), start=1):
        packet, review, transcript = _packet_and_review(
            project_root, schema_root, inputs, provider, index
        )
        validate_stage3_review_submission(review, packet, schema_root)
        transcript_path = tmp_path / f"{provider}.transcript"
        transcript_path.write_bytes(transcript)
        capture_path = tmp_path / f"{provider}.capture"
        manifest = capture_review_submission(
            review,
            packet,
            transcript_path,
            schema_root,
            captured_at="2026-07-27T20:45:00Z",
            destination=capture_path,
        )
        assert manifest["review_ref"] == {
            "record_type": "stage3_comparison_review",
            "record_id": review["comparison_review_id"],
        }
        loaded_review, loaded_packet, _loaded_manifest = load_review_capture(
            capture_path, schema_root
        )
        captures.append(capture_path)
        reviews.append(loaded_review)
        packets.append(loaded_packet)

    outcome = reconcile_detector_case(
        inputs["fixture"],
        inputs["adjudication"],
        inputs["stage1_freeze"],
        inputs["label_freeze"],
        inputs["audit_bundle"],
        inputs["candidates"],
        inputs["roots"],
        inputs["detector_id"],
        reviews,
        packets,
        schema_root,
        reconciled_at="2026-07-27T21:00:00Z",
        output=tmp_path / "outcome.json",
    )

    assert outcome["comparison_status"] == "reconciled"
    assert outcome["metric_eligible"] is False
    assert outcome["promotion_evidence_eligible"] is False
    assert outcome["candidate_outcomes"][0]["status"] == "bounded_root_match"
    assert outcome["root_outcomes"][0]["status"] == "boundedly_localized"
    assert outcome["root_outcomes"][0]["matched_candidate_refs"] == outcome["candidate_refs"]
    assert outcome["metric_input_status"] == "legacy_source_projection_unavailable"
    assert outcome["detector_result_outcomes"] == []
    replay = reconcile_detector_case(
        inputs["fixture"],
        inputs["adjudication"],
        inputs["stage1_freeze"],
        inputs["label_freeze"],
        inputs["audit_bundle"],
        inputs["candidates"],
        inputs["roots"],
        inputs["detector_id"],
        reviews,
        packets,
        schema_root,
        reconciled_at=outcome["reconciled_at"],
        output=tmp_path / "replay.json",
        expected_outcome=outcome,
    )
    assert replay == outcome
    assert (tmp_path / "replay.json").read_bytes() == (tmp_path / "outcome.json").read_bytes()
    assert len(captures) == 2


def test_stage3_preserves_one_exact_projection_per_detector_result(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _stage3_inputs(project_root)
    second = deepcopy(inputs["audit_bundle"]["detector_results"][0])
    second["result_id"] = "result:second-opportunity"
    second["state"] = "no_issue_detected_within_coverage"
    second.pop("candidate")
    inputs["audit_bundle"]["detector_results"].append(second)
    candidate = inputs["candidates"][0]
    candidate["audit_bundle_digest"] = semantic_digest(inputs["audit_bundle"])
    candidate["evaluation_candidate_id"] = evaluation_candidate_id(candidate)
    pairs = [
        _packet_and_review(project_root, schema_root, inputs, provider, index)
        for index, provider in enumerate(("Anthropic", "OpenAI"), start=1)
    ]

    outcome = reconcile_detector_case(
        inputs["fixture"],
        inputs["adjudication"],
        inputs["stage1_freeze"],
        inputs["label_freeze"],
        inputs["audit_bundle"],
        inputs["candidates"],
        inputs["roots"],
        inputs["detector_id"],
        [review for _packet, review, _transcript in pairs],
        [packet for packet, _review, _transcript in pairs],
        schema_root,
        reconciled_at="2026-07-27T21:00:00Z",
        output=tmp_path / "two-opportunities.json",
    )

    assert outcome["detector_result_outcomes"] == []
    assert outcome["metric_input_status"] == "legacy_source_projection_unavailable"

    mutated = deepcopy(outcome)
    mutated["detector_run_outcome"]["coverage_status"] = "unknown"
    with pytest.raises(Stage3ProtocolError, match="replay"):
        reconcile_detector_case(
            inputs["fixture"],
            inputs["adjudication"],
            inputs["stage1_freeze"],
            inputs["label_freeze"],
            inputs["audit_bundle"],
            inputs["candidates"],
            inputs["roots"],
            inputs["detector_id"],
            [review for _packet, review, _transcript in pairs],
            [packet for packet, _review, _transcript in pairs],
            schema_root,
            reconciled_at=outcome["reconciled_at"],
            expected_outcome=mutated,
        )


def test_complete_fixture_cannot_reconcile_without_exact_proof_inputs(
    project_root: Path, schema_root: Path
) -> None:
    inputs = _stage3_inputs(project_root)
    inputs["fixture"]["qualification_proof_status"] = "complete"
    inputs["fixture"]["proof_evidence"] = _example(project_root, "benchmark-fixture.example.json")[
        "proof_evidence"
    ]

    with pytest.raises(Stage3ProtocolError, match="requires exact proof inputs"):
        reconcile_detector_case(
            inputs["fixture"],
            inputs["adjudication"],
            inputs["stage1_freeze"],
            inputs["label_freeze"],
            inputs["audit_bundle"],
            inputs["candidates"],
            inputs["roots"],
            inputs["detector_id"],
            [],
            [],
            schema_root,
            reconciled_at="2026-07-27T21:00:00Z",
        )


def test_stage3_rejects_prior_context_candidate_mutation_and_unfrozen_evidence(
    project_root: Path, schema_root: Path
) -> None:
    inputs = _stage3_inputs(project_root)
    reused = _reviewer(project_root, "Anthropic", 1)
    reused["execution_context_id"] = inputs["stage1_freeze"]["reviews"][0]["execution_context_id"]
    with pytest.raises(Stage3ProtocolError, match="reuses"):
        build_stage3_review_packet(
            inputs["fixture"],
            inputs["adjudication"],
            inputs["stage1_freeze"],
            inputs["label_freeze"],
            inputs["audit_bundle"],
            inputs["candidates"],
            inputs["roots"],
            inputs["detector_id"],
            reused,
            "Compare exact frozen evidence.",
            schema_root,
            created_at="2026-07-27T20:20:00Z",
        )

    mutated = deepcopy(inputs)
    mutated["candidates"][0]["bounded_statement"] = "Mutated after stable identity."
    with pytest.raises(Stage3ProtocolError, match="candidate ID"):
        build_stage3_review_packet(
            mutated["fixture"],
            mutated["adjudication"],
            mutated["stage1_freeze"],
            mutated["label_freeze"],
            mutated["audit_bundle"],
            mutated["candidates"],
            mutated["roots"],
            mutated["detector_id"],
            _reviewer(project_root, "Anthropic", 1),
            "Compare exact frozen evidence.",
            schema_root,
            created_at="2026-07-27T20:20:00Z",
        )

    packet, review, _transcript = _packet_and_review(
        project_root, schema_root, inputs, "Anthropic", 1
    )
    review["candidate_mappings"][0]["evidence"][0]["description"] = "Invented evidence."
    with pytest.raises(Stage3ProtocolError, match="outside the frozen packet"):
        validate_stage3_review_submission(review, packet, schema_root)


def test_stage3_disagreement_is_explicitly_excluded_and_metric_ineligible(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _stage3_inputs(project_root)
    pairs = [
        _packet_and_review(project_root, schema_root, inputs, provider, index)
        for index, provider in enumerate(("Anthropic", "OpenAI"), start=1)
    ]
    pairs[1][1]["candidate_mappings"][0]["statement_boundedness"] = "exceeds_adjudicated_bounds"
    for packet, review, _transcript in pairs:
        validate_stage3_review_submission(review, packet, schema_root)

    outcome = reconcile_detector_case(
        inputs["fixture"],
        inputs["adjudication"],
        inputs["stage1_freeze"],
        inputs["label_freeze"],
        inputs["audit_bundle"],
        inputs["candidates"],
        inputs["roots"],
        inputs["detector_id"],
        [review for _packet, review, _transcript in pairs],
        [packet for packet, _review, _transcript in pairs],
        schema_root,
        reconciled_at="2026-07-27T21:00:00Z",
        output=tmp_path / "excluded.json",
    )

    assert outcome["comparison_status"] == "comparison_excluded"
    assert outcome["exact_cross_provider_agreement"] is False
    assert outcome["metric_eligible"] is False
    assert outcome["promotion_evidence_eligible"] is False
    assert outcome["candidate_outcomes"][0]["status"] == "unresolved"
    assert outcome["root_outcomes"][0]["status"] == "unresolved"


@pytest.mark.parametrize(
    ("field", "value", "candidate_status", "root_status"),
    [
        (
            "statement_boundedness",
            "exceeds_adjudicated_bounds",
            "overstated_root_match",
            "localized_but_overstated",
        ),
        (
            "affected_scope",
            "exceeds_adjudicated_scope",
            "overstated_root_match",
            "localized_but_overstated",
        ),
    ],
)
def test_exact_stage3_overstatement_is_not_a_bounded_match(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    field: str,
    value: str,
    candidate_status: str,
    root_status: str,
) -> None:
    inputs = _stage3_inputs(project_root)
    pairs = [
        _packet_and_review(project_root, schema_root, inputs, provider, index)
        for index, provider in enumerate(("Anthropic", "OpenAI"), start=1)
    ]
    for packet, review, _transcript in pairs:
        review["candidate_mappings"][0][field] = value
        validate_stage3_review_submission(review, packet, schema_root)

    outcome = reconcile_detector_case(
        inputs["fixture"],
        inputs["adjudication"],
        inputs["stage1_freeze"],
        inputs["label_freeze"],
        inputs["audit_bundle"],
        inputs["candidates"],
        inputs["roots"],
        inputs["detector_id"],
        [review for _packet, review, _transcript in pairs],
        [packet for packet, _review, _transcript in pairs],
        schema_root,
        reconciled_at="2026-07-27T21:00:00Z",
        output=tmp_path / f"overstated-{field}.json",
    )

    assert outcome["candidate_outcomes"][0]["status"] == candidate_status
    assert outcome["root_outcomes"][0]["status"] == root_status


def test_exact_out_of_scope_candidate_is_disclosed_and_excluded_from_root_match(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _stage3_inputs(project_root)
    pairs = [
        _packet_and_review(project_root, schema_root, inputs, provider, index)
        for index, provider in enumerate(("Anthropic", "OpenAI"), start=1)
    ]
    for packet, review, _transcript in pairs:
        mapping = review["candidate_mappings"][0]
        mapping.update(
            {
                "root_cause_ref": None,
                "scientific_relation": "different_root_cause",
                "statement_boundedness": "not_applicable",
                "affected_scope": "outside_declared_scope",
                "issue_class_relationship": "not_applicable",
            }
        )
        review["unmatched_root_cause_refs"] = deepcopy(packet["root_cause_refs"])
        validate_stage3_review_submission(review, packet, schema_root)

    outcome = reconcile_detector_case(
        inputs["fixture"],
        inputs["adjudication"],
        inputs["stage1_freeze"],
        inputs["label_freeze"],
        inputs["audit_bundle"],
        inputs["candidates"],
        inputs["roots"],
        inputs["detector_id"],
        [review for _packet, review, _transcript in pairs],
        [packet for packet, _review, _transcript in pairs],
        schema_root,
        reconciled_at="2026-07-27T21:00:00Z",
        output=tmp_path / "out-of-scope.json",
    )

    assert outcome["candidate_outcomes"][0]["status"] == "out_of_declared_scope"
    assert outcome["candidate_outcomes"][0]["root_cause_ref"] is None
    assert outcome["root_outcomes"][0]["status"] == "missed"


def test_duplicate_candidate_manifestations_cannot_inflate_root_recall(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _stage3_inputs(project_root)
    duplicate = deepcopy(inputs["candidates"][0])
    duplicate["title"] = "Second manifestation of the same bounded root"
    duplicate["evaluation_candidate_id"] = evaluation_candidate_id(duplicate)
    inputs["candidates"].append(duplicate)
    pairs = [
        _packet_and_review(project_root, schema_root, inputs, provider, index)
        for index, provider in enumerate(("Anthropic", "OpenAI"), start=1)
    ]
    for packet, review, _transcript in pairs:
        second_mapping = deepcopy(review["candidate_mappings"][0])
        second_mapping["candidate_ref"] = deepcopy(packet["candidate_refs"][1])
        review["candidate_mappings"].append(second_mapping)
        validate_stage3_review_submission(review, packet, schema_root)

    outcome = reconcile_detector_case(
        inputs["fixture"],
        inputs["adjudication"],
        inputs["stage1_freeze"],
        inputs["label_freeze"],
        inputs["audit_bundle"],
        inputs["candidates"],
        inputs["roots"],
        inputs["detector_id"],
        [review for _packet, review, _transcript in pairs],
        [packet for packet, _review, _transcript in pairs],
        schema_root,
        reconciled_at="2026-07-27T21:00:00Z",
        output=tmp_path / "duplicate.json",
    )

    assert len(outcome["candidate_outcomes"]) == 2
    assert {item["status"] for item in outcome["candidate_outcomes"]} == {"bounded_root_match"}
    assert len(outcome["root_outcomes"]) == 1
    assert outcome["root_outcomes"][0]["status"] == "boundedly_localized"
    assert len(outcome["root_outcomes"][0]["matched_candidate_refs"]) == 2


def test_hard_negative_candidate_is_a_false_accusation_without_inventing_root(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _stage3_inputs(project_root)
    fixture = inputs["fixture"]
    adjudication = inputs["adjudication"]
    fixture.update(
        {
            "fixture_kind": "hard_negative_fixture",
            "execution_evidence": "clean_environment_executed",
            "expected_issue_labels": [],
            "expected_root_cause_refs": [],
            "scientific_contract_refs": [
                {"record_type": "scientific_contract", "record_id": "contract:1"}
            ],
        }
    )
    fixture["proof_obligations"].update(
        {
            "hard_negative_pattern_documented": True,
            "decisive_innocent_explanation_documented": True,
            "positive_root_cause_documented": False,
        }
    )
    adjudication.update(
        {
            "label_status": "hard_negative_eligible",
            "adjudicated_root_cause_refs": [],
            "root_cause_reconciliation_status": "not_applicable",
        }
    )
    label_freeze = inputs["label_freeze"]
    label_freeze.update(
        {
            "adjudication_digest": semantic_digest(adjudication),
            "adjudicated_root_causes": [],
            "label_status": "hard_negative_eligible",
        }
    )
    label_freeze.pop("freeze_digest")
    label_freeze["freeze_digest"] = semantic_digest(label_freeze)
    candidate = inputs["candidates"][0]
    candidate["scientific_label_freeze_digest"] = label_freeze["freeze_digest"]
    candidate["evaluation_candidate_id"] = evaluation_candidate_id(candidate)
    inputs["roots"] = []
    LocalSchemaRegistry(schema_root).validate(fixture)
    LocalSchemaRegistry(schema_root).validate(adjudication)
    pairs = [
        _packet_and_review(project_root, schema_root, inputs, provider, index)
        for index, provider in enumerate(("Anthropic", "OpenAI"), start=1)
    ]
    for packet, review, _transcript in pairs:
        validate_stage3_review_submission(review, packet, schema_root)

    outcome = reconcile_detector_case(
        fixture,
        adjudication,
        inputs["stage1_freeze"],
        label_freeze,
        inputs["audit_bundle"],
        inputs["candidates"],
        [],
        inputs["detector_id"],
        [review for _packet, review, _transcript in pairs],
        [packet for packet, _review, _transcript in pairs],
        schema_root,
        reconciled_at="2026-07-27T21:00:00Z",
        output=tmp_path / "hard-negative.json",
    )

    assert outcome["comparison_status"] == "reconciled"
    assert outcome["root_cause_refs"] == []
    assert outcome["root_outcomes"] == []
    assert outcome["candidate_outcomes"][0] == {
        "candidate_ref": outcome["candidate_refs"][0],
        "status": "false_root_localization",
        "root_cause_ref": None,
    }


def test_positive_abstention_misses_one_root_without_inventing_candidate(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _stage3_inputs(project_root)
    result = inputs["audit_bundle"]["detector_results"][0]
    result["state"] = "no_issue_detected_within_coverage"
    result.pop("candidate")
    inputs["audit_bundle"]["findings"] = []
    inputs["audit_bundle"]["adjudications"] = []
    inputs["candidates"] = []
    pairs = [
        _packet_and_review(project_root, schema_root, inputs, provider, index)
        for index, provider in enumerate(("Anthropic", "OpenAI"), start=1)
    ]
    for packet, review, _transcript in pairs:
        validate_stage3_review_submission(review, packet, schema_root)

    outcome = reconcile_detector_case(
        inputs["fixture"],
        inputs["adjudication"],
        inputs["stage1_freeze"],
        inputs["label_freeze"],
        inputs["audit_bundle"],
        [],
        inputs["roots"],
        inputs["detector_id"],
        [review for _packet, review, _transcript in pairs],
        [packet for packet, _review, _transcript in pairs],
        schema_root,
        reconciled_at="2026-07-27T21:00:00Z",
        output=tmp_path / "missed.json",
    )

    assert outcome["candidate_refs"] == []
    assert outcome["candidate_outcomes"] == []
    assert outcome["root_outcomes"][0]["status"] == "missed"
    assert outcome["detector_run_outcome"] == {
        "execution_status": "completed",
        "applicability_status": "applicable",
        "coverage_status": "covered",
    }


@pytest.mark.parametrize(
    ("state", "applicability", "coverage", "expected"),
    [
        (
            "no_issue_detected_within_coverage",
            "applicable",
            "covered",
            ("completed", "applicable", "covered"),
        ),
        (
            "not_applicable",
            "not_applicable",
            "not_covered",
            ("completed", "not_applicable", "not_covered"),
        ),
        (
            "insufficient_semantics",
            "uncertain",
            "unknown",
            ("completed", "uncertain", "unknown"),
        ),
        (
            "unsupported_path",
            "applicable",
            "not_covered",
            ("completed", "applicable", "not_covered"),
        ),
        (
            "execution_evidence_unavailable",
            "applicable",
            "unknown",
            ("completed", "applicable", "unknown"),
        ),
        (
            "detector_error",
            "uncertain",
            "unknown",
            ("detector_error", "uncertain", "unknown"),
        ),
    ],
)
def test_stage3_preserves_disjoint_detector_run_states_without_inventing_a_candidate(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    state: str,
    applicability: str,
    coverage: str,
    expected: tuple[str, str, str],
) -> None:
    inputs = _stage3_inputs(project_root)
    result = inputs["audit_bundle"]["detector_results"][0]
    result["state"] = state
    result.pop("candidate")
    result["applicability"]["status"] = applicability
    result["coverage"]["status"] = coverage
    result["coverage"]["gaps"] = [] if coverage == "covered" else [f"State: {state}."]
    inputs["audit_bundle"]["findings"] = []
    inputs["audit_bundle"]["adjudications"] = []
    inputs["candidates"] = []
    pairs = [
        _packet_and_review(project_root, schema_root, inputs, provider, index)
        for index, provider in enumerate(("Anthropic", "OpenAI"), start=1)
    ]
    for packet, review, _transcript in pairs:
        validate_stage3_review_submission(review, packet, schema_root)

    outcome = reconcile_detector_case(
        inputs["fixture"],
        inputs["adjudication"],
        inputs["stage1_freeze"],
        inputs["label_freeze"],
        inputs["audit_bundle"],
        [],
        inputs["roots"],
        inputs["detector_id"],
        [review for _packet, review, _transcript in pairs],
        [packet for packet, _review, _transcript in pairs],
        schema_root,
        reconciled_at="2026-07-27T21:00:00Z",
        output=tmp_path / f"{state}.json",
    )

    assert outcome["candidate_outcomes"] == []
    assert outcome["root_outcomes"][0]["status"] == "missed"
    assert outcome["detector_run_outcome"] == {
        "execution_status": expected[0],
        "applicability_status": expected[1],
        "coverage_status": expected[2],
    }


def test_stage3_cli_writes_packet_from_exact_public_inputs(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _stage3_inputs(project_root)
    paths: dict[str, Path] = {}
    for name in (
        "fixture",
        "adjudication",
        "stage1_freeze",
        "label_freeze",
        "audit_bundle",
    ):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(inputs[name]), encoding="utf-8")
        paths[name] = path
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(inputs["candidates"][0]), encoding="utf-8")
    root_path = tmp_path / "root.json"
    root_path.write_text(json.dumps(inputs["roots"][0]), encoding="utf-8")
    reviewer_path = tmp_path / "reviewer.json"
    reviewer_path.write_text(json.dumps(_reviewer(project_root, "Anthropic", 1)), encoding="utf-8")
    prompt_path = tmp_path / "prompt.txt"
    prompt_path.write_text("Compare every candidate and root.\n", encoding="utf-8")
    output = tmp_path / "packet.json"

    assert (
        evaluation_main(
            [
                "stage3-packet",
                "--fixture",
                str(paths["fixture"]),
                "--adjudication",
                str(paths["adjudication"]),
                "--stage1-freeze",
                str(paths["stage1_freeze"]),
                "--label-freeze",
                str(paths["label_freeze"]),
                "--audit-bundle",
                str(paths["audit_bundle"]),
                "--candidate",
                str(candidate_path),
                "--adjudicated-root-cause",
                str(root_path),
                "--detector-id",
                inputs["detector_id"],
                "--reviewer-agent",
                str(reviewer_path),
                "--prompt",
                str(prompt_path),
                "--schema-root",
                str(schema_root),
                "--created-at",
                "2026-07-27T20:20:00Z",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    packet = json.loads(output.read_text(encoding="utf-8"))
    digest = packet.pop("packet_digest")
    assert digest == semantic_digest(packet)
    assert packet["comparison_access_required"]["other_stage3_reviews_hidden"] is True


def test_stage3_cli_reconciles_captures_and_replays_without_a_new_timestamp(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    inputs = _stage3_inputs(project_root)
    paths: dict[str, Path] = {}
    for name in (
        "fixture",
        "adjudication",
        "stage1_freeze",
        "label_freeze",
        "audit_bundle",
    ):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(inputs[name]), encoding="utf-8")
        paths[name] = path
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(inputs["candidates"][0]), encoding="utf-8")
    root_path = tmp_path / "root.json"
    root_path.write_text(json.dumps(inputs["roots"][0]), encoding="utf-8")

    capture_paths: list[Path] = []
    for index, provider in enumerate(("Anthropic", "OpenAI"), start=1):
        packet, review, transcript = _packet_and_review(
            project_root, schema_root, inputs, provider, index
        )
        transcript_path = tmp_path / f"{provider}.transcript"
        transcript_path.write_bytes(transcript)
        capture_path = tmp_path / f"{provider}.capture"
        capture_review_submission(
            review,
            packet,
            transcript_path,
            schema_root,
            captured_at="2026-07-27T20:45:00Z",
            destination=capture_path,
        )
        capture_paths.append(capture_path)

    shared_args = [
        "--fixture",
        str(paths["fixture"]),
        "--adjudication",
        str(paths["adjudication"]),
        "--stage1-freeze",
        str(paths["stage1_freeze"]),
        "--label-freeze",
        str(paths["label_freeze"]),
        "--audit-bundle",
        str(paths["audit_bundle"]),
        "--candidate",
        str(candidate_path),
        "--adjudicated-root-cause",
        str(root_path),
        "--detector-id",
        inputs["detector_id"],
        "--stage3-capture",
        str(capture_paths[0]),
        "--stage3-capture",
        str(capture_paths[1]),
        "--schema-root",
        str(schema_root),
    ]
    outcome_path = tmp_path / "outcome.json"
    assert (
        evaluation_main(
            [
                "reconcile-stage3",
                *shared_args,
                "--reconciled-at",
                "2026-07-27T21:00:00Z",
                "--output",
                str(outcome_path),
            ]
        )
        == 0
    )

    replay_path = tmp_path / "replay.json"
    assert (
        evaluation_main(
            [
                "replay-stage3",
                *shared_args,
                "--source-outcome",
                str(outcome_path),
                "--output",
                str(replay_path),
            ]
        )
        == 0
    )
    assert replay_path.read_bytes() == outcome_path.read_bytes()


def test_stage3_records_validate_and_render_without_becoming_findings_or_qualification(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    bundle = _example(project_root, "audit-bundle.example.json")
    candidate = _example(project_root, "detector-evaluation-candidate.example.json")
    review_a = _example(project_root, "stage3-comparison-review.example.json")
    review_b = deepcopy(review_a)
    review_b["comparison_review_id"] = "stage3-review:provider-b:case-1"
    review_b["reviewer_agent"]["provider"] = "OpenAI"
    review_b["reviewer_agent"]["execution_context_id"] = "context:stage3:provider-b:case-1"
    outcome = _example(project_root, "detector-case-outcome.example.json")
    fixture = _example(project_root, "benchmark-fixture.example.json")
    snapshot = _example(project_root, "repository-snapshot.example.json")
    benchmark_adjudication = _example(project_root, "benchmark-adjudication.example.json")
    adjudicated_root = _example(project_root, "adjudicated-root-cause.example.json")
    root_ref = {
        "record_type": "adjudicated_root_cause",
        "record_id": adjudicated_root["adjudicated_root_cause_id"],
    }
    outcome["root_cause_refs"] = [deepcopy(root_ref)]
    outcome["root_outcomes"][0]["root_cause_ref"] = deepcopy(root_ref)
    outcome["candidate_outcomes"][0]["root_cause_ref"] = deepcopy(root_ref)
    panel_reviews: list[dict[str, Any]] = []
    for ref in benchmark_adjudication["stage1_review_refs"]:
        review = _example(project_root, "agent-review.example.json")
        review["review_id"] = ref["record_id"]
        panel_reviews.append(review)
    for ref in benchmark_adjudication["stage2_review_refs"]:
        review = _example(project_root, "agent-review.stage2.example.json")
        review["review_id"] = ref["record_id"]
        panel_reviews.append(review)
    fixture.update(
        {
            "fixture_kind": "positive_issue_fixture",
            "execution_evidence": "not_executed",
            "expected_issue_labels": ["claim_result_disagreement"],
            "expected_root_cause_refs": [deepcopy(root_ref)],
            "scientific_contract_refs": [],
            "snapshot_ref": {
                "record_type": "repository_snapshot",
                "record_id": snapshot["snapshot_id"],
            },
            "adjudication_ref": {
                "record_type": "benchmark_adjudication",
                "record_id": benchmark_adjudication["adjudication_id"],
            },
        }
    )
    fixture["declared_scope"]["operation_refs"] = []
    fixture["proof_obligations"].update(
        {
            "hard_negative_pattern_documented": False,
            "decisive_innocent_explanation_documented": False,
            "positive_root_cause_documented": True,
        }
    )
    fixture["proof_evidence"]["public_inputs"].update(
        {
            "source_snapshots": [
                {
                    "record_ref": deepcopy(fixture["snapshot_ref"]),
                    "semantic_digest": semantic_digest(snapshot),
                }
            ],
            "adjudications": [
                {
                    "record_ref": deepcopy(fixture["adjudication_ref"]),
                    "semantic_digest": semantic_digest(benchmark_adjudication),
                }
            ],
            "agent_reviews": sorted(
                [
                    {
                        "record_ref": {
                            "record_type": "agent_review",
                            "record_id": review["review_id"],
                        },
                        "semantic_digest": semantic_digest(review),
                    }
                    for review in panel_reviews
                ],
                key=lambda item: item["record_ref"]["record_id"],
            ),
            "adjudicated_root_causes": [
                {
                    "record_ref": deepcopy(root_ref),
                    "semantic_digest": semantic_digest(adjudicated_root),
                }
            ],
            "scientific_contracts": [],
            "operations": [],
            "environments": [],
            "executions": [],
            "sandbox_capabilities": [],
        }
    )
    outcome.update(
        {
            "fixture_ref": {
                "record_type": "benchmark_fixture",
                "record_id": fixture["fixture_id"],
            },
            "fixture_semantic_digest": semantic_digest(fixture),
            "qualification_proof_status": fixture["qualification_proof_status"],
            "problem_id": fixture["problem_id"],
            "corpus_partition": fixture["corpus_partition"],
            "fixture_kind": fixture["fixture_kind"],
        }
    )
    metric_set_example = _example(project_root, "qualification-metric-set.example.json")
    metric_set = build_qualification_metric_set(
        [outcome],
        [fixture],
        metric_set_example["qualification_envelope"],
        schema_root,
        generated_at="2026-07-28T20:30:00Z",
    )
    bundle["detector_evaluation_candidates"] = [candidate]
    bundle["stage3_comparison_reviews"] = [review_a, review_b]
    bundle["detector_case_outcomes"] = [outcome]
    bundle["qualification_metric_sets"] = [metric_set]
    bundle["benchmark_fixtures"] = [fixture]
    bundle["repository_snapshots"] = [snapshot]
    bundle["benchmark_adjudications"] = [benchmark_adjudication]
    bundle["agent_reviews"] = panel_reviews
    bundle["adjudicated_root_causes"] = [adjudicated_root]
    claim = bundle["claims"][0]
    claim["lineage"]["input_refs"] = []
    claim["lineage"]["operation_refs"] = []
    claim["lineage"]["result_refs"] = []
    claim["report_ref"] = {"record_type": "artifact", "record_id": "artifact:report"}
    bundle["artifacts"] = [
        {
            "record_type": "artifact",
            "artifact_id": "artifact:report",
        }
    ]
    bundle["reproduction_requests"] = []
    grade_counts = bundle["coverage_records"][0]["claim_coverage"]["lineage_grade_counts"]
    for dimension in grade_counts:
        grade_counts[dimension] = {
            "complete": 0,
            "partial": 0,
            "missing": 0,
            "unavailable": 1,
            "opaque": 0,
            "total": 1,
        }
    bundle["coverage_records"][0]["claim_coverage"]["claims_total"] = 1
    bundle["coverage_records"][0]["claim_coverage"]["claims_with_complete_lineage"] = 0
    bundle["coverage_records"][0]["extensions"] = {
        "x-run-state": "complete",
        "x-pending-work": [],
    }

    LocalSchemaRegistry(schema_root).validate(
        {
            **bundle,
            "artifacts": _example(project_root, "audit-bundle.example.json")["artifacts"],
            "claims": _example(project_root, "audit-bundle.example.json")["claims"],
            "reproduction_requests": _example(project_root, "audit-bundle.example.json")[
                "reproduction_requests"
            ],
        }
    )
    report_path = tmp_path / "stage3-report.html"
    render_report(bundle, report_path)
    html = report_path.read_text(encoding="utf-8")
    assert "Detector qualification evidence" in html
    assert candidate["evaluation_candidate_id"] in html
    assert outcome["case_id"] in html
    assert metric_set["metric_set_id"] in html
    assert metric_set["bootstrap"]["input_digest"] in html
    assert "exact detector opportunities" in html
    assert "valid and" in html
    assert "Evaluation candidates are not Findings" in html
    assert "Promotion remains prohibited" in html
    assert "Control-family strata" in html
    assert "clean execution" in html

    authority_drift = deepcopy(bundle)
    authority_drift["detector_evaluation_candidates"][0]["production_admission_permitted"] = True
    with pytest.raises(ReportContractError, match="production Finding authority"):
        render_report(authority_drift, tmp_path / "authority-drift.html")

    metric_drift = deepcopy(bundle)
    metric_drift["qualification_metric_sets"][0]["metrics"][0]["numerator"] += 1
    with pytest.raises(ReportContractError, match="metrics does not recompute"):
        render_report(metric_drift, tmp_path / "metric-drift.html")

    count_drift = deepcopy(bundle)
    count_drift["qualification_metric_sets"][0]["counts"]["workflows"] += 1
    with pytest.raises(ReportContractError, match="counts does not recompute"):
        render_report(count_drift, tmp_path / "count-drift.html")

    digest_drift = deepcopy(bundle)
    digest_drift["qualification_metric_sets"][0]["bootstrap"]["input_digest"] = (
        "sha256:" + "00" * 32
    )
    with pytest.raises(ReportContractError, match="bootstrap does not recompute"):
        render_report(digest_drift, tmp_path / "digest-drift.html")

    fixture_drift = deepcopy(bundle)
    fixture_drift["benchmark_fixtures"][0]["limitations"].append("Unbound report-only mutation.")
    with pytest.raises(ReportContractError, match="fixture digest"):
        render_report(fixture_drift, tmp_path / "fixture-drift.html")

    proof_input_drift = deepcopy(bundle)
    proof_input_drift["benchmark_fixtures"][0]["proof_evidence"]["public_inputs"][
        "source_snapshots"
    ][0]["semantic_digest"] = "sha256:" + "0" * 64
    proof_input_drift["detector_case_outcomes"][0]["fixture_semantic_digest"] = semantic_digest(
        proof_input_drift["benchmark_fixtures"][0]
    )
    with pytest.raises(ReportContractError, match="proof input digest drifted"):
        render_report(proof_input_drift, tmp_path / "proof-input-drift.html")
