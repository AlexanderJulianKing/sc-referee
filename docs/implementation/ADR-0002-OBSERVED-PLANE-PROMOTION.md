# ADR-0002: Promote the minimum observed-computation and control-plane records

## Status

Accepted on 2026-07-28 for public schema release `0.6.0` by the repository owner. The vendored
v0.5.0 public schema package remains immutable; the decision is implemented only in the new
v0.6.0 package and coordinated runtime migration.

## Context

The accepted architecture requires `AuditRun`, `StageResult`, `FileRecord`, `Operation`,
`Artifact`, and typed observed-result records, but public schema v0.5.0 does not define them.
The starter's `urn:sc-referee:starter:v0.1.0` schemas are too loose for public records:

- they omit `schema_version` and provenance;
- they use inconsistent `run_id` fields instead of `audit_run_id`;
- operation inputs and outputs are untyped strings;
- `FileRecord.identity_strength` partially duplicates the accepted public `AssetIdentity` tier;
- `ObservedResult` supports only one fixture scalar and conflates a computed value with its
  scientific orientation; and
- the provisional `AuditRun` requires a snapshot identifier before a snapshot can exist.

Silently treating those shapes as public would change record meaning without the ADR and
migration required by `AGENTS.md` and the implementation plan.

## Decision

Publish a coordinated, immutable public schema release at version `0.6.0`. The release adds the
six records as one migration because their references and lifecycle invariants are coupled.

### Common envelope

Every promoted record uses:

- an exact released `schema_version` rather than `latest`;
- one stable type-specific identifier;
- `audit_run_id` when the record belongs to a run;
- public `RecordRef` and `SourceRef` objects rather than bare identifiers; and
- public `Provenance`.

The `AuditBundle` additions are classified as a breaking public shape change because the six new
arrays are required, so the accepted release is `0.6.0`, not `0.5.1`.

### AuditRun

`AuditRun` records append-only lifecycle observations. The initial `created` state permits no
snapshot reference. States at or after `snapshotted` require a `RepositorySnapshot` reference.
Terminal states distinguish complete, deadline-partial, host-limit-partial, scientist-cancelled,
and controller-failed outcomes. A linked continuation uses an optional parent-run reference; it
does not mutate the earlier run.

An accepted revision must also align `CoverageRecord.overall_status` with scientist cancellation
before a cancelled public bundle can be required.

### StageResult

`StageResult` records one stage attempt, sequence, status, bounded details, optional typed error,
start/completion timestamps when known, and produced-record references. Missing timing remains
absent or explicitly unknown; implementations must not invent timestamps.

### FileRecord

`FileRecord` inventories one in-scope filesystem entry without claiming scientific semantics. It
records a snapshot reference, normalized repository-relative path, filesystem kind, byte size
when observed, safe classification, inspection disposition, and exactly one `AssetIdentity`
reference when an identity record exists. A symlink records its link identity and is not followed.
Unsupported or unreadable boundaries remain inventoried when their path can be observed and carry
an explicit limitation.

The promoted record must not duplicate the five public identity tiers under a second vocabulary.
The starter's `strong`, `manifest`, `weak`, and `unidentified` field is therefore migration-only.

### Operation

`Operation` is an observed parser output, not a statement that the scientific transformation is
valid. It records one accepted core operation kind, exact source spans, typed input/output record
references, literal parameters when independently checkable, implementation and package identity
when observed, determinism state, parser-result reference, inspection status, opaque or unsupported
boundaries, and provenance. Unknown dispatch emits `opaque_operation`; it never disappears.

Literal extraction and scientific interpretation remain separate. An operation parser may record
`comparison="treated versus control"` only when the literal is present in source; assigning its
scientific role requires a separately authorized assertion or contract.

### Artifact

`Artifact` identifies a material input or output and its observed role, source or location,
producer-operation references, consumer-operation references, and `AssetIdentity` reference. It
does not establish the trustworthiness of the producing code, scientific semantics, or numeric
correctness.

### ObservedResult

`ObservedResult` records a typed literal or deterministically verified value linked to its
producing operation and artifact/source evidence. Scalar, interval, vector-summary, and table-cell
variants should be discriminated rather than overloading one numeric `value` property.

Comparison text, orientation, scale, unit, population, and timing each carry an epistemic state.
Unknown is represented explicitly and never reversed into an asserted value. A material premise
may be Finding-eligible only when its exact state and evidence satisfy the ordinary admission
kernel; model confidence cannot establish it.

## Required cross-schema changes

The accepted release must update, together:

1. the schema catalog and immutable W3ID identifiers;
2. `record-union.schema.json`;
3. `audit-bundle.schema.json` with explicit arrays for the promoted record types;
4. examples for every normal, unknown, opaque, unreadable, partial, and terminal variant;
5. controller-invariant tests for lifecycle, identity linkage, unknown propagation, and typed
   references; and
6. migration notes from provisional v0.1.0 and public v0.5.0.

## Migration rules

- `run_id` becomes `audit_run_id`; this is a field rename, not an alias.
- Provisional `FileRecord.identity_strength` maps only through its linked public `AssetIdentity`;
  migration must reject a mismatch instead of choosing one.
- Bare operation input/output identifiers require an explicit target record type during migration.
- A provisional `ObservedResult.orientation="unknown"` remains unknown.
- A provisional scalar with missing producer or artifact linkage migrates with partial lineage; it
  does not become complete by default.
- Existing v0.5.0 bundles remain valid only under the immutable v0.5.0 schemas. No in-place rewrite
  is permitted.

## Acceptance evidence required

- Positive schema examples for all six records.
- Negative tests for a pre-snapshot run that fabricates a snapshot, a post-snapshot run without
  one, a followed symlink, an operation with an untyped edge, an opaque operation reported as
  supported, and an unknown result orientation promoted to known.
- End-to-end generation of the walking-skeleton records from its immutable source snapshot.
- Model-free replay with byte-identical normalized observed and assessment records.
- A migration test that preserves every provisional unknown and fails closed on ambiguous bare
  references.

## Acceptance evidence

The nonpublic templates in `schema-proposals/observed-plane/` and the explicit-version candidate
builder supplied the review evidence for this decision. Before acceptance, the generated
candidate:

- was exercised at the accepted version `0.6.0`;
- copies rather than edits the immutable v0.5.0 baseline;
- coordinates the six schemas with the catalog, record union, and AuditBundle arrays;
- contains 13 positive examples covering created and terminal runs, a partial stage, symlink and
  unreadable files, supported and opaque operations, an artifact, all four result-value variants,
  and explicit unknown result semantics; and
- has negative invariant tests for fabricated lifecycle linkage, followed symlinks, untyped
  operation edges, opaque operations reported as supported, and unknown orientation promoted
  without evidence.

The bounded migration rehearsal also promotes an actually generated walking-skeleton audit into a
schema-valid candidate bundle. It independently recomputes the scalar from immutable source and
CSV bytes, resolves FileRecord/AssetIdentity and Operation/Artifact/ObservedResult references,
preserves provisional unknown orientation, derives terminal reasons only from recorded stage
details, and rejects conflicting identity or bare-edge evidence. During this rehearsal, a real
parser contradiction was found and fixed: result-file Artifacts now list every observed write
operation that produces them.

Candidate packages remain stamped `accepted: false` and `public_release: false` as historical
review artifacts. The accepted release builder emits a distinct immutable package with an exact
manifest. W3ID publication and hosted conformance remain release-distribution gates and are not
implied by local package generation.

## Consequences

- Asset identities and graph edges become resolvable without dangling provisional targets.
- Snapshot, parser, and controller records share the public envelope and naming conventions.
- The schema release is larger than six isolated files because bundle and lifecycle semantics are
  coupled.
- D01 and E01 may leave provisional status only after the coordinated `0.6.0` package, runtime
  records, migration, and acceptance tests pass together.

## Acceptance record

- Decision: accept ADR-0002.
- Exact public schema version: `0.6.0`.
- Accepted by: repository owner, in the implementation task on 2026-07-28.
- Not accepted by this decision: detector qualification, domain broadening, W3ID deployment, or a
  correctness/capability claim.
