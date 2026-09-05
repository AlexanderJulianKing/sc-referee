# Migration from the earlier public implementation

This branch is a total architectural replacement. It does not preserve backward compatibility with
the earlier public CLI, Python API, configuration files, demo datasets, benchmark engine, audit
directories, or internal record layout.

The earlier Git history remains in the repository so the replacement can be reviewed as a pull
request. That history is provenance, not a compatibility requirement.

## From 0.3.0 to 0.4.0

Program `0.4.0` uses public record schema `0.21.0` and adds these user-visible release mechanics:

- The program has reported public record schema `0.21.0` since before this release; the README
  banner was stale at `0.19.0` and is corrected here. Schema `0.20.0` adds the exact dependence
  detector `2.1.0` qualification identity and the materiality shape for reportless Findings.
  Schema `0.21.0` adds the exact dependence detector `3.1.0` qualification identity. Schemas
  `0.19.0` and `0.20.0` remain immutable migration baselines. See the changelogs under
  `reference/schemas-v0.20.0/` and `reference/schemas-v0.21.0/`.
- `sc-referee draft-profile` deterministically validates an agent's proposed ordered outcome
  family and two-group contrast column against the selected protocol and CSV header. It writes the
  validated profile plus a `.provenance.json` sidecar; validation gives the proposal no authority.
- `sc-referee method-contract` accepts `--draft-provenance`. The method-contract skill now follows
  propose, validate, present, correct if needed, and scientist-confirm. The final freeze binds the
  scientist's `--actor-id`, the confirmed profile, and the validated provenance sidecar. See
  [`ADR-0082`](implementation/ADR-0082-METHOD-CONTRACT-DRAFT-THEN-CONFIRM.md).
- Development audits accept `--attestations` for the closed multiple-testing correction-scope
  question flow. Author attestations remain separate from Findings, and this development lane
  cannot emit a Finding. See
  [`ADR-0080`](implementation/ADR-0080-MULTIPLE-TESTING-CORRECTION-SCOPE-QUESTIONS-AND-ATTESTATIONS.md).
- The frozen multiple-testing 3.1-3.4 lanes remain byte-identical except for the performance-only
  re-pin of the v3 and v3.3 dataflow implementation bytes. The recorded `624`-row snapshot and
  `199`-project real-CLI comparison found zero output differences. See
  [`ADR-0081`](implementation/ADR-0081-FROZEN-LANE-PERFORMANCE-REPIN.md).
- `make test-parallel` is an opt-in development gate. It runs the eligible test lane in parallel
  and the serial-only lane separately; the ordinary `pytest` gate remains supported.
- Audit terminal output reports an Answer count when Answers are present.

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
sc-referee 0.4.0 (schema 0.21.0; starter lineage 0.1.0)
```

The program version, record-schema version, and historical starter lineage are deliberately
separate. The accepted `0.6.0` minimum-proud-product language refers to the architecture boundary,
not an already published Python package version.

## Release identity and prior implementation

The overhaul is released as program version `0.4.0`. Citation metadata names Alexander King as
the sole human author and separately acknowledges Codex and Claude as AI development
collaborators. The prior implementation remains recoverable from Git history; no compatibility
layer is claimed or added. A release tag and any W3ID deployment remain separate publication
operations.
