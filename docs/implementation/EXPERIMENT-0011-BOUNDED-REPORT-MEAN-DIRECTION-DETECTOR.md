# Experiment 0011: Bounded report/mean-direction consistency detector

- **Status:** Active experimental detector; no production Finding permission
- **Date:** 2026-07-29
- **Authority:** SA-FR-031, SA-FR-033, SA-FR-034, SA-FR-101, SA-NFR-014,
  accepted ADR-0010, and accepted ADR-0017
- **Scope:** One explicit directional sentence on the resolved Markdown publication surface and
  one exact statically linked Python two-group raw mean-difference computation

## Purpose

Exercise the first real, domain-neutral detector over normal repository audits without broadening
scientific interpretation or granting experimental output Finding authority. The detector checks
one demonstrated source-level contradiction: an exact report writer carries a raw two-group
mean-difference result into the selected report path while a literal sentence on that path states
the opposite direction for the same group labels and outcome-column label.

## Exact applicability envelope

The detector is scheduled once for every final directional Claim extracted by the bounded Markdown
grammar. It is applicable only when all of the following are true:

- the Claim is an independently verified explicit `increased` or `decreased` sentence;
- the Claim has exactly one result linked by the bounded literal-alignment profile;
- the link records exact static result-Artifact flow into a writer for the selected report path;
- the linked result is a finite scalar recomputed by the auditor-owned two-group raw
  mean-difference verifier;
- the producing Operation contains exact outcome-column, left-group, and right-group literals;
- the sentence subject, comparison, and object labels match those literals exactly after only
  case and whitespace normalization; and
- no opposite-direction final Claim exists on the same publication surface for the same literal
  subject, object, and comparison.

The detector does not require a scientific measurement-scale interpretation. Its statement is
limited to the raw values in the exactly named column and the exact source-level writer path. It
does not establish which analysis the authors intended, whether the checked source was executed,
whether the biological conclusion is false, or whether a different analysis would agree.

## Finite counterevidence protocol

Every applicable or candidate-producing evaluation records these closed checks:

1. **Literal report conflict:** search the other extracted final Claims on the same selected
   surface for the same normalized subject, object, and comparison with the opposite direction.
   A match suppresses the candidate and makes the target semantically insufficient.
2. **Exact source-flow binding:** inspect the Claim lineage and referenced Operations for one
   unique bounded result alignment and static result-Artifact flow into the selected report
   writer. Unavailability blocks candidate production.
3. **Group orientation:** compare the sentence's literal subject/comparator order with the
   Operation's left/right group literals and the ObservedResult comparison/orientation slots.
   Conflict or unavailability blocks candidate production.
4. **Raw value-column binding:** compare the sentence's literal object with the Operation's exact
   outcome-column literal and require the supported raw mean-difference implementation.
   Conflict or unavailability blocks candidate production.

No open-ended search, model interpretation, repository execution, package-default inference, or
scientific convention is part of the protocol.

## Output ceiling

A sign conflict emits `DetectorResult.state: evaluation_finding_candidate` with
`detector_maturity: experimental`. The production admission service cannot admit that state and the
detector manifest does not permit Findings. Agreement emits
`no_issue_detected_within_coverage`; unresolved evidence emits `insufficient_semantics`; constructs
outside the exact scalar/operation profile emit `unsupported_path`; and a sibling report conflict
records decisive counterevidence and suppresses the candidate.

## Exit evidence

- positive, covered-negative, hard-negative, ambiguous, unsupported-path, and decisive
  counterevidence fixtures terminate in their declared states;
- mutation tests prove manifest/implementation and deterministic-input changes fail closed or
  change exact output identity;
- an end-to-end normal audit emits the experimental result but no Finding, does not execute project
  code, and replays byte-for-byte from the semantic lock;
- the public capability matrix names the exact cross-profile experiment, experimental maturity,
  absent qualification, and a non-Finding output ceiling; and
- the static report visibly separates experimental detector output from admitted Findings.

## Remaining coverage limitation

This profile covers only the exact bounded Markdown sentence grammar, exact bounded Python raw
mean-difference form, exact literal label alignment, and exact static report-writer flow. It does
not cover notebooks, R, transformed scales, ratios, regression coefficients, adjusted estimates,
plots, tables, prose qualifications beyond the closed sibling-conflict check, runtime execution,
or scientific correctness. Synthetic fixtures are development evidence only; no real-corpus
qualification or detector promotion is claimed.
