# Experiment 0045: Bounded gzip-delimited header inventory

- **Status:** Completed
- **Date:** 2026-08-02
- **Decision:** Accepted ADR-0054 under the owner's standing authorization
- **Schema:** Unchanged at `0.18.0`
- **Backlog item:** Second tranche of L10

## Question

Can sc-referee inventory the exact header of fully identified `.csv.gz` and `.tsv.gz` artifacts
without decompressing their row bodies, admitting compression bombs, executing project code, or
broadening scientific claims?

## Design

A shared auditor-owned reader classifies only exact CSV/TSV and CSV/TSV-plus-gzip compound
suffixes. It reads one strict UTF-8 logical record from immutable snapshot bytes in chunks of at
most 64 KiB. The header ceiling is 1 MiB and the total logical-read ceiling is one sentinel byte
larger. The controller checks cancellation and its pre-lock deadline before the physical read and
between logical chunks.

The repository snapshot stores `x-delimited-read-receipts` with physical content identity,
encoding, measured raw and logical bytes, chunks, ceilings, status, and a closed termination
reason. Header Variables remain names only; all row and scientific semantics stay unknown.

## Tests added or extended

- `test_gzip_csv_and_tsv_headers_are_read_without_decompressing_the_body`
- `test_compressed_header_bomb_and_malformed_gzip_are_localized`
- `test_compressed_header_reader_propagates_cancellation_between_chunks`
- `test_compressed_header_receipt_is_locked_and_replayed_without_project_execution`
- existing non-UTF-8, wide, ambiguous, weak-identity, and uncompressed controls remain active

## Acceptance criterion targeted

This tranche targets bounded measured gzip header reads, multiline logical-record correctness,
localized malformed/over-budget coverage, cancellation, no execution, immutable replay, and
unchanged Finding authority.

## Result

All targeted controls pass. The full checkpoint passes 1,379 tests, Ruff, formatting, strict
typing for 110 production and 28 evaluation files, starter/schema validation, the 121-case
regression ledger with all 26 module baselines, and the complete clean-wheel handoff verifier.
The public schema remains 0.18.0 and the capability matrix remains 15 entries with no detector
qualification claim.

## Remaining limitation

Full compressed row bodies do not yet feed L09 calculation adapters. The reader does not validate
gzip bytes after the header or support other compression formats, Parquet/Arrow, Zarr, or large
physical files.
