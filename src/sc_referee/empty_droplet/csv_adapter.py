"""Exact string-first adapters for the ratified dense CSV transports."""
from __future__ import annotations

import csv
from dataclasses import dataclass
import io
from pathlib import Path
import re
import zlib

import numpy as np
from scipy import sparse

from .digest import digest_source_bytes
from .paths import resolve_within
from .schema import (
    BarcodeKey, EmptyDropletUnavailableReason, EmptyDropletValidationError,
    FeatureKey, SourceDeclaration, freeze_bool_vector, freeze_csr, freeze_u64_vector,
)


MAX_DECOMPRESSED_BYTES = 256 * 1024 * 1024
_UINT_RE = re.compile(r"(?:0|[1-9][0-9]*)\Z", flags=re.ASCII)
_U64_MAX = 2**64 - 1


@dataclass(frozen=True)
class ParsedEmptyDropletTable:
    counts: sparse.csr_matrix
    total_counts: np.ndarray
    barcode_ledger: tuple[BarcodeKey, ...]
    feature_ledger: tuple[FeatureKey, ...]
    empty_membership: np.ndarray
    source_byte_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "counts", freeze_csr(self.counts))
        object.__setattr__(self, "total_counts", freeze_u64_vector(self.total_counts, name="total_counts"))
        object.__setattr__(self, "barcode_ledger", tuple(self.barcode_ledger))
        object.__setattr__(self, "feature_ledger", tuple(self.feature_ledger))
        object.__setattr__(self, "empty_membership", freeze_bool_vector(self.empty_membership, name="empty_membership"))


def _failure(reason: EmptyDropletUnavailableReason, message: str):
    raise EmptyDropletValidationError(reason, message)


def _read_transport(root: Path, declaration) -> tuple[bytes, str]:
    try:
        path = resolve_within(root, declaration.path)
        raw = path.read_bytes()
    except (OSError, ValueError) as exc:
        _failure(EmptyDropletUnavailableReason.SOURCE_UNREADABLE_OR_UNSAFE, str(exc))
    source_hash = digest_source_bytes(raw)
    if declaration.compression == "none":
        payload = raw
    elif declaration.compression == "gzip":
        try:
            inflater = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)
            payload = inflater.decompress(raw, MAX_DECOMPRESSED_BYTES + 1)
            if (
                len(payload) > MAX_DECOMPRESSED_BYTES
                or inflater.unconsumed_tail
            ):
                raise ValueError("gzip must be one complete bounded member with no trailing bytes")
            payload += inflater.flush()
            if not inflater.eof or inflater.unused_data or len(payload) > MAX_DECOMPRESSED_BYTES:
                raise ValueError("gzip must be one complete bounded member with no trailing bytes")
        except (zlib.error, ValueError) as exc:
            _failure(
                EmptyDropletUnavailableReason.SOURCE_UNREADABLE_OR_UNSAFE,
                f"gzip source is corrupt, truncated, concatenated, trailing, or unsafe: {exc}",
            )
    else:
        _failure(EmptyDropletUnavailableReason.UNSUPPORTED_FORMAT, "unsupported CSV compression")
    try:
        payload.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        _failure(EmptyDropletUnavailableReason.SOURCE_UNREADABLE_OR_UNSAFE, f"source is not strict UTF-8: {exc}")
    return payload, source_hash


def _rows(payload: bytes) -> list[list[str]]:
    try:
        reader = csv.reader(io.StringIO(payload.decode("utf-8"), newline=""), strict=True)
        rows = list(reader)
    except (csv.Error, UnicodeError) as exc:
        _failure(EmptyDropletUnavailableReason.MALFORMED_MATRIX, f"CSV parse failed: {exc}")
    if not rows or not rows[0] or any(column == "" for column in rows[0]):
        _failure(EmptyDropletUnavailableReason.MALFORMED_MATRIX, "CSV header is absent or blank")
    width = len(rows[0])
    if len(set(rows[0])) != width or any(len(row) != width for row in rows[1:]):
        _failure(EmptyDropletUnavailableReason.MALFORMED_MATRIX, "CSV has duplicate headers or ragged rows")
    return rows


def parse_u64_lexeme(value: str, *, identity: str) -> int:
    if not isinstance(value, str) or not _UINT_RE.fullmatch(value):
        _failure(
            EmptyDropletUnavailableReason.NOT_RAW_INTEGER_COUNTS,
            f"{identity} is not a canonical non-negative integer lexeme",
        )
    integer = int(value, 10)
    if integer > _U64_MAX:
        _failure(EmptyDropletUnavailableReason.NOT_RAW_INTEGER_COUNTS, f"{identity} exceeds uint64")
    return integer


def parse_empty_droplet_csv(root: Path, declaration: SourceDeclaration) -> ParsedEmptyDropletTable:
    if declaration.role != "explicit_empty_droplet_count_table" or declaration.format != "dense_csv/v1":
        _failure(EmptyDropletUnavailableReason.UNSUPPORTED_FORMAT, "source role or format is unsupported")
    genes = tuple(declaration.gene_count_columns)
    if not genes or len(set(genes)) != len(genes):
        _failure(EmptyDropletUnavailableReason.FEATURE_IDENTITY_INVALID, "gene identities must be nonempty and unique")
    expected = (declaration.barcode_key_column, declaration.total_count_column, *genes)
    if len(set(expected)) != len(expected):
        _failure(EmptyDropletUnavailableReason.FEATURE_IDENTITY_INVALID, "declared columns overlap")
    payload, source_hash = _read_transport(root, declaration)
    rows = _rows(payload)
    if tuple(rows[0]) != expected:
        _failure(
            EmptyDropletUnavailableReason.MATRIX_OR_MODALITY_AMBIGUOUS,
            "CSV header must exactly equal the confirmed barcode, total, and ordered gene columns",
        )
    if len(rows) == 1:
        _failure(EmptyDropletUnavailableReason.EMPTY_POOL_DEGENERATE, "empty table has zero rows")
    barcodes: list[BarcodeKey] = []
    seen: set[BarcodeKey] = set()
    totals: list[int] = []
    matrix: list[list[int]] = []
    for row_number, row in enumerate(rows[1:], start=2):
        native = row[0]
        if not native or native != native.strip():
            _failure(EmptyDropletUnavailableReason.BARCODE_IDENTITY_INVALID, f"invalid barcode at row {row_number}")
        key = BarcodeKey(declaration.namespace, native)
        if key in seen:
            _failure(EmptyDropletUnavailableReason.BARCODE_IDENTITY_INVALID, f"duplicate barcode at row {row_number}")
        seen.add(key)
        barcodes.append(key)
        totals.append(parse_u64_lexeme(row[1], identity=f"row {row_number} total count"))
        matrix.append([
            parse_u64_lexeme(value, identity=f"row {row_number} gene {gene}")
            for gene, value in zip(genes, row[2:])
        ])
    dense = np.array(matrix, dtype=np.uint64)
    if not np.any(dense):
        _failure(EmptyDropletUnavailableReason.EMPTY_POOL_DEGENERATE, "selected gene panel aggregate is zero")
    return ParsedEmptyDropletTable(
        counts=sparse.csr_matrix(dense), total_counts=np.array(totals, dtype=np.uint64),
        barcode_ledger=tuple(barcodes),
        feature_ledger=tuple(FeatureKey(gene) for gene in genes),
        empty_membership=np.ones(len(barcodes), dtype=np.bool_), source_byte_hash=source_hash,
    )


read_csv_transport = _read_transport
parse_csv_rows = _rows
