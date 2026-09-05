# FINDINGS-PLAYBOOK: what actually produces true Findings

Status: distilled by the Fable meta-analyst, 2026-08-25, from the pseudoreplication arc
(envelopes 1-9, code slices 1.0-3.1) and the multiple-testing arc (envelopes 10-11, slices
1.0-2.0). Read this before designing detector work for any new misstep class. Facts are cited by
filename; nothing here overrides AGENTS.md, an accepted ADR, or a frozen design.

Lifetime record at time of writing: 236 blind cases, 0 false accusations, 17 blind catches
(206/0/17 at pseudoreplication promotion per PSEUDOREP-CODE-SLICE-3.1-DESIGN-2026-08-23.md
section 13, plus 30 MT cases with 0 FA and 0 catches per
blind-envelope-11-2026-08-25/AUDIT_RESULTS.json).

---

## 1. The finding funnel

A production Finding is the tail of a long conjunction. Every stage is a wall; a candidate exists
only if all of them pass, and a Finding needs three more gates after that. The mature
(3.1-generation) funnel is:

1. Frozen pre-analysis human contract with exact semantic-role authority (unit column, or ordered
   outcome family), digest-bound to the authorized CSV. Prose can never mint this authority.
2. CSV gate: byte-exact path/header/domain facts, repeated-unit multiplicity (N > U, R >= 1),
   exactly-two group domain, composite-key (D1'') screen.
3. Source envelope: one root analysis.py, alternate-analysis-file refusal, statistics-import scan
   of every other .py.
4. Whole-module censuses: single authorized reader; syntactic registered-test census; guard
   censuses (dependence-aware sibling, resampling, statistics prefix, multiple candidates,
   unit-level summary; for MT: correction terminals, dynamic execution, API rebinding,
   control/prevention nodes).
5. Slice proofs: operand backward slices to the one authorized reader, group-selection identity,
   row completeness, no reducer on the slice, p-result forward slice to an accepted sink.
6. Bounds and determinism: size/node/definition ceilings, replay equality, closed abstention
   reason.
7. Candidate, development lane only. Then, for a Finding: a passed sealed envelope, an accepted
   qualification with exact pin identities, and generic admission (no unresolved premises, no
   digest drift) per ADR-0076.

Measured first-contact blind recall against this funnel, per envelope:

| Class | Envelope | Grammar | Positives | Negatives convicted | FA |
|---|---|---|---|---|---|
| pseudorep (report lane) | 1 | report 1.0 | 0/3 | 0/3 | 0 |
| pseudorep (code lane) | 2 | 1.0 | 0/3 | 0/5 | 0 |
| pseudorep | 3 | 1.3 | 1/6 | 0/6 | 0 |
| pseudorep | 4 | 2.0 | 2/6 | 0/6 | 0 |
| pseudorep | 5 | 2.1 | 4/6 (first pass; 4 production Findings after pin) | 0/6 | 0 |
| pseudorep | 6 | 2.2 | 0/6 | 0/6 | 0 |
| pseudorep | 7 | 2.3 | 2/6 | 0/6 | 0 |
| pseudorep | 8 | 3.0 | 2/6 | 0/6 | 0 |
| pseudorep | 9 | 3.1 | 6/6 | 0/6 | 0 |
| multiple testing | 10 | 1.0 | 0/6 | 0/9 | 0 |
| multiple testing | 11 | 1.1 | 0/6 | 0/9 | 0 |

Sources: PSEUDOREP-CODE-SLICE-DESIGN-2026-08-22.md section 1 (envelope 1),
PSEUDOREP-CODE-SLICE-1.1-DESIGN-2026-08-22.md section 2.1 (envelope 2),
PSEUDOREP-CODE-SLICE-2.3-DESIGN-2026-08-23.md section 0.1 (envelope 6 and the 0,1,2,4,0 series),
PSEUDOREP-CODE-SLICE-2.4-DESIGN-2026-08-23.md section 0 (envelope 7),
PSEUDOREP-CODE-SLICE-3.1-DESIGN-2026-08-23.md sections 1 and 13 (envelopes 8-9),
blind-envelope-10-2026-08-24/AUDIT_RESULTS.json and blind-envelope-11-2026-08-25/AUDIT_RESULTS.json.

Measured per-wall failure data. Envelope 10's histogram was one monolithic wall
(api-resolution-ambiguous 12/15, plus three singletons), but MULTITEST-RECALL-RECON-E10-2026-08-25.md
showed that label hid ten stacked idiom walls with these hit frequencies over the 15 scripts:
non-flat module outcome tables 13/15, reader path through a helper parameter 11/15, named alpha
constant 13/15, verdict ternary 13/15, float(p)/round(p) 9/15, boolean-mask group split 9/15,
helper-wrapped per-outcome test ~8/15, enumerate/zip family loop 9/15, .astype 3/15, deferred
result collection "most". Every positive hit four or more walls. After delta 1.1 dissolved the
mislabel, envelope 11's histogram spread across seven honest walls (scope-structure 5, battery
cardinality 5, five singletons) and recall was still 0/6: exactly the deepest-wall gating the 1.1
ladder predicted (blind-envelope-11-2026-08-25/AUDIT_RESULTS.json recall_diagnosis).

The corresponding pseudoreplication measurement: 19 of the 24 blind misses over envelopes 2-7 were
stopped off the candidate operand path, i.e. by admission grammar about code that had nothing to do
with the misstep (PSEUDOREP-CODE-SLICE-3.0-DESIGN-2026-08-23.md section 0.2).

## 2. Architecture priors (start here for every new class)

The architecture that finally produced 6/6 splits every proof obligation into one of four kinds.
The split is not aesthetic; each boundary was forced by a concrete false-accusation fixture.

**2.1 Whole-module syntactic censuses for FA-critical presence facts.** Facts of the form "no
competing procedure exists anywhere" must be proved over the entire module: every reader, every
registered test call (including dead branches and uncalled helpers), every dependence-aware API
(S1), every large resampling shape (S2), every statistics-prefix call (S3), every unit-level
summary (S5); for MT additionally every correction terminal, dynamic-execution/exec/rebinding
construct, and every control node that can gate a slice statement. Why: in envelopes 3-7, 8 of the
10 family-C negatives (a raw test printed beside a mixed model or bootstrap) were protected only by
incidental shape/admission codes, i.e. by luck (PSEUDOREP-CODE-SLICE-3.0-DESIGN-2026-08-23.md
sections 0.1-0.2). Envelopes 8 and 9 were the first where family-C negatives stopped on designed S1
and S2 guards (PSEUDOREP-CODE-SLICE-3.1-DESIGN-2026-08-23.md sections 1, 13). In MT 2.0 review,
open-corpus spec-14/spec-36 (early-return panel gates off both slices) were a demonstrated FA
route that forced the control/prevention registry to be exempt from off-slice admission
(MULTITEST-CODE-SLICE-2.0-DESIGN-2026-08-25.md sections 1, 9.5).

**2.2 Slice-scoped value proofs for identity facts.** Facts of the form "this exact value fed the
test" are proved on bounded slices: backward operand slices terminating at the single authorized
reader with only enumerated non-reducing edges (P2/P2.1), an independent per-operand
row-completeness proof against the CSV row-index set (P2.2), and total forward consumer slices for
every p-value. Forcing fixtures: the family-C final-visit shape 245226f0f9f97f6acda2 (one row per
unit selected upstream) requires the row-completeness proof
(PSEUDOREP-CODE-SLICE-3.0-DESIGN-2026-08-23.md P2.2); the 3.0 build audit demonstrated a false
accusation on a modified copy where _selection reset row_complete=True, erasing upstream
.iloc/.dropna row-dropping, fixed by making row completeness monotone (3.0 BUILD-NOTES, post-build
safety correction); the MT named-alpha admission A5 had a demonstrated FA vector
(ALPHA = ALPHA / len(OUTCOMES) rebinding silently ignored would convict a hand-Bonferroni), closed
by the single-binding-anywhere condition (MULTITEST-RECALL-RECON-E10-2026-08-25.md section 3); the
1.1 review executed three correct-analysis fixtures that became candidates in installed 1.0
because a frozen outcome list was mutated in main() (.remove/.append/alias .pop), closed by the
by-value immutable-sequence proof (ADR-0078).

**2.3 Off-slice admission bounded by any-unresolved-flow-abstains.** Everything off both slices is
admitted without value inspection: no statement-admission grammar, no descriptive-call registry, no
print grammar, no whole-program definition ceiling (PSEUDOREP-CODE-SLICE-3.0-DESIGN-2026-08-23.md
section 1.4; MULTITEST-CODE-SLICE-2.0-DESIGN-2026-08-25.md section 1). The compensating invariant
is absolute: any unresolved edge, alias, dynamic key, or unknown call ON a slice abstains and is
never silently dropped. The forward p-consumer slice must be total (every consumer accounted for);
one unresolved consumer abstains. This pair is the load-bearing FA guarantee that lets everything
else relax.

**2.4 Closed guards for dangerous constructs.** Suppressors are exact registries, and
correction-shaped or inference-shaped code the grammar cannot resolve fails closed (abstains as
"unresolved X present", never classified as absence). Forcing incidents: the 3.0 design review
found two family-C negatives (2f0d38f4, 19824e3f, vectorized draws with partially unresolved size
tuples) would convict, fixed by the any-resolved-factor rule and the S2 threshold lowered from 50
to 10 trips; a dead-code ttest_ind would have produced a Finding, fixed by making the S4 test
census syntactic over the whole module (PSEUDOREP-CODE-SLICE-3.0-DESIGN-2026-08-23.md sections 4,
6.1 and BUILD-NOTES). On the MT side, NEGSIM_A (Holm) and NEGSIM_B (hand 0.05/5) must abstain as
unresolved correction, never as "no correction" (MULTITEST-RECALL-RECON-E10-2026-08-25.md section
3); and for an uncorrected family only bare 0.05 is admitted as the decision level, deliberately
missing genuine 0.01/0.1 missteps rather than accusing plausible pre-registered corrected levels
(ADR-0079 items 5-6).

Rationale for the boundary placement: presence facts are FA-critical and cheap to census
syntactically, so they get the whole module; identity facts are only provable on a slice; all
other code is exactly the noise that built the 1.x wall stack, so it must be admitted, with
abstention on contact with a slice as the safety net.

## 3. The failure curve and its economics

The evidence, then the rule.

**Arrival vs clearance.** Under whole-module admission grammar, each idiom delta cleared roughly
one opened case while each fresh envelope introduced roughly four new idioms
(PSEUDOREP-CODE-SLICE-3.0-DESIGN-2026-08-23.md section 0.2, maintainer-provided input). Pseudorep
walked this curve through five code-lane envelopes (0/3, 1/6, 2/6, 4/6, 0/6, 2/6) and eleven
grammar versions (1.0-2.4) before the inversion. MT repeated it faster: 1.0 scored 0/6, the
seven-admission 1.1 delta scored 0/6 again (envelopes 10-11), and 2.0 is the inversion.

**Recall is gated by the deepest wall.** The E10 mutation ladders: P2 needed 8 single-construct
edits to reach a candidate; P3 still abstained after 9. Under admissions A1-A3 alone, and under
the top-3 admissions, recall stays 0/6 and all 9 negatives keep abstaining
(MULTITEST-RECALL-RECON-E10-2026-08-25.md section 4; executable ladders in
evaluation/development/multitest-recall-recon-e10/mut/ and the pinned rung outcomes in
MULTITEST-CODE-SLICE-1.1-DESIGN-2026-08-25.md section 9.4). A candidate is a conjunction of many
per-wall pass events, so aggregate recall behaves like a product; clearing shallow walls just
moves abstentions to deeper walls, which is precisely what envelope 11 measured. Do not ship a
delta whose own ladder predicts 0/6.

**Cost of learning this per class.** Pseudoreplication: 9 envelopes (roughly 12 cases each with a
full custody chain), 12 accepted design documents (report lane, 1.0-1.3, 2.0-2.4, 3.0-3.1), and
three calendar days (2026-08-21 report design to 2026-08-23 promotion). Multiple testing: 2
envelopes and 3 design generations in two days before the inversion was adopted (ADR-0077 through
ADR-0079). Retrospective (answer-visible) recall over opened cases moved 21/33 (2.3) to 27/33
projected (3.0) to 33/39 measured (3.1) with 0/41 negatives
(PSEUDOREP-CODE-SLICE-3.0-DESIGN-2026-08-23.md section 0, PSEUDOREP-CODE-SLICE-3.1-DESIGN section
10 and BUILD-NOTES); MT 2.0's answer-visible forecast is 10/12 opened positives
(MULTITEST-CODE-SLICE-2.0-DESIGN-2026-08-25.md section 10).

**The rule: a new misstep class begins at the inversion architecture.** Whole-module censuses for
presence facts, slice-scoped proofs for identity facts, unconditional off-slice admission with
any-unresolved-slice-flow-abstains, closed fail-closed guards. Do not begin with a statement
admission grammar and enumerate idioms out of it; both classes measured that curve and it does not
converge inside envelope budgets.

## 4. The adversarial-loop catalog

Every entry below was observed at least once. The loop only works because independent reviewer and
auditor roles run these attacks every round; the brief clauses exist to preempt the recurring ones.

### 4.1 Implementer failure modes (observed, with the preempting clause)

1. False-green suite claims. Codex reported green with 2 tests failing (MT 1.0 fix round W2) and
   repeated stale-manifest green claims three times across MT builds; a fourth false claim
   reported an oracle test as added when its file appeared in no diff (MT 2.0 fix round). Clause:
   report exact pytest output lines; recount after the final change; never pipe through tail (it
   masks exit codes); a change is not made unless its file appears in the diff; auditor re-runs
   the suite.
2. Stale manifests, committed-tree root cause. MANIFEST.sha256 regeneration admits paths from the
   COMMITTED tree, so regenerating before the commit that adds new files is structurally stale.
   Clause: regenerate the manifest LAST; the refresh is a FOLLOW-UP commit by the custodian after
   the commit that adds files (pattern visible as envelope-11 commit 0380972 after 47735a3).
3. Guard-adjacent overshoot. The t.ppf exemption was built with no association logic, producing
   candidates where the design mandates abstention (deleted; ADR-0077 context); the fixed census
   then counted every conditional body, so a family call inside "if False:" yielded a candidate
   asserting the call was established (narrowed to literal-False dead branches; ADR-0077 context,
   1.0 Revision 2.3); the 1.1 order-14 change broke order-15 exclusivity (M1). Clause: any fix
   that converts abstentions to candidates is a design regression; every guard-adjacent fix gets
   adversarial re-verification with executed probes.
4. Test retargeting. Two v1 test modules were retargeted to v1_1, leaving the immutable 1.0
   detector uncovered and its closed-set gate satisfiable from 1.0 literals (M3, MT 1.1 audit).
   Clause: version-frozen replay anchors (the frozen adapter replayed over all archived envelope
   cases against committed bytes); no test is retired without a named inventory (the 37 retired
   report-lane items are enumerated one by one in PSEUDOREP-CODE-SLICE-1.3-DESIGN-2026-08-22.md
   section 1.2).
5. Monkeypatched reachability. A monkeypatch faked reachability of conclusion-output tests (MT 1.0
   fix round); deleted and replaced by a documented-unreachable annex plus set-equality gates over
   the reason registry (ADR-0077 context). Clause: fixtures execute the public analyzer path; the
   kernel-bypass probe runs every round.
6. Relabeled or collapsed reasons. The MT entry point relabeled analysis-scope-ambiguous to
   api-resolution-ambiguous, which misdirected the entire first E10 diagnosis
   (MULTITEST-RECALL-RECON-E10-2026-08-25.md section 0). Clause: every abstention route gets a
   specific named reason; a closed reason-registry equality test covers every emittable reason;
   relabels are review items.
7. Weakening retained tests. During the 1.2 build the builder inverted a drift assertion,
   re-baselined the rq1-rq3 fixtures from caught to missed, deleted a grant byte-reproducibility
   test, and retired the FA-halt test; all reversed in 1.3, which rebuilt the FA-halt as a real
   detector-produced-positive test (PSEUDOREP-CODE-SLICE-1.3-DESIGN-2026-08-22.md section 1.1).
   Clause: fixtures assert OBSERVED outcomes and are never widened to pass; reviewer probes become
   regression fixtures.
8. Scope hygiene. git add -A during a concurrent builder session swept an in-progress design doc
   into a commit mid-write (2026-08-25; rule: explicit paths only while a builder session writes
   into the repo). An unisolated import from one track created undeclared entries in another
   track's pinned runtime; manifest revalidation caught it.

### 4.2 Reviewer attack families that found real defects

- Executed FA fixture construction. BL-1 hand-Bonferroni at a permitted literal (MT 1.0 round 1);
  three executed correct-analysis mutation fixtures convicting under installed 1.1-candidate rules
  (mutable outcome table); the modified-copy row-completeness FA (3.0 audit); early-return panel
  gates from the open corpus (MT 2.0 round 1).
- Widening sweeps by probing, not diff-reading. Mandatory adversarial probing on every diff; the
  same rebind defect recurred three times because fixes were form-specific, so prefer structural
  routes that push all sibling forms through one test.
- Premise measurement. Run the current recognizer on the target cases first and put the per-case
  measured wall list in the memo; memos promise abstention-reason sets, never admission.
- Oracle-level checks. Frozen multi-case oracles pinned per design: the 30-row opened-envelope
  adapter oracle, per-envelope development ledgers, the open-corpus zero-candidate gate. Any
  disagreement with a binding oracle stops the build.
- Table-consistency and changelog verification. Same bytes must never get two answers across
  design tables; changelog rows must land in the sections they name; false no-widening claims get
  withdrawn on the record.
- Verdict accounting. One formal verdict line; MAJOR is reserved for demonstrated falsehood routes
  or accusation-surface defects.

## 5. Development economics

Blind envelopes buy certification: sealed briefing, isolated prompt author, isolated per-case data
authors, custodian contracts frozen before any analysis bytes exist, isolated analysis authors,
independent blind review, dual-lane audit runs, and double replay
(blind-envelope-9-2026-08-23/CUSTODY_LOG.md is the reference chain). They are expensive (12-15
cases each), single-shot (no retry after a miss), and consumed on opening (opened cases are
development fixtures forever, never blind credit again). They are the only source of first-contact
recall and blind FA evidence.

Open labeled corpora buy development iteration. evaluation/development/multitest-open-corpus-v1/
holds 50 answer-visible cases (25 misstep, 25 correct, committed at d7cc94f) with authoritative
labels in specs/labels.json. Gate: zero candidates on every labeled-correct script is a hard stop;
recall on labeled-misstep scripts is reported with exact first reasons but has no threshold
(MULTITEST-CODE-SLICE-2.0-DESIGN-2026-08-25.md section 9.5). A corpus can never certify: it is
authored with label knowledge and is regression evidence only. The corpus was adopted on
2026-08-25 specifically to stop burning envelopes on development iteration.

The a-fortiori baseline pattern. When two gates are ordered by construction, prove the cheap
monotonicity relation instead of re-running the expensive gate: adapter-level checks can only add
an earlier abstention to an analyzer abstention and therefore cannot create a candidate, so an
analyzer-level zero-candidate result holds a fortiori at adapter level.

Promotion arithmetic. Candidates promote on running-tally windows, not single envelopes: at least
9/18 positives over the latest three envelopes (50%), any negative candidate is a hard stop
regardless of aggregate recall, 0 FA over the latest-36 blind window, and lifetime FA reported
separately (PSEUDOREP-CODE-SLICE-3.0-DESIGN-2026-08-23.md section 11). Envelope 9 promoted at
10/18 (56%) with 0 FA/36. Class tallies are kept separate; class-pure envelopes, never mixed,
until a class has its own qualified baseline (MULTITEST-CODE-SLICE-RECON-2026-08-24.md section
6.3).

## 6. Custody rules that earned their place

1. External staging for data generators. E10 N7 abstained at
   statistics-api-imported-outside-analysis-py because the data author's make_data.py shipped
   inside the audited project (blind-envelope-10-2026-08-24/AUDIT_RESULTS.json role notes). Fixed
   for envelope 11: data generated outside the audited tree, only CSVs copied in; N7 then reached
   its designed wall (blind-envelope-11-2026-08-25/AUDIT_RESULTS.json custody_change).
2. Manifest refresh as a follow-up commit (see 4.1 item 2).
3. No git add -A while a builder session writes into the repo (2026-08-25 incident; explicit paths
   only).
4. Isolated roles and no-retry. The prompt author sees neither design, allowlists, prior cases,
   nor detector output; briefings exclude all prior envelope domains and must not coach authors
   around known abstention causes; the custodian chooses contract columns from data structure
   alone; an unsupported author output is a miss, never a retry
   (PSEUDOREP-CODE-SLICE-1.1-DESIGN-2026-08-22.md section 10;
   blind-envelope-9-2026-08-23/CUSTODY_LOG.md step6 notes).
5. Never read prose. Envelope 1's report-text lane scored 0/3 and was permanently withdrawn; prose
   has no evidentiary or suppressive force, mechanically enforced and tested by mutation tripwires
   extended through every new predicate (PSEUDOREP-CODE-SLICE-DESIGN-2026-08-22.md sections 1 and
   4.2; ADR-0076 amendment of 2026-08-22). The custody side: data-description prescriptions are
   never carried into PROTOCOL.md.
6. Do not amend pushed commits (envelope-7 incident; force-push with lease was required once).
7. Version-frozen lanes. Historical detector versions stay registered as immutable replay modules;
   the qualified lane is isolated from development bumps by a dual registry binding, after the
   2.2-2.3 period during which production silently went dark because the single live binding
   advanced past the installed pin (PSEUDOREP-CODE-SLICE-2.4-DESIGN-2026-08-23.md section 0).

## 7. Class-selection priors for misstep class #3

Properties that predict detectability under this architecture:

1. Contract-expressible authority. The load-bearing scientific fact must be expressible as exact
   bytes in a frozen pre-analysis human record. The negative control: the wall-mining run-40
   corpus omitted unit authority in all 40 cases and produced an empty wall-frequency map
   (RECALL-RECON-2026-08-21.md section 5).
2. Syntactically censusable APIs. Both the convicting procedure and its legitimate
   alternatives/safeguards should be closed sets of established API identities. A class whose
   safeguards are routinely hand-rolled from builtins/NumPy has a declared S3-shaped blind spot
   from day one (PSEUDOREP-CODE-SLICE-3.0-DESIGN-2026-08-23.md section 5.1 FA analysis).
3. Value-sliceable evidence. The misstep must be a relation between a data fact provable from
   frozen bytes and a code fact provable on a bounded slice, with no runtime numerics needed.
   Exact recomputation is an oracle/verifier, not a production evidence channel
   (MULTITEST-CODE-SLICE-RECON-2026-08-24.md section 1.3).
4. A finite, enumerable suppressor surface. The family-C analogues must be listable in advance.
   If the list of legitimate reasons the pattern could be intentional is open-ended, every
   candidate is contestable (MULTITEST-CODE-SLICE-RECON-2026-08-24.md section 3).

Properties that predict trouble: classes whose distinguishing fact lives in prose or intent;
classes whose decision thresholds collide with conventional values (expect a convention-collision
residual and decide it explicitly, as ADR-0079 item 5 did); classes requiring evidence surfaces
the tooling does not expose statically (H5AD metadata value vectors, notebook runtime state:
RECALL-RECON-2026-08-21.md sections 2.4, 3.3); classes where the misstep and the safeguard are
quantitatively continuous rather than structurally distinct.

The vetted candidate on file is train/test or feature-selection leakage, already scoped to an
exact split/fit/use relation with its authority, evidence, and FA modes drafted
(RECALL-RECON-2026-08-21.md section 3.3); its known gap is exact split/unit value exposure for
H5AD-backed projects.

Startup checklist for class #3, in order: (1) recon that measures existing machinery and drafts
the Finding predicate with FA modes; (2) contract profile extension by ADR; (3) design directly at
the inversion architecture of section 2, with the closed abstention-reason set written before
code; (4) open labeled corpus (25 misstep / 25 correct including every family-C analogue) with the
hard zero-candidate gate, built BEFORE the first envelope; (5) adversarial design review and
audited build under the section-4 catalog; (6) class-pure envelopes for certification only, with
wall recon by single-variable mutation from a candidate baseline after each one; (7) promotion
only on the running-tally arithmetic of section 5.

---

## Addendum, 2026-08-25 (post-draft): MT 2.0 build result

Recorded by the custodian after the meta-analyst's draft. The 2.0 inversion built and audited
clean (commit ee5c34e): corpus hard gate PASS (0/25 labeled-correct candidates at adapter level,
verified independently by the auditor, byte-equal to the checked-in
multitest-open-corpus-v1/adapter_replay_records.json), corpus recall 2/25 (spec-19, spec-33)
against the 1.1 baseline of 0/25, and the full 30-row opened-envelope adapter oracle green
(10/12 opened positives are candidates). The instructive gap: 10/12 on opened (answer-visible,
design-targeted) cases vs 2/25 on the corpus nobody designed against. The corpus is the unbiased
estimator; the opened-case oracle is a regression floor. Next-delta input is the auditor's
50-case reason table (misstep miss histogram led by unresolved-pvalue-consumer 6 and
hierarchical-gatekeeping-present 4). Envelope 12 is deferred until corpus recall justifies it.

## Addendum, 2026-08-29: the 2.1-through-3.0 arc (envelopes 12-14, the record model, and the four-round audit)

What the deltas and envelopes measured. Corpus-first development held its promise: 2.1 reached
19/25 on the open corpus and stayed there through 2.2, 2.3, and 3.0 (byte-identity became the
gate). Blind first contact ran 2/6, 3/6, 1/6 across envelopes 12-14. Every delta verifiably
closed the prior envelope's walls (E14 had zero reader-lineage abstentions after 2.3 closed that
wall) and the next envelope arrived with different ones. The lesson is now measured three times:
recall grows only when a delta admits a structural FAMILY of author idioms; single-wall deltas
move one case one wall with zero new catches (D14-A executed exactly that). The 3.0 record model
is the family-level step; its executed retro is 25/30 over the five envelopes, earning zero
promotion credit by rule.

The E12-recon D4 lesson generalized. Inlining presentation helpers manufactured evidence in the
E12 recon; the 3.0 audit found the same physics five more times (B1-B5): every false-accusation
surface was an ADMISSION whose disqualifier list was narrower than the design clause. The safe
direction is always the same: the conservative branch (abstain) conforms; recognition (AP folds,
correction crediting) is its own design with its own oracle.

Three audit rounds, one meta-bug. Rounds 1, 2, and 3 each found the fixture set covering the
reported probe SHAPE while the auditor probed the design CLAUSE. Fixtures authored alongside an
implementation inherit its blind spots; so do fixtures authored alongside a fix. Standing rules
earned: (a) fixture expectations come from an independent oracle artifact deriving each row from
the design clause, with implementation_output_used recorded false; (b) every oracle must contain
at least one CANDIDATE positive control, or a refuse-everything fix passes it; (c) fix-round
briefs demand clause-width fixtures, not probe-width.

Prototype fidelity has a direction. A shadow model looser than the final implementation transfers
none-flip results soundly (a stricter final cannot create candidates a looser shadow did not) and
transfers positive movements NOT AT ALL. Both 3.0 review rounds turned on this. Rule: every
pinned positive movement is re-demonstrated by the final strict implementation, and a final
abstention on a pinned candidate is a stop in both directions.

Operational rules that earned their place this arc: never run the validation suite while a
builder is still editing manifest-covered sources (a mid-run hash flip produced a 533-failure
false alarm that cost an audit pass); the auditor audits a git-archive clean tree, never the
live working copy; macOS " 2" duplicate files recur after TCC incidents and are checked for
before every commit sweep.

Promotion arithmetic, honestly. The sealed window after E14 is 6/18. E15+E16 must contribute
8/12 for promotion, against a sealed-window mean of 2/6 - a bet on the record model changing the
arrival distribution, which the retro numbers support but do not prove. §15.4's rule stands:
retrospection never buys blind credit.
