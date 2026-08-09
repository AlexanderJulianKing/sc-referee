# Experiment 0057: Founder-orientation semantic v3 shadow recognizer

- **Status:** Active development shadow; not qualified or promoted for Finding output
- **Date:** 2026-08-09
- **Governing boundary:** ADR-0069 and the frozen founder-orientation v2.2.6 tuple
- **Production impact:** Adds an independent question-only shadow adapter; v2.2.6 remains present
  and byte-identical
- **Finding impact:** None; this experiment does not qualify a detector or authorize a Finding
- **Execution impact:** None; the recognizer is static and never executes project-authored code

## Decision

Evaluate a proof-producing semantic abstract interpreter alongside founder-orientation v2.2.6.
The analyzer may recognize more compositional Python spellings, but it has no observation authority
by itself. It must emit a closed typed certificate, and a smaller independent kernel must accept
every row-alignment, transform, selector, fold, sink-lineage, path-agreement, noninterference, and
comparison-completeness obligation before the adapter can emit an operand.

The v2 and v3 adapters are independent inputs to the existing scientific-check reducer. If both
are applicable and disagree on the operand or analysis-scope join, the module is ambiguous. An
explicit ambiguity from either adapter also dominates. There is no vote, precedence rule, or
fallback that converts disagreement into an operand. V2 abstention does not manufacture a vote
against a complete v3 certificate.

## Frozen epistemic boundary

- An orientation observation describes the exact report-reaching equality selector and its
  staged-column parity. It does not infer intended biology, approve a repair, establish execution,
  or certify numeric correctness beyond the closed proof.
- Selector recovery is extensional over exactly one predicate and exact numeric false/true values.
  Equality must receive the strictly larger value.
- A parity transform is accepted only when the kernel can justify it over the represented runtime
  domain. In particular, xor-one, absolute-difference-one, and logical-not remain abstentions
  until a separate proof establishes a binary staged-column domain; their Python semantics are
  not complements over arbitrary numeric values.
- Helper bodies are evaluated with call-site abstract arguments. Unsupported recursion, variadic
  dispatch, higher-order use, or unresolved control joins abstain when they can reach the proof
  slice.
- Ordinary opaque constructs outside the certified slice do not invalidate a certificate. The
  v2 module-wide bans for reflection, import substitution, dynamic dispatch, executable
  annotations, star imports, and builtin shadowing remain fail-closed.
- The optional single-parity-bit CSV refinement is not enabled in semantic v3.0.0. Any unresolved
  parity remains an abstention.
- Production code execution is prohibited. Intake sandbox evidence is not an analyzer input.

## Implementation identity

The v3 adapter implementation digest binds the complete new semantic dependency closure:

1. `founder_orientation_semantic_adapter.py`;
2. `founder_orientation_semantic.py`;
3. `founder_orientation_certificate.py`; and
4. `founder_orientation_semantic_ir.py`.

The closure also binds the frozen v2/report helpers reused for parsing, hard bans, report
reconciliation, and tokenization. A change to any bound byte changes the adapter identity.

## Development acceptance gates

- all five error-bearing founder pilot workflows produce the repaired operand under v3;
- all ten paired pilot controls produce no repaired operand;
- every historical executable wrong-answer counterexample either abstains or agrees with runtime;
- all 27 envelope-10 burned cases and the frozen v2 suite remain green;
- release-manifest, regression-corpus, capability-ledger, and prospective-template derivations
  replay from the changed component inventory; and
- the repository's complete lint, type, test, and starter-validation gates pass.

Passing these development gates does not promote v3 beyond question-only shadow status. Any later
Finding authority still requires the accepted prospective qualification and explicit promotion
process.
