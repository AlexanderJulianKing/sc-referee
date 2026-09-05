# Multiple-testing recall reconnaissance: envelope 16 (2026-08-30)

Post-hoc, unblinded analysis of the five missed positives in blind-envelope-16-2026-08-30,
detector code_csv_multiple_testing 3.2.0 at repo 0676ea2. Scored result: recall 1/6, 0/9 FA,
0 Findings, replay 15/15. N1 resolved covered/complete 5/5 (a TRUE clearance on a role-map
negative, the second blind covered/complete in the class). Everything below distinguishes
observed (from sealed run output and source reading) from inferred (hypotheses requiring
probe verification before any build).

## Per-case disposition

| Role | Case | Author idiom (observed) | Detector outcome (observed) | Class |
|---|---|---|---|---|
| P1 | c89a2a42 | Unrolled per-outcome t-test blocks, raw p verdicts, no correction | CANDIDATE uncorrected family 4/4 | CAUGHT |
| P2 | 7a43fa7b | Loop over (column,label) tuples, raw p verdicts; terminal "k of N significant" sum over verdict strings | abstain hierarchical-gatekeeping-present | mislabeled-gate miss |
| P3 | 5a9c5b43 | Helper compare() returns dict with embedded significant flag; dict comprehension over outcomes; presentation loop | abstain unresolved-pvalue-consumer | consumer-proof miss |
| P4 | 9ced761b | Helper test_outcomes() returns list of dicts; presentation loop with If p<ALPHA guarding direction prints; terminal n_significant sum | abstain hierarchical-gatekeeping-present | mislabeled-gate miss |
| P5 | 7be23db3 | multipletests(holm) over the 2 declared primaries only; raw for 4 secondaries; family N=6 | abstain test-battery-cardinality-unresolved | known residual (library-subset cardinality, E14 recon P4-type) |
| P6 | 8ff6de72 | Hand Bonferroni p_raw*len(OUTCOMES) capped, on 2 of 5 outcomes selected by NAME-set membership; second-loop consumption via None-sentinel | abstain unresolved-manual-correction-present + ConditionalConcern + MaterialQuestion | 3.2 design residual working as designed |

## The load-bearing observation

P2 and P4 are the PLAIN uncorrected-family misstep, the exact shape P1 was caught on. The
difference is packaging, not science: P1 unrolled its tests into separate blocks; P2/P4 loop
over a tuple list and summarize. Both abstained under `hierarchical-gatekeeping-present`.

Observed in source (_hierarchy_guard, code_csv_multiple_testing_dataflow_v3.py:13976-14080):
the guard flags ANY control expression whose test is p-derived unless it matches one of five
enumerated presentation exemptions (terminal rendering If, terminal rendering IfExp,
presentation-optional IfExp, terminal family transport loop, terminal family membership
comprehension control).

Inferred (needs probe verification): the triggering constructs are
(a) `sum(1 for r in results if r["verdict"] == "significant")` / `if r["p_value"] < ALPHA`
comprehension filters feeding a terminal count print, and
(b) presentation `If` blocks that compute a local (e.g. `direction`) before printing, which
disqualifies the terminal-rendering exemption.
Neither construct gates any test execution; both sit after every test call. The guard's
purpose (screen-then-test census instability) does not apply: nothing downstream of these
controls can run or suppress a test.

## Why this matters for FA safety

The guard is doing real FA work on true gated designs; it cannot simply be narrowed. But the
exemption lattice already contains the needed machinery: `can_prevent_slice` proves whether a
node precedes any test call or sink. A safe extension is a TERMINAL-POSITION proof: a
p-derived control whose owner (and every statement reachable under it) contains no test call,
no record store consumed before a test, and no execution-prevention edge, is presentation, not
gatekeeping. That is a narrowing of an abstention gate, which converts abstentions into
analyzer progress, so every 3.3 fixture set must re-prove the gated-screen negatives
(E10/E12/E13/E15 N6-type) still abstain or stay non-candidates.

## Delta candidates for MT 3.3, in priority order

1. Terminal-presentation proof for the hierarchy guard (unlocks P2+P4-shape: plain loops with
   summary counts; projected largest recall family - loops are the modal idiom).
2. Helper-returns-record consumer proof (P3-shape: compare()-style helper returning a dict
   with the conclusion computed adjacent to the test; consumer set closes inside the helper
   plus terminal presentation).
3. Library-subset cardinality (P5-shape) stays a residual pending the policy ADR (factor/input
   subset vs contract N).
4. Name-set-selected partial hand correction (P6-shape) stays the 3.2 documented residual; the
   question layer fired correctly (MaterialQuestion + ConditionalConcern raised blind).

## Scoring context

Window restarted at E16: 1/6 means promotion via E16+E17 requires 6/6 and is effectively
closed; the working window is now E17+E18 >= 7/12. Blind reviewer comparison: 6/6 positive
recall with 1 FA (N6 swimmers flagged MISSTEP; role-map negative; detector abstained
authorized-reader-lineage-unavailable). Lifetime detector record after E16: 0 FA over 311
blind cases (296 + 15).
