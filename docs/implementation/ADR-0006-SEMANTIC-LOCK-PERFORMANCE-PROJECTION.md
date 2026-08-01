# ADR-0006: Define a replayable semantic-lock performance projection

- **Status:** Accepted
- **Date:** 2026-07-28
- **Schema release:** `0.8.0` (no schema change)
- **Related requirements:** SA-FR-044, SA-FR-047, SA-FR-049, acceptance criteria AC-11,
  AC-24–27, AC-35–36, AC-50

## Context

The accepted public `PerformanceRecord` can carry elapsed time, paused time, model usage, I/O,
cache counts, stage timings, resource measurements, and a termination disposition. The linked
deadline ledger additionally retains the event and segment history needed to prove scientist-wait
pauses and fresh resume budgets, but that ledger is an implementation protocol rather than an
accepted public record.

A run-final performance record cannot be placed in the immutable semantic lock before report and
integrity work finishes. Regenerating elapsed values during replay would instead make replay
nondeterministic. Treating a record captured at semantic lock as total run duration would be
misleading. Schema v0.8.0 deliberately permits multiple PerformanceRecords and open extensions,
so it can represent a bounded measurement snapshot without changing the schema.

The current controller also meters only snapshot identity reads. Parser, graph, report, and storage
I/O are not fully instrumented. The interaction CLI accepts externally produced bounded proposals;
their presence does not prove that the sc-referee controller itself called a model provider.

## Decision

If accepted, define the following bounded v0.8.0 projection profile.

### Measurement boundary

Every completed semantic lock contains exactly one `PerformanceRecord` for the current AuditRun.
It measures the interval through semantic lock, not the final run duration. Its stable identity is
bound to the AuditRun and the `semantic_lock` boundary. Replay copies and validates this locked
record byte-for-byte and never resamples a clock.

The record uses:

- `termination.state: partial` and `termination.reason: other`, with detail explaining that the
  measurement interval ended at semantic lock and that AuditRun records carry the run outcome;
- one `through_semantic_lock` stage timing;
- `x-measurement-boundary: semantic_lock`;
- `x-postlock-elapsed-included: false`; and
- `x-deadline-ledger-digest` when a linked interaction ledger exists.

The PerformanceRecord termination object describes this measurement interval only. It cannot
override or summarize the terminal AuditRun state.

### Time accounting

Initial audits project the most recently checked user-visible elapsed value from the in-memory
deadline controller and zero paused scientist time. Linked interaction runs project active and
paused seconds from the current canonical ledger segment at the semantic-lock checkpoint. Prior
linked segments are not aggregated into the current run's record.

### Model accounting

`model_usage.calls` counts only provider calls initiated and observed by the sc-referee controller.
It is zero for the current CLI/skill protocol. Submitted model-authored SemanticAssertions and
WorkItems do not increment this field because sc-referee did not observe their provider call.
Unknown token counts remain `null`; they are never inferred from packet size or proposal count.

### I/O, cache, and resource accounting

The current I/O fields project only metered snapshot identity reads:

- `source_bytes_read` is the full-digest byte count;
- `large_asset_bytes_read` is the sampled-fingerprint byte count; and
- `network_bytes_received` is `null`.

The extension `x-io-measurement-scope: snapshot_identity_reads_only` makes the incomplete
instrumentation explicit. Parser, graph, report, and storage I/O are not implied to be included.

Cache hits, misses, and invalidations are current-AuditRun parser-cache counts only. A linked run
that merely carries parent cache records reports zero current-run cache activity. The extension
`x-cache-scope: current_audit_run_parser_cache_only` preserves that boundary.

Unmeasured CPU time, peak memory, and token usage remain `null`. No zero is used to represent an
unknown quantity.

## Rejected alternatives

- Mutating the semantic lock after report completion would make the lock non-immutable.
- Measuring replay wall time would make semantic replay output differ from its source lock.
- Calling the semantic-lock measurement a completed run would overstate its boundary.
- Counting proposal submissions as model calls would invent controller-observed provider usage.
- Treating snapshot identity bytes as total I/O would conceal unmetered reads.
- Publishing the deadline ledger as a public record without a schema release would bypass schema
  governance.

## Acceptance evidence required

1. General audits validate one semantic-lock PerformanceRecord and preserve it byte-for-byte in
   replay and canonical JSONL.
2. Cold and warm audits project current-run parser cache misses and hits respectively.
3. An injected-time interaction projects exact current-segment active and paused time while model
   usage remains zero for externally submitted proposals.
4. A second linked segment does not aggregate the first segment's time or cache activity.
5. Tests prove the record identifies its measurement and I/O scopes and cannot be interpreted as
   a run-final measurement.
6. Reports label the record as a semantic-lock measurement and continue to derive final outcome
   from AuditRun/CoverageRecord state.

## Consequences

- Schema v0.8.0 remains immutable; this ADR narrows use of fields and extensions already accepted.
- Public aggregate measurements become replayable without promoting the deadline ledger.
- Total run time, detailed stage timings, complete I/O accounting, CPU, memory, provider tokens,
  service latency, and the public deadline event chain remain explicit coverage limitations.
- A future schema may add a run-final measurement boundary and typed deadline segments without
  reinterpreting records produced under this profile.

## Acceptance record

- Decision: accept ADR-0006 using immutable schema release `0.8.0`.
- Accepted by: repository owner in the implementation task on 2026-07-28.
- The measurement is explicitly bounded through semantic lock and does not claim run-final time.
