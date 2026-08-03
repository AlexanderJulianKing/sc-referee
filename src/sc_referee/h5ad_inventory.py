from __future__ import annotations

import io
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Literal

import h5py  # type: ignore[import-untyped]
import numpy as np

from sc_referee.core.ids import sha256_digest, stable_id
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.scientific_checks import RecordRef
from sc_referee.snapshot.identity import build_asset_identity, full_digest_evidence
from sc_referee.snapshot.repository import SnapshotOutput
from sc_referee.version import SCHEMA_VERSION

MAX_H5AD_FIELDS = 64
MAX_H5AD_AXIS_ITEMS = 2_000_000
MAX_H5AD_MATRIX_ELEMENTS = 2_000_000
MAX_H5AD_MATRIX_BYTES = 16 * 1024 * 1024
MAX_H5AD_TEXT_BYTES = 2 * 1024 * 1024
MAX_H5AD_LOGICAL_READ_BYTES = 64 * 1024 * 1024
MAX_H5AD_READ_CHUNK_BYTES = 1024 * 1024
MAX_H5AD_SPARSE_STORED_VALUES = 8_000_000
MAX_H5AD_UNIQUENESS_ITEMS = 100_000
MAX_H5AD_STRING_CHUNK_ITEMS = 4_096
_ALLOWED_COMPRESSIONS = {None, "gzip", "lzf", "szip"}


class H5ADInspectionError(ValueError):
    """Raised when a selected H5AD escapes the bounded structural profile."""


@dataclass(frozen=True)
class H5ADStructure:
    path: str
    artifact_ref: RecordRef
    source_ref: dict[str, Any]
    content_digest: str
    matrix_path: str
    shape: tuple[int, int]
    matrix_storage: str
    matrix_dtype: str
    matrix_nonnegative: bool
    matrix_integer_valued: bool
    matrix_sum: int
    matrix_stored_values: int
    logical_bytes_read: int
    read_chunks: int
    obs_fields: tuple[str, ...]
    obs_index: str
    observation_index_unique: bool | None
    var_index: str
    feature_index_unique: bool | None
    field_storage: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class H5ADReadReceipt:
    path: str
    content_digest: str
    status: Literal["inspected", "unsupported"]
    raw_file_bytes: int
    logical_bytes_read: int
    read_chunks: int
    logical_byte_ceiling: int
    chunk_byte_ceiling: int
    termination_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "content_digest": self.content_digest,
            "status": self.status,
            "raw_file_bytes": self.raw_file_bytes,
            "logical_bytes_read": self.logical_bytes_read,
            "read_chunks": self.read_chunks,
            "logical_byte_ceiling": self.logical_byte_ceiling,
            "chunk_byte_ceiling": self.chunk_byte_ceiling,
            "termination_reason": self.termination_reason,
        }


@dataclass
class _ReadMeter:
    checkpoint: Callable[[], None] | None
    logical_bytes_read: int = 0
    read_chunks: int = 0

    def before_read(self) -> None:
        if self.checkpoint is not None:
            self.checkpoint()

    def record(self, byte_count: int) -> None:
        if byte_count < 0 or byte_count > MAX_H5AD_READ_CHUNK_BYTES:
            raise H5ADInspectionError("H5AD read escaped the chunk-byte ceiling")
        if self.logical_bytes_read + byte_count > MAX_H5AD_LOGICAL_READ_BYTES:
            raise H5ADInspectionError("H5AD logical reads exceed the decompressed-byte ceiling")
        self.logical_bytes_read += byte_count
        self.read_chunks += 1


@dataclass(frozen=True)
class H5ADInventoryOutput:
    artifacts: list[dict[str, Any]]
    asset_identities: list[dict[str, Any]]
    data_assets: list[dict[str, Any]]
    variables: list[dict[str, Any]]
    structures: tuple[H5ADStructure, ...]
    inspected_paths: tuple[str, ...]
    unavailable_paths: tuple[str, ...]
    unsupported_paths: tuple[str, ...]
    ambiguous_artifact_paths: tuple[str, ...]
    read_receipts: tuple[H5ADReadReceipt, ...]


def inspect_h5ad_inventory(
    snapshot: SnapshotOutput,
    existing_artifacts: list[dict[str, Any]],
    run_id: str,
    created_at: str,
    *,
    read_checkpoint: Callable[[], None] | None = None,
) -> H5ADInventoryOutput:
    """Inspect only explicitly selected, fully identified H5AD material inputs."""

    selected_paths = _selected_h5ad_paths(snapshot)
    files_by_path = {
        str(record["path"]): record
        for record in snapshot.file_records
        if record.get("entry_kind") == "regular_file"
    }
    identities_by_file_id = {
        str(record.get("asset_ref", {}).get("record_id")): record
        for record in snapshot.asset_identity_records
        if record.get("asset_ref", {}).get("record_type") == "file_record"
    }
    artifacts_by_path: dict[str, list[dict[str, Any]]] = {}
    for artifact in existing_artifacts:
        path = artifact.get("path")
        if isinstance(path, str):
            artifacts_by_path.setdefault(path, []).append(artifact)

    artifacts: list[dict[str, Any]] = []
    asset_identities: list[dict[str, Any]] = []
    data_assets: list[dict[str, Any]] = []
    variables: list[dict[str, Any]] = []
    structures: list[H5ADStructure] = []
    inspected: list[str] = []
    unavailable: list[str] = []
    unsupported: list[str] = []
    ambiguous: list[str] = []
    read_receipts: list[H5ADReadReceipt] = []

    for path in selected_paths:
        file_record = files_by_path.get(path)
        identity = (
            identities_by_file_id.get(str(file_record["file_id"]))
            if file_record is not None
            else None
        )
        digest = (
            identity.get("identity_evidence", {}).get("digest")
            if isinstance(identity, dict) and identity.get("tier") == "full_digest"
            else None
        )
        materialized = snapshot.materialized_root / path
        if (
            file_record is None
            or not isinstance(digest, str)
            or not materialized.is_file()
            or materialized.is_symlink()
        ):
            unavailable.append(path)
            continue
        if read_checkpoint is not None:
            read_checkpoint()
        try:
            payload = materialized.read_bytes()
        except OSError:
            unavailable.append(path)
            continue
        if sha256_digest(payload) != digest:
            unavailable.append(path)
            continue
        matches = artifacts_by_path.get(path, [])
        if len(matches) > 1:
            ambiguous.append(path)
            continue
        source_ref = _source_ref(path, digest)
        meter = _ReadMeter(read_checkpoint)
        try:
            raw_structure = _inspect_h5ad(payload, path, digest, source_ref, meter)
        except (H5ADInspectionError, OSError, ValueError):
            unsupported.append(path)
            read_receipts.append(
                H5ADReadReceipt(
                    path=path,
                    content_digest=digest,
                    status="unsupported",
                    raw_file_bytes=len(payload),
                    logical_bytes_read=meter.logical_bytes_read,
                    read_chunks=meter.read_chunks,
                    logical_byte_ceiling=MAX_H5AD_LOGICAL_READ_BYTES,
                    chunk_byte_ceiling=MAX_H5AD_READ_CHUNK_BYTES,
                    termination_reason="unsupported_layout_or_budget",
                )
            )
            continue

        if matches:
            artifact = matches[0]
        else:
            artifact, artifact_identity = _inventoried_h5ad_artifact(
                path,
                digest,
                source_ref,
                run_id,
                created_at,
            )
            artifacts.append(artifact)
            asset_identities.append(artifact_identity)
        structure = H5ADStructure(
            artifact_ref=RecordRef("artifact", str(artifact["artifact_id"])),
            **raw_structure,
        )
        data_asset, h5ad_variables = _public_records(
            structure,
            artifact,
            run_id,
            created_at,
        )
        structures.append(structure)
        data_assets.append(data_asset)
        variables.extend(h5ad_variables)
        inspected.append(path)
        read_receipts.append(
            H5ADReadReceipt(
                path=path,
                content_digest=digest,
                status="inspected",
                raw_file_bytes=len(payload),
                logical_bytes_read=meter.logical_bytes_read,
                read_chunks=meter.read_chunks,
                logical_byte_ceiling=MAX_H5AD_LOGICAL_READ_BYTES,
                chunk_byte_ceiling=MAX_H5AD_READ_CHUNK_BYTES,
                termination_reason=None,
            )
        )

    return H5ADInventoryOutput(
        artifacts=sorted(artifacts, key=lambda item: str(item["artifact_id"])),
        asset_identities=sorted(asset_identities, key=lambda item: str(item["asset_identity_id"])),
        data_assets=sorted(data_assets, key=lambda item: str(item["data_asset_id"])),
        variables=sorted(variables, key=lambda item: str(item["variable_id"])),
        structures=tuple(sorted(structures, key=lambda item: item.path)),
        inspected_paths=tuple(sorted(inspected)),
        unavailable_paths=tuple(sorted(unavailable)),
        unsupported_paths=tuple(sorted(unsupported)),
        ambiguous_artifact_paths=tuple(sorted(ambiguous)),
        read_receipts=tuple(sorted(read_receipts, key=lambda item: item.path)),
    )


def _selected_h5ad_paths(snapshot: SnapshotOutput) -> tuple[str, ...]:
    values = snapshot.snapshot_record.get("extensions", {}).get("x-material-full-digest-paths", [])
    return tuple(
        sorted(
            value
            for value in values
            if isinstance(value, str) and PurePosixPath(value).suffix.casefold() == ".h5ad"
        )
    )


def _inspect_h5ad(
    payload: bytes,
    path: str,
    digest: str,
    source_ref: dict[str, Any],
    meter: _ReadMeter,
) -> dict[str, Any]:
    try:
        handle = h5py.File(io.BytesIO(payload), "r")
    except (OSError, ValueError) as error:
        raise H5ADInspectionError("selected file is not a readable HDF5 container") from error
    with handle:
        if _attribute_text(handle.attrs.get("encoding-type")) != "anndata":
            raise H5ADInspectionError("root encoding-type is not anndata")
        matrix = _hard_object(handle, "X", (h5py.Dataset, h5py.Group))
        matrix_info = _inspect_matrix(matrix, meter)
        n_obs, n_vars = matrix_info["shape"]

        obs = _hard_object(handle, "obs", h5py.Group)
        var = _hard_object(handle, "var", h5py.Group)
        if _attribute_text(obs.attrs.get("encoding-type")) != "dataframe":
            raise H5ADInspectionError("obs is not an AnnData dataframe encoding")
        if _attribute_text(var.attrs.get("encoding-type")) != "dataframe":
            raise H5ADInspectionError("var is not an AnnData dataframe encoding")
        obs_index = _attribute_text(obs.attrs.get("_index"))
        var_index = _attribute_text(var.attrs.get("_index"))
        if not obs_index or not var_index:
            raise H5ADInspectionError("obs or var index declaration is unavailable")
        if len(obs) > MAX_H5AD_FIELDS or len(var) > MAX_H5AD_FIELDS:
            raise H5ADInspectionError("axis metadata exceeds the field ceiling")

        field_storage: list[tuple[str, str]] = []
        obs_fields: list[str] = []
        observation_index_unique: bool | None = None
        for name in sorted(obs.keys()):
            storage, unique = _inspect_axis_field(
                obs,
                name,
                n_obs,
                meter,
                check_uniqueness=name == obs_index,
            )
            field_storage.append((f"obs/{name}", storage))
            obs_fields.append(name)
            if name == obs_index:
                observation_index_unique = unique
        if obs_index not in obs_fields:
            raise H5ADInspectionError("declared obs index is not present")

        feature_storage, feature_index_unique = _inspect_axis_field(
            var,
            var_index,
            n_vars,
            meter,
            check_uniqueness=True,
        )
        field_storage.append((f"var/{var_index}", feature_storage))

    return {
        "path": path,
        "source_ref": source_ref,
        "content_digest": digest,
        "matrix_path": "X",
        **matrix_info,
        "logical_bytes_read": meter.logical_bytes_read,
        "read_chunks": meter.read_chunks,
        "obs_fields": tuple(obs_fields),
        "obs_index": obs_index,
        "observation_index_unique": observation_index_unique,
        "var_index": var_index,
        "feature_index_unique": feature_index_unique,
        "field_storage": tuple(field_storage),
    }


def _inspect_matrix(matrix: Any, meter: _ReadMeter) -> dict[str, Any]:
    if isinstance(matrix, h5py.Dataset):
        return _inspect_dense_matrix(matrix, meter)
    if not isinstance(matrix, h5py.Group):
        raise H5ADInspectionError("X has an unsupported HDF5 object type")
    return _inspect_sparse_matrix(matrix, meter)


def _inspect_dense_matrix(matrix: h5py.Dataset, meter: _ReadMeter) -> dict[str, Any]:
    if len(matrix.shape) != 2:
        raise H5ADInspectionError("X is not two-dimensional")
    n_obs, n_vars = (int(matrix.shape[0]), int(matrix.shape[1]))
    if (
        n_obs < 1
        or n_vars < 1
        or n_obs > MAX_H5AD_AXIS_ITEMS
        or n_vars > MAX_H5AD_AXIS_ITEMS
        or n_obs * n_vars > MAX_H5AD_MATRIX_ELEMENTS
        or int(matrix.nbytes) > MAX_H5AD_MATRIX_BYTES
    ):
        raise H5ADInspectionError("X exceeds the bounded dense-matrix profile")
    if matrix.dtype.kind not in {"i", "u"}:
        raise H5ADInspectionError("X is not stored as a dense integer array")
    _require_supported_dataset(matrix, "X")

    matrix_nonnegative = True
    matrix_sum = 0
    columns_per_chunk = max(
        1,
        min(n_vars, MAX_H5AD_READ_CHUNK_BYTES // max(1, matrix.dtype.itemsize)),
    )
    rows_per_chunk = max(
        1,
        min(
            n_obs,
            MAX_H5AD_READ_CHUNK_BYTES // max(1, columns_per_chunk * matrix.dtype.itemsize),
        ),
    )
    for row_start in range(0, n_obs, rows_per_chunk):
        row_stop = min(n_obs, row_start + rows_per_chunk)
        for column_start in range(0, n_vars, columns_per_chunk):
            column_stop = min(n_vars, column_start + columns_per_chunk)
            meter.before_read()
            block = np.asarray(matrix[row_start:row_stop, column_start:column_stop])
            expected = (row_stop - row_start, column_stop - column_start)
            if block.shape != expected:
                raise H5ADInspectionError("X returned an inconsistent bounded slice")
            meter.record(int(block.nbytes))
            if bool(np.any(block < 0)):
                matrix_nonnegative = False
            matrix_sum += sum(int(value) for value in block.flat)
    return {
        "shape": (n_obs, n_vars),
        "matrix_storage": "dense",
        "matrix_dtype": str(matrix.dtype),
        "matrix_nonnegative": matrix_nonnegative,
        "matrix_integer_valued": True,
        "matrix_sum": matrix_sum,
        "matrix_stored_values": n_obs * n_vars,
    }


def _inspect_sparse_matrix(matrix: h5py.Group, meter: _ReadMeter) -> dict[str, Any]:
    storage = _attribute_text(matrix.attrs.get("encoding-type"))
    if storage not in {"csr_matrix", "csc_matrix"}:
        raise H5ADInspectionError("X sparse encoding is unsupported")
    shape = _sparse_shape(matrix.attrs.get("shape"))
    n_obs, n_vars = shape
    if n_obs < 1 or n_vars < 1 or n_obs > MAX_H5AD_AXIS_ITEMS or n_vars > MAX_H5AD_AXIS_ITEMS:
        raise H5ADInspectionError("X exceeds the bounded sparse-axis profile")
    data = _hard_object(matrix, "data", h5py.Dataset)
    indices = _hard_object(matrix, "indices", h5py.Dataset)
    indptr = _hard_object(matrix, "indptr", h5py.Dataset)
    for name, dataset in (("data", data), ("indices", indices), ("indptr", indptr)):
        if len(dataset.shape) != 1 or dataset.dtype.kind not in {"i", "u"}:
            raise H5ADInspectionError(f"X sparse {name} is not one integer vector")
        _require_supported_dataset(dataset, f"X/{name}")
    nnz = int(data.shape[0])
    if int(indices.shape[0]) != nnz or nnz > MAX_H5AD_SPARSE_STORED_VALUES:
        raise H5ADInspectionError("X sparse stored-value arrays are inconsistent or over budget")
    major = n_obs if storage == "csr_matrix" else n_vars
    minor = n_vars if storage == "csr_matrix" else n_obs
    if int(indptr.shape[0]) != major + 1:
        raise H5ADInspectionError("X sparse pointer length does not match its shape")
    logical_size = int(data.nbytes) + int(indices.nbytes) + int(indptr.nbytes)
    if logical_size > MAX_H5AD_LOGICAL_READ_BYTES:
        raise H5ADInspectionError("X sparse arrays exceed the decompressed-byte ceiling")

    matrix_nonnegative = True
    matrix_sum = 0
    for block in _numeric_chunks(data, meter):
        if bool(np.any(block < 0)):
            matrix_nonnegative = False
        matrix_sum += sum(int(value) for value in block.flat)
    for block in _numeric_chunks(indices, meter):
        if block.size and (int(block.min()) < 0 or int(block.max()) >= minor):
            raise H5ADInspectionError("X sparse indices fall outside the minor axis")
    previous: int | None = None
    pointer_count = 0
    for block in _numeric_chunks(indptr, meter):
        for raw_value in block.flat:
            value = int(raw_value)
            if value < 0 or value > nnz or (previous is not None and value < previous):
                raise H5ADInspectionError("X sparse pointers are invalid or nonmonotonic")
            if pointer_count == 0 and value != 0:
                raise H5ADInspectionError("X sparse pointers must start at zero")
            previous = value
            pointer_count += 1
    if previous != nnz:
        raise H5ADInspectionError("X sparse pointers do not terminate at stored-value count")
    return {
        "shape": shape,
        "matrix_storage": "csr" if storage == "csr_matrix" else "csc",
        "matrix_dtype": str(data.dtype),
        "matrix_nonnegative": matrix_nonnegative,
        "matrix_integer_valued": True,
        "matrix_sum": matrix_sum,
        "matrix_stored_values": nnz,
    }


def _sparse_shape(value: Any) -> tuple[int, int]:
    raw = np.asarray(value)
    if raw.shape != (2,) or raw.dtype.kind not in {"i", "u"}:
        raise H5ADInspectionError("X sparse shape must be exactly two integers")
    return int(raw[0]), int(raw[1])


def _require_supported_dataset(dataset: h5py.Dataset, label: str) -> None:
    if dataset.is_virtual or dataset.compression not in _ALLOWED_COMPRESSIONS:
        raise H5ADInspectionError(f"{label} uses an unsupported virtual or compressed layout")


def _numeric_chunks(dataset: h5py.Dataset, meter: _ReadMeter) -> Any:
    items_per_chunk = max(
        1,
        MAX_H5AD_READ_CHUNK_BYTES // max(1, dataset.dtype.itemsize),
    )
    for start in range(0, int(dataset.shape[0]), items_per_chunk):
        stop = min(int(dataset.shape[0]), start + items_per_chunk)
        meter.before_read()
        block = np.asarray(dataset[start:stop])
        if block.shape != (stop - start,):
            raise H5ADInspectionError("H5AD numeric vector returned an inconsistent slice")
        meter.record(int(block.nbytes))
        yield block


def _hard_object(
    parent: h5py.Group | h5py.File,
    name: str,
    expected_type: type[Any] | tuple[type[Any], ...],
) -> Any:
    link = parent.get(name, getlink=True)
    if not isinstance(link, h5py.HardLink):
        raise H5ADInspectionError(f"{name} is missing or is not a hard HDF5 link")
    value = parent.get(name)
    if not isinstance(value, expected_type):
        raise H5ADInspectionError(f"{name} has an unsupported HDF5 object type")
    return value


def _inspect_axis_field(
    parent: h5py.Group,
    name: str,
    length: int,
    meter: _ReadMeter,
    *,
    check_uniqueness: bool,
) -> tuple[str, bool | None]:
    value = _hard_object(parent, name, (h5py.Group, h5py.Dataset))
    if isinstance(value, h5py.Dataset):
        return "string", _read_string_dataset(
            value,
            length,
            meter,
            check_uniqueness=check_uniqueness,
        )
    if _attribute_text(value.attrs.get("encoding-type")) != "categorical":
        raise H5ADInspectionError(f"axis field {name!r} is not string or categorical")
    categories = _hard_object(value, "categories", h5py.Dataset)
    codes = _hard_object(value, "codes", h5py.Dataset)
    category_values = _collect_string_dataset(categories, int(categories.shape[0]), meter)
    if len(set(category_values)) != len(category_values):
        raise H5ADInspectionError(f"categorical field {name!r} has duplicate categories")
    if len(codes.shape) != 1 or int(codes.shape[0]) != length or codes.dtype.kind not in {"i", "u"}:
        raise H5ADInspectionError(f"categorical field {name!r} has invalid codes")
    _require_supported_dataset(codes, f"axis field {name!r} codes")
    uniqueness = _UniquenessTracker(check_uniqueness)
    for code_values in _numeric_chunks(codes, meter):
        if code_values.size and (
            int(code_values.min()) < -1 or int(code_values.max()) >= len(category_values)
        ):
            raise H5ADInspectionError(f"categorical field {name!r} has out-of-range codes")
        if check_uniqueness:
            for code in code_values.flat:
                uniqueness.observe(int(code))
    return "categorical", uniqueness.result()


@dataclass
class _UniquenessTracker:
    enabled: bool
    seen: set[Any] | None = None
    duplicate: bool = False

    def __post_init__(self) -> None:
        if self.enabled:
            self.seen = set()

    def observe(self, value: Any) -> None:
        if not self.enabled or self.duplicate or self.seen is None:
            return
        if value in self.seen:
            self.duplicate = True
            return
        self.seen.add(value)
        if len(self.seen) > MAX_H5AD_UNIQUENESS_ITEMS:
            self.seen = None

    def result(self) -> bool | None:
        if not self.enabled:
            return None
        if self.duplicate:
            return False
        return self.seen is not None


def _read_string_dataset(
    dataset: h5py.Dataset,
    length: int,
    meter: _ReadMeter,
    *,
    check_uniqueness: bool,
) -> bool | None:
    if len(dataset.shape) != 1 or int(dataset.shape[0]) != length:
        raise H5ADInspectionError("axis string field has an inconsistent shape")
    if length > MAX_H5AD_AXIS_ITEMS:
        raise H5ADInspectionError("axis string field exceeds the item ceiling")
    _require_supported_dataset(dataset, "axis string field")
    uniqueness = _UniquenessTracker(check_uniqueness)
    text_bytes = 0
    for start in range(0, length, MAX_H5AD_STRING_CHUNK_ITEMS):
        stop = min(length, start + MAX_H5AD_STRING_CHUNK_ITEMS)
        meter.before_read()
        try:
            raw = dataset.asstr(encoding="utf-8", errors="strict")[start:stop]
        except (OSError, TypeError, UnicodeError) as error:
            raise H5ADInspectionError("axis string field is not strict UTF-8") from error
        values = tuple(str(item) for item in np.asarray(raw).tolist())
        if len(values) != stop - start or any(not item for item in values):
            raise H5ADInspectionError("axis string field contains an empty identifier")
        chunk_bytes = sum(len(item.encode("utf-8")) for item in values)
        text_bytes += chunk_bytes
        if text_bytes > MAX_H5AD_TEXT_BYTES:
            raise H5ADInspectionError("axis string values exceed the text ceiling")
        meter.record(chunk_bytes)
        for item in values:
            uniqueness.observe(item)
    return uniqueness.result()


def _collect_string_dataset(
    dataset: h5py.Dataset,
    length: int,
    meter: _ReadMeter,
) -> tuple[str, ...]:
    if length > MAX_H5AD_UNIQUENESS_ITEMS:
        raise H5ADInspectionError("categorical dictionary exceeds the item ceiling")
    values: list[str] = []
    if len(dataset.shape) != 1 or int(dataset.shape[0]) != length:
        raise H5ADInspectionError("categorical dictionary has an inconsistent shape")
    _require_supported_dataset(dataset, "categorical dictionary")
    text_bytes = 0
    for start in range(0, length, MAX_H5AD_STRING_CHUNK_ITEMS):
        stop = min(length, start + MAX_H5AD_STRING_CHUNK_ITEMS)
        meter.before_read()
        try:
            raw = dataset.asstr(encoding="utf-8", errors="strict")[start:stop]
        except (OSError, TypeError, UnicodeError) as error:
            raise H5ADInspectionError("categorical dictionary is not strict UTF-8") from error
        chunk = tuple(str(item) for item in np.asarray(raw).tolist())
        if len(chunk) != stop - start or any(not item for item in chunk):
            raise H5ADInspectionError("categorical dictionary contains an empty value")
        chunk_bytes = sum(len(item.encode("utf-8")) for item in chunk)
        text_bytes += chunk_bytes
        if text_bytes > MAX_H5AD_TEXT_BYTES:
            raise H5ADInspectionError("categorical dictionary exceeds the text ceiling")
        meter.record(chunk_bytes)
        values.extend(chunk)
    return tuple(values)


def _attribute_text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="strict")
    return str(value) if isinstance(value, str) else ""


def _source_ref(path: str, digest: str, *, fragment: str | None = None) -> dict[str, Any]:
    locator = path if fragment is None else f"{path}#/{fragment.lstrip('/')}"
    return {
        "source_kind": "artifact",
        "locator": locator,
        "path": path,
        "content_digest": digest,
    }


def _inventoried_h5ad_artifact(
    path: str,
    digest: str,
    source_ref: dict[str, Any],
    run_id: str,
    created_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    artifact_id = stable_id("artifact", path, digest)
    identity = build_asset_identity(
        audit_run_id=run_id,
        asset_record_type="artifact",
        asset_record_id=artifact_id,
        evidence=full_digest_evidence(digest),
        created_at=created_at,
    )
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "artifact",
        "artifact_id": artifact_id,
        "audit_run_id": run_id,
        "kind": "data_file",
        "observed_role": "inventoried_explicit_h5ad_material_input",
        "path": path,
        "source_refs": [deepcopy(source_ref)],
        "producer_operation_refs": [],
        "consumer_operation_refs": [],
        "asset_identity_ref": typed_ref("asset_identity", str(identity["asset_identity_id"])),
        "limitations": [
            "Caller selection and H5AD syntax do not establish scientific role, analysis use, "
            "experimental unit, or biological meaning."
        ],
        "provenance": controller_provenance("bounded_h5ad_material_inventory", created_at),
    }
    return artifact, identity


def _public_records(
    structure: H5ADStructure,
    artifact: dict[str, Any],
    run_id: str,
    created_at: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data_asset_id = stable_id(
        "data-asset",
        run_id,
        str(artifact["artifact_id"]),
        structure.content_digest,
    )
    variables: list[dict[str, Any]] = []
    for observed_name, storage_type in structure.field_storage:
        fragment = observed_name
        source_ref = _source_ref(structure.path, structure.content_digest, fragment=fragment)
        variables.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "variable",
                "variable_id": stable_id("variable", data_asset_id, observed_name),
                "audit_run_id": run_id,
                "data_asset_ref": typed_ref("data_asset", data_asset_id),
                "observed_name": observed_name,
                "storage_type": storage_type,
                "scientific_meaning_status": "unresolved",
                "semantic_assertion_refs": [],
                "source_refs": [source_ref],
                "limitations": [
                    "The stored H5AD field name and encoding do not establish its scientific "
                    "meaning, unit, role, or use in a reported analysis."
                ],
                "provenance": controller_provenance("bounded_h5ad_material_inventory", created_at),
            }
        )
    limitations: list[str] = []
    structure_status = "complete"
    if structure.observation_index_unique is False:
        structure_status = "partial"
        limitations.append(
            "The inspected observation index is not unique; cell or sample binding is incomplete."
        )
    elif structure.observation_index_unique is None:
        structure_status = "partial"
        limitations.append(
            "Observation-index uniqueness exceeded the exact uniqueness-check budget."
        )
    if structure.feature_index_unique is False:
        structure_status = "partial"
        limitations.append(
            "The inspected feature index is not unique; feature-level binding is incomplete."
        )
    elif structure.feature_index_unique is None:
        structure_status = "partial"
        limitations.append("Feature-index uniqueness exceeded the exact uniqueness-check budget.")
    data_asset = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "data_asset",
        "data_asset_id": data_asset_id,
        "audit_run_id": run_id,
        "artifact_ref": typed_ref("artifact", str(artifact["artifact_id"])),
        "asset_identity_ref": deepcopy(artifact["asset_identity_ref"]),
        "role": "unknown",
        "format": "matrix",
        "path": structure.path,
        "structure_status": structure_status,
        "variable_refs": [typed_ref("variable", str(item["variable_id"])) for item in variables],
        "source_refs": [deepcopy(structure.source_ref)],
        "limitations": limitations,
        "provenance": controller_provenance("bounded_h5ad_material_inventory", created_at),
    }
    return data_asset, variables
