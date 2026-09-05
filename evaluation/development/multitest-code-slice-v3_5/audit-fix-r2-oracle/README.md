# MT 3.5 audit-fix round-2 independent oracle

This directory is the independent expected-row authority for the second MT 3.5 adversarial audit
fix. Like `../audit-fix-r1-oracle/` and the seven MT 3.4 fix oracles, it is separate from
`../prototype-sweep/` and from `../opened-oracle/`, whose row hashes are pinned in the test suite
so that no post-hoc fixture may be added to them.

Round 1 closed a false clearance: a library correction whose outputs never reached a decision
was still carrying a `covered`/`complete` row. Round 2 closes three ways that proof could be
satisfied by a program whose verdicts are not the correction's, and removes one way it accused a
program whose verdicts are.

## What the round-1 audit found

Every reproducer is an anchored edit of the sealed E18 N1 source, base SHA-256
`e9b7355f0aba7a5c4f8c230a8f64f422e84993d1c64bca50229b53e9626948ff`.

**Rebinding.** `adjusted_p_values = raw_p_values` written straight after the correction call
still cleared, and so did `reject = [p < ALPHA for p in raw_p_values]`. `_assignment_expressions`
drops a multiply-assigned name, while `correction_return_names` keeps the historical binding for
ever, so every later load was attributed to the correction rather than to the assignment that
actually reaches it.

**Misplacement.** `wrong_reject = [reject[1], reject[0], reject[2], reject[3], reject[4]]` zipped
into the presentation loop still cleared, and so did the adjusted twin. Every verdict does read a
corrected value; outcomes 0 and 1 read each other's. The round-1 code reduced a decision's origin
to a *kind* before comparing it with the position it was rendered at, so "the corrected value
belonging to position 1 was used to judge position 0" became the bare word `corrected`.

**A false accusation.** `for i, result in enumerate(results): print(f"{result['label']}:
{'DIFFERENT' if reject[i] else 'NO DIFFERENCE'}")` is a correct, complete correction, and round 1
published it as a catch. Rule A treated every load of a correction output under a registered sink
payload as display-only, so it could not tell `print(reject[i])` from
`print("SIG" if reject[i] else "ns")`. The merge gate found the same class of defect on the
development code-slice fixture, whose entire published result is `print(reject[0])`,
`print(reject[1])`, `print(reject[2])`.

**A threshold.** `adjusted_p < ALPHA * 2` still clears. See the exclusion below.

## The closure

Three rules, all in the 3.5 core. The frozen 3.3 and 3.4 lanes keep the defects and this oracle
records that, exactly as the round-1 oracle does.

**Rule A, flow-sensitive return names.** A name bound from a correction's return tuple carries
the correction only until the next statement that binds it. Every binder Python has is
enumerated -- assignment in all three spellings, a loop target, a walrus, a `with ... as`, an
import alias, a `del`, a nested definition and its parameters, an `except ... as` -- over the
author's own parse rather than the normalised tree, whose positions are the normaliser's and not
the program's. A binding is *establishing* when it is the correction call itself, an alias of a
name still carrying it, or the identity-preserving `list()`/`tuple()` copy the engine's own alias
closure already accepts; anything else is foreign, and a name with a foreign binding after an
establishing one has lost the correction. The rule is applied at the name and not at the load,
which is the conservative reading the design asks for: a rebinding inside a loop body or a branch
reaches loads a straight-line reading would put before it.

A load of a lost name is not evidence that the correction reached a decision, and a value read
through one carries the `rebound` origin: the position is still concluded, because the program
does publish a verdict for it, but the verdict is neither proved to consume the correction nor
proved to be the raw p-value. That is a decisive origin that is neither, and a clearance may not
stand on it.

**Rule B, position identity.** A decision at rendered position `i` consumes the correction only
when it reads the correction output belonging to `i`. Two readings answer which outcome a sink
payload is *about*, and both are the engine's own: the record it renders, identified by the
family origin of that record's p-value field, and the unrolled iteration its names were generated
for, read back off the loop unroller's own naming through a format written in one place and read
in one place. When the answer is unambiguous and a consuming origin sits at another position, the
rendered position is told so and the row abstains. The position set the sink route establishes is
untouched: only the origins are marked, so the rule can cost a clearance and can never buy one.

**Rule C, decisive use and per-position reads inside sink payloads.** Only the *displayed* part
of a payload is a display. The part whose value selects what is rendered -- the test of an
`IfExp`, each operand of a `BoolOp`, the operand of `not`, a comparison -- is a use, and so is
the read of a single position's own element. What stays a display is a whole-vector dump such as
`print("adjusted: %s" % list(adjusted))`, which shows the array beside verdicts read from
somewhere else and proves nothing about any position. Both round-1 display rows have that shape
and keep their round-1 outcomes.

The bare read of a per-position element splits in two, because the two halves of a correction's
return say different things. A `reject` element is the position's decision: `print(reject[0])`
publishes outcome 0's corrected verdict and there is nothing else for a reader to read it off, so
it carries the position on its own. An adjusted *value* is a number that a threshold still has to
be applied to, so it stays a display and cannot carry a position by itself. The rotated by-name
lookup below is what makes that distinction load-bearing.

## The threshold exclusion, stated

`adjusted_p < ALPHA * 2` clears, and this round does not close it. The row is pinned as
`codex-r2-blocker-5-threshold-alpha-times-two` and measured, not assumed.

This check's clearance asserts **complete family correction over the authorized outcome family**:
that a correction was applied to the whole authorized family, and that each published verdict
consumed its own corrected value. Whether the threshold a verdict compares against is the alpha
the source declares is a different dimension. It has its own frozen guard and its own reason, and
folding it into the consumption proof would make one abstention reason carry two claims that a
reader would then be unable to tell apart. The conservative twin `adjusted_p < ALPHA / 2` is
carried beside it, byte-identical to the digest the audit published for it, to show that the
exclusion is about the dimension and not about the direction of the error.

A reader acting on a `covered`/`complete` row is entitled to read it as "the whole declared
family was corrected together and every verdict was read off its own corrected value". It does
not say the verdict used the declared alpha.

## The twenty-eight rows

**Five rows are the audit's blocker sources**, rebuilt from the recipes in the round-1 verdict
and asserted against the five SHA-256 digests it published. Four now abstain on the frozen
consumption reason; the fifth is the threshold exclusion above.

**Five rows are the inline-verdict variants round 1 regressed on.** Two are the verdict's own
published bytes; the verdict names three more (unrolled, plain-print and `.format()` spellings)
but publishes only digests for them, so those are rebuilt by shape and carry this oracle's own
digests. `fixture_sources.CODEX_DIGESTS` and `SHAPE_REPRODUCED` say which is which and the test
asserts it. All five are back to `covered`/`complete` over the whole family.

**Six rows are correct consumption forms from the audit's own probe table** that this round must
not move: a verdict name assigned before printing, a helper receiving the zip-bound scalar, the
`float()` transport, a swapped text polarity, the conservative half-alpha threshold, and the
partial three-corrected/two-raw program that the table records as reaching rule B and being
refused. The verdict published digests without sources for that table, so these are shape
reproductions and are labelled as such -- with one exception: the half-alpha row was rebuilt by
shape and turned out to be byte-identical to the digest the verdict published, so it is carried
as the verdict's bytes.

**Twelve rows are fresh adversarial variants**, one per way a return name can be rebound or a
correction output can reach the wrong outcome: a rebinding inside a branch, a rebinding through a
helper, a permutation via `sorted(zip(...))`, a rotated index expression and its correct
`i + 0` twin, an aligned by-name lookup and its rotated twin, `del` then a fresh binding, a slice
copy, a `list()` copy, and a numpy re-wrap. Six of them are declined by an earlier frozen gate in
both lanes and are pinned as coverage boundaries rather than as closures.

**One row is the sealed E18 N1 source itself**, carried unaltered.

## Two rows to read together

`adversarial-by-name-dict-lookup-with-the-correct-key` and
`adversarial-by-name-dict-lookup-with-a-rotated-key` differ only in the key the presentation loop
looks the decision up by. The first is a correct analysis; the second judges outcome 0 by
outcome 1's decision. Nothing in the engine's reading separates them, so refusing both is the
only answer that does not clear the second. The correct one's lost clearance is recorded here as
a measured cost of closing the misplacement route, not as an oversight.

## Named kills

`tests/test_code_csv_multiple_testing_consumption_r2_v3_5.py` executes five, each removing one
rule and naming what comes back:

* **A** -- no name is ever treated as rebound: all four rebinding rows clear again.
* **B** -- a payload's rendered position is never established: both permutation blockers clear
  again.
* **C** -- every load under a sink payload is a display again: all five inline-verdict controls
  are published as catches, which is the round-1 regression.
* **D** -- a bare adjusted *value* carries its position the way a `reject` element does: the
  rotated by-name lookup clears again.
* **E** -- the two bare-read kinds are asserted directly, which is what keeps the development
  code-slice fixture's `print(reject[i])` a verdict and the printed adjusted number a display.

The round-1 suite's seven kills still execute unchanged.

## Inherited defect

Every route this round closes is present in the byte-frozen v3, v3.2, v3.3 and v3.4 lanes and is
closed only in v3.5, which supersedes them in the active development binding. The frozen lanes
are unchanged and stay byte-identical, and the tests assert their anchor bytes alongside the rest.
