# Migration from schema 0.2.0 to 0.5.0

This is a breaking pre-1.0 migration.

1. Change every `schema_version` and versioned `$ref` from `0.2.0` to `0.5.0`.
2. Add `publication_surface_status` and `data_identity_summary` to every CoverageRecord.
3. For each causal Claim, create and reference one `CausalEstimand` and one `IdentificationContract`.
4. Represent the run policy in an `AuditPlan`; model call and token limits are `null` and host-managed, while elapsed-time deadlines remain finite.
5. Store final-surface resolution as `PublicationSurface`, data identity as `DataAsset`, network-derived evidence as `ExternalEvidence`, environment reconstruction as `EnvironmentReconstruction`, expensive external execution requests as `ReproductionRequest`, and timing and local usage metrics as `PerformanceRecord`.
6. Treat causal graphs as optional and `partial_open_world` unless an authoritative source explicitly asserts stronger completeness.
7. Update AuditBundle collections and record-union handling for the new record types.

The deterministic controller must reject a causal Claim that lacks the required causal references and must not infer absence of a causal edge from a partial graph.
