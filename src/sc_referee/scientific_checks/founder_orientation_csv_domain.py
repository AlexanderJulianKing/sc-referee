"""Bounded staged-CSV domain proofs for founder-orientation semantic v3.1.

This module reads immutable controller-frozen data bytes.  It never imports or
executes project-authored code and never derives an orientation from data
values.  Its only positive result is an exact binary-domain fact for one named
column of one path-and-digest-bound CSV.
"""

from __future__ import annotations

import csv
import io

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks.core import FrozenMaterialInput
from sc_referee.scientific_checks.founder_orientation_semantic_ir import (
    CsvBinaryDomainFact,
)

MAX_FOUNDER_CSV_DOMAIN_BYTES = 8 * 1024 * 1024
MAX_FOUNDER_CSV_DOMAIN_ROWS = 100_000
MAX_FOUNDER_CSV_DOMAIN_FIELDS = 256
MAX_FOUNDER_CSV_DOMAIN_FIELD_BYTES = 64 * 1024
RECOGNIZED_BINARY_CSV_VALUES = ("0", "1")


def prove_binary_csv_column(
    material: FrozenMaterialInput,
    *,
    path: str,
    content_digest: str,
    column: str,
) -> CsvBinaryDomainFact | None:
    """Prove one exact CSV column is a nonempty subset of ``{"0", "1"}``.

    Every failure is an abstention: wrong binding, digest drift, unsupported
    encoding or layout, ragged rows, non-binary data, or any resource ceiling.
    """

    if (
        path != material.path
        or content_digest != material.content_digest
        or not column
        or not path.lower().endswith(".csv")
        or len(material.content) > MAX_FOUNDER_CSV_DOMAIN_BYTES
        or sha256_digest(material.content) != content_digest
    ):
        return None
    try:
        text = material.content.decode("utf-8", errors="strict")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        header = reader.fieldnames
        if (
            header is None
            or not header
            or len(header) > MAX_FOUNDER_CSV_DOMAIN_FIELDS
            or len(set(header)) != len(header)
            or column not in header
            or any(
                not item or len(item.encode("utf-8")) > MAX_FOUNDER_CSV_DOMAIN_FIELD_BYTES
                for item in header
            )
        ):
            return None
        row_count = 0
        for row_count, row in enumerate(reader, start=1):
            if row_count > MAX_FOUNDER_CSV_DOMAIN_ROWS or None in row:
                return None
            values = tuple(row.get(name) for name in header)
            if any(value is None for value in values):
                return None
            fields = tuple(str(value) for value in values)
            if any(
                len(value.encode("utf-8")) > MAX_FOUNDER_CSV_DOMAIN_FIELD_BYTES for value in fields
            ):
                return None
            if str(row[column]) not in RECOGNIZED_BINARY_CSV_VALUES:
                return None
        if row_count == 0:
            return None
    except (csv.Error, UnicodeError, ValueError, OverflowError):
        return None
    return CsvBinaryDomainFact(
        path=path,
        content_digest=content_digest,
        column=column,
        row_count=row_count,
        recognized_values=RECOGNIZED_BINARY_CSV_VALUES,
    )
