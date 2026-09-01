# MT 3.4 audit-fix round-1 independent oracle

This directory is the independent expected-row authority for the MT 3.4 adversarial audit fix.
It is separate from `../prototype-sweep/` because that directory is immutable design evidence:
its `MANIFEST.json`, `results.json`, and `instrument_results.json` hashes are pinned in the test
suite, so no post-hoc fixture may be added to it.

The provenance chain is:

1. `docs/implementation/MULTITEST-3.4-COMPREHENSION-ITERATOR-DESIGN-2026-08-31.md`, section 3.3's
   ordering rule (an abstaining re-analysis returns the frozen 3.3 reason byte-for-byte),
   section 4.2's generator-sequence order-equality condition, and section 6.1's admitted
   iterator and 6.2's position derivation;
2. the frozen B1/B4 record-mutation closure in `rm._record_boundary_reason`, which is the
   discipline the sequence-object closure mirrors rather than a new one;
3. the MT 3.4 adversarial audit dated 2026-08-31, which returned FIX-REQUIRED with one false
   accusation, one major, and one surviving mutant; and
4. `EXPECTED_ROWS.json`, which transcribes those design-mandated outcomes and attack shapes.

`fixture_sources.py` owns deterministic source selection and mutation recipes only.

## What the nine rows prove

Four rows are the false accusation. Each is a scientifically correct seven-outcome analysis: the
selection sequence the membership guard reads is grown to the full declared family before the
loop runs, so every outcome's p-value is multiplied by the number of comparisons and capped. The
recognizer reads the literal, which still shows three names, and before the fix emitted a
`strict_subset` accusation against a complete correction. The four spellings are a direct
`.extend`, an aliased `.extend`, an aliased `+=`, and an aliased slice store. All four must
refuse at the sequence-object stability gate and keep the frozen 3.3 abstention unchanged.

Two rows are the shadowed builtin. Both bind the name `enumerate` to a project-local function.
One body agrees with the builtin and one does not; the point of carrying both is that the
recognizer cannot tell them apart, so agreement is never a licence to read the name as the
builtin. Neither row is an outcome flip, which is why both carry `correct_analysis: false`: they
pin the gate.

One row is the surviving mutant. Replacing the contract-order equality with equal-length matching
survived the shipped suite because the pinned out-of-contract-order fixture builds its sequence
with `list(reversed(OUTCOMES))`, which is not a resolvable module sequence and is refused before
the order-equality predicate is reached. This row writes the same six declared outcomes out as a
flat list literal in a different order, so the sequence resolves, has the contract length, and
has exactly the contract member set. Order equality is then the only predicate that can refuse
it.

Two rows are non-vacuity controls. The first is the sealed E17 P6 source unaltered, so a closure
that over-narrowed would lose the pinned movement here. The second carries a live alias that
nothing mutates, so a closure that refused aliasing rather than mutation would lose the movement
here instead. Both must still reach `strict_subset` over positions 0, 1, and 2 in a family of
seven.

## Reason authority

Every abstention reason in `EXPECTED_ROWS.json` is the byte-frozen 3.3 analyzer's own reason for
that source. Design section 3.3 steps 5 and 6 require an abstaining 3.4 re-analysis to return it
unchanged, so the pinned reason restates the ordering rule rather than transcribing 3.4 output.
The test recomputes the frozen 3.3 row live and asserts three-way equality, so a wrong pin fails.
