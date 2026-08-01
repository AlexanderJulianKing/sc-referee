# ADR-0028: Ask whether a transition path continues across unobserved intervals

- **Status:** Accepted
- **Date:** 2026-07-30
- **Accepted:** Under the repository owner's standing authorization for non-major ADRs that do not
  expand Finding authority, schema meaning, execution privilege, or public maturity claims
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None
- **Related decisions:** Accepted ADR-0019, revised ADR-0020, accepted ADR-0023, and Experiment 0025
- **Evidence basis:** Two separately authored answer-isolated pulse-admixture workflows and a
  fresh evaluator-owned transition-continuity/full-map-exposure 2-by-2

## Plain-language summary

Two independent workflow-writing runs made the same path decision after filtering ancestry
tracts: both treated a masked or uncalled interval as ending the chromosome path, so retained
tracts on opposite sides could not contribute a transition. Both also used retained called length
rather than full chromosome-map length for pulse timing. Both missed the released timing values.

After repairing the separately demonstrated chromosome-3 label orientation, changing transition
continuity alone and changing exposure alone each left both timing fields outside tolerance.
Changing both moved all four requested fields inside tolerance. This establishes two separate
fixed-case choices. ADR-0023 already covers exposure; this ADR adds only the missing transition-
continuity question. Neither module selects the scientifically governing choice.

## Decision

### 1. Add one atomic dependence-structure question

Add `check:within-sequence-transition-path-continuity` under the ScientificContract
`dependence_structure` dimension. Its closed operands are:

- `preserve_within_sequence_path_across_unobserved_intervals`; and
- `terminate_path_at_unobserved_or_filtered_intervals`.

The first operand requires an explicit selected-report declaration that transitions are evaluated
between successive retained states within one sequence across intervening missing, masked,
filtered, or uncalled intervals while sequence ends remain boundaries. The second requires an
explicit declaration that those intervals terminate the path and transitions are evaluated only
at contiguous retained-state boundaries.

### 2. Keep path continuity separate from exposure and label orientation

Path continuity controls which retained states are adjacent for transition counting. Exposure
controls the denominator or opportunity used by the transition model. Label orientation controls
the meaning of observed state labels. One report may therefore create separate questions for path
continuity and exposure. Neither question implies or answers the other, and chromosome-label
harmonization remains unsupported by this module.

### 3. Preserve scientist authority and the existing output ceiling

The auditor may recognize only an explicit selected-Markdown declaration. It cannot infer hidden
states inside a gap, impute a transition, decide that a gap preserves or terminates a scientific
process, or treat agreement with a benchmark as authority. The scientist may select one listed
review-scoped requirement or retain the choice as unknown.

The module is question-only, Finding-ineligible, metric-ineligible, and promotion-ineligible. It
executes no project code and adds no schema release, detector qualification, execution privilege,
or correctness claim.

### 4. Repair the existing exposure adapter without broadening its meaning

ADR-0023's `check:full-map-ancestry-exposure` additionally recognizes the fresh report's explicit
forms: a statement that pulse-time transition exposure uses retained callable A-plus-B length, a
statement that it uses complete chromosome-map length, or the exact statement that unrepresented
map length is not time-model exposure. An ancestry-fraction denominator alone still cannot answer
the pulse-time question.

## Alternatives rejected

### Declare path preservation scientifically correct

Rejected because missing intervals can be censoring boundaries in some models and latent portions
of one continuing sequence in others. The governing dependence model must come from the scientist,
not the benchmark or auditor.

### Fold continuity into full-map exposure

Rejected because the fresh 2-by-2 shows that either change can be made without the other and that
neither alone repairs the fixed case.

### Add a population-genetics-specific error detector

Rejected because the underlying choice concerns finite-state paths across retained-data gaps. The
module uses domain-neutral semantic roles and remains an exact report adapter rather than a rule
keyed to GeneBench identity, chromosome 3, ancestry labels, or numeric targets.

## Acceptance evidence

- Both independently authored baseline reports map to the terminate-path operand.
- The corrected prior report and fresh combined ablation map to the preserve-path operand.
- Reports containing both complete declarations are ambiguous and create no question.
- Plotting-only continuity language and incomplete transition summaries create no question.
- Transition continuity and pulse-time exposure coexist as two independent questions.
- Matching and conflicting scientist Answers produce deterministic, Finding-ineligible
  compatibility Disclosures and replay exactly.
- Removing the transition module leaves the founder-orientation sibling evaluation unchanged.
- The fresh baseline, four 2-by-2 cells, and prior baseline/corrected reports audit with zero
  Findings and replay without model access or project execution.

## Remaining limitation

The adapter recognizes a small explicit Markdown grammar. It does not parse source-code data flow,
hidden-state marginalization, interval censoring, imputation, notebooks, non-Markdown reports, or
arbitrary graph and time-series models. The recurrence uses two independently authored workflows
over one public-development task. The 2-by-2 demonstrates numerical relevance only for that fixed
case and does not establish which operand governs another study or qualify a detector.
