# Experiment 0051: Prospective ten-envelope qualification protocol

- **Status:** Evaluation infrastructure implemented; this repository contains no qualification
  case labels or outcomes
- **Date:** 2026-08-03
- **Related decisions:** ADR-0042, ADR-0056, ADR-0060, ADR-0061
- **Production impact:** None; the production package does not import this evaluation module
- **Finding impact:** None; protocol, ledger, and threshold artifacts explicitly carry no Finding
  or promotion authority
- **Execution impact:** None; the protocol does not execute inspected projects or invoke reviewers

## Objective

Make the remaining external qualification work finite and auditable without turning development
examples into evidence. The study-design layer must freeze the detector, ten atomic relation
envelopes, participants, authoring briefs, case assignments, pilot/held-out split, and the complete
control matrix before any scientific label or detector outcome is available.

## Implemented protocol

`sc_referee_evaluation.prospective_qualification` implements three write-once artifact stages:

1. `freeze_prospective_qualification_protocol` validates and freezes a caller-supplied study
   specification. Every pilot and held-out envelope must have exactly one error-bearing, corrected
   twin, valid alternative, hard negative, ambiguous, unsupported, and independently authored
   renamed implementation. Corrected and renamed cases bind the error-bearing reference directly.
2. `seal_prospective_outcome_ledger` requires exactly one retained outcome per frozen assignment.
   Contaminated, failed, withdrawn, unavailable, and intended-cell-mismatch outcomes remain in the
   ledger. No replacement or omission path exists.
3. `freeze_pilot_threshold_decision` accepts a threshold decision only after every pilot assignment
   is complete and its designed cell is independently confirmed. Held-out labels cannot predate an
   approved, digest-bound threshold decision.

The protocol binds disjoint author, Stage-1 reviewer, Stage-2 reviewer, and detector-implementer
identities and execution contexts. Stage-1 requires four reviewers across at least two providers;
Stage-2 requires two fresh reviewers across at least two providers. These are frozen declarations,
not proof that the people, providers, or transcripts are authentic.

Public and internal development cases may appear only in a development-regression block and are
always excluded from qualification metrics. Pilot cases are also metric-ineligible for final
qualification. Only complete, uncontaminated, externally authenticated, cell-confirmed held-out
outcomes are projected as held-out metric inputs. Even those records do not qualify or promote a
detector by themselves.

## Frozen ten-envelope template

`evaluation/prospective-qualification-v1/ten-envelope-study.template.json` binds one generic
check/candidate relation per target family to the current method-conflict binding digest. It
contains no task, benchmark, repository, fixture, or answer identity. In particular, the cis-MVMR
slot is the phase-split instrument-construction relation:

- `check:phase-split-mvmr-instrument-construction`; and
- `phase1-ld-conditional-signals-phase2-joint-coefficients`.

The file is a self-digested, machine-readable planning template with
`qualification_authority: none_template_only`. It intentionally omits invented detector locks,
participants, identity evidence, cases, labels, and outcomes.

## CLI surface

The isolated evaluation CLI exposes:

```text
sc-referee-eval freeze-prospective-protocol ...
sc-referee-eval seal-prospective-outcomes ...
sc-referee-eval freeze-pilot-thresholds ...
```

The canonical artifact shapes are published as evaluation-private JSON Schemas under
`evaluation/prospective-qualification-v1/`. Python validation additionally enforces chronology,
cross-record references, complete matrix coverage, role isolation, and digest replay.

The standalone scaffold builder freezes actual assignments only after it is given both the
coordinator envelope template and the independently self-digested benchmark-blind authoring
template:

```text
python scripts/build_prospective_study_scaffold.py \
  --template evaluation/prospective-qualification-v1/ten-envelope-study.template.json \
  --authoring-template evaluation/prospective-qualification-v1/benchmark-blind-authoring-briefs.template.json \
  --setup /path/to/private-study-setup.json \
  --output-root /new/write-once/study-package
```

The builder retains check IDs, candidate IDs, binding digests, block roles, and the blind-to-
coordinator relation map only in coordinator artifacts. Author queues contain block-neutral opaque
tokens, one relation premise, one construction brief, neutral deliverables, and an opaque
submission channel. The script never authors a case, runs the detector, creates a label, or opens a
held-out queue.

Before an author implements a case, the coordinator can compile the frozen assignment into one
claimless method-contract input shell per case:

```text
python scripts/build_prospective_method_contract_inputs.py \
  --protocol /study/coordinator/protocol.json \
  --relation-binding-map /study/coordinator/relation-binding-map.json \
  --authoring-briefs-root /study/coordinator/authoring-briefs \
  --block-id block:opaque-a \
  --scientist-id scientist:stable-id \
  --output-root /new/write-once/contract-inputs
```

The builder replays the protocol, mapping, and brief digests; requires the complete 10 × 7 block
matrix; emits the exact registered check/candidate profile plus the human-authorized premise; and
makes both inputs read-only. It refuses held-out preparation by default. It does not run
`method-contract`, author project material, execute case code, release packets, create labels, or
grant qualification authority.

## Verification

Focused tests cover:

- the complete 10 × 2 × 7 matrix (140 prospectively assigned cases);
- exact registry and candidate binding of the ten-envelope template;
- author-queue exclusion of coordinator identifiers and block roles;
- content-addressed binding between the coordinator and benchmark-blind templates;
- deterministic create-once method-contract inputs for all 70 cases in a selected block;
- digest replay, read-only task/profile inputs, and default refusal of held-out preparation;
- opaque case identities and corrected/renamed pair constraints;
- development/public-source exclusion from pilot and held-out blocks;
- author/reviewer/context isolation and cross-provider review panels;
- omission and duplicate-outcome rejection;
- pilot-before-threshold-before-held-out chronology;
- contaminated, unauthenticated, incomplete, and mislabeled-case retention;
- schema validity and self-digest replay; and
- all three CLI artifact stages.

## External work still required

No independent evidence was created in this experiment. Reaching ten real Findings still requires:

1. freeze the real detector manifest and implementation bytes;
2. recruit and authenticate independent authors and cross-provider reviewers;
3. prepare and digest the authoring briefs without exposing recognizers, labels, or prior outputs;
4. freeze the actual opaque no-replacement assignments;
5. author all prospective pilot workflows and retain every outcome;
6. complete authenticated answer-blind Stage-1 and independent Stage-2 adjudication;
7. freeze a maintainer-approved numeric threshold decision from the complete pilot;
8. open and evaluate the still-sealed held-out block without changing detector logic;
9. calculate the separately accepted envelope-specific qualification metrics; and
10. make ten separate maintainer promotion decisions under the forward promotion schema.

Any detector change after label access mints a new detector version and restarts qualification.
None of the template, test-generated records, or local protocol validation may be cited as
independent authorship, authenticated review, a qualified envelope, or a production Finding.
