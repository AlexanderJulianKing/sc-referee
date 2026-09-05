# MT 2.0 recall recon over the open-corpus misses (2026-08-25)

Provenance: isolated Opus recon at repo state ebcd355 (worked from a clean GitHub clone after a
host permission interruption; zero repo files modified). Method per FINDINGS-PLAYBOOK.md: every
diagnosis confirmed by running the pristine v2 analyzer in-process; every projected catch
demonstrated by a single-construct mutation ladder whose final rung is an EXECUTED candidate;
three prototype rules additionally executed corpus-wide. Executable artifacts preserved under
evaluation/development/multitest-recall-recon-corpus20/ (h.py harness reproducing 49/50 checked-in
reasons, the one difference being spec-30's expected adapter-earlier abstention; lad/spec-NN/
ladders; amend_build.py prototypes; trace_build.py wall tracer).

## Headline

- 23 misses diagnosed to exact constructs; ladder evidence per case.
- Bins: 14 clearable by narrow admissions (A), 4 by guard refinements with FA analyses (B),
  5 deliberate residuals (C: spec-23 round(p); spec-13/29/47 per-member thresholds under the
  {0.05} narrowing and ADR-0079 items 5-6; spec-37 dynamic-key p dict, protected by the
  correct-dynamic-p-dict FA fixture). spec-39 = B-deferred (four refinements + a new numpy
  container grammar).
- Projected post-delta corpus score: 17/25 on executed per-rung evidence; 19/25 if R16 (two-pass
  zip transport) lands across BOTH the transport exclusion and the family-position mapping;
  20/25 is the hard ceiling while the designed narrowings stand.
- Correct-case impact: NONE FLIP. Prototypes A1/A3/A1+A2+A3 executed over all 50 cases: correct
  candidates 0/25 throughout; only movements are spec-28 and spec-42 shifting between abstention
  reasons. Per-construct checks: spec-48 keeps unresolved-decision-threshold under R5 (the
  required correct-hand-sidak outcome); spec-50 keeps its abstention; spec-14/18/36/40 keep exact
  first reasons under R10 incl. the two order-9 pins.
- Eleven of 23 misses are held by four mundane presentation idioms (% formatting, if/else verdict
  statements, small formatting helpers, plain record types), none near the scientific claim.
- Label lesson repeated from E10: unresolved-pvalue-consumer hid three distinct constructs;
  hierarchical-gatekeeping-present likewise.

## Proposals (ranked; full grammars and FA analyses in the recon transcript, summarized here)

R2/R3b statement-form terminal rendering (two exact single-statement constant-arm If shapes; arms
outside the shapes stay in the hierarchy registry; must mirror the ternary handling in BOTH the
hierarchy exclusion and the conclusion census). R1 literal %-formatting as a presentation edge
(display that is the right operand of Constant-str % is payload, not family container; members
still walked by the forward consumer guard). R5 pure presentation helper (single-return
presentation body over the p parameter; any arithmetic/call return stays unresolved - blocks the
hand-Holm helper shape). R4 local dataclass/namedtuple as reconstructable record (field-only
bodies; any method disqualifies). R14 stored member decision (single reaching definition already
satisfying the decision grammar; transport only). R9 pre-bound same-frame group mask (bare
equality only; negation/BoolOp/isin stay refused - preserves the spec-14/36 order-9 pins). R6/R7
helper-local threshold constant + helper-return rendering transports. R12 nearest-preceding
definition for unconditional straight-line rebinding (widest rule; conditional stores stay
refused; REQUIRES its own executed adversarial fixture per the recon's caution). R11 counted
while-loop normalization (exact i=0/while i<len/ i+=1 shape only). R10 .to_numpy(dtype=CLOSED)
as an A6-equivalent identity edge (executed: spec-14/18/36/40 unaffected). R13 presentation
join. R16 two-pass zip transport (drop the correction-return requirement; require every zip
argument to resolve; cover the family-position mapping). R15 record-member origin precision
(tightest conditions; the one flow-reducing rule). R18 decision as two-element constant table
index. Declined: recognizing p < ALPHA/K as manual Bonferroni COVERAGE - a correction-surface
change requiring its own ADR review, not an admission (would also convict hand subfamily
thresholds).

## Oracle to pin (design must re-pin at ADAPTER level per the spec-30 caveat)

Candidates expected: spec-01,03,05,09,11,15,17,19,21(strict_subset),25,27,31,33,35,41,
43(strict_subset),49 = 17; plus 07,45 under full R16 = 19. Abstain unchanged: spec-13,23,29,37,
39,47. Correct cases: all 25 abstain (hard gate).
