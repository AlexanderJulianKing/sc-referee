# Migration from v0.18.0 to v0.19.0

Ordinary public records receive the new schema version and historical qualification records gain
null binding scopes while retaining deferred threshold policy and no promotion authority.

The two Round-1 private method-promotion record pairs require an explicit fail-closed re-stamp:
path-valued review ledgers move from `agent_adjudication_refs` to `evaluation_refs`; author ids are
derived from the digest-frozen authoring protocol; human-scientific approvals remain empty; the
non-schema `positive_issue` label is removed; maintainer actors are nested inside dated,
decision-bound approvals; and the Stage-3 artifact disclosure is retained. Private absolute-count
annotations remain external grant-pin gates rather than becoming self-certified threshold-policy
or safety-gate fields. The migration report records every such projection and creates no grant or
Finding authority.
