# Experiment 0054: Selected-result verifier qualification

- **Status:** Pre-case target/oracle/protocol freeze complete; no qualification case assigned or
  evaluated
- **Date:** 2026-08-04
- **Governing boundary:** ADR-0022, ADR-0042, Experiment 0053
- **Production impact:** None; this experiment is evaluation-private
- **Finding impact:** None; passing this experiment cannot qualify a scientific detector or emit a
  Finding
- **Execution impact:** The target verifier does not execute project-authored code

## Question

Can the exact `python-static-marked-report-v1` selected-result verifier be shown, by a separately
implemented oracle and previously unseen cases, to reproduce the profile's closed selected-result
state and exact binding without false completion?

## Exact scope

Qualification binds one immutable tuple:

1. target verifier version, entry points, source digest, and dependency/runtime contract;
2. selected-result profile identifier, version, grammar, roles, encodings, and budgets;
3. validation-wrapper source digest;
4. independent oracle source digest and dependency closure; and
5. this experiment's assignments, comparison rules, and pass decision.

Passing permits that tuple to supply selected-result evidence to the prospective qualification
controller. It does not establish that a selected result is scientifically correct, qualify any
issue class, qualify any detector, authorize a production Finding, or generalize to another
language, grammar, runtime contract, or implementation digest.

## Why this is smaller than detector qualification

The target is a deterministic evidence checker with a closed grammar. It is not deciding a
scientific issue and therefore does not need the full four-reviewer scientific adjudication panel
used to label detector cases. Independence is instead established by separately authored cases,
an oracle that does not import or reuse the target parser/evaluator, sealed target outputs, and
exact byte-level comparison.

This is a finite profile-conformance claim, not an estimate of performance on arbitrary software.
The study will not convert its sample counts into a population-wide error-rate claim.

## Frozen study shape

There are two no-replacement blocks of 48 cases each: a pilot and a held-out block. Each block has
the following fixed cells:

| Oracle state | Cell | Cases |
|---|---|---:|
| `V` | unique exact static binding, including renamed/relocated and allowed writer variants | 12 |
| `A` | multiple supported results, writers, producers, or alternatives | 8 |
| `I` | applicable grammar with missing evidence or retained-byte mismatch | 8 |
| `U` | dynamic or opaque code and unsupported producer/language | 4 |
| `U` | file-role, executable, shebang, extra-file, or source-artifact boundary | 4 |
| `U` | encoding, newline, or text-runtime boundary | 4 |
| `U` | syntax, statement, value, line, tree, or other finite-budget boundary | 4 |
| `U` | replay, mutation, path, or filesystem-safety boundary | 4 |

Two provider families independently supply 24 cases per block. Each provider must contribute to
every oracle state, no construction family may contribute more than half of a block, and at least
four construction clusters must occur in every state. Mechanically derived siblings share a
cluster and do not manufacture independent sample size.

The pilot may reveal defects. Any target change after pilot execution creates a new verifier
identity and requires new pilot and held-out assignments. The held-out block stays sealed until the
unchanged tuple passes the pilot and the maintainer freezes the held-out-open decision.

## Closed oracle states

- `V` (`verified_unique`): exactly one supported selected-result binding exists and every expected
  report, result, producer, operand, alternative, byte digest, and line span is exact.
- `A` (`ambiguous`): more than one supported binding or selected-result interpretation remains.
- `I` (`insufficient`): the profile is otherwise applicable but a required exact artifact,
  dependency, selected result, or byte equality is absent.
- `U` (`unsupported`): the case is outside the frozen grammar, role, encoding, runtime,
  filesystem, or resource envelope.

Only `V` may correspond to target status `one_selected_result_rederived` and validation status
`verified_complete`.

## Oracle isolation

The oracle must be implemented in a separate evaluation-private module and dependency closure. It
must not import, invoke, copy, or accept output from
`prospective_selected_result_verifier`, `prospective_qualification_v2`, production parsers,
production detectors, or their semantic helpers. Allowlisted shared behavior is limited to
standard-library canonical JSON, SHA-256, byte reads, and lexical relative-path normalization.

Each case is created with a typed construction certificate. The independent oracle checks the
certificate against the complete retained byte tree and emits its state and, for `V`, the exact
expected binding. The target verifier never receives the certificate, oracle state, expected
reason, cell, or expected binding. The oracle never receives target output. A separate comparison
step runs only after both artifacts are frozen.

Static import inspection and runtime import trapping must demonstrate the firewall. The oracle
proof retains complete file inventory, exact spans and digests, implementation lock, chronology,
and a self-digest. An oracle disagreement or invalid certificate is retained; it is not replaced,
voted away, or relabeled after target output is visible.

## Chronology

1. Freeze the exact target, oracle, profile, matrices, prompts, assignments, metrics, and pass
   rule before any metric case exists.
2. Create opaque no-replacement pilot and held-out assignments without state, cell, reason, or
   expected binding.
3. Independently author cases and construction certificates. Keep the held-out block sealed.
4. Validate and freeze pilot oracle proofs without target output.
5. Run the frozen target in a separate context and freeze every output before comparison.
6. Compare all assigned pilot cases, retain every failure, and freeze the pilot decision.
7. If and only if the tuple passes unchanged, open the held-out block.
8. Repeat oracle freeze, target-output freeze, and comparison for every held-out assignment.
9. Make an explicit maintainer verifier-only qualification decision.

No assigned case may be replaced because of an invalid certificate, disagreement, crash, target
outcome, or inconvenient cell realization.

## Exact comparison and pass rule

A false completion occurs when an `A`, `I`, or `U` case produces
`one_selected_result_rederived` or when the validation wrapper produces `verified_complete`. A
false rejection or wrong binding occurs when a `V` case does not produce the oracle's exact
binding. A state mismatch includes a wrong `A`/`I`/`U` state or reason code. An exception,
timeout, nondeterministic record, stale replay, or case omission is a failure, never an exclusion.

The pilot and held-out blocks must each satisfy all of the following:

- 0 false completions among all 36 non-`V` cases;
- 0 false rejections or wrong bindings among all 12 `V` cases;
- 48 of 48 exact closed-state and reason-code matches;
- 0 uncaught exceptions, uncontrolled resource failures, or omitted assignments;
- 48 of 48 oracle certificates valid before target-output reveal;
- 48 of 48 identity, chronology, inventory, and digest records complete; and
- two fresh-location replays with byte-identical canonical target and comparison records.

These thresholds cannot be weakened after pilot results. A failing exact tuple remains failed.

## Required durable artifacts

- [x] Pre-case freeze manifest binding target, oracle, profile, protocol, matrices, prompts, and
  pass rules.
- [ ] Opaque pilot and held-out assignment manifests frozen before case construction.
- [x] Independent oracle implementation with import-firewall and mutation tests.
- [ ] Complete pilot case trees, construction certificates, oracle proofs, target outputs, and
  comparison records.
- [ ] Pilot decision freezing the unchanged tuple before held-out opening.
- [ ] Complete held-out case trees, construction certificates, oracle proofs, target outputs, and
  comparison records.
- [ ] Verifier-only qualification decision with exact limitations and replay evidence.
- [ ] Installed evaluation-wheel replay on a fresh location.
- [ ] Delivery-plan evidence update; no ten-envelope matrix cell changes at this gate.

## Current result and non-result

The committed pre-case directory is
`evaluation/qualification/selected-result-verifier-v1.0.0-precase/`. It binds target verifier
digest `sha256:d34ad9b7a85bf78840fb9109bd764a26e5a25a4e89484ce2788436120ead7eac`,
selected-result profile digest
`sha256:12478b6b21fb12be7388a7a570adadd8ffc68ea09ab2803074dfc77feb6699d0`,
and the separate certificate-oracle implementation. The builder is write-once and byte-replays the
complete freeze. Focused tests cover certificate, inventory, span, state/binding, mutation,
symlink, import-firewall, target-drift, no-overwrite, answer-blindness, and freeze-replay behavior.

No case, assignment, oracle proof, target output, metric, threshold result, or qualification
decision exists yet. Existing unit tests and adversarial code review remain development evidence
only. The target bytes are frozen for the study, but the verifier is not yet qualified.
