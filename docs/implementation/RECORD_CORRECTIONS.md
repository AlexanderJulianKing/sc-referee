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

## 2026-08-11 — method-conflict check registration invalidated installed grant pins

Registering the question-only multiple-testing check in commit `d09c9fe` changed the shared
bounded-analysis method-conflict detector manifest's check allowlist. That manifest digest is an
input to every method-conflict binding digest, so both installed production grants became stale
even though neither promoted check, adapter, recognition grammar, sealed examination, metric, nor
threshold changed. The stale state failed closed: capability-matrix generation refused both
binding-scoped grants rather than publishing authority under mismatched identities.

The two promotion records and installed grant resources were deterministically re-derived from
the unchanged sealed evidence at the new live detector and binding identities. The canonical
first-Finding demonstrations were also rerun because their audit bundles and semantic locks
correctly pin the installed qualification and binding digests.

Standing procedure: **any registration of a check in the shared method-conflict detector allowlist
must re-derive every installed method-conflict grant in the same commit**. CI now checks both that
the capability matrix builds and that each installed pin's binding and detector-manifest digests
equal its live registry binding. A future authority-design decision should consider removing the
unrelated-check allowlist from binding identity so question-only registration does not invalidate
otherwise unchanged production grants.
