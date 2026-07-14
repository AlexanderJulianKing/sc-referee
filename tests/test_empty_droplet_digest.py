import hashlib
import struct

import numpy as np
from scipy import sparse

from sc_referee.empty_droplet.digest import (
    DIGEST_POLICY_ID, digest_barcode_ledger, digest_csr_u64, digest_u64_vector,
)
from sc_referee.empty_droplet.schema import BarcodeKey


def _frame(raw: bytes) -> bytes:
    return struct.pack("<Q", len(raw)) + raw


def test_barcode_ledger_digest_matches_independent_framing_oracle():
    keys = (BarcodeKey("", "empty_1"), BarcodeKey("", "empty_2"))
    h = hashlib.sha256()
    h.update(b"sc-referee-empty-droplet-barcode-ledger-v1\0")
    h.update(_frame(DIGEST_POLICY_ID.encode()))
    h.update(struct.pack("<Q", 2))
    for key in keys:
        h.update(b"barcode-key\0")
        h.update(_frame(key.namespace.encode()))
        h.update(_frame(key.native_barcode.encode()))
    assert digest_barcode_ledger(keys) == f"sha256:{h.hexdigest()}"


def test_csr_digest_is_storage_independent_after_canonicalization():
    dense = np.array([[5, 0, 1], [0, 3, 0]], dtype=np.uint64)
    a = sparse.csr_matrix(dense)
    b = sparse.coo_matrix(dense).tocsc()
    assert digest_csr_u64(a) == digest_csr_u64(b)
    assert digest_csr_u64(a) != digest_csr_u64(a[:, ::-1])


def test_total_vector_digest_binds_column_and_barcode_order():
    assert digest_u64_vector("total_umi", np.array([12, 9], dtype=np.uint64)) != (
        digest_u64_vector("total_umi", np.array([9, 12], dtype=np.uint64))
    )


def test_empty_digest_domain_is_distinct_from_existing_digest_families():
    keys = (BarcodeKey("", "empty_1"),)
    value = digest_barcode_ledger(keys)
    row_domain = hashlib.sha256(b"row-ledger-digest-v1" + b"empty_1").hexdigest()
    column_domain = hashlib.sha256(
        b"sc-referee-column-space-matrix-digest-v1\0" + b"empty_1"
    ).hexdigest()
    assert value not in {f"sha256:{row_domain}", f"sha256:{column_domain}"}
