# ADR-0077: Contract-bound multiple-testing code-slice detector

- **Status:** Accepted
- **Date:** 2026-08-24
- **Acceptance provenance:** accepted under the standing executive authority Alex King granted the
  supervisor on 2026-08-21 (development-lane ADR/registry mechanics; escalation reserved for public,
  one-way, or zero-FA-weakening changes, none of which apply). Adversarial design review approved
  Revision 2 for build; ND-6 and ND-7 were required as final pre-build narrowings
- **Decision owners:** Alex / sc-referee maintainers
- **Scope:** Development-only multiple-testing code slice 1.0 and scientific-requirement contract
  profile 1.2.0
- **Companion design:**
  `docs/implementation/MULTITEST-CODE-SLICE-1.0-DESIGN-2026-08-24.md`, Revision 2.1,
  `sha256:39b01821aac7058773a60ab93d065703cf31f3f0165779fd21d001612e5c5308`
- **Execution impact:** None; project-authored code remains unexecuted
- **Production impact:** None; no qualification, grant, GrantPin, or production Finding authority is
  installed

## Context

The installed multiple-testing component asks a question but does not prove a contract/code
conflict. The accepted design establishes a separate, conservative code/CSV lane for one exact human
contract: an ordered family of at least three authorized CSV outcomes must receive complete-family
correction. The detector may report a development evaluation candidate only when bounded static
analysis proves an exact uniform family battery and complete per-member conclusions while its finite
correction and counterevidence censuses classify correction coverage as absent or a strict subset.

The design passed adversarial review on Revision 2. Before build, ND-6 closed binary-float conversion
in both exact-Decimal product rules, and ND-7 repaired changelog cross-references. Those changes only
remove candidate eligibility or correct the design record.

## Decision

1. Add scientific-requirement profile `1.2.0` only for
   `check:authorized-complete-family-correction-over-code-test-battery` and candidate
   `complete-correction-over-authorized-outcome-family`. Its authority contains only the authorized
   CSV path, group column, ordered outcome-column family, and the two exact version discriminators.
   Group values and the uniform registered test API are derived.
2. Add the check, adapter, detector, and Finding-profile identities frozen in the companion design at
   version `1.0.0`. Register their binding only in the development projection. It emits evaluation
   candidates and abstentions but zero Findings.
3. The ordered predicate, all registries, ceilings, first abstention codes, structural grammars,
   evidence projection, wording slots, and guard precedence are exactly those in design sections 4
   through 7. Unknown, imported, file-loaded, conditional, dynamic, opaque, unsupported, or
   incompletely censused lineage abstains.
4. Code/CSV/API structure is the only detector evidence. Comments, docstrings, Markdown, reports,
   task text, output labels, format text, and inferred scientific meaning are unavailable. The one new
   identifier channel is closed to the terminal callee slot of `ast.Call`; identifiers in every
   non-callee position are unavailable.
5. The bare-decision and `scipy.stats.t.ppf` mirror product rules use exact `Decimal` values
   constructed from numeric literal source text, or `Decimal(repr(value))` only when source text is
   unavailable. `Decimal(float_value)` is forbidden because its binary expansion can evade exact
   equality with the conventional family-alpha values.
6. Existing pseudoreplication 3.1 implementation modules are copied into new versioned
   multiple-testing modules where needed and are not edited or imported as private implementation.
   Existing multiple-testing recognition, complete-domain, and qualified dependence surfaces remain
   byte- and outcome-immutable.
7. The wording profile is independently versioned and contract-conflict bounded. It states that the
   analyzed source did not enter a recognized correction; it does not infer that no correction was
   applied, that correction was scientifically required, or that the analysis is invalid.

## Accepted residual and protocol deviation

The bare-literal product rule tests only `{0.01, 0.05, 0.1}` as conventional family alphas. It does
not infer arbitrary family alpha. Consequently, unconventional alphas whose quotients are permitted
decision literals, including `0.15 / 3 == 0.05`, `0.5 / 5 == 0.1`, and `0.3 / 3 == 0.1`, remain
convictable by this slice. This is an accepted residual and not evidence that such alphas are
impossible.

Envelope 10 has six positive and nine negative roles rather than the originally amended six/eight
shape because N9 isolates the bare-literal product rule. Its hard stops are zero of nine negative
candidates, zero Findings anywhere, and byte-identical replay for all 15 cases. The additional role
enlarges only the zero-candidate negative surface and does not enlarge candidate or Finding
eligibility.

## Registry and authority isolation

Only development registry bytes and directly enclosing registry/lock/replay digests may change as
enumerated by design section 8.1. A two-registry differential gate must prove that no GrantPin,
grant, qualification, metric-set, threshold-policy, or qualified Finding field derives from the
lane-inclusive registry digest. The qualified pseudoreplication 3.1 adapter, grammar, wording v1/v2,
GrantPin, grant, qualification records, Findings, and `method_conflict_grant_pins.py` remain
byte-untouched. The complete-domain qualified lane remains byte-untouched.

The development-only fact/subject augmentation is implemented in a new integration overlay that
delegates to the frozen shared compiler. The shared `scientific_checks/integration.py` bytes and its
pre-existing qualified semantic dependency closures remain unchanged; the controller selects the
overlay only for the development lane.

## Consequences

- Correction-registry additions are candidate-surface changes, not automatically conservative: a
  newly accepted correction may establish strict-subset coverage and create a candidate. Each future
  addition requires its own review and ADR decision.
- The new lane cannot make production Findings until a later accepted qualification and promotion
  installs an exact grant and GrantPin.
- First-contact recall may be low because assumption checks and any unregistered inferential sibling
  cause abstention. Briefings must not coach authors to avoid those checks.
- Existing `1.0.0` and `1.1.0` scientific-requirement records retain byte-identical resolved values,
  digests, locks, Answers, and error strings.

## Validation

Build acceptance is the complete checklist in companion-design section 13, including every section-9
test gate, the prose tripwire, the deterministic opened-corpus census, two-registry differential
isolation, zero development Findings, unchanged qualified lanes, deterministic replay, and all
repository-required commands. A load-bearing gate that cannot pass as written is a design regression;
the implementation must stop rather than broaden the design.
