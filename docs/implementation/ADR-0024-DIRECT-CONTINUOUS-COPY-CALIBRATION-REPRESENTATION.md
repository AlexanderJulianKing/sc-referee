# ADR-0024: Represent direct continuous copy calibration separately from classifier expectation

- **Status:** Accepted
- **Date:** 2026-07-30
- **Accepted:** Under the repository owner's standing authorization for non-major ADRs that do not
  expand Finding authority, schema meaning, execution privilege, or public maturity claims
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None
- **Related decisions:** Accepted ADR-0019, revised ADR-0020, and Experiment 0025
- **Evidence basis:** Experiment 0025 structural-copy calibration ablations

## Plain-language summary

A continuous copy-number exposure can be produced in at least two materially different ways. A
classifier can estimate probabilities for copy states 0, 1, and 2 and report their posterior
expectation. Alternatively, a calibration regression can predict copy count directly on a
continuous scale. Neither is an integer hard call, but they are not the same measurement model.

The first version of `check:classifier-derived-copy-dosage-representation` offered only hard state
and posterior expectation. That closed answer set could not represent a scientist who intended
direct continuous calibration. This ADR adds that third representation while keeping calibration
pooling or stratification as a separate, still-unsupported choice.

## Context

The fresh structural-copy workflow in Experiment 0025 used pooled multinomial classifiers and
posterior expected copy count. It matched the carrier count and support code but missed the public
expression and clinical tolerances. A fixed-case ablation replaced only the upstream dosage-
calibration regime with direct continuous RidgeCV calibration within ancestry groups; all four
answer fields then fell within contract.

Two reverse controls prevent an overbroad conclusion. A pooled direct RidgeCV calibration and an
ancestry-stratified posterior-expectation classifier each still missed the clinical tolerance.
Therefore the experiment does not establish that direct regression is universally preferable, or
that representation alone explains every downstream result. It does establish that posterior
expectation and direct continuous calibration are distinct scientist-governed representations
that the existing finite question must not collapse.

## Decision

### 1. Extend the existing representation question

Keep the stable check ID `check:classifier-derived-copy-dosage-representation`, but advance its
check and selected-report adapter versions to `1.1.0`. The historical ID remains stable for replay
and release-manifest continuity; user-facing wording refers to calibrated copy-number
representation rather than classifiers alone.

The `measurement_model` question has three closed operands:

- `integer_hard_copy_state_as_numeric_dosage`;
- `continuous_posterior_expected_copy_dosage`; and
- `direct_continuous_calibrated_copy_dosage`.

The third operand means that a regression or other explicitly named direct calibration model
predicts copy count continuously for the downstream quantitative exposure. It does not imply a
particular regression family, penalty, group structure, or threshold.

### 2. Require an exact selected-report declaration

The selected-Markdown adapter may recognize direct continuous calibration only when one paragraph
states both that continuous calibrated copy dosage is the primary, full-cohort, or downstream
representation and that a linear, ridge, or regression calibration model produced that dosage.
Merely fitting a regression for QC, plotting continuous values, reporting calibration accuracy, or
using a directly measured continuous assay value cannot establish the operand.

Conflicting supported declarations remain `ambiguous`. Method-like calibration wording without a
complete downstream representation declaration remains `unsupported`.

### 3. Do not conflate representation with calibration pooling

Whether one calibration model is pooled across transport groups or fitted separately within
ancestry, site, batch, or another declared group is an independent choice. The two-by-two
structural ablation shows that pooling and output representation can vary independently. This ADR
does not add a pooling question, infer that any grouping is scientifically required, or describe
the direct operand as group-specific.

A future pooling module requires its own recurring explicit representations, scientist authority,
and finite positive, good, ambiguous, hard-negative, removal, sibling, and replay controls.

### 4. Preserve the question-only ceiling

The expanded module cannot choose a representation, prove that a reported calibration executed,
validate calibration labels or transportability, establish a numeric cause, or emit a Finding.
Matching and conflicting scientist Answers remain deterministic Disclosures. No public schema,
detector maturity, qualification status, or execution privilege changes.

## Alternatives rejected

### Treat every non-integer dosage as one continuous representation

Rejected because posterior class expectation and direct continuous regression encode different
model targets and can yield different exposures even when both lie between 0 and 2.

### Combine direct calibration with ancestry stratification in one operand

Rejected because the two choices cross independently. A composite operand would repeat the
offset/scale and fraction/time conflations corrected earlier in the program.

### Add a calibration-pooling question now

Rejected because the frozen report does not explicitly declare its pooling policy and there is not
yet an independently recurring, report-connected pair of supported pooling declarations. The
conservative result is an explicit coverage limitation.

## Acceptance evidence

- Exact hard-state, posterior-expectation, and direct-continuous declarations each produce their
  own operand through the common audit interface.
- Any two supported declarations are ambiguous; QC-only regression, plotted probabilities,
  under-specified cross-paragraph wording, and unrelated dosage uses do not produce a question.
- Matching and conflicting Answers for the new operand compile only to replay-stable Disclosures.
- The frozen posterior-expectation workflow, successful direct-continuous ablation, pooled-direct
  reverse control, and stratified-posterior reverse control remain zero-Finding audits.
- Unrelated and sibling scientific-check controls gain no new question.

## Remaining limitation

The v1.1 adapter recognizes three explicit selected-Markdown representation declarations. It does
not parse arbitrary calibration source code, decide between valid model families, validate
cross-validation or calibration transport, determine whether pooling or stratification governs,
or attribute a numeric mismatch. Those boundaries remain unknown or unsupported rather than
Findings.
