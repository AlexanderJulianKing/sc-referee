# Controller invariants for v0.19.0

- Binding, check, detector, profile, adapter, and threshold-policy identities are exact and
  content-addressed before any promotion can be considered.
- Path-valued evaluation ledgers are carried by `evaluation_refs`; they are never represented as
  invented typed adjudication records.
- Every software-maintainer approval identifies its actor, approval date, and governing ADR.
- Static-scope evidence explicitly discloses whether a Stage-3 comparison artifact exists.
- Schema validity is representation only: an independently installed, matching grant and all
  controller admission gates remain necessary for production Finding authority.
- Migration never invents review, scientific approval, qualification, or Finding authority.
