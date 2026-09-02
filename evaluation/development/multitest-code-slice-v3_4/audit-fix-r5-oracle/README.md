# MT 3.4 audit-fix round-5 independent oracle

This directory is the independent expected-row authority for the fifth MT 3.4 adversarial audit
fix. Like `../audit-fix-r1-oracle/` through `../audit-fix-r4-oracle/`, it is separate from
`../prototype-sweep/`, whose `MANIFEST.json`, `results.json`, and `instrument_results.json` hashes
are pinned in the test suite so that no post-hoc fixture may be added to it.

Rounds 1 and 2 closed admission routes. Round 3 was the first fix on the classification side, and
round 4 closed the rest of the bindings a correction store can travel through *inside one scope*.
Round 5 closes the one route round 4 named and left open: the store is written in another scope.

## The confirmed route

A correct, complete Bonferroni correction over the six declared outcomes, written as

```python
def bonferroni_adjust(entry, n_tests):
    entry["p"] = min(entry["p"] * n_tests, 1.0)


for name, record in results.items():
    bonferroni_adjust(record, len(OUTCOMES))
```

with every verdict read afterwards, is classified `candidate`/`none` over a family of six. The
custodian reproduced it through the real contract and audit pipeline.

The round-4 closure enumerates `record` correctly; the store it is looking for is not there. The
store is `entry["p"] = ...`, and argument passing is a non-capture under the frozen discipline, so
nothing binds `entry` to the record. Round 4's names are matched module-wide, which is why the twin
program whose helper parameter is *also* called `record` already refuses: the disposition turned on
the parameter name alone, and the round-4 oracle pinned both halves of that pair to record it.

## The closure

A call whose callee resolves to a project-local definition in the same module makes the **call
site** a mutation of every argument whose bound parameter is stored through in the callee body.
That mutation is checked against the round-3 and round-4 name sets exactly as a direct store is,
and it lands on the same reason, `pvalue-family-collection-unresolved`, which the through-name
sibling already carries. No reason is added: the closed set stays at 61.

**Callee resolution is by definition, not by name shape.** A callee resolves only to a `def`, an
`async def`, a name bound once to a `lambda`, or a method of a class defined in this module, and
only when the name has exactly one such definition and this module binds it nowhere else -- not
imported, not reassigned, not a parameter. A method resolves through the class name, through a
variable bound once to a constructor call on that class, or through the enclosing method's own
first parameter; `staticmethod` and `classmethod` decide whether the first argument is the
receiver. `map` and `filter` resolve their callable and apply it to the elements of the iterables
beside them, and `sorted`, `min`, and `max` do the same for `key=`. Everything else resolves to
nothing and stays a non-capture, which is the frozen `len(OUTCOMES)`,
`", ".join(MUSCULOSKELETAL)`, `print(record)`, `sorted(results.items())` discipline the pinned 3.3
evidence rows depend on and that rounds 1 to 4 all preserve.

**Argument binding covers the positional slots, the keyword names, and both star buckets.** A
positional argument binds the slot at its index or the `*args` bucket past the last slot; a keyword
argument binds the parameter its name matches or the `**kwargs` bucket; a starred or
double-starred argument forwards an unknown position, so it is bound to every parameter of its
callee at once and is captured when any of them stores. That is the conservative reading the audit
asked to measure, and it needs no separate rule: `forward(record, n)` into
`def forward(*args): rescale(*args)` is captured through the bucket in both directions.

**A parameter is stored through when the round-3 and round-4 closures say so.** The callee body is
read as a module, the parameter's round-3 alias component is taken, and the round-4 record-derived
enumeration is run over it with the parameter seeded as both a mapping of records and a sequence of
them. A store, an in-place mutation, or a display escape through any name that reaches counts, and
so does handing one of them to another storing helper. The seeding difference from the module level
is deliberate: a bare `for x in X` target is left opaque at module level because the collection's
seed does not say whether iterating it yields keys, floats, or records, and a parameter has no
seed at all -- it holds whatever the call site handed it, and the store it reaches is invisible to
the frozen engine either way.

**Recursion resolves to a fixpoint.** The storing set only grows, so a mutually recursive callee
graph converges rather than needing a conservative refusal, and a helper that only calls itself
never becomes storing.

## What the twenty-five rows prove

**Fourteen rows are the false-accusation class.** Every one is a complete, correct six-outcome
Bonferroni correction that the shipped 3.4.0 recognizer, with the round-4 closure installed,
accused of being uncorrected. Five differ in how the helper body reaches the store -- directly,
through a local alias, through a second helper, inside an `if`, through `update`. One defines the
helper after the call. Three differ in how the argument binds -- keyword, `*args` forwarding,
`**kwargs` forwarding. Two reach a lambda, one bound to a name and one applied through `map`. One
reaches a static method of a project-local class. Two hand over the collection itself, one as the
mapping and one as its values view. Each lands on the frozen reason its through-name sibling
carries.

**One row is the reason authority.** `correct-explicit-loop-record-store-through-name` is the
identical program with the store written through `results`; every refused row names it, and the
test recomputes its frozen 3.3 row live and asserts the equality, so a wrong pin fails rather than
passes.

**One row is the named open residual, and it is open at the analyzer level only.**
`correct-record-in-helper-imported-from-a-sibling-module` writes the identical correction in a
helper that lives in another project module. This recognizer reads one source file, so the callee
resolves to no definition it can read. Refusing on an unresolvable callee would refuse every
builtin and library call the pinned evidence rows depend on, so the row is still classified
`candidate`/`none` and is pinned with `expected_open_false_accusation`.

Every row in this oracle is measured through the analyzer alone, and at that level the pin is
correct. It is not a deployed accusation route. Run through the real pipeline -- method-contract
followed by audit with the development lane and the material input, custodian-measured 2026-09-02
-- the same project comes back `unsupported` at `api-resolution-ambiguous`, with no classification
at all: the api-resolution and helper-expansion counterevidence gate refuses before the 3.4
classification runs, because it can resolve nothing for a callee defined outside the file under
analysis. Closing the row at the analyzer level would still mean widening what the recognizer
*reads*, which is a change to the analysis envelope rather than to this closure.

**One row is a measured cost, recorded rather than hidden.**
`boundary-read-only-helper-calling-a-method-on-its-parameter` is a genuinely uncorrected family
whose presentation loop hands each record to a helper that only reads it -- but reads it with
`entry.get("p")`. The frozen B1/B4 record-mutation census counts every method call whose receiver
is a name as an in-place mutation, because a method may mutate its receiver and this recognizer
never executes project code. Round 5 reuses that census unchanged rather than enumerating which
method names are safe, so this row is refused and one true accusation is traded for the closure.
No row in the 170 evidence sources, the 245 fixtures, or the 50 corpus adapter rows has that shape,
so the cost is a pinned hypothetical and not a measured loss. Its sibling
`positive-read-only-helper-on-uncorrected-family` reads the same field by subscript and keeps its
accusation.

**One row is a measured disposition that was never a false accusation.**
`correct-record-in-instance-method-of-a-project-local-class` abstains at
`unresolved-manual-correction-present` in the frozen 3.3 pipeline and abstains there afterwards.
Only its static-method twin was ever classified, and the pair records which half of the
class-method shape the closure actually had to reach.

**Seven rows are non-vacuity and movement controls.** Three are read-only calls that the closure
must not refuse -- a helper that reads one record, a helper that reads the whole collection, and a
block whose every call over a record-derived name is a builtin. One is the uncorrected baseline
each of them is one inserted call away from. One is a complete correction carried out on the
threshold with a live read-only helper call beside it, so the closure is shown to guard coverage
classifications at no cost. The two sealed E17 sources are carried unaltered, because both pinned
3.4 movements land on the classification path this closure sits directly on.

The read-only helpers are named `significance_label` and `collection_summary` rather than `verdict`
and `result`. P3's own presentation loop binds both of those names, and a name this module binds
twice is not a resolvable callee, so a control spelled that way would pass because the callee never
resolved rather than because the helper only reads. The first draft of the round-5 control did
exactly that, and the mutation kill that treats every helper parameter as storing is what caught
it.

## Inherited defect

The defect is present in the byte-frozen v3 and v3.3 lanes and is narrowed only in v3.4, which
supersedes them in the active development binding. The frozen lanes are unchanged and stay
byte-identical, and the round-5 tests assert their anchor bytes alongside the rest.
