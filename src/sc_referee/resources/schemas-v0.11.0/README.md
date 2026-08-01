# sc-referee schema package

**Version:** 0.11.0

This immutable JSON Schema Draft 2020-12 package defines the public sc-referee record model at
`https://w3id.org/sc-referee/schema/v0.11.0/`.

Version 0.11.0 implements accepted ADR-0010 and ADR-0011. It represents experimental detector
outputs that satisfy every non-maturity Finding check without granting production Finding authority,
preserves one exact metric projection per source DetectorResult, and closes all twelve qualification
metric formulas and the deterministic clustered-bootstrap protocol.

Migration from v0.10.0 is fail-closed. It invents no detector state, evaluation candidate,
opportunity projection, metric, interval, qualification, or Finding. Accepted v0.10.0 and earlier
schema packages remain immutable.
