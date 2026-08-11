"""Fail-closed tests for the multiple-testing v1 p-value-family prover."""

from __future__ import annotations

import csv
import io
import random
from typing import Literal

import pytest

from sc_referee.core.ids import sha256_digest
from sc_referee.multiple_testing_recognition import pvalue_domain
from sc_referee.multiple_testing_recognition.certificate import (
    family_hypothesis_token,
    family_observation_token,
    family_pvalue_token,
)
from sc_referee.multiple_testing_recognition.ir import (
    MAX_PVALUE_FAMILY_COLUMNS,
    MAX_PVALUE_FAMILY_FIELD_BYTES,
    MAX_PVALUE_FAMILY_PROOF_RECORD_BYTES,
    MAX_PVALUE_FAMILY_ROWS,
    MAX_PVALUE_FAMILY_SOURCE_BYTES,
    SPLITLINES_ONLY_SEPARATORS,
    PValueFamilyFact,
)
from sc_referee.multiple_testing_recognition.pvalue_domain import (
    prove_pvalue_family,
    pvalue_family_row_domain,
)
from sc_referee.scientific_checks import FrozenMaterialInput, RecordRef

LineModel = Literal["splitlines", "csv_newline"]


def _material(content: bytes, *, path: str = "results/tests.csv") -> FrozenMaterialInput:
    return FrozenMaterialInput(
        path=path,
        file_ref=RecordRef("file_record", "file:tests"),
        asset_identity_ref=RecordRef("asset_identity", "identity:tests"),
        content=content,
        content_digest=sha256_digest(content),
    )


def _prove(
    material: FrozenMaterialInput,
    value_column: str = "pvalue",
    *,
    line_model: LineModel | str = "csv_newline",
) -> PValueFamilyFact | None:
    return prove_pvalue_family(
        material,
        path=material.path,
        content_digest=material.content_digest,
        value_column=value_column,
        line_model=line_model,
    )


def _csv_rows(
    rows: list[tuple[str, str]],
    *,
    header: tuple[str, str] = ("hypothesis", "pvalue"),
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _row_csv(row_count: int) -> bytes:
    rows = ["hypothesis,pvalue"]
    rows.extend(f"h{index:05d},0.5" for index in range(row_count))
    return ("\n".join(rows) + "\n").encode("utf-8")


def _csv_with_exact_byte_count(byte_count: int) -> bytes:
    header = b"hypothesis,pvalue,note\n"
    remaining = byte_count - len(header)
    for row_count in range(1, MAX_PVALUE_FAMILY_ROWS + 1):
        prefixes = [f"h{index},0.5,".encode("ascii") for index in range(row_count)]
        payload_bytes = remaining - sum(len(prefix) + 1 for prefix in prefixes)
        if row_count <= payload_bytes <= MAX_PVALUE_FAMILY_FIELD_BYTES * row_count:
            rows: list[bytes] = []
            for prefix in prefixes:
                field_bytes = min(
                    payload_bytes - (row_count - len(rows) - 1), MAX_PVALUE_FAMILY_FIELD_BYTES
                )
                rows.append(prefix + (b"x" * field_bytes) + b"\n")
                payload_bytes -= field_bytes
            assert payload_bytes == 0
            content = header + b"".join(rows)
            assert len(content) == byte_count
            return content
    raise AssertionError("could not construct exact-size CSV")


def test_ordered_family_fact_is_digest_bound_and_kernel_recomputable() -> None:
    material = _material(b"hypothesis,contrast,pvalue\nh1,a,0.01\nh2,b,0.01\nh3,c,1\n")
    fact = _prove(material)
    assert fact is not None
    assert fact.path == material.path
    assert fact.content_digest == material.content_digest
    assert fact.file_ref.record_id == material.file_ref.record_id
    assert fact.asset_identity_ref.record_id == material.asset_identity_ref.record_id
    assert fact.reader_form == "csv_dictreader_file"
    assert fact.line_model == "csv_newline"
    assert fact.splitlines_only_separators_absent
    assert fact.dialect == "excel"
    assert fact.normalization == "byte_exact_utf8"
    assert fact.declared_missing_value_tokens == ()
    assert fact.header == ("hypothesis", "contrast", "pvalue")
    assert fact.hypothesis_key_columns == ("hypothesis", "contrast")
    assert fact.pvalue_column == "pvalue"
    assert fact.row_count == 3
    assert fact.key_value_tuples == (("h1", "a"), ("h2", "b"), ("h3", "c"))
    assert fact.raw_pvalue_lexemes == ("0.01", "0.01", "1")
    assert fact.canonical_pvalue_decimals == ("0.01", "0.01", "1")
    assert len(set(fact.observation_tokens)) == 3
    assert len(set(fact.hypothesis_tokens)) == 3
    assert len(set(fact.pvalue_tokens)) == 3

    assert fact.row_domain == pvalue_family_row_domain(
        material.path, material.content_digest, "csv_newline"
    )
    assert fact.observation_tokens == tuple(
        family_observation_token(
            fact.path,
            fact.content_digest,
            fact.row_domain,
            row_ordinal,
        )
        for row_ordinal in range(1, 4)
    )
    assert fact.hypothesis_tokens == tuple(
        family_hypothesis_token(fact.hypothesis_key_columns, values)
        for values in fact.key_value_tuples
    )
    assert fact.pvalue_tokens == tuple(
        family_pvalue_token(fact.row_domain, position, hypothesis, fact.pvalue_column)
        for position, hypothesis in enumerate(fact.hypothesis_tokens)
    )


def test_duplicate_pvalues_are_distinct_position_bound_family_members() -> None:
    fact = _prove(_material(b"hypothesis,pvalue\nh1,0.5\nh2,0.5\nh3,0.5\n"))
    assert fact is not None
    assert fact.raw_pvalue_lexemes == ("0.5", "0.5", "0.5")
    assert len(set(fact.pvalue_tokens)) == 3


def test_edge_values_and_raw_fixed_point_spellings_are_preserved() -> None:
    fact = _prove(_material(b"hypothesis,pvalue\nh1,0\nh2,1\nh3,0.000\nh4,1.000\nh5,00.50\n"))
    assert fact is not None
    assert fact.raw_pvalue_lexemes == ("0", "1", "0.000", "1.000", "00.50")
    assert fact.canonical_pvalue_decimals == ("0", "1", "0", "1", "0.5")


def test_complete_nonvalue_header_is_the_ordered_composite_key() -> None:
    fact = _prove(_material(b"site,pvalue,gene\ns1,0.2,g1\ns1,0.3,g2\n"))
    assert fact is not None
    assert fact.hypothesis_key_columns == ("site", "gene")
    assert fact.key_value_tuples == (("s1", "g1"), ("s1", "g2"))


def test_duplicate_hypothesis_key_abstains_even_when_pvalues_differ() -> None:
    assert _prove(_material(b"hypothesis,pvalue\nh1,0.1\nh1,0.2\n")) is None


@pytest.mark.parametrize(
    "content",
    [
        b"hypothesis,pvalue\n,0.1\n",
        b'hypothesis,pvalue\n"",0.1\n',
        b"hypothesis,pvalue\nh1,\n",
        b'hypothesis,pvalue\nh1,""\n',
        b"hypothesis,pvalue\nh1\n",
    ],
)
def test_empty_or_missing_key_or_pvalue_abstains(content: bytes) -> None:
    assert _prove(_material(content)) is None


@pytest.mark.parametrize(
    "raw",
    [
        "1e-2",
        "1E-2",
        "0e0",
        "+0.5",
        "-0",
        ".5",
        "1.",
        " 0.5",
        "0.5 ",
        "1_0",
        "NaN",
        "Infinity",
        "-Infinity",
        "1.0001",
        "2",
        "abc",
    ],
)
def test_unsupported_decimal_spelling_or_value_abstains(raw: str) -> None:
    assert _prove(_material(_csv_rows([("h1", raw)]))) is None


def test_scientific_notation_is_explicitly_unsupported() -> None:
    assert _prove(_material(b"hypothesis,pvalue\nh1,1e-2\n")) is None


def test_duplicate_or_empty_header_and_value_only_table_abstain() -> None:
    assert _prove(_material(b"hypothesis,pvalue,pvalue\nh1,0.1,0.1\n")) is None
    assert _prove(_material(b",pvalue\nh1,0.1\n")) is None
    assert _prove(_material(b"pvalue\n0.1\n")) is None


@pytest.mark.parametrize(
    "content",
    [
        b"hypothesis,pvalue\nh1\n",
        b"hypothesis,pvalue\nh1,0.1,extra\n",
    ],
)
def test_short_and_long_ragged_rows_abstain(content: bytes) -> None:
    assert _prove(_material(content)) is None


def test_digest_path_and_extension_drift_abstain() -> None:
    material = _material(b"hypothesis,pvalue\nh1,0.1\n")
    assert (
        prove_pvalue_family(
            material,
            path=material.path,
            content_digest="sha256:" + "0" * 64,
            value_column="pvalue",
            line_model="csv_newline",
        )
        is None
    )
    assert (
        prove_pvalue_family(
            material,
            path="results/other.csv",
            content_digest=material.content_digest,
            value_column="pvalue",
            line_model="csv_newline",
        )
        is None
    )
    assert _prove(_material(material.content, path="results/tests.txt")) is None


def test_frozen_byte_rehash_detects_post_construction_drift() -> None:
    material = _material(b"hypothesis,pvalue\nh1,0.1\n")
    object.__setattr__(material, "content", b"hypothesis,pvalue\nh1,0.2\n")
    assert _prove(material) is None


@pytest.mark.parametrize("line_model", ["csv_newline", "splitlines"])
def test_clean_csv_is_proven_under_both_certified_line_models(
    line_model: LineModel,
) -> None:
    fact = _prove(
        _material(b"hypothesis,pvalue\nh1,0\nh2,1\n"),
        line_model=line_model,
    )
    assert fact is not None
    assert fact.line_model == line_model
    assert fact.reader_form == (
        "csv_dictreader_splitlines" if line_model == "splitlines" else "csv_dictreader_file"
    )
    assert fact.normalization == (
        "splitlines_rejoined_utf8" if line_model == "splitlines" else "byte_exact_utf8"
    )
    assert fact.raw_pvalue_lexemes == ("0", "1")


@pytest.mark.parametrize("separator", ["\x85", "\u2028"])
def test_splitlines_only_separator_abstains_only_for_that_runtime_model(
    separator: str,
) -> None:
    material = _material(
        ("hypothesis,pvalue,note\nh1,0.1,x" + separator + "y\nh2,0.2,z\n").encode()
    )
    assert _prove(material, line_model="splitlines") is None
    fact = _prove(material, line_model="csv_newline")
    assert fact is not None
    assert fact.row_count == 2
    assert not fact.splitlines_only_separators_absent


@pytest.mark.parametrize("separator", SPLITLINES_ONLY_SEPARATORS)
def test_every_splitlines_only_separator_is_guarded(separator: str) -> None:
    material = _material(("hypothesis,pvalue,note\nh1,0.1,x" + separator + "y\n").encode())
    assert _prove(material, line_model="splitlines") is None


def test_quoted_embedded_newline_uses_the_certified_runtime_model() -> None:
    material = _material(
        b'hypothesis,pvalue,note\nh1,0.1,"first line\nsecond line"\nh2,0.2,plain\n'
    )
    csv_fact = _prove(material, line_model="csv_newline")
    splitlines_fact = _prove(material, line_model="splitlines")
    assert csv_fact is not None
    assert splitlines_fact is not None
    assert csv_fact.row_count == splitlines_fact.row_count == 2
    assert csv_fact.raw_pvalue_lexemes == splitlines_fact.raw_pvalue_lexemes == ("0.1", "0.2")
    assert csv_fact.row_domain != splitlines_fact.row_domain
    assert csv_fact.observation_tokens != splitlines_fact.observation_tokens


def test_utf8_bom_abstains_instead_of_rewriting_the_header() -> None:
    assert _prove(_material(b"\xef\xbb\xbfhypothesis,pvalue\nh1,0.1\n")) is None


def test_trailing_blank_line_does_not_manufacture_a_family_member() -> None:
    fact = _prove(_material(b"hypothesis,pvalue\nh1,0.1\nh2,0.2\n\n"))
    assert fact is not None
    assert fact.row_count == 2


def test_invalid_utf8_empty_table_unknown_column_and_line_model_abstain() -> None:
    assert _prove(_material(b"hypothesis,pvalue\nh1,\xff\n")) is None
    assert _prove(_material(b"hypothesis,pvalue\n")) is None
    assert _prove(_material(b"hypothesis,pvalue\nh1,0.1\n"), "other") is None
    assert _prove(_material(b"hypothesis,pvalue\nh1,0.1\n"), line_model="universal") is None


def test_same_frozen_input_replays_the_identical_fact() -> None:
    material = _material(b"hypothesis,pvalue\nh1,0.1\nh2,0.1\n")
    first = _prove(material)
    second = _prove(material)
    assert first is not None
    assert first == second


def test_byte_ceiling_accepts_boundary_and_rejects_boundary_plus_one() -> None:
    boundary = _csv_with_exact_byte_count(MAX_PVALUE_FAMILY_SOURCE_BYTES)
    fact = _prove(_material(boundary))
    assert fact is not None
    assert fact.source_byte_count == MAX_PVALUE_FAMILY_SOURCE_BYTES
    assert _prove(_material(boundary + b"x")) is None


def test_column_ceiling_accepts_boundary_and_rejects_boundary_plus_one() -> None:
    def content(column_count: int) -> bytes:
        key_columns = [f"key-{index}" for index in range(column_count - 1)]
        header = [*key_columns, "pvalue"]
        row = [*(f"value-{index}" for index in range(column_count - 1)), "0.5"]
        return (",".join(header) + "\n" + ",".join(row) + "\n").encode()

    fact = _prove(_material(content(MAX_PVALUE_FAMILY_COLUMNS)))
    assert fact is not None
    assert len(fact.header) == MAX_PVALUE_FAMILY_COLUMNS
    assert _prove(_material(content(MAX_PVALUE_FAMILY_COLUMNS + 1))) is None


def test_field_byte_ceiling_accepts_boundary_and_rejects_boundary_plus_one() -> None:
    boundary = b"x" * MAX_PVALUE_FAMILY_FIELD_BYTES
    fact = _prove(_material(b"hypothesis,pvalue\n" + boundary + b",0.5\n"))
    assert fact is not None
    assert _prove(_material(b"hypothesis,pvalue\n" + boundary + b"x,0.5\n")) is None


def test_row_ceiling_accepts_boundary_and_rejects_boundary_plus_one() -> None:
    fact = _prove(_material(_row_csv(MAX_PVALUE_FAMILY_ROWS)))
    assert fact is not None
    assert fact.row_count == MAX_PVALUE_FAMILY_ROWS
    assert _prove(_material(_row_csv(MAX_PVALUE_FAMILY_ROWS + 1))) is None


def test_proof_record_ceiling_accepts_boundary_and_rejects_boundary_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert MAX_PVALUE_FAMILY_PROOF_RECORD_BYTES == 8 * 1024 * 1024
    material = _material(b"hypothesis,pvalue\nh1,0.1\nh2,0.2\n")
    fact = _prove(material)
    assert fact is not None
    fact_size = pvalue_domain._proof_record_byte_count(fact)
    monkeypatch.setattr(pvalue_domain, "MAX_PVALUE_FAMILY_PROOF_RECORD_BYTES", fact_size)
    assert _prove(material) is not None
    monkeypatch.setattr(pvalue_domain, "MAX_PVALUE_FAMILY_PROOF_RECORD_BYTES", fact_size - 1)
    assert _prove(material) is None


def test_fuzz_agrees_with_csv_dictreader_order_and_exact_fields() -> None:
    rng = random.Random(20260811)
    supported_values = ("0", "1", "0.01", "0.500", "00.25", "0.3333333333333333")
    labels = ("plain", "with space", "comma,value", 'quote"value', "ümlaut")
    for _ in range(75):
        row_count = rng.randint(1, 40)
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("hypothesis", "label", "pvalue"))
        for index in range(row_count):
            writer.writerow(
                (
                    f"h{index:04d}",
                    labels[rng.randrange(len(labels))],
                    supported_values[rng.randrange(len(supported_values))],
                )
            )
        content = stream.getvalue().encode("utf-8")
        material = _material(content)
        for line_model in ("csv_newline", "splitlines"):
            fact = _prove(material, line_model=line_model)
            assert fact is not None
            text = content.decode("utf-8")
            source = (
                io.StringIO(text, newline="") if line_model == "csv_newline" else text.splitlines()
            )
            expected = tuple(csv.DictReader(source))
            assert fact.raw_pvalue_lexemes == tuple(row["pvalue"] for row in expected)
            assert fact.key_value_tuples == tuple(
                (row["hypothesis"], row["label"]) for row in expected
            )
