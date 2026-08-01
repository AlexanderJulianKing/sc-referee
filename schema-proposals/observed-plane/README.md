# Observed-plane schema review candidate

This directory contains nonpublic templates supporting proposed implementation ADR-0002. The
templates deliberately contain `__SCHEMA_VERSION__`; they are not valid release artifacts and
must not be used for runtime persistence.

Build a disposable review package only after supplying an explicit candidate version:

```bash
python scripts/build_observed_schema_candidate.py \
  --release-version <exact-semver> \
  --output <empty-directory>
```

The builder copies the immutable public v0.5.0 baseline into a new versioned package, rewrites its
internal W3ID references, adds the six proposed schemas, updates the catalog, record union, and
AuditBundle, and adds positive review examples. Its `PROPOSAL_STATUS.json` always states that the
result is unaccepted and nonpublic.

The candidate reduces implementation uncertainty but does not resolve whether the release should
be 0.5.1 or 0.6.0. Only accepted architecture authority can make that decision.

The bounded migration rehearsal can then transform a generated walking-skeleton audit and validate
the complete candidate bundle:

```bash
python scripts/migrate_observed_schema_candidate.py \
  <audit-output> <candidate-schema-directory> \
  --output <empty-directory>
```

This rehearsal re-verifies the supported scalar from immutable source and CSV bytes, preserves
unknown semantic slots, resolves typed graph links, and fails closed on contradictory identity or
lineage evidence. It supports only the walking-skeleton scalar path and is not a general or
authority-approved production migration.
