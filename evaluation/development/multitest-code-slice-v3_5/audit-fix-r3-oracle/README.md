# MT 3.5 audit-fix round-3 oracle

This 18-row oracle closes the three findings in the round-2 re-audit without adding an
abstention reason. Every source is an anchored edit of sealed E18 N1, whose SHA-256 is
`e9b7355f0aba7a5c4f8c230a8f64f422e84993d1c64bca50229b53e9626948ff`.

Eight rows reproduce the exact SHA-256 values published in the verdict:

- five correct analyses that round 2 falsely narrowed because a nested-function parameter,
  nested-function local, or class attribute reused the spelling `reject`;
- the `match`-capture false clearance; and
- the two hand-unrolled `results[i]` false clearances.

The remaining ten rows pin the sealed control and the requested boundaries: aligned direct
record subscripts, a called `nonlocal` rebinding, a method parameter, comprehension versus
ordinary-loop targets, unrelated pattern captures, unique intermediate record names, a uniquely
literal-bound index, and an unresolved index.

The expected rows are authored from Python binding semantics and the round-2 consumption claim,
not from implementation output. The test executes every row through both the analyzer and the
real adapter/controller path, compares every frozen-3.4 identity claim, checks the closed reason
set remains 61, and records four named mutation kills:

1. flattening lexical scopes accuses the three published false-accusation rows again;
2. dropping pattern captures clears the `match` blocker;
3. restoring the all-positions origin fallback clears the swapped-record blocker; and
4. dropping indexed-record resolution refuses the aligned hand-unrolled control.
