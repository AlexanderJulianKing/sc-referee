# Migration from v0.10.0 to v0.11.0

Update only schema namespaces and versions for existing records, except as follows:

- Give each legacy DetectorCaseOutcome
  `metric_input_status: legacy_source_projection_unavailable`, an empty
  `detector_result_outcomes` array, and false metric/promotion eligibility. Preserve its prior flags
  in namespaced migration metadata.
- Remove every legacy QualificationMetricSet from an AuditBundle's authoritative metric-set array
  and preserve its exact payload only in namespaced migration metadata. A standalone legacy metric
  set is reported as non-authoritative legacy evidence and is not emitted as v0.11.
- Clear StorageManifest arrays because migrated canonical bytes require a new manifest.

Do not infer or create a DetectorResult state, evaluation candidate, opportunity projection,
Finding, equivalence decision, estimate, interval, qualification, capability claim, or maturity.
