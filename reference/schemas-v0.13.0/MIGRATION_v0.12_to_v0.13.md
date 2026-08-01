# Migration from v0.12.0 to v0.13.0

- Add an empty `project_execution_authorizations` array. Never create a controller-registry entry.
- Mark prior claimed project capability as `legacy_probe_projection_unavailable`, set support and
  rootless verification false, and retain no invented capability proof.
- Mark prior project-workflow Executions `legacy_authorization_projection_unavailable`; other
  executions are `not_required` or `imported`. No project-execution projection is invented.
- Downgrade complete fixtures dependent on legacy project execution and make linked outcomes and
  authoritative metric sets ineligible.
- Clear StorageManifests because canonical bytes change.
