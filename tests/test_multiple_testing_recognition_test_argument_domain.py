"""Fail-closed tests for the digest-bound keyed test-argument prover."""

from __future__ import annotations

import csv
import io
import random

import pytest

from sc_referee.core.ids import sha256_digest
from sc_referee.multiple_testing_recognition import test_argument_domain
from sc_referee.multiple_testing_recognition.ir import (
    MAX_TEST_ARGUMENT_DOMAIN_COLUMNS,
    MAX_TEST_ARGUMENT_DOMAIN_FIELD_BYTES,
    MAX_TEST_ARGUMENT_DOMAIN_PROOF_RECORD_BYTES,
    MAX_TEST_ARGUMENT_DOMAIN_ROWS,
    MAX_TEST_ARGUMENT_DOMAIN_SOURCE_BYTES,
    SPLITLINES_ONLY_SEPARATORS,
    TestArgumentDomainFact,
)
from sc_referee.multiple_testing_recognition.test_argument_domain import (
    prove_test_argument_domain,
)
from sc_referee.multiple_testing_recognition.test_argument_domain import (
    test_argument_row_domain as argument_row_domain,
)
from sc_referee.scientific_checks import FrozenMaterialInput, RecordRef

_PATH = "inputs/measurements.csv"
_KEYS = ("gene",)
_LEFT = ("x1", "x2")
_RIGHT = ("y1", "y2")


def _material(content: bytes, *, path: str = _PATH) -> FrozenMaterialInput:
    return FrozenMaterialInput(
        path=path,
        file_ref=RecordRef("file_record", "file:measurements"),
        asset_identity_ref=RecordRef("asset_identity", "asset:measurements"),
        content=content,
        content_digest=sha256_digest(content),
    )


def _prove(
    material: FrozenMaterialInput,
    *,
    keys: tuple[str, ...] = _KEYS,
    left: tuple[str, ...] = _LEFT,
    right: tuple[str, ...] = _RIGHT,
    line_model: str = "csv_newline",
) -> TestArgumentDomainFact | None:
    return prove_test_argument_domain(
        material,
        path=material.path,
        content_digest=material.content_digest,
        key_columns=keys,
        left_columns=left,
        right_columns=right,
        line_model=line_model,
    )


def _base(rows: tuple[str, ...] = ("g1,1.0,2.0,3.0,4.0",)) -> bytes:
    return ("gene,x1,x2,y1,y2\n" + "\n".join(rows) + "\n").encode()


def test_fact_preserves_order_raw_lexemes_and_binary64_spellings() -> None:
    material = _material(_base(("g2,-1.5,2.00,3.25,4.0", "g1,0,1.0,-0,2.5")))
    fact = _prove(material)
    assert fact is not None
    assert fact.path == material.path
    assert fact.content_digest == material.content_digest
    assert fact.row_domain == argument_row_domain(
        material.path, material.content_digest, "csv_newline"
    )
    assert fact.header == ("gene", "x1", "x2", "y1", "y2")
    assert fact.key_value_tuples == (("g2",), ("g1",))
    assert fact.left_raw_measurement_lexemes == (("-1.5", "2.00"), ("0", "1.0"))
    assert fact.right_raw_measurement_lexemes == (("3.25", "4.0"), ("-0", "2.5"))
    assert fact.left_binary64_hex[0] == ((-1.5).hex(), (2.0).hex())
    assert len(set(fact.hypothesis_tokens)) == fact.row_count == 2


def test_composite_keys_are_exact_tuples_and_reordered_rows_are_retained() -> None:
    content = b"site,gene,x1,x2,y1,y2\ns2,g2,2,3,4,5\ns1,g1,1,2,3,4\n"
    fact = _prove(_material(content), keys=("site", "gene"))
    assert fact is not None
    assert fact.key_value_tuples == (("s2", "g2"), ("s1", "g1"))


@pytest.mark.parametrize(
    "content",
    [
        _base(("g1,1,2,3,4", "g1,5,6,7,8")),
        _base((",1,2,3,4",)),
        _base(("g1,,2,3,4",)),
        b"gene,x1,x2,y1,y2\ng1,1,2,3\n",
        b"gene,x1,x2,y1,y2\ng1,1,2,3,4,5\n",
        b"gene,x1,x1,y1,y2\ng1,1,2,3,4\n",
        b",x1,x2,y1,y2\ng1,1,2,3,4\n",
        b"gene,x1,x2,y1,y2\n",
        b"\xef\xbb\xbfgene,x1,x2,y1,y2\ng1,1,2,3,4\n",
    ],
)
def test_duplicate_missing_ragged_header_empty_and_bom_inputs_refuse(content: bytes) -> None:
    assert _prove(_material(content)) is None


@pytest.mark.parametrize(
    "raw",
    [
        "+1",
        "1e0",
        "1E0",
        ".5",
        "1.",
        " 1",
        "1 ",
        "1_0",
        "NaN",
        "Infinity",
        "-Infinity",
        "1e309",
        "-0.0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",
    ],
)
def test_nonclosed_or_nonfinite_measurement_lexemes_refuse(raw: str) -> None:
    assert _prove(_material(_base((f"g1,{raw},2,3,4",)))) is None


def test_columns_must_be_disjoint_and_cover_the_header_exactly() -> None:
    material = _material(_base())
    assert _prove(material, left=("x1", "x2"), right=("x2", "y2")) is None
    assert _prove(material, left=("x1", "x2"), right=("y1", "other")) is None
    extra = _material(b"gene,x1,x2,y1,y2,note\ng1,1,2,3,4,z\n")
    assert _prove(extra) is None
    assert _prove(material, left=("x1",), right=_RIGHT) is None


def test_digest_path_extension_utf8_and_post_construction_drift_refuse() -> None:
    material = _material(_base())
    assert (
        prove_test_argument_domain(
            material,
            path=material.path,
            content_digest="sha256:" + "0" * 64,
            key_columns=_KEYS,
            left_columns=_LEFT,
            right_columns=_RIGHT,
            line_model="csv_newline",
        )
        is None
    )
    assert _prove(_material(_base(), path="inputs/measurements.txt")) is None
    assert _prove(_material(b"gene,x1,x2,y1,y2\ng1,\xff,2,3,4\n")) is None
    object.__setattr__(material, "content", _base(("g1,9,2,3,4",)))
    assert _prove(material) is None


@pytest.mark.parametrize("line_model", ["splitlines", "csv_newline"])
def test_both_reader_models_and_trailing_blank_line(line_model: str) -> None:
    fact = _prove(_material(_base(("g1,1,2,3,4",)) + b"\n"), line_model=line_model)
    assert fact is not None
    assert fact.row_count == 1
    assert fact.reader_form == (
        "csv_dictreader_splitlines" if line_model == "splitlines" else "csv_dictreader_file"
    )


@pytest.mark.parametrize("separator", SPLITLINES_ONLY_SEPARATORS)
def test_splitlines_only_separators_are_guarded(separator: str) -> None:
    material = _material(_base(((f"g{separator}1,1,2,3,4"),)))
    assert _prove(material, line_model="splitlines") is None


def test_embedded_newline_uses_each_certified_reader_model() -> None:
    content = b'gene,x1,x2,y1,y2\n"g\n1",1,2,3,4\ng2,2,3,4,5\n'
    csv_fact = _prove(_material(content), line_model="csv_newline")
    split_fact = _prove(_material(content), line_model="splitlines")
    assert csv_fact is not None and split_fact is not None
    assert csv_fact.key_value_tuples == (("g\n1",), ("g2",))
    assert split_fact.key_value_tuples == (("g1",), ("g2",))
    assert csv_fact.row_domain != split_fact.row_domain


def _rows(row_count: int) -> bytes:
    return _base(tuple(f"g{index:05d},1,2,3,4" for index in range(row_count)))


def test_row_ceiling_boundary_and_plus_one() -> None:
    fact = _prove(_material(_rows(MAX_TEST_ARGUMENT_DOMAIN_ROWS)))
    assert fact is not None and fact.row_count == MAX_TEST_ARGUMENT_DOMAIN_ROWS
    assert _prove(_material(_rows(MAX_TEST_ARGUMENT_DOMAIN_ROWS + 1))) is None


def test_column_ceiling_boundary_and_plus_one() -> None:
    def build(column_count: int) -> tuple[bytes, tuple[str, ...]]:
        keys = tuple(f"k{index}" for index in range(column_count - 4))
        header = (*keys, "x1", "x2", "y1", "y2")
        row = (*(f"v{index}" for index in range(len(keys))), "1", "2", "3", "4")
        return (",".join(header) + "\n" + ",".join(row) + "\n").encode(), keys

    content, keys = build(MAX_TEST_ARGUMENT_DOMAIN_COLUMNS)
    fact = _prove(_material(content), keys=keys)
    assert fact is not None and len(fact.header) == MAX_TEST_ARGUMENT_DOMAIN_COLUMNS
    content, keys = build(MAX_TEST_ARGUMENT_DOMAIN_COLUMNS + 1)
    assert _prove(_material(content), keys=keys) is None


def test_field_ceiling_boundary_and_plus_one() -> None:
    boundary = "k" * MAX_TEST_ARGUMENT_DOMAIN_FIELD_BYTES
    fact = _prove(_material(_base((f"{boundary},1,2,3,4",))))
    assert fact is not None
    assert _prove(_material(_base((f"{boundary}k,1,2,3,4",)))) is None
    header_boundary = "k" * MAX_TEST_ARGUMENT_DOMAIN_FIELD_BYTES
    content = f"{header_boundary},x1,x2,y1,y2\ng1,1,2,3,4\n".encode()
    assert _prove(_material(content), keys=(header_boundary,)) is not None
    header_too_long = header_boundary + "k"
    content = f"{header_too_long},x1,x2,y1,y2\ng1,1,2,3,4\n".encode()
    assert _prove(_material(content), keys=(header_too_long,)) is None


def test_source_byte_ceiling_boundary_and_plus_one(monkeypatch: pytest.MonkeyPatch) -> None:
    material = _material(_base(("g1,1,2,3,4",)))
    boundary = len(material.content)
    monkeypatch.setattr(test_argument_domain, "MAX_TEST_ARGUMENT_DOMAIN_SOURCE_BYTES", boundary)
    assert _prove(material) is not None
    monkeypatch.setattr(
        test_argument_domain,
        "MAX_TEST_ARGUMENT_DOMAIN_SOURCE_BYTES",
        boundary - 1,
    )
    assert _prove(material) is None
    assert MAX_TEST_ARGUMENT_DOMAIN_SOURCE_BYTES == 1_000_000


def test_proof_record_ceiling_boundary_and_plus_one(monkeypatch: pytest.MonkeyPatch) -> None:
    material = _material(_base(("g1,1,2,3,4", "g2,2,3,4,5")))
    fact = _prove(material)
    assert fact is not None
    size = test_argument_domain._proof_record_byte_count(fact)
    monkeypatch.setattr(test_argument_domain, "MAX_TEST_ARGUMENT_DOMAIN_PROOF_RECORD_BYTES", size)
    assert _prove(material) is not None
    monkeypatch.setattr(
        test_argument_domain,
        "MAX_TEST_ARGUMENT_DOMAIN_PROOF_RECORD_BYTES",
        size - 1,
    )
    assert _prove(material) is None
    assert MAX_TEST_ARGUMENT_DOMAIN_PROOF_RECORD_BYTES == 8 * 1024 * 1024


def test_fuzz_agrees_with_dictreader_exact_order_and_float_values() -> None:
    rng = random.Random(20260811)
    values = ("0", "-0", "1", "-1.5", "2.00", "0.125")
    for _ in range(50):
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("gene", "x1", "x2", "y1", "y2"))
        for index in range(rng.randint(1, 30)):
            writer.writerow((f"g{index}", *(rng.choice(values) for _ in range(4))))
        content = stream.getvalue().encode()
        for line_model in ("csv_newline", "splitlines"):
            fact = _prove(_material(content), line_model=line_model)
            assert fact is not None
            source = (
                io.StringIO(content.decode(), newline="")
                if line_model == "csv_newline"
                else content.decode().splitlines()
            )
            expected = tuple(csv.DictReader(source))
            assert fact.key_value_tuples == tuple((row["gene"],) for row in expected)
            assert fact.left_raw_measurement_lexemes == tuple(
                (row["x1"], row["x2"]) for row in expected
            )
