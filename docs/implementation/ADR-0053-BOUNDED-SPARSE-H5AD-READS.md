# ADR-0053: Add bounded sparse-H5AD reads before broader large-artifact formats

- **Status:** Accepted under the owner's standing authorization for non-escalating architecture
  decisions
- **Date:** 2026-08-02
- **Related decisions:** ADR-0017, ADR-0045, ADR-0048, ADR-0052
- **Related backlog item:** L10
- **Coordinated schema release:** None; retain public schema 0.18.0
- **Finding impact:** None
- **Execution impact:** None; only auditor-owned HDF5 reads are permitted

## Context

The current selected-material boundary fully identifies and copies at most 16 MiB per audit. The
H5AD inventory then supports only a dense integer `X` whose logical matrix is also at most 16 MiB.
This excludes common AnnData CSR/CSC storage even when a matrix with millions of logical cells has
few stored values and fits safely inside the exact selected-material envelope.

Increasing the material-copy budget to accommodate arbitrary multi-gigabyte repositories would
make ordinary audits unexpectedly expensive. Reading a live source after snapshot capture would
also violate the immutable-input boundary. Adding Parquet, Arrow, and Zarr simultaneously would
introduce unrelated dependencies and failure modes before the common byte-accounting behavior is
proven.

## Decision

1. Keep the existing exact selected-material boundary: no large weakly identified or unmaterialized
   H5AD may contribute structural or calculation evidence.
2. Extend the auditor-owned H5AD reader to exact AnnData dense, CSR, and CSC `X` layouts. Sparse
   groups must use hard links, an exact two-integer shape, integer data/indices/indptr arrays, valid
   pointer boundaries, in-range indices, allowlisted compression, and finite axis and stored-value
   ceilings.
3. Read matrix arrays, categorical codes, and string axes in fixed logical chunks. Never densify a
   sparse matrix in the inventory path. Count raw selected-file bytes, decompressed logical bytes,
   chunks, shape, and stored values in a deterministic snapshot extension.
4. Enforce an independent decompressed-read ceiling. A small compressed file whose logical arrays
   exceed that ceiling is unsupported; compression cannot bypass the memory/read budget.
5. Invoke the controller's cancellation and deadline checkpoint between bounded chunks. A stop
   request terminates through the existing controller state machine rather than being converted
   into scientific evidence.
6. Check axis-index uniqueness exactly only while the finite uniqueness budget remains. A
   demonstrated duplicate makes structure partial. If the budget is exceeded without completing
   the check, uniqueness remains explicitly unknown and structure is partial.
7. Sparse structure, nonnegativity, integer storage, and count sum are observations only. They do
   not establish assay type, normalization, experimental unit, analysis use, or biological meaning.
8. Keep L10 open after this tranche. Compressed delimited summaries and any Parquet/Arrow or Zarr
   adapters require separate dependency and identity decisions informed by concrete corpus inputs.

## Alternatives rejected

### Raise the exact material-input budget until every H5AD fits

Rejected because copying and hashing a multi-gigabyte or terabyte-scale input can dominate the
audit and is unnecessary for many review questions.

### Inspect weakly fingerprinted live H5AD files after snapshot capture

Rejected because post-snapshot source bytes could diverge and cannot support deterministic replay
or exact calculation lineage.

### Densify sparse matrices for easier validation

Rejected because logical shape, not stored-value count, controls dense memory use. A valid sparse
matrix can have a huge dense shape while remaining cheap to inspect structurally.

### Add every requested large-data format in one change

Rejected because the formats have different trust, dependency, random-access, compression, and
identity boundaries. The shared accounting behavior should be validated on the already installed
HDF5 stack first.

## Acceptance evidence required

- dense, CSR, and CSC layouts produce bounded structural inventories without project execution;
- a sparse matrix with a million-scale logical axis and small stored-value count is scanned without
  dense allocation;
- malformed pointers, out-of-range indices, unsupported links/compression, duplicate axes, and
  chunk-boundary mutations localize to partial or unsupported coverage;
- compressed logical arrays cannot exceed the decompressed-read budget;
- an injected cancellation/deadline exception is observed between chunks and propagates unchanged;
- read receipts are deterministic and semantic-lock replay does not reopen the project; and
- schema 0.18.0, calculation authority, and all Finding ceilings remain unchanged.

## Remaining limitations

Exact inspection still requires the H5AD file to fit the 16 MiB selected-material copy budget.
Large logical sparse shape does not mean arbitrary physical file size is supported. Layers, `raw`,
backed or remote arrays, compound dtypes, floating count representations, general AnnData
extensions, Parquet/Arrow, Zarr, and compressed delimited inputs remain unsupported pending their
own bounded adapters.
