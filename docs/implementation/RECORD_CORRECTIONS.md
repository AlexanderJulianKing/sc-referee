# Record corrections

## 2026-08-11 — schema-v0.19 acceptance test-count claim

The handoff and pushed commit message for commit `98793bb` stated that the full repository suite
had “3,960 passed.” Independent measurement at that commit found **3,428 passed**.

The retained Stage-3 run transcript was inspected. It records full-suite pytest commands as
successful, but it does not retain a pytest terminal summary or any measured count of 3,960.
The number 3,960 appears only in the assistant-authored final handoff text (duplicated when that
text was replayed into the transcript). No focused, vendored, or full-suite counts in the retained
record sum to 3,960. The discrepancy was therefore an unsupported manual transcription in the
handoff, not the result of a different pytest invocation. The pushed commit is immutable; this
entry supplies the audit-trail correction.
