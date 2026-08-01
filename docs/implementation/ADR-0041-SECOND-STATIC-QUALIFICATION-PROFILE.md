# ADR-0041: Add a second closed static qualification profile

- **Status:** Accepted under the repository owner's standing authorization for narrow,
  non-authority-changing schema maintenance
- **Date:** 2026-07-31
- **Coordinated public schema release:** `0.16.0`
- **Related decisions:** Accepted ADR-0009 through ADR-0012, ADR-0017, ADR-0022, ADR-0039,
  and ADR-0040
- **Finding impact:** None; the target detector remains experimental and Finding-ineligible
- **Execution impact:** None; neither verifier nor fixture construction executes project code

## Context

ADR-0040 freezes `detector:bounded-analysis-method-conflict` version `0.1.0`. The detector can
produce one bounded evaluation-only candidate when an exact human review requirement conflicts
with matching declarations in a selected report and its uniquely connected static source writer.
Its statement does not claim that the source ran, that the mismatch caused a numeric result, or
that the requested method is universally correct.

Qualification needs verified-good and hard-negative controls. These are appropriately static
controls because every material repository premise of the candidate is an immutable report or
source declaration plus a static writer/scope relation. Requiring a project rerun would not prove
those premises and would make the deferred execution system a prerequisite for the evidence-first
product.

Immutable schema v0.15.0 admits static controls only for
`detector:bounded-report-mean-direction`. It fixes the profile target, verifier entry point,
selection rules, and proof facts to a CSV mean-direction grammar. Reusing that record for the
ADR-0040 detector would misstate the detector, evidence, and qualification envelope.

## Decision

### 1. Publish forward-only schema v0.16.0

Preserve v0.15.0 unchanged. Extend the existing `StaticQualificationProfile` and
`StaticQualificationProof` records as closed discriminated variants rather than introducing a
generic static-proof flag.

The original bounded-direction variant keeps its exact v0.15 meaning. The second variant is
`bounded_analysis_method_conflict_v1` and binds only:

- `detector:bounded-analysis-method-conflict` version `0.1.0` and its exact manifest and
  implementation digests;
- the Markdown and Python parser/profile/version manifests in the frozen applicability envelope;
- evaluator entry point
  `sc_referee_evaluation.analysis_method_qualification:verify_bounded_analysis_method_case`;
- a complete implementation/dependency digest lock;
- `.md` and `.py` whole-snapshot candidate enumeration under finite budgets;
- one selected report named by the pre-case opaque assignment;
- one unique supported Python writer for that selected report;
- one closed founder-orientation report operand and one independently derived source operand; and
- exact canonical question, human Answer, and ScientificContract inputs for the review
  requirement.

No profile may mix one variant's detector, verifier, selection rules, vocabulary, or fact shape
with the other variant.

### 2. Add exact review-authority inputs to static fixture proof

The static fixture proof branch gains required, possibly empty, collections for MaterialQuestion,
Answer, and SemanticAssertion inputs. Existing direction controls use empty collections. The new
profile requires exactly one answered, analysis-scoped founder-orientation question, one matching
human Answer, one matching ScientificContract, and the exact accepted Answer-derived requirement
assertion.

The evaluator validates their typed identities and semantic digests, Answer self-digest,
respondent/authority scope, question candidates and scope, contract dimension, accepted assertion,
and exact canonical operand. A model proposal, repository statement, benchmark answer, or
self-reported confidence cannot substitute for the human Answer.

These inputs establish only the requirement governing that review. They do not establish
historical intent or universal scientific adequacy.

### 3. Independently rederive repository facts from raw bytes

The new verifier is isolated from production parsers, scientific-check adapters, detector code,
and semantic fact helpers. It reads no project module and executes no project code. From exact
full-digest bytes it independently:

1. enumerates every `.md` and `.py` snapshot candidate under the frozen budgets;
2. decodes every candidate as strict UTF-8 and rejects inventory or identity gaps;
3. inventories both closed founder-orientation declarations in the complete selected report;
4. parses Python with `ast` without import or execution;
5. recognizes only the two closed source forms: supplied founder alleles passed directly to an
   emission call, or a uniquely bound orientation-repair result passed to that call;
6. admits only one source file containing both one supported operand and one unique literal
   source-parent-relative writer for the selected report;
7. rejects competing writers, competing operands, dynamic paths, unsupported dataflow, weak
   identities, ambiguity, and over-budget cases; and
8. searches all retained report/source bytes and the exact scoped semantic inputs for the ten
   detector counterevidence classes.

The proof records the report operand, source operand, review requirement, exact spans, selected
writer path, complete candidate inventory, supported closure, exclusions, check outcomes, and
chronology. A complete proof does not require that the three operands agree; conflict, match, and
hard-negative states remain visible for independent label and detector comparison.

### 4. Keep qualification chronology and authority unchanged

The accepted order remains:

```text
detector + verifier + profile + selection protocol freeze
  -> opaque case assignment
  -> blind Stage-1/Stage-2 scientific-label freeze
  -> independent static proof freeze
  -> production detector dispatch
  -> fresh cross-provider Stage-3 comparison
```

The proof is qualification-controller evidence and never a production detector input. All four
Stage-1 runs, both Stage-2 adjudications, both fresh Stage-3 comparisons, held-out separation,
counterevidence controls, clustered metrics, pilot-informed thresholds, public reporting, and an
explicit maintainer promotion remain mandatory.

The human authority records may be frozen in an earlier production audit than the opaque
qualification assignment. The proof therefore binds each Question, Answer, ScientificContract,
and accepted assertion by exact typed identity and semantic digest, but does not claim that the
Answer's source-snapshot digest identifies later qualification-case bytes. This separation is
required for hard negatives that preserve the authorized review requirement while independently
varying report or source declarations. It does not permit a verifier to invent or edit authority.

For this exact analysis-scoped profile, static fixtures may carry empty Claim and Operation scope
collections. The profile's immutable raw-byte proof independently establishes the selected report,
source, and writer closure; no production Operation or source span is accepted as a substitute.
The exception is detector- and profile-specific and does not weaken other fixture families.

### 5. Migrate v0.15.0 fail closed

The migration preserves ordinary records but treats existing static profiles and proofs as legacy
evidence whose new variant identity cannot be inferred from a bare public bundle. It retains their
exact v0.15 payloads in namespaced migration metadata, clears authoritative static profile/proof
arrays, demotes dependent static fixtures/outcomes to incomplete legacy proof status, removes
dependent authoritative metric sets, and clears storage manifests. It creates no second profile,
proof, Answer, question, assertion, qualification, maturity, Finding permission, or execution
authority.

## Alternatives rejected

### Generalize the v0.15 direction proof into an open-ended static verifier

Rejected because static completeness is detector- and grammar-specific. An open-ended verifier
would recreate the unbound proof problem that ADR-0012 removed.

### Treat the production detector result as proof of its own control

Rejected because a shared detector/parser defect could certify itself. The qualification verifier
must independently derive all material repository facts.

### Omit the human Answer from qualification proof

Rejected because the detector's narrow statement compares repository declarations with a human
review requirement. Without the exact Answer and scope, that material premise is unknown.

### Require workflow execution instead

Rejected because the candidate makes no execution claim, rerunning large workflows may be
infeasible, and a successful run would not by itself prove the declaration or review requirement.

## Test, acceptance criterion, and remaining limitation

- **Tests required:** both profile variants and cross-variant rejection; exact conflict and matching
  controls; report-only, source-only, competing-writer, competing-operand, dynamic-path,
  unsupported-dataflow, weak-identity, byte-drift, inventory-drift, budget, chronology, Answer,
  question, contract, assertion, and all-ten-counterevidence mutations; static fixture generation,
  Stage 3, metrics, report, JSONL/SQLite, RO-Crate, migration, packaging, and replay; import audit
  proving production fact derivation is not reused.
- **Acceptance criterion:** schema-valid, replayable static controls can bind either exact profile
  without mixing their meanings, while every missing or ambiguous material input fails closed and
  ADR-0040 still emits zero production Findings.
- **Remaining limitation:** implementation supplies mechanism and local control evidence only. No
  authenticated answer-blind cross-provider case, held-out qualification metric, threshold,
  maintainer promotion, or Finding permission follows from this ADR or schema release.
