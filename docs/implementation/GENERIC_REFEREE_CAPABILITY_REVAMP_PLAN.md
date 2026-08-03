# Generic referee capability revamp plan

- **Status:** Active planning artifact
- **Scope:** Product-wide scientific capability architecture, beginning with dependence and
  pseudoreplication
- **Policy effect:** None. Record meaning, Finding authority, and public capability claims may
  change only through separately accepted ADRs and qualification evidence.

## Purpose

Turn sc-referee's bounded scientific calculations into useful referee capabilities without
overfitting production logic to one benchmark, repository, language, file layout, domain, or known
answer.

The first complete vertical will be generic dependence and pseudoreplication review. The same
architecture will then be applied selectively to other scientific-error families.

## Progress snapshot: 2026-08-03

The immediate cold-recognition lane has authored, frozen, audited, and graded all ten public
GeneBench-Pro workflows in answer-isolated contexts. Eight were outside the public grading
contract and all eight now reach at least one relevant bounded method question. Five were replayed
against external evaluation requirements and produced exact review-scoped incompatibility
Disclosures. No production Finding authority was added. One of two within-contract controls also
produced a relevant unresolved question.

This completes the ten-case inventory, not the broader capability program. In particular, the
population-genetics label-orientation error still requires a data/model adapter, and the generic
dependence/pseudoreplication vertical remains the next architectural milestone.

“Generic” means that the evaluator operates on domain-neutral scientific relationships and accepts
evidence through removable adapters. It does not mean that static software can understand opaque
arbitrary workflows. Unsupported evidence must abstain cleanly.

## Current diagnosis

The cross-cutting evidence infrastructure is substantially reusable:

- immutable snapshots and exact identity grades;
- typed evidence, questions, Answers, and lineage records;
- semantic lock, integrity verification, and deterministic replay;
- bounded, non-executing source and material-input adapters;
- calculation and detector registries with implementation digests;
- conservative Finding admission; and
- answer-isolated qualification and metric machinery.

The scientific product layer is less mature. Most current calculation modules produce useful exact
Disclosure-only observations; the selected feature-identifier module can additionally feed one
nonproduction evaluation candidate after an exact human Answer. The real-project detector paths
are experimental and unqualified. Several capability descriptions use “full for a declared
profile” to mean that a calculation is available, even when automatic recognition, diagnosis,
impact tracing, referee reporting, and Finding authority are absent.

This distinction is the portfolio-wide issue to repair.

## Capability maturity vocabulary

Replace broad labels such as **full** with separately reported dimensions:

1. **Inventoried** — relevant files or operations were structurally identified.
2. **Recognized** — exact evidence was normalized into a supported scientific case.
3. **Structurally verified** — applicability and all finite safeguards/counterevidence were
   resolved deterministically.
4. **Impact tested** — an optional bounded alternative analysis or exact result comparison was
   completed.
5. **Evaluation candidate** — Finding-shaped output passed nonproduction admission and may enter
   answer-side evaluation.
6. **Finding-qualified** — a separately promoted detector envelope may emit a production Finding.

Each capability must report these dimensions independently. No aggregate “full” status is allowed.

## Minimal reusable architecture

Do not build a universal ontology of scientific workflows. Use one small common protocol plus a
compact normalized case for each issue family:

```text
workflow evidence
    -> removable evidence adapters
    -> family-specific normalized ReviewCase
    -> deterministic evaluator
    -> question / covered negative / evaluation candidate / abstention
    -> optional impact adapter
    -> referee-oriented report
    -> independent qualification and possible promotion
```

### Common ReviewCase protocol

Every family-specific case exposes only shared control information:

- case family and version;
- exact review target and affected result/Claim references;
- exact source, record, and material-input evidence references;
- applicability premises and their states;
- finite safeguard/counterevidence checks;
- unresolved semantic dimensions;
- unsupported constructs;
- deterministic input digest; and
- declared output ceiling.

Use internal typed Python structures first. Add or change public schema records only after the
interface survives cross-domain use. Do not silently overload an accepted record's meaning.

### Separation of responsibilities

- **Adapters** bind workflow-specific evidence into a normalized case.
- **Evaluators** contain domain-neutral scientific decision rules over that case.
- **Impact adapters** optionally recompute or compare outcomes; they do not control structural
  applicability.
- **Reporters** explain demonstrated facts, unknowns, and requested evidence in referee language.
- **Qualification** alone grants production Finding authority.

## First vertical: generic dependence and pseudoreplication

### DependenceCase

The first normalized case contains:

- analyzed observation set;
- intended independent-unit definition and authority;
- observation-to-unit membership relation;
- count and distribution of observations per independent unit;
- exact analysis input binding;
- fitted/tested estimator or procedure binding;
- declared or statically verified dependence behavior;
- candidate dependence safeguards;
- affected result and Claim references; and
- unresolved or opaque evidence.

The core uses `observation`, `independent_unit`, `membership`, `cluster`, `block`, and `safeguard`.
It must not contain domain terms such as `cell`, `patient`, `well`, `animal`, `image`, `visit`, or
`site`.

### Deterministic decision rule

A structural pseudoreplication candidate is eligible only when all of the following are
established:

1. multiple analyzed observations belong to at least one shared independent unit;
2. those observations entered the fitted or tested analysis separately;
3. the bound procedure used row-level independence for the relevant uncertainty or randomization;
4. no applicable dependence safeguard was present;
5. every registered finite counterevidence check completed; and
6. the affected result or Claim is exactly localized.

Outcomes are:

- repeated units, row-level independence, no safeguard: structural evaluation candidate;
- repeated units with a verified applicable safeguard: covered negative;
- unresolved unit or model semantics: MaterialQuestion;
- opaque input, estimator, wrapper, or lineage: Disclosure/unsupported;
- one observation per independent unit: not applicable.

### Safeguard registry

The initial finite registry should cover exact evidence for:

- aggregation to one row per independent unit before fitting;
- mixed-effects models with the governing grouping structure;
- generalized estimating equations with the governing cluster;
- cluster-robust uncertainty with the governing cluster;
- paired or blocked analysis when the design requires it;
- cluster-level permutation, bootstrap, or randomization; and
- explicitly supported dependence-aware domain methods.

Presence of a keyword is insufficient. Each safeguard adapter must bind the grouping operand, the
analysis target, and the procedure that consumed it. Ambiguous wrappers and dynamic dispatch
abstain.

### Evidence adapters

Prove domain neutrality with at least three materially different initial adapters:

1. single-cell observations nested within biological samples or participants;
2. longitudinal or repeated-measure tabular observations nested within participants; and
3. nested experimental or imaging observations such as fields/wells within specimens/animals.

Each adapter maps its evidence into the same DependenceCase. The evaluator must remain byte-for-byte
unchanged when adapters are added or removed.

Candidate unit names discovered from conventions may be offered only as questions. Unit authority
must come from exact report/method evidence, a data dictionary, a bound contract, or an explicit
human Answer.

### Optional impact analysis

Structural detection must not require recomputation. When exact bounded inputs and a declared
alternative are available, removable impact adapters may:

- aggregate to the independent unit;
- fit a declared cluster-aware, paired, blocked, or mixed model;
- compare effect direction and magnitude;
- compare uncertainty and multiplicity-adjusted results;
- localize changed reported results and Claims; and
- report power separately from result survival.

Loss of significance under an underpowered alternative is not evidence that an effect is absent.
Impact evidence may strengthen a localized consequence statement, but it cannot repair missing
structural premises or grant Finding authority.

### Referee reporting

The main report should state, in order:

1. the concrete observed design or model relationship;
2. the exact concern or covered safeguard;
3. the affected result or Claim;
4. completed impact evidence and its limitations; and
5. the next evidence or correction requested.

Questions must request missing facts rather than ask the scientist to endorse a software premise.
Unrelated `not_applicable` checks are collapsed into a coverage appendix and do not inflate the
headline Disclosure count.

## Portfolio maturity audit

The current scientific families require different amounts of surrounding work. Existing
deterministic arithmetic should be preserved unless a separate correctness defect is found.

| Family | Reusable asset | Missing referee layer | Planned treatment |
|---|---|---|---|
| Dependence / pseudoreplication | Patient-level sensitivity calculation and bounded H5AD/table readers | General evidence binding, safeguard verification, structural detector, Claim localization, qualification | First complete vertical |
| Design integrity, pairing, aggregation | Exact categorical design, pairing, aliasing, and aggregation calculations | Automatic design-role binding, governing-unit authority, affected-result lineage, qualification | Reuse DependenceCase evidence where possible; split only genuinely distinct decisions |
| Multiple testing | Exact complete-family Benjamini-Hochberg recomputation | Discovery of the tested family, proof of completeness, report/result lineage, alternate-procedure envelopes | Build a compact MultiplicityCase after dependence |
| Model/response compatibility | Exact finite R-call registry and response-scale comparison | General call/data binding, wrapper handling, result lineage, broader languages, qualification | Build a MethodCompatibilityCase; keep a finite method registry |
| Circular selection and testing | Exact narrow Scanpy selection-reuse observation | Domain-neutral selection/test identity, safeguard verification, Seurat and other adapters, impact/Claim tracing | Build a SelectionReuseCase after method binding improves |
| Identifier integrity | Exact selected CSV/TSV-to-H5AD set comparison | Identifier-role authority, malformed-value classes, mappings, producer lineage, downstream impact, qualification | Replace equality-led interaction with an IdentifierIntegrityCase |
| Effect relevance | Exact declared threshold/table summary | Claim semantics, authoritative threshold, affected-claim binding, meaningful referee conclusion | Keep calculation; add only when natural claim evidence is available |
| eQTL sign/support | Exact bounded donor-level OLS comparison | Broader estimator families, adjustment semantics, result/Claim lineage, natural qualification | Retain as a domain adapter; do not force into a universal core |
| Hi-C estimator fidelity | Exact bounded arithmetic-background recomputation | Broader estimator evidence, target meaning, result/Claim lineage, natural qualification | Retain as a domain adapter; broaden only from recurrent natural cases |
| Sequence-record boundary | Exact recurrent two-line/AST boundary observation | Natural scientific recurrence, consequence tracing, qualification | Keep Disclosure-only until non-benchmark demand recurs |
| Experimental method conflicts | Typed question, Answer, comparison, and qualification-proof machinery | Registered natural scientific bindings and independent qualification | Reuse as control infrastructure, not as a universal scientific interpreter |

## Prioritization rule

After dependence, select the next family by all four factors:

1. repeated occurrence in independent natural workflows;
2. material referee value;
3. ability to define a finite, falsifiable evidence and counterevidence envelope; and
4. availability of positive, safeguarded-negative, ambiguous, and opaque qualification cases.

One benchmark miss or one convenient local capsule is insufficient.

Recommended order, subject to recurrence evidence:

1. dependence, pairing, and aggregation structure;
2. multiple-testing family integrity;
3. model/response compatibility;
4. circular selection/testing;
5. identifier integrity and transformation;
6. effect/claim relevance; and
7. domain-specific numerical families as supported adapters.

## Anti-overfitting requirements

Production code and manifests must contain no benchmark/task names, repository names, paths,
hashes, expected result counts, known answer values, or domain-specific constants outside a
separately identified adapter whose domain semantics require them.

Every family must include:

- file, column, variable, level, and identifier renaming tests;
- row/column reordering and equivalent-encoding tests;
- positive, corrected, safeguarded-negative, hard-negative, ambiguous, unsupported, malformed,
  and over-budget roles;
- wrapper, alias, dynamic-dispatch, and conflicting-evidence controls where source code is used;
- adapter-removal and sibling-module-isolation tests;
- mutation tests for every applicability and counterevidence gate;
- natural non-benchmark workflows held out during implementation;
- leave-one-domain-out evaluation for domain-neutral cores; and
- answer-isolated labels and comparison records with no production access to answer keys.

Model confidence, repository self-assertion, filename convention, or expected scientific practice
cannot establish a Finding premise.

## Qualification and promotion

Before evaluating a candidate detector:

1. freeze the detector version and supported envelope;
2. freeze case inclusion, exclusion, and opportunity denominators;
3. freeze independently adjudicated scientific labels;
4. predeclare promotion metrics and thresholds;
5. include natural positives, valid safeguards, ambiguous cases, and critical hard negatives; and
6. keep problem clusters together across evaluation splits and resampling.

Promotion requires the accepted cross-provider review and metric process. No local fixture,
development benchmark, compatibility target, point estimate, or maintainer intuition substitutes
for that evidence. Known critical hard-negative failures block promotion even when aggregate
metrics appear acceptable.

Promotion is envelope-specific. A qualified explicit tabular dependence envelope does not grant
authority over arbitrary single-cell, imaging, longitudinal, or opaque workflows.

## Delivery sequence

### Immediate cold-recognition lane — Natural workflow reality check

Run this lane before and alongside the deeper family verticals:

- author all ten public GeneBench-Pro workflows in answer-isolated fresh contexts;
- freeze and audit before answer-side grading;
- record relevant check coverage as absent, unsupported, applicable, or checked;
- use misses to propose generic normalized cases or bounded adapters only after the cold artifact is
  frozen;
- require renamed-layout, corrected, hard-negative, ambiguity, and unsupported controls for every
  production change; and
- retain within-contract workflows as false-accusation and covered-negative controls.

**Exit gate:** every case has an honest coverage state, and each implemented change improves a
generic method family without benchmark identity or answer leakage. This gate does not imply
qualification.

### Phase 0 — Truthful capability surface

- Add an ADR for the multidimensional maturity vocabulary.
- Update generated capability manifests and human documentation.
- Replace “full” claims with exact recognition, verification, impact, and Finding dimensions.
- Collapse unrelated not-applicable checks in headline reporting without deleting coverage.

**Exit gate:** no public surface can describe a calculation-only path as an end-to-end detector.

### Phase 1 — Common protocol and dependence core

- Add the internal ReviewCase protocol and DependenceCase.
- Freeze the deterministic decision table and safeguard registry.
- Add pure evaluator tests before workflow adapters.
- Preserve current sensitivity calculation as a removable impact adapter.

**Exit gate:** domain-neutral synthetic cases cover every decision and counterevidence branch.

### Phase 2 — Cross-domain adapters and reporting

- Add the three initial materially different adapters.
- Bind affected results/Claims where exact lineage exists.
- Add natural-language referee summaries and evidence-seeking questions.
- Keep unsupported workflows localized and non-adverse.

**Exit gate:** the unchanged evaluator handles single-cell, longitudinal, and nested experimental
cases, including valid safeguards and abstentions.

### Phase 3 — Natural validation and qualification candidate

- Freeze unrelated natural workflows and held-out mutations.
- Run invariance, removal, hard-negative, and leave-one-domain-out tests.
- Produce experimental evaluation candidates only.
- Run the accepted answer-isolated review and metric protocol.

**Exit gate:** evidence supports or rejects a narrowly stated promotion proposal without changing
the frozen detector.

### Phase 4 — Envelope-specific production promotion

- Accept a promotion ADR only if predeclared thresholds and reviewer requirements pass.
- Publish the exact supported envelope and abstentions.
- Keep broader adapters experimental until independently qualified.

**Exit gate:** production Findings are possible only inside the accepted envelope and replay
deterministically from exact evidence.

### Phase 5 — Portfolio migration

- Apply the same pattern to the next recurrence-ranked family.
- Reuse control infrastructure and evidence adapters where semantics genuinely match.
- Do not force unrelated scientific questions into DependenceCase or a universal evaluator.
- Retire or relabel legacy calculation-only capability claims as each family migrates.

**Exit gate:** every advertised scientific family states its exact maturity dimensions and has a
clear retain, revamp, qualify, or defer decision.

## Required engineering gates for every implementation change

- Accepted ADR for changes to record meaning, Finding eligibility, authority, execution privilege,
  or public capability claims.
- Tests before or with behavior changes.
- Strict type checking for core interfaces.
- Exact normalized prompt/work-packet and semantic digests where models are used outside the
  production decision path.
- No project-authored code execution in the production MPP.
- Localized parser/adapter failure.
- Immutable initial snapshot and live-workspace divergence reporting.
- Required repository checks: Ruff lint, Ruff format check, mypy, pytest, and starter validation.

## Non-goals

- A universal ontology for all scientific computation.
- General arbitrary-program understanding.
- Automatic inference of the biological unit from a column name.
- Automatic execution of project workflows.
- Open-ended LLM scientific-error hunting in production.
- One detector version claiming all languages, domains, models, and data layouts.
- A global pass, risk rating, or correctness certificate.

## Definition of portfolio success

The revamp succeeds when:

- useful deterministic calculations are preserved;
- every scientific capability has honest multidimensional maturity;
- at least one domain-neutral core works through several unrelated adapters;
- valid safeguards reliably produce covered negatives;
- ambiguous and opaque workflows abstain rather than accuse;
- reports prioritize material referee conclusions and collapse irrelevant coverage;
- error rates are measured on independently adjudicated natural workflows; and
- production Findings remain restricted to separately qualified envelopes.

## Immediate next action

Complete the ten-case cold-recognition ledger while beginning the first data-dependent generic
case for a miss that cannot be resolved by prose or bounded source syntax. In parallel, draft the
Phase 0 maturity ADR and freeze the Biermann, longitudinal, and nested-experiment controls for the
DependenceCase vertical. Neither lane pre-authorizes Finding promotion or portfolio-wide semantic
changes.
