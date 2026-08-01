# Experiment 0036: One-command semantic regression corpus

## Question

Can one development command rerun every local retained corpus case and detect changes in the
scientific meaning of direct audits and replays without treating timestamps, run identities,
rendered reports, or disposable SQLite as canonical evidence?

## Scope

This experiment completes post-MPP backlog item L02. It adds answer-side development machinery
only. It changes no public schema, record meaning, detector authority, Finding admission rule,
scientific-check behavior, calculation-check behavior, model privilege, or project-execution
privilege.

The canonical execution plan binds the current regression-ledger digest to four already retained
Benjamini-Hochberg repository controls. The runner derives every pytest node ID from the ledger,
runs the unique selectors in one subprocess, copies each retained repository workspace to a
temporary directory, statically audits the copy, replays its semantic lock, and compares a closed
semantic projection. The projection includes assessment counts, exact question dimensions,
Disclosure title counts, calculation-check identities, applicability, comparison outcomes, output
ceilings, coverage termination reasons, execution and authorization counts, model-call state, final
audit state, and replay equality.

Run IDs, timestamps, HTML, internal record identities, and `audit.db` are absent from the
projection. Retained target-project code is not executed. The command emits an optional canonical,
create-once, timestamp-free receipt and explicitly forbids using the run as detector qualification
evidence.

## Acceptance criteria

1. `python scripts/run_regression_corpus.py` runs every local ledger case through either its exact
   retained pytest selector or direct audit and replay.
2. Every repository-tree case is present exactly once in the digest-bound execution plan, and its
   declared applicability stays within the ledger contract.
3. A lost question, new false question, changed output ceiling, missing or new Disclosure,
   unexpected Finding or ConditionalConcern, calculation applicability or outcome drift, partial
   coverage change, replay difference, target-project execution, execution authorization, model
   call, or post-lock model access fails with a specific reason.
4. Repeated runs produce the same semantic receipt and leave every retained corpus byte unchanged.
5. The corpus includes an explicit unsupported case, an explicit replay guard, and partial direct
   audits.
6. CI and the complete handoff verifier run the one-command corpus.

## Tests added

`tests/test_regression_corpus_runner.py` validates exact direct-case coverage, plan and ledger
binding, registry/component binding, safe workspace paths, canonical JSON, qualification-safe
authority, create-once canonical receipts, deterministic repeated audits, retained-tree immutability,
unsupported and replay roles, partial coverage, timestamp/identity/report/SQLite independence, and
each semantic comparison mutation with its exact failure class.

The L01 ledger adds two focused cases: the existing count-model unsupported producer test and the
existing scientific-registry semantic-lock replay test. The one command now represents 31 ledger
cases through 19 unique pytest selectors and four direct audit/replay controls.

## Result

The focused L02 suite passes 26 tests. A real one-command run passes all 27 pytest-backed ledger
cases through 19 unique selectors and field-compares all four direct controls. The ambiguous case
retains its multiplicity question; the corrected twin remains conformant; the hard negative remains
not applicable; and the positive remains nonconformant with its bounded Disclosure. All four have
zero Findings, zero ConditionalConcerns, zero target-project executions or authorizations, zero
model calls, no post-lock model access, partial coverage, and exact semantic replay.

The first test run found that auditing a retained workspace in place created a project-local cache.
The runner was corrected to audit a temporary copy, and a repeated-run digest assertion now proves
that the retained source tree remains unchanged.

## Remaining limitations

- Pytest-backed cases retain their focused assertions rather than receiving the full field-by-field
  direct comparison used for materialized repository controls.
- External revisions require a separate pinned, digest-verified offline preparation step before a
  future runner can execute them.
- This answer-visible corpus is development regression evidence only. It does not qualify a
  detector or establish general scientific validity.
- L03 must still supply every mandatory regression role for every active module.
