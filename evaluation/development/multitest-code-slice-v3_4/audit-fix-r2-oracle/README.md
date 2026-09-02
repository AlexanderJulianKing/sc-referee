# MT 3.4 audit-fix round-2 independent oracle

This directory is the independent expected-row authority for the second MT 3.4 adversarial audit
fix. Like `../audit-fix-r1-oracle/`, it is separate from `../prototype-sweep/`, whose
`MANIFEST.json`, `results.json`, and `instrument_results.json` hashes are pinned in the test
suite so that no post-hoc fixture may be added to it.

The provenance chain is:

1. `docs/implementation/MULTITEST-3.4-COMPREHENSION-ITERATOR-DESIGN-2026-08-31.md`, section 3.3's
   ordering rule (an abstaining re-analysis returns the frozen 3.3 reason byte-for-byte),
   section 4.2's generator-sequence resolution and collected-name clause, and section 6.2's
   position derivation;
2. the frozen B1/B4 record-mutation closure in `rm._record_boundary_reason`, which is the
   discipline both lanes mirror rather than a new one;
3. the round-1 audit fix, which proved the sequence-object closure on the correction lane; and
4. `EXPECTED_ROWS.json`, which transcribes the design-mandated outcomes and the round-2 attack
   shapes.

`fixture_sources.py` owns deterministic source selection and mutation recipes only.

## What the twelve rows prove

**Two rows are a residual on the round-1 blocker.** Round 1 refused a bare Name bound to a target
this module cannot follow: a tuple unpack, a record field, a subscript. A container display binds
the same object without being any of those. `PLAN = {"family": MUSCULOSKELETAL}` followed by
`PLAN["family"].extend(OUTCOMES[3:])` grows the selection sequence to the full declared family
with no Store, no augmented assignment, and no method call whose receiver is a Name, so nothing
the round-1 mutation census watches ever moves. Both rows are scientifically correct
seven-outcome corrections that the shipped recognizer accused of being strict subsets of three.
The dict-display and list-display spellings are carried separately because the closure has to
cover the display forms as a class.

**Three rows are the comprehension lane's own false accusation.** Each cuts the generator
sequence to a single outcome before the comprehension runs, through a container display, a record
field, and a walrus binding in turn. One test judged against one fixed threshold owes no
correction, and the recognizer read the six-name literal and accused an absent correction over a
family of six that never exists at runtime. These are the rows that make the comprehension gap a
demonstrated false accusation rather than an argument from symmetry with the correction lane.

**Three rows pin gates without claiming recall.** Two are aliased and escaped mutations that
leave five outcomes tested uncorrected, so their abstentions are not recall claims; they exist to
show the admission is refused at the lane's own gate rather than by whichever upstream refusal
happens to arrive first. Both carry `correct_analysis: false` for that reason. The third is
section 4.2's collected-name clause evaded by a second name for the collection.

**Four rows are non-vacuity controls.** The two sealed E17 sources are carried unaltered, so a
closure that over-narrowed would lose the pinned P3 and P6 movements here. One row carries a live
alias of the generator sequence that nothing mutates, so a closure that refused aliasing rather
than mutation would lose the P3 movement instead. The last writes the collected-name store
through the collected name itself, which section 4.2 permits and the pinned corpus row uses, so
the aliased row above is refused for its alias and not for its store.

## Reason authority

Every abstention reason in `EXPECTED_ROWS.json` is the byte-frozen 3.3 analyzer's own reason for
that source. Design section 3.3 steps 5 and 6 require an abstaining 3.4 re-analysis to return it
unchanged, so the pinned reason restates the ordering rule rather than transcribing 3.4 output.
The test recomputes the frozen 3.3 row live and asserts three-way equality, so a wrong pin fails.

## One shape this oracle does not close

`positive-comprehension-collected-target-store-through-name` and its aliased sibling both abstain,
and the aliased one now abstains because the alias is refused. Written as an explicit loop instead
of a comprehension, with the same alias, the byte-frozen 3.3 analyzer reaches
`candidate`/`none` over six on its own, with no 3.4 admission anywhere in the census. That row is
outside the 3.4 diff and is recorded in the round-2 report as a question for the auditor rather
than repaired here, because repairing it would move frozen baseline rows.
