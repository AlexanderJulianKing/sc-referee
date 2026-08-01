# Experiment 0006: Deterministic RO-Crate 1.3 export profile

- **Status:** Active local implementation profile; not an external validation claim
- **Date:** 2026-07-28
- **Authority:** Specification ADR-0039, SA-FR-099, AC-63, and accepted public schema v0.12.0
- **Scope:** One integrity-verified completed audit exported as an attached RO-Crate 1.3 ZIP

## Purpose

Implement the already-specified RO-Crate export without changing native record authority,
executing project code, or silently choosing an ambiguous self-referential digest.

## Exact profile

The exporter accepts only an audit that passes the existing bundle, semantic-lock, canonical-file,
SQLite-projection, and report-contract checks. It creates one new ZIP path without replacement and
contains:

- `ro-crate-metadata.json`, using the RO-Crate 1.3 context and metadata descriptor;
- `ro-crate-export.json`, a schema-valid public `ROCrateExport` record;
- `native/audit.bundle.json` and `native/report.html`; and
- every storage-manifest-bound native JSON/JSONL file plus the self-excluded native
  `derived/storage-manifest.jsonl`.

The disposable SQLite projection, parser caches, materialized repository snapshot bytes, and any
unbound auxiliary files are excluded. The native files that are included are copied byte for byte;
the source audit is never modified.

The CLI requires a declared crate-author name and license URI/name. These values describe the
exported audit package, are not authenticated, and do not establish licensing or authorship of the
audited scientific project.

## Digest decision

`ROCrateExport.content_digest` uses
`canonical-json-file-inventory-excluding-ro-crate-export-v1`: SHA-256 over canonical JSON for the
sorted `{path, digest, size_bytes}` inventory of `ro-crate-metadata.json` and every `native/`
payload file. `ro-crate-export.json` is excluded because it contains `content_digest` itself. The
record names this profile and exclusion in `extensions`. The ZIP container digest is deliberately
not substituted for the schema field.

## Validation boundary

Offline validation checks the closed ZIP member set, safe unique paths, stored non-symlink files,
canonical generated JSON, RO-Crate 1.3 descriptor/root/file entities, declared author and license,
file sizes/digests, native bundle schema and report policy, semantic-lock binding, storage-manifest
binding, export-record schema, entity references, and the inventory digest. It does not resolve the
network JSON-LD context, authenticate the declared author or license, validate an external profile,
or prove that a third-party RO-Crate consumer accepts the archive.

## Exit evidence

- deterministic exports from the same audit and declared metadata are byte-identical;
- every included native file is byte-identical to its source;
- native bundle and report tampering, metadata drift, digest drift, duplicate/unsafe members, and
  overwrite attempts fail closed;
- the CLI export and offline validation round-trip passes from an installed wheel; and
- full handoff verification records the profile without changing public schema v0.12.0.

