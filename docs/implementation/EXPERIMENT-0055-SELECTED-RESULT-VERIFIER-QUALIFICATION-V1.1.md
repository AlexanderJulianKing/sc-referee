# Experiment 0055: Selected-result verifier qualification v1.1

- **Status:** Stopped before case authoring; preserved as non-qualifying high-assurance development
  work and superseded on the delivery path by Experiment 0056
- **Date:** 2026-08-04
- **Supersedes:** Invalidated Experiment 0054
- **Production impact:** None; evaluation-private qualification only
- **Finding impact:** None; this experiment cannot qualify a scientific detector or emit a Finding

## Stop record

No metric-eligible case, provider review, label, target outcome, threshold, or promotion was created
under this experiment. A normative audit found that its separate 96-case meta-study, cryptographic
registrar, exhaustive distribution locking, hostile-local-operator threat model, and fresh-location
replays were not required by the accepted specification, ADRs, or schemas. Continuing them would
delay direct scientific-detector qualification without increasing the evidence required for a
Finding. Experiment 0056 therefore preserves the useful deterministic comparator and adversarial
tests while qualifying the ten detector envelopes directly under every accepted epistemic,
4+2-review, held-out, replay, safety, promotion, and public-claim requirement.

## Question

Does the exact frozen selected-result derivation and validation-wrapper tuple reproduce a finite,
target-independent semantic truth set with exact evidence binding and no false completion?

## Why a new study version is required

Experiment 0054 failed before target execution because the case author's certificate supplied the
semantic answer, byte spans were compared only after reduction to line locators, study assignments
and packets were not enforced by the public controller, chronology was declarative, the target was
imported during the oracle phase, and the validation wrapper was not exercised. A clean-room oracle
author also demonstrated that the frozen high-level profile was not detailed enough to derive the
target's exact reason and binding vocabulary independently.

Those defects change qualification meaning and cannot be repaired invisibly after case authoring.
Version 1.1 therefore requires a new freeze, new opaque assignments, and new cases. All v1.0 cases
remain retained but metric-ineligible.

## Truth architecture

The v1.1 truth source has three ordered layers:

1. a standard-library byte verifier checks the complete retained tree, construction-certificate
   self-digest, file inventory, exact half-open spans, and exact span digests without importing the
   target; and
2. exactly two target-blind semantic validators inspect the retained bytes and the complete frozen
   semantic review contract independently of the case author and each other, retaining their full
   evidence before certificate reveal; and
3. separate post-reveal reconciliation records compare those immutable blind reviews with the
   byte-verified certificate.

The two semantic validators must use distinct authenticated provider sessions and fresh execution
contexts, must be from providers different from the case author and one another, must not see the
construction certificate, author contract, target source, target tests, target output, or the
other review before the blind barrier, and must retain the full review evidence rather than only a
caller-supplied digest. Both validators must independently return the same `V`, `A`, `I`, or `U`
state, the same registered reason, and—for `V`—the same exact binding. After the complete blind
panel is sealed, each separate reconciliation must agree with the byte-verified construction
certificate. Disagreement is a retained failed assignment; it is never replaced or majority-voted.

The construction certificate alone has no semantic authority. The blind semantic reviews alone
cannot establish file identity. Only their exact conjunction can create an oracle proof, and that
proof still has no scientific Finding authority.

## Frozen semantic review contract

Before any v1.1 case is authored, freeze a target-independent JSON contract containing:

- the four closed states and their applicability order;
- the complete registered reason-code taxonomy partitioned by state;
- the exact file-inventory and half-open byte-span certificate schemas;
- the canonical whole-file convention for selected reports and operands;
- the canonical whole-line, line-ending-inclusive convention for selected-result and producer
  evidence;
- the exact positive-binding digest projection;
- deterministic reason precedence for cases satisfying multiple boundaries;
- the complete 48-case-per-block state/cell matrix and diversity constraints;
- author, validator, target-runner, and comparison identity/independence requirements; and
- the target-blind input allowlists for each phase.

The contract explains the complete normative grammar in target-independent language, including
its permitted syntax and precedence. It must not expose target source, tests, benchmark identities,
expected target outputs, or case-specific answers.

## Study shape and no-replacement rule

Retain the two 48-case blocks and state/cell counts from Experiment 0054: 12 `V`, 8 `A`, 8 `I`,
and 20 `U` per block, split evenly across the five registered `U` cells. Two provider families each
author 24 cases per block. Every state has at least four construction clusters, and no construction
family supplies more than half a block.

All 96 v1.1 case identifiers and target packets are newly generated and frozen before authoring.
The held-out block remains sealed until an exact passing pilot decision exists. Invalid,
disagreeing, contaminated, crashed, or inconvenient cases remain in the denominator and are not
replaced.

## Enforced execution phases

Every phase consumes and replays the exact runner freeze, assignment self-digest, predecessor
manifest, complete inventory, and implementation locks.

1. **Semantic freeze:** two pre-reveal blind reviews, a block barrier, certificate reveal, two
   separate reconciliations, and byte verification; target module absent at static and runtime
   import checks.
2. **Blind derivation:** a separately installed target worker receives only case-byte snapshots,
   opaque packets, and a target-release authorization created after the oracle barrier. It has no
   oracle-phase or provider-pack path and receives no certificate, state, reason, cell, binding,
   attestation, reconciliation, or author declaration.
3. **Validation wrapper:** only after blind derivation is frozen, reveal the pre-frozen author case
   contract and run the exact validation wrapper.
4. **Comparison:** bind assignment, packet, profile, implementation, oracle proof, derivation,
   validation, and exact locator-receipt span digests.

Target execution cannot begin from a caller-supplied timestamp alone. It requires the complete
self-digested semantic-phase manifest and inventory. Held-out execution additionally requires the
self-digested passing pilot decision. Paths must be lexical descendants of their phase roots and
must not traverse symlinks.

## Exact comparison

For `V`, the selected report and every operand must cover the complete retained file. The selected
result and producer must cover complete retained lines including their line endings. Oracle span
digests must equal the target locator-receipt span digests; line-number equality alone is
insufficient. The target packet's case, profile, and selected-report path must exactly equal the
frozen assignment.

The validation wrapper must produce:

- `verified_complete` with `exact_independent_binding_match` only for a `V` case whose pre-frozen
  author declaration equals the exact independently derived binding;
- `ambiguous_selected_result` with the registered `A` reason for `A`;
- `insufficient_evidence` with the registered `I` reason for `I`; and
- `unsupported_structure` with the registered `U` reason for `U`.

Any non-`V` `verified_complete`, wrong state, wrong reason, wrong binding, exception, omission,
stale replay, manifest drift, or uncontrolled resource failure fails the exact tuple.

## Pass rule

Pilot and held-out must each independently achieve all of the following:

- 48 of 48 valid byte certificates and unanimous two-validator semantic panels;
- 48 of 48 exact derivation state and reason matches;
- 12 of 12 exact `V` bindings, including byte-span receipt equality;
- 48 of 48 exact validation-wrapper outcomes;
- zero false `verified_complete` outcomes among the 36 non-`V` cases;
- zero exceptions, omissions, replacements, identity failures, or chronology failures; and
- two fresh-location replays with byte-identical canonical semantic, target, validation, and
  comparison records, excluding explicitly declared location/runtime identity fields.

Thresholds cannot be weakened after pilot. Any target, wrapper, byte verifier, semantic contract,
controller, runner, assignment, adapter, or comparison change creates a new tuple and reopens pilot.

## Checklist

- [ ] Freeze the complete semantic review contract and registered taxonomy.
- [ ] Freeze corrected byte verifier, attestation controller, exact binding comparison, and import
  firewall.
- [ ] Freeze runner, target-only projection, manifest chains, held-out gate, and path safety.
- [ ] Add and freeze validation-wrapper phase and comparison.
- [ ] Generate and seal 96 new opaque no-replacement assignments.
- [ ] Author and retain 48 pilot cases across two provider families.
- [ ] Complete two cross-provider semantic attestations for all 48 pilot cases.
- [ ] Run and replay the exact pilot tuple; freeze pass/fail decision.
- [ ] Open held-out only after an exact passing pilot decision.
- [ ] Repeat authoring, attestations, execution, and replay for all 48 held-out cases.
- [ ] Freeze verifier-only qualification decision and installed-wheel fresh-location replay.
- [ ] Update the ten-Findings delivery plan without changing any envelope matrix cell at this gate.

## Current non-result

The complete semantic contract and 96 answer-blind assignments have been regenerated after
closing a hash-order-dependent target traversal defect. They are not yet part of an accepted
runner freeze. No v1.1 case, blind review, reconciliation, oracle proof, target output, wrapper
output, comparison, metric, or qualification decision exists. Corrective code and tests are
development evidence only. The selected-result verifier remains unqualified, and the ten-Findings
production score remains 0/10.
