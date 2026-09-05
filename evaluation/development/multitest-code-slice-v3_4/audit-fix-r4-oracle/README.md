# MT 3.4 audit-fix round-4 independent oracle

This directory is the independent expected-row authority for the fourth MT 3.4 adversarial audit
fix. Like `../audit-fix-r1-oracle/` through `../audit-fix-r3-oracle/`, it is separate from
`../prototype-sweep/`, whose `MANIFEST.json`, `results.json`, and `instrument_results.json` hashes
are pinned in the test suite so that no post-hoc fixture may be added to it.

Rounds 1 and 2 closed admission routes. Round 3 was the first fix on the classification side: a
correct Bonferroni pass written through a second *name for the record collection* was published as
an accusation, and the closure followed the bare `A = B` alias edges that make such a name. Round 4
closes the rest of that class.

## The confirmed route

A correct, complete Bonferroni correction over the six declared outcomes, written as

```python
for name, record in results.items():
    record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
```

with every verdict read afterwards, is classified `candidate`/`none` over a family of six. The
round-3 closure does not reach it. `record` is not a second name for the collection, so no alias
edge binds it, and `results.items()` is a call on the collection's own name, which the closure
excludes because the collection's own stores are exactly what the frozen engine already judges.

The store is invisible to the frozen engine for the same reason round 3's aliased store was: the
engine reconstructs family membership from the stores written through the collection's own name,
and this store names `record`. The identical program with the store written through `results`
abstains at `pvalue-family-collection-unresolved`.

## The closure

A record-derived binding is any name bound to one of the collection's records, to the collection
itself, or to a container of its records. The enumeration is closed and it composes, because the
forms compose. Three roles are tracked:

* **mappings** -- names for a container still keyed or indexed by family member whose values are
  the tracked records: the collection, its round-3 aliases, `dict(X)`, `X.copy()`.
* **sequences** -- names bound to an iterable of those records, or to a fixed-length unpack of
  them: `X.values()`, `X.items()`, `enumerate(...)`, `zip(...)`, `sorted(...)`, `list(...)`,
  `tuple(...)`, `reversed(...)`, `iter(...)`, and a comprehension that yields records. The recorded
  shape says which positions of an element are records, so `(key, record)` binds only its second.
* **records** -- names for one record: an iteration target whose element shape is a record, `X[k]`,
  `X.get(k)`, `X.setdefault(k, ...)`, `X.pop(k)`, `next(iter(X.values()))`, `list(X.values())[i]`,
  the walrus spellings of each, and a record rebound to a third name.

A store, an in-place mutation, or a display escape through any of these refuses the classification
exactly as round 3 does, on the same reason, `pvalue-family-collection-unresolved`, which the
through-name sibling already carries. No reason is added: the closed set stays at 61.

Three boundaries are deliberate.

**Reads are never refused.** The closure is over stores and mutations. Six read-only controls hold
it there, one per binding form, all on genuinely uncorrected families that keep their accusation.
`for name, record in results.items(): flag = "SIGNIFICANT" if record["p"] < ALPHA` is the single
most common correct presentation idiom, and the pinned E17 P3 movement is built on the same shape.

**The key half of an `items()` unpack is not a record.** A key is not a record, and the store a key
reaches is `X[k][...]`, which is written through the collection's own name and is already what the
frozen engine sees. The `correct-keys-view-store-through-name` row verifies that: the frozen
pipeline refuses it today, so there is no false accusation there for a key rule to close. Treating
the key as a record would refuse
`for name, record in results.items(): print(name.replace("_", " "), record["p"])` over an
uncorrected family, which is a true accusation, and the
`positive-read-only-items-loop-key-method-call` row is the guard against exactly that.

**The target of a bare `for x in X` is not a record.** Iterating a mapping yields keys, iterating
a collected p-value table yields floats, and the collection's seed does not say which. Four pinned
rows are true accusations that survive only because of this boundary, and they were found by
measurement rather than argued. `E10:P5` and `E12:P5` each write a partial Holm adjustment as
`for row, adjusted in zip(primary, p_adjusted): row["p_adjusted"] = ...` over a list built by one
comprehension, with the `multipletests` call itself plainly visible to the frozen engine, so
nothing is hidden and the partial coverage is exactly what the accusation says. `corpus:spec-21`
and `corpus:spec-45` read a loop variable of a tracked list into a display. Enumerating bare
iteration targets refuses all four and closes no demonstrated route in exchange: where a bare
iteration really does hand out records, the store it reaches is `X[k][...]`, which is written
through the collection's own name and which the frozen engine already refuses, as the
`correct-keys-view-store-through-name` row pins.

## What the forty-five rows prove

**Thirty-one rows are the false-accusation class.** Every one is a complete, correct six-outcome
Bonferroni correction that the shipped 3.4.0 recognizer, with the round-3 closure installed,
accused of being uncorrected. Thirteen reach the record through an iteration target, four through a
subscript or a lookup, two through a walrus, four through a chain, seven through the build agent's
own inventions, and one through a record passed to a helper whose parameter reuses the caller's
name. Each lands on the frozen reason its through-name sibling carries.

**One row is a partial correction carried for its binding form.** `next(iter(results.values()))`
corrects one member of six, so it is not a correct analysis. It is the only enumerated spelling
that binds a record with no loop at all, and a store into one member is still a store the frozen
engine cannot see.

**Two rows are the reason authority.** `correct-explicit-loop-record-store-through-name` is the
identical program with the store written through `results`; every refused row names it, and the
test recomputes its frozen 3.3 row live and asserts the equality, so a wrong pin fails rather than
passes. `correct-keys-view-store-through-name` verifies the keys-view boundary above.

**One row is the named open residual.** `correct-record-in-helper-distinct-parameter-name` passes
the record to a helper that stores through its own, differently named parameter. Argument passing
stays a non-capture under the frozen discipline, so nothing binds the parameter to the record and
the row is still classified `candidate`/`none`. It is a live false accusation that round 4 does not
close, pinned with `expected_open_false_accusation` so it is a recorded row rather than a later
discovery. Closing it would mean deciding what a helper parameter aliases, which is the same wider
question the round-3 oracle left open for the collection-argument spelling. Its shared-name twin
records that the disposition turns on the parameter name alone.

**Ten rows are non-vacuity and movement controls.** Six are read-only bindings, one per form, on a
genuinely uncorrected family that keeps its `candidate`/`none` row; one is the uncorrected baseline
each of them is one inserted read away from; one is a complete correction carried out on the
threshold, so the closure is shown to guard coverage classifications at no cost. The two sealed E17
sources are carried unaltered, because both pinned 3.4 movements land on the classification path
this closure sits directly on, and E17 P3's own `result = results[outcome]` is an enumerated
record-derived binding that is only read.

One of the thirty-one, `correct-invented-collection-dict-unpack-display-items-record-store`, is
refused by the round-2 display-escape half rather than by anything round 4 adds: `{**results}`
reads the collection into a mapping display. It is carried so the two halves are pinned as covering
that shape together, and so a later narrowing of either half is caught here.

## Inherited defect

The defect is present in the byte-frozen v3 and v3.3 lanes and is narrowed only in v3.4, which
supersedes them in the active development binding. The frozen lanes are unchanged and stay
byte-identical, and the round-4 tests assert their anchor bytes alongside the rest.
