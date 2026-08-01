# ADR-0030: Connect one bounded recovered-technical-group co-reference form

- **Status:** Accepted
- **Date:** 2026-07-30
- **Accepted:** Under the repository owner's standing authorization for non-major ADRs that do not
  expand Finding authority, schema meaning, execution privilege, or public maturity claims
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None
- **Related decisions:** Revised ADR-0020, accepted ADR-0023, and Experiment 0025
- **Evidence basis:** A fresh answer-isolated ambient-state workflow and a frozen evaluator-owned
  activation-scale/technical-group ablation

## Plain-language summary

A fresh agent independently reported a donor-level contamination proxy, observed that its values
separated into two ranges, reconstructed that separation as a technical group, and included it as
a categorical covariate in the primary model. The already accepted technical-group question did
not appear because its original grammar expected the technical group to be named again after the
word `included`; the fresh report used the ordinary pronoun `it`.

This is a report-connectivity miss, not a new scientific choice. This ADR permits one finite,
paragraph-scoped co-reference form for the existing inclusion operand. It does not decide that the
reconstructed group is real, confounding, or scientifically required.

## Decision

### 1. Add one finite paragraph-scoped inclusion rule

Advance `check:recoverable-technical-group-adjustment` and its selected-report adapter to version
`1.1.0`, preserving the check ID, `adjustment_set` dimension, and two accepted operands. The
existing `include_recovered_technical_group_covariate` operand may additionally be observed only
when one immutable selected-report paragraph explicitly contains all of the following connected
statements:

1. an ambient, contamination, soup, negative-control, or technical-proxy estimate, fraction,
   rate, or summary;
2. an explicit separation, split, clustering, gap, or threshold in that technical proxy;
3. a statement that the author reconstructed **that** technical group; and
4. a statement that the author included **it** as a categorical covariate in the primary model.

The grammar has finite character-distance ceilings and remains paragraph-scoped. It does not add
general pronoun resolution, source-code dataflow, or cross-section inference.

### 2. Preserve hard negatives and ambiguity

A reconstructed group used only in QC, a sensitivity model, a plot, or an unstated adjustment set
remains unsupported. Directly recorded batch, biological treatment groups, and other unrelated
covariates remain not applicable. A selected report containing supported inclusion and omission
declarations remains ambiguous rather than selecting either operand.

### 3. Do not add an activation-scale question

The fresh baseline used a normalized activation score and missed the released tolerance. Changing
only to corrected-count scale moved the estimate farther from the hidden reference. Adding only
the recovered technical group came close but remained outside the exact `0.05` tolerance. Only
the combined fixed-case change was within tolerance. This recurs the interaction seen in the prior
ambient-state case, but it does not identify one universally governing score, marker set,
threshold, or normalization scale. Those choices remain unsupported.

### 4. Preserve authority and output ceilings

The adapter records only explicit selected-report wording. The existing question still asks the
scientist which adjustment-set treatment governs or retains the unknown. It does not establish
execution, historical intent, group validity, confounding, numerical cause, or scientific
correctness. The module remains question-only and Finding-ineligible. No schema, detector
qualification, execution privilege, metric authority, or public maturity claim changes.

## Alternatives rejected

### Add a benchmark-specific activation-scale rule

Rejected because the scale-only ablation failed and multiple state definitions were already
target-equivalent in the prior finite decomposition. One passing combined arm does not establish a
general score recipe.

### Resolve arbitrary pronouns across a report

Rejected because unconstrained co-reference could connect a technical proxy to the wrong model,
sensitivity analysis, or group. The accepted form is local, explicit, ordered, and finite.

### Leave the fresh report unsupported

Rejected because all premises of the already accepted inclusion operand are explicit in one
paragraph. The missing link is only the bounded `that`/`it` wording, not an implicit scientific
interpretation.

## Acceptance evidence

- The untouched fresh workflow and scale-only ablation each retain zero technical-group questions.
- The group-only and combined ablations each map to
  `include_recovered_technical_group_covariate` and expose exactly the existing scientist question
  with zero Findings.
- A domain-neutral sample-level wording maps to the same operand, while a sensitivity-model-only
  wording remains unsupported.
- The official answer-side grader reports absolute errors of `0.07917562931420985` for the fresh
  baseline, `0.1555092202035674` for scale only, `0.05698746797129339` for group only, and
  `0.03872659574387538` for the combined change, against the exact `0.05` tolerance. Only the
  combined arm is within the released contract.
- All four post-change audits have verified integrity, zero Findings, no project execution, no
  model calls, and byte-identical semantic-lock and HTML-report replay.
- The repository checkpoint passes `987` tests, Ruff, formatting, strict typing, starter/schema
  validation, clean-wheel installation, and the complete handoff verifier.

## Remaining limitation

The rule covers one explicit selected-Markdown co-reference family. It cannot validate the proxy,
discover an unreported group, infer whether a technical variable is confounding, interpret tables
or notebooks, connect arbitrary prose, choose an adjustment set, or attribute a numeric mismatch.
This public-development evidence does not qualify a detector or authorize Findings.
