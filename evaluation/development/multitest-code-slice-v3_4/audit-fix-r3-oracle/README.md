# MT 3.4 audit-fix round-3 independent oracle

This directory is the independent expected-row authority for the third MT 3.4 adversarial audit
fix. Like `../audit-fix-r1-oracle/` and `../audit-fix-r2-oracle/`, it is separate from
`../prototype-sweep/`, whose `MANIFEST.json`, `results.json`, and `instrument_results.json` hashes
are pinned in the test suite so that no post-hoc fixture may be added to it.

Rounds 1 and 2 both closed *admission* routes: a 3.4 admission fired where it should not have, and
withholding it returned the row to a frozen 3.3 abstention. Round 3 is the first fix on the
*classification* side. The row it closes carries no 3.4 admission at all. The byte-frozen 3.3
pipeline reaches `candidate`/`none` on its own, step 3 of the design's section-3.3 ordering rule
returns that classification untouched, and the accusation is published.

## The confirmed route

A correct, complete Bonferroni correction over the six declared outcomes, written as

```python
adjusted = results
for name in adjusted:
    adjusted[name]["p"] = min(adjusted[name]["p"] * len(OUTCOMES), 1.0)
```

with every verdict read from `results[outcome]["p"] < ALPHA` afterwards, is classified
`candidate`/`none` over a family of six: an accusation that a corrected analysis was never
corrected. The identical program with the same store written through `results` abstains at
`pvalue-family-collection-unresolved`.

The asymmetry is not a judgement about the two spellings. The frozen engine reconstructs family
membership from the stores written through the collection's own name, and `for name in adjusted`
iterates a mapping, so the member each store names is not resolvable either way. Through
`results` the engine sees an unresolvable store and refuses. Through `adjusted` it sees no store
on the collection at all, and reads a family whose every member still carries its raw p. The
alias hides the correction; it does not resolve the family.

## The closure

Before a classification is returned -- the frozen one at step 3 or the re-analysed one at step 5 --
no other name for the record collection may receive a store, a mutation, or a display escape. The
closure is the one rounds 1 and 2 built, applied to a different object: `cm._alias_edges` supplies
the undirected Name-to-Name edges and the container, field, and tuple display escapes,
`cm._object_mutated_names` supplies the in-place mutation census, and the walk runs over the whole
alias component of the collection name. The collection's own stores are excluded, because those
are exactly what the frozen engine already sees and judges.

A record collection is a name bound once to a mapping or list display, a `dict()` or `list()` call,
or one comprehension, and filled by subscript store. The display need not be empty: seeding it with
a descriptive key changes nothing about how the family is built or corrected, and the asymmetry
survives intact. What keeps a literal table out is the store requirement, not the seed, so the
declared outcome list and the label table are never tracked however they are aliased.

Two boundaries are deliberate. Reads through an alias are never refused: a live second name that
nothing stores through leaves the component clean, and the two `positive-...alias-read-only` and
`positive-...alias-reported-not-stored` rows hold it there. Passing the collection to a call is not
a capture, which is the frozen `len(OUTCOMES)` discipline the pinned 3.3 evidence rows depend on;
`correct-explicit-loop-collection-helper-argument` pins what the frozen pipeline does with that
shape instead.

## What the nineteen rows prove

**Eight rows are the false accusation and its variants.** All eight are complete, correct
six-outcome Bonferroni corrections that the shipped 3.4.0 recognizer accused of being uncorrected:
the reported probe, the alias bound before the collection loop runs, an alias of an alias, the same
program written at module scope, the container-display and attribute-field escapes, and the same
collection opened with one descriptive key already in it rather than empty. Each one lands on the
frozen reason its through-name sibling carries.

**Four rows are the reason authority and the argument-passing disposition.** The three through-name
spellings are the rows whose frozen 3.3 abstention authorizes every pin above; each aliased row
names its own sibling and the test asserts the equality live, so the seeded row is pinned against
the seeded sibling rather than the empty-seed one. The helper-argument row records that the frozen
pipeline already refuses that shape, so no false accusation exists there to close.

**Two rows are the dead-store pair.** The aliased correction placed after every verdict has been
printed cannot have reached a conclusion, so it is not a correct analysis, and it abstains for the
same reason its through-name twin does. Whether a store is dead is a question about statement order
that this closure does not answer. Carrying both spellings pins that a classification survives a
store only when the closure can see the store at all.

**Five rows are non-vacuity controls.** Two are genuinely uncorrected families that must keep
their `candidate`/`none` row -- one with a live read-only alias of the record collection, one with
an alias of the declared outcome list, which is not a record collection. One is a complete
correction carried out on the threshold rather than on the p-values, so it is `covered`/`complete`
with a live alias of its record collection: the closure guards coverage classifications too, and
this row is what shows guarding them costs nothing. The two sealed E17 sources are carried
unaltered, because the round-3 closure sits directly on the classification path where both pinned
3.4 movements land.

## Reason authority

Rounds 1 and 2 could pin every abstention against the byte-frozen 3.3 analyzer's own reason for the
same source. Round 3 cannot: 3.3 classifies these rows, which is the defect. The authority is the
frozen 3.3 reason for the row's *through-name sibling* instead, named in each row's
`expected_reason_sibling`. The test recomputes the sibling's frozen 3.3 row live and asserts the
shipped 3.4 reason for the aliased row equals it, so a wrong pin fails rather than passes. Nothing
here adds a reason: the closed set stays at 61.

## Inherited defect

The defect is present in the byte-frozen v3 and v3.3 lanes and is narrowed only in v3.4, which
supersedes them in the active development binding. The frozen lanes are unchanged and stay
byte-identical, and the round-3 tests assert their anchor bytes alongside the rest.

## One shape this oracle does not close

`correct-explicit-loop-collection-helper-argument` passes the collection to a helper that writes
the correction through its own parameter. The frozen pipeline refuses it today at
`unresolved-manual-correction-present`, so it is not a false accusation and the closure leaves it
alone. Argument passing stays a non-capture. If a later change makes that reason unreachable for
this shape, the row becomes a false accusation of exactly the round-3 kind, and closing it would
require deciding what a helper parameter aliases -- which is a wider question than this closure
answers. The row is carried here so that change is caught rather than discovered in an envelope.
