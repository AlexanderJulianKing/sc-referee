# ADR-0001: Define the storage-manifest digest binding set

- **Status:** Proposed; implemented only as an explicit Milestone 0 extension profile
- **Date:** 2026-07-27
- **Related requirements:** ADR-0029, `storage-manifest.schema.json`, C03

## Context

The public v0.5 `StorageManifest` schema requires `canonical_manifest_digest` but does not
define the canonical serialization or the files it binds. A byte manifest also cannot include
the `StorageManifest` record or an aggregate `AuditBundle` containing that record without a
self-reference.

## Proposed decision

Define profile `x-sc-referee-m0-canonical-files-v1` as follows:

1. Bind `semantic.lock.json` and every JSON or JSONL file under `observed/` and `derived/`.
2. Exclude the immutable source materialization under `observed/snapshot/materialized/`; its
   file identities are bound by the repository snapshot records.
3. Exclude `derived/storage-manifest.jsonl` and `audit.bundle.json` to avoid recursive hashes.
   The bundle remains a normalized aggregate of the individually validated native records.
4. Sort entries by root-relative POSIX path. Each entry contains `path`, `digest`, and
   `size_bytes`. Compute `canonical_manifest_digest` as the sc-referee semantic SHA-256 digest
   of that entry array.
5. Verify that the manifest has neither missing nor extra files and that the disposable SQLite
   index contains exactly the normalized records in the audit bundle.
6. Treat successful `StorageManifest` emission and verification as the final run commit marker.
   The append-only terminal run-journal entries are written before that marker so their final
   bytes are included. A terminal journal state without a valid manifest is therefore an
   incomplete commit, not a trustworthy completed audit.

The binding entry array and exclusions are stored in `StorageManifest.extensions` with `x-`
keys. This is a temporary implementation profile, not a change to the W3ID schema contract.

## Promotion condition

Accept or supersede this ADR before treating the digest profile as a durable public
interchange contract. Bundle signing and external trust-root policy remain deferred under
OD-033.
