# Experiment 0056: Lean direct ten-Findings qualification

- **Status:** Active frozen first-envelope lane; first three-case authoring intake failed with zero
  metric-eligible cases
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

A maintainer-directed pre-exposure amendment reduces each threshold pilot to the smallest causal
triad that distinguishes the scientific relation from its operands:

1. error-bearing: complete-domain target with a retained-subset denominator;
2. corrected twin: complete-domain target with a complete-domain denominator; and
3. valid alternative: explicitly conditional target with the matching retained-subset denominator.

For this first envelope, the already sealed held-out block remains the accepted seven-role set:
error-bearing, corrected twin, valid alternative, hard negative, ambiguous, unsupported, and
independently renamed implementation. The first lane's four surplus pilot assignments were frozen
before this amendment; because no author brief has been exposed, they remain immutable, unopened,
and metric-ineligible rather than being deleted, reclassified, or counted as attempts. This
amendment does not reduce the 4+2 reviewer panel or the accepted ADR-0061 held-out promotion gate.
It makes no assignment-count or execution decision for the other nine envelopes.

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
- [x] Freeze the pre-exposure pilot-scope amendment and retain the four excluded assignments as
  unopened and metric-ineligible.
- [ ] Author and retain the three-case pilot causal triad without replacement.
- [ ] Complete the required 4+2 blinded review panel and freeze resolved labels.
- [ ] Run and replay the frozen detector on all three pilot opportunities.
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
The enrollment is declared-not-authenticated and the sealed author briefs have not been exposed.
Three Codex reviewer configurations have exact passing calibration evidence. Three frozen Claude
Code calibration attempts in protocol v3 terminated before inference because local OAuth had
expired; their immutable failures are retained. Before any case exposure, versioned adjudication-
protocol amendment digest
`sha256:e3f8f012e02e29112e83e83cdfb4b4e3b2ad82eaed4d5058cc3a9bd4f221395e`
replaces only those inactive configurations with three exact Claude Desktop App 1.25927.0, Opus 5,
Extra, incognito Home Chat contexts. Replacement enrollment digest
`sha256:95ef5badd874db346279de725a35679da80d00bf8d40c323041b414ce750a5bc`
and calibration protocol digest
`sha256:9427d044c529ffbf0c3ef07ae034550e3cfe841d105ddc9d61dfb2d4eeda2af4`
were frozen before prompt submission. All three amended configurations then passed the unchanged
six-vignette suite in one retained app attempt each. App ledger digest
`sha256:bf6f76588f197817f8fd3df184efacb36cca8ded4eaf7f8ba6d22fb3d60bbe29`
and active aggregate digest
`sha256:3c64169c830ff1e963f81fe0e774e367021e3ad4f77892641002e4ff7f13e030`
record 6/6 active passes while preserving all 18 historical attempts and 12 failures. Capture-only
amendment digest
`sha256:bc50aaf34a1cb6508329138156f49efdc4bed2ffc4ba1d4fbe4f12941e573189`
records that fresh Claude incognito chats expose one shared nonpersistent route rather than unique
visible conversation URLs; it changes no scientific rubric or verdict. These calibration records
create no scientific label, metric, qualification, promotion, or Finding authority.

Before any author brief exposure, first-envelope pilot-scope amendment digest
`sha256:35e1d193113b807257baab48bf2bd2d9b6482ed620bae09a1f36aa5541b91861`
retains the four surplus pilot assignments as unopened and metric-ineligible and authorizes only
the three-case causal triad. Authoring-protocol digest
`sha256:51808c104df89a701f1b6dd612894207760c02da7c969dcb68df86ae589593af`
binds those three briefs to two one-shot author contexts. The error/corrected pair shares its
frozen Claude author identity; the valid alternative uses one frozen Codex author identity. No
workflow, declaration, scientific label, detector outcome, or Finding existed at that freeze.

The first authoring execution is now retained as a failed intake, not counted as a scientific
pilot. Claude's first response failed JSON parsing before admission. Intake-recovery amendment
digest `sha256:3b4ab839a056256f6b93aba1e1f452a0ecb98cb17b93d915acf5b5318d00a06c`
authorized one fresh transport-only call while retaining that failure; the recovery response and
the Codex response then produced three author declarations. Authoring-ledger digest
`sha256:b1a0bcdaf9aa9a7fc2970bd94c510ac9b8ac5475e0e90d5ce7d4f39a540a58f6`
retains all three attempts and one exact metadata-only redundant-locator canonicalization.

The frozen model-free selected-result verifier subsequently rejected all three case trees before
scientific review: two Claude producers do not parse as Python, and the Codex producer uses a
writer signature outside the frozen finite grammar. Selected-result intake-ledger digest
`sha256:ee9ee169fe6b6970ea2a85565750f6e99a34273b4d0f3a0f9ab02bb6d34cffeb`
therefore records three `unsupported_structure` outcomes, zero verified cases, zero labels, zero
detector outcomes, and zero metric-eligible opportunities. These failures cannot be treated as
negative controls or repaired into cases. The next authoring iteration must be frozen before new
calls, must constrain only the already-frozen static producer grammar, and must retain this entire
failed iteration. The authoring and downstream checkboxes remain unchecked.

Second-iteration restart-amendment digest
`sha256:41a274b59e79712216d3b2602758b757ca0c86767837e0e385d7344fd53039bc`
creates three new opaque case identities and two fresh enrolled author contexts while retaining the
failed iteration and changing no scientific brief. Authoring-protocol digest
`sha256:a925a0f05b7ab16f61da02c65b2f47506b0dfad14b0f0f3f630aaded29ef49cb`
changes only transport to physical-line arrays and states the already-frozen straight-line static
producer grammar. A first local Codex launch was blocked before inference by the managed sandbox's
read-only Codex state database; its empty-response failure is retained. After explicit
authorization, the exact frozen Codex and Claude prompts were each submitted once. Both responses
parse and pass their frozen JSON schemas, but none of their three payloads was admitted: the two
Claude payloads each decode an LF inside one physical-line producer entry, and the Codex payload
places `produce.py` outside the frozen `workflow/` producer role. Failure-ledger digest
`sha256:20dab1bcdd87463601a7f84425a032fb026f70ea4737dc3cb2e8c7e3e7449143`
binds both exact captures and records zero verified or metric-eligible cases, zero labels, and zero
detector outcomes. These responses are retained without repair. Any next authoring iteration must
be frozen before inference, use new opaque identities, keep the scientific briefs unchanged, and
constrain only generic transport/role-path details needed by the already-frozen verifier.

Third-iteration restart-amendment digest
`sha256:fc4683fe691926f82d8cf9979f0a9089ce7525d34cfcd03db34600ca3161614e`
and authoring-protocol digest
`sha256:0f70e92a2a87b4c3225734fe871ac31ec2535ac02390efb1743e78c3e78e385a`
are frozen before any v3 inference. They create fresh opaque cases, call identities, and author
contexts while retaining v1 and v2 unchanged. Scientific briefs and detector/verifier bytes are
identical in meaning. The only new constraints are exact `inputs/`, `workflow/`, and `results/`
paths, physical ASCII lines without terminators, an escape-free producer that obtains LF from its
input through the existing supported indexing grammar, and a declaration span bound to the exact
final report writer. A canonical preflight reaches `verified_complete` under the unchanged static
verifier.

Both frozen v3 prompts were then submitted once and their exact responses retained. Every response
passed the frozen transport, exact role-path, declaration, and final-writer checks. Temporary
model-free intake rederived both Claude selected-result bindings exactly. The Codex response used
negative list indices on producer lines 6--8; Python represents those indices as unary expressions,
which the frozen static evaluator cannot evaluate. Because the v3 prompt permitted indexing without
excluding this form, this is an author-protocol/verifier grammar mismatch rather than a scientific
failure or author violation. The atomic cohort recorder admitted nothing. Failure-ledger digest
`sha256:622610d8632696edb70a9b112f20877601fcd45d44b73b753a77e1b75863c136`
binds both exact captures and records two verified bindings, one unsupported case, zero admissions,
zero metric-eligible cases, zero scientific labels, and zero detector outcomes. V3 is retained
unchanged and supplies no pilot evidence. A fourth iteration must be frozen before inference, use
fresh opaque identities and contexts, preserve the scientific briefs and detector/verifier, and
remove the ambiguity by allowing only the verifier's small render-only expression grammar after
the exact five-line input-binding prefix.

Fourth-iteration restart-amendment digest
`sha256:fd92ebaad0655d55efa29600f12a9db583486bef7c99f306b66e7596bb44272e`
and authoring-protocol digest
`sha256:2a853080b2e2faace3f6bfdfe440843e1023c199f02b3cee27d32ee70eaf307f`
are frozen before v4 inference. They bind render-only grammar profile
`authoring-render-only-v1` at source commit
`938d85804035a4654ee8397b01c9e210bbbda2d7`, create fresh opaque cases, call
identities, and contexts, and retain all earlier failures. Scientific briefs and the detector and
selected-result verifier are unchanged. After the exact five-line input-binding prefix, the
producer may use only ASCII scalar literals, earlier render names, addition, and plain-name
f-strings; calls, attributes, subscripts, slices, unary operators, conversions, and format
specifications are forbidden. The controller must run that syntax-generic validator before the
unchanged static selected-result verifier and must admit the three-case cohort atomically. No v4
prompt had been externally submitted at that freeze.

Both v4 prompts were subsequently submitted once in their exact frozen contexts. Authoring-ledger
digest `sha256:6487d1b7cccfb1fdb90fc080b93ea84233b3f81543d17e7ac3a99f30f3270ebc`
binds exact Claude capture
`sha256:cb5081820c7700e5bb67af1c5cf280a29f6f775dd24c1629c7183b49a414f50f`
and exact Codex capture
`sha256:411c474f2cd0ff2409bc94a73a816ce2e49e613f919457288f31e0702ea51492`.
All three submitted case trees pass the frozen render grammar and the unchanged model-free static
selected-result verifier. Their author declarations, exact role files, coordinator contracts,
independent derivations, and validations are frozen. Every case rederives one selected result, one
final report writer, and one complete input operand with no alternative producer; project-authored
code was not executed. The complete cohort is admitted with three metric-eligible pilot
opportunities and still has zero scientific labels and zero detector outcomes. This completes the
authoring, declaration-freeze, and independent selected-result rederivation prerequisites only; it
does not supply a scientific verdict, detector result, qualification decision, or Finding.

## Stop conditions

Do not promote when the selected result is unresolved, a source reference is missing, the review
panel is incomplete, material dissent exists, finite counterevidence is incomplete, a required
threshold or schema is deferred, a held-out safety gate fails, or installed-product behavior does
not replay. Retain every failure in its denominator; do not replace inconvenient cases.

## Completion meaning

This experiment is successful only when the delivery matrix reaches 10/10 `finding_qualified` and
10/10 installed-product acceptance. A comparator, protocol, case assignment, review, label,
evaluation candidate, or passing development test is not a completed Finding.
