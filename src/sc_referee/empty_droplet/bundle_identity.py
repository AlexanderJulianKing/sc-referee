"""Read-only identity witness linking an existing Bundle to confirmed cells.csv."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import sparse

from .csv_adapter import parse_csv_rows, parse_u64_lexeme, read_csv_transport
from .digest import (
    digest_barcode_ledger, digest_csr_u64, digest_feature_ledger, digest_fields,
    digest_index_vector, digest_text_sequence, digest_u64_vector,
)
from .schema import (
    BarcodeKey, EmptyDropletUnavailableReason, EmptyDropletValidationError,
    FeatureKey, FeatureMapping, FilteredLinkDeclaration, freeze_index_vector,
)


@dataclass(frozen=True)
class FilteredBundleIdentityWitness:
    filtered_bundle_identity: str
    filtered_source_identity: str
    filtered_content_identity: str
    filtered_source_byte_hash: str
    filtered_cell_ledger: tuple[BarcodeKey, ...]
    filtered_feature_ledger: tuple[FeatureKey, ...]
    bundle_cell_to_cells_table_row: np.ndarray
    bundle_feature_mapping: tuple[FeatureMapping, ...]
    shared_count_coherent: bool
    total_count_coherence: bool | str
    filtered_cell_ledger_digest: str
    filtered_feature_ledger_digest: str
    cell_mapping_digest: str
    feature_mapping_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "filtered_cell_ledger", tuple(self.filtered_cell_ledger))
        object.__setattr__(self, "filtered_feature_ledger", tuple(self.filtered_feature_ledger))
        object.__setattr__(self, "bundle_feature_mapping", tuple(self.bundle_feature_mapping))
        object.__setattr__(self, "bundle_cell_to_cells_table_row", freeze_index_vector(
            self.bundle_cell_to_cells_table_row, name="bundle_cell_to_cells_table_row"
        ))


def _fail(reason: EmptyDropletUnavailableReason, message: str):
    raise EmptyDropletValidationError(reason, message)


def _bundle_u64_matrix(bundle) -> np.ndarray | sparse.csr_matrix:
    if getattr(bundle, "measure", None) is None or bundle.measure.kind != "counts" or bundle.measure.counts is None:
        _fail(EmptyDropletUnavailableReason.FILTERED_LINK_MISMATCH, "Bundle lacks a raw count matrix")
    raw = bundle.measure.counts
    array = sparse.csr_matrix(raw) if sparse.issparse(raw) else np.asarray(raw)
    if getattr(array, "ndim", 2) != 2 or array.dtype.kind == "b" or not np.issubdtype(array.dtype, np.integer):
        _fail(EmptyDropletUnavailableReason.NOT_RAW_INTEGER_COUNTS, "Bundle counts are not exact integers")
    values = array.data if sparse.issparse(array) else array
    if np.issubdtype(array.dtype, np.signedinteger) and values.size and np.any(values < 0):
        _fail(EmptyDropletUnavailableReason.NOT_RAW_INTEGER_COUNTS, "Bundle counts are negative")
    if sparse.issparse(array):
        return array.astype(np.uint64, copy=True)
    return np.array(array, dtype=np.uint64, order="C", copy=True)


def _bundle_total(value, identity: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        _fail(EmptyDropletUnavailableReason.NOT_RAW_INTEGER_COUNTS, f"{identity} is not an exact integer")
    integer = int(value)
    if integer < 0 or integer > 2**64 - 1:
        _fail(EmptyDropletUnavailableReason.NOT_RAW_INTEGER_COUNTS, f"{identity} is outside uint64")
    return integer


def capture_filtered_bundle_identity(
    root: Path, declaration: FilteredLinkDeclaration, bundle,
) -> FilteredBundleIdentityWitness:
    if declaration.format != "filtered_cells_csv/v1":
        _fail(EmptyDropletUnavailableReason.UNSUPPORTED_FORMAT, "filtered table format is unsupported")
    genes = tuple(declaration.gene_count_columns)
    if not genes or len(set(genes)) != len(genes):
        _fail(EmptyDropletUnavailableReason.FEATURE_IDENTITY_INVALID, "filtered gene identities are invalid")
    payload, source_hash = read_csv_transport(root, declaration)
    rows = parse_csv_rows(payload)
    header = rows[0]
    required = (declaration.cell_key_column, declaration.total_count_column, *genes)
    if any(header.count(column) != 1 for column in required):
        _fail(EmptyDropletUnavailableReason.RAW_FILTERED_FEATURE_MISMATCH, "confirmed cells columns are not exact")
    cell_col = header.index(declaration.cell_key_column)
    total_col = header.index(declaration.total_count_column)
    gene_cols = tuple(header.index(gene) for gene in genes)
    source_cells: list[BarcodeKey] = []
    source_counts: list[list[int]] = []
    source_totals: list[int] = []
    cell_rows: dict[BarcodeKey, int] = {}
    for source_row, row in enumerate(rows[1:]):
        native = row[cell_col]
        if not native or native != native.strip():
            _fail(EmptyDropletUnavailableReason.BARCODE_IDENTITY_INVALID, "cells.csv has an invalid cell identity")
        key = BarcodeKey(declaration.namespace, native)
        if key in cell_rows:
            _fail(EmptyDropletUnavailableReason.BARCODE_IDENTITY_INVALID, "cells.csv has duplicate cell identities")
        cell_rows[key] = source_row
        source_cells.append(key)
        source_totals.append(parse_u64_lexeme(row[total_col], identity=f"cells row {source_row + 2} total"))
        source_counts.append([
            parse_u64_lexeme(row[column], identity=f"cells row {source_row + 2} gene {gene}")
            for gene, column in zip(genes, gene_cols)
        ])
    if not source_cells:
        _fail(EmptyDropletUnavailableReason.RAW_FILTERED_BARCODE_MISMATCH, "cells.csv has no analyzed cells")

    native_bundle_cells = tuple(bundle.observations.index.tolist())
    if any(not isinstance(cell, str) or not cell or cell != cell.strip() for cell in native_bundle_cells):
        _fail(EmptyDropletUnavailableReason.BARCODE_IDENTITY_INVALID, "Bundle cell identities are invalid")
    bundle_cells = tuple(BarcodeKey(declaration.namespace, cell) for cell in native_bundle_cells)
    if len(set(bundle_cells)) != len(bundle_cells) or set(bundle_cells) != set(source_cells):
        _fail(EmptyDropletUnavailableReason.RAW_FILTERED_BARCODE_MISMATCH, "Bundle and cells.csv cell ledgers are not bijective")

    native_features = tuple(bundle.measure.feature_index)
    if any(not isinstance(feature, str) or not feature for feature in native_features):
        _fail(EmptyDropletUnavailableReason.FEATURE_IDENTITY_INVALID, "Bundle feature identities are invalid")
    if len(set(native_features)) != len(native_features) or set(native_features) != set(genes):
        _fail(EmptyDropletUnavailableReason.RAW_FILTERED_FEATURE_MISMATCH, "Bundle and cells.csv feature ledgers differ")
    counts = _bundle_u64_matrix(bundle)
    if counts.shape != (len(bundle_cells), len(native_features)):
        _fail(EmptyDropletUnavailableReason.FILTERED_LINK_MISMATCH, "Bundle count shape does not match its ledgers")
    cell_mapping = np.array([cell_rows[key] for key in bundle_cells], dtype=np.uint64)
    feature_positions = {gene: index for index, gene in enumerate(genes)}
    mappings = tuple(
        FeatureMapping(
            feature_key=FeatureKey(feature), cells_table_column=gene_cols[feature_positions[feature]],
            empty_feature_column=feature_positions[feature],
        )
        for feature in native_features
    )
    cells_counts = np.array(source_counts, dtype=np.uint64)
    expected = cells_counts[cell_mapping.astype(np.intp)][:, [feature_positions[f] for f in native_features]]
    coherent = ((counts != sparse.csr_matrix(expected)).nnz == 0
                if sparse.issparse(counts) else np.array_equal(counts, expected))
    if not coherent:
        _fail(EmptyDropletUnavailableReason.FILTERED_LINK_MISMATCH, "Bundle and cells.csv shared gene counts differ")

    total_coherence: bool | str = "not_comparable"
    if declaration.total_count_column in bundle.observations.columns:
        observed_totals = np.array([
            _bundle_total(value, f"Bundle {declaration.total_count_column}")
            for value in bundle.observations[declaration.total_count_column].tolist()
        ], dtype=np.uint64)
        expected_totals = np.array(source_totals, dtype=np.uint64)[cell_mapping.astype(np.intp)]
        if not np.array_equal(observed_totals, expected_totals):
            _fail(EmptyDropletUnavailableReason.FILTERED_LINK_MISMATCH, "Bundle and cells.csv total counts differ")
        total_coherence = True

    feature_ledger = tuple(FeatureKey(feature) for feature in native_features)
    cell_ledger_digest = digest_barcode_ledger(bundle_cells)
    feature_ledger_digest = digest_feature_ledger(feature_ledger)
    cell_mapping_digest = digest_index_vector("bundle-cell-to-cells-row", cell_mapping)
    feature_mapping_digest = digest_text_sequence("bundle-feature-mapping", (
        f"{mapping.feature_key.feature_id}\0{mapping.cells_table_column}\0{mapping.empty_feature_column}"
        for mapping in mappings
    ))
    bundle_identity = digest_fields("filtered-bundle-identity", (
        ("cell_ledger", cell_ledger_digest), ("feature_ledger", feature_ledger_digest),
        ("counts", digest_csr_u64(sparse.csr_matrix(counts))),
        ("measure_kind", bundle.measure.kind),
    ))
    source_semantics = digest_fields("filtered-source-semantics", (
        ("format", declaration.format), ("compression", declaration.compression),
        ("cell_key_column", declaration.cell_key_column),
        ("total_count_column", declaration.total_count_column),
        ("genes", digest_text_sequence("filtered-source-genes", genes)),
        ("namespace", declaration.namespace),
    ))
    source_identity = digest_fields("filtered-source-identity", (
        ("bytes", source_hash), ("semantics", source_semantics),
    ))
    source_cell_ledger_digest = digest_barcode_ledger(tuple(source_cells))
    source_content_identity = digest_fields("filtered-source-content", (
        ("cell_ledger", source_cell_ledger_digest),
        ("feature_ledger", digest_feature_ledger(tuple(FeatureKey(gene) for gene in genes))),
        ("counts", digest_csr_u64(sparse.csr_matrix(np.array(source_counts, dtype=np.uint64)))),
        ("totals", digest_u64_vector(declaration.total_count_column, np.array(source_totals, dtype=np.uint64), source_cell_ledger_digest)),
        ("namespace", declaration.namespace),
    ))
    return FilteredBundleIdentityWitness(
        filtered_bundle_identity=bundle_identity, filtered_source_identity=source_identity,
        filtered_content_identity=source_content_identity,
        filtered_source_byte_hash=source_hash, filtered_cell_ledger=bundle_cells,
        filtered_feature_ledger=feature_ledger, bundle_cell_to_cells_table_row=cell_mapping,
        bundle_feature_mapping=mappings, shared_count_coherent=True,
        total_count_coherence=total_coherence,
        filtered_cell_ledger_digest=cell_ledger_digest,
        filtered_feature_ledger_digest=feature_ledger_digest,
        cell_mapping_digest=cell_mapping_digest, feature_mapping_digest=feature_mapping_digest,
    )
