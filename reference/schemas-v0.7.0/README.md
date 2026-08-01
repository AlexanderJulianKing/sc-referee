# sc-referee schema package

**Version:** 0.7.0

This immutable JSON Schema Draft 2020-12 package defines the public sc-referee record model at
`https://w3id.org/sc-referee/schema/v0.7.0/`.

Version 0.7.0 implements accepted ADR-0004 by adding public WorkItem and Answer records, typed
pre-lock semantic interaction states, and required AuditBundle arrays. Existing v0.6.0 and v0.5.0
documents remain valid only under their immutable packages and are never rewritten in place.

Model outputs remain proposals. Scientist answers establish intent only within explicit authority
scope. Neither may overwrite observed execution or bypass semantic lock and Finding admission.
