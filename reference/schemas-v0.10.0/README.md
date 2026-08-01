# sc-referee schema package

**Version:** 0.10.0

This immutable JSON Schema Draft 2020-12 package defines the public sc-referee record model at
`https://w3id.org/sc-referee/schema/v0.10.0/`.

Version 0.10.0 implements accepted ADR-0009. It separates qualification-only detector candidates
from production Findings, records fresh cross-provider Stage-3 comparison reviews, deterministically
reconciles detector/root-cause case outcomes, and publishes typed problem-clustered metric evidence.

No record in this release permits detector promotion while the numeric threshold policy remains
deferred. Evaluation candidates have no production Finding authority. Prose similarity, model
confidence, and majority vote cannot establish detector/root-cause equivalence. Accepted v0.9.0 and
earlier schema packages remain immutable.
