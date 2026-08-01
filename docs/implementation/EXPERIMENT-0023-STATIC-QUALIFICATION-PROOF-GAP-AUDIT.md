# Experiment 0023: Static qualification-proof gap audit

- **Status:** Completed; follow-up accepted and implemented
- **Date:** 2026-07-30
- **Public schema change:** None
- **Production detector or Finding authority:** None
- **Accepted follow-up:** ADR-0022 and coordinated schema v0.15.0

## Question

Can accepted schema v0.14.0 qualify verified-good and hard-negative controls for the bounded
non-executing direction detector using existing independently produced evidence, without requiring
sc-referee to execute project-authored code or changing an accepted record's meaning?

## Inputs inspected

- accepted ADR-0012's fixture proof decision;
- accepted ADR-0017's evidence-first, non-executing MPP boundary;
- deferred ADR-0015's linked-execution closure analysis;
- the v0.14.0 `BenchmarkFixture`, `Execution`, and `AuditBundle` schemas;
- the isolated evaluator's control-fixture construction and proof replay;
- the complete fixture, Stage-3, metric, report, and migration tests; and
- Experiment 0011's exact bounded report/raw-mean direction detector envelope.

## Result

The answer is **no** for the controls required to qualify this detector.

| Fixture kind | Complete v0.14.0 proof without execution? | Exact boundary |
|---|---:|---|
| `positive_issue_fixture` | Yes | Panel, root-cause, immutable source, and chronology proof; no negative-control claim |
| `scope_verified_good` | No | May use only bounded documented external execution |
| `verified_good_fixture` | No | Requires `clean_environment_executed` plus Environment, Execution, and SandboxCapability |
| `hard_negative_fixture` | No | Requires the same clean execution plus exact suspicious-pattern and innocent-explanation evidence |
| `ambiguous_fixture` | Not eligible | Explicitly excluded from resolved metrics and promotion evidence |

The public schema rejects `execution_evidence: not_executed` for a complete verified-good or
hard-negative fixture. The evaluator independently rejects empty Environment and Execution inputs.
The added regression test locks both sides of that boundary.

An imported execution does not solve the general control requirement. It is admitted only for a
scope-verified-good fixture and cannot satisfy the required verified-good and hard-negative safety
gates. Representing it as clean project execution would invent authorization, sandbox, lock,
artifact, and identity authority. Deferred ADR-0015 separately establishes that v0.14.0 cannot
publish the complete linked-execution dependency closure needed for a clean control.

## Why static proof is appropriate for the motivating detector

Experiment 0011 makes a bounded source-level statement. Its required report sentence, raw table
bytes, auditor-owned mean calculation, Python operation, literal label orientation, writer path,
and opposite-claim search are all static and finite. The detector does not claim that the project
ran, that the report was rendered, that the biological conclusion is false, or that the whole
analysis is correct.

Forcing a project rerun would therefore establish a different fact from the detector premise. It
could be useful later for runtime lineage, but it is neither necessary nor sufficient for this
exact static contradiction. Conversely, a vague statement that the repository was reviewed is not
enough: the proof must close the detector-specific inputs, identities, scope, and counterevidence
checks independently of the detector output.

## Decision from the audit

A forward-only schema ADR is necessary. Existing v0.14.0 fields cannot be reinterpreted safely.
After fresh-context broad-design review, proposed ADR-0022 preserves all existing clean-control
kinds and adds distinct `static_scope_verified_good` and `static_scope_hard_negative` kinds. It
requires a pre-case frozen detector/verifier profile, independent rederivation from immutable raw
bytes, typed proof records, derived graph/chronology invariants, and proof-family-stratified metrics
and reporting. The complete 4+2 answer-blind scientific panel and every threshold, maintainer, and
promotion gate remain.

No schema, evaluator behavior, detector maturity, capability entry, or Finding permission changes
in this experiment. The accepted v0.14.0 package remains immutable.

Follow-up status: the owner subsequently accepted ADR-0022 and coordinated schema v0.15.0. The
implementation and its validation evidence are recorded separately; this gap audit remains the
historical evidence for why the forward-only change was necessary.

## Test, acceptance criterion, and remaining limitation

- **Test added:**
  `tests/test_evaluation_control_fixture.py::test_v014_deliberately_rejects_a_complete_static_control`.
- **Acceptance criterion satisfied:** the exact qualification blocker is demonstrated in both the
  public schema and runtime evaluator, and the revised proposed remedy neither depends on project
  execution nor lets production semantic machinery certify itself.
- **Remaining coverage limitation:** the proposed static proof structure has not been accepted or
  implemented. No real qualification case, independent reviewer evidence, metric, threshold, or
  promoted detector exists.
