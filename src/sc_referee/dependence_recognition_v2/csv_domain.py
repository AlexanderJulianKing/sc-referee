"""Digest-bound ordered group-sequence proofs for dependence growth-1."""

from __future__ import annotations

import csv
import io
import re
from collections import defaultdict
from dataclasses import asdict
from typing import cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.dependence_recognition.csv_domain import _parse_unit_key_domain
from sc_referee.dependence_recognition.ir import (
    MAX_DEPENDENCE_CSV_DOMAIN_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES,
    MAX_DEPENDENCE_CSV_DOMAIN_FIELDS,
    MAX_DEPENDENCE_CSV_DOMAIN_ROWS,
    MAX_V1_MEMBERSHIPS,
    SPLITLINES_ONLY_SEPARATORS,
    RecordRef,
)
from sc_referee.dependence_recognition_v2.ir import (
    MAX_V2_GROUPS,
    CastKind,
    GroupValueSequence,
    GroupValueSequenceFact,
    GroupValueSequenceObligation,
)
from sc_referee.dependence_recognition_v2.pandas_runtime_premise import (
    PANDAS_3_0_5_DEFAULT_MISSING_TOKENS,
    PANDAS_GROUP_CASEFOLD_REFUSALS,
    PANDAS_GROUP_LITERAL_PATTERN,
    PANDAS_VALUE_PATTERN,
)
from sc_referee.scientific_checks.core import FrozenMaterialInput


def prove_group_value_sequences(
    material: FrozenMaterialInput,
    *,
    path: str,
    content_digest: str,
    line_model: str,
    reader_form: str,
    encoding: str,
    authorized_unit_column: str,
    group_key_column: str,
    value_column: str,
    cast_kind: CastKind,
    predeclared_bucket_keys: tuple[str, ...] = (),
) -> GroupValueSequenceFact | None:
    """Prove ordered group sequences; every ambiguity returns ``None``."""

    fact, _reason = prove_group_value_sequences_with_reason(
        material,
        obligation=GroupValueSequenceObligation(
            path=path,
            content_digest=content_digest,
            line_model=line_model,
            reader_form=reader_form,
            encoding=encoding,
            authorized_unit_column=authorized_unit_column,
            group_key_column=group_key_column,
            value_column=value_column,
            cast_kind=cast_kind,
            predeclared_bucket_keys=predeclared_bucket_keys,
        ),
    )
    return fact


def prove_group_value_sequences_with_reason(
    material: FrozenMaterialInput,
    *,
    obligation: GroupValueSequenceObligation,
) -> tuple[GroupValueSequenceFact | None, str | None]:
    """Internal controller API retaining one granular safe refusal reason."""

    if obligation.pandas_source is not None:
        return prove_pandas_group_value_sequences_with_reason(material, obligation=obligation)

    if (
        obligation.path != material.path
        or obligation.content_digest != material.content_digest
        or sha256_digest(material.content) != obligation.content_digest
    ):
        return None, "group-domain-binding-mismatch"
    if obligation.group_key_column == obligation.value_column:
        return None, "group-key-equals-value-column"
    if obligation.group_key_column == obligation.authorized_unit_column:
        return None, "group-key-is-unit-column"
    if obligation.encoding not in {"utf-8", "ascii"}:
        return None, "unsupported-reader-encoding"
    ascii_proven = material.content.isascii()
    if obligation.encoding == "ascii" and not ascii_proven:
        return None, "reader-bytes-not-ascii"
    diagnostic = _shape_diagnostic(material.content, obligation)
    if diagnostic is not None:
        return None, diagnostic
    parsed = _parse_unit_key_domain(
        material,
        path=obligation.path,
        content_digest=obligation.content_digest,
        key_columns=(obligation.authorized_unit_column,),
        line_model=obligation.line_model,
    )
    if parsed is None or len(parsed.key_value_tuples) > MAX_V1_MEMBERSHIPS:
        return None, "group-domain-unproven"
    if len(set(parsed.key_value_tuples)) > 5_000:
        return None, "group-domain-unproven"
    try:
        text = material.content.decode("utf-8", errors="strict")
        reader = _reader(text, obligation.line_model)
        if reader is None or reader.fieldnames is None:
            return None, "group-domain-unproven"
        rows = list(reader)
    except (csv.Error, UnicodeError, ValueError, OverflowError):
        return None, "group-domain-unproven"
    if len(rows) != len(parsed.key_value_tuples):
        return None, "group-domain-unproven"

    grouped: dict[str, list[tuple[int, str, str, str]]] = defaultdict(list)
    for index, row in enumerate(rows, start=1):
        group = row.get(obligation.group_key_column)
        value = row.get(obligation.value_column)
        unit = row.get(obligation.authorized_unit_column)
        if not all(isinstance(item, str) for item in (group, value, unit)):
            return None, "group-domain-unproven"
        if group == "" or unit == "":
            return None, "group-key-or-unit-cell-empty"
        if value == "":
            return None, "group-value-cast-unproven"
        assert isinstance(group, str) and isinstance(value, str) and isinstance(unit, str)
        try:
            converted = _apply_cast(value, obligation.cast_kind)
        except (TypeError, ValueError, OverflowError):
            return None, "group-value-cast-unproven"
        unit_id = f"unit-key:{semantic_digest({'column': obligation.authorized_unit_column, 'value': unit})}"
        observation_id = f"observation:{semantic_digest({'path': obligation.path, 'digest': obligation.content_digest, 'row': index})}"
        grouped[group].append((index, observation_id, unit_id, repr(converted)))
        if len(grouped) > MAX_V2_GROUPS:
            return None, "group-operand-arity-mismatch"
    observed_keys = set(grouped)
    if obligation.predeclared_bucket_keys and not observed_keys <= set(
        obligation.predeclared_bucket_keys
    ):
        return None, "group-set-not-closed"
    if obligation.predeclared_bucket_keys and observed_keys != set(
        obligation.predeclared_bucket_keys
    ):
        return None, "group-bucket-unpopulated"
    sequences = tuple(
        GroupValueSequence(
            group_key=key,
            row_indices=tuple(item[0] for item in grouped[key]),
            observation_ids=tuple(item[1] for item in grouped[key]),
            authorized_unit_ids=tuple(item[2] for item in grouped[key]),
            source_values=tuple(
                cast(str, rows[item[0] - 1][obligation.value_column]) for item in grouped[key]
            ),
            cast_value_reprs=tuple(item[3] for item in grouped[key]),
        )
        for key in sorted(grouped)
    )
    fact = GroupValueSequenceFact(
        evidence_id=f"dependence-growth-group-proof:{semantic_digest(asdict(obligation))}",
        path=obligation.path,
        content_digest=obligation.content_digest,
        file_ref=RecordRef(material.file_ref.record_type, material.file_ref.record_id),
        asset_identity_ref=RecordRef(
            material.asset_identity_ref.record_type,
            material.asset_identity_ref.record_id,
        ),
        line_model=obligation.line_model,
        reader_form=obligation.reader_form,
        encoding=obligation.encoding,
        ascii_bytes_proven=ascii_proven,
        header=parsed.header,
        authorized_unit_column=obligation.authorized_unit_column,
        group_key_column=obligation.group_key_column,
        value_column=obligation.value_column,
        cast_kind=obligation.cast_kind,
        row_count=len(rows),
        groups=sequences,
        predeclared_bucket_keys=obligation.predeclared_bucket_keys,
    )
    return fact, None


def prove_pandas_group_value_sequences_with_reason(
    material: FrozenMaterialInput,
    *,
    obligation: GroupValueSequenceObligation,
) -> tuple[GroupValueSequenceFact | None, str | None]:
    """Reconstruct Growth-14 operands from the original no-terminal-LF bytes.

    Physical validation deliberately precedes decoding and record splitting.  This
    controller/analyzer implementation is separate from the certificate kernel's
    byte scanner.
    """

    failure = "pandas-material-domain-unproven"
    descriptor = obligation.pandas_source
    if descriptor is None:
        return None, failure
    try:
        if (
            material.path != obligation.path
            or material.content_digest != obligation.content_digest
            or sha256_digest(material.content) != obligation.content_digest
            or obligation.line_model != "pandas_no_terminal_lf"
            or obligation.reader_form != "pandas_read_csv_simple"
            or obligation.encoding != "ascii"
            or obligation.cast_kind != "pandas_numeric"
            or obligation.path != descriptor.reader_path
            or obligation.group_key_column != descriptor.group_column
            or obligation.value_column != descriptor.value_column
            or len(descriptor.operands) != 2
        ):
            return None, failure
        records = _pandas_analyzer_physical_records(material.content)
        if records is None:
            return None, failure
        fields = [record.split(b",") for record in records]
        width = len(fields[0])
        if (
            width == 0
            or width > MAX_DEPENDENCE_CSV_DOMAIN_FIELDS
            or len(fields) - 1 > MAX_DEPENDENCE_CSV_DOMAIN_ROWS
            or len(fields) - 1 > MAX_V1_MEMBERSHIPS
            or any(len(record) != width for record in fields)
            or any(
                len(cell) > MAX_DEPENDENCE_CSV_DOMAIN_FIELD_BYTES
                for record in fields
                for cell in record
            )
        ):
            return None, failure
        header = tuple(cell.decode("ascii", errors="strict") for cell in fields[0])
        if (
            any(
                not name or name != name.strip() or name in PANDAS_3_0_5_DEFAULT_MISSING_TOKENS
                for name in header
            )
            or len(header) != len(set(header))
            or len({name.casefold() for name in header}) != len(header)
            or len(
                {
                    obligation.authorized_unit_column,
                    obligation.group_key_column,
                    obligation.value_column,
                }
            )
            != 3
            or not {
                obligation.authorized_unit_column,
                obligation.group_key_column,
                obligation.value_column,
            }
            <= set(header)
        ):
            return None, failure
        unit_index = header.index(obligation.authorized_unit_column)
        group_index = header.index(obligation.group_key_column)
        value_index = header.index(obligation.value_column)
        group_keys = tuple(item.group_key for item in descriptor.operands)
        if (
            len(group_keys) != 2
            or len(set(group_keys)) != 2
            or obligation.predeclared_bucket_keys != group_keys
            or any(
                re.fullmatch(PANDAS_GROUP_LITERAL_PATTERN, key, flags=re.ASCII) is None
                or key.casefold() in PANDAS_GROUP_CASEFOLD_REFUSALS
                for key in group_keys
            )
        ):
            return None, failure
        dropna_selected = any(item.projection == "dropna" for item in descriptor.operands)
        decoded_rows: list[tuple[str, ...]] = []
        integer_dtype = True
        for raw_row in fields[1:]:
            row = tuple(cell.decode("ascii", errors="strict") for cell in raw_row)
            for column_index, cell in enumerate(row):
                if not cell or cell != cell.strip():
                    if column_index == value_index and dropna_selected:
                        return None, "pandas-dropna-not-proven"
                    return None, failure
                if cell in PANDAS_3_0_5_DEFAULT_MISSING_TOKENS:
                    if column_index == value_index and dropna_selected:
                        return None, "pandas-dropna-not-proven"
                    return None, failure
            if (
                row[group_index] not in group_keys
                or re.fullmatch(PANDAS_VALUE_PATTERN, row[value_index], flags=re.ASCII) is None
            ):
                return None, failure
            integer_dtype = integer_dtype and "." not in row[value_index]
            decoded_rows.append(row)
        if not decoded_rows:
            return None, failure

        grouped: dict[str, list[tuple[int, str, str, str, str]]] = defaultdict(list)
        distinct_units: set[str] = set()
        for row_index, row in enumerate(decoded_rows, start=1):
            group = row[group_index]
            unit = row[unit_index]
            source_value = row[value_index]
            distinct_units.add(unit)
            if len(distinct_units) > 5_000:
                return None, failure
            rebuilt = float(source_value)
            grouped[group].append(
                (
                    row_index,
                    f"observation:{semantic_digest({'path': obligation.path, 'digest': obligation.content_digest, 'row': row_index})}",
                    f"unit-key:{semantic_digest({'column': obligation.authorized_unit_column, 'value': unit})}",
                    source_value,
                    repr(rebuilt),
                )
            )
        if set(grouped) != set(group_keys):
            return None, failure
        groups = tuple(
            GroupValueSequence(
                group_key=key,
                row_indices=tuple(item[0] for item in grouped[key]),
                observation_ids=tuple(item[1] for item in grouped[key]),
                authorized_unit_ids=tuple(item[2] for item in grouped[key]),
                source_values=tuple(item[3] for item in grouped[key]),
                cast_value_reprs=tuple(item[4] for item in grouped[key]),
            )
            for key in sorted(grouped)
        )
        return (
            GroupValueSequenceFact(
                evidence_id=(
                    "dependence-growth-group-proof:" + semantic_digest(asdict(obligation))
                ),
                path=obligation.path,
                content_digest=obligation.content_digest,
                file_ref=RecordRef(material.file_ref.record_type, material.file_ref.record_id),
                asset_identity_ref=RecordRef(
                    material.asset_identity_ref.record_type,
                    material.asset_identity_ref.record_id,
                ),
                line_model=obligation.line_model,
                reader_form=obligation.reader_form,
                encoding=obligation.encoding,
                ascii_bytes_proven=True,
                header=header,
                authorized_unit_column=obligation.authorized_unit_column,
                group_key_column=obligation.group_key_column,
                value_column=obligation.value_column,
                cast_kind=obligation.cast_kind,
                row_count=len(decoded_rows),
                groups=groups,
                predeclared_bucket_keys=obligation.predeclared_bucket_keys,
                pandas_value_dtype="int64" if integer_dtype else "float64",
            ),
            None,
        )
    except (IndexError, UnicodeError, TypeError, ValueError, OverflowError, RecursionError):
        return None, failure


def _pandas_analyzer_physical_records(content: bytes) -> tuple[bytes, ...] | None:
    """Validate the bound physical stream before decode or record splitting."""

    if (
        not content
        or len(content) > MAX_DEPENDENCE_CSV_DOMAIN_BYTES
        or not content.isascii()
        or content.startswith(b"\xef\xbb\xbf")
        or content.startswith(b"\n")
        or content.endswith(b"\n")
        or b"\n\n" in content
        or b"\n" not in content
        or b"\r" in content
        or b"\x00" in content
        or b'"' in content
        or b"\\" in content
    ):
        return None
    # Splitting is permitted only after every physical byte invariant above is
    # established.  The original bytes are never stripped, appended, or rebuilt.
    records = tuple(content.split(b"\n"))
    return records if all(records) else None


def _apply_cast(value: str, cast_kind: CastKind) -> object:
    if cast_kind == "float":
        return float(value)
    if cast_kind == "int":
        return int(value)
    # Passing the raw CSV string to either v1 registered procedure is not a
    # consumable numeric operand.  The growth claim therefore refuses rather
    # than treating successful string extraction as procedure consumability.
    raise ValueError("uncast CSV strings are not certified numeric operands")


def _reader(text: str, line_model: str) -> csv.DictReader[str] | None:
    if line_model == "splitlines":
        if any(separator in text for separator in SPLITLINES_ONLY_SEPARATORS):
            return None
        return csv.DictReader(text.splitlines())
    if line_model == "csv_newline":
        return csv.DictReader(io.StringIO(text, newline=""))
    return None


def _shape_diagnostic(content: bytes, obligation: GroupValueSequenceObligation) -> str | None:
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return (
            "reader-bytes-not-ascii" if obligation.encoding == "ascii" else "group-domain-unproven"
        )
    if text.startswith("\ufeff"):
        return "bom-unsupported"
    reader = _reader(text, obligation.line_model)
    if reader is None:
        return "group-domain-unproven"
    header = reader.fieldnames
    if header and len(header) != len(set(header)):
        return "duplicate-header"
    if not header or any(not item for item in header):
        return "group-domain-unproven"
    if not {
        obligation.authorized_unit_column,
        obligation.group_key_column,
        obligation.value_column,
    } <= set(header):
        return "group-domain-unproven"
    try:
        for row in reader:
            if None in row or any(row.get(column) is None for column in header):
                return "ragged-row"
            if (
                row.get(obligation.authorized_unit_column) == ""
                or row.get(obligation.group_key_column) == ""
            ):
                return "group-key-or-unit-cell-empty"
    except csv.Error:
        return "ragged-row"
    return None
