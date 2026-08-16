"""Digest-bound ordered pair-position proofs for the development v2 shadow."""

from __future__ import annotations

import csv
import io
import math
from dataclasses import asdict

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.dependence_recognition.ir import MAX_V1_MEMBERSHIPS, RecordRef
from sc_referee.dependence_recognition_v2.ir import (
    PairedObservation,
    PairedValueSequenceFact,
    PairedValueSequenceObligation,
)
from sc_referee.scientific_checks.core import FrozenMaterialInput


def prove_paired_value_sequence_with_reason(
    material: FrozenMaterialInput,
    *,
    obligation: PairedValueSequenceObligation,
) -> tuple[PairedValueSequenceFact | None, str | None]:
    """Prove one complete row-ordered paired sequence; uncertainty is named."""

    if (
        obligation.path != material.path
        or obligation.content_digest != material.content_digest
        or sha256_digest(material.content) != obligation.content_digest
    ):
        return None, "paired-domain-binding-mismatch"
    if obligation.encoding not in {"utf-8", "ascii"}:
        return None, "unsupported-reader-encoding"
    if (
        obligation.reader_form != "csv_dictreader_direct_file"
        or obligation.line_model != "csv_newline"
    ):
        return None, "paired-domain-unproven"
    ascii_proven = material.content.isascii()
    try:
        text = material.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return (
            None,
            "reader-bytes-not-ascii"
            if obligation.encoding == "ascii"
            else "paired-domain-unproven",
        )
    if text.startswith("\ufeff"):
        return None, "bom-unsupported"
    if obligation.encoding == "ascii" and not ascii_proven:
        return None, "reader-bytes-not-ascii"
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        header = tuple(reader.fieldnames or ())
        if len(header) != len(set(header)):
            return None, "duplicate-header"
        required = {
            obligation.authorized_unit_column,
            obligation.left_value_column,
            obligation.right_value_column,
        }
        if (
            not header
            or any(not item for item in header)
            or not required <= set(header)
            or len(required) != 3
        ):
            return None, "paired-domain-unproven"
        rows = list(reader)
    except (csv.Error, UnicodeError):
        return None, "ragged-row"
    if not rows or len(rows) > 10_000 or len(rows) > MAX_V1_MEMBERSHIPS:
        return None, "paired-domain-unproven"
    observations: list[PairedObservation] = []
    for index, row in enumerate(rows, start=1):
        if None in row or any(row.get(column) is None for column in header):
            return None, "ragged-row"
        unit = row[obligation.authorized_unit_column]
        left = row[obligation.left_value_column]
        right = row[obligation.right_value_column]
        if unit == "":
            return None, "paired-unit-cell-empty"
        if left == "" or right == "":
            return None, "paired-value-cast-unproven"
        try:
            left_value = _cast(left, obligation.left_cast_kind)
            right_value = _cast(right, obligation.right_cast_kind)
        except (TypeError, ValueError, OverflowError):
            return None, "paired-value-cast-unproven"
        if not math.isfinite(left_value) or not math.isfinite(right_value):
            return None, "paired-value-not-finite"
        observations.append(
            PairedObservation(
                row_index=index,
                observation_id=f"paired-observation:{semantic_digest({'path': obligation.path, 'digest': obligation.content_digest, 'row': index})}",
                authorized_unit_id=f"unit-key:{semantic_digest({'column': obligation.authorized_unit_column, 'value': unit})}",
                left_source_value=left,
                right_source_value=right,
                left_cast_value_repr=repr(left_value),
                right_cast_value_repr=repr(right_value),
            )
        )
    return (
        PairedValueSequenceFact(
            evidence_id=f"dependence-growth-paired-proof:{semantic_digest(asdict(obligation))}",
            path=obligation.path,
            content_digest=obligation.content_digest,
            file_ref=RecordRef(material.file_ref.record_type, material.file_ref.record_id),
            asset_identity_ref=RecordRef(
                material.asset_identity_ref.record_type, material.asset_identity_ref.record_id
            ),
            line_model=obligation.line_model,
            reader_form=obligation.reader_form,
            encoding=obligation.encoding,
            ascii_bytes_proven=ascii_proven,
            header=header,
            authorized_unit_column=obligation.authorized_unit_column,
            left_value_column=obligation.left_value_column,
            right_value_column=obligation.right_value_column,
            left_cast_kind=obligation.left_cast_kind,
            right_cast_kind=obligation.right_cast_kind,
            row_count=len(observations),
            observations=tuple(observations),
        ),
        None,
    )


def _cast(value: str, kind: str) -> float | int:
    if kind == "float":
        return float(value)
    if kind == "int":
        return int(value)
    raise ValueError("unsupported paired cast")
