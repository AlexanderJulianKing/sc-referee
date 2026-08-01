# ADR-0023: Separate pulse-timing exposure from the ancestry-fraction denominator

- **Status:** Accepted
- **Date:** 2026-07-30
- **Accepted:** Under the repository owner's standing authorization for non-major ADRs that do not
  expand authority, schema meaning, or public capability
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None
- **Related decisions:** Accepted ADR-0018, ADR-0019, and revised ADR-0020
- **Evidence basis:** Experiment 0025 population-genetics one-change ablations

## Plain-language summary

The pulse-admixture workflow contains two different length calculations. One divides called
ancestry-A length by called ancestry-A plus ancestry-B length to report an ancestry fraction. The
other supplies the chromosome length over which ancestry switches could occur to estimate time
since admixture. These quantities can legitimately use different universes in the same analysis.

The first version of `check:full-map-ancestry-exposure` treated either statement as evidence for
one shared denominator choice. A corrected workflow therefore reported a called-tract ancestry
fraction and full-map pulse-time exposure, but sc-referee incorrectly projected the fraction
statement as though the timing calculation also used only called tracts.

This ADR narrows the existing question to pulse timing. An ancestry-fraction denominator cannot
trigger or answer it. The separate choice of whether gaps terminate the transition-counting path
also remains unsupported rather than being folded into the exposure question.

## Context

The frozen Experiment 0025 population-genetics workflow missed all four answer fields. A
one-change chromosome-3 A/B-label harmonization ablation moved both ancestry fractions within
their public numeric tolerances while both pulse-time estimates remained outside tolerance. A
second bounded ablation retained that label repair, counted transitions between successive
eligible tracts within each chromosome across intervening uncalled or filtered spans, and used the
complete chromosome-map length for pulse-time exposure. All four fields then fell within their
contracts.

The corrected report accurately states both of the following:

1. ancestry fractions use eligible called A divided by eligible called A plus B length; and
2. pulse timing uses the complete chromosome-map length in
   `t = N_switch / (2 m (1-m) L_map)`.

The existing adapter matched the first paragraph before considering the timing paragraph and
reported `high_confidence_called_tract_exposure_only` for the whole pulse model. That observation
was not entailed by its cited evidence. Preserving it would violate ADR-0020's exact-applicability
and normalized-observation boundary.

## Decision

### 1. Scope the existing check to pulse timing only

Keep the stable check ID `check:full-map-ancestry-exposure`, but advance the check and selected-
report adapter versions to `1.1.0`. Bind the check to the existing ScientificContract
`time_definition` dimension rather than `denominator_or_universe`.

Its two closed, scientist-governed operands are:

- `full_chromosome_map_exposure`; and
- `high_confidence_called_tract_exposure_only`.

Both operands refer only to the exposure definition used by the pulse-time calculation. The
question wording and candidate labels must say so explicitly.

### 2. Require an exact pulse-time declaration

The selected-report adapter may recognize the called-tract operand only from the bounded
single-pulse timing relation
`t = N_switch / ((1-m)L_A + mL_B)`. It may recognize the full-map operand only when the same
paragraph explicitly says that transition or pulse-time exposure uses the complete/full
chromosome/genetic-map length and reports the bounded
`t = N_switch / (2 m (1-m) L_map)` relation.

A paragraph defining `p_A = L_A / (L_A + L_B)`, an eligible-called A-plus-B ancestry-fraction
denominator, a QC length table, or gap exclusions from that fraction cannot establish either
pulse-time operand. Method-like pulse wording without one supported timing declaration is
`unsupported`; contradictory supported declarations are `ambiguous`.

### 3. Keep transition-path continuity separate

Whether successive eligible tracts are connected across intervening uncalled or filtered spans is
an independent transition-counting policy. The successful fixed-case ablation is causal evidence
for this one frozen workflow, but it is not independent recurrence or authority for a production
question. The existing module must neither infer this policy nor treat it as synonymous with map
exposure. A future module requires its own abstract obligation, evidence, counterexamples, and
validation.

### 4. Preserve the question-only ceiling

This correction does not establish which pulse-time definition governs a review, prove that the
reported calculation executed, validate ancestry labels or calls, or attribute a numeric error.
The module remains experimental, question-only, Finding-ineligible, metric-ineligible, and
qualification-ineligible. No public schema, detector maturity, execution privilege, or capability
claim changes.

## Alternatives rejected

### Keep one composite ancestry-exposure operand

Rejected because one analysis may correctly use a called denominator for ancestry fractions and a
full map for pulse timing. A composite scalar would hide two scientific decisions and make partial
or mixed policies impossible to represent faithfully.

### Add the gap-bridging policy to the same question

Rejected because transition counting and exposure length are not mutually exclusive alternatives.
Combining them would repeat the offset/scale conflation rejected in the CRISPR review and would
overfit one fixed-case repair.

### Ask two new questions immediately

Rejected for now. The ablation demonstrates a second atomic choice in one public-development case,
but no independent recurrence has established that a reusable transition-path question is worth
adding. The conservative result is explicit unsupported coverage.

## Acceptance evidence

- Exact called-time and full-map-time declarations each produce the expected operand through the
  common registry and ordinary audit interface.
- A report with a called ancestry-fraction denominator and full-map pulse timing produces only the
  full-map timing operand under `time_definition`.
- A fraction-denominator declaration alone is `not_applicable`; a transition-path declaration
  without an exposure formula is `unsupported`; conflicting supported timing formulas are
  `ambiguous`.
- The original and chromosome-label-only workflows still expose called-tract pulse timing. The
  combined corrected workflow exposes full-map pulse timing despite retaining a called
  ancestry-fraction denominator.
- All three audits have zero Findings and zero ConditionalConcerns, and their semantic locks and
  rendered reports replay byte-for-byte without model access or project execution.

## Remaining limitation

The v1.1 adapter recognizes only two explicit selected-Markdown timing declarations. It does not
parse general equations, inspect source implementation, validate the single-pulse model, determine
which definition is scientifically appropriate, cover transition-path continuity, detect label
orientation, or prove numerical causality. Those boundaries remain explicit unknown or
unsupported coverage, not Findings.
