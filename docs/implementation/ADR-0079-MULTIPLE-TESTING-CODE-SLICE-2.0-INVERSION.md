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
