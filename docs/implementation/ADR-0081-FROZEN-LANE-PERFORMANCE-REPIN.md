# ADR-0081: Performance-only re-pin of the byte-frozen multiple-testing v3 and v3.3 lanes

- **Status:** Accepted
- **Date:** 2026-09-02
- **Acceptance provenance:** Alex authorized touching the byte-frozen multiple-testing lanes for
  performance on 2026-09-02, on the condition that outputs be proven identical before the re-pin
- **Decision owners:** Alex / sc-referee maintainers
- **Scope:** `code_csv_multiple_testing_dataflow_v3.py` and
  `code_csv_multiple_testing_dataflow_v3_3.py`
- **Execution impact:** None; project-authored code remains unexecuted
- **Production impact:** None. Every classification, abstention reason, corrected-position list,
  authorized count, evidence span, admission-census row and recorded module evaluation digest is
  unchanged. What moves is the raw bytes of two implementation files, which this ADR re-pins.

## Context

One 3.4 analyzer call on a 90-line `analysis.py` took 1.03 s and its frozen 3.3 twin 0.62 s. A
profile of one call attributed about 82% of the run to a single expression: `_precise_record_member`
asked, for one name at a time, whether the analysis scope contains any `name[...] = `,
`name.attr = `, an annotated or augmented form of either, or a `del` of one, and answered by
walking every statement in the scope from scratch. The answer depends on the scope, not on the
name, so a 90-line file produced about 2.3 million `ast.walk` steps for one analysis. The same
expression is present in both byte-frozen lanes, and the 3.4 layer runs the 3.3 pipeline which runs
the v3 pipeline, so one 3.4 call paid the cost three times over.

The evidence suites feel this directly. The multiple-testing tier took 1:45:19 serially and the
whole suite 47:51 at four workers, which is long enough that an audit round is bounded by the test
clock rather than by the work.

Nothing about that expression is load-bearing for what the analyzer decides. It is a scope-level
property that was being computed once per question instead of once per scope.

## Decision

1. In both byte-frozen lanes, collect the set of names written through as a member anywhere in the
   engine's scope once per `_MtEngine`, on first use, and answer `_precise_record_member`'s
   question as a membership test against that set. The set is exactly the names the per-name walk
   it replaces would have matched: the same four statement kinds, the same target lists, the same
   `Subscript`-or-`Attribute`-over-`Name` shape. The engine's scope is the statement tuple it was
   constructed with and is not rebuilt while it runs, so one collection answers every question.
   No other line of either frozen lane changes.
2. Re-pin the two lanes' digests in the two anchor tests that carry them, and regenerate the
   scientific-check release registry and the capability maturity ledger from the live bytes.
3. This is a performance-only re-pin. It grants no new admission, adds no reason, moves no row,
   and changes no Finding eligibility, authority, execution privilege, or public capability claim.

An in-process memo of the frozen twin's results was built, measured and then withdrawn by the
custodian on the same day. Its only measured benefit was inside the test suites, because a real
audit analyzes each source once, and AGENTS.md forbids process-local state in deterministic logic.
The frozen-lane change below stands on its own and carries no such state.

## Files changed and digests

| File | Old SHA-256 | New SHA-256 |
| --- | --- | --- |
| `src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3.py` | `498bf5c22305270fe64ed1ef73b7ac8a7a2637ce4f64520e8d9ca4ac15166618` | `0388b4a1d3a28b7549af85362d0d4e7f13ffc2b4807dc129d242c4927870c0d1` |
| `src/sc_referee/scientific_checks/code_csv_multiple_testing_dataflow_v3_3.py` | `c82510238b422af746299e9e1c418a0474107d1b57d119fd7dc5685e037edd2e` | `ddcb29549dda5dcf164848730679027161e34692282cfeaabf84e089db58b857` |

No other implementation file changed. `code_csv_multiple_testing_dataflow_v3_2.py` carries no copy
of the expression, and `code_csv_multiple_testing_dataflow_v3_4.py` is byte-identical to its
round-7 state at `f690db88677a9f79a3a162dc7dff907d8c377a28c1d2b02095f6fadea62ed789`. Both keep the
digests they already had.

Re-pinned in:

- `tests/test_code_csv_multiple_testing_comprehension_v3_4.py`,
  `test_frozen_3_1_3_2_3_3_anchor_bytes_are_exact` (the v3 and v3.3 rows)
- `tests/test_multiple_testing_scope_questions_v3_1.py`,
  `test_frozen_v3_anchor_bytes_are_unchanged` (the v3 row)
- `src/sc_referee/resources/scientific-check-manifests-v1/registry.json`, regenerated with
  `scripts/build_scientific_check_release_manifest.py`; the only two leaves that move are the
  `implementation_files` entries for these two files
- `docs/implementation/CAPABILITY_MATURITY_LEDGER.json`, regenerated with
  `scripts/build_capability_maturity_ledger.py`; the only two leaves that move are
  `source_digests.scientific_registry` and `ledger_digest`

The dated design documents that record what was frozen at the time
(`MULTITEST-3.1-SCOPE-QUESTIONS-ATTESTATION-DESIGN-2026-08-29.md`,
`MULTITEST-3.3-TERMINAL-PRESENTATION-DESIGN-2026-08-30.md`,
`MULTITEST-3.4-COMPREHENSION-ITERATOR-DESIGN-2026-08-31.md`,
`MULTITEST-RECALL-RECON-E18-2026-09-02.md`) are left as written. They are records of a past state,
and this table is where the move is declared.

## Evidence that the outputs are identical

The equivalence was measured, not argued. A snapshot script ran every row of the evidence universe
the round-7 sweep covers through all four analyzer lanes and recorded, per row, the canonical JSON
of the shipped 3.4 result (classification or abstention reason, corrected positions, family size,
registered APIs, output sink kinds, every evidence span), the 3.4 admission census, and the frozen
3.3, 3.2 and v3 results beside it.

- 624 rows: the 245 lane fixtures, the 170 evidence sources (120 opened envelope cases and 50 open
  corpus cases), and all 209 round-1 to round-7 audit-fix oracle sources.
- The whole snapshot hashes to `c38a6650a37eecd59d5c87dee47275a0bb46dbbc496e7e96a5832ba6eea2892c`
  before the change and after it, and the 3.6 MB row file is byte-identical. Mismatches: **0**.

Through the real CLI pipeline (`method-contract` then `audit --development-lane`, one fresh
contract per project), 199 projects were compared: all 135 cases of envelopes E10 to E18 and 64
probe projects rebuilt from the round-6, round-7 and round-8 probe builders. Every recorded field
is identical, including every check's `module_evaluation_digest`: **0** full-record mismatches,
**0** errors, and zero Findings in every run. Retro recall over E10 to E18 is unchanged at 5/6,
6/6, 6/6, 4/6, 4/6, 3/6, 4/6, 6/6, 2/6, with zero negative candidates in every envelope.

## What a frozen method contract does

Two different mechanisms respond to a change of these bytes, and they behave differently. Both were
tested rather than assumed.

- The CLI's release-manifest drift check compares the live implementation files against the
  `implementation_files` inventory in `registry.json`. With a stale registry, `method-contract`
  refuses with `scientific-check release manifest or implementation drift` (exit 2). Regenerating
  the registry, which this change does, restores it (exit 0).
- A method contract frozen before this change still validates and audits cleanly afterwards. The
  check manifest's `implementation_digest` is a semantic digest over the check identity, its
  requirement candidate and the adapter grammar digest; it does not cover the analyzer module
  bytes. Envelope 18's round-7 contract lock was re-run against the new lane and audited to exit 0
  with the same records. That differs from the round-7 fix, which moved the 3.4 module and with it
  the digests the contract is bound to.

## Measured effect

Single call on the sealed E17 P3 source (82 lines), best of five, serial:

| | Before | After |
| --- | --- | --- |
| One 3.4 call | 1.0271 s | 0.1840 s |
| One frozen 3.3 call | 0.6174 s | 0.0852 s |

## Consequences

- The two frozen lanes are no longer byte-identical to their round-7 state. Their new bytes are
  pinned here and in the two anchor tests, and the argument that they are the same analyzer is the
  624-row and 199-project equivalence above, not the absence of a diff.
- The release manifest must be regenerated with the change, or every `method-contract` invocation
  refuses on drift.
- Any future change to either frozen lane must repeat the same equivalence measurement before its
  digest is re-pinned.
