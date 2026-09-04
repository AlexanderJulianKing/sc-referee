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

**Adversarial audit fix, round 4.** The round-3 audit found one route the round-3 closure does not
cover, and it is the same defect reached through a different binding. A correct, complete
Bonferroni correction over the declared family, written as

```python
for name, record in results.items():
    record["p"] = min(record["p"] * len(OUTCOMES), 1.0)
```

is classified `candidate`/`none` over the uncorrected family. `record` is not a second name for the
collection, so no alias edge binds it, and `results.items()` is a call on the collection's own
name, which round 3 excludes because the collection's own stores are exactly what the frozen engine
already judges. The store is invisible to the engine for the round-3 reason: family membership is
reconstructed from the stores written through the collection's own name, and this store names
`record`.

Rounds 1 to 3 each closed one binding form and the next audit found another. Round 4 closes the
class instead, by enumerating every binding that reaches a record rather than matching the spelling
that was reported. A record-derived binding is any name bound to one of the collection's records,
to the collection itself, or to a container of its records: the mapping views `values()` and
`items()`, the wrappers `iter`, `list`, `tuple`, `sorted`, `reversed`, `enumerate`, and `zip`, the
shallow copies `dict(X)` and `X.copy()`, the lookups `X[k]`, `X.get(k)`, `X.setdefault(k, ...)`,
and `X.pop(k)`, `next(...)` over any of them, an index into any of them, a comprehension that
yields records, the walrus and `async for` spellings of each, tuple and nested unpacking of any of
them, and any chain of the above. A store, an in-place mutation, or a display escape through any of
them refuses the classification exactly as round 3 does, on the same reason,
`pvalue-family-collection-unresolved`, which the through-name sibling already carries. No reason is
invented and the closed set stays at 61. The narrowing again lives only in the v3.4 modules and is
applied to classifications only, so the byte-frozen lanes are unchanged and no frozen abstention
reason can move.

Three boundaries are deliberate and each is pinned by a non-vacuity row and an executable mutation
kill. Reads are never refused: `for name, record in results.items(): flag = record["p"] < ALPHA` is
the single most common correct presentation idiom, six read-only controls on genuinely uncorrected
families keep their accusations, and the pinned E17 P3 movement is built on the same shape. The key
half of an `items()` unpack is not a record: a key is not a record, the store a key reaches is
written through the collection's own name and is already refused, and treating the key as a record
would swallow a true accusation whose presentation loop calls a method on the key. The target of a
bare `for x in X` is not a record either: iterating a mapping yields keys and iterating a collected
p-value table yields floats, and the collection's seed does not say which. Four pinned rows are
true accusations that survive only because of that boundary -- E10 P5 and E12 P5, whose partial
Holm adjustment is written `for row, adjusted in zip(primary, p_adjusted): row["p_adjusted"] = ...`
with the `multipletests` call itself plainly visible, and two open-corpus missteps that read a loop
variable of a tracked list into a display. Enumerating those targets closes no demonstrated route
in exchange, because where a bare iteration really does hand out records the store it reaches is
`X[k][...]`, written through the collection's own name and already refused.

One residual is named rather than left to a later audit. Argument passing stays a non-capture under
the frozen discipline, so a helper that receives the record and stores through its own,
differently named parameter is outside this closure and its row is still classified
`candidate`/`none`. It is carried in the round-4 oracle as an open false accusation, alongside the
twin whose helper parameter reuses the caller's name and which therefore refuses through
whole-module name matching. Closing it would mean deciding what a helper parameter aliases, which
is the same wider question the round-3 oracle left open for the collection-argument spelling.

Both pinned 3.4 movements, all 170 evidence rows, all 245 fixtures, all 50 corpus adapter rows,
every none-flip population including the round-1, round-2, and round-3 rows, the E10-E17 retro
recall including E17 `6/6`, the question census `28 -> 27`, and the frozen 3.1/3.2/3.3 anchor bytes
are re-demonstrated unchanged. Blind scoring, promotion arithmetic, role maps, sealed audit bytes,
wording, contract profile `1.2.0`, qualified lanes, and GrantPins remain unchanged; sealed E17
stays `4/6`.

**Adversarial audit fix, round 5.** Round 4 closed every binding a correction store can travel
through inside one scope and named the one route it could not reach. The custodian reproduced that
route through the real contract and audit pipeline: a correct, complete Bonferroni correction over
the declared family, written as

```python
def bonferroni_adjust(entry, n_tests):
    entry["p"] = min(entry["p"] * n_tests, 1.0)


for name, record in results.items():
    bonferroni_adjust(record, len(OUTCOMES))
```

is classified `candidate`/`none` over the uncorrected family. Round 4 enumerates `record`
correctly; the store it looks for is not there. The store is `entry["p"] = ...`, argument passing
is a non-capture under the frozen discipline, and nothing binds `entry` to the record. Round 4's
names are matched module-wide, so the twin program whose helper parameter is also called `record`
already refused: the disposition turned on the parameter name alone.

Round 5 adds one edge. A call whose callee resolves to a project-local definition in the same
module makes the call site a mutation of every argument whose bound parameter is stored through in
the callee body. That mutation is checked against the round-3 and round-4 name sets exactly as a
direct store is, and it lands on the same reason, `pvalue-family-collection-unresolved`, which the
through-name sibling already carries. No reason is invented and the closed set stays at 61. The
narrowing again lives only in the v3.4 modules and is applied to classifications only, so the
byte-frozen lanes are unchanged and no frozen abstention reason can move.

Three dispositions are deliberate. Callee resolution is by definition, not by name shape: a callee
resolves only to a `def`, an `async def`, a name bound once to a `lambda`, or a method of a class
defined in this module, and only when the name has exactly one such definition and this module
binds it nowhere else. Methods resolve through the class name, through a variable bound once to a
constructor call on that class, or through the enclosing method's own first parameter, with
`staticmethod` and `classmethod` deciding the receiver; `map` and `filter` resolve their callable
and apply it to the elements of the iterables beside them, as do `sorted`, `min`, and `max` for
`key=`. Everything else resolves to nothing and stays a non-capture, which is the frozen
`len(OUTCOMES)`, `", ".join(MUSCULOSKELETAL)`, `print(record)`, `sorted(results.items())`
discipline the pinned evidence rows depend on. Argument binding covers the positional slots, the
keyword names, and both star buckets: a starred or double-starred argument forwards an unknown
position, so it is bound to every parameter of its callee at once and is captured when any of them
stores, which is the conservative reading and needs no rule of its own. Recursion resolves to a
fixpoint rather than to a conservative refusal, because the storing set only grows.

A parameter is stored through when the round-3 and round-4 closures say so, run over the callee
body with the parameter seeded as both a mapping of records and a sequence of them. The seeding
difference from the module level is deliberate: a bare `for x in X` target is left opaque at module
level because the collection's seed does not say whether iterating it yields keys, floats, or
records, and a parameter has no seed at all -- it holds whatever the call site handed it.

Two boundaries are recorded rather than hidden. A helper defined in a sibling project module stays
a false accusation, because this recognizer reads one source file and refusing on an unresolvable
callee would refuse every builtin and library call the pinned evidence rows depend on; the row is
carried in the round-5 oracle with `expected_open_false_accusation`, and closing it means widening
what the recognizer reads rather than what it infers. A helper that only reads its parameter, but
reads it with a method call, is refused, because round 5 reuses the frozen B1/B4 receiver-method
census unchanged rather than enumerating which method names are safe; no row in the 170 evidence
sources, the 245 fixtures, or the 50 corpus adapter rows has that shape, so the cost is a pinned
hypothetical rather than a measured loss, and it too is carried as an oracle row.

Both pinned 3.4 movements, all 170 evidence rows, all 245 fixtures, all 50 corpus adapter rows,
every none-flip population including the round-1, round-2, round-3, and round-4 rows, the E10-E17
retro recall including E17 `6/6`, the question census `28 -> 27`, and the frozen 3.1/3.2/3.3 anchor
bytes are re-demonstrated unchanged. The round-4 residual set is now empty. Blind scoring,
promotion arithmetic, role maps, sealed audit bytes, wording, contract profile `1.2.0`, qualified
lanes, and GrantPins remain unchanged; sealed E17 stays `4/6`.

**Adversarial audit fix, round 6.** Round 5 read every callee it could not resolve as a
non-capture. The round-4 and round-5 adversarial audit demonstrated fourteen deployed routes
through that reading, each a complete and correct Bonferroni pass over the declared family
classified `candidate`/`none` over the uncorrected family, and the custodian rebuilt every one of
them as a real project and confirmed the disposition through the real contract and audit pipeline.
The routes are `dict.update(record, p=...)` and `operator.setitem(record, ...)`;
`functools.partial(rescale, family_size=6)`, a static method stored in a name,
`ADJUSTERS["bonferroni"](record, 6)`, a storing lambda held in a list, a decorator-supplied
wrapper, and `setattr` on a property-setter wrapper; a storing callback reaching every record
through `pd.Series(...).apply(rescale)`, and a helper handed `[results[name]]`; a returned alias
and a returned values view; a no-argument closure over the collection and a default argument bound
to the record; and six shapes in which the correcting helper is defined exactly once in the scope
the call site reads it from but round 5's module-wide shadow census refused to resolve it.

Round 6 decides those calls, in both directions, and adds no reason. A call that is handed a
tracked object -- the collection, a round-3 alias, or a round-4 mapping, sequence, or record
binding -- is a mutation of that object unless the callee is a project-local definition whose body
only reads what it binds, or is a read-only builtin or library API on a closed allowlist. Calls
with no tracked argument are untouched, so the frozen `len(OUTCOMES)` and
`", ".join(MUSCULOSKELETAL)` non-capture discipline every earlier round preserves is exactly as it
was. The allowlist is measured rather than chosen: a census over the 245 prototype fixtures, the
E10-E17 envelope cases, the open-corpus rows, and the round-1 through round-5 oracle sources
reports every callee that receives a tracked argument anywhere in the evidence base, and exactly
those are on it together with their obvious read-only siblings -- the builtins `len` (45 rows),
`zip` (22), `list` (6), `sorted` (6), `enumerate` (5), `set` (5), `min` (4), `max` (3), `iter`
(2), `dict`, `float`, `next`, `print`, `reversed`, `sum`, and `tuple`; the str methods, which
carry 470 of the measured calls; the imported `multipletests` (14), `mean` (8), and `stdev` (8);
the module APIs `statistics.mean`, `statistics.stdev`, `stats.ttest_ind` (4), `pg.multicomp` (2),
and `pd.DataFrame`; and the container-insertion methods, measured as
`secondary_results.append(result)` on E13:P5. `getattr`, `setattr`, `delattr`, `exec`, `eval`,
`vars`, `globals`, `locals`, `apply`, `functools.partial`, and the `operator` mutators are never
on it, and `map`, `filter`, the `key=` builtins, and the `apply`-shaped library methods are on it
only while the callable beside them resolves read-only.

Four further dispositions follow. Callee resolution is now per scope chain: each function and
lambda owns the names its own body binds, a class body owns its own attributes and is never on a
function's scope chain, and the module owns the rest, so a callee resolves when the innermost
scope on the chain that binds the name binds it exactly once and binds it as a definition.
Anything else is unresolvable and fails closed, including two conditional definitions, an import
followed by a definition, a class body binding one method name twice, a name bound to a partial or
a bound method or a dictionary entry, and a subscript callee. The result of a call that is handed
a tracked object carries that object's role unless the callee provably hands back nothing it was
given, so `target = identity(record)` binds the record itself while a helper returning a new
dictionary built from one collected p hands back nothing. A project-local callable that stores
through a parameter is a storing callable, and so is any name, container entry, `functools.partial`,
bound or static method, or decorated definition that carries one; invoking one with a tracked
argument is a mutation, and so is passing one to a call that also carries a tracked argument or
receiver. A `def` or `lambda` whose body stores through a free variable is a mutation at its
definition site whether or not it is called, because a definition is an escape, and a default
argument bound to a tracked name is the same escape one binding earlier.

Five soundness fixes recover true accusations the round-5 closure lost, each on a family that
really was left uncorrected. A parameter is seeded with the role of the argument it binds and not
with both roles at once, so a helper that iterates its mapping parameter bare yields keys exactly
as the module-level bare-iteration boundary says. A starred argument forwards elements and a
double-starred argument forwards values, so `*record` and `**record` hand over strings and scalars
and bind nothing, while a bucket with no role of its own is still forwarded conservatively. A
subscript or lookup on a record is a scalar and a subscript of a mapping of records is a record,
so a helper handed one collected p receives a float. A parameter rebound to a fresh value in
straight-line code, before the parameter is read at all, is detached from the argument, and
`dict(entry)` detaches only a record-role parameter because a shallow copy of a mapping of records
still holds the same records. A wrapper name the module binds itself is resolved as the definition
it is rather than recognized by spelling, so a project-local `sorted` returning unrelated
dictionaries is not read as the builtin row wrapper.

The whole delta lives in the v3.4 correction model. The v3.4 dataflow module is byte-unchanged, so
the ordering rule, the section-6 and section-7 admissions, the closed reason set of 61, and every
abstention path are untouched, and the byte-frozen 3.1, 3.2, and 3.3 lanes stay byte-identical.
Every refused row lands on `pvalue-family-collection-unresolved`, which the through-name sibling
already carries. Across the 245 fixtures, the E10-E17 envelope cases, the open-corpus rows, and
the round-1 through round-5 oracle rows -- 525 rows in all -- exactly one row moves:
`correct-record-in-helper-imported-from-a-sibling-module`, the open false accusation round 5 pinned
by name, which now refuses rather than accusing a correct analysis. The move is declared in the
test rather than by editing the round-5 oracle, whose pins stay as round 5 measured them. Five
costs are pinned by name in the round-6 oracle, each a refusal of a genuinely uncorrected family:
`boundary-helper-parameter-rebound-inside-a-branch`, because on the path where the branch is not
taken the store is written through the record; `boundary-overwritten-class-method`, because a class
body binding one method name twice does not say which definition runs; and
`boundary-read-only-helper-calling-keys-on-its-parameter`,
`boundary-read-only-helper-calling-items-on-its-parameter`, and
`boundary-read-only-helper-calling-copy-on-its-parameter`, which are the rest of the frozen B1/B4
receiver-method census whose `.get()` sibling the round-5 oracle already pins. No row in the 170
evidence sources, the 245 fixtures, or the 50 corpus adapter rows has any of those shapes, so each
cost is a pinned hypothetical rather than a measured loss. Both pinned 3.4 movements, the E10-E17
retro recall, the question census `28 -> 27`, and the frozen anchor bytes are re-demonstrated
unchanged. The residual set is empty: no correct-analysis row in the round-6 oracle is left
accused, and none is pinned open.

**Adversarial audit fix, round 7.** Round 6 fails closed on a callee it cannot resolve. It did not
fail closed on a value it cannot follow or on a callable it cannot resolve, and it keyed its
library allowlist on the spelling of a name rather than on what the imports say the name is. The
round-6 adversarial audit demonstrated nine deployed routes through those three gaps, each a
complete and correct Bonferroni pass over the declared family classified `candidate`/`none` over
the uncorrected family, and the custodian rebuilt every one of them as a real project and confirmed
the disposition through the real contract and audit pipeline. The routes are a class wearing the
`json` spelling beside a storing `dumps` staticmethod; a record put into a list by `append` and
then corrected through the list, and the same through `extend`; a helper returning a generator
expression over its parameter; and four callables reaching `pd.Series(...).apply` -- a wrapper that
stores only by calling a storing helper, a callable held in an attribute, one taken out of a
dictionary with `.get`, and one returned by a chain of identity functions. In the other direction
the audit demonstrated ten deployed losses of a true accusation: `import json as payload` and
`from json import dumps as serialize`, `copy.deepcopy`, `pprint.pprint`, a `csv.DictWriter` writing
each record out, `seen.index` and `seen.count` after an allowlisted `seen.append`, a genuine
`functools.wraps` wrapper around a read-only helper, a helper returning `{"names": list(table)}`
over a mapping parameter, a method whose bare call resolved to a same-named sibling method instead
of the module function, and a bare call to an `async def`.

Round 7 makes the three sides uniform and adds no reason. Value flow now fails closed the way
callee flow does. `append`, `extend`, `insert`, `add`, and a subscript store put the collection's
own record objects into another container without copying them, so that container holds the
family's records and a store written through one of its elements is a store into the family; the
insertion call itself stays read-only, because it does not write into the record. A container
reached *only* by an insertion is judged on what is done to it afterwards, not on the insertion:
the frozen receiver-method census reads any method call as an in-place mutation, so counting
`held.append(record)` against `held` would refuse `seen.append(record); seen.index(record)`, which
only reads a family that really was left uncorrected. Such a container therefore permits the
insertion and query methods that filled and read it and refuses on everything else -- an augmented
assignment, a `del`, a nested subscript store, or any other method call -- while a container the
round-6 enumeration already reached by an ordinary binding form keeps its round-6 disposition
exactly. A generator expression, a comprehension, and a `lambda` are objects that hand out whatever
their body names, so a helper returning either hands the record straight back, while
`[row["p"] for row in results.values()]` stays fresh because its element is a scalar. Iterating a
mapping yields its keys, so the freshness test draws the module-level bare-iteration boundary one
scope in and `{"names": list(table)}` over a mapping parameter is a fresh dictionary of strings;
the same wrapper over a sequence parameter yields the records and keeps its root.

A callable position fails closed the same way. Round 6 asked whether a callable beside a tracked
argument was known to store and admitted everything it could not read; the question is now the
other way round, and a callable position is admitted only for a `lambda` or a project-local
definition that does not store, a read-only builtin, an allowlisted library target, or a bound
method of a tracked container whose spelling is on a closed read-only method set from which `pop`
and `setdefault` are absent. The classification runs after the interprocedural storing fixpoint,
which is what closes the wrapper route, and the role enumeration and the call census feed each
other to a fixpoint for the same reason: deciding whether a call hands an argument back needs
callee resolution, and callee resolution needs the roles. A callback-bearing call also reaches its
receiver's roots unconditionally, which is what closes the four `apply` routes: `apply` is on the
never-allowlisted callee set and stays there, so the callable beside it is never consulted and the
receiver is the only place the records appear.

The allowlist is keyed on import-resolved targets rather than on spellings. A qualified or bare
library callee is allowlisted only when its base name is bound in the scope chain exclusively by
`import` statements and the identity those statements give it is an allowlisted target:
`import pandas as pd` and `import pandas` are both `pandas`, `from scipy import stats` and
`import scipy.stats as stats` are both `scipy.stats`, `from json import dumps as serialize` is
`json.dumps`, and `from operator import setitem as put` is `operator.setitem`. A base name bound by
anything else is not a library name, so `json = Mutator` resolves project-locally to the class and
its storing staticmethod is seen rather than merely feared. Five measured targets are added, each
justified by one named oracle row that loses a true accusation without it -- `copy.copy` and
`copy.deepcopy`, `pprint.pprint` and `pprint.pformat`, `json.load` and `json.loads` as the read
siblings of the already-measured `json.dump` and `json.dumps`, the `csv` writer constructors with
the `writerow`, `writerows`, and `writeheader` methods on a name bound exactly once to one of them,
and the container query methods `index`, `count`, and `get` on a receiver the role enumeration
already tracks -- together with the `math` reducers, which are the scalar-returning siblings of the
already-measured `statistics` reducers. The forbidden set is kept exactly as it was, and `update`
stays off the insertion allowlist because `dict.update(record, p=...)` is the measured round-6
unbound-mutation route.

Three resolution-semantics defects are fixed. A class body is not an enclosing lexical scope in
Python, so a bare `inspect` inside `Report.show` resolves to the module-level `inspect` and never
to `Report.inspect`, which is reached only through `self.`, `cls.`, or `Report.`. A `global` or
`nonlocal` declaration continues the lookup in the scope it names, and a declaring scope that also
writes the name leaves the target ambiguous and fails closed. A decorator whose structure is a
`functools.wraps`-style forwarder is transparent, proved rather than guessed: one plain parameter,
every own return the same bare name, that name bound by exactly one nested `def`, a wrapper that
neither stores through its parameters nor writes through a free variable, and no call in the
wrapper but a call of the decorator's own parameter.

The whole delta again lives in the v3.4 correction model. The v3.4 dataflow module is
byte-unchanged, so the ordering rule, the section-6 and section-7 admissions, the closed reason set
of 61, and every abstention path are untouched, and the byte-frozen 3.1, 3.2, and 3.3 lanes stay
byte-identical. Every refusal this round produces lands on `pvalue-family-collection-unresolved`,
which the through-name sibling already carries. Across the 245 fixtures, the E10-E17 envelope
cases, the open-corpus rows, and the round-1 through round-6 oracle rows -- 573 rows in all -- not
one row moves, and the round-6 and round-5 move maps are declared empty in the test rather than
assumed. Five costs are pinned by name in the round-7 oracle, and every one of them is inherited
from an earlier round's rule rather than introduced here: `boundary-unawaited-async-call`, because
a bare call to an `async def` creates a coroutine and runs no body and this recognizer does not
reason about awaits; `boundary-lru-cache-decorated-read-only-helper`, because a library decorator
is a call this module cannot read; `boundary-record-inserted-by-subscript-into-a-second-mapping`,
because a bare name bound into a subscript location escapes under the round-1 and round-2 rule;
`boundary-read-only-helper-calling-values-on-its-parameter`, which is the frozen receiver-method
census one method along from the three the round-6 oracle pins; and
`boundary-read-only-pandas-apply`, because `apply` is on the never-allowlisted callee set. Three
further correct-analysis rows are refused by an upstream gate rather than by this closure -- the
API-resolution gate, the frozen helper yield census, and the p-value consumer proof -- and are
recorded with the reason they actually carry. Both pinned 3.4 movements, the E10-E17 retro recall,
the question census `28 -> 27`, and the frozen anchor bytes are re-demonstrated unchanged. The
residual set is empty: no correct-analysis row in the round-7 oracle is left accused, and none is
pinned open.

**Custodian post-audit note, 2026-09-02 (rounds 6 and 7 merged with measured residuals).** The
round-7 adversarial re-audit returned FIX-REQUIRED, the fourth consecutive verdict on this closure,
and the claim above that the residual set is empty holds only inside the pinned universe. Outside
it, the custodian rebuilt every audit shape as a real project and measured it through the real
contract and audit pipeline (`e18-tools/codex-r7-pipeline-measurement.txt` and
`codex-r7-plain-store-measurement.txt` beside this repository). Four plain-store routes still
publish an accusation against a correct, complete Bonferroni pass: a list owned by a dictionary key
or a `defaultdict` that records are appended to and then corrected through; a two-hop identity
return (`pass_one` calling `pass_two`) whose result is stored through; and a lambda whose default
argument hands the record back through a zero-argument call. A project-local `append` method on an
object the resolver cannot bind is admitted by spelling and stores through its argument. Seven
read-only shapes on an uncorrected family now refuse without a pin: `np.array(list(...values()))`,
`OrderedDict(results)`, `deque(results.values())`, `tabulate(results.values())`,
`key=operator.itemgetter("p")`, a tracing `functools.wraps` decorator that prints before
forwarding, and a helper returning a scalar projection `{name: table[name]["p"]}`. None of these
shapes occurs in the 120 blind cases of E10 through E17, the 245 fixtures, or the corpus rows, and
the 573-row sweep is unmoved, which is why the lane is merged for envelope 18 rather than held for
an eighth round. The residuals are queued as MT 3.5, whose recommended direction is an inversion of
this closure: classify only while every use of the family collection and every value derived from
it stays inside a closed grammar of proven read-only forms, so that convergence is by construction
rather than by enumeration of store shapes.

## Recall-delta 3.5 amendment

The accepted design `docs/implementation/MULTITEST-3.5-RECALL-DELTAS-DESIGN-2026-09-03.md`,
Revision 0, has raw SHA-256
`b48436c2374041fb8a1651ada4e7da920d8a91866c3894c51ea0566bdfa599b2` and advances only the
development check, adapter, and detector to `3.5.0`. Version 3.5 ships four syntactic admissions in
three groups, specifies two more that are not installed, and adds **no scientific classification
rule**, test API, correction form, threshold, family-position source, row-mask route, reader,
reducer, record mutation, conclusion polarity, or wording rule. The closed abstention-reason set
stays at **61** and is byte-identical to the 3.4 set. The contract profile stays `1.2.0`. The
correction recogniser is the 3.4 one, unchanged.

**Corrected trigger attribution, observed rather than inferred.** Two attributions in the E18 recon
are corrected here by measurement, and the corrections decide where the code goes. First, delta 4a
does **not** belong in `_mask`. The recon attributed E18 P3's group-mask refusal to `_mask`
(`dataflow_v3_3.py:7628`) reading its comparator through `_Resolver.string`; an executed counter on
`_mask` during the 3.4 re-analysis of E18 P3 records **zero calls**. The frozen route that parses
`data[data[GROUP_COLUMN] == LOW_SALT]` for a two-step group slice is the engine's own
`_bare_group_mask_frame` (`dataflow_v3_3.py:11751`) and `_mask_rows` (`dataflow_v3_3.py:11855`).
Second, delta 3 does **not** reach the second wall the recon names. On the sealed E18 P6 source with
only the reader opened, the second wall is `helper-free-name-unbound`, captured in the helper
binder's own frame at the free name `row`, line 56, in the helper `group_values`: the comprehension
target of a `return`-statement comprehension is not in `local_names`, because `_store_names` is
collected over `body_without_return`. That wall sits before the AP selector where delta 2 lives.

**Delta 1, formatted display arms, shipped.** At three arm positions only -- the inline arm test in
`_terminal_rendering_ifexp`, the assignment-arm test in `_mt_v21_terminal_rendering_if`, and the arm
test in `_terminal_ifexp_positions` -- an arm is a display value when it is a bare string constant
(frozen, unchanged), a `Call(func=Attribute(value=Constant(str), attr="format"), args=ARGVAL+,
keywords=[])`, or a `JoinedStr` of string constants and `FormattedValue`s. `ARGVAL` is a non-bool
scalar `str`/`int`/`float` constant, such a constant under unary `+`/`-`, or a Name bound exactly
once at module level to a scalar literal with exactly one Store in the whole module and no
`AugAssign`. Every `FormattedValue.format_spec` must be `None` or wholly constant string text, at
least one `FormattedValue` must be present, and the concatenated constant text must satisfy the
frozen 256-byte display bound. An admitted arm must additionally carry an empty `_p_origins` and no
decision position under `_decision_positions_in_expr`; everything else in the frozen exemption is
unchanged. Refused: an argument that is a `Call`, an `Attribute`, a `Subscript`, a `BinOp`, a
`Compare`, or a comprehension; a Name outside the module-constant table; the p-value or any
p-derived value; `keywords` on `.format`; a `Starred` argument; `.format` on anything but a bare
display constant; an attribute call other than `str.format`; the `%` form; a nested call inside an
f-string interpolation; a non-constant `format_spec`; and the matched print-payload arm test at
`dataflow_v3_3.py:13994`, which is deliberately left frozen. The shared `_mt_v21_display_string` and
`_display_string` predicates, which have twenty other call sites between them, are **not** widened.
The design narrows the brief: the threshold `ALPHA` is admitted because it is a module-level
constant, and the p-value is refused, because interpolating a p-derived value would give the
assigned verdict name a p-lineage it does not have.

**Delta 2, set literals in the AP selector, specified and NOT installed.** A module-level `NAME = {
STR (, STR)* }` binding is readable by the membership branch of `_static_bool` when the value is an
`ast.Set` with at least one element and every element a non-bool `str` constant, the written
elements are already unique, the name has exactly one Store or Del in the whole module and no
`AugAssign`, and **every** Load of the name is the right operand of an `In` or `NotIn`
`ast.Compare` with one operator and one comparator. The table is never merged into `sequences`, so a
set can never become a row-table iterator, an `enumerate` argument, a factor source, or an ordered
position source. Refused: `ast.SetComp`, `set(...)`, `frozenset(...)`, any non-string element, a
written duplicate, a name used in iteration, `len()`, subscript, or any non-membership position, a
name bound more than once, and a binding that is not at module level. All nine refusals and the
three admissions are executed against the production predicate.

**Delta 3, standard-library `csv` reader lineage, specified and NOT installed.** `with open(PATH,
KW*) as HANDLE: return list(csv.DictReader(HANDLE))` and the `csv.reader` form are an authorized
reader lineage when the `with` has exactly one item and exactly one body statement, the context
expression is a call to the unshadowed `open` with exactly one positional argument, the `as` target
is a simple Name, the body statement is a `Return` of `list(...)` with one argument and no keywords,
and that argument is a `csv.DictReader`/`csv.reader` call with exactly one positional argument that
is the `with` handle Name and no keywords. `KW` is `newline=`, `encoding=`, or a `mode=` without
`"b"`, each a string constant. Refused: `restkey`, `restval`, an explicit `delimiter`, `dialect`,
`quotechar`, or any other reader keyword; binary mode; a reader not materialised by `list(...)`; a
filtered or transforming comprehension in place of `list(...)`; more than one `with` item; more than
one body statement; an `open` keyword outside the admitted set; and a reader over a handle other
than the `with` target. All nine refusals and both admissions are executed against the production
predicate, and the sealed E18 N6 reader, which iterates `csv.DictReader(handle)` inside a `for`,
records zero admitted paths.

**Delta 4a, numeric group-mask comparator, shipped.** A numeric-token helper is consulted at the
comparator position in `_bare_group_mask_frame` and in `_mask_rows`, and nowhere else. It admits a
non-bool `int`/`float` literal, such a literal under unary `+`/`-`, or a Name bound exactly once at
module level to such a literal, when all of: the mask is an `ast.Compare` with one `ast.Eq` operator
and one comparator whose other side is a `Subscript` reading the contract group column; every
non-header cell of that column in the authorized CSV parses as a finite decimal under `repr`
normalisation; the two contract `group_values` tokens normalise to two distinct decimal texts; the
literal's own normalised decimal text equals exactly one of those two tokens; and the value is not a
`bool`, not non-finite, and its text carries no thousands separator, underscore, or surrounding
whitespace. The admitted value is the CSV token, so everything downstream sees the same string the
frozen path would have seen for a string-spelled group constant. Refused: `!=` and every operator
other than `==`; a comparator that is a call, an attribute, a subscript, or arithmetic; a `bool`; a
non-finite float; a token column that is not wholly decimal; two group tokens that collapse under
normalisation; a literal matching neither token or both; and a mask on a column that is not the
group column. `_Resolver.string` is **not** widened, and neither is `_mask`. `!=` is refused
deliberately: admitting it would require returning the other group token, which means reading the
binary group domain inside a predicate that does not hold it.

**Delta 4b, terminal-position proof for a presentation loop, shipped as 4a's pair.** A sixth `For`
exemption in `_hierarchy_guard` exempts a loop's own iterator control when all five hold: the owner
is an `ast.For`, not `ast.AsyncFor`, with no `orelse` and a non-empty body, and the iterator is a
bare Name, `enumerate(NAME)`, or `enumerate(NAME, start=<int literal>)` with `enumerate`
unshadowed; no node under the loop is a `Return`, `Break`, `Continue`, `Raise`, `While`, `Try`,
`Match`, `Assert`, `With`, `AsyncWith`, `AsyncFor`, `Global`, `Nonlocal`, `Lambda`, `Yield`,
`YieldFrom`, `Await`, `FunctionDef`, `AsyncFunctionDef`, or `ClassDef`, and no call under it
resolves to `sys.exit`; no registered test API call, no recognised correction API call, and no
`.pvalue` attribute read occurs at any source position at or after the loop's own position; for
every name the loop binds, including its target, every Load of that name after the loop's end and
outside it is dominated by a Store outside the loop and after its end; and at least one statement in
the loop body is an `ast.Expr` whose call is a registered sink. The exemption applies to the loop's
own iterator control only: every `If`, `IfExp`, comprehension, and boolean control inside the body
is still a separate entry in the guard's control list, judged on its own frozen exemptions. Refused:
a loop followed by a registered test; an early `return`; a `break`; a `continue`; a binding that
escapes; a loop that renders nothing; an iterator that is a call other than the two `enumerate`
forms; a non-literal `start`; a positional second argument to `enumerate`; an `async for`; and a
loop with an `orelse`.

**Delta 5, cardinality read of the reconstructed family, shipped.** A sixth admitted form in the
`Call` branch of `_off_grammar_transform_guard` admits `len(COLLECTION)` when the callee resolves to
the unshadowed builtin `len` with exactly one positional argument and no keywords; the argument is a
bare `ast.Name`; `_p_sequence` of that Name is exactly the contract-order position tuple `0..N-1`;
the name has exactly one Store or Del in the analysis scope; and every ancestor of the call, up to
and including the enclosing statement, is a display node -- an `ast.JoinedStr`, an
`ast.FormattedValue`, a `"<literal>".format(...)` call, a `print`/`str` call, or a registered sink
call -- with the enclosing statement an `ast.Expr` whose call is a registered sink, and the call
additionally satisfying the frozen `_mt_v2_rendering_load_reaches_sink` route. The admitted value is
the family size, which the analyser already holds from the contract, so the admission introduces no
new value route into the model; what it removes is an unaccounted-for consumer of the record
collection. Refused: a `len()` whose value enters a comparison, arithmetic, a subscript, a `range`
loop bound, a threshold, an assignment to a local, a record store, or a return; a `len()` over a
filtered comprehension or over any Name whose `_p_sequence` is not the complete contract-order
family; a `len()` with keywords or with more than one argument; and a shadowed `len`. The
load-bearing refusal is storing the value before printing it, because a stored value is no longer
provably display-only.

**The ordering rule, inherited unchanged.** A row the unchanged 3.4 lane classifies is returned
untouched and no 3.5 production is attempted. A row it abstains on is re-analysed with the shipped
productions, and that re-analysis is adopted only when it is itself a classification; otherwise the
frozen 3.4 reason is returned byte-for-byte. The round-3 to round-7 alias closure runs before any
classification is returned, at both points a classification can be returned, and is neither
weakened, bypassed, nor reordered. The 3.4 lane is therefore the frozen previous lane under 3.5
exactly as the 3.3 lane was under 3.4.

**The executed movement set is exactly four rows.**

```text
E15:P3:afe47b2a7ea87ed21a69  abstain unresolved-manual-correction-present
                          -> candidate none, corrected {}, N=5            (delta 5)
E17:N1:e2d8b1bdf4baa671a1b4  abstain test-operand-lineage-unresolved
                          -> covered complete, corrected {0,1,2,3}, N=4   (delta 4a)
E18:P2:5a9277448db34379ce78  abstain hierarchical-gatekeeping-present
                          -> candidate none, corrected {}, N=6            (delta 1)
E18:P3:d1b1fc47ccdabd0c2f22  abstain test-operand-lineage-unresolved
                          -> candidate none, corrected {}, N=5            (deltas 4a+4b)
```

Three are catches. **The E17 N1 clearance is true, and a false clearance is held to the same zero
standard as a false accusation.** The source calls `multipletests(p_raw, alpha=ALPHA)` once over all
four declared outcomes and reads every verdict off the `reject` vector, printing the raw p-values
for reference only. Its group constants are the integers `GROUP_LOW = 18` and `GROUP_HIGH = 24`, and
the authorized CSV's `temperature_c` column holds exactly the two tokens `18` (40 rows) and `24` (40
rows). Delta 4a maps each literal onto exactly one token, the operand lineage resolves, and the
**frozen** classifier then reaches `covered`/`complete` over positions `{0,1,2,3}` of 4 on its own.
No 3.5 production made that call. All 181 other evidence rows and all 245 frozen 3.4 fixtures are
outcome-identical, and no frozen classification anywhere is lost.

**Every none-flip population is zero.** Opened negatives `0/81`; corpus correct-labelled cases
`0/25`; all correct-analysis fixtures `0/199`; new 3.5 correct-analysis fixtures `0/5`; frozen 3.4
fixtures that moved at all `0/245`; frozen 3.4 evidence rows that moved at all `2/170`, both pinned;
negatives gaining a candidate `0/81`; real-pipeline negatives gaining a non-complete classification
`0/81`; custodian probe projects that moved `0/64`. The corpus score is unchanged at `0/25` correct
candidates and `19/25` misstep candidates, with zero adapter-row movements across all fifty rows.

**The admission census, across 185 evidence cases and 283 fixtures.** `d1-format-arm` 14 admitted
spans, `d2-set-selector` 0 (specified, not installed), `d3-csv-reader` 0 (specified, not installed),
`d4a-numeric-group` 20, `d4b-loop-terminal` 9, `d5-cardinality-read` 9. Across the 185 evidence
cases the shipped productions fire on **four** rows in total, and every one of them is a pinned
movement; every other admission in the census belongs to a fixture this design authored to test
itself. An executed hook on `_off_grammar_transform_guard` records that 53 opened cases reach the
guard, 17 of them negatives, and that exactly **one** case in the whole opened population carries a
p-derived `len()`.

**Retro candidate recall, computed on opened bytes.** E10 `5/6`, E11 `6/6`, E12 `6/6`, E13 `4/6`,
E14 `4/6`, E15 `4/6` (was `3/6`, delta 5), E16 `4/6`, E17 `6/6`, E18 `4/6` (was `2/6`, deltas 1 and
4). Retro recall over the nine opened envelopes moves from `40/54` to `43/54`, three catches. These
are development projections and never rescore a sealed first-contact envelope: sealed E15 stays
`2/6`, sealed E17 stays `4/6`, sealed E18 stays `2/6`, and the E17+E18 promotion window is unchanged
at `6/12`. The clearance does not enter the recall table, because E17 N1 is a negative; what changes
is that one more correct analysis is positively cleared rather than left unresolved. Eleven of the
54 opened positives still abstain, down from fourteen.

**The correction-scope question census is `28` before and `28` after, with an empty removed set.**
E15 P3 carried no correction-scope question under 3.4 even though its reason qualifies, because
`locate_correction_scope_witness` finds no witness in a program that contains no correction at all.
That is the question layer working, and it is why closing delta 5 removes nothing.

**The decision not to install deltas 2 and 3, with its executed evidence.** Delta 3 was measured
with a deliberately over-generous stand-in: any module containing a `csv.DictReader` or `csv.reader`
call is granted the authorized path, which is strictly looser than the section 1.3 grammar, so
whatever it cannot reach the real grammar cannot reach either. On E18 P6 that stand-in moves the
abstention from `authorized-reader-lineage-unavailable` to `helper-free-name-unbound`, and that wall
sits **before** the AP selector where delta 2 lives, so delta 2 cannot fire on E18 P6 either. Under
the ordering rule an abstaining re-analysis returns the frozen 3.4 reason byte-for-byte, so
installing either production would change no public byte anywhere in the evidence. Delta 2 is
nonetheless demonstrated correct so a later delta can pick it up with the equivalence already
proved: on a pandas rung of E18 P6 that clears the reader and the row model but keeps the `set`
literal, the set and tuple spellings of the same three-name selector both produce
`candidate`/`strict_subset` over positions `(0, 3, 4)` of 8. Neither may be installed until the
third wall behind delta 3 -- the comprehension target bound inside a helper `return` -- is closed
and every population is re-run.

**What is unchanged.** Classification, correction recognition, the AP correction model, wording, the
61-reason closed set, the contract profile `1.2.0`, the round-3 to round-7 closure, every frozen
3.1/3.2/3.3/3.4 file and result, every corpus replay record, every prior comparison row, every
qualified lane, every GrantPin, every wording object, and every scoring byte. The byte-frozen 3.3
dataflow and terminal-presentation modules are copied, not edited: the shipped lane runs
`code_csv_multiple_testing_dataflow_core_v3_5.py` and
`code_csv_multiple_testing_terminal_presentation_v3_5.py`, and the frozen originals stay at their
ADR-0081 digests, asserted by a test that reads each file.
