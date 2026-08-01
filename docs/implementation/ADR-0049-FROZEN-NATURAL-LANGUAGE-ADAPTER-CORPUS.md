# ADR-0049: Expand report wording only from frozen independent declarations

- **Status:** Accepted
- **Date:** 2026-08-01
- **Related decisions:** ADR-0020, ADR-0029, ADR-0030, ADR-0042, ADR-0048
- **Related backlog item:** L06
- **Coordinated schema release:** None; retain public schema 0.18.0

## Context

The selected-report adapter already maps finite explicit prose to normalized scientific-method
operands, but most rules were introduced while repairing one development workflow. L06 requires
broader natural wording without turning the adapter into an open-ended language interpreter or
keying behavior to a benchmark, repository, author, or result.

A non-executing probe of 19 retained fresh-context workflows found two exact report-connectivity
misses. One report explicitly formed poststrata from ancestry, family-history tier, site, and wave,
then weighted each completed-partner cell rate by its share of all roster rows. Another explicitly
omitted uncalled gaps and rejected intervals from ancestry exposure and used the called A/B-length
pulse denominator. Both statements instantiate already accepted operands. No new scientific choice
or governing authority is needed.

The same probe found an important close negative: a structural-copy report described rounded copy
counts and later used a variable called dosage, but did not explicitly connect the rounded calls to
that downstream dosage. That report must remain unsupported.

## Decision

1. Freeze the exact observed excerpts, their full origin-report digests, source spans, expected
   applicability, and qualification exclusion in `evaluation/natural-language-adapter-v1/`.
2. Advance `check:direct-standardization-conditioning-set` and its selected-report adapter to
   version 1.1.0. Admit the existing
   `include_named_availability_variables_in_direct_standardization_cells` operand when one selected
   report paragraph explicitly:
   - forms poststrata or standardization cells from a substantive stratum plus family history,
     site, and wave; and
   - weights the completed-row rate or distribution in each cell by that cell's share of all
     roster or target-population rows.
3. Advance `check:full-map-ancestry-exposure` and its selected-report adapter to version 1.2.0.
   Admit the existing `high_confidence_called_tract_exposure_only` operand when one selected report
   paragraph explicitly:
   - omits or excludes uncalled or masked gaps and rejected or filtered intervals from ancestry
     exposure; and
   - gives the two-state pulse denominator using called `L_A` and `L_B` lengths with `p_A`.
4. Keep the grammar paragraph-scoped and finite. It may contain domain terms needed to identify the
   operand, but it may not inspect corpus case IDs, experiment IDs, origin digests, repository
   names, numeric answers, or benchmark identity.
5. A missing target-population weighting statement or missing exposure-handling statement remains
   unsupported. Competing supported declarations remain ambiguous. Rounded copy-count language
   without an explicit downstream representation link remains unsupported.
6. The adapters continue to record explicit reported declarations only. They do not establish that
   the method ran, that the declaration is scientifically correct, or which listed method governs.
   Their output ceiling remains one bounded scientist question and zero Findings.

## Authority and schema impact

This changes two internal recognition grammars and their content-addressed manifests. It does not
change public record meaning, scientific authority, Finding eligibility, execution privilege,
model privilege, or schema 0.18.0. The decision is accepted under the repository owner's standing
authorization for non-material ADR and schema decisions.

## Acceptance evidence required

- both frozen positive excerpts map to their pre-existing normalized operands;
- removing the target weighting or exposure-handling premise makes the exact case unsupported;
- adding the opposite supported declaration makes the module ambiguous;
- the unlinked rounded-copy report and unrelated sibling checks create no question;
- removing either changed module leaves all sibling module evaluations byte-equivalent;
- missing publication-scope evidence prevents an applicable observation;
- each frozen full-report audit has zero Findings, zero project executions, and zero model calls;
- semantic questions, assertions, disclosures, Findings, and coverage replay exactly; and
- the full corpus-level false-question regression and required handoff gates pass.

## Remaining limitations

This decision adds two wording families, not general natural-language understanding. It cannot
resolve arbitrary pronouns, infer unstated dataflow, connect headings to remote paragraphs, decide
whether a declaration governed the executed analysis, or determine which method is scientifically
appropriate. The corpus is answer-visible fresh-agent development evidence and is ineligible for
detector qualification or general scientific-validity claims.
