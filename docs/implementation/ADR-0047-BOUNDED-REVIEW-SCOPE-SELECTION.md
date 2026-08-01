# ADR-0047: Bind bounded review-scope selections to immutable audit segments

- **Status:** Accepted
- **Date:** 2026-08-01
- **Related requirements:** SA-FR-004, SA-FR-013, SA-FR-024, SA-FR-045, SA-FR-071;
  Post-MPP backlog L04

## Context

The ordinary audit can already ask which publication artifact is final and can receive a typed
human Answer in a linked exact-snapshot segment. It cannot offer the same workflow when more than
one parsed analysis source, observed material input, or snapshotted analysis output is plausible.
Users must currently restart the audit with flags or edit internal records. In addition, a resume
segment schedules every open question even though the current append-only protocol resolves one
question per segment, and its next lock does not reliably retain unrelated questions or prior
Answers.

Review-scope selection is metadata authority. It is not scientific intent, observed execution,
lineage proof, or evidence that a selected artifact is correct or was used.

## Decision

1. The controller inventories exact source, input, and output candidates from existing public
   FileRecord, Artifact, ParserResult, and AssetIdentity records. A selectable candidate must be a
   safe repository-relative regular file with a full digest in the immutable snapshot. Static
   output paths without snapshotted bytes, symlinks, weak identities, and unsupported paths are not
   selectable.
2. Zero candidates remain explicitly unavailable in the internal semantic-lock projection. One
   candidate remains a unique candidate but is not silently promoted to scientist-selected scope.
   Two or more candidates produce one closed MaterialQuestion per scope dimension, subject to a
   finite candidate limit. Each option binds the exact record, AssetIdentity, path, digest,
   snapshot, and consequence. The ordinary explicit unknown option remains available.
3. A scientist may select one listed option, select none, retain unknown, or submit a bounded
   structured selection of several listed candidates. The Answer uses existing
   `metadata_definition` authority scoped to the exact RepositorySnapshot. It establishes only the
   review scope named by that question.
4. Linked resume can target exactly one named open question and the skill should do so. The
   backward-compatible default may schedule all open questions, but one append-only segment still
   records one scientist Answer; unanswered work remains open for later linked segments. The new
   segment recaptures the source snapshot using the original preferred and material full-digest
   paths, and rejects any digest or identity drift before scheduling work.
5. Locking a linked segment retains prior Answers, answered/deferred questions, unrelated open
   questions, and their immutable identities. The lock contains a deterministic internal
   `scope_selections` projection for downstream static joins. Conflicting, stale, missing,
   over-limit, or tampered selections are rejected and the parent audit remains unchanged.
   The integrity-verified question projection advances to protocol 0.2.0 and exposes the selection
   profile, kind, multi-selection permission, maximum count, and authority limitation.
6. The existing model-proposal-before-Answer protocol remains in place. Removing that extra step is
   a general interaction-ergonomics change reserved for L15; it is not necessary to change public
   WorkItem meaning for L04.

## Schema and authority impact

No schema release is required. Public schema 0.18.0 already permits arbitrary closed
MaterialQuestion dimensions, structured Answer values, RepositorySnapshot record references, and
`metadata_definition` authority. The selection contract is versioned in `x-` extensions and is
validated by the deterministic controller. `scope_selections` is an internal semantic-lock input,
not a new public record or correctness claim.

This decision does not authorize project execution, establish artifact materiality from filenames,
prove that selected source produced selected output, or let a model choose the scientist's scope.

## Acceptance evidence

- zero, one, many, and over-limit candidate inventories;
- single, multiple, none, and unknown selections;
- stale Answer, conflicting Answer, missing record, unsafe path, symlink, weak identity, and digest
  drift rejection;
- exact targeted linked resume, preservation across two linked segments, and parent immutability;
- semantic lock and model-disabled replay with identical selection meaning; and
- cancellation before selection without a fabricated Answer.

## Acceptance record

- Decision: accepted under the repository owner's standing authorization to auto-accept minor
  ADRs and schema decisions unless they require a material product re-evaluation.
- Accepted by: repository owner through that standing authorization on 2026-08-01.

## Remaining limitation

Selection establishes review scope only. General source-to-report, source-to-input, and
output-to-report joins remain L05 work, and proposal-free scientist interaction remains L15 work.
