# Experiment 0047: Generic contract-bound ReviewCase candidate

- **Status:** Implemented as an experimental, nonpromoting candidate
- **Date:** 2026-08-03
- **Governing decision:** Accepted ADR-0060; active public schema v0.18.0
- **Candidate:** `detector:bounded-analysis-method-conflict` version `0.3.0`
- **Finding authority:** None

## Question

Can one pre-analysis human selection from any installed scientific-check manifest bind
automatically to a later exact workflow observation, compile into one small domain-neutral review
case, and reach the existing evaluation-only conflict detector without benchmark identity or a
post-audit scientist Answer?

## Change

The claimless method-contract lifecycle now accepts `scientific_check_requirement_v1`, containing
only one installed `check_id` and one published `candidate_id`. The semantic lock freezes the full
check manifest, candidate operand, dimension, comparison form, post-hoc ledger identity, and human
Answer chain. A later audit verifies unchanged task bytes and registry identities before binding
the parent requirement to one exact matching analysis question as a `prior_scientist_record`.

The method-conflict registry now contains an explicit content-addressed evaluation binding for all
20 substantive installed scientific checks. Report-only, static-only, and corroborated
report-plus-static evidence planes use the same detector. The detector compiles its authority,
operands, selected-analysis path, finite applicability checks, counterevidence, unknowns, and
output ceiling into an internal `ReviewCase` with a replay-stable digest.

## Version and qualification boundary

Adding the ReviewCase projection changes detector output and implementation identity, so the
candidate advances from `0.2.0` to `0.3.0`. The immutable v0.2 pre-case freeze remains historical
and cannot qualify v0.3. The active v0.18 typed qualification profile admits only the historical
v0.2 identity and its numeric-threshold policy cannot encode a promotion. A new forward-only
qualification schema and a new pre-case freeze are therefore required before any v0.3 envelope
can be promoted.

All v0.3 bindings remain `production_finding_permitted: false`; exact conflicts remain
`evaluation_finding_candidate`. Public GeneBench cases are development-only and excluded from
qualification.

## Evidence and result

Tests cover claimless creation, authority replay, task and registry drift, not-applicable binding,
report-only and static-only conflicts, covered negatives, all ten finite suppressors, ReviewCase
canonicality, all 20 binding identities, and a production-source benchmark-identity firewall.

The experiment establishes a generic recognition and comparison substrate. It does not establish
accuracy, held-out qualification, promotion, or a production Finding.
