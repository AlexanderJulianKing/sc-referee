# Experiment 0040: Frozen natural-language adapter expansion

## Question

Can existing selected-report checks recognize independently observed ordinary wording through a
frozen, parameterized conformance corpus without weakening ambiguity, unsupported-input,
scope-evidence, no-execution, replay, or Finding boundaries?

## Baseline probe

Nineteen retained fresh-context scientific workflows were audited non-executingly with an exact
selected `report.md`. Thirteen existing checks produced their bounded questions. Two reports
contained explicit declarations for accepted operands but remained unsupported:

- the carrier-risk report formed exact ancestry/family-history/site/wave poststrata and weighted
  each completed-partner cell rate by its share of all roster rows; and
- the recent-pulse report excluded uncalled gaps and rejected intervals from ancestry exposure and
  used the called-length `p_A`, `L_A`, and `L_B` denominator.

A separate structural-copy report mentioned rounded copy counts and later a dosage variable without
stating that the rounded calls were the downstream dosage. It remained unsupported and was frozen
as a close negative. All 19 probes produced zero Findings and did not execute project code or call a
model.

## Change

ADR-0049 adds one paragraph-scoped rule to each of the two existing selected-report profiles. The
normalized operands, role bindings, question wording, output ceiling, scope join, counterevidence,
and prohibited inferences are unchanged. The content-addressed release manifest binds the new
grammar versions.

The new `evaluation/natural-language-adapter-v1/manifest.json` freezes three exact excerpts with
their content digests, origin-report digests, source spans, expected states, and explicit exclusion
from qualification. Adapter grammars contain no corpus identity fields.

## Tests added

`tests/test_natural_language_adapters.py` provides a parameterized conformance suite covering:

- both independently observed positive wordings and the unlinked-dosage close negative;
- one-premise wording mutations;
- competing-declaration ambiguity;
- module removal and sibling isolation;
- missing publication-scope counterevidence;
- corpus identity and mutation rejection;
- absence of corpus identity keys from adapter grammar projections; and
- full-audit question ceilings, zero Findings, no execution, no model calls, and exact replay.

## Result

The complete 1,321-test suite passes. Both frozen positive excerpts map to their pre-existing
operands and create only the corresponding bounded scientist question. The unlinked-dosage report,
one-premise mutations, and unrelated sibling checks create no question. Competing declarations
remain ambiguous, missing publication scope abstains, and removing either changed module leaves
all sibling evaluations byte-equivalent. Every corpus audit has zero Findings, executions,
execution authorizations, and model calls, and its semantic outputs replay exactly.

The full handoff verifier also passes: Ruff and both strict mypy suites are clean; 79 public schema
examples validate at schema 0.18.0; all 26 active module baselines, 10 retained sources, and 103
ledger cases remain complete and qualification-ineligible; both clean wheels build and install;
and the walking-skeleton, interaction, semantic-lock, replay, RO-Crate, storage, capability, and
schema-migration checks pass through schema 0.18.0.

## Remaining limitations

- Only two new natural wording families are admitted.
- The frozen examples are benchmark-derived fresh-agent reports, not representative natural-science
  prose and not qualification evidence.
- Explicit report wording does not prove execution, lineage, primary-analysis status, or
  scientific correctness.
- Source-language breadth remains L07 and cross-cell connectivity remains L08.
