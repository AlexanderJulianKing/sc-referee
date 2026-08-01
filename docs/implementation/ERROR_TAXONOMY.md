# Error and non-error taxonomy

| Code | Meaning | Controller effect |
|---|---|---|
| `parser_unsupported` | Valid surface outside parser coverage | Continue; disclose gap |
| `parser_malformed_source` | Source cannot be parsed | Continue; localize path |
| `parser_defect` | Parser violated its contract | Continue if possible; flag implementation error |
| `asset_missing` | Referenced asset unavailable | Continue; limit lineage |
| `opaque_operation` | Operation observed but internals unsupported | Continue; Disclosure |
| `material_unknown` | Scientific meaning could reverse a conclusion | Question; no Finding |
| `detector_not_applicable` | Target outside detector semantics | Continue |
| `detector_abstained` | Required evidence unavailable or conflicted | Continue; coverage gap |
| `detector_defect` | Detector violated manifest or invariant | Suppress candidate; implementation failure |
| `deadline_exhausted` | Hard elapsed deadline reached | Checkpoint and partial report |
| `host_model_limit` | Host refused further model work | Checkpoint and partial report |
| `sandbox_unavailable` | Qualifying project-execution backend absent | Static audit continues |
| `controller_integrity_failure` | Canonical records or identities cannot be trusted | Stop affected run |

Do not collapse these into a generic warning count.
