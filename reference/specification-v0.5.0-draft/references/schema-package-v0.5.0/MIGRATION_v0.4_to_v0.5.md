# Migration from schema v0.4.0 to v0.5.0

Version 0.5.0 is a breaking schema revision.

- Change every schema version and canonical reference from `v0.4.0` to `v0.5.0`.
- Replace `independent_scientific_approvals` in `DetectorQualification` with `review_basis`, `agent_adjudication_refs`, optional `human_scientific_approvals`, required promotion safety gates, and an explicit qualification-basis disclosure.
- Replace detector-manifest scientific-approval counts with qualification review basis and agent-adjudication counts.
- Add `AgentReview`, `BenchmarkAdjudication`, `BenchmarkFixture`, `CapabilityMatrix`, and `ROCrateExport` records.
- Add corresponding arrays to `AuditBundle` and references to `RecordUnion`.
- Historical v0.4 records remain valid under the v0.4 namespace and MUST NOT be silently reinterpreted as v0.5.

- Stage-2 `AgentReview` records require an explicit falsification attempt; eligible adjudications require complete falsification records and per-provider participation counts.
- Hard-negative fixtures require clean execution and a documented decisive innocent explanation.
- Capability-matrix detector entries require review-basis disclosure and enforce maturity/output coherence.
