# Migration from v0.5.0 to v0.6.0

ADR-0002 authorizes these coordinated public record changes at version `0.6.0`.

Migration from the starter's `urn:sc-referee:starter:v0.1.0` records is fail-closed:

- rename `run_id` to `audit_run_id`; never retain both fields;
- rename the type-specific identifiers to `audit_run_id`, `file_record_id`, and
  `observed_result_id` where the candidate schemas require them;
- add the exact released `schema_version` and independently sourced public `Provenance`;
- convert snapshot, parent-run, parser-result, operation, artifact, identity, input, and output
  identifiers to typed `RecordRef` objects;
- derive FileRecord identity only through the linked public AssetIdentity; reject a mismatch
  between `identity_strength`, `digest`, and the AssetIdentity rather than choosing one;
- preserve symlinks as unfollowed inventory entries and preserve unreadable or unsupported paths
  as explicit limitations;
- map only literal independently checkable operation parameters; unknown dispatch becomes
  `opaque_operation` with a nonempty opaque boundary;
- migrate a scalar only when its producer, artifact, and source lineage can be linked explicitly;
  otherwise preserve partial, missing, or unavailable lineage;
- convert comparison, orientation, scale, unit, population, and timing independently into
  epistemic slots; an absent or provisional `unknown` value remains `unknown`; and
- reject any migration that would make an unknown semantic slot known without exact evidence.

Migration from a valid public v0.5.0 AuditBundle is also fail-closed:

- validate the complete source bundle under the immutable v0.5.0 package before conversion;
- reject mixed `schema_version` values;
- version existing public records and canonical schema-namespace fields together;
- add empty arrays for the six record types that v0.5.0 could not represent;
- never infer observed-plane records from unrelated claims, extensions, or prose; and
- drop the old StorageManifest because migrated bytes require a newly computed manifest.

Existing public v0.5.0 records remain valid under the immutable v0.5.0 package. The release builder copies and rewrites schemas into a new directory; it never edits the baseline in place.

A bounded migration rehearsal now covers the generated walking-skeleton scalar path, including
independent scalar re-verification, typed reference resolution, unknown preservation, and
public-bundle validation.
