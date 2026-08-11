# Migration from the earlier public implementation

This branch is a total architectural replacement. It does not preserve backward compatibility with
the earlier public CLI, Python API, configuration files, demo datasets, benchmark engine, audit
directories, or internal record layout.

The earlier Git history remains in the repository so the replacement can be reviewed as a pull
request. That history is provenance, not a compatibility requirement.

## Before replacing an existing installation

1. Keep the old environment or installed package until any reports you need have been exported.
2. Archive old audit directories as immutable historical artifacts.
3. Install the overhaul in a new virtual environment.
4. Run the bundled demo and check `sc-referee version` before auditing a real repository.
5. Create new audit output directories; do not reuse or overwrite an old run.
6. Compare conclusions manually and preserve the different capability envelopes.

Do not feed an old audit directory to the new CLI and assume that successful JSON parsing means the
old scientific meaning was recovered. The immutable schema packages contain explicit migrations
for accepted schema evolution inside the overhaul, but that is not a blanket migration promise for
the previous public program.

## Important behavior changes

### Evidence-first and non-executing

The supported production path statically inspects existing repository evidence. It does not run
project-authored scripts, notebooks, package installers, workflow engines, or containers.

Historical synthetic executor scaffolding remains disabled and is not a supported fallback.

### Conservative assessment categories

A Finding is reserved for a demonstrated issue that passes strict admission. Unknowns,
conditionals, opaque boundaries, unsupported paths, and unqualified experimental candidates are
kept in their own record types.

### Semantic lock and replay

The overhaul freezes semantic state before final deterministic evaluation and reporting. No model
calls occur after the lock. Replay regenerates supported semantic records and reports without
re-executing the project or consulting a model.

### Canonical storage

JSON and JSONL are canonical. SQLite is a generated, disposable index. Back up the canonical audit
directory rather than treating `audit.db` as the primary record.

### Explicit coverage

The new architecture records selected, inspected, unsupported, unavailable, and opaque boundaries.
It does not issue a global pass, risk score, publication approval, or correctness certificate.

## Versions

The current release reports:

```text
sc-referee 0.3.0 (schema 0.19.0; starter lineage 0.1.0)
```

The program version, record-schema version, and historical starter lineage are deliberately
separate. The accepted `0.6.0` minimum-proud-product language refers to the architecture boundary,
not an already published Python package version.

## Release identity and prior implementation

The overhaul is released as program version `0.3.0`. Citation metadata names Alexander King as
the sole human author and separately acknowledges Codex and Claude as AI development
collaborators. The prior implementation remains recoverable from Git history; no compatibility
layer is claimed or added. A release tag and any W3ID deployment remain separate publication
operations.
