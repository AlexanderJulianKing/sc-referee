# Migration from v0.7.0 to v0.8.0

Add empty arrays for DataAsset, Variable, AnalysisDecision, SelectionEnvelope, Execution, and
Environment. Do not infer these records from filenames or roles. Preserve each v0.7.0 Claim's
result, operation, input, missing, and opaque references. Set all six new grades and the new
aggregate to `unavailable`; preserve the former aggregate in the
`x-v0-7-aggregate-lineage-status` Claim extension. Recalculate coverage accordingly. Do not carry
forward a StorageManifest because migrated bytes require a new manifest.
