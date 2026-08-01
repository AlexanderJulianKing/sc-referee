# ADR-0019: Interactive post-hoc scientific review with a scientist in the loop

- **Status:** Accepted
- **Date:** 2026-07-29
- **Accepted:** 2026-07-29 by repository owner
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None proposed
- **Related decisions:** Accepted ADR-0017 and ADR-0018
- **Evidence basis:** Experiment 0018's complete ten-case GeneBench public-development sweep

## Context

sc-referee is primarily a reviewer of an existing scientific workflow. A scientist uses the
`scientific-audit` skill through a coding-agent host such as Codex, points it at a completed or
partly completed analysis, and asks what has gone wrong. The scientist is normally present and can
answer focused questions about the scientific question, intended estimand, governing protocol,
method choices, publication surface, and known limitations.

The separate pre-analysis `method-contract` skill is useful when someone wants guardrails before
building an analysis, but it is not the primary product and must not become a prerequisite for
reviewing an inherited repository.

The ten-case GeneBench public-development sweep shows both why interaction is needed and why it
must remain evidence-bound. One agent workflow was wholly inside its answer contract and nine
missed at least one field. Three failure investigations supported exact bounded localization, but
the six later failures produced six different method families and zero recurrence for the four
existing static source profiles. A post-hoc auditor cannot safely infer one uniquely correct method
from a wrong answer, available columns, or model intuition. It can, however, combine repository
evidence with explicit scientist answers and then check exact compatibility deterministically.

The scientist's availability does not remove epistemic boundaries. An audit-time Answer can state
what requirement should govern this review. It cannot by itself prove what code executed, what the
authors historically intended before seeing results, or which method is universally correct.
Repository text remains evidence rather than instructions, and model confidence remains
non-authoritative.

## Recommended decision

### 1. Keep post-hoc `scientific-audit` as the primary workflow

The primary agentic path MUST accept an existing repository, report, manuscript, notebook project,
or analysis directory and review it without requiring a prior sc-referee contract. It MUST inspect
existing task/protocol text, methods, source, inputs, outputs, logs, and provenance within declared
budgets and without executing project-authored code.

The audit SHOULD become more informative when an existing preregistration, protocol, analysis
plan, or frozen method contract is available. Absence of those artifacts limits only conclusions
that depend on intended method; it does not prevent the audit from checking internal
contradictions, exact invariants, lineage, or other independently established obligations.

The optional `method-contract` skill remains a separate preventive companion for new workflows.
It is not automatically invoked by `scientific-audit`, and its absence is not a defect.

### 2. Use a bounded scientist-in-the-loop interaction before semantic lock

After snapshotting and initial deterministic inspection, the audit MAY ask the present scientist
focused questions needed to resolve a material premise. Questions MUST be derived from an exact
repository ambiguity, an unresolved ScientificContract dimension, or a named closed detector
profile. They MUST NOT be open-ended invitations for the model to hunt for scientific errors.

Useful question classes include:

- which candidate file is the final report or publication surface;
- what scientific quantity, population, comparison, scale, or time point the reported result is
  intended to answer;
- which of a finite set of visibly used denominators, controls, backgrounds, adjustments, or
  operation orders should govern the audit comparison;
- whether a named protocol or analysis-plan file is authoritative for this analysis; and
- whether the scientist wants an unresolved choice preserved as unknown.

The coding agent SHOULD explain each question in plain language, state why the answer changes
coverage, and ask no more than a small coherent group at once. The scientist may answer “unknown”
or decline; that response preserves the unknown and does not block unrelated audit work.

Before recording an Answer, the agent MUST show the exact normalized value and scope that will be
stored. It may help translate the scientist's words into a proposed structured value, but it may
not silently add method requirements, approve its own interpretation, or treat conversational
agreement as an unrecorded premise.

All material questions and Answers occur before semantic lock. After lock, detection, reporting,
status inspection, and replay remain model-free.

### 3. Distinguish four kinds of evidence

The interactive audit maintains four separate planes:

1. **Repository evidence:** exact task, protocol, report, source, artifact, and imported provenance
   records from the immutable snapshot.
2. **Model proposal:** exact-span extraction or normalized-value proposals from the coding agent.
   These remain proposed and Finding-ineligible until independently verified.
3. **Scientist Answer:** a scope-bound human declaration made during the audit. It may establish the
   method requirement that governs this review, but it does not prove historical intent,
   execution, numeric truth, or universal scientific validity.
4. **Controller verification:** deterministic reconstruction of a closed value, source fact, or
   compatibility result. Only this plane can turn supported inputs into a verified detector
   premise.

Conflicts among these planes remain explicit. A scientist's statement that code ran does not create
an Execution record. A report's statement that a method was used does not prove implementation. A
static source shape does not prove that source executed. A retrospective Answer does not rewrite a
preregistration or the initial repository snapshot.

### 4. Build one small post-hoc method ledger over existing records

The first new profile, `posthoc_method_ledger_v1`, projects supported values from existing v0.14.0
ScientificContract dimensions, SemanticAssertions, exact report spans, supported static
Operations, and scope-bound human Answers. It is a derived, manifest-bound controller projection,
not a new public record type or an unconstrained semantic object.

The first deterministic comparison vocabulary contains only:

1. **`value_equals`** — one exact canonical scalar or closed profile value must match;
2. **`set_relation`** — a reported or implemented set must contain every required member and no
   explicitly forbidden member; and
3. **`step_precedes`** — one named analysis step must precede another named step.

Each obligation binds exactly one existing ScientificContract dimension, one applicability state,
one authority source, complete canonical operands, and the exact Claim or analysis scope. Values
are limited to canonical JSON strings, finite numbers, booleans, and arrays of unique strings. No
free-text similarity, synonym expansion, approximate match, model-scored equivalence, or automatic
statistical recommendation enters the deterministic comparator.

An agent may use these forms to log what it sees and what the scientist says. That logging is not
itself a scientific judgment. The deterministic controller checks only exact relations between
separately authorized and separately evidenced values.

If a requirement cannot be represented in one of the 17 existing dimensions without distortion,
implementation stops for that requirement, records a schema gap, and preserves it as unknown. It
MUST NOT overload `measurement_model`, a generic `object`, or an `x-` extension merely to avoid a
schema decision.

### 5. Produce bounded outcomes, not a correctness verdict

The post-hoc ledger comparator emits one of:

- covered negative for an exact compatible relation;
- exact conflict candidate for an exact incompatibility;
- unresolved obligation when a scientist or governing source has not supplied the needed choice;
- unsupported path when reported or source semantics cannot be verified; or
- not applicable.

An exact conflict is worded according to its authority. For an audit-time Answer, the strongest
claim is that the selected report or supported source conflicts with the scientist-specified
requirement governing this review. It does not claim that the same requirement was preregistered or
historically intended. A contemporaneous protocol may support stronger historical wording only
when its identity, scope, chronology, and incorporation are independently established.

No ledger result becomes a production Finding until its exact profile has passed the existing
qualification and admission gates. Missing authority, incomplete source verification, conflicting
scientist Answers, ambiguous scope, or unsupported code suppresses the candidate and produces a
question or coverage limitation instead.

Passing every implemented check is never a correctness certificate. The report MUST state which
relations were checked, which were unsupported, and which scientific choices remained unknown.

### 6. Use an interaction lifecycle compatible with ordinary coding-agent sessions

The primary lifecycle is:

1. snapshot the repository and select or ask about the publication surface;
2. inventory claims, reported methods, source shapes, artifacts, and existing provenance without
   executing project code;
3. construct a partial method ledger from exact evidence;
4. present the scientist with only the bounded unresolved questions needed by applicable profiles;
5. display and record exact scoped Answers, preserving unknown or conflicting responses;
6. rerun deterministic extraction and compatibility checks;
7. create the semantic lock;
8. run model-free detection and reporting; and
9. explain Findings, questions, and coverage in plain language through the skill.

The coding-agent host is a transport and explanation layer over canonical CLI state. It MUST use
status, question, Answer, lock, and replay transitions rather than keeping material decisions only
in chat memory. A session restart or different supported host must not change record meaning.

### 7. Validate the review workflow on existing failed and covered-good analyses

The first validation set MUST operate after the workflows already exist. It does not ask new coding
agents to solve the scientific tasks again.

It includes:

- new post-hoc audits of the QTL, CRISPRi/CasRx, and pulse-admixture workspaces from Experiment
  0018, with explicit scientist Answers supplied before each new lock;
- the MVMR covered-good case, to prove that compatible nonidentical implementations are not forced
  into conflicts;
- an unanswered or “unknown” scientist question that must preserve the unresolved premise;
- conflicting human and repository declarations that must remain conflicted;
- a false self-compliance case where a report claims compatibility but a closed static source
  verifier contradicts it; and
- mutation, scope, chronology, write-once, replay, no-project-execution, and no-post-lock-model
  tests.

Public reference reports may be used only to define evaluation-private questions or expected
outcomes after the original locks. They do not become production intent, held-out evidence, or
qualification. A later fresh-context skill usability test should give an agent only the raw
repository and normal audit request, then verify that it reaches the correct bounded question and
resumes after a scientist Answer without seeing the expected result.

Success means the review skill can turn scientist clarification plus exact repository evidence into
deterministic, narrowly worded compatibility results while preserving unknown, covered-good, and
contradictory controls. It does not require every wrong numerical answer to be diagnosed: some
methods will remain unsupported, and some repositories will lack enough evidence even after
interaction.

### 8. Defer new formats and method rules until validation identifies a bottleneck

Do not add notebook, R, arbitrary workflow execution, or further source profiles merely to create
the appearance of breadth. Add a parser or verifier when the post-hoc validation set shows that an
otherwise exact premise is blocked by a real representation. Add a new scientific rule only after
an exact obligation recurs or the scientist supplies a scope-bound governing requirement.

No schema release is coordinated with this ADR. If implementation discovers that a required
meaning cannot fit an existing v0.14.0 dimension without semantic overloading, stop, register the
gap, and propose a separate forward-only schema ADR.

## Alternatives

### Require the coding agent to use a contract before implementation

Rejected as the primary product path because the user wants an after-the-fact referee, and many
valuable targets are inherited analyses with no sc-referee contract. The optional preventive skill
remains available.

### Add detectors for all nine failed workflows

Rejected because six later failures do not recur under the existing profiles, public answer keys
cannot establish production intent, and per-case grammars would not generalize to a new workflow.

### Let the reviewing model select the correct method

Rejected because the same or a similar model may have created the faulty analysis, model agreement
is not authority, and a plausible convention does not establish the scoped review requirement.

### Treat a scientist's audit-time Answer as historical proof

Rejected because retrospective clarification can govern the present review but cannot by itself
prove preregistration, original intent, execution, or result truth.

### Run an open-ended conversational scientific review without canonical records

Rejected because material premises would live only in chat state, replay would depend on hidden
model context, and uncertainty could be silently converted into accusation.

## Acceptance evidence required

1. `scientific-audit` remains the primary trigger for existing-workflow review; `method-contract`
   remains optional and separate.
2. The controller derives every question from exact unresolved evidence or one named closed
   profile; an open-ended issue-hunting prompt cannot enter the production path.
3. The skill displays the exact normalized Answer and scope before recording it, accepts
   “unknown,” and persists every material interaction in canonical records before lock.
4. Model proposals cannot establish intent; scientist Answers cannot establish execution or
   historical intent; controller verification remains separate.
5. One closed manifest defines the three comparison forms, exact dimension binding, authority
   inputs, and stable digests; all other forms fail closed.
6. Contract-free repositories complete with useful independent evidence plus explicit intended-
   method limitations rather than failing globally.
7. An exact scientist-specified conflict uses retrospective, review-scoped wording and cannot
   become a Finding without ordinary qualification and admission.
8. Post-hoc QTL, CRISPRi/CasRx, pulse-admixture, MVMR, unknown, conflict, and false-self-compliance
   controls pass without executing project code.
9. Task, report, Answer, profile, source, scope, chronology, and lock mutation fail closed; replay
   is deterministic and no model call occurs after lock.
10. Skill documentation states that checked compatibility is not scientific correctness and that
    unsupported methods remain unknown even when a scientist is present.

## Consequences

- The next implementation cycle improves the actual reviewer and its agentic interaction rather
  than requiring the auditor to participate in analysis construction.
- A present scientist can resolve the exact ambiguities that prevented useful post-hoc
  localization in several GeneBench cases.
- The audit remains useful when the scientist does not know an answer, declines to choose, or has
  no historical protocol; those limitations stay explicit.
- Pre-analysis contracting remains available as an optional stronger source of intent evidence.
- The first implementation remains small: one derived profile, three exact comparison forms,
  existing public records, no project execution, and no schema release by default.
- Fresh-context skill usability testing requires separate authorization because it invokes another
  agent, but the initial post-hoc fixed-workspace validation does not require new scientific
  workflow generation.
