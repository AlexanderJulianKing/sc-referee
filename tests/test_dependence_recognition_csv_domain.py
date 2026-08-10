"""Fail-closed tests for the dependence v1 CSV membership prover."""

from __future__ import annotations

from typing import Literal

import pytest

from sc_referee.core.ids import sha256_digest
from sc_referee.dependence_recognition import csv_domain
from sc_referee.dependence_recognition.csv_domain import (
    MAX_DEPENDENCE_CSV_DISTINCT_KEYS,
    MAX_DEPENDENCE_CSV_PROOF_RECORD_BYTES,
    prove_unit_key_multiplicity,
)
from sc_referee.dependence_recognition.ir import (
    MAX_DEPENDENCE_CSV_DOMAIN_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELDS,
    MAX_DEPENDENCE_CSV_DOMAIN_ROWS,
    MAX_V1_MEMBERSHIPS,
    SPLITLINES_ONLY_SEPARATORS,
    UnitKeyMultiplicityFact,
)
from sc_referee.scientific_checks import FrozenMaterialInput, RecordRef

LineModel = Literal["splitlines", "csv_newline"]


def _material(content: bytes, *, path: str = "inputs/data.csv") -> FrozenMaterialInput:
    return FrozenMaterialInput(
        path=path,
        file_ref=RecordRef("file_record", "file:data"),
        asset_identity_ref=RecordRef("asset_identity", "identity:data"),
        content=content,
        content_digest=sha256_digest(content),
    )


def _prove(
    material: FrozenMaterialInput,
    key_columns: tuple[str, ...] = ("unit",),
    *,
    line_model: LineModel | str = "csv_newline",
) -> UnitKeyMultiplicityFact | None:
    return prove_unit_key_multiplicity(
        material,
        path=material.path,
        content_digest=material.content_digest,
        key_columns=key_columns,
        line_model=line_model,
    )


def _row_csv(row_count: int, *, unique: bool) -> bytes:
    rows = ["unit"]
    rows.extend(f"unit-{index}" if unique else "unit-a" for index in range(row_count))
    return ("\n".join(rows) + "\n").encode()


def _csv_with_exact_byte_count(byte_count: int) -> bytes:
    header = b"unit,note\n"
    remaining = byte_count - len(header)
    maximum_row_bytes = MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES + 3
    row_count = (remaining + maximum_row_bytes - 1) // maximum_row_bytes
    assert row_count > 0
    payload_bytes = remaining - (3 * row_count)
    assert 0 <= payload_bytes <= MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES * row_count
    rows: list[bytes] = []
    for _ in range(row_count):
        field_bytes = min(payload_bytes, MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES)
        rows.append(b"u," + (b"x" * field_bytes) + b"\n")
        payload_bytes -= field_bytes
    assert payload_bytes == 0
    content = header + b"".join(rows)
    assert len(content) == byte_count
    return content


def test_duplicate_key_fact_is_bound_and_recomputable() -> None:
    material = _material(b"unit,value\na,1\nb,2\na,3\n")
    fact = _prove(material)
    assert fact is not None
    assert fact.path == material.path
    assert fact.content_digest == material.content_digest
    assert fact.file_ref.record_id == material.file_ref.record_id
    assert fact.asset_identity_ref.record_id == material.asset_identity_ref.record_id
    assert fact.reader_form == "csv_dictreader_file"
    assert fact.line_model == "csv_newline"
    assert fact.dialect == "excel"
    assert fact.normalization == "byte_exact_utf8"
    assert fact.declared_missing_value_tokens == ()
    assert fact.row_count == 3
    assert len(fact.observation_ids) == 3
    assert len(set(fact.observation_ids)) == 3
    assert fact.unit_ids[0] == fact.unit_ids[2]
    assert fact.unit_ids[0] != fact.unit_ids[1]
    assert sorted(count for _, count in fact.multiplicities) == [1, 2]
    assert fact.repeated_unit_ids == (fact.unit_ids[0],)


def test_non_duplicate_key_is_also_positively_proven() -> None:
    fact = _prove(_material(b"unit,value\na,1\nb,2\nc,3\n"))
    assert fact is not None
    assert fact.distinct_key_count == 3
    assert all(count == 1 for _, count in fact.multiplicities)
    assert fact.repeated_unit_ids == ()


def test_composite_key_repetition_is_computed_over_the_ordered_tuple() -> None:
    content = b"site,subject,value\na,1,0\na,2,0\nb,1,0\nb,2,0\n"
    fact = _prove(_material(content), ("site", "subject"))
    assert fact is not None
    assert fact.key_columns == ("site", "subject")
    assert fact.distinct_key_count == 4
    assert fact.repeated_unit_ids == ()
    assert len(set(fact.unit_ids)) == 4


def test_composite_key_duplicate_is_proven_without_collapsing_components() -> None:
    content = b"site,subject,value\na,1,0\na,1,1\na,2,0\n"
    fact = _prove(_material(content), ("site", "subject"))
    assert fact is not None
    assert fact.unit_ids[0] == fact.unit_ids[1]
    assert fact.unit_ids[0] != fact.unit_ids[2]
    assert fact.repeated_unit_ids == (fact.unit_ids[0],)


def test_composite_key_column_order_is_part_of_the_identity() -> None:
    material = _material(b"site,subject\na,1\n")
    forward = _prove(material, ("site", "subject"))
    reverse = _prove(material, ("subject", "site"))
    assert forward is not None
    assert reverse is not None
    assert forward.key_columns != reverse.key_columns
    assert forward.unit_ids != reverse.unit_ids


def test_whitespace_variants_are_distinct_byte_exact_keys() -> None:
    fact = _prove(_material(b"unit\na\n a\na \n"))
    assert fact is not None
    assert fact.distinct_key_count == 3
    assert len(set(fact.unit_ids)) == 3
    assert fact.repeated_unit_ids == ()


def test_no_missing_sentinel_is_guessed() -> None:
    fact = _prove(_material(b"unit\nNA\nnone\nnull\n"))
    assert fact is not None
    assert fact.distinct_key_count == 3
    assert fact.declared_missing_value_tokens == ()


@pytest.mark.parametrize(
    "content",
    [
        b"unit,value\n,1\n",
        b'unit,value\n"",1\n',
        b"value,unit\n1\n",
    ],
)
def test_empty_or_missing_key_component_abstains(content: bytes) -> None:
    assert _prove(_material(content)) is None


def test_duplicate_header_abstains() -> None:
    assert _prove(_material(b"unit,unit\na,a\n")) is None


@pytest.mark.parametrize(
    "content",
    [
        b"unit,value\na\n",
        b"unit,value\na,1,extra\n",
    ],
)
def test_short_and_long_ragged_rows_abstain(content: bytes) -> None:
    assert _prove(_material(content)) is None


def test_digest_argument_drift_abstains() -> None:
    material = _material(b"unit\na\n")
    assert (
        prove_unit_key_multiplicity(
            material,
            path=material.path,
            content_digest="sha256:" + "0" * 64,
            key_columns=("unit",),
            line_model="csv_newline",
        )
        is None
    )


def test_frozen_byte_rehash_detects_post_construction_drift() -> None:
    material = _material(b"unit\na\n")
    object.__setattr__(material, "content", b"unit\nb\n")
    assert _prove(material) is None


def test_path_and_extension_binding_abstain_on_mismatch() -> None:
    material = _material(b"unit\na\n")
    assert (
        prove_unit_key_multiplicity(
            material,
            path="inputs/other.csv",
            content_digest=material.content_digest,
            key_columns=("unit",),
            line_model="csv_newline",
        )
        is None
    )
    non_csv = _material(b"unit\na\n", path="inputs/data.txt")
    assert _prove(non_csv) is None


@pytest.mark.parametrize("line_model", ["csv_newline", "splitlines"])
def test_clean_csv_is_proven_under_both_certified_line_models(line_model: LineModel) -> None:
    fact = _prove(_material(b"unit,value\na,1\na,2\n"), line_model=line_model)
    assert fact is not None
    assert fact.line_model == line_model
    assert fact.reader_form == (
        "csv_dictreader_splitlines" if line_model == "splitlines" else "csv_dictreader_file"
    )
    assert fact.row_count == 2
    assert fact.repeated_unit_ids


@pytest.mark.parametrize("separator", ["\x85", "\u2028"])
def test_splitlines_only_separator_abstains_only_for_that_runtime_model(
    separator: str,
) -> None:
    material = _material(("unit,note\na,x" + separator + "y\nb,z\n").encode())
    assert _prove(material, line_model="splitlines") is None
    fact = _prove(material, line_model="csv_newline")
    assert fact is not None
    assert fact.row_count == 2


@pytest.mark.parametrize("separator", SPLITLINES_ONLY_SEPARATORS)
def test_every_splitlines_only_separator_is_guarded(separator: str) -> None:
    material = _material(("unit,note\na,x" + separator + "y\n").encode())
    assert _prove(material, line_model="splitlines") is None


def test_quoted_embedded_newline_uses_the_certified_runtime_model() -> None:
    material = _material(b'unit,note\na,"first line\nsecond line"\nb,plain\n')
    csv_fact = _prove(material, line_model="csv_newline")
    splitlines_fact = _prove(material, line_model="splitlines")
    assert csv_fact is not None
    assert splitlines_fact is not None
    assert csv_fact.row_count == splitlines_fact.row_count == 2
    assert csv_fact.row_domain != splitlines_fact.row_domain
    assert csv_fact.observation_ids != splitlines_fact.observation_ids


def test_utf8_bom_abstains_instead_of_rewriting_the_header() -> None:
    assert _prove(_material(b"\xef\xbb\xbfunit,value\na,1\n")) is None


def test_trailing_blank_line_does_not_manufacture_a_membership() -> None:
    fact = _prove(_material(b"unit\na\nb\n\n"))
    assert fact is not None
    assert fact.row_count == 2


def test_invalid_utf8_empty_table_and_unknown_line_model_abstain() -> None:
    assert _prove(_material(b"unit\n\xff\n")) is None
    assert _prove(_material(b"unit\n")) is None
    assert _prove(_material(b"unit\na\n"), line_model="universal") is None


@pytest.mark.parametrize(
    "key_columns",
    [(), ("",), ("unit", "unit"), ("other",)],
)
def test_invalid_or_unavailable_key_column_set_abstains(
    key_columns: tuple[str, ...],
) -> None:
    assert _prove(_material(b"unit\na\n"), key_columns) is None


def test_same_frozen_input_replays_the_identical_fact() -> None:
    material = _material(b"unit\na\na\n")
    first = _prove(material)
    second = _prove(material)
    assert first is not None
    assert first == second


def test_byte_ceiling_accepts_boundary_and_rejects_boundary_plus_one() -> None:
    boundary = _csv_with_exact_byte_count(MAX_DEPENDENCE_CSV_DOMAIN_BYTES)
    fact = _prove(_material(boundary))
    assert fact is not None
    assert fact.source_byte_count == MAX_DEPENDENCE_CSV_DOMAIN_BYTES
    assert _prove(_material(boundary + b"x")) is None


def test_field_count_ceiling_accepts_boundary_and_rejects_boundary_plus_one() -> None:
    def content(field_count: int) -> bytes:
        header = ["unit", *(f"field-{index}" for index in range(1, field_count))]
        row = ["u", *("" for _ in range(1, field_count))]
        return (",".join(header) + "\n" + ",".join(row) + "\n").encode()

    fact = _prove(_material(content(MAX_DEPENDENCE_CSV_DOMAIN_FIELDS)))
    assert fact is not None
    assert len(fact.header) == MAX_DEPENDENCE_CSV_DOMAIN_FIELDS
    assert _prove(_material(content(MAX_DEPENDENCE_CSV_DOMAIN_FIELDS + 1))) is None


def test_field_byte_ceiling_accepts_boundary_and_rejects_boundary_plus_one() -> None:
    boundary = b"x" * MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES
    fact = _prove(_material(b"unit\n" + boundary + b"\n"))
    assert fact is not None
    assert _prove(_material(b"unit\n" + boundary + b"x\n")) is None


def test_row_ceiling_guard_is_exact_when_isolated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert MAX_DEPENDENCE_CSV_DOMAIN_ROWS == 100_000
    monkeypatch.setattr(csv_domain, "MAX_DEPENDENCE_CSV_DOMAIN_ROWS", 2)
    monkeypatch.setattr(csv_domain, "MAX_V1_MEMBERSHIPS", 3)
    monkeypatch.setattr(csv_domain, "MAX_DEPENDENCE_CSV_DISTINCT_KEYS", 3)
    assert _prove(_material(_row_csv(2, unique=True))) is not None
    assert _prove(_material(_row_csv(3, unique=True))) is None


def test_membership_ceiling_accepts_boundary_and_rejects_boundary_plus_one() -> None:
    fact = _prove(_material(_row_csv(MAX_V1_MEMBERSHIPS, unique=True)))
    assert fact is not None
    assert fact.row_count == MAX_V1_MEMBERSHIPS
    assert fact.distinct_key_count == MAX_DEPENDENCE_CSV_DISTINCT_KEYS
    assert _prove(_material(_row_csv(MAX_V1_MEMBERSHIPS + 1, unique=True))) is None


def test_distinct_key_ceiling_guard_is_exact_when_isolated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert MAX_DEPENDENCE_CSV_DISTINCT_KEYS == 10_000
    monkeypatch.setattr(csv_domain, "MAX_DEPENDENCE_CSV_DISTINCT_KEYS", 2)
    assert _prove(_material(_row_csv(2, unique=True))) is not None
    assert _prove(_material(_row_csv(3, unique=True))) is None


def test_proof_record_ceiling_accepts_boundary_and_rejects_boundary_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert MAX_DEPENDENCE_CSV_PROOF_RECORD_BYTES == MAX_DEPENDENCE_CSV_DOMAIN_BYTES
    material = _material(b"unit\na\na\n")
    fact = _prove(material)
    assert fact is not None
    fact_size = csv_domain._proof_record_byte_count(fact)
    monkeypatch.setattr(csv_domain, "MAX_DEPENDENCE_CSV_PROOF_RECORD_BYTES", fact_size)
    assert _prove(material) is not None
    monkeypatch.setattr(csv_domain, "MAX_DEPENDENCE_CSV_PROOF_RECORD_BYTES", fact_size - 1)
    assert _prove(material) is None
