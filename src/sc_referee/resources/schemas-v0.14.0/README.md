# sc-referee schema release 0.14.0

This immutable accepted local release implements ADR-0014's typed, non-model
`project_execution` WorkItem request and exact authorization binding. A locked request is not
authority: a fresh direct single-use authorization and qualifying rootless OCI capability remain
mandatory before any launch.

The package is forward-only from v0.13.0. It does not claim W3ID deployment, public
backend availability, or authorization of any particular workflow.
