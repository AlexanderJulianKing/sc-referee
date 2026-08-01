# Changelog

## 0.14.0

- Added the closed `project_execution_request_v1` WorkItem packet and
  `awaiting_authorization` state.
- Kept semantic/model packets closed as `semantic_or_auditor_work_v1`.
- Bound authorization evidence to the exact WorkItem semantic digest and an explicit binding
  status.
- Added a fail-closed migration from v0.13.0; no request, digest, registry entry,
  launch authority, qualifying execution, fixture proof, or metric is invented.
