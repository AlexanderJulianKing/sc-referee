"""Digest-bound symbolic count-set proofs for dependence growth-2."""

from __future__ import annotations

import csv
import io
from dataclasses import asdict

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.dependence_recognition.csv_domain import _parse_unit_key_domain
from sc_referee.dependence_recognition.ir import (
    MAX_V1_MEMBERSHIPS,
    SPLITLINES_ONLY_SEPARATORS,
    RecordRef,
)
from sc_referee.dependence_recognition_v2.ir import (
    CountDomainRow,
    CountOperandObligation,
    CountPredicateAtom,
    CountProcedureFact,
    CountProcedureObligation,
    CountSetProof,
)
from sc_referee.scientific_checks.core import FrozenMaterialInput


def prove_count_procedure_domain(
    material: FrozenMaterialInput,
    *,
    obligation: CountProcedureObligation,
) -> CountProcedureFact | None:
    """Prove all symbolic count sets; ambiguity returns ``None``."""

    fact, _reason = prove_count_procedure_domain_with_reason(material, obligation=obligation)
    return fact


def prove_count_procedure_domain_with_reason(
    material: FrozenMaterialInput,
    *,
    obligation: CountProcedureObligation,
) -> tuple[CountProcedureFact | None, str | None]:
    """Controller API retaining one granular safe refusal reason."""

    if (
        material.path != obligation.path
        or material.content_digest != obligation.content_digest
        or sha256_digest(material.content) != obligation.content_digest
    ):
        return None, "group-domain-binding-mismatch"
    if obligation.encoding not in {"utf-8", "ascii"}:
        return None, "unsupported-reader-encoding"
    ascii_proven = material.content.isascii()
    if obligation.encoding == "ascii" and not ascii_proven:
        return None, "reader-bytes-not-ascii"
    try:
        text = material.content.decode("utf-8", errors="strict")
        reader = _reader(text, obligation.line_model)
        if reader is None or reader.fieldnames is None:
            return None, "group-domain-unproven"
        rows = list(reader)
    except (csv.Error, UnicodeError, ValueError, OverflowError):
        return None, "group-domain-unproven"
    header = tuple(reader.fieldnames)
    if (
        not rows
        or len(header) != len(set(header))
        or any(not item for item in header)
        or obligation.authorized_unit_column not in header
        or any(None in row or any(row.get(column) is None for column in header) for row in rows)
    ):
        return None, "group-domain-unproven"
    atoms = (
        *obligation.universe_atoms,
        *(atom for operand in obligation.operands for atom in operand.domain_atoms),
        *(atom for operand in obligation.operands for atom in operand.predicate_atoms),
    )
    if any(atom.column not in header for atom in atoms):
        return None, "group-domain-unproven"
    if any(row.get(obligation.authorized_unit_column) == "" for row in rows):
        return None, "group-key-or-unit-cell-empty"
    if any(
        group.group_key_column not in header
        or not group.predeclared_bucket_keys
        or len(group.predeclared_bucket_keys) != len(set(group.predeclared_bucket_keys))
        or any(row.get(group.group_key_column) not in group.predeclared_bucket_keys for row in rows)
        for group in obligation.group_domains
    ):
        return None, "group-set-not-closed"
    parsed = _parse_unit_key_domain(
        material,
        path=obligation.path,
        content_digest=obligation.content_digest,
        key_columns=(obligation.authorized_unit_column,),
        line_model=obligation.line_model,
    )
    if (
        parsed is None
        or len(parsed.key_value_tuples) > MAX_V1_MEMBERSHIPS
        or len(rows) != len(parsed.key_value_tuples)
    ):
        return None, "group-domain-unproven"

    universe = tuple(
        index for index, row in enumerate(rows, start=1) if _matches(row, obligation.universe_atoms)
    )
    proofs = tuple(
        _prove_operand(
            operand,
            rows=rows,
            path=obligation.path,
            content_digest=obligation.content_digest,
            unit_column=obligation.authorized_unit_column,
        )
        for operand in obligation.operands
    )
    domain_rows = tuple(
        CountDomainRow(
            row_index=index,
            values=tuple((column, str(row[column])) for column in header),
            observation_id=(
                "observation:"
                + semantic_digest(
                    {"path": obligation.path, "digest": obligation.content_digest, "row": index}
                )
            ),
            authorized_unit_id=(
                "unit-key:"
                + semantic_digest(
                    {
                        "column": obligation.authorized_unit_column,
                        "value": row[obligation.authorized_unit_column],
                    }
                )
            ),
        )
        for index, row in enumerate(rows, start=1)
    )
    return (
        CountProcedureFact(
            evidence_id=("dependence-growth-count-proof:" + semantic_digest(asdict(obligation))),
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
            header=header,
            authorized_unit_column=obligation.authorized_unit_column,
            row_count=len(rows),
            rows=domain_rows,
            operands=proofs,
            universe_row_indices=universe,
        ),
        None,
    )


def _prove_operand(
    operand: CountOperandObligation,
    *,
    rows: list[dict[str | None, str | None]],
    path: str,
    content_digest: str,
    unit_column: str,
) -> CountSetProof:
    indices = tuple(
        index
        for index, row in enumerate(rows, start=1)
        if _matches(row, operand.domain_atoms) and _matches(row, operand.predicate_atoms)
    )
    return CountSetProof(
        operand_id=operand.operand_id,
        position=operand.position,
        row_indices=indices,
        observation_ids=tuple(
            "observation:" + semantic_digest({"path": path, "digest": content_digest, "row": index})
            for index in indices
        ),
        authorized_unit_ids=tuple(
            "unit-key:"
            + semantic_digest({"column": unit_column, "value": rows[index - 1][unit_column]})
            for index in indices
        ),
        cardinality=len(indices),
    )


def _matches(row: dict[str | None, str | None], atoms: tuple[CountPredicateAtom, ...]) -> bool:
    for atom in atoms:
        value = row.get(atom.column)
        if not isinstance(value, str):
            return False
        if atom.operator == "eq" and value != atom.literal:
            return False
        if atom.operator == "ne" and value == atom.literal:
            return False
    return True


def _reader(text: str, line_model: str) -> csv.DictReader[str] | None:
    if line_model == "splitlines":
        if any(separator in text for separator in SPLITLINES_ONLY_SEPARATORS):
            return None
        return csv.DictReader(text.splitlines())
    if line_model == "csv_newline":
        return csv.DictReader(io.StringIO(text, newline=""))
    return None
