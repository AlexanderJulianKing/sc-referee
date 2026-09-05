# MT 3.5 recall-delta opened oracle

This directory is the independent expected-row authority for the shipped multiple-testing 3.5
lane. It is separate from `../prototype-sweep/` because that directory is immutable design
evidence: its `MANIFEST.json`, `results.json`, and `instrument_results.json` digests are pinned
in the design and in the test suite, so nothing may be added to it after the fact.

## Provenance

`EXPECTED_ROWS.json` is recomputed from the design's own executed sweep, not from the output of
this build. The chain is:

1. `docs/implementation/MULTITEST-3.5-RECALL-DELTAS-DESIGN-2026-09-03.md`, revision 0, at repo
   commit `efdc1fb0`. Section 1 owns the five grammars and their refusal lists, section 3 the
   movement set, section 4 the none-flip populations, section 5 the admission census, section 6
   the retro table, and section 8 what the build must prove;
2. `../prototype-sweep/results.json`, digest
   `sha256:2a1d93c12ebda184a71171f19f797cd192930ae33a4af2800a7ab8e8730dbdcd`, which the design
   pins and which `verify.py` in that directory reproduces byte-for-byte; and
3. this file, which projects that sweep's 185 evidence rows and 38 new fixture rows into the
   shape the shipped lane is asserted against.

`tests/test_multiple_testing_opened_oracle_v3_5.py` reads the pinned digest, rebuilds this
file's row set from `results.json` in the same process, and asserts the two agree before it
compares either against the analyzer. A hand edit to `EXPECTED_ROWS.json` therefore fails the
suite rather than passing it.

## What the rows carry

Each of the 185 evidence rows carries the frozen 3.4 row, the expected 3.5 row, the expected
per-case admission census, and whether the row moves. Exactly four rows move:

| Case | Frozen 3.4 | Expected 3.5 | Production |
|---|---|---|---|
| `E15:P3:afe47b2a7ea87ed21a69` | `abstain`, `unresolved-manual-correction-present` | `candidate`, `none`, N=5, corrected `[]` | D5 |
| `E17:N1:e2d8b1bdf4baa671a1b4` | `abstain`, `test-operand-lineage-unresolved` | `covered`, `complete`, N=4, corrected `[0,1,2,3]` | D4a |
| `E18:P2:5a9277448db34379ce78` | `abstain`, `hierarchical-gatekeeping-present` | `candidate`, `none`, N=6, corrected `[]` | D1 |
| `E18:P3:d1b1fc47ccdabd0c2f22` | `abstain`, `test-operand-lineage-unresolved` | `candidate`, `none`, N=5, corrected `[]` | D4a + D4b |

Three are catches. `E17:N1` is a clearance of a correct analysis: the source corrects all four
declared outcomes with one `multipletests` call, and its only wall was that its group constants
are the integers `18` and `24` rather than strings. A negative reaching `covered` is the desired
answer; a negative reaching `candidate` is a false accusation and an unconditional stop.

Two rows, `E10:N7:6d2fdc67ab98bc0e0e6e` and `corpus:spec-30`, resolve at adapter level before
the source analyzer runs. They carry both the frozen adapter row and the source analyzer's own
reason, because a direct analyzer call returns the second and the pipeline returns the first.
No 3.5 admission may cross either, which the test checks against an empty census.

The 38 fixture rows are the design's own new fixtures, executed against the shipped lane. Each
carries either `required_admission` (the named production must fire) or `refused_admission` (the
named production must not fire at all). A refusal row additionally has to have an abstaining 3.4
baseline, or its assertion would be vacuous: the ordering rule attempts no production at all on
a row the 3.4 lane already classifies.

## What this directory is not

It is not a rescoring of any sealed envelope. Retro recall over the nine opened envelopes moves
from `40/54` to `43/54`, and those are development projections computed on opened bytes. Sealed
E15 stays `2/6`, sealed E18 stays `2/6`, and the E17+E18 promotion window stays `6/12`.
