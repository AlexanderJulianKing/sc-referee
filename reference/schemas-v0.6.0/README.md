# sc-referee schema package

**Version:** 0.6.0

This immutable JSON Schema Draft 2020-12 package defines the public sc-referee record model at
`https://w3id.org/sc-referee/schema/v0.6.0/`.

Version 0.6.0 promotes the minimum observed-computation and control-plane records accepted by
ADR-0002: `AuditRun`, `StageResult`, `FileRecord`, `Operation`, `Artifact`, and `ObservedResult`.
`AuditBundle` now requires arrays for all six record types. Existing 0.5.0 documents remain valid
only under the immutable 0.5.0 package; they are never rewritten in place.

Accepted ADR-0003 permits an unresolved `PublicationSurface` with no candidates only when
publication materiality remains unassessable and an open `MaterialQuestion` is linked. A
`CoverageRecord` may use no publication-surface references only when it explicitly labels that
scope unresolved or unavailable. Resolved surfaces and resolved coverage still require evidence.

The epistemic boundary is unchanged: a Finding is a narrowly worded demonstrated issue. Unknown,
conditional, unsupported, or opaque evidence is represented explicitly and is not a Finding.

## Validation

```bash
python tools/validate_records.py examples
pytest -q
```

Schema validation establishes record shape and selected deterministic invariants. It does not
establish scientific detector validity, graph reachability, W3ID deployment, or a global
correctness claim.
