# ADR-0061: Stage a per-binding method-conflict promotion path

- **Status:** Accepted for implementation of a nonpublic schema candidate and fail-closed
  authority resolver
- **Date:** 2026-08-03
- **Related decisions:** ADR-0011, ADR-0022, ADR-0037, ADR-0042, ADR-0060
- **Coordinated schema candidate:** `0.19.0`
- **Finding impact:** None until the candidate schema is accepted and an exact binding has real
  pilot-informed thresholds, independent qualification evidence, and maintainer promotion
- **Execution impact:** None

## Context

The generic method-conflict detector is now version `0.3.0` and each registered scientific check
has a content-addressed production binding. Immutable public schema v0.18.0 can describe only the
historical `0.2.0` typed static-method qualification freeze. Its qualification metrics and
DetectorQualification records also fix the numeric policy to
`deferred_until_pilot_threshold_adr`, which correctly makes a promoted outcome invalid.

The missing representation must not be solved by editing v0.18.0, treating public development
cases as qualification evidence, placing authority in extensions, or granting all scientific
checks the maturity of one qualified binding.

## Decision

1. Preserve v0.18.0 byte-for-byte. Build a reproducible, explicitly nonpublic v0.19.0 schema
   candidate from that baseline.
2. Add `typed_static_method_conflict_v2`, bound to detector version `0.3.0`. Its method binding
   retains the independent qualification adapter identity and separately binds the exact
   production-registry binding digest. The historical v1/v0.2 branch remains valid and distinct.
3. Add an exact `binding_scope` to QualificationMetricSet and DetectorQualification. The scope
   binds the check, production binding, detector manifest, static profile, and independent
   qualification adapter. A v0.3 method-conflict promotion cannot omit it.
4. Replace the deferred-policy-only shape, in the candidate schema only, with a closed choice:
   either the existing deferred sentinel or a content-addressed pilot-informed threshold policy.
   The latter records its decision ADR, pilot evidence references, freeze chronology, minimum
   counts, and finite metric requirements. It is not itself a promotion.
5. Permit a thresholded metric set to say `promotion_permitted: true` only when it is held-out,
   promotion-evidence eligible, binding-scoped, and bound to the pilot-informed policy. A promoted
   DetectorQualification additionally requires one exact metric-set reference, all safety gates,
   static-proof disclosure, independent adjudication references, and maintainer approval.
6. Add a deterministic authority resolver. It returns a grant only when the qualification,
   metric set, threshold policy, detector manifest, and production binding agree exactly and every
   threshold passes. Missing, deferred, public-development, excluded, inestimable, mismatched, or
   nonpromoted inputs return no grant.
7. Keep the authority resolver disconnected from the production controller while the schema is a
   candidate and the installed grant registry is empty. It may project an evaluation candidate to
   a production-shaped candidate only when explicitly supplied a successfully resolved grant and
   the exact replayed work packet whose digest and target-question check identity prove that the
   DetectorResult belongs to that grant's binding. Caller-selected binding identity alone is not
   authority.
8. Migrate v0.18 records fail closed: add null binding scopes, retain the deferred threshold
   sentinel, clear storage manifests after canonical bytes change, and create no qualification,
   threshold, maturity, or Finding authority.

## Why the schema remains a candidate

No independent pilot block or threshold ADR exists yet. Accepting a promotion-capable public
schema as the active runtime schema before that decision would imply that an unresolved policy is
settled. The candidate closes the engineering representation gap and makes the remaining external
gate exact without inventing its values.

## Promotion acceptance gate

For each binding independently, promotion still requires all of the following:

- a pre-case v0.3 profile and opaque assignment;
- fresh held-out error, corrected, valid-alternative, hard-negative, ambiguous, unsupported, and
  renamed-form cases;
- four blind Stage-1 reviews across two provider families and two fresh Stage-2 adjudications;
- independent static proof and fresh Stage-3 comparison with material disagreements excluded;
- a pilot-informed threshold ADR frozen before held-out labels are observed;
- recomputed clustered metrics satisfying every frozen count and metric threshold;
- a public qualification report and explicit software-maintainer promotion; and
- an accepted forward public schema release plus an installed content-addressed grant.

Until all items exist, every method-conflict binding remains experimental and
`production_finding_permitted` remains false.
