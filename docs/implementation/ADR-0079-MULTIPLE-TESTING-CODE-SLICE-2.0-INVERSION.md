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
