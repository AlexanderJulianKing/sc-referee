"""Bounded digest-bound CSV unit-key multiplicity proofs.

This trusted prover reads only controller-frozen bytes.  It never imports or
executes project-authored code.  Its positive result is one closed
``UnitKeyMultiplicityFact`` for an exact ordered key, reader model, path, and
content digest.  Every ambiguity, malformed row, unsupported model, or budget
overflow returns ``None``.

The two line models deliberately reproduce the two certified runtime forms.
``splitlines`` means ``csv.DictReader(text.splitlines())`` and therefore
abstains when a separator unique to :meth:`str.splitlines` occurs anywhere.
``csv_newline`` means ``csv.DictReader`` over an untranslated text stream.
Facts proven under one model cannot be reused under the other.
"""

from __future__ import annotations

import csv
import io
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.dependence_recognition.ir import (
    MAX_DEPENDENCE_CSV_DOMAIN_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELDS,
    MAX_DEPENDENCE_CSV_DOMAIN_ROWS,
    MAX_V1_MEMBERSHIPS,
    RECOGNIZED_LINE_MODELS,
    RECOGNIZED_READER_MODELS,
    SPLITLINES_ONLY_SEPARATORS,
    ReaderForm,
    RecordRef,
    UnitKeyMultiplicityFact,
)
from sc_referee.scientific_checks.core import FrozenMaterialInput

# These are independent output budgets even where their numerical values match
# an input budget.  The first bounds the key map; the second bounds the complete
# canonical fact rather than only the source bytes.
MAX_DEPENDENCE_CSV_DISTINCT_KEYS = MAX_V1_MEMBERSHIPS
MAX_DEPENDENCE_CSV_PROOF_RECORD_BYTES = MAX_DEPENDENCE_CSV_DOMAIN_BYTES

_READER_FOR_LINE_MODEL: dict[str, ReaderForm] = {
    line_model: reader_form for reader_form, line_model in RECOGNIZED_READER_MODELS
}
_DIALECT = "excel"
_NORMALIZATION = "byte_exact_utf8"


def prove_unit_key_multiplicity(
    material: FrozenMaterialInput,
    *,
    path: str,
    content_digest: str,
    key_columns: tuple[str, ...],
    line_model: str,
) -> UnitKeyMultiplicityFact | None:
    """Prove exact per-row memberships and key multiplicities over frozen bytes.

    Key columns are an ordered composite key.  Values are compared exactly as
    strict UTF-8 strings returned by the certified ``csv.DictReader`` model:
    there is no trimming, case folding, numeric conversion, NA inference, or
    sentinel guessing.  An empty component, missing component, or ragged row
    abstains.  Both repeated and one-row-per-key domains produce positive facts.
    """

    if (
        line_model not in RECOGNIZED_LINE_MODELS
        or path != material.path
        or content_digest != material.content_digest
        or not path.lower().endswith(".csv")
        or not key_columns
        or len(key_columns) != len(set(key_columns))
        or any(not column for column in key_columns)
        or len(material.content) > MAX_DEPENDENCE_CSV_DOMAIN_BYTES
        or sha256_digest(material.content) != content_digest
    ):
        return None
    try:
        text = material.content.decode("utf-8", errors="strict")
        # ``utf-8`` intentionally does not erase a BOM.  Reject it rather than
        # silently changing the runtime header or accepting a BOM-prefixed key.
        if text.startswith("\ufeff"):
            return None
        splitlines_only_separators_absent = not any(
            separator in text for separator in SPLITLINES_ONLY_SEPARATORS
        )
        reader = _line_model_reader(text, line_model)
        if reader is None:
            return None
        header = reader.fieldnames
        if not _header_is_supported(header, key_columns):
            return None
        assert header is not None

        row_domain = _row_domain(path, content_digest, line_model)
        observation_ids: list[str] = []
        key_value_tuples: list[tuple[str, ...]] = []
        unit_ids: list[str] = []
        unit_id_by_key: dict[tuple[str, ...], str] = {}
        row_count = 0
        for row_count, row in enumerate(reader, start=1):
            if (
                row_count > MAX_DEPENDENCE_CSV_DOMAIN_ROWS
                or row_count > MAX_V1_MEMBERSHIPS
                or None in row
            ):
                return None
            values = tuple(row.get(name) for name in header)
            if any(value is None or not isinstance(value, str) for value in values):
                return None
            fields = tuple(value for value in values if isinstance(value, str))
            if len(fields) != len(header) or any(
                len(value.encode("utf-8")) > MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES
                for value in fields
            ):
                return None

            key = tuple(row.get(column) for column in key_columns)
            if any(value is None or not isinstance(value, str) or value == "" for value in key):
                return None
            exact_key = tuple(value for value in key if isinstance(value, str))
            if len(exact_key) != len(key_columns):
                return None
            unit_id = unit_id_by_key.get(exact_key)
            if unit_id is None:
                if len(unit_id_by_key) >= MAX_DEPENDENCE_CSV_DISTINCT_KEYS:
                    return None
                unit_id = _unit_id(key_columns, exact_key)
                unit_id_by_key[exact_key] = unit_id
            observation_ids.append(_observation_id(row_domain, row_count))
            key_value_tuples.append(exact_key)
            unit_ids.append(unit_id)
        if row_count == 0:
            return None
    except (csv.Error, UnicodeError, ValueError, OverflowError):
        return None

    counts = Counter(unit_ids)
    multiplicities = tuple(sorted(counts.items()))
    repeated_unit_ids = tuple(sorted(unit_id for unit_id, count in counts.items() if count > 1))
    fact = UnitKeyMultiplicityFact(
        evidence_id=_evidence_id(path, content_digest, key_columns, line_model),
        path=path,
        content_digest=content_digest,
        file_ref=RecordRef(material.file_ref.record_type, material.file_ref.record_id),
        asset_identity_ref=RecordRef(
            material.asset_identity_ref.record_type,
            material.asset_identity_ref.record_id,
        ),
        reader_form=_READER_FOR_LINE_MODEL[line_model],
        line_model=line_model,
        splitlines_only_separators_absent=splitlines_only_separators_absent,
        dialect=_DIALECT,
        row_domain=row_domain,
        source_byte_count=len(material.content),
        header=tuple(header),
        key_columns=key_columns,
        normalization=_NORMALIZATION,
        declared_missing_value_tokens=(),
        missing_key_value_count=0,
        row_shape_complete=True,
        row_count=row_count,
        observation_ids=tuple(observation_ids),
        key_value_tuples=tuple(key_value_tuples),
        unit_ids=tuple(unit_ids),
        distinct_key_count=len(unit_id_by_key),
        multiplicities=multiplicities,
        repeated_unit_ids=repeated_unit_ids,
    )
    if _proof_record_byte_count(fact) > MAX_DEPENDENCE_CSV_PROOF_RECORD_BYTES:
        return None
    return fact


def _header_is_supported(
    header: Sequence[str] | None,
    key_columns: tuple[str, ...],
) -> bool:
    return bool(
        header
        and len(header) <= MAX_DEPENDENCE_CSV_DOMAIN_FIELDS
        and len(header) == len(set(header))
        and set(key_columns) <= set(header)
        and all(
            item and len(item.encode("utf-8")) <= MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES
            for item in header
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


def _row_domain(path: str, content_digest: str, line_model: str) -> str:
    return semantic_digest(
        {
            "kind": "dependence-csv-row-domain-v1",
            "path": path,
            "content_digest": content_digest,
            "line_model": line_model,
            "dialect": _DIALECT,
        }
    )


def _observation_id(row_domain: str, row_index: int) -> str:
    return f"observation:{semantic_digest({'row_domain': row_domain, 'row_index': row_index})}"


def _unit_id(key_columns: tuple[str, ...], key: tuple[str, ...]) -> str:
    return f"unit-key:{semantic_digest({'key_columns': key_columns, 'key_values': key})}"


def _evidence_id(
    path: str,
    content_digest: str,
    key_columns: tuple[str, ...],
    line_model: str,
) -> str:
    return f"dependence-csv-proof:{semantic_digest({'path': path, 'content_digest': content_digest, 'key_columns': key_columns, 'line_model': line_model})}"


def _proof_record_byte_count(fact: UnitKeyMultiplicityFact) -> int:
    return len(canonical_json(asdict(fact)).encode("utf-8"))
