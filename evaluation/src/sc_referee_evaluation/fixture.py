from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.version import SCHEMA_VERSION
from sc_referee_evaluation.analysis_method_qualification import (
    AnalysisMethodQualificationError,
    revalidate_analysis_method_proof,
)
from sc_referee_evaluation.capture import ReviewCaptureError, load_review_capture
from sc_referee_evaluation.qualification_adapter_registry import (
    registered_qualification_adapter,
)
from sc_referee_evaluation.review_protocol import (
    ReviewProtocolError,
    validate_scientific_review_capture_evidence,
    validate_stage1_freeze_evidence,
)
from sc_referee_evaluation.snapshot_evidence import (
    SnapshotEvidenceError,
    SnapshotEvidenceIndex,
    read_full_digest_snapshot_file,
    validate_content_addressed_snapshot,
)
from sc_referee_evaluation.static_qualification import (
    StaticQualificationError,
    revalidate_static_proof,
)
from sc_referee_evaluation.typed_method_qualification import (
    TypedMethodQualificationError,
    revalidate_registered_typed_method_proof,
)
from sc_referee_evaluation.validation import (
    EvaluationValidationError,
    validate_case_packet,
    validate_file_source_ref,
)


class FixtureGenerationError(ValueError):
    """A requested fixture would claim more than the supplied evidence establishes."""


@dataclass(frozen=True)
class FixtureProofInputs:
    """Exact public and private inputs required to replay one complete fixture proof."""

    stage1_capture_directories: list[Path]
    stage2_capture_directories: list[Path]
    stage1_freeze: dict[str, Any]
    workspace_manifests: list[dict[str, Any]]
    snapshot: dict[str, Any]
    file_records: list[dict[str, Any]]
    asset_identities: list[dict[str, Any]]
    materialized_root: Path
    scientific_contracts: list[dict[str, Any]]
    operations: list[dict[str, Any]]
    environments: list[dict[str, Any]]
    executions: list[dict[str, Any]]
    sandbox_capabilities: list[dict[str, Any]]
    evidence_records: list[dict[str, Any]]
    static_qualification_profile: dict[str, Any] | None = None
    static_qualification_proof: dict[str, Any] | None = None
    case_assignment_artifact: dict[str, Any] | None = None
    static_label_freeze_artifact: dict[str, Any] | None = None
    scientific_label_freeze: dict[str, Any] | None = None
    detector_manifest: dict[str, Any] | None = None
    parser_manifests: Sequence[dict[str, Any]] = ()
    semantic_profile_manifests: Sequence[dict[str, Any]] = ()
    version_manifests: Sequence[dict[str, Any]] = ()
    material_questions: Sequence[dict[str, Any]] = ()
    answers: Sequence[dict[str, Any]] = ()
    semantic_assertions: Sequence[dict[str, Any]] = ()


_EXCLUDED_LABELS = {
    "ambiguous_excluded",
    "insufficient_evidence",
    "adjudication_failed",
}


def generate_positive_fixture(
    adjudication: dict[str, Any],
    stage1_capture_directories: list[Path],
    stage2_capture_directories: list[Path],
    stage1_freeze: dict[str, Any],
    workspace_manifests: list[dict[str, Any]],
    adjudicated_root_causes: list[dict[str, Any]],
    snapshot: dict[str, Any],
    file_records: list[dict[str, Any]],
    asset_identities: list[dict[str, Any]],
    materialized_root: Path,
    fixture_spec: dict[str, Any],
    schema_root: Path,
    *,
    created_at: str,
    output: Path,
) -> dict[str, Any]:
    """Construct one positive only from verified capture directories and exact proof inputs."""

    if output.exists() or output.is_symlink():
        raise FixtureGenerationError(f"BenchmarkFixture output already exists: {output}")
    _validate_positive_fixture_spec(fixture_spec)
    stage1_material = _load_capture_set(stage1_capture_directories, schema_root, "stage1_blind")
    stage2_material = _load_capture_set(
        stage2_capture_directories, schema_root, "stage2_scientific_adjudication"
    )
    stage1_reviews = [review for review, _packet, _manifest in stage1_material]
    stage1_packets = [packet for _review, packet, _manifest in stage1_material]
    stage1_manifests = [manifest for _review, _packet, manifest in stage1_material]
    stage2_reviews = [review for review, _packet, _manifest in stage2_material]
    stage2_packets = [packet for _review, packet, _manifest in stage2_material]
    stage2_manifests = [manifest for _review, _packet, manifest in stage2_material]
    reviews = [*stage1_reviews, *stage2_reviews]
    try:
        validate_stage1_freeze_evidence(
            stage1_freeze,
            stage1_reviews,
            stage1_packets,
            stage1_manifests,
            schema_root,
        )
        for review, packet, manifest in stage2_material:
            validate_scientific_review_capture_evidence(
                review,
                packet,
                manifest,
                schema_root,
                expected_stage="stage2_scientific_adjudication",
            )
            if packet.get("stage1_freeze_digest") != stage1_freeze.get("freeze_digest"):
                raise FixtureGenerationError(
                    "Stage-2 capture does not bind the supplied exact Stage-1 freeze."
                )
    except (ReviewCaptureError, ReviewProtocolError) as error:
        raise FixtureGenerationError(str(error)) from error
    _validate_workspace_chain(
        workspace_manifests,
        stage1_packets,
        snapshot,
        file_records,
        asset_identities,
        materialized_root,
    )
    if adjudication.get("label_status") != "positive_demonstrated":
        raise FixtureGenerationError(
            "Positive fixture generation requires a positive_demonstrated adjudication."
        )
    if len(adjudicated_root_causes) != 1:
        raise FixtureGenerationError(
            "This positive fixture profile requires exactly one adjudicated root cause."
        )
    adjudicated_at = _timestamp(str(adjudication["adjudicated_at"]))
    if any(
        _timestamp(str(manifest["captured_at"])) > adjudicated_at for manifest in stage2_manifests
    ):
        raise FixtureGenerationError("Scientific adjudication predates a Stage-2 review capture.")
    if _timestamp(created_at) < adjudicated_at:
        raise FixtureGenerationError("Positive fixture creation cannot precede adjudication.")

    root_refs = sorted(
        [
            {
                "record_type": "adjudicated_root_cause",
                "record_id": root["adjudicated_root_cause_id"],
            }
            for root in adjudicated_root_causes
        ],
        key=lambda item: str(item["record_id"]),
    )
    issue_labels = sorted({str(root["issue_class"]) for root in adjudicated_root_causes})
    if issue_labels != sorted(fixture_spec["declared_scope"]["issue_classes"]):
        raise FixtureGenerationError(
            "Positive fixture issue scope must equal its adjudicated root issue classes."
        )
    fixture_spec_digest = semantic_digest(fixture_spec)
    proof_evidence = _positive_proof_evidence(
        adjudication,
        reviews,
        adjudicated_root_causes,
        snapshot,
        workspace_manifests,
        [*stage1_packets, *stage2_packets],
        [*stage1_manifests, *stage2_manifests],
        stage1_freeze,
    )
    proof_identity_basis = deepcopy(proof_evidence)
    proof_identity_basis.pop("source_validation_report_digest")
    fixture: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "benchmark_fixture",
        "fixture_id": stable_id(
            "positive-fixture",
            str(fixture_spec["problem_id"]),
            str(snapshot["snapshot_id"]),
            str(adjudication["adjudication_id"]),
            semantic_digest(root_refs),
            fixture_spec_digest,
            semantic_digest(proof_identity_basis),
        ),
        "fixture_kind": "positive_issue_fixture",
        "qualification_proof_status": "complete",
        "proof_evidence": proof_evidence,
        "corpus_partition": "public_development",
        "problem_id": fixture_spec["problem_id"],
        "snapshot_ref": {
            "record_type": "repository_snapshot",
            "record_id": snapshot["snapshot_id"],
        },
        "declared_scope": deepcopy(fixture_spec["declared_scope"]),
        "execution_evidence": "not_executed",
        "adjudication_ref": {
            "record_type": "benchmark_adjudication",
            "record_id": adjudication["adjudication_id"],
        },
        "proof_obligations": {
            "claim_output_agreement": True,
            "scope_semantics_resolved": True,
            "reviewed_operations_identified": True,
            "no_unresolved_material_disagreement": True,
            "hard_negative_pattern_documented": False,
            "decisive_innocent_explanation_documented": False,
            "positive_root_cause_documented": True,
        },
        "global_correctness_claim_allowed": False,
        "expected_issue_labels": issue_labels,
        "expected_root_cause_refs": root_refs,
        "scientific_contract_refs": deepcopy(fixture_spec["scientific_contract_refs"]),
        "limitations": sorted(
            {
                *fixture_spec["limitations"],
                "Public-development positive fixture; it is not held-out promotion evidence.",
                "No project execution or global workflow correctness is established.",
            }
        ),
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-eval",
                "display_name": "sc-referee evaluation controller",
            },
            "method": "deterministic_positive_fixture_generation",
            "created_at": created_at,
            "tool": "sc-referee-eval",
            "tool_version": "0.1.0",
        },
        "extensions": {
            "x-fixture-spec-digest": fixture_spec_digest,
            "x-snapshot-digest": snapshot["snapshot_digest"],
            "x-adjudication-digest": semantic_digest(adjudication),
        },
    }
    try:
        report = validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            adjudicated_root_causes=adjudicated_root_causes,
            snapshot=snapshot,
            file_records=file_records,
            asset_identities=asset_identities,
            materialized_root=materialized_root,
        )
    except EvaluationValidationError as error:
        raise FixtureGenerationError(str(error)) from error
    if (
        report.get("label_admission") != "admitted_for_declared_fixture_scope"
        or report.get("unverified_checks") != []
    ):
        raise FixtureGenerationError(
            "Positive fixture evidence did not complete every label-admission check."
        )
    proof_evidence["source_validation_report_digest"] = semantic_digest(report)
    try:
        replayed_report = validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            adjudicated_root_causes=adjudicated_root_causes,
            snapshot=snapshot,
            file_records=file_records,
            asset_identities=asset_identities,
            materialized_root=materialized_root,
        )
        LocalSchemaRegistry(schema_root).validate(fixture)
    except (EvaluationValidationError, RecordValidationError) as error:
        raise FixtureGenerationError(str(error)) from error
    if semantic_digest(replayed_report) != proof_evidence["source_validation_report_digest"]:
        raise FixtureGenerationError("Fixture source-validation report is not replay-stable.")
    write_normalized_json_once(output, fixture)
    return fixture


def _load_capture_set(
    directories: list[Path], schema_root: Path, expected_stage: str
) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    if not directories:
        raise FixtureGenerationError(
            f"Complete fixture construction requires {expected_stage} capture directories."
        )
    material: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    review_ids: set[str] = set()
    capture_ids: set[str] = set()
    for directory in directories:
        try:
            review, packet, manifest = load_review_capture(directory, schema_root)
            validate_scientific_review_capture_evidence(
                review,
                packet,
                manifest,
                schema_root,
                expected_stage=expected_stage,
            )
        except (ReviewCaptureError, ReviewProtocolError) as error:
            raise FixtureGenerationError(str(error)) from error
        review_id = str(review["review_id"])
        capture_id = str(manifest["capture_id"])
        if review_id in review_ids or capture_id in capture_ids:
            raise FixtureGenerationError("Complete fixture captures contain duplicate identities.")
        review_ids.add(review_id)
        capture_ids.add(capture_id)
        material.append((review, packet, manifest))
    return material


def _validate_workspace_chain(
    workspace_manifests: list[dict[str, Any]],
    stage1_packets: list[dict[str, Any]],
    snapshot: dict[str, Any],
    file_records: list[dict[str, Any]],
    asset_identities: list[dict[str, Any]],
    materialized_root: Path,
) -> None:
    if not workspace_manifests:
        raise FixtureGenerationError("Complete fixture construction requires a blind workspace.")
    try:
        index = validate_content_addressed_snapshot(snapshot, file_records, asset_identities)
    except SnapshotEvidenceError as error:
        raise FixtureGenerationError(str(error)) from error
    snapshot_ref = {
        "record_type": "repository_snapshot",
        "record_id": snapshot["snapshot_id"],
    }
    snapshot_digest = semantic_digest(snapshot)
    snapshot_time = _timestamp(str(snapshot["captured_at"]))
    manifests_by_digest: dict[str, dict[str, Any]] = {}
    for manifest in workspace_manifests:
        digest_input = dict(manifest)
        manifest_digest = str(digest_input.pop("manifest_digest", ""))
        if manifest_digest != semantic_digest(digest_input):
            raise FixtureGenerationError("Blind-workspace manifest digest is invalid.")
        if (
            manifest.get("record_type") != "evaluation_blind_workspace_manifest"
            or manifest.get("source_snapshot_ref") != snapshot_ref
            or manifest.get("source_snapshot_digest") != snapshot_digest
        ):
            raise FixtureGenerationError(
                "Blind workspace does not bind the supplied immutable snapshot exactly."
            )
        if _timestamp(str(manifest["created_at"])) < snapshot_time:
            raise FixtureGenerationError("Blind workspace predates snapshot capture.")
        if manifest_digest in manifests_by_digest:
            raise FixtureGenerationError("Duplicate blind-workspace manifest digest.")
        for entry in manifest["files"]:
            try:
                file_record, identity, payload, content_digest = read_full_digest_snapshot_file(
                    index, materialized_root, str(entry["path"])
                )
            except SnapshotEvidenceError as error:
                raise FixtureGenerationError(str(error)) from error
            if (
                entry.get("content_digest") != content_digest
                or entry.get("byte_size") != len(payload)
                or entry.get("file_record_ref")
                != {
                    "record_type": "file_record",
                    "record_id": file_record["file_record_id"],
                }
                or entry.get("asset_identity_ref")
                != {
                    "record_type": "asset_identity",
                    "record_id": identity["asset_identity_id"],
                }
            ):
                raise FixtureGenerationError("Blind-workspace file projection has snapshot drift.")
        manifests_by_digest[manifest_digest] = manifest

    referenced: set[str] = set()
    for packet in stage1_packets:
        projection = packet.get("workspace")
        if not isinstance(projection, dict):
            raise FixtureGenerationError("Stage-1 packet has no blind-workspace projection.")
        manifest_digest = str(projection.get("manifest_digest", ""))
        matched_manifest = manifests_by_digest.get(manifest_digest)
        if matched_manifest is None:
            raise FixtureGenerationError(
                "Stage-1 packet has no exact supplied blind-workspace manifest."
            )
        expected_projection = {
            "workspace_id": matched_manifest["workspace_id"],
            "manifest_digest": matched_manifest["manifest_digest"],
            "created_at": matched_manifest["created_at"],
            "source_snapshot_ref": deepcopy(matched_manifest["source_snapshot_ref"]),
            "source_snapshot_digest": matched_manifest["source_snapshot_digest"],
            "files": deepcopy(matched_manifest["files"]),
        }
        if projection != expected_projection:
            raise FixtureGenerationError("Stage-1 packet blind-workspace projection has drifted.")
        if _timestamp(str(packet["created_at"])) < _timestamp(str(matched_manifest["created_at"])):
            raise FixtureGenerationError("Stage-1 packet predates its blind workspace.")
        referenced.add(manifest_digest)
    if referenced != set(manifests_by_digest):
        raise FixtureGenerationError(
            "Supplied blind-workspace manifests do not exactly equal packet dependencies."
        )


def _public_input(record: dict[str, Any], record_type: str, id_field: str) -> dict[str, Any]:
    return {
        "record_ref": {"record_type": record_type, "record_id": record[id_field]},
        "semantic_digest": semantic_digest(record),
    }


def _artifact_input(kind: str, artifact_id: str, digest: str) -> dict[str, str]:
    return {"artifact_kind": kind, "artifact_id": artifact_id, "content_digest": digest}


def _sort_public_inputs(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: str(item["record_ref"]["record_id"]))


def _sort_artifacts(items: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(items, key=lambda item: item["artifact_id"])


def _positive_proof_evidence(
    adjudication: dict[str, Any],
    reviews: list[dict[str, Any]],
    roots: list[dict[str, Any]],
    snapshot: dict[str, Any],
    workspaces: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    captures: list[dict[str, Any]],
    stage1_freeze: dict[str, Any],
) -> dict[str, Any]:
    return {
        "controller_profile": "fixture-proof-evidence-v1",
        "source_validation_report_digest": "sha256:" + "0" * 64,
        "chronology_validated": True,
        "public_inputs": {
            "source_snapshots": [_public_input(snapshot, "repository_snapshot", "snapshot_id")],
            "adjudications": [
                _public_input(adjudication, "benchmark_adjudication", "adjudication_id")
            ],
            "agent_reviews": _sort_public_inputs(
                [_public_input(review, "agent_review", "review_id") for review in reviews]
            ),
            "adjudicated_root_causes": _sort_public_inputs(
                [
                    _public_input(root, "adjudicated_root_cause", "adjudicated_root_cause_id")
                    for root in roots
                ]
            ),
            "scientific_contracts": [],
            "operations": [],
            "environments": [],
            "executions": [],
            "sandbox_capabilities": [],
        },
        "protocol_artifacts": {
            "blind_workspace_manifests": _sort_artifacts(
                [
                    _artifact_input(
                        "blind_workspace_manifest",
                        str(manifest["workspace_id"]),
                        str(manifest["manifest_digest"]),
                    )
                    for manifest in workspaces
                ]
            ),
            "review_packets": _sort_artifacts(
                [
                    _artifact_input(
                        "review_packet",
                        stable_id("review-packet", str(packet["packet_digest"])),
                        str(packet["packet_digest"]),
                    )
                    for packet in packets
                ]
            ),
            "review_captures": _sort_artifacts(
                [
                    _artifact_input(
                        "review_capture",
                        str(manifest["capture_id"]),
                        str(manifest["capture_digest"]),
                    )
                    for manifest in captures
                ]
            ),
            "review_transcripts": _sort_artifacts(
                [
                    _artifact_input(
                        "review_transcript",
                        stable_id(
                            "review-transcript",
                            str(manifest["capture_id"]),
                            str(manifest["transcript_digest"]),
                        ),
                        str(manifest["transcript_digest"]),
                    )
                    for manifest in captures
                ]
            ),
            "stage1_freezes": [
                _artifact_input(
                    "stage1_freeze",
                    stable_id(
                        "stage1-freeze",
                        str(stage1_freeze["case_id"]),
                        str(stage1_freeze["freeze_digest"]),
                    ),
                    str(stage1_freeze["freeze_digest"]),
                )
            ],
        },
        "hard_negative_evidence": {
            "suspicious_pattern": [],
            "decisive_innocent_explanation": [],
        },
    }


def generate_control_fixture(
    adjudication: dict[str, Any],
    stage1_capture_directories: list[Path],
    stage2_capture_directories: list[Path],
    stage1_freeze: dict[str, Any],
    workspace_manifests: list[dict[str, Any]],
    snapshot: dict[str, Any],
    file_records: list[dict[str, Any]],
    asset_identities: list[dict[str, Any]],
    materialized_root: Path,
    scientific_contracts: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    environments: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    sandbox_capabilities: list[dict[str, Any]],
    evidence_records: list[dict[str, Any]],
    fixture_spec: dict[str, Any],
    schema_root: Path,
    *,
    created_at: str,
    output: Path,
) -> dict[str, Any]:
    """Compile a negative control from an exact panel and existing execution evidence.

    This function validates supplied public records.  It never launches project-authored code.
    """

    if output.exists() or output.is_symlink():
        raise FixtureGenerationError(f"BenchmarkFixture output already exists: {output}")
    _validate_control_fixture_spec(fixture_spec)
    fixture_kind = str(fixture_spec["fixture_kind"])
    execution_evidence = str(fixture_spec["execution_evidence"])
    if fixture_kind.startswith("static_scope_"):
        raise FixtureGenerationError(
            "Static controls require generate_static_control_fixture and an independent proof."
        )

    stage1_material = _load_capture_set(stage1_capture_directories, schema_root, "stage1_blind")
    stage2_material = _load_capture_set(
        stage2_capture_directories, schema_root, "stage2_scientific_adjudication"
    )
    stage1_reviews = [review for review, _packet, _manifest in stage1_material]
    stage1_packets = [packet for _review, packet, _manifest in stage1_material]
    stage1_manifests = [manifest for _review, _packet, manifest in stage1_material]
    stage2_reviews = [review for review, _packet, _manifest in stage2_material]
    stage2_packets = [packet for _review, packet, _manifest in stage2_material]
    stage2_manifests = [manifest for _review, _packet, manifest in stage2_material]
    reviews = [*stage1_reviews, *stage2_reviews]
    try:
        validate_stage1_freeze_evidence(
            stage1_freeze,
            stage1_reviews,
            stage1_packets,
            stage1_manifests,
            schema_root,
        )
        for review, packet, manifest in stage2_material:
            validate_scientific_review_capture_evidence(
                review,
                packet,
                manifest,
                schema_root,
                expected_stage="stage2_scientific_adjudication",
            )
            if packet.get("stage1_freeze_digest") != stage1_freeze.get("freeze_digest"):
                raise FixtureGenerationError(
                    "Stage-2 control capture does not bind the supplied exact Stage-1 freeze."
                )
    except (ReviewCaptureError, ReviewProtocolError) as error:
        raise FixtureGenerationError(str(error)) from error

    _validate_workspace_chain(
        workspace_manifests,
        stage1_packets,
        snapshot,
        file_records,
        asset_identities,
        materialized_root,
    )
    expected_label = (
        "hard_negative_eligible"
        if fixture_kind == "hard_negative_fixture"
        else "verified_good_eligible"
    )
    if adjudication.get("label_status") != expected_label:
        raise FixtureGenerationError(f"{fixture_kind} requires a {expected_label} adjudication.")
    if adjudication.get("adjudicated_root_cause_refs") != []:
        raise FixtureGenerationError("A negative control cannot carry a positive root cause.")

    adjudicated_at = _timestamp(str(adjudication["adjudicated_at"]))
    if any(
        _timestamp(str(manifest["captured_at"])) > adjudicated_at for manifest in stage2_manifests
    ):
        raise FixtureGenerationError("Control adjudication predates a Stage-2 review capture.")
    if _timestamp(created_at) < adjudicated_at:
        raise FixtureGenerationError("Control fixture creation cannot precede adjudication.")

    registry = LocalSchemaRegistry(schema_root)
    public_records = [
        *scientific_contracts,
        *operations,
        *environments,
        *executions,
        *sandbox_capabilities,
        *evidence_records,
    ]
    try:
        for record in public_records:
            registry.validate(record)
    except RecordValidationError as error:
        raise FixtureGenerationError(str(error)) from error
    record_index = _record_index([snapshot, *file_records, *asset_identities, *public_records])
    try:
        snapshot_index = validate_content_addressed_snapshot(
            snapshot, file_records, asset_identities
        )
    except SnapshotEvidenceError as error:
        raise FixtureGenerationError(str(error)) from error

    contract_refs = _exact_record_refs(scientific_contracts, "scientific_contract", "contract_id")
    operation_refs = _exact_record_refs(operations, "operation", "operation_id")
    execution_refs = _exact_record_refs(executions, "execution", "execution_id")
    environment_refs = _exact_record_refs(environments, "environment", "environment_id")
    capability_refs = _exact_record_refs(
        sandbox_capabilities, "sandbox_capability", "sandbox_capability_id"
    )
    if fixture_spec["scientific_contract_refs"] != contract_refs:
        raise FixtureGenerationError(
            "Control scientific_contract_refs do not exactly equal supplied contracts."
        )
    if fixture_spec["declared_scope"]["operation_refs"] != operation_refs:
        raise FixtureGenerationError(
            "Control operation scope does not exactly equal supplied Operations."
        )
    for ref in fixture_spec["declared_scope"]["claim_refs"]:
        _resolve_record_ref(ref, record_index, "control claim scope")
    for contract in scientific_contracts:
        if contract.get("status") != "resolved":
            raise FixtureGenerationError("A complete control requires resolved contracts.")
        _validate_record_source_refs(
            contract, snapshot_index, materialized_root, "ScientificContract"
        )
    for operation in operations:
        if operation.get("inspection_status") != "supported" or operation.get("opaque_boundaries"):
            raise FixtureGenerationError(
                "A complete control requires supported, non-opaque reviewed Operations."
            )
        _validate_record_source_refs(operation, snapshot_index, materialized_root, "Operation")

    hard_negative_evidence = deepcopy(fixture_spec["hard_negative_evidence"])
    _validate_hard_negative_evidence(
        hard_negative_evidence,
        fixture_kind,
        record_index,
        snapshot_index,
        materialized_root,
    )
    expected_answer_side_refs = _unique_sorted_objects(
        [
            *contract_refs,
            *_hard_negative_packet_refs(hard_negative_evidence, snapshot_index),
        ]
    )
    if _sorted_objects(adjudication.get("answer_side_evidence_refs")) != (
        expected_answer_side_refs
    ):
        raise FixtureGenerationError(
            "Control adjudication does not bind the exact answer-side evidence set."
        )
    for packet in stage2_packets:
        if _sorted_objects(packet.get("answer_side_evidence_refs")) != expected_answer_side_refs:
            raise FixtureGenerationError(
                "Stage-2 control packet does not contain the exact answer-side evidence set."
            )
        if _sorted_objects(packet.get("reference_analysis_refs")) != operation_refs:
            raise FixtureGenerationError(
                "Stage-2 control packet does not contain the exact reviewed Operation set."
            )
        if _sorted_objects(packet.get("execution_comparison_refs")) != execution_refs:
            raise FixtureGenerationError(
                "Stage-2 control packet does not contain the exact Execution set."
            )

    _validate_control_executions(
        fixture_kind,
        execution_evidence,
        environments,
        executions,
        sandbox_capabilities,
        record_index,
        snapshot,
        stage2_packets,
    )

    fixture_spec_digest = semantic_digest(fixture_spec)
    proof_evidence = _control_proof_evidence(
        adjudication,
        reviews,
        snapshot,
        workspace_manifests,
        [*stage1_packets, *stage2_packets],
        [*stage1_manifests, *stage2_manifests],
        stage1_freeze,
        scientific_contracts,
        operations,
        environments,
        executions,
        sandbox_capabilities,
        hard_negative_evidence,
    )
    proof_identity_basis = deepcopy(proof_evidence)
    proof_identity_basis.pop("source_validation_report_digest")
    is_hard_negative = fixture_kind == "hard_negative_fixture"
    fixture: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "benchmark_fixture",
        "fixture_id": stable_id(
            "control-fixture",
            fixture_kind,
            str(fixture_spec["problem_id"]),
            str(snapshot["snapshot_id"]),
            str(adjudication["adjudication_id"]),
            fixture_spec_digest,
            semantic_digest(proof_identity_basis),
        ),
        "fixture_kind": fixture_kind,
        "qualification_proof_status": "complete",
        "proof_evidence": proof_evidence,
        "corpus_partition": "public_development",
        "problem_id": fixture_spec["problem_id"],
        "snapshot_ref": {
            "record_type": "repository_snapshot",
            "record_id": snapshot["snapshot_id"],
        },
        "declared_scope": deepcopy(fixture_spec["declared_scope"]),
        "execution_evidence": execution_evidence,
        "adjudication_ref": {
            "record_type": "benchmark_adjudication",
            "record_id": adjudication["adjudication_id"],
        },
        "proof_obligations": {
            "claim_output_agreement": True,
            "scope_semantics_resolved": True,
            "reviewed_operations_identified": True,
            "no_unresolved_material_disagreement": True,
            "hard_negative_pattern_documented": is_hard_negative,
            "decisive_innocent_explanation_documented": is_hard_negative,
            "positive_root_cause_documented": False,
        },
        "global_correctness_claim_allowed": False,
        "expected_issue_labels": [],
        "expected_root_cause_refs": [],
        "scientific_contract_refs": contract_refs,
        "limitations": sorted(
            {
                *fixture_spec["limitations"],
                "Public-development control; it is not held-out promotion evidence.",
                "Verification is limited to the declared claims, operations, and detector scope.",
            }
        ),
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-eval",
                "display_name": "sc-referee evaluation controller",
            },
            "method": "deterministic_control_fixture_generation",
            "created_at": created_at,
            "tool": "sc-referee-eval",
            "tool_version": "0.1.0",
        },
        "extensions": {
            "x-fixture-spec-digest": fixture_spec_digest,
            "x-snapshot-digest": snapshot["snapshot_digest"],
            "x-adjudication-digest": semantic_digest(adjudication),
            "x-execution-input-digest": semantic_digest(
                {
                    "executions": execution_refs,
                    "environments": environment_refs,
                    "sandbox_capabilities": capability_refs,
                }
            ),
        },
    }
    try:
        report = validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            snapshot=snapshot,
            file_records=file_records,
            asset_identities=asset_identities,
            materialized_root=materialized_root,
        )
    except EvaluationValidationError as error:
        raise FixtureGenerationError(str(error)) from error
    if (
        report.get("label_admission") != "admitted_for_declared_fixture_scope"
        or report.get("unverified_checks") != []
    ):
        raise FixtureGenerationError(
            "Control fixture evidence did not complete every label-admission check."
        )
    proof_evidence["source_validation_report_digest"] = semantic_digest(report)
    try:
        replayed_report = validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            snapshot=snapshot,
            file_records=file_records,
            asset_identities=asset_identities,
            materialized_root=materialized_root,
        )
        registry.validate(fixture)
    except (EvaluationValidationError, RecordValidationError) as error:
        raise FixtureGenerationError(str(error)) from error
    if semantic_digest(replayed_report) != proof_evidence["source_validation_report_digest"]:
        raise FixtureGenerationError("Control source-validation report is not replay-stable.")
    write_normalized_json_once(output, fixture)
    return fixture


def generate_static_control_fixture(
    adjudication: dict[str, Any],
    adjudicated_root_causes: list[dict[str, Any]],
    proof_inputs: FixtureProofInputs,
    fixture_spec: dict[str, Any],
    schema_root: Path,
    *,
    created_at: str,
    output: Path,
) -> dict[str, Any]:
    """Compile one non-executing static control from an exact independent proof."""

    if output.exists() or output.is_symlink():
        raise FixtureGenerationError(f"BenchmarkFixture output already exists: {output}")
    _validate_control_fixture_spec(fixture_spec)
    fixture_kind = str(fixture_spec["fixture_kind"])
    if fixture_kind not in {
        "static_scope_verified_good",
        "static_scope_hard_negative",
    }:
        raise FixtureGenerationError("Static fixture generation requires one static fixture kind.")
    if adjudicated_root_causes:
        raise FixtureGenerationError("A static negative control cannot contain root causes.")
    _require_static_only_proof_basis(proof_inputs)
    supported_detectors = {
        "bounded_report_mean_direction_v1": "detector:bounded-report-mean-direction",
        "bounded_analysis_method_conflict_v1": "detector:bounded-analysis-method-conflict",
        "typed_static_method_conflict_v1": "detector:bounded-analysis-method-conflict",
    }
    profile = proof_inputs.static_qualification_profile
    profile_kind = profile.get("profile_kind") if isinstance(profile, Mapping) else None
    expected_detector = supported_detectors.get(str(profile_kind))
    if expected_detector is None or fixture_spec["declared_scope"]["detector_ids"] != [
        expected_detector
    ]:
        raise FixtureGenerationError(
            "Static fixture detector scope does not equal its exact frozen profile variant."
        )
    expected_label = (
        "hard_negative_eligible"
        if fixture_kind == "static_scope_hard_negative"
        else "verified_good_eligible"
    )
    if adjudication.get("label_status") != expected_label:
        raise FixtureGenerationError(f"{fixture_kind} requires a {expected_label} adjudication.")

    stage1_material = _load_capture_set(
        proof_inputs.stage1_capture_directories,
        schema_root,
        "stage1_blind",
    )
    stage2_material = _load_capture_set(
        proof_inputs.stage2_capture_directories,
        schema_root,
        "stage2_scientific_adjudication",
    )
    reviews = [
        *[review for review, _packet, _manifest in stage1_material],
        *[review for review, _packet, _manifest in stage2_material],
    ]
    packets = [
        *[packet for _review, packet, _manifest in stage1_material],
        *[packet for _review, packet, _manifest in stage2_material],
    ]
    manifests = [
        *[manifest for _review, _packet, manifest in stage1_material],
        *[manifest for _review, _packet, manifest in stage2_material],
    ]
    contract_refs = _exact_record_refs(
        proof_inputs.scientific_contracts,
        "scientific_contract",
        "contract_id",
    )
    operation_refs = _exact_record_refs(proof_inputs.operations, "operation", "operation_id")
    if (
        fixture_spec["scientific_contract_refs"] != contract_refs
        or fixture_spec["declared_scope"]["operation_refs"] != operation_refs
        or fixture_spec["execution_evidence"] != "not_executed"
    ):
        raise FixtureGenerationError(
            "Static fixture specification does not equal its contract, operation, or execution basis."
        )
    static_proof = proof_inputs.static_qualification_proof
    assert isinstance(static_proof, dict)
    hard_evidence = deepcopy(fixture_spec["hard_negative_evidence"])
    proof_evidence = _static_control_proof_evidence(
        adjudication,
        reviews,
        proof_inputs.snapshot,
        proof_inputs.workspace_manifests,
        packets,
        manifests,
        proof_inputs.stage1_freeze,
        proof_inputs.scientific_contracts,
        proof_inputs.operations,
        list(proof_inputs.material_questions),
        list(proof_inputs.answers),
        list(proof_inputs.semantic_assertions),
        static_proof,
        hard_evidence,
    )
    proof_identity_basis = deepcopy(proof_evidence)
    proof_identity_basis.pop("source_validation_report_digest")
    is_hard = fixture_kind == "static_scope_hard_negative"
    fixture_spec_digest = semantic_digest(fixture_spec)
    fixture: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "benchmark_fixture",
        "fixture_id": stable_id(
            "static-control-fixture",
            fixture_kind,
            str(fixture_spec["problem_id"]),
            str(proof_inputs.snapshot["snapshot_id"]),
            str(adjudication["adjudication_id"]),
            fixture_spec_digest,
            semantic_digest(proof_identity_basis),
        ),
        "fixture_kind": fixture_kind,
        "qualification_proof_status": "complete",
        "proof_evidence": proof_evidence,
        "corpus_partition": "public_development",
        "problem_id": fixture_spec["problem_id"],
        "snapshot_ref": {
            "record_type": "repository_snapshot",
            "record_id": proof_inputs.snapshot["snapshot_id"],
        },
        "declared_scope": deepcopy(fixture_spec["declared_scope"]),
        "execution_evidence": "not_executed",
        "adjudication_ref": {
            "record_type": "benchmark_adjudication",
            "record_id": adjudication["adjudication_id"],
        },
        "proof_obligations": {
            "claim_output_agreement": True,
            "scope_semantics_resolved": True,
            "reviewed_operations_identified": True,
            "no_unresolved_material_disagreement": True,
            "hard_negative_pattern_documented": is_hard,
            "decisive_innocent_explanation_documented": is_hard,
            "positive_root_cause_documented": False,
        },
        "global_correctness_claim_allowed": False,
        "expected_issue_labels": [],
        "expected_root_cause_refs": [],
        "scientific_contract_refs": contract_refs,
        "limitations": sorted(
            {
                *fixture_spec["limitations"],
                "Public-development static control; it is not held-out promotion evidence.",
                "No project execution or global workflow correctness is established.",
                "Verification is limited to the exact frozen static qualification profile.",
            }
        ),
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-eval",
                "display_name": "sc-referee evaluation controller",
            },
            "method": "deterministic_static_control_fixture_generation",
            "created_at": created_at,
            "tool": "sc-referee-eval",
            "tool_version": "0.1.0",
        },
        "extensions": {
            "x-fixture-spec-digest": fixture_spec_digest,
            "x-snapshot-digest": proof_inputs.snapshot["snapshot_digest"],
            "x-adjudication-digest": semantic_digest(adjudication),
            "x-static-proof-digest": semantic_digest(static_proof),
        },
    }
    try:
        report = validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            snapshot=proof_inputs.snapshot,
            file_records=proof_inputs.file_records,
            asset_identities=proof_inputs.asset_identities,
            materialized_root=proof_inputs.materialized_root,
        )
    except EvaluationValidationError as error:
        raise FixtureGenerationError(str(error)) from error
    if (
        report.get("label_admission") != "admitted_for_declared_fixture_scope"
        or report.get("unverified_checks") != []
    ):
        raise FixtureGenerationError("Static fixture panel did not establish its bounded label.")
    proof_evidence["source_validation_report_digest"] = semantic_digest(report)
    revalidate_fixture_proof(
        fixture,
        adjudication,
        [],
        proof_inputs,
        schema_root,
    )
    write_normalized_json_once(output, fixture)
    return fixture


def revalidate_fixture_proof(
    fixture: dict[str, Any],
    adjudication: dict[str, Any],
    adjudicated_root_causes: list[dict[str, Any]],
    proof_inputs: FixtureProofInputs,
    schema_root: Path,
) -> dict[str, Any]:
    """Replay a complete fixture proof from its exact external evidence set."""

    registry = LocalSchemaRegistry(schema_root)
    if fixture.get("qualification_proof_status") != "complete":
        raise FixtureGenerationError("Only a complete fixture has a replayable proof projection.")
    try:
        registry.validate(fixture)
        registry.validate(adjudication)
        for record in [
            *adjudicated_root_causes,
            *proof_inputs.scientific_contracts,
            *proof_inputs.material_questions,
            *proof_inputs.answers,
            *proof_inputs.semantic_assertions,
            *proof_inputs.operations,
            *proof_inputs.environments,
            *proof_inputs.executions,
            *proof_inputs.sandbox_capabilities,
            *proof_inputs.evidence_records,
            *(
                [proof_inputs.static_qualification_profile]
                if proof_inputs.static_qualification_profile is not None
                else []
            ),
            *(
                [proof_inputs.static_qualification_proof]
                if proof_inputs.static_qualification_proof is not None
                else []
            ),
        ]:
            registry.validate(record)
    except RecordValidationError as error:
        raise FixtureGenerationError(str(error)) from error

    stage1_material = _load_capture_set(
        proof_inputs.stage1_capture_directories, schema_root, "stage1_blind"
    )
    stage2_material = _load_capture_set(
        proof_inputs.stage2_capture_directories,
        schema_root,
        "stage2_scientific_adjudication",
    )
    stage1_reviews = [review for review, _packet, _manifest in stage1_material]
    stage1_packets = [packet for _review, packet, _manifest in stage1_material]
    stage1_manifests = [manifest for _review, _packet, manifest in stage1_material]
    stage2_reviews = [review for review, _packet, _manifest in stage2_material]
    stage2_packets = [packet for _review, packet, _manifest in stage2_material]
    stage2_manifests = [manifest for _review, _packet, manifest in stage2_material]
    reviews = [*stage1_reviews, *stage2_reviews]
    packets = [*stage1_packets, *stage2_packets]
    manifests = [*stage1_manifests, *stage2_manifests]
    try:
        validate_stage1_freeze_evidence(
            proof_inputs.stage1_freeze,
            stage1_reviews,
            stage1_packets,
            stage1_manifests,
            schema_root,
        )
        for review, packet, manifest in stage2_material:
            validate_scientific_review_capture_evidence(
                review,
                packet,
                manifest,
                schema_root,
                expected_stage="stage2_scientific_adjudication",
            )
            if packet.get("stage1_freeze_digest") != proof_inputs.stage1_freeze.get(
                "freeze_digest"
            ):
                raise FixtureGenerationError(
                    "Stage-2 proof capture does not bind the exact Stage-1 freeze."
                )
    except (ReviewCaptureError, ReviewProtocolError) as error:
        raise FixtureGenerationError(str(error)) from error
    _validate_workspace_chain(
        proof_inputs.workspace_manifests,
        stage1_packets,
        proof_inputs.snapshot,
        proof_inputs.file_records,
        proof_inputs.asset_identities,
        proof_inputs.materialized_root,
    )
    adjudicated_at = _timestamp(str(adjudication["adjudicated_at"]))
    if any(
        _timestamp(str(manifest["captured_at"])) > adjudicated_at for manifest in stage2_manifests
    ):
        raise FixtureGenerationError("Adjudication predates a Stage-2 proof capture.")
    provenance = fixture.get("provenance")
    if (
        not isinstance(provenance, dict)
        or _timestamp(str(provenance.get("created_at", ""))) < adjudicated_at
    ):
        raise FixtureGenerationError("Fixture creation predates its adjudication.")

    try:
        snapshot_index = validate_content_addressed_snapshot(
            proof_inputs.snapshot,
            proof_inputs.file_records,
            proof_inputs.asset_identities,
        )
    except SnapshotEvidenceError as error:
        raise FixtureGenerationError(str(error)) from error
    record_index = _record_index(
        [
            proof_inputs.snapshot,
            *proof_inputs.file_records,
            *proof_inputs.asset_identities,
            *proof_inputs.scientific_contracts,
            *proof_inputs.material_questions,
            *proof_inputs.answers,
            *proof_inputs.semantic_assertions,
            *proof_inputs.operations,
            *proof_inputs.environments,
            *proof_inputs.executions,
            *proof_inputs.sandbox_capabilities,
            *proof_inputs.evidence_records,
        ]
    )

    fixture_kind = str(fixture["fixture_kind"])
    if fixture_kind == "positive_issue_fixture":
        if any(
            (
                proof_inputs.scientific_contracts,
                proof_inputs.operations,
                proof_inputs.environments,
                proof_inputs.executions,
                proof_inputs.sandbox_capabilities,
            )
        ):
            raise FixtureGenerationError(
                "The bounded positive profile cannot acquire unrelated control proof inputs."
            )
        for packet in stage2_packets:
            if any(
                packet.get(field)
                for field in (
                    "answer_side_evidence_refs",
                    "reference_analysis_refs",
                    "execution_comparison_refs",
                )
            ):
                raise FixtureGenerationError(
                    "The bounded positive Stage-2 packet has unexpected control evidence."
                )
        expected_proof = _positive_proof_evidence(
            adjudication,
            reviews,
            adjudicated_root_causes,
            proof_inputs.snapshot,
            proof_inputs.workspace_manifests,
            packets,
            manifests,
            proof_inputs.stage1_freeze,
        )
    elif fixture_kind in {
        "static_scope_verified_good",
        "static_scope_hard_negative",
    }:
        if adjudicated_root_causes:
            raise FixtureGenerationError("A static negative control cannot contain root causes.")
        _require_static_only_proof_basis(proof_inputs)
        contract_refs = _exact_record_refs(
            proof_inputs.scientific_contracts,
            "scientific_contract",
            "contract_id",
        )
        operation_refs = _exact_record_refs(proof_inputs.operations, "operation", "operation_id")
        if (
            fixture.get("execution_evidence") != "not_executed"
            or fixture.get("scientific_contract_refs") != contract_refs
            or fixture.get("declared_scope", {}).get("operation_refs") != operation_refs
        ):
            raise FixtureGenerationError(
                "Static control execution, contract, or operation scope has drifted."
            )
        static_claims = []
        for ref in fixture.get("declared_scope", {}).get("claim_refs", []):
            claim = _resolve_record_ref(ref, record_index, "static control claim scope")
            _validate_record_source_refs(
                claim,
                snapshot_index,
                proof_inputs.materialized_root,
                "Claim",
            )
            static_claims.append(claim)
        for contract in proof_inputs.scientific_contracts:
            is_method_profile = isinstance(
                proof_inputs.static_qualification_profile, Mapping
            ) and proof_inputs.static_qualification_profile.get("profile_kind") in {
                "bounded_analysis_method_conflict_v1",
                "typed_static_method_conflict_v1",
            }
            if not is_method_profile and contract.get("status") != "resolved":
                raise FixtureGenerationError("A static control requires resolved contracts.")
            _validate_record_source_refs(
                contract,
                snapshot_index,
                proof_inputs.materialized_root,
                "ScientificContract",
            )
        for operation in proof_inputs.operations:
            if operation.get("inspection_status") != "supported" or operation.get(
                "opaque_boundaries"
            ):
                raise FixtureGenerationError(
                    "A static control requires supported, non-opaque reviewed Operations."
                )
            _validate_record_source_refs(
                operation,
                snapshot_index,
                proof_inputs.materialized_root,
                "Operation",
            )
        current_proof = fixture.get("proof_evidence")
        if not isinstance(current_proof, dict):
            raise FixtureGenerationError("Complete static fixture proof_evidence is absent.")
        hard_evidence = deepcopy(current_proof.get("hard_negative_evidence"))
        if not isinstance(hard_evidence, dict):
            raise FixtureGenerationError("Static hard-negative evidence is absent.")
        _validate_hard_negative_evidence(
            hard_evidence,
            fixture_kind,
            record_index,
            snapshot_index,
            proof_inputs.materialized_root,
        )
        answer_refs = _unique_sorted_objects(
            [
                *contract_refs,
                *_exact_record_refs(
                    list(proof_inputs.material_questions),
                    "material_question",
                    "question_id",
                ),
                *_exact_record_refs(list(proof_inputs.answers), "answer", "answer_id"),
                *_exact_record_refs(
                    list(proof_inputs.semantic_assertions),
                    "semantic_assertion",
                    "assertion_id",
                ),
                *_hard_negative_packet_refs(hard_evidence, snapshot_index),
            ]
        )
        if _sorted_objects(adjudication.get("answer_side_evidence_refs")) != answer_refs:
            raise FixtureGenerationError(
                "Static control adjudication answer-side evidence has drifted."
            )
        for packet in stage2_packets:
            if (
                _sorted_objects(packet.get("answer_side_evidence_refs")) != answer_refs
                or _sorted_objects(packet.get("reference_analysis_refs")) != operation_refs
                or packet.get("execution_comparison_refs") != []
            ):
                raise FixtureGenerationError("Static control Stage-2 proof packet has drifted.")
        static_proof = _revalidate_static_fixture_inputs(
            fixture,
            adjudication,
            proof_inputs,
        )
        if static_proof.get("proof_profile_kind") == "bounded_report_mean_direction_v1":
            proof_claims = sorted(
                str(item["sentence"]) for item in static_proof["derived_facts"]["literal_claims"]
            )
            scoped_claims = sorted(str(claim.get("text", "")) for claim in static_claims)
            if scoped_claims != proof_claims:
                raise FixtureGenerationError(
                    "Static fixture Claim scope does not equal the independently inventoried report claims."
                )
        elif static_claims:
            raise FixtureGenerationError(
                "Static method controls are question-scoped and cannot claim a Claim target."
            )
        expected_proof = _static_control_proof_evidence(
            adjudication,
            reviews,
            proof_inputs.snapshot,
            proof_inputs.workspace_manifests,
            packets,
            manifests,
            proof_inputs.stage1_freeze,
            proof_inputs.scientific_contracts,
            proof_inputs.operations,
            list(proof_inputs.material_questions),
            list(proof_inputs.answers),
            list(proof_inputs.semantic_assertions),
            static_proof,
            hard_evidence,
        )
    elif fixture_kind in {
        "verified_good_fixture",
        "scope_verified_good",
        "hard_negative_fixture",
    }:
        if adjudicated_root_causes:
            raise FixtureGenerationError("A negative control proof cannot contain root causes.")
        contract_refs = _exact_record_refs(
            proof_inputs.scientific_contracts,
            "scientific_contract",
            "contract_id",
        )
        operation_refs = _exact_record_refs(proof_inputs.operations, "operation", "operation_id")
        execution_refs = _exact_record_refs(proof_inputs.executions, "execution", "execution_id")
        if (
            fixture.get("scientific_contract_refs") != contract_refs
            or fixture.get("declared_scope", {}).get("operation_refs") != operation_refs
        ):
            raise FixtureGenerationError(
                "Control fixture contract or operation proof inputs have drifted."
            )
        for ref in fixture.get("declared_scope", {}).get("claim_refs", []):
            _resolve_record_ref(ref, record_index, "control claim scope")
        for contract in proof_inputs.scientific_contracts:
            if contract.get("status") != "resolved":
                raise FixtureGenerationError("A complete control requires resolved contracts.")
            _validate_record_source_refs(
                contract,
                snapshot_index,
                proof_inputs.materialized_root,
                "ScientificContract",
            )
        for operation in proof_inputs.operations:
            if operation.get("inspection_status") != "supported" or operation.get(
                "opaque_boundaries"
            ):
                raise FixtureGenerationError(
                    "A complete control requires supported, non-opaque reviewed Operations."
                )
            _validate_record_source_refs(
                operation,
                snapshot_index,
                proof_inputs.materialized_root,
                "Operation",
            )
        current_proof = fixture.get("proof_evidence")
        if not isinstance(current_proof, dict):
            raise FixtureGenerationError("Complete fixture proof_evidence is absent.")
        hard_evidence = deepcopy(current_proof.get("hard_negative_evidence"))
        if not isinstance(hard_evidence, dict):
            raise FixtureGenerationError("Complete control hard-negative evidence is absent.")
        _validate_hard_negative_evidence(
            hard_evidence,
            fixture_kind,
            record_index,
            snapshot_index,
            proof_inputs.materialized_root,
        )
        answer_refs = _unique_sorted_objects(
            [
                *contract_refs,
                *_hard_negative_packet_refs(hard_evidence, snapshot_index),
            ]
        )
        if _sorted_objects(adjudication.get("answer_side_evidence_refs")) != answer_refs:
            raise FixtureGenerationError("Control adjudication answer-side evidence has drifted.")
        for packet in stage2_packets:
            if (
                _sorted_objects(packet.get("answer_side_evidence_refs")) != answer_refs
                or _sorted_objects(packet.get("reference_analysis_refs")) != operation_refs
                or _sorted_objects(packet.get("execution_comparison_refs")) != execution_refs
            ):
                raise FixtureGenerationError("Control Stage-2 proof packet has drifted.")
        _validate_control_executions(
            fixture_kind,
            str(fixture["execution_evidence"]),
            proof_inputs.environments,
            proof_inputs.executions,
            proof_inputs.sandbox_capabilities,
            record_index,
            proof_inputs.snapshot,
            stage2_packets,
        )
        expected_proof = _control_proof_evidence(
            adjudication,
            reviews,
            proof_inputs.snapshot,
            proof_inputs.workspace_manifests,
            packets,
            manifests,
            proof_inputs.stage1_freeze,
            proof_inputs.scientific_contracts,
            proof_inputs.operations,
            proof_inputs.environments,
            proof_inputs.executions,
            proof_inputs.sandbox_capabilities,
            hard_evidence,
        )
    else:
        raise FixtureGenerationError(
            f"Fixture kind {fixture_kind!r} cannot carry a complete proof."
        )

    try:
        report = validate_case_packet(
            fixture,
            adjudication,
            reviews,
            schema_root,
            adjudicated_root_causes=adjudicated_root_causes,
            snapshot=proof_inputs.snapshot,
            file_records=proof_inputs.file_records,
            asset_identities=proof_inputs.asset_identities,
            materialized_root=proof_inputs.materialized_root,
        )
    except EvaluationValidationError as error:
        raise FixtureGenerationError(str(error)) from error
    if (
        report.get("label_admission") != "admitted_for_declared_fixture_scope"
        or report.get("unverified_checks") != []
    ):
        raise FixtureGenerationError("Fixture proof replay did not readmit the exact label.")
    expected_proof["source_validation_report_digest"] = semantic_digest(report)
    if fixture.get("proof_evidence") != expected_proof:
        raise FixtureGenerationError(
            "Fixture proof projection does not equal the exact replayed evidence set."
        )
    return report


def _require_static_only_proof_basis(proof_inputs: FixtureProofInputs) -> None:
    if any(
        (
            proof_inputs.environments,
            proof_inputs.executions,
            proof_inputs.sandbox_capabilities,
        )
    ):
        raise FixtureGenerationError(
            "A static control cannot acquire execution, environment, or sandbox authority."
        )
    required = {
        "static qualification profile": proof_inputs.static_qualification_profile,
        "static qualification proof": proof_inputs.static_qualification_proof,
        "case assignment artifact": proof_inputs.case_assignment_artifact,
        "static label-freeze artifact": proof_inputs.static_label_freeze_artifact,
        "scientific-label freeze": proof_inputs.scientific_label_freeze,
        "detector manifest": proof_inputs.detector_manifest,
    }
    missing = [label for label, value in required.items() if value is None]
    if missing or not all(
        (
            proof_inputs.parser_manifests,
            proof_inputs.semantic_profile_manifests,
            proof_inputs.version_manifests,
        )
    ):
        raise FixtureGenerationError(
            "Static control exact proof inputs are incomplete: " + ", ".join(missing)
        )


def _revalidate_static_fixture_inputs(
    fixture: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    proof_inputs: FixtureProofInputs,
) -> dict[str, Any]:
    _require_static_only_proof_basis(proof_inputs)
    profile = proof_inputs.static_qualification_profile
    proof = proof_inputs.static_qualification_proof
    assignment = proof_inputs.case_assignment_artifact
    label_artifact = proof_inputs.static_label_freeze_artifact
    scientific_freeze = proof_inputs.scientific_label_freeze
    detector_manifest = proof_inputs.detector_manifest
    assert isinstance(profile, dict)
    assert isinstance(proof, dict)
    assert isinstance(assignment, dict)
    assert isinstance(label_artifact, dict)
    assert isinstance(scientific_freeze, dict)
    assert isinstance(detector_manifest, dict)

    freeze_basis = deepcopy(scientific_freeze)
    freeze_digest = freeze_basis.pop("freeze_digest", None)
    if (
        scientific_freeze.get("record_type") != "evaluation_scientific_label_freeze"
        or freeze_digest != semantic_digest(freeze_basis)
        or scientific_freeze.get("case_id") != adjudication.get("case_id")
        or scientific_freeze.get("adjudication_ref")
        != {
            "record_type": "benchmark_adjudication",
            "record_id": adjudication.get("adjudication_id"),
        }
        or scientific_freeze.get("adjudication_digest") != semantic_digest(adjudication)
        or scientific_freeze.get("label_status") != adjudication.get("label_status")
        or scientific_freeze.get("detector_output_observed") is not False
    ):
        raise FixtureGenerationError(
            "Static control scientific-label freeze does not bind the exact adjudication."
        )
    expected_artifact_payload = {
        "adjudication_digest": semantic_digest(adjudication),
        "adjudication_id": adjudication.get("adjudication_id"),
        "case_id": adjudication.get("case_id"),
        "label_status": adjudication.get("label_status"),
        "scientific_label_freeze_digest": freeze_digest,
    }
    if label_artifact.get("payload") != expected_artifact_payload:
        raise FixtureGenerationError(
            "Static proof label artifact does not project the exact frozen scientific label."
        )
    if _timestamp(str(label_artifact.get("created_at", ""))) < _timestamp(
        str(scientific_freeze.get("frozen_at", ""))
    ):
        raise FixtureGenerationError(
            "Static label-artifact projection predates the scientific-label freeze."
        )
    try:
        profile_kind = profile.get("profile_kind")
        if profile_kind == "typed_static_method_conflict_v1":
            binding = profile.get("method_binding")
            if not isinstance(binding, Mapping):
                raise TypedMethodQualificationError("typed profile binding is absent")
            replayed = revalidate_registered_typed_method_proof(
                proof,
                workspace_root=proof_inputs.materialized_root,
                profile=profile,
                adapter=registered_qualification_adapter(binding),
                case_assignment_artifact=assignment,
                label_freeze_artifact=label_artifact,
                snapshot=proof_inputs.snapshot,
                file_records=proof_inputs.file_records,
                asset_identities=proof_inputs.asset_identities,
                material_questions=proof_inputs.material_questions,
                answers=proof_inputs.answers,
                scientific_contracts=proof_inputs.scientific_contracts,
                semantic_assertions=proof_inputs.semantic_assertions,
                detector_manifest=detector_manifest,
                parser_manifests=proof_inputs.parser_manifests,
                semantic_profile_manifests=proof_inputs.semantic_profile_manifests,
                version_manifests=proof_inputs.version_manifests,
            )
        elif profile_kind == "bounded_analysis_method_conflict_v1":
            replayed = revalidate_analysis_method_proof(
                proof,
                proof_inputs.materialized_root,
                profile,
                assignment,
                label_artifact,
                proof_inputs.snapshot,
                proof_inputs.file_records,
                proof_inputs.asset_identities,
                proof_inputs.material_questions,
                proof_inputs.answers,
                proof_inputs.scientific_contracts,
                proof_inputs.semantic_assertions,
                detector_manifest,
                proof_inputs.parser_manifests,
                proof_inputs.semantic_profile_manifests,
                proof_inputs.version_manifests,
            )
        else:
            replayed = revalidate_static_proof(
                proof,
                proof_inputs.materialized_root,
                profile,
                assignment,
                label_artifact,
                proof_inputs.snapshot,
                proof_inputs.file_records,
                proof_inputs.asset_identities,
                detector_manifest,
                proof_inputs.parser_manifests,
                proof_inputs.semantic_profile_manifests,
                proof_inputs.version_manifests,
            )
    except (
        StaticQualificationError,
        AnalysisMethodQualificationError,
        TypedMethodQualificationError,
    ) as error:
        raise FixtureGenerationError(
            f"Static qualification proof replay failed: {error}"
        ) from error
    if replayed.get("proof_status") != "complete":
        raise FixtureGenerationError("An unavailable static proof cannot establish a control.")
    fixture_provenance = fixture.get("provenance")
    if not isinstance(fixture_provenance, Mapping) or _timestamp(
        str(fixture_provenance.get("created_at", ""))
    ) < _timestamp(str(replayed["chronology"]["proof_frozen_at"])):
        raise FixtureGenerationError("Static control fixture creation predates its proof freeze.")
    if any(
        item.get("completion_status") != "completed"
        for item in [
            *replayed["applicability_results"],
            *replayed["counterevidence_results"],
        ]
    ):
        raise FixtureGenerationError("Static control has an incomplete mandatory check.")
    if profile.get("profile_kind") in {
        "bounded_analysis_method_conflict_v1",
        "typed_static_method_conflict_v1",
    }:
        facts = replayed.get("derived_facts")
        if profile.get("profile_kind") == "typed_static_method_conflict_v1":
            comparison = facts.get("comparison") if isinstance(facts, Mapping) else None
            compatible = (
                isinstance(comparison, Mapping) and comparison.get("outcome") == "covered_negative"
            )
        else:
            compatible = (
                isinstance(facts, Mapping)
                and len(
                    {
                        facts.get("report_operand"),
                        facts.get("source_operand"),
                        facts.get("requirement_operand"),
                    }
                )
                == 1
            )
        if not compatible:
            raise FixtureGenerationError(
                "Static method control does not establish exact report/source/requirement agreement."
            )
    else:
        relation = [
            item
            for item in replayed["applicability_results"]
            if item.get("check_id") == "claim_result_relation"
        ]
        if len(relation) != 1 or relation[0].get("outcome") != "conflict_absent":
            raise FixtureGenerationError(
                "Static negative control does not independently establish claim/result agreement."
            )
    if any(
        item.get("outcome") != "counterevidence_absent"
        for item in replayed["counterevidence_results"]
    ):
        raise FixtureGenerationError(
            "Static negative control retains decisive opposite-direction counterevidence."
        )
    public_inputs = fixture.get("proof_evidence", {}).get("public_inputs", {})
    expected_bound = [_public_input(replayed, "static_qualification_proof", "proof_id")]
    if public_inputs.get("static_qualification_proofs") != expected_bound:
        raise FixtureGenerationError("Static fixture does not bind the exact replayed proof.")
    return replayed


def _static_control_proof_evidence(
    adjudication: dict[str, Any],
    reviews: list[dict[str, Any]],
    snapshot: dict[str, Any],
    workspaces: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    captures: list[dict[str, Any]],
    stage1_freeze: dict[str, Any],
    scientific_contracts: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    material_questions: list[dict[str, Any]],
    answers: list[dict[str, Any]],
    semantic_assertions: list[dict[str, Any]],
    static_proof: dict[str, Any],
    hard_negative_evidence: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    proof = _control_proof_evidence(
        adjudication,
        reviews,
        snapshot,
        workspaces,
        packets,
        captures,
        stage1_freeze,
        scientific_contracts,
        operations,
        [],
        [],
        [],
        hard_negative_evidence,
    )
    proof["controller_profile"] = "fixture-proof-evidence-static-v1"
    proof["public_inputs"]["static_qualification_proofs"] = [
        _public_input(static_proof, "static_qualification_proof", "proof_id")
    ]
    proof["public_inputs"]["material_questions"] = _public_inputs(
        material_questions, "material_question", "question_id"
    )
    proof["public_inputs"]["answers"] = _public_inputs(answers, "answer", "answer_id")
    proof["public_inputs"]["semantic_assertions"] = _public_inputs(
        semantic_assertions, "semantic_assertion", "assertion_id"
    )
    return proof


def _control_proof_evidence(
    adjudication: dict[str, Any],
    reviews: list[dict[str, Any]],
    snapshot: dict[str, Any],
    workspaces: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    captures: list[dict[str, Any]],
    stage1_freeze: dict[str, Any],
    scientific_contracts: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    environments: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    sandbox_capabilities: list[dict[str, Any]],
    hard_negative_evidence: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    proof = _positive_proof_evidence(
        adjudication,
        reviews,
        [],
        snapshot,
        workspaces,
        packets,
        captures,
        stage1_freeze,
    )
    proof["public_inputs"].update(
        {
            "scientific_contracts": _public_inputs(
                scientific_contracts, "scientific_contract", "contract_id"
            ),
            "operations": _public_inputs(operations, "operation", "operation_id"),
            "environments": _public_inputs(environments, "environment", "environment_id"),
            "executions": _public_inputs(executions, "execution", "execution_id"),
            "sandbox_capabilities": _public_inputs(
                sandbox_capabilities,
                "sandbox_capability",
                "sandbox_capability_id",
            ),
        }
    )
    proof["hard_negative_evidence"] = deepcopy(hard_negative_evidence)
    return proof


def _public_inputs(
    records: list[dict[str, Any]], record_type: str, id_field: str
) -> list[dict[str, Any]]:
    return _sort_public_inputs([_public_input(record, record_type, id_field) for record in records])


def _exact_record_refs(
    records: list[dict[str, Any]], record_type: str, id_field: str
) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    identities: set[str] = set()
    for record in records:
        if record.get("record_type") != record_type:
            raise FixtureGenerationError(
                f"Expected {record_type} proof input, got {record.get('record_type')!r}."
            )
        record_id = str(record.get(id_field, ""))
        if not record_id or record_id in identities:
            raise FixtureGenerationError(f"Duplicate or missing {record_type} identity.")
        identities.add(record_id)
        refs.append({"record_type": record_type, "record_id": record_id})
    return _sorted_objects(refs)


def _record_index(records: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        identity = _record_identity(record)
        if identity in result:
            raise FixtureGenerationError(
                f"Duplicate exact proof record {identity[0]}/{identity[1]}."
            )
        result[identity] = record
    return result


def _record_identity(record: dict[str, Any]) -> tuple[str, str]:
    record_type = record.get("record_type")
    if not isinstance(record_type, str) or not record_type:
        raise FixtureGenerationError("Evidence input has no public record_type.")
    explicit_fields = {
        "agent_review": "review_id",
        "benchmark_adjudication": "adjudication_id",
        "benchmark_fixture": "fixture_id",
        "scientific_contract": "contract_id",
        "repository_snapshot": "snapshot_id",
        "file_record": "file_record_id",
        "asset_identity": "asset_identity_id",
        "operation": "operation_id",
        "environment": "environment_id",
        "execution": "execution_id",
        "sandbox_capability": "sandbox_capability_id",
    }
    field = explicit_fields.get(record_type, f"{record_type}_id")
    value = record.get(field)
    if not isinstance(value, str) or not value:
        candidates = [
            key
            for key, candidate in record.items()
            if key.endswith("_id")
            and key != "audit_run_id"
            and isinstance(candidate, str)
            and candidate
        ]
        if len(candidates) != 1:
            raise FixtureGenerationError(
                f"Cannot determine exact identity for evidence record {record_type!r}."
            )
        value = str(record[candidates[0]])
    return record_type, value


def _resolve_record_ref(
    ref: dict[str, Any],
    record_index: dict[tuple[str, str], dict[str, Any]],
    purpose: str,
) -> dict[str, Any]:
    key = (str(ref.get("record_type", "")), str(ref.get("record_id", "")))
    resolved = record_index.get(key)
    if resolved is None:
        raise FixtureGenerationError(f"Unresolved {purpose} record reference {key[0]}/{key[1]}.")
    return resolved


def _validate_record_source_refs(
    record: dict[str, Any],
    snapshot_index: SnapshotEvidenceIndex,
    materialized_root: Path,
    purpose: str,
) -> None:
    source_refs = record.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        raise FixtureGenerationError(f"{purpose} has no independently checkable source refs.")
    for source_ref in source_refs:
        try:
            validate_file_source_ref(source_ref, snapshot_index, materialized_root)
        except EvaluationValidationError as error:
            raise FixtureGenerationError(f"{purpose} source evidence failed: {error}") from error


def _validate_hard_negative_evidence(
    evidence: dict[str, list[dict[str, Any]]],
    fixture_kind: str,
    record_index: dict[tuple[str, str], dict[str, Any]],
    snapshot_index: SnapshotEvidenceIndex,
    materialized_root: Path,
) -> None:
    required = {"suspicious_pattern", "decisive_innocent_explanation"}
    if set(evidence) != required:
        raise FixtureGenerationError("Hard-negative evidence has unexpected fields.")
    if fixture_kind in {"hard_negative_fixture", "static_scope_hard_negative"}:
        if any(not evidence[field] for field in required):
            raise FixtureGenerationError(
                "A hard-negative control requires both suspicious-pattern and decisive-explanation evidence."
            )
    elif any(evidence[field] for field in required):
        raise FixtureGenerationError(
            "Verified-good controls cannot carry hard-negative proof evidence."
        )
    # The fixture schema is the authoritative EvidenceItem shape.  Validate it in a
    # temporary schema-valid projection rather than accepting free-form descriptions.
    for field in sorted(required):
        for item in evidence[field]:
            if not isinstance(item, dict):
                raise FixtureGenerationError("Hard-negative evidence items must be objects.")
            for source_ref in item.get("source_refs", []):
                try:
                    validate_file_source_ref(source_ref, snapshot_index, materialized_root)
                except EvaluationValidationError as error:
                    raise FixtureGenerationError(
                        f"Hard-negative {field} source evidence failed: {error}"
                    ) from error
            for ref in item.get("record_refs", []):
                _resolve_record_ref(ref, record_index, f"hard-negative {field}")
            if not item.get("source_refs") and not item.get("record_refs"):
                raise FixtureGenerationError(
                    "Hard-negative evidence cannot be established by prose or confidence alone."
                )


def _hard_negative_packet_refs(
    evidence: dict[str, list[dict[str, Any]]], snapshot_index: SnapshotEvidenceIndex
) -> list[dict[str, str]]:
    """Project evidence into the typed public refs accepted by Stage-2 packets."""

    refs: list[dict[str, str]] = []
    for category in evidence.values():
        for item in category:
            refs.extend(deepcopy(item.get("record_refs", [])))
            for source_ref in item.get("source_refs", []):
                path = source_ref.get("path")
                file_record = (
                    snapshot_index.files_by_path.get(path) if isinstance(path, str) else None
                )
                if file_record is None:
                    raise FixtureGenerationError(
                        "Hard-negative source evidence has no exact FileRecord packet projection."
                    )
                refs.append(
                    {
                        "record_type": "file_record",
                        "record_id": str(file_record["file_record_id"]),
                    }
                )
    return refs


def _validate_control_executions(
    fixture_kind: str,
    execution_evidence: str,
    environments: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    sandbox_capabilities: list[dict[str, Any]],
    record_index: dict[tuple[str, str], dict[str, Any]],
    snapshot: dict[str, Any],
    stage2_packets: list[dict[str, Any]],
) -> None:
    if not environments or not executions:
        raise FixtureGenerationError(
            "A complete control requires exact Environment and Execution records."
        )
    latest_allowed = min(_timestamp(str(packet["created_at"])) for packet in stage2_packets)
    snapshot_time = _timestamp(str(snapshot["captured_at"]))
    environment_index = {
        str(environment["environment_id"]): environment for environment in environments
    }
    capability_index = {
        str(capability["sandbox_capability_id"]): capability for capability in sandbox_capabilities
    }
    referenced_environments: set[str] = set()
    referenced_capabilities: set[str] = set()
    for execution in executions:
        environment_ref = execution["environment_ref"]
        environment_id = str(environment_ref.get("record_id", ""))
        environment = environment_index.get(environment_id)
        if environment_ref.get("record_type") != "environment" or environment is None:
            raise FixtureGenerationError("Execution has no exact supplied Environment.")
        referenced_environments.add(environment_id)
        if not execution.get("input_refs") or not execution.get("output_refs"):
            raise FixtureGenerationError(
                "Control Execution requires nonempty input and output refs."
            )
        for ref in [*execution["input_refs"], *execution["output_refs"]]:
            _resolve_record_ref(ref, record_index, "Execution input/output")
        timing = execution["timing"]
        if timing.get("state") not in {"observed", "imported"}:
            raise FixtureGenerationError("Control Execution timing was not observed or imported.")
        started_at = _timestamp(str(timing["started_at"]))
        finished_at = _timestamp(str(timing["finished_at"]))
        if finished_at < started_at or finished_at > latest_allowed:
            raise FixtureGenerationError(
                "Control Execution chronology does not fit the immutable answer-side panel."
            )
        if execution["exit"].get("state") != "succeeded" or execution["exit"].get("code") != 0:
            raise FixtureGenerationError("A failed Execution cannot establish a control.")

        if execution_evidence == "clean_environment_executed":
            if started_at < snapshot_time:
                raise FixtureGenerationError(
                    "Clean project execution cannot predate its immutable source snapshot."
                )
            if (
                execution.get("execution_kind") != "project_workflow"
                or execution.get("actor") != "project_workflow"
                or execution.get("identity_strength") != "exact"
                or environment.get("environment_kind") != "project_runtime"
                or environment.get("identity_status") != "exact"
            ):
                raise FixtureGenerationError(
                    "Clean execution requires an exact project-workflow Execution and project Environment."
                )
            sandbox = execution["sandbox"]
            capability_ref = sandbox.get("sandbox_capability_ref")
            capability_id = (
                str(capability_ref.get("record_id", "")) if isinstance(capability_ref, dict) else ""
            )
            capability = capability_index.get(capability_id)
            if (
                not isinstance(capability_ref, dict)
                or capability_ref.get("record_type") != "sandbox_capability"
                or capability is None
            ):
                raise FixtureGenerationError(
                    "Clean execution has no exact supplied SandboxCapability."
                )
            referenced_capabilities.add(capability_id)
            controls = capability.get("controls", {})
            if (
                sandbox.get("authorization_status") != "authorized"
                or sandbox.get("project_code_executed") is not True
                or sandbox.get("network_policy") != "denied"
                or capability.get("backend_kind") != "rootless_oci"
                or capability.get("rootless_verified") is not True
                or capability.get("project_code_execution_supported") is not True
                or capability.get("unsafe_fallback_available") is not False
                or not all(
                    controls.get(name) is True
                    for name in (
                        "repository_read_only",
                        "writable_roots_enforced",
                        "network_default_denied",
                        "resource_limits_enforced",
                        "process_limits_enforced",
                        "device_access_restricted",
                        "capabilities_dropped",
                    )
                )
            ):
                raise FixtureGenerationError(
                    "Execution does not prove the authorized rootless-OCI control envelope."
                )
            if _timestamp(str(capability["captured_at"])) > started_at:
                raise FixtureGenerationError(
                    "Sandbox capability was captured after execution began."
                )
        elif execution_evidence == "documented_external_execution":
            if fixture_kind != "scope_verified_good":
                raise FixtureGenerationError(
                    "Documented external execution is limited to scope_verified_good fixtures."
                )
            sandbox = execution["sandbox"]
            if (
                execution.get("execution_kind") != "imported"
                or execution.get("actor") != "external_import"
                or execution.get("identity_strength") not in {"imported_strong", "exact"}
                or timing.get("state") != "imported"
                or environment.get("environment_kind") != "imported_runtime"
                or not execution.get("limitations")
                or sandbox.get("project_code_executed") is not False
                or sandbox.get("authorization_status") not in {"not_required", "unknown"}
                or sandbox.get("network_policy") not in {"denied", "unknown"}
                or "sandbox_capability_ref" in sandbox
            ):
                raise FixtureGenerationError(
                    "Documented external execution requires a bounded imported Execution with limitations."
                )
        else:
            raise FixtureGenerationError(
                "A complete control cannot be established without execution evidence."
            )
    if referenced_environments != set(environment_index):
        raise FixtureGenerationError(
            "Supplied Environments do not exactly equal the control Execution dependencies."
        )
    if execution_evidence == "clean_environment_executed":
        if not sandbox_capabilities or referenced_capabilities != set(capability_index):
            raise FixtureGenerationError(
                "Supplied SandboxCapabilities do not exactly equal clean Execution dependencies."
            )
    elif sandbox_capabilities:
        raise FixtureGenerationError(
            "Documented external execution cannot acquire authority from a local sandbox record."
        )


def _validate_control_fixture_spec(fixture_spec: dict[str, Any]) -> None:
    required = {
        "problem_id",
        "fixture_kind",
        "declared_scope",
        "scientific_contract_refs",
        "execution_evidence",
        "hard_negative_evidence",
        "limitations",
    }
    if set(fixture_spec) != required:
        raise FixtureGenerationError("Control fixture specification has unexpected fields.")
    if fixture_spec.get("fixture_kind") not in {
        "verified_good_fixture",
        "scope_verified_good",
        "hard_negative_fixture",
        "static_scope_verified_good",
        "static_scope_hard_negative",
    }:
        raise FixtureGenerationError("Unsupported control fixture_kind.")
    if not isinstance(fixture_spec.get("problem_id"), str) or not fixture_spec["problem_id"]:
        raise FixtureGenerationError("Control problem_id must be non-empty.")
    scope = fixture_spec.get("declared_scope")
    if not isinstance(scope, dict) or set(scope) != {
        "claim_refs",
        "detector_ids",
        "issue_classes",
        "operation_refs",
    }:
        raise FixtureGenerationError("Control declared_scope is malformed.")
    method_question_scope = scope.get("detector_ids") == [
        "detector:bounded-analysis-method-conflict"
    ]
    for field in ("claim_refs", "operation_refs"):
        values = scope[field]
        if (
            not isinstance(values, list)
            or (not values and not method_question_scope)
            or not all(isinstance(value, dict) for value in values)
        ):
            raise FixtureGenerationError(f"Control {field} must contain exact record refs.")
        if _sorted_objects(values) != values:
            raise FixtureGenerationError(f"Control {field} must be canonically ordered.")
    for field in ("detector_ids", "issue_classes"):
        values = scope[field]
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value for value in values)
            or values != sorted(set(values))
        ):
            raise FixtureGenerationError(
                f"Control {field} must be one ordered unique nonempty string list."
            )
    refs = fixture_spec.get("scientific_contract_refs")
    if not isinstance(refs, list) or not refs or not all(isinstance(ref, dict) for ref in refs):
        raise FixtureGenerationError("Control requires exact ScientificContract refs.")
    if _sorted_objects(refs) != refs:
        raise FixtureGenerationError("Control ScientificContract refs must be ordered.")
    if fixture_spec.get("execution_evidence") not in {
        "clean_environment_executed",
        "documented_external_execution",
        "not_executed",
    }:
        raise FixtureGenerationError("Control execution_evidence is not admissible.")
    is_static = str(fixture_spec.get("fixture_kind", "")).startswith("static_scope_")
    if is_static != (fixture_spec.get("execution_evidence") == "not_executed"):
        raise FixtureGenerationError(
            "Only static control fixture kinds may use the non-executing proof basis."
        )
    evidence = fixture_spec.get("hard_negative_evidence")
    if not isinstance(evidence, dict) or any(
        not isinstance(evidence.get(field), list)
        for field in ("suspicious_pattern", "decisive_innocent_explanation")
    ):
        raise FixtureGenerationError("Control hard_negative_evidence is malformed.")
    limitations = fixture_spec.get("limitations")
    if not isinstance(limitations, list) or any(
        not isinstance(value, str) or not value for value in limitations
    ):
        raise FixtureGenerationError("Control limitations must be one list of nonempty strings.")


def _sorted_objects(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise FixtureGenerationError("Expected one list of evidence/reference objects.")
    return sorted((deepcopy(item) for item in value), key=semantic_digest)


def _unique_sorted_objects(value: Any) -> list[dict[str, Any]]:
    unique = {semantic_digest(item): item for item in _sorted_objects(value)}
    return [deepcopy(unique[digest]) for digest in sorted(unique)]


def generate_ambiguous_fixture(
    adjudication: dict[str, Any],
    snapshot: dict[str, Any],
    file_records: list[dict[str, Any]],
    asset_identities: list[dict[str, Any]],
    fixture_spec: dict[str, Any],
    schema_root: Path,
    *,
    created_at: str,
    output: Path,
) -> dict[str, Any]:
    """Generate only an excluded ambiguous fixture from exact public evidence."""

    if output.exists() or output.is_symlink():
        raise FixtureGenerationError(f"BenchmarkFixture output already exists: {output}")
    registry = LocalSchemaRegistry(schema_root)
    try:
        for record in [adjudication, snapshot, *file_records, *asset_identities]:
            registry.validate(record)
    except RecordValidationError as error:
        raise FixtureGenerationError(str(error)) from error
    try:
        validate_content_addressed_snapshot(snapshot, file_records, asset_identities)
    except SnapshotEvidenceError as error:
        raise FixtureGenerationError(str(error)) from error
    _validate_fixture_spec(fixture_spec)
    if adjudication.get("label_status") not in _EXCLUDED_LABELS:
        raise FixtureGenerationError(
            "This bounded generator accepts only excluded ambiguous adjudications."
        )
    adjudicated_at = _timestamp(str(adjudication["adjudicated_at"]))
    snapshot_captured_at = _timestamp(str(snapshot["captured_at"]))
    fixture_created_at = _timestamp(created_at)
    if adjudicated_at < snapshot_captured_at or fixture_created_at < adjudicated_at:
        raise FixtureGenerationError(
            "Snapshot, adjudication, and fixture creation chronology is invalid."
        )

    fixture_spec_digest = semantic_digest(fixture_spec)
    fixture: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "benchmark_fixture",
        "fixture_id": stable_id(
            "ambiguous-fixture",
            str(fixture_spec["problem_id"]),
            str(snapshot["snapshot_id"]),
            str(adjudication["adjudication_id"]),
            fixture_spec_digest,
        ),
        "fixture_kind": "ambiguous_fixture",
        "qualification_proof_status": "excluded_label",
        "proof_evidence": None,
        "corpus_partition": "public_development",
        "problem_id": fixture_spec["problem_id"],
        "snapshot_ref": {
            "record_type": "repository_snapshot",
            "record_id": snapshot["snapshot_id"],
        },
        "declared_scope": fixture_spec["declared_scope"],
        "execution_evidence": "not_executed",
        "adjudication_ref": {
            "record_type": "benchmark_adjudication",
            "record_id": adjudication["adjudication_id"],
        },
        "proof_obligations": {
            "claim_output_agreement": False,
            "scope_semantics_resolved": False,
            "reviewed_operations_identified": False,
            "no_unresolved_material_disagreement": False,
            "hard_negative_pattern_documented": False,
            "decisive_innocent_explanation_documented": False,
            "positive_root_cause_documented": False,
        },
        "global_correctness_claim_allowed": False,
        "expected_issue_labels": [],
        "expected_root_cause_refs": [],
        "scientific_contract_refs": fixture_spec["scientific_contract_refs"],
        "limitations": sorted(
            {
                *fixture_spec["limitations"],
                "Excluded ambiguous fixture; it is not a positive or verified-good control.",
                "No project execution or scientific-label admission is established by generation.",
            }
        ),
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-eval",
                "display_name": "sc-referee evaluation controller",
            },
            "method": "explicit_ambiguous_fixture_generation",
            "created_at": created_at,
            "tool": "sc-referee-eval",
            "tool_version": "0.1.0",
        },
        "extensions": {
            "x-fixture-spec-digest": fixture_spec_digest,
            "x-snapshot-digest": snapshot["snapshot_digest"],
        },
    }
    try:
        registry.validate(fixture)
    except RecordValidationError as error:  # pragma: no cover - exact spec validation routes here
        raise FixtureGenerationError(str(error)) from error
    write_normalized_json_once(output, fixture)
    return fixture


def _validate_fixture_spec(fixture_spec: dict[str, Any]) -> None:
    if set(fixture_spec) != {
        "problem_id",
        "declared_scope",
        "scientific_contract_refs",
        "limitations",
    }:
        raise FixtureGenerationError("Ambiguous fixture specification has unexpected fields.")
    if not isinstance(fixture_spec.get("problem_id"), str) or not fixture_spec["problem_id"]:
        raise FixtureGenerationError("Ambiguous fixture problem_id must be non-empty.")
    if not isinstance(fixture_spec.get("declared_scope"), dict):
        raise FixtureGenerationError("Ambiguous fixture declared_scope must be one object.")
    scope = fixture_spec["declared_scope"]
    if set(scope) != {"claim_refs", "detector_ids", "issue_classes", "operation_refs"}:
        raise FixtureGenerationError("Ambiguous fixture declared_scope has unexpected fields.")
    if scope.get("claim_refs") != [] or scope.get("operation_refs") != []:
        raise FixtureGenerationError(
            "This first generator accepts detector/issue scope only; record refs are unresolved."
        )
    if not isinstance(scope.get("detector_ids"), list) or not scope["detector_ids"]:
        raise FixtureGenerationError("Ambiguous fixture requires at least one detector_id.")
    if not isinstance(scope.get("issue_classes"), list) or not scope["issue_classes"]:
        raise FixtureGenerationError("Ambiguous fixture requires at least one issue class.")
    for key in ("scientific_contract_refs", "limitations"):
        if not isinstance(fixture_spec.get(key), list):
            raise FixtureGenerationError(f"Ambiguous fixture {key} must be one list.")
    if not all(isinstance(value, str) and value for value in fixture_spec["limitations"]):
        raise FixtureGenerationError("Ambiguous fixture limitations must be non-empty strings.")
    if not all(isinstance(value, dict) for value in fixture_spec["scientific_contract_refs"]):
        raise FixtureGenerationError(
            "Ambiguous fixture scientific_contract_refs must be record-reference objects."
        )
    if fixture_spec["scientific_contract_refs"]:
        raise FixtureGenerationError(
            "This first generator cannot resolve ScientificContract references."
        )


def _validate_positive_fixture_spec(fixture_spec: dict[str, Any]) -> None:
    if set(fixture_spec) != {
        "problem_id",
        "declared_scope",
        "scientific_contract_refs",
        "limitations",
    }:
        raise FixtureGenerationError("Positive fixture specification has unexpected fields.")
    if not isinstance(fixture_spec.get("problem_id"), str) or not fixture_spec["problem_id"]:
        raise FixtureGenerationError("Positive fixture problem_id must be non-empty.")
    scope = fixture_spec.get("declared_scope")
    if not isinstance(scope, dict) or set(scope) != {
        "claim_refs",
        "detector_ids",
        "issue_classes",
        "operation_refs",
    }:
        raise FixtureGenerationError("Positive fixture declared_scope is malformed.")
    if scope["claim_refs"] or scope["operation_refs"]:
        raise FixtureGenerationError(
            "This positive generator accepts detector/issue scope only; record refs are unresolved."
        )
    for field in ("detector_ids", "issue_classes"):
        values = scope[field]
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value for value in values)
            or values != sorted(set(values))
        ):
            raise FixtureGenerationError(
                f"Positive fixture {field} must be one ordered unique nonempty string list."
            )
    if fixture_spec.get("scientific_contract_refs") != []:
        raise FixtureGenerationError(
            "This positive generator cannot resolve ScientificContract references."
        )
    limitations = fixture_spec.get("limitations")
    if not isinstance(limitations, list) or any(
        not isinstance(value, str) or not value for value in limitations
    ):
        raise FixtureGenerationError(
            "Positive fixture limitations must be one list of nonempty strings."
        )


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise FixtureGenerationError(f"Invalid fixture-generation timestamp {value!r}.") from error
    if parsed.tzinfo is None:
        raise FixtureGenerationError("Fixture-generation timestamps must include an offset.")
    return parsed
