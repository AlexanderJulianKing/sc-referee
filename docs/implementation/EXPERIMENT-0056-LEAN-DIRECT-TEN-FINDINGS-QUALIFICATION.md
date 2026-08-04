# Experiment 0056: Lean direct ten-Findings qualification

- **Status:** Active frozen first-envelope lane; no metric-eligible case authored
- **Date:** 2026-08-04
- **Supersedes:** Experiment 0055 as the delivery-path qualification design
- **Production impact:** None until an exact detector envelope completes pilot, held-out,
  promotion, and installed-product acceptance
- **Finding impact:** None at experiment creation; the current honest score remains 0/10

## Decision

Qualify each of the ten scientific detector envelopes directly. Do not first run a separate
96-case study to qualify the selected-result comparator. The comparator is auditor-owned,
deterministic infrastructure: freeze its implementation/build identity, test its finite grammar
and adversarial controls, and use it only to compare independently frozen scientific labels with
detector outputs. It has no scientific-label or Finding authority of its own.

This change removes requirements invented by Experiment 0055 that are absent from the accepted
specification, ADRs, and schemas:

- a separate 96-case verifier meta-study;
- a cryptographic registrar and signed event chain;
- exhaustive installed-distribution `RECORD` locking;
- a hostile-local-operator/Python-shadow-package threat model; and
- two fresh-filesystem-location replays per provider bundle.

The Experiment 0055 code and tests remain preserved as non-qualifying development work. Stopping
that experiment does not promote a detector, authorize a Finding, or weaken an accepted rule.

## Pre-case amendment: v3 author, panel, and evidence binding

Before any case was assigned, a normative audit found three defects in the evaluation-private v2
label contract. This amendment replaces that contract with v3; no v2 author declaration, case,
review, label, threshold, or outcome is grandfathered.

First, the case author receives and freezes only an author selected-result declaration. That
artifact contains the opaque case identity, result-selection state, exact result evidence needed
for that state, authorship identity, and chronology. It cannot contain the relation envelope,
check, candidate, binding-registry identity, canonical issue class, answer, grade, detector
identity, or detector output. A coordinator subsequently binds the already-frozen author artifact
to the scientific envelope in a separate authority-free case contract. This implements the
accepted requirement that case/workflow generation omit target labels and detector-side evidence;
the coordinator binding does not retroactively expose those fields to the author.

Second, the author declaration can state `one_selected_result`, `multiple_candidate_results`, or
`unsupported_producer_surface`. The latter two states require explicit candidate or unsupported
producer locators and require the single selected-result binding and digest to be null. Independent
validation maps them to ambiguous or unsupported outcomes, so an author is never required to
fabricate one selected result merely to satisfy the data shape.

Third, the v3 Stage-2 label is only an evaluation projection of the existing complete 4+2 panel
freeze. It requires a self-digest-valid `evaluation_scientific_label_freeze` for the same case,
created before detector observation, with a nonempty Stage-1 freeze digest and exactly two Stage-2
entries from two provider families. Each compact v3 Stage-2 summary binds the corresponding full
AgentReview record ID, digest, provider, and execution context, and the v3 output retains the panel
freeze digest. The freezer accepts the complete schema-valid AgentReview bytes and derives the
summary verdict, issue class, selected-result status, counterevidence status, reviewer identity,
provider, context, completion time, and semantic digest from those bytes; none of those semantic
fields is caller-authored summary input. It cannot substitute two loose summaries for the accepted
panel.

The accepted authorities require distinct reviewer identities and execution contexts, two Stage-2
provider families, and exact retained review identities. They do not require every case author or
the deterministic selected-result validator to use a third provider family. V3 therefore permits
provider-family reuse across those roles while still rejecting identity or execution-context
reuse. The selected-result validator remains deterministic, evaluation-only, and without
scientific-label, qualification, or Finding authority.

## Threat model

The delivery study must detect accidental mutation, stale inputs, label leakage, author/reviewer
overlap, provider/context reuse, post-label detector changes, unsupported evidence, reversed
unknowns, incomplete counterevidence, and non-replayable comparisons. It does so with immutable
snapshots, canonical hashes, frozen build and implementation digests, exact provider/model/surface/
version/context identities, retained prompts/tool/environment/transcript digests, blinded labels,
and deterministic replay.

The study does not claim to withstand a malicious owner of the qualification workstation who can
replace the operating system, Python importer, credentials, or retained evidence and then fabricate
a new study. Hashes establish exact identity and replay; they do not establish scientific truth.
Scientific truth comes from the required independent blinded review panel and deterministic
admission checks.

If project-authored code is executed, the accepted rootless-OCI SandboxCapability and Execution
records remain mandatory. Static closed-scope and documented external-execution proof families do
not acquire a bespoke OCI-package-attestation requirement.

## Requirements retained without reduction

Every production Finding still requires:

1. direct entailment from exact retained evidence;
2. no reversal of an unknown or unresolved premise;
3. exact detector applicability;
4. completed finite counterevidence checks;
5. bounded deterministic wording and model-free replay;
6. validated or publication-grade detector maturity within one exact qualified envelope;
7. four blind Stage-1 reviews across two providers and two fresh cross-provider Stage-2 reviews;
8. labels frozen before detector comparison, with material dissent excluded;
9. pilot-informed thresholds accepted before the held-out block opens;
10. held-out safety gates, a public qualification report, and an exact maintainer promotion;
11. a narrow generated capability-matrix claim with limitations and abstentions; and
12. CLI and installed-skill acceptance with corrected and adverse controls Finding-clean.

Agent-only review remains explicitly disclosed as agent-only. The accepted 4+2 panel is not reduced
to one adjudicator.

## Direct study shape

The existing 140-case design remains the complete objective: ten envelopes, seven cells, and two
blocks. Each envelope has these frozen cells in both pilot and held-out:

1. error-bearing;
2. corrected twin;
3. valid alternative;
4. hard negative;
5. ambiguous;
6. unsupported; and
7. independently renamed implementation.

Cases are frozen and opened envelope by envelope so the program can obtain a real 1/10 result
before spending resources on all ten. No envelope's detector may change after its pilot begins;
changes create a new tuple and reopen that envelope. The first lane is
`check:complete-domain-exposure-denominator`, selected because it already has the broadest generic
development matrix and two qualification-ineligible, independently renamed positive smokes.

## First-envelope sequence

- [x] Close its remaining file/function/identifier, wrapper/alias, reordered representation, and
  equivalent-encoding development controls.
- [x] Freeze its exact detector manifest, check/candidate/adapter binding, comparator/build digest,
  case-evidence contract, issue-class entry, and fourteen opaque assignments.
- [x] Seal the seven held-out assignments before any pilot label or detector outcome exists.
- [ ] Author and retain all seven pilot cases without replacement.
- [ ] Complete the required 4+2 blinded review panel and freeze resolved labels.
- [ ] Run and replay the frozen detector on all seven pilot opportunities.
- [ ] Use pilot results to accept a numeric threshold ADR and forward schema capable of representing
  a non-deferred promotion policy.
- [ ] Open, author, review, run, and replay the seven held-out cases without changing the tuple.
- [ ] Apply the accepted safety gates and publish the envelope qualification report.
- [ ] Record an exact maintainer promotion or failure decision.
- [ ] If promoted, prove the intended Finding and all control outcomes through the CLI, Codex skill,
  and Claude Code skill on fresh installations.

The current exact pre-case evidence is the repaired v3 tuple digest
`sha256:2526c7d710705bc8705ffc8dbc062f233c5555f8e9445d1ffea23c50a68a14d6`,
participant-enrollment digest
`sha256:c29bdc3c277b840c2bf9b4369f69181190663530467926ccfdfb24407eff0016`,
authoring-brief manifest digest
`sha256:7133cb96256ab17a7eff58efa4d2b9a97dc9c2addac575a3ec03b830c869ec8e`,
and direct-lane freeze digest
`sha256:c58ee57c01d5f7c46855eb9f554d0a476f664e44edbdd7e15679bd53d72fa12b`.
An earlier zero-exposure lane was superseded before authentication or author access because its
author prompt mentioned a README that conflicts with the comparator's exact case-tree grammar; its
bytes and supersession record remain retained and cannot contribute evidence.
The enrollment is declared-not-authenticated, all six reviewer configurations remain calibration-
gated, and the sealed author briefs have not been exposed. These freezes create no scientific
label, metric, qualification, promotion, or Finding authority.

## Stop conditions

Do not promote when the selected result is unresolved, a source reference is missing, the review
panel is incomplete, material dissent exists, finite counterevidence is incomplete, a required
threshold or schema is deferred, a held-out safety gate fails, or installed-product behavior does
not replay. Retain every failure in its denominator; do not replace inconvenient cases.

## Completion meaning

This experiment is successful only when the delivery matrix reaches 10/10 `finding_qualified` and
10/10 installed-product acceptance. A comparator, protocol, case assignment, review, label,
evaluation candidate, or passing development test is not a completed Finding.
