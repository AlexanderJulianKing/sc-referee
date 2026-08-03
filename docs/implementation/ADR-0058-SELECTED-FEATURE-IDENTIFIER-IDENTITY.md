# ADR-0058: Add a bounded selected feature-identifier identity candidate

- **Status:** Accepted under the repository owner's explicit request to pursue the first real
  Finding path
- **Date:** 2026-08-02
- **Related decisions:** ADR-0010, ADR-0044, ADR-0045, ADR-0052, ADR-0053
- **Coordinated schema release:** None; retain public schema 0.18.0
- **Finding impact:** Adds an experimental `evaluation_finding_candidate`; production Finding
  permission remains false until a separate detector-promotion decision
- **Execution impact:** None; selected CSV/TSV and H5AD bytes are read by auditor-owned adapters
  and project-authored code is never executed

## Context

The Biermann review workspace contains one selected result table and one selected H5AD artifact
whose feature axes have the same cardinality and 35,638 byte-for-byte matching identifiers, but
twelve identifiers differ. The observed difference is deterministic. It is not yet a Finding
because the audit has no human-authorized statement that the two selected axes must use one exact
identifier set, and the relevant detector has no qualification or promotion record.

Treating high overlap, similar filenames, or date-like values as proof of a shared namespace would
create false accusations. Conversely, leaving the exact comparison only in prose prevents the
ordinary audit from asking the one material question and from producing qualification-ready,
replayable detector output after the scientist answers it.

## Decision

1. Add `calculation-check:selected-feature-identifier-identity-v1`. It accepts one closed
   `sc-referee-feature-identity-v1` declaration from the explicitly selected report or one selected
   calculation-contract sidecar. The declaration names exactly one bounded delimited table,
   identifier column, H5AD artifact, H5AD `var/` field, and the comparison form
   `exact_identifier_set_equality`.
2. Require both named artifacts to be explicit full-digest material inputs. Parse the complete
   declared delimited identifier column and H5AD feature axis without importing or executing
   project code. Identifiers must be strict UTF-8, nonempty, already trimmed, and unique. The
   delimited table is capped at 100,000 rows, 128 columns, and 8 MiB of logical text. The H5AD axis
   is capped at 100,000 identifiers and 4 MiB of text.
3. Compare exact decoded identifier strings as sets. Reordering produces a conformant deterministic
   comparison and no adverse assessment. No case, whitespace, date, alias, Unicode, or
   biological-name normalization is permitted. Duplicate or malformed identifiers, multiple
   declarations, unavailable paths, unsupported H5AD encodings, or incomplete reads abstain.
4. A non-equal comparison initially emits one `MaterialQuestion`: whether exact set equality is a
   requirement for this review, whether different identifiers are permitted, whether an alternate
   mapping governs, or whether the premise should remain unknown. The declaration selects the
   comparison operands only; it is not scientific authority.
5. Extend the linked interaction protocol for the one closed dimension
   `feature_identifier_identity_requirement`. Only an exact human Answer may establish the
   review-scoped equality requirement. The Answer does not establish historical intent,
   producer lineage, execution, which representation is authoritative, or scientific impact.
6. Add `detector:bounded-feature-identifier-identity` as an experimental detector. With an exact
   equality Answer, complete inputs, unique axes, no normalization, and a full deterministic set
   comparison, a mismatch emits `evaluation_finding_candidate`. Conformant comparisons require no
   material question and are not scheduled for adverse detector assessment. A
   different-identifier Answer makes the detector not applicable, an alternate mapping remains
   unsupported, and an unknown Answer remains insufficient semantics.
7. The bounded candidate states only that the two exact selected identifier sets conflict with the
   human requirement governing this review, including the exact left-only and right-only counts.
   It does not infer corruption, spreadsheet conversion, direction of repair, producer lineage,
   execution, affected results, biological meaning, or publication invalidity.
8. The detector manifest remains `experimental`, its qualification reference remains null, and
   `x-production-finding-permitted` remains false. Production admission must reject it. A separate
   held-out qualification, threshold ADR, public qualification report, maintainer decision, and
   promotion ADR are required before changing maturity or Finding permission.
9. Publish a content-addressed calculation registry v13 and capability entries without changing
   schema 0.18.0 or any prior immutable manifest release.

## Alternatives rejected

### Infer a shared namespace from high overlap

Rejected because related but intentionally different artifacts can overlap heavily. Content
similarity may motivate a question but cannot establish the material equality premise.

### Call date-like substitutions corruption

Rejected because the exact bytes do not establish when, why, or by which software the values
changed. The initial detector compares only the declared identifier sets.

### Emit a Finding immediately

Rejected because a successful case proves only the non-maturity admission gates. Public GeneBench
and Biermann development cases are not held-out qualification evidence, and no accepted numeric
threshold or detector promotion exists.

## Acceptance evidence required

- exact equality, reordering, and a corrected pair produce conformant deterministic comparisons
  with no adverse assessment;
- one or more exact set differences produce the bounded MaterialQuestion and, after the human
  equality Answer, one evaluation candidate with all material premises established;
- a different-identifier Answer, alternate mapping, retained unknown, duplicates, whitespace,
  wrong columns or axes, malformed H5AD, multiple declarations, missing selected inputs, and
  over-budget inputs fail closed;
- every finite counterevidence mutation suppresses the candidate;
- the shared non-maturity admission evaluator accepts the candidate shape while production
  admission rejects the experimental state;
- semantic-lock replay preserves observations, questions, Answers, detector results, coverage, and
  zero production Findings;
- no project-authored code executes and no model access occurs after semantic lock; and
- the v13 calculation manifest and capability source set are canonical, packaged, and explicitly
  deny production Finding permission.

## Remaining qualification work

This decision creates a qualification-ready detector, not a promoted detector. Before any real
production Finding can be emitted, the project still needs held-out positive, verified-good,
hard-negative, ambiguous, unsupported, and decisive-counterevidence cases; four blind Stage-1
reviews and two fresh Stage-2 adjudications across two provider families; problem-cluster-aware
metrics and intervals; a predeclared threshold decision; a public qualification report; and a
separate accepted promotion record.
