"""One-way canonical evidence bytes; deliberately provides no loader."""
from __future__ import annotations

from dataclasses import fields
import struct

import numpy as np

from .digest import encode_barcode_key, encode_feature_key, frame_bytes, frame_sequence, frame_text
from .schema import DIGEST_POLICY_ID, EmptyDropletCountsArtifact


def _u64(values) -> bytes:
    array = np.ascontiguousarray(values, dtype="<u8")
    return struct.pack("<Q", array.size) + array.tobytes(order="C")


def canonical_artifact_bytes(artifact: EmptyDropletCountsArtifact) -> bytes:
    """Project every normative field to deterministic bytes; this is not deserialization API."""
    matrix = artifact.counts
    digest_records = tuple(
        frame_text(field.name) + frame_text(getattr(artifact.digests, field.name))
        for field in fields(artifact.digests)
    )
    mapping_records = tuple(
        encode_feature_key(mapping.feature_key)
        + struct.pack("<Q", mapping.cells_table_column)
        + struct.pack("<Q", mapping.empty_feature_column)
        for mapping in artifact.filtered_bundle_link.bundle_feature_mapping
    )
    source_records = tuple(
        frame_text(record.role) + frame_text(record.relative_path)
        + frame_text(record.byte_sha256) + frame_text(record.format)
        + frame_text(record.compression)
        for record in artifact.source_provenance
    )
    parts = (
        b"sc-referee-empty-droplet-canonical-artifact-bytes-v1\0",
        frame_text(DIGEST_POLICY_ID), frame_text(artifact.schema_id),
        struct.pack("<QQ", *artifact.shape),
        _u64(matrix.indptr), _u64(matrix.indices), _u64(matrix.data),
        _u64(artifact.total_counts),
        frame_sequence(tuple(encode_barcode_key(key) for key in artifact.barcode_ledger)),
        frame_sequence(tuple(encode_feature_key(key) for key in artifact.feature_ledger)),
        struct.pack("<Q", artifact.empty_membership.size)
        + np.ascontiguousarray(artifact.empty_membership, dtype=np.uint8).tobytes(),
        frame_sequence(tuple(encode_barcode_key(key) for key in artifact.selected_barcodes)),
        frame_text(artifact.membership_provenance.method_id),
        frame_text(artifact.membership_provenance.authority),
        frame_text(artifact.filtered_bundle_link.filtered_bundle_identity),
        frame_text(artifact.filtered_bundle_link.filtered_source_identity),
        frame_sequence(tuple(encode_barcode_key(key) for key in artifact.filtered_bundle_link.filtered_cell_ledger)),
        frame_sequence(tuple(encode_feature_key(key) for key in artifact.filtered_bundle_link.filtered_feature_ledger)),
        _u64(artifact.filtered_bundle_link.bundle_cell_to_cells_table_row),
        frame_sequence(mapping_records),
        bytes((artifact.filtered_bundle_link.empty_vs_cell_disjoint, artifact.filtered_bundle_link.shared_count_coherent)),
        frame_text(str(artifact.filtered_bundle_link.total_count_coherence).lower()),
        frame_text(artifact.filtered_bundle_link.namespace_policy),
        frame_text(artifact.filtered_bundle_link.link_digest),
        frame_sequence(source_records), frame_sequence(digest_records),
        frame_text(artifact.droplet_ledger_identity),
        frame_text(artifact.artifact_content_identity), frame_text(artifact.attestation_identity),
    )
    return b"".join(parts)
