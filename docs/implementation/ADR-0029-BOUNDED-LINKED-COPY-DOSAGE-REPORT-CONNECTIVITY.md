# ADR-0029: Connect one bounded multi-paragraph copy-dosage declaration

- **Status:** Accepted
- **Date:** 2026-07-30
- **Accepted:** Under the repository owner's standing authorization for non-major ADRs that do not
  expand Finding authority, schema meaning, execution privilege, or public maturity claims
- **Target architecture specification:** `0.6.0`
- **Coordinated public schema release:** None
- **Related decisions:** Revised ADR-0020, accepted ADR-0024, and Experiment 0025
- **Evidence basis:** A fresh answer-isolated covered-good structural-copy workflow whose exact
  selected report split one direct continuous dosage declaration across bounded report sections

## Plain-language summary

A fresh agent independently produced a passing structural-copy analysis. It explicitly retained a
continuous copy index rather than rounding, learned the named copy index with Ridge regression,
and used calibrated dosage for that same named structural target in the downstream clinical model.
The original ADR-0024 adapter nevertheless classified the check as not applicable because it
required the complete declaration inside one paragraph.

That is a report-connectivity miss, not a new scientific choice. This ADR permits one tightly
bounded document-level join of those three explicit statements. It does not add a calibration-
pooling question: the fresh agent chose group-specific calibration, so the earlier failed pooled
choice did not independently recur.

## Decision

### 1. Add a bounded document-scoped rule to the existing dosage check

Advance `check:classifier-derived-copy-dosage-representation` and its selected-report adapter to
version `1.2.0`, preserving the check ID and the three ADR-0024 operands. The direct-continuous
operand may additionally be observed when one immutable selected Markdown report contains all of
the following explicit connected statements:

1. a continuous copy index is retained for dosage calibration rather than rounded;
2. a literally named copy target's copy index is learned with Ridge regression; and
3. a downstream model includes calibrated dosage for that exact same literal target.

The target-name backreference must resolve exactly. A calibration statement for one target and a
downstream statement for another cannot connect. The rule has finite character-distance ceilings,
and its evidence span is localized from the first representation statement through the bound
downstream statement rather than citing unrelated report sections.

### 2. Preserve the paragraph-scoped default

All existing selected-report rules remain paragraph-scoped. Document scope is explicit in the
manifested rule and is not a general license to combine scientific fragments across a report.
Method-only, QC-only, mismatched-target, incomplete, and conflicting representations abstain.

### 3. Do not add a pooling or stratification question

The fresh workflow independently chose group-specific direct calibration and placed all four
released fields within tolerance. That is a covered-good recurrence for direct continuous dosage,
not recurrence of the earlier pooled-calibration failure. The accepted limitation remains:
pooling versus group-specific calibration is unsupported until both choices recur in independent,
report-connected workflows with a finite scientist-governed answer set.

### 4. Preserve the output and authority ceilings

The adapter records only explicit selected-report wording. It does not establish execution,
historical intent, calibration validity, transportability, numeric cause, or scientific
correctness. The check remains question-only and Finding-ineligible. No schema, detector
qualification, execution privilege, metric authority, or public maturity claim changes.

## Alternatives rejected

### Treat the fresh passing workflow as proof that group-specific calibration is required

Rejected because one successful choice is not scientist authority or a universal rule, and the
fresh run did not reproduce the alternative pooled choice.

### Join arbitrary method fragments anywhere in a report

Rejected because unrelated targets or sensitivity analyses could be conflated. The admitted rule
requires the same literal copy target, a named direct regression, an explicit non-rounding
continuous representation, a downstream use, and finite distances.

### Leave the check not applicable

Rejected because all material premises of the already accepted ADR-0024 operand are explicit and
independently checkable in the selected report. The missing piece was bounded text connectivity,
not scientific interpretation.

## Acceptance evidence

- The fresh report maps to `direct_continuous_calibrated_copy_dosage` and creates exactly one
  MaterialQuestion with zero Findings.
- Its `n_calibrated_carriers`, support code, expression coefficient, and clinical coefficient all
  pass the released answer contract after pre-grade semantic lock and model-free replay.
- Existing posterior, ancestry-specific direct, pooled direct, and ancestry-specific posterior
  reports retain their original operands.
- A mismatched calibration/downstream target and a calibration-QC-only report remain unsupported.
- Unrelated report prefixes and suffixes are excluded from the linked evidence span.
- Every actual-workflow audit replays semantic-lock and HTML-report bytes exactly without project
  execution or post-lock model access.

## Remaining limitation

The linked grammar covers one explicit Markdown wording family and one literal target-name join.
It does not resolve pronouns, aliases, tables, source-code dataflow, notebooks, arbitrary report
sections, model execution, or multiple competing copy targets. It does not determine whether
continuous direct calibration, posterior expectation, hard state, pooling, or stratification is
scientifically appropriate for another analysis.
