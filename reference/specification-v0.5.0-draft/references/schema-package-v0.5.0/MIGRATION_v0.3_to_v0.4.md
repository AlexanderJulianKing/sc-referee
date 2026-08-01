# Migration from schema 0.3.0 to 0.5.0

Schema 0.5.0 is a breaking pre-1.0 release.

## Canonical identity change

All `$id` and `$ref` values move from the placeholder `example.org` namespace to immutable W3ID identifiers under:

```text
https://w3id.org/sc-referee/schema/v0.5.0/
```

Records must set `schema_version` to `0.5.0`. A 0.3 record is not made into a 0.4 record by changing only its version string; it must be revalidated against the 0.4 schema.

## AuditPlan additions

`AuditPlan` now requires:

- `snapshot_policy`
- `parser_policy`
- `storage_policy`
- `cache_policy`
- `sandbox_policy`
- `report_policy`

These fields encode accepted implementation foundations and remove environment-dependent defaults.

## New record types

- `tool_identity`
- `repository_snapshot`
- `parser_manifest`
- `parser_result`
- `sandbox_capability`
- `cache_policy`
- `cache_entry`
- `storage_manifest`
- `performance_record`
- `detector_qualification`

`AuditBundle` requires arrays for each new record type. Empty arrays are valid when a bundle legitimately contains no instance.

## Detector manifests

The `validation` block may now link to a detector-qualification record and report maintainer and independent-scientific approval counts. Cross-record consistency remains a controller invariant.

## Product rename

Distribution metadata and documentation now use `sc-referee`. The Claude invocation remains `/scientific-audit`.
