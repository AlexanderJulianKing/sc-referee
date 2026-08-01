# Migration from v0.11.0 to v0.12.0

Migration is fail closed. Existing eligible fixtures receive
`legacy_proof_projection_unavailable` and `proof_evidence: null`; excluded ambiguous fixtures
receive `excluded_label`. No capture, packet, transcript, workspace, chronology, execution,
sandbox, hard-negative explanation, or other proof is inferred. Case outcomes copy the fixture
status and digest, receive a new identity, and become metric- and promotion-ineligible when proof
is unavailable. Legacy QualificationMetricSets are retained only in a namespaced bundle extension,
and StorageManifests are cleared because canonical bytes change.
