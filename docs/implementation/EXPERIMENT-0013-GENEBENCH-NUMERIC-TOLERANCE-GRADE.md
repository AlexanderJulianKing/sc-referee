# Experiment 0013: GeneBench numeric-tolerance grade

- **Status:** Active evaluation-private experiment
- **Date:** 2026-07-29
- **Scope:** Non-executing comparison of one frozen public-development GeneBench answer with one
  exact `multi_numeric_tolerance` answer-side contract

## Purpose

Record whether an independently produced answer is outside an exact public benchmark tolerance
without executing the submitted workflow or the package's reference grader. This closes the
mechanical comparison gap exposed by Experiment 0012. It does not establish a scientific root
cause, create a Finding, admit a fixture label, populate a qualification metric, or support
detector promotion.

## Experimental envelope

`sc-referee-eval grade-genebench-public-numeric` consumes:

- one already-local GeneBench public package and its exact canonical preflight;
- one declared `eval_id`;
- one integrity-verified, terminal sc-referee audit captured before answer-side grading;
- one full-digest `answer.json` from that audit's immutable semantic-lock snapshot;
- one explicit grading timestamp after semantic lock; and
- one absent output path.

The grader reruns the complete package preflight, reads only the selected verified
`eval_config.json` as answer-side data, and supports only a closed `multi_numeric_tolerance`
contract with one finite nonnegative `absolute_tolerance` per exact ground-truth key. The answer
must be an exact `{answer, reasoning}` JSON envelope, have exactly the contract keys, and contain
finite JSON numbers rather than booleans or numeric strings. It compares each key with
`abs(actual - expected) <= absolute_tolerance` and emits value digests, absolute errors, and
per-key decisions.

Before comparison it verifies the audit bundle, deterministic report, semantic-lock digest,
canonical storage manifest, disposable SQLite projection, snapshot/identity chain, exact answer
bytes, terminal state, and absence of post-lock model access. The package's `reference_grader.py`
is neither imported nor executed. The output is write-once, self-digested, explicitly
public-development-only, and ineligible for metrics or promotion.

## Epistemic boundary

An outside-tolerance grade demonstrates only that the frozen answer and verified public answer
contract disagree by more than the declared numeric tolerance. It is not itself a Finding and does
not demonstrate which method, premise, implementation step, or scientific interpretation caused
the mismatch. Root-cause localization requires separate source-bound evidence and the ordinary
Finding admission gates.

## Exit evidence

- Matching and mismatching synthetic answers produce deterministic per-key grades.
- Answer, package, preflight, semantic-lock, timestamp, strict answer schema, grader-contract, and
  existing-output mutations fail closed.
- A malicious reference-grader marker remains absent across direct and CLI tests.
- The built evaluation CLI records and verifies its canonical self-digest without replacement.
- The real `hic_sv_masked_loop_strength` grade is
  `genebench-multi-numeric-grade:0c298df33af770f1ab3b`, bound to audit
  `audit:5ba8baec083d459ebda55d2d9e7a3b25` and semantic lock
  `sha256:1fb8a3635269b39731ffd3e949f06eb4cafdba0424fb4555cc809425b046f975`.
  Its case, control, and delta absolute errors are respectively `0.13780558924821396`,
  `0.5461243400592221`, and `0.408318750811008`; all exceed `0.02`. The grade is explicitly
  metric-, held-out-, and promotion-ineligible.

## Remaining limitations

This profile covers only absolute tolerances in the exact public contract shape above. Relative
tolerances, weights, min/max constraints, permissive numeric-string coercion, other GeneBench
grader types, and held-out corpora remain unsupported. Public benchmark answers may have appeared
in model training data, so this run cannot establish reviewer independence or qualification.
