# ADR-0027: Ask how an average of directional measurement-error rates governs the observation model

- **Status:** Accepted
- **Date:** 2026-07-30
- **Accepted:** Under the repository owner's standing authorization for non-major ADRs that do not
  expand Finding authority, schema meaning, execution privilege, or public maturity claims
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None
- **Related decisions:** Accepted ADR-0019, revised ADR-0020, and Experiment 0025
- **Evidence basis:** Two separately authored, answer-isolated Wright-Fisher workflows using the
  same released inputs, plus a released-data asymmetric-error ablation

## Plain-language summary

Two independent workflow-writing runs made the same important modeling choice. The input reported
only the average of two directional allele-miscall rates. Both workflows used that average as if
the error rate were identical in both directions. Both selected the correct locus, but both
underestimated its selection coefficient outside the answer contract. A released-data control that
split the average into direction-specific rates recovered the target coefficient.

This does not prove that an asymmetric split is universally correct. It proves that treating an
average of directional error rates as one symmetric rate is a real, recurring scientific-method
choice that the auditor should make visible to the scientist. The new check remains a question,
never a Finding.

## Context

The earlier answer-isolated workflow reported locus `A` with approximately `s=0.0462` after using
a symmetric error approximation. Its report explicitly stated that only the average of the two
directional allele-miscall rates was available and that its read likelihood therefore assumed
symmetric errors.

The fresh workflow independently implemented a finite-state haploid Wright-Fisher HMM, correctly
polarized the derived allele before emission, and again treated the reported `0.16` average as the
rate in both directions. It selected locus `A` but returned `s=0.063559`; the released contract is
`0.101256` with absolute tolerance `0.02`. The absolute error is `0.037697`.

The answer-side report and released-data ablation decompose the average using the prompt's
approximately one-percent instrument-error floor and an independently corroborated high-error
direction. The resulting direction-specific rates recover approximately `s=0.101255`. That fixed-
case result establishes numerical relevance in this released task. It does not establish a
universal damage model or authorize the auditor to infer the high-error direction.

## Decision

### 1. Add one atomic measurement-model question

Add `check:directional-measurement-error-interpretation` under the ScientificContract
`measurement_model` dimension. Its closed operands are:

- `reported_average_as_symmetric_bidirectional_error_rate`; and
- `direction_specific_error_rates_from_average_and_directional_constraint`.

The first operand requires an explicit selected-report declaration that a reported average of two
directional error rates is used symmetrically in both directions in the primary observation,
likelihood, or emission model. The second requires an explicit declaration that the reported
average is decomposed into direction-specific rates using an independently or externally supplied
directional constraint such as a baseline error floor or established high-error direction.

### 2. Do not infer the directional constraint

The check may recognize only what the selected report explicitly says. It cannot infer an
ancient-DNA damage process from sample age, nucleotide labels, assay names, model confidence, the
benchmark answer, or numerical agreement. It cannot manufacture a low-direction floor or decide
which direction is larger.

If the scientist has not supplied the governing observation model, the result remains a
MaterialQuestion. Selecting either listed operand creates only a review-scoped compatibility
Disclosure. It does not establish historical intent, execution, numerical causality, or universal
scientific correctness.

### 3. Keep allele orientation separate

Derived-versus-ancestral allele orientation and directional measurement error are distinct. A
workflow can repair allele orientation correctly while still choosing a symmetric error model, as
the fresh workflow did. The existing founder-orientation question remains limited to founder-state
HMM representations and neither module answers or suppresses the other.

### 4. Preserve the existing authority ceiling

The module is selected-Markdown only, question-only, Finding-ineligible, metric-ineligible, and
promotion-ineligible. It executes no project code and adds no schema release, detector
qualification, execution privilege, or public maturity claim.

## Alternatives rejected

### Declare symmetric error scientifically wrong

Rejected because a symmetric model can be appropriate when directional rates are exchangeable or
independently established as equal. The auditor does not possess that authority from report text
alone.

### Add an ancient-DNA C-to-T detector

Rejected because that would hard-code one biological mechanism and encourage implicit scientific
interpretation. The admitted obligation applies to any assay that explicitly reports an average of
directional error rates and then chooses how to represent those rates in an observation model.

### Fold the choice into allele orientation

Rejected because polarization chooses which state is being modeled, while directional error rates
describe how one state is observed as the other. The fresh failure demonstrates that one can be
correct while the other remains unresolved.

## Acceptance evidence

- The two separately authored Wright-Fisher reports map to the symmetric-average operand.
- An explicit direction-specific decomposition maps to the alternative operand.
- A report containing both complete declarations is ambiguous and creates no question.
- QC-only rate plots and a symmetric HMM transition-matrix lookalike create no question.
- The directional-error module and founder-orientation module can coexist as independent
  questions.
- Removing the new module leaves the existing founder module's canonical evaluation unchanged.
- Both real workflow audits produce zero Findings, exactly one new question, and byte-identical
  semantic-lock and HTML-report replay without project execution or post-lock model access.

## Remaining limitation

The adapter recognizes a small explicit Markdown grammar. It does not parse general prose,
notebooks, source-code data flow, non-Markdown reports, implicit assay mechanisms, or arbitrary
measurement-error models. The recurrence uses two independently authored workflows over one public
development task, not an independent real-world corpus. The fixed-case ablation demonstrates
numerical relevance only for that released task and does not qualify a detector or establish which
operand should govern another study.
