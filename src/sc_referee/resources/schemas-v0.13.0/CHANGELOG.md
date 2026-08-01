# Changelog

## 0.13.0

- Added `ProjectExecutionAuthorization` with one-attempt, exact source-lock/snapshot/capability,
  image, argv, environment, output, limit, expiry, acknowledgement, and registry bindings.
- Replaced label-only rootless capability claims with an effective probe projection.
- Added exact authorization, consumption, policy, log, resource, and cleanup evidence to project
  workflow Executions.
- Added `AuditBundle.project_execution_authorizations` and linked record-union/catalog support.
- Added a fail-closed migration from v0.12.0; no migrated bytes grant launch authority.
