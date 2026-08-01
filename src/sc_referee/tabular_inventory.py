from __future__ import annotations

import csv
import io
from copy import deepcopy
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from sc_referee.core.ids import sha256_digest, stable_id
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.snapshot.identity import build_asset_identity, full_digest_evidence
from sc_referee.snapshot.repository import SnapshotOutput
from sc_referee.version import SCHEMA_VERSION

MAX_DELIMITED_HEADER_COLUMNS = 1024


@dataclass(frozen=True)
class TabularInventoryOutput:
    artifacts: list[dict[str, Any]]
    asset_identities: list[dict[str, Any]]
    data_assets: list[dict[str, Any]]
    variables: list[dict[str, Any]]
    inspected_paths: tuple[str, ...]
    unavailable_paths: tuple[str, ...]
    ambiguous_artifact_paths: tuple[str, ...]


@dataclass(frozen=True)
class _HeaderInspection:
    names: tuple[str, ...]
    source_ref: dict[str, Any]
    structure_status: str
    limitations: tuple[str, ...]


def inspect_delimited_inventory(
    snapshot: SnapshotOutput,
    existing_artifacts: list[dict[str, Any]],
    existing_data_assets: list[dict[str, Any]],
    run_id: str,
    created_at: str,
) -> TabularInventoryOutput:
    """Inventory exact CSV/TSV headers without interpreting rows or scientific meaning."""

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

    for logical_path, file_record in sorted(raw_files.items()):
        suffix = PurePosixPath(logical_path).suffix.casefold()
        if suffix not in {".csv", ".tsv"} or logical_path in existing_data_paths:
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
        inspection = _inspect_header(logical_path, suffix, payload, digest)
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
                "format": suffix.removeprefix("."),
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
    )


def _inspect_header(
    logical_path: str,
    suffix: str,
    payload: bytes,
    digest: str,
) -> _HeaderInspection:
    generic_ref: dict[str, Any] = {
        "source_kind": "artifact",
        "locator": logical_path,
        "path": logical_path,
        "content_digest": digest,
    }
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _HeaderInspection(
            names=(),
            source_ref=generic_ref,
            structure_status="opaque",
            limitations=(
                "Strict UTF-8 decoding failed; no delimited-table structure was inferred.",
            ),
        )
    handle = io.StringIO(text, newline="")
    reader = csv.reader(handle, delimiter="\t" if suffix == ".tsv" else ",")
    try:
        header = next(reader)
    except StopIteration:
        return _HeaderInspection(
            names=(),
            source_ref=generic_ref,
            structure_status="unavailable",
            limitations=("The delimited file is empty; no header was available.",),
        )
    except csv.Error:
        return _HeaderInspection(
            names=(),
            source_ref=generic_ref,
            structure_status="opaque",
            limitations=("The first delimited record could not be parsed safely.",),
        )

    end_line = max(1, reader.line_num)
    header_text = "\n".join(text.splitlines()[:end_line])
    source_ref = {
        "source_kind": "file_span",
        "locator": f"{logical_path}:1-{end_line}",
        "path": logical_path,
        "content_digest": digest,
        "start_line": 1,
        "end_line": end_line,
        "quoted_text": header_text,
    }
    if not header or any(not name for name in header) or len(set(header)) != len(header):
        return _HeaderInspection(
            names=(),
            source_ref=source_ref,
            structure_status="opaque",
            limitations=(
                "The delimited header is missing, empty, or duplicated; no variables were emitted.",
            ),
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
        )
    return _HeaderInspection(
        names=tuple(header),
        source_ref=source_ref,
        structure_status="partial",
        limitations=(
            "Only the exact delimited header was inspected; row shape, row count, cell values, "
            "storage types, and scientific meanings remain unknown.",
            "Static source linkage, when present, does not establish runtime input or output use.",
        ),
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
