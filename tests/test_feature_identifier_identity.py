from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import h5py  # type: ignore[import-untyped]

from sc_referee.calculation_checks.feature_identifier_identity import (
    FEATURE_IDENTIFIER_IDENTITY_CHECK_ID,
    FEATURE_IDENTIFIER_IDENTITY_DIMENSION,
)
from sc_referee.calculation_checks.profiles import (
    sequence_boundary_calculation_check_registry,
)
from sc_referee.capability_matrix import (
    default_capability_manifest_root,
    load_capability_detector_manifest,
)
from sc_referee.controller import replay, run_audit
from sc_referee.core.ids import canonical_json
from sc_referee.detectors.admission import (
    AdmissionContext,
    admit_finding,
    evaluate_non_maturity_finding_admission,
)
from sc_referee.detectors.feature_identifier_identity import (
    BoundedFeatureIdentifierIdentityDetector,
)
from sc_referee.interaction import (
    create_candidate_answer,
    lock_semantics,
    record_answer,
    resume_semantics,
    submit_proposal,
    work_packet,
    work_queue,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.version import SCHEMA_VERSION


def _write_project(
    root: Path,
    *,
    left_ids: tuple[str, ...],
    right_ids: tuple[str, ...],
) -> None:
    (root / "report.md").write_text(
        "# Selected feature comparison\n\n"
        "```sc-referee-feature-identity-v1\n"
        "left_input: results/features.csv\n"
        "left_identifier_column: feature_id\n"
        "right_input: data/matrix.h5ad\n"
        "right_identifier_field: var/_index\n"
        "comparison: exact_identifier_set_equality\n"
        "```\n",
        encoding="utf-8",
    )
    (root / "results").mkdir()
    (root / "results" / "features.csv").write_text(
        "feature_id,score\n"
        + "".join(f"{identifier},{index}\n" for index, identifier in enumerate(left_ids)),
        encoding="utf-8",
    )
    (root / "data").mkdir()
    with h5py.File(root / "data" / "matrix.h5ad", "w") as handle:
        handle.attrs["encoding-type"] = "anndata"
        handle.create_dataset("X", data=[[index for index, _ in enumerate(right_ids)]])
        var = handle.create_group("var")
        var.create_dataset(
            "_index",
            data=list(right_ids),
            dtype=h5py.string_dtype(encoding="utf-8"),
        )


def _run_project(
    tmp_path: Path,
    schema_root: Path,
    *,
    left_ids: tuple[str, ...] = ("GENE1", "GENE2", "GENE3"),
    right_ids: tuple[str, ...] = ("GENE1", "GENE2", "GENE4"),
) -> tuple[Path, Path, dict[str, Any]]:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_project(repository, left_ids=left_ids, right_ids=right_ids)
    output = tmp_path / "audit"
    bundle = run_audit(
        repository,
        output,
        schema_root,
        report="report.md",
        material_inputs=("results/features.csv", "data/matrix.h5ad"),
    )
    return repository, output, bundle


def _feature_observation(bundle: dict[str, Any]) -> dict[str, Any]:
    observations = [
        item
        for item in bundle["deterministic_check_observations"]
        if item["check_manifest"]["check_id"] == FEATURE_IDENTIFIER_IDENTITY_CHECK_ID
    ]
    assert len(observations) == 1
    return observations[0]


def _feature_question(bundle: dict[str, Any]) -> dict[str, Any]:
    questions = [
        item
        for item in bundle["material_questions"]
        if item["unknown_semantic_dimension"] == FEATURE_IDENTIFIER_IDENTITY_DIMENSION
    ]
    assert len(questions) == 1
    return questions[0]


def _feature_result(bundle: dict[str, Any]) -> dict[str, Any]:
    results = [
        item
        for item in bundle["detector_results"]
        if item["detector_id"] == BoundedFeatureIdentifierIdentityDetector.detector_id
    ]
    assert len(results) == 1
    return results[0]


def _proposal(packet: dict[str, Any], option: dict[str, Any]) -> dict[str, Any]:
    work_item = packet["work_item"]
    bounded_packet = work_item["packet"]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "semantic_assertion",
        "assertion_id": "assertion:model-feature-identity-proposal",
        "audit_run_id": packet["audit_run_id"],
        "subject_ref": copy.deepcopy(work_item["target_refs"][0]),
        "predicate": "proposed_feature_identifier_relationship",
        "object": copy.deepcopy(option["value"]),
        "semantic_role": "inferred",
        "assertion_class": "implicit_scientific_inference",
        "epistemic_status": "proposed",
        "authority_scope": "none",
        "independently_checkable": False,
        "finding_eligibility": "ineligible",
        "verification": {"status": "not_checked", "method": "not_applicable"},
        "certainty": {
            "level": "low",
            "basis": "Only the scientist can establish the relationship governing this review.",
        },
        "rationale": "This restates one closed option without establishing scientific intent.",
        "source_refs": [copy.deepcopy(bounded_packet["source_refs"][0])],
        "provenance": {
            "actor": {"actor_kind": "model", "actor_id": "model:test"},
            "method": "bounded_semantic_proposal",
            "created_at": "2026-08-02T12:01:00Z",
            "tool": "test-model-adapter",
            "tool_version": "1.0.0",
        },
        "extensions": {
            "x-work-item-ref": {
                "record_type": "work_item",
                "record_id": work_item["work_item_id"],
            },
            "x-packet-digest": bounded_packet["packet_digest"],
            "x-prompt-template-digest": bounded_packet["prompt_template_digest"],
        },
    }


def _answer_feature_question(
    repository: Path,
    source: Path,
    bundle: dict[str, Any],
    tmp_path: Path,
    schema_root: Path,
    *,
    label: str,
) -> tuple[Path, dict[str, Any]]:
    question = _feature_question(bundle)
    option = next(item for item in question["candidate_answers"] if item["label"] == label)
    session = tmp_path / f"interaction-{label.casefold().replace(' ', '-')}"
    resume_semantics(
        source,
        repository,
        session,
        schema_root,
        question_id=question["question_id"],
        created_at="2026-08-02T12:00:00Z",
    )
    queue = work_queue(session, schema_root)
    assert len(queue["work_items"]) == 1
    work_item_id = queue["work_items"][0]["work_item_id"]
    packet = work_packet(session, work_item_id, schema_root)
    submit_proposal(
        session,
        work_item_id,
        _proposal(packet, option),
        schema_root,
        submitted_at="2026-08-02T12:01:00Z",
    )
    answer = create_candidate_answer(
        session,
        question["question_id"],
        option["answer_id"],
        "scientist:test",
        schema_root,
        answered_at="2026-08-02T12:02:00Z",
    )
    record_answer(session, answer, schema_root)
    locked = lock_semantics(
        session,
        schema_root,
        locked_at="2026-08-02T12:03:00Z",
    )
    return session, locked


def test_unanswered_exact_mismatch_is_one_material_question(
    tmp_path: Path, schema_root: Path
) -> None:
    _, _, bundle = _run_project(tmp_path, schema_root)

    observation = _feature_observation(bundle)
    question = _feature_question(bundle)
    result = _feature_result(bundle)

    assert observation["comparison"]["outcome"] == "nonconformant"
    assert question["status"] == "open"
    assert result["state"] == "insufficient_semantics"
    assert bundle["findings"] == []
    assert all(
        item.get("extensions", {}).get("x-calculation-observation-ref")
        != {
            "record_type": "deterministic_check_observation",
            "record_id": observation["deterministic_check_observation_id"],
        }
        for item in bundle["disclosures"]
    )


def test_answered_exact_mismatch_is_evaluation_only_and_replays(
    tmp_path: Path, schema_root: Path
) -> None:
    repository, source, bundle = _run_project(tmp_path, schema_root)
    session, locked = _answer_feature_question(
        repository,
        source,
        bundle,
        tmp_path,
        schema_root,
        label="Exact equality required",
    )
    result = _feature_result(locked)

    assert result["state"] == "evaluation_finding_candidate"
    assert result["coverage"]["status"] == "covered"
    assert result["extensions"]["x-production-finding-permitted"] is False
    assert all(
        item["status"] == "completed" and item["outcome"] == "no_counterevidence"
        for item in result["counterevidence_execution"]
    )
    assert locked["findings"] == []
    LocalSchemaRegistry(schema_root).validate(result)

    manifest = load_capability_detector_manifest(
        default_capability_manifest_root(),
        schema_root,
        BoundedFeatureIdentifierIdentityDetector.detector_id,
    )
    detector = BoundedFeatureIdentifierIdentityDetector(manifest)
    context = AdmissionContext(
        finding_draft=detector.finding_draft(result),
        source_references_resolved=True,
        detector_qualification_applies=False,
        wording_constraints_satisfied=True,
        expected_deterministic_input_digest=result["deterministic_input_digest"],
        required_counterevidence_check_ids=detector.check_ids,
        non_inferences=(
            "No producer lineage, repair direction, biological meaning, numerical impact, or publication-level consequence is established.",
        ),
    )
    assert evaluate_non_maturity_finding_admission(result, context) is not None
    assert admit_finding(result, context) is None

    replayed = replay(session / "semantic.lock.json", tmp_path / "replay", schema_root)
    assert canonical_json(_feature_result(replayed)) == canonical_json(result)


def test_alternate_mapping_suppresses_candidate(tmp_path: Path, schema_root: Path) -> None:
    repository, source, bundle = _run_project(tmp_path, schema_root)
    _, locked = _answer_feature_question(
        repository,
        source,
        bundle,
        tmp_path,
        schema_root,
        label="A mapping governs",
    )

    result = _feature_result(locked)
    assert result["state"] == "unsupported_path"
    assert "candidate" not in result
    assert locked["findings"] == []


def test_retained_unknown_suppresses_candidate(tmp_path: Path, schema_root: Path) -> None:
    repository, source, bundle = _run_project(tmp_path, schema_root)
    _, locked = _answer_feature_question(
        repository,
        source,
        bundle,
        tmp_path,
        schema_root,
        label="Retain unknown",
    )

    result = _feature_result(locked)
    assert result["state"] == "insufficient_semantics"
    assert "candidate" not in result
    assert locked["findings"] == []


def test_duplicate_identifiers_are_unsupported(tmp_path: Path, schema_root: Path) -> None:
    _, _, bundle = _run_project(
        tmp_path,
        schema_root,
        left_ids=("GENE1", "GENE1", "GENE2"),
    )

    observation = _feature_observation(bundle)
    assert observation["applicability"] == "unsupported"
    assert not any(
        item["unknown_semantic_dimension"] == FEATURE_IDENTIFIER_IDENTITY_DIMENSION
        for item in bundle["material_questions"]
    )
    assert not any(
        item["detector_id"] == BoundedFeatureIdentifierIdentityDetector.detector_id
        for item in bundle["detector_results"]
    )
    assert any(
        item["title"] == "Selected feature-identifier comparison could not be completed"
        for item in bundle["disclosures"]
    )


def test_reordered_equal_sets_produce_no_adverse_assessment(
    tmp_path: Path, schema_root: Path
) -> None:
    _, _, bundle = _run_project(
        tmp_path,
        schema_root,
        right_ids=("GENE3", "GENE1", "GENE2"),
    )

    observation = _feature_observation(bundle)
    assert observation["comparison"]["outcome"] == "conformant"
    assert not any(
        item["unknown_semantic_dimension"] == FEATURE_IDENTIFIER_IDENTITY_DIMENSION
        for item in bundle["material_questions"]
    )
    assert not any(
        item["detector_id"] == BoundedFeatureIdentifierIdentityDetector.detector_id
        for item in bundle["detector_results"]
    )
    assert bundle["findings"] == []


def test_module_removal_isolated(tmp_path: Path, schema_root: Path) -> None:
    repository = tmp_path / "project"
    repository.mkdir()
    _write_project(
        repository,
        left_ids=("GENE1", "GENE2", "GENE3"),
        right_ids=("GENE1", "GENE2", "GENE4"),
    )

    bundle = run_audit(
        repository,
        tmp_path / "audit",
        schema_root,
        report="report.md",
        material_inputs=("results/features.csv", "data/matrix.h5ad"),
        calculation_check_registry=sequence_boundary_calculation_check_registry(),
    )

    assert not any(
        item["check_manifest"]["check_id"] == FEATURE_IDENTIFIER_IDENTITY_CHECK_ID
        for item in bundle["deterministic_check_observations"]
    )
    assert not any(
        item["unknown_semantic_dimension"] == FEATURE_IDENTIFIER_IDENTITY_DIMENSION
        for item in bundle["material_questions"]
    )
    assert not any(
        item["detector_id"] == BoundedFeatureIdentifierIdentityDetector.detector_id
        for item in bundle["detector_results"]
    )
