# ADR-0055: Feed fully bounded gzip tables into existing deterministic calculations

- **Status:** Accepted under the owner's standing authorization for non-escalating architecture
  decisions
- **Date:** 2026-08-02
- **Related decisions:** ADR-0017, ADR-0045, ADR-0052, ADR-0054
- **Related backlog item:** Third tranche of L10
- **Coordinated schema release:** None; retain public schema 0.18.0
- **Finding impact:** None; all affected checks remain Disclosure-only
- **Execution impact:** None; only auditor-owned standard-library decompression is permitted

## Context

ADR-0054 inventories the first logical record of exact `.csv.gz` and `.tsv.gz` artifacts but
deliberately does not expose their row bodies to calculations. The L09 adapters already accept
explicit scientist-selected CSV or TSV contracts. Requiring users to make an uncompressed copy of
the same bounded summary is unnecessary friction, but a compressed file's physical size does not
bound its decompressed size.

The calculation layer therefore needs a complete decoded view with separate resource accounting,
content identity, cancellation, and replay guarantees. This is an input-format change, not a new
scientific method or a broader authority claim.

## Decision

1. Extend only exact case-insensitive `.csv.gz` and `.tsv.gz` paths already covered by the shared
   delimited classifier. No archive sniffing, alternate compression, or inferred dialect is added.
2. Read only immutable full-digest snapshot bytes. Physical identity remains the digest of the
   exact gzip bytes; the decoded content receives a separate digest and cannot replace physical
   identity.
3. Fully validate the gzip stream to EOF in auditor-owned code. Read at most 64 KiB per chunk,
   admit at most 8 MiB of decoded content per input plus one sentinel byte, and admit at most
   64 MiB of aggregate logical reads per calculation context.
4. Record deterministic calculation-read receipts containing both identities, measured raw and
   logical bytes, chunk counts, all ceilings, status, aggregate accounting, and a closed
   termination reason. Bind the decoded receipt and digest into the calculation context digest and
   semantic lock.
5. Invoke the controller cancellation/deadline checkpoint before the physical read and between
   decompression chunks. Control exceptions propagate unchanged.
6. Route decoded bytes through one shared table-text boundary. Every existing table-consuming L09
   family keeps its own row, identifier, value, and scientific-contract checks unchanged.
7. If compression is malformed or any raw, decoded, aggregate, encoding, or family-specific table
   budget fails, omit that input from calculation authority. Existing adapters then abstain or
   return unsupported; no partial table may create an Observation or Finding.
8. Preserve all physical snapshot budgets, public schema 0.18.0, no-project-execution behavior,
   and every existing Disclosure-only ceiling. Publish a new v11 content-addressed calculation
   manifest; earlier manifests remain historical release evidence.

## Alternatives rejected

### Decompress the file once into a temporary artifact

Rejected because it creates a second storage and cleanup surface without improving authority.
The bounded decoded view is held only in the frozen in-memory calculation context and represented
by its receipt and digest in the lock.

### Treat compressed and uncompressed bytes as the same artifact identity

Rejected because two gzip encodings may decode to identical rows while remaining different
repository evidence. Equivalence is asserted only for normalized calculation operands and
outcomes, not artifact identity or context digest.

### Let each calculation adapter decompress its own input

Rejected because resource accounting, cancellation, error localization, and identity binding must
be uniform and independently testable rather than duplicated across scientific modules.

## Acceptance evidence required

- all seven table-consuming calculation families produce equivalent normalized operands and
  outcomes for paired uncompressed and gzip inputs;
- malformed gzip, a highly compressed over-budget body, an exhausted aggregate budget, and
  invalid UTF-8 fail locally without Findings;
- cancellation propagates between chunks;
- one physical compressed input is decoded at most once per context;
- calculation receipts and results replay from the semantic lock after live-source mutation and
  without project execution; and
- all prior uncompressed, ambiguity, isolation, and regression controls remain unchanged.

## Remaining limitations

The 8 MiB decoded-input and 64 MiB aggregate ceilings intentionally exclude larger summaries.
Format support does not establish column meanings, units, assay semantics, normalization, or
scientific suitability. Parquet/Arrow, Zarr, other compression formats, and large physical files
remain unsupported.
