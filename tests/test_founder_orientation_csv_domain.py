"""Fail-closed tests for the founder v3.1 staged-CSV domain prover."""

from __future__ import annotations

from sc_referee.core.ids import sha256_digest
from sc_referee.scientific_checks import FrozenMaterialInput, RecordRef
from sc_referee.scientific_checks.founder_orientation_csv_domain import (
    MAX_FOUNDER_CSV_DOMAIN_BYTES,
    prove_binary_csv_column,
)


def _material(content: bytes) -> FrozenMaterialInput:
    return FrozenMaterialInput(
        path="inputs/data.csv",
        file_ref=RecordRef("file_record", "file:data"),
        asset_identity_ref=RecordRef("asset_identity", "identity:data"),
        content=content,
        content_digest=sha256_digest(content),
    )


def _prove(
    material: FrozenMaterialInput,
    column: str = "observed",
    *,
    line_model: str = "csv_newline",
):
    return prove_binary_csv_column(
        material,
        path=material.path,
        content_digest=material.content_digest,
        column=column,
        line_model=line_model,
    )


def test_binary_column_is_proven_over_exact_digest_bound_bytes() -> None:
    material = _material(b"id,observed,panel\na,0,1\nb,1,0\n")
    fact = _prove(material)
    assert fact is not None
    assert fact.path == material.path
    assert fact.content_digest == material.content_digest
    assert fact.column == "observed"
    assert fact.row_count == 2
    assert fact.recognized_values == ("0", "1")


def test_non_binary_column_fails_closed() -> None:
    material = _material(b"id,observed,panel\na,0,1\nb,2,0\n")
    assert _prove(material) is None


def test_short_dictreader_row_fails_closed() -> None:
    material = _material(b"id,observed,panel\na,0,1\nb,1\n")
    assert _prove(material) is None


def test_digest_mismatch_fails_closed() -> None:
    material = _material(b"id,observed,panel\na,0,1\n")
    assert (
        prove_binary_csv_column(
            material,
            path=material.path,
            content_digest="sha256:" + "0" * 64,
            column="observed",
            line_model="csv_newline",
        )
        is None
    )


def test_byte_ceiling_overflow_fails_closed_before_csv_parsing() -> None:
    material = _material(b"x" * (MAX_FOUNDER_CSV_DOMAIN_BYTES + 1))
    assert _prove(material) is None
