# MT 3.4 audit-fix round-7 independent oracle

This directory is the independent expected-row authority for the seventh MT 3.4 adversarial audit
fix. Like `../audit-fix-r1-oracle/` through `../audit-fix-r6-oracle/`, it is separate from
`../prototype-sweep/`, whose `MANIFEST.json`, `results.json`, and `instrument_results.json` hashes
are pinned in the test suite so that no post-hoc fixture may be added to it.

Rounds 1 and 2 closed admission routes. Round 3 was the first fix on the classification side.
Round 4 closed the rest of the bindings a correction store can travel through inside one scope,
round 5 followed the store into a project-local helper, and round 6 decided the calls round 5 left
as non-captures. Round 7 makes that decision uniform, because the audit demonstrated that round 6
failed closed on one kind of thing and open on two others.

## What round 6 got wrong, in both directions

Round 6 fails closed on a **callee** it cannot resolve. It did not fail closed on a **value** it
cannot follow, or on a **callable** it cannot resolve, and it keyed its library allowlist on the
spelling of a name rather than on what the imports say the name is. The audit reproduced nine
complete, correct Bonferroni programs that stayed `candidate`/`none` over a family of six because
of those three gaps, through the real contract and audit pipeline rather than only at the analyzer
level: a class wearing the `json` spelling beside a storing `dumps` staticmethod; a record appended
to a list and then corrected through the list; the same through `extend`; a helper returning a
generator expression over its parameter; and four callables reaching `Series.apply` -- a wrapper
that stores only by calling a storing helper, a callable held in an attribute, one taken out of a
dictionary with `.get`, and one returned by a chain of identity functions.

In the other direction, round 6 refused ten programs whose family really was left uncorrected, so
ten true accusations were lost: `import json as payload` and `from json import dumps as serialize`,
`copy.deepcopy`, `pprint.pprint`, a `csv.DictWriter` writing each record out, `seen.index` and
`seen.count` after an allowlisted `seen.append`, a genuine `functools.wraps` wrapper around a
read-only helper, a helper returning `{"names": list(table)}` over a mapping parameter, a method
whose bare call resolved to a same-named sibling method instead of the module function, and a bare
call to an `async def`.

## The closure

**Rule A(1), value flow fails closed like callee flow.** `append`, `extend`, `insert`, `add`, and a
subscript store all put the collection's own record objects into another container without copying
them, so that container holds the family's records and a store written through one of its elements
is a store into the family. Round 6 read the insertion call as read-only -- correctly, because it
does not write into the record -- and dropped the record's role on the way in.

The container is judged on what is done to it afterwards, not on the insertion itself. The frozen
mutation census reads any receiver method call as an in-place mutation, so counting
`held.append(record)` against `held` would refuse `seen.append(record); seen.index(record)`, which
only reads a family that really was left uncorrected. A container reached **only** by an insertion
is therefore allowed the insertion and query methods that filled and read it, and refuses on
everything else: an augmented assignment, a `del`, a nested subscript store such as
`held[0]["p"] = ...`, or any other method call. A container the round-6 enumeration already
reached by an ordinary binding form keeps its round-6 disposition exactly.

**Rule A(2), a lazy display is not fresh.** A generator expression, a comprehension, and a `lambda`
are objects that hand out whatever their body names. `def stream(entry): return (entry for _ in
range(1))` and `def getter(entry): return lambda: entry` both hand the record straight back, and
round 6 read both as fresh because it only understood concrete displays. A comprehension target
that appears in the element expression carries the roots of the iterable it was drawn from, so
`(e for e in entry)` is not fresh either, while `[row["p"] for row in results.values()]` still is:
its element is a scalar.

**Rule A(3), mapping iteration stops at the keys.** Iterating a mapping yields its keys, and a key
is not a record: that is the module-level bare-iteration boundary four pinned true accusations
already depend on. The freshness test now draws the same boundary one scope in, so
`{"names": list(table)}` over a mapping parameter is a fresh dictionary of strings. The same
wrapper over a sequence parameter yields the records and keeps its root.

**Rule B, a callable position fails closed.** Round 6 asked whether a callable beside a tracked
argument was *known* to store, and admitted everything it could not read. The question is now the
other way round: a callable position is admitted only for a `lambda` or a project-local definition
that does not store, a read-only builtin, an allowlisted library target, or a bound method of a
tracked container whose spelling is on the closed read-only method set. An attribute of a project
object, a `dict.get` result, a call expression, a comprehension-produced callable, and every other
unresolvable callable are storing by default.

The classification runs **after** the interprocedural storing fixpoint, which is what closes the
wrapper route: `def wrapper(entry): direct(entry)` writes nothing in its own body, so a
classification built from the direct census reads it as read-only. Roles and the call census feed
each other to a fixpoint for the same reason: deciding whether a call hands an argument back needs
callee resolution, and callee resolution needs the roles.

**Rule C, the allowlist is keyed on import-resolved targets.** A qualified or bare library callee
is allowlisted only when its base name is bound in the scope chain exclusively by `import`
statements, and only when the identity those statements give it is an allowlisted target.
`import pandas as pd` and `import pandas` are both `pandas`; `from scipy import stats` and
`import scipy.stats as stats` are both `scipy.stats`; `from json import dumps as serialize` is
`json.dumps` and `from operator import setitem as put` is `operator.setitem`. A base name bound by
anything else is not a library name: `json = Mutator` resolves project-locally to the class, whose
storing staticmethod is then seen rather than merely feared.

**Semantics fix D(1), class bodies are off the lexical chain.** A class namespace is not an
enclosing scope in Python. A bare `inspect` inside `Report.show` is the module-level `inspect`,
never `Report.inspect`, which is reached only through `self.`, `cls.`, or `Report.`.

**Semantics fix D(2), `global` and `nonlocal` rebind the lookup.** A declaration continues the
lookup in the scope it names. A declaring scope that also writes the name leaves the target scope
ambiguous, and rule A fails closed on it.

**Semantics fix D(3), a forwarding decorator is transparent.** The proof is structural and
complete, not a guess from a spelling: the decorator is a project-local `def` of exactly one plain
parameter; every one of its own returns is the same bare name; that name is bound by exactly one
nested `def`; the nested wrapper neither stores through its parameters nor writes through a free
variable; and every call the wrapper makes is a call of the decorator's own parameter. A
`@functools.wraps(func)` on the wrapper is admitted, because it copies metadata and changes nothing
about what the wrapper does with its arguments.

## What the fifty-one rows prove

**Twenty-two rows are the false-accusation class**, and every one is a complete, correct
six-outcome Bonferroni correction that the shipped 3.4.0 recognizer, with the round-6 closure
installed, accused of being uncorrected. Six reach the store through a container the record was
inserted into. Four reach it through a lazy display. Four reach it through a callable this
recognizer could not resolve, and four more through the receiver of a callback-bearing call whose
callable it could not read. Three reach it through a name whose library identity the spelling
misrepresented.

**Two more `apply` rows are controls rather than closures.** A comprehension-produced lambda is
already refused by the round-6 definition escape, and a `functools.partial` of a storing definition
by the round-6 storing-callable propagation. Both are measured under the round-7 receiver mutant
and are unmoved by it, which is what separates them from the four rows that mutant readmits.

**Three more rows are correct analyses an earlier gate refuses.** A masquerade written beside a
genuine `import json` is declined by the upstream API-resolution gate; a `yield` helper is declined
by the frozen helper census; and a `map` over an insertion container is declined by the frozen
p-value consumer proof. None of them is accused, which is the property that matters, and each is
recorded with the reason it actually carries rather than with the reason this round's rule would
have given it.

**One row is the reason authority.** `correct-explicit-loop-record-store-through-name` is the
identical program with the store written through `results`; every closed row names it, and the test
recomputes its frozen 3.3 row live and asserts the equality, so a wrong pin fails rather than
passes.

**Fifteen rows are true accusations round 6 lost or could have lost**, each on a family that
really is left uncorrected. Nine are read-only library and container calls the import-resolved
allowlist recovers. Two are read-only callables in a callable position, which is what shows the
callable rule admits as well as refuses. Two are the mapping-key freshness boundary. One is the
forwarding decorator. One is the class-scope lookup.

**Five rows are costs, pinned by name and every one of them inherited.** A bare call to an
`async def` creates a coroutine and runs no body, and the conservative disposition stays because
this recognizer does not reason about awaits. A `functools.lru_cache` decorator is a library call
this module cannot read, so the decorated name is unresolvable, which is round 6's rule unchanged.
A record bound into a subscript location escapes, which is the round-1 and round-2 rule unchanged.
A helper calling `.values()` on its parameter is caught by the frozen receiver-method census,
exactly as its `.keys()`, `.items()`, and `.copy()` siblings are in the round-6 oracle. And `apply`
is on the never-allowlisted callee set, so a read-only `Series.apply` over an uncorrected family
is refused; that set is what stops the whole Direction-1 apply class and it is kept as it is.

**The residual set is empty.** No row is declared an open false accusation.

**Four rows are movement controls.** The uncorrected baseline every read-only control is measured
against, the coverage guard, and the two sealed E17 sources carried unaltered, whose
`candidate`/`none` over six and `candidate`/`strict_subset` over (0, 1, 2) of seven are the pinned
3.4 movements.

## Provenance

`EXPECTED_ROWS.json` is authored from the round-7 design, from the frozen 3.3 reason carried by the
through-name sibling, and from the Codex round-6 audit ledger. `implementation_output_used` is
`false`. The corrected-position tuples of the classified movement rows are properties of the sealed
cases and are pinned identically by the round-2 through round-6 oracles.

`fixture_sources.py` owns source selection and mutation only. Every row is one anchored edit of the
sealed E17 P3 analysis source: the collection comprehension is rewritten as the equivalent explicit
loop, one block is placed immediately after the collection statement, and any definitions are
placed immediately before `def main():` with any imports after `from scipy import stats`. Each
anchor is asserted to occur exactly once, so a drift in the sealed source fails the build rather
than silently producing a different program.
