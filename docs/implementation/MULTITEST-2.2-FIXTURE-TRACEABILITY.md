# Multiple-testing 2.2 fixture traceability map

Closes audit minor m1 for the 2.2 build (commits 6da8c75 + 4b496b0). The design
(MULTITEST-CODE-SLICE-2.2-DESIGN-2026-08-26.md, Revision 0a, sha256
64041f538ef64b4f1307702fa7c43b594dc745e10a93a30e572cdda8492a0a39) declares six
normative §8 fixture long-names. The repository implements every one of those
behaviors, but under the short recon keys from the E12 recon plus
separately-named delta tests. This map is the authoritative correspondence; the
audit independently executed each row and confirmed the asserted outcome.

| Design §8 normative name | Implemented as | Asserted outcome |
| --- | --- | --- |
| FA-2-conditional-subexpression-family-call | test_d2_refuses_lazy_family_call | abstain: test-battery-cardinality-unresolved (distinct fixture from recon FA-2, which asserts unresolved-manual-correction-present) |
| FA-3-complete-hand-bonferroni-len-contract-table | recon key FA-3 | covered/complete |
| FA-5a (mutated membership set) | recon key FA-5 | abstain: analysis-scope-structure-unsupported |
| FA-5b (whole-family membership set) | recon key FA-5b | covered/complete |
| FA-6a (secretly adjusting presentation helper) | recon key FA-6 | abstain: unresolved-pvalue-consumer |
| FA-6b (nested computed threshold) | test_d6_nested_computed_threshold_stays_unresolved | abstain: unresolved-pvalue-consumer |

Recon keys FA-2 (inline-comprehension battery with whole-family Holm,
abstain: unresolved-manual-correction-present) and FA-3b (multiplier is len()
of a non-family container, abstain: unresolved-manual-correction-present)
predate the design's §8 list and remain in force unchanged.

Audit minor m2 (the 1.0 closed-set gate glob at
test_code_csv_multiple_testing_abstention_reasons_v1.py:307 is unscoped and now
satisfiable from later-lane literals) is carried forward deliberately: every
later lane's gate is correctly scoped, and retro-scoping a frozen 1.0 test file
is not worth touching a frozen surface. Recorded here so the carry-forward is a
decision, not an oversight.

## 2.3 audit carry-forwards (2026-08-27)

The 2.3 audit (APPROVE-COMMIT, commits c251bcc + a33200c) carried two minors, both deliberate:

- m1: test_multiple_testing_e10_replay_v2.py keeps its stale _v2 name while correctly running the
  ACTIVE binding (now 2.3) against the E10/E11/E12 45-row expectations. The content is the right
  gate; the rename to an "active-binding" name is deferred to the next audited build rather than
  applied post-audit by the custodian, because test-file renames touch suite collection.
- m2: the 1.0 closed-set gate glob (documented above) remains as recorded.

## 3.0 audit carry-forwards (2026-08-29)

The 3.0 build cleared audit on round 4 (APPROVE-COMMIT at b5b04a4 + 143c3ec) after five
false-accusation surfaces (B1-B5) were found by constructed probes and closed as narrowings.
Two items carried for the record:

- The §6.5 AP(C, POS) branch (recognizing an in-record hand correction as a COMPLETE correction)
  is absent, not just deferred: every in-loop hand-correction shape abstains. Safe direction. A
  future round that builds AP recognition reopens exactly the surface that produced B1, B4, and
  B5 and must carry probe coverage at least as wide as this build's cumulative set.
- Three round-3 oracle rows join §6.5 prose to its code block (the round-1 convention). A
  stricter reading of the quote-vs-paraphrase split would mark them paraphrase; faithful either
  way, recorded for the next oracle edit.
