# MT 3.4 audit-fix round-6 independent oracle

This directory is the independent expected-row authority for the sixth MT 3.4 adversarial audit
fix. Like `../audit-fix-r1-oracle/` through `../audit-fix-r5-oracle/`, it is separate from
`../prototype-sweep/`, whose `MANIFEST.json`, `results.json`, and `instrument_results.json` hashes
are pinned in the test suite so that no post-hoc fixture may be added to it.

Rounds 1 and 2 closed admission routes. Round 3 was the first fix on the classification side.
Round 4 closed the rest of the bindings a correction store can travel through inside one scope,
and round 5 followed the store into a project-local helper. Round 6 decides the calls round 5
left as non-captures, in both directions, because the audit demonstrated a live false accusation
and a live lost accusation on each side of that boundary.

## What round 5 got wrong, in both directions

Round 5 read every callee it could not resolve as a non-capture. The audit reproduced fourteen
complete, correct Bonferroni programs that stayed `candidate`/`none` over a family of six because
of it, through the real contract and audit pipeline rather than only at the analyzer level:
`dict.update(record, p=...)`, `operator.setitem(record, ...)`,
`functools.partial(rescale, family_size=6)`, a static method stored in a name,
`ADJUSTERS["bonferroni"](record, 6)`, a lambda held in a list, a decorator-supplied wrapper,
`setattr` on a property-setter wrapper, `pd.Series(list(results.values())).apply(rescale)`, a
helper handed `[results[name]]`, a helper defined beside an unrelated parameter of the same name,
a class attribute of the same name, a second nested definition of the same name, an unused nested
definition of the same name, two conditional definitions, an import followed by the correcting
definition, a returned alias, a returned values view, a no-argument closure over the collection,
and a default argument bound to the record.

In the other direction, round 5 refused seven programs whose family really was left uncorrected,
so seven true accusations were lost: a parameter rebound to a fresh dictionary, `*record`
forwarding, a helper that iterates its mapping parameter bare, a helper handed one collected p as
a float, a store only in a never-called nested function, a project-local `sorted` returning
unrelated dictionaries, and a helper that reads with `.get()`.

## The closure

**Rule A, fail closed on an unresolvable callee.** A call that is handed a tracked object -- the
collection, a round-3 alias, or a round-4 mapping, sequence, or record binding -- is a mutation of
that object unless the callee is a project-local definition whose body only reads what it binds,
or a read-only builtin or library API on the closed allowlist. Calls with no tracked argument are
untouched, so the frozen `len(OUTCOMES)` and `", ".join(MUSCULOSKELETAL)` non-capture discipline
every earlier round preserves is exactly as it was. This inverts the round-5 default for one kind
of call and for nothing else.

**The allowlist is measured, not chosen.** A census over the 245 prototype fixtures, the E10-E17
envelope cases, the open-corpus rows, and the round-1 through round-5 oracle sources reports every
callee that receives a tracked argument anywhere in the evidence base. Exactly these are on it,
plus their obvious read-only siblings: the builtins `len` (45 rows), `zip` (22), `list` (6),
`sorted` (6), `enumerate` (5), `set` (5), `min` (4), `max` (3), `iter` (2), `dict`, `float`,
`next`, `print`, `reversed`, `sum`, `tuple`; the str methods, which carry 470 of the measured
calls; the imported `multipletests` (14 rows), `mean` (8), `stdev` (8); the module APIs
`statistics.mean`, `statistics.stdev`, `stats.ttest_ind` (4), `pg.multicomp` (2), `pd.DataFrame`;
and the container-insertion methods, measured as `secondary_results.append(result)` on E13:P5.
`getattr`, `setattr`, `delattr`, `exec`, `eval`, `vars`, `globals`, `locals`, `apply`,
`functools.partial`, and the `operator` mutators are never on it. `map`, `filter`, the `key=`
builtins, and the `apply`-shaped library methods are on it only while the callable beside them
resolves read-only.

**Callee resolution is per scope chain.** Round 5 gathered every parameter name and every `Name`
store in the module and refused to resolve any function sharing a spelling with one of them. That
is not what Python does, and it was a measured false-accusation route six ways over. Each function
and lambda owns the names its own body binds, a class body owns its own attributes and is never on
a function's scope chain, and the module owns the rest. A callee resolves when the innermost scope
on the chain that binds the name binds it exactly once and binds it as a definition. Anything else
is unresolvable and fails closed: two conditional definitions, an import followed by a definition,
a class body binding one method name twice, a name bound to a partial or a bound method or a
dictionary entry, and a subscript callee.

**Rule B, return flow.** The result of a call that is handed a tracked object carries that
object's role, unless the callee provably hands back nothing it was given. The freshness test is
role-aware for the same reason soundness fix 3 is: a helper returning `{"p": entry["p"]}` builds a
new dictionary out of one scalar, and refusing a caller that stores into it would cost a true
accusation.

**Rule C, storing callables as values.** A project-local callable that stores through a parameter
is a storing callable, and so is any name, container entry, `functools.partial`, bound or static
method, or decorated definition that carries one. Invoking one with a tracked argument is a
mutation, and so is passing one to a call that also carries a tracked argument or receiver.

**Rule D, closures and nested definitions.** A `def` or `lambda` whose body stores through a free
variable is a mutation at its definition site, called or not, because a definition is an escape. A
default argument bound to a tracked name is the same escape one binding earlier. Inside a resolved
helper the rule runs the other way: a nested definition that is never read there is dead code, and
reading it as part of the helper is what lost the never-called-nested-store accusation.

**Five soundness fixes.** A parameter is seeded with the role of the argument it binds and not with
both roles at once; `*X` forwards elements and `**X` forwards values, so a record forwards neither;
a subscript of a record is a scalar and a subscript of a mapping of records is a record; a
parameter rebound to a fresh value in straight-line code before any store through it is detached
from the argument; and a wrapper name the module binds itself is resolved as the definition it is
rather than recognized by spelling.

**Recursion resolves to a fixpoint.** The storing set and the storing-callable set only grow, so a
cyclic or mutually recursive callee graph converges rather than needing a conservative refusal.

## What the forty-eight rows prove

**Twenty-three rows are the false-accusation class**, and every one is a complete, correct
six-outcome Bonferroni correction that the shipped 3.4.0 recognizer, with the round-5 closure
installed, accused of being uncorrected. Twelve reach the store through a callee this recognizer
cannot resolve. Six define the correcting helper exactly once in the scope the call site reads it
from, and two of those six are genuinely ambiguous and fail closed rather than resolving. Two
reach it through a returned alias. Three reach it through a definition rather than a call.

**One row is the reason authority.** `correct-explicit-loop-record-store-through-name` is the
identical program with the store written through `results`; every refused row names it, and the
test recomputes its frozen 3.3 row live and asserts the equality, so a wrong pin fails rather than
passes.

**The round-5 residual set is now empty.** `correct-record-in-helper-imported-from-a-sibling-module`
was round 5's one named open false accusation, pinned because a callee defined in another module
resolves to nothing this recognizer can read. Rule A decides it without widening what the
recognizer reads: a callee it cannot resolve and cannot allowlist is a mutation of what it is
handed. That is the one round-5 oracle row round 6 moves, and the move is declared by name in the
test's `_R6_MOVES_R5_ROWS` constant rather than by editing the round-5 oracle, which stays
byte-for-byte as round 5 measured it.

**Eight rows are the true accusations round 5 lost**, one per soundness fix and per half of rule D,
each on a family that really is left uncorrected. Refusing any of them again is what mutation kills
(f) and (g) measure.

**Seven rows are the read-only allowlist controls.** Library calls over the collection, a helper
returning a new dictionary the caller then stores into, a decorated read-only helper whose
decorator provably returns its own parameter, read-only `sorted(key=...)` and `map` callbacks, a
`*args` read-only helper, a collected p stored into a separate output dictionary, and the
str-method route that carries 470 of the measured calls. Each is one call away from the
uncorrected baseline and has to reach the same disposition it does.

**Five rows are measured costs, recorded rather than hidden.** One is a helper whose parameter is
rebound inside a branch: on the path where the branch is not taken the store is written through the
record, so only a straight-line rebinding detaches the parameter. One is an overwritten class
method, where the definition that actually runs is read-only but the class body binds the name
twice, so the callee is unresolvable and rule A fails closed. Three are the rest of the frozen
receiver-method census -- `.keys()`, `.items()`, and `.copy()` on a tracked parameter -- whose
`.get()` sibling the round-5 oracle already pins. Round 6 reuses that census unchanged rather than
enumerating which method names are safe, so all four are refused and four true accusations are
traded for the closure. No row in the 170 evidence sources, the 245 fixtures, or the 50 corpus
adapter rows has any of those shapes, so each cost is a pinned hypothetical and not a measured
loss.

**Four rows are movement controls.** The uncorrected baseline every read-only control is measured
against, a complete correction carried out on the threshold with a live library call beside it so
coverage classifications are shown to be guarded at no cost, and the two sealed E17 sources carried
unaltered, because both pinned 3.4 movements land on the classification path this closure sits
directly on.

## No reason is added

Every refused row lands on `pvalue-family-collection-unresolved`, which the through-name sibling
already carries and which is in the closed set of 61. Round 6 adds no abstention reason, and the
test asserts the set is unchanged.

## Inherited defect

The defect is present in the byte-frozen v3 and v3.3 lanes and is narrowed only in v3.4, which
supersedes them in the active development binding. The frozen lanes are unchanged and stay
byte-identical, and the round-6 tests assert their anchor bytes alongside the rest.
