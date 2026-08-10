# Pilot-b protocol notes (recorded at lane creation, before intake)

1. **Correction of the pilot-a commit message.** Commit `fc91a19` describes pilot-a's outcome as
   "Primary and escalation reviewers genuinely disagree." The official review record
   (`pilot-a/review/REVIEW_LEDGER.json`) shows the opposite: the primary reviewer
   (`fable-10`) and the escalation reviewer (`opus-08`) unanimously returned
   `demonstrated_issue` on the three control cases; the disagreement was between both
   reviewers and the answer key. The escalation mechanism can confirm the key or leave a case
   unresolved; it cannot overrule the key, and it correctly left the three cases unresolved.
   The retired attempt's verdicts (`opus-07`) are evidentially void and were mistakenly cited
   in contemporaneous session notes. Two independent blind reviewers found the pilot-a case
   template itself instantiated the issue class in every case; envelope-b's disjoint-collection
   template is the response.

2. **Known one-directional effect of the review-scope sentence.** Pilot-b's review instructions
   append: "Judge only whether this exact issue class is demonstrated in the selected report.
   Other methodological concerns, however serious, are outside this review and must not be
   recorded as this issue class." The sentence names no role, verdict, or data pattern, but its
   practical weight falls mostly on the paired-procedure (`ttest_rel`) case, where a real
   concern of a different class exists and the sentence steers the reviewer away from recording
   it as this class. Recorded here as a deliberate, disclosed asymmetry rather than a neutral
   edit.

3. **Scope of the covered-negative observation.** The detector's `covered_negative` route
   proves one analyzed row per authorized `k1` unit over the digest-bound input. The `k2`
   collection's items are equally real source items under the task declaration, but no per-row
   key can name 24 items across 12 rows, so the covered-negative observation is scoped to the
   `k1` namespace and asserts nothing about `k2` repetition. In these six cases the gap is
   empty: the only planted repeat duplicates whole rows, repeating both namespaces.

4. **Authority approvals.** The five per-case authorization locks are written under the
   maintainer's recorded standing authorization (see
   `~/Desktop/random_stuff/sc-referee-design-memos/standing-authorization-2026-08-10.md`),
   scope-limited to this envelope template; the ambiguous case receives no lock by design.

## Pilot-b closure (recorded after intake refusal)

Intake refused all six authored cases with `frozen-workflow-template-mismatch`. Cause: the
frozen-workflow-template enforcement (commit 655c960) was added at intake without updating the
author-facing case requirements to state the template byte-exactly; both authors produced
semantically identical workflows in their own import styles (`from scipy.stats import X` and
`import scipy.stats`), which the analyzer certifies but the template check refuses. The authors
were honest; the configuration was internally inconsistent. Per program rules no authored file
is repaired by sighted editing: pilot-b is closed at intake, its authoring artifacts retained
byte-complete. No reviewer or detector observed any case, so reviewer `fable-11` and escalation
`opus-09` remain unspent. Author identities `opus-15` and `opus-16` are spent. Pilot-c proceeds
with the case requirements carrying the frozen template verbatim and fresh authors
`opus-17`/`opus-18`.
