# Dependence pilot-a review escalation, attempt 1 retirement disclosure (corrected)

This document was first written attributing the attempt-1 projection failure to the reviewer's
response. That attribution was wrong, and this corrected version replaces it in full; the
correction itself is part of the record.

## Retired attempt

- Reviewer identity: `actor:dependence-a-reviewer-opus-07` (escalation role)
- Model: `claude-opus-5` (pinned binary `2.1.221`)
- Session id: `2b7e0d6f-c847-57ec-a58f-10e27e242dea`
- Prompt digest: `sha256:5b041772e0040aa62a6a2fb40f86d3472d64beed609fe6a07577c5fc8e3d3eb5`
- Stdout digest: `sha256:b63da499b3b90632f9d801698754b9330983300db24761239b5a5122fcc9ebfd`
- Transport error: none (the one-shot call completed cleanly, return code 0)

## What actually happened

The escalation call completed transport-clean and returned a well-formed batch review payload
covering exactly the three escalated cases. The projection failure ("Stage-1 workspace payloads
do not match the packets") was caused by a harness defect, not by the response: the escalation
branch of `_run_review_call` passed the full six-case workspace-payload mapping to the
projection while the packet set contained only the three escalated cases, so the set-equality
check refused every possible escalation batch. The escalation branch had never run in any prior
pilot, and the end-to-end fixture stubbed `_run_review_call` wholesale, so the defect was latent
until this first real escalation. The reviewer prompt itself was built from the case subset
only, so both attempt-1 and attempt-2 reviewers saw exactly the correct three blind workspaces;
blindness was never affected.

The defect was fixed by restricting the workspace-payload mapping to the case subset inside
`_run_review_call` (one line plus comment). With the fix, attempt 1's retained bytes would also
have projected. Re-projection of retained bytes is deterministic post-processing, not a second
model attempt.

## Disposition

- The first re-run attempt under `actor:dependence-a-reviewer-opus-08` (before the defect was
  understood) failed with the identical harness error, which is what proved the failure
  systematic and prompted the code-level diagnosis. Its capture is likewise retained,
  byte-complete, at `review/process-captures/escalation-dependence-a-reviewer-opus-08/`.
- Ordinal 07 remains retired: its packets were moved aside and rebuilt for ordinal 08 before
  the true cause was known, and the program does not un-retire identities. Its capture remains
  at `review/process-captures/escalation-dependence-a-reviewer-opus-07/`, byte-complete.
- The escalation record for this pilot is produced by re-projecting ordinal 08's retained bytes
  under the fixed harness. Exactly one escalation attempt's verdicts enter the review ledger.
- The primary review capture (`actor:dependence-a-reviewer-fable-10`) is untouched and reused by
  the retained-call mechanism throughout.
