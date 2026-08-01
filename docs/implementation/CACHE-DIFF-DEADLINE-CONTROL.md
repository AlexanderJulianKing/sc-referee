# Project-local cache, audit diff, and linked deadline control

## Implemented scope

The general Python/Markdown path now caches parser results only when the immutable snapshot has an
exact full content digest. Cache entries live below the audited repository's
`.sc-referee/cache/v1/` root. The controller rejects a symbolic-link or nondirectory cache
boundary and does not substitute a user-global source-derived cache.

Each parser cache key binds:

- the resolved project identity;
- exact source content digest and safe repository-relative path;
- parser component and tool versions;
- public schema version; and
- the normalized cache-policy digest.

Accepted ADR-0007 wraps every parser blob, descendant blob, parser index, and descendant index in
a canonical `hmac_sha256_external_key_v1` envelope. The HMAC covers normalized content, format,
project identity, and a nonsecret key identifier. Verification occurs before a cached scientific
payload is consumed. An offline repository/cache writer can recompute plain hashes but cannot
forge reuse without the external key.

The default provider first accepts `SC_REFEREE_CACHE_AUTH_KEY` as URL-safe base64 encoding exactly
32 key bytes. This is required in CI. Otherwise it generates or retrieves the key through macOS
Keychain or Linux Secret Service when available. The key is sent to a platform creation command on
standard input, never as a command argument. Missing, invalid, unavailable, or malformed
credentials make persistent caching unavailable for that run; static analysis continues normally.

Python keys additionally bind every literal local file dependency observed by the parser. A
referenced file must have an exact full digest or that Python result remains uncached. Exact
absence is bound as absence, so later creation also forces recomputation.

The current index identifies the active key for each parser/path pair. A changed or removed path
invalidates only that pair; unchanged exact inputs remain hits. Cached ParserResults are rebound
only to the new AuditRun identifier, then publicly schema-validated before graph promotion.
Per-Python static-graph promotions and the bounded repository lineage plane have separate
versioned descendant keys. Static graphs depend on their exact parser key. Bounded lineage depends
on every relevant static-graph key plus the auditor runtime identity. A warm exact hit skips both
promotion and bounded verification. Claims, questions, detectors, and reports are still
recomputed from the materialized public records.

One nonblocking exclusive writer lease now covers an audit's parser and descendant cache phase.
If another process already holds it, the contending audit marks the cache unavailable, performs
the static work directly, writes no cache blob or index, and continues without waiting. The lock
target is opened without following symlinks and must be a regular file. This serializes mutable
index updates while preserving the audit deadline.

`sc-referee diff <before-audit> <after-audit>` compares two integrity-verified bundles. Its
digest-bound implementation document reports added, removed, changed, and unchanged paths, the
after-run parser-cache disposition, and assessment-count deltas. It explicitly is not a
correctness comparison. `AuditDiff` does not yet have an accepted public record schema.

## Linked deadline ledger

Every `resume` creates a fresh deadline segment using the source audit's mode and cutoff/deadline
pair. It does not extend the parent segment. The canonical
`observed/deadline-ledger.json` retains the linked prior segments and is protected by a semantic
digest.

The current segment counts wall time from segment creation through model proposal submission,
pauses only after the bounded proposal is durably submitted and the controller is explicitly
awaiting a scientist Answer, resumes at the Answer timestamp, and counts controller work through
semantic lock and report completion. A hard deadline before semantic lock writes a terminal public
AuditRun journal and preserves the registered absence of a pre-lock AuditBundle. A post-lock
deadline produces partial-budget coverage and an integrity-verifiable partial bundle.

Accepted ADR-0006 projects the current segment into exactly one public PerformanceRecord at
semantic lock. Initial audits use the most recently checked in-memory deadline value; linked
segments use only the current ledger segment's active and paused seconds. The public record binds
the lock-time ledger digest, reports zero controller-observed provider calls for externally
submitted proposals, and carries only current-AuditRun parser-cache counts. Replay copies the
record exactly and does not sample a new clock.

## Acceptance evidence

- cold parser misses become exact warm hits without changing stable parser-result identities;
- changing one Python file invalidates that parser entry while an unchanged Markdown entry hits;
- removal is reported as both an audit-diff removal and a cache invalidation;
- a report-only edit preserves Python static-graph and bounded-lineage hits;
- changing a literal CSV dependency invalidates the Python parser, static graph, and bounded
  lineage and changes the independently verified result;
- an exact warm run succeeds with the graph promoter and bounded verifier replaced by fail-fast
  test doubles, proving that the descendants were actually reused;
- identical files in a different repository remain misses;
- a project-authored `.sc-referee` symlink is never followed or written through;
- replay preserves public CacheEntry and CachePolicy records;
- a two-hour explicit scientist wait records 7,200 paused seconds but only 180 active seconds;
- a second linked interaction retains the first segment and receives a fresh budget; and
- quick-mode pre-lock work terminates durably at 300 active seconds;
- a contending cache run completes without waiting or changing either mutable index, after which a
  normal changed run invalidates coherently and an exact warm run hits; and
- a symlinked writer-lease target is rejected without changing its target.
- parser payload tampering remains a miss even when every ordinary digest is recomputed;
- parser- or descendant-index tampering forces fail-closed recomputation;
- rotating the external key makes every old entry miss, followed by exact warm hits under the new
  key;
- no audit, report, lock, or cache file contains raw, base64, or hexadecimal key bytes;
- a missing key completes the audit without persistent reuse; and
- a project-authored nested cache-shard symlink is neither read nor written through.
- general and linked runs emit one schema-valid PerformanceRecord whose JSONL and replay bytes are
  identical;
- cold and warm audits project current-run parser misses and hits without counting descendant
  cache activity; and
- a second linked segment excludes its parent's elapsed, paused, and cache counts.

## Remaining limitations

- Static graphs are cached per Python source, but bounded lineage is one repository aggregate and
  therefore invalidates as a unit when any relevant Python/data dependency changes.
- The audit-diff document and detailed deadline event chain are implementation protocols, not
  accepted public record types. Public promotion requires an ADR and schema revision.
- The public PerformanceRecord ends at semantic lock. It excludes post-lock report, storage, and
  integrity time and does not provide total run duration, detailed stage timing, CPU, memory,
  token, network, or complete I/O measurements.
- HMAC authentication defends repository content, copied/prepopulated caches, and offline writers
  that lack the external key. It does not defend against an arbitrary active same-user process that
  can read tool credentials or process memory. Platform backends have unit coverage; live
  macOS/Linux credential-store smoke tests remain environment-specific external evidence. Cache
  reuse is never itself Finding evidence.
