from __future__ import annotations

import hashlib
import inspect
import itertools
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, TypeVar, cast

import pytest
from sc_referee_evaluation.audit_ladder.slice_b import (
    CsvQuestionRequestV1,
    render_slice_b_report_v1,
)
from sc_referee_evaluation.audit_ladder.slice_b.composition import (
    SliceBAnswerDispositionV1,
    SliceBAnswerTreeContractError,
    SliceBAnswerTreeResolutionV1,
    SliceBCompositionContractError,
    SliceBCompositionDispositionV1,
    SliceBCompositionResultV1,
    compose_slice_b_question_v1,
    resolve_slice_b_answer_tree_v1,
)
from sc_referee_evaluation.audit_ladder.slice_b.renderer import (
    CsvComparisonGroupSizesObservationV1,
    CsvSelectedCardinalitiesObservationV1,
    CsvTableShapeObservationV1,
    CsvUnitComparisonIncidenceObservationV1,
    SliceBObservationSetV1,
    SliceBPrimaryRefusalReasonV1,
    SliceBQuestionRenderIRV1,
    render_slice_b_component_v1,
)

from sc_referee.controller import (
    FrozenFileManifestInput,
    ManifestBoundFrozenInspectionContext,
)
from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.scientific_checks.core import FrozenBaseRecord, FrozenMaterialInput, RecordRef

_SELECTED_PATH = "inputs/selected.csv"
_MATERIAL_CSV = (
    b"HEADER_ALPHA,HEADER_BETA,HEADER_GAMMA\n"
    b"RAW_CELL_ONE,ARM_A,1\n"
    b"RAW_CELL_ONE,ARM_B,2\n"
    b"RAW_CELL_TWO,ARM_A,3\n"
    b"RAW_CELL_TWO,ARM_B,4\n"
)
_ANSWER_TOKENS = ("yes", "no", "unknown", "not-applicable")
_T = TypeVar("_T")


@dataclass(frozen=True)
class _Fixture:
    context: ManifestBoundFrozenInspectionContext
    selected_path: str
    content: bytes
    snapshot_record: FrozenBaseRecord
    selected_file_record: FrozenBaseRecord
    selected_identity_record: FrozenBaseRecord
    scope_digest: str


def _record(ref: RecordRef, payload: dict[str, object]) -> FrozenBaseRecord:
    return FrozenBaseRecord.from_record(ref, payload)


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return sha256_digest(encoded)


def _fixture(
    content: bytes = _MATERIAL_CSV,
    *,
    selected_path: str = _SELECTED_PATH,
    suffix: str = "base",
) -> _Fixture:
    identity_suffix = hashlib.sha256(content + suffix.encode("ascii")).hexdigest()[:16]
    snapshot_digest = sha256_digest(f"snapshot:{identity_suffix}".encode("ascii"))
    surface = RecordRef("publication_surface", f"surface:{identity_suffix}")
    other_surface = RecordRef("publication_surface", f"surface:other:{identity_suffix}")
    artifact = RecordRef("artifact", f"artifact:{identity_suffix}")
    snapshot_ref = RecordRef("repository_snapshot", f"snapshot:{identity_suffix}")
    selected_file_ref = RecordRef("file_record", f"file:selected:{identity_suffix}")
    selected_identity_ref = RecordRef("asset_identity", f"identity:selected:{identity_suffix}")
    other_path = "support/other.csv"
    other_content = b"left,right\n1,2\n"
    other_file_ref = RecordRef("file_record", f"file:other:{identity_suffix}")
    other_identity_ref = RecordRef("asset_identity", f"identity:other:{identity_suffix}")
    directory_ref = RecordRef("file_record", f"file:directory:{identity_suffix}")
    directory_identity_ref = RecordRef("asset_identity", f"identity:directory:{identity_suffix}")
    manifest_ref = "observed/files.jsonl"
    material_paths = sorted((selected_path, other_path))
    snapshot_payload: dict[str, object] = {
        "snapshot_id": snapshot_ref.record_id,
        "snapshot_digest": snapshot_digest,
        "included_roots": ["."],
        "file_manifest_ref": manifest_ref,
        "immutability": True,
        "extensions": {
            "x-material-full-digest-paths": material_paths,
            "x-material-input-identities": [
                {"path": path, "tier": "full_digest"} for path in material_paths
            ],
        },
    }
    snapshot_record = _record(snapshot_ref, snapshot_payload)
    selected_file = _record(
        selected_file_ref,
        {
            "record_type": "file_record",
            "file_record_id": selected_file_ref.record_id,
            "path": selected_path,
            "entry_kind": "regular_file",
            "byte_size": len(content),
            "snapshot_ref": snapshot_ref.to_dict(),
            "asset_identity_ref": selected_identity_ref.to_dict(),
        },
    )
    selected_identity = _record(
        selected_identity_ref,
        {
            "record_type": "asset_identity",
            "asset_identity_id": selected_identity_ref.record_id,
            "tier": "full_digest",
            "asset_ref": selected_file_ref.to_dict(),
            "identity_evidence": {
                "kind": "full_digest",
                "digest": sha256_digest(content),
            },
        },
    )
    other_file = _record(
        other_file_ref,
        {
            "record_type": "file_record",
            "file_record_id": other_file_ref.record_id,
            "path": other_path,
            "entry_kind": "regular_file",
            "byte_size": len(other_content),
            "snapshot_ref": snapshot_ref.to_dict(),
            "asset_identity_ref": other_identity_ref.to_dict(),
        },
    )
    other_identity = _record(
        other_identity_ref,
        {
            "record_type": "asset_identity",
            "asset_identity_id": other_identity_ref.record_id,
            "tier": "full_digest",
            "asset_ref": other_file_ref.to_dict(),
            "identity_evidence": {
                "kind": "full_digest",
                "digest": sha256_digest(other_content),
            },
        },
    )
    directory = _record(
        directory_ref,
        {
            "record_type": "file_record",
            "file_record_id": directory_ref.record_id,
            "path": "support/nested",
            "entry_kind": "directory",
            "byte_size": 0,
            "snapshot_ref": snapshot_ref.to_dict(),
            "asset_identity_ref": directory_identity_ref.to_dict(),
        },
    )
    directory_identity = _record(
        directory_identity_ref,
        {
            "record_type": "asset_identity",
            "asset_identity_id": directory_identity_ref.record_id,
            "tier": "unidentified",
            "asset_ref": directory_ref.to_dict(),
            "identity_evidence": {"kind": "unidentified", "reason": "directory"},
        },
    )
    file_records = tuple(sorted((selected_file, other_file, directory), key=_record_path))
    manifest_bytes = b"".join(record.canonical_payload + b"\n" for record in file_records)
    manifest = FrozenFileManifestInput(
        file_manifest_ref=manifest_ref,
        canonical_jsonl_bytes=manifest_bytes,
        manifest_digest=sha256_digest(manifest_bytes),
    )
    materials_by_path = {
        selected_path: FrozenMaterialInput(
            path=selected_path,
            file_ref=selected_file_ref,
            asset_identity_ref=selected_identity_ref,
            content=content,
            content_digest=sha256_digest(content),
        ),
        other_path: FrozenMaterialInput(
            path=other_path,
            file_ref=other_file_ref,
            asset_identity_ref=other_identity_ref,
            content=other_content,
            content_digest=sha256_digest(other_content),
        ),
    }
    context = ManifestBoundFrozenInspectionContext(
        snapshot_digest=snapshot_digest,
        selected_surface_ref=surface,
        selected_artifact_ref=artifact,
        documents=(),
        base_records=(
            _record(surface, {"publication_surface_id": surface.record_id}),
            _record(other_surface, {"publication_surface_id": other_surface.record_id}),
            _record(artifact, {"artifact_id": artifact.record_id}),
            snapshot_record,
            selected_file,
            selected_identity,
            other_file,
            other_identity,
            directory,
            directory_identity,
        ),
        material_inputs=tuple(materials_by_path[path] for path in material_paths),
        file_manifest_input=manifest,
    )
    scope_digest = _oracle_scope_digest(
        snapshot_record=snapshot_record,
        manifest=manifest,
        selected_path=selected_path,
        selected_file_record=selected_file,
        selected_identity_record=selected_identity,
        content=content,
    )
    return _Fixture(
        context=context,
        selected_path=selected_path,
        content=content,
        snapshot_record=snapshot_record,
        selected_file_record=selected_file,
        selected_identity_record=selected_identity,
        scope_digest=scope_digest,
    )


def _record_path(record: FrozenBaseRecord) -> str:
    value = json.loads(record.canonical_payload)
    assert isinstance(value, dict)
    return cast(str, value["path"])


def _oracle_scope_digest(
    *,
    snapshot_record: FrozenBaseRecord,
    manifest: FrozenFileManifestInput,
    selected_path: str,
    selected_file_record: FrozenBaseRecord,
    selected_identity_record: FrozenBaseRecord,
    content: bytes,
) -> str:
    return _canonical_digest(
        {
            "profile": "slice-b-explicit-material-input-selection-v1",
            "snapshot_ref": snapshot_record.ref.to_dict(),
            "snapshot_payload_digest": sha256_digest(snapshot_record.canonical_payload),
            "file_manifest_ref": manifest.file_manifest_ref,
            "manifest_digest": sha256_digest(manifest.canonical_jsonl_bytes),
            "selected_path": selected_path,
            "selected_file_ref": selected_file_record.ref.to_dict(),
            "selected_asset_identity_ref": selected_identity_record.ref.to_dict(),
            "selected_content_digest": sha256_digest(content),
        }
    )


def _oracle_observations(
    fixture: _Fixture,
    *,
    context: ManifestBoundFrozenInspectionContext | None = None,
    scope_digest: str | None = None,
) -> SliceBObservationSetV1:
    active_context = fixture.context if context is None else context
    active_scope = fixture.scope_digest if scope_digest is None else scope_digest
    physical = fixture.content[:-1].split(b"\n")
    rows = tuple(tuple(line.split(b",")) for line in physical)
    data = rows[1:]
    candidates = [row[0] for row in data]
    comparisons = [row[1] for row in data]
    candidate_counts = Counter(candidates)
    comparison_counts = Counter(comparisons)
    associations: dict[bytes, set[bytes]] = defaultdict(set)
    for candidate, comparison in zip(candidates, comparisons, strict=True):
        associations[candidate].add(comparison)
    histogram = Counter(len(values) for values in associations.values())
    file_ref_digest = _canonical_digest(fixture.selected_file_record.ref.to_dict())
    content_digest = sha256_digest(fixture.content)
    common: dict[str, object] = {
        "observation_version": "slice-b-observation-v1",
        "snapshot_digest": active_context.snapshot_digest,
        "file_record_ref_digest": file_ref_digest,
        "content_digest": content_digest,
        "selected_file_ordinal": 1,
        "review_scope_selection_evidence_digest": active_scope,
        "finding_eligible": False,
    }
    shape_fields = {
        **common,
        "observation_type": "csv-table-shape-v1",
        "verifier_id": "slice-b-csv-shape-verifier-v1",
        "data_row_count": len(data),
        "column_count": len(rows[0]),
    }
    shape = CsvTableShapeObservationV1(
        observation_version="slice-b-observation-v1",
        observation_type="csv-table-shape-v1",
        verifier_id="slice-b-csv-shape-verifier-v1",
        snapshot_digest=active_context.snapshot_digest,
        file_record_ref_digest=file_ref_digest,
        content_digest=content_digest,
        selected_file_ordinal=1,
        review_scope_selection_evidence_digest=active_scope,
        data_row_count=len(data),
        column_count=len(rows[0]),
        observation_id=_canonical_digest(shape_fields),
        finding_eligible=False,
    )
    cardinality_fields = {
        **common,
        "observation_type": "csv-selected-cardinalities-v1",
        "verifier_id": "slice-b-csv-cardinality-verifier-v1",
        "candidate_unit_column_index": 0,
        "comparison_column_index": 1,
        "candidate_unit_distinct_count": len(candidate_counts),
        "comparison_distinct_count": len(comparison_counts),
    }
    cardinality = CsvSelectedCardinalitiesObservationV1(
        observation_version="slice-b-observation-v1",
        observation_type="csv-selected-cardinalities-v1",
        verifier_id="slice-b-csv-cardinality-verifier-v1",
        snapshot_digest=active_context.snapshot_digest,
        file_record_ref_digest=file_ref_digest,
        content_digest=content_digest,
        selected_file_ordinal=1,
        review_scope_selection_evidence_digest=active_scope,
        candidate_unit_column_index=0,
        comparison_column_index=1,
        candidate_unit_distinct_count=len(candidate_counts),
        comparison_distinct_count=len(comparison_counts),
        observation_id=_canonical_digest(cardinality_fields),
        finding_eligible=False,
    )
    sizes = tuple(sorted(comparison_counts.values()))
    group_fields = {
        **common,
        "observation_type": "csv-comparison-group-sizes-v1",
        "verifier_id": "slice-b-csv-group-size-verifier-v1",
        "comparison_column_index": 1,
        "sorted_group_sizes": sizes,
    }
    group = CsvComparisonGroupSizesObservationV1(
        observation_version="slice-b-observation-v1",
        observation_type="csv-comparison-group-sizes-v1",
        verifier_id="slice-b-csv-group-size-verifier-v1",
        snapshot_digest=active_context.snapshot_digest,
        file_record_ref_digest=file_ref_digest,
        content_digest=content_digest,
        selected_file_ordinal=1,
        review_scope_selection_evidence_digest=active_scope,
        comparison_column_index=1,
        sorted_group_sizes=sizes,
        observation_id=_canonical_digest(group_fields),
        finding_eligible=False,
    )
    repeated = sum(count > 1 for count in candidate_counts.values())
    cross = sum(len(values) > 1 for values in associations.values())
    histogram_value = tuple(sorted(histogram.items()))
    incidence_fields = {
        **common,
        "observation_type": "csv-unit-comparison-incidence-v1",
        "verifier_id": "slice-b-csv-incidence-verifier-v1",
        "candidate_unit_column_index": 0,
        "comparison_column_index": 1,
        "repeated_candidate_value_count": repeated,
        "cross_comparison_candidate_value_count": cross,
        "comparison_values_per_candidate_histogram": histogram_value,
    }
    incidence = CsvUnitComparisonIncidenceObservationV1(
        observation_version="slice-b-observation-v1",
        observation_type="csv-unit-comparison-incidence-v1",
        verifier_id="slice-b-csv-incidence-verifier-v1",
        snapshot_digest=active_context.snapshot_digest,
        file_record_ref_digest=file_ref_digest,
        content_digest=content_digest,
        selected_file_ordinal=1,
        review_scope_selection_evidence_digest=active_scope,
        candidate_unit_column_index=0,
        comparison_column_index=1,
        repeated_candidate_value_count=repeated,
        cross_comparison_candidate_value_count=cross,
        comparison_values_per_candidate_histogram=histogram_value,
        observation_id=_canonical_digest(incidence_fields),
        finding_eligible=False,
    )
    return shape, cardinality, group, incidence


def _compose(
    fixture: _Fixture,
    observations: object | None = None,
    *,
    context: ManifestBoundFrozenInspectionContext | None = None,
) -> SliceBCompositionResultV1:
    active_context = fixture.context if context is None else context
    primary = _oracle_observations(fixture) if observations is None else observations
    return compose_slice_b_question_v1(
        context=active_context,
        selected_path=fixture.selected_path,
        candidate_unit_column_index=0,
        comparison_column_index=1,
        primary_observations=primary,
    )


def _forge_dataclass(value: _T, **changes: object) -> _T:
    forged = object.__new__(type(value))
    field_names = cast(dict[str, object], type(value).__dict__["__dataclass_fields__"])
    for name in field_names:
        object.__setattr__(
            forged,
            name,
            changes.get(name, getattr(value, name)),
        )
    return forged


def _replace_base_record(
    context: ManifestBoundFrozenInspectionContext,
    old: FrozenBaseRecord,
    new: FrozenBaseRecord,
) -> ManifestBoundFrozenInspectionContext:
    return _forge_dataclass(
        context,
        base_records=tuple(new if record is old else record for record in context.base_records),
    )


def _snapshot_payload(fixture: _Fixture) -> dict[str, Any]:
    value = json.loads(fixture.snapshot_record.canonical_payload)
    assert isinstance(value, dict)
    return value


def _mutated_scope_context(
    fixture: _Fixture,
    mutate: Any,
) -> ManifestBoundFrozenInspectionContext:
    payload = _snapshot_payload(fixture)
    mutate(payload)
    replacement = FrozenBaseRecord.from_record(fixture.snapshot_record.ref, payload)
    return _replace_base_record(fixture.context, fixture.snapshot_record, replacement)


def _rebind_unrelated_manifest_record(
    fixture: _Fixture,
    *,
    field: str,
    value: object,
) -> tuple[ManifestBoundFrozenInspectionContext, SliceBObservationSetV1]:
    unrelated = next(
        record
        for record in fixture.context.base_records
        if record.ref.record_type == "file_record"
        and json.loads(record.canonical_payload).get("path") == "support/nested"
    )
    payload = json.loads(unrelated.canonical_payload)
    assert isinstance(payload, dict)
    payload[field] = value
    replacement = FrozenBaseRecord.from_record(unrelated.ref, payload)
    manifest = fixture.context.file_manifest_input
    assert manifest is not None
    manifest_lines = [
        replacement.canonical_payload if line == unrelated.canonical_payload else line
        for line in manifest.canonical_jsonl_bytes[:-1].split(b"\n")
    ]
    manifest_bytes = b"\n".join(manifest_lines) + b"\n"
    rebound_manifest = FrozenFileManifestInput(
        file_manifest_ref=manifest.file_manifest_ref,
        canonical_jsonl_bytes=manifest_bytes,
        manifest_digest=sha256_digest(manifest_bytes),
    )
    context = _forge_dataclass(
        _replace_base_record(fixture.context, unrelated, replacement),
        file_manifest_input=rebound_manifest,
    )
    scope_digest = _oracle_scope_digest(
        snapshot_record=fixture.snapshot_record,
        manifest=rebound_manifest,
        selected_path=fixture.selected_path,
        selected_file_record=fixture.selected_file_record,
        selected_identity_record=fixture.selected_identity_record,
        content=fixture.content,
    )
    return context, _oracle_observations(
        fixture,
        context=context,
        scope_digest=scope_digest,
    )


def _assert_rederivation_mismatch(result: SliceBCompositionResultV1) -> None:
    assert result.disposition is SliceBCompositionDispositionV1.OBSERVATION_REDERIVATION_MISMATCH
    assert result.observations is None
    assert result.question is None
    assert result.primary_refusal is SliceBPrimaryRefusalReasonV1.OBSERVATION_REDERIVATION_MISMATCH
    assert result.question_scope_unresolved is False


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("entry_kind", "alien"),
        ("entry_kind", "fifo"),
        ("path", "support/\x00nested"),
        ("path", "support/\x1fnested"),
        ("path", "support/\x7fnested"),
        (
            "asset_identity_ref",
            {
                "record_type": "asset_identity",
                "record_id": "asset identity with spaces",
            },
        ),
        (
            "asset_identity_ref",
            {"record_type": "asset_identity", "record_id": "asset\tidentity"},
        ),
    ),
    ids=(
        "reviewer-alien-entry-kind",
        "adjacent-unknown-entry-kind",
        "reviewer-nul-path",
        "adjacent-c0-path",
        "adjacent-del-path",
        "reviewer-whitespace-identity-reference",
        "adjacent-tab-identity-reference",
    ),
)
def test_composition_manifest_envelope_parity_refuses_without_report_authority(
    field: str,
    value: object,
) -> None:
    fixture = _fixture()
    context, observations = _rebind_unrelated_manifest_record(
        fixture,
        field=field,
        value=value,
    )

    result = _compose(fixture, observations, context=context)
    _assert_rederivation_mismatch(result)
    report = render_slice_b_component_v1(
        snapshot_digest=context.snapshot_digest,
        primary_refusal=result.primary_refusal,
        observations=result.observations,
        question=result.question,
        question_scope_unresolved=result.question_scope_unresolved,
    )
    assert b"Input CSV bytes: UNVERIFIED\n" in report
    assert b"## Material questions\nNone.\n" in report
    assert b"## Observation appendix\nNone.\n" in report
    assert report.count(b"slice-b-observation-rederivation-mismatch") == 1
    assert b"MATERIAL QUESTION. Question" not in report
    assert b"VERIFIED OBSERVATION" not in report

    transaction_report = render_slice_b_report_v1(
        context,
        CsvQuestionRequestV1(
            selected_path=fixture.selected_path,
            candidate_unit_column_index=0,
            comparison_column_index=1,
        ),
    )
    assert transaction_report.count(b"slice-b-manifest-bijection-invalid") == 1
    assert b"MATERIAL QUESTION. Question" not in transaction_report
    assert b"VERIFIED OBSERVATION" not in transaction_report


def test_duplicate_selected_identity_association_refuses_independent_composition() -> None:
    fixture = _fixture()
    context, observations = _rebind_unrelated_manifest_record(
        fixture,
        field="asset_identity_ref",
        value=fixture.selected_identity_record.ref.to_dict(),
    )

    _assert_rederivation_mismatch(_compose(fixture, observations, context=context))


def test_composition_emits_exact_renderer_types_and_no_raw_prose() -> None:
    fixture = _fixture()
    observations = _oracle_observations(fixture)
    result = _compose(fixture, observations)

    assert result.disposition is SliceBCompositionDispositionV1.QUESTION
    assert result.observations is not observations
    assert tuple(type(item) for item in result.observations or ()) == (
        CsvTableShapeObservationV1,
        CsvSelectedCardinalitiesObservationV1,
        CsvComparisonGroupSizesObservationV1,
        CsvUnitComparisonIncidenceObservationV1,
    )
    assert type(result.question) is SliceBQuestionRenderIRV1
    assert result.question is not None
    assert result.question.basis_observation_ids == tuple(
        item.observation_id for item in cast(SliceBObservationSetV1, result.observations)
    )
    assert result.question.review_scope_selection_evidence_digest == fixture.scope_digest
    assert result.question.finding_eligible is False

    report = render_slice_b_component_v1(
        snapshot_digest=fixture.context.snapshot_digest,
        primary_refusal=result.primary_refusal,
        observations=result.observations,
        question=result.question,
        question_scope_unresolved=result.question_scope_unresolved,
    )
    assert b"- Evidence grade: MATERIAL QUESTION." in report
    for raw_value in (
        fixture.selected_path.encode("ascii"),
        b"HEADER_ALPHA",
        b"HEADER_BETA",
        b"RAW_CELL_ONE",
        b"ARM_A",
    ):
        assert raw_value not in report


def test_composition_is_deterministic_and_answers_cannot_feed_renderer() -> None:
    fixture = _fixture()
    observations = _oracle_observations(fixture)
    first = _compose(fixture, observations)
    second = _compose(fixture, observations)
    assert first == second
    assert first.question is not second.question
    assert inspect.signature(compose_slice_b_question_v1).parameters.keys() == {
        "context",
        "selected_path",
        "candidate_unit_column_index",
        "comparison_column_index",
        "primary_observations",
    }
    before = render_slice_b_component_v1(
        snapshot_digest=fixture.context.snapshot_digest,
        primary_refusal=first.primary_refusal,
        observations=first.observations,
        question=first.question,
        question_scope_unresolved=first.question_scope_unresolved,
    )
    for answers in (
        ("no", "yes", "unknown", "yes"),
        ("unknown", "no", "not-applicable", "not-applicable"),
        ("yes", "yes", "yes", "no"),
    ):
        resolve_slice_b_answer_tree_v1(answers)
    after = render_slice_b_component_v1(
        snapshot_digest=fixture.context.snapshot_digest,
        primary_refusal=first.primary_refusal,
        observations=first.observations,
        question=first.question,
        question_scope_unresolved=first.question_scope_unresolved,
    )
    assert before == after


def test_scope_graph_and_selected_surface_values_are_ignored() -> None:
    fixture = _fixture()
    observations = _oracle_observations(fixture)
    baseline = _compose(fixture, observations)
    surfaces = [
        record.ref
        for record in fixture.context.base_records
        if record.ref.record_type == "publication_surface"
    ]
    assert len(surfaces) == 2
    for graph_value in (None, object(), {"forged": "graph"}, ("unrelated",)):
        attacked = _forge_dataclass(
            fixture.context,
            selected_surface_ref=surfaces[1],
            scope_join_graph=graph_value,
        )
        result = _compose(fixture, observations, context=attacked)
        assert result == baseline


def test_production_shaped_old_scope_graph_is_ignored() -> None:
    from sc_referee.scientific_checks.core import (
        ScopeJoinEdge,
        ScopeJoinProof,
        StaticScopeJoinGraph,
    )

    fixture = _fixture()
    observations = _oracle_observations(fixture)
    surface_record = next(
        record
        for record in fixture.context.base_records
        if record.ref == fixture.context.selected_surface_ref
    )
    proof = ScopeJoinProof.create(
        edge=ScopeJoinEdge(
            source_ref=fixture.selected_file_record.ref,
            relation="selected_material_input_for_review",
            target_ref=fixture.context.selected_surface_ref,
        ),
        profile="selected-material-input-for-review",
        evidence_refs=(
            fixture.selected_file_record.ref,
            fixture.selected_identity_record.ref,
            fixture.context.selected_surface_ref,
        ),
        evidence_payload_digests=(
            fixture.selected_file_record.payload_digest,
            fixture.selected_identity_record.payload_digest,
            surface_record.payload_digest,
            sha256_digest(b"opaque-unretained-projection"),
        ),
        snapshot_digest=fixture.context.snapshot_digest,
        authority_limitations=(
            "Review selection does not establish execution, lineage, scientific intent, materiality, or correctness.",
        ),
    )
    graph = StaticScopeJoinGraph(
        snapshot_digest=fixture.context.snapshot_digest,
        proofs=(proof,),
    )
    attacked = _forge_dataclass(fixture.context, scope_join_graph=graph)
    assert _compose(fixture, observations, context=attacked) == _compose(fixture, observations)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.pop("extensions"),
        lambda payload: payload.__setitem__("extensions", []),
        lambda payload: cast(dict[str, Any], payload["extensions"]).pop(
            "x-material-full-digest-paths"
        ),
        lambda payload: cast(dict[str, Any], payload["extensions"]).__setitem__(
            "x-material-full-digest-paths", [_SELECTED_PATH, _SELECTED_PATH]
        ),
        lambda payload: cast(dict[str, Any], payload["extensions"]).__setitem__(
            "x-material-full-digest-paths", ["support/other.csv", _SELECTED_PATH]
        ),
        lambda payload: cast(dict[str, Any], payload["extensions"]).__setitem__(
            "x-material-full-digest-paths", [_SELECTED_PATH, "extra/missing.csv"]
        ),
        lambda payload: cast(dict[str, Any], payload["extensions"]).pop(
            "x-material-input-identities"
        ),
        lambda payload: cast(dict[str, Any], payload["extensions"]).__setitem__(
            "x-material-input-identities",
            [
                {"path": _SELECTED_PATH, "tier": "sampled_digest"},
                {"path": "support/other.csv", "tier": "full_digest"},
            ],
        ),
        lambda payload: cast(dict[str, Any], payload["extensions"]).__setitem__(
            "x-material-input-identities",
            [
                {"path": _SELECTED_PATH, "tier": "full_digest", "extra": True},
                {"path": "support/other.csv", "tier": "full_digest"},
            ],
        ),
    ],
    ids=(
        "missing-extensions",
        "malformed-extensions",
        "missing-path-list",
        "duplicate-path",
        "reordered-paths",
        "cross-file-path",
        "missing-identity-list",
        "tier-mismatch",
        "identity-extra-key",
    ),
)
def test_scope_preimage_attacks_preserve_observations_and_select_secondary_coverage(
    mutate: Any,
) -> None:
    fixture = _fixture()
    attacked = _mutated_scope_context(fixture, mutate)
    observations = _oracle_observations(
        fixture,
        context=attacked,
        scope_digest="unresolved",
    )
    result = _compose(fixture, observations, context=attacked)
    assert result.disposition is SliceBCompositionDispositionV1.QUESTION_SCOPE_UNRESOLVED
    assert result.observations == observations
    assert result.question is None
    assert result.primary_refusal is None
    assert result.question_scope_unresolved is True
    report = render_slice_b_component_v1(
        snapshot_digest=attacked.snapshot_digest,
        primary_refusal=result.primary_refusal,
        observations=result.observations,
        question=result.question,
        question_scope_unresolved=result.question_scope_unresolved,
    )
    assert report.count(b"slice-b-question-scope-unresolved") == 1
    assert report.count(b"VERIFIED OBSERVATION") == 4
    assert b"MATERIAL QUESTION. Question" not in report


def test_selected_material_input_subclass_cannot_feed_rederivation() -> None:
    fixture = _fixture()

    class MaterialSubclass(FrozenMaterialInput):
        pass

    original = fixture.context.material_inputs[0]
    subclassed = MaterialSubclass(
        path=original.path,
        file_ref=original.file_ref,
        asset_identity_ref=original.asset_identity_ref,
        content=original.content,
        content_digest=original.content_digest,
    )
    materials = (subclassed, *fixture.context.material_inputs[1:])
    attacked = _forge_dataclass(fixture.context, material_inputs=materials)
    observations = _oracle_observations(fixture)
    _assert_rederivation_mismatch(_compose(fixture, observations, context=attacked))


def test_scope_digest_uses_exact_manifest_bytes_not_line_order_cache() -> None:
    fixture = _fixture()
    manifest = fixture.context.file_manifest_input
    assert manifest is not None
    lines = manifest.canonical_jsonl_bytes[:-1].split(b"\n")
    reordered_bytes = b"\n".join(reversed(lines)) + b"\n"
    reordered_manifest = FrozenFileManifestInput(
        file_manifest_ref=manifest.file_manifest_ref,
        canonical_jsonl_bytes=reordered_bytes,
        manifest_digest=sha256_digest(reordered_bytes),
    )
    attacked = _forge_dataclass(fixture.context, file_manifest_input=reordered_manifest)
    scope_digest = _oracle_scope_digest(
        snapshot_record=fixture.snapshot_record,
        manifest=reordered_manifest,
        selected_path=fixture.selected_path,
        selected_file_record=fixture.selected_file_record,
        selected_identity_record=fixture.selected_identity_record,
        content=fixture.content,
    )
    observations = _oracle_observations(fixture, context=attacked, scope_digest=scope_digest)
    result = _compose(fixture, observations, context=attacked)
    assert result.disposition is SliceBCompositionDispositionV1.QUESTION
    assert result.question is not None
    assert result.question.review_scope_selection_evidence_digest == scope_digest
    assert scope_digest != fixture.scope_digest


@pytest.mark.parametrize(
    "attack",
    (
        "manifest-missing-line",
        "manifest-duplicate-line",
        "manifest-malformed",
        "manifest-stale-digest",
        "unrelated-record-omission",
        "snapshot-stale-payload-digest",
        "snapshot-noncanonical",
        "selected-nonregular",
        "cross-snapshot",
        "cross-file-material",
        "cross-identity-material",
        "selected-path-mismatch",
    ),
)
def test_manifest_material_and_snapshot_attacks_refuse_rederivation(attack: str) -> None:
    fixture = _fixture()
    context = fixture.context
    manifest = context.file_manifest_input
    assert manifest is not None
    observations = _oracle_observations(fixture)

    if attack.startswith("manifest") or attack == "unrelated-record-omission":
        lines = manifest.canonical_jsonl_bytes[:-1].split(b"\n")
        if attack in {"manifest-missing-line", "unrelated-record-omission"}:
            attacked_bytes = b"\n".join(lines[:-1]) + b"\n"
            attacked_digest = sha256_digest(attacked_bytes)
        elif attack == "manifest-duplicate-line":
            attacked_bytes = manifest.canonical_jsonl_bytes + lines[0] + b"\n"
            attacked_digest = sha256_digest(attacked_bytes)
        elif attack == "manifest-malformed":
            attacked_bytes = b'{"not":"canonical", "space":true}\n'
            attacked_digest = sha256_digest(attacked_bytes)
        else:
            attacked_bytes = manifest.canonical_jsonl_bytes + b" "
            attacked_digest = manifest.manifest_digest
        attacked_manifest = _forge_dataclass(
            manifest,
            canonical_jsonl_bytes=attacked_bytes,
            manifest_digest=attacked_digest,
        )
        context = _forge_dataclass(context, file_manifest_input=attacked_manifest)
    elif attack == "snapshot-stale-payload-digest":
        payload = _snapshot_payload(fixture)
        payload["immutability"] = False
        stale = _forge_dataclass(
            fixture.snapshot_record,
            canonical_payload=canonical_json(payload).encode("utf-8"),
        )
        context = _replace_base_record(context, fixture.snapshot_record, stale)
    elif attack == "snapshot-noncanonical":
        noncanonical = _forge_dataclass(
            fixture.snapshot_record,
            canonical_payload=fixture.snapshot_record.canonical_payload + b" ",
            payload_digest=sha256_digest(fixture.snapshot_record.canonical_payload + b" "),
        )
        context = _replace_base_record(context, fixture.snapshot_record, noncanonical)
    elif attack in {"selected-nonregular", "cross-snapshot"}:
        payload = json.loads(fixture.selected_file_record.canonical_payload)
        assert isinstance(payload, dict)
        if attack == "selected-nonregular":
            payload["entry_kind"] = "symlink"
        else:
            payload["snapshot_ref"] = {
                "record_type": "repository_snapshot",
                "record_id": "snapshot:other",
            }
        replacement = FrozenBaseRecord.from_record(fixture.selected_file_record.ref, payload)
        context = _replace_base_record(context, fixture.selected_file_record, replacement)
        manifest_lines = [
            replacement.canonical_payload
            if line == fixture.selected_file_record.canonical_payload
            else line
            for line in manifest.canonical_jsonl_bytes[:-1].split(b"\n")
        ]
        attacked_bytes = b"\n".join(manifest_lines) + b"\n"
        context = _forge_dataclass(
            context,
            file_manifest_input=FrozenFileManifestInput(
                manifest.file_manifest_ref,
                attacked_bytes,
                sha256_digest(attacked_bytes),
            ),
        )
    elif attack in {"cross-file-material", "cross-identity-material"}:
        selected_material = next(
            item for item in context.material_inputs if item.path == fixture.selected_path
        )
        other_material = next(
            item for item in context.material_inputs if item is not selected_material
        )
        changes = (
            {"file_ref": other_material.file_ref}
            if attack == "cross-file-material"
            else {"asset_identity_ref": other_material.asset_identity_ref}
        )
        forged_material = _forge_dataclass(selected_material, **changes)
        context = _forge_dataclass(
            context,
            material_inputs=tuple(
                forged_material if item is selected_material else item
                for item in context.material_inputs
            ),
        )
    else:
        result = compose_slice_b_question_v1(
            context=context,
            selected_path="inputs/missing.csv",
            candidate_unit_column_index=0,
            comparison_column_index=1,
            primary_observations=observations,
        )
        _assert_rederivation_mismatch(result)
        return

    _assert_rederivation_mismatch(_compose(fixture, observations, context=context))


def test_live_file_a_to_b_to_a_cannot_change_frozen_composition(tmp_path: Path) -> None:
    fixture = _fixture()
    observations = _oracle_observations(fixture)
    live = tmp_path / "selected.csv"
    live.write_bytes(b"attacker,replacement\nB,B\n")
    first = _compose(fixture, observations)
    live.write_bytes(fixture.content)
    second = _compose(fixture, observations)
    assert first == second
    assert first.question is not None


@pytest.mark.parametrize(
    "content",
    (
        b"",
        b"u,g\na,b",
        b"u,g\na,b\ntrailing",
        b"u,g\na,b\n\n",
        b"u,g\r\na,b\r\n",
        b"u,g\na,\tb\n",
        b"u,g\na,\x00b\n",
        b"u,g\na,\x7fb\n",
        b"\xef\xbb\xbfu,g\na,b\n",
        b'u,g\n"a",b\n',
        b"u,g\na,\n",
        b"u,u\na,b\n",
        b"u,g\na,b,c\n",
        b"only\na\n",
        b"u,g\n",
        b",".join(f"h{index}".encode("ascii") for index in range(65))
        + b"\n"
        + b",".join(b"x" for _ in range(65))
        + b"\n",
        b"u,g\n" + b"x" * 257 + b",b\n",
        b"u,g\n" + b"a,b\n" * 100_001,
        b"u,g\n" + b"a,b\n" * 300_000,
    ),
    ids=(
        "empty",
        "missing-terminal-lf",
        "extra-trailing-bytes",
        "blank-row",
        "crlf",
        "tab",
        "nul",
        "del",
        "bom",
        "quote",
        "empty-field",
        "duplicate-header",
        "ragged",
        "one-column",
        "zero-row",
        "sixty-five-columns",
        "field-over-256",
        "row-budget",
        "byte-budget",
    ),
)
def test_default_deny_csv_language_never_accepts_forged_primary_observations(
    content: bytes,
) -> None:
    attacked = _fixture(content, suffix=hashlib.sha256(content).hexdigest()[:12])
    foreign = _fixture(suffix="valid-primary")
    _assert_rederivation_mismatch(_compose(attacked, _oracle_observations(foreign)))


def test_in_range_request_column_outside_verified_width_refuses_rederivation() -> None:
    fixture = _fixture()
    result = compose_slice_b_question_v1(
        context=fixture.context,
        selected_path=fixture.selected_path,
        candidate_unit_column_index=0,
        comparison_column_index=63,
        primary_observations=_oracle_observations(fixture),
    )
    _assert_rederivation_mismatch(result)


def test_observation_singles_pairs_triples_and_all_reordering_refuse() -> None:
    fixture = _fixture()
    alternate = _fixture(
        _MATERIAL_CSV.replace(b"RAW_CELL_TWO", b"RAW_CELL_ALT"), suffix="alternate"
    )
    primary = _oracle_observations(fixture)
    foreign = _oracle_observations(alternate)
    for width in (1, 2, 3):
        for indices in itertools.combinations(range(4), width):
            mixed = tuple(
                foreign[index] if index in indices else primary[index] for index in range(4)
            )
            _assert_rederivation_mismatch(_compose(fixture, mixed))
    _assert_rederivation_mismatch(_compose(fixture, foreign))

    for ordering in itertools.permutations(range(4)):
        reordered = tuple(primary[index] for index in ordering)
        result = _compose(fixture, reordered)
        if ordering == (0, 1, 2, 3):
            assert result.disposition is SliceBCompositionDispositionV1.QUESTION
        else:
            _assert_rederivation_mismatch(result)


def test_observation_forgery_duplicate_missing_extra_and_mutable_aliases_refuse() -> None:
    fixture = _fixture()
    primary = _oracle_observations(fixture)
    forged_id = replace(primary[0], observation_id=sha256_digest(b"forged"))
    _assert_rederivation_mismatch(_compose(fixture, (forged_id, *primary[1:])))
    _assert_rederivation_mismatch(_compose(fixture, primary[:3]))
    _assert_rederivation_mismatch(_compose(fixture, (*primary, primary[3])))
    _assert_rederivation_mismatch(_compose(fixture, [*primary]))
    _assert_rederivation_mismatch(
        _compose(fixture, (primary[0], primary[0], primary[2], primary[3]))
    )

    mutable_sizes = _forge_dataclass(primary[2], sorted_group_sizes=[2, 2])
    _assert_rederivation_mismatch(
        _compose(fixture, (primary[0], primary[1], mutable_sizes, primary[3]))
    )
    missing_field = object.__new__(CsvTableShapeObservationV1)
    _assert_rederivation_mismatch(_compose(fixture, (missing_field, *primary[1:])))

    class ShapeSubclass(CsvTableShapeObservationV1):
        pass

    subclass = ShapeSubclass(**asdict(primary[0]))
    _assert_rederivation_mismatch(_compose(fixture, (subclass, *primary[1:])))

    bool_row_count = _forge_dataclass(primary[0], data_row_count=True)
    bool_cardinality = _forge_dataclass(primary[1], candidate_unit_distinct_count=True)
    bool_group = _forge_dataclass(primary[2], sorted_group_sizes=(True, 2))
    bool_histogram = _forge_dataclass(
        primary[3], comparison_values_per_candidate_histogram=((2, True),)
    )
    for forged, index in (
        (bool_row_count, 0),
        (bool_cardinality, 1),
        (bool_group, 2),
        (bool_histogram, 3),
    ):
        attacked = tuple(
            forged if item_index == index else item for item_index, item in enumerate(primary)
        )
        _assert_rederivation_mismatch(_compose(fixture, attacked))


@pytest.mark.parametrize(
    ("content", "expected"),
    (
        (b"u,g\nu1,A\n", SliceBCompositionDispositionV1.NO_QUESTION),
        (b"u,g\nu1,A\nu2,B\n", SliceBCompositionDispositionV1.NO_QUESTION),
        (b"u,g\nu1,A\nu1,A\n", SliceBCompositionDispositionV1.NO_QUESTION),
        (b"u,g\nu1,A\nu1,A\nu2,B\n", SliceBCompositionDispositionV1.NO_QUESTION),
        (b"u,g\nu1,A\nu1,B\n", SliceBCompositionDispositionV1.QUESTION),
    ),
)
def test_question_predicate_boundaries(content: bytes, expected: object) -> None:
    fixture = _fixture(content, suffix=hashlib.sha256(content).hexdigest()[:8])
    result = _compose(fixture, _oracle_observations(fixture))
    assert result.disposition is expected
    assert (result.question is not None) is (expected is SliceBCompositionDispositionV1.QUESTION)
    assert result.question_scope_unresolved is False


def test_false_predicate_and_primary_mismatch_render_exact_coverage_states() -> None:
    no_question_fixture = _fixture(b"u,g\nu1,A\nu2,B\n", suffix="no-question-render")
    no_question = _compose(no_question_fixture, _oracle_observations(no_question_fixture))
    no_question_report = render_slice_b_component_v1(
        snapshot_digest=no_question_fixture.context.snapshot_digest,
        primary_refusal=no_question.primary_refusal,
        observations=no_question.observations,
        question=no_question.question,
        question_scope_unresolved=no_question.question_scope_unresolved,
    )
    assert b"## Material questions\nNone.\n" in no_question_report
    assert b"slice-b-question-scope-unresolved" not in no_question_report
    assert no_question_report.count(b"VERIFIED OBSERVATION") == 4

    fixture = _fixture()
    primary = _oracle_observations(fixture)
    forged = (replace(primary[0], data_row_count=3), *primary[1:])
    mismatch = _compose(fixture, forged)
    mismatch_report = render_slice_b_component_v1(
        snapshot_digest=fixture.context.snapshot_digest,
        primary_refusal=mismatch.primary_refusal,
        observations=mismatch.observations,
        question=mismatch.question,
        question_scope_unresolved=mismatch.question_scope_unresolved,
    )
    assert b"Input CSV bytes: UNVERIFIED" in mismatch_report
    assert mismatch_report.count(b"slice-b-observation-rederivation-mismatch") == 1
    assert b"## Observation appendix\nNone.\n" in mismatch_report


def test_defined_aggregate_counterexample_changes_only_identity_payloads() -> None:
    first = _fixture(
        b"candidate,comparison\na,x\na,x\na,x\na,x\nb,x\nb,x\n",
        suffix="four-two",
    )
    second = _fixture(
        b"candidate,comparison\na,x\na,x\na,x\nb,x\nb,x\nb,x\n",
        suffix="three-three",
    )
    first_result = _compose(first, _oracle_observations(first))
    second_result = _compose(second, _oracle_observations(second))
    assert first_result.disposition is SliceBCompositionDispositionV1.NO_QUESTION
    assert second_result.disposition is SliceBCompositionDispositionV1.NO_QUESTION
    first_observations = cast(SliceBObservationSetV1, first_result.observations)
    second_observations = cast(SliceBObservationSetV1, second_result.observations)
    assert (
        first_observations[0].data_row_count,
        first_observations[0].column_count,
        first_observations[1].candidate_unit_distinct_count,
        first_observations[1].comparison_distinct_count,
        first_observations[2].sorted_group_sizes,
        first_observations[3].repeated_candidate_value_count,
        first_observations[3].cross_comparison_candidate_value_count,
        first_observations[3].comparison_values_per_candidate_histogram,
    ) == (6, 2, 2, 1, (6,), 2, 0, ((1, 2),))
    assert tuple(_numeric_payload(item) for item in first_observations) == tuple(
        _numeric_payload(item) for item in second_observations
    )
    assert first_observations[0].content_digest != second_observations[0].content_digest
    assert tuple(item.observation_id for item in first_observations) != tuple(
        item.observation_id for item in second_observations
    )


def _numeric_payload(
    observation: CsvTableShapeObservationV1
    | CsvSelectedCardinalitiesObservationV1
    | CsvComparisonGroupSizesObservationV1
    | CsvUnitComparisonIncidenceObservationV1,
) -> tuple[object, ...]:
    ignored = {
        "observation_version",
        "observation_type",
        "verifier_id",
        "snapshot_digest",
        "file_record_ref_digest",
        "content_digest",
        "selected_file_ordinal",
        "review_scope_selection_evidence_digest",
        "observation_id",
        "finding_eligible",
    }
    return tuple(value for key, value in asdict(observation).items() if key not in ignored)


def test_row_permutation_and_bijective_renaming_preserve_numeric_facts_not_ids() -> None:
    permuted = (
        b"HEADER_ALPHA,HEADER_BETA,HEADER_GAMMA\n"
        b"RAW_CELL_TWO,ARM_B,4\n"
        b"RAW_CELL_ONE,ARM_A,1\n"
        b"RAW_CELL_TWO,ARM_A,3\n"
        b"RAW_CELL_ONE,ARM_B,2\n"
    )
    renamed = (
        b"RENAMED_ONE,RENAMED_TWO,RENAMED_THREE\n"
        b"VALUE_X,GROUP_X,1\n"
        b"VALUE_X,GROUP_Y,2\n"
        b"VALUE_Y,GROUP_X,3\n"
        b"VALUE_Y,GROUP_Y,4\n"
    )
    results = []
    for index, content in enumerate((_MATERIAL_CSV, permuted, renamed)):
        fixture = _fixture(content, suffix=f"equivalent-{index}")
        results.append(_compose(fixture, _oracle_observations(fixture)))
    numeric = [
        tuple(_numeric_payload(item) for item in cast(SliceBObservationSetV1, result.observations))
        for result in results
    ]
    assert numeric[0] == numeric[1] == numeric[2]
    ids = [
        tuple(item.observation_id for item in cast(SliceBObservationSetV1, result.observations))
        for result in results
    ]
    assert len(set(ids)) == 3


@pytest.mark.parametrize(
    "field",
    (
        "observation_id",
        "content_digest",
        "snapshot_digest",
        "file_record_ref_digest",
        "review_scope_selection_evidence_digest",
        "finding_eligible",
    ),
)
def test_every_common_observation_field_is_rederived(field: str) -> None:
    fixture = _fixture()
    primary = _oracle_observations(fixture)
    current = getattr(primary[0], field)
    if field == "finding_eligible":
        replacement: object = True
    else:
        replacement = sha256_digest(f"forged:{field}".encode("ascii"))
    assert replacement != current
    forged_shape = _forge_dataclass(primary[0], **{field: replacement})
    _assert_rederivation_mismatch(_compose(fixture, (forged_shape, *primary[1:])))


@pytest.mark.parametrize(
    ("selected_path", "candidate", "comparison"),
    (
        ("/absolute.csv", 0, 1),
        ("../escape.csv", 0, 1),
        (_SELECTED_PATH, True, 1),
        (_SELECTED_PATH, 0, False),
        (_SELECTED_PATH, 0, 0),
        (_SELECTED_PATH, -1, 1),
        (_SELECTED_PATH, 0, 64),
    ),
)
def test_request_contract_values_never_become_coverage(
    selected_path: str,
    candidate: object,
    comparison: object,
) -> None:
    fixture = _fixture()
    with pytest.raises(SliceBCompositionContractError):
        compose_slice_b_question_v1(
            context=fixture.context,
            selected_path=selected_path,
            candidate_unit_column_index=cast(int, candidate),
            comparison_column_index=cast(int, comparison),
            primary_observations=_oracle_observations(fixture),
        )


def test_answer_tree_exhaustive_256_legal_counts_and_disposition_conflicts() -> None:
    legal = []
    illegal = []
    eligible = []
    by_normalized: dict[tuple[str, ...], set[SliceBAnswerDispositionV1]] = defaultdict(set)
    counts: Counter[SliceBAnswerDispositionV1] = Counter()
    for raw in itertools.product(_ANSWER_TOKENS, repeat=4):
        if raw[0] != "not-applicable":
            eligible.append(raw)
        try:
            resolved = resolve_slice_b_answer_tree_v1(raw)
        except SliceBAnswerTreeContractError:
            illegal.append(raw)
            continue
        legal.append(raw)
        counts[resolved.disposition] += 1
        by_normalized[resolved.normalized_answers].add(resolved.disposition)

    assert len(tuple(itertools.product(_ANSWER_TOKENS, repeat=4))) == 256
    assert len(eligible) == 192
    assert len(legal) == 136
    assert len([raw for raw in illegal if raw[0] != "not-applicable"]) == 56
    assert len([raw for raw in illegal if raw[0] == "not-applicable"]) == 64
    assert counts == {
        SliceBAnswerDispositionV1.RESOLVED_INAPPLICABLE: 112,
        SliceBAnswerDispositionV1.RETAINS_MATERIAL_QUESTION: 22,
        SliceBAnswerDispositionV1.RESOLVED_DEPENDENCE_ACCOUNTED: 1,
        SliceBAnswerDispositionV1.REQUIRES_FURTHER_EVIDENCE: 1,
    }
    assert len(by_normalized) == 31
    assert sum(len(dispositions) > 1 for dispositions in by_normalized.values()) == 0


def test_answer_tree_first_no_siblings_and_counterexample() -> None:
    first_no_counts: Counter[int] = Counter()
    for raw in itertools.product(_ANSWER_TOKENS, repeat=4):
        try:
            resolved = resolve_slice_b_answer_tree_v1(raw)
        except SliceBAnswerTreeContractError:
            continue
        first_no = next((index for index in range(3) if raw[index] == "no"), None)
        if first_no is None:
            continue
        first_no_counts[first_no + 1] += 1
        assert resolved.normalized_answers[: first_no + 1] == raw[: first_no + 1]
        assert resolved.normalized_answers[first_no + 1 :] == ("not-applicable",) * (3 - first_no)
        assert resolved.disposition is SliceBAnswerDispositionV1.RESOLVED_INAPPLICABLE
    assert first_no_counts == {1: 64, 2: 32, 3: 16}

    counterexample = ("unknown", "no", "not-applicable", "not-applicable")
    resolved = resolve_slice_b_answer_tree_v1(counterexample)
    assert resolved.normalized_answers == counterexample
    assert resolved.disposition is SliceBAnswerDispositionV1.RESOLVED_INAPPLICABLE


def test_exact_73_row_fixture_is_independently_reconstructed() -> None:
    rows: list[dict[str, object]] = []
    for raw in itertools.product(_ANSWER_TOKENS, repeat=4):
        literal_legal = raw[0] != "not-applicable" and all(
            answer != "not-applicable" or "no" in raw[:index] for index, answer in enumerate(raw)
        )
        historical_conflict = "no" in raw[:3] and "unknown" in raw
        if not literal_legal or not historical_conflict:
            continue
        first_no = next(index for index in range(3) if raw[index] == "no")
        normalized = raw[: first_no + 1] + ("not-applicable",) * (3 - first_no)
        rows.append(
            {
                "row_index": len(rows) + 1,
                "raw_answers": list(raw),
                "normalized_answers": list(normalized),
                "expected_disposition": "resolved-inapplicable",
            }
        )
        implementation = resolve_slice_b_answer_tree_v1(raw)
        assert list(implementation.normalized_answers) == list(normalized)
        assert implementation.disposition.value == "resolved-inapplicable"

    fixture_value = {
        "fixture_schema": "slice-b-answer-tree-point-fix-fixture-v1",
        "rows": rows,
    }
    fixture_bytes = (
        json.dumps(
            fixture_value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    assert len(rows) == 73
    assert [row["row_index"] for row in rows] == list(range(1, 74))
    assert len({tuple(cast(list[str], row["raw_answers"])) for row in rows}) == 73
    assert len(fixture_bytes) == 13_677
    assert hashlib.sha256(fixture_bytes).hexdigest() == (
        "29453a87fbdf6869f198358bf5d6295ab34fab160109848e682a16c5e3c70e77"
    )
    assert rows[68] == {
        "row_index": 69,
        "raw_answers": ["unknown", "no", "not-applicable", "not-applicable"],
        "normalized_answers": [
            "unknown",
            "no",
            "not-applicable",
            "not-applicable",
        ],
        "expected_disposition": "resolved-inapplicable",
    }


@pytest.mark.parametrize(
    ("raw", "normalized", "disposition"),
    (
        (
            ("unknown", "yes", "no", "yes"),
            ("unknown", "yes", "no", "not-applicable"),
            SliceBAnswerDispositionV1.RESOLVED_INAPPLICABLE,
        ),
        (
            ("unknown", "yes", "yes", "yes"),
            ("unknown", "yes", "yes", "yes"),
            SliceBAnswerDispositionV1.RETAINS_MATERIAL_QUESTION,
        ),
        (
            ("yes", "yes", "yes", "yes"),
            ("yes", "yes", "yes", "yes"),
            SliceBAnswerDispositionV1.RESOLVED_DEPENDENCE_ACCOUNTED,
        ),
        (
            ("yes", "yes", "yes", "no"),
            ("yes", "yes", "yes", "no"),
            SliceBAnswerDispositionV1.REQUIRES_FURTHER_EVIDENCE,
        ),
        (
            ("yes", "yes", "yes", "unknown"),
            ("yes", "yes", "yes", "unknown"),
            SliceBAnswerDispositionV1.RETAINS_MATERIAL_QUESTION,
        ),
    ),
)
def test_answer_tree_applicability_and_dependence_worlds(
    raw: tuple[str, str, str, str],
    normalized: tuple[str, str, str, str],
    disposition: SliceBAnswerDispositionV1,
) -> None:
    result = resolve_slice_b_answer_tree_v1(raw)
    assert result.normalized_answers == normalized
    assert result.disposition is disposition


@pytest.mark.parametrize(
    "raw",
    (
        ["yes", "yes", "yes", "yes"],
        ("not-applicable", "yes", "yes", "yes"),
        ("yes", "not-applicable", "yes", "yes"),
        ("unknown", "yes", "not-applicable", "yes"),
        ("yes", "yes", "yes", "not-applicable"),
        ("yes", "yes", "bogus", "yes"),
        ("yes", "yes", "yes"),
    ),
)
def test_answer_tree_illegal_forms_raise_typed_error(raw: object) -> None:
    with pytest.raises(SliceBAnswerTreeContractError):
        resolve_slice_b_answer_tree_v1(raw)


def test_answer_resolution_value_rejects_forged_normalized_dispositions() -> None:
    with pytest.raises(SliceBAnswerTreeContractError):
        SliceBAnswerTreeResolutionV1(
            normalized_answers=("unknown", "no", "yes", "not-applicable"),
            disposition=SliceBAnswerDispositionV1.RESOLVED_INAPPLICABLE,
        )
    with pytest.raises(SliceBAnswerTreeContractError):
        SliceBAnswerTreeResolutionV1(
            normalized_answers=("yes", "yes", "yes", "yes"),
            disposition=SliceBAnswerDispositionV1.RETAINS_MATERIAL_QUESTION,
        )
