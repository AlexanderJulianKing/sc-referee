from __future__ import annotations

import io
from copy import deepcopy
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

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
    obs_fields: tuple[str, ...]
    obs_index: str
    var_index: str
    feature_index_unique: bool
    field_storage: tuple[tuple[str, str], ...]


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


def inspect_h5ad_inventory(
    snapshot: SnapshotOutput,
    existing_artifacts: list[dict[str, Any]],
    run_id: str,
    created_at: str,
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
        try:
            raw_structure = _inspect_h5ad(payload, path, digest, source_ref)
        except (H5ADInspectionError, OSError, ValueError):
            unsupported.append(path)
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
) -> dict[str, Any]:
    try:
        handle = h5py.File(io.BytesIO(payload), "r")
    except (OSError, ValueError) as error:
        raise H5ADInspectionError("selected file is not a readable HDF5 container") from error
    with handle:
        if _attribute_text(handle.attrs.get("encoding-type")) != "anndata":
            raise H5ADInspectionError("root encoding-type is not anndata")
        matrix = _hard_object(handle, "X", h5py.Dataset)
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
        if matrix.is_virtual or matrix.compression not in _ALLOWED_COMPRESSIONS:
            raise H5ADInspectionError("X uses an unsupported virtual or compressed layout")

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
        for name in sorted(obs.keys()):
            storage = _inspect_axis_field(obs, name, n_obs)
            field_storage.append((f"obs/{name}", storage))
            obs_fields.append(name)
        if obs_index not in obs_fields:
            raise H5ADInspectionError("declared obs index is not present")

        feature_values, feature_storage = _read_axis_strings(var, var_index, n_vars)
        field_storage.append((f"var/{var_index}", feature_storage))
        feature_index_unique = len(set(feature_values)) == len(feature_values)

        matrix_nonnegative = True
        matrix_sum = 0
        rows_per_chunk = max(1, min(n_obs, 1_048_576 // max(1, n_vars * matrix.dtype.itemsize)))
        for start in range(0, n_obs, rows_per_chunk):
            block = np.asarray(matrix[start : min(n_obs, start + rows_per_chunk), :])
            if block.shape != (min(rows_per_chunk, n_obs - start), n_vars):
                raise H5ADInspectionError("X returned an inconsistent bounded slice")
            if bool(np.any(block < 0)):
                matrix_nonnegative = False
            matrix_sum += int(block.sum(dtype=object))

    return {
        "path": path,
        "source_ref": source_ref,
        "content_digest": digest,
        "matrix_path": "X",
        "shape": (n_obs, n_vars),
        "matrix_storage": "dense",
        "matrix_dtype": str(matrix.dtype),
        "matrix_nonnegative": matrix_nonnegative,
        "matrix_integer_valued": True,
        "matrix_sum": matrix_sum,
        "obs_fields": tuple(obs_fields),
        "obs_index": obs_index,
        "var_index": var_index,
        "feature_index_unique": feature_index_unique,
        "field_storage": tuple(field_storage),
    }


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


def _inspect_axis_field(parent: h5py.Group, name: str, length: int) -> str:
    value = _hard_object(parent, name, (h5py.Group, h5py.Dataset))
    if isinstance(value, h5py.Dataset):
        _read_string_dataset(value, length)
        return "string"
    if _attribute_text(value.attrs.get("encoding-type")) != "categorical":
        raise H5ADInspectionError(f"axis field {name!r} is not string or categorical")
    categories = _hard_object(value, "categories", h5py.Dataset)
    codes = _hard_object(value, "codes", h5py.Dataset)
    category_values = _read_string_dataset(categories, int(categories.shape[0]))
    if len(codes.shape) != 1 or int(codes.shape[0]) != length or codes.dtype.kind not in {"i", "u"}:
        raise H5ADInspectionError(f"categorical field {name!r} has invalid codes")
    code_values = np.asarray(codes[...])
    if code_values.size and (
        int(code_values.min()) < -1 or int(code_values.max()) >= len(category_values)
    ):
        raise H5ADInspectionError(f"categorical field {name!r} has out-of-range codes")
    return "categorical"


def _read_axis_strings(parent: h5py.Group, name: str, length: int) -> tuple[tuple[str, ...], str]:
    value = _hard_object(parent, name, h5py.Dataset)
    return _read_string_dataset(value, length), "string"


def _read_string_dataset(dataset: h5py.Dataset, length: int) -> tuple[str, ...]:
    if len(dataset.shape) != 1 or int(dataset.shape[0]) != length:
        raise H5ADInspectionError("axis string field has an inconsistent shape")
    if length > MAX_H5AD_AXIS_ITEMS:
        raise H5ADInspectionError("axis string field exceeds the item ceiling")
    try:
        raw = dataset.asstr(encoding="utf-8", errors="strict")[...]
    except (OSError, TypeError, UnicodeError) as error:
        raise H5ADInspectionError("axis string field is not strict UTF-8") from error
    values = tuple(str(item) for item in np.asarray(raw).tolist())
    if any(not item for item in values):
        raise H5ADInspectionError("axis string field contains an empty identifier")
    if sum(len(item.encode("utf-8")) for item in values) > MAX_H5AD_TEXT_BYTES:
        raise H5ADInspectionError("axis string values exceed the text ceiling")
    return values


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
    if not structure.feature_index_unique:
        structure_status = "partial"
        limitations.append(
            "The inspected feature index is not unique; feature-level binding is incomplete."
        )
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
