"""Frozen, domain-separated digest framing for empty-droplet artifacts."""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from .schema import BarcodeKey, DIGEST_POLICY_ID, FeatureKey, freeze_csr, freeze_u64_vector


def frame_bytes(raw: bytes) -> bytes:
    return struct.pack("<Q", len(raw)) + raw


def frame_text(value: str) -> bytes:
    return frame_bytes(value.encode("utf-8", errors="strict"))


def frame_sequence(items: Sequence[bytes]) -> bytes:
    return struct.pack("<Q", len(items)) + b"".join(items)


def _hasher(kind: str):
    digest = hashlib.sha256()
    digest.update(f"sc-referee-empty-droplet-{kind}-v1\0".encode("ascii"))
    digest.update(frame_text(DIGEST_POLICY_ID))
    return digest


def _finish(digest) -> str:
    return "sha256:" + digest.hexdigest()


def encode_barcode_key(key: BarcodeKey) -> bytes:
    if not isinstance(key, BarcodeKey):
        raise TypeError("barcode ledger requires BarcodeKey values")
    return b"barcode-key\0" + frame_text(key.namespace) + frame_text(key.native_barcode)


def _optional_text(value: str | None) -> bytes:
    return b"none\0" if value is None else b"text\0" + frame_text(value)


def encode_feature_key(key: FeatureKey) -> bytes:
    if not isinstance(key, FeatureKey):
        raise TypeError("feature ledger requires FeatureKey values")
    return (
        b"feature-key\0" + frame_text(key.feature_id)
        + _optional_text(key.feature_name) + frame_text(key.feature_type)
        + _optional_text(key.genome_or_reference)
    )


def digest_barcode_ledger(keys: Iterable[BarcodeKey]) -> str:
    encoded = tuple(encode_barcode_key(key) for key in tuple(keys))
    digest = _hasher("barcode-ledger")
    digest.update(frame_sequence(encoded))
    return _finish(digest)


def digest_feature_ledger(keys: Iterable[FeatureKey]) -> str:
    encoded = tuple(encode_feature_key(key) for key in tuple(keys))
    digest = _hasher("feature-ledger")
    digest.update(frame_sequence(encoded))
    return _finish(digest)


def digest_membership_set(keys: Iterable[BarcodeKey]) -> str:
    encoded = tuple(sorted(encode_barcode_key(key) for key in tuple(keys)))
    if len(encoded) != len(set(encoded)):
        raise ValueError("semantic membership set contains duplicates")
    digest = _hasher("semantic-membership-set")
    digest.update(frame_sequence(encoded))
    return _finish(digest)


def digest_bool_vector(values) -> str:
    array = np.asarray(values)
    if array.ndim != 1 or array.dtype.kind != "b":
        raise ValueError("membership must be a one-dimensional boolean vector")
    digest = _hasher("aligned-membership")
    digest.update(struct.pack("<Q", array.size))
    digest.update(np.ascontiguousarray(array, dtype=np.uint8).tobytes())
    return _finish(digest)


def _u64_bytes(values) -> bytes:
    array = freeze_u64_vector(values, name="digest vector")
    return np.ascontiguousarray(array, dtype="<u8").tobytes(order="C")


def digest_u64_vector(column_identity: str, values, barcode_ledger_digest: str = "") -> str:
    array = freeze_u64_vector(values, name=column_identity)
    digest = _hasher("u64-vector")
    digest.update(frame_text(column_identity))
    digest.update(frame_text(barcode_ledger_digest))
    digest.update(struct.pack("<Q", array.size))
    digest.update(_u64_bytes(array))
    return _finish(digest)


def digest_index_vector(name: str, values) -> str:
    return digest_u64_vector(f"index:{name}", values)


def digest_csr_u64(value) -> str:
    matrix = freeze_csr(value)
    digest = _hasher("canonical-csr-matrix")
    digest.update(struct.pack("<Q", 2))
    digest.update(struct.pack("<Q", matrix.shape[0]))
    digest.update(struct.pack("<Q", matrix.shape[1]))
    for vector in (matrix.indptr, matrix.indices, matrix.data):
        digest.update(struct.pack("<Q", vector.size))
        digest.update(np.ascontiguousarray(vector, dtype="<u8").tobytes(order="C"))
    return _finish(digest)


def digest_source_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def hash_file_bytes(path: Path) -> str:
    with Path(path).open("rb") as handle:
        digest = hashlib.sha256()
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def digest_fields(kind: str, fields: Iterable[tuple[str, str]]) -> str:
    records = tuple(frame_text(name) + frame_text(value) for name, value in fields)
    digest = _hasher(kind)
    digest.update(frame_sequence(records))
    return _finish(digest)


def digest_text_sequence(kind: str, values: Iterable[str]) -> str:
    encoded = tuple(frame_text(value) for value in values)
    digest = _hasher(kind)
    digest.update(frame_sequence(encoded))
    return _finish(digest)
