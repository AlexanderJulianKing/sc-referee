# Qualification report: repeated authorized units entering a row-independent procedure

- **Check:** `check:authorized-independent-unit-entry-into-row-independent-procedure`, version
  1.1.0
- **Detector:** `detector:bounded-analysis-method-conflict` (question-only public output ceiling)
- **Binding:**
  `method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1`
- **Date:** 2026-08-10
- **Result: PASSED the sealed held-out block, seven of seven**, exactly meeting the accepted
  ADR-0072 threshold: zero candidates on five controls and both of two demonstrated errors caught

## The error class, in plain terms

A row can be a measurement without being an independent scientific unit. If several rows come
from the same authorized unit—for example, several measurements from one participant—but a
row-independent two-sample procedure receives all of those rows as if each were an independent
entry, the procedure's row count overstates the independent-unit count. This qualification is
narrower than pseudoreplication generally: it covers only an explicitly authorized unit-key column
in one digest-bound CSV, the frozen Python workflow grammar, and the registered procedure calls.

## How the detector recognizes it

Recognition is a static propose-then-verify pipeline. It never guesses which column is the unit
key and never executes author code during the audit.

1. A human-approved, digest-sealed authority lock names the ordered unit-key columns, the governed
   CSV bytes, the procedure, and the selected result scope. Missing or conflicting authority asks a
   question or abstains; it cannot produce a positive certificate.
2. The untrusted analyzer accepts only the frozen Python envelope: the two certified `csv.DictReader`
   forms, identity-only row lineage, an exact live callable from the three-entry SciPy 1.14.0
   registry, and one statically selected report sink. Every unmodeled subtree invalidates the
   values it may touch.
3. The controller-side CSV prover re-hashes the frozen input, reads strict UTF-8 under the
   certified line model, and proves the exact multiplicity of each byte-exact ordered key tuple.
   Empty keys, ragged rows, duplicate headers, digest drift, or proof ceilings cause abstention.
4. A small trusted certificate kernel rechecks thirteen closed obligations: source, reader,
   table, authority, fact closure, multiplicity, key domain, lineage, callable identity,
   safeguard completeness, noninterference, sink identity, and singleton resolution. Only its
   accepted certificate can become an evaluation candidate or a covered-negative observation.
5. The unchanged generic method-conflict detector compares the certified observed operand with the
   exact human requirement. The public ceiling remains question-only; this report records no
   production Finding authority.

## Development record: four blind pilots and the threshold rehearsal

All case authors and reviewers were blind to detector output. The two refused pilots are retained
as protocol outcomes, not erased or scored as detector attempts.

| Run | Sensitivity | False accusations | Honest outcome |
| --- | ---: | ---: | --- |
| pilot a | n/a | n/a | **Review-unresolved; detector never ran.** The template paired the two collections on every row. Primary and escalation reviewers unanimously found the three nominal controls in-class, contradicting the answer key, so the protocol refused to launder the key. |
| pilot b | n/a | n/a | **Closed at intake; review and detector never ran.** All six honest author submissions violated a byte-frozen workflow template that the author-facing brief had not stated byte-exactly. The configuration defect was category-closed with one shared template constant. |
| pilot c | 1/1 | 0/5 | **Passed 6/6.** The pasted-row positive was caught; all five controls stayed nonpositive. Escalation did run for the ambiguous case after the primary returned a conditional question; it resolved cleanly with no unresolved case. |
| pilot d | 1/1 | 0/5 | **Passed 6/6.** The positive used different repeated measurements rather than pasted rows; the all-distinct hard negative had a report byte-identical to the error and stayed clean. No escalation ran. |
| threshold rehearsal | 2/2 | 0/5 | **Passed 7/7.** The second positive used three measurements per unit and `mannwhitneyu`; all five controls stayed nonpositive. This rehearsal happened after the ADR-0072 bars were accepted and supplied no threshold-setting evidence. |

The two completed six-case pilots were 12/12, and the seven-case rehearsal was 7/7. Those results
show consistency inside the deliberately narrow frozen workflow; they do not enlarge the sealed
exam or its two-positive denominator.

## The sealed held-out examination

The seven held-out case identities and briefs were digest-sealed before authoring. ADR-0072 froze a
two-of-two sensitivity bar and zero-of-five false-accusation bar before the threshold rehearsal.
The heldout opening then bound that accepted decision and the still-unobserved heldout block before
exam authoring. Authors, reviewer, and detector used fresh seats that did not participate in the
rehearsal.

| Case | Role | Static detector outcome | Qualification outcome |
| --- | --- | --- | --- |
| `case:8a68d6ae147ce49e2a11` | error-bearing, `ttest_ind` with two different measurements per authorized unit | evaluation candidate | **caught (true positive)** |
| `case:c37ea6f502dc593de820` | independently renamed implementation, `mannwhitneyu` with three measurements per authorized unit | evaluation candidate | **caught (true positive)** |
| `case:a516621a9cc0c4f6854d` | corrected twin, one row per authorized unit | covered-negative note | clean (true negative) |
| `case:e9e6bf9e80c9287dabe5` | valid alternative, one row per authorized unit | covered-negative note | clean (true negative) |
| `case:6f1702f1e1ff3855d34f` | hard negative, 24 distinct authorized keys and an error-byte-identical report | covered-negative note | clean (true negative) |
| `case:75bb533785f478cbdd8d` | ambiguous unit authority withheld | ambiguous abstention (independent-unit-definition-unresolved) | abstained, clean (true negative) |
| `case:c41c53bc6fedd68b0ccc` | paired `ttest_rel` procedure | named `paired-procedure-operand-unverified` abstention | abstained, clean (true negative) |

Integrity: one attempt; reviewer labels matched all seven sealed roles; no escalation and no
unresolved case; labels froze before detector observation; deterministic replay was byte-equal;
two evaluation candidates and zero production Findings; the static detector audit executed no
project-authored code. Intake separately ran the authored fixture workflows in the pinned sandbox
to establish ground-truth report bytes; that is not execution evidence for the recognizer.

Six retained opening/ledger digests:

- opening:
  `sha256:8599661c954459daad710f61462ee3666dab8d9659f94e94714824ee6ad67c61`;
- authoring protocol:
  `sha256:458c7176308c33de64bde0922823a2c4c7e91a1d1bc90ec86693ace0e86ed596`;
- intake ledger:
  `sha256:dbab0dd56d330192e7e8ed4d68b6e7612e0fb4a8d4ad50d59b8c5f0d0e4a6b83`;
- review ledger:
  `sha256:6d3fac7bd3791aeffc161e406a6ab7b87e753347a3476a80d2ae2d0fe9d57019`;
- scientific-label ledger:
  `sha256:10566c55b4a863ab174a94090a50d542f9f0e8464a979251c74e25efc91df55e`;
- detector-run ledger:
  `sha256:7beb928087f8073f543636e0231e7fc57c1f9a843ea182107bf0b121a2e3d9d5`.

## Disclosures

- **Role-derived authority.** The ambiguous control received no dependence-authorization lock by
  construction, while every other role received one. Detector behavior keyed on authority was
  therefore also keyed on a role-derived signal.
- **`requirements.txt` evidence asymmetry.** The detector observed the controller-supplied pinned
  requirements material (`scipy==1.14.0`, `numpy==2.2.6`), while the blind reviewer did not. The
  detector/reviewer comparison was not evidence-blind agreement.
- **k1 namespace scope.** Authority named `k1`, and every covered-negative proof established one
  analyzed row per authorized `k1` unit only. It made no clearance claim about the `k2` namespace
  or dependence structures outside the named key.
- **Review-scope sentence's one-directional effect.** Review instructions said concerns outside
  the exact issue class were out of scope. Its known practical effect was one-directional on the
  paired-procedure control: it steered the reviewer away from relabeling a different pairing
  concern as this issue class. The detector independently abstained with
  `paired-procedure-operand-unverified`.
- **Unblinded orchestrator lock minting.** Authority locks were minted after intake by the
  unblinded orchestrator. Blindness covers authors, reviewers, and detector development, not the lock
  minter. The locks record human-approved scope; they are not execution evidence.
- **Agent-only review.** Scientific labels were established under ADR-0067 by one calibrated blind
  model reviewer, with escalation reserved for a non-clean result, rather than by human scientific
  experts. The heldout review was clean and did not fire escalation.
- **Single-provider composition.** ADR-0066 permitted the available single-provider design. The
  heldout authors and reviewer were Anthropic model contexts (Opus authors, Fable reviewer); there
  was no cross-provider heldout composition.
- **Acceptance before rehearsal.** The maintainer accepted ADR-0072 and its two-of-two/zero-of-five
  bars before the threshold rehearsal ran. The rehearsal was a dress rehearsal for the seventh
  construction, not pilot evidence used to choose the bars.
- **One shot.** No heldout case was repaired, re-authored after admission, or rerun for its score.

## Limitations

- Qualification covers one exact binding, check version, adapter, grammar, detector manifest, and
  scientific-check registry tuple. It does not promote sibling bindings or the shared detector
  generally.
- The qualified grammar is intentionally small: strict CSV, the two certified `DictReader` forms,
  identity-only row lineage, a byte-frozen statement-form Python template, a pinned SciPy 1.14.0
  callable, and one exact selected writer path. Pandas, filtering, aggregation, wrapping, dynamic
  dispatch, larger membership domains, and unrecognized newline/write models abstain.
- The only covered-negative route is one digest-bound row per authorized unit. Paired-procedure
  operand alignment and unit-level aggregation remain named gaps.
- Both heldout positives exercise exact unit-key multiplicity under the same proof architecture.
  The renamed positive changes the procedure and repetition structure, not the frozen workflow
  grammar.
- Seven problem clusters are too few for strong distributional claims. Cluster-aware intervals
  are reported, but ADR-0072 uses exact point-estimate and count gates.
- Zero observed false accusations is evidence for this envelope, not a correctness certificate,
  domain-wide pseudoreplication detector, or permission to issue production Findings.

## Replay

The lane is content-addressed and retained in the repository. The dependence driver and generic
lean pipeline revalidate the opening, authoring, intake, authority, review, label, and detector
digest chain. Every detector entry records `replay_equal: true`. The evaluation-private projector
in `evaluation/src/sc_referee_evaluation/dependence_promotion.py` independently rechecks the six
published digests, the exam-time tuple, all seven closed outcomes, and the ADR-0072 bars before it
can compile qualification metrics.
