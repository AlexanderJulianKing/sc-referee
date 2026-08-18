from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, fields
from pathlib import Path

import pytest
from sc_referee_evaluation.audit_ladder.slice_b import CsvQuestionRequestV1

from sc_referee.controller import (
    FrozenFileManifestInput,
    ManifestBoundFrozenInspectionContext,
)
from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.scientific_checks.core import FrozenBaseRecord, FrozenMaterialInput, RecordRef

M2_DIR = Path(__file__).resolve().parents[1] / "m2"
M2_CSV = M2_DIR / "data.csv"
M2_REPORT = M2_DIR / "expected-report.md"
SOURCE_M2_CSV = Path("examples/walking-skeleton/data.csv")


@dataclass(frozen=True, slots=True)
class SliceBFrozenCase:
    context: ManifestBoundFrozenInspectionContext
    request: CsvQuestionRequestV1
    request_bytes: bytes
    content: bytes
    snapshot_record: FrozenBaseRecord
    selected_file_record: FrozenBaseRecord
    selected_identity_record: FrozenBaseRecord


def build_slice_b_case(
    content: bytes,
    *,
    selected_path: str = "examples/walking-skeleton/data.csv",
    candidate_unit_column_index: int = 0,
    comparison_column_index: int = 1,
    identity: str | None = None,
    scope_valid: bool = True,
) -> SliceBFrozenCase:
    """Construct existing frozen record capabilities; this is not a CSV parser."""

    stable_identity = (
        identity
        or hashlib.sha256(selected_path.encode("ascii") + b"\x00" + content).hexdigest()[:16]
    )
    surface_ref = RecordRef("publication_surface", f"surface:slice-b:{stable_identity}")
    artifact_ref = RecordRef("artifact", f"artifact:slice-b:{stable_identity}")
    snapshot_ref = RecordRef("repository_snapshot", f"snapshot:slice-b:{stable_identity}")
    file_ref = RecordRef("file_record", f"file:slice-b:{stable_identity}")
    identity_ref = RecordRef("asset_identity", f"asset:slice-b:{stable_identity}")
    manifest_ref = "observed/files.jsonl"
    content_digest = sha256_digest(content)
    snapshot_digest = sha256_digest(
        canonical_json(
            [
                {
                    "byte_size": len(content),
                    "digest": content_digest,
                    "entry_kind": "regular_file",
                    "path": selected_path,
                }
            ]
        ).encode("utf-8")
    )
    extensions: object = {
        "x-material-full-digest-paths": [selected_path],
        "x-material-input-identities": [{"path": selected_path, "tier": "full_digest"}],
    }
    snapshot_record = FrozenBaseRecord.from_record(
        snapshot_ref,
        {
            "extensions": extensions,
            "file_manifest_ref": manifest_ref,
            "immutability": True,
            "included_roots": ["."],
            "record_type": "repository_snapshot",
            "schema_version": "0.19.0",
            "snapshot_digest": snapshot_digest,
            "snapshot_id": snapshot_ref.record_id,
        },
    )
    file_record = FrozenBaseRecord.from_record(
        file_ref,
        {
            "asset_identity_ref": identity_ref.to_dict(),
            "byte_size": len(content),
            "entry_kind": "regular_file",
            "file_record_id": file_ref.record_id,
            "path": selected_path,
            "record_type": "file_record",
            "schema_version": "0.19.0",
            "snapshot_ref": snapshot_ref.to_dict(),
        },
    )
    identity_record = FrozenBaseRecord.from_record(
        identity_ref,
        {
            "asset_identity_id": identity_ref.record_id,
            "asset_ref": file_ref.to_dict(),
            "identity_evidence": {"digest": content_digest, "kind": "full_digest"},
            "record_type": "asset_identity",
            "schema_version": "0.19.0",
            "tier": "full_digest",
        },
    )
    surface_record = FrozenBaseRecord.from_record(
        surface_ref,
        {"publication_surface_id": surface_ref.record_id},
    )
    artifact_record = FrozenBaseRecord.from_record(
        artifact_ref,
        {"artifact_id": artifact_ref.record_id},
    )
    manifest_bytes = file_record.canonical_payload + b"\n"
    manifest = FrozenFileManifestInput(
        file_manifest_ref=manifest_ref,
        canonical_jsonl_bytes=manifest_bytes,
        manifest_digest=sha256_digest(manifest_bytes),
    )
    material = FrozenMaterialInput(
        path=selected_path,
        file_ref=file_ref,
        asset_identity_ref=identity_ref,
        content=content,
        content_digest=content_digest,
    )
    context = ManifestBoundFrozenInspectionContext(
        snapshot_digest=snapshot_digest,
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(),
        base_records=(
            surface_record,
            artifact_record,
            snapshot_record,
            file_record,
            identity_record,
        ),
        material_inputs=(material,),
        file_manifest_input=manifest,
    )
    if not scope_valid:
        snapshot_payload = json.loads(snapshot_record.canonical_payload)
        assert type(snapshot_payload) is dict
        snapshot_payload["extensions"] = {
            "x-material-full-digest-paths": [],
            "x-material-input-identities": [],
        }
        unresolved_snapshot = FrozenBaseRecord.from_record(snapshot_ref, snapshot_payload)
        unchecked_context = object.__new__(ManifestBoundFrozenInspectionContext)
        for field in fields(context):
            value = getattr(context, field.name)
            if field.name == "base_records":
                value = tuple(
                    unresolved_snapshot if record is snapshot_record else record
                    for record in context.base_records
                )
            object.__setattr__(unchecked_context, field.name, value)
        context = unchecked_context
        snapshot_record = unresolved_snapshot
    request_mapping = {
        "candidate_unit_column_index": candidate_unit_column_index,
        "comparison_column_index": comparison_column_index,
        "request_version": "csv-question-request-v1",
        "selected_path": selected_path,
    }
    request_bytes = canonical_json(request_mapping).encode("utf-8") + b"\n"
    parsed_request = json.loads(request_bytes)
    assert type(parsed_request) is dict
    assert canonical_json(parsed_request).encode("utf-8") + b"\n" == request_bytes
    request = CsvQuestionRequestV1(**parsed_request)
    return SliceBFrozenCase(
        context=context,
        request=request,
        request_bytes=request_bytes,
        content=content,
        snapshot_record=snapshot_record,
        selected_file_record=file_record,
        selected_identity_record=identity_record,
    )


@pytest.fixture
def slice_b_case_factory() -> Callable[..., SliceBFrozenCase]:
    return build_slice_b_case


@pytest.fixture
def m2_frozen_case() -> SliceBFrozenCase:
    return build_slice_b_case(M2_CSV.read_bytes(), identity="m2")
