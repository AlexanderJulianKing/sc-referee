"""Closed human confirmation bound to safe paths, bytes, semantics, and actors."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import yaml

from .digest import digest_fields, digest_text_sequence
from .paths import source_byte_hash
from .schema import (
    DECLARATION_SCHEMA_ID, ConfirmationProvenance, EmptyDropletIngestDeclaration,
    EmptyDropletUnavailableReason, EmptyDropletValidationError, FilteredLinkDeclaration,
    IntegrityRecord, MembershipDeclaration, ProposalProvenance, SourceDeclaration,
)


_TOP = {"schema_id", "confirmed_by_human", "source", "membership", "filtered_link", "proposal", "confirmation", "integrity"}
_SOURCE = {"role", "format", "compression", "path", "barcode_key_column", "total_count_column", "gene_count_columns", "namespace"}
_MEMBERSHIP = {"method_id"}
_FILTERED = {"path", "format", "compression", "cell_key_column", "total_count_column", "gene_count_columns", "namespace"}
_PROPOSAL = {"proposer_kind", "proposer_id", "evidence"}
_CONFIRMATION = {"confirmer_actor_id", "confirmation_event_id", "confirmed_at"}
_INTEGRITY = {"source_sha256", "filtered_source_sha256", "semantic_digest"}


def _closed(value, fields: set[str], name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ValueError(f"{name} must have exactly the closed schema fields")
    return value


def _strings(values, name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(values, list) or not values or not all(isinstance(v, str) for v in values):
        raise ValueError(f"{name} must be a non-empty string list")
    if not allow_empty and any(not value for value in values):
        raise ValueError(f"{name} cannot contain empty identities")
    return tuple(values)


def declaration_from_mapping(value: Mapping[str, object]) -> EmptyDropletIngestDeclaration:
    top = _closed(value, _TOP, "declaration")
    if top["schema_id"] != DECLARATION_SCHEMA_ID or not isinstance(top["confirmed_by_human"], bool):
        raise ValueError("unsupported declaration schema or confirmation flag")
    source = _closed(top["source"], _SOURCE, "source")
    membership = _closed(top["membership"], _MEMBERSHIP, "membership")
    filtered = _closed(top["filtered_link"], _FILTERED, "filtered_link")
    proposal = _closed(top["proposal"], _PROPOSAL, "proposal")
    confirmation = _closed(top["confirmation"], _CONFIRMATION, "confirmation")
    integrity = _closed(top["integrity"], _INTEGRITY, "integrity")
    scalar_groups = (
        (source, _SOURCE - {"gene_count_columns"}, "source"),
        (membership, _MEMBERSHIP, "membership"),
        (filtered, _FILTERED - {"gene_count_columns"}, "filtered_link"),
        (proposal, _PROPOSAL - {"evidence"}, "proposal"),
        (confirmation, _CONFIRMATION, "confirmation"),
        (integrity, _INTEGRITY, "integrity"),
    )
    for group, fields, name in scalar_groups:
        if any(not isinstance(group[field], str) for field in fields):
            raise ValueError(f"{name} scalar fields must be strings")
    evidence = _strings(proposal["evidence"], "proposal.evidence")
    return EmptyDropletIngestDeclaration(
        schema_id=top["schema_id"], confirmed_by_human=top["confirmed_by_human"],
        source=SourceDeclaration(**{**source, "gene_count_columns": _strings(source["gene_count_columns"], "source.gene_count_columns")}),
        membership=MembershipDeclaration(**membership),
        filtered_link=FilteredLinkDeclaration(**{**filtered, "gene_count_columns": _strings(filtered["gene_count_columns"], "filtered_link.gene_count_columns")}),
        proposal=ProposalProvenance(**{**proposal, "evidence": evidence}),
        confirmation=ConfirmationProvenance(**confirmation),
        integrity=IntegrityRecord(**integrity),
    )


def declaration_to_mapping(value: EmptyDropletIngestDeclaration) -> dict:
    return {
        "schema_id": value.schema_id, "confirmed_by_human": value.confirmed_by_human,
        "source": {
            "role": value.source.role, "format": value.source.format,
            "compression": value.source.compression, "path": value.source.path,
            "barcode_key_column": value.source.barcode_key_column,
            "total_count_column": value.source.total_count_column,
            "gene_count_columns": list(value.source.gene_count_columns),
            "namespace": value.source.namespace,
        },
        "membership": {"method_id": value.membership.method_id},
        "filtered_link": {
            "path": value.filtered_link.path, "format": value.filtered_link.format,
            "compression": value.filtered_link.compression,
            "cell_key_column": value.filtered_link.cell_key_column,
            "total_count_column": value.filtered_link.total_count_column,
            "gene_count_columns": list(value.filtered_link.gene_count_columns),
            "namespace": value.filtered_link.namespace,
        },
        "proposal": {
            "proposer_kind": value.proposal.proposer_kind,
            "proposer_id": value.proposal.proposer_id,
            "evidence": list(value.proposal.evidence),
        },
        "confirmation": {
            "confirmer_actor_id": value.confirmation.confirmer_actor_id,
            "confirmation_event_id": value.confirmation.confirmation_event_id,
            "confirmed_at": value.confirmation.confirmed_at,
        },
        "integrity": {
            "source_sha256": value.integrity.source_sha256,
            "filtered_source_sha256": value.integrity.filtered_source_sha256,
            "semantic_digest": value.integrity.semantic_digest,
        },
    }


def semantic_digest(value: EmptyDropletIngestDeclaration) -> str:
    source_genes = digest_text_sequence("confirmation-source-gene-columns", value.source.gene_count_columns)
    filtered_genes = digest_text_sequence("confirmation-filtered-gene-columns", value.filtered_link.gene_count_columns)
    evidence = digest_text_sequence("confirmation-proposal-evidence", value.proposal.evidence)
    return digest_fields("confirmation-semantics", (
        ("schema_id", value.schema_id), ("source.role", value.source.role),
        ("source.format", value.source.format), ("source.compression", value.source.compression),
        ("source.path", value.source.path), ("source.barcode_key_column", value.source.barcode_key_column),
        ("source.total_count_column", value.source.total_count_column), ("source.gene_count_columns", source_genes),
        ("source.namespace", value.source.namespace), ("membership.method_id", value.membership.method_id),
        ("filtered.path", value.filtered_link.path), ("filtered.format", value.filtered_link.format),
        ("filtered.compression", value.filtered_link.compression),
        ("filtered.cell_key_column", value.filtered_link.cell_key_column),
        ("filtered.total_count_column", value.filtered_link.total_count_column),
        ("filtered.gene_count_columns", filtered_genes), ("filtered.namespace", value.filtered_link.namespace),
        ("proposal.proposer_kind", value.proposal.proposer_kind),
        ("proposal.proposer_id", value.proposal.proposer_id), ("proposal.evidence", evidence),
    ))


def load_declaration(path: Path) -> EmptyDropletIngestDeclaration:
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError("declaration is unreadable") from exc
    return declaration_from_mapping(raw)


def confirm_declaration(
    path: Path, *, confirmer_actor_id: str, confirmation_event_id: str,
    confirmed_at: str | None = None,
) -> EmptyDropletIngestDeclaration:
    if not confirmer_actor_id or not confirmation_event_id:
        raise ValueError("confirmer actor and confirmation event are required")
    declaration = load_declaration(path)
    if declaration.confirmed_by_human:
        raise ValueError("reconfirmation requires a fresh proposed declaration")
    root = Path(path).resolve(strict=True).parent
    source_hash = source_byte_hash(root, declaration.source.path)
    filtered_hash = source_byte_hash(root, declaration.filtered_link.path)
    event_time = confirmed_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    confirmed = replace(
        declaration, confirmed_by_human=True,
        confirmation=ConfirmationProvenance(confirmer_actor_id, confirmation_event_id, event_time),
        integrity=IntegrityRecord(source_hash, filtered_hash, semantic_digest(declaration)),
    )
    Path(path).write_text(yaml.safe_dump(declaration_to_mapping(confirmed), sort_keys=False), encoding="utf-8")
    return confirmed


def validate_declaration_integrity(root: Path, value: EmptyDropletIngestDeclaration) -> None:
    if not value.confirmed_by_human or not value.confirmation.confirmer_actor_id or not value.confirmation.confirmation_event_id:
        raise EmptyDropletValidationError(
            EmptyDropletUnavailableReason.CONFIRMATION_PROVENANCE_INCOMPLETE,
            "declaration lacks complete human confirmation provenance",
        )
    try:
        source_hash = source_byte_hash(root, value.source.path)
        filtered_hash = source_byte_hash(root, value.filtered_link.path)
    except ValueError as exc:
        raise EmptyDropletValidationError(
            EmptyDropletUnavailableReason.SOURCE_UNREADABLE_OR_UNSAFE, str(exc)
        ) from exc
    expected_semantics = semantic_digest(value)
    if (
        source_hash != value.integrity.source_sha256
        or filtered_hash != value.integrity.filtered_source_sha256
        or expected_semantics != value.integrity.semantic_digest
    ):
        raise EmptyDropletValidationError(
            EmptyDropletUnavailableReason.INTEGRITY_DRIFT,
            "confirmed source bytes or semantic declaration changed",
        )
