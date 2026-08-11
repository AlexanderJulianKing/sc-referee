"""Bounded digest-bound CSV proofs for ordered p-value families.

This controller-side prover reads only frozen material bytes.  It never imports
or executes project-authored code.  A positive result is one closed
``PValueFamilyFact`` for an exact path, digest, value column, and certified
reader model; malformed input, ambiguity, or budget overflow returns ``None``.

The public Stage-2 API deliberately names only ``value_column``.  To preserve
the Stage-1 fact and authority contract without guessing a unit key, the
ordered composite hypothesis key is the complete header, in source order,
excluding ``value_column``.  At least one such column is required, every key
tuple must be unique and nonempty, and later kernel verification requires the
human authority to name this exact ordered key.  Extra metadata therefore
narrows toward abstention rather than being silently discarded.

Raw p-value lexemes are retained byte-exactly as decoded UTF-8 field values.
The v1 numerical grammar is intentionally narrower than :class:`Decimal`:
unsigned ASCII fixed-point notation only (``DIGITS`` or ``DIGITS.DIGITS``).
Signs, exponent/scientific notation, whitespace, underscores, non-finite
values, and values outside ``[0, 1]`` are unsupported.  A separate canonical
fixed-point spelling is derived only for trusted arithmetic; it never defines
family scope or replaces the raw lexeme.

The two line models reproduce the certified runtime forms.  ``splitlines``
means ``csv.DictReader(text.splitlines())`` and refuses any separator unique to
``str.splitlines``.  ``csv_newline`` means
``csv.DictReader(open(path, ..., newline=""))`` and is reproduced using an
untranslated text stream.  A fact for one model cannot be reused for the other.
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import cast

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.multiple_testing_recognition.ir import (
    MAX_PVALUE_FAMILY_COLUMNS,
    MAX_PVALUE_FAMILY_FIELD_BYTES,
    MAX_PVALUE_FAMILY_PROOF_RECORD_BYTES,
    MAX_PVALUE_FAMILY_ROWS,
    MAX_PVALUE_FAMILY_SOURCE_BYTES,
    RECOGNIZED_READER_MODELS,
    SPLITLINES_ONLY_SEPARATORS,
    LineModel,
    PValueFamilyFact,
    ReaderForm,
    RecordRef,
)
from sc_referee.scientific_checks.core import FrozenMaterialInput

_DIALECT = "excel"
_FIXED_POINT_DECIMAL = re.compile(r"[0-9]+(?:\.[0-9]+)?", flags=re.ASCII)
_READER_FOR_LINE_MODEL: dict[str, ReaderForm] = {
    line_model: reader_form for reader_form, line_model in RECOGNIZED_READER_MODELS
}
_NORMALIZATION_BY_LINE_MODEL = {
    "splitlines": "splitlines_rejoined_utf8",
    "csv_newline": "byte_exact_utf8",
}


@dataclass(frozen=True)
class _ParsedPValueFamily:
    header: tuple[str, ...]
    hypothesis_key_columns: tuple[str, ...]
    key_value_tuples: tuple[tuple[str, ...], ...]
    raw_pvalue_lexemes: tuple[str, ...]
    canonical_pvalue_decimals: tuple[str, ...]
    splitlines_only_separators_absent: bool


def prove_pvalue_family(
    material: FrozenMaterialInput,
    *,
    path: str,
    content_digest: str,
    value_column: str,
    line_model: str,
) -> PValueFamilyFact | None:
    """Prove one exact ordered p-value family over controller-frozen CSV bytes.

    Equal p-value lexemes are allowed and remain distinct position-bound family
    values.  Hypothesis keys are the ordered tuple of every non-value column;
    duplicate or empty keys abstain.  No trimming, NA inference, float
    conversion, sorting, tolerance, or numerical matching is performed.
    """

    parsed = _parse_pvalue_family(
        material,
        path=path,
        content_digest=content_digest,
        value_column=value_column,
        line_model=line_model,
    )
    if parsed is None:
        return None

    row_count = len(parsed.key_value_tuples)
    row_domain = pvalue_family_row_domain(path, content_digest, line_model)
    observation_tokens = tuple(
        _observation_token(path, content_digest, row_domain, row_ordinal)
        for row_ordinal in range(1, row_count + 1)
    )
    hypothesis_tokens = tuple(
        _hypothesis_token(parsed.hypothesis_key_columns, key_values)
        for key_values in parsed.key_value_tuples
    )
    pvalue_tokens = tuple(
        _pvalue_token(row_domain, position, hypothesis_token, value_column)
        for position, hypothesis_token in enumerate(hypothesis_tokens)
    )
    fact = PValueFamilyFact(
        evidence_id=_evidence_id(
            path,
            content_digest,
            parsed.hypothesis_key_columns,
            value_column,
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
        hypothesis_key_columns=parsed.hypothesis_key_columns,
        pvalue_column=value_column,
        normalization=_NORMALIZATION_BY_LINE_MODEL[line_model],
        declared_missing_value_tokens=(),
        missing_key_value_count=0,
        missing_pvalue_count=0,
        row_shape_complete=True,
        row_count=row_count,
        observation_tokens=observation_tokens,
        key_value_tuples=parsed.key_value_tuples,
        hypothesis_tokens=hypothesis_tokens,
        raw_pvalue_lexemes=parsed.raw_pvalue_lexemes,
        canonical_pvalue_decimals=parsed.canonical_pvalue_decimals,
        pvalue_tokens=pvalue_tokens,
    )
    if _proof_record_byte_count(fact) > MAX_PVALUE_FAMILY_PROOF_RECORD_BYTES:
        return None
    return fact


def _parse_pvalue_family(
    material: FrozenMaterialInput,
    *,
    path: str,
    content_digest: str,
    value_column: str,
    line_model: str,
) -> _ParsedPValueFamily | None:
    if (
        line_model not in _READER_FOR_LINE_MODEL
        or path != material.path
        or content_digest != material.content_digest
        or not path.lower().endswith(".csv")
        or not value_column
        or len(material.content) > MAX_PVALUE_FAMILY_SOURCE_BYTES
        or sha256_digest(material.content) != content_digest
    ):
        return None
    try:
        text = material.content.decode("utf-8", errors="strict")
        if text.startswith("\ufeff"):
            return None
        splitlines_only_separators_absent = not any(
            separator in text for separator in SPLITLINES_ONLY_SEPARATORS
        )
        reader = _line_model_reader(text, line_model)
        if reader is None:
            return None
        header = reader.fieldnames
        if not _header_is_supported(header, value_column):
            return None
        assert header is not None
        hypothesis_key_columns = tuple(column for column in header if column != value_column)

        key_value_tuples: list[tuple[str, ...]] = []
        raw_pvalue_lexemes: list[str] = []
        canonical_pvalue_decimals: list[str] = []
        seen_keys: set[tuple[str, ...]] = set()
        for row_count, row in enumerate(reader, start=1):
            if row_count > MAX_PVALUE_FAMILY_ROWS or None in row:
                return None
            values = tuple(row.get(name) for name in header)
            if any(value is None or not isinstance(value, str) for value in values):
                return None
            fields = tuple(value for value in values if isinstance(value, str))
            if len(fields) != len(header) or any(
                len(value.encode("utf-8")) > MAX_PVALUE_FAMILY_FIELD_BYTES for value in fields
            ):
                return None

            key = tuple(row.get(column) for column in hypothesis_key_columns)
            if any(value is None or not isinstance(value, str) or value == "" for value in key):
                return None
            exact_key = tuple(value for value in key if isinstance(value, str))
            if len(exact_key) != len(hypothesis_key_columns) or exact_key in seen_keys:
                return None

            raw = row.get(value_column)
            if raw is None or not isinstance(raw, str):
                return None
            parsed_decimal = _parse_fixed_point_decimal(raw)
            if parsed_decimal is None:
                return None

            seen_keys.add(exact_key)
            key_value_tuples.append(exact_key)
            raw_pvalue_lexemes.append(raw)
            canonical_pvalue_decimals.append(_canonical_decimal(parsed_decimal))
        if not key_value_tuples:
            return None
    except (csv.Error, UnicodeError, ValueError, OverflowError, MemoryError):
        return None
    return _ParsedPValueFamily(
        header=tuple(header),
        hypothesis_key_columns=hypothesis_key_columns,
        key_value_tuples=tuple(key_value_tuples),
        raw_pvalue_lexemes=tuple(raw_pvalue_lexemes),
        canonical_pvalue_decimals=tuple(canonical_pvalue_decimals),
        splitlines_only_separators_absent=splitlines_only_separators_absent,
    )


def _header_is_supported(header: Sequence[str] | None, value_column: str) -> bool:
    return bool(
        header
        and len(header) <= MAX_PVALUE_FAMILY_COLUMNS
        and len(header) == len(set(header))
        and value_column in header
        and len(header) >= 2
        and all(
            item and len(item.encode("utf-8")) <= MAX_PVALUE_FAMILY_FIELD_BYTES for item in header
        )
    )


def _line_model_reader(text: str, line_model: str) -> csv.DictReader[str] | None:
    if line_model == "splitlines":
        if any(separator in text for separator in SPLITLINES_ONLY_SEPARATORS):
            return None
        return csv.DictReader(text.splitlines())
    if line_model == "csv_newline":
        return csv.DictReader(io.StringIO(text, newline=""))
    return None


def _parse_fixed_point_decimal(raw: str) -> Decimal | None:
    if _FIXED_POINT_DECIMAL.fullmatch(raw) is None:
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return None
    if not value.is_finite() or value < 0 or value > 1:
        return None
    return value


def _canonical_decimal(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def pvalue_family_row_domain(path: str, content_digest: str, line_model: str) -> str:
    """Return the row-domain identity without inspecting CSV contents."""

    return semantic_digest(
        {
            "kind": "multiple-testing-pvalue-family-row-domain-v1",
            "path": path,
            "content_digest": content_digest,
            "line_model": line_model,
            "dialect": _DIALECT,
        }
    )


def _observation_token(
    path: str,
    content_digest: str,
    row_domain: str,
    row_ordinal: int,
) -> str:
    return "family-observation:" + semantic_digest(
        {
            "schema": "pvalue-family-observation-v1",
            "path": path,
            "content_digest": content_digest,
            "row_domain": row_domain,
            "row_ordinal": row_ordinal,
        }
    )


def _hypothesis_token(
    key_columns: tuple[str, ...],
    key_values: tuple[str, ...],
) -> str:
    return "family-hypothesis:" + semantic_digest(
        {
            "schema": "pvalue-family-hypothesis-v1",
            "key_columns": key_columns,
            "key_values": key_values,
        }
    )


def _pvalue_token(
    row_domain: str,
    position: int,
    hypothesis_token: str,
    pvalue_column: str,
) -> str:
    return "family-pvalue:" + semantic_digest(
        {
            "schema": "pvalue-family-position-v1",
            "row_domain": row_domain,
            "position": position,
            "hypothesis_token": hypothesis_token,
            "pvalue_column": pvalue_column,
        }
    )


def _evidence_id(
    path: str,
    content_digest: str,
    hypothesis_key_columns: tuple[str, ...],
    value_column: str,
    line_model: str,
) -> str:
    return "multiple-testing-pvalue-family-proof:" + semantic_digest(
        {
            "path": path,
            "content_digest": content_digest,
            "hypothesis_key_columns": hypothesis_key_columns,
            "value_column": value_column,
            "line_model": line_model,
        }
    )


def _proof_record_byte_count(fact: PValueFamilyFact) -> int:
    return len(canonical_json(asdict(fact)).encode("utf-8"))


__all__ = ["prove_pvalue_family", "pvalue_family_row_domain"]
