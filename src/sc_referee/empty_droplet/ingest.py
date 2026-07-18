"""Fail-closed orchestration for empty_droplet_raw_counts/v1."""
from __future__ import annotations

from pathlib import Path

from .bundle_identity import capture_filtered_bundle_identity
from .confirmation import load_declaration, semantic_digest
from .csv_adapter import parse_empty_droplet_csv
from .digest import (
    digest_barcode_ledger, digest_bool_vector, digest_csr_u64, digest_feature_ledger,
    digest_fields, digest_membership_set, digest_text_sequence, digest_u64_vector,
)
from .link import build_filtered_link
from .paths import source_byte_hash
from .schema import (
    ARTIFACT_SCHEMA_ID, DIGEST_POLICY_ID, DECLARATION_SCHEMA_ID, ArtifactDigests,
    ArtifactUnavailable, Available, EmptyDropletCountsArtifact, EmptyDropletIngestDeclaration,
    EmptyDropletUnavailableReason as R, EmptyDropletValidationError, EvidenceItem,
    MembershipProvenance, SourceRecord,
)


ADAPTER_ID = "dense_csv_exact/v1"
MEMBERSHIP_METHOD_ID = "explicit_empty_table_rows/v1"


def _unavailable(reason: R, message: str, secondary: tuple[R, ...] = ()) -> ArtifactUnavailable:
    evidence = (EvidenceItem("validation", message),)
    actionable = {
        R.CONFIRMATION_PROVENANCE_INCOMPLETE, R.RAW_SOURCE_AMBIGUOUS,
        R.RAW_ROLE_UNCONFIRMED, R.RAW_MATRIX_ABSENT,
        R.UNFILTERED_BARCODE_UNIVERSE_ABSENT, R.EMPTY_SET_UNDEFINED,
        R.EMPTY_METHOD_UNVERIFIABLE, R.EMPTY_AUTHORITIES_CONFLICT,
        R.THRESHOLD_CONTRACT_INVALID, R.RAW_ASSEMBLY_SCOPE_UNVERIFIED,
    }
    return ArtifactUnavailable(
        reason_code=reason, message=message, evidence=evidence,
        actionability="supply_and_confirm" if reason in actionable else "correct_or_replace_input",
        secondary_reason_codes=secondary,
    )


def _failure_result(failures: list[tuple[R, str]]) -> ArtifactUnavailable:
    unique: dict[R, str] = {}
    for reason, message in failures:
        unique.setdefault(reason, message)
    ordered = sorted(unique, key=lambda reason: tuple(R).index(reason))
    primary = ordered[0]
    return _unavailable(primary, unique[primary], tuple(ordered[1:]))


def _declaration_failures(root: Path, declaration: EmptyDropletIngestDeclaration):
    failures: list[tuple[R, str]] = []
    hashes: dict[str, str] = {}
    for name, relative in (
        ("source", declaration.source.path), ("filtered", declaration.filtered_link.path)
    ):
        try:
            hashes[name] = source_byte_hash(root, relative)
        except ValueError as exc:
            failures.append((R.SOURCE_UNREADABLE_OR_UNSAFE, str(exc)))
    confirmation_complete = (
        declaration.confirmed_by_human
        and bool(declaration.confirmation.confirmer_actor_id)
        and bool(declaration.confirmation.confirmation_event_id)
        and bool(declaration.confirmation.confirmed_at)
    )
    if not confirmation_complete:
        failures.append((R.CONFIRMATION_PROVENANCE_INCOMPLETE, "human confirmation provenance is incomplete"))
    integrity_populated = any((
        declaration.integrity.source_sha256,
        declaration.integrity.filtered_source_sha256,
        declaration.integrity.semantic_digest,
    ))
    if hashes.keys() == {"source", "filtered"} and (integrity_populated or declaration.confirmed_by_human):
        if (
            hashes["source"] != declaration.integrity.source_sha256
            or hashes["filtered"] != declaration.integrity.filtered_source_sha256
            or semantic_digest(declaration) != declaration.integrity.semantic_digest
        ):
            failures.append((R.INTEGRITY_DRIFT, "confirmed source bytes or semantic declaration changed"))
    if declaration.source.role != "explicit_empty_droplet_count_table":
        failures.append((R.RAW_ROLE_UNCONFIRMED, "empty table role is not confirmed"))
    if declaration.membership.method_id != MEMBERSHIP_METHOD_ID:
        failures.append((R.EMPTY_METHOD_UNVERIFIABLE, "only explicit table-row membership is supported"))
    if declaration.schema_id != DECLARATION_SCHEMA_ID:
        failures.append((R.VERSION_INCOMPATIBLE, "unsupported declaration schema"))
    if (
        declaration.source.format != "dense_csv/v1"
        or declaration.filtered_link.format != "filtered_cells_csv/v1"
        or declaration.source.compression not in {"none", "gzip"}
        or declaration.filtered_link.compression not in {"none", "gzip"}
    ):
        failures.append((R.UNSUPPORTED_FORMAT, "confirmed adapter format or transport is unsupported"))
    return failures


def _feature_mapping_digest(link) -> str:
    return digest_text_sequence("complete-feature-mapping", (
        f"{mapping.feature_key.feature_id}\0{mapping.cells_table_column}\0{mapping.empty_feature_column}"
        for mapping in link.bundle_feature_mapping
    ))


def _artifact_digests(declaration, parsed, witness, link, source_records):
    barcode_digest = digest_barcode_ledger(parsed.barcode_ledger)
    feature_digest = digest_feature_ledger(parsed.feature_ledger)
    matrix_digest = digest_csr_u64(parsed.counts)
    total_digest = digest_u64_vector(
        declaration.source.total_count_column, parsed.total_counts, barcode_digest
    )
    supplied_membership = digest_fields("supplied-membership-ledger", (
        ("method", MEMBERSHIP_METHOD_ID), ("barcode_ledger", barcode_digest),
    ))
    semantic_membership = digest_membership_set(parsed.barcode_ledger)
    aligned_membership = digest_bool_vector(parsed.empty_membership)
    source_provenance = digest_text_sequence("source-provenance", (
        f"{record.role}\0{record.relative_path}\0{record.byte_sha256}\0{record.format}\0{record.compression}"
        for record in source_records
    ))
    feature_mapping = _feature_mapping_digest(link)
    droplet_ledger = digest_fields("droplet-ledger-identity", (
        ("supplied", supplied_membership), ("semantic_set", semantic_membership),
        ("aligned", aligned_membership),
    ))
    content = digest_fields("artifact-content", (
        ("schema", ARTIFACT_SCHEMA_ID), ("digest_policy", DIGEST_POLICY_ID),
        ("adapter", ADAPTER_ID), ("membership_method", MEMBERSHIP_METHOD_ID),
        ("matrix", matrix_digest), ("totals", total_digest),
        ("barcode_ledger", barcode_digest), ("feature_ledger", feature_digest),
        ("droplet_ledger", droplet_ledger), ("filtered_link", link.link_digest),
    ))
    attestation = digest_fields("artifact-attestation", (
        ("artifact_content", content), ("source_provenance", source_provenance),
        ("confirmation_semantics", declaration.integrity.semantic_digest),
        ("proposer_kind", declaration.proposal.proposer_kind),
        ("proposer_id", declaration.proposal.proposer_id),
        ("confirmer", declaration.confirmation.confirmer_actor_id),
        ("confirmation_event", declaration.confirmation.confirmation_event_id),
        ("confirmed_at", declaration.confirmation.confirmed_at),
    ))
    return ArtifactDigests(
        source_byte_hash=parsed.source_byte_hash,
        filtered_source_byte_hash=witness.filtered_source_byte_hash,
        confirmation_semantic_digest=declaration.integrity.semantic_digest,
        matrix_digest=matrix_digest, total_count_digest=total_digest,
        barcode_ledger_digest=barcode_digest, feature_ledger_digest=feature_digest,
        supplied_membership_ledger_digest=supplied_membership,
        semantic_membership_set_digest=semantic_membership,
        aligned_membership_digest=aligned_membership,
        filtered_cell_ledger_digest=witness.filtered_cell_ledger_digest,
        filtered_feature_ledger_digest=witness.filtered_feature_ledger_digest,
        cell_mapping_digest=witness.cell_mapping_digest,
        feature_mapping_digest=feature_mapping,
        filtered_bundle_identity=witness.filtered_bundle_identity,
        filtered_link_digest=link.link_digest, source_provenance_digest=source_provenance,
        artifact_content_digest=content, attestation_digest=attestation,
    ), droplet_ledger


def ingest_empty_droplet_counts(
    root: Path,
    declaration: EmptyDropletIngestDeclaration | Path | None,
    filtered_bundle,
):
    if declaration is None:
        return _unavailable(
            R.RAW_MATRIX_ABSENT, "no human-confirmed empty-droplet table was supplied",
            (R.UNFILTERED_BARCODE_UNIVERSE_ABSENT,),
        )
    try:
        if isinstance(declaration, (str, Path)):
            declaration = load_declaration(Path(declaration))
        if not isinstance(declaration, EmptyDropletIngestDeclaration):
            raise EmptyDropletValidationError(R.CONFIRMATION_PROVENANCE_INCOMPLETE, "invalid declaration object")
        failures = _declaration_failures(root, declaration)
        if any(reason in {R.SOURCE_UNREADABLE_OR_UNSAFE, R.UNSUPPORTED_FORMAT, R.VERSION_INCOMPATIBLE} for reason, _ in failures):
            return _failure_result(failures)
        parsed = witness = link = None
        try:
            parsed = parse_empty_droplet_csv(root, declaration.source)
        except EmptyDropletValidationError as exc:
            failures.append((exc.reason_code, str(exc)))
        try:
            witness = capture_filtered_bundle_identity(root, declaration.filtered_link, filtered_bundle)
        except EmptyDropletValidationError as exc:
            failures.append((exc.reason_code, str(exc)))
        if parsed is not None and witness is not None:
            try:
                link = build_filtered_link(parsed, witness, declaration.source, declaration.filtered_link)
            except EmptyDropletValidationError as exc:
                failures.append((exc.reason_code, str(exc)))
        if failures:
            return _failure_result(failures)
        assert parsed is not None and witness is not None and link is not None
        source_records = (
            SourceRecord(
                role=declaration.source.role, relative_path=declaration.source.path,
                byte_sha256=parsed.source_byte_hash, format=declaration.source.format,
                compression=declaration.source.compression,
            ),
            SourceRecord(
                role="analyzed_cell_count_table", relative_path=declaration.filtered_link.path,
                byte_sha256=witness.filtered_source_byte_hash,
                format=declaration.filtered_link.format,
                compression=declaration.filtered_link.compression,
            ),
        )
        digests, droplet_ledger = _artifact_digests(
            declaration, parsed, witness, link, source_records
        )
        artifact = EmptyDropletCountsArtifact(
            schema_id=ARTIFACT_SCHEMA_ID, digest_policy_id=DIGEST_POLICY_ID,
            counts=parsed.counts, total_counts=parsed.total_counts,
            shape=parsed.counts.shape, barcode_ledger=parsed.barcode_ledger,
            feature_ledger=parsed.feature_ledger,
            empty_membership=parsed.empty_membership,
            selected_barcodes=parsed.barcode_ledger,
            membership_provenance=MembershipProvenance(MEMBERSHIP_METHOD_ID),
            filtered_bundle_link=link, source_provenance=source_records,
            digests=digests, droplet_ledger_identity=droplet_ledger,
            artifact_content_identity=digests.artifact_content_digest,
            attestation_identity=digests.attestation_digest,
        )
        if not verify_artifact_integrity(artifact):
            return _unavailable(R.DIGEST_FAILURE, "artifact digest verification failed")
        return Available(artifact)
    except EmptyDropletValidationError as exc:
        return _unavailable(exc.reason_code, str(exc))
    except (OSError, UnicodeError) as exc:
        return _unavailable(R.SOURCE_UNREADABLE_OR_UNSAFE, str(exc))
    except (TypeError, ValueError, OverflowError) as exc:
        return _unavailable(R.DIGEST_FAILURE, f"canonical artifact construction failed: {exc}")


def verify_artifact_integrity(artifact: EmptyDropletCountsArtifact) -> bool:
    try:
        barcode = digest_barcode_ledger(artifact.barcode_ledger)
        expected = {
            "matrix_digest": digest_csr_u64(artifact.counts),
            "total_count_digest": digest_u64_vector("total_umi", artifact.total_counts, barcode),
            "barcode_ledger_digest": barcode,
            "feature_ledger_digest": digest_feature_ledger(artifact.feature_ledger),
            "semantic_membership_set_digest": digest_membership_set(artifact.selected_barcodes),
            "aligned_membership_digest": digest_bool_vector(artifact.empty_membership),
            "filtered_link_digest": artifact.filtered_bundle_link.link_digest,
        }
        return all(getattr(artifact.digests, name) == value for name, value in expected.items()) and (
            artifact.artifact_content_identity == artifact.digests.artifact_content_digest
            and artifact.attestation_identity == artifact.digests.attestation_digest
            and artifact.selected_barcodes == tuple(
                barcode for barcode, member in zip(artifact.barcode_ledger, artifact.empty_membership) if member
            )
        )
    except (TypeError, ValueError, OverflowError):
        return False
