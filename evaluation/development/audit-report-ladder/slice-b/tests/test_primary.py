from __future__ import annotations

import json
from dataclasses import dataclass, fields, replace
from typing import Any, TypeVar, cast

import pytest
from sc_referee_evaluation.audit_ladder.slice_b import (
    PRIMARY_REFUSAL_PRECEDENCE,
    CsvQuestionRequestV1,
    CsvTableShapeObservationV1,
    SliceBContractError,
    SliceBPrimaryObservationResult,
    SliceBPrimaryRefusal,
    canonical_observation_bytes,
    verify_csv_comparison_group_sizes_v1,
    verify_csv_selected_cardinalities_v1,
    verify_csv_table_shape_v1,
    verify_csv_unit_comparison_incidence_v1,
)
from sc_referee_evaluation.audit_ladder.slice_b import primary as primary_module

from sc_referee.controller import (
    FrozenFileManifestInput,
    ManifestBoundFrozenInspectionContext,
)
from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.scientific_checks.core import FrozenBaseRecord, FrozenMaterialInput, RecordRef

_CSV = b"candidate,comparison,value\nu1,A,1\nu1,B,2\nu2,A,3\nu2,B,4\n"
_SELECTED_PATH = "data/selected.csv"
_VERIFY = (
    verify_csv_table_shape_v1,
    verify_csv_selected_cardinalities_v1,
    verify_csv_comparison_group_sizes_v1,
    verify_csv_unit_comparison_incidence_v1,
)
_T = TypeVar("_T")


@dataclass(frozen=True)
class _Fixture:
    context: ManifestBoundFrozenInspectionContext
    request: CsvQuestionRequestV1


def _base(ref: RecordRef, payload: dict[str, Any]) -> FrozenBaseRecord:
    return FrozenBaseRecord.from_record(ref, payload)


def _fixture(
    content: bytes = _CSV,
    *,
    candidate_index: int = 0,
    comparison_index: int = 1,
    include_nonregular: bool = True,
) -> _Fixture:
    surface_ref = RecordRef("publication_surface", "surface:slice-b:test")
    artifact_ref = RecordRef("artifact", "artifact:slice-b:test")
    snapshot_ref = RecordRef("repository_snapshot", "snapshot:slice-b:test")
    inventory: list[tuple[str, str, bytes]] = [
        (_SELECTED_PATH, "regular_file", content),
        ("notes/readme.txt", "regular_file", b"context only\n"),
    ]
    if include_nonregular:
        inventory.extend(
            [
                ("empty-dir", "directory", b""),
                ("latest-data", "symlink", b"data/selected.csv"),
                ("device-node", "special", b""),
            ]
        )
    snapshot_digest = sha256_digest(
        canonical_json(
            [
                {
                    "path": path,
                    "entry_kind": entry_kind,
                    "byte_size": len(payload),
                    "digest": sha256_digest(payload),
                }
                for path, entry_kind, payload in inventory
            ]
        ).encode("utf-8")
    )
    snapshot_payload = {
        "schema_version": "0.19.0",
        "record_type": "repository_snapshot",
        "snapshot_id": snapshot_ref.record_id,
        "snapshot_digest": snapshot_digest,
        "immutability": True,
        "file_manifest_ref": "observed/files.jsonl",
        "included_roots": ["."],
        "extensions": {
            "x-material-full-digest-paths": [_SELECTED_PATH],
            "x-material-input-identities": [{"path": _SELECTED_PATH, "tier": "full_digest"}],
        },
    }
    records = [
        _base(surface_ref, {"publication_surface_id": surface_ref.record_id}),
        _base(artifact_ref, {"artifact_id": artifact_ref.record_id}),
        _base(snapshot_ref, snapshot_payload),
    ]
    selected_file_ref: RecordRef | None = None
    selected_identity_ref: RecordRef | None = None
    for index, (path, entry_kind, payload) in enumerate(sorted(inventory)):
        file_ref = RecordRef("file_record", f"file:slice-b:{index}")
        identity_ref = RecordRef("asset_identity", f"asset:slice-b:{index}")
        file_payload = {
            "schema_version": "0.19.0",
            "record_type": "file_record",
            "file_record_id": file_ref.record_id,
            "snapshot_ref": snapshot_ref.to_dict(),
            "path": path,
            "entry_kind": entry_kind,
            "byte_size": len(payload),
            "asset_identity_ref": identity_ref.to_dict(),
        }
        if entry_kind == "regular_file":
            identity_payload = {
                "schema_version": "0.19.0",
                "record_type": "asset_identity",
                "asset_identity_id": identity_ref.record_id,
                "asset_ref": file_ref.to_dict(),
                "tier": "full_digest",
                "identity_evidence": {
                    "kind": "full_digest",
                    "digest": sha256_digest(payload),
                },
            }
        else:
            identity_payload = {
                "schema_version": "0.19.0",
                "record_type": "asset_identity",
                "asset_identity_id": identity_ref.record_id,
                "asset_ref": file_ref.to_dict(),
                "tier": "unidentified",
                "identity_evidence": {"kind": "unidentified", "reason": entry_kind},
            }
        records.extend((_base(file_ref, file_payload), _base(identity_ref, identity_payload)))
        if path == _SELECTED_PATH:
            selected_file_ref = file_ref
            selected_identity_ref = identity_ref
    assert selected_file_ref is not None
    assert selected_identity_ref is not None
    manifest_bytes = _manifest_bytes(tuple(records), snapshot_ref.to_dict())
    context = ManifestBoundFrozenInspectionContext(
        snapshot_digest=snapshot_digest,
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(),
        base_records=tuple(records),
        material_inputs=(
            FrozenMaterialInput(
                path=_SELECTED_PATH,
                file_ref=selected_file_ref,
                asset_identity_ref=selected_identity_ref,
                content=content,
                content_digest=sha256_digest(content),
            ),
        ),
        file_manifest_input=FrozenFileManifestInput(
            file_manifest_ref="observed/files.jsonl",
            canonical_jsonl_bytes=manifest_bytes,
            manifest_digest=sha256_digest(manifest_bytes),
        ),
    )
    return _Fixture(
        context=context,
        request=CsvQuestionRequestV1(
            selected_path=_SELECTED_PATH,
            candidate_unit_column_index=candidate_index,
            comparison_column_index=comparison_index,
        ),
    )


def _manifest_bytes(records: tuple[FrozenBaseRecord, ...], snapshot_ref: dict[str, str]) -> bytes:
    return b"".join(
        record.canonical_payload + b"\n"
        for record in records
        if record.ref.record_type == "file_record"
        and json.loads(record.canonical_payload).get("snapshot_ref") == snapshot_ref
    )


def _unchecked(value: _T, **changes: object) -> _T:
    clone = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(
            clone,
            field.name,
            changes[field.name] if field.name in changes else getattr(value, field.name),
        )
    return cast(_T, clone)


def _with_manifest(context: ManifestBoundFrozenInspectionContext, raw: bytes) -> _Fixture:
    manifest = FrozenFileManifestInput(
        file_manifest_ref="observed/files.jsonl",
        canonical_jsonl_bytes=raw,
        manifest_digest=sha256_digest(raw),
    )
    changed = _unchecked(context, file_manifest_input=manifest)
    return _Fixture(changed, _fixture().request)


def _parsed_manifest(context: ManifestBoundFrozenInspectionContext) -> list[dict[str, Any]]:
    manifest = context.file_manifest_input
    assert manifest is not None
    return [json.loads(line) for line in manifest.canonical_jsonl_bytes.splitlines()]


def _manifest_from_entries(entries: list[dict[str, Any]]) -> bytes:
    return b"".join(canonical_json(entry).encode("utf-8") + b"\n" for entry in entries)


def _replace_record(
    context: ManifestBoundFrozenInspectionContext,
    target: RecordRef,
    payload: dict[str, Any],
    *,
    refresh_manifest: bool,
) -> ManifestBoundFrozenInspectionContext:
    replacement = _base(target, payload)
    records = tuple(
        replacement if record.ref == target else record for record in context.base_records
    )
    changed = _unchecked(context, base_records=records)
    if not refresh_manifest:
        return changed
    snapshot = next(record for record in records if record.ref.record_type == "repository_snapshot")
    raw = _manifest_bytes(records, snapshot.ref.to_dict())
    return _unchecked(
        changed,
        file_manifest_input=FrozenFileManifestInput(
            file_manifest_ref="observed/files.jsonl",
            canonical_jsonl_bytes=raw,
            manifest_digest=sha256_digest(raw),
        ),
    )


def _selected_file_record(context: ManifestBoundFrozenInspectionContext) -> FrozenBaseRecord:
    return next(
        record
        for record in context.base_records
        if record.ref.record_type == "file_record"
        and json.loads(record.canonical_payload).get("path") == _SELECTED_PATH
    )


def _selected_identity_record(context: ManifestBoundFrozenInspectionContext) -> FrozenBaseRecord:
    selected = _selected_file_record(context)
    identity_ref = json.loads(selected.canonical_payload)["asset_identity_ref"]
    return next(record for record in context.base_records if record.ref.to_dict() == identity_ref)


def _snapshot_record(context: ManifestBoundFrozenInspectionContext) -> FrozenBaseRecord:
    return next(
        record for record in context.base_records if record.ref.record_type == "repository_snapshot"
    )


def _all_results(fixture: _Fixture) -> tuple[SliceBPrimaryObservationResult, ...]:
    return tuple(verifier(fixture.context, fixture.request) for verifier in _VERIFY)


def _assert_refusal(fixture: _Fixture, reason: SliceBPrimaryRefusal) -> None:
    results = _all_results(fixture)
    assert [result.observation for result in results] == [None] * 4
    assert [result.refusal for result in results] == [reason] * 4
    assert not any(result.verified for result in results)


def _observations(fixture: _Fixture) -> tuple[Any, ...]:
    results = _all_results(fixture)
    assert [result.refusal for result in results] == [None] * 4
    observations = tuple(result.observation for result in results)
    assert all(observation is not None for observation in observations)
    return observations


def _numeric_payloads(fixture: _Fixture) -> tuple[dict[str, Any], ...]:
    common = {
        "observation_version",
        "observation_type",
        "verifier_id",
        "snapshot_digest",
        "file_record_ref_digest",
        "content_digest",
        "selected_file_ordinal",
        "review_scope_selection_evidence_digest",
        "finding_eligible",
        "observation_id",
    }
    return tuple(
        {key: value for key, value in observation.to_dict().items() if key not in common}
        for observation in _observations(fixture)
    )


def test_four_primary_verifiers_emit_exact_canonical_observed_facts() -> None:
    fixture = _fixture()
    shape, cardinalities, group_sizes, incidence = _observations(fixture)

    assert (shape.data_row_count, shape.column_count) == (4, 3)
    assert (
        cardinalities.candidate_unit_distinct_count,
        cardinalities.comparison_distinct_count,
    ) == (2, 2)
    assert group_sizes.sorted_group_sizes == (2, 2)
    assert (
        incidence.repeated_candidate_value_count,
        incidence.cross_comparison_candidate_value_count,
        incidence.comparison_values_per_candidate_histogram,
    ) == (2, 2, ((2, 2),))
    assert [
        observation.observation_type
        for observation in (shape, cardinalities, group_sizes, incidence)
    ] == [
        "csv-table-shape-v1",
        "csv-selected-cardinalities-v1",
        "csv-comparison-group-sizes-v1",
        "csv-unit-comparison-incidence-v1",
    ]
    assert all(observation.finding_eligible is False for observation in _observations(fixture))
    assert len({observation.content_digest for observation in _observations(fixture)}) == 1
    assert len({observation.snapshot_digest for observation in _observations(fixture)}) == 1
    assert len({observation.file_record_ref_digest for observation in _observations(fixture)}) == 1
    assert all(observation.selected_file_ordinal == 1 for observation in _observations(fixture))
    assert all(
        json.loads(canonical_observation_bytes(observation)) == observation.to_dict()
        for observation in _observations(fixture)
    )
    for observation in _observations(fixture):
        projection = observation.to_dict()
        observation_id = projection.pop("observation_id")
        assert observation_id == sha256_digest(canonical_json(projection).encode("utf-8"))


def test_primary_refusal_enum_is_closed_and_in_binding_order() -> None:
    assert [reason.value for reason in PRIMARY_REFUSAL_PRECEDENCE] == [
        "slice-b-manifest-input-absent",
        "slice-b-manifest-digest-invalid",
        "slice-b-manifest-bijection-invalid",
        "slice-b-selected-file-not-material",
        "slice-b-selected-file-identity-invalid",
        "slice-b-csv-byte-budget-exceeded",
        "slice-b-csv-byte-language-unsupported",
        "slice-b-csv-header-invalid",
        "slice-b-csv-shape-invalid",
        "slice-b-csv-row-budget-exceeded",
        "slice-b-column-role-invalid",
        "slice-b-observation-rederivation-mismatch",
    ]


def test_exact_review_scope_evidence_digest_uses_all_nine_retained_preimages() -> None:
    fixture = _fixture()
    context = fixture.context
    snapshot = _snapshot_record(context)
    selected = _selected_file_record(context)
    identity = _selected_identity_record(context)
    material = context.material_inputs[0]
    manifest = context.file_manifest_input
    assert manifest is not None
    projection = {
        "profile": "slice-b-explicit-material-input-selection-v1",
        "snapshot_ref": snapshot.ref.to_dict(),
        "snapshot_payload_digest": sha256_digest(snapshot.canonical_payload),
        "file_manifest_ref": manifest.file_manifest_ref,
        "manifest_digest": manifest.manifest_digest,
        "selected_path": material.path,
        "selected_file_ref": selected.ref.to_dict(),
        "selected_asset_identity_ref": identity.ref.to_dict(),
        "selected_content_digest": material.content_digest,
    }
    expected = sha256_digest(canonical_json(projection).encode("utf-8"))

    assert {item.review_scope_selection_evidence_digest for item in _observations(fixture)} == {
        expected
    }


@pytest.mark.parametrize(
    "extension_mutation",
    [
        {"x-material-full-digest-paths": [], "x-material-input-identities": []},
        {
            "x-material-full-digest-paths": [_SELECTED_PATH, _SELECTED_PATH],
            "x-material-input-identities": [
                {"path": _SELECTED_PATH, "tier": "full_digest"},
                {"path": _SELECTED_PATH, "tier": "full_digest"},
            ],
        },
        {
            "x-material-full-digest-paths": [_SELECTED_PATH],
            "x-material-input-identities": [{"path": _SELECTED_PATH, "tier": "manifest"}],
        },
        {
            "x-material-full-digest-paths": [_SELECTED_PATH],
            "x-material-input-identities": [
                {"path": _SELECTED_PATH, "tier": "full_digest", "extra": True}
            ],
        },
        {
            "x-material-full-digest-paths": [_SELECTED_PATH, "extra.csv"],
            "x-material-input-identities": [
                {"path": _SELECTED_PATH, "tier": "full_digest"},
                {"path": "extra.csv", "tier": "full_digest"},
            ],
        },
    ],
)
def test_scope_only_snapshot_or_material_list_attacks_preserve_facts_as_unresolved(
    extension_mutation: dict[str, Any],
) -> None:
    fixture = _fixture()
    snapshot = _snapshot_record(fixture.context)
    payload = json.loads(snapshot.canonical_payload)
    payload["extensions"] = extension_mutation
    changed = _replace_record(
        fixture.context,
        snapshot.ref,
        payload,
        refresh_manifest=False,
    )
    observations = _observations(_Fixture(changed, fixture.request))

    assert [item.review_scope_selection_evidence_digest for item in observations] == [
        "unresolved"
    ] * 4
    assert _numeric_payloads(_Fixture(changed, fixture.request)) == _numeric_payloads(fixture)


def test_graph_proposals_are_ignored_by_the_primary_scope_derivation() -> None:
    fixture = _fixture()
    baseline = [item.to_dict() for item in _observations(fixture)]
    forged_graph = {"cached_scope_digest": "sha256:" + "0" * 64, "verdict": "selected"}
    changed = _unchecked(fixture.context, scope_join_graph=forged_graph)

    assert [
        item.to_dict() for item in _observations(_Fixture(changed, fixture.request))
    ] == baseline


def test_manifest_absence_and_forged_manifest_capability_refuse() -> None:
    fixture = _fixture()
    _assert_refusal(
        _Fixture(_unchecked(fixture.context, file_manifest_input=None), fixture.request),
        SliceBPrimaryRefusal.MANIFEST_INPUT_ABSENT,
    )

    class CachedManifest:
        file_manifest_ref = "observed/files.jsonl"
        canonical_jsonl_bytes = fixture.context.file_manifest_input.canonical_jsonl_bytes  # type: ignore[union-attr]
        manifest_digest = fixture.context.file_manifest_input.manifest_digest  # type: ignore[union-attr]

    _assert_refusal(
        _Fixture(
            _unchecked(fixture.context, file_manifest_input=CachedManifest()), fixture.request
        ),
        SliceBPrimaryRefusal.MANIFEST_INPUT_ABSENT,
    )


def test_manifest_stale_digest_precedes_every_later_fault() -> None:
    fixture = _fixture(b"bad framing")
    manifest = fixture.context.file_manifest_input
    assert manifest is not None
    stale = _unchecked(manifest, manifest_digest="sha256:" + "0" * 64)
    changed = _unchecked(fixture.context, file_manifest_input=stale, material_inputs=())

    _assert_refusal(
        _Fixture(changed, fixture.request),
        SliceBPrimaryRefusal.MANIFEST_DIGEST_INVALID,
    )


@pytest.mark.parametrize(
    "attack",
    [
        "missing",
        "extra",
        "duplicate",
        "path-mismatch",
        "kind-mismatch",
        "size-mismatch",
        "identity-mismatch",
        "snapshot-mismatch",
        "malformed",
        "noncanonical",
        "missing-terminal-lf",
        "extra-terminal-lf",
    ],
)
def test_manifest_line_attacks_refuse_the_exact_bijection(attack: str) -> None:
    fixture = _fixture()
    entries = _parsed_manifest(fixture.context)
    selected_index = next(
        index for index, item in enumerate(entries) if item["path"] == _SELECTED_PATH
    )
    if attack == "missing":
        raw = _manifest_from_entries(entries[:-1])
    elif attack == "extra":
        extra = dict(entries[-1])
        extra["file_record_id"] = "file:slice-b:extra"
        extra["path"] = "extra/path.csv"
        raw = _manifest_from_entries([*entries, extra])
    elif attack == "duplicate":
        raw = _manifest_from_entries([*entries, entries[0]])
    elif attack in {
        "path-mismatch",
        "kind-mismatch",
        "size-mismatch",
        "identity-mismatch",
        "snapshot-mismatch",
    }:
        changed = [dict(item) for item in entries]
        target = changed[selected_index]
        if attack == "path-mismatch":
            target["path"] = "data/other.csv"
        elif attack == "kind-mismatch":
            target["entry_kind"] = "symlink"
        elif attack == "size-mismatch":
            target["byte_size"] += 1
        elif attack == "identity-mismatch":
            target["asset_identity_ref"] = {
                "record_type": "asset_identity",
                "record_id": "asset:other",
            }
        else:
            target["snapshot_ref"] = {
                "record_type": "repository_snapshot",
                "record_id": "snapshot:other",
            }
        raw = _manifest_from_entries(changed)
    elif attack == "malformed":
        raw = b'{"broken"\n'
    elif attack == "noncanonical":
        raw = b'{ "record_type": "file_record" }\n'
    elif attack == "missing-terminal-lf":
        original = fixture.context.file_manifest_input
        assert original is not None
        raw = original.canonical_jsonl_bytes[:-1]
    else:
        original = fixture.context.file_manifest_input
        assert original is not None
        raw = original.canonical_jsonl_bytes + b"\n"
    changed_fixture = _with_manifest(fixture.context, raw)

    _assert_refusal(changed_fixture, SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)


def test_manifest_reference_mismatch_is_a_bijection_refusal() -> None:
    fixture = _fixture()
    manifest = fixture.context.file_manifest_input
    assert manifest is not None
    changed_manifest = FrozenFileManifestInput(
        file_manifest_ref="other/files.jsonl",
        canonical_jsonl_bytes=manifest.canonical_jsonl_bytes,
        manifest_digest=manifest.manifest_digest,
    )
    _assert_refusal(
        _Fixture(
            _unchecked(fixture.context, file_manifest_input=changed_manifest), fixture.request
        ),
        SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID,
    )


def test_extra_or_duplicate_snapshot_file_records_refuse_even_when_manifest_is_unchanged() -> None:
    fixture = _fixture()
    selected = _selected_file_record(fixture.context)
    payload = json.loads(selected.canonical_payload)
    extra_ref = RecordRef("file_record", "file:slice-b:unmanifested")
    payload["file_record_id"] = extra_ref.record_id
    payload["path"] = "data/unmanifested.csv"
    extra = _base(extra_ref, payload)
    extra_context = _unchecked(
        fixture.context,
        base_records=(*fixture.context.base_records, extra),
    )
    _assert_refusal(
        _Fixture(extra_context, fixture.request),
        SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID,
    )

    duplicate_context = _unchecked(
        fixture.context,
        base_records=(*fixture.context.base_records, selected),
    )
    _assert_refusal(
        _Fixture(duplicate_context, fixture.request),
        SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID,
    )


def test_missing_selected_base_record_and_duplicate_associated_path_refuse_bijection() -> None:
    fixture = _fixture()
    selected = _selected_file_record(fixture.context)
    missing_records = tuple(record for record in fixture.context.base_records if record != selected)
    _assert_refusal(
        _Fixture(_unchecked(fixture.context, base_records=missing_records), fixture.request),
        SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID,
    )

    payload = json.loads(selected.canonical_payload)
    duplicate_ref = RecordRef("file_record", "file:slice-b:duplicate-path")
    duplicate_identity_ref = RecordRef("asset_identity", "asset:slice-b:duplicate-path")
    payload["file_record_id"] = duplicate_ref.record_id
    payload["asset_identity_ref"] = duplicate_identity_ref.to_dict()
    duplicate_file = _base(duplicate_ref, payload)
    duplicate_identity = _base(
        duplicate_identity_ref,
        {
            "record_type": "asset_identity",
            "asset_identity_id": duplicate_identity_ref.record_id,
            "asset_ref": duplicate_ref.to_dict(),
            "tier": "full_digest",
            "identity_evidence": {
                "kind": "full_digest",
                "digest": sha256_digest(_CSV),
            },
        },
    )
    records = (*fixture.context.base_records, duplicate_file, duplicate_identity)
    snapshot = _snapshot_record(fixture.context)
    raw = _manifest_bytes(records, snapshot.ref.to_dict())
    duplicate_path_context = _unchecked(
        fixture.context,
        base_records=records,
        file_manifest_input=FrozenFileManifestInput(
            file_manifest_ref="observed/files.jsonl",
            canonical_jsonl_bytes=raw,
            manifest_digest=sha256_digest(raw),
        ),
    )
    _assert_refusal(
        _Fixture(duplicate_path_context, fixture.request),
        SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID,
    )


@pytest.mark.parametrize("entry_kind", ["directory", "symlink", "special", "unknown"])
def test_selected_nonregular_entries_refuse_as_not_material(entry_kind: str) -> None:
    fixture = _fixture()
    selected = _selected_file_record(fixture.context)
    payload = json.loads(selected.canonical_payload)
    payload["entry_kind"] = entry_kind
    changed = _replace_record(
        fixture.context,
        selected.ref,
        payload,
        refresh_manifest=True,
    )

    _assert_refusal(
        _Fixture(changed, fixture.request),
        SliceBPrimaryRefusal.SELECTED_FILE_NOT_MATERIAL,
    )


def test_correct_unrelated_nonregular_entries_are_visible_but_do_not_block_observations() -> None:
    with_nonregular = _fixture(include_nonregular=True)
    without_nonregular = _fixture(include_nonregular=False)
    assert all(result.verified for result in _all_results(with_nonregular))
    assert _numeric_payloads(with_nonregular) == _numeric_payloads(without_nonregular)

    entries = _parsed_manifest(with_nonregular.context)
    omitted = [item for item in entries if item["path"] != "latest-data"]
    _assert_refusal(
        _with_manifest(with_nonregular.context, _manifest_from_entries(omitted)),
        SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID,
    )


def test_missing_or_wrong_file_material_capability_refuses_before_identity() -> None:
    fixture = _fixture()
    _assert_refusal(
        _Fixture(_unchecked(fixture.context, material_inputs=()), fixture.request),
        SliceBPrimaryRefusal.SELECTED_FILE_NOT_MATERIAL,
    )
    material = fixture.context.material_inputs[0]
    wrong_file = _unchecked(material, file_ref=RecordRef("file_record", "file:wrong"))
    _assert_refusal(
        _Fixture(_unchecked(fixture.context, material_inputs=(wrong_file,)), fixture.request),
        SliceBPrimaryRefusal.SELECTED_FILE_NOT_MATERIAL,
    )
    missing_path_request = CsvQuestionRequestV1(
        selected_path="data/not-selected.csv",
        candidate_unit_column_index=0,
        comparison_column_index=1,
    )
    _assert_refusal(
        _Fixture(fixture.context, missing_path_request),
        SliceBPrimaryRefusal.SELECTED_FILE_NOT_MATERIAL,
    )


def test_missing_selected_identity_base_record_refuses_full_digest_join() -> None:
    fixture = _fixture()
    identity = _selected_identity_record(fixture.context)
    records = tuple(record for record in fixture.context.base_records if record != identity)
    _assert_refusal(
        _Fixture(_unchecked(fixture.context, base_records=records), fixture.request),
        SliceBPrimaryRefusal.SELECTED_FILE_IDENTITY_INVALID,
    )


@pytest.mark.parametrize(
    "attack",
    [
        "stale-material-content",
        "material-only-rehash",
        "wrong-material-identity-ref",
        "stale-identity-digest",
        "manifest-size-vs-content",
        "duplicate-identity-claim",
    ],
)
def test_full_digest_material_and_identity_attacks_refuse(attack: str) -> None:
    fixture = _fixture()
    context = fixture.context
    material = context.material_inputs[0]
    if attack == "stale-material-content":
        changed_material = _unchecked(material, content=material.content.replace(b"u1", b"z1", 1))
        context = _unchecked(context, material_inputs=(changed_material,))
    elif attack == "material-only-rehash":
        changed_content = material.content.replace(b"u1", b"z1", 1)
        changed_material = _unchecked(
            material,
            content=changed_content,
            content_digest=sha256_digest(changed_content),
        )
        context = _unchecked(context, material_inputs=(changed_material,))
    elif attack == "wrong-material-identity-ref":
        changed_material = _unchecked(
            material,
            asset_identity_ref=RecordRef("asset_identity", "asset:wrong"),
        )
        context = _unchecked(context, material_inputs=(changed_material,))
    elif attack == "stale-identity-digest":
        identity = _selected_identity_record(context)
        payload = json.loads(identity.canonical_payload)
        payload["identity_evidence"]["digest"] = "sha256:" + "0" * 64
        context = _replace_record(context, identity.ref, payload, refresh_manifest=False)
    elif attack == "manifest-size-vs-content":
        selected = _selected_file_record(context)
        payload = json.loads(selected.canonical_payload)
        payload["byte_size"] += 1
        context = _replace_record(context, selected.ref, payload, refresh_manifest=True)
    else:
        selected = _selected_file_record(context)
        identity = _selected_identity_record(context)
        payload = json.loads(identity.canonical_payload)
        duplicate_ref = RecordRef("asset_identity", "asset:slice-b:duplicate")
        payload["asset_identity_id"] = duplicate_ref.record_id
        duplicate = _base(duplicate_ref, payload)
        context = _unchecked(context, base_records=(*context.base_records, duplicate))

    _assert_refusal(
        _Fixture(context, fixture.request),
        SliceBPrimaryRefusal.SELECTED_FILE_IDENTITY_INVALID,
    )


@pytest.mark.parametrize(
    ("content", "reason"),
    [
        (b"", SliceBPrimaryRefusal.CSV_BYTE_LANGUAGE_UNSUPPORTED),
        (b"a,b\n1,2", SliceBPrimaryRefusal.CSV_BYTE_LANGUAGE_UNSUPPORTED),
        (b"a,b\n1,2\n\n", SliceBPrimaryRefusal.CSV_BYTE_LANGUAGE_UNSUPPORTED),
        (b"a,b\r\n1,2\r\n", SliceBPrimaryRefusal.CSV_BYTE_LANGUAGE_UNSUPPORTED),
        (b"a,b\n1,\t2\n", SliceBPrimaryRefusal.CSV_BYTE_LANGUAGE_UNSUPPORTED),
        (b"a,b\n1,\x002\n", SliceBPrimaryRefusal.CSV_BYTE_LANGUAGE_UNSUPPORTED),
        (b"a,b\n1,\x7f\n", SliceBPrimaryRefusal.CSV_BYTE_LANGUAGE_UNSUPPORTED),
        (b"\xef\xbb\xbfa,b\n1,2\n", SliceBPrimaryRefusal.CSV_BYTE_LANGUAGE_UNSUPPORTED),
        ("a,b\n1,é\n".encode(), SliceBPrimaryRefusal.CSV_BYTE_LANGUAGE_UNSUPPORTED),
        (b'a,b\n1,"2"\n', SliceBPrimaryRefusal.CSV_BYTE_LANGUAGE_UNSUPPORTED),
        (b"only\nvalue\n", SliceBPrimaryRefusal.CSV_HEADER_INVALID),
        (b"a,a\n1,2\n", SliceBPrimaryRefusal.CSV_HEADER_INVALID),
        (b"a,\n1,2\n", SliceBPrimaryRefusal.CSV_HEADER_INVALID),
        (b"a;b\n1;2\n", SliceBPrimaryRefusal.CSV_HEADER_INVALID),
        (b"a,b\n", SliceBPrimaryRefusal.CSV_SHAPE_INVALID),
        (b"a,b\n1\n", SliceBPrimaryRefusal.CSV_SHAPE_INVALID),
        (b"a,b\n1,\n", SliceBPrimaryRefusal.CSV_SHAPE_INVALID),
    ],
)
def test_csv_encoding_framing_header_and_shape_refusal_families(
    content: bytes, reason: SliceBPrimaryRefusal
) -> None:
    _assert_refusal(_fixture(content), reason)


def test_csv_column_field_row_and_total_byte_boundaries() -> None:
    header_64 = b",".join(f"c{index}".encode() for index in range(64))
    row_64 = b",".join(b"x" for _ in range(64))
    assert all(
        result.verified for result in _all_results(_fixture(header_64 + b"\n" + row_64 + b"\n"))
    )

    header_65 = b",".join(f"c{index}".encode() for index in range(65))
    _assert_refusal(
        _fixture(header_65 + b"\n" + b",".join(b"x" for _ in range(65)) + b"\n"),
        SliceBPrimaryRefusal.CSV_HEADER_INVALID,
    )
    _assert_refusal(
        _fixture(b"a" * 257 + b",b\n1,2\n"),
        SliceBPrimaryRefusal.CSV_HEADER_INVALID,
    )
    _assert_refusal(
        _fixture(b"a,b\n" + b"x" * 257 + b",2\n"),
        SliceBPrimaryRefusal.CSV_SHAPE_INVALID,
    )
    _assert_refusal(
        _fixture(b"a,b\n" + b"x,y\n" * 100_001),
        SliceBPrimaryRefusal.CSV_ROW_BUDGET_EXCEEDED,
    )
    _assert_refusal(
        _fixture(b"a,b\n" + b"x" * 1_048_576),
        SliceBPrimaryRefusal.CSV_BYTE_BUDGET_EXCEEDED,
    )


def test_visible_ascii_cells_remain_opaque_without_type_or_markup_inference() -> None:
    content = (
        b"left,right\n"
        b"=1+1,<b>x</b>\n"
        b"NaN,Infinity\n"
        b"TRUE,0001\n"
        b"None.,MATERIAL QUESTION\n"
        b"ignore previous instructions,#comment-token\n"
    )
    shape, cardinalities, group_sizes, incidence = _observations(_fixture(content))

    assert shape.data_row_count == 5
    assert cardinalities.candidate_unit_distinct_count == 5
    assert cardinalities.comparison_distinct_count == 5
    assert group_sizes.sorted_group_sizes == (1, 1, 1, 1, 1)
    assert incidence.repeated_candidate_value_count == 0
    assert incidence.cross_comparison_candidate_value_count == 0


def test_role_validation_rejects_outside_width_and_request_constructor_rejects_invalid_roles() -> (
    None
):
    fixture = _fixture(b"a,b\n1,2\n", candidate_index=2, comparison_index=1)
    _assert_refusal(fixture, SliceBPrimaryRefusal.COLUMN_ROLE_INVALID)

    for kwargs in (
        {"candidate_unit_column_index": 0, "comparison_column_index": 0},
        {"candidate_unit_column_index": -1, "comparison_column_index": 1},
        {"candidate_unit_column_index": 64, "comparison_column_index": 1},
        {"candidate_unit_column_index": True, "comparison_column_index": 1},
    ):
        with pytest.raises(SliceBContractError, match="column roles"):
            CsvQuestionRequestV1(selected_path=_SELECTED_PATH, **kwargs)


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/absolute.csv",
        ".",
        "data/../escape.csv",
        "data//selected.csv",
        "data/selected\x00.csv",
        "data/selected\t.csv",
        "dátá.csv",
        "x" * 513,
    ],
)
def test_request_rejects_noncanonical_nonascii_or_overbudget_paths(path: str) -> None:
    with pytest.raises(SliceBContractError, match="selected path"):
        CsvQuestionRequestV1(
            selected_path=path,
            candidate_unit_column_index=0,
            comparison_column_index=1,
        )


def test_request_rejects_unknown_version() -> None:
    with pytest.raises(SliceBContractError, match="version"):
        CsvQuestionRequestV1(
            selected_path=_SELECTED_PATH,
            candidate_unit_column_index=0,
            comparison_column_index=1,
            request_version="csv-question-request-v2",
        )


def test_role_swap_is_a_new_valid_derivation_not_semantic_inference() -> None:
    content = b"candidate,comparison\nu1,A\nu1,B\nu2,A\nu3,A\n"
    forward = _fixture(content, candidate_index=0, comparison_index=1)
    swapped = _fixture(content, candidate_index=1, comparison_index=0)
    forward_values = _numeric_payloads(forward)
    swapped_values = _numeric_payloads(swapped)

    assert all(result.verified for result in _all_results(forward))
    assert all(result.verified for result in _all_results(swapped))
    assert forward_values != swapped_values
    assert forward_values[1]["candidate_unit_column_index"] == 0
    assert swapped_values[1]["candidate_unit_column_index"] == 1


def test_partition_preserving_rename_and_row_permutation_preserve_only_numeric_payloads() -> None:
    original = _fixture()
    renamed = _fixture(_CSV.replace(b"u1", b"z1").replace(b"u2", b"z2"))
    permuted = _fixture(b"candidate,comparison,value\nu2,B,4\nu1,A,1\nu2,A,3\nu1,B,2\n")
    original_observations = _observations(original)

    assert _numeric_payloads(renamed) == _numeric_payloads(original)
    assert _numeric_payloads(permuted) == _numeric_payloads(original)
    for changed in (renamed, permuted):
        changed_observations = _observations(changed)
        assert {item.content_digest for item in changed_observations} != {
            item.content_digest for item in original_observations
        }
        assert [item.observation_id for item in changed_observations] != [
            item.observation_id for item in original_observations
        ]
        assert {item.review_scope_selection_evidence_digest for item in changed_observations} != {
            item.review_scope_selection_evidence_digest for item in original_observations
        }


def test_partition_changing_mutation_changes_the_defined_aggregate_and_ids() -> None:
    original = _fixture()
    changed = _fixture(_CSV.replace(b"u2", b"u1"))

    assert _numeric_payloads(changed) != _numeric_payloads(original)
    assert _numeric_payloads(original)[1]["candidate_unit_distinct_count"] == 2
    assert _numeric_payloads(changed)[1]["candidate_unit_distinct_count"] == 1
    assert [item.observation_id for item in _observations(changed)] != [
        item.observation_id for item in _observations(original)
    ]


def test_reviewed_partition_change_with_equal_registered_aggregates_changes_only_identity() -> None:
    four_two = _fixture(b"candidate,comparison\na,x\na,x\na,x\na,x\nb,x\nb,x\n")
    three_three = _fixture(b"candidate,comparison\na,x\na,x\na,x\nb,x\nb,x\nb,x\n")

    assert _numeric_payloads(four_two) == _numeric_payloads(three_three)
    assert _numeric_payloads(four_two) == (
        {"data_row_count": 6, "column_count": 2},
        {
            "candidate_unit_column_index": 0,
            "comparison_column_index": 1,
            "candidate_unit_distinct_count": 2,
            "comparison_distinct_count": 1,
        },
        {"comparison_column_index": 1, "sorted_group_sizes": [6]},
        {
            "candidate_unit_column_index": 0,
            "comparison_column_index": 1,
            "repeated_candidate_value_count": 2,
            "cross_comparison_candidate_value_count": 0,
            "comparison_values_per_candidate_histogram": [[1, 2]],
        },
    )
    assert [item.content_digest for item in _observations(four_two)] != [
        item.content_digest for item in _observations(three_three)
    ]
    assert [item.observation_id for item in _observations(four_two)] != [
        item.observation_id for item in _observations(three_three)
    ]


def test_each_verifier_reparses_frozen_bytes_and_does_not_reuse_a_carried_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture()
    original = primary_module._parse_primary_csv_bytes
    calls: list[bytes] = []

    def counted(content: bytes, request: CsvQuestionRequestV1) -> Any:
        calls.append(content)
        return original(content, request)

    monkeypatch.setattr(primary_module, "_parse_primary_csv_bytes", counted)
    first = _all_results(fixture)
    second = _all_results(fixture)

    assert calls == [_CSV] * 8
    assert [item.observation for item in first] == [item.observation for item in second]
    assert all(
        left.observation is not right.observation for left, right in zip(first, second, strict=True)
    )


def test_live_filesystem_and_a_to_b_to_a_swap_hooks_are_never_consulted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture()

    def forbidden_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("primary verifier attempted a live filesystem read")

    monkeypatch.setattr("builtins.open", forbidden_open)
    assert all(result.verified for result in _all_results(fixture))


def test_forged_replaced_subclassed_or_carried_observations_cannot_feed_primary_verifiers() -> None:
    fixture = _fixture()
    shape = cast(CsvTableShapeObservationV1, _observations(fixture)[0])
    with pytest.raises(SliceBContractError, match="observation id"):
        canonical_observation_bytes(replace(shape, data_row_count=shape.data_row_count + 1))
    forged = _unchecked(shape, data_row_count=shape.data_row_count + 1)
    with pytest.raises(SliceBContractError, match="observation id"):
        canonical_observation_bytes(forged)
    with pytest.raises(SliceBContractError, match="canonical closed record"):
        canonical_observation_bytes(cast(Any, object.__new__(CsvTableShapeObservationV1)))

    bool_projection = shape.to_dict()
    bool_projection["data_row_count"] = True
    id_projection = dict(bool_projection)
    id_projection.pop("observation_id")
    bool_projection["observation_id"] = sha256_digest(canonical_json(id_projection).encode("utf-8"))
    with pytest.raises(SliceBContractError, match="shape observation"):
        canonical_observation_bytes(CsvTableShapeObservationV1(**bool_projection))
    with pytest.raises(TypeError):
        CsvTableShapeObservationV1(**shape.to_dict(), extra_field="proposal")
    with pytest.raises(SliceBContractError, match="request"):
        verify_csv_table_shape_v1(fixture.context, cast(Any, shape))
    with pytest.raises(TypeError):
        verify_csv_table_shape_v1(fixture.context, fixture.request, observation=shape)  # type: ignore[call-arg]


def test_cached_or_proposal_context_objects_refuse_even_if_they_copy_valid_attributes() -> None:
    fixture = _fixture()

    class CachedContext:
        def __init__(self) -> None:
            self.__dict__.update(
                fixture.context.__dict__ if hasattr(fixture.context, "__dict__") else {}
            )
            self.file_manifest_input = fixture.context.file_manifest_input
            self.base_records = fixture.context.base_records
            self.material_inputs = fixture.context.material_inputs
            self.snapshot_digest = fixture.context.snapshot_digest
            self.cached_table = ((b"forged", b"table"),)
            self.proposed_observation = {"data_row_count": 999}

    _assert_refusal(
        _Fixture(cast(Any, CachedContext()), fixture.request),
        SliceBPrimaryRefusal.MANIFEST_INPUT_ABSENT,
    )


def test_result_value_rejects_forged_observation_and_unknown_refusal() -> None:
    fixture = _fixture()
    shape = cast(CsvTableShapeObservationV1, _observations(fixture)[0])
    forged = _unchecked(shape, observation_id="sha256:" + "0" * 64)
    with pytest.raises(SliceBContractError, match="observation id"):
        SliceBPrimaryObservationResult(observation=forged, refusal=None)
    with pytest.raises(SliceBContractError, match="closed enum"):
        SliceBPrimaryObservationResult(
            observation=None,
            refusal=cast(Any, "slice-b-made-up-refusal"),
        )
    with pytest.raises(SliceBContractError, match="exactly one"):
        SliceBPrimaryObservationResult(observation=None, refusal=None)
