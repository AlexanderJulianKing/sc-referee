# ADR-0054: Add bounded gzip-delimited header inventory before full compressed calculations

- **Status:** Accepted under the owner's standing authorization for non-escalating architecture
  decisions
- **Date:** 2026-08-02
- **Related decisions:** ADR-0017, ADR-0045, ADR-0048, ADR-0053
- **Related backlog item:** Second tranche of L10
- **Coordinated schema release:** None; retain public schema 0.18.0
- **Finding impact:** None
- **Execution impact:** None; only auditor-owned standard-library decompression is permitted

## Context

The exact delimited-table inventory recognizes `.csv` and `.tsv` only after their complete
physical bytes have been frozen and fully digested. Scientific repositories commonly store the
same summaries as `.csv.gz` or `.tsv.gz`. Treating these as opaque loses even exact column-name
inventory, while fully decompressing every archive would let a small physical file consume
unbounded time or memory.

Header inventory and full calculation input are different authority surfaces. A header can be
read from one bounded logical record without inspecting rows. Feeding a compressed table into an
L09 recomputation requires complete bounded decompression, measured calculation receipts, and
cross-family equivalence tests. Combining both in one change would conceal that difference.

## Decision

1. Recognize only exact case-insensitive `.csv.gz` and `.tsv.gz` compound suffixes in addition to
   uncompressed `.csv` and `.tsv`. Other archives and inferred dialects remain unsupported.
2. Read only from immutable, fully digested snapshot bytes. Preserve the existing 5,000,000-byte
   ordinary snapshot budget and 16 MiB selected-material budget; do not read the live project.
3. Use the Python standard library to stream one strict UTF-8 logical CSV/TSV record. Permit
   quoted physical newlines, cap each decompressed read at 64 KiB, cap the header at 1 MiB, and
   reserve one additional sentinel byte to distinguish an over-budget unterminated record.
4. Stop after the first complete logical record. Do not decompress or validate the gzip member
   body, infer row count or types, or claim that a valid header makes the remaining table valid.
5. Record deterministic snapshot receipts with content identity, encoding, raw bytes, logical
   bytes read, chunk count, every ceiling, status, and a closed termination reason. Replay uses
   the locked receipt and never reopens the project.
6. Invoke the controller cancellation/deadline checkpoint before physical reads and between
   logical chunks. Control exceptions propagate unchanged and never become coverage evidence.
7. Localize malformed gzip, non-UTF-8 headers, malformed records, and over-budget headers as
   opaque structure. Emit no Variables from those paths and no Findings from any header result.
8. Keep full gzip-table calculation support pending. That follow-up must reuse the shared bounded
   reader, measure complete decompressed bytes, and prove uncompressed/compressed equivalence
   without weakening any L09 contract or Finding ceiling.

## Alternatives rejected

### Fully decompress every exact gzip file before parsing

Rejected because physical compressed size does not bound logical size, and header inventory does
not need row bodies.

### Read only the first physical line

Rejected because valid CSV and TSV headers can contain quoted newlines. The bounded unit is the
first logical record, not the first newline-delimited byte sequence.

### Infer compression from magic bytes regardless of path

Rejected because silent format inference broadens applicability. The exact compound suffix and
gzip framing must agree.

### Immediately enable all L09 calculations over compressed tables

Rejected for this tranche because complete decompression has different accounting and replay
requirements from a prefix-only inventory. It remains the next compressed-delimited step.

## Acceptance evidence required

- `.csv.gz` and `.tsv.gz` headers, including a quoted multiline header, produce the same bounded
  Variables as their uncompressed logical records;
- a highly compressed multi-megabyte body is not read after the header;
- an oversized first record and malformed gzip member localize to opaque structure with closed
  receipts and no Variables or Findings;
- cancellation propagates between chunks;
- exact receipts survive live-source mutation and semantic-lock replay without project execution;
  and
- schema 0.18.0, material-copy budgets, calculation authority, and Finding ceilings remain
  unchanged.

## Remaining limitations

The gzip member after its first logical record is not decompressed or validated. Row counts,
values, types, scientific meanings, full compressed calculation inputs, non-gzip compression,
Parquet/Arrow, Zarr, and large physical files remain unsupported.
