# Experiment 0008: Root SHA-256 checksum-manifest identity profile

- **Status:** Active local implementation profile; not independent byte verification
- **Date:** 2026-07-29
- **Authority:** Specification ADR-0020, SA-FR-016, SA-FR-050, sections 3.8 and 6.11, accepted public schema v0.14.0, and accepted implementation ADR-0017
- **Scope:** Conservative import of repository-supplied per-file SHA-256 declarations for inventoried regular files

## Purpose

Make very large local assets more identifiable without reading their complete bodies, while
preserving the distinction between a checksum declared by the audited repository and a checksum
independently verified by sc-referee.

## Exact profile

The snapshotter considers only root-level regular files named `SHA256SUMS`, `sha256sums.txt`, or
with a case-insensitive `.sha256` suffix. A candidate is usable only when the byte-read policy
captured its complete body and strict UTF-8 decoding succeeds. Every nonblank, non-comment line
must have exactly this form:

```text
<64 lowercase hexadecimal characters><two ASCII spaces><safe repository-relative POSIX path>
```

Absolute paths, traversal components, backslashes, noncanonical paths, self-references, malformed
lines, unsupported checksum syntax, and empty manifests invalidate the whole candidate. Nested
manifest candidates remain outside this profile because their path base is not standardized.

A target must be an inventoried regular file. More than one admitted declaration for the same
target is treated as ambiguous, even when the text agrees, and no declaration is selected. A
complete digest independently computed from the target body always outranks a repository
declaration.

## Evidence meaning

For an admitted target, public `AssetIdentity.identity_evidence.manifest_digest` is the per-file
SHA-256 value declared on the exact referenced manifest line. The `manifest_ref` binds the root
manifest path, line number, quoted line, and independently computed full digest of the manifest
file itself.

This tier does not establish that the target bytes match the declared digest. The target body is
not materialized merely because the declaration exists. The identity therefore carries an
explicit limitation, and coverage says that only conclusions depending on exact target-byte
verification are limited. Snapshot capture retains the inventoried target size and modification
time as extension metadata for later workspace-divergence checks; unchanged metadata cannot prove
unchanged target content.

Malformed, ambiguous, or over-budget candidates are localized in the repository snapshot and
coverage record. They do not become Findings and do not prevent independent source, report, claim,
or replay work.

## Exit evidence

- a 10-billion-byte sparse asset receives manifest identity without full target read or
  materialization while its report and source remain inspectable;
- exact manifest source evidence and the repository-supplied limitation validate under public
  schema v0.14.0 and replay byte-for-byte;
- conflicting, unsafe, nested, and over-budget manifests cannot upgrade target identity;
- a computed full digest wins over a conflicting declared checksum;
- invalid manifest syntax becomes a localized replayable coverage gap; and
- no test imports or executes project-authored code.
