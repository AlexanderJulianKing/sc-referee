"""Primary Slice-B CSV observation verifiers.

This module is an unregistered development surface.  Every public verifier starts
from the controller-frozen context, reconstructs the complete selected-byte join,
and parses the CSV anew.  Parsed manifests, tables, facts, and success bits are not
accepted from callers and are not cached between verifier calls.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from itertools import pairwise
from pathlib import PurePosixPath
from typing import Any, Final, NoReturn, TypeAlias, TypeGuard, cast, final

from sc_referee.controller import (
    FrozenFileManifestInput,
    ManifestBoundFrozenInspectionContext,
)
from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.scientific_checks.core import FrozenBaseRecord, FrozenMaterialInput, RecordRef
from sc_referee_evaluation.audit_ladder.slice_b.renderer import (
    CsvComparisonGroupSizesObservationV1,
    CsvSelectedCardinalitiesObservationV1,
    CsvTableShapeObservationV1,
    CsvUnitComparisonIncidenceObservationV1,
    SliceBObservationV1,
    SliceBPrimaryRefusalReasonV1,
)

_REQUEST_VERSION: Final = "csv-question-request-v1"
_OBSERVATION_VERSION: Final = "slice-b-observation-v1"
_UNRESOLVED_SCOPE: Final = "unresolved"
_MAX_PATH_BYTES: Final = 512
_MAX_CSV_BYTES: Final = 1_048_576
_MAX_FIELD_BYTES: Final = 256
_MAX_COLUMNS: Final = 64
_MAX_ROWS: Final = 100_000
_ENTRY_KINDS: Final = frozenset({"regular_file", "directory", "symlink", "special", "unknown"})


class SliceBContractError(ValueError):
    """A caller-created value escaped the closed Slice-B contract."""


SliceBPrimaryRefusal: TypeAlias = SliceBPrimaryRefusalReasonV1


@final
@dataclass(frozen=True, slots=True)
class CsvQuestionRequestV1:
    """The only controller-selected role request accepted by the primary verifiers."""

    selected_path: str
    candidate_unit_column_index: int
    comparison_column_index: int
    request_version: str = _REQUEST_VERSION

    def __post_init__(self) -> None:
        _require_request(self)


@final
@dataclass(frozen=True, slots=True)
class SliceBPrimaryObservationResult:
    """Exactly one verified observation or one closed primary refusal."""

    observation: SliceBObservationV1 | None
    refusal: SliceBPrimaryRefusal | None

    def __post_init__(self) -> None:
        if type(self) is not SliceBPrimaryObservationResult:
            raise SliceBContractError("result subclasses are not accepted")
        if (self.observation is None) == (self.refusal is None):
            raise SliceBContractError("result must contain exactly one outcome")
        if self.refusal is not None and type(self.refusal) is not SliceBPrimaryRefusalReasonV1:
            raise SliceBContractError("result refusal is outside the closed enum")
        if self.observation is not None:
            canonical_observation_bytes(self.observation)

    @property
    def verified(self) -> bool:
        return self.observation is not None


def canonical_observation_bytes(observation: SliceBObservationV1) -> bytes:
    """Revalidate and serialize one exact immutable observation record."""

    try:
        _validate_primary_observation(observation)
        return canonical_json(observation.to_dict()).encode("utf-8")
    except (AttributeError, KeyError, TypeError, UnicodeError) as error:
        raise SliceBContractError("observation is not one canonical closed record") from error


def _validate_primary_observation(observation: SliceBObservationV1) -> None:
    if type(observation) is CsvTableShapeObservationV1:
        _validate_common_observation(
            observation,
            observation_type="csv-table-shape-v1",
            verifier_id="slice-b-csv-shape-verifier-v1",
        )
        if not _bounded_int(observation.data_row_count, 1, _MAX_ROWS) or not _bounded_int(
            observation.column_count, 2, _MAX_COLUMNS
        ):
            raise SliceBContractError("shape observation payload is outside its bounds")
    elif type(observation) is CsvSelectedCardinalitiesObservationV1:
        _validate_common_observation(
            observation,
            observation_type="csv-selected-cardinalities-v1",
            verifier_id="slice-b-csv-cardinality-verifier-v1",
        )
        _require_distinct_column_indices(
            observation.candidate_unit_column_index,
            observation.comparison_column_index,
        )
        if not _bounded_int(
            observation.candidate_unit_distinct_count, 1, _MAX_ROWS
        ) or not _bounded_int(observation.comparison_distinct_count, 1, _MAX_ROWS):
            raise SliceBContractError("cardinality observation payload is outside its bounds")
    elif type(observation) is CsvComparisonGroupSizesObservationV1:
        _validate_common_observation(
            observation,
            observation_type="csv-comparison-group-sizes-v1",
            verifier_id="slice-b-csv-group-size-verifier-v1",
        )
        if not _bounded_int(observation.comparison_column_index, 0, _MAX_COLUMNS - 1):
            raise SliceBContractError("group-size column index is outside its bound")
        sizes = observation.sorted_group_sizes
        if (
            type(sizes) is not tuple
            or not sizes
            or len(sizes) > _MAX_ROWS
            or any(type(value) is not int or value < 1 for value in sizes)
            or tuple(sorted(sizes)) != sizes
            or sum(sizes) > _MAX_ROWS
        ):
            raise SliceBContractError("group-size vector is outside the closed schema")
    elif type(observation) is CsvUnitComparisonIncidenceObservationV1:
        _validate_common_observation(
            observation,
            observation_type="csv-unit-comparison-incidence-v1",
            verifier_id="slice-b-csv-incidence-verifier-v1",
        )
        _require_distinct_column_indices(
            observation.candidate_unit_column_index,
            observation.comparison_column_index,
        )
        if not _bounded_int(
            observation.repeated_candidate_value_count, 0, _MAX_ROWS
        ) or not _bounded_int(observation.cross_comparison_candidate_value_count, 0, _MAX_ROWS):
            raise SliceBContractError("incidence counts are outside their bounds")
        histogram = observation.comparison_values_per_candidate_histogram
        if (
            type(histogram) is not tuple
            or not histogram
            or len(histogram) > _MAX_ROWS
            or any(
                type(pair) is not tuple
                or len(pair) != 2
                or type(pair[0]) is not int
                or type(pair[1]) is not int
                or pair[0] < 1
                or pair[1] < 1
                for pair in histogram
            )
        ):
            raise SliceBContractError("incidence histogram is outside the closed schema")
        first_components = tuple(pair[0] for pair in histogram)
        if (
            any(left >= right for left, right in pairwise(first_components))
            or sum(pair[1] for pair in histogram) > _MAX_ROWS
            or observation.cross_comparison_candidate_value_count
            != sum(pair[1] for pair in histogram if pair[0] > 1)
        ):
            raise SliceBContractError("incidence histogram algebra is invalid")
    else:
        raise SliceBContractError("unknown or subclassed observation type")
    _require_matching_observation_id(observation)


def _validate_common_observation(
    observation: SliceBObservationV1,
    *,
    observation_type: str,
    verifier_id: str,
) -> None:
    if (
        type(observation.observation_version) is not str
        or observation.observation_version != _OBSERVATION_VERSION
        or type(observation.observation_type) is not str
        or observation.observation_type != observation_type
        or type(observation.verifier_id) is not str
        or observation.verifier_id != verifier_id
        or not _is_sha256(observation.snapshot_digest)
        or not _is_sha256(observation.file_record_ref_digest)
        or not _is_sha256(observation.content_digest)
        or type(observation.selected_file_ordinal) is not int
        or observation.selected_file_ordinal != 1
        or not (
            observation.review_scope_selection_evidence_digest == _UNRESOLVED_SCOPE
            or _is_sha256(observation.review_scope_selection_evidence_digest)
        )
        or observation.finding_eligible is not False
        or type(observation.observation_id) is not str
    ):
        raise SliceBContractError("observation common fields are outside the closed schema")


def verify_csv_table_shape_v1(
    context: ManifestBoundFrozenInspectionContext,
    request: CsvQuestionRequestV1,
) -> SliceBPrimaryObservationResult:
    """Independently verify table shape from frozen manifest-bound bytes."""

    return _verify(context, request, _build_shape_observation)


def verify_csv_selected_cardinalities_v1(
    context: ManifestBoundFrozenInspectionContext,
    request: CsvQuestionRequestV1,
) -> SliceBPrimaryObservationResult:
    """Independently verify both selected-column cardinalities."""

    return _verify(context, request, _build_cardinality_observation)


def verify_csv_comparison_group_sizes_v1(
    context: ManifestBoundFrozenInspectionContext,
    request: CsvQuestionRequestV1,
) -> SliceBPrimaryObservationResult:
    """Independently verify the sorted comparison-group size vector."""

    return _verify(context, request, _build_group_size_observation)


def verify_csv_unit_comparison_incidence_v1(
    context: ManifestBoundFrozenInspectionContext,
    request: CsvQuestionRequestV1,
) -> SliceBPrimaryObservationResult:
    """Independently verify candidate/comparison incidence aggregates."""

    return _verify(context, request, _build_incidence_observation)


@dataclass(frozen=True, slots=True)
class _CsvTable:
    header: tuple[bytes, ...]
    rows: tuple[tuple[bytes, ...], ...]


@dataclass(frozen=True, slots=True)
class _PrimaryTransaction:
    snapshot_digest: str
    file_record_ref_digest: str
    content_digest: str
    review_scope_selection_evidence_digest: str
    table: _CsvTable
    request: CsvQuestionRequestV1


class _PrimaryRefusalError(Exception):
    def __init__(self, refusal: SliceBPrimaryRefusal) -> None:
        super().__init__(refusal.value)
        self.refusal = refusal


def _verify(
    context: ManifestBoundFrozenInspectionContext,
    request: CsvQuestionRequestV1,
    builder: Callable[[_PrimaryTransaction], SliceBObservationV1],
) -> SliceBPrimaryObservationResult:
    _require_request(request)
    try:
        transaction = _primary_transaction(context, request)
        observation = builder(transaction)
    except _PrimaryRefusalError as error:
        return SliceBPrimaryObservationResult(observation=None, refusal=error.refusal)
    return SliceBPrimaryObservationResult(observation=observation, refusal=None)


def _primary_transaction(
    context: ManifestBoundFrozenInspectionContext,
    request: CsvQuestionRequestV1,
) -> _PrimaryTransaction:
    if type(context) is not ManifestBoundFrozenInspectionContext:
        _refuse(SliceBPrimaryRefusal.MANIFEST_INPUT_ABSENT)
    manifest_value = getattr(context, "file_manifest_input", None)
    if type(manifest_value) is not FrozenFileManifestInput:
        _refuse(SliceBPrimaryRefusal.MANIFEST_INPUT_ABSENT)
    manifest = manifest_value
    manifest_ref_value = getattr(manifest, "file_manifest_ref", None)
    manifest_bytes_value = getattr(manifest, "canonical_jsonl_bytes", None)
    manifest_digest_value = getattr(manifest, "manifest_digest", None)
    if (
        type(manifest_ref_value) is not str
        or not _safe_relative_posix_path(manifest_ref_value)
        or type(manifest_bytes_value) is not bytes
        or not _is_sha256(manifest_digest_value)
        or sha256_digest(manifest_bytes_value) != manifest_digest_value
    ):
        _refuse(SliceBPrimaryRefusal.MANIFEST_DIGEST_INVALID)
    manifest_ref = manifest_ref_value
    manifest_bytes = manifest_bytes_value

    snapshot_digest_value = getattr(context, "snapshot_digest", None)
    base_records_value = getattr(context, "base_records", None)
    if not _is_sha256(snapshot_digest_value) or type(base_records_value) is not tuple:
        _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)
    snapshot_digest = snapshot_digest_value
    base_records = cast(tuple[object, ...], base_records_value)
    parsed_records = _parse_base_records(base_records)
    snapshots = [
        (record, payload)
        for record, payload in parsed_records
        if record.ref.record_type == "repository_snapshot"
    ]
    if len(snapshots) != 1:
        _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)
    snapshot_record, snapshot_payload = snapshots[0]
    snapshot_ref = _record_ref_mapping(snapshot_record.ref)
    if (
        snapshot_payload.get("snapshot_id") != snapshot_record.ref.record_id
        or snapshot_payload.get("snapshot_digest") != snapshot_digest
        or snapshot_payload.get("immutability") is not True
        or snapshot_payload.get("file_manifest_ref") != manifest_ref
    ):
        _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)

    file_records = _manifest_record_bijection(
        parsed_records,
        snapshot_ref=snapshot_ref,
        manifest_bytes=manifest_bytes,
    )
    selected = [pair for pair in file_records if pair[1]["path"] == request.selected_path]
    if len(selected) != 1 or selected[0][1]["entry_kind"] != "regular_file":
        _refuse(SliceBPrimaryRefusal.SELECTED_FILE_NOT_MATERIAL)
    file_record, file_payload = selected[0]

    material_inputs_value = getattr(context, "material_inputs", None)
    if type(material_inputs_value) is not tuple:
        _refuse(SliceBPrimaryRefusal.SELECTED_FILE_NOT_MATERIAL)
    material_inputs = cast(tuple[object, ...], material_inputs_value)
    selected_materials = [
        item
        for item in material_inputs
        if type(item) is FrozenMaterialInput
        and getattr(item, "path", None) == request.selected_path
    ]
    if len(selected_materials) != 1:
        _refuse(SliceBPrimaryRefusal.SELECTED_FILE_NOT_MATERIAL)
    material = selected_materials[0]
    if not _same_record_ref(getattr(material, "file_ref", None), file_record.ref):
        _refuse(SliceBPrimaryRefusal.SELECTED_FILE_NOT_MATERIAL)

    identity_record = _selected_full_digest_identity(
        parsed_records,
        file_records,
        file_record=file_record,
        file_payload=file_payload,
    )
    material_identity_ref = getattr(material, "asset_identity_ref", None)
    content_value = getattr(material, "content", None)
    content_digest_value = getattr(material, "content_digest", None)
    if (
        identity_record is None
        or not _same_record_ref(material_identity_ref, identity_record[0].ref)
        or type(content_value) is not bytes
        or not _is_sha256(content_digest_value)
        or sha256_digest(content_value) != content_digest_value
        or identity_record[1]["identity_evidence"]["digest"] != content_digest_value
        or file_payload["byte_size"] != len(content_value)
    ):
        _refuse(SliceBPrimaryRefusal.SELECTED_FILE_IDENTITY_INVALID)
    content = content_value
    content_digest = content_digest_value

    scope_digest = _review_scope_selection_digest(
        context=context,
        snapshot_record=snapshot_record,
        snapshot_payload=snapshot_payload,
        manifest=manifest,
        file_record=file_record,
        identity_record=identity_record[0],
        material=material,
    )
    table = _parse_primary_csv_bytes(content, request)
    return _PrimaryTransaction(
        snapshot_digest=snapshot_digest,
        file_record_ref_digest=sha256_digest(
            canonical_json(_record_ref_mapping(file_record.ref)).encode("utf-8")
        ),
        content_digest=content_digest,
        review_scope_selection_evidence_digest=scope_digest,
        table=table,
        request=request,
    )


def _parse_base_records(
    base_records: tuple[object, ...],
) -> tuple[tuple[FrozenBaseRecord, dict[str, Any]], ...]:
    parsed: list[tuple[FrozenBaseRecord, dict[str, Any]]] = []
    seen_refs: set[tuple[str, str]] = set()
    try:
        for candidate in base_records:
            if type(candidate) is not FrozenBaseRecord:
                _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)
            record = candidate
            if type(record.ref) is not RecordRef:
                _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)
            ref_key = _record_ref_key(record.ref)
            if ref_key in seen_refs:
                _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)
            payload = record.canonical_payload
            if (
                type(payload) is not bytes
                or not _is_sha256(record.payload_digest)
                or sha256_digest(payload) != record.payload_digest
            ):
                _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)
            parsed.append((record, _decode_canonical_object(payload)))
            seen_refs.add(ref_key)
    except (AttributeError, TypeError, UnicodeError, ValueError, RecursionError):
        _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)
    return tuple(parsed)


def _manifest_record_bijection(
    parsed_records: tuple[tuple[FrozenBaseRecord, dict[str, Any]], ...],
    *,
    snapshot_ref: dict[str, str],
    manifest_bytes: bytes,
) -> tuple[tuple[FrozenBaseRecord, dict[str, Any]], ...]:
    associated: dict[str, tuple[FrozenBaseRecord, dict[str, Any]]] = {}
    associated_paths: set[str] = set()
    try:
        for record, payload in parsed_records:
            if (
                record.ref.record_type != "file_record"
                or payload.get("snapshot_ref") != snapshot_ref
            ):
                continue
            record_id = payload.get("file_record_id")
            path = payload.get("path")
            entry_kind = payload.get("entry_kind")
            byte_size = payload.get("byte_size")
            identity_ref = payload.get("asset_identity_ref")
            if (
                payload.get("record_type") != "file_record"
                or type(record_id) is not str
                or record_id != record.ref.record_id
                or record_id in associated
                or type(path) is not str
                or not _safe_relative_posix_path(path)
                or path in associated_paths
                or type(entry_kind) is not str
                or entry_kind not in _ENTRY_KINDS
                or type(byte_size) is not int
                or byte_size < 0
                or not _is_record_ref_mapping(identity_ref, "asset_identity")
            ):
                _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)
            associated[record_id] = (record, payload)
            associated_paths.add(path)
        if not associated or not manifest_bytes or not manifest_bytes.endswith(b"\n"):
            _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)

        joined: list[tuple[FrozenBaseRecord, dict[str, Any]]] = []
        manifest_ids: set[str] = set()
        manifest_paths: set[str] = set()
        for encoded in manifest_bytes[:-1].split(b"\n"):
            if not encoded:
                _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)
            entry = _decode_canonical_object(encoded)
            record_id = entry.get("file_record_id")
            path = entry.get("path")
            if (
                entry.get("record_type") != "file_record"
                or entry.get("snapshot_ref") != snapshot_ref
                or type(record_id) is not str
                or record_id in manifest_ids
                or type(path) is not str
                or path in manifest_paths
            ):
                _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)
            match = associated.get(record_id)
            if match is None or match[0].canonical_payload != encoded:
                _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)
            manifest_ids.add(record_id)
            manifest_paths.add(path)
            joined.append(match)
        if manifest_ids != set(associated) or len(joined) != len(associated):
            _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)
        return tuple(joined)
    except (AttributeError, KeyError, TypeError, UnicodeError, ValueError, RecursionError):
        _refuse(SliceBPrimaryRefusal.MANIFEST_BIJECTION_INVALID)


def _selected_full_digest_identity(
    parsed_records: tuple[tuple[FrozenBaseRecord, dict[str, Any]], ...],
    joined_files: tuple[tuple[FrozenBaseRecord, dict[str, Any]], ...],
    *,
    file_record: FrozenBaseRecord,
    file_payload: dict[str, Any],
) -> tuple[FrozenBaseRecord, dict[str, Any]] | None:
    identity_ref = file_payload.get("asset_identity_ref")
    if not _is_record_ref_mapping(identity_ref, "asset_identity"):
        return None
    if (
        sum(payload.get("asset_identity_ref") == identity_ref for _record, payload in joined_files)
        != 1
    ):
        return None
    selected_ref = _record_ref_mapping(file_record.ref)
    claims: list[tuple[FrozenBaseRecord, dict[str, Any]]] = []
    referenced: list[tuple[FrozenBaseRecord, dict[str, Any]]] = []
    for record, payload in parsed_records:
        if record.ref.record_type != "asset_identity":
            continue
        if payload.get("asset_ref") == selected_ref:
            claims.append((record, payload))
        if _record_ref_mapping(record.ref) == identity_ref:
            referenced.append((record, payload))
    if len(claims) != 1 or len(referenced) != 1 or claims[0][0].ref != referenced[0][0].ref:
        return None
    record, payload = claims[0]
    evidence = payload.get("identity_evidence")
    if (
        payload.get("record_type") != "asset_identity"
        or payload.get("asset_identity_id") != record.ref.record_id
        or payload.get("tier") != "full_digest"
        or payload.get("asset_ref") != selected_ref
        or type(evidence) is not dict
        or set(evidence) != {"kind", "digest"}
        or evidence.get("kind") != "full_digest"
        or not _is_sha256(evidence.get("digest"))
    ):
        return None
    return record, payload


def _review_scope_selection_digest(
    *,
    context: ManifestBoundFrozenInspectionContext,
    snapshot_record: FrozenBaseRecord,
    snapshot_payload: dict[str, Any],
    manifest: FrozenFileManifestInput,
    file_record: FrozenBaseRecord,
    identity_record: FrozenBaseRecord,
    material: FrozenMaterialInput,
) -> str:
    try:
        extensions = snapshot_payload.get("extensions")
        if type(extensions) is not dict:
            return _UNRESOLVED_SCOPE
        paths = extensions.get("x-material-full-digest-paths")
        identities = extensions.get("x-material-input-identities")
        if (
            type(paths) is not list
            or not 1 <= len(paths) <= 8
            or any(type(path) is not str or not _safe_relative_posix_path(path) for path in paths)
            or paths != sorted(paths)
            or len(paths) != len(set(paths))
            or type(identities) is not list
        ):
            return _UNRESOLVED_SCOPE
        expected_identities = [{"path": path, "tier": "full_digest"} for path in paths]
        if identities != expected_identities or any(
            type(item) is not dict or set(item) != {"path", "tier"} for item in identities
        ):
            return _UNRESOLVED_SCOPE
        material_inputs = getattr(context, "material_inputs", None)
        if type(material_inputs) is not tuple or any(
            type(item) is not FrozenMaterialInput
            or type(getattr(item, "path", None)) is not str
            or not _safe_relative_posix_path(item.path)
            for item in material_inputs
        ):
            return _UNRESOLVED_SCOPE
        material_paths = [item.path for item in material_inputs]
        if material_paths != paths or material_paths.count(material.path) != 1:
            return _UNRESOLVED_SCOPE
        if (
            snapshot_payload.get("file_manifest_ref") != manifest.file_manifest_ref
            or sha256_digest(manifest.canonical_jsonl_bytes) != manifest.manifest_digest
        ):
            return _UNRESOLVED_SCOPE
        projection = {
            "profile": "slice-b-explicit-material-input-selection-v1",
            "snapshot_ref": _record_ref_mapping(snapshot_record.ref),
            "snapshot_payload_digest": sha256_digest(snapshot_record.canonical_payload),
            "file_manifest_ref": manifest.file_manifest_ref,
            "manifest_digest": manifest.manifest_digest,
            "selected_path": material.path,
            "selected_file_ref": _record_ref_mapping(file_record.ref),
            "selected_asset_identity_ref": _record_ref_mapping(identity_record.ref),
            "selected_content_digest": material.content_digest,
        }
        return sha256_digest(canonical_json(projection).encode("utf-8"))
    except (AttributeError, TypeError, UnicodeError, ValueError, RecursionError):
        return _UNRESOLVED_SCOPE


def _parse_primary_csv_bytes(content: bytes, request: CsvQuestionRequestV1) -> _CsvTable:
    if len(content) > _MAX_CSV_BYTES:
        _refuse(SliceBPrimaryRefusal.CSV_BYTE_BUDGET_EXCEEDED)
    if (
        not content
        or any(byte != 0x0A and not 0x20 <= byte <= 0x7E for byte in content)
        or b'"' in content
        or not content.endswith(b"\n")
    ):
        _refuse(SliceBPrimaryRefusal.CSV_BYTE_LANGUAGE_UNSUPPORTED)
    physical_lines = content[:-1].split(b"\n")
    if not physical_lines or any(not line for line in physical_lines):
        _refuse(SliceBPrimaryRefusal.CSV_BYTE_LANGUAGE_UNSUPPORTED)

    header = tuple(physical_lines[0].split(b","))
    if (
        not 2 <= len(header) <= _MAX_COLUMNS
        or any(not field or len(field) > _MAX_FIELD_BYTES for field in header)
        or len(header) != len(set(header))
    ):
        _refuse(SliceBPrimaryRefusal.CSV_HEADER_INVALID)
    data_lines = physical_lines[1:]
    if not data_lines:
        _refuse(SliceBPrimaryRefusal.CSV_SHAPE_INVALID)
    rows: list[tuple[bytes, ...]] = []
    for line in data_lines:
        row = tuple(line.split(b","))
        if len(row) != len(header) or any(
            not field or len(field) > _MAX_FIELD_BYTES for field in row
        ):
            _refuse(SliceBPrimaryRefusal.CSV_SHAPE_INVALID)
        rows.append(row)
    if len(rows) > _MAX_ROWS:
        _refuse(SliceBPrimaryRefusal.CSV_ROW_BUDGET_EXCEEDED)
    if request.candidate_unit_column_index >= len(header) or request.comparison_column_index >= len(
        header
    ):
        _refuse(SliceBPrimaryRefusal.COLUMN_ROLE_INVALID)
    return _CsvTable(header=header, rows=tuple(rows))


def _build_shape_observation(transaction: _PrimaryTransaction) -> SliceBObservationV1:
    projection = {
        **_common_observation_projection(
            transaction,
            observation_type="csv-table-shape-v1",
            verifier_id="slice-b-csv-shape-verifier-v1",
        ),
        "data_row_count": len(transaction.table.rows),
        "column_count": len(transaction.table.header),
    }
    return CsvTableShapeObservationV1(
        **projection,
        observation_id=sha256_digest(canonical_json(projection).encode("utf-8")),
    )


def _build_cardinality_observation(transaction: _PrimaryTransaction) -> SliceBObservationV1:
    request = transaction.request
    candidate_count = len(
        {row[request.candidate_unit_column_index] for row in transaction.table.rows}
    )
    comparison_count = len({row[request.comparison_column_index] for row in transaction.table.rows})
    projection = {
        **_common_observation_projection(
            transaction,
            observation_type="csv-selected-cardinalities-v1",
            verifier_id="slice-b-csv-cardinality-verifier-v1",
        ),
        "candidate_unit_column_index": request.candidate_unit_column_index,
        "comparison_column_index": request.comparison_column_index,
        "candidate_unit_distinct_count": candidate_count,
        "comparison_distinct_count": comparison_count,
    }
    return CsvSelectedCardinalitiesObservationV1(
        **projection,
        observation_id=sha256_digest(canonical_json(projection).encode("utf-8")),
    )


def _build_group_size_observation(transaction: _PrimaryTransaction) -> SliceBObservationV1:
    comparison_index = transaction.request.comparison_column_index
    sizes = tuple(sorted(Counter(row[comparison_index] for row in transaction.table.rows).values()))
    projection = {
        **_common_observation_projection(
            transaction,
            observation_type="csv-comparison-group-sizes-v1",
            verifier_id="slice-b-csv-group-size-verifier-v1",
        ),
        "comparison_column_index": comparison_index,
        "sorted_group_sizes": list(sizes),
    }
    return CsvComparisonGroupSizesObservationV1(
        **{key: value for key, value in projection.items() if key != "sorted_group_sizes"},
        sorted_group_sizes=sizes,
        observation_id=sha256_digest(canonical_json(projection).encode("utf-8")),
    )


def _build_incidence_observation(transaction: _PrimaryTransaction) -> SliceBObservationV1:
    candidate_index = transaction.request.candidate_unit_column_index
    comparison_index = transaction.request.comparison_column_index
    multiplicities: Counter[bytes] = Counter()
    comparisons: dict[bytes, set[bytes]] = {}
    for row in transaction.table.rows:
        candidate = row[candidate_index]
        multiplicities[candidate] += 1
        comparisons.setdefault(candidate, set()).add(row[comparison_index])
    repeated_count = sum(count > 1 for count in multiplicities.values())
    cross_count = sum(len(values) > 1 for values in comparisons.values())
    histogram_counts = Counter(len(values) for values in comparisons.values())
    histogram = tuple(sorted(histogram_counts.items()))
    projection = {
        **_common_observation_projection(
            transaction,
            observation_type="csv-unit-comparison-incidence-v1",
            verifier_id="slice-b-csv-incidence-verifier-v1",
        ),
        "candidate_unit_column_index": candidate_index,
        "comparison_column_index": comparison_index,
        "repeated_candidate_value_count": repeated_count,
        "cross_comparison_candidate_value_count": cross_count,
        "comparison_values_per_candidate_histogram": [list(pair) for pair in histogram],
    }
    return CsvUnitComparisonIncidenceObservationV1(
        **{
            key: value
            for key, value in projection.items()
            if key != "comparison_values_per_candidate_histogram"
        },
        comparison_values_per_candidate_histogram=histogram,
        observation_id=sha256_digest(canonical_json(projection).encode("utf-8")),
    )


def _common_observation_projection(
    transaction: _PrimaryTransaction,
    *,
    observation_type: str,
    verifier_id: str,
) -> dict[str, Any]:
    return {
        "observation_version": _OBSERVATION_VERSION,
        "observation_type": observation_type,
        "verifier_id": verifier_id,
        "snapshot_digest": transaction.snapshot_digest,
        "file_record_ref_digest": transaction.file_record_ref_digest,
        "content_digest": transaction.content_digest,
        "selected_file_ordinal": 1,
        "review_scope_selection_evidence_digest": (
            transaction.review_scope_selection_evidence_digest
        ),
        "finding_eligible": False,
    }


def _require_matching_observation_id(observation: SliceBObservationV1) -> None:
    projection = observation.to_dict()
    claimed = projection.pop("observation_id", None)
    if not _is_sha256(claimed) or claimed != sha256_digest(
        canonical_json(projection).encode("utf-8")
    ):
        raise SliceBContractError("observation id does not match its canonical preimage")


def _require_request(request: object) -> None:
    if type(request) is not CsvQuestionRequestV1:
        raise SliceBContractError("request must be the exact closed Slice-B request type")
    if (
        type(request.request_version) is not str
        or request.request_version != _REQUEST_VERSION
        or type(request.selected_path) is not str
        or not _safe_relative_posix_path(
            request.selected_path,
            ascii_only=True,
            max_bytes=_MAX_PATH_BYTES,
        )
    ):
        raise SliceBContractError("request version or selected path is invalid")
    _require_distinct_column_indices(
        request.candidate_unit_column_index,
        request.comparison_column_index,
    )


def _require_distinct_column_indices(candidate: object, comparison: object) -> None:
    if (
        not _bounded_int(candidate, 0, _MAX_COLUMNS - 1)
        or not _bounded_int(comparison, 0, _MAX_COLUMNS - 1)
        or candidate == comparison
    ):
        raise SliceBContractError("selected column roles must be distinct bounded integers")


def _decode_canonical_object(payload: bytes) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-JSON numeric constant {value}")

    value = json.loads(payload.decode("utf-8", errors="strict"), parse_constant=reject_constant)
    if type(value) is not dict or canonical_json(value).encode("utf-8") != payload:
        raise ValueError("payload is not one canonical JSON object")
    return value


def _record_ref_mapping(ref: RecordRef) -> dict[str, str]:
    if type(ref) is not RecordRef:
        raise ValueError("record reference type is invalid")
    record_type = getattr(ref, "record_type", None)
    record_id = getattr(ref, "record_id", None)
    if (
        type(record_type) is not str
        or not record_type
        or record_type.strip() != record_type
        or any(character.isspace() for character in record_type)
        or type(record_id) is not str
        or not record_id
        or record_id.strip() != record_id
        or any(character.isspace() for character in record_id)
    ):
        raise ValueError("record reference value is invalid")
    return {"record_type": record_type, "record_id": record_id}


def _record_ref_key(ref: RecordRef) -> tuple[str, str]:
    value = _record_ref_mapping(ref)
    return value["record_type"], value["record_id"]


def _same_record_ref(value: object, expected: RecordRef) -> bool:
    if type(value) is not RecordRef:
        return False
    try:
        return _record_ref_mapping(value) == _record_ref_mapping(expected)
    except ValueError:
        return False


def _is_record_ref_mapping(value: object, record_type: str) -> TypeGuard[dict[str, str]]:
    return (
        type(value) is dict
        and set(value) == {"record_type", "record_id"}
        and value.get("record_type") == record_type
        and type(value.get("record_id")) is str
        and bool(value["record_id"])
        and not any(character.isspace() for character in value["record_id"])
    )


def _safe_relative_posix_path(
    value: str,
    *,
    ascii_only: bool = False,
    max_bytes: int | None = None,
) -> bool:
    if type(value) is not str or not value:
        return False
    try:
        encoded = value.encode("ascii" if ascii_only else "utf-8")
    except UnicodeEncodeError:
        return False
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value) or (
        max_bytes is not None and len(encoded) > max_bytes
    ):
        return False
    candidate = PurePosixPath(value)
    return (
        not candidate.is_absolute()
        and candidate.as_posix() == value
        and value != "."
        and all(part not in {"", ".", ".."} for part in candidate.parts)
    )


def _is_sha256(value: object) -> TypeGuard[str]:
    return (
        type(value) is str
        and len(value) == 71
        and value.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in value[7:])
    )


def _bounded_int(value: object, lower: int, upper: int) -> TypeGuard[int]:
    return type(value) is int and lower <= value <= upper


def _refuse(refusal: SliceBPrimaryRefusal) -> NoReturn:
    raise _PrimaryRefusalError(refusal)
