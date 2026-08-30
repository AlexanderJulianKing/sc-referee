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
