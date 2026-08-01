# ADR-0031: Connect two bounded explicit TXR1 operand forms

- **Status:** Accepted
- **Date:** 2026-07-30
- **Accepted:** Under the repository owner's standing authorization for non-major ADRs that do not
  expand Finding authority, schema meaning, execution privilege, or public maturity claims
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None
- **Related decisions:** Accepted ADR-0017, ADR-0026, ADR-0030, and Experiment 0025
- **Evidence basis:** One fresh answer-isolated TXR1 workflow and a frozen evaluator-owned
  target-definition/missingness-strategy two-by-two

## Plain-language summary

A fresh agent chose a third molecular target rule and a third missing-outcome implementation. The
workflow missed all three numeric tolerances, but neither representation was one of the finite
choices already accepted under ADR-0026. Those fresh choices therefore remain unsupported.

The evaluator then changed one axis at a time. Its repaired reports explicitly described two
already accepted operands, but the question adapters did not recognize their natural wording.
This ADR connects those exact report forms to the existing target-definition and missingness
questions. It does not decide which choice is correct and does not add an AIPW-versus-IPW rule.

## Decision

### 1. Connect one explicit adjusted-clonality declaration

Advance `check:somatic-clonality-representation` and its selected-report adapter to version
`1.1.0`, preserving the check ID, `target_population` dimension, and both accepted operands.
The existing `purity_copy_adjusted_clonal_fraction_window_for_target_eligibility` operand may
additionally be observed when one selected-report sentence explicitly states either:

1. an evaluator-frozen `reference_target`, optionally formatted as Markdown inline code, then
   requires a purity/copy-adjusted clonality quantity; or
2. a prespecified or predefined primary-target eligibility rule requires that adjusted quantity;

and the same rule states a single-copy CCF, cancer-cell-fraction, or clonal-fraction range or
window. Finite sentence-distance ceilings remain in force.

### 2. Connect one explicit baseline-only assessment declaration

Advance `check:posttreatment-missingness-strategy` and its selected-report adapter to version
`1.1.0`, preserving the check ID, `missingness_and_transport` dimension, and both accepted
operands. The existing
`assessment_weighting_excluding_posttreatment_endpoint_from_missingness_model` operand may
additionally be observed only when the selected report explicitly connects all of the following:

1. the primary missing-outcome strategy, estimator, or analysis, or an evaluator-owned ablation;
2. an observed toxicity, adverse event, intermediate endpoint, or mediator deliberately excluded
   from every assessment-model predictor set;
3. the excluded variable's after-treatment or post-treatment timing; and
4. inverse-assessment weighting or residual correction transporting observed outcomes.

The primary/evaluator qualifier must precede the exclusion declaration. A sensitivity-only
exclusion followed later by a statement that the primary strategy is unknown cannot match.

### 3. Preserve unsupported fresh choices and estimator uncertainty

The fresh 400-patient molecular rule is neither a direct local-copy ceiling nor the accepted
adjusted-clonality gate. Its assessment model includes observed post-treatment toxicity while
using an AIPW residual correction, so it is neither of the two accepted missingness operands.
Both remain unsupported and produce no question.

The fixed-case target repair explains most of the numerical difference. Excluding toxicity from
the assessment model does not independently repair this fresh workflow and slightly worsens the
benefit estimate when combined with the frozen target. The remaining AIPW-versus-normalized-IPW
difference is not selected by the public task and is not admitted as a scientific question.

### 4. Preserve authority and output ceilings

Both modules remain question-only and Finding-ineligible. They record explicit selected-report
method declarations and return authority to the scientist. They do not prove that a method ran,
validate a target or missingness assumption, infer causality, use numeric agreement as scientific
authority, execute project code, qualify a detector, or change any public schema or maturity
claim.

## Alternatives rejected

### Treat every failed fresh workflow as an admitted choice

Rejected because the fresh target and hybrid assessment representation did not recur an accepted
finite choice, and benchmark disagreement cannot define scientific authority.

### Add an AIPW-versus-IPW correctness rule

Rejected because both are recognizable estimator families with finite-sample and nuisance-model
differences, while the public task does not establish which must govern.

### Infer the repaired operands from source code or numeric movement

Rejected because the production audit does not execute project code, and neither source
appearance nor a closer benchmark answer establishes the selected scientific method. The accepted
connection is limited to explicit final-report wording.

## Acceptance evidence

- The fresh workflow reproduces byte-identically, returns benefit `31.332`, toxicity `33.832`, and
  net utility `19.491` percentage points, and fails all three released numeric tolerances.
- The target-only ablation returns `44.009`, `36.325`, and `31.296`; the missingness-only ablation
  returns `32.443`, `33.832`, and `20.602`; and the combined ablation returns `45.023`, `36.325`,
  and `32.309`. The target-only and combined cells pass toxicity but remain outside the benefit
  and net tolerances; the missingness-only cell fails all numeric fields.
- After this connectivity change, the untouched workflow has no MaterialQuestion, target-only has
  exactly the existing adjusted-clonality question, missingness-only has exactly the existing
  assessment-strategy question, and combined has both. Every cell retains zero Findings.
- All four post-change audits have verified integrity, no project execution, zero model calls,
  byte-identical semantic locks, and byte-identical HTML-report replay.
- Exact natural-language positives, ambiguity controls, a sensitivity-only missingness hard
  negative, a sensitivity-only clonality hard negative, and a four-cell independence regression
  pass in the automated suite.

## Remaining limitation

These rules cover two explicit selected-Markdown declaration families. They do not parse arbitrary
missing-data or somatic-target prose, infer temporal order from source names, validate CCF or
missingness assumptions, identify an estimator from code, select a threshold, choose between AIPW
and IPW, or attribute a numerical mismatch. This public-development evidence does not qualify a
detector or authorize Findings.
