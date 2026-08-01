# ADR-0038: Admit an exact selected-container cell scope join

- **Status:** Accepted under the repository owner's standing authorization for non-authority-
  changing development ADRs
- **Date:** 2026-07-30
- **Related decisions:** Accepted ADR-0020, ADR-0034, ADR-0035, ADR-0036, and ADR-0037
- **Schema impact:** None; accepted schema v0.15.0 remains unchanged

## Context

ADR-0037 allows an existing static scientific adapter to inspect exact notebook or Quarto cell
bytes, but every static cell observation remains unscoped. That is correct when a cell lives in an
unselected analysis file: repository membership alone does not prove that it contributes to the
reported analysis. It is unnecessarily weak when the selected publication Artifact is the exact
notebook or Quarto container that contains the cell. In that case the immutable artifact identity,
container digest, cell location, and publication-surface selection establish a finite containment
path.

Containment still does not establish execution, primacy, output lineage, or scientific intent. The
question-only scientific-check contract already separates an exact observed operand from the
scientist's later choice of the governing requirement, so selected-container membership can safely
establish applicability without establishing correctness.

## Decision

### 1. Admit only exact selected-container membership

A static cell observation receives an analysis-scope path only when all of the following hold:

1. the inspection source is an independently verified `notebook_cell` or `document_chunk`;
2. its repository path equals the one selected report Artifact path;
3. its parent-container digest equals the selected Artifact's full-digest AssetIdentity;
4. the resolved PublicationSurface selects exactly that Artifact;
5. the child parser identity and cell location passed ADR-0037 verification; and
6. a Quarto cell is not explicitly declared `eval: false`.

The path is `FileRecord -> selected Artifact -> PublicationSurface`. It establishes only that the
exact static source fragment is contained in the exact selected source artifact.

### 2. Permit only the existing question-only consequence

When the existing founder-orientation AST adapter finds exactly one supported target in such a
cell and completes its finite sibling checks, its normalized observation may be `applicable`. The
existing reducer may then ask the scientist which listed requirement governs this review. The
derived SemanticAssertion records only the statically observed code shape and remains
Finding-ineligible.

No statement says that the cell ran, produced an output, is the primary analysis, reflects
historical intent, or is scientifically correct. Those remain explicit non-inferences. An exact
reported-text observation that conflicts with the cell still produces ambiguity rather than a
question.

### 3. Preserve unscoped behavior everywhere else

A cell in an unselected notebook or Quarto file, an ordinary source file lacking typed output
lineage, an explicitly disabled Quarto cell, a weak-digest artifact, a path/digest mismatch, or a
multiple-target source remains unscoped or unsupported. Future scientist-confirmed scope links or
exact source-to-result lineage require a separate decision; this ADR does not invent them.

## Alternatives rejected

### Treat every repository cell as analysis-scoped

Rejected because repositories routinely contain unused, exploratory, tutorial, and sensitivity
code.

### Require proof that the cell executed before asking anything

Rejected because the question reports a static method shape and asks the scientist for the
governing requirement; it does not claim execution. Requiring authenticated execution would make
the evidence-first product unusable on large or non-rerunnable workflows.

### Treat selected-container membership as a Finding premise

Rejected because containment is not execution, code-to-result lineage, scientific intent, or
correctness.

## Test, acceptance criterion, and remaining limitation

- **Tests added:** selected notebook and selected Quarto positive scope joins; exact cell source
  citations; explicitly disabled Quarto, unselected notebook, tampered identity, and existing
  multiple-target hard negatives; no execution; question-only compilation; semantic lock; and
  replay.
- **Acceptance criterion satisfied:** an exact supported method shape inside the exact selected
  notebook or Quarto source can produce one bounded scientist question without claiming that the
  cell executed or that its method is correct.
- **Remaining limitation:** separate analysis files still require exact typed result lineage or an
  explicit scientist-confirmed scope link. Cross-cell state, primary-versus-sensitivity role,
  output provenance, runtime execution, and Findings remain unsupported.
