# Experiment 0044: Bounded sparse-H5AD inventory

- **Status:** Completed
- **Date:** 2026-08-02
- **Decision:** Accepted ADR-0053 under the owner's standing authorization
- **Schema:** Unchanged at `0.18.0`
- **Backlog item:** First tranche of L10

## Question

Can sc-referee inspect the physical structure of exact selected CSR/CSC AnnData matrices with
million-scale logical axes without dense allocation, unbounded decompression, project execution,
or stronger scientific claims?

## Design

The existing 16 MiB exact selected-material boundary remains unchanged. Inside that immutable
copy, the H5AD inventory accepts an integer dense dataset or an exact AnnData `csr_matrix` or
`csc_matrix` group. Sparse `data`, `indices`, and `indptr` arrays are validated as hard-linked,
one-dimensional integer datasets with an exact two-integer shape, allowlisted compression,
consistent lengths, in-range indices, and monotonic zero-to-nnz pointers.

All dense tiles, sparse vectors, categorical codes, and string axes are read in chunks no larger
than 1 MiB. Total decompressed logical reads are capped at 64 MiB independently of compressed file
size. A controller checkpoint checks cancellation and the pre-lock deadline before bounded reads.
Sparse arrays are never densified by the inventory.

The snapshot records deterministic `x-h5ad-read-receipts` containing exact content identity, raw
file bytes, logical bytes read, chunk count, ceilings, status, and a closed termination reason.
These receipts survive semantic lock and replay without reopening the project.

## Result

Focused tests pass for dense, CSR, and CSC layouts. A CSR fixture with 1,000,001 logical rows and
only two stored values is structurally inventoried and records its duplicated observation index as
partial. A nonmonotonic pointer placed across the one-megabyte chunk boundary is unsupported. A
tiny HDF5 file declaring more than 64 MiB of compressed sparse arrays is rejected before
decompression. An injected cancellation exception propagates unchanged between reads.

The existing dense inventory, selected-only authority, schema validation, calculation-context
isolation, audit integration, replay, and zero-Finding controls remain intact.

The full checkpoint passes 1,375 tests, Ruff, formatting, strict typing for 109 production and 28
evaluation files, starter/schema validation, the 121-case regression ledger with all 26 module
baselines, and the complete clean-wheel handoff verifier.

## Tests added or extended

- `test_selected_csr_and_csc_h5ad_are_scanned_without_dense_materialization`
- `test_million_scale_sparse_shape_stays_chunked_and_records_duplicate_cells`
- `test_sparse_pointer_chunk_boundary_mutation_is_localized`
- `test_sparse_compression_cannot_bypass_logical_read_budget`
- `test_h5ad_reader_propagates_injected_cancellation_between_chunks`
- the existing audit integration test now locks and replays the exact read receipt after the live
  source is changed

## Acceptance criterion satisfied

This tranche establishes declared and measured bounded reads, localized over-budget coverage,
sparse/dense layout support, duplicate-axis handling, chunk-boundary mutation detection,
cancellation checkpoints, and replay without dense allocation or project execution.

## Remaining limitation

L10 is not complete. Exact H5AD inspection still requires the physical file to fit the existing
16 MiB selected-material copy budget. Sparse inventory does not add sparse sensitivity
recomputation or infer assay/layer/unit semantics. Compressed delimited summaries, Parquet/Arrow,
Zarr, and genuinely large physical files still need separate bounded adapters and controls.
