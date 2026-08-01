# ADR-0003: Represent an unavailable publication surface without inventing an artifact

- **Status:** Accepted
- **Date:** 2026-07-28
- **Related requirements:** SA-FR-004, AC-03, ADR-0021, `publication-surface.schema.json`, `coverage-record.schema.json`

## Context

An arbitrary scientific repository may contain source code or data but no report, notebook,
manuscript, table set, figure set, or rendered artifact. The normative controller must still
inventory the repository and ask one material question; it must not invent a publication artifact.

Public schema 0.6.0 cannot represent that state:

- `PublicationSurface.candidates` requires at least one artifact; and
- `CoverageRecord.scope.publication_surface_refs` requires at least one record reference.

Using the repository root, a source file, or an unidentified synthetic artifact as a publication
surface would turn missing evidence into asserted evidence. Omitting the only CoverageRecord would
also prevent a truthful report of what was inspected.

## Decision

Before public distribution of 0.6.0, revise the coordinated local release so that:

1. `PublicationSurface.candidates` may be empty only when `status` is `unresolved`, selection kind
   is `unresolved`, publication materiality is false, and the selection links one open
   `MaterialQuestion`.
2. `CoverageRecord.scope.publication_surface_refs` may be empty only when an explicit
   `publication_surface_status` is `unavailable` or `unresolved`.
3. A resolved publication surface continues to require at least one candidate and selected
   artifact reference.
4. Empty candidates never permit detector eligibility, publication materiality, or a Finding
   whose wording depends on a final publication claim.
5. Add positive examples for an unavailable surface and negative tests that reject a resolved
   empty surface, assessable materiality, and empty references labeled resolved.

This changes no detector or Finding semantics. It only permits an explicit unknown that the
controller already needs to preserve.

## Implemented treatment

The coordinated local v0.6.0 release permits the explicit unavailable state, and the controller
completes a schema-valid evidence-limited audit for repositories with no fully identified
publication-like artifact. It emits one unresolved empty-candidate PublicationSurface, one linked
open MaterialQuestion, an empty CoverageRecord publication reference list labeled `unavailable`,
zero eligible detector targets, and no Finding derived from the missing surface.

## Consequences

- `sc-referee audit` can complete a truthful partial report for source-only repositories.
- Existing resolved and ambiguous-candidate records remain valid.
- The 0.6.0 package manifest, embedded runtime copy, examples, invariant tests, and distribution
  parity tests must be regenerated together.

## Acceptance record

- Decision: accept ADR-0003.
- Exact coordinated schema version: `0.6.0`, amended before external publication.
- Accepted by: repository owner in the implementation task on 2026-07-28.
- Not accepted by this decision: fabricated publication artifacts, detector eligibility from an
  unavailable surface, model-derived material premises, legacy GitHub compatibility, or W3ID
  deployment.
