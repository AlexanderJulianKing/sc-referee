# Changelog

## 0.19.0 pre-use correction — 2026-08-11

- Corrected the accepted release in place before first use: agent-panel and mixed-panel review now
  require two path-valued `evaluation_refs`, so the conditional review-evidence branch genuinely
  narrows the unconditional one-reference floor.
- Kept the same release version because no grant was installed, no record was published outside
  this repository, and nothing external consumed the prior bytes.
- Recorded the prior closed-tree manifest-content digest for the audit trail:
  `sha256:7188bd85b51f28e57ff0aa022fc2a2043ec248968bac19b37a63599a616cce9d`.

## 0.19.0 — 2026-08-11

- Added exact detector-v0.3 binding scopes and pilot-informed numeric threshold policies.
- Added dated, decision-bound `MaintainerApproval` objects.
- Added the closed `stage3_comparison_artifact_exists` disclosure field.
- Assigned path-valued review ledgers to `evaluation_refs`; `agent_adjudication_refs` remains
  reserved for typed adjudication records.
- Preserved v0.18.0 as an immutable migration baseline.
