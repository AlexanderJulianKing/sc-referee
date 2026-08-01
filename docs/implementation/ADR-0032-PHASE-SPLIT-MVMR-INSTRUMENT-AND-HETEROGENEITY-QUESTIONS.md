# ADR-0032: Add atomic phase-split MVMR instrument and heterogeneity questions

- **Status:** Accepted
- **Date:** 2026-07-30
- **Accepted:** Under the repository owner's standing authorization for non-major ADRs that do not
  expand Finding authority, schema meaning, execution privilege, or public maturity claims
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None
- **Related decisions:** Revised ADR-0020, accepted ADR-0021, and Experiment 0025
- **Evidence basis:** Two independently authored phase-split cis-MVMR workflows and a frozen
  evaluator-owned instrument-construction/heterogeneity-estimator two-by-two

## Plain-language summary

A fresh agent built a careful, reproducible MVMR analysis, but chose six LD-conditional signals
and ordinary full-covariance GLS. Both requested effects missed the released tolerance. The earlier
independently authored workflow used a marginal screening union and a robust fit on LD-whitened
residuals; both fields passed.

A fixed four-cell decomposition showed that neither change works alone. Only the combination of
the marginal union and robust fit reaches both reference values. This establishes two separate
method choices worth showing to the scientist. It does not establish that the passing combination
is universally correct.

## Decision

### 1. Add one phase-split instrument-construction question

Add question-only `check:phase-split-mvmr-instrument-construction` under `measurement_model` with
two finite operands:

1. `phase1_ld_conditional_signal_union_with_phase2_joint_coefficients`; and
2. `phase1_marginal_signal_union_with_phase2_marginal_coefficients`.

The selected-Markdown adapter may observe an operand only when one paragraph explicitly connects
the phase-1 union and its LD representation to the matching phase-2 coefficient representation.
Generic p-value screening, a marginal sensitivity, single-exposure analysis, unlinked phase
descriptions, and an unstated coefficient representation remain unsupported or not applicable.

The question is:

> Which phase-split instrument construction governs the multivariable MR effect for this review?

### 2. Add one residual-heterogeneity-estimator question

Add question-only `check:mvmr-residual-heterogeneity-estimator` under `dependence_structure` with
two finite operands:

1. `zero_intercept_generalized_ivw_or_gls`; and
2. `redescending_robust_m_estimator_on_ld_whitened_innovations`.

The selected-Markdown adapter requires an explicit primary estimator section or the earlier
independently authored report's explicit ordinary-GLS rejection followed by its governing robust
fit. A robust sensitivity with no primary estimator does not establish this operand. Conflicting
governing declarations remain ambiguous.

The question is:

> Which residual-heterogeneity estimator governs the multivariable MR effect for this review?

### 3. Keep LD treatment as a separate existing question

Advance `check:ld-covariance-whitening-before-robust-fit` and its selected-report adapter to
version `1.1.0`. Add only the explicit natural form `Tukey-biweight M-regression ... on
lower-Cholesky-whitened disease residual innovations` to the existing whitened operand.

This check remains separate because estimator family and covariance treatment are different
decisions. A robust cell therefore exposes the new heterogeneity-estimator question and the
existing whitening question; a GLS cell exposes only the heterogeneity-estimator question.

### 4. Preserve unsupported covariance and causal premises

The fresh report sets unavailable cross-protein exposure-error covariance to zero, but the public
task asks only for point estimates and the finite decomposition does not implicate that choice.
ADR-0021's selected-R-Markdown `gencov` adapter is not broadened to generic Markdown.

Neither new module validates instruments, chooses a p-value threshold, proves winner's-curse
control, establishes phase independence, diagnoses horizontal pleiotropy, validates the LD
reference, or identifies the correct estimator. Numeric agreement is evaluation evidence only.

### 5. Preserve authority and output ceilings

Both new modules and the revised existing module are question-only and Finding-ineligible. They
inspect explicit selected-report text, return the finite choice to the scientist, and may preserve
the choice as unknown. They do not execute project code, infer historical intent, establish
scientific correctness or numerical cause, qualify a detector, or change any public schema,
metric, execution privilege, or maturity claim.

## Alternatives rejected

### Add one combined benchmark-compatible recipe

Rejected because instrument construction and heterogeneity response are separable scientific
decisions. Their fixed-case interaction does not justify treating the combination as one universal
method.

### Treat LD-conditional signal selection as demonstrated error

Rejected because it is a plausible method with assumptions different from a marginal tag union.
The benchmark answer does not establish that it is wrong for other loci or estimands.

### Add a cross-exposure covariance question from this Markdown report

Rejected because that choice did not move the requested point estimates in the reported
second-order calculation, and ADR-0021 deliberately admits a different closed R-Markdown call
surface. One report is insufficient to broaden that adapter.

### Merge GLS-versus-robust choice into the LD-whitening question

Rejected because whether to use a robust estimator and how a robust estimator handles correlated
residuals are independent. Combining them would make scientist answers ambiguous and prevent
modular extension.

## Acceptance evidence

- The fresh conditional-GLS workflow is byte-reproducible and returns PROTA `0.4014409387` and
  PROTB `0.3647942733`, with absolute errors `0.1082857934` and `0.1427215067`.
- Marginal-GLS returns `0.3269302012` and `0.3315084093`; conditional-robust returns
  `0.4006839265` and `0.3719899837`. Both cells fail both released tolerances.
- Marginal-robust returns `0.2900914882` and `0.2275588522`, with absolute errors
  `0.0030636571` and `0.0054860856`; both fields pass.
- Post-change audits expose the two new questions in both GLS cells and both new questions plus
  the existing LD-whitening question in both robust cells. The untouched fresh workflow exposes
  its conditional-instrument and GLS operands. The earlier independent robust workflow exposes
  the robust-estimator and LD-whitening operands while its less explicit instrument wording stays
  unsupported.
- Exact positives, conflicting declarations, sensitivity-only and single-exposure hard negatives,
  robust/whitening coexistence, and a four-cell module-independence regression pass.
- The commit-pinned MVMR, MVMR-cML, and mr.raps repositories acquire no question. MR-tutorial
  retains only its pre-existing ADR-0021 covariance question.
- The six MVMR development audits and four independent repository controls have verified
  integrity, zero Findings, no project execution, zero model calls, and byte-identical semantic
  locks and HTML-report replay.
- An independent fresh-context `scientific-audit` skill run on the untouched workflow reaches
  exactly the conditional-instrument and generalized-IVW/GLS questions, presents both finite
  alternatives plus retain-unresolved, records no Answer, and preserves zero Findings. Audit
  `audit:72d115c5400140e0b17a2d8c04581b21` and its replay retain verified integrity, identical
  semantic-lock digest `sha256:d543e4ad5bdb6f97d3e7a16942625d595ac0370a8bf65f7af9f4a96c5932e95a`,
  identical semantic records, assessments, coverage, and HTML report, with project execution
  disabled and zero model calls.
- The repository checkpoint passes `1013` tests, Ruff, formatting, strict typing, and
  starter/schema validation, plus the complete clean-wheel handoff verifier.

## Remaining limitation

The new rules cover explicit phase-split selected-Markdown declarations only. They do not parse
arbitrary MR code, validate signal independence, determine instrument strength or validity,
choose marginal versus conditional representations, identify localized pleiotropy, validate SNP
ordering for Cholesky innovations, select robust tuning constants, or generalize fixed-case numeric
causality. Public GeneBench development evidence and unauthenticated local agents cannot qualify a
detector or authorize Findings.
