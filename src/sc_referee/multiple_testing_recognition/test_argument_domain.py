"""Digest-bound CSV proofs for keyed executable test arguments.

This controller-side prover reads frozen measurement bytes only.  It does not
import or execute project-authored code.  It accepts the one measurement-table
shape authorized by the executable-grammar design: a nonempty composite key,
two disjoint vector-valued operand column groups, and no unselected metadata.

Measurement lexemes use the closed ASCII grammar
``-?(0|[1-9][0-9]*)(\.[0-9]+)?``.  Whitespace, plus signs, exponent notation,
underscores, non-finite values, overflow, and nonzero values that underflow to
binary64 zero are refused.  Raw spellings and independently rederived
``float.hex()`` values are retained; no normalization defines the join.
"""

from __future__ import annotations

import csv
import io
import math
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import cast

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.multiple_testing_recognition.ir import (
    MAX_TEST_ARGUMENT_DOMAIN_COLUMNS,
    MAX_TEST_ARGUMENT_DOMAIN_FIELD_BYTES,
    MAX_TEST_ARGUMENT_DOMAIN_PROOF_RECORD_BYTES,
    MAX_TEST_ARGUMENT_DOMAIN_ROWS,
    MAX_TEST_ARGUMENT_DOMAIN_SOURCE_BYTES,
    RECOGNIZED_READER_MODELS,
    SPLITLINES_ONLY_SEPARATORS,
    LineModel,
    ReaderForm,
    RecordRef,
    TestArgumentDomainFact,
)
from sc_referee.scientific_checks.core import FrozenMaterialInput

_DIALECT = "excel"
_MEASUREMENT = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", flags=re.ASCII)
_READER_FOR_LINE_MODEL: dict[str, ReaderForm] = {
    line_model: reader_form for reader_form, line_model in RECOGNIZED_READER_MODELS
}
_NORMALIZATION_BY_LINE_MODEL = {
    "splitlines": "splitlines_rejoined_utf8",
    "csv_newline": "byte_exact_utf8",
}


@dataclass(frozen=True)
class _ParsedArguments:
    header: tuple[str, ...]
    key_value_tuples: tuple[tuple[str, ...], ...]
    left_raw: tuple[tuple[str, ...], ...]
    right_raw: tuple[tuple[str, ...], ...]
    left_hex: tuple[tuple[str, ...], ...]
    right_hex: tuple[tuple[str, ...], ...]
    splitlines_only_separators_absent: bool


def prove_test_argument_domain(
    material: FrozenMaterialInput,
    *,
    path: str,
    content_digest: str,
    key_columns: tuple[str, ...],
    left_columns: tuple[str, ...],
    right_columns: tuple[str, ...],
    line_model: str,
) -> TestArgumentDomainFact | None:
    """Prove one exact unique-key map to two finite binary64 vectors."""

    parsed = _parse(
        material,
        path=path,
        content_digest=content_digest,
        key_columns=key_columns,
        left_columns=left_columns,
        right_columns=right_columns,
        line_model=line_model,
    )
    if parsed is None:
        return None
    row_domain = test_argument_row_domain(path, content_digest, line_model)
    row_count = len(parsed.key_value_tuples)
    observation_tokens = tuple(
        _observation_token(path, content_digest, row_domain, ordinal)
        for ordinal in range(1, row_count + 1)
    )
    hypothesis_tokens = tuple(
        _hypothesis_token(key_columns, key_values) for key_values in parsed.key_value_tuples
    )
    fact = TestArgumentDomainFact(
        evidence_id=_evidence_id(
            path,
            content_digest,
            key_columns,
            left_columns,
            right_columns,
            line_model,
        ),
        path=path,
        content_digest=content_digest,
        file_ref=RecordRef(material.file_ref.record_type, material.file_ref.record_id),
        asset_identity_ref=RecordRef(
            material.asset_identity_ref.record_type,
            material.asset_identity_ref.record_id,
        ),
        reader_form=_READER_FOR_LINE_MODEL[line_model],
        line_model=cast(LineModel, line_model),
        splitlines_only_separators_absent=parsed.splitlines_only_separators_absent,
        dialect=_DIALECT,
        row_domain=row_domain,
        source_byte_count=len(material.content),
        header=parsed.header,
        measurement_key_columns=key_columns,
        left_measurement_columns=left_columns,
        right_measurement_columns=right_columns,
        normalization=_NORMALIZATION_BY_LINE_MODEL[line_model],
        declared_missing_value_tokens=(),
        missing_key_value_count=0,
        missing_measurement_value_count=0,
        row_shape_complete=True,
        row_count=row_count,
        observation_tokens=observation_tokens,
        key_value_tuples=parsed.key_value_tuples,
        hypothesis_tokens=hypothesis_tokens,
        left_raw_measurement_lexemes=parsed.left_raw,
        right_raw_measurement_lexemes=parsed.right_raw,
        left_binary64_hex=parsed.left_hex,
        right_binary64_hex=parsed.right_hex,
    )
    if _proof_record_byte_count(fact) > MAX_TEST_ARGUMENT_DOMAIN_PROOF_RECORD_BYTES:
        return None
    return fact


def test_argument_row_domain(path: str, content_digest: str, line_model: str) -> str:
    """Return the stable identity for one certified measurement row domain."""

    return "test-argument-rows:" + semantic_digest(
        {
            "schema": "test-argument-row-domain-v1",
            "path": path,
            "content_digest": content_digest,
            "line_model": line_model,
        }
    )


def _parse(
    material: FrozenMaterialInput,
    *,
    path: str,
    content_digest: str,
    key_columns: tuple[str, ...],
    left_columns: tuple[str, ...],
    right_columns: tuple[str, ...],
    line_model: str,
) -> _ParsedArguments | None:
    groups = (key_columns, left_columns, right_columns)
    flat_columns = (*key_columns, *left_columns, *right_columns)
    if (
        line_model not in _READER_FOR_LINE_MODEL
        or path != material.path
        or content_digest != material.content_digest
        or not path.lower().endswith(".csv")
        or len(material.content) > MAX_TEST_ARGUMENT_DOMAIN_SOURCE_BYTES
        or sha256_digest(material.content) != content_digest
        or any(not group or len(group) != len(set(group)) for group in groups)
        or len(left_columns) < 2
        or len(right_columns) < 2
        or len(flat_columns) != len(set(flat_columns))
    ):
        return None
    try:
        text = material.content.decode("utf-8", errors="strict")
        if text.startswith("\ufeff"):
            return None
        separators_absent = not any(separator in text for separator in SPLITLINES_ONLY_SEPARATORS)
        reader = _line_model_reader(text, line_model)
        if reader is None or not _header_is_supported(reader.fieldnames, flat_columns):
            return None
        assert reader.fieldnames is not None
        header = tuple(reader.fieldnames)
        if any(
            len(value.encode("utf-8")) > MAX_TEST_ARGUMENT_DOMAIN_FIELD_BYTES for value in header
        ):
            return None
        keys: list[tuple[str, ...]] = []
        left_raw: list[tuple[str, ...]] = []
        right_raw: list[tuple[str, ...]] = []
        left_hex: list[tuple[str, ...]] = []
        right_hex: list[tuple[str, ...]] = []
        seen: set[tuple[str, ...]] = set()
        for row_count, row in enumerate(reader, start=1):
            if row_count > MAX_TEST_ARGUMENT_DOMAIN_ROWS or None in row:
                return None
            values = tuple(row.get(column) for column in header)
            if any(value is None or not isinstance(value, str) for value in values):
                return None
            fields = tuple(value for value in values if isinstance(value, str))
            if len(fields) != len(header) or any(
                len(value.encode("utf-8")) > MAX_TEST_ARGUMENT_DOMAIN_FIELD_BYTES
                for value in fields
            ):
                return None
            key = tuple(row.get(column) for column in key_columns)
            if any(value is None or not isinstance(value, str) or value == "" for value in key):
                return None
            exact_key = tuple(value for value in key if isinstance(value, str))
            if len(exact_key) != len(key_columns) or exact_key in seen:
                return None
            left = _measurement_vector(row, left_columns)
            right = _measurement_vector(row, right_columns)
            if left is None or right is None:
                return None
            seen.add(exact_key)
            keys.append(exact_key)
            left_raw.append(left[0])
            left_hex.append(left[1])
            right_raw.append(right[0])
            right_hex.append(right[1])
    except (csv.Error, UnicodeError, ValueError, OverflowError, MemoryError, RecursionError):
        return None
    if not keys:
        return None
    return _ParsedArguments(
        header,
        tuple(keys),
        tuple(left_raw),
        tuple(right_raw),
        tuple(left_hex),
        tuple(right_hex),
        separators_absent,
    )


def _measurement_vector(
    row: dict[str | None, str | list[str] | None],
    columns: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    raw_values: list[str] = []
    hex_values: list[str] = []
    for column in columns:
        raw = row.get(column)
        if not isinstance(raw, str) or not _MEASUREMENT.fullmatch(raw):
            return None
        try:
            exact = Decimal(raw)
            value = float(raw)
        except (InvalidOperation, ValueError, OverflowError):
            return None
        if not math.isfinite(value) or (exact != 0 and value == 0.0):
            return None
        raw_values.append(raw)
        hex_values.append(value.hex())
    return tuple(raw_values), tuple(hex_values)


def _line_model_reader(text: str, line_model: str) -> csv.DictReader[str] | None:
    if line_model == "splitlines":
        if any(separator in text for separator in SPLITLINES_ONLY_SEPARATORS):
            return None
        return csv.DictReader(text.splitlines(), dialect=_DIALECT)
    if line_model == "csv_newline":
        return csv.DictReader(io.StringIO(text, newline=""), dialect=_DIALECT)
    return None


def _header_is_supported(
    header: Sequence[str] | None,
    selected_columns: tuple[str, ...],
) -> bool:
    return bool(
        header
        and 0 < len(header) <= MAX_TEST_ARGUMENT_DOMAIN_COLUMNS
        and len(header) == len(set(header))
        and all(value for value in header)
        and len(header) == len(selected_columns)
        and set(header) == set(selected_columns)
    )


def _observation_token(path: str, digest: str, row_domain: str, ordinal: int) -> str:
    return "test-argument-observation:" + semantic_digest(
        {
            "schema": "test-argument-observation-v1",
            "path": path,
            "content_digest": digest,
            "row_domain": row_domain,
            "row_ordinal": ordinal,
        }
    )


def _hypothesis_token(columns: tuple[str, ...], values: tuple[str, ...]) -> str:
    return "family-hypothesis:" + semantic_digest(
        {
            "schema": "pvalue-family-hypothesis-v1",
            "key_columns": columns,
            "key_values": values,
        }
    )


def _proof_record_byte_count(fact: TestArgumentDomainFact) -> int:
    return len(canonical_json(asdict(fact)).encode("utf-8"))


def _evidence_id(
    path: str,
    digest: str,
    key_columns: tuple[str, ...],
    left_columns: tuple[str, ...],
    right_columns: tuple[str, ...],
    line_model: str,
) -> str:
    return "multiple-testing-test-argument-proof:" + semantic_digest(
        {
            "path": path,
            "content_digest": digest,
            "key_columns": key_columns,
            "left_columns": left_columns,
            "right_columns": right_columns,
            "line_model": line_model,
        }
    )


__all__ = ["prove_test_argument_domain", "test_argument_row_domain"]
