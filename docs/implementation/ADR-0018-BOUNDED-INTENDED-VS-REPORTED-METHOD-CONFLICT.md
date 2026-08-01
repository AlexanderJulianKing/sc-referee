# ADR-0018: Add evidence-bound method obligations and deterministic compatibility checks

- **Status:** Accepted
- **Date:** 2026-07-29
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None
- **Related requirements:** SA-FR-018–025, SA-FR-067, SA-FR-080, AC-18, AC-26, AC-43,
  AC-61–62

## Context

The first authorized GeneBench public-development run exposed two different limitations. A
fresh-context agent wrote and twice reproduced a Hi-C workflow, but all three requested values
missed their absolute tolerances. The frozen production audit emitted no Claim, ObservedResult,
DetectorResult, or Finding. It correctly refused to derive the right scientific estimator from an
underspecified task, but it also failed to surface the unresolved analytic choice that was visible
in the submitted report.

The task requested mean `log2(observed/expected)` loop strength but did not define `expected`. The
workflow selected a replicate-wise, low-mappability-filtered, leave-one-out same-distance
arithmetic mean. Its report also showed that alternative background choices produced different
requested case and control values. A post-hoc decision report from the agent acknowledged that
the expected-count estimator was not uniquely specified and that the answer should have stated
that limitation more clearly.

Answer-side evidence later showed that the benchmark expected a masked negative-binomial model
with replicate intercepts, restriction-site adjustment, and condition-specific GC and distance
terms. That evidence establishes the benchmark scoring contract after the audit; it cannot be
inserted into the original production audit or used to pretend that the visible task uniquely
specified that model. The numeric mismatch likewise demonstrates disagreement, not its scientific
cause.

The resulting architectural need is broader than a single intended-versus-reported comparison but
narrower than an open-ended scientific reviewer. sc-referee needs to compile exact evidence about
the requested quantity, data design, declared obligations, reported method, and unresolved
analytic choices into a typed method ledger. Closed deterministic rules may then establish exact
incompatibilities or produce bounded questions. They must not select a universally correct method
from field names, data shape, model confidence, or a question category.

Existing schema v0.14.0 already separates ScientificContract intent, SemanticAssertion authority,
exact Claim/report spans, Operation evidence, Answers, questions, disclosures, DetectorResults,
and Finding admission. The first implementation can use those records and closed derived profiles;
it does not require a new public record type.

## Recommended decision

### 1. Treat method adequacy as a compatibility problem, not automatic method selection

No production rule maps a scientific question type directly to one correct statistical method.
Method adequacy depends jointly on the requested quantity, observation and sampling design,
measurement process, dependence structure, declared baseline or null, required adjustments,
uncertainty target, assumptions, and tolerated approximation. Several methods may remain
compatible with the same evidence.

sc-referee may prove that a reported method conflicts with an exact obligation or that a governing
choice remains unresolved. It may not claim that satisfying the implemented checks proves general
scientific correctness, sufficiency, optimality, or uniqueness. Passing every applicable rule is
a bounded covered-negative result, never a correctness certificate.

### 2. Compile an evidence-bound typed method ledger

The first ledger has two separate planes.

The **question and obligation plane** projects only supported values for:

- target quantity or estimand;
- population, unit, condition, time, and analysis resolution;
- observation type and measurement scale;
- sampling, replication, pairing, clustering, or other declared dependence;
- baseline, null, control, background, or `expected` definition;
- required adjustment, control, exclusion, or selection terms;
- requested uncertainty or inferential target.

The **reported method plane** projects only supported values for:

- estimator family and output transform;
- likelihood, variance family, link, loss, or other exact model declaration;
- grouping, intercept, replicate, pairing, or clustering treatment;
- covariates, controls, exclusions, and target-handling rules;
- aggregation, conditioning, and analysis resolution;
- uncertainty calculation; and
- explicitly reported alternatives, sensitivity analyses, or unresolved choices.

The ledger is not a new public record and is not stored as an unconstrained object in a
SemanticAssertion or extension. It is a canonical derived projection that the controller
recomputes from named v0.14.0 records. Its canonical input includes the public schema version, one
closed profile identifier and version, the profile-manifest digest, every input record identity,
every accepted assertion identity, field-level completeness, and exact source identities. A
DetectorResult binds that projection through `detector_version`, `detector_manifest_digest`, and
`deterministic_input_digest`; replay reconstructs the same projection and refuses any digest or
completeness mismatch.

The first mapping to v0.14.0 is fixed as follows:

| Ledger meaning | Governing v0.14.0 representation |
|---|---|
| target, outcome, comparison, and transform | ScientificContract `estimand`, `outcome`, `comparison`, and `scale_and_orientation` slots |
| population, unit, time, and resolution | `target_population`, `analysis_population`, `unit_of_analysis`, `time_definition`, and `scale_and_orientation` slots |
| observation and measurement model | `outcome` and `measurement_model` slots |
| replication, grouping, and dependence | `unit_of_analysis`, `denominator_or_universe`, and `dependence_structure` slots |
| null, control, background, or expected definition | `comparison`, `control_set`, `denominator_or_universe`, and `measurement_model` slots |
| required covariates, controls, masks, and exclusions | `adjustment_set`, `control_set`, and `selection_process` slots |
| uncertainty target | `uncertainty_target` slot |
| exact reported wording | SemanticAssertion with `semantic_role: reported`, `authority_scope: reported_wording`, and the Claim as subject |
| exact supported static implementation facts | Operation `literal_parameters` under a named parser profile |
| independently admitted runtime facts | Execution and linked observed records; never inferred from source existence |
| unresolved governing meaning | unknown/conflicted ScientificContract slot plus MaterialQuestion and coverage disposition |
| deterministic comparison outcome | DetectorResult premises, evidence, finite counterevidence, coverage, and state |

Every profile field must name one exact row of this mapping and one closed predicate/value grammar.
If a required meaning does not fit a listed ScientificContract dimension or record without
distortion, implementation stops and records the gap in `SCHEMA_GAP_REGISTER.md`; it does not place
the value opportunistically in `measurement_model`, `object`, or an `x-` extension. v0.14.0 has no
general approximation-policy or numeric-tolerance contract dimension. That gap is registered, and
the first vertical slice therefore does not use approximation materiality as a premise.

Every populated value retains its exact source span, source identity, scope, extraction profile,
and authority grade. An exact report statement establishes only `reported_wording`. Static code
may establish that compatible source exists under a closed parser profile, but it does not prove
which path ran. Existing independently admitted runtime evidence may separately establish what
ran. None of these planes silently overwrites another.

An LLM may propose literal SemanticAssertions only when each entry cites an exact span. Exact quote
presence alone does not verify the normalized predicate or value. A profile-specific controller
verifier must independently reparse the cited bytes, reproduce the closed field/value mapping, and
emit or admit a separate controller-produced verified assertion before the value enters the
ledger. The model proposal remains immutable and Finding-ineligible or pending. Unsupported
synonyms, qualifications, partial lists, and failed normalization remain unresolved.

The model may also propose unresolved fields or candidate questions. Model confidence, repeated
agreement by the same model, a fresh model's opinion, or an agent's own earlier method choice does
not establish an obligation or resolve an ambiguity.

Absence is worded narrowly. The system may record that no supported explicit definition was
detected within the completely inspected declared surfaces. It must not turn parser nonrecognition,
opaque prose, incomplete inspection, or an uninspected external protocol into a claim that no
definition exists.

### 3. Apply small, versioned deterministic rule families

Rules operate only on complete compatible ledger fields and are manifest-bound. The following rule
families are the roadmap taxonomy, not the first implementation commitment:

1. **target compatibility:** quantity, transform, unit, condition, population, and resolution;
2. **baseline-definition compatibility:** declared null, control, background, or expected value;
3. **data and estimator compatibility:** exact supported input and estimator types without inferring
   a preferred model family;
4. **design and dependence compatibility:** declared replication, pairing, grouping, or clustering;
5. **adjustment and exclusion compatibility:** exact required versus reported terms and masks;
6. **information-boundary compatibility:** target contamination and declared training, test, or
   selection exclusions;
7. **uncertainty compatibility:** requested versus reported uncertainty target and sampling level;
8. **analytic-fork resolution:** exact report evidence that an unprespecified choice changes a
   requested output; and
9. **approximation compatibility:** an exact declared approximation against an exact governing
   tolerance or policy.

Each rule produces one closed disposition: covered negative, exact conflict candidate, unresolved
obligation, unsupported path, or not applicable. A rule cannot convert an available column, a
plausible scientific convention, an empirical pattern, or an LLM suggestion into a required
adjustment or estimator. New method knowledge enters through a new versioned profile and tests,
not an open-ended similarity judgment.

The first vertical slice implements only `expected_count_background_v1` and the minimum rules
needed to compare its exact expected/background definition, estimator family, link and variance
family, grouping structure, covariate terms, exclusions, target handling, and resolution. Every
other rule family and construct returns `unsupported_path` or not applicable. The profile may not
infer `negative_binomial_glm` merely because inputs are counts or because GC and restriction-site
columns are present.

Approximation compatibility remains roadmap-only until a governing tolerance or approximation
policy has a non-overloaded accepted representation. Without one, sc-referee may state exact
alternative values and ask which method governs, but it must not call their difference material,
acceptable, negligible, or excessive.

### 4. Separate unresolved obligations from demonstrated conflicts

An unresolved obligation produces a MaterialQuestion, non-accusatory Disclosure, or explicit
`insufficient_semantics`/`unsupported_path` coverage state. It is not a Finding or an experimental
Finding candidate.

For example, the combination below may justify a question when every premise is exact:

- the selected task requests `observed/expected`;
- no supported explicit expected-count definition is found across completely inspected governing
  surfaces;
- the selected final report declares one primary background method; and
- the same report provides exact compatible sensitivity results showing that alternative
  background choices produce different requested values.

The bounded output asks which expected-count definition governs the requested values and records
the demonstrated sensitivity. It does not declare the selected estimator wrong or nominate a
negative-binomial model.

An exact conflict candidate requires an authoritative obligation in addition to a reported method.
Eligible obligation authority remains limited to:

- exact explicit task, preregistration, protocol, or analysis-plan text with the correct
  `scientific_intent` scope;
- a scope-bound human Answer applied to a ScientificContract; or
- immutable or cached authoritative external evidence with durable identity and independently
  verified exact extraction, but only when the scoped task, protocol, analysis plan, or human
  Answer explicitly incorporates that external source as governing for this analysis.

A benchmark answer key, hidden reference method, numeric grade, unscoped repository file, model
proposal, model confidence, or generally authoritative guideline that was never incorporated into
the analysis contract cannot establish production intent.

Current v0.14.0 structured-Answer handling deliberately emits an accepted but Finding-ineligible
scientist-declaration assertion. ADR-0018 does not silently reinterpret that record. For a closed
method profile, a new controller derivation may create a separate eligible intent assertion only
after it deterministically verifies the Answer digest, human respondent, authority kind, exact
subject and semantic dimensions, source snapshot, governing question, closed profile shape, and
contract scope. The original Answer and scientist-declaration assertion remain immutable and
ineligible. The derived assertion uses `assertion_class: deterministic_derivation`,
`semantic_role: intended`, `authority_scope: scientific_intent`,
`independently_checkable: true`, verified status with deterministic-comparison method, and a
declared versioned `x-answer-ref`/profile binding. It establishes only that the verified human
Answer governs this scoped method contract; it does not establish scientific truth or executed
computation. Any missing or conflicting check leaves the derived assertion absent.

### 5. Keep exact method conflicts experimental and Finding-ineligible

`detector:bounded-reported-method-contract-conflict` may emit an
`evaluation_finding_candidate` only when all of the following are exact and complete:

1. one selected final Claim is bound to one ScientificContract;
2. one intended method profile has eligible authority and exact scope;
3. one unambiguous report method statement is extracted from the selected publication surface;
4. both profiles are complete under the same version;
5. their incompatibility follows from a deterministic field comparison;
6. finite checks find no alternate or superseding intended profile, conflicting report statement,
   sensitivity-analysis-only qualifier, protocol amendment, approved deviation, conditional-
   applicability mismatch, Claim-to-method scope mismatch, or unsupported construct; and
7. every premise and source reference replays identically.

Candidate wording states only that the selected report's stated method conflicts with the declared
governing method obligation. It does not claim that the code executed, that the numeric result is
wrong for no other reason, or that the governing method is universally scientifically correct.

Missing authority, partial profiles, conflicting declarations, or unsupported prose suppress the
candidate. Numeric mismatch remains evaluation evidence and never supplies a scientific-cause
premise. The detector remains denied production Finding admission until the existing independent
qualification and promotion gates are satisfied.

### 6. Use separate pre-analysis and post-hoc entry points over shared records

Pre-analysis method contracting and post-hoc repository audit share ScientificContract,
SemanticAssertion, WorkItem, MaterialQuestion, Answer, semantic-lock, and compatibility-engine
semantics, but they are not one lifecycle or one skill trigger.

For an agent-created workflow, a distinct `sc-referee method-contract` entry point and separate
agentic method-contract skill construct an analysis-level ScientificContract before analysis code
or a publication Claim exists. The contract is scoped to exact task/protocol FileRecord or
Artifact subjects, records unresolved choices, asks the scientist a bounded question when needed,
and freezes the resolved contract through its own claimless semantic-lock path. It must not invent
a report, publication surface, or Claim to reuse the post-hoc controller. A later Claim binds a
claim-level ScientificContract whose `scope.parent_contract_id` points to that frozen analysis
contract. The coding agent's own method proposal or implementation may populate reported or static
planes; it cannot approve its choice as governing authority.

The existing `scientific-audit` skill and `sc-referee audit` remain post-hoc only. For an existing
repository, they reconstruct literal, source-bound ledger entries from the declared task, protocol,
report, supported source, data schema, and admitted external evidence. Missing documentation
remains unknown. The audit does not execute project code, infer the original research question from
data alone, require large data to be materialized, or provide statistical consulting.

This separation allows the same model to assist with checkable transcription without treating
self-review as scientific independence. A different model or reviewer may propose additional
questions, but its unsupported judgment remains advisory.

### 7. Preserve benchmark and semantic-lock separation

The original GeneBench audit remains unchanged. Before answer reacquisition, a future diagnostic
may surface only the task's unsupported expected-count definition and any exact method sensitivity
contained in the frozen submitted report. It must not infer the hidden benchmark method.

After semantic lock, the answer-side evaluation may construct a diagnostic copy of the exact
reference method profile and test whether the experimental conflict detector localizes the already
adjudicated benchmark mismatch. That diagnostic is public-development evaluation evidence only.
The reference report, answer values, grader, and grade must never enter production detector inputs
or the agent-visible workspace.

No detector promotion follows from this case. Promotion still requires eligible answer-blind
fixtures, independent review, Stage-3 equivalence, clustered metrics, a later threshold decision,
and all existing admission gates.

## Alternatives

### Map every question type to one statistical method

Rejected because question labels do not uniquely determine an estimand, data-generating process,
assumption set, or acceptable approximation. Such a catalog would encode unjustified defaults and
misrepresent compatibility as universal correctness.

### Infer the right method from available columns or empirical patterns

Rejected because the presence of counts, GC, restriction sites, batches, or other fields can
motivate a question but cannot establish that a particular estimator or adjustment is required.

### Ask an LLM whether the method is scientifically appropriate

Rejected as a material-premise path. The model may transcribe exact facts or propose questions,
but an open-ended judgment would recreate prohibited scientific-error hunting and could repeat the
same error made by the coding agent.

### Treat same-model reconsideration as independent corroboration

Rejected because a changed prompt may elicit uncertainty or a different answer without supplying
new authority. Same-model and cross-model agreement can aid recall but cannot establish a Finding
premise.

### Treat every numeric answer-key mismatch as a method Finding

Rejected because a mismatch demonstrates disagreement but not its cause, publication materiality,
or the governing scientific obligation.

### Parse submitted code as proof of execution

Rejected because source existence does not prove which path ran. Static code may corroborate a
reported method under a separate profile, while candidate wording remains bounded to its actual
evidence grade.

## Acceptance evidence required

1. Every `expected_count_background_v1` field maps to named v0.14.0 records and dimensions, and
   replay reconstructs the canonical ledger, profile-manifest digest, completeness, and
   deterministic input digest without reading an unconstrained semantic payload.
2. Exact task, protocol, report, and supported-source grammars preserve exact spans and authority;
   a profile verifier independently reproduces each normalized value rather than relying on quote
   presence or a model-supplied object.
3. Same-model or cross-model proposals cannot establish intended-method authority. The proposed
   assertion remains immutable while the distinct controller-verified assertion and every
   fail-closed mutation are replay-tested.
4. A missing supported baseline definition plus exact differing report sensitivities produces a
   bounded MaterialQuestion or Disclosure, never a candidate or Finding; absent governing
   tolerance prevents materiality wording.
5. Available-but-unused variables without an authoritative adjustment obligation produce at most a
   bounded question; they cannot nominate a required estimator.
6. Existing structured Answer machinery accepts the closed intended-method value only within the
   named ScientificContract dimensions and exact scope. The original Answer-derived declaration
   remains Finding-ineligible; only the separately verified controller derivation can become an
   eligible governing-intent premise.
7. A claimless pre-analysis method-contract run freezes one analysis-level contract without a
   fabricated publication surface or Claim, and a later Claim contract binds it through
   `parent_contract_id`. The existing audit skill remains post-hoc.
8. Matching expected/background profiles produce covered-negative output. One exact authoritative
   incompatibility may produce an experimental candidate that remains denied Finding admission.
9. Missing authority, partial profiles, alternate or superseded methods, amendments, approved
   deviations, conditional applicability, contradictory statements, sensitivity-only declarations,
   wrong scope, incomplete inspection, and opaque text suppress the candidate.
10. Every finite counterevidence check is evidence-linked, mutation-tested, and replay-stable.
11. Audit, linked human Answer, semantic lock, detector result, report, SQLite, and replay remain
    schema-valid and byte-deterministic without model calls after lock or project-code execution.
12. A pre-answer GeneBench regression can surface the unresolved expected-count obligation without
    learning the reference method. A separate post-lock evaluation diagnostic can localize
    `same_distance_arithmetic_mean` versus an explicitly supplied `negative_binomial_glm` profile
    without changing the original zero-Finding audit.
13. One non-Hi-C portability set covers a positive, covered negative, ambiguity, and hard negative
    before any qualification claim; broader rule families remain explicitly unsupported.
14. Capability output names only exact ledger/rule profiles, maturity, unsupported cases, and the
    nonproduction ceiling; it makes no domain-wide, correctness, or qualification claim.

## Consequences

- sc-referee gains a general compatibility-checking pattern without pretending to be an
  omniscient statistician.
- A separate agentic method-contract skill can prevent silent analytic defaults before
  implementation, while the existing audit skill remains post-hoc and undocumented repositories
  preserve missing intent as unknown.
- Deterministic Python decides only compatibility among established fields. The LLM may help log
  cited variables and propose questions but cannot decide the material scientific premise.
- The GeneBench case can produce a useful pre-answer method-definition question and a separate
  answer-side root-cause diagnostic without contaminating the frozen audit.
- The first implementation is only `expected_count_background_v1`; the broader rule taxonomy is a
  roadmap. New rules require adjudicated failures, explicit authority semantics, and tests.
- General approximation/tolerance intent remains a registered schema gap and cannot be smuggled
  into an existing dimension or extension.
- No public schema v0.15.0 is required or scheduled. Accepted schema v0.14.0 remains immutable.
- The built-in project executor remains post-MPP under ADR-0017.

## Acceptance record

Accepted by the project owner on 2026-07-29 after independent broad-design review and the four
resulting corrections. The accepted decision requires a replayable projection over named v0.14.0
records, profile-specific controller verification and a separate Answer-eligibility derivation, a
claimless pre-analysis method-contract entry point distinct from the post-hoc audit skill, and an
initial implementation limited to `expected_count_background_v1`. It schedules no public schema
release, does not resolve the registered general approximation/tolerance gap, and grants no
project-code execution authority.
