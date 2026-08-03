from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

from sc_referee.core.ids import sha256_digest, stable_id
from sc_referee.delimited_io import (
    BoundedDelimitedHeader,
    DelimitedReadError,
    classify_delimited_path,
    read_bounded_delimited_header,
)
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.snapshot.identity import build_asset_identity, full_digest_evidence
from sc_referee.snapshot.repository import SnapshotOutput
from sc_referee.version import SCHEMA_VERSION

MAX_DELIMITED_HEADER_COLUMNS = 1024
MAX_DELIMITED_HEADER_BYTES = 1024 * 1024
MAX_DELIMITED_LOGICAL_READ_BYTES = MAX_DELIMITED_HEADER_BYTES + 1
MAX_DELIMITED_READ_CHUNK_BYTES = 64 * 1024


@dataclass(frozen=True)
class DelimitedReadReceipt:
    path: str
    content_digest: str
    content_encoding: Literal["identity", "gzip"]
    status: Literal["inspected", "unsupported"]
    raw_file_bytes: int
    logical_bytes_read: int
    read_chunks: int
    raw_byte_ceiling: int
    header_byte_ceiling: int
    logical_read_byte_ceiling: int
    chunk_byte_ceiling: int
    termination_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "content_digest": self.content_digest,
            "content_encoding": self.content_encoding,
            "status": self.status,
            "raw_file_bytes": self.raw_file_bytes,
            "logical_bytes_read": self.logical_bytes_read,
            "read_chunks": self.read_chunks,
            "raw_byte_ceiling": self.raw_byte_ceiling,
            "header_byte_ceiling": self.header_byte_ceiling,
            "logical_read_byte_ceiling": self.logical_read_byte_ceiling,
            "chunk_byte_ceiling": self.chunk_byte_ceiling,
            "termination_reason": self.termination_reason,
        }


@dataclass(frozen=True)
class TabularInventoryOutput:
    artifacts: list[dict[str, Any]]
    asset_identities: list[dict[str, Any]]
    data_assets: list[dict[str, Any]]
    variables: list[dict[str, Any]]
    inspected_paths: tuple[str, ...]
    unavailable_paths: tuple[str, ...]
    ambiguous_artifact_paths: tuple[str, ...]
    read_receipts: tuple[DelimitedReadReceipt, ...]


@dataclass(frozen=True)
class _HeaderInspection:
    names: tuple[str, ...]
    source_ref: dict[str, Any]
    structure_status: str
    limitations: tuple[str, ...]
    table_format: Literal["csv", "tsv"]


def inspect_delimited_inventory(
    snapshot: SnapshotOutput,
    existing_artifacts: list[dict[str, Any]],
    existing_data_assets: list[dict[str, Any]],
    run_id: str,
    created_at: str,
    *,
    read_checkpoint: Callable[[], None] | None = None,
) -> TabularInventoryOutput:
    """Inventory exact CSV/TSV or gzip-compressed headers without interpreting rows."""

    raw_files = {
        str(record["path"]): record
        for record in snapshot.file_records
        if record.get("entry_kind") == "regular_file"
    }
    identities_by_file_id = {
        str(record["asset_ref"]["record_id"]): record
        for record in snapshot.asset_identity_records
        if record.get("asset_ref", {}).get("record_type") == "file_record"
    }
    artifacts_by_path: dict[str, list[dict[str, Any]]] = {}
    for artifact in existing_artifacts:
        path = artifact.get("path")
        if isinstance(path, str):
            artifacts_by_path.setdefault(path, []).append(artifact)
    existing_data_paths = {
        str(record["path"])
        for record in existing_data_assets
        if isinstance(record.get("path"), str)
    }

    new_artifacts: list[dict[str, Any]] = []
    new_identities: list[dict[str, Any]] = []
    data_assets: list[dict[str, Any]] = []
    variables: list[dict[str, Any]] = []
    inspected_paths: list[str] = []
    unavailable_paths: list[str] = []
    ambiguous_artifact_paths: list[str] = []
    read_receipts: list[DelimitedReadReceipt] = []

    selected_material_paths = {
        str(value)
        for value in snapshot.snapshot_record.get("extensions", {}).get(
            "x-material-full-digest-paths", []
        )
        if isinstance(value, str)
    }

    for logical_path, file_record in sorted(raw_files.items()):
        file_format = classify_delimited_path(logical_path)
        if file_format is None or logical_path in existing_data_paths:
            continue
        identity = identities_by_file_id.get(str(file_record["file_id"]))
        materialized = snapshot.materialized_root / logical_path
        if (
            identity is None
            or identity.get("tier") != "full_digest"
            or not materialized.is_file()
            or materialized.is_symlink()
        ):
            unavailable_paths.append(logical_path)
            continue
        digest = identity.get("identity_evidence", {}).get("digest")
        if not isinstance(digest, str):
            unavailable_paths.append(logical_path)
            continue
        if read_checkpoint is not None and file_format.content_encoding == "gzip":
            read_checkpoint()
        try:
            payload = materialized.read_bytes()
        except OSError:
            unavailable_paths.append(logical_path)
            continue
        if sha256_digest(payload) != digest:
            unavailable_paths.append(logical_path)
            continue

        matching_artifacts = artifacts_by_path.get(logical_path, [])
        if len(matching_artifacts) > 1:
            ambiguous_artifact_paths.append(logical_path)
            continue
        raw_byte_ceiling = (
            snapshot.identity_policy.material_full_digest_byte_budget
            if logical_path in selected_material_paths
            else snapshot.identity_policy.full_digest_byte_budget
        )
        try:
            bounded_header = read_bounded_delimited_header(
                payload,
                logical_path,
                raw_byte_ceiling=raw_byte_ceiling,
                header_byte_ceiling=MAX_DELIMITED_HEADER_BYTES,
                logical_read_byte_ceiling=MAX_DELIMITED_LOGICAL_READ_BYTES,
                chunk_byte_ceiling=MAX_DELIMITED_READ_CHUNK_BYTES,
                checkpoint=read_checkpoint,
            )
        except DelimitedReadError as error:
            inspection = _opaque_header(logical_path, digest, file_format.table_format, str(error))
            read_receipts.append(
                DelimitedReadReceipt(
                    path=logical_path,
                    content_digest=digest,
                    content_encoding=file_format.content_encoding,
                    status="unsupported",
                    raw_file_bytes=len(payload),
                    logical_bytes_read=error.logical_bytes_read,
                    read_chunks=error.read_chunks,
                    raw_byte_ceiling=raw_byte_ceiling,
                    header_byte_ceiling=MAX_DELIMITED_HEADER_BYTES,
                    logical_read_byte_ceiling=MAX_DELIMITED_LOGICAL_READ_BYTES,
                    chunk_byte_ceiling=MAX_DELIMITED_READ_CHUNK_BYTES,
                    termination_reason=error.reason,
                )
            )
        else:
            inspection = _inspect_header(logical_path, bounded_header, digest)
            read_receipts.append(
                DelimitedReadReceipt(
                    path=logical_path,
                    content_digest=digest,
                    content_encoding=bounded_header.content_encoding,
                    status="inspected",
                    raw_file_bytes=len(payload),
                    logical_bytes_read=bounded_header.logical_bytes_read,
                    read_chunks=bounded_header.read_chunks,
                    raw_byte_ceiling=raw_byte_ceiling,
                    header_byte_ceiling=MAX_DELIMITED_HEADER_BYTES,
                    logical_read_byte_ceiling=MAX_DELIMITED_LOGICAL_READ_BYTES,
                    chunk_byte_ceiling=MAX_DELIMITED_READ_CHUNK_BYTES,
                    termination_reason=None,
                )
            )
        if matching_artifacts:
            artifact = matching_artifacts[0]
        else:
            artifact, artifact_identity = _inventoried_table_artifact(
                logical_path,
                digest,
                inspection.source_ref,
                run_id,
                created_at,
            )
            new_artifacts.append(artifact)
            new_identities.append(artifact_identity)

        data_asset_id = stable_id(
            "data-asset",
            run_id,
            str(artifact["artifact_id"]),
            digest,
        )
        table_variables = _header_variables(
            inspection,
            data_asset_id,
            run_id,
            created_at,
        )
        data_assets.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "data_asset",
                "data_asset_id": data_asset_id,
                "audit_run_id": run_id,
                "artifact_ref": typed_ref("artifact", str(artifact["artifact_id"])),
                "asset_identity_ref": deepcopy(artifact["asset_identity_ref"]),
                "role": _data_role(artifact),
                "format": inspection.table_format,
                "path": logical_path,
                "structure_status": inspection.structure_status,
                "variable_refs": [
                    typed_ref("variable", str(record["variable_id"])) for record in table_variables
                ],
                "source_refs": [deepcopy(inspection.source_ref)],
                "limitations": list(inspection.limitations),
                "provenance": controller_provenance(
                    "bounded_delimited_header_inventory",
                    created_at,
                ),
            }
        )
        variables.extend(table_variables)
        inspected_paths.append(logical_path)

    return TabularInventoryOutput(
        artifacts=sorted(new_artifacts, key=lambda item: str(item["artifact_id"])),
        asset_identities=sorted(new_identities, key=lambda item: str(item["asset_identity_id"])),
        data_assets=sorted(data_assets, key=lambda item: str(item["data_asset_id"])),
        variables=sorted(variables, key=lambda item: str(item["variable_id"])),
        inspected_paths=tuple(sorted(inspected_paths)),
        unavailable_paths=tuple(sorted(unavailable_paths)),
        ambiguous_artifact_paths=tuple(sorted(ambiguous_artifact_paths)),
        read_receipts=tuple(sorted(read_receipts, key=lambda item: item.path)),
    )


def _inspect_header(
    logical_path: str,
    header_read: BoundedDelimitedHeader,
    digest: str,
) -> _HeaderInspection:
    generic_ref: dict[str, Any] = {
        "source_kind": "artifact",
        "locator": logical_path,
        "path": logical_path,
        "content_digest": digest,
    }
    header = header_read.names
    if not header:
        return _HeaderInspection(
            names=(),
            source_ref=generic_ref,
            structure_status="unavailable",
            limitations=("The delimited file is empty; no header was available.",),
            table_format=header_read.table_format,
        )
    source_ref = {
        "source_kind": "file_span",
        "locator": f"{logical_path}:1-{header_read.end_line}",
        "path": logical_path,
        "content_digest": digest,
        "start_line": 1,
        "end_line": header_read.end_line,
        "quoted_text": header_read.quoted_text,
    }
    if not header or any(not name for name in header) or len(set(header)) != len(header):
        return _HeaderInspection(
            names=(),
            source_ref=source_ref,
            structure_status="opaque",
            limitations=(
                "The delimited header is missing, empty, or duplicated; no variables were emitted.",
            ),
            table_format=header_read.table_format,
        )
    if len(header) > MAX_DELIMITED_HEADER_COLUMNS:
        return _HeaderInspection(
            names=(),
            source_ref=source_ref,
            structure_status="partial",
            limitations=(
                f"The header has {len(header)} columns, exceeding the "
                f"{MAX_DELIMITED_HEADER_COLUMNS}-column record ceiling; no variables were emitted.",
            ),
            table_format=header_read.table_format,
        )
    limitations = [
        "Only the exact delimited header was inspected; row shape, row count, cell values, "
        "storage types, and scientific meanings remain unknown."
    ]
    if header_read.content_encoding == "gzip":
        limitations.append(
            "The gzip member after the first logical record was not decompressed or validated."
        )
    limitations.append(
        "Static source linkage, when present, does not establish runtime input or output use."
    )
    return _HeaderInspection(
        names=tuple(header),
        source_ref=source_ref,
        structure_status="partial",
        limitations=tuple(limitations),
        table_format=header_read.table_format,
    )


def _opaque_header(
    logical_path: str,
    digest: str,
    table_format: Literal["csv", "tsv"],
    reason: str,
) -> _HeaderInspection:
    return _HeaderInspection(
        names=(),
        source_ref={
            "source_kind": "artifact",
            "locator": logical_path,
            "path": logical_path,
            "content_digest": digest,
        },
        structure_status="opaque",
        limitations=(f"The bounded delimited header read failed: {reason}.",),
        table_format=table_format,
    )


def _inventoried_table_artifact(
    logical_path: str,
    digest: str,
    source_ref: dict[str, Any],
    run_id: str,
    created_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    artifact_id = stable_id("artifact", logical_path, digest)
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
        "kind": "table",
        "observed_role": "inventoried_delimited_table",
        "path": logical_path,
        "source_refs": [deepcopy(source_ref)],
        "producer_operation_refs": [],
        "consumer_operation_refs": [],
        "asset_identity_ref": typed_ref("asset_identity", str(identity["asset_identity_id"])),
        "limitations": [
            "Repository presence and table syntax do not establish whether this is an input, "
            "intermediate, output, or publication artifact."
        ],
        "provenance": controller_provenance("bounded_delimited_header_inventory", created_at),
    }
    return artifact, identity


def _header_variables(
    inspection: _HeaderInspection,
    data_asset_id: str,
    run_id: str,
    created_at: str,
) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": SCHEMA_VERSION,
            "record_type": "variable",
            "variable_id": stable_id("variable", data_asset_id, name),
            "audit_run_id": run_id,
            "data_asset_ref": typed_ref("data_asset", data_asset_id),
            "observed_name": name,
            "storage_type": "unknown",
            "scientific_meaning_status": "unresolved",
            "semantic_assertion_refs": [],
            "source_refs": [deepcopy(inspection.source_ref)],
            "limitations": [
                "The exact header name does not establish storage type, scientific role, unit, "
                "scale, or meaning; row values were not inspected by this profile."
            ],
            "provenance": controller_provenance(
                "bounded_delimited_header_inventory",
                created_at,
            ),
        }
        for name in inspection.names
    ]


def _data_role(artifact: dict[str, Any]) -> str:
    has_producer = bool(artifact.get("producer_operation_refs"))
    has_consumer = bool(artifact.get("consumer_operation_refs"))
    if has_producer and has_consumer:
        return "intermediate"
    if has_producer:
        return "output"
    if has_consumer:
        return "input"
    return "unknown"
