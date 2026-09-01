# ADR-0079: Multiple-testing code-slice 2.0 architecture inversion

- **Status:** Accepted
- **Date:** 2026-08-25
- **Acceptance provenance:** the supervisor approved design Revision 2 for build
- **Decision owners:** Alex / sc-referee maintainers
- **Scope:** Development-only multiple-testing code slice `2.0.0`
- **Companion design:**
  `docs/implementation/MULTITEST-CODE-SLICE-2.0-DESIGN-2026-08-25.md`, Revision 2,
  `sha256:c435efab3a821131192e783fa4d1fdc217418f3101b0cf6299bb6e867d2236c5`
- **Execution impact:** None; project-authored code remains unexecuted
- **Production impact:** None; no qualification, grant, GrantPin, or production Finding authority is
  installed

## Context

Envelopes 10 and 11 each produced zero false accusations and zero Findings but zero of six
first-contact positive candidates. The 1.x recognizer required realistic analyses to cross many
independent whole-module value grammars. The accepted 2.0 design retains the whole-module evidence
needed to exclude hidden tests, corrections, inference siblings, repeated constructs, dynamic
execution, API rebinding, and execution-prevention controls while moving operand and p-value proofs
to bounded value slices.

## Decision

1. Add check, adapter, and detector version `2.0.0` under the stable multiple-testing semantic IDs
   and advance only the development binding. Versions 1.0 and 1.1 remain immutable replay modules.
2. Keep the registered-test, correction-terminal, statistics-prefix, and repeated-construct
   censuses whole-module and syntactic. Add abstention-only dynamic-execution and API-rebinding
   censuses. Operand identity and complete-row equality use backward value slices; every local family
   p value uses a total forward consumer slice.
3. Off-slice statements and helper bodies are admitted without value inspection except for the
   whole-module control/prevention registry. That registry includes the closed 1.0 control-node set,
   early exits that can prevent a slice node, and the unresolved prevention residual.
4. The hierarchy implementation is a versioned copy. Its only presentation exclusion is the exact
   terminal-rendering grammar with total forward accounting; it is not a general verdict-text or
   branch exemption.
5. For an uncorrected family with `N >= 3`, only bare `0.05` is admitted. Bare `0.01` and `0.1`
   abstain. This deliberately misses genuinely uncorrected analyses at those levels to avoid
   accusing plausible pre-registered corrected levels.
6. When any recognized correction exists, the admitted comparison set remains
   `{0.01, 0.05, 0.1}`. Consequently, an `N = 4` strict-subset analysis whose excluded raw members
   use pre-registered `0.01` remains convictable because `0.01 * 4 = 0.04` does not trigger the
   product rule. This is an accepted residual, not evidence that the level was uncorrected.
7. The live-conditional rule is an abstaining conservative rule. It does not restore the
   candidate-producing branch traversal withdrawn by 1.0 Revision 2.3.
8. `analysis-scope-structure-unsupported` changes predicate meaning: 1.1 used it for the chosen
   module/setup grammar, while 2.0 uses it only for tracked outcome-sequence stability. Reason
   distributions across those versions must never compare the two occurrences as one predicate.
9. Contract profile `1.2.0` and the existing Finding wording profile remain unchanged. Code, CSV
   values, and closed API identities remain the only detector evidence channels; prose is excluded.

## Isolation

Only development MT manifests, the active development binding, the lane-inclusive registry digest,
and downstream locks directly binding that digest may change. Qualified pseudoreplication 3.1,
complete-domain components, grants, GrantPins, qualifications, Findings, wording profiles,
`method_conflict_grant_pins.py`, every dependence dataflow module, and the 1.0/1.1 MT modules remain
byte-invariant.

## Validation and stop rule

Every companion-design gate is mandatory: exact guard adversaries, total consumer accounting,
closed reason equality, the 30-case adapter oracle, PROBE/NEGSIM and ladder replay, historical
anchors, and the 50-case adapter-level open-corpus gate with zero candidates on 25 labeled-correct
scripts. Any disagreement with a binding oracle is a design regression; implementation stops rather
than widening a grammar or relabeling an outcome.

## Delta 2.1 amendment

The accepted delta design
`docs/implementation/MULTITEST-CODE-SLICE-2.1-DESIGN-2026-08-25.md`, Revision 1a,
`sha256:d468fba746b6eb741f5cc47abc6bd5e5e529ff3e63988f80ec8c3a8c208e4165`,
advances only the development check, adapter, and detector to `2.1.0`. It adopts the closed R1,
R2/R3b, R4-R7, R9-R16, and R18 value transports exactly as specified there; R16 is one indivisible
transport-and-position rule, and R2/R3b uses one shared classifier in both hierarchy exclusion and
conclusion credit. R8 and R17 remain declined. Treating `p < ALPHA/K` as manual Bonferroni coverage
remains deferred to a future policy ADR.

The `MASK.sum()` presentation read is an intentional design-time extension beyond the recon's R9
summary, admitted solely for the nonfeeding, registered-sink-only spec-25 shape. It never supplies
row selection or control provenance. R12 refuses helper, conditional, and loop-carried stores;
R15 is the only origin-reducing rule and falls back conservatively on any unresolved record store.
No whole-module census, threshold/product rule, correction guard, row-completeness proof, qualified
lane component, wording object, grant, GrantPin, qualification, or Finding authority is weakened.
Revision 1a records that R5 exposes `spec-47`'s deeper
`unresolved-decision-threshold` wall; the case remains an abstention and no candidate surface
changes.

## Delta 2.2 amendment

The accepted delta design
`docs/implementation/MULTITEST-CODE-SLICE-2.2-DESIGN-2026-08-26.md`, Revision 0a,
has raw SHA-256 `64041f538ef64b4f1307702fa7c43b594dc745e10a93a30e572cdda8492a0a39` and
advances only the development check, adapter, and detector to `2.2.0`. It adopts D2 statement-level
family-call normalization, D3 exact contract-table cardinality, D5 immutable contract-header set
membership, and D6's second invocation of the unchanged terminal-helper transformer. The global
censuses continue to consume only the untouched source tree. D2 preserves a one-to-one dynamic
occurrence map and evaluation count; D3 answers only the existing manual-correction family-size
query; D5 is never an order, iteration, position, or cardinality source; and D6 is structurally
idempotent.

The one-argument unshadowed `sorted(OUTCOME_SET)` presentation read is an intentional design-time
extension beyond the E12 recon summary. It is admitted only off every test, correction, p-value,
and control slice and supplies no analyzable result. D5 admits only `ast.Set` displays, never a
`frozenset(...)` call. Consequently, `analysis-scope-structure-unsupported` gains a second 2.2
predicate for failed D5 set stability, alongside the 2.0 outcome-sequence-stability precedent.
Occurrences of that reason string in 1.1, 2.0/2.1, and 2.2 name different predicates and must never
be compared across versions as one measure.

D1 and D4 remain withdrawn. In particular, presentation-helper inlining manufactured false
decision/correction evidence in the executed recon; repeating the closed transformer is the safe
ordering equivalent. The complete hand-Bonferroni D3 fixture and complete frozen-set D5 fixture
resolve covered/complete, which are deliberate safe removals of conservative abstentions rather
than new candidate surfaces.

## Delta 2.3 amendment

The accepted delta design
`docs/implementation/MULTITEST-CODE-SLICE-2.3-DESIGN-2026-08-27.md`, Revision 1a,
has raw SHA-256 `4cfed92169acd51154fd110c351a23421454501e090aaf9c2ed662b8a4feb5e5`
and advances only the development check, adapter, and detector to `2.3.0`. D13-A adds one exact
function-local reader-path value edge for the closed `os.path` and `pathlib` productions. The
module-wide unique-binding, no-alias, no-mutation, no-escape proof is mandatory; the binding is
never a frame root and the reader APIs, keyword grammar, and row proofs remain unchanged.

D13-B closes provenance only between an already-recognized terminal rendering and one jointly
matched final sink clone. The immutable composite relation includes source position, complete AST
structure, singleton family position, transport-to-decision containment, ordered occurrence
multiplicity, and one-to-one clone ownership. One map is shared by off-grammar exclusion,
hierarchy exclusion, and conclusion credit. It runs after the successful 2.2 D6 second-pass
equality check, mutates no AST, and is idempotent including descriptor multiplicity.

The combined implementation retains the executed `0/25`, `0/36`, and `0/6` none-flip gates. P2's
exact `2N` call count and P6's proper-subset manual factor remain deliberate residuals requiring
separate evidence/wording and correction-policy review. The only opened row movements are E13 P5
to `strict_subset {0,1}/7` and E13 P6/N1/N9 to their specified deeper abstention walls.

## Record-model 3.0 amendment

The accepted record-model design
`docs/implementation/MULTITEST-CODE-SLICE-3.0-RECORD-MODEL-DESIGN-2026-08-28.md`, Revision 1b,
has raw SHA-256 `e950b6015198c92e7f7f16d30f901be9f131c0145e96524a22df4e33ed6ec166`
and advances only the development check, adapter, and detector to `3.0.0`. It adds one closed
symbolic record graph for exact list-appended Dict/Tuple/R4 records, exact positional subsets, a
minimal bounded DataFrame row table, and static table-selected dispatch between the two registered
two-group APIs. D14-A adds only the exact singleton projection-binding cardinality normalization.

The frozen family-member rule already requires one registered two-group test per authorized
outcome; it does not require API uniformity. Version 3.0 therefore replaces the pre-3.0 uniformity
guard with an exact one-call-per-position dispatch plan. Unresolved, input-derived, unregistered,
double-call, or operand-inconsistent dispatch abstains. Evidence profile
`code_csv_multiple_testing_evidence_v2` records the ordered API identity at every family position
and its derived sorted set. Wording profile
`method-conflict-finding:code-csv-complete-family-correction-requirement-conflict-v2` deletes the
singular `TEST_API` slot and states only the proved per-position registered-call count. All other
wording bytes and non-inferences are retained.

Record, subset, and DataFrame admissions are transports, not correction or threshold recognizers.
Whole-module registered-call, correction-terminal, statistics-prefix, dynamic-execution,
API-rebinding, repeated-construct, and prevention censuses remain authoritative. Every unresolved
p/record/table consumer abstains, and section 6.4's final implementation refuses any store after a
p/flag/table field consumer. `mixed-test-api-family` is retired only in 3.0; its pre-3.0 uses are
not comparable to the eight new closed record-model reasons. Zip write-back, proper-subset manual
factors, and `p < ALPHA/K` correction coverage remain excluded.

The Revision-1a shadow sweep is a build oracle, not a production dependency. Its admission may be
looser than the final grammar, so none-flip evidence transfers to a stricter implementation but
positive movements do not. Revision 1b consequently requires the final strict implementation to
re-demonstrate E12 P5 and E14 P2/P4/P5; either a missing pinned candidate or a new candidate on a
pinned noncandidate is a stop-and-report regression.

## AP correction-recognition 3.2 amendment

The accepted design
`docs/implementation/MULTITEST-3.2-CORRECTION-RECOGNITION-DESIGN-2026-08-29.md`, Revision 1a,
has raw SHA-256 `81e5db51d8f93983497baa7c121dc28ac7dbd3e959dc4961696b87f7e27641bf`
and advances only the development check, adapter, and detector to `3.2.0`. AP recognition is a
closed normalization, never an independent classifier: it subtracts one proved-unique exact
Bonferroni fold and requires the byte-frozen 3.0 analyzer to prove the remaining raw family and
conclusions independently.

The only factors admitted are an integer literal equal to the contract family size, exact
`len(NAME)` whose resolved position-zero headers are byte-order-equal to the contract outcomes,
or one stable direct binding to either form. Alias chains, factor mismatch, duplicate folds,
mutation, merge, polarity, unresolved consumers, cross-function record flow, and all B1-B5
laundering variants remain abstentions. Strict-subset coverage requires corrected conclusions at
every position in `C` and proved raw conclusions at every position outside `C`; complete coverage
requires all contract positions.

The 3.1 question and asymmetric-attestation policy is unchanged. AP removes a question only when
scope is structurally proved. From 3.2 onward a B-answer location may prioritize AP as an existing
check, but the Answer and claimed factor never enter the proof; answer removal must produce the
same corrected positions. Blind scoring, public record types, wording, and qualified lanes remain
unchanged.

## Terminal-presentation and helper-record 3.3 amendment

The accepted design
`docs/implementation/MULTITEST-3.3-TERMINAL-PRESENTATION-DESIGN-2026-08-30.md`, Revision 0,
has raw SHA-256 `cbc37990e9a713c486bf903cefef03c08ad264e7b6112383330b56a0c3f6c224`
and advances only the development check, adapter, and detector to `3.3.0`. Instrumented frozen-
3.2 execution establishes that E16 P2 is blocked by its verdict `IfExp`, E16 P4 by its
presentation `If`, and E16 P3 by unresolved helper-returned record consumption; terminal count
syntax alone is not treated as the trigger.

Version 3.3 adds two proof facts and no scientific classifier. The terminal proof excludes only
one exact control occurrence after total downstream-consumer and execution-prevention checks.
The helper proof admits only one top-level synchronous, single-call-site helper returning one
flat literal record into one complete-family comprehension, with total p/conclusion consumer
accounting. The hierarchy control universe remains global; only immutable proved occurrences are
excluded. Global test, correction, statistics, repetition, dynamic-execution, API-rebinding, and
outcome-mutation censuses always inspect the untouched source tree. The existing 3.2/3.0 analyzer
alone re-proves operands, rows, family cardinality, thresholds, conclusions, correction/AP state,
and classification.

The executed movement set is exactly E16 P2/P3/P4 to uncorrected-family candidates at `N=6/5/7`.
The final implementation must re-demonstrate all three, while every prior row and pinned
noncandidate stays unchanged. The no-attestation correction-scope census is `25 -> 25`: those
three cases carried publication-surface questions, not MT correction-scope questions, so no
unrelated MaterialQuestion may be removed. Wording, contract profile, qualified lanes, blind
scoring, and the asymmetric attestation rule remain unchanged; answer-guided proof may do nothing
that the answer-removed path cannot reproduce.

## Comprehension, iterator, and cap 3.4 amendment

The accepted design
`docs/implementation/MULTITEST-3.4-COMPREHENSION-ITERATOR-DESIGN-2026-08-31.md`, Revision 0,
has raw SHA-256 `2f7bd77e1020777c9fcdc5573edc87c43567ba153fd3fc1f801926752993c854`
and advances only the development check, adapter, and detector to `3.4.0`. Version 3.4 adds three
narrow syntactic admissions, specifies a fourth that is not shipped, and records one reason defect
without correcting it. It adds no scientific classification rule, test API, correction form,
threshold, family-position source, row-mask route, reader, reducer, record mutation, conclusion
polarity, or wording rule.

**Observed trigger attribution.** Instrumented execution of the shipped 3.3 hierarchy guard shows
that E17 P3 `a2e031f79e31c80fd900` stops at exactly one tracked control, the line 71 columns 35-54
`result['p'] < ALPHA` compare, with **zero** p-origins, no correction control, and all six contract
outcome headers. The control is tracked only by the outcome-headers branch of `_control_tracked`,
so `hierarchical-gatekeeping-present` asserts a gate that was never demonstrated. The zero-p-origin
finding is the same fact that causes the miss: the dict comprehension is never normalized into the
record model, so `result["p"]` resolves to no p-origin. E17 P6 `b4e507c4b55954752f14` tracks no
hierarchy control at all; it is blocked by `enumerate(OUTCOMES, start=1)` failing the bare-Name row
table and by the cap reassignment competing with the product in the single-reaching-fold proof.
Both walls are spelling, not science: an author who writes the same computation as an explicit loop
with `min(p * F, 1.0)` was already caught.

**Extension A, the comprehension grammar and its lowering.** One `ast.Assign` or `ast.AnnAssign`
with a single `ast.Name` target whose value is a one-generator `ast.DictComp` or `ast.ListComp`,
whose generator is not async and carries no `ifs`, whose target is a simple Name, whose iterable is
a bare Name resolving to a stable module sequence that is order-equal to the contract outcome
tuple, whose dict key is exactly the generator target, and whose element is one closed `SCALAR`
call or one flat literal record of `SCALAR` values that loads the generator target, is lowered to
the equivalent explicit loop. The collected name must have exactly one Store or Del in the whole
module and may never be augmented, deleted, subscript-stored, or receiver-mutated elsewhere.
`ast.Lambda`, `ast.NamedExpr`, `ast.Await`, `ast.Yield`, `ast.YieldFrom`, `ast.IfExp`,
`ast.Starred`, any nested comprehension, `ast.JoinedStr`, `ast.Slice`, and any keyword-carrying
call inside the element are absolute refusals. The lowering is a graph fact: production builds an
`ast.Module` and never rewrites source text. Element identity and idempotence are asserted at
runtime on every lowering.

**Extension B is specified and not shipped.** The print-only terminal `IfExp` production is stated
in full in design section 5 with its three named verdict-store disqualifiers. It is not installed
in the shipped recognizer set. The executed evidence is decisive in both directions: across all 170
evidence cases and all 245 fixtures it admits zero positions on any abstaining row, and on E16 P4
its one admitted `IfExp` position at `(82, 35, 82, 60)` collides with the 3.3 single-occurrence
requirement in `prove_terminal_presentation`, which then returns `None` and loses a pinned
candidate/`none` `N=7`. A later delta that wants the shape must first decide what
`prove_terminal_presentation` should do with more than one admissible position, which is a 3.3
design question and is not answered here.

**Extension C, the `enumerate` row table.** `_complete_rows` admits `enumerate(NAME)` and
`enumerate(NAME, start=K)` when the callee is the unshadowed simple Name `enumerate`, there is
exactly one positional argument and it is a bare Name resolving through the unchanged
`_module_sequences` to a stable flat literal sequence, keywords are absent or exactly one `start=`
with an integer literal that is not a bool, the loop target is an exact two-element tuple or list of
distinct simple Names, the sequence length equals the contract family size, and the sequence
elements in order equal the contract outcome tuple. Position derivation is unchanged: positions come
from the index in the sequence, so `K` is never consulted and `start=0`, `start=1`, and an absent
`start` produce the identical row table. The counter is bound in every row to a distinguished object
that is neither a `bool` nor any contract outcome string, so `_static_bool` returns `None` for it,
`_positions_for` then refuses, and a membership test against a contract name set is false on every
row. Any use of the counter in the correction or decision path therefore refuses. That is a property
of the binding, not a lint against the identifier.

**Extension D, the adjacent if-cap.** The exact pair `X = A * B` immediately followed, in the same
block, by an `ast.If` with no `orelse` whose test is one of `X > 1`, `X >= 1`, `1 < X`, `1 <= X`
against a numeric one that is not a bool, and whose body holds exactly one `ast.Assign` writing a
numeric one to the same Name, is one fold equal to `min(A * B, 1.0)`. It changes exactly three
things and nothing else: the cap reassignment is excluded from the competing-assignment set in the
single-reaching-fold proof; the cap `ast.If` is transparent in `_positions_for`, because it chooses
between `A * B` and `1.0` for the same position rather than selecting family positions; and the
surrogate lowering drops the whole cap statement together with its fold, exactly as
`min(A * B, 1.0)` does. Without the surrogate drop the retained `1.0` reads as a second decision
threshold and abstains at `unresolved-decision-threshold`. Factor resolution, name-set selection,
transport proofs, conclusion consumption, and classification are untouched. The if-cap and `min`
spellings of the same complete correction produce identical coverage records.

**Extension E is recorded and not applied.** The observed mislabel is real: when only the
outcome-headers branch of `_control_tracked` matches, the analyzer has proved that a control reads
outcome columns and has proved neither a p-origin, a correction dependence, nor an
execution-prevention edge, yet it emits `hierarchical-gatekeeping-present`. The specified routing to
the already-registered `pvalue-control-dependence-unresolved` was executed side by side with the
unrouted reason on every row. It relabels **zero** of the 170 evidence cases and **ten** fixtures,
eight of which are frozen gatekeeping controls whose reason is already accurate. The discriminator
that would separate them is whether the control's owner subtree contains a registered test and
whether `can_prevent_slice` holds for an exit edge under it, which is a real design item rather than
a routing tweak. Version 3.4 therefore keeps the current reason and records the defect and its
measured blast radius. No new reason is invented, and the closed set stays at 61.

**The hierarchy registry stays global, and the ordering rule is load-bearing.** Version 3.4 removes
no node kind and no owner class from the control registry, and section 8 would have changed only
which reason is emitted, never whether an abstention occurs. The analyzer runs every unchanged
adapter precondition and global census on original bytes, then the complete unchanged 3.3 pipeline.
A classification is returned untouched and no 3.4 admission is attempted. Only on an abstention is
the source re-analyzed with the comprehension normalization supplied as a graph fact and the
section-6 and section-7 admissions inside the AP recognizer, and that re-analysis is adopted only if
it is itself a classification; otherwise the step-2 abstention reason is returned byte-for-byte. An
earlier revision normalized unconditionally and lost the pinned E16 P3 and E16 P4 candidates. Six
executed rows re-analyze to a different wall than 3.3 recorded, so the rule is exercised rather than
decorative. Classification, correction recognition, row completeness, and wording remain unchanged.

**Executed movement set, none-flip, and admission census.** The movement set is exactly
`{E17:P3 -> candidate/none, corrected_positions {}, N=6}` and
`{E17:P6 -> candidate/strict_subset, corrected_positions {0,1,2}, N=7}`. All 155 earlier evidence
rows, all other thirteen E17 rows, and all 50 corpus adapter rows are outcome-identical; corpus
score remains `0/25` correct and `19/25` misstep. None-flip is zero in every measured population:
corpus-correct `0/25`, opened negatives `0/72`, all correct fixtures `0/194`, cumulative-v3 correct
`0/62`, B5 expression variants `0/63`, 3.1 laundering-adjacent `0/16`, AP correct `0/13`, frozen
gatekeeping `0/12`, 3.3 terminal and helper correct `0/17`, and the new 3.4 correct set `0/11`. The
executed admission census over 170 cases and 245 fixtures is comprehension 16, `enumerate` 16, cap
5, terminal `IfExp` 0.

**Question census and prototype/final asymmetry.** The no-attestation correction-scope census moves
`28 -> 27`, removing exactly `E17:P6:b4e507c4b55954752f14` because the ambiguity its
MaterialQuestion asked about resolved into a demonstrated candidate. No non-MT MaterialQuestion is
removed, and E17 P3 contributed nothing to the removal set because
`hierarchical-gatekeeping-present` is not a qualifying reason. Fidelity between the design prototype
and the final implementation is asymmetric at integration boundaries. The prototype spliced
normalized source text and its AP recognizer therefore read normalized bytes; production supplies
the normalization only as a graph fact and never rewrites source, so its AP recognizer reads the
original bytes. Production is consequently stricter on exactly two correct-analysis fixtures,
`correct-comprehension-corrected-family` and `correct-terminal-verdict-rebound-into-name`, which
abstain at `unresolved-decision-threshold` byte-identically to frozen 3.3 where the prototype
reached covered/`complete`. None-flip evidence transfers to a stricter implementation; a positive
movement does not. The final implementation independently re-demonstrates E17 P3 and E17 P6 at
their exact pinned outcomes through the real adapter and controller path, and a conservative
abstention on either of those two pinned candidates would be a stop rather than permission to loosen
the design. Blind scoring, promotion arithmetic, role maps, sealed audit bytes, wording, contract
profile `1.2.0`, qualified lanes, GrantPins, and the asymmetric attestation rule remain unchanged;
sealed E17 stays `4/6` and is never rescored.

**Adversarial audit fixes, rounds 1 to 3.** Three narrowings were added after the 3.4 build, each
demonstrated on executed probes rather than argued from symmetry. Rounds 1 and 2 withhold a 3.4
admission: the sequence-object closure proves the *object* behind a selection-sequence name stable
rather than only the name, over the whole alias component and including container, field, and
walrus display escapes, and the comprehension lane shares that closure by import rather than by
restatement. A withheld admission returns the row to its frozen 3.3 abstention byte-for-byte, so
neither round can move a public record.

Round 3 is different in kind and is recorded here as a **narrowing of an inherited defect**. The
route it closes carries no 3.4 admission at all. A correct, complete Bonferroni correction over the
declared family, written as

```python
adjusted = results
for name in adjusted:
    adjusted[name]["p"] = min(adjusted[name]["p"] * len(OUTCOMES), 1.0)
```

is classified `candidate`/`none` over the uncorrected family by the byte-frozen 3.3 pipeline on its
own, and step 3 of the ordering rule returns that classification untouched. The identical program
with the same store written through `results` abstains at `pvalue-family-collection-unresolved`.
The frozen engine reconstructs family membership from the stores written through the collection's
own name, so through `results` it sees an unresolvable store and refuses, while through `adjusted`
it sees no store on the collection at all and reads a family whose every member still carries its
raw p. The alias hides the correction rather than resolving the family, so the accusation is false
in the strongest sense available: the analysis it accuses is correct, and the analyzer already
refuses to judge the same analysis written one line differently.

The defect is present in the byte-frozen v3 and v3.3 lanes. Those lanes are unchanged and stay
byte-identical; the narrowing lives only in the v3.4 modules, which supersede them in the active
development binding, and no frozen abstention reason anywhere can move because the closure is
applied to classifications only. Before a classification is returned -- the frozen one at step 3 or
the re-analysed one at step 5 -- no other name for the record collection may receive a store, a
mutation, or a display escape, over the whole alias component and whole-module rather than per
scope. A refused classification lands on `pvalue-family-collection-unresolved`, which is the frozen
reason its through-name sibling already carries; no reason is invented and the closed set stays at
61. A record collection is a name bound once to an empty mapping or list, or to one comprehension,
and filled by subscript store; list builders filled by `append` are excluded because the frozen
B1/B4 closure in `_record_boundary_reason` already refuses a second name for a tracked builder.

Two boundaries are deliberate and are pinned by non-vacuity rows. Reads through an alias are never
refused, so a genuinely uncorrected family with a live second name for its record collection keeps
its `candidate`/`none` row. Passing the collection to a call is not a capture, which is the frozen
`len(OUTCOMES)` discipline the pinned 3.3 evidence rows depend on; a correction written inside a
helper the collection is passed to is already refused by the frozen pipeline at
`unresolved-manual-correction-present`, so no false accusation exists there and argument-passing
semantics are untouched. A store through an alias that cannot have reached any conclusion is
refused with the rest, because whether a store is dead is a question about statement order that
this closure does not answer and its through-name spelling is refused too.

The round-3 movement set is exactly seven oracle rows, all in the refusing direction. Both pinned
3.4 movements, all 170 evidence rows, all 245 fixtures, all 50 corpus adapter rows, every none-flip
population, the E10-E17 retro recall including E17 `6/6`, the question census `28 -> 27`, and the
frozen 3.1/3.2/3.3 anchor bytes are re-demonstrated unchanged. Blind scoring, promotion arithmetic,
role maps, sealed audit bytes, wording, contract profile `1.2.0`, qualified lanes, and GrantPins
remain unchanged; sealed E17 stays `4/6`.
