# Experiment 0052: Generic denominator-relation development smoke

- **Status:** Complete, development-only
- **Date:** 2026-08-04
- **Related decision:** ADR-0065
- **Qualification use permitted:** No
- **Held-out material accessed:** No
- **Project-authored code executed:** No
- **Finding authority:** None

## Question

Can one subject-neutral selected-report adapter recognize the same closed denominator-domain
conflict across independently renamed workflows and emit the existing ordinary DetectorResult,
without task identities, case identities, answer values, or subject-area labels in its production
grammar?

## Change under test

The new `check:complete-domain-exposure-denominator` has two opaque canonical operands:

- `complete_declared_domain_exposure`; and
- `retained_observed_subset_exposure_only`.

It applies only when the selected report explicitly identifies a primary rate or spacing target,
the retained observed subset, and whether missing, filtered, masked, uncalled, or low-confidence
parts of the declared domain enter the denominator. The check does not infer the governing domain,
missing states, execution, causality, or scientific correctness. A pre-analysis method contract
supplies the required operand.

## Synthetic development matrix

The end-to-end tests freeze the requirement, run the real non-executing audit, and replay it across:

- three conflicting reports from acoustic-survey, microscopy-transect, and environmental-timeline
  vocabularies;
- two corrected reports from orbital-timeline and route-survey vocabularies;
- one explicit two-method ambiguity;
- one triggered but opaque denominator description; and
- one unrelated retention report.

The three conflicts emit `evaluation_finding_candidate`; the two corrected variants emit
`no_issue_detected_within_coverage`; and ambiguous, opaque, and unrelated cases emit no adverse
DetectorResult. Every case emits zero Findings and executes no project code.

## Label-visible pilot smoke

After the grammar and synthetic controls were implemented, two already label-visible v1 pilot
positives were copied into temporary development workspaces. A new generic requirement lock was
created before each workflow copy, but the implementer had already seen both source cases. This
ordering prevents accidental use of the old check lock; it does not make the examples prospective
or qualification-eligible.

Both audits produced one applicable normalized observation and one development-only
`evaluation_finding_candidate`:

| Development case | Observation digest | DetectorResult | Deterministic input digest |
|---|---|---|---|
| `case:64089f0b79fe1406456b` | `sha256:c984eca9fb0237d84b1f7cf7cb537a754ea545f82e15bcba4b8f9488439cc1b9` | `detector-result:a9d4666d702daf84f18b` | `sha256:a01471396dd453b8173ac6070fe1ad728310a03aec7f271a62b425f54dee4f03` |
| `case:fdf67ba59425e6a7620d` | `sha256:1eff7aaab7c2c27ed68a37c1f28d17fa56d8c382241f4015001ad6b0dff14e39` | `detector-result:159093e9c4ba371a5a9b` | `sha256:47c018d8f2a1eff8999085c74dfdbefc979699029082cf1a5ef80e08ef8184d8` |

The common check-manifest digest was
`sha256:0be7441b6d24dd18584c0a340f57c7f9d74148d62e3d69aa58ded1f5dcf2649e`.
Each result compared required `complete_declared_domain_exposure` with observed
`retained_observed_subset_exposure_only`. The old v1 pilot artifacts and outcomes were not changed.

## Interpretation boundary

This demonstrates recognition and deterministic evaluation on development examples. It is not an
error-rate estimate, independent qualification, production Finding, or evidence about all
workflows. The two pilot cases were selected after their labels were known, and the adapter was
developed with access to their text. The sealed v1 held-out block remains unopened.

Any qualification claim requires a new detector/check/adapter freeze, opaque assignments, fresh
independent cases, canonical issue classes, exact selected-result provenance, pilot-frozen numeric
thresholds, held-out metrics, and a maintainer promotion for this exact binding.
