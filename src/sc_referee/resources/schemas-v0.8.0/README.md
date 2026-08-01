# sc-referee schema package

**Version:** 0.8.0

This immutable JSON Schema Draft 2020-12 package defines the public sc-referee record model at
`https://w3id.org/sc-referee/schema/v0.8.0/`.

Version 0.8.0 implements accepted ADR-0005. Claim lineage is graded independently across report,
result, computation, input, execution, and semantic origin. DataAsset, Variable,
AnalysisDecision, SelectionEnvelope, Execution, and Environment are public records. The aggregate
Claim lineage status is a deterministic summary and cannot overstate a component grade.

Auditor verification and project workflow execution are different authorities. An auditor-owned
Execution never proves that project code ran. Column structure never supplies scientific meaning.
Accepted v0.7.0, v0.6.0, and v0.5.0 packages remain immutable.
