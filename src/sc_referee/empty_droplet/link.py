"""Exact, complete filtered-link construction; never intersects or normalizes."""
from __future__ import annotations

from .bundle_identity import FilteredBundleIdentityWitness
from .csv_adapter import ParsedEmptyDropletTable
from .digest import (
    digest_barcode_ledger, digest_csr_u64, digest_feature_ledger, digest_fields,
    digest_text_sequence, digest_u64_vector,
)
from .schema import (
    EmptyDropletUnavailableReason, EmptyDropletValidationError, FeatureMapping,
    FilteredBundleLink, FilteredLinkDeclaration, SourceDeclaration,
)


NAMESPACE_POLICY = "exact_native_single_namespace/v1"


def _fail(reason: EmptyDropletUnavailableReason, message: str):
    raise EmptyDropletValidationError(reason, message)


def build_filtered_link(
    empty: ParsedEmptyDropletTable,
    witness: FilteredBundleIdentityWitness,
    source: SourceDeclaration,
    filtered: FilteredLinkDeclaration,
) -> FilteredBundleLink:
    if source.namespace != filtered.namespace:
        _fail(EmptyDropletUnavailableReason.RAW_FILTERED_FEATURE_MISMATCH, "empty and cell namespaces differ")
    empty_keys = set(empty.barcode_ledger)
    cell_keys = set(witness.filtered_cell_ledger)
    if empty_keys & cell_keys:
        _fail(EmptyDropletUnavailableReason.EMPTY_CELL_OVERLAP, "empty and analyzed-cell identities overlap")

    empty_positions = {feature.feature_id: index for index, feature in enumerate(empty.feature_ledger)}
    filtered_ids = tuple(feature.feature_id for feature in witness.filtered_feature_ledger)
    if len(empty_positions) != len(empty.feature_ledger) or set(empty_positions) != set(filtered_ids):
        _fail(
            EmptyDropletUnavailableReason.RAW_FILTERED_FEATURE_MISMATCH,
            "empty table and filtered Bundle do not have the identical feature panel",
        )
    mappings = tuple(
        FeatureMapping(
            feature_key=mapping.feature_key,
            cells_table_column=mapping.cells_table_column,
            empty_feature_column=empty_positions[mapping.feature_key.feature_id],
        )
        for mapping in witness.bundle_feature_mapping
    )
    feature_mapping_digest = digest_text_sequence("complete-feature-mapping", (
        f"{mapping.feature_key.feature_id}\0{mapping.cells_table_column}\0{mapping.empty_feature_column}"
        for mapping in mappings
    ))
    empty_barcode_digest = digest_barcode_ledger(empty.barcode_ledger)
    empty_content_identity = digest_fields("empty-source-content", (
        ("barcode_ledger", empty_barcode_digest),
        ("feature_ledger", digest_feature_ledger(empty.feature_ledger)),
        ("counts", digest_csr_u64(empty.counts)),
        ("totals", digest_u64_vector(source.total_count_column, empty.total_counts, empty_barcode_digest)),
        ("namespace", source.namespace),
    ))
    link_digest = digest_fields("filtered-link", (
        ("filtered_bundle_identity", witness.filtered_bundle_identity),
        ("filtered_source_content", witness.filtered_content_identity),
        ("empty_source_content", empty_content_identity),
        ("filtered_cell_ledger", witness.filtered_cell_ledger_digest),
        ("filtered_feature_ledger", witness.filtered_feature_ledger_digest),
        ("cell_mapping", witness.cell_mapping_digest),
        ("feature_mapping", feature_mapping_digest),
        ("empty_vs_cell_disjoint", "true"),
        ("shared_count_coherent", "true"),
        ("total_count_coherence", str(witness.total_count_coherence).lower()),
        ("source_adapter", source.format), ("filtered_adapter", filtered.format),
        ("namespace", source.namespace), ("namespace_policy", NAMESPACE_POLICY),
    ))
    return FilteredBundleLink(
        filtered_bundle_identity=witness.filtered_bundle_identity,
        filtered_source_identity=witness.filtered_source_identity,
        filtered_cell_ledger=witness.filtered_cell_ledger,
        filtered_feature_ledger=witness.filtered_feature_ledger,
        bundle_cell_to_cells_table_row=witness.bundle_cell_to_cells_table_row,
        bundle_feature_mapping=mappings,
        empty_vs_cell_disjoint=True, shared_count_coherent=True,
        total_count_coherence=witness.total_count_coherence,
        namespace_policy=NAMESPACE_POLICY, link_digest=link_digest,
    )
