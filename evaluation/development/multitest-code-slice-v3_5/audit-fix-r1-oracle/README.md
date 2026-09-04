# MT 3.5 audit-fix round-1 independent oracle

This directory is the independent expected-row authority for the first MT 3.5 adversarial audit
fix. Like `../../multitest-code-slice-v3_4/audit-fix-r1-oracle/` through
`../../multitest-code-slice-v3_4/audit-fix-r7-oracle/`, it is separate from
`../prototype-sweep/` and from `../opened-oracle/`, whose row hashes are pinned in the test
suite so that no post-hoc fixture may be added to them.

Every earlier fix round on this check narrowed the accusation side: a correct analysis was being
published as a catch, and the round closed the route. This round is the other kind. It closes a
**false clearance**, which is the highest-severity defect this project can carry, because a
clearance is the one output a reader is entitled to act on without reading further.

## The confirmed route

A program that runs one test per declared outcome, passes the whole family of raw p-values to
`multipletests`, and then prints every verdict from the raw p-value is cleared
`covered`/`complete` over the whole family. The returned `reject` and adjusted arrays are never
read. The Codex 3.5 audit demonstrated it on four sources; the custodian then measured the same
route on the **shipped 3.4 lane**, which clears it too, and therefore on every lane before 3.4,
since the library-correction clearance path predates the 3.4 deltas. It is an inherited defect
that 3.5 widened the reach of rather than one 3.5 introduced.

The structural cause is that recognition and consumption were never connected.
`_correction_census()` recognises a correction from the API and its input positions;
`_correction_returns_supported()` checks the *shape* of every load of a bound return name and so
succeeds vacuously when there is no load at all; the conclusion positions are established
separately; and `complete` was assigned from the correction's input positions alone. Nothing
required the correction's output to reach the conclusions it was supposed to correct.

## The closure

Three rules, all in the 3.5 core and its lane. The frozen 3.3 and 3.4 lanes keep the defect and
this oracle records that, exactly as ADR-0079 records the inherited alias false accusation.

**Rule A, the deadness proof.** A library correction corrects a position only if the correction's
own outputs can reach a decision at all. Every name the return tuple binds is enumerated, the
alias closure the engine already builds included, and the correction counts as *consumed* only
when one of those names is loaded somewhere that is not a registered sink payload. A load inside
a payload shows the value; showing an adjusted number beside a verdict read off the raw p-value
is exactly the shape all four reproducers take. A correction that is not consumed is removed
from the corrected set, so a family whose only correction is dead is `candidate`/`none` -- the
row its twin with that statement deleted already carries. The rule is per call, so a source with
one dead correction and one consumed correction keeps the consumed one's coverage.

This is a proof and not an estimate. `_correction_returns_supported` already refuses every load
shape it cannot account for, so the loads enumerated here are all the loads there are, and no
load outside a display means no conclusion can consume the value. The scan reads the original
statements as well as the normalised ones, because a loop normalisation can drop a genuine load
from the normalised tree and a load in either reading is a load.

**Rule B, the per-position clearance proof.** A clearance asserts that every published verdict in
the family was read off a corrected value, so every position has to prove it. Each conclusion
position carries the origin kinds its decision reached it through -- `raw` for the position's own
test p-value, `corrected` for the per-position element of an accepted correction's `reject` or
adjusted vector, `manual` for an accepted manual correction, and `display` for a bare read of a
correction output that is not itself a decision. A correction output read as the test of a
conditional is a consumption, not a display, which is what makes
`"DIFFERENT" if rejected else "NO DIFFERENCE"` count. If any position of a `complete` row fails
to prove consumption, the row abstains on `unresolved-manual-correction-present`, the reason the
3.2 AP path already emits at its own conclusion-consumption gate (fix commit 7d46e8f). No reason
is added; the closed set stays at 61.

Rule B is applied to the clearance and to nothing else. A `strict_subset` row is an accusation
whose corrected half is not the claim being made, and refusing one for an unproved consumption
drops a true accusation instead of a false clearance. Two sealed rows measure that cost directly:
`E13:P5` and `E17:P5` both carry a partial correction whose consumption the proof cannot follow
through the loop normalisation, and both keep their accusation because rule B does not look at
them.

**Rule C, the D4a/D4b pairing.** D4b removes a hierarchy wall and D4a supplies the group lineage
the design ships it with. D4b alone carrying a *clearance* would mean the wall was the only thing
between a source and `covered`/`complete`, which is the position the audit found it in. D4b alone
carrying a *candidate* is the shipped `correct-d4a-string-group-constants` row, a true accusation
the 3.5 oracle pins. The pairing is therefore applied to the clearance only. See the blocker-3
row below for why the audit's stronger reading was not adopted.

**Where the rules are applied.** The 3.5 ordering rule returns a frozen 3.4 classification
untouched at step 2, and the route is inherited, so a proof living only in the 3.5 core could not
reach the rows that matter. The lane now probes the core before returning a frozen clearance, in
the same position and for the same reason the round-3 to round-7 alias closure sits there. The
probe is one-directional and checked to be so: it may only remove corrected positions from the
frozen row or replace it with the frozen consumption reason, never add a position, change the
family size, or turn an abstention into a classification. It records no admission, because a
probe that changes nothing may not leave a 3.5 admission on a row no 3.5 production carried; when
it does change the row it is re-run with the census open, so every published row still records
the admissions its own analysis made.

## What the twenty-four rows prove

**Four rows are the audit's reproducers**, rebuilt from the recipes in the verdict and asserted
against the four SHA-256 digests the verdict published, so a drifted recipe fails here rather
than quietly testing a different program. All four now land on `candidate`/`none` over the full
family.

**Three rows are the custodian's probes.** `custodian-n1-control` is the sealed E18 N1 source
itself and keeps its clearance; `custodian-n1-raw-plain-arms` is the plain-arm mutant the
custodian measured cleared by the shipped 3.4 lane; the format-arm mutant is byte-identical to
Codex reproducer 1 and is carried once, under the reproducer's name.

**One row is the reason authority.** `authority-n1-raw-plain-arms-without-the-correction` is the
identical raw-arm program with the correction statement and its import deleted. Nothing reads
that statement's results, so deleting it changes nothing a reader could observe, and whatever row
it carries is the row the raw-arm probes must carry. Both lanes agree on it, so the authority is
not a 3.5 artefact. The three blocker rows built on sealed P-case sources are pinned against
their own unaltered twins the same way, and the test asserts each twin equality live.

**Two rows are consumption forms that must keep their clearance.** The zip-bound `reject` element
read as a bare truth value, and a source with a second, consumed correction beside a dead first
one.

**Two rows are false clearances this round closes beyond the audit's four.**
`adversarial-outputs-loaded-only-into-a-display` prints both arrays and decides from the raw p;
rule A's display exclusion refuses it. `adversarial-reject-printed-verdict-from-raw-p` prints
`reject` while the loop's own zip still loads the adjusted array, so rule A cannot call the
outputs dead and rule B refuses the clearance instead. The shipped 3.4 lane clears both.

**Eight rows are coverage boundaries.** Each is a source an earlier frozen gate declines before
the consumption proof is reached: a correction output handed to a helper, iterated in a
comprehension, assigned into a frame column, indexed by a computed subscript, or zipped against
column names rather than records. Five of the eight are *correct* analyses that neither lane
classifies, so they are unsupported rather than accused. Each is pinned as identical to its own
frozen 3.4 row, recomputed live, so a later round that moves one has to say so.

**One row is the named residual.** `adversarial-reject-consumed-at-three-of-five-positions` is
the partial-consumption route: three verdicts from `reject`, two from the raw p. Rule B would
refuse a clearance built that way, but in this spelling an earlier wall stands in front of the
row, so no executed row demonstrates rule B doing it. The gap is recorded by name here rather
than left for a later audit to find. Reaching it needs a spelling that survives the hierarchy
guard, which is a wider question than this round.

**Five rows are the sealed movement controls**, carried unaltered: the two sealed clearances the
round must not lose and the three pinned 3.5 movements it must not disturb.

## The blocker-3 disagreement, recorded

The audit's third blocker asked for the frozen 3.4 reason on the ground that D4b may never move a
public result without D4a. That invariant is not the design's. Section 1.4 says the converse --
that D4a alone reaches only a different abstention, which the ordering rule turns into no public
change -- and the shipped 3.5 oracle pins `correct-d4a-string-group-constants`, which is blocker
3 without the dead correction statement, as a D4b-alone movement to `candidate`/`none`. That row
is a true accusation on a genuinely uncorrected family. Enforcing the audit's reading was
implemented, measured, and reverted: it deleted that pinned row. The pairing was narrowed to the
clearance, and blocker 3's false clearance is closed by rule A instead, landing on the same
`candidate`/`none` its own twin already carries. The row is not a false clearance any more; it
just does not carry the reason the audit asked for.

## Inherited defect

The route is present in the byte-frozen v3, v3.2, v3.3 and v3.4 lanes and is closed only in
v3.5, which supersedes them in the active development binding. The frozen lanes are unchanged and
stay byte-identical, and the round-1 tests assert their anchor bytes alongside the rest.
