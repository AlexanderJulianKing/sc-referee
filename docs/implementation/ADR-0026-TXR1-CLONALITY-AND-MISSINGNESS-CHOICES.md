# ADR-0026: Keep somatic clonality and missing-outcome strategy as separate questions

- **Status:** Accepted
- **Date:** 2026-07-30
- **Accepted:** Under the repository owner's standing authorization for non-major ADRs that do not
  expand Finding authority, schema meaning, execution privilege, or public maturity claims
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None
- **Related decisions:** Accepted ADR-0019, revised ADR-0020, and Experiment 0025
- **Evidence basis:** Experiment 0025 TXR1 fixed-case 2-by-2 target/estimator ablations

## Plain-language summary

The TXR1 workflow was wrong in two independent places. It selected the molecular target group
using a direct copy-number ceiling instead of the released analysis's purity/copy-adjusted
clonality representation. It also handled missing week-16 outcomes with sequential imputation that
conditioned on week-8 toxicity, while the released target-trial estimator used normalized
assessment weights that excluded that post-treatment endpoint from the missingness model.

Repairing only either choice still failed the answer contract. Repairing both passed every field.
The two decisions must therefore remain separate. This ADR admits two narrow, scientist-governed
questions and does not declare either operand universally correct.

## Context

The generated workflow selected `387` patients and returned code `1`, benefit `36.5`, toxicity
`33.6`, and net utility `24.8`. The released contract expects code `1`, benefit `42.9143`, toxicity
`35.9689`, and net utility `30.3252`.

An independent released-data reconstruction recovered the documented `354`-patient target and
normalized IPTW/IPCW estimator. Its outputs were benefit `42.9326`, toxicity `35.9668`, and net
utility `30.3443`, all within contract. A target-only repair returned `44.3`, `33.6`, and `32.5`,
failing all three numeric fields. An estimator-only repair returned `39.58`, `35.4116`, and
`27.1859`, passing toxicity but failing benefit and net. The combined repair is therefore not a
single indivisible method and neither one-axis repair is a correctness certificate.

## Decision

### 1. Add a post-treatment missingness-strategy question

Add `check:posttreatment-missingness-strategy` under the ScientificContract
`missingness_and_transport` dimension. Its closed operands are:

- `sequential_outcome_imputation_conditioning_on_posttreatment_endpoint`; and
- `assessment_weighting_excluding_posttreatment_endpoint_from_missingness_model`.

The first operand requires one selected-Markdown paragraph explicitly binding an assessed-case
outcome model to a named observed post-treatment endpoint, missing-outcome imputation, and
integration over its treatment-specific distribution. The second requires an explicit
assessment/censoring model, exclusion of the named endpoint because it occurs after treatment, and
IPCW or equivalent inverse assessment-weight wording.

Descriptive associations, baseline histories, complete outcomes, unspecified missingness prose,
and conflicting supported declarations create no question. They remain not applicable,
unsupported, or ambiguous.

### 2. Add a somatic clonality-representation question

Add `check:somatic-clonality-representation` under the ScientificContract `target_population`
dimension. Its closed operands are:

- `direct_local_copy_number_ceiling_for_target_eligibility`; and
- `purity_copy_adjusted_clonal_fraction_window_for_target_eligibility`.

Both operands require an explicit selected-report target-membership declaration in a somatic,
structural-variant, or breakpoint context. The first binds the target gate to a direct local copy-
number ceiling. The second binds it to an explicit purity/copy-adjusted CCF, cancer-cell-fraction,
or clonal-fraction window. The adapter does not hard-code the TXR1 marker, thresholds, target size,
or benchmark answer.

Plots, descriptive copy-number or CCF summaries, negated target definitions, threshold-free prose,
and conflicting declarations cannot establish one operand.

### 3. Preserve atomicity and scientist authority

The two modules may coexist, and neither answers or suppresses the other. The target definition
does not establish the missingness strategy; the missingness strategy does not establish the
target. The scientist may select either finite operand in either question or retain the
requirement unresolved.

Numeric agreement, the evaluation answer, repository text, and model confidence cannot supply the
scientific requirement. Matching and conflicting Answers compile only to deterministic
Disclosures. Both modules remain question-only and cannot emit Findings.

### 4. Keep source inference and general causal validation outside this slice

This slice recognizes exact selected-report declarations only. It does not infer temporal order
from variable names in source code, prove that reported models executed, validate exchangeability
or missing-at-random assumptions, determine alteration multiplicity, validate CCF biology, or
attribute a numeric miss. No public schema, detector qualification, maturity metric, execution
privilege, or Finding authority changes.

## Alternatives rejected

### Add one TXR1-specific compound check

Rejected because the 2-by-2 proves two independently varying choices. A compound check would
overfit the benchmark and conceal partial repairs.

### Declare post-treatment conditioning universally wrong

Rejected because temporal role alone does not determine the estimand or valid identification
strategy. The governing strategy remains scientist- or protocol-authorized.

### Treat copy-number correction as one universal CCF formula

Rejected because general somatic analyses may require alteration multiplicity, local major-copy
constraints, or other measurement models. This module asks which reported representation governs;
it does not select a universal formula or threshold.

## Acceptance evidence

- Exact declarations for both missingness operands and both clonality operands produce their own
  question-only observations.
- Dual declarations are ambiguous; descriptive, baseline-history, complete-data, QC-only, and
  negated-target controls produce no question.
- A four-cell test proves the two modules vary independently without suppressing each other.
- The frozen original, target-only, estimator-only, and combined reports project the four expected
  operand pairs with zero Findings.
- The original and both one-axis repairs remain outside the answer contract as specified; the
  combined repair passes all four fields.
- All four semantic locks and HTML reports replay byte-for-byte without project execution or model
  access after lock.

## Remaining limitation

Each adapter recognizes a small explicit Markdown grammar. It does not parse arbitrary prose,
source code, notebooks, non-Markdown reports, or implicit temporal and measurement roles. The
fixed-case ablations demonstrate numerical mechanism only for this released synthetic task. They
do not establish a universal causal estimator, clonality model, threshold, detector qualification,
or Finding permission.
