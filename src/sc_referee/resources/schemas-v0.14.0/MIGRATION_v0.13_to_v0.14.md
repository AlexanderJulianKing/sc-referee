# Migration from v0.13.0 to v0.14.0

- Mark existing WorkItem packets `semantic_or_auditor_work_v1` and recompute their packet digest.
- Create no project-execution WorkItem and no private controller state.
- Mark existing ProjectExecutionAuthorization evidence
  `legacy_work_item_semantics_unavailable` and set its WorkItem digest to null.
- Demote project-workflow Executions depending on legacy authorization to unavailable projection.
- Downgrade dependent fixtures and remove authoritative metrics.
- Clear StorageManifests because canonical bytes change.
