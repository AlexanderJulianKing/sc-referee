# ADR-0020: Modular scientific-check profiles and analysis-scoped question triggers

- **Status:** Accepted, revision 2
- **Date:** 2026-07-29
- **Revised:** 2026-07-29 after owner generality review
- **Accepted:** 2026-07-29 by repository owner
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None proposed
- **Related decisions:** Accepted ADR-0017, ADR-0018, and ADR-0019
- **Evidence basis:** Experiments 0019 and 0020

## Context

Experiment 0019 proves that `posthoc_method_ledger_v1` can deterministically compare a closed
scientist requirement with exact reported or static source evidence. The fixed QTL and pulse-
admixture cases yield review-scoped conflicts, MVMR yields a covered negative, CRISPRi/CasRx stays
unknown, and a report cannot override contradictory static source evidence.

Experiment 0020 then tested the ordinary product boundary. An independent fresh-context agent used
the `scientific-audit` skill on only the raw QTL repository. The skill, audit, integrity check, and
model-free replay all worked, but the controller extracted no Claim, ScientificContract,
SemanticAssertion, or MaterialQuestion. The agent therefore had nothing canonical to ask the
scientist and correctly refused to invent a method requirement.

Adding one hard-coded QTL recognizer would close that single test while overfitting the product.
The intended product must instead support a growing collection of narrowly evidenced scientific
checks. A check about founder-state orientation should apply to every supported implementation of
that method, regardless of assay name, repository layout, or GeneBench case identity. A different
method error should be addable or removable without editing the audit controller, interaction
lifecycle, record schemas, or unrelated checks.

Generality does not mean that a model may search any repository for arbitrary scientific mistakes.
It means that one conservative framework can accept any repository, apply every installed check
whose exact applicability is demonstrated, ask bounded scientist questions when required, and
state clearly which checks were unavailable. Scientific coverage grows by adding independently
testable method profiles, not by broadening model discretion.

Accepted schema v0.14.0 already permits analysis-scoped ScientificContracts, MaterialQuestions
with no affected Claim, Answers scoped to typed records, ineligible SemanticAssertions, and
extension-bound profile metadata. The concrete test has not demonstrated a need for a new public
record type. If implementation cannot preserve the meanings below without overloading one of
those records, it must stop and propose a forward-only schema ADR.

## Recommended decision

### 1. Define one modular scientific-check interface

Create an explicitly injected, deterministically ordered `scientific_check_registry_v1`. The
registry contains auditor-controlled scientific-check modules. It MUST NOT discover or execute
modules from the repository being audited.

Every module participates in the same controller-facing lifecycle:

1. **Applicability:** determine from exact typed records and immutable source evidence whether the
   check applies, does not apply, is ambiguous, or is unsupported.
2. **Observation:** extract one closed reported-text or static-source operand with exact provenance,
   or abstain.
3. **Counterevidence:** complete the module's finite sibling, ambiguity, contradiction, and
   suppressor checks and preserve their receipts.
4. **Question:** when scientific intent is required, construct only the manifest-authorized finite
   MaterialQuestion and candidate operands.
5. **Comparison:** invoke an allowed deterministic ledger relation over separately authorized
   requirement and observation operands.
6. **Outcome ceiling:** declare the strongest public output that this module and maturity state may
   produce.

Adapters perform applicability, observation, and finite source-level counterevidence inspection.
The method-level check is a pure reducer over their normalized outputs and owns only the closed
question and comparison policy. Section 2 defines that boundary normatively.

The controller owns scheduling, records, interaction, semantic lock, replay, report policy, and
Finding admission. Adapters receive a capability-limited read-only inspection context containing
only controller-provided immutable bytes, parsed syntax, and typed base records. They receive no
project import handle, subprocess or execution handle, model client, network client, writable
repository handle, canonical store, or sibling-module output. A module cannot write canonical
files, call a model, execute project code, silently add a premise, or emit a Finding directly.

For v1, every module reads the same frozen base-inspection view: snapshot identities, FileRecords,
Artifacts, ParserResults, parser-owned Operations, resolved publication-surface state, and named
controller-owned shared derivations produced before module evaluation. A module MUST NOT consume
SemanticAssertions, questions, ledger projections, or other records emitted by a sibling module in
the same run. Inter-module dependencies require a later accepted decision with a digest-bound
acyclic dependency graph. This rule prevents adding or removing one check from changing another
check's applicability through hidden derived state.

Adding a module MUST require only:

- its implementation behind the common interface;
- one canonical manifest and explicit registry entry;
- conformance, positive, covered-good, ambiguity, unrelated hard-negative, and mutation fixtures;
  and
- documentation of its evidence and authority ceiling.

It MUST NOT require a module-specific branch in the controller, interaction protocol, reporter,
semantic-lock builder, or schemas. Removing or disabling a module means removing it from the
explicit registry construction. Unaffected module-local observation, question, comparison, and
assessment projections remain byte-stable. The audit-level registry inventory, coverage,
semantic-lock digest, report, and storage bookkeeping necessarily change to name the now-
unavailable check rather than silently implying it ran.

### 2. Separate abstract scientific checks from language and tool adapters

Each module has one method-level `check_id` and one or more exact `adapter_id` implementations.

The check defines the scientific obligation, contract dimension, comparison form, candidate
requirements, and authority limits. An adapter recognizes that obligation in one bounded source or
report representation. For example, a founder-orientation-before-emission check may initially have
one Python AST adapter; a later R adapter may support the same check without changing its meaning,
question, comparison, or outcome policy.

Applicability MUST be based on exact method roles and data flow supported by the adapter. It MUST
NOT depend on:

- a GeneBench case ID, answer key, expected numeric result, repository name, or fixture path;
- the presence of words such as “QTL,” “HMM,” or a package name by themselves;
- a model's similarity score or inferred scientific intent; or
- function names alone when their argument roles and required flow are unresolved.

An adapter may recognize multiple equivalent supported spellings or structures only when each is
enumerated and independently tested. Dynamic dispatch, ambiguous role assignment, multiple
competing targets, or an unrecognized implementation remains unsupported.

This separation is the core generality guarantee: a scientific rule can apply across assays and
tools that implement the same supported method, while language-specific recognition can grow
without duplicating the scientific rule.

Every adapter emits exactly one canonical `normalized_method_observation_v1` value or a closed
abstention. This is an internal semantic-lock input, not a new public record. It contains:

- check, adapter, parser, implementation, and manifest identities and digests;
- applicability and completeness states;
- one exact method-target typed reference plus closed semantic-role bindings;
- one canonical observed operand and its evidence plane (`reported_text` or `static_source`);
- exact source spans, content identities, and parser-result references;
- an exact analysis-scope join path through existing typed records;
- finite ambiguity, sibling, suppressor, and counterevidence receipts; and
- explicit non-inferences and the adapter's output ceiling.

The adapter cannot choose a question, intended requirement, comparison outcome, assessment type,
or wording. The method-level check validates the observation against its manifest and acts as a
pure reducer. Registry order has no semantic effect. Equivalent observations for the same target,
operand, authority plane, and scope path deduplicate canonically. Differing operands for the same
target, multiple competing targets, incompatible scope paths, or cross-adapter disagreement remain
ambiguous or unsupported; the reducer does not choose a preferred adapter.

At least one initial method check must be exercised through two materially different adapters.
For the first slice, the founder-orientation check SHOULD use both an exact selected-report method
adapter and a Python static-source adapter. Agreement may strengthen a bounded scope join, while
disagreement remains explicit. A later R adapter can demonstrate cross-language portability
without changing the check reducer.

### 3. Keep questions, compatibility checks, and detectors as distinct authority tiers

“Alert” is a user-interface idea, not one evidentiary record type. The framework must preserve the
difference among:

- a MaterialQuestion asking which method governs;
- a Disclosure reporting a bounded compatibility result or coverage limitation;
- a ConditionalConcern describing a verified conditional consequence without asserting the
  premise; and
- a Finding demonstrating an admitted issue.

The first registry supports two module authority tiers:

1. **Experimental question-only:** may create a pre-lock MaterialQuestion and a post-answer,
   Finding-ineligible compatibility Disclosure. It cannot emit a DetectorResult or Finding.
2. **Qualified detector:** may request detector scheduling only when a separate accepted detector
   manifest, qualification record, applicability proof, and ordinary Finding-admission premises
   authorize it. The module still cannot bypass the controller.

A question-only module is not a detector merely because an incompatible answer can be compared.
Conversely, adding or removing a qualified detector should reuse the same registry and evidence
interfaces without weakening detector qualification.

Changing a module manifest's maturity field cannot promote it. The registry admits qualified-
detector behavior only when a separately accepted, integrity-verified qualification artifact and
the existing detector manifest authorize the exact check and adapter versions. Missing, stale, or
inconsistent qualification caps the module at its lower authority tier.

Scientific authority stays separate from method recognition. A module may enumerate possible
methods, but it cannot decide which method is correct for the study unless an independently
applicable authoritative rule already establishes that obligation. Otherwise the present
scientist, a governing protocol, or another accepted authority must supply it. Model confidence,
repository prose, and source structure cannot establish that premise by themselves.

### 4. Require closed, versioned manifests for every module and adapter

Each module manifest MUST bind:

- check ID, semantic version, canonical digest, implementation digest, and maturity tier;
- one existing ScientificContract dimension and one allowed
  `posthoc_method_ledger_v1` comparison form;
- finite canonical requirement operands and plain-language labels;
- the provenance and authority basis for including each candidate operand, excluding an answer key
  as the sole production basis;
- all adapter IDs, versions, implementation digests, supported parser profiles, and source
  languages;
- the exact `normalized_method_observation_v1` contract and permitted semantic-role vocabulary;
- exact applicability, observation, ambiguity, counterevidence, and suppressor profiles;
- required record types, analysis-scope rule, and evidence identity strength;
- output ceiling, permitted wording, prohibited inferences, and Finding eligibility; and
- known gaps plus the fixtures that establish each supported and unsupported boundary.

Registry construction fails closed on duplicate IDs, incompatible versions, missing manifests,
digest mismatch, unknown comparison forms, or a module whose declared output exceeds its maturity.
Module evaluation order is canonical and must not change results. A module sees no sibling output.
One module failure is localized; it does not terminate or alter unrelated inspection.

The registry and semantic lock record exactly which checks and adapters were enabled, applicable,
unsupported, and completed. Reports distinguish “not installed,” “not applicable,” “unsupported,”
and “checked.” Removing a module can never make an unchecked method appear covered.

### 5. Scope claimless post-hoc questions to one selected analysis surface

When no Claim exists, the selected PublicationSurface is the typed proxy for the exact analysis
being reviewed. A module MAY create one ScientificContract with:

- `scope.level = "analysis"`;
- exactly one `scope.subject_refs` entry naming that selected PublicationSurface; and
- exact task, protocol, report, and source spans in `source_refs` when available.

The PublicationSurface proxy does not assert that one report contains only one analysis, that the
report is scientifically authoritative, or that source code produced it. A module is applicable
only when its finite scope checks identify one selected surface, one unambiguous method target, and
an explicit replayable scope-join path through existing typed records. A valid static-source path
may, for example, connect the target's FileRecord or Operation through a supported static writer
Operation and its `output_refs` to the exact selected report Artifact. Co-presence in one
repository, matching vocabulary, a shared filename, or an extension carrying both IDs is not a
scope join. Multi-analysis, multi-surface, missing-lineage, or otherwise ambiguous repositories
fail closed.

The resulting MaterialQuestion has `affected_claim_ids: []`. Its check, adapter, contract, observed
operand, comparison form, candidates, scope-join path, and evidence bindings are controller-
generated and digest-bound. A scientist may select one candidate, provide an exactly normalized
supported value after explicit confirmation, answer `unknown`, or decline. The Answer authority
scope MUST name the same selected PublicationSurface and exact semantic dimension.

If a later Claim is extracted, it is not silently added to this analysis contract. Any Claim-level
binding requires a separate deterministic derivation that preserves the original analysis scope
and source identities.

### 6. Represent static source as static source, not execution or report text

For one exact supported static match, the controller records an ineligible SemanticAssertion with:

- predicate `statically_observed_<dimension>`;
- semantic role `observed`;
- assertion class `deterministic_derivation`;
- authority scope `none`;
- subject equal to the actual observed FileRecord or Operation method target;
- exact immutable source spans plus check and adapter digests; and
- an explicit limitation that static inspection does not establish execution, runtime values,
  historical intent, numerical causality, or scientific correctness.

It MUST NOT reuse `reported_<dimension>`, `reported_wording`, or `executed_computation`. The ledger
manifest distinguishes verified report-text operands from verified static-source operands and uses
authority-specific outcome wording.

The static assertion is Finding-ineligible. It may establish only the exact operand consumed by
the question and compatibility projection. Its relationship to the analysis-scoped contract is
established only by the normalized observation's replayed typed scope-join path. The selected
PublicationSurface is never made the subject of a source-code property. An ordinary Operation
record may be referenced as support, but a generic opaque Operation cannot be upgraded into method
semantics by model interpretation.

If v0.14.0 Operation, Artifact, FileRecord, PublicationSurface, and source-reference relations
cannot represent the required scope path for a marker repository, implementation stops and records
the existing typed-graph-edge schema gap. An `x-` extension may carry redundant IDs and digests for
navigation, but it cannot be the material source-to-analysis join. A forward-only schema ADR is
required before that marker can enter the ordinary interaction path.

### 7. Reuse one analysis-scoped interaction and comparison lifecycle

The existing `questions`, `work-queue`, `work-packet`, proposal, Answer, resume, lock, status, and
replay commands remain authoritative. Extend them once to accept analysis-scoped scientific-intent
questions whose subject is the selected PublicationSurface and whose affected Claim list is empty.
No module receives a private chat protocol.

After a scientist Answer, the controller may derive `verified_intended_<dimension>` only when it
verifies the Answer digest, human actor, response source, exact analysis subject, exact dimension,
closed comparison form, canonical operand, source snapshot, module and adapter manifests, and
write-once chronology. This derivation establishes only the requirement governing the current
review.

`posthoc_method_ledger_v1` then compares that requirement with the exact observed operand. Its
analysis-scoped outcomes remain:

- `covered_negative` for an exact compatible relation;
- `exact_conflict_candidate` for an exact incompatible relation;
- `unresolved_obligation` for an unknown or absent governing answer;
- `unsupported_path` for unavailable or ambiguous source semantics; or
- `not_applicable`.

An analysis-scoped result is rendered as a Disclosure with exact checked scope and evidence. It is
never a Finding. The internal ledger outcome may remain `exact_conflict_candidate` for compatibility,
but public wording uses “exact review-scoped incompatibility,” not “detector candidate.” Static-
source wording says only that the statically inspected source shape is incompatible with the
scientist-specified requirement for this review. It does not claim that the source ran, that the
authors historically intended the requirement, or that the difference caused a reported numeric
error.

### 8. Prove modularity with three unlike method families, not one case

The first implementation MUST route three existing evaluation profiles through the same ordinary-
audit module interface:

1. **Founder-state orientation before HMM emission** — initially exercised by the QTL workspace;
2. **Full-map versus called-tract ancestry exposure** — initially exercised by the pulse-
   admixture workspace; and
3. **LD-covariance whitening before robust fitting** — initially exercised by the MVMR workspace.

These are marker cases, not the scope definition. Their check IDs, manifests, and adapters MUST
contain no GeneBench case identity, expected numeric answer, or fixture-specific path. Each check
must have a structurally distinct supported implementation fixture, a compatible control, an
unrelated hard negative, an ambiguity case, and source/digest mutations. One intentionally simple
fourth conformance module must also be addable and removable without changing core controller,
interaction, report, or schema code; it exists only to prove the extension seam.

The founder-orientation check must additionally pass through both selected-report and static-
source adapters with the normalized intermediate contract. This proves the check/adapter seam;
three one-check/one-adapter markers alone prove only registry extensibility.

All three real profiles begin as experimental, public-development-only, question-only, Finding-
ineligible, metric-ineligible, and promotion-ineligible. Passing all three shows that the framework
supports different dimensions and method structures. It does not qualify the checks, cover an
entire field, or establish that their initial adapters recognize every implementation of those
methods.

### 9. Use GeneBench breadth as a development map, not the definition of generality

The ten GeneBench-Pro cases may be tracked in a coverage ledger showing, for each case, which
installed checks were applicable, unsupported, or absent. Reaching all ten with justified profiles
would be a meaningful development milestone. It would not by itself prove general scientific
coverage because the cases are public, finite, and not independently representative.

A new GeneBench failure may motivate a module only when the proposed check is stated as an abstract
method obligation, has evidence beyond the answer key, and passes unrelated and structurally
varied tests. Do not create `case_id` branches or one-off expected-answer recognizers merely to
increase the coverage count.

Before any profile gains a qualified detector or broad capability claim, it requires the ordinary
independent qualification process and non-GeneBench evidence. The architecture should make that
future growth incremental: new checks extend the registry while the conservative core remains
unchanged.

Before claiming method-level portability even at the experimental question tier, one check must
also pass answer-blind non-GeneBench repositories from independent authors across materially
different layouts, symbols, and supported implementation styles. Those public repositories need
not contain a scientific mistake. A covered-good applicable workflow, an unrelated hard negative,
or a repository on which the module correctly abstains can establish portability and false-
applicability evidence without accusing an unrelated researcher. Controlled mutations and fresh-
agent implementations may exercise the incompatible branch, but they remain synthetic or agent-
generated evidence rather than independent scientific positives.

Metamorphic tests must preserve the result across repository names, paths, irrelevant formatting,
irrelevant code, and symbol renaming while role/data-flow mutations change or suppress the result.
Hard negatives include vocabulary lookalikes, unused helpers, multiple targets, dynamic dispatch,
and unrelated source. A later qualified-detector claim still requires the ordinary real positive
and hard-negative evidence gates; this question-only architecture does not redefine them. The
strongest honest portability claim remains “supports these enumerated representations of method X
through adapters A and B,” never “recognizes any workflow using method X.”

### 10. Re-run fresh-context usability through the scientist boundary

After implementation, repeat Experiment 0020 from a clean copy of the raw QTL repository with a
fresh agent that has not seen the expected result or approved Answer. The controller must produce
one bounded analysis-scoped question. The agent must explain it plainly, show the exact proposed
normalized Answer and scope, stop for the scientist, record only the supplied Answer, resume,
lock, interpret, and replay.

Also run ordinary audits for the pulse-admixture and MVMR markers to prove the same controller path
loads different modules without case-specific orchestration. Removing one module must suppress
only its question and explicitly change its coverage state.

The repository owner has standing authorization for this and later fresh-context
`scientific-audit` usability test runs. That authorization does not let a test agent approve an
ADR, choose the scientist's Answer, see answer-side references, execute project code, or alter
public authority.

## Independent broad-design review

An independent fresh-context agent reviewed revision 2 for modularity, method-level generality,
schema fit, conservative authority, and implementation practicality. Its initial review identified
three architectural defects:

1. the check/adapter split lacked a normalized intermediate contract and multi-adapter arbitration;
2. sibling-module isolation was tested but not normatively guaranteed; and
3. the proposed static assertion incorrectly used the PublicationSurface as the subject of a
   source-code fact without an explicit source-to-analysis join.

This revision incorporates all three corrections, plus a capability-limited adapter API, two-
adapter portability proof, precise removal semantics, separate qualification-artifact promotion,
bounded public incompatibility wording, and non-GeneBench metamorphic evidence before any method-
level portability claim.

The reviewer's follow-up blocker audit found no remaining architectural blockers. It judged the
framework sufficiently general and modular for an architecture decision while emphasizing that
implementation must still prove the typed v0.14.0 scope join, module isolation, adapter
arbitration, fresh-context interaction, and independent non-GeneBench portability. Failure of one
marker to establish a typed scope join must produce abstention or a schema-gap proposal, not a
weakened relation.

## Alternatives

### Hard-code the QTL source pattern in the controller

Rejected because it would close one benchmark case without creating an extensible scientific-
check system.

### Broaden general Markdown Claim extraction until all reports parse

Rejected as the immediate fix. Arbitrary result sections do not establish the contract dimension,
method applicability, or scientific authority needed for a bounded comparison, and broad Claim
extraction would add a much larger false-association surface.

### Promote evaluation probes directly as detectors

Rejected. Public-development positives and corrected controls do not establish detector
qualification, intended method, numerical causality, or Finding authority.

### Load project-supplied detector plugins

Rejected. Executing a plugin from the audited repository would violate the non-executing MPP and
allow project text or code to redefine the referee. Modules must come from the explicitly selected
auditor-controlled registry.

### Let the skill agent invent checks while reviewing

Rejected. That would make scientific issue discovery and applicability depend on model judgment
and could reproduce the same assumptions that created the workflow.

### Require a pre-analysis method contract

Rejected as the primary path under ADR-0019. The product must review inherited repositories while
remaining honest about unresolved method intent.

### Add a new public ScientificCheck record in schema v0.15.0 now

Deferred. Existing v0.14.0 records appear sufficient for the bounded interaction slice, while
manifests and registry state can remain controller inputs to semantic lock. Implementation must
prove that claim or stop with a schema gap rather than hide new record meaning in an extension.

## Acceptance evidence required

1. One generic registry protocol schedules every module without check-specific controller,
   interaction, report, semantic-lock, or schema branches.
2. Every adapter receives only the capability-limited frozen base-inspection view and emits the
   closed `normalized_method_observation_v1`; the method-level check is a pure reducer over that
   value.
3. Modules are deterministic, digest-bound, explicitly injected, isolated, never loaded from the
   audited repository, and unable to read sibling outputs.
4. Equivalent multi-adapter observations deduplicate; disagreements, multiple targets, and
   incompatible scope paths abstain independently of registry order.
5. Adding and removing a conformance module changes only its registry, manifest, implementation,
   fixtures, module-local output, and declared audit-level coverage; unaffected module-local
   outputs remain byte-stable.
6. QTL orientation, pulse-admixture exposure, and MVMR whitening use the same ordinary-audit
   interface across different dimensions and comparison structures.
7. The founder-orientation check uses materially different selected-report and static-source
   adapters without duplicating the scientific rule.
8. No production applicability rule contains a GeneBench case ID, expected answer, fixture path,
   repository name, or unverified model inference.
9. Each initial module recognizes its exact positive and structurally distinct supported variant;
   compatible, unrelated, ambiguous, dynamic, multiple-target, parser-mismatch, and incomplete-
   counterevidence cases fail closed.
10. Questions, contracts, candidates, observations, comparison forms, module and adapter digests,
    selected surface, snapshot, typed scope-join path, and source spans are controller-derived and
    mutation-tested; co-presence or an extension-only join is rejected.
11. Direct compatibility yields a covered negative, exact incompatibility yields an “exact review-
    scoped incompatibility” Disclosure, and `unknown` remains unresolved for every comparison form
    exercised.
12. Report claims cannot override contradictory static source, and static source never establishes
   execution.
13. Claim-scoped ADR-0019 behavior remains unchanged, while analysis-scoped WorkItem, Answer,
    declaration, derivation, ledger, disclosure, and report paths validate under v0.14.0.
    If the source-to-analysis join cannot validate through existing typed records, the marker
    abstains and a schema ADR precedes implementation.
14. Duplicate module IDs, manifest drift, nondeterministic ordering, cross-module leakage, scope
    mutation, Answer mutation, and lock mutation fail closed; one module failure remains local.
15. Fresh-context QTL usability reaches the scientist boundary without expected-result leakage;
    QTL, pulse-admixture, and MVMR marker runs replay deterministically.
16. No project-authored code runs, no model establishes a material premise, and no model call occurs
    after semantic lock.
17. A manifest edit alone cannot promote maturity; an exact separately accepted qualification
    artifact and existing detector admission remain mandatory.
18. Detector capability-matrix entries, qualified capability claims, metrics, and Finding
    authority remain unchanged; documentation identifies these initial modules as experimental and
    question-only.
19. The GeneBench coverage ledger distinguishes applicable, unsupported, absent, and checked; it
    never treats ten public cases as qualification or general scientific coverage.
20. Any method-level portability claim names exact supported adapters and follows answer-blind non-
    GeneBench, independent-author, metamorphic, role-mutation, and hard-negative evidence. The
    independent public evidence may be covered-good, negative, or a correct abstention; a public
    error positive is not required for experimental question-only portability.

## Consequences

- The controller gains one stable extension seam rather than accumulating domain-specific
  branches.
- Scientific checks can be added, removed, or given new language adapters without changing their
  authority or unrelated checks.
- The first three method profiles make the modularity claim testable across distinct scientific
  structures while remaining narrow and non-accusatory.
- The scientist, not the coding model or static profile, chooses a study-specific requirement when
  no independently authoritative rule resolves it.
- Static inspection and execution evidence remain separate.
- Any repository can be audited, but only installed, demonstrably applicable checks count as
  checked; most scientific methods will initially remain unsupported.
- GeneBench breadth becomes a useful development scorecard without becoming a source of hidden
  case-specific rules or a qualification corpus.
- No schema release is planned, but an implementation-discovered representation mismatch is a
  stop condition requiring the schema-gap process.
- This decision improves the extensibility of the scientific reviewer; it does not by itself
  complete detector qualification or the evidence-first MPP.

## Implementation evidence

The accepted revision is implemented without a schema change. `scientific_check_registry_v1` is
explicitly injected and canonically ordered. It evaluates immutable normalized observations from
capability-limited adapters, applies pure module reducers, localizes adapter failure, arbitrates
equivalent and conflicting observations, verifies packaged source-byte implementation identities,
and locks installed and explicitly unavailable module state. Ordinary audit compilation reuses
v0.14.0 ScientificContract, SemanticAssertion, MaterialQuestion, Answer, semantic-lock, report,
storage, and replay paths.

QTL founder orientation, pulse-admixture exposure, and MVMR whitening use the same interface with
six exact supported operands. A removable conformance module proves that removal produces an
explicit `not_installed` coverage disclosure while leaving substantive module projections byte-
stable. The QTL check uses separate selected-report and Python source adapters. The source adapter
recognizes formal data roles and bounded callsite dataflow, survives local symbol renaming and an
unused lookalike helper, and fails closed for multiple role-complete targets. Because the marker
repository has no typed source-to-selected-analysis path, that exact source observation is only an
internal corroborator or suppressor and is never compiled as public evidence.

An independent fresh-context `scientific-audit` skill run on the answer-blind raw QTL workspace now
produces zero Findings and one exact analysis-scoped MaterialQuestion, explains the report/source
authority boundary, verifies integrity, and stops for the scientist's choice. A subsequent UI
follow-up exposes the exact observed operand, immutable source, finite candidates, comparison form,
scope, authority limitation, unknown path, and downstream consequence in both the typed agent
payload and rendered HTML.

- **Tests added:** `tests/test_scientific_check_registry.py`,
  `tests/test_scientific_check_integration.py`, and analysis-scoped additions to
  `tests/test_posthoc_method_ledger.py` and `tests/test_agent_protocol.py`.
- **Acceptance criteria satisfied:** generic scheduling, frozen adapter boundary, pure reduction,
  deterministic arbitration, sibling isolation, removable-module coverage, three-family marker
  reuse, distinct QTL adapters, identity-independent applicability, closed mutation behavior,
  analysis-scoped interaction, and model-free lock/replay behavior are exercised.
- **Fresh-context acceptance criterion satisfied:** the scientist selected the exact repair-before-
  emission operand; the controller recorded the structured Answer, produced one review-scoped
  incompatibility Disclosure with zero Findings, locked without later model access, and replayed
  the same snapshot, semantic-lock digest, assessments, and repository paths.
- **Independent abstention criterion satisfied:** Experiment 0021 audits and replays six
  commit-pinned, independently authored non-GeneBench QTL and robust-MR repositories across R,
  C/C++, Python, Rcpp, and different package/report layouts. All retain zero Findings and zero
  MaterialQuestions; five close-domain MVMR surfaces are `not_applicable`, while the closest
  method-like hard negative is explicitly `unsupported` rather than coerced into an operand.
- **Remaining coverage limitation:** Experiment 0021 proves false-applicability control, not useful
  method portability. No current adapter produced an applicable observation on an independently
  authored repository. No detector has been qualified, no metric or Finding authority changed,
  and public static-source questions remain unavailable without a typed source-to-selected-
  analysis join or a forward-only schema ADR.
