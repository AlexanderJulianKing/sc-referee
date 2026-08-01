# ADR-0037: Add a cell-aware scientific evidence contract

- **Status:** Accepted under the repository owner's standing authorization for non-authority-
  changing development ADRs
- **Date:** 2026-07-30
- **Related decisions:** Accepted ADR-0020, ADR-0034, ADR-0035, and ADR-0036
- **Schema impact:** None; accepted schema v0.15.0 remains unchanged

## Context

ADR-0036 makes exact Python and R notebook and Quarto cells available as canonical child parser
results. Scientific-check adapters still receive only whole-file `InspectionDocument` values. That
internal contract identifies a document by repository path and assumes that the inspected bytes
hash to the public source reference's `content_digest`. Both assumptions are correct for ordinary
files but wrong for a cell: several independently inspected cells share one container path, while
the public source reference authenticates the container and the inspected bytes have a separate
cell-source digest.

Passing cell bytes through the whole-file contract would either collide cells or falsely describe
cell bytes as the notebook or Quarto file. The public v0.15.0 `SourceRef` already supports
`notebook_cell` and `document_chunk`, so no public schema addition is required.

## Decision

### 1. Bind inspected bytes to an immutable public source location

`InspectionDocument` gains one immutable, canonical source-location value. It records the exact
public `SourceRef` for the inspected unit independently from the digest of the bytes presented to
an adapter. Ordinary files receive a derived `file_span` location and preserve existing behavior.
Virtual cells retain the parent container path and full-content digest plus their exact cell ID or
chunk label. Their inspected-content digest remains the separately verified cell-source digest.

Document uniqueness is defined by exact source location and parser-result identity, not repository
path alone. A line offset translates an adapter's cell-relative coordinates to absolute Quarto
document lines; notebook coordinates remain cell-relative.

### 2. Re-extract cell bytes independently before exposing them to an adapter

The scientific-check integration does not trust a child parser result to supply arbitrary bytes.
It resolves the child's declared parent parser result, rereads the immutable snapshot container,
reapplies the accepted notebook or Quarto extraction ceilings, verifies the parent digest, cell
identity, cell-source digest, bridge metadata, parser/language pairing, and source location, and
only then constructs an inspection document. Any mismatch localizes to an unavailable virtual
document.

The base-R duplicate remains suppressed when the Tree-sitter-R result for the same exact cell is
available, just as for ordinary `.R` files.

### 3. Preserve cell-aware citations without inventing execution semantics

Evidence spans are resolved through the exact parser-result-bound inspection document. Public
citations preserve `notebook_cell` or `document_chunk`, the parent container digest, exact cell
identity, and bounded quoted cell text. Identical cells in one container remain distinct.

Existing static scientific adapters may inspect an independently parsed cell only within their
already accepted grammar. A cell-only static observation remains unscoped and question-ineligible
unless an existing typed analysis-scope join is independently available. No concatenation or
cross-cell name resolution is introduced.

### 4. Add no new scientific or execution authority

This contract adds transport and provenance, not a scientific rule. It does not establish cell
execution, execution order, shared state, output authenticity, rendering, code-to-result lineage,
Claims, analysis intent, numerical causality, detector qualification, or Findings. Quarto prose,
notebook markdown, and saved outputs remain outside scientific-check inputs in this slice.

## Alternatives rejected

### Use a synthetic path for every cell

Rejected because a synthetic path is not the repository object's public identity and can obscure
the authenticated parent container.

### Trust the child parser result's quoted text

Rejected because the adapter boundary must reproduce evidence from immutable snapshot bytes, not
accept derived text without independent digest and location verification.

### Concatenate cells before inspection

Rejected because concatenation invents shared state and ordering and can make unsupported
cross-cell dataflow appear established.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** immutable source-location validation; two same-path cell identities; notebook
  and Quarto cell byte re-extraction; tampered bridge metadata rejection; exact notebook-cell and
  absolute Quarto evidence citations; cell-only static observation remaining question-ineligible;
  inert execution markers; semantic lock; and replay.
- **Acceptance criterion satisfied:** an existing bounded static scientific adapter can inspect
  exact independently verified cell bytes and preserve a truthful cell-level citation without
  executing project code or gaining scientific authority.
- **Remaining limitation:** cells remain isolated fragments. Cross-cell dataflow, prose and Claim
  extraction, output provenance, runtime state, rendering, additional R scientific adapters, and
  any new question, detector, or Finding coverage remain unsupported.
