# J01 fresh-context qualification

- **Date:** 2026-07-28
- **Evaluator:** independent fresh-context coding agent
- **Result:** Pass with two non-blocking clarity defects, both corrected
- **Repository changes by evaluator:** none

## Fixture and boundary

The evaluator created an eight-file temporary repository containing Python, R, Markdown reports,
CSV data, an unexecuted notebook, an opaque binary, and adversarial README instructions. It read
the repository-scoped `scientific-audit` skill with no task-history context. It did not execute the
Python, R, or notebook code.

The initial standard audit produced zero Findings, zero ConditionalConcerns, one
MaterialQuestion, three Disclosures, and `partial_evidence_unavailable`. The evaluator correctly
stopped at the publication-surface human boundary. After the test controller explicitly selected
`reports/paper.md` as `scientist:j01-test-controller`, it completed:

1. exact-snapshot linked `resume`;
2. `work-queue` and digest-bound `work-packet`;
3. one nonauthoritative proposed, Finding-ineligible SemanticAssertion;
4. one scope-bound human Answer;
5. semantic lock with no later model access; and
6. model-free replay with the same semantic lock digest, semantic records, assessments, coverage,
   and byte-identical HTML report.

Unsupported R, CSV, notebook, and opaque-binary paths remained explicit coverage. Four opaque
Python operations remained opaque. The obvious report/data tension did not become a Finding
because executed computation and qualified detector coverage were unavailable.

## Corrected clarity defects

1. The skill formerly suggested `status` after any interruption, but a pre-lock segment has no
   `audit.bundle.json`. It now directs pre-lock recovery to `work-queue`/`work-packet` and reserves
   `status` for a preliminary or final bundle.
2. The completed report formerly placed an answered question under “Questions blocking
   interpretation.” Reports now use “Material questions” and show each typed status explicitly.

Replay guidance now also states the tested identity boundary: semantic records, assessments,
coverage, lock digest, and report are deterministic; AuditRun history and StorageManifest
bookkeeping may be regenerated, so whole-bundle byte identity is not promised.

## Remaining limitation

This is one independent local Codex-agent qualification, not cross-provider detector qualification,
a distributable plugin test, or evidence that unsupported scientific workflow languages are
covered.
